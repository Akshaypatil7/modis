import rasterio as rio
import numpy as np
import pytest
import requests_mock as mock

from context import STACQuery, Modis

def test_aoiclipped_fetcher_fetch_in_dry_run_mode(requests_mock):
    assert 1 == 0

def test_aoiclipped_fetcher_fetch(requests_mock):
    assert 1 == 0

def test_aoiclipped_fetcher_fetch_live():

    query = STACQuery.from_dict({
        "zoom_level": 9,
        "time": "2019-01-01T16:40:49+00:00/2019-01-25T16:41:49+00:00",
        "limit": 2,
        "bbox": [
          10.857563107274474,
          36.55558775726571,
          10.863281576894225,
          36.559284899311415
        ]
    })

    result = Modis.AOIClippedFetcher().fetch(query, dry_run=False)

    assert len(result.features) == 2

    #assert os.path.isfile("/tmp/quicklooks/%s.jpeg" % result.features[0]['id'])
    #assert os.path.isfile("/tmp/quicklooks/%s.jpeg" % result.features[1]['id'])
