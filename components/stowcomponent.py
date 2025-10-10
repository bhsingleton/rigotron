from maya.api import OpenMaya as om
from mpy import mpyattribute
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import transformutils, shapeutils
from . import basecomponent
from ..libs import Side

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class StowComponent(basecomponent.BaseComponent):
    """
    Overload of `BaseComponent` that implements stow components.
    """

    # region Dunderscores
    __default_component_name__ = 'Stow'
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit skeleton specs
        #
        stowSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        stowSpec.name = self.formatName()
        stowSpec.side = self.componentSide
        stowSpec.type = self.Type.OTHER
        stowSpec.otherType = self.componentName
        stowSpec.driver.name = self.formatName(type='control')

        # Call parent method
        #
        return super(StowComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        stowSpec, = self.skeletonSpecs()
        stowExportJoint = stowSpec.getNode()
        stowExportMatrix = stowExportJoint.worldMatrix()

        componentSide = self.Side(self.componentSide)
        requiresMirroring = componentSide == self.Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__.get(componentSide, om.MMatrix.kIdentity)

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        # Create stow control
        #
        stowMatrix = mirrorMatrix * stowExportMatrix

        stowSpaceName = self.formatName(type='space')
        stowSpace = self.scene.createNode('transform', name=stowSpaceName, parent=controlsGroup)
        stowSpace.setWorldMatrix(stowMatrix, skipScale=True)
        stowSpace.freezeTransform()

        stowCtrlName = self.formatName(type='control')
        stowCtrl = self.scene.createNode('transform', name=stowCtrlName, parent=stowSpace)
        stowCtrl.addPointHelper('cross', size=15.0, colorRGB=colorRGB, lineWidth=4.0)
        stowCtrl.addDivider('Settings')
        stowCtrl.addAttr(longName='stowed', attributeType='float', min=0.0, max=1.0, keyable=True)
        stowCtrl.prepareChannelBoxForAnimation()
        self.publishNode(stowCtrl, alias='Stow')

        stowOffsetCtrlName = self.formatName(subname='Offset', type='control')
        stowOffsetCtrl = self.scene.createNode('transform', name=stowOffsetCtrlName, parent=stowCtrl)
        stowOffsetCtrl.addPointHelper('cylinder', size=15.0, colorRGB=lightColorRGB, lineWidth=2.0)
        stowOffsetCtrl.addDivider('Settings')
        stowOffsetCtrl.addProxyAttr('stowed', stowCtrl['stowed'])
        stowOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(stowOffsetCtrl, alias='Offset')

        stowCtrl.userProperties['space'] = stowSpace.uuid()
        stowCtrl.userProperties['offset'] = stowOffsetCtrl.uuid()

        # Tag controls
        #
        stowCtrl.tagAsController(children=[stowOffsetCtrl])
        stowOffsetCtrl.tagAsController(parent=stowCtrl)

    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.

        :rtype: None
        """

        # Decompose component
        #
        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        rootComponent = self.findRootComponent()
        handComponents = rootComponent.findComponentDescendants('HandComponent')
        leftHandComponents = [component for component in handComponents if component.componentId == self.componentId and component.componentSide == self.Side.LEFT]
        rightHandComponents = [component for component in handComponents if component.componentId == self.componentId and component.componentSide == self.Side.RIGHT]

        # Check if space switching is required
        #
        stowCtrl = self.getPublishedNode('Stow')
        stowOffsetCtrl = self.getPublishedNode('Offset')
        stowSpace = self.scene(stowCtrl.userProperties['space'])

        hasLeftHandComponent = len(leftHandComponents) > 0
        hasRightHandComponent = len(rightHandComponents) > 0
        requiresSpaceSwitching = hasLeftHandComponent or hasRightHandComponent

        if not requiresSpaceSwitching:

            stowSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)
            return

        # Evaluate prop components
        #
        stowCtrl.addDivider('Spaces')
        stowCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (Default)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        stowCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHandComponent, hidden=(not hasLeftHandComponent))
        stowCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHandComponent, hidden=(not hasRightHandComponent))
        stowCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (Default)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        stowCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHandComponent, hidden=(not hasLeftHandComponent))
        stowCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHandComponent, hidden=(not hasRightHandComponent))

        stowOffsetCtrl.addDivider('Spaces')
        stowOffsetCtrl.addProxyAttr('positionSpaceW0', stowCtrl['positionSpaceW0'])
        stowOffsetCtrl.addProxyAttr('positionSpaceW1', stowCtrl['positionSpaceW1'])
        stowOffsetCtrl.addProxyAttr('positionSpaceW2', stowCtrl['positionSpaceW2'])
        stowOffsetCtrl.addProxyAttr('rotationSpaceW0', stowCtrl['rotationSpaceW0'])
        stowOffsetCtrl.addProxyAttr('rotationSpaceW1', stowCtrl['rotationSpaceW1'])
        stowOffsetCtrl.addProxyAttr('rotationSpaceW2', stowCtrl['rotationSpaceW2'])

        spaceSwitch = stowSpace.addSpaceSwitch([parentExportCtrl], maintainOffset=True)
        spaceSwitch.weighted = True
        spaceSwitch.connectPlugs(stowCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
        spaceSwitch.connectPlugs(stowCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')

        if hasLeftHandComponent:

            # Add left hand to space switch
            #
            handComponent = leftHandComponents[0]
            handCtrl = handComponent.getPublishedNode('Hand')

            index = spaceSwitch.addTarget(handCtrl)
            spaceSwitch.connectPlugs(stowCtrl['positionSpaceW1'], f'target[{index}].targetTranslateWeight')
            spaceSwitch.connectPlugs(stowCtrl['rotationSpaceW1'], f'target[{index}].targetRotateWeight')

            # Check if prop component exists
            # If so, update target offset matrix for left hand target
            #
            propComponents = handComponent.findComponentDescendants('PropComponent')
            hasPropComponent = len(propComponents) > 0

            if hasPropComponent:

                propComponent = propComponents[0]
                propCtrl = propComponent.getPublishedNode('Prop')

                offsetMatrix = propCtrl.worldMatrix() * handCtrl.worldInverseMatrix()
                targetOffsetTranslate, targetOffsetRotate, targetOffsetScale = transformutils.decomposeTransformMatrix(offsetMatrix)
                spaceSwitch.setAttr(f'target[{index}]', {'targetOffsetTranslate': targetOffsetTranslate, 'targetOffsetRotate': targetOffsetRotate}, convertUnits=False)

        if hasRightHandComponent:

            # Add right hand to space switch
            #
            handComponent = rightHandComponents[0]
            handCtrl = handComponent.getPublishedNode('Hand')

            index = spaceSwitch.addTarget(handCtrl)
            spaceSwitch.connectPlugs(stowCtrl['positionSpaceW2'], f'target[{index}].targetTranslateWeight')
            spaceSwitch.connectPlugs(stowCtrl['rotationSpaceW2'], f'target[{index}].targetRotateWeight')

            # Check if prop component exists
            # If so, update target offset matrix for right hand target
            #
            propComponents = handComponent.findComponentDescendants('PropComponent')
            hasPropComponent = len(propComponents) > 0

            if hasPropComponent:

                propComponent = propComponents[0]
                propCtrl = propComponent.getPublishedNode('Prop')

                offsetMatrix = propCtrl.worldMatrix() * handCtrl.worldInverseMatrix()
                targetOffsetTranslate, targetOffsetRotate, targetOffsetScale = transformutils.decomposeTransformMatrix(offsetMatrix)
                spaceSwitch.setAttr(f'target[{index}]', {'targetOffsetTranslate': targetOffsetTranslate, 'targetOffsetRotate': targetOffsetRotate}, convertUnits=False)
    # endregion
