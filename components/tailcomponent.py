from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from itertools import chain
from collections import namedtuple
from typing import List, Union
from dcc.maya.libs import transformutils, shapeutils
from rigomatic.libs import kinematicutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


TailFKPair = namedtuple('TailFKPair', ('rot', 'trans'))


class TailComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements chain components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Tail'
    __default_tail_matrix__ = om.MMatrix(
        [
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 100.0, 1.0)
        ]
    )
    __default_tail_spacing__ = 20.0
    # endregion

    # region Attributes
    numTailLinks = mpyattribute.MPyAttribute('numTailLinks', attributeType='int', min=3, default=5)

    @numTailLinks.changed
    def numTailLinks(self, numTailLinks):
        """
        Changed method that notifies any tail-link size changes.

        :type numTailLinks: int
        :rtype: None
        """

        self.markDirty()
    # endregion

    # region Methods
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Edit skeleton specs
        #
        tailCount = int(self.numTailLinks) + 1
        *tailSpecs, tailTipSpec = self.resizeSkeletonSpecs(tailCount, skeletonSpecs)

        for (i, tailSpec) in enumerate(tailSpecs, start=1):

            tailSpec['name'] = self.formatName(index=i)
            tailSpec['driver'] = self.formatName(index=i, type='control')

        tailTipSpec['name'] = self.formatName(name=f'{self.componentName}Tip')
        tailTipSpec['driver'] = self.formatName(name=f'{self.componentName}Tip', type='target')

        # Call parent method
        #
        super(TailComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        componentSide = self.Side(self.componentSide)
        *tailSpecs, tailTipSpec = self.skeletonSpecs()

        # Create tail joints
        #
        tailCount = len(tailSpecs)
        tailJoints = [None] * tailCount

        for (i, tailSpec) in enumerate(tailSpecs):

            parent = tailJoints[i - 1] if (i > 0) else None

            tailJoint = self.scene.createNode('joint', name=tailSpec.name, parent=parent)
            tailJoint.side = componentSide
            tailJoint.type = self.Type.OTHER
            tailJoint.otherType = self.componentName

            defaultTailSpacing = (i + 1) * self.__default_tail_spacing__
            defaultTailMatrix = transformutils.createTranslateMatrix([defaultTailSpacing, 0.0, 0.0]) * self.__default_tail_matrix__
            tailMatrix = tailSpec.getMatrix(default=defaultTailMatrix)
            tailJoint.setWorldMatrix(tailMatrix)

            tailSpec.uuid = tailJoint.uuid()
            tailJoints[i] = tailJoint

        # Create tip joint
        #
        tailTipJoint = self.scene.createNode('joint', name=tailTipSpec.name, parent=tailJoints[-1])
        tailTipJoint.side = componentSide
        tailTipJoint.type = self.Type.OTHER
        tailTipJoint.otherType = self.componentName

        defaultTailSpacing = (tailCount + 1) * self.__default_tail_spacing__
        defaultTailTipMatrix = transformutils.createTranslateMatrix([defaultTailSpacing, 0.0, 0.0]) * self.__default_tail_matrix__
        tailTipMatrix = tailTipSpec.getMatrix(default=defaultTailTipMatrix)
        tailTipJoint.setWorldMatrix(tailTipMatrix)

        tailTipSpec.uuid = tailTipJoint.uuid()

        return (*tailJoints, tailTipJoint)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Get component properties
        #
        componentSide = self.Side(self.componentSide)
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        *tailSpecs, tailTipSpec = self.skeletonSpecs()
        tailExportJoints = [self.scene(tailSpec.uuid) for tailSpec in chain(tailSpecs, [tailTipSpec])]

        # Create base control
        #
        baseCtrl = self.scene.createNode('transform')
        baseCtrl.copyTransform(tailExportJoints[0])
        baseCtrl.prepareChannelBoxForAnimation()

        # Create FK controls
        #
        rootComponent = self.findRootComponent()
        worldSpaceCtrl = rootComponent.getPublishedNode('Motion')

        numTailFKCtrls = len(tailSpecs)
        tailFKCtrls = [None] * numTailFKCtrls  # type: List[Union[TailFKPair, None]]

        for (i, tailExportJoint) in enumerate(tailExportJoints[:-1]):

            # Create FK control
            #
            index = str(i + 1).zfill(2)
            previousFKRotCtrl = tailFKCtrls[i - 1].rot if (i > 0) else None
            previousFKTransCtrl = tailFKCtrls[i - 1].trans if (i > 0) else None

            tailFKSpaceName = self.formatName(subname='FK', index=index, kinemat='Rot', type='space')
            tailFKSpace = self.scene.createNode('transform', name=tailFKSpaceName, parent=controlsGroup)
            tailFKSpace.copyTransform(tailExportJoint)
            tailFKSpace.freezeTransform()

            tailFKOffsetName = self.formatName(subname='FK', index=index, kinemat='Rot', type='offset')
            tailFKOffset = self.scene.createNode('transform', name=tailFKOffsetName, parent=tailFKSpace)

            tailFKRotCtrlName = self.formatName(subname='FK', index=index, kinemat='Rot', type='control')
            tailFKRotCtrl = self.scene.createNode('transform', name=tailFKRotCtrlName, parent=tailFKOffset)
            tailFKRotCtrl.addPointHelper('box', size=18.0, side=componentSide)
            tailFKRotCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
            tailFKRotCtrl.prepareChannelBoxForAnimation()
            self.publishNode(tailFKRotCtrl, alias=f'{self.componentName}{index}_FK_Rot')

            tailFKTransCtrlName = self.formatName(subname='FK', index=index, kinemat='Trans', type='control')
            tailFKTransCtrl = self.scene.createNode('transform', name=tailFKTransCtrlName, parent=tailFKRotCtrl)
            tailFKTransCtrl.addPointHelper('axisView', size=12.0, localScale=(0.0, 3.0, 3.0), side=componentSide)
            tailFKTransCtrl.prepareChannelBoxForAnimation()
            self.publishNode(tailFKTransCtrl, alias=f'{self.componentName}{index}_FK_Trans')

            tailFKRotCtrl.userProperties['space'] = tailFKSpace.uuid()
            tailFKRotCtrl.userProperties['offset'] = tailFKOffset.uuid()

            # Add space switching to control
            #
            localSpaceCtrl = previousFKRotCtrl if (previousFKRotCtrl is not None) else baseCtrl
            spaceTargets = (localSpaceCtrl, worldSpaceCtrl)

            tailFKSpaceSwitch = tailFKSpace.addSpaceSwitch(spaceTargets)
            tailFKSpaceSwitch.weighted = True
            tailFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            tailFKSpaceSwitch.connectPlugs(tailFKRotCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            tailFKSpaceSwitch.connectPlugs(tailFKRotCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

            tailFKCtrls[i] = TailFKPair(tailFKRotCtrl, tailFKTransCtrl)

            # Resize preview control
            #
            if previousFKRotCtrl is not None:

                previousFKRotCtrl.shape().reorientAndScaleToFit(tailFKRotCtrl)

        tailIKTipTargetName = self.formatName()
        tailIKTipTarget = self.scene.createNode('transform', name=tailIKTipTargetName, parent=tailFKCtrls[-1].trans)
        tailIKTipTarget.displayLocalAxis = True
        tailIKTipTarget.visibility = False
        tailIKTipTarget.copyTransform(tailExportJoints[-1])
        tailIKTipTarget.freezeTransform()

        firstFKRotCtrl, firstFKTransCtrl = tailFKCtrls[0]
        lastFKRotCtrl, lastFKTransCtrl = tailFKCtrls[-1]

        lastFKRotCtrl.shape().reorientAndScaleToFit(tailIKTipTarget)

        # Create tail IK base control
        #
        tailIKBaseSpaceName = self.formatName(subname='IK', kinemat='Base', type='space')
        tailIKBaseSpace = self.scene.createNode('transform', name=tailIKBaseSpaceName, parent=controlsGroup)
        tailIKBaseSpace.copyTransform(tailExportJoints[0])
        tailIKBaseSpace.freezeTransform()
        tailIKBaseSpace.addConstraint('transformConstraint', [tailFKCtrls[0].trans])

        tailIKBaseCtrlName = self.formatName(subname='IK', kinemat='Base', type='control')
        tailIKBaseCtrl = self.scene.createNode('transform', name=tailIKBaseCtrlName, parent=tailIKBaseSpace)
        tailIKBaseCtrl.addPointHelper('sphere', size=24.0, side=componentSide)
        tailIKBaseCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0)
        tailIKBaseCtrl.prepareChannelBoxForAnimation()
        self.publishNode(tailIKBaseCtrl, alias=f'{self.componentName}_IK_Base')

        # Create tail IK tip control
        #
        tailIKTipSpaceName = self.formatName(subname='IK', kinemat='Tip', type='space')
        tailIKTipSpace = self.scene.createNode('transform', name=tailIKTipSpaceName, parent=controlsGroup)
        tailIKTipSpace.copyTransform(tailExportJoints[0])
        tailIKTipSpace.freezeTransform()
        tailIKTipSpace.addConstraint('transformConstraint', [tailIKTipTarget])

        tailIKTipCtrlName = self.formatName(subname='IK', kinemat='Tip', type='control')
        tailIKTipCtrl = self.scene.createNode('transform', name=tailIKTipCtrlName, parent=tailIKTipSpace)
        tailIKTipCtrl.addPointHelper('sphere', size=24.0, side=componentSide)
        tailIKTipCtrl.addProxyAttr('stretch', tailIKBaseCtrl['stretch'])
        tailIKTipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(tailIKTipCtrl, alias=f'{self.componentName}_IK_Tip')

        # Create base and tip joints
        #
        tailIKBaseJointName = self.formatName(subname='IK', kinemat='Base', type='joint')
        tailIKBaseJoint = self.scene.createNode('joint', name=tailIKBaseJointName, parent=jointsGroup)
        tailIKBaseJoint.copyTransform(tailExportJoints[0])
        tailIKBaseJoint.addConstraint('transformConstraint', [tailIKBaseCtrl])

        tailIKTipJointName = self.formatName(subname='IK', kinemat='Tip', type='joint')
        tailIKTipJoint = self.scene.createNode('joint', name=tailIKTipJointName, parent=jointsGroup)
        tailIKTipJoint.copyTransform(tailExportJoints[-1])
        tailIKTipJoint.addConstraint('transformConstraint', [tailIKTipCtrl])

        # Create curve from points
        #
        controlPoints = [joint.translation(space=om.MSpace.kWorld) for joint in tailExportJoints]
        numControlPoints = len(controlPoints)

        curveData = shapeutils.createCurveFromPoints(controlPoints, degree=1)

        curveName = self.formatName(type='nurbsCurve')
        curve = self.scene.createNode('transform', name=curveName, parent=privateGroup)
        curve.inheritsTransform = False
        curve.lockAttr('translate', 'rotate', 'scale')

        curveShape = self.scene.createNode('bezierCurve', name=f'{curveName}Shape', parent=curve)
        curveShape.setAttr('cached', curveData)

        # Add skin deformer to curve
        #
        influences = (tailIKBaseJoint.object(), tailIKTipJoint.object())

        skinCluster = curveShape.addDeformer('skinCluster')
        skinCluster.skinningMethod = 0  # Linear
        skinCluster.maxInfluences = 2
        skinCluster.maintainMaxInfluences = True
        skinCluster.addInfluences(*influences)

        # Create remap for skin weights
        #
        skinRemap = self.scene.createNode('remapArray')
        skinRemap.setAttr('value', [{'value_FloatValue': 1.0, 'value_Interp': 2}, {'value_FloatValue': 0.0,'value_Interp': 2}])

        intermediateCurve = skinCluster.intermediateObject()
        curveLength = intermediateCurve.length()

        parameters = [None] * numControlPoints

        for i in range(numControlPoints):

            # Calculate parameter for point
            #
            point = intermediateCurve.cvPosition(i)
            param = intermediateCurve.getParamAtPoint(point)
            paramLength = intermediateCurve.findLengthFromParam(param)

            parameter = paramLength / curveLength
            parameters[i] = parameter

            # Connect remap parameter
            #
            skinRemap.setAttr(f'parameter[{i}]', parameter)
            skinRemap.connectPlugs(f'outValue[{i}].outValueX', skinCluster[f'weightList[{i}].weights[0]'])

            reverseWeight = self.scene.createNode('revDoubleLinear')
            reverseWeight.connectPlugs(skinRemap[f'outValue[{i}].outValueX'], 'input')
            reverseWeight.connectPlugs('output', skinCluster[f'weightList[{i}].weights[1]'])

        # Override control-points on intermediate-object
        #
        nodes = [tailFKTransCtrl for (tailFKRotCtrl, tailFKTransCtrl) in tailFKCtrls]
        nodes.append(tailIKTipTarget)

        matrices = [None] * numControlPoints

        for (i, node) in enumerate(nodes):

            index = i + 1

            multMatrixName = self.formatName(subname='ControlPoint', index=index, type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(node[f'worldMatrix[{node.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(intermediateCurve[f'parentInverseMatrix[{intermediateCurve.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(subname='ControlPoint', index=index, type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', intermediateCurve[f'controlPoints[{i}].xValue'], force=True)
            breakMatrix.connectPlugs('row4Y', intermediateCurve[f'controlPoints[{i}].yValue'], force=True)
            breakMatrix.connectPlugs('row4Z', intermediateCurve[f'controlPoints[{i}].zValue'], force=True)

            matrices[i] = breakMatrix

        # Override pre-bind matrices on skin cluster
        #
        tailIKBaseCtrl.connectPlugs(f'parentInverseMatrix[{tailIKBaseJoint.instanceNumber()}]', skinCluster['bindPreMatrix[0]'])
        tailIKTipCtrl.connectPlugs(f'parentInverseMatrix[{tailIKTipJoint.instanceNumber()}]', skinCluster['bindPreMatrix[1]'])

        # Create tail IK joints
        #
        numTailIKJoints = len(tailExportJoints)
        tailIKJoints = [None] * numTailIKJoints

        for (i, tailExportJoint) in enumerate(tailExportJoints):

            index = i + 1
            parent = tailIKJoints[i - 1] if (i > 0) else jointsGroup

            tailIKJointName = self.formatName(subname='IK', index=index, type='joint')
            tailIKJoint = self.scene.createNode('joint', name=tailIKJointName, parent=parent)
            tailIKJoint.copyTransform(tailExportJoint)

            tailIKJoints[i] = tailIKJoint

        # Setup spline IK solver
        #
        splineIKHandle, splineIKEffector = kinematicutils.applySplineSolver(tailIKJoints[0], tailIKJoints[-1], curveShape)
        splineIKHandle.setParent(privateGroup)
        splineIKHandle.rootOnCurve = True
        splineIKHandle.rootTwistMode = True
        splineIKHandle.dTwistControlEnable = True
        splineIKHandle.dWorldUpType = 4  # Object Rotation Up (Start/End)
        splineIKHandle.dForwardAxis = 0  # Positive X
        splineIKHandle.dWorldUpAxis = 3  # Positive Z
        splineIKHandle.dWorldUpVector = (0.0, 0.0, 1.0)
        splineIKHandle.dWorldUpVectorEnd = (0.0, 0.0, 1.0)
        splineIKHandle.connectPlugs(tailIKBaseJoint[f'worldMatrix[{tailIKBaseJoint.instanceNumber()}]'], 'dWorldUpMatrix')
        splineIKHandle.connectPlugs(tailIKTipJoint[f'worldMatrix[{tailIKTipJoint.instanceNumber()}]'], 'dWorldUpMatrixEnd')

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
            tailBlendName = self.formatName(subname='Length', index=(i + 1), type='blendTwoAttr')
            tailBlend = self.scene.createNode('blendTwoAttr', name=tailBlendName)
            tailBlend.connectPlugs(tailIKTipCtrl['stretch'], 'attributesBlender')
            tailBlend.connectPlugs(baseDistance['distance'], 'input[0]')
            tailBlend.connectPlugs(stretchDistance['distance'], 'input[1]')
            tailBlend.connectPlugs('output', endJoint['translateX'])

        # Create macro controls
        #
        tailRotateBaseSpaceName = self.formatName(subname='Rotate', kinemat='Base', type='space')
        tailRotateBaseSpace = self.scene.createNode('transform', name=tailRotateBaseSpaceName, parent=controlsGroup)
        tailRotateBaseSpace.copyTransform(tailIKBaseCtrl)
        tailRotateBaseSpace.freezeTransform()
        tailRotateBaseSpace.addConstraint('transformConstraint', [tailIKBaseCtrl])

        tailRotateBaseCtrlName = self.formatName(subname='Rotate', kinemat='Base', type='control')
        tailRotateBaseCtrl = self.scene.createNode('transform', name=tailRotateBaseCtrlName, parent=tailRotateBaseSpace)
        tailRotateBaseCtrl.addShape('RoundQuadArrowCurve', size=30.0, side=componentSide)
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
        tailRotateTipCtrl.addShape('RoundQuadArrowCurve', size=30.0, localRotate=(0.0, 0.0, 180.0), side=componentSide)
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

        nodes = [self.scene(tailFKRotCtrl.userProperties['offset']) for (tailFKRotCtrl, tailFKTransCtrl) in tailFKCtrls]
        nodes.append(tailIKTipTarget)

        for (i, node) in enumerate(nodes):

            parameter = parameters[i]

            tailTranslateRemap.setAttr(f'parameter[{i}]', parameter)
            tailRotateRemap.setAttr(f'parameter[{i}]', parameter)
            tailScaleRemap.setAttr(f'parameter[{i}]', parameter)

            tailTranslateRemap.connectPlugs(f'outValue[{i}]', node['translate'])
            tailRotateRemap.connectPlugs(f'outValue[{i}]', node['rotate'])
            tailScaleRemap.connectPlugs(f'outValue[{i}]', node['scale'])

        # Create micro controls
        #
        for (i, tailIKJoint) in enumerate(tailIKJoints[:-1]):

            index = i + 1

            tailSpaceName = self.formatName(index=index, type='space')
            tailSpace = self.scene.createNode('transform', name=tailSpaceName, parent=controlsGroup)
            tailSpace.copyTransform(tailIKJoint)
            tailSpace.freezeTransform()
            tailSpace.addConstraint('transformConstraint', [tailIKJoint])

            tailCtrlName = self.formatName(index=index, type='control')
            tailCtrl = self.scene.createNode('transform', name=tailCtrlName, parent=tailSpace)
            tailCtrl.addPointHelper('tearDrop', size=24.0, localRotate=(-90.0, 0.0, 0.0), side=componentSide)
            tailCtrl.prepareChannelBoxForAnimation()
            self.publishNode(tailCtrl, alias=f'{self.componentName}{index}')

            tailExportJoints[i].addConstraint('transformConstraint', [tailCtrl])
    # endregion
