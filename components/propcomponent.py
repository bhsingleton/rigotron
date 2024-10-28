from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import transformutils, shapeutils
from . import basecomponent
from ..libs import Side, Type

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PropComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements prop components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Prop'
    __default_prop_matrices__ = {
        Side.LEFT: om.MMatrix(
            [
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (100.0, 0.0, 150.0, 1.0)
            ]
        ),
        Side.RIGHT: om.MMatrix(
            [
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (-100.0, 0.0, 150.0, 1.0)
            ]
        ),
        Side.CENTER: om.MMatrix(
            [
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (0.0, -50.0, 150.0, 1.0)
            ]
        )
    }
    # endregion

    # region Attributes
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
        propSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        propSpec.name = self.formatName()
        propSpec.driver = self.formatName(subname='Offset', type='control')

        # Call parent method
        #
        super(PropComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        componentSide = self.Side(self.componentSide)
        propSpec, = self.skeletonSpecs()

        # Create upper joint
        #
        jointType = self.Type.PROP_A if (componentSide == self.Side.LEFT) else self.Type.PROP_B if (componentSide == self.Side.RIGHT) else self.Type.PROP_C

        propJoint = self.scene.createNode('joint', name=propSpec.name)
        propJoint.side = componentSide
        propJoint.type = jointType
        propJoint.drawStyle = self.Style.JOINT
        propJoint.displayLocalAxis = True
        propSpec.uuid = propJoint.uuid()

        defaultPropMatrix = self.__default_prop_matrices__[componentSide]
        propMatrix = propSpec.getMatrix(default=defaultPropMatrix)
        propJoint.setWorldMatrix(propMatrix)

        return (propJoint,)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        propSpec, = self.skeletonSpecs()
        propExportJoint = self.scene(propSpec.uuid)
        propMatrix = propExportJoint.worldMatrix()

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

        # Create prop control
        #
        propSpaceName = self.formatName(type='space')
        propSpace = self.scene.createNode('transform', name=propSpaceName, parent=controlsGroup)
        propSpace.setWorldMatrix(mirrorMatrix * propMatrix)
        propSpace.freezeTransform()

        propSpaceSwitch = propSpace.addSpaceSwitch([], maintainOffset=True)
        propSpaceSwitch.weighted = True

        propCtrlName = self.formatName(type='control')
        propCtrl = self.scene.createNode('transform', name=propCtrlName, parent=propSpace)
        propCtrl.addPointHelper('cross', size=15.0, colorRGB=colorRGB, lineWidth=4.0)
        propCtrl.prepareChannelBoxForAnimation()
        self.publishNode(propCtrl, alias='Prop')

        propOffsetCtrl = self.scene.createNode('transform', name=propSpec.driver, parent=propCtrl)
        propOffsetCtrl.addPointHelper('cylinder', size=15.0, colorRGB=lightColorRGB, lineWidth=2.0)
        propOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(propOffsetCtrl, alias='Offset')

        propCtrl.userProperties['space'] = propSpace.uuid()
        propCtrl.userProperties['offset'] = propOffsetCtrl.uuid()
        propCtrl.userProperties['spaceSwitch'] = propSpaceSwitch.uuid()

    def repairOppositeRig(self):
        """
        Repairs any broken connections on the opposite prop component.

        :rtype: None
        """

        # Check if opposite control exists
        #
        propCtrl = self.getPublishedNode('Prop')
        oppositePropCtrl = propCtrl.getOppositeNode()

        hasOpposite = oppositePropCtrl is not self

        if not hasOpposite:

            return

        # Get opposite space switch
        #
        oppositePropOffsetCtrl = self.scene(oppositePropCtrl.userProperties['offset'])
        oppositePropSpaceSwitch = self.scene(oppositePropCtrl.userProperties['spaceSwitch'])

        for target in oppositePropSpaceSwitch.targets():

            targetNode = self.scene(target.name())
            targetNode.connectPlugs(f'worldMatrix[{targetNode.instanceNumber()}]', oppositePropSpaceSwitch[f'target[{target.index}].targetMatrix'], force=True)

    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.

        :rtype: None
        """

        # Find space options
        #
        rootComponent = self.findRootComponent()
        spineComponent = rootComponent.findComponentDescendants('SpineComponent')[0]
        handComponents = spineComponent.findComponentDescendants('HandComponent')

        leftHandComponents = [component for component in handComponents if component.componentSide == self.Side.LEFT and component.componentId == self.componentId]
        leftHandComponent = leftHandComponents[0] if (len(leftHandComponents) > 0) else None
        rightHandComponents = [component for component in handComponents if component.componentSide == self.Side.RIGHT and component.componentId == self.componentId]
        rightHandComponent = rightHandComponents[0] if (len(rightHandComponents) > 0) else None

        worldCtrl = rootComponent.getPublishedNode('Motion')
        pelvisCtrl = spineComponent.getPublishedNode('Pelvis')
        chestCtrl = spineComponent.getPublishedNode('Chest')

        hasLeftHand = leftHandComponent is not None
        leftHandExists = leftHandComponent.componentStatus == self.Status.RIG if hasLeftHand else False
        leftHandCtrl = leftHandComponent.getPublishedNode('Hand') if leftHandExists else None

        hasRightHand = rightHandComponent is not None
        rightHandExists = rightHandComponent.componentStatus == self.Status.RIG if hasRightHand else False
        rightHandCtrl = rightHandComponent.getPublishedNode('Hand') if rightHandExists else None

        # Evaluate component side
        #
        propCtrl = self.getPublishedNode('Prop')
        propOffsetCtrl = self.scene(propCtrl.userProperties['offset'])
        propSpaceSwitch = self.scene(propCtrl.userProperties['spaceSwitch'])

        componentSide = self.Side(self.componentSide)

        if componentSide == self.Side.LEFT:

            # Add space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            if hasRightHand:

                propCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=True)

            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            if hasRightHand:

                propCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=True)

            # Add proxy attributes to offset control
            #
            propOffsetCtrl.addDivider('Spaces')
            propOffsetCtrl.addProxyAttr('positionSpaceW0', propCtrl['positionSpaceW0'])
            propOffsetCtrl.addProxyAttr('positionSpaceW1', propCtrl['positionSpaceW1'])
            propOffsetCtrl.addProxyAttr('positionSpaceW2', propCtrl['positionSpaceW2'])
            propOffsetCtrl.addProxyAttr('positionSpaceW3', propCtrl['positionSpaceW3'])

            if hasRightHand:

                propOffsetCtrl.addProxyAttr('positionSpaceW4', propCtrl['positionSpaceW4'])

            propOffsetCtrl.addProxyAttr('rotationSpaceW0', propCtrl['rotationSpaceW0'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW1', propCtrl['rotationSpaceW1'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW2', propCtrl['rotationSpaceW2'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW3', propCtrl['rotationSpaceW3'])

            if hasRightHand:

                propOffsetCtrl.addProxyAttr('rotationSpaceW4', propCtrl['rotationSpaceW4'])

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl, leftHandCtrl])
            propSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetRotate': (-90.0, 0.0, -90.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')

            if hasRightHand:

                propMatrix = propCtrl.worldMatrix()
                handMirrorMatrix = transformutils.createRotationMatrix([0.0, 0.0, 180.0])
                propMirrorMatrix = transformutils.createRotationMatrix([0.0, 180.0, 0.0])
                targetOffsetMatrix = propMirrorMatrix * (propMatrix * (handMirrorMatrix * leftHandCtrl.worldMatrix()).inverse())
                targetOffsetTranslate, targetOffsetRotate, targetOffsetScale = transformutils.decomposeTransformMatrix(targetOffsetMatrix)

                index = propSpaceSwitch.addTarget(rightHandCtrl)
                propSpaceSwitch.setAttr(f'target[{index}]', {'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetTranslate': targetOffsetTranslate, 'targetOffsetRotate': targetOffsetRotate}, convertUnits=False)
                propSpaceSwitch.connectPlugs(propCtrl[f'positionSpaceW{index}'], f'target[{index}].targetTranslateWeight')
                propSpaceSwitch.connectPlugs(propCtrl[f'rotationSpaceW{index}'], f'target[{index}].targetRotateWeight')

        elif componentSide == self.Side.RIGHT:

            # Add space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            if hasLeftHand:

                propCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=True)

            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            if hasLeftHand:

                propCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=True)

            # Add proxy attributes to offset control
            #
            propOffsetCtrl.addDivider('Spaces')
            propOffsetCtrl.addProxyAttr('positionSpaceW0', propCtrl['positionSpaceW0'])
            propOffsetCtrl.addProxyAttr('positionSpaceW1', propCtrl['positionSpaceW1'])
            propOffsetCtrl.addProxyAttr('positionSpaceW2', propCtrl['positionSpaceW2'])
            propOffsetCtrl.addProxyAttr('positionSpaceW3', propCtrl['positionSpaceW3'])

            if hasLeftHand:

                propOffsetCtrl.addProxyAttr('positionSpaceW4', propCtrl['positionSpaceW4'])

            propOffsetCtrl.addProxyAttr('rotationSpaceW0', propCtrl['rotationSpaceW0'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW1', propCtrl['rotationSpaceW1'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW2', propCtrl['rotationSpaceW2'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW3', propCtrl['rotationSpaceW3'])

            if hasLeftHand:

                propOffsetCtrl.addProxyAttr('rotationSpaceW4', propCtrl['rotationSpaceW4'])

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl, rightHandCtrl])
            propSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetRotate': (90.0, 0.0, 90.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')

            if hasLeftHand:

                propMatrix = propCtrl.worldMatrix()
                handMirrorMatrix = transformutils.createRotationMatrix([0.0, 0.0, 180.0])
                propMirrorMatrix = transformutils.createRotationMatrix([0.0, 180.0, 0.0])
                targetOffsetMatrix = propMirrorMatrix * (propMatrix * (handMirrorMatrix * rightHandCtrl.worldMatrix()).inverse())
                targetOffsetTranslate, targetOffsetRotate, targetOffsetScale = transformutils.decomposeTransformMatrix(targetOffsetMatrix)

                index = propSpaceSwitch.addTarget(leftHandCtrl)
                propSpaceSwitch.setAttr(f'target[{index}]', {'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetTranslate': targetOffsetTranslate, 'targetOffsetRotate': targetOffsetRotate}, convertUnits=False)
                propSpaceSwitch.connectPlugs(propCtrl[f'positionSpaceW{index}'], f'target[{index}].targetTranslateWeight')
                propSpaceSwitch.connectPlugs(propCtrl[f'rotationSpaceW{index}'], f'target[{index}].targetRotateWeight')

        else:

            # Add space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            # Add proxy attributes to offset control
            #
            propOffsetCtrl.addDivider('Spaces')
            propOffsetCtrl.addProxyAttr('positionSpaceW0', propCtrl['positionSpaceW0'])
            propOffsetCtrl.addProxyAttr('positionSpaceW1', propCtrl['positionSpaceW1'])
            propOffsetCtrl.addProxyAttr('positionSpaceW2', propCtrl['positionSpaceW2'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW0', propCtrl['rotationSpaceW0'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW1', propCtrl['rotationSpaceW1'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW2', propCtrl['rotationSpaceW2'])

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl])
            propSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetRotate': (-90.0, 0.0, -90.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')

        # Check if opposite rig requires repairs
        #
        self.repairOppositeRig()
    # endregion
