from typing import IO, Any
from io import BytesIO
import tempfile
import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET
from pathlib import Path
import collections


from dateutil import parser
import requests
from requests import Response
import mercantile
import rasterio as rio
from rasterio.merge import merge
import numpy as np
from shapely.geometry import box

from blockutils.logging import get_logger
from blockutils.stac import STACQuery

logger = get_logger(__name__)


class WMTSException(Exception):
    pass

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
        now = datetime.datetime.now()
        date_list = sorted([(now - timedelta(days=idx + 1)).strftime('%Y-%m-%d') for idx in range(query.limit)])
    else:
        # time is set, first check if it is an interval or only one point in time
        date_strings = str(query.time).split("/")
        date_points = [parser.parse(date_str) for date_str in date_strings]
        if len(date_points) == 2:
            time_diff = date_points[1] - date_points[0]
            days_in_interval = time_diff.days + bool(time_diff.seconds)
            date_list = \
                [(date_points[1] - timedelta(days=idx)).strftime('%Y-%m-%d') for idx in range(days_in_interval)]
            date_list.sort()
            if len(date_list) > query.limit:
                # Only return the newest dates up to the limit
                date_list = date_list[-query.limit:]
        else:
            # Only one point in time is given; return only that date
            date_list = [date_points[0].strftime('%Y-%m-%d')]
    return date_list


def make_list_layer_band(layers, count):
    out_list = []
    band_order = []
    layer_names = []
    for layer in layers:
        layer_names += [layer] * (layers[layer]['out_ar_shape'][0])
        band_order += list(range(1, layers[layer]['out_ar_shape'][0]+1))

    for band_number in range(1, count+1):
        layer_name = layer_names[band_number-1]
        layer_band = band_order[band_number-1]
        out_list += [[band_number, layer_name, layer_band]]
    return out_list


