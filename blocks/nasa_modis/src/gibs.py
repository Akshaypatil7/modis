from typing import IO, Any
from io import BytesIO
import tempfile
import datetime
from datetime import timedelta
from pathlib import Path

from dateutil import parser
import requests
import mercantile
import rasterio as rio

from rasterio.merge import merge

from blockutils.logging import get_logger
from blockutils.stac import STACQuery

logger = get_logger(__name__)


class WMTSException(Exception):
    pass

class GibsAPI:

    def __init__(self):
        self.wmts_url = "https://gibs.earthdata.nasa.gov/wmts"
        self.wmts_endpoint = "/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default" + \
                             "/{date}/GoogleMapsCompatible_Level9/{zoom}/{y}/{x}.jpg"
        self.quicklook_size = 512, 512

    def extract_query_dates(self, query: STACQuery) -> list:
        """
        Extraction of query dates usable by GIBS WMTS

        The MODIS block allows STAC parameters time and limit to be set. The MODIS dataset though offers a mostly
        complete coverage of the whole earth every day. By combining time and limit parameters this method returns
        a list of date that can be used for inclusion in WMTS GetTile requests.

        :param query: A STACQuery object
        :return: A list of GIBS WMTS consumable dates
        """

        if query.time is None:
            # Return latest [limit] dates counting from yesterday backwards
            now = datetime.datetime.now()
            date_list = sorted([(now - timedelta(days=idx + 1)).strftime('%Y-%m-%d') for idx in range(query.limit)])
        else:
            # time is set, first check if it is an interval or only one point in time
            date_strings = str(query.time).split("/")
            date_points = [parser.parse(date_str) for date_str in date_strings]
            if len(date_points) == 2:
                time_diff = date_points[1] - date_points[0]
                days_in_interval = time_diff.days + bool(time_diff.seconds)
                date_list = \
                    [(date_points[1] - timedelta(days=idx)).strftime('%Y-%m-%d') for idx in range(days_in_interval)]
                date_list.sort()
                if len(date_list) > query.limit:
                    # Only return the newest dates up to the limit
                    date_list = date_list[-query.limit:]
            else:
                # Only one point in time is given; return only that date
                date_list = [date_points[0].strftime('%Y-%m-%d')]
        return date_list


    def download_wmts_tile_as_geotiff(self, date: str, tile: mercantile.Tile) -> IO[Any]:
        tile_url = self.wmts_url + self.wmts_endpoint.format(date=date, x=tile.x, y=tile.y, zoom=tile.z)

        logger.debug(tile_url)

        wmts_response = requests.get(tile_url)

        if wmts_response.status_code != 200:
            raise requests.RequestException

        img: rio.MemoryFile = BytesIO(wmts_response.content)

        bands = []
        with rio.open(img, driver='JPEG') as image:
            for i in range(image.count):
                bands.append(image.read(i + 1))
            tile_meta = image.meta

        tile_transform = rio.transform.from_bounds(*mercantile.xy_bounds(tile),
                                                   width=tile_meta.get("width"),
                                                   height=tile_meta.get("height"))

        tile_meta.update(driver="GTiff", crs="EPSG:3857", transform=tile_transform)

        tmp_file = tempfile.NamedTemporaryFile()

        with rio.open(tmp_file.name, 'w', **tile_meta) as output_tile:
            for idx, band in enumerate(bands):
                output_tile.write(band, idx + 1)

        return tmp_file


    def get_merged_image(self, tiles: list, date: str, output_uuid: str) -> Path:
        """
        Fetches all tiles for one date, merges them and returns a GeoTIFF
        """

        img_files = []
        logger.info("Downloading tiles")
        for tile in tiles:
            tiff_file = self.download_wmts_tile_as_geotiff(date, tile)
            img_files.append(rio.open(tiff_file.name, driver="GTiff"))
        # Now merge the images
        out_ar, out_trans = merge(img_files)

        merged_img_meta = img_files[0].meta.copy()
        merged_img_meta.update({
            "transform": out_trans,
            "height": out_ar.shape[1],
            "width": out_ar.shape[2],
        })

        img_filename = "/tmp/output/%s.tif" % str(output_uuid)

        with rio.open(img_filename, "w", **merged_img_meta) as dataset:
            dataset.write(out_ar)

        return Path(img_filename)

    def write_quicklook(self, output_uuid: str) -> str:
        """
        Write quicklook (downsampled image) to disk
        """
        pass




