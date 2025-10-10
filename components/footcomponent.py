import json

from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.dataclasses.colour import Colour
from dcc.python import stringutils
from dcc.maya.libs import transformutils, shapeutils
from dcc.maya.json import mshapeparser
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
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (5.0, -10.0, 0.0, 1.0)
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
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (5.0, -10.0, 0.0, 1.0)
                ]
            )
        }
    }
    __default_pivot_points__ = [
        (0.0, -10.0, 0.0),
        (0.0, -10.0, -5.0),
        (0.0, 0.0, -5.0),
        (0.0, 10.0, -5.0),
        (0.0, 10.0, 0.0),
        (0.0, 10.0, 5.0),
        (0.0, 0.0, 5.0),
        (0.0, -10.0, 5.0)
    ]
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
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, -10.0, 1.0)
                ]
            ),
            ToeType.LONG: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, -5.0, 1.0)
                ]
            ),
            ToeType.MIDDLE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 0.0, 1.0)
                ]
            ),
            ToeType.RING: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 5.0, 1.0)
                ]
            ),
            ToeType.PINKY: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 10.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            ToeType.BIG: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 10.0, 1.0)
                ]
            ),
            ToeType.LONG: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 5.0, 1.0)
                ]
            ),
            ToeType.MIDDLE: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, 0.0, 1.0)
                ]
            ),
            ToeType.RING: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, -5.0, 1.0)
                ]
            ),
            ToeType.PINKY: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 0.0, -10.0, 1.0)
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

    @bigToeEnabled.changed
    def bigToeEnabled(self, bigToeEnabled):
        """
        Changed method that notifies any big-toe state changes.

        :type bigToeEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numBigToeLinks.changed
    def numBigToeLinks(self, numBigToeLinks):
        """
        Changed method that notifies any big-toe link size changes.

        :type numBigToeLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()

    @numToes.changed
    def numToes(self, numToes):
        """
        Changed method that notifies any toe state changes.

        :type numToes: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numToeLinks.changed
    def numToeLinks(self, numToeLinks):
        """
        Changed method that notifies any toe link size changes.

        :type numToeLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def toeFlags(self):
        """
        Returns the enabled flags for each toe.

        :rtype: Dict[ToeType, bool]
        """

        numToes = int(self.numToes)
        numToeLinks = int(self.numToeLinks)

        bigToeEnabled = bool(self.bigToeEnabled)
        longToeEnabled = bigToeEnabled or ((numToes > 1) and (numToeLinks >= 1)) or ((numToes == 1) and (numToeLinks > 1))

        if numToes == 1:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: longToeEnabled, ToeType.MIDDLE: False, ToeType.RING: False, ToeType.PINKY: False}

        elif numToes == 2:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: longToeEnabled, ToeType.MIDDLE: False, ToeType.RING: False, ToeType.PINKY: True}

        elif numToes == 3:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: longToeEnabled, ToeType.MIDDLE: True, ToeType.RING: False, ToeType.PINKY: True}

        else:

            return {ToeType.BIG: bigToeEnabled, ToeType.LONG: longToeEnabled, ToeType.MIDDLE: True, ToeType.RING: True, ToeType.PINKY: True}

    def invalidatePivots(self, pivotSpecs, **kwargs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: List[pivotspec.PivotSpec]
        """

        # Edit pivot spec
        #
        skeletonNamespace = self.skeletonNamespace()

        pivotSpec, = self.resizePivots(1, pivotSpecs)
        pivotSpec.name = self.formatName(subname='Pivot', type='nurbsCurve')
        pivotSpec.driver.name = self.formatName()
        pivotSpec.driver.namespace = skeletonNamespace
        pivotSpec.driver.type = pivotSpec.driver.Type.CONSTRAINT
        pivotSpec.driver.skipTranslate = (False, False, True)

        # Check if default shape exists
        # If not, go ahead and populate default shape!
        #
        if stringutils.isNullOrEmpty(pivotSpec.shapes):

            controlPoints = list(self.__default_pivot_points__)
            controlPoints.extend(controlPoints[:3])  # Periodic curves require overlapping points equal to the degree!

            count, degree, form = len(controlPoints), 3, om.MFnNurbsCurve.kPeriodic
            knots, degree = shapeutils.createKnotVector(count, degree, form=form)

            shape = {
                'typeName': 'nurbsCurve',
                'degree': degree,
                'form': form,
                'controlPoints': controlPoints,
                'knots': knots,
                'lineWidth': -1.0
            }

            pivotSpec.shapes = json.dumps([shape])

        # Call parent method
        #
        return super(FootComponent, self).invalidatePivots(pivotSpecs, **kwargs)

    def repairPivots(self, force=False):
        """
        Repairs the internal pivot specs for this component.

        :rtype: None
        """

        # Invalidate pivot spec
        # This will ensure the driver specs are up-to-date!
        #
        pivotSpec, = self.pivots(force=force)

        # Call parent method
        #
        return super(FootComponent, self).repairPivots(force=force)

    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit foot spec
        #
        footSide = self.Side(self.componentSide)

        footSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        footSpec.name = self.formatName()
        footSpec.side = footSide
        footSpec.type = self.Type.FOOT
        footSpec.defaultMatrix = self.__default_component_matrices__[footSide][self.FootType.FOOT]
        footSpec.driver.name = self.formatName(subname='Ankle', kinemat='Blend', type='joint')

        # Edit ball spec
        #
        ballSpec, = self.resizeSkeleton(1, footSpec.children, hierarchical=False)
        ballSpec.name = self.formatName(subname='Ball')
        ballSpec.side = footSide
        ballSpec.type = self.Type.TOE
        ballSpec.defaultMatrix = self.__default_component_matrices__[footSide][self.FootType.BALL]
        ballSpec.driver.name = self.formatName(subname='Toes', type='control')

        # Iterate through toe specs
        #
        toeFlags = self.toeFlags()
        numBigToeLinks, numToeLinks = int(self.numBigToeLinks), int(self.numToeLinks)
        jointTypes = (self.Type.BIG_TOE, self.Type.INDEX_TOE, self.Type.MIDDLE_TOE, self.Type.RING_TOE, self.Type.PINKY_TOE)

        numToeMembers = len(self.ToeType)
        topLevelToeSpecs = self.resizeSkeleton(numToeMembers, ballSpec.children, hierarchical=False)

        for (toeType, baseToeSpec) in enumerate(topLevelToeSpecs):

            # Decompose toes
            #
            toeType = self.ToeType(toeType)
            toeEnabled = toeFlags.get(toeType, False)
            toeName = toeType.name.title()
            fullToeName = f'{toeName}Toe'
            jointType = jointTypes[toeType]

            # Iterate through digit specs
            #
            isBig = (toeType == self.ToeType.BIG)
            toeSize = numBigToeLinks if isBig else numToeLinks

            *inbetweenToeSpecs, toeTipSpec = self.resizeSkeleton(toeSize, baseToeSpec, hierarchical=True)

            for (i, toeSpec) in enumerate((baseToeSpec, *inbetweenToeSpecs), start=1):

                isFirstToe = (i == 1)
                defaultMatrix = self.__default_digit_matrices__[footSide][toeType] if isFirstToe else transformutils.createTranslateMatrix((self.__default_digit_spacing__, 0.0, 0.0))

                toeSpec.enabled = toeEnabled
                toeSpec.name = self.formatName(subname=fullToeName, index=i)
                toeSpec.type = jointType
                toeSpec.defaultMatrix = defaultMatrix
                toeSpec.driver.name = self.formatName(subname=fullToeName, index=i, type='control')

            # Edit tip spec
            #
            fullToeTipName = f'{fullToeName}Tip'

            toeTipSpec.enabled = toeEnabled
            toeTipSpec.name = self.formatName(subname=fullToeTipName)
            toeTipSpec.type = jointType
            toeTipSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_digit_spacing__, 0.0, 0.0))
            toeTipSpec.driver.name = self.formatName(subname=fullToeTipName, type='target')

        # Call parent method
        #
        return super(FootComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def repairSkeleton(self, force=False):
        """
        Repairs the internal skeleton specs for this component.

        :type force: bool
        :rtype: None
        """

        # Rename legacy joints
        #
        toesName = self.formatName(subname='Toes')
        ballName = self.formatName(subname='Ball')

        if self.scene.doesNodeExist(toesName):

            toesExportJoint = self.scene(toesName)

            log.warning(f'Renaming "{toesName}" > "{ballName}"')
            toesExportJoint.setName(ballName)

        # Call parent method
        #
        return super(FootComponent, self).repairSkeleton(force=force)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        footSpec, = self.skeleton()
        footExportJoint = footSpec.getNode()
        footExportMatrix = footExportJoint.worldMatrix()

        ballSpec, = footSpec.children
        ballExportJoint = ballSpec.getNode()
        ballExportMatrix = ballExportJoint.worldMatrix()

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

            raise NotImplementedError('buildRig() limbless foot components have not been implemented!')

        # Get required limb nodes
        #
        limbComponent = limbComponents[0]

        switchCtrl = self.scene(limbComponent.userProperties['switchControl'])
        limbFKCtrl = self.scene(limbComponent.userProperties['fkControls'][-1])
        limbIKCtrl = self.scene(limbComponent.userProperties['ikControls'][-1])
        limbIKOffsetCtrl = self.scene(limbIKCtrl.userProperties['offset'])

        hasReverseIKJoints = 'rikJoints' in limbComponent.userProperties
        limbTipIKJoint = self.scene(limbComponent.userProperties['ikJoints'][-1])
        limbTipRIKJoint = self.scene(limbComponent.userProperties['rikJoints'][-1]) if hasReverseIKJoints else limbTipIKJoint

        # Create foot control
        #
        footCtrlMatrix = mirrorMatrix * footExportMatrix

        footSpaceName = self.formatName(type='space')
        footSpace = self.scene.createNode('transform', name=footSpaceName, parent=controlsGroup)
        footSpace.setWorldMatrix(footCtrlMatrix)
        footSpace.freezeTransform()

        footCtrlName = self.formatName(type='control')
        footCtrl = self.scene.createNode('transform', name=footCtrlName, parent=footSpace)
        footCtrl.addDivider('Spaces')
        footCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        footCtrl.prepareChannelBoxForAnimation()
        footCtrl.userProperties['ignoreShapes'] = True
        self.publishNode(footCtrl, alias=self.componentName)

        footSpaceSwitch = footSpace.addSpaceSwitch([limbFKCtrl, limbIKOffsetCtrl, motionCtrl], maintainOffset=True)
        footSpaceSwitch.weighted = True
        footSpaceSwitch.setAttr('target', [{'targetReverse': (True, True, True)}, {}, {'targetWeight': (0.0, 0.0, 0.0)}])
        footSpaceSwitch.connectPlugs(switchCtrl['mode'], 'target[0].targetWeight')
        footSpaceSwitch.connectPlugs(switchCtrl['mode'], 'target[1].targetWeight')
        footSpaceSwitch.connectPlugs(footCtrl['localOrGlobal'], 'target[2].targetRotateWeight')

        if hasReverseIKJoints:

            footCtrl.addAttr(longName='localCalfLock', attributeType='float', min=0.0, max=1.0, keyable=True)

            footIKSpaceSwitchName = self.formatName(subname='IK', type='spaceSwitch')
            footIKSpaceSwitch = self.scene.createNode('spaceSwitch', name=footIKSpaceSwitchName)
            footIKSpaceSwitch.weighted = True
            footIKSpaceSwitch.setAttr('restMatrix', footCtrlMatrix)
            footIKSpaceSwitch.addTargets([limbIKOffsetCtrl, limbTipIKJoint], maintainOffset=True)
            footIKSpaceSwitch.setAttr('target[0]', {'targetReverse': (True, True, True)})
            footIKSpaceSwitch.connectPlugs(footCtrl['localCalfLock'], 'target[0].targetWeight')
            footIKSpaceSwitch.connectPlugs(footCtrl['localCalfLock'], 'target[1].targetWeight')
            footIKSpaceSwitch.connectPlugs('outputMatrix', footSpaceSwitch['target[1].targetMatrix'], force=True)

        # Decompose foot pivot curve
        #
        pivotSpec, = self.pivots()
        pivotCurveData = mshapeparser.loads(pivotSpec.shapes)[0]
        fnPivotCurve = om.MFnNurbsCurve(pivotCurveData)

        pivotMatrix = om.MMatrix(pivotSpec.worldMatrix)
        pivotCurvePoints = [om.MPoint(point) * pivotMatrix for point in fnPivotCurve.cvPositions()]

        # Add intermediate shape to foot control
        #
        footIntermediatePoints = [point * footCtrlMatrix.inverse() for point in pivotCurvePoints]

        footIntermediateObject = footCtrl.addCurve(footIntermediatePoints, degree=fnPivotCurve.degree, form=fnPivotCurve.form)
        footIntermediateObject.isIntermediateObject = True
        footIntermediateObject.setName(f'{footCtrl.name()}ShapeOrig')

        # Add foot control shape
        #
        footCurveBox = footIntermediateObject.curveBox()
        worldCenter = om.MPoint(footCurveBox.center) * footIntermediateObject.worldMatrix()
        localCenter = worldCenter * footCtrl.worldInverseMatrix()
        localSizeX, localSizeY, localSizeZ = footCurveBox.width, footCurveBox.height, footCurveBox.depth

        footCtrlShape = footCtrl.addPointHelper(
            'square',
            size=1.0,
            localPosition=localCenter,
            localScale=(1.0, localSizeY, localSizeZ),
            colorRGB=colorRGB,
            lineWidth=4.0
        )

        # Setup foot pivot controls
        #
        localHalfSizeY = localSizeY * 0.25
        localHalfSizeZ = localSizeZ * 0.5

        footPivotCurvePoints = om.MVectorArray(
            [
                (0.0, 0.0, 0.0),
                (0.0, 0.0, localHalfSizeZ),
                (0.0, -localHalfSizeY, localHalfSizeZ),
                (0.0, 0.0, (localHalfSizeZ + localHalfSizeY)),
                (0.0, localHalfSizeY, localHalfSizeZ),
                (0.0, 0.0, localHalfSizeZ),
                (0.0, 0.0, 0.0),
                (localHalfSizeZ, 0.0, 0.0),
                (-localHalfSizeZ, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, -localHalfSizeZ),
                (0.0, -localHalfSizeY, -localHalfSizeZ),
                (0.0, 0.0, (-localHalfSizeZ - localHalfSizeY)),
                (0.0, localHalfSizeY, -localHalfSizeZ),
                (0.0, 0.0, -localHalfSizeZ),
                (0.0, 0.0, 0.0)
            ]
        )

        footPivotCtrlName = self.formatName(subname='Pivot', type='control')
        footPivotCtrl = self.scene.createNode('transform', name=footPivotCtrlName, parent=footCtrl)
        footPivotCtrl.addCurve(footPivotCurvePoints, degree=1, form=om.MFnNurbsCurve.kClosed, colorRGB=lightColorRGB)
        footPivotCtrl.prepareChannelBoxForAnimation()
        footPivotCtrl.userProperties['ignoreShapes'] = True
        self.publishNode(footPivotCtrl, alias='Foot_Pivot')

        footCenterName = self.formatName(subname='Center', type='vectorMath')
        footCenter = self.scene.createNode('vectorMath', name=footCenterName)
        footCenter.operation = 9  # Average
        footCenter.connectPlugs(footCtrlShape['boundingBoxMin'], 'inFloatA')
        footCenter.connectPlugs(footCtrlShape['boundingBoxMax'], 'inFloatB')

        footPivotMatrixName = self.formatName(subname='Pivot', type='composeMatrix')
        footPivotMatrix = self.scene.createNode('composeMatrix', name=footPivotMatrixName)
        footPivotMatrix.connectPlugs(footCenter['outFloat'], 'inputTranslate')
        footPivotMatrix.connectPlugs('outputMatrix', footPivotCtrl['offsetParentMatrix'])

        footPivotMultMatrixName = self.formatName(subname='Pivot', type='multMatrix')
        footPivotMultMatrix = self.scene.createNode('multMatrix', name=footPivotMultMatrixName)
        footPivotMultMatrix.connectPlugs(footPivotCtrl[f'worldMatrix[{footPivotCtrl.instanceNumber()}]'], 'matrixIn[0]')
        footPivotMultMatrix.connectPlugs(footIntermediateObject[f'worldInverseMatrix[{footIntermediateObject.instanceNumber()}]'], 'matrixIn[1]')

        footPivotName = self.formatName(subname='Pivot', type='vectorProduct')
        footPivot = self.scene.createNode('vectorProduct', name=footPivotName)
        footPivot.operation = 3  # Vector matrix product
        footPivot.input1 = (-1.0 * mirrorSign, 0.0, 0.0)
        footPivot.connectPlugs(footPivotMultMatrix['matrixSum'], 'matrix')

        footNormalName = self.formatName(subname='Normal', type='vectorProduct')
        footNormal = self.scene.createNode('vectorProduct', name=footNormalName)
        footNormal.operation = 3  # Vector matrix product
        footNormal.input1 = (-1.0 * mirrorSign, 0.0, 0.0)
        footNormal.connectPlugs(footIntermediateObject['matrix'], 'matrix')

        footProjectedVectorName = self.formatName(subname='ProjectedVector', type='vectorMath')
        footProjectedVector = self.scene.createNode('vectorMath', name=footProjectedVectorName)
        footProjectedVector.operation = 18  # Project
        footProjectedVector.normalize = True
        footProjectedVector.connectPlugs(footNormal['output'], 'inFloatA')
        footProjectedVector.connectPlugs(footPivot['output'], 'inFloatB')

        footMaxSizeName = self.formatName(subname='MaxSize', type='max')
        footMaxSize = self.scene.createNode('max', name=footMaxSizeName)
        footMaxSize.connectPlugs(footIntermediateObject['boundingBoxSizeX'], 'input[0]')
        footMaxSize.connectPlugs(footIntermediateObject['boundingBoxSizeY'], 'input[1]')
        footMaxSize.connectPlugs(footIntermediateObject['boundingBoxSizeZ'], 'input[2]')

        footScaledVectorName = self.formatName(subname='ScaledVector', type='vectorMath')
        footScaledVector = self.scene.createNode('vectorMath', name=footScaledVectorName)
        footScaledVector.operation = 2  # Multiply
        footScaledVector.connectPlugs(footProjectedVector['outFloat'], 'inFloatA')
        footScaledVector.connectPlugs(footMaxSize['output'], 'inFloatB')

        footInputName = self.formatName(subname='Point', type='vectorMath')
        footInput = self.scene.createNode('vectorMath', name=footInputName)
        footInput.operation = 0  # Add
        footInput.connectPlugs(footCenter['outFloat'], 'inFloatA')
        footInput.connectPlugs(footScaledVector['outFloat'], 'inFloatB')

        footPointOnCurveName = self.formatName(subname='Pivot', type='nearestPointOnCurve')
        footPointOnCurve = self.scene.createNode('nearestPointOnCurve', name=footPointOnCurveName)
        footPointOnCurve.connectPlugs(footIntermediateObject['local'], 'inputCurve')
        footPointOnCurve.connectPlugs(footInput['outFloat'], 'inPosition')

        footVectorLengthName = self.formatName(subname='VectorLength', type='length')
        footVectorLength = self.scene.createNode('length', name=footVectorLengthName)
        footVectorLength.connectPlugs(footProjectedVector['outFloat'], 'input')

        footPivotConditionName = self.formatName(subname='Pivot', type='condition')
        footPivotCondition = self.scene.createNode('condition', name=footPivotConditionName)
        footPivotCondition.operation = 2  # Greater than
        footPivotCondition.secondTerm = 0.001  # Super important!
        footPivotCondition.connectPlugs(footVectorLength['output'], 'firstTerm')
        footPivotCondition.connectPlugs(footPointOnCurve['result.position'], 'colorIfTrue')
        footPivotCondition.connectPlugs(footCenter['outFloat'], 'colorIfFalse')

        footPivotTargetName = self.formatName(subname='Pivot', type='target')
        footPivotTarget = self.scene.createNode('transform', name=footPivotTargetName, parent=footCtrl)
        footPivotTarget.connectPlugs(footPivotCondition['outColor'], 'rotatePivot')
        footPivotTarget.connectPlugs(footPivotCtrl['rotateOrder'], 'rotateOrder')
        footPivotTarget.connectPlugs(footPivotCtrl['rotate'], 'rotate')
        footPivotTarget.connectPlugs(footPivotCondition['outColor'], 'scalePivot')
        footPivotTarget.connectPlugs(footPivotCtrl['scale'], 'scale')
        footPivotTarget.connectPlugs(footPivotCtrl['translate'], 'translate')

        # Compose heel and toe-tip matrices
        #
        footForwardVector, footUpVector, footRightVector, footPoint = transformutils.breakMatrix(footExportMatrix, normalize=True)
        footRotationMatrix = transformutils.createRotationMatrix(footExportMatrix)
        ballRotationMatrix = transformutils.createRotationMatrix(ballExportMatrix)

        groundDot = footForwardVector * (worldCenter - footPoint)
        groundPoint = footPoint + (footForwardVector * groundDot)

        toeTipDot = footCurveBox.max.y if (componentSide == self.Side.RIGHT) else footCurveBox.min.y
        toeTipPoint = groundPoint + (footUpVector * (toeTipDot * mirrorSign))
        toeTipMatrix = footRotationMatrix * transformutils.createTranslateMatrix(toeTipPoint)
        toeTipExportMatrix = ballRotationMatrix * transformutils.createTranslateMatrix(toeTipPoint)

        heelDot = footCurveBox.min.y if (componentSide == self.Side.RIGHT) else footCurveBox.max.y
        heelPoint = groundPoint + (footUpVector * (heelDot * mirrorSign))
        heelMatrix = footRotationMatrix * transformutils.createTranslateMatrix(heelPoint)

        # Create heel roll control
        #
        heelRollCtrlName = self.formatName(subname='Heel', type='control')
        heelRollCtrl = self.scene.createNode('transform', name=heelRollCtrlName, parent=footPivotTarget)
        heelRollCtrl.addPointHelper('triangle', size=localHalfSizeZ, localPosition=(0.0, 0.0, localCenter.z), localRotate=(0.0, 0.0, 90.0 * mirrorSign), colorRGB=lightColorRGB)
        heelRollCtrl.setWorldMatrix(heelMatrix, skipRotate=True, skipScale=True)
        heelRollCtrl.freezeTransform()
        heelRollCtrl.prepareChannelBoxForAnimation()
        heelRollCtrl.userProperties['ignoreShapes'] = True
        self.publishNode(heelRollCtrl, alias='Heel')

        # Create toe-tip roll control
        #
        toeRollCtrlName = self.formatName(subname='ToeTip', type='control')
        toeRollCtrl = self.scene.createNode('transform', name=toeRollCtrlName, parent=heelRollCtrl)
        toeRollCtrl.addPointHelper('triangle', size=localHalfSizeZ, localPosition=(0.0, 0.0, localCenter.z), localRotate=(0.0, 0.0, -90.0 * mirrorSign), colorRGB=lightColorRGB)
        toeRollCtrl.setWorldMatrix(toeTipMatrix, skipRotate=True, skipScale=True)
        toeRollCtrl.freezeTransform()
        toeRollCtrl.prepareChannelBoxForAnimation()
        toeRollCtrl.userProperties['ignoreShapes'] = True
        self.publishNode(toeRollCtrl, alias='ToeTip')

        ballIKTargetName = self.formatName(subname='Ball', kinemat='IK', type='target')
        ballIKTarget = self.scene.createNode('transform', name=ballIKTargetName, parent=toeRollCtrl)
        ballIKTarget.displayLocalAxis = True
        ballIKTarget.visibility = False
        ballIKTarget.setWorldMatrix(toeTipExportMatrix, skipScale=True)
        ballIKTarget.freezeTransform()
        ballIKTarget.lock()

        # Create kinematic foot joints
        #
        jointTypes = ('Ankle', 'Ball', 'ToeTip')
        kinematicTypes = ('FK', 'IK', 'Blend')

        footFKJoints = [None] * 3
        footIKJoints = [None] * 3
        footBlendJoints = [None] * 3
        footMatrices = (footExportMatrix, ballExportMatrix, toeTipExportMatrix)
        kinematicJoints = (footFKJoints, footIKJoints, footBlendJoints)

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = kinematicJoints[i][j - 1] if (j > 0) else jointsGroup
                inheritsTransform = not (j == 0)

                jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.inheritsTransform = inheritsTransform
                joint.displayLocalAxis = True
                joint.setWorldMatrix(footMatrices[j])

                kinematicJoints[i][j] = joint

        footFKJoint, ballFKJoint, toeTipFKJoint = footFKJoints
        footIKJoint, ballIKJoint, toeTipIKJoint = footIKJoints
        footBlendJoint, ballBlendJoint, toeTipBlendJoint = footBlendJoints

        blender = switchCtrl['mode']
        footBlender = setuputils.createTransformBlends(footFKJoint, footIKJoint, footBlendJoint, blender=blender)
        ballBlender = setuputils.createTransformBlends(ballFKJoint, ballIKJoint, ballBlendJoint, blender=blender)
        toeTipBlender = setuputils.createTransformBlends(toeTipFKJoint, toeTipIKJoint, toeTipBlendJoint, blender=blender)

        footBlender.setName(self.formatName(subname=jointTypes[0], type='blendTransform'))
        ballBlender.setName(self.formatName(subname=jointTypes[1], type='blendTransform'))
        toeTipBlender.setName(self.formatName(subname=jointTypes[2], type='blendTransform'))

        # Constrain foot FK joints
        #
        footFKJoint.addConstraint('transformConstraint', [footCtrl], maintainOffset=requiresMirroring)

        footFKJoint.connectPlugs('scale', ballFKJoint['scale'])
        ballFKJoint.connectPlugs('scale', toeTipFKJoint['scale'])

        # Create foot roll control
        #
        ballRollCtrlName = self.formatName(subname='Ball', type='control')
        ballRollCtrl = self.scene.createNode('transform', name=ballRollCtrlName, parent=toeRollCtrl)
        ballRollCtrl.addShape('RoundLollipopCurve', size=(localSizeY * 0.75), localScale=(mirrorSign, mirrorSign, 1.0), colorRGB=lightColorRGB, lineWidth=4.0)
        ballRollCtrl.setWorldMatrix(ballExportMatrix, skipRotate=True, skipScale=True)
        ballRollCtrl.hideAttr('scale', lock=True)
        ballRollCtrl.freezeTransform()
        ballRollCtrl.prepareChannelBoxForAnimation()
        self.publishNode(ballRollCtrl, alias='Ball')

        ankleIKTargetName = self.formatName(subname='Ankle', kinemat='IK', type='target')
        ankleIKTarget = self.scene.createNode('transform', name=ankleIKTargetName, parent=ballRollCtrl)
        ankleIKTarget.displayLocalAxis = True
        ankleIKTarget.visibility = False
        ankleIKTarget.copyTransform(ballExportJoint, skipScale=True)
        ankleIKTarget.freezeTransform()
        ankleIKTarget.lock()

        footIKTargetName = self.formatName(subname='IK', type='target')
        footIKTarget = self.scene.createNode('transform', name=footIKTargetName, parent=ballRollCtrl)
        footIKTarget.displayLocalAxis = True
        footIKTarget.visibility = False
        footIKTarget.copyTransform(footExportJoint, skipScale=True)
        footIKTarget.freezeTransform()
        footIKTarget.lock()

        self.userProperties['ikTarget'] = footIKTarget.uuid()

        # Create IK emulators
        #
        limbPickMatrixName = self.formatName(name=limbComponent.componentName, type='pickMatrix')
        limbPickMatrix = self.scene.createNode('pickMatrix', name=limbPickMatrixName)
        limbPickMatrix.useTranslate = True
        limbPickMatrix.useRotate = False
        limbPickMatrix.useScale = False
        limbPickMatrix.useShear = False
        limbPickMatrix.connectPlugs(limbTipRIKJoint[f'worldMatrix[{limbTipRIKJoint.instanceNumber()}]'], 'inputMatrix')

        footPickMatrixName = self.formatName(type='pickMatrix')
        footPickMatrix = self.scene.createNode('pickMatrix', name=footPickMatrixName)
        footPickMatrix.useTranslate = False
        footPickMatrix.useRotate = True
        footPickMatrix.useScale = True
        footPickMatrix.useShear = False
        footPickMatrix.connectPlugs(footCtrl[f'worldMatrix[{footCtrl.instanceNumber()}]'], 'inputMatrix')

        footRestMultMatrixName = self.formatName(subname='Ankle', kinemat='Rest', type='multMatrix')
        footRestMultMatrix = self.scene.createNode('multMatrix', name=footRestMultMatrixName)
        footRestMultMatrix.connectPlugs(footPickMatrix['outputMatrix'], 'matrixIn[0]')
        footRestMultMatrix.connectPlugs(limbPickMatrix['outputMatrix'], 'matrixIn[1]')

        footRestDecomposeMatrixName = self.formatName(subname='Ankle', kinemat='Rest', type='decomposeMatrix')
        footRestDecomposeMatrix = self.scene.createNode('decomposeMatrix', name=footRestDecomposeMatrixName)
        footRestDecomposeMatrix.connectPlugs(footRestMultMatrix['matrixSum'], 'inputMatrix')

        ankleRestMatrixName = self.formatName(subname='Ankle', kinemat='Rest', type='composeMatrix')
        ankleRestMatrix = self.scene.createNode('composeMatrix', name=ankleRestMatrixName)
        ankleRestMatrix.connectPlugs(footRestDecomposeMatrix['outputTranslate'], 'inputTranslate')
        ankleRestMatrix.useEulerRotation = True
        ankleRestMatrix.inputRotate = footIKJoint.getAttr('rotate')
        ankleRestMatrix.connectPlugs(footRestDecomposeMatrix['outputScale'], 'inputScale')

        ballRestMatrixName = self.formatName(subname='Ball', kinemat='Rest', type='composeMatrix')
        ballRestMatrix = self.scene.createNode('composeMatrix', name=ballRestMatrixName)
        ballRestMatrix.inputTranslate = ballIKJoint.getAttr('translate')
        ballRestMatrix.useEulerRotation = True
        ballRestMatrix.inputRotate = ballIKJoint.getAttr('rotate')
        ballRestMatrix.connectPlugs(footRestDecomposeMatrix['outputScale'], 'inputScale')

        toeTipRestMatrixName = self.formatName(subname='ToeTip', kinemat='Rest', type='composeMatrix')
        toeTipRestMatrix = self.scene.createNode('composeMatrix', name=toeTipRestMatrixName)
        toeTipRestMatrix.inputTranslate = toeTipIKJoint.getAttr('translate')
        toeTipRestMatrix.useEulerRotation = True
        toeTipRestMatrix.inputRotate = toeTipIKJoint.getAttr('rotate')
        toeTipRestMatrix.connectPlugs(footRestDecomposeMatrix['outputScale'], 'inputScale')

        ankleIKEmulatorName = self.formatName(subname='Ankle', type='ikEmulator')
        ankleIKEmulator = self.scene.createNode('ikEmulator', name=ankleIKEmulatorName)
        ankleIKEmulator.forwardAxis = 0  # X
        ankleIKEmulator.forwardAxisFlip = False
        ankleIKEmulator.upAxis = 1  # Y
        ankleIKEmulator.upAxisFlip = True
        ankleIKEmulator.poleType = 3  # Goal
        ankleIKEmulator.segmentScaleCompensate = True
        ankleIKEmulator.connectPlugs(ankleRestMatrix['outputMatrix'], 'restMatrix[0]')
        ankleIKEmulator.connectPlugs(ballRestMatrix['outputMatrix'], 'restMatrix[1]')
        ankleIKEmulator.connectPlugs(ankleIKTarget[f'worldMatrix[{ankleIKTarget.instanceNumber()}]'], 'goal')
        
        ballIKEmulatorName = self.formatName(subname='Ball', type='ikEmulator')
        ballIKEmulator = self.scene.createNode('ikEmulator', name=ballIKEmulatorName)
        ballIKEmulator.forwardAxis = 0  # X
        ballIKEmulator.forwardAxisFlip = False
        ballIKEmulator.upAxis = 1  # Y
        ballIKEmulator.upAxisFlip = True
        ballIKEmulator.poleType = 3  # Goal
        ballIKEmulator.segmentScaleCompensate = True
        ballIKEmulator.connectPlugs(ankleIKEmulator['outMatrix[1]'], 'restMatrix[0]')
        ballIKEmulator.connectPlugs(toeTipRestMatrix['outputMatrix'], 'restMatrix[1]')
        ballIKEmulator.connectPlugs(ballIKJoint[f'parentMatrix[{ballIKJoint.instanceNumber()}]'], 'parentRestMatrix')
        ballIKEmulator.connectPlugs(ballIKTarget[f'worldMatrix[{ballIKTarget.instanceNumber()}]'], 'goal')
        ballIKEmulator.connectPlugs(ballIKJoint[f'parentInverseMatrix[{ballIKJoint.instanceNumber()}]'], 'parentInverseMatrix')

        # Connect emulators to IK joints
        #
        ankleIKMatrixName = self.formatName(subname='Ankle', kinemat='IK', type='decomposeMatrix')
        ankleIKMatrix = self.scene.createNode('decomposeMatrix', name=ankleIKMatrixName)
        ankleIKMatrix.connectPlugs(ankleIKEmulator['outMatrix[0]'], 'inputMatrix')
        ankleIKMatrix.connectPlugs(footIKJoint['rotateOrder'], 'inputRotateOrder')
        ankleIKMatrix.connectPlugs('outputTranslate', footIKJoint['translate'])
        ankleIKMatrix.connectPlugs('outputRotate', footIKJoint['rotate'])
        ankleIKMatrix.connectPlugs('outputScale', footIKJoint['scale'])

        ballIKMatrixName = self.formatName(subname='Ball', kinemat='IK', type='decomposeMatrix')
        ballIKMatrix = self.scene.createNode('decomposeMatrix', name=ballIKMatrixName)
        ballIKMatrix.connectPlugs(ballIKEmulator['outMatrix[0]'], 'inputMatrix')
        ballIKMatrix.connectPlugs(ballIKJoint['rotateOrder'], 'inputRotateOrder')
        ballIKMatrix.connectPlugs('outputTranslate', ballIKJoint['translate'])
        ballIKMatrix.connectPlugs('outputRotate', ballIKJoint['rotate'])
        ballIKMatrix.connectPlugs('outputScale', ballIKJoint['scale'])

        toeTipIKName = self.formatName(subname='ToeTip', kinemat='IK', type='decomposeMatrix')
        toeTipIKMatrix = self.scene.createNode('decomposeMatrix', name=toeTipIKName)
        toeTipIKMatrix.connectPlugs(ballIKEmulator['outMatrix[1]'], 'inputMatrix')
        toeTipIKMatrix.connectPlugs(toeTipIKJoint['rotateOrder'], 'inputRotateOrder')
        toeTipIKMatrix.connectPlugs('outputTranslate', toeTipIKJoint['translate'])
        toeTipIKMatrix.connectPlugs('outputRotate', toeTipIKJoint['rotate'])
        toeTipIKMatrix.connectPlugs('outputScale', toeTipIKJoint['scale'])

        # Create toes control
        #
        toesMatrix = mirrorMatrix * ballBlendJoint.worldMatrix()
        localScaleZ = footCtrl.shape().localScaleZ

        toesSpaceName = self.formatName(subname='Toes', type='space')
        toesSpace = self.scene.createNode('transform', name=toesSpaceName, parent=controlsGroup)
        toesSpace.setWorldMatrix(toesMatrix)
        toesSpace.freezeTransform()
        toesSpace.addConstraint('transformConstraint', [ballBlendJoint], maintainOffset=requiresMirroring)

        toesCtrlName = self.formatName(subname='Toes', type='control')
        toesCtrl = self.scene.createNode('transform', name=toesCtrlName, parent=toesSpace)
        toesCtrl.addPointHelper('square', size=1.0, localScale=(1.0, localScaleZ * 0.5, localScaleZ), colorRGB=colorRGB)
        toesCtrl.prepareChannelBoxForAnimation()
        self.publishNode(toesCtrl, alias='Toes')

        if ballSpec.enabled:

            # Add pose attributes
            #
            footCtrl.addDivider('Poses')
            footCtrl.addAttr(longName='curl', attributeType='angle', keyable=True)
            footCtrl.addAttr(longName='spread', attributeType='angle', keyable=True)
            footCtrl.addAttr(longName='splay', attributeType='angle', keyable=True)

            # Create pose driver negate nodes
            #
            toeHalfSpreadName = self.formatName(subname='HalfSpread', type='floatMath')
            toeHalfSpread = self.scene.createNode('floatMath', name=toeHalfSpreadName)
            toeHalfSpread.operation = 2  # Multiply
            toeHalfSpread.connectPlugs(footCtrl['spread'], 'inAngleA')
            toeHalfSpread.setAttr('inAngleB', 0.5)

            toeNegateHalfSpreadName = self.formatName(subname='NegateHalfSpread', type='floatMath')
            toeNegateHalfSpread = self.scene.createNode('floatMath', name=toeNegateHalfSpreadName)
            toeNegateHalfSpread.operation = 2  # Multiply
            toeNegateHalfSpread.connectPlugs(footCtrl['spread'], 'inAngleA')
            toeNegateHalfSpread.setAttr('inAngleB', -0.5)

            toeNegateSpreadName = self.formatName(subname='NegateSpread', type='floatMath')
            toeNegateSpread = self.scene.createNode('floatMath', name=toeNegateSpreadName)
            toeNegateSpread.operation = 2  # Multiply
            toeNegateSpread.connectPlugs(footCtrl['spread'], 'inAngleA')
            toeNegateSpread.setAttr('inAngleB', -1.0)

            toeNegateSplayName = self.formatName(subname='NegateSplay', type='floatMath')
            toeNegateSplay = self.scene.createNode('floatMath', name=toeNegateSplayName)
            toeNegateSplay.operation = 2  # Multiply
            toeNegateSplay.connectPlugs(footCtrl['splay'], 'inAngleA')
            toeNegateSplay.setAttr('inAngleB', -1.0)

            toeNegateHalfSplayName = self.formatName(subname='NegateHalfSplay', type='floatMath')
            toeNegateHalfSplay = self.scene.createNode('floatMath', name=toeNegateHalfSplayName)
            toeNegateHalfSplay.operation = 2  # Multiply
            toeNegateHalfSplay.connectPlugs(footCtrl['splay'], 'inAngleA')
            toeNegateHalfSplay.setAttr('inAngleB', -(1.0 / 3.0))

            toeHalfSplayName = self.formatName(subname='HalfSplay', type='floatMath')
            toeHalfSplay = self.scene.createNode('floatMath', name=toeHalfSplayName)
            toeHalfSplay.operation = 2  # Multiply
            toeHalfSplay.connectPlugs(footCtrl['splay'], 'inAngleA')
            toeHalfSplay.setAttr('inAngleB', (1.0 / 3.0))

            # Iterate through toe groups
            #
            for (toeType, firstToeSpec) in enumerate(ballSpec.children):

                # Check if toe spec is enabled
                #
                if not firstToeSpec.enabled:

                    continue

                # Create toe master control
                #
                *toeSpecs, toeTipSpec = self.flattenSpecs(firstToeSpec, skipDisabled=False)

                toeType = self.ToeType(toeType)
                toeName = toeType.name.title()
                fullToeName = f'{toeName}Toe'
                firstToeExportJoint = firstToeSpec.getNode()

                masterToeCtrlName = self.formatName(subname=fullToeName, type='control')
                masterToeCtrl = self.scene.createNode('transform', name=masterToeCtrlName, parent=toesCtrl)
                masterToeCtrl.addPointHelper('square', size=(5.0 * rigScale), localScale=(1.0, 2.0, 0.25), colorRGB=lightColorRGB)
                masterToeCtrl.copyTransform(firstToeExportJoint)
                masterToeCtrl.freezeTransform()
                masterToeCtrl.prepareChannelBoxForAnimation()
                self.publishNode(masterToeCtrl, alias=fullToeName)

                # Iterate through toe group
                #
                numToeCtrls = len(toeSpecs)
                toeCtrls = [None] * numToeCtrls

                for (i, toeSpec) in enumerate(toeSpecs):

                    # Create toe control
                    #
                    toeIndex = i + 1
                    toeExportJoint = self.scene(toeSpec.uuid)
                    toeParent = toeCtrls[i - 1] if (i > 0) else masterToeCtrl
                    toeAlias = f'{fullToeName}{str(toeIndex).zfill(2)}'

                    toeCtrlName = self.formatName(subname=fullToeName, index=toeIndex, type='control')
                    toeCtrl = self.scene.createNode('transform', name=toeCtrlName, parent=toeParent)
                    toeCtrl.addPointHelper('disc', size=(5.0 * rigScale), localRotate=(0.0, 90.0, 0.0), colorRGB=colorRGB)
                    toeCtrl.prepareChannelBoxForAnimation()
                    self.publishNode(toeCtrl, alias=toeAlias)

                    toeCtrls[i] = toeCtrl

                    # Connect additives to toe control
                    #
                    toeMatrix = toeExportJoint.worldMatrix() * toeCtrl.parentInverseMatrix()
                    translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(toeMatrix)

                    toeComposeMatrixName = self.formatName(subname=fullToeName, index=toeIndex, type='composeMatrix')
                    toeComposeMatrix = self.scene.createNode('composeMatrix', name=toeComposeMatrixName)
                    toeComposeMatrix.setAttr('inputTranslate', translation)
                    toeComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)

                    toeArrayMathName = self.formatName(subname=fullToeName, index=toeIndex, type='arrayMath')
                    toeArrayMath = self.scene.createNode('arrayMath', name=toeArrayMathName)

                    if i > 0:

                        toeArrayMath.connectPlugs(masterToeCtrl['translateX'], 'inDistance[0].inDistanceX')
                        toeArrayMath.connectPlugs(masterToeCtrl['rotate'], 'inAngle[0]')

                    toeOffsetComposeMatrixName = self.formatName(subname=fullToeName, index=toeIndex, kinemat='Offset', type='composeMatrix')
                    toeOffsetComposeMatrix = self.scene.createNode('composeMatrix', name=toeOffsetComposeMatrixName)
                    toeOffsetComposeMatrix.connectPlugs(toeArrayMath['outDistance'], 'inputTranslate')
                    toeOffsetComposeMatrix.connectPlugs(toeArrayMath['outAngle'], 'inputRotate')

                    toeMultMatrixName = self.formatName(subname=fullToeName, index=toeIndex, type='multMatrix')
                    toeMultMatrix = self.scene.createNode('multMatrix', name=toeMultMatrixName)
                    toeMultMatrix.connectPlugs(toeOffsetComposeMatrix['outputMatrix'], 'matrixIn[0]')
                    toeMultMatrix.connectPlugs(toeComposeMatrix['outputMatrix'], 'matrixIn[1]')
                    toeMultMatrix.connectPlugs('matrixSum', toeCtrl['offsetParentMatrix'])

                    toeCtrl.userProperties['type'] = toeType
                    toeCtrl.userProperties['offset'] = toeArrayMath.uuid()

                # Create toe tip target
                #
                toeTipExportJoint = toeTipSpec.getNode()

                toeTipTargetName = self.formatName(subname=f'{fullToeName}Tip', type='target')
                toeTipTarget = self.scene.createNode('transform', name=toeTipTargetName, parent=toeCtrls[-1])
                toeTipTarget.displayLocalAxis = True
                toeTipTarget.visibility = False
                toeTipTarget.copyTransform(toeTipExportJoint, skipScale=True)
                toeTipTarget.freezeTransform()

                # Connect pose drivers to toe offsets
                #
                for (i, toeCtrl) in enumerate(toeCtrls):

                    # Connect curl driver
                    #
                    toeArrayMath = self.scene(toeCtrl.userProperties['offset'])
                    toeArrayMath.connectPlugs(footCtrl['curl'], 'inAngle[1].inAngleZ')

                    # Connect spread driver
                    #
                    if i == 0 and toeType != ToeType.BIG:

                        if toeType == ToeType.LONG:

                            toeHalfSpread.connectPlugs('outAngle', toeArrayMath['inAngle[2].inAngleY'])

                        elif toeType == ToeType.MIDDLE:

                            pass

                        elif toeType == ToeType.RING:

                            toeNegateHalfSpread.connectPlugs('outAngle', toeArrayMath['inAngle[2].inAngleY'])

                        else:

                            toeNegateSpread.connectPlugs('outAngle', toeArrayMath['inAngle[2].inAngleY'])

                    # Connect splay driver
                    #
                    if i == 0 and toeType != ToeType.BIG:

                        if toeType == ToeType.LONG:

                            toeNegateSplay.connectPlugs('outAngle', toeArrayMath['inAngle[2].inAngleZ'])

                        elif toeType == ToeType.MIDDLE:

                            toeNegateHalfSplay.connectPlugs('outAngle', toeArrayMath['inAngle[2].inAngleZ'])

                        elif toeType == ToeType.RING:

                            toeHalfSplay.connectPlugs('outAngle', toeArrayMath['inAngle[2].inAngleZ'])

                        else:

                            footCtrl.connectPlugs('splay', toeArrayMath['inAngle[2].inAngleZ'])

        # Call parent method
        #
        return super(FootComponent, self).buildRig()
    # endregion
