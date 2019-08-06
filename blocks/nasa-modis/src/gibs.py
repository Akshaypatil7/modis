from io import BytesIO
import tempfile
from pathlib import Path

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
        self.wmts_endpoint = "/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}" + \
                             "/GoogleMapsCompatible_Level9/{zoom}/{x}/{y}.jpg"
        self.quicklook_size = 512, 512

    def extract_query_dates(self, query: STACQuery):
        """
        Extraction of query dates usable by GIBS WMTS

        The MODIS block allows STAC parameters time and limit to be set. The MODIS dataset though offers a mostly
        complete coverage of the whole earth every day. By combining time and limit parameters this method returns
        a list of date that can be used for inclusion in WMTS GetTile requests.

        :param query: A STACQuery object
        :return: A list of GIBS WMTS consumable dates
        """



    def download_wmts_tile_as_geotiff(self, date: str, tile: mercantile.Tile) -> BytesIO:
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

        # TODO don't forget cleanup

        return Path(img_filename)

    def write_quicklook(self, output_uuid: str) -> str:
        """
        Write quicklook (downsampled image) to disk
        """
        pass




