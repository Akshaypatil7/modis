import rasterio as rio
from rasterio.transform import Affine
from rasterio.crs import CRS
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
          38.941807150840766,
          21.288749561718983,
          39.686130881309516,
          21.808610762909364
    ]
    })

    result = Modis.AOIClippedFetcher().fetch(query, dry_run=False)

    assert len(result.features) == 2

    expected_meta = {
        'driver': 'GTiff',
        'dtype': 'uint8',
        'nodata': None,
        'width': 513,
        'height': 513,
        'count': 3,
        'crs': CRS.from_dict(init='epsg:3857'),
        'transform': Affine(305.74811314070394, 0.0, 4304933.433021126,
                            0.0, -305.7481131407003, 2504688.5428486546)}

    img_filename = "/tmp/output/%s" % result.features[0]["properties"]["up42.data.aoiclipped"]
    with rio.open(img_filename) as dataset:
        band2 = dataset.read(2)
        assert np.sum(band2) == 28360474
        assert dataset.meta == expected_meta

    #assert os.path.isfile("/tmp/quicklooks/%s.jpeg" % result.features[0]['id'])
    #assert os.path.isfile("/tmp/quicklooks/%s.jpeg" % result.features[1]['id'])
