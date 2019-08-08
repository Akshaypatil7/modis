"""
Helper module allowing src modules to be imported into tests
"""
# pylint: disable=wrong-import-position
# pylint: disable=unused-import

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from modis import Modis
from gibs import GibsAPI, extract_query_dates
from blockutils.stac import STACQuery
