from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils, plugutils
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
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
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
            LimbType.TIP: om.MMatrix(
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
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
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
            LimbType.TIP: om.MMatrix(
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

    # region Methods
    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.

        :rtype: None
        """

        # Check if hand component exists
        #
        handComponents = self.findComponentDescendants('HandComponent')
        hasHandComponent = len(handComponents)

        if not hasHandComponent:

            return

        # Evaluate handedness
        #
        handComponent = handComponents[0]
        isPreferred = bool(handComponent.preferredHand)

        if not isPreferred:

            return

        # Get opposite hand control
        #
        wristIKCtrl = self.getPublishedNode(f'Wrist_IK')
        handCtrl = handComponent.getPublishedNode('Hand')

        otherWristIKCtrl = wristIKCtrl.getOppositeNode()

        if otherWristIKCtrl is None:

            return

        # Check if space target entry already exists
        #
        side = self.Side(self.componentSide)
        sidePrefix = side.name[0].upper()

        otherSpaceSwitch = self.scene(otherWristIKCtrl.userProperties['spaceSwitch'])
        targets = {target.name(): target.index for target in otherSpaceSwitch.iterTargets()}
        index = targets.get(handCtrl.name(), None)

        hasTarget = isinstance(index, int)

        if hasTarget:

            # Reconnect target to space switch
            #
            otherSpaceSwitch.connectPlugs(handCtrl[f'worldMatrix[{handCtrl.instanceNumber()}]'], f'target[{index}].targetMatrix', force=True)

        else:

            # Append control to opposite space switch targets
            #
            index = otherSpaceSwitch.addTarget(handCtrl, maintainOffset=False)

            otherWristIKCtrl.addDivider('Extras')
            otherWristIKCtrl.addAttr(longName=f'positionSpaceW{index}', niceName=f'Position Space ({sidePrefix}_Hand)', attributeType='float', min=0.0, max=1.0, keyable=True)
            otherWristIKCtrl.addAttr(longName=f'rotationSpaceW{index}', niceName=f'Rotation Space ({sidePrefix}_Hand)', attributeType='float', min=0.0, max=1.0, keyable=True)

            otherSpaceSwitch.connectPlugs(otherWristIKCtrl[f'positionSpaceW{index}'], f'target[{index}].targetTranslateWeight')
            otherSpaceSwitch.connectPlugs(otherWristIKCtrl[f'rotationSpaceW{index}'], f'target[{index}].targetRotateWeight')

        # Edit target offsets
        #
        otherSpace = self.scene(otherWristIKCtrl.userProperties['space'])
        offsetMatrix = otherSpace.worldMatrix() * otherWristIKCtrl.worldInverseMatrix()
        mirrorMatrix = self.__default_mirror_matrices__[self.Side.RIGHT]
        twistMatrix = transformutils.createRotationMatrix([180.0, 0.0, 0.0])

        targetMatrix = (offsetMatrix * (twistMatrix * (mirrorMatrix * wristIKCtrl.worldMatrix()))) * handCtrl.worldInverseMatrix()  # Trust the math
        offsetRotate = transformutils.decomposeTransformMatrix(targetMatrix)[1]

        otherSpaceSwitch.setAttr(f'target[{index}]', {'targetScaleWeight': 0.0, 'targetOffsetRotate': offsetRotate}, convertUnits=False)
    # endregion
