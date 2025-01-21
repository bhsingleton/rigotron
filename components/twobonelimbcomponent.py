import math

from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.maya.libs import transformutils, shapeutils
from dcc.dataclasses.colour import Colour
from rigomatic.libs import kinematicutils
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
    HINGE = 1
    LOWER = 2
    EXTREMITY = 3


class TwoBoneLimbComponent(limbcomponent.LimbComponent):
    """
    Overload of `AbstractComponent` that outlines two-bone limb components.
    """

    # region Dunderscores
    __default_limb_names__ = ('', '', '')
    __default_limb_types__ = (Type.NONE, Type.NONE, Type.NONE)
    __default_limb_matrices__ = {Side.LEFT: {}, Side.RIGHT: {}}
    __default_rbf_samples__ = {Side.LEFT: {}, Side.RIGHT: {}}
    __default_hinge_name__ = ''
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
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        numMembers = len(self.LimbType)
        upperLimbSpec, hingeSpec, lowerLimbSpec, extremitySpec = self.resizeSkeletonSpecs(numMembers, skeletonSpecs)

        # Iterate through limb specs
        #
        limbNames = (self.__default_limb_names__[0], self.__default_limb_names__[1])
        limbSpecs = (upperLimbSpec, lowerLimbSpec)

        twistEnabled = bool(self.twistEnabled)
        twistCount = self.numTwistLinks if twistEnabled else 0

        for (i, (limbName, limbSpec)) in enumerate(zip(limbNames, limbSpecs)):

            # Edit limb name
            #
            limbSpec.name = self.formatName(name=limbName)
            limbSpec.driver = self.formatName(name=limbName, type='joint')

            # Edit twist specs
            #
            twistSpecs = self.resizeSkeletonSpecs(twistCount, limbSpec.children)

            for (j, twistSpec) in enumerate(twistSpecs, start=1):

                twistSpec.name = self.formatName(name=limbName, subname='Twist', index=j)
                twistSpec.driver = self.formatName(name=limbName, subname='Twist', index=j, type='control')
                twistSpec.enabled = twistEnabled

        extremityName = self.__default_limb_names__[-1]
        extremitySpec.name = self.formatName(name=extremityName)
        extremitySpec.driver = self.formatName(name=extremityName, type='joint')

        # Edit hinge spec
        #
        hingeSpec.name = self.formatName(name=self.__default_hinge_name__)
        hingeSpec.driver = self.formatName(name=self.__default_hinge_name__, type='control')
        hingeSpec.enabled = bool(self.hingeEnabled)

        # Call parent method
        #
        super(TwoBoneLimbComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        componentSide = self.Side(self.componentSide)

        upperLimbSpec, hingeSpec, lowerLimbSpec, limbTipSpec = self.skeletonSpecs()
        upperType, lowerType, extremityType = self.__default_limb_types__

        # Create upper joint
        #
        upperJoint = self.scene.createNode('joint', name=upperLimbSpec.name)
        upperJoint.side = componentSide
        upperJoint.type = upperType
        upperJoint.drawStyle = self.Style.BOX
        upperJoint.displayLocalAxis = True
        upperLimbSpec.uuid = upperJoint.uuid()

        defaultUpperLimbMatrix = self.__default_limb_matrices__[componentSide][LimbType.UPPER]
        upperLimbMatrix = upperLimbSpec.getMatrix(default=defaultUpperLimbMatrix)
        upperJoint.setWorldMatrix(upperLimbMatrix)

        # Create upper-twist joints
        #
        upperTwistSpecs = upperLimbSpec.children

        upperTwistCount = len(upperTwistSpecs)
        upperTwistJoints = [None] * upperTwistCount

        for (i, twistSpec) in enumerate(upperTwistSpecs):
            
            twistJoint = self.scene.createNode('joint', name=twistSpec.name, parent=upperJoint)
            twistJoint.side = componentSide
            twistJoint.type = self.Type.NONE
            twistJoint.drawStyle = self.Style.JOINT
            twistJoint.displayLocalAxis = True
            twistSpec.uuid = twistJoint.uuid()

            upperTwistJoints[i] = twistJoint

        # Create lower  joint
        #
        lowerJoint = self.scene.createNode('joint', name=lowerLimbSpec.name, parent=upperJoint)
        lowerJoint.side = componentSide
        lowerJoint.type = lowerType
        lowerJoint.drawStyle = self.Style.BOX
        lowerJoint.displayLocalAxis = True
        lowerLimbSpec.uuid = lowerJoint.uuid()

        defaultLowerMatrix = self.__default_limb_matrices__[componentSide][LimbType.LOWER]
        lowerMatrix = lowerLimbSpec.getMatrix(default=defaultLowerMatrix)
        lowerJoint.setWorldMatrix(lowerMatrix)

        # Create lower-twist joints
        #
        lowerTwistSpecs = lowerLimbSpec.children

        lowerTwistCount = len(lowerTwistSpecs)
        lowerTwistJoints = [None] * lowerTwistCount

        for (i, twistSpec) in enumerate(lowerTwistSpecs):

            twistJoint = self.scene.createNode('joint', name=twistSpec.name, parent=lowerJoint)
            twistJoint.side = componentSide
            twistJoint.type = self.Type.NONE
            twistJoint.drawStyle = self.Style.JOINT
            twistJoint.displayLocalAxis = True
            twistSpec.uuid = twistJoint.uuid()

            lowerTwistJoints[i] = twistJoint

        # Create hinge joint
        #
        hingeJoint = None

        if hingeSpec.enabled:

            hingeJoint = self.scene.createNode('joint', name=hingeSpec.name, parent=lowerJoint)
            hingeJoint.side = componentSide
            hingeJoint.type = self.Type.NONE
            hingeJoint.drawStyle = self.Style.JOINT
            hingeJoint.displayLocalAxis = True
            hingeSpec.uuid = hingeJoint.uuid()

            defaultHingeMatrix = self.__default_limb_matrices__[componentSide][LimbType.HINGE]
            hingeMatrix = hingeSpec.getMatrix(default=defaultHingeMatrix)
            hingeJoint.setWorldMatrix(hingeMatrix)

        # Create extremity joint
        #
        extremityJoint = self.scene.createNode('joint', name=limbTipSpec.name, parent=lowerJoint)
        extremityJoint.side = componentSide
        extremityJoint.type = extremityType
        extremityJoint.displayLocalAxis = True
        limbTipSpec.uuid = extremityJoint.uuid()

        defaultExtremityMatrix = self.__default_limb_matrices__[componentSide][LimbType.EXTREMITY]
        extremityMatrix = limbTipSpec.getMatrix(default=defaultExtremityMatrix)
        extremityJoint.setWorldMatrix(extremityMatrix)

        return (upperJoint, hingeJoint, lowerJoint, extremityJoint)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        limbName = self.componentName
        hingeName = self.__default_hinge_name__
        upperLimbName, lowerLimbName, extremityName = self.__default_limb_names__

        upperLimbSpec, hingeSpec, lowerLimbSpec, extremitySpec = self.skeletonSpecs()
        upperExportJoint = self.scene(upperLimbSpec.name)
        lowerExportJoint = self.scene(lowerLimbSpec.name)
        extremityExportJoint = self.scene(extremitySpec.name)

        upperMatrix = upperExportJoint.worldMatrix()
        lowerMatrix = lowerExportJoint.worldMatrix()
        extremityMatrix = extremityExportJoint.worldMatrix()

        componentSide = self.Side(self.componentSide)
        requiresMirroring = componentSide == self.Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        limbOrigin = transformutils.breakMatrix(upperMatrix)[3]
        hingePoint = transformutils.breakMatrix(lowerMatrix)[3]
        limbGoal = transformutils.breakMatrix(extremityMatrix)[3]

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
        defaultLimbMatrix = self.__default_limb_matrices__[componentSide][self.LimbType.UPPER]
        limbMatrix = mirrorMatrix * transformutils.createRotationMatrix(defaultLimbMatrix) * transformutils.createTranslateMatrix(limbOrigin)

        limbTargetName = self.formatName(type='target')
        limbTarget = self.scene.createNode('transform', name=limbTargetName, parent=privateGroup)
        limbTarget.setWorldMatrix(limbMatrix)
        limbTarget.freezeTransform()

        target = clavicleCtrl if hasClavicleComponent else spineCtrl
        limbTarget.addConstraint('transformConstraint', [target], maintainOffset=True)

        # Create kinematic limb joints
        #
        jointTypes = (upperLimbName, lowerLimbName, extremityName)
        kinematicTypes = ('FK', 'IK', 'RIK', 'Blend')

        limbFKJoints = [None] * 3
        limbIKJoints = [None] * 3
        limbRIKJoints = [None] * 3
        limbBlendJoints = [None] * 3
        limbMatrices = (upperMatrix, lowerMatrix, extremityMatrix)
        kinematicJoints = (limbFKJoints, limbIKJoints, limbRIKJoints, limbBlendJoints)

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = kinematicJoints[i][j - 1] if j > 0 else jointsGroup

                jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
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
        switchCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=(0.0, 25.0 * limbSign, 0.0), localRotate=(0.0, 0.0, -90.0 * limbSign), colorRGB=darkColorRGB)
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
        limbSpaceName = self.formatName(name=upperLimbName, type='space')
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
        extremityBlender.setName(self.formatName(subname=extremityName, type='blendTransform'))

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
        upperFKMatrix = mirrorMatrix * upperMatrix

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

        lowerFKMatrix = mirrorMatrix * lowerMatrix

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
        
        extremityFKTargetName = self.formatName(name=extremityName, kinemat='FK', type='target')
        extremityFKTarget = self.scene.createNode('transform', name=extremityFKTargetName, parent=lowerFKCtrl)

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(extremityMatrix * lowerMatrix.inverse())
        extremityFKComposeMatrixName = self.formatName(name=extremityName, kinemat='FK', type='composeMatrix')
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
        # TODO: Reintegrate local position/scale connections once we move to Maya 2025
        #
        upperFKShape = upperFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        upperFKShape.reorientAndScaleToFit(lowerFKCtrl)

        lowerFKShape = lowerFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        lowerFKShape.reorientAndScaleToFit(extremityFKTarget)

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

        if hasExtremity:

            extremityComponent = extremityComponents[0]
            extremitySpecs = extremityComponent.skeletonSpecs()
            extremityIKMatrix = mirrorMatrix * self.scene(extremitySpecs[0].uuid).worldMatrix()

        # Create IK extremity control
        #
        defaultWorldSpace = 1.0 if isLeg else 0.0
        defaultLimbSpace = 1.0 if isArm else 0.0
        preEulerRotation = transformutils.decomposeTransformMatrix(extremityIKMatrix)[1]

        extremityIKSpaceName = self.formatName(name=extremityName, kinemat='IK', type='space')
        extremityIKSpace = self.scene.createNode('transform', name=extremityIKSpaceName, parent=controlsGroup)
        extremityIKSpace.setWorldMatrix(extremityIKMatrix, skipRotate=True)
        extremityIKSpace.freezeTransform()

        extremityIKCtrlName = self.formatName(name=extremityName, kinemat='IK', type='control')
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
        self.publishNode(extremityIKCtrl, alias=f'{extremityName}_IK')

        extremityIKOffsetCtrlName = self.formatName(name=extremityName, kinemat='IK', subname='Offset', type='control')
        extremityIKOffsetCtrl = self.scene.createNode('transform', name=extremityIKOffsetCtrlName, parent=extremityIKCtrl)
        extremityIKOffsetCtrl.addPointHelper('axisView', size=10.0, localScale=(3.0 * rigScale, 3.0 * rigScale, 3.0 * rigScale), colorRGB=lightColorRGB)
        extremityIKOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(extremityIKOffsetCtrl, alias=f'{extremityName}_IK_Offset')

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

        # Apply IK solvers
        #
        lowerAngle = math.degrees(lowerIKJoint.eulerRotation().z)
        lowerAngleSign = math.copysign(1.0, lowerAngle)
        preferredAngle = lowerAngle if (abs(lowerAngle) >= 1.0) else lowerAngleSign

        lowerIKJoint.preferredAngleZ = preferredAngle
        lowerRIKJoint.preferredAngleZ = preferredAngle

        limbIKHandle, limbIKEffector = kinematicutils.applyRotationPlaneSolver(upperIKJoint, extremityIKJoint)
        limbIKEffector.setName(self.formatName(type='ikEffector'))
        limbIKHandle.setName(self.formatName(type='ikHandle'))
        limbIKHandle.setParent(privateGroup)
        limbIKHandle.connectPlugs(switchCtrl['twist'], 'twist')

        limbRIKHandle, limbRIKEffector = kinematicutils.applyRotationPlaneSolver(upperRIKJoint, extremityRIKJoint)
        limbRIKEffector.setName(self.formatName(subname='Reverse', type='ikEffector'))
        limbRIKHandle.setName(self.formatName(subname='Reverse', type='ikHandle'))
        limbRIKHandle.setParent(privateGroup)
        limbRIKHandle.connectPlugs(switchCtrl['twist'], 'twist')

        # Constrain IK joints
        #
        upperIKJoint.addConstraint('transformConstraint', [limbCtrl], skipRotate=True)
        upperIKJoint.connectPlugs('scale', lowerIKJoint['scale'])
        lowerIKJoint.connectPlugs('scale', extremityIKJoint['scale'])

        upperRIKJoint.addConstraint('transformConstraint', [limbCtrl], skipRotate=True)
        upperRIKJoint.connectPlugs('scale', lowerRIKJoint['scale'])
        lowerRIKJoint.connectPlugs('scale', extremityRIKJoint['scale'])

        # Apply IK softening
        #
        ikHandleTargetName = self.formatName(kinemat='IK', type='target')
        ikHandleTarget = self.scene.createNode('transform', name=ikHandleTargetName, parent=privateGroup)
        ikHandleTarget.displayLocalAxis = True
        ikHandleTarget.visibility = False
        ikHandleTarget.copyTransform(limbIKHandle, skipRotate=True, skipScale=True)

        limbIKHandle.addConstraint('pointConstraint', [ikHandleTarget])

        rikHandleTargetName = self.formatName(kinemat='RIK', type='target')
        rikHandleTarget = self.scene.createNode('transform', name=rikHandleTargetName, parent=privateGroup)
        rikHandleTarget.displayLocalAxis = True
        rikHandleTarget.visibility = False
        rikHandleTarget.copyTransform(limbRIKHandle, skipRotate=True, skipScale=True)

        limbRIKHandle.addConstraint('pointConstraint', [rikHandleTarget])

        limbReverseStretchName = self.formatName(subname='Stretch', type='revDoubleLinear')
        limbReverseStretch = self.scene.createNode('revDoubleLinear', name=limbReverseStretchName)
        limbReverseStretch.connectPlugs(switchCtrl['stretch'], 'input')

        limbIKSoftenerName = self.formatName(kinemat='IK', type='ikSoftener')
        limbIKSoftener = self.scene.createNode('ikSoftener', name=limbIKSoftenerName)
        limbIKSoftener.chainScaleCompensate = True
        limbIKSoftener.connectPlugs(switchCtrl['soften'], 'radius')
        limbIKSoftener.connectPlugs(limbReverseStretch['output'], 'envelope')
        limbIKSoftener.connectPlugs(limbLength['output1D'], 'chainLength')
        limbIKSoftener.connectPlugs(limbCtrl[f'worldMatrix[{limbCtrl.instanceNumber()}]'], 'startMatrix')
        limbIKSoftener.connectPlugs(extremityIKOffsetCtrl[f'worldMatrix[{extremityIKOffsetCtrl.instanceNumber()}]'], 'endMatrix')
        limbIKSoftener.connectPlugs(ikHandleTarget[f'parentInverseMatrix[{ikHandleTarget.instanceNumber()}]'], 'parentInverseMatrix')
        limbIKSoftener.connectPlugs('outPosition', ikHandleTarget['translate'])

        limbRIKSoftenerName = self.formatName(kinemat='RIK', type='ikSoftener')
        limbRIKSoftener = self.scene.createNode('ikSoftener', name=limbRIKSoftenerName)
        limbRIKSoftener.chainScaleCompensate = True
        limbRIKSoftener.connectPlugs(switchCtrl['soften'], 'radius')
        limbRIKSoftener.connectPlugs(limbReverseStretch['output'], 'envelope')
        limbRIKSoftener.connectPlugs(limbLength['output1D'], 'chainLength')
        limbRIKSoftener.connectPlugs(limbCtrl[f'worldMatrix[{limbCtrl.instanceNumber()}]'], 'startMatrix')
        limbRIKSoftener.connectPlugs(extremityIKOffsetCtrl[f'worldMatrix[{extremityIKOffsetCtrl.instanceNumber()}]'], 'endMatrix')
        limbRIKSoftener.connectPlugs(rikHandleTarget[f'parentInverseMatrix[{rikHandleTarget.instanceNumber()}]'], 'parentInverseMatrix')
        limbRIKSoftener.connectPlugs('outPosition', rikHandleTarget['translate'])

        # Calculate default PV matrix
        #
        upVector = -((transformutils.breakMatrix(upperMatrix, normalize=True)[1] * 0.5) + (transformutils.breakMatrix(lowerMatrix, normalize=True)[1] * 0.5)).normal()
        forwardVector = (transformutils.breakMatrix(extremityMatrix)[3] - limbOrigin).normal()
        rightVector = (forwardVector ^ upVector).normal()
        poleVector = (rightVector ^ forwardVector).normal()

        upperVector = (transformutils.breakMatrix(lowerMatrix)[3] - limbOrigin)
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
        followTipJoint.connectPlugs(limbIKSoftener['softDistance'], followTipJoint['translateX'])
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
        forwardVectorMultMatrix.connectPlugs(limbIKSoftener['outWorldVector'], 'input')
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
        limbPVCtrl.prepareChannelBoxForAnimation()
        self.publishNode(limbPVCtrl, alias=f'{limbName}_PV')

        limbPVSpaceSwitch = limbPVSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, spineCtrl, limbCtrl, followTarget], weighted=True, maintainOffset=True)
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW0'], 'target[0].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW1'], 'target[1].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW2'], 'target[2].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW3'], 'target[3].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW4'], 'target[4].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW5'], 'target[5].targetWeight')

        limbIKHandle.addConstraint('poleVectorConstraint', [limbPVCtrl])
        limbRIKHandle.addConstraint('poleVectorConstraint', [limbPVCtrl])

        limbPVCtrl.userProperties['space'] = limbPVSpace.uuid()
        limbPVCtrl.userProperties['spaceSwitch'] = limbPVSpaceSwitch.uuid()

        limbPVCtrl.tagAsController(parent=extremityIKCtrl)

        # Setup stretch on IK joints
        #
        upperIKStretchName = self.formatName(name=upperLimbName, kinemat='IK', subname='Stretch', type='multDoubleLinear')
        upperIKStretch = self.scene.createNode('multDoubleLinear', name=upperIKStretchName)
        upperIKStretch.connectPlugs(upperLength['output1D'], 'input1')
        upperIKStretch.connectPlugs(limbIKSoftener['softScale'], 'input2')

        upperIKEnvelopeName = self.formatName(name=upperLimbName, kinemat='IK', subname='Envelope', type='blendTwoAttr')
        upperIKEnvelope = self.scene.createNode('blendTwoAttr', name=upperIKEnvelopeName)
        upperIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        upperIKEnvelope.connectPlugs(upperLength['output1D'], 'input[0]')
        upperIKEnvelope.connectPlugs(upperIKStretch['output'], 'input[1]')
        upperIKEnvelope.connectPlugs('output', lowerIKJoint['translateX'])

        lowerIKStretchName = self.formatName(name=lowerLimbName, kinemat='IK', subname='Stretch', type='multDoubleLinear')
        lowerIKStretch = self.scene.createNode('multDoubleLinear', name=lowerIKStretchName)
        lowerIKStretch.connectPlugs(lowerLength['output1D'], 'input1')
        lowerIKStretch.connectPlugs(limbIKSoftener['softScale'], 'input2')

        lowerIKEnvelopeName = self.formatName(name=lowerLimbName, kinemat='IK', subname='Envelope', type='blendTwoAttr')
        lowerIKEnvelope = self.scene.createNode('blendTwoAttr', name=lowerIKEnvelopeName)
        lowerIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        lowerIKEnvelope.connectPlugs(lowerLength['output1D'], 'input[0]')
        lowerIKEnvelope.connectPlugs(lowerIKStretch['output'], 'input[1]')
        lowerIKEnvelope.connectPlugs('output', extremityIKJoint['translateX'])

        # Setup stretch on RIK joints
        #
        upperRIKStretchName = self.formatName(name=upperLimbName, kinemat='RIK', subname='Stretch', type='multDoubleLinear')
        upperRIKStretch = self.scene.createNode('multDoubleLinear', name=upperRIKStretchName)
        upperRIKStretch.connectPlugs(upperLength['output1D'], 'input1')
        upperRIKStretch.connectPlugs(limbRIKSoftener['softScale'], 'input2')

        upperRIKEnvelopeName = self.formatName(name=upperLimbName, kinemat='RIK', subname='Envelope', type='blendTwoAttr')
        upperRIKEnvelope = self.scene.createNode('blendTwoAttr', name=upperRIKEnvelopeName)
        upperRIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        upperRIKEnvelope.connectPlugs(upperLength['output1D'], 'input[0]')
        upperRIKEnvelope.connectPlugs(upperRIKStretch['output'], 'input[1]')

        upperRIKDistanceName = self.formatName(name=upperLimbName, kinemat='RIK', subname='Pin', type='distanceBetween')
        upperRIKDistance = self.scene.createNode('distanceBetween', name=upperRIKDistanceName)
        upperRIKDistance.connectPlugs(limbCtrl[f'worldMatrix[{limbCtrl.instanceNumber()}]'], 'inMatrix1')
        upperRIKDistance.connectPlugs(limbPVCtrl[f'worldMatrix[{limbPVCtrl.instanceNumber()}]'], 'inMatrix2')

        upperRIKPinName = self.formatName(name=upperLimbName, kinemat='RIK', subname='Pin', type='blendTwoAttr')
        upperRIKPin = self.scene.createNode('blendTwoAttr', name=upperRIKPinName)
        upperRIKPin.connectPlugs(switchCtrl['pin'], 'attributesBlender')
        upperRIKPin.connectPlugs(upperRIKEnvelope['output'], 'input[0]')
        upperRIKPin.connectPlugs(upperRIKDistance['distance'], 'input[1]')
        upperRIKPin.connectPlugs('output', lowerRIKJoint['translateX'])

        lowerRIKStretchName = self.formatName(name=lowerLimbName, kinemat='RIK', subname='Stretch', type='multDoubleLinear')
        lowerRIKStretch = self.scene.createNode('multDoubleLinear', name=lowerRIKStretchName)
        lowerRIKStretch.connectPlugs(lowerLength['output1D'], 'input1')
        lowerRIKStretch.connectPlugs(limbRIKSoftener['softScale'], 'input2')

        lowerRIKEnvelopeName = self.formatName(name=lowerLimbName, kinemat='RIK', subname='Envelope', type='blendTwoAttr')
        lowerRIKEnvelope = self.scene.createNode('blendTwoAttr', name=lowerRIKEnvelopeName)
        lowerRIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        lowerRIKEnvelope.connectPlugs(lowerLength['output1D'], 'input[0]')
        lowerRIKEnvelope.connectPlugs(lowerRIKStretch['output'], 'input[1]')

        lowerRIKDistanceName = self.formatName(name=lowerLimbName, kinemat='RIK', subname='Pin', type='distanceBetween')
        lowerRIKDistance = self.scene.createNode('distanceBetween', name=lowerRIKDistanceName)
        lowerRIKDistance.connectPlugs(limbPVCtrl[f'worldMatrix[{limbPVCtrl.instanceNumber()}]'], 'inMatrix1')
        lowerRIKDistance.connectPlugs(limbRIKSoftener[f'outWorldMatrix'], 'inMatrix2')

        lowerRIKPinName = self.formatName(name=lowerLimbName, kinemat='RIK', subname='Pin', type='blendTwoAttr')
        lowerRIKPin = self.scene.createNode('blendTwoAttr', name=lowerRIKPinName)
        lowerRIKPin.connectPlugs(switchCtrl['pin'], 'attributesBlender')
        lowerRIKPin.connectPlugs(lowerRIKEnvelope['output'], 'input[0]')
        lowerRIKPin.connectPlugs(lowerRIKDistance['distance'], 'input[1]')
        lowerRIKPin.connectPlugs('output', extremityRIKJoint['translateX'])

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

            hingeExportJoint = self.scene(hingeSpec.uuid)
            hingeExportJoint.copyTransform(hingeCtrl)

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

        extremityJointName = self.formatName(name=extremityName, type='joint')
        extremityJoint = self.scene.createNode('joint', name=extremityJointName, parent=lowerJoint)
        extremityJoint.addConstraint('pointConstraint', [extremityBlendJoint], skipTranslateY=True, skipTranslateZ=True)
        extremityJoint.connectPlugs(extremityBlendJoint['scale'], 'scale')

        # Create PV handle curve
        #
        controlPoints = [transformutils.breakMatrix(matrix)[3] for matrix in (poleMatrix, lowerMatrix)]
        curveData = shapeutils.createCurveFromPoints(controlPoints, degree=1)

        limbPVShapeName = self.formatName(kinemat='PV', subname='Handle', type='control')
        limbPVShape = self.scene.createNode('nurbsCurve', name=f'{limbPVShapeName}Shape', parent=limbPVCtrl)
        limbPVShape.setAttr('cached', curveData)
        limbPVShape.useObjectColor = 2
        limbPVShape.wireColorRGB = lightColorRGB

        nodes = [limbPVCtrl, hingeCtrl]

        for (i, node) in enumerate(nodes):

            index = i + 1

            multMatrixName = self.formatName(kinemat='PV', subname='ControlPoint', index=index, type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(node[f'worldMatrix[{node.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(limbPVShape[f'parentInverseMatrix[{limbPVShape.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(kinemat='PV', subname='ControlPoint', index=index, type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', limbPVShape[f'controlPoints[{i}].xValue'])
            breakMatrix.connectPlugs('row4Y', limbPVShape[f'controlPoints[{i}].yValue'])
            breakMatrix.connectPlugs('row4Z', limbPVShape[f'controlPoints[{i}].zValue'])

        # Cache kinematic components
        #
        self.userProperties['switchControl'] = switchCtrl.uuid()

        self.userProperties['fkJoints'] = (upperFKJoint.uuid(), lowerFKJoint.uuid(), extremityFKJoint.uuid())
        self.userProperties['fkControls'] = (upperFKCtrl.uuid(), lowerFKCtrl.uuid(), extremityFKTarget.uuid())

        self.userProperties['rikJoints'] = (upperRIKJoint.uuid(), lowerRIKJoint.uuid(), extremityRIKJoint.uuid())
        self.userProperties['rikHandle'] = limbRIKHandle.uuid()
        self.userProperties['rikEffector'] = limbRIKEffector.uuid()
        self.userProperties['rikSoftener'] = limbRIKSoftener.uuid()

        self.userProperties['ikJoints'] = (upperIKJoint.uuid(), lowerIKJoint.uuid(), extremityIKJoint.uuid())
        self.userProperties['ikControls'] = (limbCtrl.uuid(), extremityIKCtrl.uuid())
        self.userProperties['ikHandle'] = limbIKHandle.uuid()
        self.userProperties['ikEffector'] = limbIKEffector.uuid()
        self.userProperties['ikSoftener'] = limbIKSoftener.uuid()
        self.userProperties['ikTarget'] = ikHandleTarget.uuid()
        self.userProperties['pvControl'] = limbPVCtrl.uuid()
        self.userProperties['hingeControl'] = hingeCtrl.uuid()

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
            upperLimbOutSpace.setWorldMatrix(upperMatrix)
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
            curveData = shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1)

            curveShape = self.scene.createNode('nurbsCurve', parent=upperLimbOutCtrl)
            curveShape.setAttr('cached', curveData)
            curveShape.useObjectColor = 2
            curveShape.wireColorRGB = lightColorRGB

            multMatrixName = self.formatName(name=upperLimbName, subname='OutHandle', type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(upperLimbCtrl[f'worldMatrix[{upperLimbCtrl.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(curveShape[f'parentInverseMatrix[{curveShape.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(name=upperLimbName, subname='OutHandle', type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', curveShape[f'controlPoints[1].xValue'])
            breakMatrix.connectPlugs('row4Y', curveShape[f'controlPoints[1].yValue'])
            breakMatrix.connectPlugs('row4Z', curveShape[f'controlPoints[1].zValue'])

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
            controlPoints = [om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin]
            curveData = shapeutils.createCurveFromPoints(controlPoints, degree=1)

            curveShape = self.scene.createNode('nurbsCurve', parent=hingeCtrl)
            curveShape.setAttr('cached', curveData)
            curveShape.template = True

            hingeHandles = [hingeInCtrl, hingeOutCtrl]

            for (i, handle) in enumerate(hingeHandles):

                isOutHandle = bool(i)
                handleType = 'Out' if isOutHandle else 'In'
                curveIndex = 2 if isOutHandle else 0

                multMatrixName = self.formatName(name=hingeName, subname=f'{handleType}Handle', type='multMatrix')
                multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
                multMatrix.connectPlugs(handle[f'worldMatrix[{handle.instanceNumber()}]'], 'matrixIn[0]')
                multMatrix.connectPlugs(curveShape[f'parentInverseMatrix[{curveShape.instanceNumber()}]'], 'matrixIn[1]')

                breakMatrixName = self.formatName(name=hingeName, subname=f'{handleType}Handle', type='breakMatrix')
                breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
                breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
                breakMatrix.connectPlugs('row4X', curveShape[f'controlPoints[{curveIndex}].xValue'])
                breakMatrix.connectPlugs('row4Y', curveShape[f'controlPoints[{curveIndex}].yValue'])
                breakMatrix.connectPlugs('row4Z', curveShape[f'controlPoints[{curveIndex}].zValue'])

            # Create lower-limb in-handle control
            #
            lowerLimbInSpaceName = self.formatName(name=extremityName, subname='In', type='space')
            lowerLimbInSpace = self.scene.createNode('transform', name=lowerLimbInSpaceName, parent=controlsGroup)
            lowerLimbInSpace.copyTransform(extremityJoint)
            lowerLimbInSpace.freezeTransform()

            lowerLimbInCtrlName = self.formatName(name=extremityName, subname='In', type='control')
            lowerLimbInCtrl = self.scene.createNode('transform', name=lowerLimbInCtrlName, parent=lowerLimbInSpace)
            lowerLimbInCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((-5.0 * rigScale), 0.0, 0.0), side=componentSide)
            lowerLimbInCtrl.addDivider('Spaces')
            lowerLimbInCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            lowerLimbInCtrl.prepareChannelBoxForAnimation()
            self.publishNode(lowerLimbInCtrl, alias=f'{extremityName}_In')

            lowerLimbInNegateName = self.formatName(name=extremityName, subname='In', type='floatMath')
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

            # Create upper-out proxy curve handles
            #
            curveData = shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1)

            curveShape = self.scene.createNode('nurbsCurve', parent=lowerLimbInCtrl)
            curveShape.setAttr('cached', curveData)
            curveShape.useObjectColor = 2
            curveShape.wireColorRGB = lightColorRGB

            multMatrixName = self.formatName(name=lowerLimbName, subname='OutHandle', type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(extremityJoint[f'worldMatrix[{extremityJoint.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(curveShape[f'parentInverseMatrix[{curveShape.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(name=lowerLimbName, subname='InHandle', type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', curveShape[f'controlPoints[1].xValue'])
            breakMatrix.connectPlugs('row4Y', curveShape[f'controlPoints[1].yValue'])
            breakMatrix.connectPlugs('row4Z', curveShape[f'controlPoints[1].zValue'])

            # Create twist curve
            #
            segmentNames = (upperLimbName, lowerLimbName)
            segmentSpecs = (upperLimbSpec, lowerLimbSpec)
            segmentJoints = (upperJoint, lowerJoint)
            segmentScalars = ((upperLimbCtrl, hingeCtrl), (hingeCtrl, extremityIKCtrl))
            segmentCtrls = ((upperLimbCtrl, upperLimbOutCtrl, hingeInCtrl, hingeCtrl), (hingeCtrl, hingeOutCtrl, lowerLimbInCtrl, extremityJoint))

            twistSolvers = [None] * 2
            scaleRemappers = [None] * 2

            for (i, (limbName, limbSpec, limbJoint, limbScalars, limbCtrls)) in enumerate(zip(segmentNames, segmentSpecs, segmentJoints, segmentScalars, segmentCtrls)):

                # Create curve segment
                #
                controlPoints = [node.translation(space=om.MSpace.kWorld) for node in limbCtrls]
                curveData = shapeutils.createCurveFromPoints(controlPoints, degree=2)

                curveName = self.formatName(name=limbName, subname='twist', type='nurbsCurve')
                curve = self.scene.createNode('transform', name=curveName, parent=controlsGroup)
                curve.inheritsTransform = False
                curve.lockAttr('translate', 'rotate', 'scale')

                curveShape = self.scene.createNode('nurbsCurve', parent=curve)
                curveShape.setAttr('cached', curveData)
                curveShape.template = True

                for (j, node) in enumerate(limbCtrls):

                    index = j + 1

                    multMatrixName = self.formatName(name=limbName, subname='ControlPoint', index=index, type='multMatrix')
                    multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
                    multMatrix.connectPlugs(node[f'worldMatrix[{node.instanceNumber()}]'], 'matrixIn[0]')
                    multMatrix.connectPlugs(curveShape[f'parentInverseMatrix[{curveShape.instanceNumber()}]'], 'matrixIn[1]')

                    breakMatrixName = self.formatName(name=limbName, subname='ControlPoint', index=index, type='breakMatrix')
                    breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
                    breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
                    breakMatrix.connectPlugs('row4X', curveShape[f'controlPoints[{j}].xValue'])
                    breakMatrix.connectPlugs('row4Y', curveShape[f'controlPoints[{j}].yValue'])
                    breakMatrix.connectPlugs('row4Z', curveShape[f'controlPoints[{j}].zValue'])

                # Create scale remapper
                #
                startCtrl, endCtrl = limbScalars

                scaleRemapperName = self.formatName(name=limbName, subname='Scale', type='remapArray')
                scaleRemapper = self.scene.createNode('remapArray', name=scaleRemapperName)
                scaleRemapper.setAttr('clamp', True)
                scaleRemapper.connectPlugs(startCtrl['scale'], 'outputMin')
                scaleRemapper.connectPlugs(endCtrl['scale'], 'outputMax')

                scaleRemappers[i] = scaleRemapper.uuid()

                # Create twist solver
                #
                twistSolverName = self.formatName(name=limbName, subname='Twist', type='twistSolver')
                twistSolver = self.scene.createNode('twistSolver', name=twistSolverName)
                twistSolver.forwardAxis = 0  # X
                twistSolver.upAxis = 2  # Z
                twistSolver.segments = self.numTwistLinks
                twistSolver.connectPlugs(startCtrl[f'worldMatrix[{startCtrl.instanceNumber()}]'], 'startMatrix')
                twistSolver.connectPlugs(endCtrl[f'worldMatrix[{endCtrl.instanceNumber()}]'], 'endMatrix')

                twistSolvers[i] = twistSolver.uuid()

                # Create twist controls
                #
                twistSpecs = limbSpec.children
                numTwistSpecs = len(twistSpecs)

                for (j, twistSpec) in enumerate(twistSpecs):

                    # Create twist controller
                    #
                    twistIndex = j + 1

                    twistSpaceName = self.formatName(name=limbName, subname='Twist', index=twistIndex, type='space')
                    twistSpace = self.scene.createNode('transform', name=twistSpaceName, parent=controlsGroup)

                    twistCtrlName = self.formatName(name=limbName, subname='Twist', index=twistIndex, type='control')
                    twistCtrl = self.scene.createNode('transform', name=twistCtrlName, parent=twistSpace)
                    twistCtrl.addShape('CrossCurve', size=(30.0 * rigScale), colorRGB=colorRGB)
                    twistCtrl.prepareChannelBoxForAnimation()
                    self.publishNode(twistCtrl, alias=f'{limbName}_Twist{str(twistIndex).zfill(2)}')

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
                    twistExportJoint = self.scene(twistSpec.uuid)
                    twistExportJoint.copyTransform(twistCtrl, skipScale=True)

                    twistSpec.matrix = twistExportJoint.matrix(asTransformationMatrix=True)
                    twistSpec.worldMatrix = twistExportJoint.worldMatrix()

            # Cache twist components
            #
            self.userProperties['twistSolvers'] = twistSolvers
            self.userProperties['scaleRemappers'] = scaleRemappers
    # endregion
