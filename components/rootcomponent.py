from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.maya.libs import shapeutils
from dcc.dataclasses.colour import Colour
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RootComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements root components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Root'
    __default_root_matrix__ = om.MMatrix.kIdentity
    # endregion

    # region Attributes
    forwardAxis = mpyattribute.MPyAttribute('forwardAxis', attributeType='enum', fields=('X', 'Y', 'Z'), default=1)
    forwardAxisFlip = mpyattribute.MPyAttribute('forwardAxisFlip', attributeType='bool', default=True)
    upAxis = mpyattribute.MPyAttribute('upAxis', attributeType='enum', fields=('X', 'Y', 'Z'), default=2)
    upAxisFlip = mpyattribute.MPyAttribute('upAxisFlip', attributeType='bool', default=False)
    usedAsProp = mpyattribute.MPyAttribute('usedAsProp', attributeType='bool', default=False)
    # endregion

    # region Methods
    def findRootComponent(self):
        """
        Returns the root component relative to this instance.
        For the sake of redundancy this overload will just return itself!

        :rtype: RootComponent
        """

        return self

    def getWorldTarget(self):
        """
        Returns the world target for space switch use.

        :rtype: Union[mpynode.MPyNode, None]
        """

        # Evaluate component state
        #
        if self.Status(self.componentStatus) != self.Status.RIG:

            return None

        # Check if this component is used as a prop
        #
        if self.usedAsProp:

            return self.getPublishedNode('Root')

        else:

            return self.getPublishedNode('Motion')

    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Update root spec
        #
        rootSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        rootSpec.name = self.formatName()
        rootSpec.side = self.componentSide
        rootSpec.type = self.Type.ROOT
        rootSpec.driver.name = self.formatName(type='control')

        # Call parent method
        #
        return super(RootComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Decompose component
        #
        rootSpec, = self.skeleton()
        rootExportJoint = rootSpec.getNode()
        rootExportMatrix = rootExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        rigScale = self.findControlRig().getRigScale()

        # Check if this component is used as a prop
        #
        usedAsProp = bool(self.usedAsProp)

        if usedAsProp:

            # Create root control
            #
            rootSpaceName = self.formatName(name='Root', type='space')
            rootSpace = self.scene.createNode('transform', name=rootSpaceName, parent=controlsGroup)
            rootSpace.setWorldMatrix(rootExportMatrix)
            rootSpace.freezeTransform()

            rootCtrlName = self.formatName(name='Root', type='control')
            rootCtrl = self.scene.createNode('transform', name=rootCtrlName, parent=rootSpace)
            rootCtrl.addPointHelper('sphere', size=(5.0 * rigScale), colorRGB=darkColorRGB)
            rootCtrl.prepareChannelBoxForAnimation()
            rootCtrl.tagAsController()
            self.publishNode(rootCtrl, alias='Root')

            # Add stow space switch placeholder
            # Connections will be handled by the `ReferencedPropRig` interface!
            #
            stowSpaceSwitchName = self.formatName(subname='Stow', type='spaceSwitch')
            stowSpaceSwitch = self.scene.createNode('spaceSwitch', name=stowSpaceSwitchName)
            stowSpaceSwitch.weighted = True
            stowSpaceSwitch.setDriven(rootSpace)
            stowSpaceSwitch.setAttr('target', [{'targetName': 'Default', 'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetName': 'Stow', 'targetWeight': (0.0, 0.0, 0.0)}])

            rootCtrl.userProperties['space'] = rootSpace.uuid()
            rootCtrl.userProperties['stowSpaceSwitch'] = stowSpaceSwitch.uuid()

        else:

            # Create master control
            #
            masterCtrlName = self.formatName(name='Master', type='control')
            masterCtrl = self.scene.createNode('transform', name=masterCtrlName, parent=controlsGroup)
            masterCtrl.addPointHelper('tearDrop', size=(100.0 * rigScale), localRotate=(90.0, 90.0, 0.0), colorRGB=colorRGB, lineWidth=4.0)
            masterCtrl.setWorldMatrix(rootExportMatrix, skipScale=True)
            masterCtrl.addGlobalScale()
            masterCtrl.prepareChannelBoxForAnimation()
            self.publishNode(masterCtrl, alias='Master')

            # Create motion control
            #
            motionCtrlName = self.formatName(name='Motion', type='control')
            motionCtrl = self.scene.createNode('transform', name=motionCtrlName, parent=masterCtrl)
            motionCtrl.addPointHelper('disc', size=(80.0 * rigScale), localRotate=(0.0, 90.0, 0.0), colorRGB=lightColorRGB, lineWidth=2.0)
            motionCtrl.prepareChannelBoxForAnimation()
            self.publishNode(motionCtrl, alias='Motion')

            # Create root control
            #
            rootSpaceName = self.formatName(name='Root', type='space')
            rootSpace = self.scene.createNode('transform', name=rootSpaceName, parent=controlsGroup)

            rootCtrlName = self.formatName(name='Root', type='control')
            rootCtrl = self.scene.createNode('transform', name=rootCtrlName, parent=rootSpace)
            rootCtrl.addPointHelper('sphere', size=(15.0 * rigScale), colorRGB=darkColorRGB)
            rootCtrl.addPointHelper('pyramid', size=(10.0 * rigScale), localPosition=(0.0, (-7.5 * rigScale), 0.0), localRotate=(0.0, 0.0, -90.0), colorRGB=darkColorRGB)
            rootCtrl.addDivider('Spaces')
            rootCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
            rootCtrl.prepareChannelBoxForAnimation()
            self.publishNode(rootCtrl, alias='Root')

            rootSpaceSwitch = rootSpace.addSpaceSwitch([motionCtrl, masterCtrl])
            rootSpaceSwitch.weighted = True
            rootSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
            rootSpaceSwitch.connectPlugs(rootCtrl['localOrGlobal'], 'target[0].targetWeight')
            rootSpaceSwitch.connectPlugs(rootCtrl['localOrGlobal'], 'target[1].targetWeight')

            # Tag and publish controllers
            #
            masterCtrl.tagAsController(children=[motionCtrl])
            motionCtrl.tagAsController(parent=masterCtrl, children=[rootCtrl])
            rootCtrl.tagAsController(parent=motionCtrl)
    # endregion
