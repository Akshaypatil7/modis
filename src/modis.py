import uuid
from typing import List

import mercantile
import requests
from geojson import Feature, FeatureCollection
from mercantile import MercantileError
from shapely.geometry import box
from shapely.ops import unary_union

from blockutils.blocks import DataBlock
from blockutils.exceptions import SupportedErrors, UP42Error
from blockutils.geometry import filter_tiles_intersect_with_geometry
from blockutils.logging import get_logger
from blockutils.stac import STACQuery

from gibs import GibsAPI, extract_query_dates

logger = get_logger(__name__)
DEFAULT_ZOOM_LEVEL = 9


class Modis(DataBlock):
    def __init__(self, default_zoom_level: int = DEFAULT_ZOOM_LEVEL):
        self.api = GibsAPI()
        self.default_zoom_level = default_zoom_level

    def fetch(self, query: STACQuery, dry_run: bool = False) -> FeatureCollection:

        query.set_param_if_not_exists("zoom_level", self.default_zoom_level)

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

        # convert the list into FeatureCollection
        output_feat_coll = FeatureCollection(list(output_features))

        logger.debug("Saving %s result features", len(output_feat_coll.get("features")))

        return output_feat_coll
