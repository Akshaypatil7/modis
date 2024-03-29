"""
Integration tests for the higher-level fetch methods
"""
# pylint: disable=unused-import, redefined-outer-name
# requests_mock used as fixture in tests
import os
import re

import rasterio as rio
import numpy as np
import pytest
from rio_cogeo.cogeo import cog_validate

from context import STACQuery, Modis

from blockutils.exceptions import UP42Error


@pytest.fixture()
def modis_instance():
    return Modis(default_zoom_level=9)


@pytest.mark.live
def test_aoiclipped_fetcher_fetch_in_dry_run_mode(modis_instance):
    """
    Test for dry-run mode i.e. only metadata is returned
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [
                123.59349578619005,
                -10.188159969024264,
                123.70257586240771,
                -10.113232998848046,
            ],
            "imagery_layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"],
        }
    )

    result = modis_instance.fetch(query, dry_run=True)

    assert len(result.features) == 1
    assert "up42.data_path" not in result.features[0]["properties"].keys()
    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])


@pytest.mark.live
def test_aoiclipped_fetcher_multiple_fetch_in_dry_run_mode(modis_instance):
    """
    Test for dry-run mode i.e. only metadata is returned, multiple imagery_layers
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [
                123.59349578619005,
                -10.188159969024264,
                123.70257586240771,
                -10.113232998848046,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "MODIS_Aqua_CorrectedReflectance_TrueColor",
            ],
        }
    )

    result = modis_instance.fetch(query, dry_run=True)

    assert len(result.features) == 1
    assert "up42.data_path" not in result.features[0]["properties"].keys()
    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])


@pytest.mark.live
def test_aoiclipped_fetcher_layer_error_fetch_in_dry_run_mode(modis_instance):
    """
    Test for dry-run mode i.e. only metadata is returned, error in name of layer
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [
                123.59349578619005,
                -10.188159969024264,
                123.70257586240771,
                -10.113232998848046,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "AN_ERROR_FOR_SURE",
            ],
        }
    )

    with pytest.raises(UP42Error, match=r".*['AN_ERROR_FOR_SURE'].*"):
        modis_instance.fetch(query, dry_run=True)


@pytest.mark.live
def test_aoiclipped_fetcher_geom_error_fetch_in_dry_run_mode(modis_instance):
    """
    Test for dry-run mode i.e. only metadata is returned, error in geometry
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [200, 200, 210, 210],
            "imagery_layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"],
        }
    )

    with pytest.raises(UP42Error):
        modis_instance.fetch(query, dry_run=True)


def test_aoiclipped_dry_run_only_bbox(requests_mock, modis_instance):
    """
    Mocked test for fetching data with only bbox param
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        mock_xml: object = xml_file.read()
    with open(os.path.join(_location_, "mock_data/tile.jpg"), "rb") as tile_file:
        mock_image: object = tile_file.read()

    matcher_get_capabilities = re.compile("WMTSCapabilities.xml")

    matcher_wms = re.compile(
        "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?"
    )
    matcher_wmts = re.compile(
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/"
        "best/MODIS_Terra_CorrectedReflectance_TrueColor/"
    )
    matcher_get_capabilities = re.compile("WMTSCapabilities.xml")

    requests_mock.get(matcher_get_capabilities, content=mock_xml)
    requests_mock.get(matcher_wms, content=mock_image)
    requests_mock.get(matcher_wmts, content=mock_image)

    query = STACQuery.from_dict({"bbox": [76.231358, 9.909276, 76.300637, 9.971047]})

    res = modis_instance.fetch(query, dry_run=True)
    assert len(res.features) == 1


def test_aoiclipped_fetcher_fetch(requests_mock, modis_instance):
    """
    Mocked test for fetching data - quicker than the live one and therefore valuable for testing
    purposes
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(_location_, "mock_data/tile.jpg"), "rb") as tile_file:
        mock_image: object = tile_file.read()

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        mock_xml: object = xml_file.read()

    matcher_wms = re.compile(
        "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?"
    )
    matcher_wmts = re.compile(
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/"
        "best/MODIS_Terra_CorrectedReflectance_TrueColor/"
    )
    matcher_get_capabilities = re.compile("WMTSCapabilities.xml")

    requests_mock.get(matcher_get_capabilities, content=mock_xml)
    requests_mock.get(matcher_wms, content=mock_image)
    requests_mock.get(matcher_wmts, content=mock_image)

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [
                123.59349578619005,
                -10.188159969024264,
                123.70257586240771,
                -10.113232998848046,
            ],
            "imagery_layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"],
        }
    )

    result = modis_instance.fetch(query, dry_run=False)

    assert len(result.features) == 1

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data_path"]
    assert cog_validate(img_filename)[0]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 7954025
        assert dataset.tags(1)["layer"] == "MODIS_Terra_CorrectedReflectance_TrueColor"
        assert dataset.tags(1)["band"] == str(1)
        assert dataset.tags(2)["band"] == str(2)
    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])


