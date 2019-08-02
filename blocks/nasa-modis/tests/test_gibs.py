import os

import mercantile
import rasterio as rio
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

def test_merge_tiles():
    assert 1 == 0

def test_write_quicklook():
    assert 1 == 0

