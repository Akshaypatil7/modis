from blockutils.logging import get_logger
from blockutils.stac import STACQuery, BoundingBox

logger = get_logger(__name__)


class WMTSException(Exception):
    pass

QUICKLOOK_SIZE = 512, 512

class GibsAPI:

    def write_quicklook(self, output_uuid: str) -> str:
        """
        Write quicklook (downsampled image) to disk
        """
        pass

    def get_wmts_tile(self):
        """
        Fetch WMTS tiles and return them as georeferenced geotiffs
        """
        pass

    def merge_tiles(self):
        """
        Merge all WMTS tiles into one geotiff
        """