def test_aoiclipped_dry_run_error_name_fetcher_fetch(requests_mock, modis_instance):
    """
    Mocked test for fetching data with error in name
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        mock_xml: object = xml_file.read()

    matcher_get_capabilities = re.compile("WMTSCapabilities.xml")

    requests_mock.get(matcher_get_capabilities, content=mock_xml)

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [
                123.59349578619005,
                -10.188159969024264,
                123.70257586240771,
                -10.113232998848046,
            ],
            "imagery_layers": ["AN_ERROR_FOR_SURE"],
        }
    )

    with pytest.raises(UP42Error, match=r".*['AN_ERROR_FOR_SURE'].*"):
        modis_instance.fetch(query, dry_run=True)


def test_aoiclipped_dry_run_multiple_error_name_fetcher_fetch(
    requests_mock, modis_instance
):
    """
    Mocked test for fetching data with error in name
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        mock_xml: object = xml_file.read()

    matcher_get_capabilities = re.compile("WMTSCapabilities.xml")

    requests_mock.get(matcher_get_capabilities, content=mock_xml)

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [
                123.59349578619005,
                -10.188159969024264,
                123.70257586240771,
                -10.113232998848046,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "MODIS_Aqua_CorrectedReflectance_TrueColor",
                "12345",
                "AN_ERROR_FOR_SURE",
            ],
        }
    )

    with pytest.raises(UP42Error, match=r".*['12345','AN_ERROR_FOR_SURE'].*"):
        modis_instance.fetch(query, dry_run=True)


def test_aoiclipped_dry_run_error_geom_fetcher_fetch(requests_mock, modis_instance):
    """
    Mocked test for fetching data with error in geom
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(
        os.path.join(_location_, "mock_data/available_imagery_layers.xml"), "rb"
    ) as xml_file:
        mock_xml: object = xml_file.read()

    matcher_get_capabilities = re.compile("WMTSCapabilities.xml")

    requests_mock.get(matcher_get_capabilities, content=mock_xml)

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
            "limit": 1,
            "bbox": [179, 89, 180, 90],
            "imagery_layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"],
        }
    )

    with pytest.raises(UP42Error):
        modis_instance.fetch(query, dry_run=True)


@pytest.mark.live
def test_aoiclipped_fetcher_fetch_live(modis_instance):
    """
    Unmocked ("live") test for fetching data
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [
                38.941807150840766,
                21.288749561718983,
                39.686130881309516,
                21.808610762909364,
            ],
            "imagery_layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"],
        }
    )

    result = modis_instance.fetch(query, dry_run=False)

    assert len(result.features) == 2

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data_path"]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 28351388
    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])


