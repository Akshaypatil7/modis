import collections
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Tuple

import mercantile
import pytz
import rasterio as rio
import requests
import xmltodict
from dateutil import parser
from requests import Response
from shapely.geometry import box
from rasterio.enums import ColorInterp

from blockutils.exceptions import SupportedErrors, UP42Error
from blockutils.logging import get_logger
from blockutils.stac import STACQuery

logger = get_logger(__name__)


class WMTSException(Exception):
    pass


def move_dates_to_past(date_points: list) -> list:
    """
    Moves dates to the past counting backwards from yesterday if the requested date range extends
    into the future
    Args:
        date_strings -- list of dates

    Returns:
        list of dates
    """
    yesterday = (datetime.utcnow() - timedelta(days=1)).replace(tzinfo=pytz.UTC)
    days_to_move = date_points[-1] - yesterday

    if days_to_move > timedelta(days=0):
        date_points = [date_points[0], date_points[1] - days_to_move]
    return date_points


def extract_query_dates(query: STACQuery) -> list:
    """
    Extraction of query dates usable by GIBS WMTS

    The MODIS block allows STAC parameters time and limit to be set. The MODIS dataset though offers a mostly
    complete coverage of the whole earth every day. By combining time and limit parameters this method returns
    a list of date that can be used for inclusion in WMTS GetTile requests.

    :param query: A STACQuery object
    :return: A list of GIBS WMTS consumable dates
    """

    if query.time is None:
        # Return latest [limit] dates counting from yesterday backwards
        now = datetime.utcnow()
        date_list = sorted(
            [
                (now - timedelta(days=idx + 1)).strftime("%Y-%m-%d")
                for idx in range(query.limit)
            ]
        )
    else:
        date_strings = str(query.time).split("/")
        # time is set, first check if it is an interval or only one point in time
        date_points = [parser.parse(date_str) for date_str in date_strings]
        date_points = move_dates_to_past(date_points)
        if len(date_points) == 2:
            time_diff = date_points[1] - date_points[0]
            days_in_interval = time_diff.days + bool(time_diff.seconds)
            date_list = [
                (date_points[1] - timedelta(days=idx)).strftime("%Y-%m-%d")
                for idx in range(days_in_interval)
            ]
            date_list.sort()
            if len(date_list) > query.limit:
                # Only return the newest dates up to the limit
                date_list = date_list[-query.limit :]
        else:
            # Only one point in time is given; return only that date
            date_list = [date_points[0].strftime("%Y-%m-%d")]
    return date_list


def make_list_layer_band(imagery_layers: collections.OrderedDict, count: int) -> List:
    """
    Makes list of all output bands and their respective provenance.

    :param imagery_layers: All imagery_layers included in output file and attributes
    :param count: The count of all bands in output file
    :return: A list output bands and their provenance
    """
    out_list: List[List] = []
    band_order: List[int] = []
    layer_names: List[str] = []

    for layer in imagery_layers:
        layer_names += [layer] * imagery_layers[layer]["bands_count"]
        band_order += list(range(1, imagery_layers[layer]["bands_count"] + 1))

    for band_number in range(1, count + 1):
        layer_name = layer_names[band_number - 1]
        layer_band = band_order[band_number - 1]
        out_list += [[band_number, layer_name, layer_band]]
    return out_list


