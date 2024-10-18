from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.maya.libs import transformutils, shapeutils
from dcc.dataclasses.colour import Colour
from . import extremitycomponent
from ..libs import Side, Style, skeletonspec, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class HandType(IntEnum):
    """
    Collection of all available hand subtypes.
    """

    HAND = 0
    KNUCKLE = 1
    FINGERS = 2


class HandPivotType(IntEnum):
    """
    Collection of all available hand pivots.
    """

    KNUCKLE = 0
    TIP = 1


class FingerType(IntEnum):
    """
    Collection of all available finger appendages.
    """

    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4


class HandComponent(extremitycomponent.ExtremityComponent):
    """
    Overload of `ExtremityComponent` that implements hand components.
    """

    # region Enums
    HandType = HandType
    HandPivotType = HandPivotType
    FingerType = FingerType
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Hand'
    __default_digit_name__ = 'Finger'
    __default_digit_types__ = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
    __default_hand_matrices__ = {
        Side.LEFT: {
            HandType.HAND: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (100.0, 0.0, 160.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            HandType.HAND: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-100.0, 0.0, 160.0, 1.0)
                ]
            )
        }
    }
    __default_pivot_matrices__ = {
        Side.LEFT: {
            HandPivotType.KNUCKLE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (120.0, 0.0, 160.0, 1.0)
                ]
            ),
            HandPivotType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (135.0, 0.0, 160.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            HandPivotType.KNUCKLE: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-120.0, 0.0, 160.0, 1.0)
                ]
            ),
            HandPivotType.TIP: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-135.0, 0.0, 160.0, 1.0)
                ]
            )
        }
    }
    __default_metacarpal_spacing__ = 10.0
    __default_finger_spacing__ = 5.0
    __default_finger_matrices__ = {
        Side.LEFT: {
            FingerType.THUMB: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (110.0, -10.0, 160.0, 1.0)
                ]
            ),
            FingerType.INDEX: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (120.0, -5.0, 160.0, 1.0)
                ]
            ),
            FingerType.MIDDLE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (120.0, 0.0, 160.0, 1.0)
                ]
            ),
            FingerType.RING: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (120.0, 5.0, 160.0, 1.0)
                ]
            ),
            FingerType.PINKY: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (120.0, 10.0, 160.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            FingerType.THUMB: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-110.0, -10.0, 160.0, 1.0)
                ]
            ),
            FingerType.INDEX: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-120.0, -5.0, 160.0, 1.0)
                ]
            ),
            FingerType.MIDDLE: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-120.0, 0.0, 160.0, 1.0)
                ]
            ),
            FingerType.RING: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-120.0, 5.0, 160.0, 1.0)
                ]
            ),
            FingerType.PINKY: om.MMatrix(
                [
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (-120.0, 10.0, 160.0, 1.0)
                ]
            )
        }
    }
    __default_mirror_matrices__ = {
        Side.LEFT: om.MMatrix.kIdentity,
        Side.RIGHT: om.MMatrix(
            [
                (-1.0, 0.0, 0.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )
    }
    # endregion

    # region Attributes
    preferredHand = mpyattribute.MPyAttribute('preferredHand', attributeType='bool', default=False)
    rollEnabled = mpyattribute.MPyAttribute('rollEnabled', attributeType='bool', default=True)
    thumbEnabled = mpyattribute.MPyAttribute('thumbEnabled', attributeType='bool', default=True)
    numThumbLinks = mpyattribute.MPyAttribute('numThumbLinks', attributeType='int', min=1, max=10, default=2)
    metacarpalsEnabled = mpyattribute.MPyAttribute('metacarpalsEnabled', attributeType='bool', default=False)
    numFingers = mpyattribute.MPyAttribute('numFingers', attributeType='int', min=0, max=4, default=4)
    numFingerLinks = mpyattribute.MPyAttribute('numFingerLinks', attributeType='int', min=1, max=10, default=3)
    # endregion

    # region Properties
    @thumbEnabled.changed
    def thumbEnabled(self, thumbEnabled):
        """
        Changed method that notifies any thumb state changes.

        :type thumbEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numThumbLinks.changed
    def numThumbLinks(self, numThumbLinks):
        """
        Changed method that notifies any thumb link size changes.

        :type numThumbLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()

    @metacarpalsEnabled.changed
    def metacarpalsEnabled(self, metacarpalsEnabled):
        """
        Changed method that notifies any metacarpal state changes.

        :type metacarpalsEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numFingers.changed
    def numFingers(self, numFingers):
        """
        Changed method that notifies any finger state changes.

        :type numFingers: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numFingerLinks.changed
    def numFingerLinks(self, numFingerLinks):
        """
        Changed method that notifies any finger link size changes.

        :type numFingerLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def locomotionType(self):
        """
        Returns the locomotion type for this component.

        :rtype: LocomotionType
        """

        return self.LocomotionType.DIGITGRADE

    def fingerFlags(self):
        """
        Returns the enabled flags for each finger.

        :rtype: Dict[FingerType, bool]
        """

        thumbEnabled = self.thumbEnabled
        numFingers = self.numFingers

        if numFingers == 0:

            return {FingerType.THUMB: thumbEnabled, FingerType.INDEX: False, FingerType.MIDDLE: False, FingerType.RING: False, FingerType.PINKY: False}

        elif numFingers == 1:

            return {FingerType.THUMB: thumbEnabled, FingerType.INDEX: True, FingerType.MIDDLE: False, FingerType.RING: False, FingerType.PINKY: False}

        elif numFingers == 2:

            return {FingerType.THUMB: thumbEnabled, FingerType.INDEX: True, FingerType.MIDDLE: False, FingerType.RING: False, FingerType.PINKY: True}

        elif numFingers == 3:

            return {FingerType.THUMB: thumbEnabled, FingerType.INDEX: True, FingerType.MIDDLE: True, FingerType.RING: False, FingerType.PINKY: True}

        else:

            return {FingerType.THUMB: thumbEnabled, FingerType.INDEX: True, FingerType.MIDDLE: True, FingerType.RING: True, FingerType.PINKY: True}

    def invalidatePivotSpecs(self, pivotSpecs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: None
        """

        # Concatenate pivot names
        #
        pivotTypes = self.HandPivotType.__members__
        numPivotTypes = len(pivotTypes)

        pivotSpecs = self.resizePivotSpecs(numPivotTypes, pivotSpecs)
        pivotEnabled = bool(self.rollEnabled)

        for (name, pivotSpec) in zip(pivotTypes.keys(), pivotSpecs):

            pivotSpec.name = self.formatName(subname=name.title(), type='locator')
            pivotSpec.enabled = pivotEnabled

        # Call parent method
        #
        super(HandComponent, self).invalidatePivotSpecs(pivotSpecs)

    def buildPivots(self):
        """
        Builds the pivots for this component.

        :rtype: Union[Tuple[mpynode.MPyNode], None]
        """

        # Iterate through pivot specs
        #
        pivotSpecs = self.pivotSpecs()
        side = self.Side(self.componentSide)

        for (i, pivotSpec) in enumerate(pivotSpecs):

            # Check if pivot is enabled
            #
            if not pivotSpec.enabled:

                continue

            # Create pivot and update transform
            #
            pivot = self.scene.createNode('transform', name=pivotSpec.name)
            pivot.addPointHelper('cross', size=20.0)
            pivotSpec.uuid = pivot.uuid()

            defaultMatrix = self.__default_pivot_matrices__[side][i]
            matrix = pivotSpec.getMatrix(default=defaultMatrix)
            pivot.setWorldMatrix(matrix)

    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        handSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)

        # Edit skeleton specs
        #
        handSpec.name = self.formatName()
        handSpec.driver = self.formatName(subname='Wrist', kinemat='Blend', type='joint')

        # Check if finger spec groups exist
        #
        fingerGroups = handSpec.groups
        numFingerGroups = len(fingerGroups)

        fingerMembers = self.FingerType.__members__
        numFingerMembers = len(fingerMembers)

        if numFingerGroups != numFingerMembers:

            fingerGroups.update([(i, []) for i in range(numFingerMembers)])

        # Iterate through finger spec groups
        #
        fingerFlags = self.fingerFlags()
        metacarpalsEnabled = bool(self.metacarpalsEnabled)

        for (fingerType, fingerGroup) in fingerGroups.items():

            # Iterate through digit specs
            #
            fingerType = self.FingerType(fingerType)
            fingerName = fingerType.name.title()
            fingerEnabled = fingerFlags.get(fingerType, False)

            isThumb = (fingerType == self.FingerType.THUMB)
            numFingerLinks = int(self.numThumbLinks) if isThumb else int(self.numFingerLinks)
            metacarpalSpec, *fingerSpecs, fingerTipSpec = self.resizeSkeletonSpecs(numFingerLinks + 2, fingerGroup)

            fullMetacarpalName = f'{fingerName}Metacarpal'
            metacarpalSpec.name = self.formatName(subname=fullMetacarpalName)
            metacarpalSpec.driver = self.formatName(subname=fullMetacarpalName, kinemat='Blend', type='joint')
            metacarpalSpec.enabled = metacarpalsEnabled and fingerEnabled

            fullFingerName = fingerName if isThumb else f'{fingerName}Finger'

            for (j, fingerSpec) in enumerate(fingerSpecs, start=1):

                fingerSpec.name = self.formatName(subname=fullFingerName, index=j)
                fingerSpec.driver = self.formatName(subname=fullFingerName, index=j, type='control')
                fingerSpec.enabled = fingerEnabled

            fullFingerTipName = f'{fullFingerName}Tip'
            fingerTipSpec.name = self.formatName(subname=fullFingerTipName)
            fingerTipSpec.driver = self.formatName(subname=fullFingerTipName, type='target')
            fingerTipSpec.enabled = fingerEnabled

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        side = self.Side(self.componentSide)
        handSpec, = self.skeletonSpecs()

        # Create hand joint
        #
        handJoint = self.scene.createNode('joint', name=handSpec.name)
        handJoint.side = side
        handJoint.type = self.Type.HAND
        handSpec.uuid = handJoint.uuid()

        handMatrix = handSpec.getMatrix(default=self.__default_hand_matrices__[side][HandType.HAND])
        handJoint.setWorldMatrix(handMatrix)

        # Create finger joints
        #
        fingerGroups = handSpec.groups
        jointTypes = (self.Type.THUMB, self.Type.INDEX_FINGER, self.Type.MIDDLE_FINGER, self.Type.RING_FINGER, self.Type.PINKY_FINGER)

        allFingerJoints = []

        for (fingerType, fingerGroup) in fingerGroups.items():

            # Check if finger is enabled
            #
            metacarpalSpec, *fingerSpecs = fingerGroup
            isEnabled = bool(fingerSpecs[0].enabled)

            if not isEnabled:

                continue

            # Create metacarpal joint
            #
            fingerType = self.FingerType(fingerType)
            jointType = jointTypes[fingerType]
            topLevelParent = handJoint
            defaultMetacarpalMatrix = self.__default_finger_matrices__[side][fingerType]

            if metacarpalSpec.enabled:

                metacarpalJoint = self.scene.createNode('joint', name=metacarpalSpec.name, parent=handJoint)
                metacarpalJoint.side = side
                metacarpalJoint.type = jointType
                metacarpalJoint.displayLocalAxis = True
                metacarpalSpec.uuid = metacarpalJoint.uuid()

                metacarpalMatrix = metacarpalSpec.getMatrix(default=defaultMetacarpalMatrix)
                metacarpalJoint.setWorldMatrix(metacarpalMatrix)

                topLevelParent = metacarpalJoint

            # Create finger joints
            #
            numFingerJoints = len(fingerSpecs)
            fingerJoints = [None] * numFingerJoints

            for (j, fingerSpec) in enumerate(fingerSpecs):

                # Create finger-link
                #
                parent = fingerJoints[j - 1] if (j > 0) else topLevelParent

                fingerJoint = self.scene.createNode('joint', name=fingerSpec.name, parent=parent)
                fingerJoint.side = side
                fingerJoint.type = jointType
                fingerJoint.displayLocalAxis = True
                fingerSpec.uuid = fingerJoint.uuid()

                defaultFingerOffset = self.__default_metacarpal_spacing__ + (self.__default_finger_spacing__ * j)
                defaultFingerMatrix = transformutils.createTranslateMatrix([defaultFingerOffset, 0.0, 0.0]) * defaultMetacarpalMatrix
                fingerMatrix = fingerSpec.getMatrix(default=defaultFingerMatrix)
                fingerJoint.setWorldMatrix(fingerMatrix)

                fingerJoints[j] = fingerJoint

            allFingerJoints.append(fingerJoints)

        return (handJoint, *allFingerJoints)

    def buildFullRig(self):
        """
        Builds the full control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        handSpec, = self.skeletonSpecs()
        handExportJoint = handSpec.getNode()

        knuckleSpec, fingerTipSpec = self.pivotSpecs()
        knucklePoint = transformutils.decomposeTransformMatrix(knuckleSpec.matrix)[0]
        fingerTipPoint = transformutils.decomposeTransformMatrix(fingerTipSpec.matrix)[0]
        handMatrix = handExportJoint.worldMatrix()
        knuckleMatrix = transformutils.createRotationMatrix(handMatrix) * transformutils.createTranslateMatrix(knucklePoint)

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        requiresMirroring = (componentSide == self.Side.RIGHT)
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        rigScale = self.findControlRig().getRigScale()

        # Get component dependencies
        #
        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        limbComponents = self.findComponentAncestors('LimbComponent')
        hasLimbComponent = len(limbComponents) == 1

        if not hasLimbComponent:

            raise NotImplementedError('buildComponent() limbless hand components have not been implemented!')

        # Get required limb nodes
        #
        limbComponent = limbComponents[0]

        switchCtrl = self.scene(limbComponent.userProperties['switchControl'])
        limbFKCtrl = self.scene(limbComponent.userProperties['fkControls'][-1])
        limbIKCtrl = self.scene(limbComponent.userProperties['ikControls'][-1])
        limbIKOffsetCtrl = self.scene(limbIKCtrl.userProperties['offset'])
        limbTipIKJoint = self.scene(limbComponent.userProperties['ikJoints'][-1])
        limbTipRIKJoint = self.scene(limbComponent.userProperties['rikJoints'][-1])
        limbRIKSoftener = self.scene(limbComponent.userProperties['rikSoftener'])

        # Create hand control
        #
        handCtrlMatrix = mirrorMatrix * handMatrix

        handSpaceName = self.formatName(type='space')
        handSpace = self.scene.createNode('transform', name=handSpaceName, parent=controlsGroup)
        handSpace.setWorldMatrix(handCtrlMatrix)
        handSpace.freezeTransform()

        handCtrlName = self.formatName(type='control')
        handCtrl = self.scene.createNode('transform', name=handCtrlName, parent=handSpace)
        handCtrl.addShape('HandCurve', size=(20.0 * rigScale), localScale=(mirrorSign, mirrorSign, 1.0), lineWidth=2.0, side=componentSide)
        handCtrl.addDivider('Settings')
        handCtrl.addAttr(longName='pin', attributeType='float', min=0.0, max=1.0, keyable=True)
        handCtrl.addDivider('Pose')
        handCtrl.addAttr(longName='curl', attributeType='angle', keyable=True)
        handCtrl.addAttr(longName='spread', attributeType='angle', keyable=True)
        handCtrl.addAttr(longName='splay', attributeType='angle', keyable=True)
        handCtrl.addDivider('Spaces')
        handCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        handCtrl.addAttr(longName='localForearmLock', attributeType='float', min=0.0, max=1.0, keyable=True)
        handCtrl.prepareChannelBoxForAnimation()
        self.publishNode(handCtrl, alias='Hand')

        handSpaceSwitch = handSpace.addSpaceSwitch([limbFKCtrl, limbIKOffsetCtrl, motionCtrl], weighted=True, maintainOffset=True)
        handSpaceSwitch.setAttr('target', [{'targetReverse': (True, True, True)}, {}, {'targetWeight': (0.0, 0.0, 0.0)}])
        handSpaceSwitch.connectPlugs(switchCtrl['mode'], 'target[0].targetWeight')
        handSpaceSwitch.connectPlugs(switchCtrl['mode'], 'target[1].targetWeight')
        handSpaceSwitch.connectPlugs(handCtrl['localOrGlobal'], 'target[2].targetRotateWeight', force=True)

        handIKSpaceSwitchName = self.formatName(subname='IK', type='spaceSwitch')
        handIKSpaceSwitch = self.scene.createNode('spaceSwitch', name=handIKSpaceSwitchName)
        handIKSpaceSwitch.weighted = True
        handIKSpaceSwitch.setAttr('restMatrix', handCtrlMatrix)
        handIKSpaceSwitch.addTargets([limbIKOffsetCtrl, limbTipIKJoint], maintainOffset=True)
        handIKSpaceSwitch.setAttr('target[0]', {'targetReverse': (True, True, True)})
        handIKSpaceSwitch.connectPlugs(handCtrl['localForearmLock'], 'target[0].targetWeight')
        handIKSpaceSwitch.connectPlugs(handCtrl['localForearmLock'], 'target[1].targetWeight')
        handIKSpaceSwitch.connectPlugs('outputMatrix', handSpaceSwitch['target[1].targetMatrix'], force=True)

        # Create pose driver negate nodes
        #
        fingerHalfSpreadName = self.formatName(subname='HalfSpread', type='floatMath')
        fingerHalfSpread = self.scene.createNode('floatMath', name=fingerHalfSpreadName)
        fingerHalfSpread.operation = 2  # Multiply
        fingerHalfSpread.connectPlugs(handCtrl['spread'], 'inAngleA')
        fingerHalfSpread.setAttr('inAngleB', 0.5)

        fingerNegateHalfSpreadName = self.formatName(subname='NegateHalfSpread', type='floatMath')
        fingerNegateHalfSpread = self.scene.createNode('floatMath', name=fingerNegateHalfSpreadName)
        fingerNegateHalfSpread.operation = 2  # Multiply
        fingerNegateHalfSpread.connectPlugs(handCtrl['spread'], 'inAngleA')
        fingerNegateHalfSpread.setAttr('inAngleB', -0.5)

        fingerNegateSpreadName = self.formatName(subname='NegateSpread', type='floatMath')
        fingerNegateSpread = self.scene.createNode('floatMath', name=fingerNegateSpreadName)
        fingerNegateSpread.operation = 2  # Multiply
        fingerNegateSpread.connectPlugs(handCtrl['spread'], 'inAngleA')
        fingerNegateSpread.setAttr('inAngleB', -1.0)

        fingerNegateSplayName = self.formatName(subname='NegateSplay', type='floatMath')
        fingerNegateSplay = self.scene.createNode('floatMath', name=fingerNegateSplayName)
        fingerNegateSplay.operation = 2  # Multiply
        fingerNegateSplay.connectPlugs(handCtrl['splay'], 'inAngleA')
        fingerNegateSplay.setAttr('inAngleB', -1.0)

        fingerNegateHalfSplayName = self.formatName(subname='NegateHalfSplay', type='floatMath')
        fingerNegateHalfSplay = self.scene.createNode('floatMath', name=fingerNegateHalfSplayName)
        fingerNegateHalfSplay.operation = 2  # Multiply
        fingerNegateHalfSplay.connectPlugs(handCtrl['splay'], 'inAngleA')
        fingerNegateHalfSplay.setAttr('inAngleB', -(1.0 / 3.0))

        fingerHalfSplayName = self.formatName(subname='HalfSplay', type='floatMath')
        fingerHalfSplay = self.scene.createNode('floatMath', name=fingerHalfSplayName)
        fingerHalfSplay.operation = 2  # Multiply
        fingerHalfSplay.connectPlugs(handCtrl['splay'], 'inAngleA')
        fingerHalfSplay.setAttr('inAngleB', (1.0 / 3.0))

        # Create roll controls
        #
        knuckleRollCtrlName = self.formatName(subname='Knuckle', type='control')
        knuckleRollCtrl = self.scene.createNode('transform', name=knuckleRollCtrlName, parent=handCtrl)
        knuckleRollCtrl.addPointHelper('tearDrop', size=(5.0 * rigScale), localPosition=(0.0, -10.0 * mirrorSign, 0.0), localRotate=(-90.0 * mirrorSign, 90.0, 0.0), side=componentSide)
        knuckleRollCtrl.setWorldMatrix(knuckleMatrix, skipRotate=True, skipScale=True)
        knuckleRollCtrl.freezeTransform()
        knuckleRollCtrl.addDivider('Settings')
        knuckleRollCtrl.addProxyAttr('pin', handCtrl['pin'])
        knuckleRollCtrl.addDivider('Poses')
        knuckleRollCtrl.addProxyAttr('curl', handCtrl['curl'])
        knuckleRollCtrl.addProxyAttr('spread', handCtrl['spread'])
        knuckleRollCtrl.addProxyAttr('splay', handCtrl['splay'])
        knuckleRollCtrl.hideAttr('scale', lock=True)
        knuckleRollCtrl.prepareChannelBoxForAnimation()
        self.publishNode(knuckleRollCtrl, alias='Knuckle')

        handIKTargetName = self.formatName(subname='IK', type='target')
        handIKTarget = self.scene.createNode('transform', name=handIKTargetName, parent=knuckleRollCtrl)
        handIKTarget.displayLocalAxis = True
        handIKTarget.visibility = False
        handIKTarget.copyTransform(handExportJoint, skipScale=True)
        handIKTarget.freezeTransform()
        handIKTarget.lock()

        limbRIKSoftener.connectPlugs(handIKTarget[f'worldMatrix[{handIKTarget.instanceNumber()}]'], 'endMatrix', force=True)

        # Create kinematic metacarpal joints
        #
        jointTypes = ('Wrist', 'Knuckle')
        kinematicTypes = ('FK', 'IK', 'Blend')
        handMatrices = (handMatrix, knuckleMatrix)

        handFKJoints = [None] * 2
        handIKJoints = [None] * 2
        handBlendJoints = [None] * 2
        handJoints = (handFKJoints, handIKJoints, handBlendJoints)

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = handJoints[i][j - 1] if (j > 0) else jointsGroup
                style = Style.BOX if (j == 0) else Style.JOINT

                jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.displayLocalAxis = True
                joint.drawStyle = style
                joint.segmentScaleCompensate = False
                joint.setWorldMatrix(handMatrices[j])

                handJoints[i][j] = joint

        handFKJoint, handTipFKJoint = handFKJoints
        handIKJoint, handTipIKJoint = handIKJoints
        handBlendJoint, handTipBlendJoint = handBlendJoints

        blender = switchCtrl['mode']
        handBlender = setuputils.createTransformBlends(handFKJoint, handIKJoint, handBlendJoint, blender=blender)
        handTipBlender = setuputils.createTransformBlends(handTipFKJoint, handTipIKJoint, handTipBlendJoint, blender=blender)

        handBlender.setName(self.formatName(subname=jointTypes[0], type='blendTransform'))
        handTipBlender.setName(self.formatName(subname=jointTypes[1], type='blendTransform'))

        # Constrain hand FK joint
        #
        handFKJoint.addConstraint('transformConstraint', [handCtrl], maintainOffset=requiresMirroring)

        # Constrain hand IK joints
        #
        handIKJoint.addConstraint('pointConstraint', [limbTipRIKJoint])
        handIKJoint.addConstraint('aimConstraint', [knuckleRollCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=knuckleRollCtrl, maintainOffset=True)
        handIKJoint.addConstraint('scaleConstraint', [handCtrl])

        # Create metacarpal/finger controls
        #
        handOffsetFKComposeMatrix, handOffsetFKMultMatrix, handOffsetFKInverseMatrix = None, None, None
        handTipOffsetFKComposeMatrix, handTipOffsetFKMultMatrix, handTipOffsetFKInverseMatrix = None, None, None

        metacarpalCtrls = []

        for (fingerId, fingerGroup) in handSpec.groups.items():

            # Check if finger is enabled
            #
            metacarpalSpec, *fingerSpecs, fingerTipSpec = fingerGroup
            isEnabled = fingerSpecs[0].enabled

            if not isEnabled:

                continue

            # Decompose finger group
            #
            fingerType = self.FingerType(fingerId)
            fingerName = fingerType.name.title()
            fullFingerName = fingerName if (fingerType is self.FingerType.THUMB) else f'{fingerName}Finger'

            fingerBaseExportJoint = self.scene(fingerSpecs[0].uuid)
            fingerBaseMatrix = fingerBaseExportJoint.worldMatrix()

            fingerTipExportJoint = self.scene(fingerTipSpec.uuid)
            fingerTipMatrix = fingerTipExportJoint.worldMatrix()

            # Check if metacarpals are enabled
            #
            metacarpalEnabled = bool(metacarpalSpec.enabled)
            metacarpalCtrl = None

            metacarpalBlendJoint, fingerBlendJoint, fingerTipBlendJoint = None, None, None

            if metacarpalEnabled:

                # Decompose metacarpal spec
                #
                fullMetacarpalName = f'{fingerName}Metacarpal'
                metacarpalExportJoint = self.scene(metacarpalSpec.uuid)
                metacarpalMatrix = metacarpalExportJoint.worldMatrix()

                # Create kinematic metacarpal joints
                #
                jointTypes = (fullMetacarpalName, fullFingerName, f'{fullFingerName}Tip')
                kinematicTypes = ('FK', 'IK', 'Blend')
                metacarpalMatrices = (metacarpalMatrix, fingerBaseMatrix, fingerTipMatrix)

                metacarpalFKJoints = [None] * 3
                metacarpalIKJoints = [None] * 3
                metacarpalBlendJoints = [None] * 3
                metacarpalJoints = (metacarpalFKJoints, metacarpalIKJoints, metacarpalBlendJoints)

                for (i, kinematicType) in enumerate(kinematicTypes):

                    for (j, jointType) in enumerate(jointTypes):

                        parent = metacarpalJoints[i][j - 1] if (j > 0) else handJoints[i][0]

                        jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                        joint = self.scene.createNode('joint', name=jointName, parent=parent)
                        joint.displayLocalAxis = True
                        joint.segmentScaleCompensate = False
                        joint.setWorldMatrix(metacarpalMatrices[j])

                        metacarpalJoints[i][j] = joint

                metacarpalFKJoint, fingerFKJoint, fingerTipFKJoint = metacarpalFKJoints
                metacarpalIKJoint, fingerIKJoint, fingerTipIKJoint = metacarpalIKJoints
                metacarpalBlendJoint, fingerBlendJoint, fingerTipBlendJoint = metacarpalBlendJoints

                metacarpalBlender = setuputils.createTransformBlends(metacarpalFKJoint, metacarpalIKJoint, metacarpalBlendJoint, blender=blender)
                fingerBlender = setuputils.createTransformBlends(fingerFKJoint, fingerIKJoint, fingerBlendJoint, blender=blender)
                fingerTipBlender = setuputils.createTransformBlends(fingerTipFKJoint, fingerTipIKJoint, fingerTipBlendJoint, blender=blender)

                metacarpalBlender.setName(self.formatName(subname=jointTypes[0], type='blendTransform'))
                fingerBlender.setName(self.formatName(subname=jointTypes[1], type='blendTransform'))
                fingerTipBlender.setName(self.formatName(subname=jointTypes[2], type='blendTransform'))

                # Create metacarpal control
                #
                metacarpalSpaceName = self.formatName(subname=fullMetacarpalName, type='space')
                metacarpalSpace = self.scene.createNode('transform', name=metacarpalSpaceName, parent=handCtrl)
                metacarpalSpace.setWorldMatrix(metacarpalMatrix)
                metacarpalSpace.freezeTransform()

                metacarpalCtrlName = self.formatName(subname=fullMetacarpalName, type='control')
                metacarpalCtrl = self.scene.createNode('transform', name=metacarpalCtrlName, parent=metacarpalSpace)
                metacarpalCtrl.addPointHelper('square', size=(5.0 * rigScale), localScale=(1.0, 2.0, 0.25), colorRGB=lightColorRGB)
                metacarpalCtrl.prepareChannelBoxForAnimation()
                self.publishNode(metacarpalCtrl, alias=fullMetacarpalName)

                metacarpalCtrl.userProperties['space'] = metacarpalSpace.uuid()
                metacarpalCtrl.userProperties['type'] = fingerType

                metacarpalCtrls.append(metacarpalCtrl)

                # Constrain metacarpal FK joint
                #
                metacarpalFKJoint.addConstraint('transformConstraint', [metacarpalCtrl], maintainOffset=requiresMirroring)

                # Repurpose FK transform components for IK joints
                #
                metacarpalIKJoint.connectPlugs(metacarpalFKJoint['translate'], 'translate')
                metacarpalIKJoint.connectPlugs(metacarpalFKJoint['scale'], 'scale')

                # Create metacarpal-tip IK target
                #
                metacarpalTipIKTargetName = self.formatName(subname=f'{fullMetacarpalName}Tip', kinemat='IK', type='target')
                metacarpalTipIKTarget = self.scene.createNode('transform', name=metacarpalTipIKTargetName, parent=knuckleRollCtrl)
                metacarpalTipIKTarget.displayLocalAxis = True
                metacarpalTipIKTarget.visibility = False
                metacarpalTipIKTarget.lock()

                metacarpalTipIKMultMatrixName = self.formatName(subname=f'{fullMetacarpalName}Tip', kinemat='IK', type='multMatrix')
                metacarpalTipIKMultMatrix = self.scene.createNode('multMatrix', name=metacarpalTipIKMultMatrixName)
                metacarpalTipIKMultMatrix.connectPlugs(fingerFKJoint[f'worldMatrix[{fingerFKJoint.instanceNumber()}]'], 'matrixIn[0]')

                if componentSide == self.Side.RIGHT:

                    if handTipOffsetFKComposeMatrix is None:

                        handTipOffsetFKComposeMatrixName = self.formatName(subname='KnuckleOffset', kinemat='FK', type='composeMatrix')
                        handTipOffsetFKComposeMatrix = self.scene.createNode('composeMatrix', name=handTipOffsetFKComposeMatrixName)
                        handTipOffsetFKComposeMatrix.setAttr('inputRotateZ', 180.0)

                    if handTipOffsetFKMultMatrix is None:

                        handTipOffsetFKMultMatrixName = self.formatName(subname='KnuckleOffset', kinemat='FK', type='multMatrix')
                        handTipOffsetFKMultMatrix = self.scene.createNode('multMatrix', name=handTipOffsetFKMultMatrixName)
                        handTipOffsetFKMultMatrix.connectPlugs(handTipOffsetFKComposeMatrix['outputMatrix'], 'matrixIn[0]')
                        handTipOffsetFKMultMatrix.connectPlugs(handTipFKJoint[f'worldMatrix[{handTipFKJoint.instanceNumber()}]'], 'matrixIn[1]')

                    if handTipOffsetFKInverseMatrix is None:

                        handTipOffsetFKInverseMatrixName = self.formatName(subname='KnuckleOffset', kinemat='FK', type='inverseMatrix')
                        handTipOffsetFKInverseMatrix = self.scene.createNode('inverseMatrix', name=handTipOffsetFKInverseMatrixName)
                        handTipOffsetFKInverseMatrix.connectPlugs(handTipOffsetFKMultMatrix['matrixSum'], 'inputMatrix')

                    metacarpalTipIKMultMatrix.connectPlugs(handTipOffsetFKInverseMatrix['outputMatrix'], 'matrixIn[1]')
                    metacarpalTipIKMultMatrix.connectPlugs('matrixSum', metacarpalTipIKTarget['offsetParentMatrix'])

                else:

                    metacarpalTipIKMultMatrix.connectPlugs(handTipFKJoint[f'worldInverseMatrix[{handTipFKJoint.instanceNumber()}]'], 'matrixIn[1]')
                    metacarpalTipIKMultMatrix.connectPlugs('matrixSum', metacarpalTipIKTarget['offsetParentMatrix'])

                # Create finger-tip IK target
                #
                fingerTipIKTargetName = self.formatName(subname=f'{fullFingerName}Tip', kinemat='IK', type='target')
                fingerTipIKTarget = self.scene.createNode('transform', name=fingerTipIKTargetName, parent=handCtrl)
                fingerTipIKTarget.displayLocalAxis = True
                fingerTipIKTarget.visibility = False
                fingerTipIKTarget.lock()

                fingerTipIKMultMatrixName = self.formatName(subname=f'{fullFingerName}Tip', kinemat='IK', type='multMatrix')
                fingerTipIKMultMatrix = self.scene.createNode('multMatrix', name=fingerTipIKMultMatrixName)
                fingerTipIKMultMatrix.connectPlugs(fingerTipFKJoint[f'worldMatrix[{fingerTipFKJoint.instanceNumber()}]'], 'matrixIn[0]')

                if componentSide == self.Side.RIGHT:

                    if handOffsetFKComposeMatrix is None:

                        handOffsetFKComposeMatrixName = self.formatName(subname='WristOffset', kinemat='FK', type='composeMatrix')
                        handOffsetFKComposeMatrix = self.scene.createNode('composeMatrix', name=handOffsetFKComposeMatrixName)
                        handOffsetFKComposeMatrix.setAttr('inputRotateZ', 180.0)

                    if handOffsetFKMultMatrix is None:

                        handOffsetFKMultMatrixName = self.formatName(subname='WristOffset', kinemat='FK', type='multMatrix')
                        handOffsetFKMultMatrix = self.scene.createNode('multMatrix', name=handOffsetFKMultMatrixName)
                        handOffsetFKMultMatrix.connectPlugs(handOffsetFKComposeMatrix['outputMatrix'], 'matrixIn[0]')
                        handOffsetFKMultMatrix.connectPlugs(handFKJoint[f'worldMatrix[{handFKJoint.instanceNumber()}]'], 'matrixIn[1]')

                    if handOffsetFKInverseMatrix is None:

                        handOffsetFKInverseMatrixName = self.formatName(subname='WristOffset', kinemat='FK', type='inverseMatrix')
                        handOffsetFKInverseMatrix = self.scene.createNode('inverseMatrix', name=handOffsetFKInverseMatrixName)
                        handOffsetFKInverseMatrix.connectPlugs(handOffsetFKMultMatrix['matrixSum'], 'inputMatrix')

                    fingerTipIKMultMatrix.connectPlugs(handOffsetFKInverseMatrix['outputMatrix'], 'matrixIn[1]')
                    fingerTipIKMultMatrix.connectPlugs('matrixSum', fingerTipIKTarget['offsetParentMatrix'])

                else:

                    fingerTipIKMultMatrix.connectPlugs(handFKJoint[f'worldInverseMatrix[{handFKJoint.instanceNumber()}]'], 'matrixIn[1]')
                    fingerTipIKMultMatrix.connectPlugs('matrixSum', fingerTipIKTarget['offsetParentMatrix'])

                metacarpalIKJoint.addConstraint('aimConstraint', [metacarpalTipIKTarget], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=metacarpalTipIKTarget, maintainOffset=True)
                fingerIKJoint.addConstraint('aimConstraint', [fingerTipIKTarget], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=fingerTipIKTarget, maintainOffset=True)

            else:

                # Create kinematic metacarpal joints
                #
                jointTypes = (fullFingerName, f'{fullFingerName}Tip')
                kinematicTypes = ('FK', 'IK', 'Blend')
                fingerMatrices = (fingerBaseMatrix, fingerTipMatrix)

                fingerFKJoints = [None] * 2
                fingerIKJoints = [None] * 2
                fingerBlendJoints = [None] * 2
                fingerKinematics = (fingerFKJoints, fingerIKJoints, fingerBlendJoints)

                for (i, kinematicType) in enumerate(kinematicTypes):

                    for (j, jointType) in enumerate(jointTypes):

                        parent = fingerKinematics[i][j - 1] if (j > 0) else handJoints[i][0]

                        jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                        joint = self.scene.createNode('joint', name=jointName, parent=parent)
                        joint.displayLocalAxis = True
                        joint.segmentScaleCompensate = False
                        joint.setWorldMatrix(fingerMatrices[j])

                        fingerKinematics[i][j] = joint

                fingerFKJoint, fingerTipFKJoint = fingerFKJoints
                fingerIKJoint, fingerTipIKJoint = fingerIKJoints
                fingerBlendJoint, fingerTipBlendJoint = fingerBlendJoints

                fingerBlender = setuputils.createTransformBlends(fingerFKJoint, fingerIKJoint, fingerBlendJoint, blender=blender)
                fingerTipBlender = setuputils.createTransformBlends(fingerTipFKJoint, fingerTipIKJoint, fingerTipBlendJoint, blender=blender)

                fingerBlender.setName(self.formatName(subname=jointTypes[0], type='blendTransform'))
                fingerTipBlender.setName(self.formatName(subname=jointTypes[1], type='blendTransform'))

            # Create finger IK control
            #
            fingerIKSpaceName = self.formatName(subname=f'{fullFingerName}', kinemat='IK', type='space')
            fingerIKSpace = self.scene.createNode('transform', name=fingerIKSpaceName, parent=controlsGroup)
            fingerIKSpace.setWorldMatrix(fingerTipMatrix)
            fingerIKSpace.freezeTransform()
            fingerIKSpace.addConstraint('transformConstraint', [fingerTipBlendJoint])

            fingerIKCtrlName = self.formatName(subname=f'{fullFingerName}', kinemat='IK', type='control')
            fingerIKCtrl = self.scene.createNode('transform', name=fingerIKCtrlName, parent=fingerIKSpace)
            fingerIKCtrl.addStar(5.0 * rigScale, numPoints=12, normal=om.MVector.kZaxisVector, colorRGB=lightColorRGB)
            fingerIKCtrl.hideAttr('scale', lock=True)
            fingerIKCtrl.prepareChannelBoxForAnimation()
            self.publishNode(fingerIKCtrl, alias=f'{fullFingerName}_IK')

            aimVector = (-1.0, 0.0, 0.0) if requiresMirroring else (1.0, 0.0, 0.0)
            worldUpVector = (0.0, 0.0, -1.0) if requiresMirroring else (0.0, 0.0, 1.0)

            fingerIKTargetName = self.formatName(subname=f'{fullFingerName}', kinemat='IK', type='target')
            fingerIKTarget = self.scene.createNode('transform', name=fingerIKTargetName, parent=privateGroup)
            fingerIKTarget.displayLocalAxis = True
            fingerIKTarget.setWorldMatrix(fingerBaseMatrix)
            fingerIKTarget.freezeTransform()
            fingerIKTarget.addConstraint('pointConstraint', [fingerBlendJoint])
            fingerIKTarget.addConstraint('aimConstraint', [fingerIKCtrl], aimVector=aimVector, upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=worldUpVector, worldUpObject=fingerIKCtrl, maintainOffset=True)
            fingerIKTarget.addConstraint('scaleConstraint', [fingerBlendJoint])

            orientTarget = metacarpalBlendJoint if metacarpalEnabled else handBlendJoint

            fingerPinTargetName = self.formatName(subname=f'{fullFingerName}', kinemat='Pin', type='target')
            fingerPinTarget = self.scene.createNode('transform', name=fingerPinTargetName, parent=privateGroup)
            fingerPinTarget.displayLocalAxis = True
            fingerPinTarget.setWorldMatrix(fingerBaseMatrix)
            fingerPinTarget.freezeTransform()
            fingerPinTarget.addConstraint('pointConstraint', [fingerBlendJoint])
            fingerPinTarget.addConstraint('orientConstraint', [orientTarget], maintainOffset=True)
            fingerPinTarget.addConstraint('scaleConstraint', [fingerBlendJoint])

            # Create finger master control
            #
            masterFingerMatrix = mirrorMatrix * fingerBlendJoint.worldMatrix()

            masterFingerSpaceName = self.formatName(subname=fullFingerName, kinemat='Master', type='space')
            masterFingerSpace = self.scene.createNode('transform', name=masterFingerSpaceName, parent=controlsGroup)
            masterFingerSpace.setWorldMatrix(masterFingerMatrix)
            masterFingerSpace.freezeTransform()

            masterFingerCtrlName = self.formatName(subname=fullFingerName, kinemat='Master', type='control')
            masterFingerCtrl = self.scene.createNode('transform', name=masterFingerCtrlName, parent=masterFingerSpace)
            masterFingerCtrl.addPointHelper('square', size=(5.0 * rigScale), localScale=(1.0, 2.0, 0.25), colorRGB=lightColorRGB)
            masterFingerCtrl.addDivider('Settings')
            masterFingerCtrl.addProxyAttr('pin', knuckleRollCtrl['pin'])
            masterFingerCtrl.addDivider('Poses')
            masterFingerCtrl.addProxyAttr('curl', handCtrl['curl'])
            masterFingerCtrl.addProxyAttr('spread', handCtrl['spread'])
            masterFingerCtrl.addProxyAttr('splay', handCtrl['splay'])
            masterFingerCtrl.prepareChannelBoxForAnimation()
            self.publishNode(masterFingerCtrl, alias=f'{fullFingerName}_Master')

            masterFingerSpaceSwitch = masterFingerSpace.addSpaceSwitch([fingerIKTarget, fingerPinTarget], maintainOffset=True)
            masterFingerSpaceSwitch.weighted = True
            masterFingerSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            masterFingerSpaceSwitch.connectPlugs(knuckleRollCtrl['pin'], 'target[0].targetRotateWeight')
            masterFingerSpaceSwitch.connectPlugs(knuckleRollCtrl['pin'], 'target[1].targetRotateWeight')

            # Iterate through finger group
            #
            numFingers = len(fingerSpecs)
            fingerCtrls = [None] * numFingers

            for (i, fingerSpec) in enumerate(fingerSpecs):

                # Create finger control
                #
                fingerIndex = i + 1
                fingerExportJoint = self.scene(fingerSpec.uuid)
                fingerMatrix = fingerExportJoint.worldMatrix()
                fingerParent = fingerCtrls[i - 1] if (i > 0) else masterFingerCtrl
                fingerAlias = f'{fullFingerName}{str(fingerIndex).zfill(2)}'

                fingerCtrlName = self.formatName(subname=fullFingerName, index=fingerIndex, type='control')
                fingerCtrl = self.scene.createNode('transform', name=fingerCtrlName, parent=fingerParent)
                fingerCtrl.addPointHelper('disc', size=(5.0 * rigScale), localRotate=(0.0, 90.0, 0.0), side=componentSide)
                fingerCtrl.prepareChannelBoxForAnimation()
                self.publishNode(fingerCtrl, alias=fingerAlias)

                fingerCtrls[i] = fingerCtrl

                # Connect additives to finger control
                #
                fingerMatrix = (mirrorMatrix * fingerMatrix) * fingerCtrl.parentInverseMatrix()
                translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(fingerMatrix)

                fingerComposeMatrixName = self.formatName(subname=fullFingerName, index=fingerIndex, type='composeMatrix')
                fingerComposeMatrix = self.scene.createNode('composeMatrix', name=fingerComposeMatrixName)
                fingerComposeMatrix.setAttr('inputTranslate', translation)
                fingerComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)

                fingerArrayMathName = self.formatName(subname=fullFingerName, index=fingerIndex, type='arrayMath')
                fingerArrayMath = self.scene.createNode('arrayMath', name=fingerArrayMathName)

                if i > 0:

                    fingerArrayMath.connectPlugs(masterFingerCtrl['translateX'], 'inDistance[0].inDistanceX')
                    fingerArrayMath.connectPlugs(masterFingerCtrl['rotate'], 'inAngle[0]')

                fingerOffsetComposeMatrixName = self.formatName(subname=fullFingerName, index=fingerIndex, kinemat='Offset', type='composeMatrix')
                fingerOffsetComposeMatrix = self.scene.createNode('composeMatrix', name=fingerOffsetComposeMatrixName)
                fingerOffsetComposeMatrix.connectPlugs(fingerArrayMath['outDistance'], 'inputTranslate')
                fingerOffsetComposeMatrix.connectPlugs(fingerArrayMath['outAngle'], 'inputRotate')

                fingerMultMatrixName = self.formatName(subname=fullFingerName, index=fingerIndex, type='multMatrix')
                fingerMultMatrix = self.scene.createNode('multMatrix', name=fingerMultMatrixName)
                fingerMultMatrix.connectPlugs(fingerOffsetComposeMatrix['outputMatrix'], 'matrixIn[0]')
                fingerMultMatrix.connectPlugs(fingerComposeMatrix['outputMatrix'], 'matrixIn[1]')
                fingerMultMatrix.connectPlugs('matrixSum', fingerCtrl['offsetParentMatrix'])

                fingerCtrl.userProperties['type'] = fingerType
                fingerCtrl.userProperties['offset'] = fingerArrayMath.uuid()

            fingerTipTargetName = self.formatName(subname=f'{fullFingerName}Tip', type='target')
            fingerTipTarget = self.scene.createNode('transform', name=fingerTipTargetName, parent=fingerCtrls[-1])
            fingerTipTarget.displayLocalAxis = True
            fingerTipTarget.visibility = False
            fingerTipTarget.copyTransform(fingerTipExportJoint)
            fingerTipTarget.freezeTransform()

            # Connect pose drivers to finger offsets
            #
            for (i, fingerCtrl) in enumerate(fingerCtrls):

                # Connect curl driver
                #
                fingerArrayMath = self.scene(fingerCtrl.userProperties['offset'])
                fingerArrayMath.connectPlugs(handCtrl['curl'], 'inAngle[1].inAngleZ')

                # Connect spread driver
                #
                if i == 0 and fingerType != FingerType.THUMB:

                    if fingerType == FingerType.INDEX:

                        fingerHalfSpread.connectPlugs('outAngle', fingerArrayMath['inAngle[2].inAngleY'])

                    elif fingerType == FingerType.MIDDLE:

                        pass

                    elif fingerType == FingerType.RING:

                        fingerNegateHalfSpread.connectPlugs('outAngle', fingerArrayMath['inAngle[2].inAngleY'])

                    else:

                        fingerNegateSpread.connectPlugs('outAngle', fingerArrayMath['inAngle[2].inAngleY'])

                # Connect splay driver
                #
                if i == 0 and fingerType != FingerType.THUMB:

                    if fingerType == FingerType.INDEX:

                        fingerNegateSplay.connectPlugs('outAngle', fingerArrayMath['inAngle[2].inAngleZ'])

                    elif fingerType == FingerType.MIDDLE:

                        fingerNegateHalfSplay.connectPlugs('outAngle', fingerArrayMath['inAngle[2].inAngleZ'])

                    elif fingerType == FingerType.RING:

                        fingerHalfSplay.connectPlugs('outAngle', fingerArrayMath['inAngle[2].inAngleZ'])

                    else:

                        handCtrl.connectPlugs('splay', fingerArrayMath['inAngle[2].inAngleZ'])

            # Tag finger controls
            #
            lastFingerIndex = len(fingerCtrls) - 1

            if metacarpalEnabled:

                metacarpalCtrl.tagAsController(parent=handCtrl, children=[masterFingerCtrl])
                masterFingerCtrl.tagAsController(parent=metacarpalCtrl, children=[fingerCtrls[0]])

            else:

                masterFingerCtrl.tagAsController(parent=handCtrl, children=[fingerCtrls[0]])

            for (i, fingerCtrl) in enumerate(fingerCtrls):

                parent = fingerCtrls[i - 1] if (i > 0) else masterFingerCtrl
                child = fingerCtrls[i + 1] if (i < lastFingerIndex) else fingerIKCtrl

                fingerCtrl.tagAsController(parent=parent, children=[child])

        # Constrain inbetween metacarpal controls
        #
        fingerMetacarpalCtrls = [metacarpalCtrl for metacarpalCtrl in metacarpalCtrls if metacarpalCtrl.userProperties['type'] != self.FingerType.THUMB]
        numFingerMetacarpalCtrls = len(fingerMetacarpalCtrls)

        if numFingerMetacarpalCtrls > 2:

            firstMetacarpalCtrl = fingerMetacarpalCtrls[0]
            lastMetacarpalCtrl = fingerMetacarpalCtrls[-1]
            inbetweenMetacarpalCtrls = fingerMetacarpalCtrls[1:-1]

            metacarpalScaleRemapName = self.formatName(subname='Metacarpal', kinemat='Scale', type='remapArray')
            metacarpalScaleRemap = self.scene.createNode('remapArray', name=metacarpalScaleRemapName)
            metacarpalScaleRemap.clamped = True
            metacarpalScaleRemap.connectPlugs(firstMetacarpalCtrl['scale'], 'outputMin')
            metacarpalScaleRemap.connectPlugs(lastMetacarpalCtrl['scale'], 'outputMax')

            for (i, metacarpalCtrl) in enumerate(inbetweenMetacarpalCtrls):

                metacarpalSpace = self.scene(metacarpalCtrl.userProperties['space'])
                weight = float(i + 1) / float(numFingerMetacarpalCtrls - 1)

                pointConstraint = metacarpalSpace.addConstraint('pointConstraint', [firstMetacarpalCtrl, lastMetacarpalCtrl])
                pointTargets = pointConstraint.targets()

                pointConstraint.setAttr(pointTargets[0].driver(), 1.0 - weight)
                pointConstraint.setAttr(pointTargets[1].driver(), weight)
                pointConstraint.maintainOffset()

                orientConstraint = metacarpalSpace.addConstraint('orientConstraint', [firstMetacarpalCtrl, lastMetacarpalCtrl])
                orientTargets = orientConstraint.targets()

                orientConstraint.setAttr(orientTargets[0].driver(), 1.0 - weight)
                orientConstraint.setAttr(orientTargets[1].driver(), weight)
                orientConstraint.maintainOffset()

                metacarpalScaleRemap.setAttr(f'parameter[{i}]', weight)
                metacarpalScaleRemap.connectPlugs(f'outValue[{i}]', metacarpalSpace['scale'])

        # Override end-matrix on parent limb's twist solver
        #
        twistSolver = self.scene(limbComponent.userProperties['twistSolvers'][-1])
        rotateMatrix = transformutils.createRotationMatrix([-90.0 * mirrorSign, 0.0, 0.0])
        offsetMatrix = rotateMatrix * (handExportJoint.worldMatrix() * handCtrl.worldInverseMatrix())

        self.overrideLimbTwist(handCtrl, twistSolver, offsetMatrix=offsetMatrix)

        # Override end-value on parent limb's scale remapper
        #
        scaleRemapper = self.scene(limbComponent.userProperties['scaleRemappers'][-1])
        self.overrideLimbRemapper(handCtrl, scaleRemapper)

        # Override local space on parent limb's extremity-in control
        #
        hingeCtrl = self.scene(limbComponent.userProperties['hingeControl'])
        otherHandles = hingeCtrl.userProperties.get('otherHandles', [])

        hasOtherHandles = len(otherHandles) == 2

        if hasOtherHandles:

            self.overrideLimbHandle(handCtrl, self.scene(otherHandles[-1]))

        # Tag hand controls
        #
        handCtrl.tagAsController(children=metacarpalCtrls)
        knuckleRollCtrl.tagAsController(parent=handCtrl)

    def buildPartialRig(self):
        """
        Builds a partial control rig for this component.

        :rtype: None
        """

        raise NotImplementedError()

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        rollEnabled = bool(self.rollEnabled)

        if rollEnabled:

            self.buildFullRig()

        else:

            self.buildPartialRig()
    # endregion