@pytest.mark.live
def test_aoiclipped_fetcher_virs_fetch_live(modis_instance):
    """
    Unmocked ("live") test for fetching VIIRS data in png
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [
                38.941807150840766,
                21.288749561718983,
                39.686130881309516,
                21.808610762909364,
            ],
            "imagery_layers": ["VIIRS_SNPP_Brightness_Temp_BandI5_Night"],
        }
    )

    result = modis_instance.fetch(query, dry_run=False)

    assert len(result.features) == 2

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data_path"]
    with rio.open(img_filename) as dataset:
        band1 = dataset.read(1)
        assert np.sum(band1) == 45232508
        assert dataset.count == 1
    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])
    assert cog_validate(img_filename)[0]


@pytest.mark.live
def test_aoiclipped_fetcher_rio_tags_fetch_live(modis_instance):
    """
    Unmocked ("live") test for fetching MODIS and VIRS data with tags
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [
                38.941807150840766,
                21.288749561718983,
                39.686130881309516,
                21.808610762909364,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "VIIRS_SNPP_Brightness_Temp_BandI5_Night",
            ],
        }
    )

    result = modis_instance.fetch(query, dry_run=False)

    assert len(result.features) == 2

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data_path"]
    with rio.open(img_filename) as dataset:
        assert dataset.count == 4
        band1 = dataset.read(1)
        assert np.sum(band1) == 29570538

        assert dataset.tags(1)["layer"] == "MODIS_Terra_CorrectedReflectance_TrueColor"
        assert dataset.tags(1)["band"] == str(1)

        assert dataset.tags(4)["layer"] == "VIIRS_SNPP_Brightness_Temp_BandI5_Night"
        assert dataset.tags(4)["band"] == str(1)

    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])


@pytest.mark.live
def test_aoiclipped_fetcher_multiple_fetch_live(modis_instance):
    """
    Unmocked ("live") test for fetching data, multiple imagery_layers
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [
                38.941807150840766,
                21.288749561718983,
                39.686130881309516,
                21.808610762909364,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "MODIS_Aqua_CorrectedReflectance_TrueColor",
            ],
        }
    )

    result = modis_instance.fetch(query, dry_run=False)

    assert len(result.features) == 2

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data_path"]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 28351388
        assert dataset.count == 6
    assert os.path.isfile("/tmp/quicklooks/%s.jpg" % result.features[0]["id"])
    assert cog_validate(img_filename)[0]


@pytest.mark.live
def test_aoiclipped_fetcher_layer_error_fetch_live(modis_instance):
    """
    Unmocked ("live") test for fetching data, error in name of layer
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [
                38.941807150840766,
                21.288749561718983,
                39.686130881309516,
                21.808610762909364,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "AN_ERROR_FOR_SURE",
            ],
        }
    )

    with pytest.raises(UP42Error, match=r".*['AN_ERROR_FOR_SURE'].*"):
        modis_instance.fetch(query, dry_run=False)


@pytest.mark.live
def test_aoiclipped_fetcher_geom_error_fetch_live(modis_instance):
    """
    Unmocked ("live") test for fetching data, error in geometry of layer
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
            "limit": 2,
            "bbox": [200, 200, 210, 210],
            "imagery_layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"],
        }
    )

    with pytest.raises(UP42Error):
        modis_instance.fetch(query, dry_run=False)


@pytest.mark.live
def test_aoiclipped_fetcher_layers_cog(modis_instance):
    """
    Unmocked ("live") test for fetching data. Tests cog conversion with image, with 7 bands.
    """

    query = STACQuery.from_dict(
        {
            "zoom_level": 9,
            "time": "2019-01-01T16:40:49+00:00/2021-02-15T23:59:59+00:00",
            "limit": 1,
            "bbox": [
                38.941807150840766,
                21.288749561718983,
                39.686130881309516,
                21.808610762909364,
            ],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "MODIS_Terra_EVI_8Day",
                "MODIS_Terra_CorrectedReflectance_Bands721",
            ],
        }
    )

    result = modis_instance.fetch(query, dry_run=False)
    assert len(result.features) == 1
    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data_path"]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 28202042
        assert dataset.count == 7
    assert cog_validate(img_filename)[0]
