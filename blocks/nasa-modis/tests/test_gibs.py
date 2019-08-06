import os

import mercantile
import rasterio as rio
from rasterio.crs import CRS
from rasterio.transform import Affine

import requests_mock as mock

from context import GibsAPI, STACQuery


def test_extract_query_dates():
    """
    time is always set, be default to 1. We therefore have the following cases to test:
    (1) time is not set
    (2) limit is set to a number smaller or equal than days are in the provided time period
    (3) limit is set to a number larger than days are in the provided time period
    (4) time is set to one point in time (not a period)
    """

    # case (1)
    query = STACQuery.from_dict({
        "zoom_level": 9,
        "limit": 2,
        "bbox": [
            114.11227717995645,
            -21.861101064554884,
            114.20209027826787,
            -21.764821237030162
        ]
    })

    date_list = GibsAPI.extract_query_dates(query)

    # case (1)
    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2016-04-01T16:40:49+00:00/2019-04-25T16:41:49+00:00",
        "limit": 2,
        "bbox": [
            114.11227717995645,
            -21.861101064554884,
            114.20209027826787,
            -21.764821237030162
        ]
    })

    date_list = GibsAPI.extract_query_dates(query)

    # case (1)
    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2016-04-01T16:40:49+00:00/2019-04-02T16:41:49+00:00",
        "limit": 4,
        "bbox": [
            114.11227717995645,
            -21.861101064554884,
            114.20209027826787,
            -21.764821237030162
        ]
    })

    date_list = GibsAPI.extract_query_dates(query)

    # case (1)
    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2019-04-25T16:41:49+00:00",
        "limit": 2,
        "bbox": [
            114.11227717995645,
            -21.861101064554884,
            114.20209027826787,
            -21.764821237030162
        ]
    })

    date_list = GibsAPI.extract_query_dates(query)


def test_download_wmts_tile_as_geotiff(requests_mock):
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    test_tile = mercantile.Tile(x=290, y=300, z=9)
    test_date = '2019-06-20'

    with open(os.path.join(_location_, 'mock_data/tile.jpeg'), "rb") as fp:
        fake_tile: object = fp.read()

    requests_mock.get(mock.ANY, content=fake_tile)

    result = GibsAPI().download_wmts_tile_as_geotiff(test_date, test_tile)

    expected_meta = {
        'driver': 'GTiff',
        'dtype': 'uint8',
        'nodata': None,
        'width': 256,
        'height': 256,
        'count': 3,
        'crs': CRS.from_dict(init='epsg:3857'),
        'transform': Affine(305.74811314070394, 0.0, 2661231.5767766964,
                            0.0, -305.7481131407094, -3443946.746416901)}

    with rio.open(result) as dataset:
        dataset.meta == expected_meta


def test_get_merged_image():
    test_tiles = [mercantile.Tile(x=290, y=300, z=9), mercantile.Tile(x=290, y=301, z=9)]

    test_date = '2019-06-20'

    result_filename = GibsAPI().get_merged_image(test_tiles, test_date, "a8ebbe34-4d63-4eef-8ff4-c69da3ee359d")

    expected_meta = {
        'driver': 'GTiff',
        'dtype': 'uint8',
        'nodata': None,
        'width': 256,
        'height': 512,
        'count': 3,
        'crs': CRS.from_dict(init='epsg:3857'),
        'transform': Affine(305.74811314070394, 0.0, 2661231.5767766964,
                            0.0, -305.7481131407094, -3443946.746416901)}

    with rio.open(str(result_filename)) as dataset:
        assert dataset.meta == expected_meta


def test_write_quicklook():
    assert 1 == 0

