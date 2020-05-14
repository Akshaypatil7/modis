"""
Unit tests for all methods in the Gibs module i.e. internal logic and API interaction
"""

import os
import collections

import pytest
import mercantile
import rasterio as rio
from rasterio.crs import CRS
from rasterio.transform import Affine
from PIL import Image

import requests_mock as mock
from blockutils.common import meta_is_equal
from context import (
    GibsAPI,
    extract_query_dates,
    ensure_data_directories_exist,
    STACQuery,
    make_list_layer_band,
)


@pytest.fixture(scope="session", autouse=True)
def fixture():
    ensure_data_directories_exist()


@pytest.mark.live
def test_get_capabilities_live():
    assert GibsAPI().get_capabilities().status_code == 200


@pytest.mark.live
def test_get_dict_available_imagery_layers_live():
    imagery_layers = GibsAPI().get_dict_available_imagery_layers()
    print(imagery_layers)
    print(len(imagery_layers))
    assert len(imagery_layers) >= 5


def test_get_dict_available_imagery_layers(requests_mock):
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        fake_xml: object = xml_file.read()

    requests_mock.get(mock.ANY, content=fake_xml)

    imagery_layers = GibsAPI().get_dict_available_imagery_layers()

    assert (
        imagery_layers["MODIS_Aqua_CorrectedReflectance_TrueColor"]["Identifier"]
        == "MODIS_Aqua_CorrectedReflectance_TrueColor"
    )
    assert len(imagery_layers) == 45


def test_validate_imagery_layers(requests_mock):
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        fake_xml: object = xml_file.read()

    requests_mock.get(mock.ANY, content=fake_xml)

    valid, invalid, _ = GibsAPI().validate_imagery_layers(
        ["MODIS_Aqua_CorrectedReflectance_TrueColor"], [50, 50, 60, 60]
    )
    assert valid
    assert invalid == ([], [])

    valid, invalid, _ = GibsAPI().validate_imagery_layers(["ABC"], [50, 50, 60, 60])
    assert not valid
    assert invalid[0] == ["ABC"]

    multiple_valid, invalid, _ = GibsAPI().validate_imagery_layers(
        [
            "MODIS_Aqua_CorrectedReflectance_TrueColor",
            "MODIS_Terra_CorrectedReflectance_TrueColor",
        ],
        [50, 50, 60, 60],
    )
    assert multiple_valid
    assert invalid == ([], [])

    multiple_valid, invalid, _ = GibsAPI().validate_imagery_layers(
        [
            "MODIS_Aqua_CorrectedReflectance_TrueColor",
            "MODIS_Terra_CorrectedReflectance_TrueColor",
            "ABC",
        ],
        [50, 50, 60, 60],
    )
    assert not multiple_valid
    assert invalid[0] == ["ABC"]

    multiple_geom, invalid, _ = GibsAPI().validate_imagery_layers(
        ["MODIS_Aqua_CorrectedReflectance_TrueColor"], [200, 200, 210, 210]
    )
    assert not multiple_geom
    assert invalid[0] == []
    assert invalid[1] == [
        "POLYGON ((180 -85.051129, 180 85.051129, -180 85.051129, -180 -85.051129, 180 -85.051129))"
    ]


def test_extract_query_dates():
    """
    time parameter  is always set, be default to 1. We therefore have the following cases to test:
    (1) time is not set
    (2) limit is set to a number smaller or equal than days are in the provided time period
    (3) limit is set to a number larger than days are in the provided time period
    (4) time is set to one point in time (not a period)
    """

    # case (1)
    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "limit": 2,
            "bbox": [
                114.11227717995645,
                -21.861101064554884,
                114.20209027826787,
                -21.764821237030162,
            ],
        }
    )

    date_list = extract_query_dates(query)
    assert len(date_list) == 2
    assert date_list[0] < date_list[1]
    for date in date_list:
        assert date.startswith("20")

    # case (2)
    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-04-20T16:40:49+00:00/2019-04-25T17:45:49+00:00",
            "limit": 2,
            "bbox": [
                114.11227717995645,
                -21.861101064554884,
                114.20209027826787,
                -21.764821237030162,
            ],
        }
    )

    date_list = extract_query_dates(query)
    assert date_list == ["2019-04-24", "2019-04-25"]

    # case (3)
    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-04-01T16:40:49+00:00/2019-04-02T16:41:49+00:00",
            "limit": 4,
            "bbox": [
                114.11227717995645,
                -21.861101064554884,
                114.20209027826787,
                -21.764821237030162,
            ],
        }
    )

    date_list = extract_query_dates(query)
    assert date_list == ["2019-04-01", "2019-04-02"]

    # case (4)
    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-04-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [
                114.11227717995645,
                -21.861101064554884,
                114.20209027826787,
                -21.764821237030162,
            ],
        }
    )

    date_list = extract_query_dates(query)
    assert date_list == ["2019-04-25"]


