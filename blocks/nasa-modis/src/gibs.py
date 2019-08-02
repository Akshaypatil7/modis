from io import BytesIO
import tempfile
from pathlib import Path

import requests
from mercantile import Tile
import rasterio as rio

from rasterio.merge import merge

from blockutils.logging import get_logger

logger = get_logger(__name__)


class WMTSException(Exception):
    pass

class GibsAPI:

    def __init__(self):
        self.wmts_url = "https://gibs.earthdata.nasa.gov/wmts"
        self.wmts_endpoint = "/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}" + \
                             "/GoogleMapsCompatible_Level9/{zoom}/{x}/{y}.jpg"
        self.quicklook_size = 512, 512

    def get_wmts_tile(self, date: str, tile: Tile):
        tile_url = self.wmts_url + self.wmts_endpoint.format(date=date, x=tile.x, y=tile.y, zoom=tile.z)

        logger.debug(tile_url)

        wmts_response = requests.get(tile_url)

        if wmts_response.status_code != 200:
            raise requests.RequestException

        return wmts_response.content

    def get_merged_image(self, tiles: list, date: str, output_uuid: str) -> Path:
        """
        Fetches all tiles for one date, merges them and returns a GeoTIFF
        """

        def copy_filelike_to_filelike(src, dst, bufsize=16384):
            while True:
                buf = src.read(bufsize)
                if not buf:
                    break
                dst.write(buf)

        logger.info("Downloading tiles")

        img_files = []

        for tile in tiles:
            img_buffer = BytesIO(self.get_wmts_tile(date, tile))
            tmp_file = tempfile.NamedTemporaryFile()
            with open(tmp_file.name, "wb") as outfile:
                copy_filelike_to_filelike(img_buffer, outfile)

            img_files.append(rio.open(tmp_file.name))

        logger.info("Merging tiles into one GeoTIFF file")

        out_ar, out_trans = merge(img_files)

        img_filename = "/tmp/output/%s.tif" % output_uuid

        merged_img_meta = img_files[0].meta.copy()
        merged_img_meta.update({
            "transform": out_trans,
            "height": out_ar.shape[1],
            "width": out_ar.shape[2],
        })

        with rio.open(img_filename, "w", **merged_img_meta) as dataset:
            dataset.write(out_ar)

        return Path(img_filename)

    def write_quicklook(self, output_uuid: str) -> str:
        """
        Write quicklook (downsampled image) to disk
        """
        pass




