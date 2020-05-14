import uuid
from typing import List

import mercantile
from geojson import Feature, FeatureCollection
import requests
from mercantile import MercantileError
from shapely.geometry import box
from shapely.ops import unary_union

from blockutils.common import (
    BlockModes,
    ensure_data_directories_exist,
    get_block_mode,
    load_query,
    save_metadata,
)
from blockutils.fetcher import AbstractAOIClippedFetcher, AbstractFetcher
from blockutils.geometry import filter_tiles_intersect_with_geometry
from blockutils.logging import get_logger
from blockutils.stac import STACQuery
from blockutils.exceptions import UP42Error, SupportedErrors, catch_exceptions
from gibs import GibsAPI, extract_query_dates

logger = get_logger(__name__)


class Modis:

    DEFAULT_ZOOM_LEVEL = 9

    @staticmethod
    @catch_exceptions(logger)
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

            ensure_data_directories_exist()

            # Get the list of tiles that cover the query AOI. Sorted by (y, x) in ascending order
            try:
                tile_list = list(
                    filter_tiles_intersect_with_geometry(
                        tiles=mercantile.tiles(
                            *query.bounds(), zooms=query.zoom_level, truncate=True
                        ),
                        geometry=query.geometry(),
                    )
                )
            except MercantileError:
                raise UP42Error(SupportedErrors.INPUT_PARAMETERS_ERROR)

            output_features: List[Feature] = []

            date_list = extract_query_dates(query)

            logger.debug("Checking layer %r", query.imagery_layers)
            are_valid, invalid, valid_imagery_layers = self.api.validate_imagery_layers(
                query.imagery_layers, query.bounds()
            )
            if are_valid:
                logger.debug("Layers %r OK!", query.imagery_layers)
            else:
                raise UP42Error(
                    SupportedErrors.INPUT_PARAMETERS_ERROR,
                    "Invalid Layers. %r have invalid names."
                    "%r are layer bounds, search should be within this." % invalid,
                )

            for query_date in date_list:
                for layer in valid_imagery_layers:
                    feature_id: str = str(uuid.uuid4())
                    return_poly = unary_union(
                        [box(*tuple(mercantile.bounds(bbox))) for bbox in tile_list]
                    )
                    feature = Feature(
                        id=feature_id, bbox=return_poly.bounds, geometry=return_poly
                    )

                    try:
                        self.api.write_quicklook(
                            layer, return_poly.bounds, query_date, feature_id
                        )
                    except requests.exceptions.HTTPError:
                        continue

                if not dry_run:
                    # Fetch tiles and patch them together
                    try:
                        self.api.get_merged_image(
                            valid_imagery_layers, tile_list, query_date, feature_id
                        )
                        feature["properties"]["up42.data_path"] = "%s.tif" % feature_id
                    except requests.exceptions.HTTPError:
                        raise UP42Error(
                            SupportedErrors.API_CONNECTION_ERROR,
                            message="Failed to get merged Image",
                        )

                logger.debug(feature)
                output_features.append(feature)

            return FeatureCollection(list(output_features))
