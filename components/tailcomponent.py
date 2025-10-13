from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from itertools import chain
from collections import namedtuple
from typing import List, Union
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import transformutils, shapeutils
from rigomatic.libs import kinematicutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


TailFKPair = namedtuple('TailFKPair', ('space', 'group', 'rot', 'trans'))


class TailComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements chain components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Tail'
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 100.0, 1.0)
        ]
    )
    __default_component_spacing__ = 20.0
    # endregion

    # region Attributes
    numTailLinks = mpyattribute.MPyAttribute('numTailLinks', attributeType='int', min=3, default=5)

    @numTailLinks.changed
    def numTailLinks(self, numTailLinks):
        """
        Changed method that notifies any tail link size changes.

        :type numTailLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit tail specs
        #
        tailSide = self.Side(self.componentSide)

        tailSize = int(self.numTailLinks) + 1  # Reserve space for tip spec!
        *tailSpecs, tailTipSpec = self.resizeSkeleton(tailSize, skeletonSpecs, hierarchical=True)

        for (i, tailSpec) in enumerate(tailSpecs, start=1):

            isFirstTailSpec = (i == 1)
            defaultMatrix = om.MMatrix(self.__default_tail_matrix__) if isFirstTailSpec else transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))

            tailSpec.name = self.formatName(index=i)
            tailSpec.side = tailSide
            tailSpec.type = self.Type.OTHER
            tailSpec.otherType = self.componentName
            tailSpec.defaultMatrix = defaultMatrix
            tailSpec.driver.name = self.formatName(index=i, type='control')

        # Edit tail tip spec
        #
        tailTipSpec.name = self.formatName(name=f'{self.componentName}Tip')
        tailTipSpec.side = tailSide
        tailTipSpec.type = self.Type.OTHER
        tailTipSpec.otherType = self.componentName
        tailTipSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))
        tailTipSpec.driver.name = self.formatName(name=f'{self.componentName}Tip', type='target')

        # Call parent method
        #
        return super(TailComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Get component properties
        #
        *tailSpecs, tailTipSpec = self.skeleton(flatten=True)
        tailExportJoints = [tailSpec.getNode() for tailSpec in chain(tailSpecs, [tailTipSpec])]
        firstTailExportJoint, lastTailExportJoint = tailExportJoints[0], tailExportJoints[-1]

        rigScale = self.findControlRig().getRigScale()
        componentSide = self.Side(self.componentSide)
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create base control
        #
        baseSpaceName = self.formatName(subname='Base', type='space')
        baseSpace = self.scene.createNode('transform', name=baseSpaceName, parent=controlsGroup)
        baseSpace.copyTransform(firstTailExportJoint)
        baseSpace.freezeTransform()
        baseSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        baseSpaceName = self.formatName(subname='Base', type='control')
        baseCtrl = self.scene.createNode('transform', name=baseSpaceName, parent=baseSpace)
        baseCtrl.addStar(30.0, numPoints=4, colorRGB=darkColorRGB)
        baseCtrl.prepareChannelBoxForAnimation()
        self.publishNode(baseCtrl, alias='Base')

        # Create tail FK controls
        #
        rootComponent = self.findRootComponent()
        worldSpaceCtrl = rootComponent.getPublishedNode('Motion')

        numTailFKPairs = len(tailSpecs)
        tailFKPairs = [None] * numTailFKPairs  # type: List[Union[TailFKPair, None]]

        for (i, tailExportJoint) in enumerate(tailExportJoints[:-1]):

            # Create FK control
            #
            index = str(i + 1).zfill(2)
            previousFKRotCtrl = tailFKPairs[i - 1].rot if (i > 0) else None
            previousFKTransCtrl = tailFKPairs[i - 1].trans if (i > 0) else None

            tailFKSpaceName = self.formatName(subname='FK', index=index, kinemat='Rot', type='space')
            tailFKSpace = self.scene.createNode('transform', name=tailFKSpaceName, parent=controlsGroup)
            tailFKSpace.copyTransform(tailExportJoint)
            tailFKSpace.freezeTransform()

            tailFKGroupName = self.formatName(subname='FK', index=index, kinemat='Rot', type='transform')
            tailFKGroup = self.scene.createNode('transform', name=tailFKGroupName, parent=tailFKSpace)

            tailFKRotCtrlName = self.formatName(subname='FK', index=index, kinemat='Rot', type='control')
            tailFKRotCtrl = self.scene.createNode('freeform', name=tailFKRotCtrlName, parent=tailFKGroup)
            tailFKRotCtrl.addPointHelper('box', size=(15.0 * rigScale), colorRGB=colorRGB)
            tailFKRotCtrl.addDivider('Spaces')
            tailFKRotCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
            tailFKRotCtrl.prepareChannelBoxForAnimation()
            self.publishNode(tailFKRotCtrl, alias=f'{self.componentName}{index}_FK_Rot')

            tailFKScaleSumName = self.formatName(subname='FK', index=index, kinemat='ScaleSum', type='arrayMath')
            tailFKScaleSum = self.scene.createNode('arrayMath', name=tailFKScaleSumName)
            tailFKScaleSum.setAttr('operation', 2)  # Multiply
            tailFKScaleSum.connectPlugs(baseCtrl['scale'], 'inFloat[0]')
            tailFKScaleSum.connectPlugs('outFloat', tailFKRotCtrl['preScale'])

            for j in range(i):

                tailFKScaleSum.connectPlugs(tailFKPairs[j].rot['scale'], f'inFloat[{j + 1}]')

            tailFKTransCtrlName = self.formatName(subname='FK', index=index, kinemat='Trans', type='control')
            tailFKTransCtrl = self.scene.createNode('transform', name=tailFKTransCtrlName, parent=tailFKRotCtrl)
            tailFKTransCtrl.addPointHelper('axisView', size=(10.0 * rigScale), localScale=(0.0, 3.0, 3.0), colorRGB=lightColorRGB)
            tailFKTransCtrl.prepareChannelBoxForAnimation()
            self.publishNode(tailFKTransCtrl, alias=f'{self.componentName}{index}_FK_Trans')

            tailFKRotCtrl.userProperties['space'] = tailFKSpace.uuid()
            tailFKRotCtrl.userProperties['translate'] = tailFKTransCtrl.uuid()
            tailFKRotCtrl.userProperties['group'] = tailFKGroup.uuid()
            tailFKRotCtrl.userProperties['preScale'] = tailFKScaleSum.uuid()

            # Add space switching to control
            #
            localSpaceCtrl = previousFKRotCtrl if (previousFKRotCtrl is not None) else baseCtrl
            spaceTargets = (localSpaceCtrl, worldSpaceCtrl)

            tailFKSpaceSwitch = tailFKSpace.addSpaceSwitch(spaceTargets, weighted=True, maintainOffset=True)
            tailFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 0.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            tailFKSpaceSwitch.connectPlugs(tailFKRotCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            tailFKSpaceSwitch.connectPlugs(tailFKRotCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

            tailFKRotCtrl.userProperties['spaceSwitch'] = tailFKSpaceSwitch.uuid()

            tailFKPairs[i] = TailFKPair(tailFKSpace, tailFKGroup, tailFKRotCtrl, tailFKTransCtrl)

            # Resize preview control
            #
            if previousFKRotCtrl is not None:

                previousFKRotCtrl.shape().reorientAndScaleToFit(tailFKRotCtrl)

        tailIKTipTargetName = self.formatName(name=f'{self.componentName}Tip', type='target')
        tailIKTipTarget = self.scene.createNode('transform', name=tailIKTipTargetName, parent=tailFKPairs[-1].rot)
        tailIKTipTarget.displayLocalAxis = True
        tailIKTipTarget.visibility = False
        tailIKTipTarget.copyTransform(lastTailExportJoint)
        tailIKTipTarget.freezeTransform()

        firstFKRotCtrl, firstFKTransCtrl = tailFKPairs[0].rot, tailFKPairs[0].trans
        lastFKRotCtrl, lastFKTransCtrl = tailFKPairs[-1].rot, tailFKPairs[-1].trans

        lastFKRotCtrl.shape().reorientAndScaleToFit(tailIKTipTarget)

        # Create tail IK base control
        #
        tailIKBaseSpaceName = self.formatName(subname='IK', kinemat='Base', type='space')
        tailIKBaseSpace = self.scene.createNode('transform', name=tailIKBaseSpaceName, parent=controlsGroup)
        tailIKBaseSpace.copyTransform(tailExportJoints[0])
        tailIKBaseSpace.freezeTransform()
        tailIKBaseSpace.addConstraint('parentConstraint', [tailFKPairs[0].trans])
        tailIKBaseSpace.addConstraint('scaleConstraint', [baseCtrl])

        tailIKBaseCtrlName = self.formatName(subname='IK', kinemat='Base', type='control')
        tailIKBaseCtrl = self.scene.createNode('transform', name=tailIKBaseCtrlName, parent=tailIKBaseSpace)
        tailIKBaseCtrl.addPointHelper('sphere','fill', 'shaded', size=(20.0 * rigScale), side=componentSide)
        tailIKBaseCtrl.prepareChannelBoxForAnimation()
        self.publishNode(tailIKBaseCtrl, alias=f'{self.componentName}_IK_Base')

        constraint = tailIKBaseSpace.addConstraint('scaleConstraint', [baseCtrl])

        tailIKBaseScaleName = self.formatName(subname='IK', kinemat='Base', type='min')
        tailIKBaseScale = self.scene.createNode('min', name=tailIKBaseScaleName)
        tailIKBaseScale.connectPlugs(constraint['constraintScaleY'], 'input[0]')
        tailIKBaseScale.connectPlugs(constraint['constraintScaleZ'], 'input[1]')
        tailIKBaseScale.connectPlugs('output', tailIKBaseSpace['scale'], force=True)

        # Create tail IK tip control
        #
        tailIKTipSpaceName = self.formatName(subname='IK', kinemat='Tip', type='space')
        tailIKTipSpace = self.scene.createNode('transform', name=tailIKTipSpaceName, parent=controlsGroup)
        tailIKTipSpace.copyTransform(tailExportJoints[0])
        tailIKTipSpace.freezeTransform()
        tailIKTipSpace.addConstraint('parentConstraint', [tailIKTipTarget])
        
        tailIKTipCtrlName = self.formatName(subname='IK', kinemat='Tip', type='control')
        tailIKTipCtrl = self.scene.createNode('transform', name=tailIKTipCtrlName, parent=tailIKTipSpace)
        tailIKTipCtrl.addPointHelper('sphere','fill', 'shaded', size=(20.0 * rigScale), side=componentSide)
        tailIKTipCtrl.addDivider('Settings')
        tailIKTipCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        tailIKTipCtrl.addAttr(longName='retract', attributeType='float', min=0.0, max=1.0, keyable=True)
        tailIKTipCtrl.addAttr(longName='twist', attributeType='float', keyable=True)
        tailIKTipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(tailIKTipCtrl, alias=f'{self.componentName}_IK_Tip')

        constraint = tailIKTipSpace.addConstraint('scaleConstraint', [baseCtrl])

        tailIKTipScaleName = self.formatName(subname='IK', kinemat='Tip', type='min')
        tailIKTipScale = self.scene.createNode('min', name=tailIKTipScaleName)
        tailIKTipScale.connectPlugs(constraint['constraintScaleY'], 'input[0]')
        tailIKTipScale.connectPlugs(constraint['constraintScaleZ'], 'input[1]')
        tailIKTipScale.connectPlugs('output', tailIKTipSpace['scale'], force=True)

        # Create base and tip joints
        #
        tailIKBaseJointName = self.formatName(subname='IK', kinemat='Base', type='joint')
        tailIKBaseJoint = self.scene.createNode('joint', name=tailIKBaseJointName, parent=jointsGroup)
        tailIKBaseJoint.copyTransform(firstTailExportJoint)
        tailIKBaseJoint.addConstraint('transformConstraint', [tailIKBaseCtrl])

        tailIKTipJointName = self.formatName(subname='IK', kinemat='Tip', type='joint')
        tailIKTipJoint = self.scene.createNode('joint', name=tailIKTipJointName, parent=jointsGroup)
        tailIKTipJoint.copyTransform(lastTailExportJoint)
        tailIKTipJoint.addConstraint('transformConstraint', [tailIKTipCtrl])

        # Create curve from points
        #
        controlPoints = [joint.translation(space=om.MSpace.kWorld) for joint in tailExportJoints]
        numControlPoints = len(controlPoints)

        curveData = shapeutils.createCurveFromPoints(controlPoints, degree=1)

        curveName = self.formatName(type='nurbsCurve')
        curve = self.scene.createNode('transform', name=curveName, parent=privateGroup)
        curve.inheritsTransform = False
        curve.template = True
        curve.lockAttr('translate', 'rotate', 'scale')

        curveShape = self.scene.createNode('nurbsCurve', name=f'{curveName}Shape', parent=curve)
        curveShape.setAttr('cached', curveData)

        # Add skin deformer to curve
        #
        influences = (tailIKBaseJoint.object(), tailIKTipJoint.object())

        skinClusterName = self.formatName(type='skinCluster')
        skinCluster = curveShape.addDeformer('skinCluster', name=skinClusterName)
        skinCluster.skinningMethod = 0  # Linear
        skinCluster.maxInfluences = 2
        skinCluster.maintainMaxInfluences = True
        skinCluster.addInfluences(*influences)

        tailIKBaseCtrl.connectPlugs(f'parentInverseMatrix[{tailIKBaseCtrl.instanceNumber()}]', skinCluster['bindPreMatrix[0]'])
        tailIKTipCtrl.connectPlugs(f'parentInverseMatrix[{tailIKTipCtrl.instanceNumber()}]', skinCluster['bindPreMatrix[1]'])

        # Create remap for skin weights
        #
        weightRemapName = self.formatName(subname='Weights', type='remapArray')
        weightRemap = self.scene.createNode('remapArray', name=weightRemapName)
        weightRemap.clamp = True
        weightRemap.setAttr('value', [{'value_FloatValue': 1.0, 'value_Interp': 2}, {'value_FloatValue': 0.0,'value_Interp': 2}])

        intermediateCurve = skinCluster.intermediateObject()
        curveLength = intermediateCurve.length()
        controlNodes = [tailFKPair.trans for tailFKPair in tailFKPairs] + [tailIKTipTarget]

        parameters = [None] * numControlPoints

        for (i, controlNode) in enumerate(controlNodes):

            # Calculate parameter for point
            #
            point = intermediateCurve.cvPosition(i)
            param = intermediateCurve.getParamAtPoint(point)
            paramLength = intermediateCurve.findLengthFromParam(param)

            parameter = paramLength / curveLength
            parameters[i] = parameter

            # Add parameter to control node
            #
            controlNode.addAttr(longName='parameter', attributeType='float', min=0.0, max=1.0, hidden=True)
            controlNode.setAttr('parameter', parameter)

            # Connect remap parameter
            #
            index = i + 1

            weightRemap.connectPlugs(controlNode['parameter'], f'parameter[{i}]')
            weightRemap.connectPlugs(f'outValue[{i}].outValueX', skinCluster[f'weightList[{i}].weights[0]'])

            reverseWeightName = self.formatName(subname='Weight', index=index, type='revDoubleLinear')
            reverseWeight = self.scene.createNode('revDoubleLinear', name=reverseWeightName)
            reverseWeight.connectPlugs(weightRemap[f'outValue[{i}].outValueX'], 'input')
            reverseWeight.connectPlugs('output', skinCluster[f'weightList[{i}].weights[1]'])

        # Override control-points on intermediate-object
        #
        matrices = [None] * numControlPoints

        for (i, controlNode) in enumerate(controlNodes):

            index = i + 1

            multMatrixName = self.formatName(subname='ControlPoint', index=index, type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(controlNode[f'worldMatrix[{controlNode.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(intermediateCurve[f'parentInverseMatrix[{intermediateCurve.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(subname='ControlPoint', index=index, type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', intermediateCurve[f'controlPoints[{i}].xValue'], force=True)
            breakMatrix.connectPlugs('row4Y', intermediateCurve[f'controlPoints[{i}].yValue'], force=True)
            breakMatrix.connectPlugs('row4Z', intermediateCurve[f'controlPoints[{i}].zValue'], force=True)

            matrices[i] = breakMatrix

        # Create tail IK joints
        #
        numTailIKJoints = len(tailExportJoints)
        tailIKJoints = [None] * numTailIKJoints

        lastIndex = numTailIKJoints - 1

        for (i, tailExportJoint) in enumerate(tailExportJoints):

            index = i + 1
            name = self.formatName(subname='IK', index=index, type='joint') if (i != lastIndex) else self.formatName(name=f'{self.componentName}Tip', subname='IK', type='joint')
            parent = tailIKJoints[i - 1] if (i > 0) else jointsGroup

            tailIKJoint = self.scene.createNode('joint', name=name, parent=parent)
            tailIKJoint.copyTransform(tailExportJoint)
            tailIKJoints[i] = tailIKJoint

        # Setup spline IK solver
        #
        splineIKHandle, splineIKEffector = kinematicutils.applySplineSolver(tailIKJoints[0], tailIKJoints[-1], curveShape)
        splineIKHandle.setName(self.formatName(type='ikHandle'))
        splineIKEffector.setName(self.formatName(type='ikEffector'))
        splineIKHandle.setParent(privateGroup)
        splineIKHandle.rootOnCurve = True
        splineIKHandle.rootTwistMode = True
        splineIKHandle.dTwistControlEnable = True
        splineIKHandle.dWorldUpType = 3  # Object Rotation Up
        splineIKHandle.dForwardAxis = 0  # Positive X
        splineIKHandle.dWorldUpAxis = 3  # Positive Z
        splineIKHandle.dWorldUpVector = (0.0, 0.0, 1.0)
        splineIKHandle.dWorldUpVectorEnd = (0.0, 0.0, 1.0)
        splineIKHandle.connectPlugs(tailIKBaseJoint[f'worldMatrix[{tailIKBaseJoint.instanceNumber()}]'], 'dWorldUpMatrix')

        # Setup spline IK twist
        #
        tailStartTwistSolverName = self.formatName(subname='StartTwist', kinemat='IK', type='twistSolver')
        tailStartTwistSolver = self.scene.createNode('twistSolver', name=tailStartTwistSolverName)
        tailStartTwistSolver.setAttr('forwardAxis', 0)  # X
        tailStartTwistSolver.setAttr('upAxis', 2)  # Z
        tailStartTwistSolver.setAttr('inverse', True)
        tailStartTwistSolver.connectPlugs(tailIKBaseCtrl[f'parentMatrix[{tailIKBaseCtrl.instanceNumber()}]'], 'startMatrix')
        tailStartTwistSolver.connectPlugs(tailIKBaseCtrl[f'worldMatrix[{tailIKBaseCtrl.instanceNumber()}]'], 'endMatrix')

        tailEndTwistSolverName = self.formatName(subname='EndTwist', kinemat='IK', type='twistSolver')
        tailEndTwistSolver = self.scene.createNode('twistSolver', name=tailEndTwistSolverName)
        tailEndTwistSolver.setAttr('forwardAxis', 0)  # X
        tailEndTwistSolver.setAttr('upAxis', 2)  # Z
        tailEndTwistSolver.connectPlugs(tailIKTipCtrl[f'parentMatrix[{tailIKTipCtrl.instanceNumber()}]'], 'startMatrix')
        tailEndTwistSolver.connectPlugs(tailIKTipCtrl[f'worldMatrix[{tailIKTipCtrl.instanceNumber()}]'], 'endMatrix')

        tailFKTwistSumName = self.formatName(subname='TwistSum', kinemat='FK', type='arrayMath')
        tailFKTwistSum = self.scene.createNode('arrayMath', name=tailFKTwistSumName)

        tailFKtwistSource = [baseCtrl] + [tailFKPair.rot for tailFKPair in tailFKPairs]

        for (i, (startFKCtrl, endFKCtrl)) in enumerate(zip(tailFKtwistSource[:-1], tailFKtwistSource[1:])):

            multMatrixName = self.formatName(subname='Twist', kinemat='FK', type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(endFKCtrl[f'worldMatrix[{endFKCtrl.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(startFKCtrl[f'worldInverseMatrix[{startFKCtrl.instanceNumber()}]'], 'matrixIn[1]')

            decomposeMatrixName = self.formatName(subname='Twist', kinemat='FK', type='multMatrix')
            decomposeMatrix = self.scene.createNode('decomposeMatrix', name=decomposeMatrixName)
            decomposeMatrix.connectPlugs(multMatrix['matrixSum'], 'inputMatrix')
            decomposeMatrix.connectPlugs('outputRotateX', tailFKTwistSum[f'inAngle[{i}].inAngleX'])

        tailTwistSumName = self.formatName(subname='TwistSum', type='arrayMath')
        tailTwistSum = self.scene.createNode('arrayMath', name=tailTwistSumName)
        tailTwistSum.connectPlugs(tailFKTwistSum['outAngleX'], 'inAngle[0].inAngleX')
        tailTwistSum.connectPlugs(tailStartTwistSolver['roll'], 'inAngle[1].inAngleX')
        tailTwistSum.connectPlugs(tailEndTwistSolver['roll'], 'inAngle[2].inAngleX')
        tailTwistSum.connectPlugs(tailIKTipCtrl['twist'], 'inAngle[3].inAngleX')
        tailTwistSum.connectPlugs('outAngleX', splineIKHandle['twist'])

        # Setup spline IK stretch
        #
        curveInfoName = self.formatName(type='curveInfo')
        curveInfo = self.scene.createNode('curveInfo', name=curveInfoName)
        curveInfo.connectPlugs(curveShape[f'worldSpace[{curveShape.instanceNumber()}]'], 'inputCurve')

        intermediateInfoName = self.formatName(subname='Intermediate', type='curveInfo')
        intermediateInfo = self.scene.createNode('curveInfo', name=intermediateInfoName)
        intermediateInfo.connectPlugs(intermediateCurve[f'worldSpace[{intermediateCurve.instanceNumber()}]'], 'inputCurve')

        for (i, (startJoint, endJoint)) in enumerate(zip(tailIKJoints[:-1], tailIKJoints[1:])):

            # Create distance-between nodes
            #
            baseDistanceName = self.formatName(subname='Length', index=(i + 1), type='distanceBetween')
            baseDistance = self.scene.createNode('distanceBetween', name=baseDistanceName)
            baseDistance.connectPlugs(intermediateInfo[f'controlPoints[{i}]'], 'point1')
            baseDistance.connectPlugs(intermediateInfo[f'controlPoints[{i + 1}]'], 'point2')

            stretchDistanceName = self.formatName(subname='IntermediateLength', index=(i + 1), type='distanceBetween')
            stretchDistance = self.scene.createNode('distanceBetween', name=stretchDistanceName)
            stretchDistance.connectPlugs(curveInfo[f'controlPoints[{i}]'], 'point1')
            stretchDistance.connectPlugs(curveInfo[f'controlPoints[{i + 1}]'], 'point2')

            # Create spine-length multiplier
            #
            tailBlendName = self.formatName(subname='Length', index=(i + 1), type='lerp')
            tailBlend = self.scene.createNode('lerp', name=tailBlendName)
            tailBlend.connectPlugs(tailIKTipCtrl['stretch'], 'weight')
            tailBlend.connectPlugs(baseDistance['distance'], 'input1')
            tailBlend.connectPlugs(stretchDistance['distance'], 'input2')

            tailRetractName = self.formatName(subname='Retract', index=(i + 1), type='lerp')
            tailRetract = self.scene.createNode('lerp', name=tailRetractName)
            tailRetract.connectPlugs(tailIKTipCtrl['retract'], 'weight')
            tailRetract.connectPlugs(tailBlend['output'], 'input1')
            tailRetract.setAttr('input2', 0.001)
            tailRetract.connectPlugs('output', endJoint['translateX'])

        # Create macro controls
        #
        tailRotateBaseSpaceName = self.formatName(subname='Rotate', kinemat='Base', type='space')
        tailRotateBaseSpace = self.scene.createNode('transform', name=tailRotateBaseSpaceName, parent=controlsGroup)
        tailRotateBaseSpace.copyTransform(tailIKBaseCtrl)
        tailRotateBaseSpace.freezeTransform()
        tailRotateBaseSpace.addConstraint('transformConstraint', [tailIKBaseCtrl])

        tailRotateBaseCtrlName = self.formatName(subname='Rotate', kinemat='Base', type='control')
        tailRotateBaseCtrl = self.scene.createNode('transform', name=tailRotateBaseCtrlName, parent=tailRotateBaseSpace)
        tailRotateBaseCtrl.addShape('RoundQuadArrowCurve', size=(25.0 * rigScale), colorRGB=darkColorRGB)
        tailRotateBaseCtrl.prepareChannelBoxForAnimation()
        tailRotateBaseCtrl.connectPlugs('inverseMatrix', tailRotateBaseCtrl['offsetParentMatrix'])
        self.publishNode(tailRotateBaseCtrl, alias=f'{self.componentName}_Rotate_Base')

        tailRotateTipSpaceName = self.formatName(subname='Rotate', kinemat='Tip', type='space')
        tailRotateTipSpace = self.scene.createNode('transform', name=tailRotateTipSpaceName, parent=controlsGroup)
        tailRotateTipSpace.copyTransform(tailIKTipCtrl)
        tailRotateTipSpace.freezeTransform()
        tailRotateTipSpace.addConstraint('transformConstraint', [tailIKTipCtrl])

        tailRotateTipCtrlName = self.formatName(subname='Rotate', kinemat='Tip', type='control')
        tailRotateTipCtrl = self.scene.createNode('transform', name=tailRotateTipCtrlName, parent=tailRotateTipSpace)
        tailRotateTipCtrl.addShape('RoundQuadArrowCurve', size=(25.0 * rigScale), localRotate=(0.0, 0.0, 180.0), colorRGB=darkColorRGB)
        tailRotateTipCtrl.prepareChannelBoxForAnimation()
        tailRotateTipCtrl.connectPlugs('inverseMatrix', tailRotateTipCtrl['offsetParentMatrix'])
        self.publishNode(tailRotateTipCtrl, alias=f'{self.componentName}_Rotate_Tip')

        # Connect macros to FK controls
        #
        tailTranslateRemapName = self.formatName(subname='Translate', type='remapArray')
        tailTranslateRemap = self.scene.createNode('remapArray', name=tailTranslateRemapName)
        tailTranslateRemap.setAttr('clamp', True)
        tailTranslateRemap.connectPlugs(tailRotateBaseCtrl['translate'], tailTranslateRemap['outputMin'])
        tailTranslateRemap.connectPlugs(tailRotateTipCtrl['translate'], tailTranslateRemap['outputMax'])

        tailRotateRemapName = self.formatName(subname='Rotate', type='remapArray')
        tailRotateRemap = self.scene.createNode('remapArray', name=tailRotateRemapName)
        tailRotateRemap.setAttr('clamp', True)
        tailRotateRemap.connectPlugs(tailRotateBaseCtrl['rotate'], tailRotateRemap['outputMin'])
        tailRotateRemap.connectPlugs(tailRotateTipCtrl['rotate'], tailRotateRemap['outputMax'])

        tailScaleRemapName = self.formatName(subname='Scale', type='remapArray')
        tailScaleRemap = self.scene.createNode('remapArray', name=tailScaleRemapName)
        tailScaleRemap.setAttr('clamp', True)
        tailScaleRemap.connectPlugs(tailRotateBaseCtrl['scale'], tailScaleRemap['outputMin'])
        tailScaleRemap.connectPlugs(tailRotateTipCtrl['scale'], tailScaleRemap['outputMax'])

        for (i, tailFKPair) in enumerate(tailFKPairs):

            tailTranslateRemap.connectPlugs(tailFKPair.trans['parameter'], f'parameter[{i}]')
            tailRotateRemap.connectPlugs(tailFKPair.trans['parameter'], f'parameter[{i}]')
            tailScaleRemap.connectPlugs(tailFKPair.trans['parameter'], f'parameter[{i}]')

            tailTranslateRemap.connectPlugs(f'outValue[{i}]', tailFKPair.group['translate'])
            tailRotateRemap.connectPlugs(f'outValue[{i}]', tailFKPair.group['rotate'])

            tailFKScaleSum = self.scene(tailFKPair.rot.userProperties['preScale'])
            lastIndex = tailFKScaleSum['inFloat'].evaluateNumElements()
            tailScaleRemap.connectPlugs(f'outValue[{i}]', tailFKScaleSum[f'inFloat[{lastIndex}]'])

        # Create micro controls
        #
        for (i, (controlNode, tailIKJoint)) in enumerate(zip(controlNodes[:-1], tailIKJoints[:-1]), start=1):

            tailSpaceName = self.formatName(index=i, type='space')
            tailSpace = self.scene.createNode('transform', name=tailSpaceName, parent=controlsGroup)
            tailSpace.copyTransform(tailIKJoint)
            tailSpace.freezeTransform()
            tailSpace.addConstraint('parentConstraint', [tailIKJoint])
            tailSpace.addConstraint('scaleConstraint', [controlNode])

            tailCtrlName = self.formatName(index=i, type='control')
            tailCtrl = self.scene.createNode('transform', name=tailCtrlName, parent=tailSpace)
            tailCtrl.addPointHelper('tearDrop', size=(20.0 * rigScale), localRotate=(-90.0, 0.0, 0.0), colorRGB=darkColorRGB)
            tailCtrl.prepareChannelBoxForAnimation()
            self.publishNode(tailCtrl, alias=f'{self.componentName}{str(i).zfill(2)}')
    # endregion
