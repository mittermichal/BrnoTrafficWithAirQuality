import requests
import os
import sys

import vars
import time

"""
script to download test data from tomtom traffic vector flow api

docs:
https://developer.tomtom.com/content/traffic-api-explorer#/Traffic%20Flow
https://developer.tomtom.com/traffic-api/traffic-api-documentation-traffic-flow/vector-flow-tiles 
"""

if __name__ == '__main__':
    api_key = os.getenv('KEY')
    if not api_key:
        print('set KEY as env. variable')
        print(f'e.g. KEY=12345 python {sys.argv[0]}')
        exit(1)

    lon, lat = vars.CURRENT_STATION
    zoom = vars.ZOOM
    # bbox = convert.point_radius_bbox(lon, lat, zoom, convert.meters_to_tile(vars.RADIUS, zoom))
    bbox = vars.BRNO_BBOX
    time_string = time.strftime("%Y-%m-%dT%H:%M:%S")
    os.mkdir(f'testData/{time_string}')
    for x in range(bbox[0][0], bbox[1][0]+1):
        for y in range(bbox[0][1], bbox[1][1]+1):
            print(x, y)
            response = requests.get(f'https://api.tomtom.com/traffic/map/4/tile/flow/relative/{zoom}/{x}/{y}.pbf?roadTypes=%5B0%2C1%2C2%2C3%2C4%2C5%2C6%2C7%2C8%5D&tags=%5Broad_type%2Ctraffic_level%2Ctraffic_road_coverage%2Cleft_hand_traffic%2Croad_closure%5D&key={api_key}')
            with open(f'testData/{time_string}/test_{x}_{y}.pbf', 'wb') as f:
                bytes_saved = f.write(response.content)
                print(f'saved {bytes_saved} bytes')
