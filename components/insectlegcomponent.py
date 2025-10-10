from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyattribute
from dcc.maya.libs import transformutils, shapeutils
from dcc.dataclasses.colour import Colour
from rigomatic.libs import kinematicutils
from enum import IntEnum
from . import limbcomponent
from ..libs import Side, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LimbType(IntEnum):
    """
    Enum class of all available insect limb types.
    """

    COXA = 0
    FEMUR = 1
    TIBIA = 2
    TIBIA_TIP = 3


class InsectLegComponent(limbcomponent.LimbComponent):
    """
    Overload of `AbstractComponent` that outlines insect leg components.
    """

    # region Dunderscores
    __default_component_name__ = 'Leg'
    __default_limb_names__ = ('Coxa', 'Femur', 'Tibia', 'TibiaTip')
    __default_limb_matrices__ = {
        Side.LEFT: {
            LimbType.COXA: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (9.6593, 0.0, 7.41181, 1.0)
                ]
            ),
            LimbType.FEMUR: om.MMatrix(
                [
                    (0.642788, 0.0, 0.766044, 0.0),
                    (-0.766044, 0.0, 0.642788, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (19.6593, 0.0, 7.41181, 1.0)
                ]
            ),
            LimbType.TIBIA: om.MMatrix(
                [
                    (0.965926, 0.0, -0.258819, 0.0),
                    (0.258819, 0.0, 0.965926, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (35.7289, 0.0, 26.5629, 1.0)
                ]
            ),
            LimbType.TIBIA_TIP: om.MMatrix(
                [
                    (0.965926, 0.0, -0.258819, 0.0),
                    (0.258819, 0.0, 0.965926, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (55.0474, 0.0, 21.3865, 1.0)
                ]
            )
        },
        Side.RIGHT: {
            LimbType.COXA: om.MMatrix(
                [
                    (-0.965926, 0.0, -0.258819, 0.0),
                    (0.258819, 0.0, 0.965926, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (-10.0, 0.0, 10.0, 1.0)
                ]
            ),
            LimbType.FEMUR: om.MMatrix(
                [
                    (-0.642788, 0.0, 0.766044, 0.0),
                    (-0.766044, 0.0, 0.642788, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (-19.6593, 0.0, 7.41181, 1.0)
                ]
            ),
            LimbType.TIBIA: om.MMatrix(
                [
                    (-0.965926, 0.0, -0.258819, 0.0),
                    (0.258819, 0.0, 0.965926, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (-35.7289, 0.0, 26.5629, 1.0)
                ]
            )
        }
    }
    __default_rbf_samples__ = {
        Side.LEFT: [
            {'sampleName': 'Forward', 'sampleInputTranslate': om.MVector.kZaxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Backward', 'sampleInputTranslate': om.MVector.kZnegAxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Left', 'sampleInputTranslate': om.MVector.kYnegAxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Right', 'sampleInputTranslate': om.MVector.kYaxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Up', 'sampleInputTranslate': om.MVector.kXaxisVector, 'sampleOutputTranslate': (0.0, 0.0, -1.0)},
            {'sampleName': 'Down', 'sampleInputTranslate': om.MVector.kXnegAxisVector, 'sampleOutputTranslate': (0.0, 0.0, 1.0)}
        ],
        Side.RIGHT: [
            {'sampleName': 'Forward', 'sampleInputTranslate': om.MVector.kZnegAxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Backward', 'sampleInputTranslate': om.MVector.kZaxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Left', 'sampleInputTranslate': om.MVector.kYaxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Right', 'sampleInputTranslate': om.MVector.kYnegAxisVector, 'sampleOutputTranslate': (1.0, 0.0, 0.0)},
            {'sampleName': 'Up', 'sampleInputTranslate': om.MVector.kXaxisVector, 'sampleOutputTranslate': (0.0, 0.0, 1.0)},
            {'sampleName': 'Down', 'sampleInputTranslate': om.MVector.kXnegAxisVector, 'sampleOutputTranslate': (0.0, 0.0, -1.0)}
        ]
    }
    # endregion

    # region Enums
    LimbType = LimbType
    # endregion

    # region Attributes
    coxaEnabled = mpyattribute.MPyAttribute('coxaEnabled', attributeType='bool', default=True)

    @coxaEnabled.changed
    def coxaEnabled(self, coxaEnabled):
        """
        Changed method that notifies of any state changes.

        :type coxaEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()
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
        size = len(self.LimbType)
        coxaSpec, femurSpec, tibiaSpec, tibiaTipSpec = self.resizeSkeleton(size, skeletonSpecs, hierarchical=True)

        # Iterate through limb specs
        #
        coxaName, femurName, tibiaName, tibiaTipName = self.__default_limb_names__
        side = self.Side(self.componentSide)

        coxaSpec.name = self.formatName(name=coxaName)
        coxaSpec.side = side
        coxaSpec.type = self.Type.OTHER
        coxaSpec.otherType = coxaName
        coxaSpec.drawStyle = self.Style.BOX
        coxaSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.COXA]
        coxaSpec.driver.name = self.formatName(name=coxaName, type='joint')

        femurSpec.name = self.formatName(name=femurName)
        femurSpec.side = side
        femurSpec.type = self.Type.OTHER
        femurSpec.otherType = femurName
        femurSpec.drawStyle = self.Style.BOX
        femurSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.FEMUR]
        femurSpec.driver.name = self.formatName(name=femurName, type='joint')

        tibiaSpec.name = self.formatName(name=tibiaName)
        tibiaSpec.side = side
        tibiaSpec.type = self.Type.OTHER
        tibiaSpec.otherType = tibiaName
        tibiaSpec.drawStyle = self.Style.BOX
        tibiaSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.TIBIA]
        tibiaSpec.driver.name = self.formatName(name=tibiaName, type='joint')

        tibiaTipSpec.enabled = not self.hasExtremityComponent()
        tibiaTipSpec.name = self.formatName(name=tibiaTipName)
        tibiaTipSpec.side = side
        tibiaTipSpec.type = self.Type.OTHER
        tibiaTipSpec.otherType = tibiaTipName
        tibiaTipSpec.drawStyle = self.Style.BOX
        tibiaTipSpec.defaultMatrix = self.__default_limb_matrices__[side][self.LimbType.TIBIA_TIP]
        tibiaTipSpec.driver.name = self.formatName(name=tibiaTipName, type='joint')

        # Call parent method
        #
        return super(InsectLegComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def connectExtremityToIKHandle(self, extremityComponent):
        """
        Adds the supplied extremity control to the limb's IK softener.

        :type extremityComponent: rigotron.component.extremity.ExtremityComponent
        :rtype: None
        """

        # Evaluate extremity component
        #
        isInsectFootComponent = extremityComponent.className.endswith('InsectFootComponent')

        if isInsectFootComponent:

            # Override reverse IK softener
            #
            extremityCtrl = extremityComponent.getPublishedNode('Foot_IK')

            limbIKSoftener = self.scene(self.userProperties['sikSoftener'])
            limbIKSoftener.connectPlugs(extremityCtrl[f'worldMatrix[{extremityCtrl.instanceNumber()}]'], 'endMatrix', force=True)

            # Override nested IK handles
            #
            extremityIKTarget = self.scene(extremityComponent.userProperties['ikTarget'])
            limbIKHandle = self.scene(self.userProperties['ikHandles'][-1])

            constraint = limbIKHandle.findConstraint('pointConstraint', exactType=True)
            constraint.clearTargets()
            constraint.addTarget(extremityIKTarget)

        else:

            # Call parent method
            #
            super(InsectLegComponent, self).connectExtremityToIKHandle(extremityComponent)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Decompose component
        #
        coxaSpec, femurSpec, tibiaSpec, tibiaTipSpec = self.skeletonSpecs()
        coxaExportJoint = self.scene(coxaSpec.uuid)
        femurExportJoint = self.scene(femurSpec.uuid)
        tibiaExportJoint = self.scene(tibiaSpec.uuid)
        tibiaTipExportJoint = self.scene(tibiaTipSpec.uuid)

        coxaEnabled = bool(coxaSpec.enabled)
        coxaExportMatrix = coxaExportJoint.worldMatrix() if coxaEnabled else om.MMatrix.kIdentity
        femurExportMatrix = femurExportJoint.worldMatrix()
        tibiaExportMatrix = tibiaExportJoint.worldMatrix()

        extremityMatrix = self.extremityMatrix()
        defaultTibiaTipMatrix = transformutils.createRotationMatrix(tibiaExportMatrix) * transformutils.createTranslateMatrix(extremityMatrix)
        tibiaTipMatrix = tibiaTipExportJoint.worldMatrix() if (tibiaTipExportJoint is not None) else defaultTibiaTipMatrix
        tibiaTipPoint = transformutils.breakMatrix(tibiaTipMatrix)[3]

        limbOrigin = transformutils.breakMatrix(coxaExportMatrix)[3]
        limbIKOrigin = transformutils.breakMatrix(femurExportMatrix)[3]
        hingePoint = transformutils.breakMatrix(tibiaExportMatrix)[3]
        effectorMatrix = self.effectorMatrix()
        limbIKGoal = transformutils.breakMatrix(effectorMatrix)[3]

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

        spineComponent = rootComponent.findComponentDescendants('SpineComponent')[0]
        cogCtrl = spineComponent.getPublishedNode('COG')
        waistCtrl = spineComponent.getPublishedNode('Waist')
        pelvisCtrl = spineComponent.getPublishedNode('Pelvis')

        # Validate export matrices
        # Make sure to push any changes back to their associated spec!
        #
        coxaDistance = om.MPoint(limbOrigin).distanceTo(limbIKOrigin)
        femurDistance = om.MPoint(limbIKOrigin).distanceTo(hingePoint)
        tibiaDistance = om.MPoint(hingePoint).distanceTo(tibiaTipPoint)
        tarsusDistance = om.MPoint(tibiaTipPoint).distanceTo(limbIKGoal)

        coxaForwardVector = om.MVector(limbIKOrigin - limbOrigin).normal()
        coxaRightVector = transformutils.breakMatrix(coxaExportMatrix, normalize=True)[2]
        coxaExportMatrix = transformutils.createAimMatrix(0, coxaForwardVector, 2, coxaRightVector, origin=limbOrigin)

        aimVector = om.MVector(tibiaTipPoint) - om.MVector(limbIKOrigin)
        forwardVector = aimVector.normal()
        rightVector = om.MVector(tibiaTipPoint - hingePoint).normal() ^ om.MVector(limbIKOrigin - hingePoint).normal()
        poleVector = (forwardVector ^ rightVector).normal()
        solution = kinematicutils.solveIk2BoneChain(limbIKOrigin, femurDistance, tibiaTipPoint, tibiaDistance, poleVector)

        coxaExportJoint.setWorldMatrix(coxaExportMatrix, skipScale=True)
        coxaSpec.cacheMatrix(delete=False)

        femurExportMatrix = om.MMatrix(solution[0])
        femurExportJoint.setWorldMatrix(femurExportMatrix, skipScale=True)
        femurSpec.cacheMatrix(delete=False)

        tibiaExportMatrix = om.MMatrix(solution[1])
        tibiaExportJoint.setWorldMatrix(tibiaExportMatrix, skipScale=True)
        tibiaSpec.cacheMatrix(delete=False)

        tibiaTipExportMatrix = om.MMatrix(solution[2])

        self.save()  # Pushes skeleton spec changes to user property buffer!

        # Create leg target
        #
        defaultLegMatrix = coxaExportMatrix if coxaEnabled else femurExportMatrix
        legMatrix = mirrorMatrix * defaultLegMatrix

        legTargetName = self.formatName(name='Leg', type='target')
        legTarget = self.scene.createNode('transform', name=legTargetName, parent=privateGroup)
        legTarget.setWorldMatrix(legMatrix)
        legTarget.freezeTransform()

        legTarget.addConstraint('transformConstraint', [waistCtrl], maintainOffset=True)
        
        # Create leg control
        #
        legSpaceName = self.formatName(type='space')
        legSpace = self.scene.createNode('transform', name=legSpaceName, parent=controlsGroup)
        legSpace.setWorldMatrix(legMatrix)
        legSpace.freezeTransform()

        legCtrlName = self.formatName(type='control')
        legCtrl = self.scene.createNode('transform', name=legCtrlName, parent=legSpace)
        legCtrl.addPointHelper('disc', 'axisView', size=(10.0 * rigScale), localScale=(0.0, 3.0, 3.0), colorRGB=colorRGB)
        legCtrl.addDivider('Settings')
        legCtrl.addAttr(longName='twist', attributeType='doubleAngle', keyable=True)
        legCtrl.addDivider('Spaces')
        legCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        legCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        legCtrl.prepareChannelBoxForAnimation()
        legCtrl.tagAsController()
        self.publishNode(legCtrl, alias='Leg')

        legSpaceSwitch = legSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, pelvisCtrl], weighted=True, maintainOffset=True)
        legSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 1.0, 1.0)}])
        legSpaceSwitch.connectPlugs(legCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
        legSpaceSwitch.connectPlugs(legCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')

        legCtrl.userProperties['space'] = legSpace.uuid()
        legCtrl.userProperties['spaceSwitch'] = legSpaceSwitch.uuid()

        # Create leg kinematic joints
        #
        legJointTypes = ('Femur', 'Tibia', 'TibiaTip')
        legKinematicTypes = ('FK', 'IK', 'Blend')

        legFKJoints = [None] * 3
        legIKJoints = [None] * 3
        legBlendJoints = [None] * 3
        legMatrices = (femurExportMatrix, tibiaExportMatrix, tibiaTipExportMatrix)
        legKinematicJoints = (legFKJoints, legIKJoints, legBlendJoints)

        for (i, kinematicType) in enumerate(legKinematicTypes):

            for (j, jointType) in enumerate(legJointTypes):

                parent = legKinematicJoints[i][j - 1] if j > 0 else jointsGroup

                jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                joint = self.scene.createNode('joint', name=jointName, parent=parent)
                joint.displayLocalAxis = True
                joint.setWorldMatrix(legMatrices[j])

                legKinematicJoints[i][j] = joint

        femurFKJoint, tibiaFKJoint, tibiaTipFKJoint = legFKJoints
        femurIKJoint, tibiaIKJoint, tibiaTipIKJoint = legIKJoints
        femurBlendJoint, tibiaBlendJoint, tibiaTipBlendJoint = legBlendJoints

        # Create leg switch control
        #
        switchCtrlName = self.formatName(subname='Switch', type='control')
        switchCtrl = self.scene.createNode('transform', name=switchCtrlName, parent=controlsGroup)
        switchCtrl.addPointHelper('pyramid', 'fill', 'shaded', size=(10.0 * rigScale), localPosition=(0.0, -25.0, 0.0), localRotate=(0.0, 0.0, 90.0), colorRGB=darkColorRGB)
        switchCtrl.addConstraint('transformConstraint', [tibiaTipBlendJoint])
        switchCtrl.addDivider('Settings')
        switchCtrl.addAttr(longName='length', attributeType='doubleLinear', array=True, hidden=True)
        switchCtrl.addAttr(longName='mode', niceName='Mode (FK/IK)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName='coxaOffset', attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName='femurOffset', attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName='tibiaOffset', attributeType='doubleLinear', keyable=True)
        switchCtrl.addAttr(longName='tarsusOffset', attributeType='doubleLinear', hidden=True)
        switchCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        switchCtrl.addAttr(longName='soften', attributeType='float', min=0.0, keyable=True)
        switchCtrl.addAttr(longName='twist', attributeType='doubleAngle', keyable=True)
        switchCtrl.hideAttr('translate', 'rotate', 'scale', lock=True)
        switchCtrl.hideAttr('visibility', lock=False)
        switchCtrl.tagAsController(parent=legCtrl)
        self.publishNode(switchCtrl, alias='Switch')

        limbLengths = (coxaDistance, femurDistance, tibiaDistance, tarsusDistance)
        switchCtrl.setAttr('length', limbLengths)
        switchCtrl.lockAttr('length')

        # Setup leg blends
        #
        blender = switchCtrl['mode']
        femurBlender = setuputils.createTransformBlends(femurFKJoint, femurIKJoint, femurBlendJoint, blender=blender)
        tibiaBlender = setuputils.createTransformBlends(tibiaFKJoint, tibiaIKJoint, tibiaBlendJoint, blender=blender)
        tibiaTipBlender = setuputils.createTransformBlends(tibiaTipFKJoint, tibiaTipIKJoint, tibiaTipBlendJoint, blender=blender)

        femurBlender.setName(self.formatName(subname='Femur', type='blendTransform'))
        tibiaBlender.setName(self.formatName(subname='Tibia', type='blendTransform'))
        tibiaTipBlender.setName(self.formatName(subname='TibiaTip', type='blendTransform'))

        # Setup leg length nodes
        #
        femurLengthName = self.formatName(name='Femur', subname='Length', type='plusMinusAverage')
        femurLength = self.scene.createNode('plusMinusAverage', name=femurLengthName)
        femurLength.setAttr('operation', 1)  # Addition
        femurLength.connectPlugs(switchCtrl['length[1]'], 'input1D[0]')
        femurLength.connectPlugs(switchCtrl['femurOffset'], 'input1D[1]')

        tibiaLengthName = self.formatName(name='Tibia', subname='Length', type='plusMinusAverage')
        tibiaLength = self.scene.createNode('plusMinusAverage', name=tibiaLengthName)
        tibiaLength.setAttr('operation', 1)  # Addition
        tibiaLength.connectPlugs(switchCtrl['length[2]'], 'input1D[0]')
        tibiaLength.connectPlugs(switchCtrl['tibiaOffset'], 'input1D[1]')

        tarsusLengthName = self.formatName(name='Tarsus', subname='Length', type='plusMinusAverage')
        tarsusLength = self.scene.createNode('plusMinusAverage', name=tarsusLengthName)
        tarsusLength.setAttr('operation', 1)  # Addition
        tarsusLength.connectPlugs(switchCtrl['length[3]'], 'input1D[0]')
        tarsusLength.connectPlugs(switchCtrl['tarsusOffset'], 'input1D[1]')

        legLengthName = self.formatName(name='Leg', subname='Length', type='plusMinusAverage')
        legLength = self.scene.createNode('plusMinusAverage', name=legLengthName)
        legLength.setAttr('operation', 1)  # Addition
        legLength.connectPlugs(femurLength['output1D'], 'input1D[1]')
        legLength.connectPlugs(tibiaLength['output1D'], 'input1D[2]')
        legLength.connectPlugs(tarsusLength['output1D'], 'input1D[3]')

        femurWeightName = self.formatName(name='Femur', subname='Weight', type='floatMath')
        femurWeight = self.scene.createNode('floatMath', name=femurWeightName)
        femurWeight.operation = 3  # Divide
        femurWeight.connectPlugs(femurLength['output1D'], 'inFloatA')
        femurWeight.connectPlugs(legLength['output1D'], 'inFloatB')

        tibiaWeightName = self.formatName(name='Tibia', subname='Weight', type='floatMath')
        tibiaWeight = self.scene.createNode('floatMath', name=tibiaWeightName)
        tibiaWeight.operation = 3  # Divide
        tibiaWeight.connectPlugs(tibiaLength['output1D'], 'inFloatA')
        tibiaWeight.connectPlugs(legLength['output1D'], 'inFloatB')

        # Create coxa components
        #
        coxaRotSpace, coxaRotSpaceSwitch, coxaRotCtrl, coxaTransCtrl = None, None, None, None

        coxaLength, coxaInverseLength, coxaWeight = None, None, None

        coxaFKJoint, coxaTipFKJoint = None, None
        coxaIKJoint, coxaTipIKJoint = None, None
        coxaBlendJoint, coxaTipBlendJoint = None, None

        if coxaEnabled:

            # Create coxa length nodes
            #
            coxaLengthName = self.formatName(name='Coxa', subname='Length', type='plusMinusAverage')
            coxaLength = self.scene.createNode('plusMinusAverage', name=coxaLengthName)
            coxaLength.setAttr('operation', 1)  # Addition
            coxaLength.connectPlugs(switchCtrl['length[0]'], 'input1D[0]')
            coxaLength.connectPlugs(switchCtrl['coxaOffset'], 'input1D[1]')

            coxaWeightName = self.formatName(name='Coxa', subname='Weight', type='floatMath')
            coxaWeight = self.scene.createNode('floatMath', name=coxaWeightName)
            coxaWeight.operation = 3  # Divide
            coxaWeight.connectPlugs(coxaLength['output1D'], 'inFloatA')
            coxaWeight.connectPlugs(legLength['output1D'], 'inFloatB')

            legLength.connectPlugs(coxaLength['output1D'], 'input1D[0]')

            # Create coxa controls
            #
            femurRotMatrix = mirrorMatrix * coxaExportMatrix

            coxaRotSpaceName = self.formatName(name='Coxa', subname='Rot', type='space')
            coxaRotSpace = self.scene.createNode('transform', name=coxaRotSpaceName, parent=controlsGroup)
            coxaRotSpace.setWorldMatrix(femurRotMatrix, skipScale=True)
            coxaRotSpace.freezeTransform()

            coxaRotCtrlName = self.formatName(name='Coxa', subname='Rot', type='control')
            coxaRotCtrl = self.scene.createNode('transform', name=coxaRotCtrlName, parent=coxaRotSpace)
            coxaRotCtrl.addDivider('Spaces')
            coxaRotCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            coxaRotCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            coxaRotCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            coxaRotCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            coxaRotCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (Leg)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            coxaRotCtrl.prepareChannelBoxForAnimation()
            self.publishNode(coxaRotCtrl, alias='Coxa_Rot')

            coxaTipExportMatrix = transformutils.createRotationMatrix(coxaExportMatrix) * transformutils.createTranslateMatrix(femurExportMatrix)

            coxaTransCtrlName = self.formatName(name='Coxa', subname='Trans', type='control')
            coxaTransCtrl = self.scene.createNode('transform', name=coxaTransCtrlName, parent=coxaRotCtrl)
            coxaTransCtrl.addPointHelper('cross', size=(15 * rigScale), lineWidth=2.0, colorRGB=darkColorRGB)
            coxaTransCtrl.addDivider('Settings')
            coxaTransCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            coxaTransCtrl.prepareChannelBoxForAnimation()
            self.publishNode(coxaTransCtrl, alias='Coxa_Trans')

            coxaTransComposeMatrixName = self.formatName(name='Coxa', subname='Trans', type='composeMatrix')
            coxaTransComposeMatrix = self.scene.createNode('composeMatrix', name=coxaTransComposeMatrixName)
            coxaTransComposeMatrix.connectPlugs(coxaLength['output1D'], 'inputTranslateX')
            coxaTransComposeMatrix.connectPlugs('outputMatrix', coxaTransCtrl['offsetParentMatrix'])

            if requiresMirroring:

                coxaInverseLengthName = self.formatName(name='Coxa', subname='InverseLength', type='floatMath')
                coxaInverseLength = self.scene.createNode('floatMath', name=coxaInverseLengthName)
                coxaInverseLength.operation = 5  # Negate
                coxaInverseLength.connectPlugs(coxaLength['output1D'], 'inFloatA')
                coxaInverseLength.connectPlugs('outFloat', coxaTransComposeMatrix['inputTranslateX'], force=True)

            coxaRotSpaceSwitch = coxaRotSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, pelvisCtrl, legCtrl], weighted=True, maintainOffset=True)
            coxaRotSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 0.0, 1.0)}])
            coxaRotSpaceSwitch.connectPlugs(coxaRotCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            coxaRotSpaceSwitch.connectPlugs(coxaRotCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            coxaRotSpaceSwitch.connectPlugs(coxaRotCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            coxaRotSpaceSwitch.connectPlugs(coxaRotCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            coxaRotSpaceSwitch.connectPlugs(coxaRotCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')

            coxaIKRotShape = coxaRotCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=colorRGB)
            coxaIKRotShape.reorientAndScaleToFit(coxaTransCtrl)

            coxaRotCtrl.tagAsController(parent=legCtrl, children=[coxaTransCtrl])
            coxaTransCtrl.tagAsController(parent=coxaRotCtrl)

            # Create coxa kinematic joints
            #
            coxaJointTypes = ('Coxa', 'CoxaTip')
            coxaKinematicTypes = ('FK', 'IK', 'Blend')

            coxaFKJoints = [None] * 2
            coxaIKJoints = [None] * 2
            coxaBlendJoints = [None] * 2
            coxaMatrices = (coxaExportMatrix, coxaTipExportMatrix)
            coxaKinematicJoints = (coxaFKJoints, coxaIKJoints, coxaBlendJoints)

            for (i, kinematicType) in enumerate(coxaKinematicTypes):

                for (j, jointType) in enumerate(coxaJointTypes):

                    parent = coxaKinematicJoints[i][j - 1] if j > 0 else jointsGroup

                    jointName = self.formatName(subname=jointType, kinemat=kinematicType, type='joint')
                    joint = self.scene.createNode('joint', name=jointName, parent=parent)
                    joint.displayLocalAxis = True
                    joint.setWorldMatrix(coxaMatrices[j])

                    coxaKinematicJoints[i][j] = joint

            coxaFKJoint, coxaTipFKJoint = coxaFKJoints
            coxaIKJoint, coxaTipIKJoint = coxaIKJoints
            coxaBlendJoint, coxaTipBlendJoint = coxaBlendJoints

            # Setup coxa blends
            #
            coxaBlender = setuputils.createTransformBlends(coxaFKJoint, coxaIKJoint, coxaBlendJoint, blender=blender)
            coxaBlender.setName(self.formatName(subname='Coxa', type='blendTransform'))

            coxaTipBlender = setuputils.createTransformBlends(coxaTipFKJoint, coxaTipIKJoint, coxaTipBlendJoint, blender=blender)
            coxaTipBlender.setName(self.formatName(subname='CoxaTip', type='blendTransform'))

            # Constrain coxa FK joints
            #
            coxaFKJoint.addConstraint('transformConstraint', [coxaRotCtrl], maintainOffset=requiresMirroring)
            coxaTipFKJoint.addConstraint('transformConstraint', [coxaTransCtrl], maintainOffset=requiresMirroring)

            # Add single-chain solver to coxa IK joints
            #
            coxaIKJoint.addConstraint('transformConstraint', [coxaRotCtrl], skipRotate=True)
            coxaIKJoint.connectPlugs('scale', coxaTipIKJoint['scale'])

            coxaIKHandle, coxaIKEffector = kinematicutils.applySingleChainSolver(coxaIKJoint, coxaTipIKJoint)
            coxaIKHandle.setName(self.formatName(name='Leg', subname='Coxa', kinemat='SC', type='ikHandle'))
            coxaIKHandle.setParent(privateGroup)
            coxaIKHandle.addConstraint('transformConstraint', [coxaTransCtrl], maintainOffset=requiresMirroring)
            coxaIKEffector.setName(self.formatName(name='Leg', subname='Coxa', kinemat='SC', type='ikEffector'))

            # Setup coxa IK stretch
            #
            coxaIKDistanceMultMatrixName = self.formatName(name='Coxa', subname='Distance', kinemat='IK', type='multMatrix')
            coxaIKDistanceMultMatrix = self.scene.createNode('multMatrix', name=coxaIKDistanceMultMatrixName)
            coxaIKDistanceMultMatrix.connectPlugs(coxaTransCtrl[f'worldMatrix[{coxaTransCtrl.instanceNumber()}]'], 'matrixIn[0]')
            coxaIKDistanceMultMatrix.connectPlugs(coxaRotCtrl[f'worldInverseMatrix[{coxaRotCtrl.instanceNumber()}]'], 'matrixIn[1]')

            coxaIKDistanceBetweenName = self.formatName(name='Coxa', subname='Distance', kinemat='IK', type='distanceBetween')
            coxaIKDistanceBetween = self.scene.createNode('distanceBetween', name=coxaIKDistanceBetweenName)
            coxaIKDistanceBetween.connectPlugs(coxaIKDistanceMultMatrix['matrixSum'], 'inMatrix2')

            coxaIKScaleName = self.formatName(name='Coxa', subname='Scale', kinemat='IK', type='divDoubleLinear')
            coxaIKScale = self.scene.createNode('divDoubleLinear', name=coxaIKScaleName)
            coxaIKScale.connectPlugs(coxaIKDistanceBetween['distance'], 'input1')
            coxaIKScale.connectPlugs(coxaLength['output1D'], 'input2')

            coxaIKStretchName = self.formatName(name='Coxa', subname='Stretch', kinemat='IK', type='multDoubleLinear')
            coxaIKStretch = self.scene.createNode('multDoubleLinear', name=coxaIKStretchName)
            coxaIKStretch.connectPlugs(coxaLength['output1D'], 'input1')
            coxaIKStretch.connectPlugs(coxaIKScale['output'], 'input2')

            coxaIKEnvelopeName = self.formatName(name='Coxa', kinemat='IK', subname='Envelope', type='blendTwoAttr')
            coxaIKEnvelope = self.scene.createNode('blendTwoAttr', name=coxaIKEnvelopeName)
            coxaIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
            coxaIKEnvelope.connectPlugs(coxaLength['output1D'], 'input[0]')
            coxaIKEnvelope.connectPlugs(coxaIKStretch['output'], 'input[1]')
            coxaIKEnvelope.connectPlugs('output', coxaTipIKJoint['translateX'])

        # Create leg FK controls
        #
        femurFKMatrix = mirrorMatrix * femurExportMatrix

        femurFKSpaceName = self.formatName(name='Femur', kinemat='FK', type='space')
        femurFKSpace = self.scene.createNode('transform', name=femurFKSpaceName, parent=controlsGroup)
        femurFKSpace.setWorldMatrix(femurFKMatrix, skipScale=True)
        femurFKSpace.freezeTransform()

        femurFKCtrlName = self.formatName(name='Femur', kinemat='FK', type='control')
        femurFKCtrl = self.scene.createNode('transform', name=femurFKCtrlName, parent=femurFKSpace)
        femurFKCtrl.addDivider('Spaces')
        femurFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        femurFKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(femurFKCtrl, alias='Femur_FK')

        femurFKTarget = coxaTransCtrl if coxaEnabled else legCtrl

        femurFKSpaceSwitch = femurFKSpace.addSpaceSwitch([femurFKTarget, motionCtrl], maintainOffset=True)
        femurFKSpaceSwitch.weighted = True
        femurFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        femurFKSpaceSwitch.connectPlugs(femurFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        femurFKSpaceSwitch.connectPlugs(femurFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

        tibiaFKMatrix = mirrorMatrix * tibiaExportMatrix

        tibiaFKTargetName = self.formatName(name='Tibia', kinemat='FK', type='target')
        tibiaFKTarget = self.scene.createNode('transform', name=tibiaFKTargetName, parent=femurFKCtrl)
        tibiaFKTarget.displayLocalAxis = True
        tibiaFKTarget.visibility = False
        tibiaFKTarget.lock()

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(tibiaFKMatrix * femurFKMatrix.inverse())
        tibiaFKComposeMatrixName = self.formatName(name='Tibia', kinemat='FK', type='composeMatrix')
        tibiaFKComposeMatrix = self.scene.createNode('composeMatrix', name=tibiaFKComposeMatrixName)
        tibiaFKComposeMatrix.setAttr('inputTranslate', translation)
        tibiaFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        tibiaFKComposeMatrix.connectPlugs(femurLength['output1D'], 'inputTranslateX')
        tibiaFKComposeMatrix.connectPlugs('outputMatrix', tibiaFKTarget['offsetParentMatrix'])

        femurInverseLength = None

        if requiresMirroring:

            femurInverseLengthName = self.formatName(name='Femur', subname='InverseLength', type='floatMath')
            femurInverseLength = self.scene.createNode('floatMath', name=femurInverseLengthName)
            femurInverseLength.operation = 5  # Negate
            femurInverseLength.connectPlugs(femurLength['output1D'], 'inFloatA')
            femurInverseLength.connectPlugs('outFloat', tibiaFKComposeMatrix['inputTranslateX'], force=True)

        tibiaFKSpaceName = self.formatName(name='Tibia', kinemat='FK', type='space')
        tibiaFKSpace = self.scene.createNode('transform', name=tibiaFKSpaceName, parent=controlsGroup)
        tibiaFKSpace.setWorldMatrix(tibiaFKMatrix, skipScale=True)
        tibiaFKSpace.freezeTransform()

        tibiaFKCtrlName = self.formatName(name='Tibia', kinemat='FK', type='control')
        tibiaFKCtrl = self.scene.createNode('transform', name=tibiaFKCtrlName, parent=tibiaFKSpace)
        tibiaFKCtrl.addDivider('Spaces')
        tibiaFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        tibiaFKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(tibiaFKCtrl, alias='Tibia_FK')

        tibiaFKSpaceSwitch = tibiaFKSpace.addSpaceSwitch([tibiaFKTarget, motionCtrl], weighted=True, maintainOffset=True)
        tibiaFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        tibiaFKSpaceSwitch.connectPlugs(tibiaFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        tibiaFKSpaceSwitch.connectPlugs(tibiaFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

        tibiaFKAimMatrixName = self.formatName(name='Tibia', subname='WorldSpace', kinemat='FK', type='aimMatrix')
        tibiaFKAimMatrix = self.scene.createNode('aimMatrix', name=tibiaFKAimMatrixName)
        tibiaFKAimMatrix.connectPlugs(tibiaFKTarget[f'worldMatrix[{tibiaFKTarget.instanceNumber()}]'], 'inputMatrix')
        tibiaFKAimMatrix.primaryInputAxis = (0.0, 0.0, 1.0)
        tibiaFKAimMatrix.primaryMode = 2  # Align
        tibiaFKAimMatrix.primaryTargetVector = (0.0, 0.0, 1.0)
        tibiaFKAimMatrix.connectPlugs(tibiaFKTarget[f'worldMatrix[{tibiaFKTarget.instanceNumber()}]'], 'primaryTargetMatrix')
        tibiaFKAimMatrix.secondaryInputAxis = (0.0, 1.0, 0.0)
        tibiaFKAimMatrix.secondaryMode = 2  # Align
        tibiaFKAimMatrix.secondaryTargetVector = (0.0, 0.0, -1.0)
        tibiaFKAimMatrix.connectPlugs(motionCtrl[f'worldMatrix[{motionCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')

        tibiaFKSpaceSwitch.replaceTarget(1, tibiaFKAimMatrix, maintainOffset=True)

        tibiaTipFKTargetName = self.formatName(name='TibiaTip', kinemat='FK', type='target')
        tibiaTipFKTarget = self.scene.createNode('transform', name=tibiaTipFKTargetName, parent=tibiaFKCtrl)
        tibiaTipFKTarget.displayLocalAxis = True
        tibiaTipFKTarget.visibility = False
        tibiaTipFKTarget.lock()

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(tibiaTipMatrix * tibiaExportMatrix.inverse())
        tibiaTipFKComposeMatrixName = self.formatName(name='TibiaTip', kinemat='FK', type='composeMatrix')
        tibiaTipFKComposeMatrix = self.scene.createNode('composeMatrix', name=tibiaTipFKComposeMatrixName)
        tibiaTipFKComposeMatrix.setAttr('inputTranslate', translation)
        tibiaTipFKComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)
        tibiaTipFKComposeMatrix.connectPlugs(tibiaLength['output1D'], 'inputTranslateX')
        tibiaTipFKComposeMatrix.connectPlugs('outputMatrix', tibiaTipFKTarget['offsetParentMatrix'])

        tibiaInverseLength = None

        if requiresMirroring:
            
            tibiaInverseLengthName = self.formatName(name='Tibia', subname='InverseLength', type='floatMath')
            tibiaInverseLength = self.scene.createNode('floatMath', name=tibiaInverseLengthName)
            tibiaInverseLength.operation = 5  # Negate
            tibiaInverseLength.connectPlugs(tibiaLength['output1D'], 'inFloatA')
            tibiaInverseLength.connectPlugs('outFloat', tibiaTipFKComposeMatrix['inputTranslateX'], force=True)

        femurFKJoint.addConstraint('transformConstraint', [femurFKCtrl], maintainOffset=requiresMirroring)
        tibiaFKJoint.addConstraint('transformConstraint', [tibiaFKCtrl], maintainOffset=requiresMirroring)
        tibiaTipFKJoint.addConstraint('transformConstraint', [tibiaTipFKTarget], maintainOffset=requiresMirroring)

        # Add FK control shapes
        #
        femurFKShape = femurFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        femurFKShape.reorientAndScaleToFit(tibiaFKCtrl)

        tibiaFKShape = tibiaFKCtrl.addPointHelper('cylinder', size=(15.0 * rigScale), lineWidth=2.0, colorRGB=lightColorRGB)
        tibiaFKShape.reorientAndScaleToFit(tibiaTipFKTarget)

        supportsResizing = int(mc.about(version=True)) >= 2025

        if supportsResizing:

            # Setup femur FK shape resizing
            #
            femurHalfLengthName = self.formatName(name='Femur', subname='HalfLength', type='floatMath')
            femurHalfLength = self.scene.createNode('floatMath', name=femurHalfLengthName)
            femurHalfLength.operation = 6  # Half
            femurHalfLength.connectPlugs(femurLength['output1D'], 'inFloatA')
            femurHalfLength.connectPlugs('outFloat', femurFKShape['localPositionX'])

            if requiresMirroring:

                femurInverseLength.connectPlugs('outFloat', femurHalfLength['inFloatA'], force=True)

            femurScaleLengthName = self.formatName(name='Femur', subname='ScaleLength', type='divDoubleLinear')
            femurScaleLength = self.scene.createNode('divDoubleLinear', name=femurScaleLengthName)
            femurScaleLength.connectPlugs(femurLength['output1D'], 'input1')
            femurScaleLength.connectPlugs(femurFKShape['size'], 'input2')
            femurScaleLength.connectPlugs('output', femurFKShape['localScaleX'])

            # Setup tibia FK shape resizing
            #
            tibiaHalfLengthName = self.formatName(name='Tibia', subname='HalfLength', type='floatMath')
            tibiaHalfLength = self.scene.createNode('floatMath', name=tibiaHalfLengthName)
            tibiaHalfLength.operation = 6  # Half
            tibiaHalfLength.connectPlugs(tibiaLength['output1D'], 'inFloatA')
            tibiaHalfLength.connectPlugs('outFloat', tibiaFKShape['localPositionX'])

            if requiresMirroring:

                tibiaInverseLength.connectPlugs('outFloat', tibiaHalfLength['inFloatA'], force=True)

            tibiaScaleLengthName = self.formatName(name='Tibia', subname='ScaleLength', type='divDoubleLinear')
            tibiaScaleLength = self.scene.createNode('divDoubleLinear', name=tibiaScaleLengthName)
            tibiaScaleLength.connectPlugs(tibiaLength['output1D'], 'input1')
            tibiaScaleLength.connectPlugs(tibiaFKShape['size'], 'input2')
            tibiaScaleLength.connectPlugs('output', tibiaFKShape['localScaleX'])

        else:

            log.debug('Skipping dynamic FK shape resizing...')

        # Tag FK controls
        #
        femurFKCtrl.tagAsController(parent=coxaTransCtrl, children=[tibiaFKCtrl])
        tibiaFKCtrl.tagAsController(parent=femurFKCtrl)

        # Create extremity IK control
        #
        extremityIKSpaceName = self.formatName(name='Leg', kinemat='IK', type='space')
        extremityIKSpace = self.scene.createNode('transform', name=extremityIKSpaceName, parent=controlsGroup)
        extremityIKSpace.setWorldMatrix(effectorMatrix, skipRotate=True)
        extremityIKSpace.freezeTransform()

        extremityIKCtrlName = self.formatName(name='Leg', kinemat='IK', type='control')
        extremityIKCtrl = self.scene.createNode('transform', name=extremityIKCtrlName, parent=extremityIKSpace)
        extremityIKCtrl.addPointHelper('disc', 'notch', size=(30.0 * rigScale), localRotate=(0.0, 90.0, -90.0), lineWidth=3.0, colorRGB=colorRGB)
        extremityIKCtrl.addDivider('Settings')
        extremityIKCtrl.addAttr(longName='twist', attributeType='doubleAngle', keyable=True)
        extremityIKCtrl.addDivider('Spaces')
        extremityIKCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (Leg)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (Leg)', attributeType='float', min=0.0, max=1.0, keyable=True)
        extremityIKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(extremityIKCtrl, alias='Leg_IK')

        extremityIKSpaceSwitch = extremityIKSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, pelvisCtrl, legCtrl], maintainOffset=True)
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

        extremityIKCtrl.tagAsController(parent=legCtrl)

        # Create PV follow system
        #
        legIKHandleTargetName = self.formatName(name='Leg', kinemat='IK', type='target')
        legIKHandleTarget = self.scene.createNode('transform', name=legIKHandleTargetName, parent=privateGroup)
        legIKHandleTarget.displayLocalAxis = True
        legIKHandleTarget.visibility = False
        legIKHandleTarget.setWorldMatrix(effectorMatrix, skipRotate=True, skipScale=True)

        legReverseStretchName = self.formatName(name='Leg', subname='Stretch', type='revDoubleLinear')
        legReverseStretch = self.scene.createNode('revDoubleLinear', name=legReverseStretchName)
        legReverseStretch.connectPlugs(switchCtrl['stretch'], 'input')

        legIKSoftenerName = self.formatName(name='Leg', kinemat='IK', type='ikSoftener')
        legIKSoftener = self.scene.createNode('ikSoftener', name=legIKSoftenerName)
        legIKSoftener.chainScaleCompensate = True
        legIKSoftener.connectPlugs(switchCtrl['soften'], 'radius')
        legIKSoftener.connectPlugs(legReverseStretch['output'], 'envelope')
        legIKSoftener.connectPlugs(legLength['output1D'], 'chainLength')
        legIKSoftener.connectPlugs(legCtrl[f'worldMatrix[{legCtrl.instanceNumber()}]'], 'startMatrix')
        legIKSoftener.connectPlugs(extremityIKCtrl[f'worldMatrix[{extremityIKCtrl.instanceNumber()}]'], 'endMatrix')
        legIKSoftener.connectPlugs(legIKHandleTarget[f'parentInverseMatrix[{legIKHandleTarget.instanceNumber()}]'], 'parentInverseMatrix')
        legIKSoftener.connectPlugs('outPosition', legIKHandleTarget['translate'])

        followJointName = self.formatName(name='Leg', subname='Follow', type='joint')
        followJoint = self.scene.createNode('joint', name=followJointName, parent=jointsGroup)
        followJoint.addConstraint('pointConstraint', [legCtrl])

        followTipJointName = self.formatName(name='Leg', subname='FollowTip', type='joint')
        followTipJoint = self.scene.createNode('joint', name=followTipJointName, parent=followJoint)
        followTipJoint.connectPlugs(legIKSoftener['softDistance'], followTipJoint['translateX'])
        followTipJoint.connectPlugs(followJoint['scale'], 'scale')

        followHalfLengthName = self.formatName(name='Leg', subname='HalfFollow', type='floatMath')
        followHalfLength = self.scene.createNode('floatMath', name=followHalfLengthName)
        followHalfLength.operation = 6  # Half
        followHalfLength.connectPlugs(followTipJoint['translateX'], 'inDistanceA')

        followTargetName = self.formatName(name='Leg', subname='Follow', type='target')
        followTarget = self.scene.createNode('transform', name=followTargetName, parent=followJoint)
        followTarget.displayLocalAxis = True
        followTarget.connectPlugs(followHalfLength['outDistance'], 'translateX')
        followTarget.addConstraint('scaleConstraint', [legCtrl])

        forwardVectorMultMatrixName = self.formatName(name='Leg', subname='Forward', type='multiplyVectorByMatrix')
        forwardVectorMultMatrix = self.scene.createNode('multiplyVectorByMatrix', name=forwardVectorMultMatrixName)
        forwardVectorMultMatrix.connectPlugs(legIKSoftener['outWorldVector'], 'input')
        forwardVectorMultMatrix.connectPlugs(waistCtrl[f'worldInverseMatrix[{waistCtrl.instanceNumber()}]'], 'matrix')

        defaultSampleInput = forwardVectorMultMatrix.getAttr('output')
        defaultSampleOutput = -poleVector * waistCtrl.worldInverseMatrix()
        followSamples = list(self.__default_rbf_samples__[componentSide])

        followRBFSolverName = self.formatName(name='Leg', subname='Follow', type='rbfSolver')
        followRBFSolver = self.scene.createNode('rbfSolver', name=followRBFSolverName)
        followRBFSolver.inputType = 0  # Euclidean
        followRBFSolver.function = 1  # Gaussian
        followRBFSolver.radius = 0.1
        followRBFSolver.setAttr('sample[0]', {'sampleName': 'Default', 'sampleInputTranslate': defaultSampleInput, 'sampleOutputTranslate': -defaultSampleOutput})
        followRBFSolver.setAttr('sample[1]', followSamples[0])
        followRBFSolver.setAttr('sample[2]', followSamples[1])
        followRBFSolver.setAttr('sample[3]', followSamples[2])
        followRBFSolver.setAttr('sample[4]', followSamples[3])
        followRBFSolver.setAttr('sample[5]', followSamples[4])
        followRBFSolver.setAttr('sample[6]', followSamples[5])
        followRBFSolver.connectPlugs(forwardVectorMultMatrix['output'], 'inputTranslate')

        followUpVectorMultMatrixName = self.formatName(name='Leg', subname='Follow', type='multiplyVectorByMatrix')
        followUpVectorMultMatrix = self.scene.createNode('multiplyVectorByMatrix', name=followUpVectorMultMatrixName)
        followUpVectorMultMatrix.connectPlugs(followRBFSolver['outputTranslate'], 'input')
        followUpVectorMultMatrix.connectPlugs(waistCtrl[f'worldMatrix[{waistCtrl.instanceNumber()}]'], 'matrix')

        followConstraint = followJoint.addConstraint('aimConstraint', [legIKHandleTarget], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, -1.0, 0.0), worldUpType=3, worldUpVector=(0.0, 1.0, 0.0))
        followConstraint.connectPlugs(followUpVectorMultMatrix['output'], 'worldUpVector')

        # Append follow space to coxa control
        #
        if coxaEnabled:

            index = coxaRotSpaceSwitch.addTarget(followJoint, maintainOffset=True)
            coxaRotCtrl.addAttr(longName=f'rotationSpaceW{index}', niceName='Rotation Space (Follow)', attributeType='float', min=0.0, max=1.0, keyable=True)

            coxaRotSpaceSwitch.setAttr(f'target[{index}].targetWeight', (0.0, 0.0, 0.0))
            coxaRotSpaceSwitch.connectPlugs(coxaRotCtrl[f'rotationSpaceW{index}'], f'target[{index}].targetRotateWeight')

        # Calculate spring IK matrices
        #
        springForwardVector = om.MVector(limbIKGoal - limbIKOrigin).normal()
        springUpVector = (transformutils.breakMatrix(effectorMatrix, normalize=True)[2] ^ springForwardVector).normal()
        springRightVector = (springForwardVector ^ springUpVector).normal()

        tarsusForwardVector = om.MVector(tibiaTipPoint - limbIKGoal).normal()
        tarsusProjectedForwardVector = transformutils.projectVector(tarsusForwardVector, springRightVector).normal()
        tarsusProjectedPoint = limbIKGoal + (tarsusProjectedForwardVector * tarsusDistance)

        springPoleVector = -((transformutils.breakMatrix(femurExportMatrix, normalize=True)[1] * 0.5) + (transformutils.breakMatrix(tibiaExportMatrix, normalize=True)[1] * 0.5)).normal()
        springProjectedPoleVector = transformutils.projectVector(springPoleVector, springRightVector)
        femurSpringMatrix, tibiaSpringMatrix, tibiaTipSpringMatrix = kinematicutils.solveIk2BoneChain(limbIKOrigin, femurDistance, tarsusProjectedPoint, tibiaDistance, springProjectedPoleVector)

        tarsusSpringMatrix = transformutils.createAimMatrix(0, -tarsusProjectedForwardVector, 2, springRightVector, origin=tarsusProjectedPoint)
        tarsusTipSpringMatrix = transformutils.createAimMatrix(0, -tarsusProjectedForwardVector, 2, springRightVector, origin=limbIKGoal)

        # Create spring IK joints from matrices
        #
        legSIKPairs = {
            'Femur': femurSpringMatrix,
            'Tibia': tibiaSpringMatrix,
            'Tarsus': tarsusSpringMatrix,
            'TarsusTip': tarsusTipSpringMatrix
        }

        legSIKJoints = [None] * 4

        for (i, (subname, matrix)) in enumerate(legSIKPairs.items()):

            parent = legSIKJoints[i - 1] if (i > 0) else jointsGroup

            jointName = self.formatName(name='Leg', subname=subname, kinemat='SIK', type='joint')
            joint = self.scene.createNode('joint', name=jointName, parent=parent)
            joint.setWorldMatrix(matrix, skipScale=True)

            legSIKJoints[i] = joint

        femurSIKJoint, tibiaSIKJoint, tarsusSIKJoint, tarsusTipSIKJoint = legSIKJoints

        femurSIKJoint.addConstraint('transformConstraint', [coxaTipIKJoint], skipRotate=True)
        femurSIKJoint.connectPlugs('scale', tibiaSIKJoint['scale'])
        tibiaSIKJoint.connectPlugs('scale', tarsusSIKJoint['scale'])
        tarsusSIKJoint.connectPlugs('scale', tarsusTipSIKJoint['scale'])

        # Apply spring IK solver
        #
        legSIKLengthName = self.formatName(subname='Length', kinemat='SIK', type='plusMinusAverage')
        legSIKLength = self.scene.createNode('plusMinusAverage', name=legSIKLengthName)
        legSIKLength.setAttr('operation', 1)  # Addition
        legSIKLength.connectPlugs(femurLength['output1D'], 'input1D[0]')
        legSIKLength.connectPlugs(tibiaLength['output1D'], 'input1D[1]')
        legSIKLength.connectPlugs(tarsusLength['output1D'], 'input1D[2]')

        legSIKHandleTargetName = self.formatName(kinemat='SIK', type='target')
        legSIKHandleTarget = self.scene.createNode('transform', name=legSIKHandleTargetName, parent=privateGroup)
        legSIKHandleTarget.displayLocalAxis = True
        legSIKHandleTarget.visibility = False
        legSIKHandleTarget.setWorldMatrix(effectorMatrix, skipRotate=True, skipScale=True)

        legSIKSoftenerName = self.formatName(kinemat='SIK', type='ikSoftener')
        legSIKSoftener = self.scene.createNode('ikSoftener', name=legSIKSoftenerName)
        legSIKSoftener.chainScaleCompensate = True
        legSIKSoftener.connectPlugs(switchCtrl['soften'], 'radius')
        legSIKSoftener.connectPlugs(legReverseStretch['output'], 'envelope')
        legSIKSoftener.connectPlugs(legSIKLength['output1D'], 'chainLength')
        legSIKSoftener.connectPlugs(coxaTransCtrl[f'worldMatrix[{coxaTransCtrl.instanceNumber()}]'], 'startMatrix')
        legSIKSoftener.connectPlugs(extremityIKCtrl[f'worldMatrix[{extremityIKCtrl.instanceNumber()}]'], 'endMatrix')
        legSIKSoftener.connectPlugs(legSIKHandleTarget[f'parentInverseMatrix[{legSIKHandleTarget.instanceNumber()}]'], 'parentInverseMatrix')
        legSIKSoftener.connectPlugs('outPosition', legSIKHandleTarget['translate'])

        legSIKHandle, legSIKEffector = kinematicutils.applySpringSolver(femurSIKJoint, tarsusTipSIKJoint)
        legSIKHandle.setName(self.formatName(subname='Spring', type='ikHandle'))
        legSIKHandle.setParent(privateGroup)
        legSIKEffector.setName(self.formatName(subname='Spring', type='ikEffector'))

        legSIKHandle.addConstraint('pointConstraint', [legSIKHandleTarget])
        legSIKHandle.connectPlugs(followUpVectorMultMatrix['output'], 'poleVector')

        legTwistSumName = self.formatName(subname='Twist', kinemat='SIK', type='arrayMath')
        legTwistSum = self.scene.createNode('arrayMath', name=legTwistSumName)
        legTwistSum.connectPlugs(legCtrl['twist'], 'inAngle[0].inAngleX')
        legTwistSum.connectPlugs(switchCtrl['twist'], 'inAngle[1].inAngleX')
        legTwistSum.connectPlugs(extremityIKCtrl['twist'], 'inAngle[2].inAngleX')
        legTwistSum.connectPlugs('outAngle.outAngleX', legSIKHandle['twist'])

        # Apply rotation-plain IK solver to remaining chain
        #
        legIKHandle, legIKEffector = kinematicutils.applyRotationPlaneSolver(femurIKJoint, tibiaTipIKJoint)
        legIKHandle.setName(self.formatName(type='ikHandle'))
        legIKHandle.setParent(privateGroup)
        legIKHandle.addConstraint('pointConstraint', [tarsusSIKJoint])
        legIKEffector.setName(self.formatName(type='ikEffector'))

        femurIKJoint.addConstraint('transformConstraint', [coxaTipIKJoint], skipRotate=True)
        femurIKJoint.connectPlugs('scale', tibiaIKJoint['scale'])
        tibiaIKJoint.connectPlugs('scale', tibiaTipIKJoint['scale'])

        # Setup stretch on spring IK joints
        #
        femurSIKStretchName = self.formatName(name='Femur', kinemat='SIK', subname='Stretch', type='multDoubleLinear')
        femurSIKStretch = self.scene.createNode('multDoubleLinear', name=femurSIKStretchName)
        femurSIKStretch.connectPlugs(femurLength['output1D'], 'input1')
        femurSIKStretch.connectPlugs(legSIKSoftener['softScale'], 'input2')

        femurSIKEnvelopeName = self.formatName(name='Femur', kinemat='SIK', subname='Envelope', type='blendTwoAttr')
        femurSIKEnvelope = self.scene.createNode('blendTwoAttr', name=femurSIKEnvelopeName)
        femurSIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        femurSIKEnvelope.connectPlugs(femurLength['output1D'], 'input[0]')
        femurSIKEnvelope.connectPlugs(femurSIKStretch['output'], 'input[1]')
        femurSIKEnvelope.connectPlugs('output', tibiaSIKJoint['translateX'])

        tibiaSIKStretchName = self.formatName(name='Tibia', kinemat='SIK', subname='Stretch', type='multDoubleLinear')
        tibiaSIKStretch = self.scene.createNode('multDoubleLinear', name=tibiaSIKStretchName)
        tibiaSIKStretch.connectPlugs(tibiaLength['output1D'], 'input1')
        tibiaSIKStretch.connectPlugs(legSIKSoftener['softScale'], 'input2')

        tibiaSIKEnvelopeName = self.formatName(name='Tibia', kinemat='SIK', subname='Envelope', type='blendTwoAttr')
        tibiaSIKEnvelope = self.scene.createNode('blendTwoAttr', name=tibiaSIKEnvelopeName)
        tibiaSIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        tibiaSIKEnvelope.connectPlugs(tibiaLength['output1D'], 'input[0]')
        tibiaSIKEnvelope.connectPlugs(tibiaSIKStretch['output'], 'input[1]')
        tibiaSIKEnvelope.connectPlugs('output', tarsusSIKJoint['translateX'])

        tarsusSIKStretchName = self.formatName(name='Tarsus', kinemat='SIK', subname='Stretch', type='multDoubleLinear')
        tarsusSIKStretch = self.scene.createNode('multDoubleLinear', name=tarsusSIKStretchName)
        tarsusSIKStretch.connectPlugs(tarsusLength['output1D'], 'input1')
        tarsusSIKStretch.connectPlugs(legSIKSoftener['softScale'], 'input2')

        tarsusSIKEnvelopeName = self.formatName(name='Tarsus', kinemat='SIK', subname='Envelope', type='blendTwoAttr')
        tarsusSIKEnvelope = self.scene.createNode('blendTwoAttr', name=tarsusSIKEnvelopeName)
        tarsusSIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        tarsusSIKEnvelope.connectPlugs(tarsusLength['output1D'], 'input[0]')
        tarsusSIKEnvelope.connectPlugs(tarsusSIKStretch['output'], 'input[1]')
        tarsusSIKEnvelope.connectPlugs('output', tarsusTipSIKJoint['translateX'])

        # Setup stretch on other IK joints
        #
        femurIKStretchName = self.formatName(name='Femur', kinemat='IK', subname='Stretch', type='multDoubleLinear')
        femurIKStretch = self.scene.createNode('multDoubleLinear', name=femurIKStretchName)
        femurIKStretch.connectPlugs(femurLength['output1D'], 'input1')
        femurIKStretch.connectPlugs(legIKSoftener['softScale'], 'input2')

        femurIKEnvelopeName = self.formatName(name='Femur', kinemat='IK', subname='Envelope', type='blendTwoAttr')
        femurIKEnvelope = self.scene.createNode('blendTwoAttr', name=femurIKEnvelopeName)
        femurIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        femurIKEnvelope.connectPlugs(femurLength['output1D'], 'input[0]')
        femurIKEnvelope.connectPlugs(femurIKStretch['output'], 'input[1]')
        femurIKEnvelope.connectPlugs('output', tibiaIKJoint['translateX'])

        tibiaIKStretchName = self.formatName(name='Tibia', kinemat='IK', subname='Stretch', type='multDoubleLinear')
        tibiaIKStretch = self.scene.createNode('multDoubleLinear', name=tibiaIKStretchName)
        tibiaIKStretch.connectPlugs(tibiaLength['output1D'], 'input1')
        tibiaIKStretch.connectPlugs(legIKSoftener['softScale'], 'input2')

        tibiaIKEnvelopeName = self.formatName(name='Tibia', kinemat='IK', subname='Envelope', type='blendTwoAttr')
        tibiaIKEnvelope = self.scene.createNode('blendTwoAttr', name=tibiaIKEnvelopeName)
        tibiaIKEnvelope.connectPlugs(switchCtrl['stretch'], 'attributesBlender')
        tibiaIKEnvelope.connectPlugs(tibiaLength['output1D'], 'input[0]')
        tibiaIKEnvelope.connectPlugs(tibiaSIKStretch['output'], 'input[1]')
        tibiaIKEnvelope.connectPlugs('output', tibiaTipIKJoint['translateX'])

        # Calculate default pole matrix
        #
        hingeVector = om.MVector(hingePoint - limbOrigin)
        hingeDot = forwardVector * hingeVector

        poleOrigin = limbOrigin + (forwardVector * hingeDot)
        polePosition = poleOrigin + (poleVector * sum([femurDistance, tibiaDistance]))

        polePositionMatrix = transformutils.createTranslateMatrix(polePosition)
        poleRotationMatrix = transformutils.createRotationMatrix([90.0, 0.0, 0.0]) * transformutils.createRotationMatrix(followJoint.worldMatrix())
        poleMatrix = poleRotationMatrix * polePositionMatrix

        # Create PV controller
        #
        legPVSpaceName = self.formatName(name='Leg', subname='PV', type='space')
        legPVSpace = self.scene.createNode('transform', name=legPVSpaceName, parent=controlsGroup)
        legPVSpace.setWorldMatrix(poleMatrix)

        legPVCtrlName = self.formatName(name='Leg', subname='PV', type='control')
        legPVCtrl = self.scene.createNode('transform', name=legPVCtrlName, parent=legPVSpace)
        legPVCtrl.addPointHelper('sphere', 'centerMarker', size=(5.0 * rigScale), side=componentSide)
        legPVCtrl.addDivider('Settings')
        legPVCtrl.addAttr(longName='twist', attributeType='float', keyable=True)
        legPVCtrl.addDivider('Spaces')
        legPVCtrl.addAttr(longName='transformSpaceW0', niceName='Transform Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legPVCtrl.addAttr(longName='transformSpaceW1', niceName='Transform Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legPVCtrl.addAttr(longName='transformSpaceW2', niceName='Transform Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legPVCtrl.addAttr(longName='transformSpaceW3', niceName='Transform Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legPVCtrl.addAttr(longName='transformSpaceW4', niceName='Transform Space (Leg)', attributeType='float', min=0.0, max=1.0, keyable=True)
        legPVCtrl.addAttr(longName='transformSpaceW5', niceName='Transform Space (Auto)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        legPVCtrl.connectPlugs('twist', legIKHandle['twist'])
        legPVCtrl.prepareChannelBoxForAnimation()
        legPVCtrl.tagAsController(parent=extremityIKCtrl)
        self.publishNode(legPVCtrl, alias='Leg_PV')

        legPVSpaceSwitch = legPVSpace.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, pelvisCtrl, legCtrl, followTarget], weighted=True, maintainOffset=True)
        legPVSpaceSwitch.connectPlugs(legPVCtrl['transformSpaceW0'], 'target[0].targetWeight')
        legPVSpaceSwitch.connectPlugs(legPVCtrl['transformSpaceW1'], 'target[1].targetWeight')
        legPVSpaceSwitch.connectPlugs(legPVCtrl['transformSpaceW2'], 'target[2].targetWeight')
        legPVSpaceSwitch.connectPlugs(legPVCtrl['transformSpaceW3'], 'target[3].targetWeight')
        legPVSpaceSwitch.connectPlugs(legPVCtrl['transformSpaceW4'], 'target[4].targetWeight')
        legPVSpaceSwitch.connectPlugs(legPVCtrl['transformSpaceW5'], 'target[5].targetWeight')

        legPVCtrl.userProperties['space'] = legPVSpace.uuid()
        legPVCtrl.userProperties['spaceSwitch'] = legPVSpaceSwitch.uuid()

        legIKHandle.addConstraint('poleVectorConstraint', [legPVCtrl])

        # Create hinge controls
        #
        trochanterSpaceName = self.formatName(name='Trochanter', type='space')
        trochanterSpace = self.scene.createNode('transform', name=trochanterSpaceName, parent=controlsGroup)
        trochanterSpace.addConstraint('pointConstraint', [coxaTipBlendJoint])
        trochanterSpace.addConstraint('orientConstraint', [coxaTipBlendJoint, femurBlendJoint])
        trochanterSpace.addConstraint('scaleConstraint', [legCtrl])
        trochanterSpace.freezeTransform()

        trochanterCtrlName = self.formatName(name='Trochanter', type='control')
        trochanterCtrl = self.scene.createNode('transform', name=trochanterCtrlName, parent=trochanterSpace)
        trochanterCtrl.addPointHelper('square', size=(20.0 * rigScale), localRotate=(45.0, 0.0, 0.0), lineWidth=4.0, colorRGB=darkColorRGB)
        trochanterCtrl.prepareChannelBoxForAnimation()
        self.publishNode(trochanterCtrl, alias='Trochanter')

        trochanterCtrl.userProperties['space'] = trochanterSpace.uuid()

        patellaBendTargetName = self.formatName(name='Patella', subname='Bend', type='target')
        patellaBendTarget = self.scene.createNode('transform', name=patellaBendTargetName, parent=privateGroup)
        patellaBendTarget.displayLocalAxis = True
        patellaBendTarget.visibility = False
        patellaBendTarget.addConstraint('pointConstraint', [tibiaBlendJoint])
        patellaBendTarget.addConstraint('orientConstraint', [femurBlendJoint, tibiaBlendJoint])
        patellaBendTarget.addConstraint('scaleConstraint', [legCtrl])

        patellaStraightTargetName = self.formatName(name='Patella', subname='Straight', type='target')
        patellaStraightTarget = self.scene.createNode('transform', name=patellaStraightTargetName, parent=privateGroup)
        patellaStraightTarget.displayLocalAxis = True
        patellaStraightTarget.visibility = False
        patellaStraightTarget.addConstraint('aimConstraint', [tibiaTipBlendJoint], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=femurBlendJoint)
        patellaStraightTarget.addConstraint('scaleConstraint', [legCtrl])

        constraint = patellaStraightTarget.addConstraint('pointConstraint', [femurBlendJoint, tibiaTipBlendJoint])
        targets = constraint.targets()
        constraint.connectPlugs(femurWeight['outFloat'], targets[1].driver())  # These are flipped for a reason!
        constraint.connectPlugs(tibiaWeight['outFloat'], targets[0].driver())  # These are flipped for a reason!

        patellaSpaceName = self.formatName(name='Patella', type='space')
        patellaSpace = self.scene.createNode('transform', name=patellaSpaceName, parent=controlsGroup)
        patellaSpace.copyTransform(patellaBendTarget)
        patellaSpace.freezeTransform()

        patellaCtrlName = self.formatName(name='Patella', type='control')
        patellaCtrl = self.scene.createNode('transform', name=patellaCtrlName, parent=patellaSpace)
        patellaCtrl.addPointHelper('square', size=(20.0 * rigScale), localRotate=(45.0, 0.0, 0.0), lineWidth=4.0, colorRGB=darkColorRGB)
        patellaCtrl.addDivider('Spaces')
        patellaCtrl.addAttr(longName='straighten', niceName='Straighten (Off/On)', attributeType='distance', min=0.0, max=1.0, default=0.0, keyable=True)
        patellaCtrl.prepareChannelBoxForAnimation()
        self.publishNode(patellaCtrl, alias='Patella')

        patellaSpaceSwitch = patellaSpace.addSpaceSwitch([patellaBendTarget, patellaStraightTarget])
        patellaSpaceSwitch.weighted = True
        patellaSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        patellaSpaceSwitch.connectPlugs(patellaCtrl['straighten'], 'target[0].targetWeight')
        patellaSpaceSwitch.connectPlugs(patellaCtrl['straighten'], 'target[1].targetWeight')

        patellaCtrl.userProperties['space'] = patellaSpace.uuid()
        patellaCtrl.userProperties['spaceSwitch'] = patellaSpaceSwitch.uuid()

        trochanterCtrl.tagAsController(parent=legCtrl, children=[patellaCtrl])
        patellaCtrl.tagAsController(parent=trochanterCtrl)

        # Create PV handle curve
        #
        legPVShapeName = self.formatName(kinemat='PV', subname='Handle', type='control')
        legPVShape = self.scene.createNode('nurbsCurve', name=f'{legPVShapeName}Shape', parent=legPVCtrl)
        legPVShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
        legPVShape.useObjectColor = 2
        legPVShape.wireColorRGB = lightColorRGB

        legPVCurveFromPointName = self.formatName(kinemat='PV', subname='Handle', type='curveFromPoint')
        legPVCurveFromPoint = self.scene.createNode('curveFromPoint', name=legPVCurveFromPointName)
        legPVCurveFromPoint.degree = 1
        legPVCurveFromPoint.connectPlugs(legPVShape[f'worldMatrix[{legPVShape.instanceNumber()}]'], 'inputMatrix[0]')
        legPVCurveFromPoint.connectPlugs(patellaCtrl[f'worldMatrix[{patellaCtrl.instanceNumber()}]'], 'inputMatrix[1]')
        legPVCurveFromPoint.connectPlugs(legPVShape[f'parentInverseMatrix[{legPVShape.instanceNumber()}]'], 'parentInverseMatrix')
        legPVCurveFromPoint.connectPlugs('outputCurve', legPVShape['create'])

        # Create target joints
        #
        coxaJointName = self.formatName(name='Coxa', type='joint')
        coxaJoint = self.scene.createNode('joint', name=coxaJointName, parent=jointsGroup)
        coxaJoint.addConstraint('pointConstraint', [coxaBlendJoint])
        coxaJoint.addConstraint('aimConstraint', [trochanterCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=femurBlendJoint)
        coxaJoint.connectPlugs(coxaBlendJoint['scale'], 'scale')

        femurJointName = self.formatName(name='Femur', type='joint')
        femurJoint = self.scene.createNode('joint', name=femurJointName, parent=jointsGroup)
        femurJoint.addConstraint('pointConstraint', [trochanterCtrl])
        femurJoint.addConstraint('aimConstraint', [patellaCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=femurBlendJoint)
        femurJoint.connectPlugs(femurBlendJoint['scale'], 'scale')

        tibiaJointName = self.formatName(name='Tibia', type='joint')
        tibiaJoint = self.scene.createNode('joint', name=tibiaJointName, parent=femurJoint)
        tibiaJoint.addConstraint('pointConstraint', [patellaCtrl], skipTranslateY=True, skipTranslateZ=True)
        tibiaJoint.addConstraint('aimConstraint', [tibiaTipBlendJoint], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=tibiaBlendJoint)
        tibiaJoint.connectPlugs(tibiaBlendJoint['scale'], 'scale')

        tibiaTipJointName = self.formatName(name='TibiaTip', type='joint')
        tibiaTipJoint = self.scene.createNode('joint', name=tibiaTipJointName, parent=tibiaJoint)
        tibiaTipJoint.addConstraint('pointConstraint', [tibiaTipBlendJoint], skipTranslateY=True, skipTranslateZ=True)
        tibiaTipJoint.connectPlugs(tibiaTipBlendJoint['scale'], 'scale')

        # Cache kinematic components
        #
        self.userProperties['switchControl'] = switchCtrl.uuid()

        self.userProperties['fkJoints'] = (femurFKJoint.uuid(), tibiaFKJoint.uuid(), tibiaTipFKJoint.uuid())
        self.userProperties['fkControls'] = (femurFKCtrl.uuid(), tibiaFKCtrl.uuid(), tibiaTipFKTarget.uuid())

        self.userProperties['ikJoints'] = (coxaIKJoint.uuid(), femurIKJoint.uuid(), tibiaIKJoint.uuid(), tibiaTipIKJoint.uuid())
        self.userProperties['ikSoftener'] = legIKSoftener.uuid()
        self.userProperties['ikControls'] = (legCtrl.uuid(), coxaRotCtrl.uuid(), coxaTransCtrl.uuid(), extremityIKCtrl.uuid())
        self.userProperties['ikTarget'] = legIKHandleTarget.uuid()
        self.userProperties['sikJoints'] = (femurSIKJoint.uuid(), tibiaSIKJoint.uuid(), tarsusSIKJoint.uuid(), tarsusTipSIKJoint.uuid())
        self.userProperties['sikSoftener'] = legSIKSoftener.uuid()
        self.userProperties['sikTarget'] = legSIKHandleTarget.uuid()
        self.userProperties['sikHandle'] = legSIKHandle.uuid()
        self.userProperties['ikHandles'] = (coxaIKHandle.uuid(), legIKHandle.uuid())
        self.userProperties['pvControl'] = legPVCtrl.uuid()
        self.userProperties['hingeControls'] = (trochanterCtrl.uuid(), patellaCtrl.uuid())

        self.userProperties['followJoints'] = (followJoint.uuid(), followTipJoint.uuid())
        self.userProperties['blendJoints'] = (femurBlendJoint.uuid(), tibiaBlendJoint.uuid(), tibiaTipBlendJoint.uuid())
        self.userProperties['targetJoints'] = (femurJoint.uuid(), tibiaJoint.uuid(), tibiaTipJoint.uuid())
    # endregion
