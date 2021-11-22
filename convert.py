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
import math

from pyproj import Transformer

transformer1 = Transformer.from_crs("epsg:4326", "epsg:3857")
transformer2 = Transformer.from_crs("epsg:3857", "epsg:4326")
EQUATOR = 40075017
TILE_PIXELS = 4096


def to_wsg(x, y):
    return transformer2.transform(y, x)


def to_3587(lon, lat):
    return transformer1.transform(lon, lat)


def tile_size(zoom: int):
    """
    :param zoom: int in range 0,22
    :return:
    """
    return EQUATOR / pow(2, zoom)


def mercator_to_tile(x, y, zoom):
    """
    Converts spherical web mercator to tile pixel X/Y, inverts y coordinates.
    https://gis.stackexchange.com/a/153851
    :param x:
    :param y:
    :param zoom:
    :return: point in EPSG:3857
    """
    num_x = x + (EQUATOR / 2.0)
    denom_x = EQUATOR / pow(2, zoom)
    num_y = y - (EQUATOR / 2.0)
    denom_y = EQUATOR / -pow(2, zoom)
    tile_x = math.modf(num_x / denom_x)
    tile_y = math.modf(num_y / denom_y)
    return (num_x / denom_x, num_y / denom_y), (int(tile_x[1]), int(tile_y[1])), (int(TILE_PIXELS*tile_x[0]), int(TILE_PIXELS*tile_y[0]))


def ___mercator_to_tile(x, y, zoom):
    """
    Converts spherical web mercator to tile pixel X/Y, inverts y coordinates.
    https://gis.stackexchange.com/a/153851
    :param x:
    :param y:
    :param zoom:
    :return: point in EPSG:3857
    """
    num_x = x + (EQUATOR / 2.0)
    denom_x = EQUATOR / pow(2, zoom)
    num_y = y - (EQUATOR / 2.0)
    denom_y = EQUATOR / -pow(2, zoom)
    tile_x = divmod(num_x, denom_x)
    tile_y = divmod(num_y, denom_y)
    return (int(tile_x[0]), int(tile_y[0])), (int(tile_x[1]), int(abs(tile_y[1])))


def wsg_to_tile(lon, lat, zoom: int):
    return mercator_to_tile(*to_3587(lon, lat), zoom)


def point_radius_bbox(lon, lat, zoom: int, tile_radius: float):
    tile_coords = wsg_to_tile(lon, lat, zoom)

    tile_pos_x = tile_coords[0][0]
    bbox_min_x = int(tile_pos_x - tile_radius)
    bbox_max_x = int(tile_pos_x + tile_radius)

    tile_pos_y = tile_coords[0][1]
    bbox_min_y = int(tile_pos_y - tile_radius)
    bbox_max_y = int(tile_pos_y + tile_radius)
    return (bbox_min_x, bbox_min_y), (bbox_max_x, bbox_max_y)


def meters_to_pixels(meters, zoom) -> int:
    return int((meters/tile_size(zoom))*TILE_PIXELS)


def meters_to_tile(meters, zoom) -> float:
    return meters/tile_size(zoom)


if __name__ == '__main__':
    print(wsg_to_tile(49.2077883, 16.6135453, 13))
    print(wsg_to_tile(49.1863633, 16.6516567, 12))
    print(point_radius_bbox(49.1863633, 16.6516567, 13, 500/TILE_PIXELS))
    print(tile_size(13))
    print(meters_to_pixels(4891.97, 13))
    print(meters_to_tile(4891.97, 14))
    # print(to_3587(49.2077883, 16.6135453))
