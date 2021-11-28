import colors
import tomtom_pb2
import sys
from google.protobuf.json_format import MessageToDict
from enum import IntEnum
from PIL import Image, ImageDraw
from collections import Counter

import vars
from vector_math import weighted_distance_sum
import convert
# import matplotlib.pyplot as plt


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


def weight(dist):
    radius = convert.meters_to_pixels(vars.RADIUS, vars.ZOOM)
    if dist == 0:
        return 2
    window = 1 - min(dist / radius, 1)
    w = 1 / dist
    return window * w


if __name__ == '__main__':
    # actual = list(parse_geometry([9, 1136, 6564]))
    # expected = [[(568, 3282)]]
    # print(expected)
    # print(actual)

    color_by_dict = {
        'wds': 'weighted distance sum',
        'road_type': 'road type',
        'total': 'weighted distance sum * road type weight * segment traffic level',
        'traffic_level': 'segment traffic level'
    }

    if len(sys.argv) <= 2:
        print("Usage:", sys.argv[0], f"TILE_FILE [{'|'.join([key for key in color_by_dict])}]")
        sys.exit(-1)

    if len(sys.argv) >= 3 and sys.argv[2] in color_by_dict:
        color_by = sys.argv[2]
    else:
        color_by = 'total'
    print(f'coloring by {color_by_dict[color_by]}')

    tile = tomtom_pb2.Tile()

    f = open(sys.argv[1], "rb")
    tile.ParseFromString(f.read())
    f.close()

    tile_dict = MessageToDict(tile)
    # https://developer.tomtom.com/traffic-api/traffic-api-documentation/vector-tile-structure#decoding-tags
    traffic_flow_layer = tile_dict["layers"][0]
    geometries = []
    road_types = Counter()
    img = Image.new("RGB", (4096, 4096))
    img1 = ImageDraw.Draw(img)
    assert traffic_flow_layer["name"] == "Traffic flow"

    # lon, lat = vars.CURRENT_STATION
    # station = convert.wsg_to_tile(lon, lat, vars.ZOOM)[2]
    station = 2590, 2578
    print(station)
    s_max = 0
    s_list = []
    wds_list = []
    traffic_levels = []
    traffic_sum = 0
    segment_count = 0
    for feature in traffic_flow_layer["features"]:
        assert feature["type"] == 'LINESTRING'
        properties = get_feature_properties(traffic_flow_layer, feature)

        road_type = properties[0][1]["stringValue"]
        road_types[road_type] += 1

        assert properties[1][0] == 'traffic_level'
        traffic_level = 1 - properties[1][1]["doubleValue"]
        traffic_levels.append(traffic_level)

        geometry = list(parse_geometry(feature["geometry"]))
        for shape in geometry:

            # split line into line segments
            segments = []
            for point_index in range(0, len(shape) - 1):
                segments.append((shape[point_index], shape[point_index + 1]))

            for segment in segments:
                segment_count += 1
                if color_by in ['total', 'wds']:
                    w_d_s = weighted_distance_sum(station, segment[0], segment[1], weight)
                    wds_list.append(w_d_s)
                    if color_by == 'total':
                        s = w_d_s * vars.ROAD_TYPE_WEIGHTS[road_type] * traffic_level * vars.RADIUS
                        traffic_sum += w_d_s * vars.ROAD_TYPE_WEIGHTS[road_type] * traffic_level * vars.RADIUS
                        if s:
                            s_list.append((s, road_type, traffic_level, w_d_s))
                        s_max = max(s * 255, s_max)
                        s = int(min(s, 1))
                        color = colors.from_level(s)
                    else:
                        color = colors.from_level(min(w_d_s * 1 / 0.003, 1))

                elif color_by == 'road_type':
                    # width = vars.ROAD_TYPE_WEIGHTS[road_type]*2
                    # color = vars.ROAD_TYPE_COLORS[road_type]
                    color = colors.from_level(vars.ROAD_TYPE_WEIGHTS[road_type]/10)
                elif color_by == 'traffic_level':
                    color = colors.from_level(traffic_level)
                else:
                    color = colors.WHITE
                width = 12
                img1.line(segment, fill=color, width=width)
        geometries.append(geometry)
        pass

    # for feature in traffic_flow_layer.
    img1.point(station, fill=(255, 255, 255))
    r = 20
    img1.rounded_rectangle(((station[0] - r, station[1] - r), (station[0] + r, station[1] + r)), r,
                           fill=(255, 255, 255))

    r = convert.meters_to_pixels(vars.RADIUS, vars.ZOOM)
    img1.rounded_rectangle(((station[0] - r, station[1] - r), (station[0] + r, station[1] + r)), r,
                           outline=(255, 255, 255), width=5)

    r = r * 2.5
    img = img.crop((station[0] - r, station[1] - r, station[0] + r, station[1] + r))

    img = img.resize((int(r/2), int(r/2)))
    img.show(title=color_by)

    # fig, ax = plt.subplots(tight_layout=True)
    # # # ax.hist([e[0] for e in s_list], bins=10)
    # ax.hist(wds_list, bins=40)
    # plt.show()
    # print(max(wds_list))

    # print(road_types)
    # print(tile)
    print(f"{segment_count=}")
    print(f"{s_max=}")
    print(f"{traffic_sum=}")