def test_make_list_layer_band():
    test_imagery_layers = collections.OrderedDict(
        {
            "MODIS_Terra_CorrectedReflectance_TrueColor": {
                "Identifier": "MODIS_Terra_CorrectedReflectance_TrueColor",
                "Format": "jpeg",
                "out_ar_shape": (3, 5, 5),
            },
            "MODIS_Aqua_CorrectedReflectance_TrueColor": {
                "Identifier": "MODIS_Aqua_CorrectedReflectance_TrueColor",
                "Format": "jpeg",
                "out_ar_shape": (3, 5, 5),
            },
        }
    )

    test_count = 6
    list_imagery_layers = make_list_layer_band(test_imagery_layers, test_count)
    assert len(list_imagery_layers) == 6
    assert list_imagery_layers[0] == [
        1,
        "MODIS_Terra_CorrectedReflectance_TrueColor",
        1,
    ]
    assert list_imagery_layers[1] == [
        2,
        "MODIS_Terra_CorrectedReflectance_TrueColor",
        2,
    ]
    assert list_imagery_layers[3] == [4, "MODIS_Aqua_CorrectedReflectance_TrueColor", 1]


def test_download_wmts_tile_as_geotiff(requests_mock):
    """
    Mocked test for tile download
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    test_tile = mercantile.Tile(x=290, y=300, z=9)
    test_date = "2019-06-20"
    test_layer = "MODIS_Terra_CorrectedReflectance_TrueColor"

    with open(os.path.join(_location_, "mock_data/tile.jpg"), "rb") as tile_file:
        fake_tile: object = tile_file.read()

    requests_mock.get(mock.ANY, content=fake_tile)

    result = GibsAPI().download_wmts_tile_as_geotiff(test_layer, test_date, test_tile)

    expected_meta = {
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": None,
        "width": 256,
        "height": 256,
        "count": 3,
        "crs": CRS.from_dict(init="epsg:3857"),
    }

    with rio.open(result) as dataset:
        meta = dataset.meta
        meta.pop("transform")
        assert meta == expected_meta


@pytest.mark.live
def test_get_merged_image():
    """
    Unmocked ("live") test making sure output images have correct metadata set
    """
    test_tiles = [
        mercantile.Tile(x=290, y=300, z=9),
        mercantile.Tile(x=290, y=301, z=9),
    ]

    test_date = "2019-06-20"
    test_layer = {
        "MODIS_Terra_CorrectedReflectance_TrueColor": {
            "Identifier": "MODIS_Terra_CorrectedReflectance_TrueColor",
            "TileMatrixSet": "GoogleMapsCompatible_Level9",
            "WGS84BoundingBox": "shapely.geometry.polygon.Polygon object at 0x130e71590",
            "Format": "jpeg",
        }
    }

    result_filename = GibsAPI().get_merged_image(
        test_layer, test_tiles, test_date, "a8ebbe34-4d63-4eef-8ff4-c69da3ee359d"
    )

    expected_meta = {
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": None,
        "width": 256,
        "height": 512,
        "count": 3,
        "crs": CRS.from_dict(init="epsg:3857"),
        "transform": Affine(
            305.74811314070394,
            0.0,
            2661231.5767766964,
            0.0,
            -305.7481131407094,
            -3443946.746416901,
        ),
    }

    with rio.open(str(result_filename)) as dataset:
        assert meta_is_equal(dataset.meta, expected_meta)


@pytest.mark.live
def test_get_multiple_merged_image():
    """
    Unmocked ("live") test with multiple imagery_layers making sure output images have
    correct metadata set
    """
    test_tiles = [
        mercantile.Tile(x=290, y=300, z=9),
        mercantile.Tile(x=290, y=301, z=9),
    ]

    test_date = "2019-06-20"
    test_imagery_layers = {
        "MODIS_Terra_CorrectedReflectance_TrueColor": {
            "Identifier": "MODIS_Terra_CorrectedReflectance_TrueColor",
            "Format": "jpeg",
        },
        "MODIS_Aqua_CorrectedReflectance_TrueColor": {
            "Identifier": "MODIS_Aqua_CorrectedReflectance_TrueColor",
            "Format": "jpeg",
        },
    }

    result_filename = GibsAPI().get_merged_image(
        test_imagery_layers,
        test_tiles,
        test_date,
        "a8ebbe34-4d63-4eef-8ff4-c69da3ee359d",
    )

    expected_meta = {
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": None,
        "width": 256,
        "height": 512,
        "count": 6,
        "crs": CRS.from_dict(init="epsg:3857"),
        "transform": Affine(
            305.74811314070394,
            0.0,
            2661231.5767766964,
            0.0,
            -305.7481131407094,
            -3443946.746416901,
        ),
    }

    with rio.open(str(result_filename)) as dataset:
        assert meta_is_equal(dataset.meta, expected_meta, atol=1e-02)


@pytest.mark.live
def test_write_quicklook():

    test_bbox = (38.671875, 20.632784250388017, 40.078125, 21.943045533438177)
    test_query_date = "2019-01-24"
    test_uuid = "17afe6e1-f10d-43a8-ac16-2a5e3404bc36"
    test_layer = "MODIS_Terra_CorrectedReflectance_TrueColor"

    GibsAPI().write_quicklook(test_layer, test_bbox, test_query_date, test_uuid)

    quicklook_path = "/tmp/quicklooks/%s.jpg" % test_uuid

    assert os.path.isfile(quicklook_path)

    image = Image.open(str(quicklook_path))
    assert image.size == (512, 477)
    assert image.mode == "RGB"
