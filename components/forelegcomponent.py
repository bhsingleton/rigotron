from maya import cmds as mc
from maya.api import OpenMaya as om
from enum import IntEnum
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

    SCAPULA = 0
    HUMERUS = 1
    RADIUS = 2
    CANNON = 3
    TIP = 4


class ForeLegComponent(limbcomponent.LimbComponent):
    """
    Overload of `LimbComponent` that implements fore-leg components.
    """

    # region Dunderscores
    __default_component_name__ = 'ForeLeg'
    __default_limb_names__ = ('Scapula', 'Humerus', 'Radius', 'Cannon', 'CannonTip')
    __default_hinge_names__ = ('Elbow', 'Wrist')
    __default_limb_types__ = (Type.COLLAR, Type.NONE, Type.SHOULDER, Type.ELBOW, Type.HAND)
    __default_limb_matrices__ = {
        Side.LEFT: {},
        Side.RIGHT: {}
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
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        numMembers = len(self.LimbType)
        scapulaSpec, humerusSpec, radiusSpec, cannonSpec, tipSpec = self.resizeSkeletonSpecs(numMembers, skeletonSpecs)

        # Iterate through limb specs
        #
        limbNames = self.__default_limb_names__[self.LimbType.RADIUS], self.__default_limb_names__[self.LimbType.CANNON]
        limbSpecs = (radiusSpec, cannonSpec)

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

        # Edit remaining specs
        #
        scapulaName = self.__default_limb_names__[self.LimbType.SCAPULA]
        scapulaSpec.name = self.formatName(name=scapulaName)
        scapulaSpec.driver = self.formatName(name=scapulaName, type='joint')

        humerusName = self.__default_limb_names__[self.LimbType.HUMERUS]
        humerusSpec.name = self.formatName(name=humerusName)
        humerusSpec.driver = self.formatName(name=humerusName, type='joint')

        tipName = self.__default_limb_names__[self.LimbType.TIP]
        tipSpec.name = self.formatName(name=tipName)
        tipSpec.driver = self.formatName(name=tipName, type='joint')
        tipSpec.enabled = not self.hasExtremityComponent()

        # Call parent method
        #
        super(ForeLegComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        componentSide = self.Side(self.componentSide)

        scapulaSpec, humerusSpec, radiusSpec, cannonSpec, tipSpec = self.skeletonSpecs()
        scapulaType, humerusType, radiusType, cannonType, tipType = self.__default_limb_types__

        # Create scapula joint
        #
        scapulaJoint = self.scene.createNode('joint', name=scapulaSpec.name)
        scapulaJoint.side = componentSide
        scapulaJoint.type = scapulaType
        scapulaJoint.drawStyle = self.Style.BOX
        scapulaJoint.displayLocalAxis = True
        scapulaSpec.uuid = scapulaJoint.uuid()

        defaultScapuleMatrix = self.__default_limb_matrices__[componentSide][self.LimbType.SCAPULA]
        scapulaMatrix = scapulaSpec.getMatrix(default=defaultScapuleMatrix)
        scapulaJoint.setWorldMatrix(scapulaMatrix, skipScale=True)

        # Create humerus joint
        #
        humerusJoint = self.scene.createNode('joint', name=humerusSpec.name, parent=scapulaJoint)
        humerusJoint.side = componentSide
        humerusJoint.type = midLimbType
        humerusJoint.drawStyle = self.Style.BOX
        humerusJoint.displayLocalAxis = True
        humerusSpec.uuid = humerusJoint.uuid()

        defaultHumerusMatrix = self.__default_limb_matrices__[componentSide][LimbType.HUMERUS]
        humerusMatrix = humerusSpec.getMatrix(default=defaultHumerusMatrix)
        humerusJoint.setWorldMatrix(humerusMatrix, skipScale=True)

        # Create radius joint
        #
        radiusJoint = self.scene.createNode('joint', name=radiusSpec.name, parent=scapulaJoint)
        radiusJoint.side = componentSide
        radiusJoint.type = midLimbType
        radiusJoint.drawStyle = self.Style.BOX
        radiusJoint.displayLocalAxis = True
        radiusSpec.uuid = radiusJoint.uuid()

        defaultRadiusMatrix = self.__default_limb_matrices__[componentSide][LimbType.RADIUS]
        radiusMatrix = radiusSpec.getMatrix(default=defaultRadiusMatrix)
        radiusJoint.setWorldMatrix(radiusMatrix, skipScale=True)

        # Create radius twist joints
        #
        radiusTwistCount = len(radiusSpec.children)
        radiusTwistJoints = [None] * radiusTwistCount

        for (i, twistSpec) in enumerate(radiusSpec.children):

            twistJoint = self.scene.createNode('joint', name=twistSpec.name, parent=radiusJoint)
            twistJoint.side = componentSide
            twistJoint.type = self.Type.NONE
            twistJoint.drawStyle = self.Style.JOINT
            twistJoint.displayLocalAxis = True
            twistSpec.uuid = twistJoint.uuid()

            radiusTwistJoints[i] = twistJoint

        # Create cannon joint
        #
        cannonJoint = self.scene.createNode('joint', name=cannonSpec.name, parent=radiusJoint)
        cannonJoint.side = componentSide
        cannonJoint.type = lowerLimbType
        cannonJoint.drawStyle = self.Style.BOX
        cannonJoint.displayLocalAxis = True
        cannonSpec.uuid = cannonJoint.uuid()

        defaultCannonLimbMatrix = self.__default_limb_matrices__[componentSide][LimbType.CANNON]
        cannonMatrix = lowerLimbSpec.getMatrix(default=defaultCannonLimbMatrix)
        cannonJoint.setWorldMatrix(cannonMatrix, skipScale=True)

        # Create cannon twist joints
        #
        cannonTwistSpecs = cannonSpec.children

        cannonTwistCount = len(cannonTwistSpecs)
        cannonTwistJoints = [None] * cannonTwistCount

        for (i, twistSpec) in enumerate(lowerTwistSpecs):

            twistJoint = self.scene.createNode('joint', name=twistSpec.name, parent=cannonJoint)
            twistJoint.side = componentSide
            twistJoint.type = self.Type.NONE
            twistJoint.drawStyle = self.Style.JOINT
            twistJoint.displayLocalAxis = True
            twistSpec.uuid = twistJoint.uuid()

            cannonTwistJoints[i] = twistJoint

        # Create tip joint
        #
        tipJoint = None

        if limbTipSpec.enabled:

            tipJoint = self.scene.createNode('joint', name=tipSpec.name, parent=cannonJoint)
            tipJoint.side = componentSide
            tipJoint.type = limbTipType
            tipJoint.displayLocalAxis = True
            tipSpec.uuid = tipJoint.uuid()

            defaultLimbTipMatrix = self.__default_limb_matrices__[componentSide][self.LimbType.TIP]
            tipMatrix = tipSpec.getMatrix(default=defaultLimbTipMatrix)
            tipJoint.setWorldMatrix(tipMatrix, skipScale=True)

        return (scapulaJoint, humerusJoint, radiusJoint, cannonJoint, tipJoint)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        limbName = self.componentName
        scapulaName, humerusName, radiusName, cannonName, tipName = self.__default_limb_names__

        scapulaSpec, humerusSpec, radiusSpec, cannonSpec, tipSpec = self.skeletonSpecs()
        scapulaExportJoint = self.scene(scapulaSpec.uuid)
        humerusExportJoint = self.scene(humerusSpec.uuid)
        radiusExportJoint = self.scene(radiusSpec.uuid)
        cannonExportJoint = self.scene(cannonSpec.uuid)
        tipExportJoint = self.scene(tipSpec.uuid)

        scapulaMatrix = scapulaExportJoint.worldMatrix()
        humerusMatrix = humerusExportJoint.worldMatrix()
        radiusMatrix = radiusExportJoint.worldMatrix()
        cannonMatrix = cannonExportJoint.worldMatrix()
        extremityMatrix = self.extremityMatrix()
        effectorMatrix = self.effectorMatrix()

        defaultTipMatrix = transformutils.createRotationMatrix(cannonMatrix) * transformutils.createTranslateMatrix(extremityMatrix)
        tipMatrix = tipExportJoint.worldMatrix() if (tipExportJoint is not None) else defaultTipMatrix

        componentSide = self.Side(self.componentSide)
        requiresMirroring = componentSide == self.Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        limbOrigin = transformutils.breakMatrix(scapulaMatrix)[3]
        altLimbOrigin = transformutils.breakMatrix(radiusMatrix)[3]
        hingePoint = transformutils.breakMatrix(cannonMatrix)[3]
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
        worldForwardVector = transformutils.findClosestWorldAxis(forwardVector)
        rightVector = transformutils.breakMatrix(upperLimbMatrix, normalize=True)[2]
        worldRightVector = transformutils.findClosestWorldAxis(rightVector)
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
        kinematicTypes = ('FK', 'IK', 'Blend')
        jointTypes = (scapulaName, humerusName, radiusName, cannonName, tipName)
        jointMatrices = (scapulaMatrix, humerusMatrix, radiusMatrix, cannonMatrix, tipMatrix)

        limbFKJoints = [None] * 5
        limbIKJoints = [None] * 5
        limbBlendJoints = [None] * 5
        kinematicJoints = (limbFKJoints, limbIKJoints, limbBlendJoints)

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = kinematicJoints[i][j - 1] if j > 0 else jointsGroup

                jointName = self.formatName(name=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.displayLocalAxis = True
                joint.setWorldMatrix(jointMatrices[j])

                kinematicJoints[i][j] = joint

        scapulaFKJoint, humerusFKJoint, radiusFKJoint, cannonFKJoint, tipFKJoint = limbFKJoints
        scapulaIKJoint, humerusIKJoint, radiusIKJoint, cannonFKJoint, tipIKJoint = limbIKJoints
        scapulaBlendJoint, humerusBlendJoint, radiusBlendJoint, cannonBlendJoint, tipBlendJoint = limbBlendJoints

        # Create switch control
        #
        upperOffsetAttr = f'{radiusName}Offset'
        lowerOffsetAttr = f'{cannonName}Offset'

        upperDistance = om.MPoint(altLimbOrigin).distanceTo(hingePoint)
        lowerDistance = om.MPoint(hingePoint).distanceTo(limbGoal)
        limbLengths = (upperDistance, lowerDistance)

        switchCtrlName = self.formatName(subname='Switch', type='control')
        switchCtrl = self.scene.createNode('transform', name=switchCtrlName, parent=controlsGroup)
        switchCtrl.addPointHelper('pyramid', 'fill', 'shaded', size=(10.0 * rigScale), localPosition=(0.0, 25.0, 0.0), localRotate=(0.0, 0.0, -90.0 * limbSign), colorRGB=darkColorRGB)
        switchCtrl.addConstraint('transformConstraint', [tipBlendJoint])
        switchCtrl.addDivider('Settings')
        switchCtrl.addAttr(longName='length', attributeType='doubleLinear', array=True, hidden=True)
        switchCtrl.addAttr(longName='mode', niceName='Mode (FK/IK)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName=upperOffsetAttr, attributeType='doubleLinear', keyable=True)
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
        limbSpaceName = self.formatName(name=upperLimbName, type='space')
        limbSpace = self.scene.createNode('transform', name=limbSpaceName, parent=controlsGroup)
        limbSpace.setWorldMatrix(limbMatrix, skipScale=True)
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
        scapulaBlender = setuputils.createTransformBlends(scapulaFKJoint, scapulaIKJoint, scapulaBlendJoint, blender=blender)
        humerusBlender = setuputils.createTransformBlends(humerusFKJoint, humerusIKJoint, humerusBlendJoint, blender=blender)
        radiusBlender = setuputils.createTransformBlends(radiusFKJoint, radiusIKJoint, radiusBlendJoint, blender=blender)
        cannonBlender = setuputils.createTransformBlends(cannonFKJoint, cannonIKJoint, cannonBlendJoint, blender=blender)
        tipBlender = setuputils.createTransformBlends(tipFKJoint, tipIKJoint, tipBlendJoint, blender=blender)

        scapulaBlender.setName(self.formatName(subname=scapulaName, type='blendTransform'))
        humerusBlender.setName(self.formatName(subname=humerusName, type='blendTransform'))
        radiusBlender.setName(self.formatName(subname=radiusName, type='blendTransform'))
        cannonBlender.setName(self.formatName(subname=cannonName, type='blendTransform'))
        tipBlender.setName(self.formatName(subname=tipName, type='blendTransform'))

        # Setup limb length nodes
        #
        radiusLengthName = self.formatName(name=radiusLimbName, subname='Length', type='plusMinusAverage')
        radiusLength = self.scene.createNode('plusMinusAverage', name=radiusLengthName)
        radiusLength.setAttr('operation', 1)  # Addition
        radiusLength.connectPlugs(switchCtrl['length[0]'], 'input1D[0]')
        radiusLength.connectPlugs(switchCtrl[radiusOffsetAttr], 'input1D[1]')

        cannonLengthName = self.formatName(name=cannonLimbName, subname='Length', type='plusMinusAverage')
        cannonLength = self.scene.createNode('plusMinusAverage', name=cannonLengthName)
        cannonLength.setAttr('operation', 1)  # Addition
        cannonLength.connectPlugs(switchCtrl['length[1]'], 'input1D[0]')
        cannonLength.connectPlugs(switchCtrl[cannonOffsetAttr], 'input1D[1]')

        limbLength = self.formatName(subname='Length', type='plusMinusAverage')
        limbLength = self.scene.createNode('plusMinusAverage', name=limbLength)
        limbLength.setAttr('operation', 1)  # Addition
        limbLength.connectPlugs(radiusLength['output1D'], 'input1D[0]')
        limbLength.connectPlugs(cannonLength['output1D'], 'input1D[1]')

        radiusWeightName = self.formatName(name=radiusLimbName, subname='Weight', type='floatMath')
        radiusWeight = self.scene.createNode('floatMath', name=radiusWeightName)
        radiusWeight.operation = 3  # Divide
        radiusWeight.connectPlugs(radiusLength['output1D'], 'inFloatA')
        radiusWeight.connectPlugs(limbLength['output1D'], 'inFloatB')

        cannonWeightName = self.formatName(name=cannonLimbName, subname='Weight', type='floatMath')
        cannonWeight = self.scene.createNode('floatMath', name=cannonWeightName)
        cannonWeight.operation = 3  # Divide
        cannonWeight.connectPlugs(cannonLength['output1D'], 'inFloatA')
        cannonWeight.connectPlugs(limbLength['output1D'], 'inFloatB')

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

    # endregion