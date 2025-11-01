from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.maya.libs import transformutils, shapeutils, plugutils
from dcc.math import floatmath
from dcc.dataclasses.colour import Colour
from rigomatic.libs import kinematicutils
from collections import namedtuple
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


NeckFKPair = namedtuple('NeckFKPair', ('rot', 'trans'))


class HeadComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements head components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Head'
    __default_component_spacing__ = 10.0
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 200.0, 1.0)
        ]
    )
    # endregion

    # region Attributes
    neckEnabled = mpyattribute.MPyAttribute('neckEnabled', attributeType='bool', default=True)
    numNeckLinks = mpyattribute.MPyAttribute('numNeckLinks', attributeType='int', min=1, default=1)

    @neckEnabled.changed
    def neckEnabled(self, neckEnabled):
        """
        Changed method that notifies any neck state changes.

        :type neckEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numNeckLinks.changed
    def numNeckLinks(self, numNeckLinks):
        """
        Changed method that notifies any neck-link size changes.

        :type numNeckLinks: int
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

        # Edit neck specs
        #
        numNeckLinks = int(self.numNeckLinks)
        neckPassthrough = not bool(self.neckEnabled)
        neckSide = self.Side(self.componentSide)

        neckSize = numNeckLinks + 1  # Save space for the head spec!
        *neckSpecs, headSpec = self.resizeSkeleton(neckSize, skeletonSpecs, hierarchical=True)

        if numNeckLinks == 0:

            pass

        elif numNeckLinks == 1:

            neckSpec = neckSpecs[0]

            neckSpec.passthrough = neckPassthrough
            neckSpec.name = self.formatName(name='Neck')
            neckSpec.side = neckSide
            neckSpec.type = self.Type.NECK
            neckSpec.defaultMatrix = om.MMatrix(self.__default_component_matrix__)
            neckSpec.driver.name = self.formatName(name='Neck', type='control')

        else:

            for (i, neckSpec) in enumerate(neckSpecs, start=1):

                isFirstNeckLink = (i == 1)
                defaultMatrix = om.MMatrix(self.__default_component_matrix__) if isFirstNeckLink else transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))

                neckSpec.passthrough = neckPassthrough
                neckSpec.name = self.formatName(name='Neck', index=i)
                neckSpec.side = neckSide
                neckSpec.type = self.Type.NECK
                neckSpec.defaultMatrix = defaultMatrix
                neckSpec.driver.name = self.formatName(name='Neck', index=i, type='control')

        # Edit head spec
        #
        headSpec.name = self.formatName()
        headSpec.side = neckSide
        headSpec.type = self.Type.HEAD
        headSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))
        headSpec.driver.name = self.formatName(kinemat='IK', type='target')

        # Call parent method
        #
        return super(HeadComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def getAttachmentTargets(self):
        """
        Returns the attachment targets for this component.
        If we're attaching to a spine component then we want to use an alternative target!

        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
        """

        # Evaluate component parent
        #
        componentParent = self.componentParent()
        isSpineComponent = componentParent.className.endswith('SpineComponent')

        if not isSpineComponent:

            return super(HeadComponent, self).getAttachmentTargets()

        # Evaluate attachment position
        #
        attachmentSpecs = self.getAttachmentOptions()
        numAttachmentSpecs = len(attachmentSpecs)

        attachmentIndex = int(self.attachmentId)
        lastIndex = numAttachmentSpecs - 1

        if attachmentIndex == lastIndex:

            attachmentSpec = attachmentSpecs[attachmentIndex]
            exportJoint = attachmentSpec.getNode()
            exportDriver = self.scene(componentParent.userProperties['spineTipIKTarget'])

            return exportJoint, exportDriver

        elif 0 <= attachmentIndex < numAttachmentSpecs:

            attachmentSpec = attachmentSpecs[attachmentIndex]
            exportJoint = attachmentSpec.getNode()
            exportDriver = attachmentSpec.driver.getDriver()

            return exportJoint, exportDriver

        else:

            return None, None

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        *neckSpecs, headSpec = self.skeleton(flatten=True)
        neckExportJoints = [neckSpec.getNode() for neckSpec in neckSpecs]
        headExportJoint = headSpec.getNode()
        headExportMatrix = headExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        controlRig = self.findControlRig()
        rigWidth, rigHeight = controlRig.getRigWidthAndHeight()
        rigScale = controlRig.getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Get space switch options
        #
        firstNeckSpec = neckSpecs[0]
        neckEnabled = bool(firstNeckSpec.enabled)

        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        spineComponents = self.findComponentAncestors('SpineComponent')
        spineExists = len(spineComponents) == 1
        spineEnabled = bool(spineComponents[0].spineEnabled) if spineExists else False

        cogCtrl, waistCtrl, chestCtrl = None, None, None

        if spineExists:

            spineComponent = spineComponents[0]
            cogCtrl = spineComponent.getPublishedNode('COG')
            waistCtrl = spineComponent.getPublishedNode('Waist')
            chestCtrl = spineComponent.getPublishedNode('Chest_IK') if spineEnabled else None

        # Create head control
        #
        headSpaceName = self.formatName(type='space')
        headSpace = self.scene.createNode('transform', name=headSpaceName, parent=controlsGroup)
        headSpace.setWorldMatrix(headExportMatrix, skipScale=True)
        headSpace.freezeTransform()

        headCtrlName = self.formatName(type='control')
        headCtrl = self.scene.createNode('transform', name=headCtrlName, parent=headSpace)
        headCtrl.addShape('CrownCurve', localPosition=(15.0 * rigScale, 0.0, 0.0), size=(15.0 * rigScale), colorRGB=colorRGB, lineWidth=4.0)
        headCtrl.prepareChannelBoxForAnimation()
        self.publishNode(headCtrl, alias='Head')

        # Check if neck was enabled
        #
        if neckEnabled:

            # Add custom attributes to head control
            #
            headCtrl.addDivider('Settings')
            headCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='lookAt', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            # Evaluate neck links
            #
            neckCount = len(neckSpecs)

            neckFKCtrls = [None] * neckCount  # type: list[NeckFKPair]
            neckIKJoints = [None] * (neckCount + 1)  # type: list[mpynode.MPyNode]

            if neckCount == 0:

                raise NotImplementedError('buildRig() unable to process invalid neck configuration!')

            elif neckCount == 1:

                # Create neck FK control
                #
                neckExportJoint = neckExportJoints[0]

                neckFKSpaceName = self.formatName(name='Neck', kinemat='FK', type='space')
                neckFKSpace = self.scene.createNode('transform', name=neckFKSpaceName, parent=controlsGroup)
                neckFKSpace.copyTransform(neckExportJoint)
                neckFKSpace.freezeTransform()

                neckFKCtrlName = self.formatName(name='Neck', kinemat='FK', type='control')
                neckFKCtrl = self.scene.createNode('transform', name=neckFKCtrlName, parent=neckFKSpace)
                neckFKCtrl.addPointHelper('disc', size=(15.0 * rigScale), colorRGB=lightColorRGB, lineWidth=2.0)
                neckFKCtrl.addDivider('Settings')
                neckFKCtrl.addAttr(longName='inheritsTwist', attributeType='angle', min=0.0, max=1.0, default=0.5, keyable=True)
                neckFKCtrl.addAttr(longName='affectsSpine', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)  # This feature on by default for Frame44 bipeds
                neckFKCtrl.addDivider('Spaces')
                neckFKCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
                neckFKCtrl.prepareChannelBoxForAnimation()
                self.publishNode(neckFKCtrl, alias='Neck_FK')

                neckFKCtrls[0] = NeckFKPair(neckFKCtrl, None)

                # Setup neck space switching
                #
                targets = [chestCtrl, motionCtrl] if spineExists else [parentExportCtrl, motionCtrl]

                neckFKSpaceSwitch = neckFKSpace.addSpaceSwitch(targets, weighted=True, maintainOffset=True)
                neckFKSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                neckFKSpaceSwitch.connectPlugs(neckFKCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                neckFKSpaceSwitch.connectPlugs(neckFKCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                neckFKCtrl.userProperties['space'] = neckFKSpace.uuid()
                neckFKCtrl.userProperties['spaceSwitch'] = neckFKSpaceSwitch.uuid()

                # Create neck IK joints
                #
                neckIKJointName = self.formatName(name='Neck', kinemat='IK', type='joint')
                neckIKJoint = self.scene.createNode('joint', name=neckIKJointName, parent=jointsGroup)
                neckIKJoint.copyTransform(neckExportJoint)
                neckIKJoint.freezePivots(includeTranslate=False, includeScale=False)

                neckTipIKJointName = self.formatName(name='NeckTip', kinemat='IK', type='joint')
                neckTipIKJoint = self.scene.createNode('joint', name=neckTipIKJointName, parent=neckIKJoint)
                neckTipIKJoint.copyTransform(headExportJoint)
                neckTipIKJoint.freezePivots(includeTranslate=False, includeScale=False)

                neckIKJoint.addConstraint('pointConstraint', [neckFKCtrl])
                neckIKJoint.addConstraint('scaleConstraint', [neckFKCtrl])

                constraint = neckIKJoint.addConstraint(
                    'aimConstraint',
                    [headCtrl],
                    aimVector=(1.0, 0.0, 0.0),
                    upVector=(0.0, 0.0, 1.0),
                    worldUpType=2,
                    worldUpVector=(0.0, 0.0, 1.0),
                    worldUpObject=neckFKCtrl
                )

                neckIKJoints[0], neckIKJoints[1] = neckIKJoint, neckTipIKJoint

                # Create head target
                #
                headIKTargetName = self.formatName(kinemat='IK', type='target')
                headIKTarget = self.scene.createNode('transform', name=headIKTargetName, parent=privateGroup)
                headIKTarget.inheritsTransform = False
                headIKTarget.displayLocalAxis = True
                headIKTarget.setWorldMatrix(headExportMatrix, skipScale=True)
                headIKTarget.freezeTransform()
                headIKTarget.addConstraint('pointConstraint', [neckTipIKJoint])
                headIKTarget.addConstraint('orientConstraint', [headCtrl])
                headIKTarget.addConstraint('scaleConstraint', [headCtrl])

                self.userProperties['headIKTarget'] = headIKTarget.uuid()

                # Create neck control
                #
                neckSpaceName = self.formatName(name='Neck', type='space')
                neckSpace = self.scene.createNode('transform', name=neckSpaceName, parent=controlsGroup)
                neckSpace.copyTransform(neckIKJoint)
                neckSpace.freezeTransform()
                neckSpace.addConstraint('transformConstraint', [neckIKJoint])

                neckCtrlName = self.formatName(name='Neck', type='control')
                neckCtrl = self.scene.createNode('transform', name=neckCtrlName, parent=neckSpace)
                neckCtrl.addPointHelper('sphere', size=(6.0 * rigScale), colorRGB=darkColorRGB)
                neckCtrl.prepareChannelBoxForAnimation()
                self.publishNode(neckCtrl, alias='Neck')

                # Setup neck stretch
                #
                neckLengthMultMatrixName = self.formatName(name='Neck', subname='Length', type='multMatrix')
                neckLengthMultMatrix = self.scene.createNode('multMatrix', name=neckLengthMultMatrixName)
                neckLengthMultMatrix.connectPlugs(headCtrl[f'parentMatrix[{headCtrl.instanceNumber()}]'], 'matrixIn[0]')
                neckLengthMultMatrix.connectPlugs(neckFKCtrl[f'parentInverseMatrix[{neckFKCtrl.instanceNumber()}]'], 'matrixIn[1]')

                neckLengthName = self.formatName(name='Neck', subname='Length', type='distanceBetween')
                neckLength = self.scene.createNode('distanceBetween', name=neckLengthName)
                neckLength.connectPlugs(neckFKCtrl['matrix'], 'inMatrix1')
                neckLength.connectPlugs(neckLengthMultMatrix['matrixSum'], 'inMatrix2')

                headDistanceMultMatrixName = self.formatName(subname='Distance', type='multMatrix')
                headDistanceMultMatrix = self.scene.createNode('multMatrix', name=headDistanceMultMatrixName)
                headDistanceMultMatrix.connectPlugs(headCtrl[f'worldMatrix[{headCtrl.instanceNumber()}]'], 'matrixIn[0]')
                headDistanceMultMatrix.connectPlugs(neckFKCtrl[f'parentInverseMatrix[{neckFKCtrl.instanceNumber()}]'], 'matrixIn[1]')

                headDistanceName = self.formatName(subname='Distance', type='distanceBetween')
                headDistance = self.scene.createNode('distanceBetween', name=headDistanceName)
                headDistance.connectPlugs(neckFKCtrl['matrix'], 'inMatrix1')
                headDistance.connectPlugs(headDistanceMultMatrix['matrixSum'], 'inMatrix2')

                headStretchBlendName = self.formatName(subname='Stretch', type='blendTwoAttr')
                headStretchBlend = self.scene.createNode('blendTwoAttr', name=headStretchBlendName)
                headStretchBlend.connectPlugs(headCtrl['stretch'], 'attributesBlender')
                headStretchBlend.connectPlugs(neckLength['distance'], 'input[0]')
                headStretchBlend.connectPlugs(headDistance['distance'], 'input[1]')
                headStretchBlend.connectPlugs('output', neckTipIKJoint['translateX'])

                # Setup neck twist
                #
                neckTwistSolverName = self.formatName(name='Neck', subname='Twist', type='twistSolver')
                neckTwistSolver = self.scene.createNode('twistSolver', name=neckTwistSolverName)
                neckTwistSolver.forwardAxis = 0  # X
                neckTwistSolver.upAxis = 2  # Z
                neckTwistSolver.segments = 2
                neckTwistSolver.connectPlugs(neckFKCtrl[f'worldMatrix[{neckFKCtrl.instanceNumber()}]'], 'startMatrix')
                neckTwistSolver.connectPlugs(headCtrl[f'worldMatrix[{headCtrl.instanceNumber()}]'], 'endMatrix')

                neckTwistEnvelopeName = self.formatName(name='Neck', subname='TwistEnvelope', type='floatMath')
                neckTwistEnvelope = self.scene.createNode('floatMath', name=neckTwistEnvelopeName)
                neckTwistEnvelope.operation = 2  # Multiply
                neckTwistEnvelope.connectPlugs(neckTwistSolver['roll'], 'inAngleA')
                neckTwistEnvelope.connectPlugs(neckFKCtrl['inheritsTwist'], 'inAngleB')

                constraint.connectPlugs(neckTwistEnvelope['outAngle'], 'offsetX')

                # Tag controllers
                #
                neckFKCtrl.tagAsController(children=[headCtrl, neckCtrl])
                neckCtrl.tagAsController(parent=neckFKCtrl)
                headCtrl.tagAsController(parent=neckFKCtrl)

            else:

                # Create neck FK controls
                #
                topLevelTargets = (chestCtrl, motionCtrl) if spineEnabled else (parentExportCtrl, motionCtrl)

                for (i, neckExportJoint) in enumerate(neckExportJoints):

                    # Create neck FK rotate control
                    #
                    index = str(i + 1).zfill(2)

                    neckFKRotSpaceName = self.formatName(name='Neck', subname='FK', kinemat='Rot', index=index, type='space')
                    neckFKRotSpace = self.scene.createNode('transform', name=neckFKRotSpaceName, parent=controlsGroup)
                    neckFKRotSpace.copyTransform(neckExportJoint)
                    neckFKRotSpace.freezeTransform()

                    neckFKRotCtrlName = self.formatName(name='Neck', subname='FK', kinemat='Rot', index=index, type='control')
                    neckFKRotCtrl = self.scene.createNode('transform', name=neckFKRotCtrlName, parent=neckFKRotSpace)
                    neckFKRotCtrl.addPointHelper('disc', size=(15.0 * rigScale), colorRGB=lightColorRGB, lineWidth=2.0)

                    if i == 0:

                        neckFKRotCtrl.addDivider('Settings')
                        neckFKRotCtrl.addAttr(longName='neckFalloff', attributeType='float', min=0.0, max=10.0, default=5, keyable=True)
                        neckFKRotCtrl.addAttr(longName='neckInfluence', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
                        neckFKRotCtrl.addAttr(longName='affectsSpine', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)  # This feature was disabled on Frame44 quadrupeds!

                    neckFKRotCtrl.addDivider('Spaces')
                    neckFKRotCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
                    neckFKRotCtrl.prepareChannelBoxForAnimation()
                    self.publishNode(neckFKRotCtrl, alias=f'Neck{index}_FK')

                    targets = (neckFKCtrls[i - 1].rot, motionCtrl) if (i > 0) else topLevelTargets

                    neckFKRotSpaceSwitch = neckFKRotSpace.addSpaceSwitch(targets, weighted=True)
                    neckFKRotSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                    neckFKRotSpaceSwitch.connectPlugs(neckFKRotCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                    neckFKRotSpaceSwitch.connectPlugs(neckFKRotCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                    neckFKRotCtrl.userProperties['space'] = neckFKRotSpace.uuid()
                    neckFKRotCtrl.userProperties['spaceSwitch'] = neckFKRotSpaceSwitch.uuid()

                    # Check if neck FK translate control is required
                    #
                    neckFKTransCtrl = None

                    if i > 0:

                        neckFKTransCtrlName = self.formatName(name='Neck', subname='FK', kinemat='Trans', index=index, type='control')
                        neckFKTransCtrl = self.scene.createNode('transform', name=neckFKTransCtrlName, parent=neckFKRotCtrl)
                        neckFKTransCtrl.addShape('LollipopCurve', size=(28.0 * rigScale), localRotate=(0.0, 90.0, 0.0), colorRGB=lightColorRGB)
                        neckFKTransCtrl.prepareChannelBoxForAnimation()
                        self.publishNode(neckFKTransCtrl, alias=f'Neck{index}_FK_Trans')

                        neckFKRotCtrl.userProperties['translate'] = neckFKTransCtrl.uuid()
                        neckFKTransCtrl.userProperties['rotate'] = neckFKRotCtrl.uuid()

                    neckFKCtrls[i] = NeckFKPair(neckFKRotCtrl, neckFKTransCtrl)

                # Create neck FK tip target
                #
                neckTipFKTargetName = self.formatName(name='NeckTip', subname='FK', type='target')
                neckTipFKTarget = self.scene.createNode('transform', name=neckTipFKTargetName, parent=neckFKCtrls[-1].rot)
                neckTipFKTarget.displayLocalAxis = True
                neckTipFKTarget.visibility = False
                neckTipFKTarget.setWorldMatrix(headExportMatrix, skipRotate=True, skipScale=True)
                neckTipFKTarget.freezeTransform()

                self.userProperties['neckTipFKTarget'] = neckTipFKTarget.uuid()

                # Create neck IK base and tip joints
                #
                firstNeckFKCtrl, lastNeckFKCtrl = neckFKCtrls[0].rot, neckFKCtrls[-1].rot
                firstNeckFKSpace = self.scene(firstNeckFKCtrl.userProperties['space'])

                neckIKBaseJointName = self.formatName(name='Neck', subname='IK', kinemat='Base', type='joint')
                neckIKBaseJoint = self.scene.createNode('joint', name=neckIKBaseJointName, parent=jointsGroup)
                neckIKBaseJoint.inheritsTransform = False
                neckIKBaseJoint.copyTransform(firstNeckFKCtrl, skipScale=True)

                neckIKBaseSpaceSwitch = neckIKBaseJoint.addSpaceSwitch([firstNeckFKCtrl, firstNeckFKSpace], weighted=True)
                neckIKBaseSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0), 'targetReverse': (False, True, False)}])
                neckIKBaseSpaceSwitch.connectPlugs(firstNeckFKCtrl['neckInfluence'], 'target[0].targetRotateWeight')
                neckIKBaseSpaceSwitch.connectPlugs(firstNeckFKCtrl['neckInfluence'], 'target[1].targetRotateWeight')

                neckIKTipJointName = self.formatName(name='Neck', subname='IK', kinemat='Tip', type='joint')
                neckIKTipJoint = self.scene.createNode('joint', name=neckIKTipJointName, parent=jointsGroup)
                neckIKTipJoint.inheritsTransform = False
                neckIKTipJoint.copyTransform(headCtrl, skipScale=True)
                neckIKTipJoint.addConstraint('transformConstraint', [headCtrl])

                # Create neck IK curve
                #
                neckIKCurveName = self.formatName(name='Neck', subname='IK', type='nurbsCurve')
                neckIKCurve = self.scene.createNode('transform', name=neckIKCurveName, subname='IK', parent=privateGroup)
                neckIKCurve.inheritsTransform = False
                neckIKCurve.lockAttr('translate', 'rotate', 'scale')

                controlPoints = [exportJoint.translation(space=om.MSpace.kWorld) for exportJoint in (*neckExportJoints, headExportJoint)]

                neckIKCurveShape = neckIKCurve.addCurve(controlPoints, degree=1)
                neckIKCurveShape.dispCV = True
                neckIKCurveShape.template = True

                # Add skin deformer to neck IK curve
                #
                neckInfluences = (neckIKBaseJoint.object(), neckIKTipJoint.object())

                skinCluster = neckIKCurveShape.addDeformer('skinCluster')
                skinCluster.skinningMethod = 0  # Linear
                skinCluster.maxInfluences = 2
                skinCluster.maintainMaxInfluences = True
                skinCluster.addInfluences(*neckInfluences)

                skinCluster.connectPlugs(firstNeckFKCtrl[f'worldInverseMatrix[{firstNeckFKCtrl.instanceNumber()}]'], 'bindPreMatrix[0]')
                skinCluster.connectPlugs(neckTipFKTarget[f'parentInverseMatrix[{neckTipFKTarget.instanceNumber()}]'], 'bindPreMatrix[1]')

                # Collect neck curve source nodes
                #
                neckIKControlNodes = [neckFKTransCtrl if (neckFKTransCtrl is not None) else neckFKRotCtrl for (neckFKRotCtrl, neckFKTransCtrl) in neckFKCtrls]
                neckIKControlNodes.append(neckTipFKTarget)

                # Create remap for skin weights
                #
                neckWeightRemapName = self.formatName(name='Neck', subname='Weights', type='remapArray')
                neckWeightRemap = self.scene.createNode('remapArray', name=neckWeightRemapName)
                neckWeightRemap.function = 1
                neckWeightRemap.connectPlugs(firstNeckFKCtrl['neckFalloff'], 'coefficient')

                neckIKIntermediateShape = skinCluster.intermediateObject()
                numControlPoints = int(neckIKIntermediateShape.numCVs)
                chestPoint = neckIKIntermediateShape.cvPosition(numControlPoints - 1)
                maxParameter = neckIKIntermediateShape.getParamAtPoint(chestPoint)
                curveLength = neckIKIntermediateShape.findLengthFromParam(maxParameter)

                parameters = [None] * numControlPoints

                for (i, controlNode) in enumerate(neckIKControlNodes):

                    # Calculate parameter for point
                    #
                    point = neckIKIntermediateShape.cvPosition(i)
                    param = neckIKIntermediateShape.getParamAtPoint(point)
                    paramLength = neckIKIntermediateShape.findLengthFromParam(param)

                    parameter = floatmath.clamp(paramLength / curveLength, 0.0, 1.0)
                    parameters[i] = parameter

                    # Add parameter to control node
                    #
                    controlNode.addAttr(longName='parameter', attributeType='float', min=0.0, max=1.0, hidden=True)
                    controlNode.setAttr('parameter', parameter)
                    controlNode.lockAttr('parameter')

                    # Connect remap parameter
                    #
                    index = i + 1

                    neckWeightRemap.connectPlugs(controlNode['parameter'], f'parameter[{i}]')
                    neckWeightRemap.connectPlugs(f'outValue[{i}].outValueX', skinCluster[f'weightList[{i}].weights[1]'])

                    neckIKReverseWeightName = self.formatName(name='Neck', subname='Weights', index=index, type='revDoubleLinear')
                    neckIKReverseWeight = self.scene.createNode('revDoubleLinear', name=neckIKReverseWeightName)
                    neckIKReverseWeight.connectPlugs(neckWeightRemap[f'outValue[{i}].outValueX'], 'input')
                    neckIKReverseWeight.connectPlugs('output', skinCluster[f'weightList[{i}].weights[0]'])

                self.userProperties['curve'] = neckIKCurveShape.uuid()
                self.userProperties['intermediateCurve'] = neckIKIntermediateShape.uuid()
                self.userProperties['skinCluster'] = skinCluster.uuid()

                neckTipFKTarget.lock()  # Should be safe to lock this node now!

                # Override control-points on intermediate-object
                #
                controlMatrices = [None] * numControlPoints  # type: list[mpynode.MPyNode]

                for (i, controlNode) in enumerate(neckIKControlNodes):

                    index = i + 1

                    neckIKMultMatrixName = self.formatName(name='Neck', subname='ControlPoint', kinemat='IK', index=index, type='multMatrix')
                    neckIKMultMatrix = self.scene.createNode('multMatrix', name=neckIKMultMatrixName)
                    neckIKMultMatrix.connectPlugs(controlNode[f'worldMatrix[{controlNode.instanceNumber()}]'], 'matrixIn[0]')
                    neckIKMultMatrix.connectPlugs(neckIKIntermediateShape[f'parentInverseMatrix[{neckIKIntermediateShape.instanceNumber()}]'], 'matrixIn[1]')

                    neckIKBreakMatrixName = self.formatName(name='Neck', subname='ControlPoint', kinemat='IK', index=index, type='breakMatrix')
                    neckIKBreakMatrix = self.scene.createNode('breakMatrix', name=neckIKBreakMatrixName)
                    neckIKBreakMatrix.connectPlugs(neckIKMultMatrix['matrixSum'], 'inMatrix')
                    neckIKBreakMatrix.connectPlugs('row4X', neckIKIntermediateShape[f'controlPoints[{i}].xValue'], force=True)
                    neckIKBreakMatrix.connectPlugs('row4Y', neckIKIntermediateShape[f'controlPoints[{i}].yValue'], force=True)
                    neckIKBreakMatrix.connectPlugs('row4Z', neckIKIntermediateShape[f'controlPoints[{i}].zValue'], force=True)

                    controlMatrices[i] = neckIKBreakMatrix

                # Create neck IK joints
                #
                for (i, (startIKNode, endIKNode)) in enumerate(zip(neckIKControlNodes[:-1], neckIKControlNodes[1:])):

                    # Create IK joint
                    #
                    index = i + 1
                    parent = neckIKJoints[i - 1] if (i > 0) else jointsGroup

                    neckIKJointName = self.formatName(name='Neck', subname='IK', index=index, type='joint')
                    neckIKJoint = self.scene.createNode('joint', name=neckIKJointName, parent=parent)

                    # Re-orient IK joint
                    #
                    neckIKOrigin = startIKNode.translation(space=om.MSpace.kWorld)
                    neckIKTarget = endIKNode.translation(space=om.MSpace.kWorld)
                    neckIKMatrix = transformutils.createAimMatrix(
                        0, (neckIKTarget - neckIKOrigin).normal(),
                        1, transformutils.breakMatrix(startIKNode.worldMatrix(), normalize=True)[1],
                        startPoint=neckIKOrigin
                    )

                    neckIKJoint.setWorldMatrix(neckIKMatrix)
                    neckIKJoints[i] = neckIKJoint

                    # Check if this is the last pair
                    # If so, create tip joint from previous aim matrix
                    #
                    if endIKNode is neckIKControlNodes[-1]:

                        lastNeckIKJointName = self.formatName(name='NeckTip', subname='IK', type='joint')
                        lastNeckIKJoint = self.scene.createNode('joint', name=lastNeckIKJointName, parent=neckIKJoint)

                        lastNeckIKMatrix = transformutils.createRotationMatrix(neckIKMatrix) * transformutils.createTranslateMatrix(neckIKTarget)
                        lastNeckIKJoint.setWorldMatrix(lastNeckIKMatrix)

                        neckIKJoints[-1] = lastNeckIKJoint

                # Create head IK target
                #
                firstNeckIKJoint, lastNeckIKJoint = neckIKJoints[0], neckIKJoints[-1]

                headIKTargetName = self.formatName(kinemat='IK', type='target')
                headIKTarget = self.scene.createNode('transform', name=headIKTargetName, parent=privateGroup)
                headIKTarget.inheritsTransform = False
                headIKTarget.displayLocalAxis = True
                headIKTarget.setWorldMatrix(headExportMatrix, skipScale=True)
                headIKTarget.freezeTransform()
                headIKTarget.addConstraint('pointConstraint', [lastNeckIKJoint])
                headIKTarget.addConstraint('orientConstraint', [headCtrl])
                headIKTarget.addConstraint('scaleConstraint', [headCtrl])

                self.userProperties['headIKTarget'] = headIKTarget.uuid()

                # Setup spline IK solver
                #
                splineIKHandle, splineIKEffector = kinematicutils.applySplineSolver(firstNeckIKJoint, lastNeckIKJoint, neckIKCurveShape)
                splineIKHandle.setName(self.formatName(name='Neck', type='ikHandle'))
                splineIKHandle.setParent(privateGroup)
                splineIKHandle.visibility = False
                splineIKHandle.rootOnCurve = True
                splineIKHandle.rootTwistMode = True
                splineIKHandle.dTwistControlEnable = True
                splineIKHandle.dWorldUpType = 4  # Object Rotation Up (Start/End)
                splineIKHandle.dForwardAxis = 0  # Positive X
                splineIKHandle.dWorldUpAxis = 0  # Positive Y
                splineIKHandle.dWorldUpVector = (0.0, 1.0, 0.0)
                splineIKHandle.dWorldUpVectorEnd = (0.0, 1.0, 0.0)
                splineIKHandle.connectPlugs(neckIKBaseJoint[f'worldMatrix[{neckIKBaseJoint.instanceNumber()}]'], 'dWorldUpMatrix')
                splineIKHandle.connectPlugs(neckIKTipJoint[f'worldMatrix[{neckIKTipJoint.instanceNumber()}]'], 'dWorldUpMatrixEnd')
                splineIKEffector.setName(self.formatName(name='Neck', type='ikEffector'))

                self.userProperties['ikHandle'] = splineIKHandle.uuid()
                self.userProperties['ikEffector'] = splineIKEffector.uuid()

                # Setup spline IK stretch
                #
                neckIKCurveInfoName = self.formatName(name='Neck', type='curveInfo')
                neckCurveInfo = self.scene.createNode('curveInfo', name=neckIKCurveInfoName)
                neckCurveInfo.connectPlugs(neckIKCurveShape[f'worldSpace[{neckIKCurveShape.instanceNumber()}]'], 'inputCurve')

                neckIntermediateInfoName = self.formatName(name='Neck', subname='Intermediate', type='curveInfo')
                neckIntermediateInfo = self.scene.createNode('curveInfo', name=neckIntermediateInfoName)
                neckIntermediateInfo.connectPlugs(neckIKIntermediateShape[f'worldSpace[{neckIKIntermediateShape.instanceNumber()}]'], 'inputCurve')

                for (i, (startIKJoint, endIKJoint)) in enumerate(zip(neckIKJoints[:-1], neckIKJoints[1:])):

                    # Create distance-between nodes
                    #
                    index = i + 1

                    neckBaseDistanceName = self.formatName(name='Neck', subname='Length', index=index, type='distanceBetween')
                    neckBaseDistance = self.scene.createNode('distanceBetween', name=neckBaseDistanceName)
                    neckBaseDistance.connectPlugs(neckIntermediateInfo[f'controlPoints[{i}]'], 'point1')
                    neckBaseDistance.connectPlugs(neckIntermediateInfo[f'controlPoints[{i + 1}]'], 'point2')

                    neckStretchDistanceName = self.formatName(name='Neck', subname='IntermediateLength', index=index, type='distanceBetween')
                    neckStretchDistance = self.scene.createNode('distanceBetween', name=neckStretchDistanceName)
                    neckStretchDistance.connectPlugs(neckCurveInfo[f'controlPoints[{i}]'], 'point1')
                    neckStretchDistance.connectPlugs(neckCurveInfo[f'controlPoints[{i + 1}]'], 'point2')

                    # Create neck-length multiplier
                    #
                    neckStretchBlendName = self.formatName(name='Neck', subname='Length', index=index, type='blendTwoAttr')
                    neckStretchBlend = self.scene.createNode('blendTwoAttr', name=neckStretchBlendName)
                    neckStretchBlend.connectPlugs(headCtrl['stretch'], 'attributesBlender')
                    neckStretchBlend.connectPlugs(neckBaseDistance['distance'], 'input[0]')
                    neckStretchBlend.connectPlugs(neckStretchDistance['distance'], 'input[1]')
                    neckStretchBlend.connectPlugs('output', endIKJoint['translateX'])

                # Setup scale remap
                #
                neckScaleRemapName = self.formatName(name='Neck', subname='Scale', type='remapArray')
                neckScaleRemap = self.scene.createNode('remapArray', name=neckScaleRemapName)
                neckScaleRemap.clamped = True
                neckScaleRemap.setAttr('parameter', parameters)
                neckScaleRemap.connectPlugs(firstNeckFKCtrl['scale'], 'outputMin')
                neckScaleRemap.connectPlugs(headCtrl['scale'], 'outputMax')

                # Create neck micro controls
                #
                neckCtrls = [None] * neckCount

                for (i, (neckIKJoint, neckExportJoint)) in enumerate(zip(neckIKJoints, neckExportJoints)):  # It's okay if these mismatch since there is no tip export joint!

                    index = str(i + 1).zfill(2)

                    neckSpaceName = self.formatName(name='Neck', index=index, type='space')
                    neckSpace = self.scene.createNode('transform', name=neckSpaceName, parent=controlsGroup)
                    neckSpace.copyTransform(neckExportJoint, skipScale=True)
                    neckSpace.freezeTransform()
                    neckSpace.addConstraint('parentConstraint', [neckIKJoint], maintainOffset=True)

                    neckCtrlName = self.formatName(name='Neck', index=index, type='control')
                    neckCtrl = self.scene.createNode('transform', name=neckCtrlName, parent=neckSpace)
                    neckCtrl.addPointHelper('sphere', size=(6.0 * rigScale), colorRGB=darkColorRGB)
                    neckCtrl.prepareChannelBoxForAnimation()
                    self.publishNode(neckCtrl, alias=f'Neck{index}')

                    scaleConstraint = neckSpace.addConstraint('scaleConstraint', [neckFKCtrls[i].rot])
                    scaleConstraint.connectPlugs(neckScaleRemap[f'outValue[{i}]'], 'offset')

                    neckCtrls[i] = neckCtrl

                # Tag neck controllers
                #
                lastNeckIndex = neckCount - 1

                for i in range(neckCount):

                    neckFKRotCtrl, neckFKTransCtrl, neckCtrl  = neckFKCtrls[i].rot, neckFKCtrls[i].trans, neckCtrls[i]
                    previousCtrl = neckFKCtrls[i - 1].rot if (i > 0) else None
                    nextCtrl = neckFKCtrls[i + 1].rot if (i < lastNeckIndex) else None

                    neckFKRotCtrl.tagAsController(parent=previousCtrl, children=[nextCtrl, neckCtrl])

                headCtrl.tagAsController(parent=lastNeckFKCtrl)

            # Override last CV on spine IK curve
            #
            firstNeckFKCtrl, lastNeckFKCtrl = neckFKCtrls[0].rot, neckFKCtrls[-1].rot

            if spineExists:

                spineComponent = spineComponents[0]

                blendTransform = self.scene(spineComponent.userProperties['controlPointOverride'])
                blendTransform.connectPlugs(firstNeckFKCtrl['affectsSpine'], 'blender', force=True)

                multMatrix = self.scene(blendTransform['inMatrix2'].source().node())
                multMatrix.connectPlugs(firstNeckFKCtrl[f'worldMatrix[{firstNeckFKCtrl.instanceNumber()}]'], 'matrixIn[0]', force=True)
                multMatrix.connectPlugs(chestCtrl[f'worldInverseMatrix[{chestCtrl.instanceNumber()}]'], 'matrixIn[1]', force=True)
                multMatrix.connectPlugs(chestCtrl[f'parentMatrix[{chestCtrl.instanceNumber()}]'], 'matrixIn[2]', force=True)

            # Create head look-at control
            #
            firstNeckExportJoint, lastNeckExportJoint = neckExportJoints[0], neckExportJoints[-1]
            headLookAtMatrix = waistCtrl.worldMatrix() if (waistCtrl is not None) else firstNeckExportJoint.worldMatrix()

            headLookAtSpaceName = self.formatName(subname='LookAt', type='space')
            headLookAtSpace = self.scene.createNode('transform', name=headLookAtSpaceName, parent=controlsGroup)
            headLookAtSpace.setWorldMatrix(headLookAtMatrix, skipRotate=True, skipScale=True)
            headLookAtSpace.freezeTransform()

            headLookAtGroupName = self.formatName(subname='LookAt', type='transform')
            headLookAtGroup = self.scene.createNode('transform', name=headLookAtGroupName, parent=headLookAtSpace)
            headLookAtGroup.setWorldMatrix(headExportMatrix, skipRotate=True, skipScale=True)
            headLookAtGroup.freezeTransform()

            headLookAtCtrlName = self.formatName(subname='LookAt', type='control')
            headLookAtCtrl = self.scene.createNode('transform', name=headLookAtCtrlName, parent=headLookAtGroup)
            headLookAtCtrl.addPointHelper('sphere', 'centerMarker', size=(20.0 * rigScale), colorRGB=colorRGB)
            headLookAtCtrl.addAttr(longName='lookAtOffset', niceName='Look-At Offset', attributeType='distance', min=1.0, default=rigWidth, channelBox=True)
            headLookAtCtrl.hideAttr('scale', lock=True)
            headLookAtCtrl.prepareChannelBoxForAnimation()
            headLookAtCtrl.addDivider('Spaces')
            headLookAtCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            headLookAtCtrl.prepareChannelBoxForAnimation()
            headLookAtCtrl.tagAsController(parent=headCtrl)
            self.publishNode(headLookAtCtrl, alias='LookAt')

            headLookAtSpaceSwitch = headLookAtSpace.addSpaceSwitch([waistCtrl, motionCtrl], weighted=True, maintainOffset=True)
            headLookAtSpaceSwitch.setAttr('target', [{'targetReverse': (True, False, False), 'targetWeight': (0.0, 0.0, 1.0)}, {'targetWeight': (0.0, 1.0, 0.0)}])
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['localOrGlobal'], 'target[0].targetTranslateWeight')
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['localOrGlobal'], 'target[1].targetTranslateWeight')

            headLookAtCtrl.userProperties['space'] = headLookAtSpace.uuid()
            headLookAtCtrl.userProperties['group'] = headLookAtGroup.uuid()
            headLookAtCtrl.userProperties['spaceSwitch'] = headLookAtSpaceSwitch.uuid()

            # Setup head look-at offset
            #
            headLookAtMatrix = headLookAtGroup.getAttr('offsetParentMatrix')
            translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(headLookAtMatrix)

            headLookAtComposeMatrixName = self.formatName(subname='LookAt', type='composeMatrix')
            headLookAtComposeMatrix = self.scene.createNode('composeMatrix', name=headLookAtComposeMatrixName)
            headLookAtComposeMatrix.setAttr('inputTranslate', translation)
            headLookAtComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)

            headLookAtOffsetInverseName = self.formatName(subname='LookAt', type='floatMath')
            headLookAtOffsetInverse = self.scene.createNode('floatMath', name=headLookAtOffsetInverseName)
            headLookAtOffsetInverse.setAttr('operation', 5)  # Negate
            headLookAtOffsetInverse.connectPlugs(headLookAtCtrl['lookAtOffset'], 'inDistanceA')

            headLookAtOffsetComposeMatrixName = self.formatName(subname='LookAtOffset', type='composeMatrix')
            headLookAtOffsetComposeMatrix = self.scene.createNode('composeMatrix', name=headLookAtOffsetComposeMatrixName)
            headLookAtOffsetComposeMatrix.connectPlugs(headLookAtOffsetInverse['outDistance'], 'inputTranslateY')

            headLookAtMultMatrixName = self.formatName(subname='LookAt', type='multMatrix')
            headLookAtMultMatrix = self.scene.createNode('multMatrix', name=headLookAtMultMatrixName)
            headLookAtMultMatrix.connectPlugs(headLookAtOffsetComposeMatrix['outputMatrix'], 'matrixIn[0]')
            headLookAtMultMatrix.connectPlugs(headLookAtComposeMatrix['outputMatrix'], 'matrixIn[1]')
            headLookAtMultMatrix.connectPlugs('matrixSum', headLookAtGroup['offsetParentMatrix'])

            # Create head look-at curve
            #
            headLookAtShapeName = self.formatName(subname='LookAtHandle', type='curve')
            headLookAtShape = self.scene.createNode('nurbsCurve', name=f'{headLookAtShapeName}Shape', parent=headLookAtCtrl)
            headLookAtShape.setAttr('cached', shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1))
            headLookAtShape.useObjectColor = 2
            headLookAtShape.wireColorRGB = lightColorRGB

            headLookAtCurveFromPointName = self.formatName(subname='LookAtHandle', type='curveFromPoint')
            headLookAtCurveFromPoint = self.scene.createNode('curveFromPoint', name=headLookAtCurveFromPointName)
            headLookAtCurveFromPoint.degree = 1
            headLookAtCurveFromPoint.connectPlugs(headLookAtCtrl[f'worldMatrix[{headLookAtCtrl.instanceNumber()}]'], 'inputMatrix[0]')
            headLookAtCurveFromPoint.connectPlugs(headCtrl[f'worldMatrix[{headCtrl.instanceNumber()}]'], 'inputMatrix[1]')
            headLookAtCurveFromPoint.connectPlugs(headLookAtShape[f'parentInverseMatrix[{headLookAtShape.instanceNumber()}]'], 'parentInverseMatrix')
            headLookAtCurveFromPoint.connectPlugs('outputCurve', headLookAtShape['create'])

            # Create default head look-at target
            #
            headDefaultTargetName = self.formatName(subname='Default', type='target')
            headDefaultTarget = self.scene.createNode('transform', name=headDefaultTargetName, parent=privateGroup)
            headDefaultTarget.displayLocalAxis = True
            headDefaultTarget.setWorldMatrix(headExportMatrix)
            headDefaultTarget.freezeTransform()

            headCtrl.addDivider('Spaces')
            headCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (Neck)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (Neck)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            headDefaultSpaceSwitch = headDefaultTarget.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, chestCtrl, lastNeckFKCtrl], weighted=True, maintainOffset=True)
            headDefaultSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 1.0, 1.0)}])
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')

            # Next, create head look-at target
            #
            headLookAtTargetName = self.formatName(subname='LookAt', type='target')
            headLookAtTarget = self.scene.createNode('transform', name=headLookAtTargetName, parent=privateGroup)
            headLookAtTarget.displayLocalAxis = True
            headLookAtTarget.addConstraint(
                'aimConstraint',
                [headLookAtCtrl],
                aimVector=(0.0, 1.0, 0.0),
                upVector=(1.0, 0.0, 0.0),
                worldUpType=2,
                worldUpVector=(0.0, 0.0, 1.0),
                worldUpObject=headLookAtCtrl
            )

            headLookAtMultMatrixName = self.formatName(subname='LookAt', type='multMatrix')
            headLookAtMultMatrix = self.scene.createNode('multMatrix', name=headLookAtMultMatrixName)
            headLookAtMultMatrix.connectPlugs(headDefaultSpaceSwitch['outputWorldMatrix'], 'matrixIn[0]')
            headLookAtMultMatrix.connectPlugs(headLookAtTarget[f'parentInverseMatrix[{headLookAtTarget.instanceNumber()}]'], 'matrixIn[1]')

            headLookAtDecomposeMatrixName = self.formatName(subname='LookAt', type='decomposeMatrix')
            headLookAtDecomposeMatrix = self.scene.createNode('decomposeMatrix', name=headLookAtDecomposeMatrixName)
            headLookAtDecomposeMatrix.connectPlugs(headLookAtTarget['rotateOrder'], 'inputRotateOrder')
            headLookAtDecomposeMatrix.connectPlugs(headLookAtMultMatrix['matrixSum'], 'inputMatrix')
            headLookAtDecomposeMatrix.connectPlugs('outputTranslate', headLookAtTarget['translate'])
            headLookAtDecomposeMatrix.connectPlugs('outputScale', headLookAtTarget['scale'])

            headLookAtCtrl.userProperties['space'] = headLookAtSpace.uuid()
            headLookAtCtrl.userProperties['group'] = headLookAtGroup.uuid()
            headLookAtCtrl.userProperties['target'] = headLookAtTarget.uuid()

            # Finally, add space switch using default and look-at targets
            #
            headSpaceSwitch = headSpace.addSpaceSwitch([headDefaultTarget, headLookAtTarget], weighted=True, maintainOffset=True)
            headSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            headSpaceSwitch.connectPlugs(headCtrl['lookAt'], 'target[0].targetWeight')
            headSpaceSwitch.connectPlugs(headCtrl['lookAt'], 'target[1].targetWeight')

            headCtrl.userProperties['space'] = headSpace.uuid()
            headCtrl.userProperties['spaceSwitch'] = headSpaceSwitch.uuid()

        else:

            # Add custom attributes to head control
            #
            headCtrl.addDivider('Spaces')
            headCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            # Add space switch to head control
            #
            headSpaceSwitch = headSpace.addSpaceSwitch([parentExportCtrl, motionCtrl], weighted=True, maintainOffset=True)
            headSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            headSpaceSwitch.connectPlugs(headCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            headSpaceSwitch.connectPlugs(headCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

            headCtrl.userProperties['space'] = headSpace.uuid()
            headCtrl.userProperties['spaceSwitch'] = headSpaceSwitch.uuid()
    # endregion
