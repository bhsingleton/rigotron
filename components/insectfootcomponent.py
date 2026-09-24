from maya.api import OpenMaya as om
from mpy import mpyattribute
from dcc.maya.libs import transformutils, shapeutils
from dcc.dataclasses.colour import Colour
from rigomatic.libs import kinematicutils
from enum import IntEnum
from . import extremitycomponent
from ..libs import Side, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class InsectFootType(IntEnum):
    """
    Enum class of all available insect foot components.
    """

    TARSUS = 0
    CLAW = 1
    TIP = 2


class InsectFootComponent(extremitycomponent.ExtremityComponent):
    """
    Overload of `ExtremityComponent` that outlines insect extremity components.
    """

    # region Dunderscores
    __default_component_name__ = 'Foot'
    __default_component_matrices__ = {
        Side.LEFT: {
            InsectFootType.TARSUS: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (50.0, 0.0, 20.0, 1.0)
                ]
            ),
            InsectFootType.CLAW: om.MMatrix(
                [
                    (0.0, 1.0, 0.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            InsectFootType.TARSUS: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (-50.0, 0.0, 20.0, 1.0)
                ]
            ),
            InsectFootType.CLAW: om.MMatrix(
                [
                    (0.0, 1.0, 0.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                ]
            )
        }
    }
    __default_component_spacing__ = 10.0
    # endregion

    # region Enums
    InsectFootType = InsectFootType
    # endregion

    # region Attributes
    numTarsusLinks = mpyattribute.MPyAttribute('numTarsusLinks', attributeType='int', min=1, max=5, default=1)
    clawEnabled = mpyattribute.MPyAttribute('clawEnabled', attributeType='bool', default=False)

    @numTarsusLinks.changed
    def numTarsusLinks(self, numTarsusLinks):
        """
        Changed method that notifies of any state changes.

        :type numTarsusLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()

    @clawEnabled.changed
    def clawEnabled(self, clawEnabled):
        """
        Changed method that notifies of any state changes.

        :type clawEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def preferredEffectorMatrix(self):
        """
        Returns the preferred effector matrix for this component.
        By default, this will return the first skeletal spec matrix!

        :rtype: om.MMatrix
        """

        *tarsusSpecs, clawSpec, tipSpec = self.skeleton(flatten=True, skipPassthrough=False)

        if clawSpec.passthrough:

            return tipSpec.getNode().worldMatrix()

        else:

            return clawSpec.getNode().worldMatrix()

    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        numTarsusLinks = int(self.numTarsusLinks)
        clawEnabled = bool(self.clawEnabled)
        size = numTarsusLinks + 2

        *tarsusSpecs, clawSpec, tipSpec = self.resizeSkeleton(size, skeletonSpecs, hierarchical=True)

        # Edit tarsus specs
        #
        side = self.Side(self.componentSide)

        for (i, tarsusSpec) in enumerate(tarsusSpecs, start=1):

            isFirstTarsus = (i == 1)
            defaultMatrix = om.MMatrix(self.__default_component_matrices__[side][self.InsectFootType.TARSUS]) if isFirstTarsus else transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))

            tarsusSpec.enabled = True
            tarsusSpec.name = self.formatName(name='Tarsus', index=i)
            tarsusSpec.side = side
            tarsusSpec.type = self.Type.OTHER
            tarsusSpec.otherType = 'Tarsus'
            tarsusSpec.drawStyle = self.Style.BOX
            tarsusSpec.defaultMatrix = defaultMatrix
            tarsusSpec.driver.name = self.formatName(name='Tarsus', kinemat='Blend', index=i, type='joint')

        # Edit claw spec
        #
        clawSpec.passthrough = not clawEnabled
        clawSpec.name = self.formatName(name='Claw')
        clawSpec.side = side
        clawSpec.type = self.Type.OTHER
        clawSpec.otherType = 'Claw'
        clawSpec.drawStyle = self.Style.BOX
        clawSpec.defaultMatrix = om.MMatrix(self.__default_component_matrices__[side][self.InsectFootType.CLAW]) * transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))
        clawSpec.driver.name = self.formatName(name='Claw', kinemat='Blend', type='joint')

        # Edit tip spec
        #
        tipName = 'ClawTip' if clawEnabled else 'TarsusTip'

        tipSpec.enabled = True
        tipSpec.name = self.formatName(name=tipName)
        tipSpec.side = side
        tipSpec.type = self.Type.OTHER
        tipSpec.otherType = tipName
        tipSpec.drawStyle = self.Style.BOX
        tipSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))
        tipSpec.driver.name = self.formatName(name=tipName, kinemat='Blend', type='joint')

        # Call parent method
        #
        return super(InsectFootComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Decompose component
        #
        *tarsusSpecs, clawSpec, tipSpec = self.skeleton(flatten=True, skipPassthrough=False)
        tarsusExportJoints = [tarsusSpec.getNode() for tarsusSpec in tarsusSpecs]
        tarsusExportMatrices = [tarsusExportJoint.worldMatrix() for tarsusExportJoint in tarsusExportJoints]

        clawExportJoint = clawSpec.getNode()
        clawExportMatrix = clawExportJoint.worldMatrix() if (clawExportJoint is not None) else om.MMatrix.kIdentity
        clawPoint = transformutils.breakMatrix(clawExportMatrix)[3]

        tipExportJoint = tipSpec.getNode()
        tipExportMatrix = tipExportJoint.worldMatrix()
        tipPoint = transformutils.breakMatrix(tipExportMatrix)[3]

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

        limbComponent = self.getAssociatedLimbComponent()
        hasLimbComponent = limbComponent is not None

        if not hasLimbComponent:

            raise NotImplementedError('buildRig() limbless foot components have not been implemented!')

        # Get required limb nodes
        #
        switchCtrl = self.scene(limbComponent.userProperties['switchControl'])
        limbFKCtrl = self.scene(limbComponent.userProperties['fkControls'][-1])
        limbIKCtrl = self.scene(limbComponent.userProperties['ikControls'][-1])

        hasIKOffset = 'offset' in limbComponent.userProperties.keys()
        limbIKOffsetCtrl = self.scene(limbIKCtrl.userProperties['offset']) if hasIKOffset else limbIKCtrl

        hasReverseIKJoints = 'rikJoints' in limbComponent.userProperties.keys()
        limbTipIKJoint = self.scene(limbComponent.userProperties['ikJoints'][-1])
        limbTipRIKJoint = self.scene(limbComponent.userProperties['rikJoints'][-1]) if hasReverseIKJoints else limbTipIKJoint

        # Create foot control
        #
        clawEnabled = not bool(clawSpec.passthrough)
        defaultClawMatrix = clawExportMatrix if clawEnabled else tipExportMatrix

        footOrigin = transformutils.breakMatrix(defaultClawMatrix)[3]
        footUpVector = om.MVector(self.scene.upVector)
        footRightVector = transformutils.breakMatrix(defaultClawMatrix, normalize=True)[2]
        footCtrlMatrix = mirrorMatrix * transformutils.createAimMatrix(2, footUpVector, 1, footRightVector, origin=footOrigin)

        footSpaceName = self.formatName(kinemat='IK', type='space')
        footSpace = self.scene.createNode('transform', name=footSpaceName, parent=controlsGroup)
        footSpace.setWorldMatrix(footCtrlMatrix)
        footSpace.freezeTransform()

        footCtrlName = self.formatName(kinemat='IK', type='control')
        footCtrl = self.scene.createNode('transform', name=footCtrlName, parent=footSpace)
        footCtrl.addShape('InvertedStarCurve', size=(30.0 * rigScale), localRotate=(0.0, 0.0, 90.0), lineWidth=3.0, colorRGB=colorRGB)
        footCtrl.addDivider('Spaces')
        footCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        footCtrl.addAttr(longName='localAutoTwist', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        footCtrl.prepareChannelBoxForAnimation()
        footCtrl.tagAsController()
        self.publishNode(footCtrl, alias=f'{self.componentName}_IK')

        footSpaceSwitch = footSpace.addSpaceSwitch([limbFKCtrl, limbIKOffsetCtrl, motionCtrl], maintainOffset=True)
        footSpaceSwitch.weighted = True
        footSpaceSwitch.setAttr('target', [{'targetReverse': (True, True, True)}, {}, {'targetWeight': (0.0, 0.0, 0.0)}])
        footSpaceSwitch.connectPlugs(switchCtrl['mode'], 'target[0].targetWeight')
        footSpaceSwitch.connectPlugs(switchCtrl['mode'], 'target[1].targetWeight')
        footSpaceSwitch.connectPlugs(footCtrl['localOrGlobal'], 'target[2].targetRotateWeight')

        coxaEnabled = bool(limbComponent.coxaEnabled)
        legUpTarget = limbComponent.getPublishedNode('Coxa_Trans') if coxaEnabled else limbComponent.getPublishedNode('Leg')
        legFollowJoint = self.scene(limbComponent.userProperties['followJoints'][-1])

        footAimMatrixName = self.formatName(subname='AutoFollow', kinemat='IK', type='aimMatrix')
        footAimMatrix = self.scene.createNode('aimMatrix', name=footAimMatrixName)
        footAimMatrix.connectPlugs(legUpTarget[f'worldMatrix[{legUpTarget.instanceNumber()}]'], 'inputMatrix')
        footAimMatrix.primaryInputAxis = (1.0, 0.0, 0.0)
        footAimMatrix.primaryMode = 1  # Aim
        footAimMatrix.primaryTargetVector = (1.0, 0.0, 0.0)
        footAimMatrix.connectPlugs(limbIKOffsetCtrl[f'worldMatrix[{limbIKOffsetCtrl.instanceNumber()}]'], 'primaryTargetMatrix')
        footAimMatrix.secondaryInputAxis = (0.0, 0.0, 1.0)
        footAimMatrix.secondaryMode = 2  # Align
        footAimMatrix.secondaryTargetVector = (0.0, 0.0, 1.0)
        footAimMatrix.connectPlugs(legFollowJoint[f'worldMatrix[{legFollowJoint.instanceNumber()}]'], 'secondaryTargetMatrix')

        footAutoTwistMatrixName = self.formatName(subname='AutoTwist', kinemat='IK', type='aimMatrix')
        footAutoTwistMatrix = self.scene.createNode('aimMatrix', name=footAutoTwistMatrixName)
        footAutoTwistMatrix.connectPlugs(limbIKCtrl[f'worldMatrix[{limbIKCtrl.instanceNumber()}]'], 'inputMatrix')
        footAutoTwistMatrix.primaryInputAxis = (0.0, 0.0, 1.0)
        footAutoTwistMatrix.primaryMode = 2  # Align
        footAutoTwistMatrix.primaryTargetVector = (0.0, 0.0, 1.0)
        footAutoTwistMatrix.connectPlugs(motionCtrl[f'worldMatrix[{motionCtrl.instanceNumber()}]'], 'primaryTargetMatrix')
        footAutoTwistMatrix.secondaryInputAxis = (0.0, 1.0, 0.0)
        footAutoTwistMatrix.secondaryMode = 2  # Align
        footAutoTwistMatrix.secondaryTargetVector = (0.0, 0.0, 1.0)
        footAutoTwistMatrix.connectPlugs(footAimMatrix['outputMatrix'], 'secondaryTargetMatrix')

        footLocalBlendMatrixName = self.formatName(name='Foot', subname='LocalSpace', kinemat='IK', type='blendTransform')
        footLocalBlendMatrix = self.scene.createNode('blendTransform', name=footLocalBlendMatrixName)
        footLocalBlendMatrix.connectPlugs(footCtrl['localAutoTwist'], 'blender')
        footLocalBlendMatrix.connectPlugs(limbIKOffsetCtrl[f'worldMatrix[{limbIKOffsetCtrl.instanceNumber()}]'], 'inMatrix1')
        footLocalBlendMatrix.connectPlugs(footAutoTwistMatrix['outputMatrix'], 'inMatrix2')

        footSpaceSwitch.replaceTarget(1, footLocalBlendMatrix)

        # Create tarsus IK controls
        #
        initialTarsusCount = len(tarsusExportJoints)
        reversedTarsusExportJoints = list(reversed(tarsusExportJoints))
        tarsusIKSourceNodes = [footCtrl] + reversedTarsusExportJoints

        tarsusIKMatrices = []
        tarsusIKCtrls = []

        for (i, (startNode, endNode)) in enumerate(zip(tarsusIKSourceNodes[:-1], tarsusIKSourceNodes[1:])):

            # Compose tarsus IK matrix
            #
            startMatrix, endMatrix = startNode.worldMatrix(), endNode.worldMatrix()

            tarsusOrigin = transformutils.breakMatrix(startMatrix, normalize=True)[3]
            tarsusGoal = transformutils.breakMatrix(endMatrix, normalize=True)[3]
            tarsusForwardVector = om.MVector(tarsusGoal - tarsusOrigin).normal()
            tarsusRightVector = transformutils.breakMatrix(endMatrix, normalize=True)[2]

            tarsusIKMatrix = mirrorMatrix * transformutils.createAimMatrix(0, -tarsusForwardVector, 2, tarsusRightVector, origin=tarsusOrigin)
            tarsusIKMatrices.append(tarsusIKMatrix)

            # Create tarsus IK target
            #
            parent = tarsusIKCtrls[i - 1] if (i > 0) else footCtrl
            index = i + 1

            tarsusIKTargetName = self.formatName(name='Tarsus', kinemat='IK', index=index, type='target')
            tarsusIKTarget = self.scene.createNode('transform', name=tarsusIKTargetName, parent=parent)
            tarsusIKTarget.displayLocalAxis = True
            tarsusIKTarget.visibility = False
            tarsusIKTarget.setWorldMatrix(tarsusIKMatrix, skipScale=True)
            tarsusIKTarget.freezeTransform()
            tarsusIKTarget.lock()

            # Create tarsus IK control
            #
            tarsusIKSpaceName = self.formatName(name='Tarsus', kinemat='IK', index=index, type='space')
            tarsusIKSpace = self.scene.createNode('transform', name=tarsusIKSpaceName, parent=controlsGroup)
            tarsusIKSpace.setWorldMatrix(tarsusIKMatrix, skipScale=True)
            tarsusIKSpace.freezeTransform()

            tarsusIKCtrlName = self.formatName(name='Tarsus', kinemat='IK', index=index, type='control')
            tarsusIKCtrl = self.scene.createNode('transform', name=tarsusIKCtrlName, parent=tarsusIKSpace)
            tarsusIKCtrl.addDivider('Settings')
            tarsusIKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            tarsusIKCtrl.prepareChannelBoxForAnimation()
            tarsusIKCtrl.tagAsController(parent=parent)
            self.publishNode(tarsusIKCtrl, alias=f'Tarsus{str(index).zfill(2)}_IK')

            tarsusIKCtrls.append(tarsusIKCtrl)

            # Create tarsus IK control shape
            #
            tarsusIKCtrlShape = tarsusIKCtrl.addPointHelper('box', size=(15.0 * rigScale), colorRGB=lightColorRGB, lineWidth=2.0)
            tarsusIKCtrlShape.reorientAndScaleToFit(endNode)

            # Setup tarsus IK space switching
            #
            tarsusIKSpaceSwitch = tarsusIKSpace.addSpaceSwitch([tarsusIKTarget, motionCtrl], weighted=True, maintainOffset=True)
            tarsusIKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            tarsusIKSpaceSwitch.connectPlugs(tarsusIKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            tarsusIKSpaceSwitch.connectPlugs(tarsusIKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

            tarsusIKAimMatrixName = self.formatName(name='Tibia', subname='WorldSpace', kinemat='IK', index=index, type='aimMatrix')
            tarsusIKAimMatrix = self.scene.createNode('aimMatrix', name=tarsusIKAimMatrixName)
            tarsusIKAimMatrix.connectPlugs(tarsusIKTarget[f'worldMatrix[{tarsusIKTarget.instanceNumber()}]'], 'inputMatrix')
            tarsusIKAimMatrix.primaryInputAxis = (0.0, 0.0, 1.0)
            tarsusIKAimMatrix.primaryMode = 2  # Align
            tarsusIKAimMatrix.primaryTargetVector = (0.0, 0.0, 1.0)
            tarsusIKAimMatrix.connectPlugs(tarsusIKTarget[f'worldMatrix[{tarsusIKTarget.instanceNumber()}]'], 'primaryTargetMatrix')
            tarsusIKAimMatrix.secondaryInputAxis = (1.0 * mirrorSign, 0.0, 0.0)
            tarsusIKAimMatrix.secondaryMode = 2  # Align
            tarsusIKAimMatrix.secondaryTargetVector = (0.0, 0.0, -1.0)
            tarsusIKAimMatrix.connectPlugs(motionCtrl[f'worldMatrix[{motionCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')

            tarsusIKSpaceSwitch.replaceTarget(1, tarsusIKAimMatrix, maintainOffset=True)

            tarsusIKCtrl.userProperties['space'] = tarsusIKSpace.uuid()
            tarsusIKCtrl.userProperties['spaceSwitch'] = tarsusIKSpaceSwitch.uuid()
            tarsusIKCtrl.userProperties['target'] = tarsusIKTarget.uuid()

        # Create limb IK target
        #
        tarsusTipIKTargetName = self.formatName(name='TarsusTip', kinemat='IK', type='target')
        tarsusTipIKTarget = self.scene.createNode('transform', name=tarsusTipIKTargetName, parent=tarsusIKCtrls[-1])
        tarsusTipIKTarget.displayLocalAxis = True
        tarsusTipIKTarget.visibility = False
        tarsusTipIKTarget.setWorldMatrix(tarsusExportMatrices[0], skipScale=True)
        tarsusTipIKTarget.freezeTransform()
        tarsusTipIKTarget.lock()

        self.userProperties['ikTarget'] = tarsusTipIKTarget.uuid()

        # Append tarsus IK control to limb's PV spaces
        #
        limbPVCtrl = self.scene(limbComponent.userProperties['pvControl'])
        limbPVSpaceSwitch = self.scene(limbPVCtrl.userProperties['spaceSwitch'])

        index = limbPVSpaceSwitch.addTarget(tarsusTipIKTarget)
        longName = f'transformSpaceW{index}'
        limbPVCtrl.addAttr(longName=longName, niceName='Transform Space (Tarsus)', attributeType='float', min=0.0, max=1.0, keyable=True)
        limbPVCtrl.connectPlugs(longName, limbPVSpaceSwitch[f'target[{index}].targetWeight'])

        # Add spring space to first tarsus IK control
        #
        isInsectLimbComponent = limbComponent.__class__.__name__.endswith('InsectLegComponent')

        if isInsectLimbComponent:

            # Add extra attributes to tarsus IK control
            #
            firstTarsusIKCtrl = tarsusIKCtrls[0]
            firstTarsusIKCtrl.addAttr(longName='localSpringLock', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            firstTarsusIKCtrl.addAttr(longName='localLeanLock', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            # Retrieve space switch and last spring IK joint
            #
            firstTarsusIKSpace = self.scene(firstTarsusIKCtrl.userProperties['space'])
            firstTarsusIKSpaceSwitch = self.scene(firstTarsusIKCtrl.userProperties['spaceSwitch'])
            firstTarsusIKTarget = self.scene(firstTarsusIKCtrl.userProperties['target'])

            lastSpringIKJoint = self.scene(limbComponent.userProperties['sikJoints'][-1])

            # Compose spring target matrix
            #
            tarsusIKSpringMatrixName = self.formatName(name='Tarsus', subname='Spring', kinemat='IK', type='aimMatrix')
            tarsusIKSpringMatrix = self.scene.createNode('aimMatrix', name=tarsusIKSpringMatrixName)
            tarsusIKSpringMatrix.connectPlugs(lastSpringIKJoint[f'worldMatrix[{lastSpringIKJoint.instanceNumber()}]'], 'inputMatrix')
            tarsusIKSpringMatrix.primaryInputAxis = (0.0, 0.0, 1.0)
            tarsusIKSpringMatrix.primaryMode = 2  # Align
            tarsusIKSpringMatrix.primaryTargetVector = (0.0, 1.0 * mirrorSign, 0.0)
            tarsusIKSpringMatrix.connectPlugs(footCtrl[f'worldMatrix[{footCtrl.instanceNumber()}]'], 'primaryTargetMatrix')
            tarsusIKSpringMatrix.secondaryInputAxis = (1.0, 0.0, 0.0)
            tarsusIKSpringMatrix.secondaryMode = 2  # Align
            tarsusIKSpringMatrix.secondaryTargetVector = (1.0, 0.0, 0.0)
            tarsusIKSpringMatrix.connectPlugs(lastSpringIKJoint[f'worldMatrix[{lastSpringIKJoint.instanceNumber()}]'], 'secondaryTargetMatrix')

            tarsusIKSpringBlendMatrixName = self.formatName(name='Tarsus', subname='Spring', kinemat='IK', type='blendTransform')
            tarsusIKSpringBlendMatrix = self.scene.createNode('blendTransform', name=tarsusIKSpringBlendMatrixName)
            tarsusIKSpringBlendMatrix.connectPlugs(firstTarsusIKCtrl['localLeanLock'], 'blender')
            tarsusIKSpringBlendMatrix.connectPlugs(lastSpringIKJoint[f'worldMatrix[{lastSpringIKJoint.instanceNumber()}]'], 'inMatrix1')
            tarsusIKSpringBlendMatrix.connectPlugs(tarsusIKSpringMatrix['outputMatrix'], 'inMatrix2')

            tarsusIKSpringOffsetMatrix = firstTarsusIKCtrl.worldMatrix() * tarsusIKSpringMatrix.getAttr('outputMatrix').inverse()
            tarsusIKSpringOffsetComposeMatrixName = self.formatName(name='Tarsus', subname='SpringOffset', kinemat='IK', type='composeMatrix')
            tarsusIKSpringOffsetComposeMatrix = self.scene.createNode('composeMatrix', name=tarsusIKSpringOffsetComposeMatrixName)
            tarsusIKSpringOffsetComposeMatrix.copyMatrix(tarsusIKSpringOffsetMatrix)

            tarsusIKSpringOffsetMultMatrixName = self.formatName(name='Tarsus', subname='SpringOffset', kinemat='IK', type='multMatrix')
            tarsusIKSpringOffsetMultMatrix = self.scene.createNode('multMatrix', name=tarsusIKSpringOffsetMultMatrixName)
            tarsusIKSpringOffsetMultMatrix.connectPlugs(tarsusIKSpringOffsetComposeMatrix['outputMatrix'], 'matrixIn[0]')
            tarsusIKSpringOffsetMultMatrix.connectPlugs(tarsusIKSpringBlendMatrix['outMatrix'], 'matrixIn[1]')

            # Create local space blend and replace target
            #
            tarsusIKLocalSpaceBlendMatrixName = self.formatName(name='Tarsus', subname='LocalSpace', kinemat='IK', index=1, type='blendTransform')
            tarsusIKLocalSpaceBlendMatrix = self.scene.createNode('blendTransform', name=tarsusIKLocalSpaceBlendMatrixName)
            tarsusIKLocalSpaceBlendMatrix.connectPlugs(firstTarsusIKCtrl['localSpringLock'], 'blender')
            tarsusIKLocalSpaceBlendMatrix.connectPlugs(firstTarsusIKTarget[f'worldMatrix[{firstTarsusIKTarget.instanceNumber()}]'], 'inMatrix1')
            tarsusIKLocalSpaceBlendMatrix.connectPlugs(tarsusIKSpringOffsetMultMatrix['matrixSum'], 'inMatrix2')

            firstTarsusIKSpaceSwitch.replaceTarget(0, tarsusIKLocalSpaceBlendMatrix, maintainOffset=False, resetOffset=True)

        # Create kinematic tarsus joints
        #
        adjustedTarsusCount = initialTarsusCount + 1
        jointTypes = (['Tarsus'] * initialTarsusCount) + ['TarsusTip']
        kinematicTypes = ('FK', 'IK', 'Blend')

        tarsusFKJoints = [None] * adjustedTarsusCount
        tarsusIKJoints = [None] * adjustedTarsusCount
        tarsusBlendJoints = [None] * adjustedTarsusCount
        tarsusMatrices = tarsusExportMatrices + ([clawExportMatrix] if clawEnabled else [tipExportMatrix])
        tarsusKinematicJoints = (tarsusFKJoints, tarsusIKJoints, tarsusBlendJoints)

        lastIndex = initialTarsusCount

        for (i, kinematicType) in enumerate(kinematicTypes):

            for (j, jointType) in enumerate(jointTypes):

                parent = tarsusKinematicJoints[i][j - 1] if (j > 0) else jointsGroup
                inheritsTransform = not (j == 0)
                index = None if (j == lastIndex) else (j + 1)

                jointName = self.formatName(name=jointType, kinemat=kinematicType, index=index, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.inheritsTransform = inheritsTransform
                joint.displayLocalAxis = True
                joint.setWorldMatrix(tarsusMatrices[j])

                tarsusKinematicJoints[i][j] = joint

        # Setup kinematic blends
        #
        blender = switchCtrl['mode']

        for (i, (tarsusFKJoint, tarsusIKJoint, tarsusBlendJoint)) in enumerate(zip(tarsusFKJoints, tarsusIKJoints, tarsusBlendJoints)):

            footBlender = setuputils.createTransformBlends(tarsusFKJoint, tarsusIKJoint, tarsusBlendJoint, blender=blender)
            footBlender.setName(self.formatName(name='Foot', subname=jointTypes[i], type='blendTransform'))

        # Create tarsus FK controls
        #
        tarsusFKCtrls = [None] * initialTarsusCount
        tarsusTipFKTarget = None

        for (i, tarsusFKJoint) in enumerate(tarsusFKJoints):

            # Evaluate position in tarsus FK chain
            #
            previousTarsusCtrl = tarsusFKCtrls[i - 1] if (i > 0) else limbFKCtrl
            index = i + 1

            if i == lastIndex:

                # Create tarsus tip FK target
                #
                tarsusTipFKTargetName = self.formatName(name='TarsusTip', kinemat='FK', type='target')
                tarsusTipFKTarget = self.scene.createNode('transform', name=tarsusTipFKTargetName, parent=tarsusFKCtrls[-1])
                tarsusTipFKTarget.displayLocalAxis = True
                tarsusTipFKTarget.visibility = False
                tarsusTipFKTarget.setWorldMatrix(tipExportMatrix, skipScale=True)
                tarsusTipFKTarget.freezeTransform()
                tarsusTipFKTarget.lock()

                tarsusFKJoint.addConstraint('transformConstraint', [tarsusTipFKTarget])

            else:

                # Create tarsus FK target
                #
                tarsusFKTargetName = self.formatName(name='Tarsus', kinemat='FK', index=index, type='target')
                tarsusFKTarget = self.scene.createNode('transform', name=tarsusFKTargetName, parent=previousTarsusCtrl)
                tarsusFKTarget.displayLocalAxis = True
                tarsusFKTarget.visibility = False
                tarsusFKTarget.copyTransform(tarsusFKJoint, skipScale=True)
                tarsusFKTarget.freezeTransform()
                tarsusFKTarget.lock()

                # Create tarsus FK control
                #
                tarsusFKCtrlMatrix = mirrorMatrix * tarsusFKTarget.worldMatrix()

                tarsusFKSpaceName = self.formatName(name='Tarsus', kinemat='FK', index=index, type='space')
                tarsusFKSpace = self.scene.createNode('transform', name=tarsusFKSpaceName, parent=controlsGroup)
                tarsusFKSpace.setWorldMatrix(tarsusFKCtrlMatrix, skipScale=True)
                tarsusFKSpace.freezeTransform()

                tarsusFKCtrlName = self.formatName(name='Tarsus', kinemat='FK', index=index, type='control')
                tarsusFKCtrl = self.scene.createNode('transform', name=tarsusFKCtrlName, parent=tarsusFKSpace)
                tarsusFKCtrl.addDivider('Settings')
                tarsusFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
                tarsusFKCtrl.prepareChannelBoxForAnimation()
                tarsusFKCtrl.tagAsController(parent=previousTarsusCtrl)

                tarsusFKShape = tarsusFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
                tarsusFKShape.reorientAndScaleToFit(tarsusFKJoints[i + 1])

                # Add space switching to tarsus FK control
                #
                tarsusFKSpaceSwitch = tarsusFKSpace.addSpaceSwitch([previousTarsusCtrl, motionCtrl], weighted=True, maintainOffset=True)
                tarsusFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                tarsusFKSpaceSwitch.connectPlugs(tarsusFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                tarsusFKSpaceSwitch.connectPlugs(tarsusFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                tarsusFKAimMatrixName = self.formatName(name='Tarsus', subname='WorldSpace', index=index, kinemat='FK', type='aimMatrix')
                tarsusFKAimMatrix = self.scene.createNode('aimMatrix', name=tarsusFKAimMatrixName)
                tarsusFKAimMatrix.connectPlugs(tarsusFKTarget[f'worldMatrix[{tarsusFKTarget.instanceNumber()}]'], 'inputMatrix')
                tarsusFKAimMatrix.primaryInputAxis = (0.0, 0.0, 1.0)
                tarsusFKAimMatrix.primaryMode = 2  # Align
                tarsusFKAimMatrix.primaryTargetVector = (0.0, 0.0, 1.0)
                tarsusFKAimMatrix.connectPlugs(tarsusFKTarget[f'worldMatrix[{tarsusFKTarget.instanceNumber()}]'], 'primaryTargetMatrix')
                tarsusFKAimMatrix.secondaryInputAxis = (0.0, 1.0, 0.0)
                tarsusFKAimMatrix.secondaryMode = 2  # Align
                tarsusFKAimMatrix.secondaryTargetVector = (0.0, 0.0, -1.0)
                tarsusFKAimMatrix.connectPlugs(motionCtrl[f'worldMatrix[{motionCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')

                tarsusFKSpaceSwitch.replaceTarget(1, tarsusFKAimMatrix, maintainOffset=True)

                tarsusFKCtrl.userProperties['space'] = tarsusFKSpace.uuid()
                tarsusFKCtrl.userProperties['spaceSwitch'] = tarsusFKSpaceSwitch.uuid()
                tarsusFKCtrl.userProperties['target'] = tarsusFKTarget.uuid()

                tarsusFKCtrls[i] = tarsusFKCtrl

                # Constrain tarsus FK joint
                #
                tarsusFKJoint.addConstraint('transformConstraint', [tarsusFKCtrl], maintainOffset=requiresMirroring)

        footSpaceSwitch.replaceTarget(0, tarsusTipFKTarget, maintainOffset=True)

        # Apply single-chain IK solvers to tarsus IK joints
        #
        reversedTarsusIKCtrls = list(reversed(tarsusIKCtrls))
        limbIKSoftener = self.scene(limbComponent.userProperties['sikSoftener'])

        for (i, (startIKJoint, endIKJoint)) in enumerate(zip(tarsusIKJoints[:-1], tarsusIKJoints[1:])):

            # Apply single-chain IK solver
            #
            tarsusIKCtrl = reversedTarsusIKCtrls[i]
            index = i + 1

            tarsusIKHandle, tarsusIKEffector = kinematicutils.applySingleChainSolver(startIKJoint, endIKJoint)
            tarsusIKHandle.setName(self.formatName(name='Foot', subname='Tarsus', index=index, type='ikHandle'))
            tarsusIKHandle.setParent(privateGroup)
            tarsusIKHandle.addConstraint('transformConstraint', [tarsusIKCtrl], maintainOffset=True)
            tarsusIKEffector.setName(self.formatName(name='Foot', subname='Tarsus', index=index, type='ikEffector'))

            # Setup IK stretch
            # TODO: Test if parent limb component supports scaling!
            #
            defaultLength = startIKJoint.distanceBetween(endIKJoint)
            tarsusIKCtrl.addAttr(longName='length', attributeType='float', default=defaultLength, hidden=True)

            tarsusIKStretchName = self.formatName(name='Tarsus', kinemat='IK', subname='Stretch', index=index, type='multDoubleLinear')
            tarsusIKStretch = self.scene.createNode('multDoubleLinear', name=tarsusIKStretchName)
            tarsusIKStretch.connectPlugs(tarsusIKCtrl['length'], 'input1')
            tarsusIKStretch.connectPlugs(limbIKSoftener['softScale'], 'input2')

            tarsusIKEnvelopeName = self.formatName(name='Tarsus', kinemat='IK', subname='Envelope', index=index, type='blendTwoAttr')
            tarsusIKEnvelope = self.scene.createNode('blendTwoAttr', name=tarsusIKEnvelopeName)
            tarsusIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
            tarsusIKEnvelope.connectPlugs(tarsusIKCtrl['length'], 'input[0]')
            tarsusIKEnvelope.connectPlugs(tarsusIKStretch['output'], 'input[1]')
            tarsusIKEnvelope.connectPlugs('output', endIKJoint['translateX'])

        tarsusIKJoints[0].addConstraint('pointConstraint', [limbTipRIKJoint])

        if clawEnabled:

            # Create claw kinematic joints
            #
            clawTypes = ('Claw', 'ClawTip')
            clawMatrices = (clawExportMatrix, tipExportMatrix)

            clawFKJoints = [None] * 2
            clawIKJoints = [None] * 2
            clawBlendJoints = [None] * 2
            clawKinematicJoints = (clawFKJoints, clawIKJoints, clawBlendJoints)

            for (i, kinematicType) in enumerate(kinematicTypes):

                for (j, clawType) in enumerate(clawTypes):

                    parent = clawKinematicJoints[i][j - 1] if (j > 0) else jointsGroup
                    inheritsTransform = not (j == 0)

                    jointName = self.formatName(name=clawType, kinemat=kinematicType, type='joint')
                    joint = self.scene.createNode('joint', name=jointName, parent=parent)
                    joint.inheritsTransform = inheritsTransform
                    joint.displayLocalAxis = True
                    joint.setWorldMatrix(clawMatrices[j])

                    clawKinematicJoints[i][j] = joint

            # Setup kinematic blends
            #
            blender = switchCtrl['mode']

            for (i, (clawFKJoint, clawIKJoint, clawBlendJoint)) in enumerate(zip(clawFKJoints, clawIKJoints, clawBlendJoints)):

                clawBlender = setuputils.createTransformBlends(clawFKJoint, clawIKJoint, clawBlendJoint, blender=blender)
                clawBlender.setName(self.formatName(name=clawTypes[i], type='blendTransform'))

            # Create claw IK controls
            #
            clawForwardVector = transformutils.breakMatrix(clawExportMatrix, normalize=True)[0]
            clawIKMatrix = transformutils.createAimMatrix(0, clawForwardVector, 1, footRightVector, origin=clawPoint)
            clawTipIKMatrix = transformutils.createRotationMatrix(clawIKMatrix) * transformutils.createTranslateMatrix(tipPoint)

            clawIKSpaceName = self.formatName(name='Claw', kinemat='IK', type='space')
            clawIKSpace = self.scene.createNode('transform', name=clawIKSpaceName, parent=controlsGroup)
            clawIKSpace.setWorldMatrix(clawIKMatrix, skipScale=True)
            clawIKSpace.freezeTransform()

            clawIKCtrlName = self.formatName(name='Claw', kinemat='IK', type='control')
            clawIKCtrl = self.scene.createNode('transform', name=clawIKCtrlName, parent=clawIKSpace)
            clawIKCtrl.addDivider('Settings')
            clawIKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            clawIKCtrl.tagAsController(parent=footCtrl)
            self.publishNode(clawIKCtrl, alias='Claw_IK')

            clawTipIKCtrlName = self.formatName(name='ClawTip', kinemat='IK', type='control')
            clawTipIKCtrl = self.scene.createNode('transform', name=clawTipIKCtrlName, parent=clawIKCtrl)
            clawTipIKCtrl.addPointHelper('pyramid', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
            clawTipIKCtrl.setWorldMatrix(clawTipIKMatrix, skipScale=True)
            clawTipIKCtrl.freezeTransform()
            clawTipIKCtrl.tagAsController(parent=clawIKCtrl)
            self.publishNode(clawTipIKCtrl, alias='ClawTip_IK')

            clawIKCtrlShape = clawIKCtrl.addPointHelper('box', size=(15.0 * rigScale), lineWidth=4.0, colorRGB=colorRGB)
            clawIKCtrlShape.reorientAndScaleToFit(clawTipIKCtrl)

            clawIKTargetName = self.formatName(name='Claw', kinemat='IK', type='target')
            clawIKTarget = self.scene.createNode('transform', name=clawIKTargetName, parent=clawTipIKCtrl)
            clawIKTarget.displayLocalAxis = True
            clawIKTarget.visibility = False
            clawIKTarget.setWorldMatrix(tipExportMatrix, skipScale=True)
            clawIKTarget.freezeTransform()
            clawIKTarget.lock()

            footIKTargetName = self.formatName(kinemat='IK', type='target')
            footIKTarget = self.scene.createNode('transform', name=footIKTargetName, parent=clawTipIKCtrl)
            footIKTarget.displayLocalAxis = True
            footIKTarget.visibility = False
            footIKTarget.setWorldMatrix(footCtrlMatrix, skipScale=True)
            footIKTarget.freezeTransform()
            footIKTarget.lock()

            # Add space switching to claw IK control
            #
            limbIKPickMatrixName = self.formatName(name='ClawTip', subname='LocalPositionSpace', kinemat='IK', type='pickMatrix')
            limbIKPickMatrix = self.scene.createNode('pickMatrix', name=limbIKPickMatrixName)
            limbIKPickMatrix.useTranslate = False
            limbIKPickMatrix.useRotate = True
            limbIKPickMatrix.useScale = True
            limbIKPickMatrix.useShear = True
            limbIKPickMatrix.connectPlugs(limbIKOffsetCtrl[f'worldMatrix[{limbIKOffsetCtrl.instanceNumber()}]'], 'inputMatrix')

            footIKPickMatrixName = self.formatName(name='ClawTip', subname='LocalRotationSpace', kinemat='IK', type='pickMatrix')
            footIKPickMatrix = self.scene.createNode('pickMatrix', name=footIKPickMatrixName)
            footIKPickMatrix.useTranslate = True
            footIKPickMatrix.useRotate = False
            footIKPickMatrix.useScale = False
            footIKPickMatrix.useShear = False
            footIKPickMatrix.connectPlugs(footCtrl[f'worldMatrix[{limbIKOffsetCtrl.instanceNumber()}]'], 'inputMatrix')

            clawTipIKLocalSpaceMultMatrixName = self.formatName(name='ClawTip', subname='LocalSpace', kinemat='IK', type='multMatrix')
            clawTipIKLocalSpaceMultMatrix = self.scene.createNode('multMatrix', name=clawTipIKLocalSpaceMultMatrixName)
            clawTipIKLocalSpaceMultMatrix.connectPlugs(limbIKPickMatrix['outputMatrix'], 'matrixIn[0]')
            clawTipIKLocalSpaceMultMatrix.connectPlugs(footIKPickMatrix['outputMatrix'], 'matrixIn[1]')

            clawIKSpaceSwitch = clawIKSpace.addSpaceSwitch([limbIKOffsetCtrl, motionCtrl], weighted=True, maintainOffset=True)
            clawIKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            clawIKSpaceSwitch.connectPlugs(clawIKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            clawIKSpaceSwitch.connectPlugs(clawIKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')
            clawIKSpaceSwitch.replaceTarget(0, clawTipIKLocalSpaceMultMatrix)

            clawIKCtrl.userProperties['space'] = clawIKSpace.uuid()
            clawIKCtrl.userProperties['spaceSwitch'] = clawIKSpaceSwitch.uuid()
            clawIKCtrl.userProperties['tip'] = clawTipIKCtrl.uuid()
            clawIKCtrl.userProperties['ikTarget'] = clawIKTarget.uuid()
            clawIKCtrl.userProperties['sikTarget'] = footIKTarget.uuid()

            # Point constrain first tarsus IK target
            #
            firstTarsusIKCtrl = tarsusIKCtrls[0]
            firstTarsusFKCtrl, lastTarsusFKCtrl = tarsusFKCtrls[0], tarsusFKCtrls[-1]

            firstTarsusIKTarget = self.scene(firstTarsusIKCtrl.userProperties['target'])
            firstTarsusIKTarget.unlock()
            firstTarsusIKTarget.addConstraint('pointConstraint', [footIKTarget])
            firstTarsusIKTarget.lock()

            # Apply single-chain IK solver to claw IK joints
            #
            clawIKJoint, clawTipIKJoint = clawIKJoints
            lastTarsusIKJoint = tarsusIKJoints[-1]

            clawIKHandle, clawIKEffector = kinematicutils.applySingleChainSolver(clawIKJoint, clawTipIKJoint)
            clawIKHandle.setName(self.formatName(name='Claw', type='ikHandle'))
            clawIKHandle.setParent(privateGroup)
            clawIKHandle.addConstraint('transformConstraint', [clawIKTarget])
            clawIKEffector.setName(self.formatName(name='Claw', type='ikEffector'))

            clawIKJoint.addConstraint('pointConstraint', [lastTarsusIKJoint])

            # Create claw FK control
            #
            clawFKTargetMatrix = mirrorMatrix * clawExportMatrix

            clawFKTargetName = self.formatName(name='Claw', kinemat='FK', type='target')
            clawFKTarget = self.scene.createNode('transform', name=clawFKTargetName, parent=lastTarsusFKCtrl)
            clawFKTarget.displayLocalAxis = True
            clawFKTarget.visibility = False
            clawFKTarget.setWorldMatrix(clawFKTargetMatrix, skipScale=True)
            clawFKTarget.freezeTransform()
            clawFKTarget.lock()

            clawFKSpaceName = self.formatName(name='Claw', kinemat='FK', type='space')
            clawFKSpace = self.scene.createNode('transform', name=clawFKSpaceName, parent=controlsGroup)
            clawFKSpace.setWorldMatrix(clawFKTargetMatrix, skipScale=True)
            clawFKSpace.freezeTransform()

            clawFKCtrlName = self.formatName(name='Claw', kinemat='FK', type='control')
            clawFKCtrl = self.scene.createNode('transform', name=clawFKCtrlName, parent=clawFKSpace)
            clawFKCtrl.addDivider('Settings')
            clawFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            clawFKCtrl.prepareChannelBoxForAnimation()
            clawFKCtrl.tagAsController(parent=firstTarsusFKCtrl)

            # Create claw-tip FK target
            #
            clawTipFKTargetMatrix = mirrorMatrix * tipExportMatrix

            clawTipFKTargetName = self.formatName(name='ClawTip', kinemat='FK', type='target')
            clawTipFKTarget = self.scene.createNode('transform', name=clawTipFKTargetName, parent=clawFKCtrl)
            clawTipFKTarget.displayLocalAxis = True
            clawTipFKTarget.visibility = False
            clawTipFKTarget.setWorldMatrix(clawTipFKTargetMatrix, skipScale=True)
            clawTipFKTarget.freezeTransform()
            clawTipFKTarget.lock()

            # Add shape to claw FK control
            #
            clawFKCtrlShape = clawFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), localRotate=(45.0, 0.0, 0.0), lineWidth=2.0, colorRGB=lightColorRGB)
            clawFKCtrlShape.reorientAndScaleToFit(clawTipFKTarget)

            # Add space switching to claw FK control
            #
            clawFKSpaceSwitch = clawFKSpace.addSpaceSwitch([clawFKTarget, motionCtrl], weighted=True, maintainOffset=True)
            clawFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            clawFKSpaceSwitch.connectPlugs(clawFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            clawFKSpaceSwitch.connectPlugs(clawFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

            clawFKAimMatrixName = self.formatName(name='Claw', subname='WorldSpace', index=index, kinemat='FK', type='aimMatrix')
            clawFKAimMatrix = self.scene.createNode('aimMatrix', name=clawFKAimMatrixName)
            clawFKAimMatrix.connectPlugs(clawFKTarget[f'worldMatrix[{clawFKTarget.instanceNumber()}]'], 'inputMatrix')
            clawFKAimMatrix.primaryInputAxis = (0.0, 0.0, 1.0)
            clawFKAimMatrix.primaryMode = 2  # Align
            clawFKAimMatrix.primaryTargetVector = (0.0, 0.0, 1.0)
            clawFKAimMatrix.connectPlugs(clawFKTarget[f'worldMatrix[{clawFKTarget.instanceNumber()}]'], 'primaryTargetMatrix')
            clawFKAimMatrix.secondaryInputAxis = (0.0, 1.0, 0.0)
            clawFKAimMatrix.secondaryMode = 2  # Align
            clawFKAimMatrix.secondaryTargetVector = (0.0, 0.0, -1.0)
            clawFKAimMatrix.connectPlugs(motionCtrl[f'worldMatrix[{motionCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')

            clawFKSpaceSwitch.replaceTarget(1, clawFKAimMatrix, maintainOffset=True)

            clawFKCtrl.userProperties['space'] = clawFKSpace.uuid()
            clawFKCtrl.userProperties['spaceSwitch'] = clawFKSpaceSwitch.uuid()
            clawFKCtrl.userProperties['target'] = clawFKTarget.uuid()

            # Constraint claw FK joints
            #
            clawFKJoints[0].addConstraint('transformConstraint', [clawFKCtrl], maintainOffset=requiresMirroring)
            clawFKJoints[1].addConstraint('transformConstraint', [clawTipFKTarget], maintainOffset=requiresMirroring)

        # Call parent method
        #
        return super(InsectFootComponent, self).buildRig()
    # endregion
