from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.maya.libs import transformutils, shapeutils
from dcc.dataclasses.colour import Colour
from rigomatic.libs import kinematicutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class HeadComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements head components.
    """

    # region Attributes
    neckEnabled = mpyattribute.MPyAttribute('neckEnabled', attributeType='bool', default=True)
    numNeckLinks = mpyattribute.MPyAttribute('numNeckLinks', attributeType='int', min=1, default=1)
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Head'
    __default_neck_spacing__ = 10.0
    __default_neck_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 200.0, 1.0)
        ]
    )
    __default_head_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0)
        ]
    )
    # endregion

    # region Properties
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
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Edit skeleton specs
        #
        neckCount = int(self.numNeckLinks)
        skeletonCount = neckCount + 1
        *neckSpecs, headSpec = self.resizeSkeletonSpecs(skeletonCount, skeletonSpecs)

        neckEnabled = bool(self.neckEnabled)

        if neckCount == 1:

            neckSpec = neckSpecs[0]
            neckSpec.name = self.formatName(name='Neck')
            neckSpec.driver = self.formatName(name='Neck', subname='IK', type='joint')
            neckSpec.enabled = neckEnabled

        else:

            for (i, neckSpec) in enumerate(neckSpecs, start=1):

                neckSpec.name = self.formatName(name='Neck', index=i)
                neckSpec.driver = self.formatName(name='Neck', index=i, type='control')
                neckSpec.enabled = neckEnabled

        headSpec.name = self.formatName()
        headSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(HeadComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        componentSide = self.Side(self.componentSide)
        *neckSpecs, headSpec = self.skeletonSpecs()

        # Create neck joints
        #
        neckCount = len(neckSpecs)
        neckJoints = [None] * neckCount

        neckEnabled = neckSpecs[0].enabled

        if neckEnabled:

            for (i, neckSpec) in enumerate(neckSpecs):

                parent = neckJoints[i - 1] if (i > 0) else None

                neckJoint = self.scene.createNode('joint', name=neckSpec.name, parent=parent)
                neckJoint.side = componentSide
                neckJoint.type = self.Type.NECK
                neckJoint.displayLocalAxis = True
                neckSpec.uuid = neckJoint.uuid()

                defaultNeckMatrix = self.__default_neck_matrix__ * transformutils.createTranslateMatrix([0.0, 0.0, (i * self.__default_neck_spacing__)])
                neckMatrix = neckSpec.getMatrix(default=defaultNeckMatrix)
                neckJoint.setWorldMatrix(neckMatrix)

                neckJoints[i] = neckJoint

        # Create head joint
        #
        parent = neckJoints[-1] if neckEnabled else None

        headJoint = self.scene.createNode('joint', name=headSpec.name, parent=parent)
        headJoint.side = componentSide
        headJoint.type = self.Type.HEAD
        headJoint.displayLocalAxis = True
        headSpec.uuid = headJoint.uuid()

        defaultHeadMatrix = self.__default_neck_matrix__ * transformutils.createTranslateMatrix([0.0, 0.0, (neckCount * self.__default_neck_spacing__)])
        headMatrix = headSpec.getMatrix(default=defaultHeadMatrix)
        headJoint.setWorldMatrix(headMatrix)

        return (*neckJoints, headJoint)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Get component properties
        #
        *neckSpecs, headSpec = self.skeletonSpecs()
        neckExportJoints = [self.scene(neckSpec.uuid) for neckSpec in neckSpecs]
        headExportJoint = self.scene(headSpec.uuid)
        headMatrix = headExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        # Get space switch options
        #
        neckEnabled = bool(neckSpecs[0].enabled)
        parentAlias = 'Neck' if neckEnabled else 'Chest'

        rootComponent = self.findRootComponent()
        spineComponent = self.findComponentAncestors('SpineComponent')[0]

        worldCtrl = rootComponent.getPublishedNode('Motion')
        cogCtrl = spineComponent.getPublishedNode('Waist')
        chestCtrl = spineComponent.getPublishedNode('Chest')

        # Create head control
        #
        headSpaceName = self.formatName(type='space')
        headSpace = self.scene.createNode('transform', name=headSpaceName, parent=controlsGroup)
        headSpace.setWorldMatrix(headMatrix)
        headSpace.freezeTransform()

        headCtrlName = self.formatName(type='control')
        headCtrl = self.scene.createNode('transform', name=headCtrlName, parent=headSpace)
        headCtrl.addShape('VisorCurve', size=20.0, colorRGB=colorRGB, lineWidth=4.0)
        headCtrl.addDivider('Customize')
        headCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, keyable=True)
        headCtrl.addAttr(longName='displayLookAt', niceName='Display Look-At', attributeType='bool', channelBox=True)
        headCtrl.addAttr(longName='lookAtOffset', niceName='Look-At Offset', attributeType='distance', min=1.0, default=100.0, channelBox=True)
        headCtrl.addDivider('Space')
        headCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        headCtrl.prepareChannelBoxForAnimation()
        self.publishNode(headCtrl, alias='Head')

        # Create head look-at control
        #
        headLookAtSpaceName = self.formatName(subname='LookAt', type='space')
        headLookAtSpace = self.scene.createNode('transform', name=headLookAtSpaceName, parent=controlsGroup)
        headLookAtSpace.setWorldMatrix(headMatrix)
        headLookAtSpace.freezeTransform()

        headLookAtCtrlName = self.formatName(subname='LookAt', type='control')
        headLookAtCtrl = self.scene.createNode('transform', name=headLookAtCtrlName, parent=headLookAtSpace)
        headLookAtCtrl.freezeTransform()
        headLookAtCtrl.addPointHelper('sphere', 'centerMarker', size=20.0, colorRGB=colorRGB)
        headLookAtCtrl.addDivider('Customize')
        headLookAtCtrl.addProxyAttr('displayLookAt', headCtrl['displayLookAt'])
        headLookAtCtrl.addProxyAttr('lookAtOffset', headCtrl['lookAtOffset'])
        headLookAtCtrl.addDivider('Space')
        headLookAtCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        headLookAtCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        headLookAtCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
        headLookAtCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (Neck)', attributeType='float', min=0.0, max=1.0, keyable=True)
        headLookAtCtrl.hideAttr('scale', lock=True)
        headLookAtCtrl.connectPlugs(headCtrl['displayLookAt'], 'visibility')
        headLookAtCtrl.prepareChannelBoxForAnimation()
        self.publishNode(headLookAtCtrl, alias='LookAt')

        headLookAtComposeMatrixName = self.formatName(subname='LookAt', type='composeMatrix')
        headLookAtComposeMatrix = self.scene.createNode('composeMatrix', name=headLookAtComposeMatrixName)
        headLookAtComposeMatrix.connectPlugs(headCtrl['lookAtOffset'], 'inputTranslateY')
        headLookAtComposeMatrix.connectPlugs('outputMatrix', headLookAtCtrl['offsetParentMatrix'])

        headLookAtTargetName = self.formatName(subname='LookAt', type='target')
        headLookAtTarget = self.scene.createNode('transform', name=headLookAtTargetName, parent=privateGroup)
        headLookAtTarget.displayLocalAxis = True
        headLookAtTarget.addConstraint('pointConstraint', [headLookAtSpace])
        headLookAtTarget.addConstraint('aimConstraint', [headLookAtCtrl], aimVector=(0.0, 1.0, 0.0), upVector=(1.0, 0.0, 0.0), worldUpType=2, worldUpVector=(1.0, 0.0, 0.0), worldUpObject=headLookAtCtrl)

        headLookAtCtrl.userProperties['space'] = headLookAtSpace.uuid()
        headLookAtCtrl.userProperties['compose'] = headLookAtComposeMatrix.uuid()
        headLookAtCtrl.userProperties['target'] = headLookAtTarget.uuid()

        # Create head look-at curve
        #
        headLookAtMatrix = headLookAtCtrl.worldMatrix()
        controlPoints = [transformutils.breakMatrix(matrix)[3] for matrix in (headLookAtMatrix, headMatrix)]
        curveData = shapeutils.createCurveFromPoints(controlPoints, degree=1)

        headLookAtShapeName = self.formatName(subname='LookAtHandle', type='control')
        headLookAtShape = self.scene.createNode('nurbsCurve', name=f'{headLookAtShapeName}Shape', parent=headLookAtCtrl)
        headLookAtShape.setAttr('cached', curveData)
        headLookAtShape.useObjectColor = 2
        headLookAtShape.wireColorRGB = lightColorRGB

        nodes = [headLookAtCtrl, headCtrl]

        for (i, node) in enumerate(nodes):

            index = i + 1

            multMatrixName = self.formatName(subname='ControlPoint', index=index, type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(node[f'worldMatrix[{node.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(headLookAtShape[f'parentInverseMatrix[{headLookAtShape.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(subname='ControlPoint', index=index, type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', headLookAtShape[f'controlPoints[{i}].xValue'])
            breakMatrix.connectPlugs('row4Y', headLookAtShape[f'controlPoints[{i}].yValue'])
            breakMatrix.connectPlugs('row4Z', headLookAtShape[f'controlPoints[{i}].zValue'])

        # Setup head space switch
        #
        headSpaceSwitch = headSpace.addSpaceSwitch([headLookAtTarget, worldCtrl], maintainOffset=True)
        headSpaceSwitch.weighted = True
        headSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        headSpaceSwitch.connectPlugs(headCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        headSpaceSwitch.connectPlugs(headCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

        headCtrl.userProperties['space'] = headSpace.uuid()
        headCtrl.userProperties['spaceSwitch'] = headSpaceSwitch.uuid()

        # Check if neck was enabled
        #
        if not neckEnabled:

            raise NotImplementedError()

        # Evaluate neck links
        #
        neckCount = len(neckSpecs)

        if neckCount == 1:

            # Decompose neck spec
            #
            neckSpec = neckSpecs[0]
            neckExportJoint = self.scene(neckSpec.uuid)

            # Create neck control
            #
            neckSpaceName = self.formatName(name='Neck', type='space')
            neckSpace = self.scene.createNode('transform', name=neckSpaceName, parent=controlsGroup)
            neckSpace.copyTransform(neckExportJoint)
            neckSpace.freezeTransform()

            neckCtrlName = self.formatName(name='Neck', type='control')
            neckCtrl = self.scene.createNode('transform', name=neckCtrlName, parent=neckSpace)
            neckCtrl.addPointHelper('disc', size=15.0, colorRGB=lightColorRGB, lineWidth=2.0)
            neckCtrl.addDivider('Customize')
            neckCtrl.addAttr(longName='inheritsTwist', attributeType='angle', min=0.0, max=1.0, default=0.5, keyable=True)
            neckCtrl.addDivider('Space')
            neckCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
            neckCtrl.prepareChannelBoxForAnimation()
            self.publishNode(neckCtrl, alias='Neck')

            neckSpaceSwitch = neckSpace.addSpaceSwitch([chestCtrl, worldCtrl], maintainOffset=True)
            neckSpaceSwitch.weighted = True
            neckSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            neckSpaceSwitch.connectPlugs(neckCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
            neckSpaceSwitch.connectPlugs(neckCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

            neckCtrl.userProperties['space'] = neckSpace.uuid()
            neckCtrl.userProperties['spaceSwitch'] = neckSpaceSwitch.uuid()

            # Connect head look-at to neck control
            #
            headLookAtSpaceSwitch = headLookAtSpace.addSpaceSwitch([worldCtrl, cogCtrl, chestCtrl, neckCtrl], maintainOffset=True)
            headLookAtSpaceSwitch.weighted = True
            headLookAtSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 0.0, 1.0)}])
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW0'], 'target[0].targetRotateWeight')
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW1'], 'target[1].targetRotateWeight')
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW2'], 'target[2].targetRotateWeight')
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW3'], 'target[3].targetRotateWeight')

            # Create neck IK joints
            #
            neckIKJointName = self.formatName(name='Neck', kinemat='IK', type='joint')
            neckIKJoint = self.scene.createNode('joint', name=neckIKJointName, parent=jointsGroup)
            neckIKJoint.copyTransform(neckExportJoint)
            neckIKJoint.freezePivots(includeTranslate=False, includeScale=False)

            neckIKTipJointName = self.formatName(name='Neck', kinemat='IK', subname='Tip', type='joint')
            neckIKTipJoint = self.scene.createNode('joint', name=neckIKTipJointName, parent=neckIKJoint)
            neckIKTipJoint.copyTransform(headExportJoint)
            neckIKTipJoint.freezePivots(includeTranslate=False, includeScale=False)

            neckIKHandle, neckIKEffector = kinematicutils.applySingleChainSolver(neckIKJoint, neckIKTipJoint)

            neckIKEffector.setName(self.formatName(name='Neck', type='ikEffector'))
            neckIKHandle.setName(self.formatName(name='Neck', type='ikHandle'))
            neckIKHandle.setParent(privateGroup)

            neckIKJoint.addConstraint('pointConstraint', [neckCtrl])
            neckIKHandle.addConstraint('pointConstraint', [headCtrl])

            # Setup neck stretch
            #
            neckLengthMultMatrixName = self.formatName(subname='Length', type='multMatrix')
            neckLengthMultMatrix = self.scene.createNode('multMatrix', name=neckLengthMultMatrixName)
            neckLengthMultMatrix.connectPlugs(headCtrl[f'parentMatrix[{headCtrl.instanceNumber()}]'], 'matrixIn[0]')
            neckLengthMultMatrix.connectPlugs(neckCtrl[f'parentInverseMatrix[{neckCtrl.instanceNumber()}]'], 'matrixIn[1]')

            neckLengthName = self.formatName(subname='Length', type='distanceBetween')
            neckLength = self.scene.createNode('distanceBetween', name=neckLengthName)
            neckLength.connectPlugs(neckCtrl['matrix'], 'inMatrix1')
            neckLength.connectPlugs(neckLengthMultMatrix['matrixSum'], 'inMatrix2')

            headDistanceMultMatrixName = self.formatName(subname='Distance', type='multMatrix')
            headDistanceMultMatrix = self.scene.createNode('multMatrix', name=headDistanceMultMatrixName)
            headDistanceMultMatrix.connectPlugs(headCtrl[f'worldMatrix[{headCtrl.instanceNumber()}]'], 'matrixIn[0]')
            headDistanceMultMatrix.connectPlugs(neckCtrl[f'parentInverseMatrix[{neckCtrl.instanceNumber()}]'], 'matrixIn[1]')

            headDistanceName = self.formatName(subname='Distance', type='distanceBetween')
            headDistance = self.scene.createNode('distanceBetween', name=headDistanceName)
            headDistance.connectPlugs(neckCtrl['matrix'], 'inMatrix1')
            headDistance.connectPlugs(headDistanceMultMatrix['matrixSum'], 'inMatrix2')

            headStretchBlendName = self.formatName(subname='Stretch', type='blendTwoAttr')
            headStretchBlend = self.scene.createNode('blendTwoAttr', name=headStretchBlendName)
            headStretchBlend.connectPlugs(headCtrl['stretch'], 'attributesBlender')
            headStretchBlend.connectPlugs(neckLength['distance'], 'input[0]')
            headStretchBlend.connectPlugs(headDistance['distance'], 'input[1]')
            headStretchBlend.connectPlugs('output', neckIKTipJoint['translateX'])

            # Setup neck twist
            #
            neckTwistSolverName = self.formatName(name='Neck', subname='Twist', type='twistSolver')
            neckTwistSolver = self.scene.createNode('twistSolver', name=neckTwistSolverName)
            neckTwistSolver.forwardAxis = 0  # X
            neckTwistSolver.upAxis = 2  # Z
            neckTwistSolver.segments = 2
            neckTwistSolver.connectPlugs(neckCtrl[f'worldMatrix[{neckCtrl.instanceNumber()}]'], 'startMatrix')
            neckTwistSolver.connectPlugs(headCtrl[f'worldMatrix[{headCtrl.instanceNumber()}]'], 'endMatrix')

            neckTwistEnvelopeName = self.formatName(name='Neck', subname='TwistEnvelope', type='linearMath')
            neckTwistEnvelope = self.scene.createNode('linearMath', name=neckTwistEnvelopeName)
            neckTwistEnvelope.operation = 2  # Multiply
            neckTwistEnvelope.connectPlugs(neckTwistSolver['roll'], 'inAngleA')
            neckTwistEnvelope.connectPlugs(neckCtrl['inheritsTwist'], 'inAngleB')

            constraint = neckIKHandle.addConstraint('orientConstraint', [neckCtrl])
            constraint.connectPlugs(neckTwistEnvelope['outAngle'], 'offsetX')

            # Tag controllers
            #
            neckCtrl.tagAsController(children=[headCtrl])
            headCtrl.tagAsController(parent=neckCtrl, children=[headLookAtCtrl])
            headLookAtCtrl.tagAsController(parent=headCtrl)

            # Constraint joints
            #
            neckExportJoint.addConstraint('pointConstraint', [neckCtrl])
            neckExportJoint.addConstraint('orientConstraint', [neckIKJoint])
            neckExportJoint.addConstraint('scaleConstraint', [neckCtrl])

            headExportJoint.addConstraint('pointConstraint', [neckIKTipJoint])
            headExportJoint.addConstraint('orientConstraint', [headCtrl])
            headExportJoint.addConstraint('scaleConstraint', [headCtrl])

        else:

            raise NotImplementedError()
    # endregion
