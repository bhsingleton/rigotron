from enum import IntEnum


class Side(IntEnum):
    """
    Enum class of all the available rig sides.
    """

    CENTER = 0
    LEFT = 1
    RIGHT = 2
    NONE = 3


class Type(IntEnum):
    """
    Enum class of all the available joint types.
    """

    NONE = 0
    ROOT = 1
    FOOT = 2
    HIP = 3
    KNEE = 4
    TOE = 5
    SPINE = 6
    HEAD = 7
    NECK = 8
    COLLAR = 9
    SHOULDER = 10
    ELBOW = 11
    HAND = 12
    FINGER = 13
    THUMB = 14
    PROP_A = 15
    PROP_B = 16
    PROP_C = 17
    OTHER = 18
    INDEX_FINGER = 19
    MIDDLE_FINGER = 20
    RING_FINGER = 21
    PINKY_FINGER = 22
    EXTRA_FINGER = 23
    BIG_TOE = 24
    INDEX_TOE = 25
    MIDDLE_TOE = 26
    RING_TOE = 27
    PINKY_TOE = 28
    EXTRA_TOE = 29


class Style(IntEnum):
    """
    Enum class of all the available joint draw styles.
    """

    BONE = 0
    BOX = 1
    NONE = 2
    JOINT = 3


class Status(IntEnum):
    """
    Enum class of all the available rig states.
    """

    META = 0
    SKELETON = 1
    RIG = 2