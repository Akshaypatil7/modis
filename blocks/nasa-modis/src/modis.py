import uuid

import mercantile
from shapely.geometry import box
from geojson import FeatureCollection, Feature
import requests

from blockutils.geometry import filter_tiles_intersect_with_geometry
from blockutils.stac import STACQuery
from blockutils.logging import get_logger
from blockutils.fetcher import AbstractFetcher, AbstractAOIClippedFetcher
from blockutils.common import (load_query, save_metadata, ensure_data_directories_exist,
                               BlockModes, get_block_mode)


from gibs import GibsAPI

logger = get_logger(__name__)

class Modis:

    DEFAULT_ZOOM_LEVEL = 9

    @staticmethod
    def run(fetcher: AbstractFetcher):
        query: STACQuery = load_query()
        query.set_param_if_not_exists("zoom_level", Modis.DEFAULT_ZOOM_LEVEL)
        dry_run: bool = get_block_mode() == BlockModes.DRY_RUN.value
        result: FeatureCollection = fetcher.fetch(query, dry_run=dry_run)
        logger.debug("Saving %s result features", len(result.get("features")))
        save_metadata(result)

    class AOIClippedFetcher(AbstractAOIClippedFetcher):
        def __init__(self):
            self.api = GibsAPI()

        def fetch(self, query: STACQuery, dry_run: bool = False) -> FeatureCollection:

            # We take whatever geometry we get and then fetch the corresponding tiles for one year per limit

            # Get the list of tiles that cover the bbox. Sorted by (y, x) in ascending order
            bbox_tile_list = list(filter_tiles_intersect_with_geometry( \
                tiles=mercantile.tiles(*query_bbox, zooms=query.zoom_level, truncate=True),
                geometry=query.geometry()))

            # Filter list by actual geometry
            feature_tile_list = list(filter_tiles_intersect_with_geometry(
                tiles=bbox_tile_list,
                geometry=query.geometry()

            ensure_data_directories_exist()


            output_features: List[Feature] = []

            for idx in query.limit:
                feature_id: str = str(uuid.uuid4())

                # Fetch tiles and patch them together

                feature = Feature()

                if not dry_run:
                    set_capability(feature, AOICLIPPED, "%s.tif" % feature_id)

            logger.debug(feature)
            output_features.append(feature)

        return FeatureCollection(list(output_features))

