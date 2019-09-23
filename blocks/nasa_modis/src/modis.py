import uuid
from typing import List

from geojson import FeatureCollection, Feature
import mercantile
from shapely.ops import unary_union
from shapely.geometry import box

from blockutils.geometry import filter_tiles_intersect_with_geometry
from blockutils.stac import STACQuery
from blockutils.logging import get_logger
from blockutils.fetcher import AbstractFetcher, AbstractAOIClippedFetcher
from blockutils.common import (load_query, save_metadata, ensure_data_directories_exist,
                               BlockModes, get_block_mode)

from gibs import GibsAPI, extract_query_dates

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

        # pylint: disable=too-many-locals
        # Variables for fetcher TODO
        def fetch(self, query: STACQuery, dry_run: bool = False) -> FeatureCollection:

            ensure_data_directories_exist()

            # Get the list of tiles that cover the query AOI. Sorted by (y, x) in ascending order
            tile_list = list(filter_tiles_intersect_with_geometry( \
                tiles=mercantile.tiles(*query.bounds(), zooms=query.zoom_level, truncate=True),
                geometry=query.geometry()))

            output_features: List[Feature] = []

            date_list = extract_query_dates(query)
            layer_list = query.layers

            logger.debug("Checking layer %r", layer_list)
            are_valid, invalid_names, invalid_geom, valid_layers = self.api.validate_layers(layer_list, query.bounds())
            if are_valid:
                logger.debug("Layers %r OK!", layer_list)
            else:
                raise ValueError("Invalid Layers. %r have invalid names."
                                 "%r are layer bounds, search should be within this." % (invalid_names, invalid_geom))

            for layer in valid_layers:
                for query_date in date_list:

                    feature_id: str = str(uuid.uuid4())
                    return_poly = unary_union([box(*tuple(mercantile.bounds(bbox))) for bbox in tile_list])
                    feature = Feature(id=feature_id,
                                      bbox=return_poly.bounds,
                                      geometry=return_poly)

                    self.api.write_quicklook(layer, return_poly.bounds, query_date, feature_id)

                    if not dry_run:
                        # Fetch tiles and patch them together
                        self.api.get_merged_image(layer, tile_list, query_date,
                                                  feature_id,
                                                  img_format=valid_layers[layer]['Format'])
                        feature["properties"]["up42.data.aoiclipped"] = "%s.tif" % feature_id

                    logger.debug(feature)
                    output_features.append(feature)

            return FeatureCollection(list(output_features))
