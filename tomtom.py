import tomtom_pb2
import sys


def ProcessTile(tile: tomtom_pb2.Tile):
    for x in tile.layers:
        print(x)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "TILE_FILE")
        sys.exit(-1)

    tile = tomtom_pb2.Tile()

    f = open(sys.argv[1], "rb")
    tile.ParseFromString(f.read())
    f.close()
    print(tile)
