import uuid
from typing import List
from pathlib import Path
from collections import OrderedDict

import mercantile
from mercantile import Tile
from mercantile import MercantileError
import requests
from geojson import Feature, FeatureCollection
from shapely.geometry import box
from shapely.ops import unary_union

from blockutils.blocks import DataBlock
from blockutils.exceptions import SupportedErrors, UP42Error
from blockutils.geometry import filter_tiles_intersect_with_geometry
from blockutils.logging import get_logger
from blockutils.stac import STACQuery
from blockutils.wmts import MultiTileMergeHelper
from blockutils.datapath import set_data_path

from blockutils.raster import to_cog

from gibs import GibsAPI, extract_query_dates

logger = get_logger(__name__)
DEFAULT_ZOOM_LEVEL = 9


class Modis(DataBlock):
    def __init__(self, default_zoom_level: int = DEFAULT_ZOOM_LEVEL):
        self.api = GibsAPI()
        self.default_zoom_level = default_zoom_level

    def get_final_merged_image(
        self,
        tile_list: List[Tile],
        valid_imagery_layers: OrderedDict,
        query_date: list,
        feature_id: str,
    ):
        img_filename = Path("/tmp/output/%s.tif" % str(feature_id))
        req_kwargs_list = []
        for layer in valid_imagery_layers:
            req_kwargs_list.append(
                {
                    "req_kwargs": {
                        "layer": layer,
                        "date": query_date,
                        "img_format": valid_imagery_layers[layer]["Format"],
                    },
                    "crs": "EPSG:3857",
                }
            )

        logger.info("Fetching tiles")
        valid_tiles = MultiTileMergeHelper.from_req_kwargs(
            tile_list,
            req=self.api.requests_wmts_tile,
            kwargs_list=req_kwargs_list,
        ).get_multiband_tif(img_filename, return_cog=False)

        logger.info(
            f"There are {len(valid_tiles[0])} valid data tiles out of {len(tile_list)}"
        )

        return img_filename

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
        except MercantileError as mercerr:
            raise UP42Error(SupportedErrors.INPUT_PARAMETERS_ERROR) from mercerr

        output_features: List[Feature] = []

        date_list = extract_query_dates(query)

        logger.debug(f"Checking layer {query.imagery_layers}")
        are_valid, invalid, valid_imagery_layers = self.api.validate_imagery_layers(
            query.imagery_layers, query.bounds()
        )
        if are_valid:
            logger.debug(f"Layers {query.imagery_layers} OK!")
        else:
            raise UP42Error(
                SupportedErrors.INPUT_PARAMETERS_ERROR,
                f"Invalid Layers. {invalid} have invalid names."
                f"{invalid} are layer bounds, search should be within this.",
            )

        for query_date in date_list:
            self.api.get_layer_bands_count(tile_list, valid_imagery_layers, query_date)
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
                img_filename = self.get_final_merged_image(
                    tile_list, valid_imagery_layers, query_date, feature_id
                )
                self.api.post_process(img_filename, valid_imagery_layers)
                to_cog(img_filename, forward_band_tags=True)
                set_data_path(feature, f"{feature_id}.tif")

            logger.debug(feature)
            output_features.append(feature)

        logger.debug(f"Saving {len(output_features)} result features")

        return FeatureCollection(list(output_features))
