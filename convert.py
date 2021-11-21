"""
https://developer.tomtom.com/maps-api/maps-api-documentation/zoom-levels-and-tile-grid
zoom
integer 	Zoom level of the tile to be rendered.
Value: 0..22

X
integer 	The x coordinate of the tile on a zoom grid.
Value: 0..2 zoom -1

Y
integer 	The y coordinate of the tile on a zoom grid.
Value: 0..2 zoom -1
"""

from pyproj import Transformer

transformer1 = Transformer.from_crs("epsg:4326", "epsg:3857")
transformer2 = Transformer.from_crs("epsg:3857", "epsg:4326")


def to_wsg(x, y):
    return transformer2.transform(y, x)


def to_3587(lon, lat):
    return transformer1.transform(lon, lat)


def mercator_to_tile(x, y, zoom):
    """
    Converts spherical web mercator to tile pixel X/Y, inverts y coordinates.
    https://gis.stackexchange.com/a/153851
    :param x:
    :param y:
    :param zoom:
    :return: point in EPSG:3857
    """
    equator = 40075017
    tile_x = int((x + (equator / 2.0)) // (equator / pow(2, zoom)))
    tile_y = int(((y - (equator / 2.0)) // (equator / -pow(2, zoom))))
    return tile_x, tile_y


def wsg_to_tile(lon, lat, zoom):
    return mercator_to_tile(*to_3587(lon, lat), zoom)