# pylint: disable=line-too-long
# Long URL and XML identifiers
class GibsAPI:

    def __init__(self):
        self.wmts_url = "https://gibs.earthdata.nasa.gov/wmts"
        self.get_capabilities_url = "/epsg3857/best/1.0.0/WMTSCapabilities.xml"
        self.wmts_endpoint = "/epsg3857/best/{layer}/default" + \
                             "/{date}/GoogleMapsCompatible_Level9/{zoom}/{y}/{x}.{img_format}"
        self.wms_url = "https://gibs.earthdata.nasa.gov/wms"
        self.wms_endpoint = "/epsg4326/best/wms.cgi?" + \
                            "SERVICE=WMS&REQUEST=GetMap&"
        self.quicklook_size = 512, 512

    def get_capabilities(self) -> Response:
        url = self.wmts_url + self.get_capabilities_url
        response = requests.request("GET", url)
        return response

    def get_list_available_layers(self):
        capabilities = ET.fromstring(self.get_capabilities().content)
        layers = {}
        for layer in capabilities[3].findall("{http://www.opengis.net/wmts/1.0}Layer"):
            extent_lc = layer.find("{http://www.opengis.net/ows/1.1}WGS84BoundingBox").find("{http://www.opengis.net/ows/1.1}LowerCorner").text
            extent_uc = layer.find("{http://www.opengis.net/ows/1.1}WGS84BoundingBox").find("{http://www.opengis.net/ows/1.1}UpperCorner").text
            coords = [float(i) for i in extent_lc.split(' ')+extent_uc.split(' ')]
            extent_bbox = box(*coords)
            candidate = {"Identifier": layer.find("{http://www.opengis.net/ows/1.1}Identifier").text,
                         "TileMatrixSet": layer.find("{http://www.opengis.net/wmts/1.0}TileMatrixSetLink").find("{http://www.opengis.net/wmts/1.0}TileMatrixSet").text,
                         "WGS84BoundingBox": extent_bbox, "Format": layer.find("{http://www.opengis.net/wmts/1.0}Format").text.split("/")[1]}
            if candidate["TileMatrixSet"] == "GoogleMapsCompatible_Level9":
                layers[candidate["Identifier"]] = candidate
        return layers

    def validate_layers(self, layers, bbox):
        available_layers = self.get_list_available_layers()
        search_geom = box(*bbox)

        is_name = True
        has_intersection = True

        invalid_names = []
        invalid_geom = []

        valid_layers = collections.OrderedDict()

        for each_layer in layers:
            is_name = each_layer in available_layers.keys() and is_name
            if is_name:
                has_intersection = available_layers[each_layer]["WGS84BoundingBox"].intersects(search_geom) and has_intersection
                if not has_intersection:
                    invalid_geom += [available_layers[each_layer]["WGS84BoundingBox"].wkt]
                else:
                    valid_layers[each_layer] = available_layers[each_layer]
            else:
                invalid_names += [each_layer]

        return (is_name and has_intersection), invalid_names, invalid_geom, valid_layers


    def download_quicklook(self, layer: str, bbox, date: str) -> Response:
        """
        Fetches an RGB quicklook image using WMS
        """
        logger.debug("Will now fetch quicklook %s for date %s", bbox, date)

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
            "TIME": date
        }

        quicklook_string = ("LAYERS={LAYER}&" +
                            "FORMAT=image/jpeg&" +
                            "WIDTH={WIDTH}&" +
                            "HEIGHT={HEIGHT}&" +
                            "CRS=CRS:84&" +
                            "BBOX={BBOX}&" +
                            "TIME={TIME}").format(**params)

        logger.debug(quicklook_string)

        response = requests.get(self.wms_url + self.wms_endpoint + quicklook_string)

        if response.status_code != 200:
            raise requests.exceptions.HTTPError("""Quicklook download unsuccessful
                                    with status code """, response.status_code)
        return response

    def write_quicklook(self, layer: str, bbox, date: str, output_uuid: str):
        """
        Write quicklook to the quicklook output location
        """
        response = self.download_quicklook(layer, bbox, date)
        name = "/tmp/quicklooks/%s.jpg" % (output_uuid)
        with open(name, 'wb') as ql_file:
            for chunk in response.iter_content():
                if chunk:
                    ql_file.write(chunk)

    def download_wmts_tile_as_geotiff(self, layer: str, date: str, tile: mercantile.Tile, img_format: str = "jpg") -> IO[Any]:
        # pylint: disable=too-many-locals
        tile_url = self.wmts_url + self.wmts_endpoint.format(layer=layer,
                                                             date=date,
                                                             x=tile.x,
                                                             y=tile.y,
                                                             zoom=tile.z,
                                                             img_format=img_format)

        logger.debug(tile_url)

        wmts_response = requests.get(tile_url)

        if wmts_response.status_code != 200:
            raise requests.RequestException

        img: rio.MemoryFile = BytesIO(wmts_response.content)

        bands = []
        with rio.open(img) as image:
            for i in range(image.count):
                bands.append(image.read(i + 1))
            tile_meta = image.meta

        tile_transform = rio.transform.from_bounds(*mercantile.xy_bounds(tile),
                                                   width=tile_meta.get("width"),
                                                   height=tile_meta.get("height"))

        tile_meta.update(driver="GTiff", crs="EPSG:3857", transform=tile_transform)

        tmp_file = tempfile.NamedTemporaryFile()

        with rio.open(tmp_file.name, 'w', **tile_meta) as output_tile:
            for idx, band in enumerate(bands):
                output_tile.write(band, idx + 1)

        return tmp_file

    # pylint: disable=too-many-locals
    # Merged image requires all args, TODO
    def get_merged_image(self, layers: dict, tiles: list, date: str, output_uuid: str) -> Path:
        """
        Fetches all tiles for one date, merges them and returns a GeoTIFF
        """

        logger.info("Downloading tiles")
        for layer in layers:
            img_files = []
            logger.info("Getting %s", layer)
            for tile in tiles:
                tiff_file = self.download_wmts_tile_as_geotiff(layer, date, tile, layers[layer]['Format'])
                img_files.append(rio.open(tiff_file.name, driver="GTiff"))
                # Now merge the images
            out_ar, out_trans = merge(img_files)
            layers[layer]['out_ar'] = out_ar
            layers[layer]['out_trans'] = out_trans
            layers[layer]['out_ar_shape'] = out_ar.shape

            logger.info("Shape of layer is %r", out_ar.shape)
            logger.info("Layer %s added!", layer)

        out_all = np.concatenate([layers[k]['out_ar'] for k in layers])

        merged_img_meta = img_files[0].meta.copy()
        merged_img_meta.update({
            "transform": out_trans,
            "height": out_all.shape[1],
            "width": out_all.shape[2],
            "count": out_all.shape[0]
        })


        img_filename = "/tmp/output/%s.tif" % str(output_uuid)

        with rio.open(img_filename, "w", **merged_img_meta) as dataset:
            for band in make_list_layer_band(layers, out_all.shape[0]):
                dataset.update_tags(band[0], layer=band[1], band=band[2])
            dataset.write(out_all)

        return Path(img_filename)
