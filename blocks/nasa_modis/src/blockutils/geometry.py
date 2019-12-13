"""
Geometry-related utilities
"""

from typing import List, Generator
import mercantile
import geojson
import shapely


def filter_tiles_intersect_with_geometry(
    tiles: List[mercantile.Tile], geometry: geojson.geometry.Geometry
) -> Generator[mercantile.Tile, None, None]:
    """
    Given a list of WMTS tiles, this function filters out all tiles which don't intersect with the supplied geojson
    geometry
    """
    geometry = shapely.geometry.shape(geometry)
    for tile in tiles:
        tile_bbox = shapely.geometry.box(*mercantile.bounds(tile)._asdict().values())
        if geometry.intersects(tile_bbox) and not geometry.touches(tile_bbox):
            yield tile
