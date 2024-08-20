from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import shapeutils
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
        propSpec.driver = self.formatName(type='control')

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

        # Find space options
        #
        rootComponent = self.findComponentAncestors('RootComponent')[0]
        spineComponent = self.findComponentAncestors('SpineComponent')[0]
        handComponents = self.findComponentAncestors('HandComponent')
        hasHandComponent = len(handComponents) == 1

        worldCtrl = rootComponent.getPublishedNode('Motion')
        pelvisCtrl = spineComponent.getPublishedNode('Pelvis')
        chestCtrl = spineComponent.getPublishedNode('Chest')
        handCtrl = handComponents[0].getPublishedNode('Hand') if hasHandComponent else None

        # Create prop control
        #
        propSpaceName = self.formatName(type='space')
        propSpace = self.scene.createNode('transform', name=propSpaceName, parent=controlsGroup)
        propSpace.setWorldMatrix(mirrorMatrix * propMatrix)
        propSpace.freezeTransform()

        propCtrlName = self.formatName(type='control')
        propCtrl = self.scene.createNode('transform', name=propCtrlName, parent=propSpace)
        propCtrl.addPointHelper('cross', size=15.0, colorRGB=colorRGB, lineWidth=4.0)
        propCtrl.addDivider('Space')
        propCtrl.prepareChannelBoxForAnimation()
        self.publishNode(propCtrl, alias='Prop')

        propOffsetCtrlName = self.formatName(subname='Offset', type='control')
        propOffsetCtrl = self.scene.createNode('transform', name=propOffsetCtrlName, parent=propCtrl)
        propOffsetCtrl.addPointHelper('cylinder', size=15.0, colorRGB=lightColorRGB, lineWidth=2.0)
        propOffsetCtrl.addDivider('Space')
        propOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(propOffsetCtrl, alias='Offset')

        propSpaceSwitch = None

        if componentSide in (self.Side.LEFT, self.Side.RIGHT):

            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            propOffsetCtrl.addProxyAttr('positionSpaceW0', propCtrl['positionSpaceW0'])
            propOffsetCtrl.addProxyAttr('positionSpaceW1', propCtrl['positionSpaceW1'])
            propOffsetCtrl.addProxyAttr('positionSpaceW2', propCtrl['positionSpaceW2'])
            propOffsetCtrl.addProxyAttr('positionSpaceW3', propCtrl['positionSpaceW3'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW0', propCtrl['rotationSpaceW0'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW1', propCtrl['rotationSpaceW1'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW2', propCtrl['rotationSpaceW2'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW3', propCtrl['rotationSpaceW3'])

            propSpaceSwitch = propSpace.addSpaceSwitch([worldCtrl, pelvisCtrl, chestCtrl, handCtrl], maintainOffset=True)
            propSpaceSwitch.weighted = True
            propSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')

        else:

            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)

            propOffsetCtrl.addProxyAttr('positionSpaceW0', propCtrl['positionSpaceW0'])
            propOffsetCtrl.addProxyAttr('positionSpaceW1', propCtrl['positionSpaceW1'])
            propOffsetCtrl.addProxyAttr('positionSpaceW2', propCtrl['positionSpaceW2'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW0', propCtrl['rotationSpaceW0'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW1', propCtrl['rotationSpaceW1'])
            propOffsetCtrl.addProxyAttr('rotationSpaceW2', propCtrl['rotationSpaceW2'])

            propSpaceSwitch = propSpace.addSpaceSwitch([worldCtrl, pelvisCtrl, chestCtrl], maintainOffset=True)
            propSpaceSwitch.weighted = True
            propSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')

        propCtrl.userProperties['space'] = propSpace.uuid()
        propCtrl.userProperties['spaceSwitch'] = propSpaceSwitch.uuid()
    # endregion
