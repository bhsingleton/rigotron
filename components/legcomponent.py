from maya.api import OpenMaya as om
from .twobonelimbcomponent import TwoBoneLimbComponent, LimbType
from ..libs import Side, Type

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LegComponent(TwoBoneLimbComponent):
    """
    Overload of `TwoBoneLimbComponent` that implements leg components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_hinge_name__ = 'Knee'
    __default_component_name__ = 'Leg'
    __default_limb_names__ = ('Thigh', 'Calf', 'Ankle')
    __default_limb_types__ = (Type.HIP, Type.KNEE, Type.FOOT)
    __default_limb_matrices__ = {
        Side.CENTER: {
            LimbType.UPPER: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 90.0, 1.0)
                ]
            ),
            LimbType.LOWER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            ),
            LimbType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            )
        },
        Side.LEFT: {
            LimbType.UPPER: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, 0.0, 90.0, 1.0)
                ]
            ),
            LimbType.LOWER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            ),
            LimbType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            LimbType.UPPER: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, 0.0, 90.0, 1.0)
                ]
            ),
            LimbType.LOWER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            ),
            LimbType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            )
        },
        Side.NONE: {
            LimbType.UPPER: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 90.0, 1.0)
                ]
            ),
            LimbType.LOWER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            ),
            LimbType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (40.0, 0.0, 0.0, 1.0)
                ]
            )
        }
    }
    __default_rbf_samples__ = {
        Side.LEFT: [
            {'sampleName': 'Forward', 'sampleInputTranslate': om.MVector.kXnegAxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Backward', 'sampleInputTranslate': om.MVector.kXaxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Left', 'sampleInputTranslate': om.MVector.kZaxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Right', 'sampleInputTranslate': om.MVector.kZnegAxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Up', 'sampleInputTranslate': om.MVector.kYaxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Down', 'sampleInputTranslate': om.MVector.kYnegAxisVector, 'sampleOutputTranslate': (-1.0, 0.0, 0.0)}
        ],
        Side.RIGHT: [
            {'sampleName': 'Forward', 'sampleInputTranslate': om.MVector.kXnegAxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Backward', 'sampleInputTranslate': om.MVector.kXaxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Left', 'sampleInputTranslate': om.MVector.kZaxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Right', 'sampleInputTranslate': om.MVector.kZnegAxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Up', 'sampleInputTranslate': om.MVector.kYaxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Down', 'sampleInputTranslate': om.MVector.kYnegAxisVector, 'sampleOutputTranslate': (-1.0, 0.0, 0.0)}
        ]
    }
    # endregion
