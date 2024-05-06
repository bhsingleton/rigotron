from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import transformutils, shapeutils
from rigomatic.libs import kinematicutils
from . import extremitycomponent
from ..libs import Side, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FootType(IntEnum):
    """
    Collection of all available foot subtypes.
    """

    FOOT = 0
    BALL = 1
    TOES = 2


class FootPivotType(IntEnum):
    """
    Collection of all available foot pivots.
    """

    HEEL = 0
    INSIDE = 1
    OUTSIDE = 2
    TIP = 3


class ToeType(IntEnum):
    """
    Collection of all available toe appendages.
    """

    BIG = 0
    LONG = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4


class FootComponent(extremitycomponent.ExtremityComponent):
    """
    Overload of `ExtremityComponent` that implements foot components.
    """

    # region Enums
    FootType = FootType
    FootPivotType = FootPivotType
    ToeType = ToeType
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Foot'
    __default_component_matrices__ = {
        Side.LEFT: {
            FootType.FOOT: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, 0.0, 10.0, 1.0)
                ]
            ),
            FootType.BALL: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, -10.0, 5.0, 1.0)
                ]
            ),
            FootType.TOES: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, -10.0, 5.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            FootType.FOOT: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, 0.0, 10.0, 1.0)
                ]
            ),
            FootType.BALL: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, -10.0, 5.0, 1.0)
                ]
            ),
            FootType.TOES: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, -10.0, 5.0, 1.0)
                ]
            )
        }
    }
    __default_pivot_matrices__ = {
        Side.LEFT: {
            FootPivotType.HEEL: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (20.0, 20.0, 0.0, 1.0)
                ]
            ),
            FootPivotType.INSIDE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 0.0, 1.0)
                ]
            ),
            FootPivotType.OUTSIDE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (30.0, 0.0, 0.0, 1.0)
                ]
            ),
            FootPivotType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (20.0, -20.0, 0.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            FootPivotType.HEEL: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-20.0, 20.0, 0.0, 1.0)
                ]
            ),
            FootPivotType.INSIDE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-10.0, 0.0, 0.0, 1.0)
                ]
            ),
            FootPivotType.OUTSIDE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-30.0, 0.0, 0.0, 1.0)
                ]
            ),
            FootPivotType.TIP: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (-20.0, -20.0, 0.0, 1.0)
                ]
            )
        }
    }
    __default_digit_name__ = 'Toe'
    __default_digit_types__ = ('Big', 'Long', 'Middle', 'Ring', 'Pinky')
    __default_digit_spacing__ = 5.0
    __default_digit_matrices__ = {
        Side.LEFT: {
            ToeType.BIG: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (10.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.LONG: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (15.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.MIDDLE: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.RING: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (25.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.PINKY: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (30.0, -15.0, 5.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            ToeType.BIG: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-10.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.LONG: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-15.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.MIDDLE: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.RING: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-25.0, -15.0, 5.0, 1.0)
                ]
            ),
            ToeType.PINKY: om.MMatrix(
                [
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-30.0, -15.0, 5.0, 1.0)
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
    bigToeEnabled = mpyattribute.MPyAttribute('bigToeEnabled', attributeType='bool', default=True)
    numBigToeLinks = mpyattribute.MPyAttribute('bigToeLinks', attributeType='int', min=1, max=3, default=2)
    numToes = mpyattribute.MPyAttribute('numToes', attributeType='int', min=1, max=4, default=4)
    numToeLinks = mpyattribute.MPyAttribute('numToeLinks', attributeType='int', min=1, max=3, default=3)
    # endregion

    # region Methods
    def toeFlags(self):
        """
        Returns the enabled flags for each toe.

        :rtype: Dict[ToeType, bool]
        """

        bigToeEnabled = self.bigToeEnabled
        numToes = self.numToes

        if numToes == 1:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: True, ToeType.MIDDLE: False, ToeType.RING: False, ToeType.PINKY: False}

        elif numToes == 2:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: True, ToeType.MIDDLE: False, ToeType.RING: False, ToeType.PINKY: True}

        elif numToes == 3:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: True, ToeType.MIDDLE: True, ToeType.RING: False, ToeType.PINKY: True}

        else:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: True, ToeType.MIDDLE: True, ToeType.RING: True, ToeType.PINKY: True}

    def invalidatePivotSpecs(self, pivotSpecs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: None
        """

        # Concatenate pivot names
        #
        pivotTypes = self.FootPivotType.__members__
        numPivotTypes = len(pivotTypes)

        pivotSpecs = self.resizePivotSpecs(numPivotTypes, pivotSpecs)

        for (name, i) in pivotTypes.items():

            pivotSpecs[i].name = self.formatName(subname=name.title(), type='locator')

        # Call parent method
        #
        super(FootComponent, self).invalidatePivotSpecs(pivotSpecs)

    def buildPivots(self):
        """
        Builds the pivots for this component.

        :rtype: Union[Tuple[mpynode.MPyNode], None]
        """

        # Iterate through default pivots
        #
        pivotSpecs = self.pivotSpecs()
        side = self.Side(self.componentSide)

        for (i, pivotSpec) in enumerate(pivotSpecs):

            pivot = self.scene.createNode('transform', name=pivotSpec.name)
            pivot.addPointHelper('cross', 'axisTripod', size=5.0)
            pivotSpec.uuid = pivot.uuid()

            matrix = pivotSpec.getMatrix(default=self.__default_pivot_matrices__[side][i])
            pivotSpec.setWorldMatrix(matrix)

    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        size = len(self.FootType)
        footSpec, ballSpec, toesSpec = self.resizeSkeletonSpecs(size, skeletonSpecs)

        # Edit skeleton specs
        #
        footSpec.name = self.formatName()
        footSpec.driver = self.formatName(type='control')

        ballSpec.name = self.formatName(subname='Ball')
        ballSpec.driver = self.formatName(subname='Ball', type='control')
        ballSpec.enabled = (self.numToes > 1) or self.bigToeEnabled

        toesSpec.name = self.formatName(subname='Toes')
        toesSpec.driver = self.formatName(subname='Toes', type='control')
        toesSpec.enabled = not ballSpec.enabled

        # Check if toe spec groups exist
        #
        toeGroups = ballSpec.groups
        numToeGroups = len(toeGroups)

        toeMembers = self.ToeType.__members__
        numToeMembers = len(toeMembers)

        if numToeGroups != numToeMembers:

            toeGroups.update([(i, []) for i in range(numToeMembers)])

        # Iterate through toe spec groups
        #
        toeFlags = self.toeFlags()

        for (i, toeLinks) in toeGroups.items():

            # Iterate through digit specs
            #
            toeType = self.ToeType(i)
            toeName = toeType.name.title()

            numToeLinks = self.numBigToeLinks if (toeType == ToeType.BIG) else self.numToeLinks
            toeLinkSpecs = self.resizeSkeletonSpecs(numToeLinks, toeLinks)

            for (j, toeLinkSpec) in enumerate(toeLinkSpecs, start=1):

                toeLinkSpec.name = self.formatName(subname=f'{toeName}Toe', index=j)
                toeLinkSpec.driver = self.formatName(subname=f'{toeName}Toe', index=j, type='control')
                toeLinkSpec.enabled = toeFlags.get(toeType, False)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        footSpec, ballSpec, toesSpec = self.skeletonSpecs()
        side = self.Side(self.componentSide)

        # Create foot joint
        #
        footJoint = self.scene.createNode('joint', name=footSpec.name)
        footJoint.side = side
        footJoint.type = self.Type.FOOT
        footSpec.uuid = footJoint.uuid()

        footMatrix = footSpec.getMatrix(default=self.__default_component_matrices__[side][FootType.FOOT])
        footJoint.setWorldMatrix(footMatrix)

        # Check if ball joint is enabled
        #
        if ballSpec.enabled:

            # Create ball joint
            #
            ballJoint = self.scene.createNode('joint', name=ballSpec.name, parent=footJoint)
            ballJoint.side = side
            ballJoint.type = self.Type.NONE
            ballSpec.uuid = ballJoint.uuid()

            ballMatrix = ballSpec.getMatrix(self.__default_component_matrices__[side][FootType.BALL])
            ballJoint.setWorldMatrix(ballMatrix)

            # Create toe joints
            #
            toeGroups = ballSpec.groups
            jointTypes = (self.Type.BIG_TOE, self.Type.INDEX_TOE, self.Type.MIDDLE_TOE, self.Type.RING_TOE, self.Type.PINKY_TOE)

            toeJoints = []

            for (i, toeLinkSpecs) in toeGroups.items():

                # Check if toe is enabled
                #
                toeType = self.ToeType(i)
                isEnabled = toeLinkSpecs[0].enabled

                if not isEnabled:

                    continue

                # Create toe joints
                #
                numToeLinks = len(toeLinkSpecs)
                toeLinks = [None] * numToeLinks

                defaultToeMatrix = self.__default_digit_matrices__[side][toeType]

                for (j, toeLinkSpec) in enumerate(toeLinkSpecs):

                    # Create toe-link
                    #
                    parent = toeLinks[j - 1] if (j > 0) else ballJoint
                    toeLink = self.scene.createNode('joint', name=toeLinkSpec.name, parent=parent)
                    toeLink.side = side
                    toeLink.type = jointTypes[i]
                    toeLinkSpec.uuid = toeLink.uuid()

                    defaultToeLinkMatrix = transformutils.createTranslateMatrix([(self.__default_digit_spacing__ * j), 0.0, 0.0]) * defaultToeMatrix
                    toeLinkMatrix = toeLinkSpec.getMatrix(default=defaultToeLinkMatrix)
                    toeLink.setWorldMatrix(toeLinkMatrix)

                    toeLinks[j] = toeLink

                toeJoints.append(toeLinks)

            return (footJoint, ballJoint, *toeJoints)

        else:

            # Create toe joint
            #
            toeJoint = self.scene.createNode('joint', name=toesSpec.name, parent=footJoint)
            toeJoint.side = side
            toeJoint.type = self.Type.NONE
            toesSpec.uuid = toeJoint.uuid()

            toeMatrix = toesSpec.getMatrix(self.__default_component_matrices__[side][FootType.TOES])
            toeJoint.setWorldMatrix(toeMatrix)

            return (footJoint, toeJoint)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Get skeleton matrices
        #
        footSpec, ballSpec, toesSpec = self.skeletonSpecs()
        footExportJoint = footSpec.getNode()
        ballExportJoint = ballSpec.getNode() if ballSpec.enabled else toesSpec.getNode()

        heelSpec, insideSpec, outsideSpec, tipSpec = self.pivotSpecs()
        heelPoint = om.MVector(transformutils.breakMatrix(heelSpec.matrix)[3])
        insidePoint = om.MVector(transformutils.breakMatrix(insideSpec.matrix)[3])
        outsidePoint = om.MVector(transformutils.breakMatrix(outsideSpec.matrix)[3])
        toeTipPoint = om.MVector(transformutils.breakMatrix(tipSpec.matrix)[3])

        footMatrix = footExportJoint.worldMatrix()
        ballMatrix = ballExportJoint.worldMatrix()
        heelMatrix = transformutils.createRotationMatrix(footMatrix) * transformutils.createTranslateMatrix(heelPoint)
        insideMatrix = transformutils.createRotationMatrix(footMatrix) * transformutils.createTranslateMatrix(insidePoint)
        outsideMatrix = transformutils.createRotationMatrix(footMatrix) * transformutils.createTranslateMatrix(outsidePoint)
        toeTipMatrix = transformutils.createRotationMatrix(ballMatrix) * transformutils.createTranslateMatrix(toeTipPoint)
        rollMatrix = transformutils.createRotationMatrix(footMatrix) * transformutils.createTranslateMatrix(ballMatrix)

        footLength = om.MPoint(heelPoint).distanceTo(om.MPoint(toeTipPoint))
        footWidth = om.MPoint(insidePoint).distanceTo(om.MPoint(outsidePoint))
        groundPoint = (heelPoint * 0.25) + (insidePoint * 0.25) + (outsidePoint * 0.25) + (toeTipPoint * 0.25)

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        requiresMirroring = (componentSide == self.Side.RIGHT)
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        # Get component dependencies
        #
        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        limbComponents = self.findComponentAncestors('LimbComponent')
        hasLimbComponent = len(limbComponents) == 1

        toesTarget = None

        if hasLimbComponent:

            # Get required limb nodes
            #
            limbComponent = limbComponents[0]

            limbCtrl = self.scene(limbComponent.userProperties['ikControls'][0])
            limbFKCtrl = self.scene(limbComponent.userProperties['fkControls'][-1])
            limbIKCtrl = self.scene(limbComponent.userProperties['ikControls'][-1])
            limbIKOffset = self.scene(limbIKCtrl.userProperties['offset'])
            limbIKJoint = self.scene(limbComponent.userProperties['ikJoints'][-1])
            limbIKTarget = self.scene(limbComponent.userProperties['ikTarget'])

            # Create foot control
            #
            footCtrlMatrix = mirrorMatrix * footMatrix
            localPosition = om.MPoint(groundPoint) * footCtrlMatrix.inverse()
            upperLimbName, lowerLimbName, limbTipName = limbComponent.__default_limb_names__
            upperLimbAttr = f'{upperLimbName.lower()}Length'
            lowerLimbAttr = f'{lowerLimbName.lower()}Length'

            footSpaceName = self.formatName(type='space')
            footSpace = self.scene.createNode('transform', name=footSpaceName, parent=controlsGroup)
            footSpace.setWorldMatrix(footCtrlMatrix)
            footSpace.freezeTransform()

            footCtrlName = self.formatName(type='control')
            footCtrl = self.scene.createNode('transform', name=footCtrlName, parent=footSpace)
            footCtrl.addPointHelper('square', size=1.0, localPosition=localPosition, localScale=(1.0, footLength, footWidth), lineWidth=3.0, colorRGB=colorRGB)
            footCtrl.addDivider('Settings')
            footCtrl.addProxyAttr('mode', limbCtrl['mode'])
            footCtrl.addProxyAttr(upperLimbAttr, limbCtrl[upperLimbAttr])
            footCtrl.addProxyAttr(lowerLimbAttr, limbCtrl[lowerLimbAttr])
            footCtrl.addProxyAttr('stretch', limbCtrl['stretch'])
            footCtrl.addProxyAttr('pin', limbCtrl['pin'])
            footCtrl.addProxyAttr('soften', limbCtrl['soften'])
            footCtrl.addProxyAttr('twist', limbCtrl['twist'])
            footCtrl.addProxyAttr('displayTwist', limbCtrl['displayTwist'])
            footCtrl.addDivider('Spaces')
            footCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            self.publishNode(footCtrl, alias='Foot')

            footSpaceSwitch = footSpace.addSpaceSwitch([limbFKCtrl, limbIKOffset, motionCtrl], maintainOffset=True)
            footSpaceSwitch.weighted = True
            footSpaceSwitch.setAttr('target', [{'targetReverse': (True, True, True)}, {}, {'targetWeight': (0.0, 0.0, 0.0)}])
            footSpaceSwitch.connectPlugs(footCtrl['mode'], 'target[0].targetWeight')
            footSpaceSwitch.connectPlugs(footCtrl['mode'], 'target[1].targetWeight')
            footSpaceSwitch.connectPlugs(footCtrl['localOrGlobal'], 'target[2].targetRotateWeight')

            # Override extremity-in control space
            #
            hingeCtrl = self.scene(limbComponent.userProperties['hingeControl'])
            otherHandles = hingeCtrl.userProperties.get('otherHandles', [])

            hasOtherHandles = len(otherHandles) == 2

            if hasOtherHandles:

                extremityInCtrl = self.scene(otherHandles[-1])

                extremityInSpace = self.scene(extremityInCtrl.userProperties['space'])
                extremityInSpace.removeConstraints()

                localCtrl = self.scene(limbComponent.userProperties['targetJoints'][-1])
                insetNegate = self.scene(extremityInCtrl.userProperties['negate'])

                extremityInSpaceSwitch = extremityInSpace.addSpaceSwitch([localCtrl, footCtrl], maintainOffset=False)
                extremityInSpaceSwitch.weighted = True
                extremityInSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                extremityInSpaceSwitch.connectPlugs(extremityInCtrl['localOrGlobal'], 'target[0].targetWeight')
                extremityInSpaceSwitch.connectPlugs(extremityInCtrl['localOrGlobal'], 'target[1].targetWeight')
                extremityInSpaceSwitch.connectPlugs(insetNegate['outDistance'], 'target[0].targetOffsetTranslateX')
                extremityInSpaceSwitch.connectPlugs(insetNegate['outDistance'], 'target[1].targetOffsetTranslateX')

            # Create kinematic foot joints
            #
            jointTypes = ('Ankle', 'Ball', 'ToeTip')
            kinematicTypes = ('FK', 'IK', 'Blend')

            footFKJoints = [None] * 3
            footIKJoints = [None] * 3
            footBlendJoints = [None] * 3
            footMatrices = (footMatrix, ballMatrix, toeTipMatrix)
            kinematicJoints = (footFKJoints, footIKJoints, footBlendJoints)

            for (i, kinematicType) in enumerate(kinematicTypes):

                for (j, jointType) in enumerate(jointTypes):

                    parent = kinematicJoints[i][j - 1] if (j > 0) else jointsGroup

                    jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                    joint = self.scene.createNode('joint', name=jointName, parent=parent)
                    joint.segmentScaleCompensate = False
                    joint.displayLocalAxis = True
                    joint.setWorldMatrix(footMatrices[j])

                    kinematicJoints[i][j] = joint

            footFKJoint, ballFKJoint, toeTipFKJoint = footFKJoints
            footIKJoint, ballIKJoint, toeTipIKJoint = footIKJoints
            footBlendJoint, ballBlendJoint, toeTipBlendJoint = footBlendJoints

            blender = footCtrl['mode']
            footBlender = setuputils.createTransformBlends(footFKJoint, footIKJoint, footBlendJoint, blender=blender)
            ballBlender = setuputils.createTransformBlends(ballFKJoint, ballIKJoint, ballBlendJoint, blender=blender)
            toeTipBlender = setuputils.createTransformBlends(toeTipFKJoint, toeTipIKJoint, toeTipBlendJoint, blender=blender)

            footBlender.setName(self.formatName(subname=jointTypes[0], type='blendTransform'))
            ballBlender.setName(self.formatName(subname=jointTypes[1], type='blendTransform'))
            toeTipBlender.setName(self.formatName(subname=jointTypes[2], type='blendTransform'))

            # Constrain foot FK joints
            #
            footFKJoint.addConstraint('transformConstraint', [footCtrl], maintainOffset=requiresMirroring)

            # Create foot roll controls
            #
            outsideFootCtrlName = self.formatName(subname='Outside', type='control')
            outsideFootCtrl = self.scene.createNode('transform', name=outsideFootCtrlName, parent=footCtrl)
            outsideFootCtrl.addPointHelper('triangle', size=15.0, localRotate=(90.0, -90.0 * mirrorSign, 0.0), colorRGB=lightColorRGB)
            outsideFootCtrl.setWorldMatrix(outsideMatrix, skipRotate=True, skipScale=True)
            outsideFootCtrl.freezeTransform()
            outsideFootCtrl.prepareChannelBoxForAnimation()
            self.publishNode(outsideFootCtrl, alias='Outside')

            insideFootCtrlName = self.formatName(subname='Inside', type='control')
            insideFootCtrl = self.scene.createNode('transform', name=insideFootCtrlName, parent=outsideFootCtrl)
            insideFootCtrl.addPointHelper('triangle', size=15.0, localRotate=(90.0, 90.0 * mirrorSign, 0.0), colorRGB=lightColorRGB)
            insideFootCtrl.setWorldMatrix(insideMatrix, skipRotate=True, skipScale=True)
            insideFootCtrl.freezeTransform()
            insideFootCtrl.prepareChannelBoxForAnimation()
            self.publishNode(insideFootCtrl, alias='Inside')

            heelRollCtrlName = self.formatName(subname='Heel', type='control')
            heelRollCtrl = self.scene.createNode('transform', name=heelRollCtrlName, parent=insideFootCtrl)
            heelRollCtrl.addPointHelper('triangle', size=15.0, localRotate=(0.0, 0.0, 90.0 * mirrorSign), colorRGB=lightColorRGB)
            heelRollCtrl.setWorldMatrix(heelMatrix, skipRotate=True, skipScale=True)
            heelRollCtrl.freezeTransform()
            heelRollCtrl.prepareChannelBoxForAnimation()
            self.publishNode(heelRollCtrl, alias='Heel')

            toeRollCtrlName = self.formatName(subname='ToeTip', type='control')
            toeRollCtrl = self.scene.createNode('transform', name=toeRollCtrlName, parent=heelRollCtrl)
            toeRollCtrl.addPointHelper('triangle', size=15.0, localRotate=(0.0, 0.0, -90.0 * mirrorSign), colorRGB=lightColorRGB)
            toeRollCtrl.setWorldMatrix(toeTipMatrix, skipRotate=True, skipScale=True)
            toeRollCtrl.freezeTransform()
            toeRollCtrl.prepareChannelBoxForAnimation()
            self.publishNode(toeRollCtrl, alias='ToeTip')

            ballRollCtrlMatrix = mirrorMatrix * rollMatrix
            footPoint = transformutils.breakMatrix(footMatrix)[3]
            footDot = self.scene.upVector * om.MVector(footPoint)
            localPosition = om.MPoint(heelPoint + (self.scene.upVector * footDot)) * ballRollCtrlMatrix.inverse()

            ballRollCtrlName = self.formatName(subname='Ball', type='control')
            ballRollCtrl = self.scene.createNode('transform', name=ballRollCtrlName, parent=toeRollCtrl)
            ballRollCtrl.addPointHelper('tearDrop', size=10.0, localPosition=localPosition, localRotate=(45.0 * mirrorSign, 90.0 * mirrorSign, 0.0), colorRGB=lightColorRGB)
            ballRollCtrl.setWorldMatrix(ballMatrix, skipRotate=True, skipScale=True)
            ballRollCtrl.freezeTransform()
            ballRollCtrl.prepareChannelBoxForAnimation()
            self.publishNode(ballRollCtrl, alias='Ball')

            limbIKTarget.setParent(ballRollCtrl, absolute=True)
            limbIKTarget.freezeTransform()

            # Apply single-chain solver to IK joints
            #
            footIKHandle, footIKEffector = kinematicutils.applySingleChainSolver(footIKJoint, ballIKJoint)
            footIKHandle.setName(self.formatName(type='ikHandle'))
            footIKHandle.setParent(privateGroup)
            footIKHandle.addConstraint('transformConstraint', [ballRollCtrl], maintainOffset=True)
            footIKEffector.setName(self.formatName(type='ikEffector'))

            ballIKHandle, ballIKEffector = kinematicutils.applySingleChainSolver(ballIKJoint, toeTipIKJoint)
            ballIKHandle.setName(self.formatName(subname='Ball', type='ikHandle'))
            ballIKHandle.setParent(privateGroup)
            ballIKHandle.addConstraint('transformConstraint', [toeRollCtrl], maintainOffset=True)
            ballIKEffector.setName(self.formatName(subname='Ball', type='ikEffector'))

            footIKJoint.addConstraint('pointConstraint', [limbIKJoint])
            footIKJoint.addConstraint('scaleConstraint', [footCtrl])

            # Add foot space to limb's pole-vector control
            #
            limbPVCtrl = self.scene(limbComponent.userProperties['pvControl'])
            self.overrideLimbPVSpace(footCtrl, limbPVCtrl)

            # Override end-matrix on limb's twist solver
            #
            twistSolver = self.scene(limbComponent.userProperties['twistSolvers'][-1])
            self.overrideLimbTwist(footCtrl, footExportJoint, twistSolver)

            # Connect visibility
            #
            footCtrl.connectPlugs('mode', heelRollCtrl['visibility'])
            footCtrl.connectPlugs('mode', ballRollCtrl['visibility'])
            footCtrl.connectPlugs('mode', toeRollCtrl['visibility'])
            footCtrl.connectPlugs('mode', insideFootCtrl['visibility'])
            footCtrl.connectPlugs('mode', outsideFootCtrl['visibility'])

            # Constrain remaining joints
            #
            footExportJoint.addConstraint('transformConstraint', [footBlendJoints[0]])
            ballExportJoint.addConstraint('transformConstraint', [footBlendJoints[1]])

            toesTarget = footBlendJoints[1]

        else:

            raise NotImplementedError('buildComponent() limbless foot components have not been implemented!')

        # Create toes control
        #
        toesMatrix = mirrorMatrix * toesTarget.worldMatrix()

        toesSpaceName = self.formatName(subname='Toes', type='space')
        toesSpace = self.scene.createNode('transform', name=toesSpaceName, parent=controlsGroup)
        toesSpace.setWorldMatrix(toesMatrix)
        toesSpace.freezeTransform()
        toesSpace.addConstraint('transformConstraint', [toesTarget], maintainOffset=requiresMirroring)

        toesCtrlName = self.formatName(subname='Toes', type='control')
        toesCtrl = self.scene.createNode('transform', name=toesCtrlName, parent=toesSpace)
        toesCtrl.addPointHelper('square', size=1.0, localScale=(1.0, (footWidth * 0.5), footWidth), colorRGB=colorRGB)
        toesCtrl.addDivider('Settings')
        toesCtrl.addProxyAttr('mode', limbCtrl['mode'])
        toesCtrl.addProxyAttr('thighLength', limbCtrl['thighLength'])
        toesCtrl.addProxyAttr('calfLength', limbCtrl['calfLength'])
        toesCtrl.addProxyAttr('stretch', limbCtrl['stretch'])
        toesCtrl.addProxyAttr('pin', limbCtrl['pin'])
        toesCtrl.addProxyAttr('soften', limbCtrl['soften'])
        toesCtrl.addProxyAttr('twist', limbCtrl['twist'])
        self.publishNode(toesCtrl, alias='Toes')

        if ballSpec.enabled:

            # Iterate through toe groups
            #
            for (toeType, toeGroup) in ballSpec.groups.items():

                # Check if toe group is enabled
                #
                toeSpec = toeGroup[0]

                if not toeSpec.enabled:

                    continue

                # Create toe master control
                #
                toeType = self.ToeType(toeType)
                toeName = toeType.name.title()
                toeJoint = self.scene(toeSpec.uuid)

                masterToeCtrlName = self.formatName(subname=f'{toeName}Toe', type='control')
                masterToeCtrl = self.scene.createNode('transform', name=masterToeCtrlName, parent=toesCtrl)
                masterToeCtrl.addPointHelper('square', size=5, localScale=(1.0, 2.0, 0.25))
                masterToeCtrl.copyTransform(toeJoint)
                masterToeCtrl.freezeTransform()

                # Iterate through toe group
                #
                numToeLinks = len(toeGroup)
                toeCtrls = [None] * numToeLinks

                for (i, toeLinkSpec) in enumerate(toeGroup):

                    # Create toe control
                    #
                    toeIndex = i + 1
                    toeJoint = self.scene(toeLinkSpec.uuid)
                    toeParent = toeCtrls[i - 1] if (i > 0) else masterToeCtrl

                    toeCtrlName = self.formatName(subname=f'{toeName}Toe', index=toeIndex, type='control')
                    toeCtrl = self.scene.createNode('transform', name=toeCtrlName, parent=toeParent)
                    toeCtrl.addPointHelper('disc', size=5, localRotate=(0.0, 90.0, 0.0), side=componentSide)
                    self.publishNode(toeCtrl, alias=f'{toeName}Toe{str(i + 1).zfill(2)}')

                    toeCtrls[i] = toeCtrl

                    # Connect additives to toe control
                    #
                    matrix = toeJoint.worldMatrix() * toeCtrl.parentInverseMatrix()
                    translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(matrix)

                    arrayMathName = self.formatName(subname=f'{toeName}Toe', index=toeIndex, type='arrayMath')
                    arrayMath = self.scene.createNode('arrayMath', name=arrayMathName)
                    arrayMath.setAttr('inDistance[0]', translation)
                    arrayMath.setAttr('inAngle[0]', eulerRotation, convertUnits=False)

                    if i > 0:

                        arrayMath.connectPlugs(masterToeCtrl['translateX'], 'inDistance[1].inDistanceX')
                        arrayMath.connectPlugs(masterToeCtrl['rotate'], 'inAngle[1]')

                    composeMatrixName = self.formatName(subname=f'{toeName}Toe', index=toeIndex, type='composeMatrix')
                    composeMatrix = self.scene.createNode('composeMatrix', name=composeMatrixName)
                    composeMatrix.connectPlugs(arrayMath['outDistance'], 'inputTranslate')
                    composeMatrix.connectPlugs(arrayMath['outAngle'], 'inputRotate')
                    composeMatrix.connectPlugs('outputMatrix', toeCtrl['offsetParentMatrix'])

                    # Constrain toe joint
                    #
                    toeJoint.addConstraint('transformConstraint', [toeCtrl])

        else:

            # Constrain toes joint
            #
            ballExportJoint.addConstraint('transformConstraint', [toesCtrl])
    # endregion
