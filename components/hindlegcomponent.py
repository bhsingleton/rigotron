from maya import cmds as mc
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

    THIGH = 0
    CALF = 1
    ANKLE = 2
    TIP = 3


class HindLegComponent(limbcomponent.LimbComponent):
    """
    Overload of `LimbComponent` that implements hind-leg components.
    """

    # region Dunderscores
    __default_component_name__ = 'Leg'
    __default_limb_names__ = ('Thigh', 'Calf', 'Ankle', 'AnkleTip')
    __default_hinge_names__ = ('Knee', 'Ankle')
    __default_limb_types__ = (Type.HIP, Type.KNEE, Type.FOOT, Type.NONE)
    __default_limb_matrices__ = {
        Side.LEFT: {
            LimbType.THIGH: om.MMatrix(
                [
                    (0.0, -0.464425, -0.885612, 0.0),
                    (0.0, 0.885612, -0.464425, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, 0.0, 90.0, 1.0)
                ]
            ),
            LimbType.CALF: om.MMatrix(
                [
                    (0.0, 0.968116, -0.250503, 0.0),
                    (0.0, 0.250503, 0.968116, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, -18.577, 54.5755, 1.0)
                ]
            ),
            LimbType.ANKLE: om.MMatrix(
                [
                    (-0.0, -0.503691, -0.863884, 0.0),
                    (0.0, 0.863884, -0.503691, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, 20.1476, 44.5554, 1.0)
                ]
            ),
            LimbType.TIP: om.MMatrix(
                [
                    (0.0, -0.503691, -0.863884, 0.0),
                    (0.0, 0.863884, -0.503691, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (20.0, 0.0, 10.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            LimbType.THIGH: om.MMatrix(
                [
                    (0.0, -0.464425, -0.885612, 0.0),
                    (0.0, 0.885612, -0.464425, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, 0.0, 90.0, 1.0)
                ]
            ),
            LimbType.CALF: om.MMatrix(
                [
                    (0.0, 0.968116, -0.250503, 0.0),
                    (0.0, 0.250503, 0.968116, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, -18.577, 54.5755, 1.0)
                ]
            ),
            LimbType.ANKLE: om.MMatrix(
                [
                    (-0.0, -0.503691, -0.863884, 0.0),
                    (0.0, 0.863884, -0.503691, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, 20.1476, 44.5554, 1.0)
                ]
            ),
            LimbType.TIP: om.MMatrix(
                [
                    (0.0, -0.503691, -0.863884, 0.0),
                    (0.0, 0.863884, -0.503691, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (-20.0, 0.0, 10.0, 1.0)
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

    # region Enums
    LimbType = LimbType
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        twistCount = int(self.numTwistLinks)
        upperCount, midCount, lowerCount = twistCount + 1, twistCount + 1, twistCount + 1

        upperSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        *upperTwistSpecs, midSpec  = self.resizeSkeleton(upperCount, upperSpec.children, hierarchical=False)
        *midTwistSpecs, lowerSpec = self.resizeSkeleton(midCount, midSpec.children, hierarchical=False)
        *lowerTwistSpecs, tipSpec = self.resizeSkeleton(lowerCount, cannonSpec.children, hierarchical=False)

        # Edit limb specs
        #
        upperName, midName, lowerName, tipName = self.__default_limb_names__
        upperType, midType, lowerType, tipType = self.__default_limb_types__
        side = self.Side(self.componentSide)

        upperSpec.name = self.formatName(name=upperName)
        upperSpec.side = side
        upperSpec.type = upperType
        upperSpec.drawStyle = self.Style.BOX
        upperSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.THIGH]
        upperSpec.driver.name = self.formatName(name=upperName, type='joint')

        midSpec.name = self.formatName(name=midName)
        midSpec.side = side
        midSpec.type = midType
        midSpec.drawStyle = self.Style.BOX
        midSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.CALF]
        midSpec.driver.name = self.formatName(name=midName, type='joint')

        cannonSpec.name = self.formatName(name=lowerName)
        cannonSpec.side = side
        cannonSpec.type = lowerType
        cannonSpec.drawStyle = self.Style.BOX
        cannonSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.ANKLE]
        cannonSpec.driver.name = self.formatName(name=lowerName, type='joint')

        limbTipSpec.enabled = not self.hasExtremityComponent()
        limbTipSpec.name = self.formatName(name=tipName)
        limbTipSpec.side = side
        limbTipSpec.type = tipType
        limbTipSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.TIP]
        limbTipSpec.driver.name = self.formatName(name=tipName, type='joint')

        # Edit twist specs
        #
        twistEnabled = bool(self.twistEnabled)

        for (twistName, twistType, twistSpecs) in ((upperName, upperType, upperTwistSpecs), (midName, midType, midTwistSpecs), (lowerName, lowerType, lowerTwistSpecs)):

            for (i, twistSpec) in enumerate(twistSpecs, start=1):

                twistSpec.enabled = twistEnabled
                twistSpec.name = self.formatName(name=twistName, subname='Twist', index=i)
                twistSpec.side = side
                twistSpec.type = twistType
                twistSpec.driver.name = self.formatName(name=twistName, subname='Twist', index=i, type='control')

        # Call parent method
        #
        return super(HindLegComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        limbName = self.componentName
        upperLimbName, midLimbName, lowerLimbName, limbTipName = self.__default_limb_names__

        upperLimbSpec, midLimbSpec, lowerLimbSpec, limbTipSpec = self.skeletonSpecs()
        upperLimbExportJoint = upperLimbSpec.getNode()
        midLimbExportJoint = midLimbSpec.getNode()
        lowerLimbExportJoint = lowerLimbSpec.getNode()
        limbTipExportJoint = limbTipSpec.getNode()

        upperLimbMatrix = upperLimbExportJoint.worldMatrix()
        midLimbMatrix = midLimbExportJoint.worldMatrix()
        lowerLimbMatrix = lowerLimbExportJoint.worldMatrix()
        extremityMatrix = self.extremityMatrix()
        effectorMatrix = self.effectorMatrix()

        defaultLimbTipMatrix = transformutils.createRotationMatrix(lowerLimbMatrix) * transformutils.createTranslateMatrix(extremityMatrix)
        limbTipMatrix = limbTipExportJoint.worldMatrix() if (limbTipExportJoint is not None) else defaultLimbTipMatrix

        componentSide = self.Side(self.componentSide)
        requiresMirroring = componentSide == self.Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        limbOrigin = transformutils.breakMatrix(upperLimbMatrix)[3]
        midPoint = transformutils.breakMatrix(midLimbMatrix)[3]
        lowerPoint = transformutils.breakMatrix(lowerLimbMatrix)[3]
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
        forwardVector = om.MVector(limbGoal - limbOrigin).normal()
        worldForwardVector = transformutils.findClosestAxis(forwardVector, om.MMatrix.kIdentity)
        rightVector = transformutils.breakMatrix(upperLimbMatrix, normalize=True)[2]
        worldRightVector = transformutils.findClosestAxis(rightVector, om.MMatrix.kIdentity)
        worldUpVector = (worldRightVector ^ worldForwardVector).normal()

        defaultLimbMatrix = transformutils.makeMatrix(worldForwardVector, worldUpVector, worldRightVector, limbOrigin)
        limbMatrix = mirrorMatrix * defaultLimbMatrix

        limbTargetName = self.formatName(type='target')
        limbTarget = self.scene.createNode('transform', name=limbTargetName, parent=privateGroup)
        limbTarget.setWorldMatrix(limbMatrix)
        limbTarget.freezeTransform()

        target = clavicleCtrl if hasClavicleComponent else spineCtrl
        limbTarget.addConstraint('transformConstraint', [target], maintainOffset=True)

        # Create kinematic limb joints
        #
        jointTypes = (upperLimbName, midLimbName, lowerLimbName, limbTipName)
        kinematicTypes = ('FK', 'IK', 'Blend')

        limbFKJoints = [None] * 4
        limbIKJoints = [None] * 4
        limbBlendJoints = [None] * 4
        limbMatrices = (upperLimbMatrix, midLimbMatrix, lowerLimbMatrix, limbTipMatrix)
        kinematicJoints = (limbFKJoints, limbIKJoints, limbBlendJoints)

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = kinematicJoints[i][j - 1] if j > 0 else jointsGroup

                jointName = self.formatName(name=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.displayLocalAxis = True
                joint.setWorldMatrix(limbMatrices[j])

                kinematicJoints[i][j] = joint

        upperFKJoint, midFKJoint, lowerFKJoint, tipFKJoint = limbFKJoints
        upperIKJoint, midIKJoint, lowerIKJoint, tipIKJoint = limbIKJoints
        upperBlendJoint, midBlendJoint, lowerBlendJoint, tipBlendJoint = limbBlendJoints

        # Create switch control
        #
        upperOffsetAttr = f'{upperLimbName.lower()}Offset'
        midOffsetAttr = f'{midLimbName.lower()}Offset'
        lowerOffsetAttr = f'{lowerLimbName.lower()}Offset'

        upperDistance = om.MPoint(limbOrigin).distanceTo(midPoint)
        midDistance = om.MPoint(midPoint).distanceTo(lowerPoint)
        lowerDistance = om.MPoint(lowerPoint).distanceTo(limbGoal)
        limbLengths = (upperDistance, midDistance, lowerDistance)

        switchCtrlName = self.formatName(subname='Switch', type='control')
        switchCtrl = self.scene.createNode('transform', name=switchCtrlName, parent=controlsGroup)
        switchCtrl.addPointHelper('pyramid', 'fill', 'shaded', size=(10.0 * rigScale), localPosition=(0.0, 25.0, 0.0), localRotate=(0.0, 0.0, -90.0), colorRGB=darkColorRGB)
        switchCtrl.addConstraint('transformConstraint', [tipBlendJoint])
        switchCtrl.addDivider('Settings')
        switchCtrl.addAttr(longName='length', attributeType='doubleLinear', array=True, hidden=True)
        switchCtrl.addAttr(longName='mode', niceName='Mode (FK/IK)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName=upperOffsetAttr, attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName=midOffsetAttr, attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName=lowerOffsetAttr, attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName='pin', attributeType='float', min=0.0, max=1.0, keyable=True)
        switchCtrl.addAttr(longName='soften', attributeType='float', min=0.0, keyable=True)
        switchCtrl.addAttr(longName='twist', attributeType='doubleAngle', keyable=True)
        switchCtrl.addAttr(longName='autoTwist', attributeType='float', min=0.0, max=1.0, keyable=True)
        switchCtrl.setAttr('length', limbLengths)
        switchCtrl.lockAttr('length')
        switchCtrl.hideAttr('translate', 'rotate', 'scale', 'visibility', lock=True)
        self.publishNode(switchCtrl, alias='Switch')

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
        upperBlender = setuputils.createTransformBlends(upperFKJoint, upperIKJoint, upperBlendJoint, blender=blender)
        midBlender = setuputils.createTransformBlends(midFKJoint, midIKJoint, midBlendJoint, blender=blender)
        lowerBlender = setuputils.createTransformBlends(lowerFKJoint, lowerIKJoint, lowerBlendJoint, blender=blender)
        tipBlender = setuputils.createTransformBlends(tipFKJoint, tipIKJoint, tipBlendJoint, blender=blender)

        upperBlender.setName(self.formatName(subname=upperLimbName, type='blendTransform'))
        midBlender.setName(self.formatName(subname=midLimbName, type='blendTransform'))
        lowerBlender.setName(self.formatName(subname=lowerLimbName, type='blendTransform'))
        tipBlender.setName(self.formatName(subname=limbTipName, type='blendTransform'))

        # Setup limb length nodes
        #
        upperLengthName = self.formatName(name=upperLimbName, subname='Length', type='plusMinusAverage')
        upperLength = self.scene.createNode('plusMinusAverage', name=upperLengthName)
        upperLength.setAttr('operation', 1)  # Addition
        upperLength.connectPlugs(switchCtrl['length[0]'], 'input1D[0]')
        upperLength.connectPlugs(switchCtrl[upperOffsetAttr], 'input1D[1]')

        midLengthName = self.formatName(name=midLimbName, subname='Length', type='plusMinusAverage')
        midLength = self.scene.createNode('plusMinusAverage', name=midLengthName)
        midLength.setAttr('operation', 1)  # Addition
        midLength.connectPlugs(switchCtrl['length[1]'], 'input1D[0]')
        midLength.connectPlugs(switchCtrl[midOffsetAttr], 'input1D[1]')

        lowerLengthName = self.formatName(name=lowerLimbName, subname='Length', type='plusMinusAverage')
        lowerLength = self.scene.createNode('plusMinusAverage', name=lowerLengthName)
        lowerLength.setAttr('operation', 1)  # Addition
        lowerLength.connectPlugs(switchCtrl['length[2]'], 'input1D[0]')
        lowerLength.connectPlugs(switchCtrl[lowerOffsetAttr], 'input1D[1]')

        limbLength = self.formatName(subname='Length', type='plusMinusAverage')
        limbLength = self.scene.createNode('plusMinusAverage', name=limbLength)
        limbLength.setAttr('operation', 1)  # Addition
        limbLength.connectPlugs(upperLength['output1D'], 'input1D[0]')
        limbLength.connectPlugs(midLength['output1D'], 'input1D[1]')
        limbLength.connectPlugs(lowerLength['output1D'], 'input1D[2]')

        upperWeightName = self.formatName(name=upperLimbName, subname='Weight', type='floatMath')
        upperWeight = self.scene.createNode('floatMath', name=upperWeightName)
        upperWeight.operation = 3  # Divide
        upperWeight.connectPlugs(upperLength['output1D'], 'inFloatA')
        upperWeight.connectPlugs(limbLength['output1D'], 'inFloatB')

        midWeightName = self.formatName(name=midLimbName, subname='Weight', type='floatMath')
        midWeight = self.scene.createNode('floatMath', name=midWeightName)
        midWeight.operation = 3  # Divide
        midWeight.connectPlugs(midLength['output1D'], 'inFloatA')
        midWeight.connectPlugs(limbLength['output1D'], 'inFloatB')

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

        midFKMatrix = mirrorMatrix * midLimbMatrix

        midFKSpaceName = self.formatName(name=midLimbName, kinemat='FK', type='space')
        midFKSpace = self.scene.createNode('transform', name=midFKSpaceName, parent=upperFKCtrl)
        midFKSpace.setWorldMatrix(midFKMatrix)
        midFKSpace.freezeTransform()

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(midFKMatrix * upperFKMatrix.inverse())
        midFKComposeMatrixName = self.formatName(name=midLimbName, kinemat='FK', type='composeMatrix')
        midFKComposeMatrix = self.scene.createNode('composeMatrix', name=midFKComposeMatrixName)
        midFKComposeMatrix.setAttr('inputTranslate', translation)
        midFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        midFKComposeMatrix.connectPlugs(upperLength['output1D'], 'inputTranslateX')
        midFKComposeMatrix.connectPlugs('outputMatrix', midFKSpace['offsetParentMatrix'])

        midFKCtrlName = self.formatName(name=midLimbName, kinemat='FK', type='control')
        midFKCtrl = self.scene.createNode('transform', name=midFKCtrlName, parent=midFKSpace)
        midFKCtrl.addDivider('Spaces')
        midFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        midFKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(midFKCtrl, alias=f'{midLimbName}_FK')

        midFKSpaceSwitch = midFKSpace.addSpaceSwitch([upperFKCtrl, motionCtrl], maintainOffset=True, skipRotateX=True, skipRotateY=True)
        midFKSpaceSwitch.weighted = True
        midFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        midFKSpaceSwitch.connectPlugs(midFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        midFKSpaceSwitch.connectPlugs(midFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')
        midFKSpaceSwitch.connectPlugs(midLength['output1D'], 'target[0].targetOffsetTranslateX')

        upperInverseLength = None

        if requiresMirroring:

            upperInverseLengthName = self.formatName(name=upperLimbName, subname='InverseLength', type='floatMath')
            upperInverseLength = self.scene.createNode('floatMath', name=upperInverseLengthName)
            upperInverseLength.operation = 5  # Negate
            upperInverseLength.connectPlugs(upperLength['output1D'], 'inFloatA')
            upperInverseLength.connectPlugs('outFloat', midFKComposeMatrix['inputTranslateX'], force=True)
            upperInverseLength.connectPlugs('outFloat', midFKSpaceSwitch['target[0].targetOffsetTranslateX'], force=True)

        lowerFKMatrix = mirrorMatrix * lowerLimbMatrix

        lowerFKSpaceName = self.formatName(name=lowerLimbName, kinemat='FK', type='space')
        lowerFKSpace = self.scene.createNode('transform', name=lowerFKSpaceName, parent=midFKCtrl)
        lowerFKSpace.setWorldMatrix(lowerFKMatrix)
        lowerFKSpace.freezeTransform()

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(lowerFKMatrix * midFKMatrix.inverse())
        lowerFKComposeMatrixName = self.formatName(name=lowerLimbName, kinemat='FK', type='composeMatrix')
        lowerFKComposeMatrix = self.scene.createNode('composeMatrix', name=lowerFKComposeMatrixName)
        lowerFKComposeMatrix.setAttr('inputTranslate', translation)
        lowerFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        lowerFKComposeMatrix.connectPlugs(midLength['output1D'], 'inputTranslateX')
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

        midInverseLength = None

        if requiresMirroring:

            midInverseLengthName = self.formatName(name=midLimbName, subname='InverseLength', type='floatMath')
            midInverseLength = self.scene.createNode('floatMath', name=midInverseLengthName)
            midInverseLength.operation = 5  # Negate
            midInverseLength.connectPlugs(midLength['output1D'], 'inFloatA')
            midInverseLength.connectPlugs('outFloat', lowerFKComposeMatrix['inputTranslateX'], force=True)
            midInverseLength.connectPlugs('outFloat', lowerFKSpaceSwitch['target[0].targetOffsetTranslateX'], force=True)

        tipFKTargetName = self.formatName(name=limbTipName, kinemat='FK', type='target')
        tipFKTarget = self.scene.createNode('transform', name=tipFKTargetName, parent=lowerFKCtrl)

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(limbTipMatrix * lowerLimbMatrix.inverse())
        tipFKComposeMatrixName = self.formatName(name=limbTipName, kinemat='FK', type='composeMatrix')
        tipFKComposeMatrix = self.scene.createNode('composeMatrix', name=tipFKComposeMatrixName)
        tipFKComposeMatrix.setAttr('inputTranslate', translation)
        tipFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        tipFKComposeMatrix.connectPlugs(lowerLength['output1D'], 'inputTranslateX')
        tipFKComposeMatrix.connectPlugs('outputMatrix', tipFKTarget['offsetParentMatrix'])

        lowerInverseLengthName = self.formatName(name=lowerLimbName, subname='InverseLength', type='floatMath')
        lowerInverseLength = self.scene.createNode('floatMath', name=lowerInverseLengthName)
        lowerInverseLength.operation = 5  # Negate
        lowerInverseLength.connectPlugs(lowerLength['output1D'], 'inFloatA')

        if requiresMirroring:

            lowerInverseLength.connectPlugs('outFloat', tipFKComposeMatrix['inputTranslateX'], force=True)

        upperFKJoint.addConstraint('transformConstraint', [upperFKCtrl], maintainOffset=requiresMirroring)
        midFKJoint.addConstraint('transformConstraint', [midFKCtrl], maintainOffset=requiresMirroring)
        lowerFKJoint.addConstraint('transformConstraint', [lowerFKCtrl], maintainOffset=requiresMirroring)
        tipFKJoint.addConstraint('transformConstraint', [tipFKTarget], maintainOffset=requiresMirroring)

        # Add FK control shapes
        #
        upperFKShape = upperFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        upperFKShape.reorientAndScaleToFit(midFKCtrl)

        midFKShape = midFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        midFKShape.reorientAndScaleToFit(lowerFKCtrl)

        lowerFKShape = lowerFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        lowerFKShape.reorientAndScaleToFit(tipFKTarget)

        supportsResizing = int(mc.about(version=True)) >= 2025

        if supportsResizing:

            # Setup upper FK shape resizing
            #
            upperHalfLengthName = self.formatName(name=upperLimbName, subname='HalfLength', type='linearMath')
            upperHalfLength = self.scene.createNode('linearMath', name=upperHalfLengthName)
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

            # Setup mid FK shape resizing
            #
            midHalfLengthName = self.formatName(name=midLimbName, subname='HalfLength', type='linearMath')
            midHalfLength = self.scene.createNode('linearMath', name=midHalfLengthName)
            midHalfLength.operation = 6  # Half
            midHalfLength.connectPlugs(midLength['output1D'], 'inFloatA')
            midHalfLength.connectPlugs('outFloat', midFKShape['localPositionX'])

            if requiresMirroring:

                midInverseLength.connectPlugs('outFloat', midHalfLength['inFloatA'], force=True)

            midScaleLengthName = self.formatName(name=midLimbName, subname='ScaleLength', type='divDoubleLinear')
            midScaleLength = self.scene.createNode('divDoubleLinear', name=midScaleLengthName)
            midScaleLength.connectPlugs(midLength['output1D'], 'input1')
            midScaleLength.connectPlugs(midFKShape['size'], 'input2')
            midScaleLength.connectPlugs('output', midFKShape['localScaleX'])

            # Setup lower FK shape resizing
            #
            lowerHalfLengthName = self.formatName(name=lowerLimbName, subname='HalfLength', type='linearMath')
            lowerHalfLength = self.scene.createNode('linearMath', name=lowerHalfLengthName)
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
        upperFKCtrl.tagAsController(parent=limbCtrl, children=[midFKCtrl])
        midFKCtrl.tagAsController(parent=upperFKCtrl, children=[lowerFKCtrl])
        lowerFKCtrl.tagAsController(parent=upperFKCtrl)

        # Create IK limb control
        #
        defaultWorldSpace = 1.0 if isLeg else 0.0
        defaultLimbSpace = 1.0 if isArm else 0.0
        extremityIKMatrix = mirrorMatrix * extremityMatrix
        extremityIKPreEulerRotation = transformutils.decomposeTransformMatrix(extremityIKMatrix)[1]

        limbIKSpaceName = self.formatName(name=lowerLimbName, kinemat='IK', type='space')
        limbIKSpace = self.scene.createNode('transform', name=limbIKSpaceName, parent=controlsGroup)
        limbIKSpace.setWorldMatrix(extremityIKMatrix, skipRotate=True)
        limbIKSpace.freezeTransform()

        limbIKCtrlName = self.formatName(name=lowerLimbName, kinemat='IK', type='control')
        limbIKCtrl = self.scene.createNode('freeform', name=limbIKCtrlName, parent=limbIKSpace)
        limbIKCtrl.addPointHelper('diamond', size=(30.0 * rigScale), lineWidth=3.0, colorRGB=colorRGB)
        limbIKCtrl.setPreEulerRotation(extremityIKPreEulerRotation)
        limbIKCtrl.addDivider('Spaces')
        limbIKCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, default=defaultWorldSpace, keyable=True)
        limbIKCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='positionSpaceW2', niceName=f'Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='positionSpaceW3', niceName=f'Position Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='positionSpaceW4', niceName=f'Position Space ({limbName})', attributeType='float', min=0.0, max=1.0, default=defaultLimbSpace, keyable=True)
        limbIKCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='rotationSpaceW3', niceName=f'Rotation Space ({spineAlias})', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.addAttr(longName='rotationSpaceW4', niceName=f'Rotation Space ({limbName})', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbIKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(limbIKCtrl, alias=f'{lowerLimbName}_IK')

        limbIKOffsetCtrlName = self.formatName(name=lowerLimbName, kinemat='IK', subname='Offset', type='control')
        limbIKOffsetCtrl = self.scene.createNode('transform', name=limbIKOffsetCtrlName, parent=limbIKCtrl)
        limbIKOffsetCtrl.addPointHelper('cross', size=(15.0 * rigScale), colorRGB=lightColorRGB)
        limbIKOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(limbIKOffsetCtrl, alias=f'{lowerLimbName}_IK_Offset')

        limbIKSpaceSwitch = limbIKSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, spineCtrl, limbCtrl], maintainOffset=True)
        limbIKSpaceSwitch.weighted = True
        limbIKSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
        limbIKSpaceSwitch.connectPlugs(limbIKCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')

        limbIKCtrl.userProperties['space'] = limbIKSpace.uuid()
        limbIKCtrl.userProperties['spaceSwitch'] = limbIKSpaceSwitch.uuid()
        limbIKCtrl.userProperties['offset'] = limbIKOffsetCtrl.uuid()

        limbIKCtrl.tagAsController(parent=limbCtrl, children=[limbIKOffsetCtrl])
        limbIKOffsetCtrl.tagAsController(parent=limbIKCtrl)

        # Create IK softener
        #
        ikHandleTargetName = self.formatName(kinemat='IK', type='target')
        ikHandleTarget = self.scene.createNode('transform', name=ikHandleTargetName, parent=privateGroup)
        ikHandleTarget.displayLocalAxis = True
        ikHandleTarget.visibility = False
        ikHandleTarget.setWorldMatrix(limbTipMatrix, skipRotate=True, skipScale=True)

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
        limbIKSoftener.connectPlugs(limbIKOffsetCtrl[f'worldMatrix[{limbIKOffsetCtrl.instanceNumber()}]'], 'endMatrix')
        limbIKSoftener.connectPlugs(ikHandleTarget[f'parentInverseMatrix[{ikHandleTarget.instanceNumber()}]'], 'parentInverseMatrix')
        limbIKSoftener.connectPlugs('outPosition', ikHandleTarget['translate'])

        # Create follow joint
        #
        preferredRightVector = transformutils.breakMatrix(extremityMatrix, normalize=True)[2]
        poleVector = (forwardVector ^ preferredRightVector).normal()
        rightVector = (poleVector ^ forwardVector).normal()

        followMatrix = transformutils.createAimMatrix(0, forwardVector, 1, poleVector, origin=limbOrigin, upAxisSign=-1)
        followTipMatrix = transformutils.createRotationMatrix(followMatrix) * transformutils.createTranslateMatrix(limbTipMatrix)

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

        followTwistJointName = self.formatName(subname='FollowTwist', type='joint')
        followTwistJoint = self.scene.createNode('joint', name=followTwistJointName, parent=followJoint)
        followTwistJoint.connectPlugs(followHalfLength['outDistance'], 'translateX')
        followTwistJoint.connectPlugs(followJoint['scale'], 'scale')

        followTargetName = self.formatName(subname='Follow', type='target')
        followTarget = self.scene.createNode('transform', name=followTargetName, parent=followTwistJoint)
        followTarget.displayLocalAxis = True

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

        # Setup follow auto twist
        #
        followTwistSolver = self.scene.createNode('twistSolver')
        followTwistSolver.forwardAxis = 0  # X
        followTwistSolver.upAxis = 2  # Z
        followTwistSolver.startOffsetMatrix = mirrorMatrix
        followTwistSolver.connectPlugs(followJoint[f'worldMatrix[{followJoint.instanceNumber()}]'], 'startMatrix')
        followTwistSolver.connectPlugs(limbIKCtrl[f'worldMatrix[{limbIKCtrl.instanceNumber()}]'], 'endMatrix')

        followTwistEnvelope = self.scene.createNode('floatMath')
        followTwistEnvelope.operation = 22
        followTwistEnvelope.connectPlugs(switchCtrl['autoTwist'], 'weight')
        followTwistEnvelope.connectPlugs(followTwistSolver['roll'], 'inAngleB')
        followTwistEnvelope.connectPlugs('outAngle', followTwistJoint['rotateX'])

        # Calculate default PV matrix
        #
        upVector = ((transformutils.breakMatrix(upperLimbMatrix, normalize=True)[1] * 0.5) + (transformutils.breakMatrix(midLimbMatrix, normalize=True)[1] * 0.5)).normal()
        forwardVector = (lowerPoint - limbOrigin).normal()
        rightVector = (forwardVector ^ upVector).normal()
        poleVector = (forwardVector ^ rightVector).normal()

        upperVector = midPoint - limbOrigin
        upperDot = forwardVector * upperVector

        poleOrigin = limbOrigin + (forwardVector * upperDot)
        polePosition = poleOrigin + (poleVector * (sum(limbLengths) - lowerDistance))
        poleMatrix = transformutils.createTranslateMatrix(polePosition)

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
        limbPVCtrl.addAttr(longName='transformSpaceW4', niceName=f'Transform Space (Leg)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW5', niceName=f'Transform Space (Foot)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.addAttr(longName='transformSpaceW6', niceName='Transform Space (Auto)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        limbPVCtrl.prepareChannelBoxForAnimation()
        self.publishNode(limbPVCtrl, alias=f'{limbName}_PV')

        limbPVSpaceSwitch = limbPVSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, spineCtrl, limbCtrl, limbIKCtrl, followTarget], weighted=True, maintainOffset=True)
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW0'], 'target[0].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW1'], 'target[1].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW2'], 'target[2].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW3'], 'target[3].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW4'], 'target[4].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW5'], 'target[5].targetWeight')
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW6'], 'target[6].targetWeight')

        limbPVCtrl.userProperties['space'] = limbPVSpace.uuid()
        limbPVCtrl.userProperties['spaceSwitch'] = limbPVSpaceSwitch.uuid()

        limbPVCtrl.tagAsController(parent=limbIKCtrl)

        # Create spring IK joints
        # It is important to know that pole vector space is based on the preferred rotation of the start joint!
        #
        preferredLowerPoint = transformutils.projectPoint(lowerPoint, rightVector, origin=limbOrigin)
        projectedLowerPoint = limbGoal + ((preferredLowerPoint - om.MVector(limbGoal)).normal() * lowerDistance)

        upperSpringMatrix, midSpringMatrix, lowerSpringMatrix = kinematicutils.solveIk2BoneChain(limbOrigin, upperDistance, projectedLowerPoint, midDistance, poleVector)
        lowerSpringMatrix = transformutils.createAimMatrix(0, (limbGoal - projectedLowerPoint).normal(), 2, rightVector, origin=projectedLowerPoint)
        tipSpringMatrix = transformutils.createRotationMatrix(lowerSpringMatrix) * transformutils.createTranslateMatrix(limbTipMatrix)
        springMatrices = (upperSpringMatrix, midSpringMatrix, lowerSpringMatrix, tipSpringMatrix)

        limbSIKJoints = [None] * 4

        for (i, (jointType, jointMatrix)) in enumerate(zip(jointTypes, springMatrices)):

            parent = limbSIKJoints[i - 1] if (i > 0) else jointsGroup

            jointName = self.formatName(name=jointType, kinemat='SIK', type='joint')
            joint = self.scene.createNode('joint', name=jointName, parent=parent)
            joint.displayLocalAxis = True
            joint.setWorldMatrix(jointMatrix, skipScale=True)

            limbSIKJoints[i] = joint

        upperSIKJoint, midSIKJoint, lowerSIKJoint, tipSIKJoint = limbSIKJoints
        upperSIKJoint.addConstraint('pointConstraint', [limbCtrl])

        limbSpringHandle, limbSpringEffector = kinematicutils.applySpringSolver(upperSIKJoint, tipSIKJoint)
        limbSpringHandle.setName(self.formatName(kinemat='Spring', type='ikHandle'))
        limbSpringHandle.setParent(privateGroup)
        limbSpringHandle.addConstraint('transformConstraint', [ikHandleTarget])
        limbSpringEffector.setName(self.formatName(kinemat='Spring', type='ikEffector'))

        followTwistBreakMatrixName = self.formatName(subname='FollowTwist', type='breakMatrix')
        followTwistBreakMatrix = self.scene.createNode('breakMatrix', name=followTwistBreakMatrixName)
        followTwistBreakMatrix.normalize = True
        followTwistBreakMatrix.connectPlugs(followTwistJoint[f'worldMatrix[{followTwistJoint.instanceNumber()}]'], 'inMatrix')

        followTwistVectorMathName = self.formatName(subname='FollowTwist', type='vectorMath')
        followTwistVectorMath = self.scene.createNode('vectorMath', name=followTwistVectorMathName)
        followTwistVectorMath.operation = 5  # Negate
        followTwistVectorMath.connectPlugs(followTwistBreakMatrix['row2X'], 'inFloatAX')
        followTwistVectorMath.connectPlugs(followTwistBreakMatrix['row2Y'], 'inFloatAY')
        followTwistVectorMath.connectPlugs(followTwistBreakMatrix['row2Z'], 'inFloatAZ')

        followTwistVectorMultMatrixName = self.formatName(subname='FollowTwist', type='multiplyVectorByMatrix')
        followTwistVectorMultMatrix = self.scene.createNode('multiplyVectorByMatrix', name=followTwistVectorMultMatrixName)
        followTwistVectorMultMatrix.connectPlugs(followTwistVectorMath['outFloat'], 'input')
        followTwistVectorMultMatrix.connectPlugs(upperSIKJoint[f'parentInverseMatrix[{upperSIKJoint.instanceNumber()}]'], 'matrix')
        followTwistVectorMultMatrix.connectPlugs('output', limbSpringHandle['poleVector'])

        # Setup stretch on IK joints
        #
        upperIKStretchName = self.formatName(name=upperLimbName, subname='Stretch', kinemat='IK', type='multDoubleLinear')
        upperIKStretch = self.scene.createNode('multDoubleLinear', name=upperIKStretchName)
        upperIKStretch.connectPlugs(upperLength['output1D'], 'input1')
        upperIKStretch.connectPlugs(limbIKSoftener['softScale'], 'input2')

        upperIKEnvelopeName = self.formatName(name=upperLimbName, subname='Envelope', kinemat='IK', type='blendTwoAttr')
        upperIKEnvelope = self.scene.createNode('blendTwoAttr', name=upperIKEnvelopeName)
        upperIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        upperIKEnvelope.connectPlugs(upperLength['output1D'], 'input[0]')
        upperIKEnvelope.connectPlugs(upperIKStretch['output'], 'input[1]')
        upperIKEnvelope.connectPlugs('output', midSIKJoint['translateX'])

        midIKStretchName = self.formatName(name=midLimbName, subname='Stretch', kinemat='IK', type='multDoubleLinear')
        midIKStretch = self.scene.createNode('multDoubleLinear', name=midIKStretchName)
        midIKStretch.connectPlugs(midLength['output1D'], 'input1')
        midIKStretch.connectPlugs(limbIKSoftener['softScale'], 'input2')

        midIKEnvelopeName = self.formatName(name=midLimbName, subname='Envelope', kinemat='IK', type='blendTwoAttr')
        midIKEnvelope = self.scene.createNode('blendTwoAttr', name=midIKEnvelopeName)
        midIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        midIKEnvelope.connectPlugs(midLength['output1D'], 'input[0]')
        midIKEnvelope.connectPlugs(midIKStretch['output'], 'input[1]')
        midIKEnvelope.connectPlugs('output', lowerSIKJoint['translateX'])

        lowerIKStretchName = self.formatName(name=lowerLimbName, subname='Stretch', kinemat='IK', type='multDoubleLinear')
        lowerIKStretch = self.scene.createNode('multDoubleLinear', name=lowerIKStretchName)
        lowerIKStretch.connectPlugs(lowerLength['output1D'], 'input1')
        lowerIKStretch.connectPlugs(limbIKSoftener['softScale'], 'input2')

        lowerIKEnvelopeName = self.formatName(name=lowerLimbName, subname='Envelope', kinemat='IK', type='blendTwoAttr')
        lowerIKEnvelope = self.scene.createNode('blendTwoAttr', name=lowerIKEnvelopeName)
        lowerIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        lowerIKEnvelope.connectPlugs(lowerLength['output1D'], 'input[0]')
        lowerIKEnvelope.connectPlugs(lowerIKStretch['output'], 'input[1]')
        lowerIKEnvelope.connectPlugs('output', tipSIKJoint['translateX'])

        # Create lower IK controls
        #
        lowerIKRotSpaceName = self.formatName(name=lowerLimbName, subname='IK', kinemat='Rot', type='space')
        lowerIKRotSpace = self.scene.createNode('transform', name=lowerIKRotSpaceName, parent=controlsGroup)
        lowerIKRotSpace.setWorldMatrix(limbTipMatrix)
        lowerIKRotSpace.freezeTransform()

        lowerIKRotCtrlName = self.formatName(name=lowerLimbName, subname='IK', kinemat='Rot', type='control')
        lowerIKRotCtrl = self.scene.createNode('transform', name=lowerIKRotCtrlName, parent=lowerIKRotSpace)
        lowerIKRotCtrl.addDivider('Spaces')
        lowerIKRotCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (Local)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        lowerIKRotCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        lowerIKRotCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Aim)', attributeType='float', min=0.0, max=1.0, keyable=True)
        lowerIKRotCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Spring)', attributeType='float', min=0.0, max=1.0, keyable=True)
        lowerIKRotCtrl.prepareChannelBoxForAnimation()
        self.publishNode(lowerIKRotCtrl, alias=f'{lowerLimbName}_IK_Rot')

        lowerIKTransCtrlName = self.formatName(name=lowerLimbName, subname='IK', kinemat='Trans', type='control')
        lowerIKTransCtrl = self.scene.createNode('transform', name=lowerIKTransCtrlName, parent=lowerIKRotCtrl)
        lowerIKTransCtrl.addPointHelper('sphere', 'cross', size=(15.0 * rigScale), colorRGB=lightColorRGB)
        lowerIKTransCtrl.hideAttr('rotate', 'scale', lock=True)
        lowerIKTransCtrl.setWorldMatrix(lowerLimbMatrix)
        lowerIKTransCtrl.freezeTransform()
        lowerIKTransCtrl.prepareChannelBoxForAnimation()
        self.publishNode(lowerIKTransCtrl, alias=f'{lowerLimbName}_IK_Trans')

        lowerIKTransInverseName = self.formatName(name=lowerLimbName, subname='IK', kinemat='Trans', type='floatMath')
        lowerIKTransInverse = self.scene.createNode('floatMath', name=lowerIKTransInverseName)
        lowerIKTransInverse.operation = 5  # Negate
        lowerIKTransInverse.connectPlugs(lowerIKEnvelope['output'], 'inFloatA')

        lowerIKTransComposeMatrixName = self.formatName(name=lowerLimbName, subname='IK', kinemat='Trans', type='composeMatrix')
        lowerIKTransComposeMatrix = self.scene.createNode('composeMatrix', name=lowerIKTransComposeMatrixName)
        lowerIKTransComposeMatrix.connectPlugs(lowerIKTransInverse['outFloat'], 'inputTranslateX')
        lowerIKTransComposeMatrix.connectPlugs('outputMatrix', lowerIKTransCtrl['offsetParentMatrix'])

        lowerIKRotShape = lowerIKRotCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), colorRGB=colorRGB)
        lowerIKRotShape.reorientAndScaleToFit(lowerIKTransCtrl)

        lowerIKRotSpaceSwitch = lowerIKRotSpace.addSpaceSwitch([ikHandleTarget, limbIKCtrl, motionCtrl, followTwistJoint, tipSIKJoint], weighted=True, maintainOffset=True)
        lowerIKRotSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 0.0)}, {'targetWeight': (0.0, 1.0, 1.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        lowerIKRotSpaceSwitch.connectPlugs(lowerIKRotCtrl['rotationSpaceW0'], 'target[1].targetRotateWeight')
        lowerIKRotSpaceSwitch.connectPlugs(lowerIKRotCtrl['rotationSpaceW1'], 'target[2].targetRotateWeight')
        lowerIKRotSpaceSwitch.connectPlugs(lowerIKRotCtrl['rotationSpaceW2'], 'target[3].targetRotateWeight')
        lowerIKRotSpaceSwitch.connectPlugs(lowerIKRotCtrl['rotationSpaceW3'], 'target[4].targetRotateWeight')

        # Override lower IK world space
        #
        limbIKRotWorldMatrixName = self.formatName(name=lowerLimbName, subname='IK', kinemat='World', type='aimMatrix')
        limbIKRotWorldMatrix = self.scene.createNode('aimMatrix', name=limbIKRotWorldMatrixName)
        limbIKRotWorldMatrix.connectPlugs(limbIKCtrl[f'worldMatrix[{limbIKCtrl.instanceNumber()}]'], 'inputMatrix')
        limbIKRotWorldMatrix.setAttr('primary', {'primaryInputAxis': (0.0, 0.0, 1.0), 'primaryMode': 2, 'primaryTargetVector': (0.0, 0.0, 1.0)})  # Align
        limbIKRotWorldMatrix.connectPlugs(limbIKCtrl[f'worldMatrix[{limbIKCtrl.instanceNumber()}]'], 'primaryTargetMatrix')
        limbIKRotWorldMatrix.setAttr('secondary', {'secondaryInputAxis': (1.0, 0.0, 0.0), 'secondaryMode': 2, 'secondaryTargetVector': (0.0, 0.0, -1.0)})  # Align
        limbIKRotWorldMatrix.connectPlugs(motionCtrl[f'worldMatrix[{motionCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')
        limbIKRotWorldMatrix.connectPlugs('outputMatrix', lowerIKRotSpaceSwitch['target[2].targetMatrix'], force=True)

        offsetMatrix = limbIKRotWorldMatrix.outputMatrix * lowerIKRotSpace.parentInverseMatrix()
        offsetTranslate, offsetRotate, offsetScale = transformutils.decomposeTransformMatrix(offsetMatrix)

        lowerIKRotSpaceSwitch.setAttr('target[1].targetOffsetTranslate', offsetTranslate)
        lowerIKRotSpaceSwitch.setAttr('target[1].targetOffsetRotate', offsetRotate, convertUnits=False)
        
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

        midRestMatrixName = self.formatName(name=midLimbName, subname='Rest', type='composeMatrix')
        midRestMatrix = self.scene.createNode('composeMatrix', name=midRestMatrixName)
        midRestMatrix.connectPlugs(upperLength['output1D'], 'inputTranslateX')
        midRestMatrix.connectPlugs(limbDecomposeMatrix['outputScale'], 'inputScale')

        lowerRestMatrixName = self.formatName(name=lowerLimbName, subname='Rest', type='composeMatrix')
        lowerRestMatrix = self.scene.createNode('composeMatrix', name=lowerRestMatrixName)
        lowerRestMatrix.connectPlugs(midLength['output1D'], 'inputTranslateX')
        lowerRestMatrix.useEulerRotation = True
        lowerRestMatrix.inputRotateZ = lowerIKJoint.getAttr('rotateZ')
        lowerRestMatrix.connectPlugs(limbDecomposeMatrix['outputScale'], 'inputScale')

        tipRestMatrixName = self.formatName(name=limbTipName, subname='Rest', type='composeMatrix')
        tipRestMatrix = self.scene.createNode('composeMatrix', name=tipRestMatrixName)
        tipRestMatrix.connectPlugs(lowerLength['output1D'], 'inputTranslateX')
        tipRestMatrix.useEulerRotation = True
        tipRestMatrix.inputRotateZ = tipIKJoint.getAttr('rotateZ')
        tipRestMatrix.connectPlugs(limbDecomposeMatrix['outputScale'], 'inputScale')

        limbRPEmulatorName = self.formatName(kinemat='RP', type='ikEmulator')
        limbRPEmulator = self.scene.createNode('ikEmulator', name=limbRPEmulatorName)
        limbRPEmulator.forwardAxis = 0  # X
        limbRPEmulator.forwardAxisFlip = False
        limbRPEmulator.upAxis = 1  # Y
        limbRPEmulator.upAxisFlip = True
        limbRPEmulator.poleType = 2  # Matrix
        limbRPEmulator.segmentScaleCompensate = True
        limbRPEmulator.connectPlugs(upperRestMatrix['outputMatrix'], 'restMatrix[0]')
        limbRPEmulator.connectPlugs(midRestMatrix['outputMatrix'], 'restMatrix[1]')
        limbRPEmulator.connectPlugs(lowerRestMatrix['outputMatrix'], 'restMatrix[2]')
        limbRPEmulator.connectPlugs(switchCtrl['stretch'], 'stretch')
        limbRPEmulator.connectPlugs(switchCtrl['twist'], 'twist')
        limbRPEmulator.connectPlugs(limbPVCtrl[f'worldMatrix[{limbPVCtrl.instanceNumber()}]'], 'poleMatrix')
        limbRPEmulator.connectPlugs(lowerIKTransCtrl[f'worldMatrix[{lowerIKTransCtrl.instanceNumber()}]'], 'goal')
        
        limbSCEmulatorName = self.formatName(kinemat='SC', type='ikEmulator')
        limbSCEmulator = self.scene.createNode('ikEmulator', name=limbSCEmulatorName)
        limbSCEmulator.forwardAxis = 0  # X
        limbSCEmulator.forwardAxisFlip = False
        limbSCEmulator.upAxis = 1  # Y
        limbSCEmulator.upAxisFlip = True
        limbSCEmulator.poleType = 3  # Goal
        limbSCEmulator.segmentScaleCompensate = True
        limbSCEmulator.connectPlugs(limbRPEmulator['outWorldMatrix[2]'], 'restMatrix[0]')
        limbSCEmulator.connectPlugs(tipRestMatrix['outputMatrix'], 'restMatrix[1]')
        limbSCEmulator.connectPlugs(switchCtrl['stretch'], 'stretch')
        limbSCEmulator.connectPlugs(lowerIKRotCtrl[f'worldMatrix[{lowerIKRotCtrl.instanceNumber()}]'], 'goal')
        limbSCEmulator.connectPlugs(lowerIKJoint[f'parentInverseMatrix[{lowerIKJoint.instanceNumber()}]'], 'parentInverseMatrix')

        # Connect emulators to IK joints
        #
        upperIKMatrixName = self.formatName(name=upperLimbName, subname='IK', type='decomposeMatrix')
        upperIKMatrix = self.scene.createNode('decomposeMatrix', name=upperIKMatrixName)
        upperIKMatrix.connectPlugs(limbRPEmulator['outMatrix[0]'], 'inputMatrix')
        upperIKMatrix.connectPlugs(upperIKJoint['rotateOrder'], 'inputRotateOrder')
        upperIKMatrix.connectPlugs('outputTranslate', upperIKJoint['translate'])
        upperIKMatrix.connectPlugs('outputRotate', upperIKJoint['rotate'])
        upperIKMatrix.connectPlugs('outputScale', upperIKJoint['scale'])

        midIKName = self.formatName(name=midLimbName, subname='IK', type='decomposeMatrix')
        midIKMatrix = self.scene.createNode('decomposeMatrix', name=midIKName)
        midIKMatrix.connectPlugs(limbRPEmulator['outMatrix[1]'], 'inputMatrix')
        midIKMatrix.connectPlugs(midIKJoint['rotateOrder'], 'inputRotateOrder')
        midIKMatrix.connectPlugs('outputTranslate', midIKJoint['translate'])
        midIKMatrix.connectPlugs('outputRotate', midIKJoint['rotate'])
        midIKMatrix.connectPlugs('outputScale', midIKJoint['scale'])

        lowerIKMatrixName = self.formatName(name=lowerLimbName, subname='IK', type='decomposeMatrix')
        lowerIKMatrix = self.scene.createNode('decomposeMatrix', name=lowerIKMatrixName)
        lowerIKMatrix.connectPlugs(limbSCEmulator['outMatrix[0]'], 'inputMatrix')
        lowerIKMatrix.connectPlugs(lowerIKJoint['rotateOrder'], 'inputRotateOrder')
        lowerIKMatrix.connectPlugs('outputTranslate', lowerIKJoint['translate'])
        lowerIKMatrix.connectPlugs('outputRotate', lowerIKJoint['rotate'])
        lowerIKMatrix.connectPlugs('outputScale', lowerIKJoint['scale'])

        tipIKMatrixName = self.formatName(name=limbTipName, subname='IK', type='decomposeMatrix')
        tipIKMatrix = self.scene.createNode('decomposeMatrix', name=tipIKMatrixName)
        tipIKMatrix.connectPlugs(limbSCEmulator['outMatrix[1]'], 'inputMatrix')
        tipIKMatrix.connectPlugs(tipIKJoint['rotateOrder'], 'inputRotateOrder')
        tipIKMatrix.connectPlugs('outputTranslate', tipIKJoint['translate'])
        tipIKMatrix.connectPlugs('outputRotate', tipIKJoint['rotate'])
        tipIKMatrix.connectPlugs('outputScale', tipIKJoint['scale'])

        # Create hinge controls
        #
        upperHingeName = self.__default_hinge_names__[0]
        upperHingeMatrix = transformutils.lerpMatrix(
            transformutils.createRotationMatrix(upperLimbMatrix) * transformutils.createTranslateMatrix(midLimbMatrix),
            midLimbMatrix,
            weight=0.5
        )

        upperHingeSpaceName = self.formatName(name=upperHingeName, type='space')
        upperHingeSpace = self.scene.createNode('transform', name=upperHingeSpaceName, parent=controlsGroup)
        upperHingeSpace.setWorldMatrix(upperHingeMatrix, skipScale=True)
        upperHingeSpace.freezeTransform()
        upperHingeSpace.addConstraint('pointConstraint', [midBlendJoint])
        upperHingeSpace.addConstraint('orientConstraint', [upperBlendJoint, midBlendJoint])
        upperHingeSpace.addConstraint('scaleConstraint', [limbCtrl])

        upperHingeCtrlName = self.formatName(name=upperHingeName, type='control')
        upperHingeCtrl = self.scene.createNode('transform', name=upperHingeCtrlName, parent=upperHingeSpace)
        upperHingeCtrl.addPointHelper('square', size=(20.0 * rigScale), localRotate=(45.0, 0.0, 0.0), lineWidth=4.0, colorRGB=darkColorRGB)
        upperHingeCtrl.prepareChannelBoxForAnimation()
        upperHingeCtrl.userProperties['space'] = upperHingeSpace.uuid()
        self.publishNode(upperHingeCtrl, alias=upperHingeName)

        lowerHingeName = self.__default_hinge_names__[1]
        lowerHingeMatrix = transformutils.lerpMatrix(
            transformutils.createRotationMatrix(midLimbMatrix) * transformutils.createTranslateMatrix(lowerLimbMatrix),
            lowerLimbMatrix,
            weight=0.5
        )

        lowerHingeSpaceName = self.formatName(name=lowerHingeName, type='space')
        lowerHingeSpace = self.scene.createNode('transform', name=lowerHingeSpaceName, parent=controlsGroup)
        lowerHingeSpace.setWorldMatrix(lowerHingeMatrix, skipScale=True)
        lowerHingeSpace.freezeTransform()
        lowerHingeSpace.addConstraint('pointConstraint', [lowerBlendJoint])
        lowerHingeSpace.addConstraint('orientConstraint', [midBlendJoint, lowerBlendJoint])
        lowerHingeSpace.addConstraint('scaleConstraint', [limbCtrl])

        lowerHingeCtrlName = self.formatName(name=lowerHingeName, type='control')
        lowerHingeCtrl = self.scene.createNode('transform', name=lowerHingeCtrlName, parent=lowerHingeSpace)
        lowerHingeCtrl.addPointHelper('square', size=(20.0 * rigScale), localRotate=(45.0, 0.0, 0.0), lineWidth=4.0, colorRGB=darkColorRGB)
        lowerHingeCtrl.prepareChannelBoxForAnimation()
        lowerHingeCtrl.userProperties['space'] = lowerHingeSpace.uuid()
        self.publishNode(lowerHingeCtrl, alias=lowerHingeName)

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
        limbPVCurveFromPoint.connectPlugs(limbPVCtrl[f'worldMatrix[{limbPVCtrl.instanceNumber()}]'], 'inputMatrix[0]')
        limbPVCurveFromPoint.connectPlugs(upperHingeCtrl[f'worldMatrix[{upperHingeCtrl.instanceNumber()}]'], 'inputMatrix[1]')
        limbPVCurveFromPoint.connectPlugs(limbPVShape[f'parentInverseMatrix[{limbPVShape.instanceNumber()}]'], 'parentInverseMatrix')
        limbPVCurveFromPoint.connectPlugs('outputCurve', limbPVShape['create'])

        # Create target joints
        #
        upperJointName = self.formatName(name=upperLimbName, type='joint')
        upperJoint = self.scene.createNode('joint', name=upperJointName, parent=jointsGroup)
        upperJoint.addConstraint('pointConstraint', [upperBlendJoint])
        upperJoint.addConstraint('aimConstraint', [upperHingeCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=upperBlendJoint)
        upperJoint.connectPlugs(upperBlendJoint['scale'], 'scale')

        midJointName = self.formatName(name=midLimbName, type='joint')
        midJoint = self.scene.createNode('joint', name=midJointName, parent=upperJoint)
        midJoint.addConstraint('pointConstraint', [upperHingeCtrl], skipTranslateY=True, skipTranslateZ=True)
        midJoint.addConstraint('aimConstraint', [lowerHingeCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=midBlendJoint)
        midJoint.connectPlugs(midBlendJoint['scale'], 'scale')

        lowerJointName = self.formatName(name=lowerLimbName, type='joint')
        lowerJoint = self.scene.createNode('joint', name=lowerJointName, parent=midJoint)
        lowerJoint.addConstraint('pointConstraint', [lowerHingeCtrl], skipTranslateY=True, skipTranslateZ=True)
        lowerJoint.addConstraint('aimConstraint', [tipBlendJoint], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=lowerBlendJoint)
        lowerJoint.connectPlugs(lowerBlendJoint['scale'], 'scale')

        tipJointName = self.formatName(name=limbTipName, type='joint')
        tipJoint = self.scene.createNode('joint', name=tipJointName, parent=lowerJoint)
        tipJoint.addConstraint('pointConstraint', [tipBlendJoint], skipTranslateY=True, skipTranslateZ=True)
        tipJoint.connectPlugs(tipBlendJoint['scale'], 'scale')

        # Cache kinematic components for later use
        #
        self.userProperties['switchControl'] = switchCtrl.uuid()

        self.userProperties['fkJoints'] = (upperFKJoint.uuid(), midFKJoint.uuid(), lowerFKJoint.uuid(), tipFKJoint.uuid())
        self.userProperties['fkControls'] = (upperFKCtrl.uuid(), midFKCtrl.uuid(), lowerFKCtrl.uuid(), tipFKTarget.uuid())

        self.userProperties['ikJoints'] = (upperIKJoint.uuid(), midIKJoint.uuid(), lowerIKJoint.uuid(), tipIKJoint.uuid())
        self.userProperties['ikControls'] = (limbCtrl.uuid(), limbIKCtrl.uuid())
        self.userProperties['ikHandle'] = limbSpringHandle.uuid()
        self.userProperties['ikEffectors'] = limbSpringEffector.uuid()
        self.userProperties['ikSoftener'] = limbIKSoftener.uuid()
        self.userProperties['ikTarget'] = ikHandleTarget.uuid()
        self.userProperties['pvControl'] = limbPVCtrl.uuid()
        self.userProperties['hingeControls'] = (upperHingeCtrl.uuid(), lowerHingeCtrl.uuid())

        self.userProperties['blendJoints'] = (upperBlendJoint.uuid(), midBlendJoint.uuid(), lowerBlendJoint.uuid(), tipBlendJoint.uuid())
        self.userProperties['targetJoints'] = (upperJoint.uuid(), midJoint.uuid(), lowerJoint.uuid(), tipJoint.uuid())

        # Check if twist is enabled
        #
        if self.twistEnabled:

            # Add extra hinge attributes
            #
            upperHingeCtrl.addDivider('Settings')
            upperHingeCtrl.addAttr(longName='handleOffset', attributeType='distance', min=0.0, keyable=True)
            upperHingeCtrl.addAttr(longName='handleInset', attributeType='distance', min=0.0, keyable=True)

            lowerHingeCtrl.addDivider('Settings')
            lowerHingeCtrl.addAttr(longName='handleOffset', attributeType='distance', min=0.0, keyable=True)
            lowerHingeCtrl.addAttr(longName='handleInset', attributeType='distance', min=0.0, keyable=True)

            # Create upper-limb twist control
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

            upperLimbCtrl.userProperties['space'] = upperLimbCtrl.uuid()

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
            upperLimbOutSpaceSwitch.connectPlugs(upperHingeCtrl['handleInset'], 'target[0].targetOffsetTranslateX')
            upperLimbOutSpaceSwitch.connectPlugs(upperHingeCtrl['handleInset'], 'target[1].targetOffsetTranslateX')

            upperLimbOutCtrl.userProperties['space'] = upperLimbOutSpace.uuid()
            upperLimbOutCtrl.userProperties['spaceSwitch'] = upperLimbOutSpaceSwitch.uuid()

            # Create upper-limb out-handle proxy curve
            #
            upperLimbCurveShape = self.scene.createNode('nurbsCurve', parent=upperLimbCtrl)
            upperLimbCurveShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            upperLimbCurveShape.template = True

            upperLimbCurveFromPoint = self.scene.createNode('curveFromPoint')
            upperLimbCurveFromPoint.degree = 1
            upperLimbCurveFromPoint.connectPlugs(upperLimbCtrl[f'worldMatrix[{upperLimbCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            upperLimbCurveFromPoint.connectPlugs(upperLimbOutCtrl[f'worldMatrix[{upperLimbOutCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            upperLimbCurveFromPoint.connectPlugs(upperLimbCurveShape[f'parentInverseMatrix[{upperLimbCurveShape.instanceNumber()}]'], 'parentInverseMatrix')
            upperLimbCurveFromPoint.connectPlugs('outputCurve', upperLimbCurveShape['create'])

            upperLimbCtrl.userProperties['curveFromPoint'] = upperLimbCurveFromPoint.uuid()

            # Add shaper controls to upper-hinge control
            #
            upperHingeInCtrlName = self.formatName(name=upperHingeName, subname='In', type='control')
            upperHingeInCtrl = self.scene.createNode('transform', name=upperHingeInCtrlName, parent=upperHingeCtrl)
            upperHingeInCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((-5.0 * rigScale), 0.0, 0.0), colorRGB=darkColorRGB)
            upperHingeInCtrl.hideAttr('rotate')
            upperHingeInCtrl.prepareChannelBoxForAnimation()
            self.publishNode(upperHingeInCtrl, alias=f'{upperHingeName}_In')

            upperHingeInNegateName = self.formatName(name=upperHingeName, subname='In', type='floatMath')
            upperHingeInNegate = self.scene.createNode('floatMath', name=upperHingeInNegateName)
            upperHingeInNegate.setAttr('operation', 5)  # Negate
            upperHingeInNegate.connectPlugs(upperHingeCtrl['handleOffset'], 'inDistanceA')

            upperHingeInMatrixName = self.formatName(name=upperHingeName, subname='In', type='composeMatrix')
            upperHingeInMatrix = self.scene.createNode('composeMatrix', name=upperHingeInMatrixName)
            upperHingeInMatrix.connectPlugs(upperHingeInNegate['outDistance'], 'inputTranslateX')
            upperHingeInMatrix.connectPlugs('outputMatrix', upperHingeInCtrl['offsetParentMatrix'])

            upperHingeOutCtrlName = self.formatName(name=upperHingeName, subname='Out', type='control')
            upperHingeOutCtrl = self.scene.createNode('transform', name=upperHingeOutCtrlName, parent=upperHingeCtrl)
            upperHingeOutCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((5.0 * rigScale), 0.0, 0.0), localRotate=(0.0, 0.0, 180.0), colorRGB=darkColorRGB)
            upperHingeOutCtrl.hideAttr('rotate')
            upperHingeOutCtrl.prepareChannelBoxForAnimation()
            self.publishNode(upperHingeOutCtrl, alias=f'{upperHingeName}_Out')

            upperHingeOutMatrixName = self.formatName(name=upperHingeName, subname='Out', type='composeMatrix')
            upperHingeOutMatrix = self.scene.createNode('composeMatrix', name=upperHingeOutMatrixName)
            upperHingeOutMatrix.connectPlugs(upperHingeCtrl['handleOffset'], 'inputTranslateX')
            upperHingeOutMatrix.connectPlugs('outputMatrix', upperHingeOutCtrl['offsetParentMatrix'])

            upperHingeCurveShape = self.scene.createNode('nurbsCurve', parent=upperHingeCtrl)
            upperHingeCurveShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            upperHingeCurveShape.template = True

            upperHingeCurveFromPointName = self.formatName(name=upperHingeName, type='curveFromPoint')
            upperHingeCurveFromPoint = self.scene.createNode('curveFromPoint', name=upperHingeCurveFromPointName)
            upperHingeCurveFromPoint.degree = 1
            upperHingeCurveFromPoint.connectPlugs(upperHingeInCtrl[f'worldMatrix[{upperHingeInCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            upperHingeCurveFromPoint.connectPlugs(upperHingeCtrl[f'worldMatrix[{upperHingeCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            upperHingeCurveFromPoint.connectPlugs(upperHingeOutCtrl[f'worldMatrix[{upperHingeOutCtrl.instanceNumber()}]'], 'inputMatrix[2]')
            upperHingeCurveFromPoint.connectPlugs(upperHingeCurveShape[f'parentInverseMatrix[{upperHingeCurveShape.instanceNumber()}]'], 'parentInverseMatrix')
            upperHingeCurveFromPoint.connectPlugs('outputCurve', upperHingeCurveShape['create'])

            upperHingeCtrl.userProperties['inHandle'] = upperHingeInCtrl.uuid()
            upperHingeCtrl.userProperties['outHandle'] = upperHingeOutCtrl.uuid()
            upperHingeCtrl.userProperties['curveFromPoint'] = upperHingeCurveFromPoint.uuid()

            # Add shaper controls to lower-hinge control
            #
            lowerHingeInCtrlName = self.formatName(name=lowerHingeName, subname='In', type='control')
            lowerHingeInCtrl = self.scene.createNode('transform', name=lowerHingeInCtrlName, parent=lowerHingeCtrl)
            lowerHingeInCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((-5.0 * rigScale), 0.0, 0.0), colorRGB=darkColorRGB)
            lowerHingeInCtrl.hideAttr('rotate')
            lowerHingeInCtrl.prepareChannelBoxForAnimation()
            self.publishNode(lowerHingeInCtrl, alias=f'{lowerHingeName}_In')

            lowerHingeInNegateName = self.formatName(name=lowerHingeName, subname='In', type='floatMath')
            lowerHingeInNegate = self.scene.createNode('floatMath', name=lowerHingeInNegateName)
            lowerHingeInNegate.setAttr('operation', 5)  # Negate
            lowerHingeInNegate.connectPlugs(lowerHingeCtrl['handleOffset'], 'inDistanceA')

            lowerHingeInMatrixName = self.formatName(name=lowerHingeName, subname='In', type='composeMatrix')
            lowerHingeInMatrix = self.scene.createNode('composeMatrix', name=lowerHingeInMatrixName)
            lowerHingeInMatrix.connectPlugs(lowerHingeInNegate['outDistance'], 'inputTranslateX')
            lowerHingeInMatrix.connectPlugs('outputMatrix', lowerHingeInCtrl['offsetParentMatrix'])

            lowerHingeOutCtrlName = self.formatName(name=lowerHingeName, subname='Out', type='control')
            lowerHingeOutCtrl = self.scene.createNode('transform', name=lowerHingeOutCtrlName, parent=lowerHingeCtrl)
            lowerHingeOutCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=((5.0 * rigScale), 0.0, 0.0), localRotate=(0.0, 0.0, 180.0), colorRGB=darkColorRGB)
            lowerHingeOutCtrl.hideAttr('rotate')
            lowerHingeOutCtrl.prepareChannelBoxForAnimation()
            self.publishNode(lowerHingeOutCtrl, alias=f'{lowerHingeName}_Out')

            lowerHingeOutMatrixName = self.formatName(name=lowerHingeName, subname='Out', type='composeMatrix')
            lowerHingeOutMatrix = self.scene.createNode('composeMatrix', name=lowerHingeOutMatrixName)
            lowerHingeOutMatrix.connectPlugs(lowerHingeCtrl['handleOffset'], 'inputTranslateX')
            lowerHingeOutMatrix.connectPlugs('outputMatrix', lowerHingeOutCtrl['offsetParentMatrix'])

            lowerHingeCurveShape = self.scene.createNode('nurbsCurve', parent=lowerHingeCtrl)
            lowerHingeCurveShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            lowerHingeCurveShape.template = True

            lowerHingeCurveFromPointName = self.formatName(name=lowerHingeName, type='curveFromPoint')
            lowerHingeCurveFromPoint = self.scene.createNode('curveFromPoint', name=lowerHingeCurveFromPointName)
            lowerHingeCurveFromPoint.degree = 1
            lowerHingeCurveFromPoint.connectPlugs(lowerHingeInCtrl[f'worldMatrix[{lowerHingeInCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            lowerHingeCurveFromPoint.connectPlugs(lowerHingeCtrl[f'worldMatrix[{lowerHingeCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            lowerHingeCurveFromPoint.connectPlugs(lowerHingeOutCtrl[f'worldMatrix[{lowerHingeOutCtrl.instanceNumber()}]'], 'inputMatrix[2]')
            lowerHingeCurveFromPoint.connectPlugs(lowerHingeCurveShape[f'parentInverseMatrix[{lowerHingeCurveShape.instanceNumber()}]'], 'parentInverseMatrix')
            lowerHingeCurveFromPoint.connectPlugs('outputCurve', lowerHingeCurveShape['create'])

            lowerHingeCtrl.userProperties['inHandle'] = lowerHingeInCtrl.uuid()
            lowerHingeCtrl.userProperties['outHandle'] = lowerHingeOutCtrl.uuid()
            lowerHingeCtrl.userProperties['curveFromPoint'] = upperHingeCurveFromPoint.uuid()

            # Create lower-limb in-handle control
            #
            lowerLimbInSpaceName = self.formatName(name=limbTipName, subname='In', type='space')
            lowerLimbInSpace = self.scene.createNode('transform', name=lowerLimbInSpaceName, parent=controlsGroup)
            lowerLimbInSpace.copyTransform(tipJoint)
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
            lowerLimbInNegate.connectPlugs(lowerHingeCtrl['handleInset'], 'inDistanceA')

            lowerLimbInSpaceSwitch = lowerLimbInSpace.addSpaceSwitch([tipJoint], maintainOffset=False)
            lowerLimbInSpaceSwitch.weighted = True
            lowerLimbInSpaceSwitch.setAttr('target[0]', {'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (True, True, True)})
            lowerLimbInSpaceSwitch.connectPlugs(lowerLimbInCtrl['localOrGlobal'], 'target[0].targetWeight')
            lowerLimbInSpaceSwitch.connectPlugs(lowerLimbInNegate['outDistance'], 'target[0].targetOffsetTranslateX')

            lowerLimbInCtrl.userProperties['negate'] = lowerLimbInNegate.uuid()
            lowerLimbInCtrl.userProperties['space'] = lowerLimbInSpace.uuid()
            lowerLimbInCtrl.userProperties['spaceSwitch'] = lowerLimbInSpaceSwitch.uuid()

            # hingeCtrl.userProperties['otherHandles'] = (upperLimbOutCtrl.uuid(), lowerLimbInCtrl.uuid())

            # Create twist curves
            #
            limbCurveName = self.formatName(subname='Twist', type='nurbsCurve')
            limbCurve = self.scene.createNode('transform', name=limbCurveName, parent=controlsGroup)
            limbCurve.inheritsTransform = False
            limbCurve.lockAttr('translate', 'rotate', 'scale')

            defaultCurveData = shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1)

            upperLimbCurveShape = self.scene.createNode('nurbsCurve', parent=limbCurve)
            upperLimbCurveShape.setAttr('cached', defaultCurveData)
            upperLimbCurveShape.template = True

            upperLimbCurveFromPoint = self.scene.createNode('curveFromPoint')
            upperLimbCurveFromPoint.degree = 3
            upperLimbCurveFromPoint.connectPlugs(upperLimbCtrl[f'worldMatrix[{upperLimbCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            upperLimbCurveFromPoint.connectPlugs(upperLimbOutCtrl[f'worldMatrix[{upperLimbOutCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            upperLimbCurveFromPoint.connectPlugs(upperHingeInCtrl[f'worldMatrix[{upperHingeInCtrl.instanceNumber()}]'], 'inputMatrix[2]')
            upperLimbCurveFromPoint.connectPlugs(upperHingeCtrl[f'worldMatrix[{upperHingeCtrl.instanceNumber()}]'], 'inputMatrix[3]')
            upperLimbCurveFromPoint.connectPlugs(upperLimbCurveShape[f'parentInverseMatrix[{upperLimbCurveShape.instanceNumber()}]'], 'parentInverseMatrix')
            upperLimbCurveFromPoint.connectPlugs('outputCurve', upperLimbCurveShape['create'])

            midLimbCurveShape = self.scene.createNode('nurbsCurve', parent=limbCurve)
            midLimbCurveShape.setAttr('cached', defaultCurveData)
            midLimbCurveShape.template = True

            midLimbCurveFromPoint = self.scene.createNode('curveFromPoint')
            midLimbCurveFromPoint.degree = 3
            midLimbCurveFromPoint.connectPlugs(upperHingeCtrl[f'worldMatrix[{upperHingeCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            midLimbCurveFromPoint.connectPlugs(upperHingeOutCtrl[f'worldMatrix[{upperHingeOutCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            midLimbCurveFromPoint.connectPlugs(lowerHingeInCtrl[f'worldMatrix[{lowerHingeInCtrl.instanceNumber()}]'], 'inputMatrix[2]')
            midLimbCurveFromPoint.connectPlugs(lowerHingeCtrl[f'worldMatrix[{lowerHingeCtrl.instanceNumber()}]'], 'inputMatrix[3]')
            midLimbCurveFromPoint.connectPlugs(midLimbCurveShape[f'parentInverseMatrix[{midLimbCurveShape.instanceNumber()}]'], 'parentInverseMatrix')
            midLimbCurveFromPoint.connectPlugs('outputCurve', midLimbCurveShape['create'])

            lowerLimbCurveShape = self.scene.createNode('nurbsCurve', parent=limbCurve)
            lowerLimbCurveShape.setAttr('cached', defaultCurveData)
            lowerLimbCurveShape.template = True

            lowerLimbCurveFromPoint = self.scene.createNode('curveFromPoint')
            lowerLimbCurveFromPoint.degree = 3
            lowerLimbCurveFromPoint.connectPlugs(lowerHingeCtrl[f'worldMatrix[{lowerHingeCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            lowerLimbCurveFromPoint.connectPlugs(lowerHingeOutCtrl[f'worldMatrix[{lowerHingeOutCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            lowerLimbCurveFromPoint.connectPlugs(lowerLimbInCtrl[f'worldMatrix[{lowerLimbInCtrl.instanceNumber()}]'], 'inputMatrix[2]')
            lowerLimbCurveFromPoint.connectPlugs(tipJoint[f'worldMatrix[{tipJoint.instanceNumber()}]'], 'inputMatrix[3]')
            lowerLimbCurveFromPoint.connectPlugs(lowerLimbCurveShape[f'parentInverseMatrix[{lowerLimbCurveShape.instanceNumber()}]'], 'parentInverseMatrix')
            lowerLimbCurveFromPoint.connectPlugs('outputCurve', lowerLimbCurveShape['create'])

            limbCurve.renameShapes()

            # Create twist controls
            #
            segmentSpecs = (upperLimbSpec, midLimbSpec, lowerLimbSpec)
            segmentNames = (upperLimbName, midLimbName, lowerLimbName)
            segmentCurves = (upperLimbCurveShape, midLimbCurveShape, lowerLimbCurveShape)
            segmentCtrls = ((upperLimbOutCtrl, upperHingeInCtrl), (upperHingeOutCtrl, lowerHingeInCtrl), (lowerHingeInCtrl, lowerLimbInCtrl))
            segmentScalers = ((upperLimbCtrl, upperHingeCtrl), (upperHingeCtrl, lowerHingeCtrl), (lowerHingeCtrl, limbIKCtrl))

            twistSolvers = [None] * 3
            scaleRemappers = [None] * 3

            for (i, (segmentName, segmentSpec, segmentCurve, (startCtrl, endCtrl), (startScaler, endScaler))) in enumerate(zip(segmentNames, segmentSpecs, segmentCurves, segmentCtrls, segmentScalers)):

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

                # Create scale remapper
                #
                scaleRemapperName = self.formatName(name=limbName, subname='Scale', type='remapArray')
                scaleRemapper = self.scene.createNode('remapArray', name=scaleRemapperName)
                scaleRemapper.setAttr('clamp', True)
                scaleRemapper.connectPlugs(startScaler['scale'], 'outputMin')
                scaleRemapper.connectPlugs(endScaler['scale'], 'outputMax')

                scaleRemappers[i] = scaleRemapper.uuid()

                # Create twist controls
                #
                numTwistSpecs = len(segmentSpec.children)

                for (j, twistSpec) in enumerate(segmentSpec.children):

                    # Create twist control
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

                    pathConstraint = twistSpace.addConstraint('pointOnCurveConstraint', [segmentCurve])
                    pathConstraint.parameter = parameter
                    pathConstraint.useFraction = True
                    pathConstraint.forwardVector = (1.0, 0.0, 0.0)
                    pathConstraint.upVector = (0.0, 0.0, 1.0)
                    pathConstraint.worldUpType = 2  # Object Rotation
                    pathConstraint.worldUpVector = (0.0, 0.0, 1.0)
                    pathConstraint.connectPlugs(startCtrl[f'worldMatrix[{startCtrl.instanceNumber()}]'], 'worldUpMatrix')
                    pathConstraint.connectPlugs(twistSolver[f'twist[{j}]'], 'twist')

                    # Add scale constraint and connect scale remapper
                    #
                    scaleConstraint = twistSpace.addConstraint('scaleConstraint', [limbCtrl])

                    scaleRemapper.setAttr(f'parameter[{j}]', parameter)
                    scaleRemapper.connectPlugs(f'outValue[{j}]', scaleConstraint['offset'])

                    # Finally, re-align export joint to control
                    # This will ensure there are no unwanted offsets when binding the skeleton!
                    #
                    twistExportJoint = twistSpec.getNode()
                    twistExportJoint.copyTransform(twistCtrl, skipScale=True)

                    twistSpec.matrix = twistExportJoint.matrix(asTransformationMatrix=True)
                    twistSpec.worldMatrix = twistExportJoint.worldMatrix()

            # Cache twist components
            #
            self.userProperties['twistSolvers'] = twistSolvers
            self.userProperties['scaleRemappers'] = scaleRemappers

        else:

            log.debug('Skipping twist setup...')
    # endregion
