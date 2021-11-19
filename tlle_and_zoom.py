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


def to_WSG(x, y):
    return transformer2.transform(y, x)


def to_3587(lon, lat):
    return transformer1.transform(lon, lat)


# wsg = to_WSG(110626.2880, 909126.0155)
# m = to_3587(*wsg)
#
# print(wsg)
# print(m)
# print(to_3587(49.2064636, 16.6085294))
