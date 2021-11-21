import tomtom_pb2
import sys
from google.protobuf.json_format import MessageToDict
from enum import IntEnum
from PIL import Image, ImageDraw

from vector_math import weighted_distance_sum


def get_feature_properties(layer, feature):
    """
    https://developer.tomtom.com/traffic-api/traffic-api-documentation/vector-tile-structure#decoding-tags
    """
    keys = layer["keys"]
    values = layer["values"]
    tags = feature["tags"]
    n = 2
    tag_chunks = [tags[i:i + n] for i in range(0, len(tags), n)]
    return [(keys[chunk[0]], values[chunk[1]]) for chunk in tag_chunks]


def parse_command_and_count(command_and_count):
    command = command_and_count & 0x7
    count = command_and_count >> 0x3
    return Command(command), count


class Command(IntEnum):
    MoveTo = 1
    LineTo = 2
    ClosePath = 7


class CommandState(IntEnum):
    MoveTo = 1
    LineTo = 2
    ClosePath = 7
    Start = 0
    End = -2
    Error = -1


COMMAND_STATES = [Command.MoveTo, Command.LineTo, Command.ClosePath]
COMMAND_COUNTS_ASSERTS = {
    Command.MoveTo: lambda _count: _count == 1,
    Command.LineTo: lambda _count: _count > 0,
    Command.ClosePath: lambda _count: _count == 0,
}


COMMAND_STATE_FUNCTION = {
    CommandState.Start: {
        Command.MoveTo: CommandState.MoveTo,
        Command.LineTo: CommandState.Error,
        Command.ClosePath: CommandState.Error,
    },
    CommandState.MoveTo: {
        Command.MoveTo: CommandState.Error,
        Command.LineTo: CommandState.LineTo,
        Command.ClosePath: CommandState.End,
    },
    CommandState.LineTo: {
        Command.MoveTo: CommandState.MoveTo,
        Command.LineTo: CommandState.Error,
        Command.ClosePath: CommandState.ClosePath,
    }
}


def parse_geometry(geometry):
    """
    generator of https://developer.tomtom.com/traffic-api/traffic-api-documentation/vector-tile-structure#decoding-geometry
    :param geometry: Feature.geometry
    :return:
    """
    x_prev = 0
    y_prev = 0
    segment = []
    command_state = CommandState.Start
    i = 0
    while i < len(geometry) and command_state != CommandState.End:
        command, count = parse_command_and_count(geometry[i])
        i = i + 1
        assert COMMAND_COUNTS_ASSERTS[command](count)
        if command == Command.MoveTo and command_state == CommandState.LineTo:
            # x_prev = 0
            # y_prev = 0
            yield segment
            segment = []
        command_state = COMMAND_STATE_FUNCTION[command_state][command]
        assert command_state != CommandState.Error
        if command_state == CommandState.End:
            break
        for _ in range(0, count):
            x_n = geometry[i]
            y_n = geometry[i + 1]
            i = i + 2
            x = x_prev + ((x_n >> 0x1) ^ (-(x_n & 0x1)))
            y = y_prev + ((y_n >> 0x1) ^ (-(y_n & 0x1)))
            x_prev = x
            y_prev = y
            segment.append((x, y))
    if segment:
        yield segment


if __name__ == '__main__':
    # actual = list(parse_geometry([9, 1136, 6564]))
    # expected = [[(568, 3282)]]
    # print(expected)
    # print(actual)

    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "TILE_FILE")
        sys.exit(-1)

    tile = tomtom_pb2.Tile()

    f = open(sys.argv[1], "rb")
    tile.ParseFromString(f.read())
    f.close()

    tile_dict = MessageToDict(tile)
    # https://developer.tomtom.com/traffic-api/traffic-api-documentation/vector-tile-structure#decoding-tags
    traffic_flow_layer = tile_dict["layers"][0]
    geometries = []
    img = Image.new("RGB", (4096, 4096))
    img1 = ImageDraw.Draw(img)
    assert traffic_flow_layer["name"] == "Traffic flow"


    def weight(dist):
        radius = 2048  # TODO calculate from meters
        if dist == 0:
            return 2
        window = 1 - min(dist / radius, 1)
        w = 1 / dist
        return window * w


    s_max = 0
    for feature in traffic_flow_layer["features"]:
        assert feature["type"] == 'LINESTRING'
        properties = get_feature_properties(traffic_flow_layer, feature)
        geometry = list(parse_geometry(feature["geometry"]))
        station = (2048, 2048)
        for shape in geometry:

            # split line into line segments
            segments = []
            for point_index in range(0, len(shape) - 1):
                segments.append((shape[point_index], shape[point_index + 1]))

            for segment in segments:
                w_d_s = weighted_distance_sum(station, segment[0], segment[1], weight)
                s = w_d_s * 1500
                s_max = max(s, s_max)
                s = int(min(s, 1) * 255)
                img1.line(segment, fill=(s, 255 - s, 0), width=15)
        geometries.append(geometry)
        pass

    # for feature in traffic_flow_layer.
    img = img.resize((1024, 1024))
    img.show()
    print(tile)
    print(s_max)
