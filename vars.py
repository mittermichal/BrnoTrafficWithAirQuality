import air_quality_stations
import colors

CURRENT_STATION = air_quality_stations.UVOZ
RADIUS = 500  # m
ZOOM = 13

BRNO_BBOX = (4472, 2805), (4475, 2807)

ROAD_TYPE_WEIGHTS = {
    "Motorway": 10,
    "International road": 9,
    "Major road": 8,
    "Secondary road": 7,
    "Connecting road": 6,
    "Major local road": 5,
    "Local road": 4,
    "Minor local road": 3,
    "Non public road": 2,
    "Parking road": 1
}

ROAD_TYPE_COLORS = {
    "Motorway": colors.MAGENTA,
    "International road": colors.RED,
    "Major road": colors.ORANGE,
    "Secondary road": colors.YELLOW,
    "Connecting road": colors.CH_GREEN,
    "Major local road": colors.GREEN,
    "Local road": colors.SPRING_GREEN,
    "Minor local road": colors.CYAN,
    "Non public road": colors.VIOLET,
    "Parking road": colors.WHITE
}