class GibsAPI:
    def __init__(self):
        self.wmts_url = "https://gibs.earthdata.nasa.gov/wmts"
        self.get_capabilities_url = "/epsg3857/best/1.0.0/WMTSCapabilities.xml"
        self.wmts_endpoint = (
            "/epsg3857/best/{layer}/default"
            + "/{date}/GoogleMapsCompatible_Level9/{zoom}/{y}/{x}.{img_format}"
        )
        self.wms_url = "https://gibs.earthdata.nasa.gov/wms"
        self.wms_endpoint = "/epsg4326/best/wms.cgi?" + "SERVICE=WMS&REQUEST=GetMap&"
        self.quicklook_size = 512, 512

    def get_capabilities(self) -> Response:
        """
        Get capabilities from WMTS service
        """
        url = self.wmts_url + self.get_capabilities_url
        response = requests.request("GET", url)
        return response

    def get_dict_available_imagery_layers(self) -> dict:
        """
        Get a dictionary of all suitable imagery_layers (with TileMatrixSet ==
        GoogleMapsCompatible_Level9) and output a dict with relevant attributes:
        Identifier, TileMatrixSet, WGS84BoundingBox and Format
        """
        capabilities = xmltodict.parse(self.get_capabilities().text)
        imagery_layers = {}
        for layer in capabilities["Capabilities"]["Contents"]["Layer"]:
            extent_lc = layer["ows:WGS84BoundingBox"]["ows:LowerCorner"]
            extent_uc = layer["ows:WGS84BoundingBox"]["ows:UpperCorner"]
            coords = [float(i) for i in extent_lc.split(" ") + extent_uc.split(" ")]
            extent_bbox = box(*coords)
            candidate = {
                "Identifier": layer["ows:Identifier"],
                "TileMatrixSet": layer["TileMatrixSetLink"]["TileMatrixSet"],
                "WGS84BoundingBox": extent_bbox,
                "Format": layer["Format"].split("/")[1],
            }
            if candidate["TileMatrixSet"] == "GoogleMapsCompatible_Level9":
                imagery_layers[candidate["Identifier"]] = candidate
        return imagery_layers

    def validate_imagery_layers(
        self, imagery_layers: collections.OrderedDict, bbox: List[float]
    ) -> Tuple[bool, Tuple, collections.OrderedDict]:
        """
        Get a dictionary of all suitable imagery_layers (with TileMatrixSet ==
        GoogleMapsCompatible_Level9) and output a dict with relevant attributes:
        Identifier, TileMatrixSet, WGS84BoundingBox and Format
        """
        available_imagery_layers = self.get_dict_available_imagery_layers()
        search_geom = box(*bbox)

        is_name = True
        has_intersection = True

        invalid_names: List[str] = []
        invalid_geom: List[str] = []

        valid_imagery_layers: collections.OrderedDict = collections.OrderedDict()

        for each_layer in imagery_layers:
            is_name = each_layer in available_imagery_layers.keys() and is_name
            if is_name:
                has_intersection = (
                    available_imagery_layers[each_layer]["WGS84BoundingBox"].intersects(
                        search_geom
                    )
                    and has_intersection
                )
                if not has_intersection:
                    invalid_geom += [
                        available_imagery_layers[each_layer]["WGS84BoundingBox"].wkt
                    ]
                else:
                    valid_imagery_layers[each_layer] = available_imagery_layers[
                        each_layer
                    ]
            else:
                invalid_names += [each_layer]

        return (
            (is_name and has_intersection),
            (invalid_names, invalid_geom),
            valid_imagery_layers,
        )

    def download_quicklook(self, layer: str, bbox, date: str) -> Response:
        """
        Fetches an RGB quicklook image using WMS
        """
        logger.debug(f"Will now fetch quicklook {bbox} for date {date}")

        width_height_ratio = abs((bbox[0] - bbox[2]) / (bbox[1] - bbox[3]))
        if width_height_ratio > 1:
            width = self.quicklook_size[0]
            height = int(self.quicklook_size[1] / width_height_ratio)
        else:
            width = int(self.quicklook_size[0] * width_height_ratio)
            height = self.quicklook_size[1]

        params = {
            "LAYER": layer,
            "WIDTH": width,
            "HEIGHT": height,
            "BBOX": ",".join([str(coord) for coord in bbox]),
            "TIME": date,
        }

        quicklook_string = (
            "LAYERS={LAYER}&"
            + "FORMAT=image/jpeg&"
            + "WIDTH={WIDTH}&"
            + "HEIGHT={HEIGHT}&"
            + "CRS=CRS:84&"
            + "BBOX={BBOX}&"
            + "TIME={TIME}"
        ).format(**params)

        logger.debug(quicklook_string)

        response = requests.get(self.wms_url + self.wms_endpoint + quicklook_string)

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                """Quicklook download unsuccessful
                                    with status code """,
                response.status_code,
            )
        return response

    def write_quicklook(self, layer: str, bbox, date: str, output_uuid: str):
        """
        Write quicklook to the quicklook output location
        """
        response = self.download_quicklook(layer, bbox, date)
        name = "/tmp/quicklooks/%s.jpg" % (output_uuid)
        with open(name, "wb") as ql_file:
            for chunk in response.iter_content():
                if chunk:
                    ql_file.write(chunk)

    # Number of variables required to fetch the tiles
    def requests_wmts_tile(
        self, tile: mercantile.Tile, layer: str, date: str, img_format: str = "jpg"
    ) -> requests.Response:
        tile_url = self.wmts_url + self.wmts_endpoint.format(
            layer=layer,
            date=date,
            x=tile.x,
            y=tile.y,
            zoom=tile.z,
            img_format=img_format,
        )

        logger.debug(tile_url)

        try:
            wmts_response = requests.get(tile_url)
            logger.info(f"response returned: {wmts_response.status_code}")
            wmts_response.raise_for_status()
        except requests.exceptions.ConnectionError as conn_err:
            logger.error("Network related error occured")
            raise UP42Error(
                SupportedErrors.API_CONNECTION_ERROR, str(conn_err)
            ) from conn_err
        except requests.exceptions.HTTPError as err:
            logger.error("HTTP error occured")
            raise UP42Error(SupportedErrors.API_CONNECTION_ERROR, str(err)) from err

        return wmts_response

    @staticmethod
    def post_process(img_filename, imagery_layers):
        with rio.open(img_filename, "r+") as dst:
            img_bands_count = dst.count
            for band in make_list_layer_band(imagery_layers, img_bands_count):
                dst.update_tags(band[0], layer=band[1], band=band[2])
            color_interp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue]
            if img_bands_count > 3:
                for _ in range(img_bands_count - 3):
                    color_interp.append(ColorInterp.undefined)

            dst.colorinterp = color_interp[:img_bands_count]

    def get_layer_bands_count(self, tile_list, imagery_layers, date):
        for layer in imagery_layers:
            wmts_response = self.requests_wmts_tile(
                tile_list[0], layer, date, imagery_layers[layer]["Format"]
            )
            img: rio.MemoryFile = BytesIO(wmts_response.content)

            with rio.open(img) as image:
                imagery_layers[layer]["bands_count"] = image.count
