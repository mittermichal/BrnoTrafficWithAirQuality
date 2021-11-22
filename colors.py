WHITE = 0, 0, 0
RED = 255, 0, 0
GREEN = 0, 255, 0
CH_GREEN = 127, 255, 0
SPRING_GREEN = 0, 255, 128
BLUE = 0, 0, 255
YELLOW = 255, 255, 0
CYAN = 0, 255, 255
ORANGE = 255, 165, 0
MAGENTA = 255, 0, 255
VIOLET = 143, 0, 255


def from_level(level: float):
    """
    :param level: 0.0 - 1.0
    :return: green - red
    """
    return int(level*255), int((1-level)*255), 0


def grey(level: float):
    """
    :param level: 0.0 - 1.0
    :return: black-white
    """
    return int(level*255), int(level*255), int(level*255)
