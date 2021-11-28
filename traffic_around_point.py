import datetime

from google.protobuf.json_format import MessageToDict
import convert
import tomtom_pb2
import vars
from tomtom import get_feature_properties, weight, parse_geometry, weighted_distance_sum
import csv


def memoize(func):
    cache = dict()

    def memoized_func(*args):
        if args in cache:
            # print('hit')
            return cache[args]
        result = func(*args)
        # print('miss')
        cache[args] = result
        return result

    return memoized_func


def get_tile_dict(filepath):
    tile = tomtom_pb2.Tile()
    with open(filepath, "rb") as file:
        tile.ParseFromString(file.read())
    return MessageToDict(tile)


get_tile_dict_mem = memoize(get_tile_dict)

if __name__ == '__main__':
    # '2021/05/05 12:04:37.692+00'
    time_str_len = len('2021/05/05 12:04:37')
    radius_tile = convert.meters_to_tile(vars.RADIUS, vars.ZOOM)
    tile_step = convert.meters_to_tile(500, vars.ZOOM)  # determines grid density

    with open('temp/traffic_sum_grid_500_500r.csv', 'w', newline='') as csv_file:
        fieldnames = ['lon', 'lat', 'time', 'value']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        tile_dicts = {}

        bbox = vars.BRNO_BBOX
        for tile_x in range(bbox[0][0], bbox[1][0] + 1):
            # print(f"{tile_x=}")
            for tile_y in range(bbox[0][1], bbox[1][1] + 1):
                filename = f"test_{tile_x}_{tile_y}.pbf"

                # padding
                if tile_x == bbox[0][0]:
                    start_x = radius_tile
                    end_x = 1
                elif tile_x == bbox[1][0]:
                    start_x = 0
                    end_x = 1 - convert.meters_to_tile(vars.RADIUS, vars.ZOOM)
                else:
                    start_x = 0
                    end_x = 1

                if tile_y == bbox[0][1]:
                    start_y = radius_tile
                    end_y = 1
                elif tile_y == bbox[1][1]:
                    start_y = 0
                    end_y = 1 - convert.meters_to_tile(vars.RADIUS, vars.ZOOM)
                else:
                    start_y = 0
                    end_y = 1

                x = start_x
                while x < end_x:
                    y = start_y
                    while y < end_y:
                        print(tile_x + x, tile_y + y)
                        # print(x, y)
                        measured_point = (tile_x + x, tile_y + y), (tile_x, tile_y), (x*convert.TILE_PIXELS, y*convert.TILE_PIXELS)
                        measured_point_wgs = convert.tile_to_wsg(
                            measured_point,
                            vars.ZOOM
                        )
                        for day in range(24, 25):
                            for hours in range(0, 24):
                                for minutes in [15]:  # range(0, 60, 15):
                                    # testData/2021-11-23T00:00
                                    folder = f"testData/2021-11-{day:02}T{hours:02}:{minutes:02}"
                                    tile_dict = get_tile_dict_mem(f"{folder}/{filename}")
                                    traffic_sum = 0
                                    traffic_flow_layer = tile_dict["layers"][0]
                                    assert traffic_flow_layer["name"] == "Traffic flow"
                                    for feature in traffic_flow_layer["features"]:
                                        assert feature["type"] == 'LINESTRING'
                                        properties = get_feature_properties(traffic_flow_layer, feature)
                                        road_type = properties[0][1]["stringValue"]

                                        assert properties[1][0] == 'traffic_level'
                                        traffic_level = 1 - properties[1][1]["doubleValue"]
                                        if traffic_level > 0:
                                            geometry = list(parse_geometry(feature["geometry"]))
                                            for shape in geometry:
                                                segments = []
                                                for point_index in range(0, len(shape) - 1):
                                                    segments.append((shape[point_index], shape[point_index + 1]))

                                                for segment in segments:
                                                    w_d_s = weighted_distance_sum(measured_point[2], segment[0], segment[1],
                                                                                  weight)
                                                    # s = w_d_s * vars.ROAD_TYPE_WEIGHTS[road_type] * traffic_level * vars.RADIUS
                                                    traffic_sum += w_d_s * vars.ROAD_TYPE_WEIGHTS[
                                                        road_type] * traffic_level * vars.RADIUS

                                    # print(f"{day} {hours}:{minutes} {traffic_sum}")
                                    writer.writerow({
                                        'lon': measured_point_wgs[0],
                                        'lat': measured_point_wgs[1],
                                        'time': datetime.datetime(2021, 11, day, hour=hours, minute=minutes).strftime(
                                            '%Y/%m/%d %H:%M:%S'),
                                        'value': int(traffic_sum)
                                    })
                        # writer.writerow({
                        #     'lon': measured_point_wgs[0],
                        #     'lat': measured_point_wgs[1]
                        # })
                        y += tile_step
                    x += tile_step
