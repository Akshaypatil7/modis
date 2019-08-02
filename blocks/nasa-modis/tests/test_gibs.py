import os

import mercantile
import rasterio as rio
from rasterio.crs import CRS
from rasterio.transform import Affine

import numpy as np
import pytest
import requests_mock as mock

from context import GibsAPI


def test_get_wmts_tile(requests_mock):
    _location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    test_tile = mercantile.Tile(x=290, y=300, z=9)
    test_date = '2019-06-20'

    with open(os.path.join(_location_, 'mock_data/tile.jpeg'), "rb") as fp:
        fake_tile: object = fp.read()

    requests_mock.get(mock.ANY, content=fake_tile)

    result = GibsAPI().get_wmts_tile(test_date, test_tile)

    assert isinstance(result, bytes)
    assert result[:5] == b'\xff\xd8\xff\xe0\x00'


def test_get_merged_image():
    test_tiles = [mercantile.Tile(x=290, y=300, z=9), mercantile.Tile(x=290, y=301, z=9)]

    test_date = '2019-04-21'

    result_filename = GibsAPI().get_merged_image(test_tiles, test_date, "a8ebbe34-4d63-4eef-8ff4-c69da3ee359d")

    import pdb; pdb.set_trace()

    expected_meta = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': None,
        'width': 256,
        'height': 512,
        'count': 12,
        'crs': CRS.from_dict(init='epsg:3857'),
        'transform': Affine(38.21851414258708, 0.0, 3717897.055790972,
                            0.0, -38.21851414259436, 4618019.500877209)}

    with rio.open(str(result_filename)) as dataset:
        assert dataset.meta == expected_meta


def test_write_quicklook():
    assert 1 == 0

