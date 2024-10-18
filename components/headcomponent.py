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

        # Decompose component
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

        controlRig = self.findControlRig()
        rigDiameter = float(controlRig.rigRadius) * 2.0
        rigScale = controlRig.getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Get space switch options
        #
        neckEnabled = bool(neckSpecs[0].enabled)

        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        spineComponent = self.findComponentAncestors('SpineComponent')[0]
        cogCtrl = spineComponent.getPublishedNode('COG')
        waistCtrl = spineComponent.getPublishedNode('Waist')
        chestCtrl = spineComponent.getPublishedNode('Chest')

        # Create head control
        #
        headTargetName = self.formatName(type='target')
        headTarget = self.scene.createNode('transform', name=headTargetName, parent=privateGroup)
        headTarget.displayLocalAxis = True
        headTarget.visibility = False
        headTarget.setWorldMatrix(headMatrix)
        headTarget.freezeTransform()

        headSpaceName = self.formatName(type='space')
        headSpace = self.scene.createNode('transform', name=headSpaceName, parent=controlsGroup)
        headSpace.setWorldMatrix(headMatrix)
        headSpace.freezeTransform()

        headCtrlName = self.formatName(type='control')
        headCtrl = self.scene.createNode('transform', name=headCtrlName, parent=headSpace)
        headCtrl.addShape('CrownCurve', localPosition=(15.0 * rigScale, 0.0, 0.0), size=(15.0 * rigScale), colorRGB=colorRGB, lineWidth=4.0)
        headCtrl.addDivider('Settings')
        headCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, keyable=True)
        headCtrl.addAttr(longName='lookAt', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        headCtrl.addAttr(longName='lookAtOffset', niceName='Look-At Offset', attributeType='distance', min=1.0, default=rigDiameter, channelBox=True)
        headCtrl.prepareChannelBoxForAnimation()
        self.publishNode(headCtrl, alias='Head')

        # Create head look-at control
        #
        headLookAtSpaceName = self.formatName(subname='LookAt', type='space')
        headLookAtSpace = self.scene.createNode('transform', name=headLookAtSpaceName, parent=controlsGroup)
        headLookAtSpace.copyTransform(waistCtrl, skipRotate=True, skipScale=True)
        headLookAtSpace.freezeTransform()

        headLookAtGroupName = self.formatName(subname='LookAt', type='transform')
        headLookAtGroup = self.scene.createNode('transform', name=headLookAtGroupName, parent=headLookAtSpace)
        headLookAtGroup.setWorldMatrix(headMatrix, skipRotate=True, skipScale=True)
        headLookAtGroup.freezeTransform()

        headLookAtCtrlName = self.formatName(subname='LookAt', type='control')
        headLookAtCtrl = self.scene.createNode('transform', name=headLookAtCtrlName, parent=headLookAtGroup)
        headLookAtCtrl.addPointHelper('sphere', 'centerMarker', size=(20.0 * rigScale), colorRGB=colorRGB)
        headLookAtCtrl.addDivider('Settings')
        headLookAtCtrl.addAttr(longName='followBody', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        headLookAtCtrl.addProxyAttr('lookAt', headCtrl['lookAt'])
        headLookAtCtrl.addProxyAttr('lookAtOffset', headCtrl['lookAtOffset'])
        headLookAtCtrl.hideAttr('scale', lock=True)
        headLookAtCtrl.prepareChannelBoxForAnimation()
        self.publishNode(headLookAtCtrl, alias='LookAt')

        headLookAtSpaceSwitch = headLookAtSpace.addSpaceSwitch([motionCtrl, waistCtrl], weighted=True, maintainOffset=True)
        headLookAtSpaceSwitch.setAttr('target', [{'targetReverse': (True, False, False), 'targetWeight': (0.0, 1.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
        headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['followBody'], 'target[0].targetTranslateWeight')
        headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['followBody'], 'target[1].targetTranslateWeight')

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
        headLookAtOffsetInverse.connectPlugs(headCtrl['lookAtOffset'], 'inDistanceA')

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
        curveData = shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1)

        headLookAtShapeName = self.formatName(subname='LookAtHandle', type='control')
        headLookAtShape = self.scene.createNode('nurbsCurve', name=f'{headLookAtShapeName}Shape', parent=headLookAtCtrl)
        headLookAtShape.setAttr('cached', curveData)
        headLookAtShape.useObjectColor = 2
        headLookAtShape.wireColorRGB = lightColorRGB

        for (i, node) in enumerate([headLookAtCtrl, headCtrl]):

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

        # Create head look-at target
        #
        headLookAtTargetName = self.formatName(subname='LookAt', type='target')
        headLookAtTarget = self.scene.createNode('transform', name=headLookAtTargetName, parent=privateGroup)
        headLookAtTarget.displayLocalAxis = True
        headLookAtTarget.addConstraint('transformConstraint', [headTarget], skipRotate=True)
        headLookAtTarget.addConstraint('aimConstraint', [headLookAtCtrl], aimVector=(0.0, 1.0, 0.0), upVector=(1.0, 0.0, 0.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=headLookAtCtrl)

        headLookAtCtrl.userProperties['space'] = headLookAtSpace.uuid()
        headLookAtCtrl.userProperties['spaceSwitch'] = headLookAtSpaceSwitch.uuid()
        headLookAtCtrl.userProperties['group'] = headLookAtGroup.uuid()
        headLookAtCtrl.userProperties['target'] = headLookAtTarget.uuid()

        # Check if neck was enabled
        #
        if neckEnabled:

            # Evaluate neck links
            #
            neckCount = len(neckSpecs)

            if neckCount == 1:

                # Create neck control
                #
                neckExportJoint = neckExportJoints[0]

                neckSpaceName = self.formatName(name='Neck', type='space')
                neckSpace = self.scene.createNode('transform', name=neckSpaceName, parent=controlsGroup)
                neckSpace.copyTransform(neckExportJoint)
                neckSpace.freezeTransform()

                neckCtrlName = self.formatName(name='Neck', type='control')
                neckCtrl = self.scene.createNode('transform', name=neckCtrlName, parent=neckSpace)
                neckCtrl.addPointHelper('disc', size=(15.0 * rigScale), colorRGB=lightColorRGB, lineWidth=2.0)
                neckCtrl.addDivider('Settings')
                neckCtrl.addAttr(longName='inheritsTwist', attributeType='angle', min=0.0, max=1.0, default=0.5, keyable=True)
                neckCtrl.addDivider('Spaces')
                neckCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
                neckCtrl.prepareChannelBoxForAnimation()
                self.publishNode(neckCtrl, alias='Neck')

                neckSpaceSwitch = neckSpace.addSpaceSwitch([parentExportCtrl, motionCtrl], weighted=True, maintainOffset=True)
                neckSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                neckSpaceSwitch.connectPlugs(neckCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                neckSpaceSwitch.connectPlugs(neckCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                neckCtrl.userProperties['space'] = neckSpace.uuid()
                neckCtrl.userProperties['spaceSwitch'] = neckSpaceSwitch.uuid()

                headTarget.setParent(neckCtrl, absolute=True)
                headTarget.freezeTransform()

                # Setup head space switching
                #
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

                headDefaultTargetName = self.formatName(subname='Default', type='target')
                headDefaultTarget = self.scene.createNode('transform', name=headDefaultTargetName, parent=privateGroup)
                headDefaultTarget.displayLocalAxis = True
                headDefaultTarget.setWorldMatrix(headMatrix)
                headDefaultTarget.freezeTransform()

                headDefaultSpaceSwitch = headDefaultTarget.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, chestCtrl, neckCtrl], weighted=True, maintainOffset=True)
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

                headSpaceSwitch = headSpace.addSpaceSwitch([headDefaultTarget, headLookAtTarget], weighted=True, maintainOffset=True)
                headSpaceSwitch.setAttr('target[0].targetReverse', (True, True, True))
                headSpaceSwitch.connectPlugs(headCtrl['lookAt'], 'target[0].targetWeight')
                headSpaceSwitch.connectPlugs(headCtrl['lookAt'], 'target[1].targetWeight')

                headCtrl.userProperties['space'] = headSpace.uuid()
                headCtrl.userProperties['spaceSwitch'] = headSpaceSwitch.uuid()

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

                neckIKJoint.addConstraint('pointConstraint', [neckCtrl])
                constraint = neckIKJoint.addConstraint('aimConstraint', [headCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 1.0, 0.0), worldUpType=2, worldUpVector=(0.0, 1.0, 0.0), worldUpObject=neckCtrl)
                neckIKJoint.addConstraint('scaleConstraint', [neckCtrl])

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

                neckTwistEnvelopeName = self.formatName(name='Neck', subname='TwistEnvelope', type='floatMath')
                neckTwistEnvelope = self.scene.createNode('floatMath', name=neckTwistEnvelopeName)
                neckTwistEnvelope.operation = 2  # Multiply
                neckTwistEnvelope.connectPlugs(neckTwistSolver['roll'], 'inAngleA')
                neckTwistEnvelope.connectPlugs(neckCtrl['inheritsTwist'], 'inAngleB')

                constraint.connectPlugs(neckTwistEnvelope['outAngle'], 'offsetX')

                # Tag controllers
                #
                neckCtrl.tagAsController(children=[headCtrl])
                headCtrl.tagAsController(parent=neckCtrl, children=[headLookAtCtrl])
                headLookAtCtrl.tagAsController(parent=headCtrl)

            else:

                raise NotImplementedError()  # TODO: Implement spline IK for neck!

        else:

            # Setup head space switching
            #
            headCtrl.addDivider('Spaces')
            headCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True)
            headCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            headDefaultTargetName = self.formatName(subname='Default', type='target')
            headDefaultTarget = self.scene.createNode('transform', name=headDefaultTargetName, parent=privateGroup)
            headDefaultTarget.displayLocalAxis = True
            headDefaultTarget.setWorldMatrix(headMatrix)
            headDefaultTarget.freezeTransform()

            headDefaultSpaceSwitch = headDefaultTarget.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl, chestCtrl], weighted=True, maintainOffset=True)
            headDefaultSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 1.0, 1.0)}])
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            headDefaultSpaceSwitch.connectPlugs(headCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')

            headSpaceSwitch = headSpace.addSpaceSwitch([headDefaultTarget, headLookAtTarget], weighted=True, maintainOffset=True)
            headSpaceSwitch.setAttr('target[0].targetReverse', (True, True, True))
            headSpaceSwitch.connectPlugs(headCtrl['lookAt'], 'target[0].targetWeight')
            headSpaceSwitch.connectPlugs(headCtrl['lookAt'], 'target[1].targetWeight')

            headCtrl.userProperties['space'] = headSpace.uuid()
            headCtrl.userProperties['spaceSwitch'] = headSpaceSwitch.uuid()

            # Constrain head target
            #
            headTarget.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

            # Connect head look-at to parent control
            #
            headLookAtSpaceSwitch = headLookAtSpace.addSpaceSwitch([motionCtrl, cogCtrl, parentExportCtrl], weighted=True, maintainOffset=True)
            headLookAtSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW0'], 'target[0].targetRotateWeight')
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW1'], 'target[1].targetRotateWeight')
            headLookAtSpaceSwitch.connectPlugs(headLookAtCtrl['positionSpaceW2'], 'target[2].targetRotateWeight')

            headLookAtTarget.addConstraint('scaleConstraint', [parentExportCtrl])
    # endregion
