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

    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: None
        """

        # Edit skeleton specs
        #
        rootSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        rootSpec.name = self.formatName()
        rootSpec.driver = self.formatName(name='Root', type='control')

        # Call parent method
        #
        super(RootComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Create root joint
        #
        rootSide = self.Side(self.componentSide)
        rootSpec, = self.skeletonSpecs()

        rootJoint = self.scene.createNode('joint', name=rootSpec.name)
        rootJoint.side = rootSide
        rootJoint.type = self.Type.ROOT
        rootJoint.displayLocalAxis = True

        rootMatrix = rootSpec.getMatrix(default=self.__default_root_matrix__)
        rootJoint.setMatrix(rootMatrix)

        # Update skeleton specs
        #
        rootSpec.uuid = rootJoint.uuid()

        return (rootJoint,)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Decompose component
        #
        rootSpec, = self.skeletonSpecs()
        rootExportJoint = self.scene(rootSpec.uuid)
        rootMatrix = rootExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)

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
            rootSpace.setWorldMatrix(rootMatrix)
            rootSpace.freezeTransform()

            rootCtrlName = self.formatName(name='Root', type='control')
            rootCtrl = self.scene.createNode('transform', name=rootCtrlName, parent=rootSpace)
            rootCtrl.addPointHelper('sphere', size=(5.0 * rigScale), colorRGB=darkColorRGB)
            rootCtrl.addDivider('Spaces')
            rootCtrl.addAttr(longName='handedness', attributeType='float', min=0.0, max=1.0, keyable=True)
            rootCtrl.addAttr(longName='stowed', attributeType='float', min=0.0, max=1.0, hidden=True)
            rootCtrl.prepareChannelBoxForAnimation()
            rootCtrl.tagAsController()
            self.publishNode(rootCtrl, alias='Root')

            # Add space switch placeholders
            # Connections will be handled by the `ReferencedPropRig` interface!
            #
            handednessSpaceSwitchName = self.formatName(subname='Handedness', type='spaceSwitch')
            handednessSpaceSwitch = self.scene.createNode('spaceSwitch', name=handednessSpaceSwitchName)
            handednessSpaceSwitch.weighted = True
            handednessSpaceSwitch.setDriven(rootSpace, skipParentInverseMatrix=True, skipTranslate=True, skipRotate=True, skipScale=True)
            handednessSpaceSwitch.setAttr('target', [{'targetName': 'Primary', 'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetName': 'Secondary', 'targetWeight': (0.0, 0.0, 0.0)}])
            handednessSpaceSwitch.connectPlugs(rootCtrl['handedness'], 'target[0].targetWeight')
            handednessSpaceSwitch.connectPlugs(rootCtrl['handedness'], 'target[1].targetWeight')

            stowSpaceSwitchName = self.formatName(subname='Stow', type='spaceSwitch')
            stowSpaceSwitch = self.scene.createNode('spaceSwitch', name=stowSpaceSwitchName)
            stowSpaceSwitch.weighted = True
            stowSpaceSwitch.setDriven(rootSpace)
            stowSpaceSwitch.setAttr('target', [{'targetName': 'Default', 'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetName': 'Stow', 'targetWeight': (0.0, 0.0, 0.0)}])
            stowSpaceSwitch.connectPlugs(handednessSpaceSwitch['outputWorldMatrix'], 'target[0].targetMatrix')
            stowSpaceSwitch.connectPlugs(rootCtrl['stowed'], 'target[0].targetWeight')
            stowSpaceSwitch.connectPlugs(rootCtrl['stowed'], 'target[1].targetWeight')

            rootCtrl.userProperties['space'] = rootSpace.uuid()
            rootCtrl.userProperties['handednessSpaceSwitch'] = handednessSpaceSwitch.uuid()
            rootCtrl.userProperties['stowSpaceSwitch'] = stowSpaceSwitch.uuid()

        else:

            # Create master control
            #
            masterCtrlName = self.formatName(name='Master', type='control')
            masterCtrl = self.scene.createNode('transform', name=masterCtrlName, parent=controlsGroup)
            masterCtrl.addPointHelper('tearDrop', size=(100.0 * rigScale), localRotate=(90.0, 90.0, 0.0), colorRGB=colorRGB, lineWidth=4.0)
            masterCtrl.setWorldMatrix(rootMatrix)
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
