import convert
import vars

if __name__ == '__main__':
    lon, lat = vars.CURRENT_STATION
    station = convert.wsg_to_tile(lon, lat, 14)
    print(station[1])
