import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from maya.app.renderSetup.views.propertyEditor.main import kWarningPropagateLightValueChange
from mpy import mpyattribute
from dcc.maya.libs import transformutils, shapeutils
from dcc.dataclasses.colour import Colour
from rigomatic.libs import kinematicutils
from enum import IntEnum
from . import limbcomponent
from ..libs import Side, Type, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LimbType(IntEnum):
    """
    Enum class of all available limb types.
    """

    UPPER = 0
    LOWER = 1
    TIP = 2


class TwoBoneLimbComponent(limbcomponent.LimbComponent):
    """
    Overload of `AbstractComponent` that outlines two-bone limb components.
    """

    # region Dunderscores
    __default_limb_names__ = ('', '', '')
    __default_hinge_name__ = ''
    __default_limb_types__ = (Type.NONE, Type.NONE, Type.NONE)
    __default_limb_matrices__ = {Side.LEFT: {}, Side.RIGHT: {}}
    __default_rbf_samples__ = {Side.LEFT: {}, Side.RIGHT: {}}
    # endregion

    # region Enums
    LimbType = LimbType
    # endregion

    # region Attributes
    hingeEnabled = mpyattribute.MPyAttribute('hingeEnabled', attributeType='bool', default=False)

    @hingeEnabled.changed
    def hingeEnabled(self, hingeEnabled):
        """
        Changed method that notifies any hinge state changes.

        :type hingeEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: None
        """

        # Resize skeleton specs
        #
        twistCount = int(self.numTwistLinks)
        upperCount, lowerCount = twistCount + 1, twistCount + 2

        upperLimbSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        *upperTwistSpecs, lowerLimbSpec  = self.resizeSkeleton(upperCount, upperLimbSpec, hierarchical=False)
        *lowerTwistSpecs, hingeSpec, limbTipSpec = self.resizeSkeleton(lowerCount, lowerLimbSpec, hierarchical=False)

        # Edit limb specs
        #
        upperName, lowerName, tipName = self.__default_limb_names__
        upperType, lowerType, tipType = self.__default_limb_types__
        side = self.Side(self.componentSide)

        upperLimbSpec.name = self.formatName(name=upperName)
        upperLimbSpec.side = side
        upperLimbSpec.type = upperType
        upperLimbSpec.drawStyle = self.Style.BOX
        upperLimbSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.UPPER]
        upperLimbSpec.driver.name = self.formatName(name=upperName, type='joint')

        lowerLimbSpec.name = self.formatName(name=lowerName)
        lowerLimbSpec.side = side
        lowerLimbSpec.type = lowerType
        lowerLimbSpec.drawStyle = self.Style.BOX
        lowerLimbSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.LOWER]
        lowerLimbSpec.driver.name = self.formatName(name=lowerName, type='joint')

        limbTipSpec.enabled = not self.hasExtremityComponent()
        limbTipSpec.name = self.formatName(name=tipName)
        limbTipSpec.side = side
        limbTipSpec.type = tipType
        limbTipSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.TIP]
        limbTipSpec.driver.name = self.formatName(name=tipName, type='joint')

        # Edit twist specs
        #
        twistEnabled = bool(self.twistEnabled)

        for (twistName, twistType, twistSpecs) in ((upperName, upperType, upperTwistSpecs), (lowerName, lowerType, lowerTwistSpecs)):

            for (i, twistSpec) in enumerate(twistSpecs, start=1):

                twistSpec.enabled = twistEnabled
                twistSpec.name = self.formatName(name=twistName, subname='Twist', index=i)
                twistSpec.side = side
                twistSpec.type = twistType
                twistSpec.driver.name = self.formatName(name=twistName, subname='Twist', index=i, type='control')

        # Edit hinge spec
        #
        hingeName = str(self.__default_hinge_name__)
        hingeEnabled = bool(self.hingeEnabled)

        hingeSpec.enabled = hingeEnabled
        hingeSpec.name = self.formatName(name=hingeName)
        hingeSpec.side = side
        hingeSpec.type = self.Type.OTHER
        hingeSpec.otherType = hingeName
        hingeSpec.driver.name = self.formatName(name=hingeName, type='control')

        # Call parent method
        #
        return super(TwoBoneLimbComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        limbName = self.componentName
        hingeName = self.__default_hinge_name__
        upperLimbName, lowerLimbName, limbTipName = self.__default_limb_names__

        referenceNode = self.skeletonReference()
        upperLimbSpec, = self.skeleton()
        *upperTwistSpecs, lowerLimbSpec  = upperLimbSpec.children
        *lowerTwistSpecs, hingeSpec, limbTipSpec = lowerLimbSpec.children

        upperLimbExportJoint = upperLimbSpec.getNode(referenceNode=referenceNode)
        lowerLimbExportJoint = lowerLimbSpec.getNode(referenceNode=referenceNode)
        limbTipExportJoint = limbTipSpec.getNode(referenceNode=referenceNode)

        upperLimbMatrix = upperLimbExportJoint.worldMatrix()
        lowerLimbMatrix = lowerLimbExportJoint.worldMatrix()
        extremityMatrix = self.extremityMatrix()
        effectorMatrix = self.effectorMatrix()

        defaultLimbTipMatrix = transformutils.createRotationMatrix(lowerLimbMatrix) * transformutils.createTranslateMatrix(extremityMatrix)
        limbTipMatrix = limbTipExportJoint.worldMatrix() if (limbTipExportJoint is not None) else defaultLimbTipMatrix
        limbOrigin = transformutils.breakMatrix(upperLimbMatrix)[3]
        hingePoint = transformutils.breakMatrix(lowerLimbMatrix)[3]
        limbGoal = transformutils.breakMatrix(extremityMatrix)[3]

        componentSide = self.Side(self.componentSide)
        requiresMirroring = componentSide == self.Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Get space switch options
        #
        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        isArm = self.className.endswith('ArmComponent')
        isLeg = self.className.endswith('LegComponent')
        spineAlias = 'Chest' if isArm else 'Pelvis'
        spineComponent = rootComponent.findComponentDescendants('SpineComponent')[0]
        cogCtrl = spineComponent.getPublishedNode('COG')
        waistCtrl = spineComponent.getPublishedNode('Waist')
        spineCtrl = spineComponent.getPublishedNode(spineAlias)

        clavicleComponents = self.findComponentAncestors('ClavicleComponent')
        hasClavicleComponent = len(clavicleComponents) > 0
        clavicleComponent = clavicleComponents[0] if hasClavicleComponent else None
        clavicleCtrl = clavicleComponent.getPublishedNode('Clavicle') if (clavicleComponent is not None) else None

        # Create limb target
        #
        defaultUpperLimbMatrix = self.__default_limb_matrices__[componentSide][self.LimbType.UPPER]
        defaultLimbMatrix = transformutils.alignMatrixToNearestAxes(defaultUpperLimbMatrix, om.MMatrix.kIdentity)
        limbMatrix = mirrorMatrix * transformutils.createRotationMatrix(defaultLimbMatrix) * transformutils.createTranslateMatrix(limbOrigin)

        limbTargetName = self.formatName(type='target')
        limbTarget = self.scene.createNode('transform', name=limbTargetName, parent=privateGroup)
        limbTarget.setWorldMatrix(limbMatrix)
        limbTarget.freezeTransform()

        target = clavicleCtrl if hasClavicleComponent else spineCtrl
        limbTarget.addConstraint('transformConstraint', [target], maintainOffset=True)

        # Create kinematic limb joints
        #
        jointTypes = (upperLimbName, lowerLimbName, limbTipName)
        kinematicTypes = ('FK', 'IK', 'RIK', 'Blend')

        limbFKJoints = [None] * 3
        limbIKJoints = [None] * 3
        limbRIKJoints = [None] * 3
        limbBlendJoints = [None] * 3
        limbMatrices = (upperLimbMatrix, lowerLimbMatrix, limbTipMatrix)
        kinematicJoints = (limbFKJoints, limbIKJoints, limbRIKJoints, limbBlendJoints)

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = kinematicJoints[i][j - 1] if j > 0 else jointsGroup
                inheritsTransform = not (j == 0)

                jointName = self.formatName(name=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.inheritsTransform = inheritsTransform
                joint.displayLocalAxis = True
                joint.setWorldMatrix(limbMatrices[j])

                kinematicJoints[i][j] = joint

        upperFKJoint, lowerFKJoint, extremityFKJoint = limbFKJoints
        upperIKJoint, lowerIKJoint, extremityIKJoint = limbIKJoints
        upperRIKJoint, lowerRIKJoint, extremityRIKJoint = limbRIKJoints
        upperBlendJoint, lowerBlendJoint, extremityBlendJoint = limbBlendJoints

        # Create switch control
        #
        upperOffsetAttr = f'{upperLimbName.lower()}Offset'
        lowerOffsetAttr = f'{lowerLimbName.lower()}Offset'
        limbSign = -1.0 if isArm else 1.0

        switchCtrlName = self.formatName(subname='Switch', type='control')
        switchCtrl = self.scene.createNode('transform', name=switchCtrlName, parent=controlsGroup)
        switchCtrl.addPointHelper('pyramid', 'fill', 'shaded', size=(10.0 * rigScale), localPosition=(0.0, 25.0 * limbSign, 0.0), localRotate=(0.0, 0.0, -90.0 * limbSign), colorRGB=darkColorRGB)
        switchCtrl.addConstraint('transformConstraint', [extremityBlendJoint])
        switchCtrl.addDivider('Settings')
        switchCtrl.addAttr(longName='length', attributeType='doubleLinear', array=True, hidden=True)
        switchCtrl.addAttr(longName='mode', niceName='Mode (FK/IK)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName=upperOffsetAttr, attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName=lowerOffsetAttr, attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName='pin', attributeType='float', min=0.0, max=1.0, keyable=True)
        switchCtrl.addAttr(longName='soften', attributeType='float', min=0.0, keyable=True)
        switchCtrl.addAttr(longName='twist', attributeType='doubleAngle', keyable=True)
        switchCtrl.hideAttr('translate', 'rotate', 'scale', lock=True)
        switchCtrl.hideAttr('visibility', lock=False)
        self.publishNode(switchCtrl, alias='Switch')

        upperDistance = om.MPoint(limbOrigin).distanceTo(hingePoint)
        lowerDistance = om.MPoint(hingePoint).distanceTo(limbGoal)
        limbLengths = (upperDistance, lowerDistance)

        switchCtrl.setAttr('length', limbLengths)
        switchCtrl.lockAttr('length')

        # Create limb control
        #
        limbSpaceName = self.formatName(type='space')
        limbSpace = self.scene.createNode('transform', name=limbSpaceName, parent=controlsGroup)
        limbSpace.setWorldMatrix(limbMatrix)
        limbSpace.freezeTransform()

        limbCtrlName = self.formatName(type='control')
        limbCtrl = self.scene.createNode('transform', name=limbCtrlName, parent=limbSpace)
        limbCtrl.addPointHelper('disc', 'axisView', size=(10.0 * rigScale), localScale=(0.0, 3.0, 3.0), colorRGB=colorRGB)
        limbCtrl.prepareChannelBoxForAnimation()
        self.publishNode(limbCtrl, alias=limbName)

        clavicleComponents = self.findComponentAncestors('ClavicleComponent')
        hasClavicleComponent = len(clavicleComponents) > 0

        limbSpaceSwitch = None

        if hasClavicleComponent:

            defaultWorldWeight = 1.0 if isArm else 0.0
            defaultClavicleWeight = 0.0 if isArm else 1.0

            limbCtrl.addDivider('Settings')
            limbCtrl.addAttr(longName='followBody', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addDivider('Spaces')
            limbCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW3', niceName=f'Position Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (Clavicle)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, default=defaultWorldWeight, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW3', niceName=f'Rotation Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (Clavicle)', attributeType='float', min=0.0, max=1.0, default=defaultClavicleWeight, keyable=True)

            limbSpaceSwitch = limbSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, spineCtrl, limbTarget], maintainOffset=True)
            limbSpaceSwitch.weighted = True
            limbSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 1.0, 1.0)}])
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')

            limbAimMatrixName = self.formatName(subname='FollowBody', type='aimMatrix')
            limbAimMatrix = self.scene.createNode('aimMatrix', name=limbAimMatrixName)
            limbAimMatrix.connectPlugs(limbCtrl['followBody'], 'envelope')
            limbAimMatrix.connectPlugs(limbSpaceSwitch['outputWorldMatrix'], 'inputMatrix')
            limbAimMatrix.setAttr('primary', {'primaryInputAxis': (0.0, 0.0, -1.0 * mirrorSign), 'primaryMode': 2, 'primaryTargetVector': (0.0, 0.0, 1.0)})  # Align
            limbAimMatrix.connectPlugs(cogCtrl[f'worldMatrix[{cogCtrl.instanceNumber()}]'], 'primaryTargetMatrix')
            limbAimMatrix.setAttr('secondary', {'secondaryInputAxis': (1.0, 0.0, 0.0), 'secondaryMode': 2, 'secondaryTargetVector': (0.0, 0.0, 1.0)})  # Align
            limbAimMatrix.connectPlugs(spineCtrl[f'worldMatrix[{spineCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')

            limbAimMultMatrixName = self.formatName(subname='FollowBody', type='multMatrix')
            limbAimMultMatrix = self.scene.createNode('multMatrix', name=limbAimMultMatrixName)
            limbAimMultMatrix.connectPlugs(limbAimMatrix['outputMatrix'], 'matrixIn[0]')
            limbAimMultMatrix.connectPlugs(limbSpace[f'parentInverseMatrix[{limbSpace.instanceNumber()}]'], 'matrixIn[1]')

            limbAimDecomposeMatrixName = self.formatName(subname='FollowBody', type='decomposeMatrix')
            limbAimDecomposeMatrix = self.scene.createNode('decomposeMatrix', name=limbAimDecomposeMatrixName)
            limbAimDecomposeMatrix.connectPlugs(limbSpace['rotateOrder'], 'inputRotateOrder')
            limbAimDecomposeMatrix.connectPlugs(limbAimMultMatrix['matrixSum'], 'inputMatrix')
            limbAimDecomposeMatrix.connectPlugs('outputTranslate', limbSpace['translate'], force=True)
            limbAimDecomposeMatrix.connectPlugs('outputRotate', limbSpace['rotate'], force=True)
            limbAimDecomposeMatrix.connectPlugs('outputScale', limbSpace['scale'], force=True)

        else:

            limbCtrl.addDivider('Spaces')
            limbCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='positionSpaceW3', niceName=f'Position Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            limbCtrl.addAttr(longName='rotationSpaceW3', niceName=f'Rotation Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            limbSpaceSwitch = limbSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, limbTarget], maintainOffset=True)
            limbSpaceSwitch.weighted = True
            limbSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 1.0, 1.0)}])
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            limbSpaceSwitch.connectPlugs(limbCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')

        limbCtrl.userProperties['space'] = limbSpace.uuid()
        limbCtrl.userProperties['spaceSwitch'] = limbSpaceSwitch.uuid()

        # Setup limb blends
        #
        blender = switchCtrl['mode']
        upperBlender = setuputils.createTransformBlends(upperFKJoint, upperRIKJoint, upperBlendJoint, blender=blender)
        lowerBlender = setuputils.createTransformBlends(lowerFKJoint, lowerRIKJoint, lowerBlendJoint, blender=blender)
        extremityBlender = setuputils.createTransformBlends(extremityFKJoint, extremityRIKJoint, extremityBlendJoint, blender=blender)

        upperBlender.setName(self.formatName(subname=upperLimbName, type='blendTransform'))
        lowerBlender.setName(self.formatName(subname=lowerLimbName, type='blendTransform'))
        extremityBlender.setName(self.formatName(subname=limbTipName, type='blendTransform'))

        # Setup limb length nodes
        #
        upperLengthName = self.formatName(name=upperLimbName, subname='Length', type='plusMinusAverage')
        upperLength = self.scene.createNode('plusMinusAverage', name=upperLengthName)
        upperLength.setAttr('operation', 1)  # Addition
        upperLength.connectPlugs(switchCtrl['length[0]'], 'input1D[0]')
        upperLength.connectPlugs(switchCtrl[upperOffsetAttr], 'input1D[1]')

        lowerLengthName = self.formatName(name=lowerLimbName, subname='Length', type='plusMinusAverage')
        lowerLength = self.scene.createNode('plusMinusAverage', name=lowerLengthName)
        lowerLength.setAttr('operation', 1)  # Addition
        lowerLength.connectPlugs(switchCtrl['length[1]'], 'input1D[0]')
        lowerLength.connectPlugs(switchCtrl[lowerOffsetAttr], 'input1D[1]')

        limbLength = self.formatName(subname='Length', type='plusMinusAverage')
        limbLength = self.scene.createNode('plusMinusAverage', name=limbLength)
        limbLength.setAttr('operation', 1)  # Addition
        limbLength.connectPlugs(upperLength['output1D'], 'input1D[0]')
        limbLength.connectPlugs(lowerLength['output1D'], 'input1D[1]')

        upperWeightName = self.formatName(name=upperLimbName, subname='Weight', type='floatMath')
        upperWeight = self.scene.createNode('floatMath', name=upperWeightName)
        upperWeight.operation = 3  # Divide
        upperWeight.connectPlugs(upperLength['output1D'], 'inFloatA')
        upperWeight.connectPlugs(limbLength['output1D'], 'inFloatB')

        lowerWeightName = self.formatName(name=lowerLimbName, subname='Weight', type='floatMath')
        lowerWeight = self.scene.createNode('floatMath', name=lowerWeightName)
        lowerWeight.operation = 3  # Divide
        lowerWeight.connectPlugs(lowerLength['output1D'], 'inFloatA')
        lowerWeight.connectPlugs(limbLength['output1D'], 'inFloatB')

        # Create FK controls
        #
        upperFKMatrix = mirrorMatrix * upperLimbMatrix

        upperFKSpaceName = self.formatName(name=upperLimbName, kinemat='FK', type='space')
        upperFKSpace = self.scene.createNode('transform', name=upperFKSpaceName, parent=controlsGroup)
        upperFKSpace.setWorldMatrix(upperFKMatrix)
        upperFKSpace.freezeTransform()

        upperFKCtrlName = self.formatName(name=upperLimbName, kinemat='FK', type='control')
        upperFKCtrl = self.scene.createNode('transform', name=upperFKCtrlName, parent=upperFKSpace)
        upperFKCtrl.addDivider('Spaces')
        upperFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        upperFKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(upperFKCtrl, alias=f'{upperLimbName}_FK')

        upperFKSpaceSwitch = upperFKSpace.addSpaceSwitch([limbCtrl, motionCtrl], maintainOffset=True)
        upperFKSpaceSwitch.weighted = True
        upperFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        upperFKSpaceSwitch.connectPlugs(upperFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        upperFKSpaceSwitch.connectPlugs(upperFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

        lowerFKMatrix = mirrorMatrix * lowerLimbMatrix

        lowerFKSpaceName = self.formatName(name=lowerLimbName, kinemat='FK', type='space')
        lowerFKSpace = self.scene.createNode('transform', name=lowerFKSpaceName, parent=upperFKCtrl)
        lowerFKSpace.setWorldMatrix(lowerFKMatrix)
        lowerFKSpace.freezeTransform()

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(lowerFKMatrix * upperFKMatrix.inverse())
        lowerFKComposeMatrixName = self.formatName(name=lowerLimbName, kinemat='FK', type='composeMatrix')
        lowerFKComposeMatrix = self.scene.createNode('composeMatrix', name=lowerFKComposeMatrixName)
        lowerFKComposeMatrix.setAttr('inputTranslate', translation)
        lowerFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        lowerFKComposeMatrix.connectPlugs(upperLength['output1D'], 'inputTranslateX')
        lowerFKComposeMatrix.connectPlugs('outputMatrix', lowerFKSpace['offsetParentMatrix'])

        lowerFKCtrlName = self.formatName(name=lowerLimbName, kinemat='FK', type='control')
        lowerFKCtrl = self.scene.createNode('transform', name=lowerFKCtrlName, parent=lowerFKSpace)
        lowerFKCtrl.addDivider('Spaces')
        lowerFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        lowerFKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(lowerFKCtrl, alias=f'{lowerLimbName}_FK')

        lowerFKSpaceSwitch = lowerFKSpace.addSpaceSwitch([upperFKCtrl, motionCtrl], maintainOffset=True, skipRotateX=True, skipRotateY=True)
        lowerFKSpaceSwitch.weighted = True
        lowerFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        lowerFKSpaceSwitch.connectPlugs(lowerFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        lowerFKSpaceSwitch.connectPlugs(lowerFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')
        lowerFKSpaceSwitch.connectPlugs(upperLength['output1D'], 'target[0].targetOffsetTranslateX')

        upperInverseLength = None

        if requiresMirroring:

            upperInverseLengthName = self.formatName(name=upperLimbName, subname='InverseLength', type='floatMath')
            upperInverseLength = self.scene.createNode('floatMath', name=upperInverseLengthName)
            upperInverseLength.operation = 5  # Negate
            upperInverseLength.connectPlugs(upperLength['output1D'], 'inFloatA')
            upperInverseLength.connectPlugs('outFloat', lowerFKComposeMatrix['inputTranslateX'], force=True)
            upperInverseLength.connectPlugs('outFloat', lowerFKSpaceSwitch['target[0].targetOffsetTranslateX'], force=True)
        
        extremityFKTargetName = self.formatName(name=limbTipName, kinemat='FK', type='target')
        extremityFKTarget = self.scene.createNode('transform', name=extremityFKTargetName, parent=lowerFKCtrl)

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(limbTipMatrix * lowerLimbMatrix.inverse())
        extremityFKComposeMatrixName = self.formatName(name=limbTipName, kinemat='FK', type='composeMatrix')
        extremityFKComposeMatrix = self.scene.createNode('composeMatrix', name=extremityFKComposeMatrixName)
        extremityFKComposeMatrix.setAttr('inputTranslate', translation)
        extremityFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        extremityFKComposeMatrix.connectPlugs(lowerLength['output1D'], 'inputTranslateX')
        extremityFKComposeMatrix.connectPlugs('outputMatrix', extremityFKTarget['offsetParentMatrix'])

        lowerInverseLength = None

        if requiresMirroring:
            
            lowerInverseLengthName = self.formatName(name=lowerLimbName, subname='InverseLength', type='floatMath')
            lowerInverseLength = self.scene.createNode('floatMath', name=lowerInverseLengthName)
            lowerInverseLength.operation = 5  # Negate
            lowerInverseLength.connectPlugs(lowerLength['output1D'], 'inFloatA')
            lowerInverseLength.connectPlugs('outFloat', extremityFKComposeMatrix['inputTranslateX'], force=True)

        upperFKJoint.addConstraint('transformConstraint', [upperFKCtrl], maintainOffset=requiresMirroring)
        lowerFKJoint.addConstraint('transformConstraint', [lowerFKCtrl], maintainOffset=requiresMirroring)
        extremityFKJoint.addConstraint('transformConstraint', [extremityFKTarget], maintainOffset=requiresMirroring)

        # Add FK control shapes
        #
        upperFKShape = upperFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        upperFKShape.reorientAndScaleToFit(lowerFKCtrl)

        lowerFKShape = lowerFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        lowerFKShape.reorientAndScaleToFit(extremityFKTarget)

        supportsResizing = int(mc.about(version=True)) >= 2025

        if supportsResizing:

            # Setup upper FK shape resizing
            #
            upperHalfLengthName = self.formatName(name=upperLimbName, subname='HalfLength', type='floatMath')
            upperHalfLength = self.scene.createNode('floatMath', name=upperHalfLengthName)
            upperHalfLength.operation = 6  # Half
            upperHalfLength.connectPlugs(upperLength['output1D'], 'inFloatA')
            upperHalfLength.connectPlugs('outFloat', upperFKShape['localPositionX'])

            if requiresMirroring:

                upperInverseLength.connectPlugs('outFloat', upperHalfLength['inFloatA'], force=True)

            upperScaleLengthName = self.formatName(name=upperLimbName, subname='ScaleLength', type='divDoubleLinear')
            upperScaleLength = self.scene.createNode('divDoubleLinear', name=upperScaleLengthName)
            upperScaleLength.connectPlugs(upperLength['output1D'], 'input1')
            upperScaleLength.connectPlugs(upperFKShape['size'], 'input2')
            upperScaleLength.connectPlugs('output', upperFKShape['localScaleX'])

            # Setup lower FK shape resizing
            #
            lowerHalfLengthName = self.formatName(name=lowerLimbName, subname='HalfLength', type='floatMath')
            lowerHalfLength = self.scene.createNode('floatMath', name=lowerHalfLengthName)
            lowerHalfLength.operation = 6  # Half
            lowerHalfLength.connectPlugs(lowerLength['output1D'], 'inFloatA')
            lowerHalfLength.connectPlugs('outFloat', lowerFKShape['localPositionX'])

            if requiresMirroring:

                lowerInverseLength.connectPlugs('outFloat', lowerHalfLength['inFloatA'], force=True)

            lowerScaleLengthName = self.formatName(name=lowerLimbName, subname='ScaleLength', type='divDoubleLinear')
            lowerScaleLength = self.scene.createNode('divDoubleLinear', name=lowerScaleLengthName)
            lowerScaleLength.connectPlugs(lowerLength['output1D'], 'input1')
            lowerScaleLength.connectPlugs(lowerFKShape['size'], 'input2')
            lowerScaleLength.connectPlugs('output', lowerFKShape['localScaleX'])

        else:

            log.debug('Skipping dynamic shape resizing...')

        # Tag FK controls
        #
        upperFKCtrl.tagAsController(parent=limbCtrl, children=[lowerFKCtrl])
        lowerFKCtrl.tagAsController(parent=upperFKCtrl)

        # Check if extremity component exists
        # If so, then use the extremity matrix from that instead!
        #
        extremityComponents = self.findComponentDescendants('ExtremityComponent')
        hasExtremity = len(extremityComponents) == 1

        extremityIKMatrix = mirrorMatrix * extremityMatrix

        if hasExtremity:  # TODO: Investigate if this is even necessary anymore?

            extremityComponent = extremityComponents[0]
            extremitySpecs = extremityComponent.skeleton()
            extremityIKMatrix = mirrorMatrix * extremitySpecs[0].getNode(referenceNode=referenceNode).worldMatrix()

        # Create IK extremity control
        #
        defaultWorldSpace = 1.0 if isLeg else 0.0
        defaultLimbSpace = 1.0 if isArm else 0.0
        preEulerRotation = transformutils.decomposeTransformMatrix(extremityIKMatrix)[1]

        extremityIKSpaceName = self.formatName(name=limbTipName, kinemat='IK', type='space')
        extremityIKSpace = self.scene.createNode('transform', name=extremityIKSpaceName, parent=controlsGroup)
        extremityIKSpace.setWorldMatrix(extremityIKMatrix, skipRotate=True)
        extremityIKSpace.freezeTransform()

        extremityIKCtrlName = self.formatName(name=limbTipName, kinemat='IK', type='control')
        extremityIKCtrl = self.scene.createNode('freeform', name=extremityIKCtrlName, parent=extremityIKSpace)
        extremityIKCtrl.addPointHelper('diamond', size=(30.0 * rigScale), lineWidth=3.0, colorRGB=colorRGB)
        extremityIKCtrl.setPreEulerRotation(preEulerRotation)
        extremityIKCtrl.addDivider('Spaces')
        extremityIKCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, default=defaultWorldSpace, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW2', niceName=f'Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW3', niceName=f'Position Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW4', niceName=f'Position Space ({limbName})', attributeType='float', min=0.0, max=1.0, default=defaultLimbSpace, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW3', niceName=f'Rotation Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW4', niceName=f'Rotation Space ({limbName})', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(extremityIKCtrl, alias=f'{limbTipName}_IK')

        extremityIKOffsetCtrlName = self.formatName(name=limbTipName, kinemat='IK', subname='Offset', type='control')
        extremityIKOffsetCtrl = self.scene.createNode('transform', name=extremityIKOffsetCtrlName, parent=extremityIKCtrl)
        extremityIKOffsetCtrl.addPointHelper('cross', 'axisTripod', size=(15.0 * rigScale), colorRGB=lightColorRGB)
        extremityIKOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(extremityIKOffsetCtrl, alias=f'{limbTipName}_IK_Offset')

        extremityIKSpaceSwitch = extremityIKSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, spineCtrl, limbCtrl], maintainOffset=True)
        extremityIKSpaceSwitch.weighted = True
        extremityIKSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
        extremityIKSpaceSwitch.connectPlugs(extremityIKCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')

        extremityIKCtrl.userProperties['space'] = extremityIKSpace.uuid()
        extremityIKCtrl.userProperties['spaceSwitch'] = extremityIKSpaceSwitch.uuid()
        extremityIKCtrl.userProperties['offset'] = extremityIKOffsetCtrl.uuid()

        extremityIKCtrl.tagAsController(parent=limbCtrl, children=[extremityIKOffsetCtrl])
        extremityIKOffsetCtrl.tagAsController(parent=extremityIKCtrl)

        # Update preferred IK angles
        #
        lowerAngle = math.degrees(lowerIKJoint.eulerRotation().z)
        lowerAngleSign = math.copysign(1.0, lowerAngle)
        preferredAngle = lowerAngle if (abs(lowerAngle) >= 1.0) else lowerAngleSign

        lowerIKJoint.preferredAngleZ = preferredAngle
        lowerRIKJoint.preferredAngleZ = preferredAngle

        # Create IK emulators
        #
        limbDecomposeMatrixName = self.formatName(type='decomposeMatrix')
        limbDecomposeMatrix = self.scene.createNode('decomposeMatrix', name=limbDecomposeMatrixName)
        limbDecomposeMatrix.connectPlugs(limbCtrl[f'worldMatrix[{limbCtrl.instanceNumber()}]'], 'inputMatrix')

        upperRestMatrixName = self.formatName(name=upperLimbName, subname='Rest', type='composeMatrix')
        upperRestMatrix = self.scene.createNode('composeMatrix', name=upperRestMatrixName)
        upperRestMatrix.connectPlugs(limbDecomposeMatrix['outputTranslate'], 'inputTranslate')
        upperRestMatrix.useEulerRotation = True
        upperRestMatrix.inputRotate = upperIKJoint.getAttr('rotate')
        upperRestMatrix.connectPlugs(limbDecomposeMatrix['outputScale'], 'inputScale')

        lowerRestMatrixName = self.formatName(name=lowerLimbName, subname='Rest', type='composeMatrix')
        lowerRestMatrix = self.scene.createNode('composeMatrix', name=lowerRestMatrixName)
        lowerRestMatrix.connectPlugs(upperLength['output1D'], 'inputTranslateX')
        lowerRestMatrix.useEulerRotation = True
        lowerRestMatrix.inputRotateZ = lowerIKJoint.getAttr('rotateZ')
        lowerRestMatrix.connectPlugs(limbDecomposeMatrix['outputScale'], 'inputScale')

        extremityRestMatrixName = self.formatName(name=limbTipName, subname='Rest', type='composeMatrix')
        extremityRestMatrix = self.scene.createNode('composeMatrix', name=extremityRestMatrixName)
        extremityRestMatrix.connectPlugs(lowerLength['output1D'], 'inputTranslateX')
        extremityRestMatrix.connectPlugs(limbDecomposeMatrix['outputScale'], 'inputScale')

        limbIKEmulatorName = self.formatName(type='ikEmulator')
        limbIKEmulator = self.scene.createNode('ikEmulator', name=limbIKEmulatorName)
        limbIKEmulator.forwardAxis = 0  # X
        limbIKEmulator.forwardAxisFlip = False
        limbIKEmulator.upAxis = 1  # Y
        limbIKEmulator.upAxisFlip = True
        limbIKEmulator.poleType = 2  # Matrix
        limbIKEmulator.segmentScaleCompensate = True
        limbIKEmulator.connectPlugs(upperRestMatrix['outputMatrix'], 'restMatrix[0]')
        limbIKEmulator.connectPlugs(lowerRestMatrix['outputMatrix'], 'restMatrix[1]')
        limbIKEmulator.connectPlugs(extremityRestMatrix['outputMatrix'], 'restMatrix[2]')
        limbIKEmulator.connectPlugs(switchCtrl['stretch'], 'stretch')
        limbIKEmulator.connectPlugs(switchCtrl['soften'], 'soften')
        limbIKEmulator.connectPlugs(switchCtrl['twist'], 'twist')
        limbIKEmulator.connectPlugs(extremityIKCtrl[f'worldMatrix[{extremityIKCtrl.instanceNumber()}]'], 'goal')

        ikHandleTargetName = self.formatName(kinemat='IK', type='target')
        ikHandleTarget = self.scene.createNode('transform', name=ikHandleTargetName, parent=privateGroup)
        ikHandleTarget.displayLocalAxis = True
        ikHandleTarget.inheritsTransform = False
        ikHandleTarget.connectPlugs(limbIKEmulator['softGoal'], 'translate')

        limbRIKEmulatorName = self.formatName(subname='Reverse', type='ikEmulator')
        limbRIKEmulator = self.scene.createNode('ikEmulator', name=limbRIKEmulatorName)
        limbRIKEmulator.forwardAxis = 0  # X
        limbRIKEmulator.forwardAxisFlip = False
        limbRIKEmulator.upAxis = 1  # Y
        limbRIKEmulator.upAxisFlip = True
        limbRIKEmulator.poleType = 2  # Matrix
        limbRIKEmulator.connectPlugs(upperRestMatrix['outputMatrix'], 'restMatrix[0]')
        limbRIKEmulator.connectPlugs(lowerRestMatrix['outputMatrix'], 'restMatrix[1]')
        limbRIKEmulator.connectPlugs(extremityRestMatrix['outputMatrix'], 'restMatrix[2]')
        limbRIKEmulator.connectPlugs(switchCtrl['pin'], 'pin')
        limbRIKEmulator.connectPlugs(switchCtrl['stretch'], 'stretch')
        limbRIKEmulator.connectPlugs(switchCtrl['soften'], 'soften')
        limbRIKEmulator.connectPlugs(switchCtrl['twist'], 'twist')
        limbRIKEmulator.connectPlugs(extremityIKCtrl[f'worldMatrix[{extremityIKCtrl.instanceNumber()}]'], 'goal')

        # Connect emulators to IK joints
        #
        upperIKMatrixName = self.formatName(name=upperLimbName, subname='IK', type='decomposeMatrix')
        upperIKMatrix = self.scene.createNode('decomposeMatrix', name=upperIKMatrixName)
        upperIKMatrix.connectPlugs(limbIKEmulator['outMatrix[0]'], 'inputMatrix')
        upperIKMatrix.connectPlugs(upperIKJoint['rotateOrder'], 'inputRotateOrder')
        upperIKMatrix.connectPlugs('outputTranslate', upperIKJoint['translate'])
        upperIKMatrix.connectPlugs('outputRotate', upperIKJoint['rotate'])
        upperIKMatrix.connectPlugs('outputScale', upperIKJoint['scale'])

        lowerIKMatrixName = self.formatName(name=lowerLimbName, subname='IK', type='decomposeMatrix')
        lowerIKMatrix = self.scene.createNode('decomposeMatrix', name=lowerIKMatrixName)
        lowerIKMatrix.connectPlugs(limbIKEmulator['outMatrix[1]'], 'inputMatrix')
        lowerIKMatrix.connectPlugs(lowerIKJoint['rotateOrder'], 'inputRotateOrder')
        lowerIKMatrix.connectPlugs('outputTranslate', lowerIKJoint['translate'])
        lowerIKMatrix.connectPlugs('outputRotate', lowerIKJoint['rotate'])
        lowerIKMatrix.connectPlugs('outputScale', lowerIKJoint['scale'])

        extremityIKName = self.formatName(name=limbTipName, subname='IK', type='decomposeMatrix')
        extremityIKMatrix = self.scene.createNode('decomposeMatrix', name=extremityIKName)
        extremityIKMatrix.connectPlugs(limbIKEmulator['outMatrix[2]'], 'inputMatrix')
        extremityIKMatrix.connectPlugs(extremityIKJoint['rotateOrder'], 'inputRotateOrder')
        extremityIKMatrix.connectPlugs('outputTranslate', extremityIKJoint['translate'])
        extremityIKMatrix.connectPlugs('outputRotate', extremityIKJoint['rotate'])
        extremityIKMatrix.connectPlugs('outputScale', extremityIKJoint['scale'])

        # Connect emulator to RIK joints
        #
        upperRIKMatrixName = self.formatName(name=upperLimbName, subname='RIK', type='decomposeMatrix')
        upperRIKMatrix = self.scene.createNode('decomposeMatrix', name=upperRIKMatrixName)
        upperRIKMatrix.connectPlugs(limbRIKEmulator['outMatrix[0]'], 'inputMatrix')
        upperRIKMatrix.connectPlugs(upperRIKJoint['rotateOrder'], 'inputRotateOrder')
        upperRIKMatrix.connectPlugs('outputTranslate', upperRIKJoint['translate'])
        upperRIKMatrix.connectPlugs('outputRotate', upperRIKJoint['rotate'])
        upperRIKMatrix.connectPlugs('outputScale', upperRIKJoint['scale'])

        lowerRIKMatrixName = self.formatName(name=lowerLimbName, subname='RIK', type='decomposeMatrix')
        lowerRIKMatrix = self.scene.createNode('decomposeMatrix', name=lowerRIKMatrixName)
        lowerRIKMatrix.connectPlugs(limbRIKEmulator['outMatrix[1]'], 'inputMatrix')
        lowerRIKMatrix.connectPlugs(lowerRIKJoint['rotateOrder'], 'inputRotateOrder')
        lowerRIKMatrix.connectPlugs('outputTranslate', lowerRIKJoint['translate'])
        lowerRIKMatrix.connectPlugs('outputRotate', lowerRIKJoint['rotate'])
        lowerRIKMatrix.connectPlugs('outputScale', lowerRIKJoint['scale'])

        extremityRIKName = self.formatName(name=limbTipName, subname='RIK', type='decomposeMatrix')
        extremityRIKMatrix = self.scene.createNode('decomposeMatrix', name=extremityRIKName)
        extremityRIKMatrix.connectPlugs(limbRIKEmulator['outMatrix[2]'], 'inputMatrix')
        extremityRIKMatrix.connectPlugs(extremityRIKJoint['rotateOrder'], 'inputRotateOrder')
        extremityRIKMatrix.connectPlugs('outputTranslate', extremityRIKJoint['translate'])
        extremityRIKMatrix.connectPlugs('outputRotate', extremityRIKJoint['rotate'])
        extremityRIKMatrix.connectPlugs('outputScale', extremityRIKJoint['scale'])

        # Calculate default PV matrix
        #
        upVector = -((transformutils.breakMatrix(upperLimbMatrix, normalize=True)[1] * 0.5) + (transformutils.breakMatrix(lowerLimbMatrix, normalize=True)[1] * 0.5)).normal()
        forwardVector = (transformutils.breakMatrix(extremityMatrix)[3] - limbOrigin).normal()
        rightVector = (forwardVector ^ upVector).normal()
        poleVector = (rightVector ^ forwardVector).normal()

        upperVector = (transformutils.breakMatrix(lowerLimbMatrix)[3] - limbOrigin)
        upperDot = forwardVector * upperVector

        poleOrigin = limbOrigin + (forwardVector * upperDot)
        polePosition = poleOrigin + (poleVector * sum(limbLengths))
        poleMatrix = transformutils.createTranslateMatrix(polePosition)

        # Create PV follow system
        #
        followJointName = self.formatName(subname='Follow', type='joint')
        followJoint = self.scene.createNode('joint', name=followJointName, parent=jointsGroup)
        followJoint.addConstraint('pointConstraint', [limbCtrl])

        followTipJointName = self.formatName(subname='FollowTip', type='joint')
        followTipJoint = self.scene.createNode('joint', name=followTipJointName, parent=followJoint)
        followTipJoint.connectPlugs(limbIKEmulator['softDistance'], followTipJoint['translateX'])
        followTipJoint.connectPlugs(followJoint['scale'], 'scale')

        followHalfLengthName = self.formatName(subname='HalfFollow', type='floatMath')
        followHalfLength = self.scene.createNode('floatMath', name=followHalfLengthName)
        followHalfLength.operation = 6  # Half
        followHalfLength.connectPlugs(followTipJoint['translateX'], 'inDistanceA')

        followTargetName = self.formatName(subname='Follow', type='target')
        followTarget = self.scene.createNode('transform', name=followTargetName, parent=followJoint)
        followTarget.displayLocalAxis = True
        followTarget.connectPlugs(followHalfLength['outDistance'], 'translateX')
        followTarget.addConstraint('scaleConstraint', [limbCtrl])

        forwardVectorMultMatrixName = self.formatName(subname='Forward', type='multiplyVectorByMatrix')
        forwardVectorMultMatrix = self.scene.createNode('multiplyVectorByMatrix', name=forwardVectorMultMatrixName)
        forwardVectorMultMatrix.connectPlugs(limbIKEmulator['softVector'], 'input')
        forwardVectorMultMatrix.connectPlugs(waistCtrl[f'worldInverseMatrix[{waistCtrl.instanceNumber()}]'], 'matrix')

        defaultSampleInput = forwardVector * waistCtrl.worldInverseMatrix()
        defaultSampleOutput = -poleVector * waistCtrl.worldInverseMatrix()
        followSamples = self.__default_rbf_samples__[componentSide]

        followRBFSolverName = self.formatName(subname='Follow', type='rbfSolver')
        followRBFSolver = self.scene.createNode('rbfSolver', name=followRBFSolverName)
        followRBFSolver.inputType = 0  # Euclidean
        followRBFSolver.function = 1  # Gaussian
        followRBFSolver.setAttr('sample[0]', {'sampleName': 'Default', 'sampleInputTranslate': defaultSampleInput, 'sampleOutputTranslate': -defaultSampleOutput})
        followRBFSolver.setAttr('sample[1]', followSamples[0])
        followRBFSolver.setAttr('sample[2]', followSamples[1])
        followRBFSolver.setAttr('sample[3]', followSamples[2])
        followRBFSolver.setAttr('sample[4]', followSamples[3])
        followRBFSolver.setAttr('sample[5]', followSamples[4])
        followRBFSolver.setAttr('sample[6]', followSamples[5])
        followRBFSolver.connectPlugs(forwardVectorMultMatrix['output'], 'inputTranslate')

        followUpVectorMultMatrixName = self.formatName(subname='Follow', type='multiplyVectorByMatrix')
        followUpVectorMultMatrix = self.scene.createNode('multiplyVectorByMatrix', name=followUpVectorMultMatrixName)
        followUpVectorMultMatrix.connectPlugs(followRBFSolver['outputTranslate'], 'input')
        followUpVectorMultMatrix.connectPlugs(waistCtrl[f'worldMatrix[{waistCtrl.instanceNumber()}]'], 'matrix')

        followConstraint = followJoint.addConstraint('aimConstraint', [ikHandleTarget], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, -1.0, 0.0), worldUpType=3, worldUpVector=(0.0, 1.0, 0.0))
        followConstraint.connectPlugs(followUpVectorMultMatrix['output'], 'worldUpVector')

        # Create PV controller
        #
        limbPVSpaceName = self.formatName(subname='PV', type='space')
        limbPVSpace = self.scene.createNode('transform', name=limbPVSpaceName, parent=controlsGroup)
        limbPVSpace.setWorldMatrix(poleMatrix)

        limbPVCtrlName = self.formatName(subname='PV', type='control')
        limbPVCtrl = self.scene.createNode('transform', name=limbPVCtrlName, parent=limbPVSpace)
        limbPVCtrl.addPointHelper('sphere', 'centerMarker', size=(5.0 * rigScale), side=componentSide)
        limbPVCtrl.addDivider('Spaces')
        limbPVCtrl.addAttr(longName='transformSpaceW0', niceName='Transform Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW1', niceName='Transform Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW2', niceName='Transform Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW3', niceName=f'Transform Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW4', niceName=f'Transform Space ({limbName})', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW5', niceName='Transform Space (Auto)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW6', niceName=f'Transform Space ({limbTipName})', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.connectPlugs(f'worldMatrix[{limbPVCtrl.instanceNumber()}]', limbIKEmulator['poleMatrix'])
        limbPVCtrl.connectPlugs(f'worldMatrix[{limbPVCtrl.instanceNumber()}]', limbRIKEmulator['poleMatrix'])
        limbPVCtrl.prepareChannelBoxForAnimation()
        limbPVCtrl.tagAsController(parent=extremityIKCtrl)
        self.publishNode(limbPVCtrl, alias=f'{limbName}_PV')

        limbPVSpaceSwitch = limbPVSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, spineCtrl, limbCtrl, followTarget, extremityIKCtrl], weighted=True, maintainOffset=True)
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW0'], 'target[0].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW1'], 'target[1].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW2'], 'target[2].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW3'], 'target[3].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW4'], 'target[4].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW5'], 'target[5].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW6'], 'target[6].targetWeight')

        limbPVCtrl.userProperties['space'] = limbPVSpace.uuid()
        limbPVCtrl.userProperties['spaceSwitch'] = limbPVSpaceSwitch.uuid()

        # Create hinge controls
        #
        hingeBendTargetName = self.formatName(name=hingeName, subname='Bend', type='target')
        hingeBendTarget = self.scene.createNode('transform', name=hingeBendTargetName, parent=privateGroup)
        hingeBendTarget.displayLocalAxis = True
        hingeBendTarget.visibility = False
        hingeBendTarget.addConstraint('pointConstraint', [lowerBlendJoint])
        hingeBendTarget.addConstraint('orientConstraint', [upperBlendJoint, lowerBlendJoint])
        hingeBendTarget.addConstraint('scaleConstraint', [limbCtrl])

        hingeStraightTargetName = self.formatName(name=hingeName, subname='Straight', type='target')
        hingeStraightTarget = self.scene.createNode('transform', name=hingeStraightTargetName, parent=privateGroup)
        hingeStraightTarget.displayLocalAxis = True
        hingeStraightTarget.visibility = False
        hingeStraightTarget.addConstraint('aimConstraint', [extremityBlendJoint], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=upperBlendJoint)
        hingeStraightTarget.addConstraint('scaleConstraint', [limbCtrl])

        constraint = hingeStraightTarget.addConstraint('pointConstraint', [upperBlendJoint, extremityBlendJoint])
        targets = constraint.targets()
        constraint.connectPlugs(upperWeight['outFloat'], targets[1].driver())  # These are flipped for a reason!
        constraint.connectPlugs(lowerWeight['outFloat'], targets[0].driver())  # These are flipped for a reason!

        hingeSpaceName = self.formatName(name=hingeName, type='space')
        hingeSpace = self.scene.createNode('transform', name=hingeSpaceName, parent=controlsGroup)
        hingeSpace.copyTransform(hingeBendTarget)
        hingeSpace.freezeTransform()

        hingeCtrlName = self.formatName(name=hingeName, type='control')
        hingeCtrl = self.scene.createNode('transform', name=hingeCtrlName, parent=hingeSpace)
        hingeCtrl.addPointHelper('square', size=(20.0 * rigScale), localRotate=(45.0, 0.0, 0.0), lineWidth=4.0, colorRGB=darkColorRGB)
        hingeCtrl.addDivider('Spaces')
        hingeCtrl.addAttr(longName='straighten', niceName='Straighten (Off/On)', attributeType='distance', min=0.0, max=1.0, default=0.0, keyable=True)
        hingeCtrl.prepareChannelBoxForAnimation()
        self.publishNode(hingeCtrl, alias=hingeName)

        hingeSpaceSwitch = hingeSpace.addSpaceSwitch([hingeBendTarget, hingeStraightTarget])
        hingeSpaceSwitch.weighted = True
        hingeSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        hingeSpaceSwitch.connectPlugs(hingeCtrl['straighten'], 'target[0].targetWeight')
        hingeSpaceSwitch.connectPlugs(hingeCtrl['straighten'], 'target[1].targetWeight')

        hingeCtrl.userProperties['space'] = hingeSpace.uuid()
        hingeCtrl.userProperties['spaceSwitch'] = hingeSpaceSwitch.uuid()

        # Check if hinge was enabled
        # If so, update bind pose on export joint!
        #
        hingeEnabled = bool(hingeSpec.enabled)

        if hingeEnabled:

            hingeExportJoint = hingeSpec.getNode(referenceNode=referenceNode)
            hingeExportJoint.copyTransform(hingeCtrl, skipScale=True)

            hingeSpec.cacheNode(delete=False)

        # Create PV handle curve
        #
        limbPVShapeName = self.formatName(kinemat='PV', subname='Handle', type='control')
        limbPVShape = self.scene.createNode('nurbsCurve', name=f'{limbPVShapeName}Shape', parent=limbPVCtrl)
        limbPVShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
        limbPVShape.useObjectColor = 2
        limbPVShape.wireColorRGB = lightColorRGB

        limbPVCurveFromPointName = self.formatName(kinemat='PV', subname='Handle', type='curveFromPoint')
        limbPVCurveFromPoint = self.scene.createNode('curveFromPoint', name=limbPVCurveFromPointName)
        limbPVCurveFromPoint.degree = 1
        limbPVCurveFromPoint.connectPlugs(limbPVShape[f'worldMatrix[{limbPVShape.instanceNumber()}]'], 'inputMatrix[0]')
        limbPVCurveFromPoint.connectPlugs(hingeCtrl[f'worldMatrix[{hingeCtrl.instanceNumber()}]'], 'inputMatrix[1]')
        limbPVCurveFromPoint.connectPlugs(limbPVShape[f'parentInverseMatrix[{limbPVShape.instanceNumber()}]'], 'parentInverseMatrix')
        limbPVCurveFromPoint.connectPlugs('outputCurve', limbPVShape['create'])

        # Create target joints
        #
        upperJointName = self.formatName(name=upperLimbName, type='joint')
        upperJoint = self.scene.createNode('joint', name=upperJointName, parent=jointsGroup)
        upperJoint.addConstraint('pointConstraint', [upperBlendJoint])
        upperJoint.addConstraint('aimConstraint', [hingeCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=upperBlendJoint)
        upperJoint.connectPlugs(upperBlendJoint['scale'], 'scale')

        lowerJointName = self.formatName(name=lowerLimbName, type='joint')
        lowerJoint = self.scene.createNode('joint', name=lowerJointName, parent=upperJoint)
        lowerJoint.addConstraint('pointConstraint', [hingeCtrl], skipTranslateY=True, skipTranslateZ=True)
        lowerJoint.addConstraint('aimConstraint', [extremityBlendJoint], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=lowerBlendJoint)
        lowerJoint.connectPlugs(lowerBlendJoint['scale'], 'scale')

        extremityJointName = self.formatName(name=limbTipName, type='joint')
        extremityJoint = self.scene.createNode('joint', name=extremityJointName, parent=lowerJoint)
        extremityJoint.addConstraint('pointConstraint', [extremityBlendJoint], skipTranslateY=True, skipTranslateZ=True)
        extremityJoint.connectPlugs(extremityBlendJoint['scale'], 'scale')

        # Cache kinematic components
        #
        self.userProperties['switchControl'] = switchCtrl.uuid()

        self.userProperties['fkJoints'] = (upperFKJoint.uuid(), lowerFKJoint.uuid(), extremityFKJoint.uuid())
        self.userProperties['fkControls'] = (upperFKCtrl.uuid(), lowerFKCtrl.uuid(), extremityFKTarget.uuid())

        self.userProperties['rikJoints'] = (upperRIKJoint.uuid(), lowerRIKJoint.uuid(), extremityRIKJoint.uuid())
        self.userProperties['rikEmulator'] = limbRIKEmulator.uuid()
        self.userProperties['ikJoints'] = (upperIKJoint.uuid(), lowerIKJoint.uuid(), extremityIKJoint.uuid())
        self.userProperties['ikEmulator'] = limbIKEmulator.uuid()
        self.userProperties['ikControls'] = (limbCtrl.uuid(), extremityIKCtrl.uuid())
        self.userProperties['ikTarget'] = ikHandleTarget.uuid()
        self.userProperties['pvControl'] = limbPVCtrl.uuid()
        self.userProperties['hingeControls'] = (hingeCtrl.uuid(),)

        self.userProperties['blendJoints'] = (upperBlendJoint.uuid(), lowerBlendJoint.uuid(), extremityBlendJoint.uuid())
        self.userProperties['targetJoints'] = (upperJoint.uuid(), lowerJoint.uuid(), extremityJoint.uuid())

        # Check if twist is enabled
        #
        if self.twistEnabled:

            # Add extra hinge attributes
            #
            hingeCtrl.addAttr(longName='handleOffset', attributeType='distance', min=0.0, keyable=True)
            hingeCtrl.addAttr(longName='handleInset', attributeType='distance', min=0.0, keyable=True)

            # Create upper twist controller
            #
            upperLimbSpaceName = self.formatName(name=upperLimbName, type='space')
            upperLimbSpace = self.scene.createNode('transform', name=upperLimbSpaceName, parent=controlsGroup)
            upperLimbSpace.copyTransform(upperJoint)
            upperLimbSpace.freezeTransform()

            upperLimbCtrlName = self.formatName(name=upperLimbName, type='control')
            upperLimbCtrl = self.scene.createNode('transform', name=upperLimbCtrlName, parent=upperLimbSpace)
            upperLimbCtrl.addPointHelper('tearDrop', 'centerMarker', size=(20.0 * rigScale), localRotate=(90.0, 0.0, 0.0), lineWidth=3.0, colorRGB=darkColorRGB)
            upperLimbCtrl.addDivider('Settings')
            upperLimbCtrl.addAttr(longName='inheritsTwist', attributeType='angle', min=0.0, max=1.0, default=1.0, keyable=True)
            upperLimbCtrl.prepareChannelBoxForAnimation()
            self.publishNode(upperLimbCtrl, alias=upperLimbName)

            limbRollSolverName = self.formatName(name=upperLimbName, subname='Roll', type='twistSolver')
            limbRollSolver = self.scene.createNode('twistSolver', name=limbRollSolverName)
            limbRollSolver.forwardAxis = 0  # X
            limbRollSolver.upAxis = 2  # Z
            limbRollSolver.inverse = True
            limbRollSolver.startOffsetMatrix = mirrorMatrix
            limbRollSolver.connectPlugs(limbTarget[f'worldMatrix[{limbTarget.instanceNumber()}]'], 'startMatrix')
            limbRollSolver.connectPlugs(upperJoint[f'worldMatrix[{upperJoint.instanceNumber()}]'], 'endMatrix')

            limbRollEnvelopeName = self.formatName(name=upperLimbName, subname='RollEnvelope', type='floatMath')
            limbRollEnvelope = self.scene.createNode('floatMath', name=limbRollEnvelopeName)
            limbRollEnvelope.setAttr('operation', 2)  # Multiply
            limbRollEnvelope.connectPlugs(limbRollSolver['roll'], 'inAngleA')
            limbRollEnvelope.connectPlugs(upperLimbCtrl['inheritsTwist'], 'inAngleB')

            limbRollConstraint = upperLimbSpace.addConstraint('transformConstraint', [upperJoint])
            limbRollConstraint.connectPlugs(limbRollEnvelope['outAngle'], 'target[0].targetOffsetRotateX')

            self.userProperties['rollSolver'] = limbRollSolver.uuid()

            # Create upper-limb out-handle control
            #
            upperLimbOutSpaceName = self.formatName(name=upperLimbName, subname='Out', type='space')
            upperLimbOutSpace = self.scene.createNode('transform', name=upperLimbOutSpaceName, parent=controlsGroup)
            upperLimbOutSpace.setWorldMatrix(upperLimbMatrix)
            upperLimbOutSpace.freezeTransform()

            upperLimbOutCtrlName = self.formatName(name=upperLimbName, subname='Out', type='control')
            upperLimbOutCtrl = self.scene.createNode('transform', name=upperLimbOutCtrlName, parent=upperLimbOutSpace)
            upperLimbOutCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((5.0 * rigScale), 0.0, 0.0), localRotate=(0.0, 0.0, 180.0), side=componentSide)
            upperLimbOutCtrl.addDivider('Spaces')
            upperLimbOutCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            upperLimbOutCtrl.prepareChannelBoxForAnimation()
            self.publishNode(upperLimbOutCtrl, alias=f'{upperLimbName}_Out')

            upperLimbOutSpaceSwitch = upperLimbOutSpace.addSpaceSwitch([upperLimbCtrl, limbCtrl], maintainOffset=False)
            upperLimbOutSpaceSwitch.weighted = True
            upperLimbOutSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            upperLimbOutSpaceSwitch.connectPlugs(upperLimbOutCtrl['localOrGlobal'], 'target[0].targetWeight')
            upperLimbOutSpaceSwitch.connectPlugs(upperLimbOutCtrl['localOrGlobal'], 'target[1].targetWeight')
            upperLimbOutSpaceSwitch.connectPlugs(hingeCtrl['handleInset'], 'target[0].targetOffsetTranslateX')
            upperLimbOutSpaceSwitch.connectPlugs(hingeCtrl['handleInset'], 'target[1].targetOffsetTranslateX')

            upperLimbOutCtrl.userProperties['space'] = upperLimbOutSpace.uuid()
            upperLimbOutCtrl.userProperties['spaceSwitch'] = upperLimbOutSpaceSwitch.uuid()

            # Create upper-limb out-handle proxy curve
            #
            upperLimbCurveName = self.formatName(name=upperLimbName, subname='Handle', type='nurbsCurve')
            upperLimbCurve = self.scene.createNode('nurbsCurve', name=f'{upperLimbCurveName}Shape', parent=upperLimbOutCtrl)
            upperLimbCurve.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            upperLimbCurve.template = True

            upperLimbCurveFromPointName = self.formatName(name=upperLimbName, subname='Handle', type='curveFromPoint')
            upperLimbCurveFromPoint = self.scene.createNode('curveFromPoint', name=upperLimbCurveFromPointName)
            upperLimbCurveFromPoint.degree = 1
            upperLimbCurveFromPoint.connectPlugs(upperLimbCtrl[f'worldMatrix[{upperLimbCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            upperLimbCurveFromPoint.connectPlugs(upperLimbOutCtrl[f'worldMatrix[{upperLimbOutCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            upperLimbCurveFromPoint.connectPlugs(upperLimbCurve[f'parentInverseMatrix[{upperLimbCurve.instanceNumber()}]'], 'parentInverseMatrix')
            upperLimbCurveFromPoint.connectPlugs('outputCurve', upperLimbCurve['create'])

            upperLimbOutCtrl.userProperties['curve'] = upperLimbCurve.uuid()
            upperLimbOutCtrl.userProperties['curveFromPoint'] = upperLimbCurveFromPoint.uuid()

            # Create hinge-in control
            #
            hingeInCtrlName = self.formatName(name=hingeName, subname='In', type='control')
            hingeInCtrl = self.scene.createNode('transform', name=hingeInCtrlName, parent=hingeCtrl)
            hingeInCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((-5.0 * rigScale), 0.0, 0.0), colorRGB=darkColorRGB)
            hingeInCtrl.hideAttr('rotate')
            hingeInCtrl.prepareChannelBoxForAnimation()
            self.publishNode(hingeInCtrl, alias=f'{hingeName}_In')

            hingeInNegateName = self.formatName(name=hingeName, subname='In', type='floatMath')
            hingeInNegate = self.scene.createNode('floatMath', name=hingeInNegateName)
            hingeInNegate.setAttr('operation', 5)  # Negate
            hingeInNegate.connectPlugs(hingeCtrl['handleOffset'], 'inDistanceA')

            hingeInMatrixName = self.formatName(name=hingeName, subname='In', type='composeMatrix')
            hingeInMatrix = self.scene.createNode('composeMatrix', name=hingeInMatrixName)
            hingeInMatrix.connectPlugs(hingeInNegate['outDistance'], 'inputTranslateX')
            hingeInMatrix.connectPlugs('outputMatrix', hingeInCtrl['offsetParentMatrix'])

            # Create hinge-out control
            #
            hingeOutCtrlName = self.formatName(name=hingeName, subname='Out', type='control')
            hingeOutCtrl = self.scene.createNode('transform', name=hingeOutCtrlName, parent=hingeCtrl)
            hingeOutCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((5.0 * rigScale), 0.0, 0.0), localRotate=(0.0, 0.0, 180.0), colorRGB=darkColorRGB)
            hingeOutCtrl.hideAttr('rotate')
            hingeOutCtrl.prepareChannelBoxForAnimation()
            self.publishNode(hingeOutCtrl, alias=f'{hingeName}_Out')

            hingeCtrl.userProperties['inHandle'] = hingeInCtrl.uuid()
            hingeCtrl.userProperties['outHandle'] = hingeOutCtrl.uuid()

            hingeOutMatrixName = self.formatName(name=hingeName, subname='Out', type='composeMatrix')
            hingeOutMatrix = self.scene.createNode('composeMatrix', name=hingeOutMatrixName)
            hingeOutMatrix.connectPlugs(hingeCtrl['handleOffset'], 'inputTranslateX')
            hingeOutMatrix.connectPlugs('outputMatrix', hingeOutCtrl['offsetParentMatrix'])

            # Create hinge proxy curve
            #
            hingeHandleCurveName = self.formatName(name=hingeName, subname='Handle', type='nurbsCurve')
            hingeHandleCurve = self.scene.createNode('nurbsCurve', name=f'{hingeHandleCurveName}Shape', parent=upperLimbCtrl)
            hingeHandleCurve.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            hingeHandleCurve.template = True

            hingeHandleCurveFromPointName = self.formatName(name=hingeName, subname='Handle', type='curveFromPoint')
            hingeHandleCurveFromPoint = self.scene.createNode('curveFromPoint', name=hingeHandleCurveFromPointName)
            hingeHandleCurveFromPoint.degree = 1
            hingeHandleCurveFromPoint.connectPlugs(hingeInCtrl[f'worldMatrix[{hingeInCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            hingeHandleCurveFromPoint.connectPlugs(hingeCtrl[f'worldMatrix[{hingeCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            hingeHandleCurveFromPoint.connectPlugs(hingeOutCtrl[f'worldMatrix[{hingeOutCtrl.instanceNumber()}]'], 'inputMatrix[2]')
            hingeHandleCurveFromPoint.connectPlugs(hingeHandleCurve[f'parentInverseMatrix[{hingeHandleCurve.instanceNumber()}]'], 'parentInverseMatrix')
            hingeHandleCurveFromPoint.connectPlugs('outputCurve', hingeHandleCurve['create'])

            hingeCtrl.userProperties['curve'] = hingeHandleCurve.uuid()
            hingeCtrl.userProperties['curveFromPoint'] = hingeHandleCurveFromPoint.uuid()

            # Create lower-limb in-handle control
            #
            lowerLimbInSpaceName = self.formatName(name=limbTipName, subname='In', type='space')
            lowerLimbInSpace = self.scene.createNode('transform', name=lowerLimbInSpaceName, parent=controlsGroup)
            lowerLimbInSpace.copyTransform(extremityJoint)
            lowerLimbInSpace.freezeTransform()

            lowerLimbInCtrlName = self.formatName(name=limbTipName, subname='In', type='control')
            lowerLimbInCtrl = self.scene.createNode('transform', name=lowerLimbInCtrlName, parent=lowerLimbInSpace)
            lowerLimbInCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((-5.0 * rigScale), 0.0, 0.0), side=componentSide)
            lowerLimbInCtrl.addDivider('Spaces')
            lowerLimbInCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            lowerLimbInCtrl.prepareChannelBoxForAnimation()
            self.publishNode(lowerLimbInCtrl, alias=f'{limbTipName}_In')

            lowerLimbInNegateName = self.formatName(name=limbTipName, subname='In', type='floatMath')
            lowerLimbInNegate = self.scene.createNode('floatMath', name=lowerLimbInNegateName)
            lowerLimbInNegate.setAttr('operation', 5)  # Negate
            lowerLimbInNegate.connectPlugs(hingeCtrl['handleInset'], 'inDistanceA')

            lowerLimbInSpaceSwitch = lowerLimbInSpace.addSpaceSwitch([extremityJoint], maintainOffset=False)
            lowerLimbInSpaceSwitch.weighted = True
            lowerLimbInSpaceSwitch.setAttr('target[0]', {'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (True, True, True)})
            lowerLimbInSpaceSwitch.connectPlugs(lowerLimbInCtrl['localOrGlobal'], 'target[0].targetWeight')
            lowerLimbInSpaceSwitch.connectPlugs(lowerLimbInNegate['outDistance'], 'target[0].targetOffsetTranslateX')

            lowerLimbInCtrl.userProperties['negate'] = lowerLimbInNegate.uuid()
            lowerLimbInCtrl.userProperties['space'] = lowerLimbInSpace.uuid()
            lowerLimbInCtrl.userProperties['spaceSwitch'] = lowerLimbInSpaceSwitch.uuid()

            hingeCtrl.userProperties['otherHandles'] = (upperLimbOutCtrl.uuid(), lowerLimbInCtrl.uuid())

            # Create lower-out proxy curve handles
            #
            lowerLimbCurveName = self.formatName(name=lowerLimbName, subname='Handle', type='nurbsCurve')
            lowerLimbCurve = self.scene.createNode('nurbsCurve', name=f'{lowerLimbCurveName}Shape', parent=lowerLimbInCtrl)
            lowerLimbCurve.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            lowerLimbCurve.template = True

            lowerLimbCurveFromPointName = self.formatName(name=lowerLimbName, subname='Handle', type='curveFromPoint')
            lowerLimbCurveFromPoint = self.scene.createNode('curveFromPoint', name=lowerLimbCurveFromPointName)
            lowerLimbCurveFromPoint.degree = 1
            lowerLimbCurveFromPoint.connectPlugs(extremityJoint[f'worldMatrix[{extremityJoint.instanceNumber()}]'], 'inputMatrix[0]')
            lowerLimbCurveFromPoint.connectPlugs(lowerLimbInCtrl[f'worldMatrix[{lowerLimbInCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            lowerLimbCurveFromPoint.connectPlugs(lowerLimbCurve[f'parentInverseMatrix[{lowerLimbCurve.instanceNumber()}]'], 'parentInverseMatrix')
            lowerLimbCurveFromPoint.connectPlugs('outputCurve', lowerLimbCurve['create'])

            lowerLimbCurve.userProperties['curve'] = lowerLimbCurve.uuid()
            lowerLimbCurve.userProperties['curveFromPoint'] = lowerLimbCurveFromPoint.uuid()

            # Create twist curve
            #
            segmentNames = (upperLimbName, lowerLimbName)
            segmentSpecs = (upperLimbSpec, lowerLimbSpec)
            segmentTwistSpecs = (upperTwistSpecs, lowerTwistSpecs)
            segmentBones = ((upperJoint, lowerJoint), (lowerJoint, extremityJoint))
            segmentCtrls = ((upperLimbCtrl, upperLimbOutCtrl, hingeInCtrl, hingeCtrl), (hingeCtrl, hingeOutCtrl, lowerLimbInCtrl, extremityJoint))
            segmentScalers = ((upperLimbCtrl, hingeCtrl), (hingeCtrl, extremityIKCtrl))

            twistSolvers = [None] * 2
            scaleRemappers = [None] * 2

            for (i, (segmentName, segmentSpec, segmentTwistSpecs, (startJoint, endJoint), (startCtrl, startOutCtrl, endInCtrl, endCtrl), (startScaler, endScaler))) in enumerate(zip(segmentNames, segmentSpecs, segmentTwistSpecs, segmentBones, segmentCtrls, segmentScalers)):

                # Create curve segment
                #
                curveName = self.formatName(name=segmentName, subname='Twist', type='nurbsCurve')
                curve = self.scene.createNode('transform', name=curveName, parent=controlsGroup)
                curve.inheritsTransform = False
                curve.lockAttr('translate', 'rotate', 'scale')

                curveShape = self.scene.createNode('nurbsCurve', parent=curve)
                curveShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin], degree=2))
                curveShape.template = True

                curveFromPointName = self.formatName(name=segmentName, subname='Twist', type='curveFromPoint')
                curveFromPoint = self.scene.createNode('curveFromPoint', name=curveFromPointName)
                curveFromPoint.degree = 3
                curveFromPoint.connectPlugs(startCtrl[f'worldMatrix[{startCtrl.instanceNumber()}]'], 'inputMatrix[0]')
                curveFromPoint.connectPlugs(startOutCtrl[f'worldMatrix[{startOutCtrl.instanceNumber()}]'], 'inputMatrix[1]')
                curveFromPoint.connectPlugs(endInCtrl[f'worldMatrix[{endInCtrl.instanceNumber()}]'], 'inputMatrix[2]')
                curveFromPoint.connectPlugs(endCtrl[f'worldMatrix[{endCtrl.instanceNumber()}]'], 'inputMatrix[3]')
                curveFromPoint.connectPlugs(curveShape[f'parentInverseMatrix[{curveShape.instanceNumber()}]'], 'parentInverseMatrix')
                curveFromPoint.connectPlugs('outputCurve', curveShape['create'])

                # Create scale remapper
                #
                scaleRemapperName = self.formatName(name=segmentName, subname='Scale', type='remapArray')
                scaleRemapper = self.scene.createNode('remapArray', name=scaleRemapperName)
                scaleRemapper.setAttr('clamp', True)
                scaleRemapper.connectPlugs(startScaler['scale'], 'outputMin')
                scaleRemapper.connectPlugs(endScaler['scale'], 'outputMax')

                scaleRemappers[i] = scaleRemapper.uuid()

                # Create twist solver
                #
                twistSolverName = self.formatName(name=segmentName, subname='Twist', type='twistSolver')
                twistSolver = self.scene.createNode('twistSolver', name=twistSolverName)
                twistSolver.forwardAxis = 0  # X
                twistSolver.upAxis = 2  # Z
                twistSolver.segments = self.numTwistLinks
                twistSolver.connectPlugs(startCtrl[f'worldMatrix[{startCtrl.instanceNumber()}]'], 'startMatrix')
                twistSolver.connectPlugs(endCtrl[f'worldMatrix[{endCtrl.instanceNumber()}]'], 'endMatrix')

                twistSolvers[i] = twistSolver.uuid()

                # Create twist controls
                #
                numTwistSpecs = len(segmentTwistSpecs)

                for (j, twistSpec) in enumerate(segmentTwistSpecs):

                    # Create twist controller
                    #
                    twistIndex = j + 1

                    twistSpaceName = self.formatName(name=segmentName, subname='Twist', index=twistIndex, type='space')
                    twistSpace = self.scene.createNode('transform', name=twistSpaceName, parent=controlsGroup)

                    twistCtrlName = self.formatName(name=segmentName, subname='Twist', index=twistIndex, type='control')
                    twistCtrl = self.scene.createNode('transform', name=twistCtrlName, parent=twistSpace)
                    twistCtrl.addShape('CrossCurve', size=(30.0 * rigScale), colorRGB=colorRGB)
                    twistCtrl.prepareChannelBoxForAnimation()
                    self.publishNode(twistCtrl, alias=f'{segmentName}_Twist{str(twistIndex).zfill(2)}')

                    # Add point-on-curve constraint
                    #
                    parameter = float(j) * (1.0 / (float(numTwistSpecs) - 1.0))

                    pathConstraint = twistSpace.addConstraint('pointOnCurveConstraint', [curveShape])
                    pathConstraint.parameter = parameter
                    pathConstraint.useFraction = True
                    pathConstraint.forwardVector = (1.0, 0.0, 0.0)
                    pathConstraint.upVector = (0.0, 0.0, 1.0)
                    pathConstraint.worldUpType = 2  # Object Rotation
                    pathConstraint.worldUpVector = (0.0, 0.0, 1.0)
                    pathConstraint.connectPlugs(startCtrl[f'worldMatrix[{startCtrl.instanceNumber()}]'], 'worldUpMatrix')
                    pathConstraint.connectPlugs(twistSolver[f'twist[{j}]'], 'twist')

                    # Connect scale remapper
                    #
                    scaleConstraint = twistSpace.addConstraint('scaleConstraint', [limbCtrl])

                    scaleRemapper.setAttr(f'parameter[{j}]', parameter)
                    scaleRemapper.connectPlugs(f'outValue[{j}]', scaleConstraint['offset'])

                    # Finally, re-align export joint to control
                    # This will ensure there are no unwanted offsets when binding the skeleton!
                    #
                    twistExportJoint = twistSpec.getNode(referenceNode=referenceNode)
                    twistExportJoint.copyTransform(twistCtrl, skipScale=True)

                    twistSpec.matrix = twistExportJoint.matrix(asTransformationMatrix=True)

            # Cache twist components
            #
            self.userProperties['twistSolvers'] = twistSolvers
            self.userProperties['scaleRemappers'] = scaleRemappers
    # endregion
