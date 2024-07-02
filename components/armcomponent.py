from maya.api import OpenMaya as om
from .twobonelimbcomponent import TwoBoneLimbComponent, LimbType
from ..libs import Side, Type

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ArmComponent(TwoBoneLimbComponent):
    """
    Overload of `AbstractComponent` that implements arm components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Arm'
    __default_hinge_name__ = 'Elbow'
    __default_limb_names__ = ('UpperArm', 'Forearm', 'Wrist')
    __default_limb_types__ = (Type.SHOULDER, Type.ELBOW, Type.HAND)
    __default_limb_matrices__ = {
        Side.LEFT: {
            LimbType.UPPER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (20.0, 0.0, 160.0, 1.0)
                ]
            ),
            LimbType.HINGE: om.MMatrix(
                [
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (60.0, 0.0, 160.0, 1.0)
                ]
            ),
            LimbType.LOWER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (60.0, 0.0, 160.0, 1.0)
                ]
            ),
            LimbType.EXTREMITY: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (100.0, 0.0, 160.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            LimbType.UPPER: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-20.0, 0.0, 160.0, 1.0)
                ]
            ),
            LimbType.HINGE: om.MMatrix(
                [
                    (0.0, 1.0, 0.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-60.0, 0.0, 160.0, 1.0)
                ]
            ),
            LimbType.LOWER: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-60.0, 0.0, 160.0, 1.0)
                ]
            ),
            LimbType.EXTREMITY: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-100.0, 0.0, 160.0, 1.0)
                ]
            )
        }
    }
    __default_rbf_samples__ = {
        Side.LEFT: [
            {'sampleName': 'Forward', 'sampleInputTranslate': om.MVector.kZaxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Backward', 'sampleInputTranslate': om.MVector.kZnegAxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Left', 'sampleInputTranslate': om.MVector.kXnegAxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Right', 'sampleInputTranslate': om.MVector.kXaxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Up', 'sampleInputTranslate': om.MVector.kYnegAxisVector, 'sampleOutputTranslate': (0.0, 0.0, -1.0)},
            {'sampleName': 'Down', 'sampleInputTranslate': om.MVector.kYaxisVector, 'sampleOutputTranslate': (0.0, 0.0, 1.0)}
        ],
        Side.RIGHT: [
            {'sampleName': 'Forward', 'sampleInputTranslate': om.MVector.kZnegAxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Backward', 'sampleInputTranslate': om.MVector.kZaxisVector, 'sampleOutputTranslate': (0.0, 1.0, 0.0)},
            {'sampleName': 'Left', 'sampleInputTranslate': om.MVector.kXaxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Right', 'sampleInputTranslate': om.MVector.kXnegAxisVector, 'sampleOutputTranslate': (0.0, -1.0, 0.0)},
            {'sampleName': 'Up', 'sampleInputTranslate': om.MVector.kYnegAxisVector, 'sampleOutputTranslate': (0.0, 0.0, 1.0)},
            {'sampleName': 'Down', 'sampleInputTranslate': om.MVector.kYaxisVector, 'sampleOutputTranslate': (0.0, 0.0, -1.0)}
        ]
    }
    # endregion
