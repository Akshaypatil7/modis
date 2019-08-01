import uuid

from gibs import GibsAPI

from blockutils.stac import STACQuery
from blockutils.logging import get_logger
from blockutils.fetcher import AbstractFetcher

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


    # Fetcher helper classes
    class AOIClippedFetcher(AbstractAOIClippedFetcher):
        def __init__(self):
            self.api = GibsAPI()

        def fetch(self, query: STACQuery, dry_run: bool = False) -> FeatureCollection:

            # Get the list of tiles that cover the bbox. Sorted by (y, x) in ascending order
            bbox_tile_list = list(filter_tiles_intersect_with_geometry( \
                tiles=mercantile.tiles(*query_bbox, zooms=query.zoom_level, truncate=True),
                geometry=query.geometry()))

            ensure_data_directories_exist()

            logger.debug("Search gave %s results", len(oa_features))

            output_features: List[Feature] = []

            for oa_feature in oa_features:
                feature_id: str = str(uuid.uuid4())

                if not dry_run:
                    set_capability(feature, AOICLIPPED, "%s.tif" % feature_id)

            logger.debug(feature)
            output_features.append(feature)

        return FeatureCollection(list(output_features))

