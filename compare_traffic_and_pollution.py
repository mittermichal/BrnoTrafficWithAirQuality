"""
for hours in range(0, 24)
    for minutes in range(0, 60, 15)
    # testData/2021-11-23T00:00
    print(f"2021-11-23T{}:{}")
"""

from google.protobuf.json_format import MessageToDict
import convert
import tomtom_pb2
import vars
from tomtom import get_feature_properties, weight, parse_geometry, weighted_distance_sum
import csv
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime

if __name__ == '__main__':
    lon, lat = vars.CURRENT_STATION
    station = convert.wsg_to_tile(lon, lat, vars.ZOOM)
    x, y = station[1]
    # '2021/05/05 12:04:37.692+00'

    day_range = range(23, 28)

    air_cols = ['no2_1h', 'pm10_1h', 'pm2_5_1h']

    air_times = {x:[] for x in air_cols}
    air_values = {x:[] for x in air_cols}

    time_str_len = len('2021/05/05 12:04:37')
    with open('temp/air_quality.csv', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            if row['code'] == 'BBNVA':
                t = time.strptime(row['actualized'][:time_str_len], '%Y/%m/%d %H:%M:%S')
                if t.tm_year == 2021 and t.tm_mon == 11 and day_range.start <= t.tm_mday < day_range.stop:
                    # print(f"{t.tm_mday} {t.tm_hour}:{t.tm_min} {row['no2_1h']}")
                    for col in air_cols:
                        if row[col]:
                            air_times[col].append(datetime.datetime.fromtimestamp(time.mktime(t)))
                            air_values[col].append(float(row[col]))

    traffic_times = []
    traffic_values = []
    filename = f"test_{x}_{y}.pbf"
    for day in day_range:
        for hours in range(0, 24):
            for minutes in [15]:  # range(0, 60, 15):
                # testData/2021-11-23T00:00
                folder = f"testData/2021-11-{day:02}T{hours:02}:{minutes:02}"
                tile = tomtom_pb2.Tile()
                with open(f"{folder}/{filename}", "rb") as file:
                    tile.ParseFromString(file.read())
                tile_dict = MessageToDict(tile)
                traffic_sum = 0
                traffic_flow_layer = tile_dict["layers"][0]
                assert traffic_flow_layer["name"] == "Traffic flow"
                for feature in traffic_flow_layer["features"]:
                    assert feature["type"] == 'LINESTRING'
                    properties = get_feature_properties(traffic_flow_layer, feature)
                    road_type = properties[0][1]["stringValue"]

                    assert properties[1][0] == 'traffic_level'
                    traffic_level = 1 - properties[1][1]["doubleValue"]

                    geometry = list(parse_geometry(feature["geometry"]))
                    for shape in geometry:
                        segments = []
                        for point_index in range(0, len(shape) - 1):
                            segments.append((shape[point_index], shape[point_index + 1]))

                        for segment in segments:
                            if traffic_level:
                                w_d_s = weighted_distance_sum(station[2], segment[0], segment[1], weight)
                                # s = w_d_s * vars.ROAD_TYPE_WEIGHTS[road_type] * traffic_level * vars.RADIUS
                                traffic_sum += w_d_s * vars.ROAD_TYPE_WEIGHTS[road_type] * traffic_level * vars.RADIUS
                print(f"{day} {hours}:{minutes} {traffic_sum}")
                traffic_times.append(datetime.datetime(2021, 11, day, hour=hours, minute=minutes))
                traffic_values.append(traffic_sum)

    fig, ax = plt.subplots()
    for col in air_cols:
        ax.plot(air_times[col], air_values[col], label=col)
    line2 = ax.plot(traffic_times, traffic_values, label='traffic')
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%A %d.%m.%Y'))
    ax.legend()
    plt.show()
