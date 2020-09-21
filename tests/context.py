"""
Helper module allowing src modules to be imported into tests
"""
# pylint: disable=wrong-import-position
# pylint: disable=unused-import

import os
import sys

from blockutils.common import ensure_data_directories_exist
from blockutils.stac import STACQuery

# NOTE: this must be before the modis and gibs imports - else tests will not find path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.gibs import (
    GibsAPI,
    extract_query_dates,
    make_list_layer_band,
    move_dates_to_past,
)
from src.modis import Modis
