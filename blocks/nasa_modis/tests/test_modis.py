"""
Integration tests for the higher-level fetch methods
"""

import os

import rasterio as rio
import numpy as np
import requests_mock as mock

from context import STACQuery, Modis

def test_aoiclipped_fetcher_fetch_in_dry_run_mode():
    """
    Test for dry-run mode i.e. only metadata is returned
    """

    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
        "limit": 1,
        "bbox": [
            123.59349578619005,
            -10.188159969024264,
            123.70257586240771,
            -10.113232998848046
        ]
    })

    result = Modis.AOIClippedFetcher().fetch(query, dry_run=True)

    assert len(result.features) == 1
    assert "up42.data.aoiclipped" not in result.features[0]["properties"].keys()


def test_aoiclipped_fetcher_fetch(requests_mock):
    """
    Mocked test for fetching data - quicker than the live one and therefore valuable for testing
    purposes
    """
    _location_ = os.path.realpath(os.path.join(os.getcwd(),
                                               os.path.dirname(__file__)))
    with open(os.path.join(_location_, 'mock_data/tile.jpg'), "rb") as tile_file:
        mock_image: object = tile_file.read()
    requests_mock.get(mock.ANY, content=mock_image)

    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2018-11-01T16:40:49+00:00/2018-11-20T16:41:49+00:00",
        "limit": 1,
        "bbox": [
            123.59349578619005,
            -10.188159969024264,
            123.70257586240771,
            -10.113232998848046
        ]
    })

    result = Modis.AOIClippedFetcher().fetch(query, dry_run=False)

    assert len(result.features) == 1

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data.aoiclipped"]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 7954025


def test_aoiclipped_fetcher_fetch_live():
    """
    Unmocked ("live") test for fetching data
    """

    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
        "limit": 2,
        "bbox": [
            38.941807150840766,
            21.288749561718983,
            39.686130881309516,
            21.808610762909364
        ]
    })

    result = Modis.AOIClippedFetcher().fetch(query, dry_run=False)

    assert len(result.features) == 2

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data.aoiclipped"]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 28360474
