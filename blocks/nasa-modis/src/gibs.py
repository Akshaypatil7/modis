import io
import uuid

from mercantile import Tile
import rasterio

from blockutils.logging import get_logger

logger = get_logger(__name__)


class WMTSException(Exception):
    pass

class GibsAPI:

    def __init__(self):
        self.wmts_url = "https://gibs.earthdata.nasa.gov/wmts"
        self.wmts_endpoint = "/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2019-04-20" + \
                             "/GoogleMapsCompatible_Level9/{zoom}/{x}/{y}.jpg"
        self.quicklook_size = 512, 512

    def get_wmts_tile(self, tile: Tile):
        tile_url = self.wmts_url + self.wmts_webm_endpoint.format(x=tile.x, y=tile.y, zoom=tile.z)

        resp = self.get(tile_url, headers={"Cache-Control": "no-cache"})
        if resp.status_code != 200:
            logger.error("Tile fetch request failed! %s %s", resp.status_code, resp.content)
            raise WMTSException()
        else:
            tile_img: rasterio.MemoryFile = io.BytesIO(resp.content)

        tile_img_filename = "/tmp/output/%s.tif" % str(uuid.uuid4())

        bands: list = []
        with rasterio.open(tile_img, driver='PNG') as image:
            for i in range(image.count):
                bands.append(image.read(i + 1))
            meta = image.meta

        tile_transform = rasterio.transform.from_bounds(*mercantile.xy_bounds(tile),
                                                        width=meta.get("width"),
                                                        height=meta.get("height"))

        # Amending metadata of panchromatic tile
        meta.update(driver="GTiff", crs="EPSG:3857", transform=tile_transform)

        with rasterio.open(tile_img_filename, 'w', **meta) as output_tile:
            for idx, band in enumerate(bands):
                output_tile.write(band, idx + 1)

        return Path(tile_img_filename)

    def get_merged_image(self):
        """
        Merge all WMTS tiles into one geotiff
        """
        for tile in tiles:
            pass

    def write_quicklook(self, output_uuid: str) -> str:
        """
        Write quicklook (downsampled image) to disk
        """
        pass




