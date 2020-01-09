"""
Helper module allowing src modules to be imported into tests
"""
# pylint: disable=wrong-import-position
# pylint: disable=unused-import

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.modis import Modis
from src.gibs import GibsAPI, extract_query_dates, make_list_layer_band
from src.blockutils.stac import STACQuery
from src.blockutils.common import ensure_data_directories_exist
