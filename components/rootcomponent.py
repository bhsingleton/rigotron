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
        rootSpec.driver = self.formatName(type='control')

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
        rootJoint.segmentScaleCompensate = False

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

        # Check if this component is used as a prop
        #
        usedAsProp = bool(self.usedAsProp)

        if usedAsProp:

            # Create master control
            #
            masterSpaceName = self.formatName(name='Master', type='space')
            masterSpace = self.scene.createNode('transform', name=masterSpaceName, parent=controlsGroup)
            masterSpace.setWorldMatrix(rootMatrix)
            masterSpace.freezeTransform()

            masterCtrlName = self.formatName(name='Master', type='control')
            masterCtrl = self.scene.createNode('transform', name=masterCtrlName, parent=masterSpace)
            masterCtrl.addPointHelper('cylinder', size=15.0, colorRGB=colorRGB, lineWidth=2.0)
            masterCtrl.addAttr(longName='stowed', attributeType='float', min=0.0, max=1.0, keyable=True)
            masterCtrl.prepareChannelBoxForAnimation()
            masterCtrl.tagAsController()
            self.publishNode(masterCtrl, alias='Master')

            masterSpaceSwitch = masterSpace.addSpaceSwitch([])
            masterSpaceSwitch.weighted = True
            masterSpaceSwitch.setAttr('target', [{'targetName': 'Default', 'targetReverse': (True, True, True)}, {'targetName': 'Stowed'}])
            masterSpaceSwitch.connectPlugs(masterCtrl['stowed'], 'target[0].targetWeight')
            masterSpaceSwitch.connectPlugs(masterCtrl['stowed'], 'target[1].targetWeight')

            masterCtrl.userProperties['space'] = masterSpace.uuid()
            masterCtrl.userProperties['spaceSwitch'] = masterSpaceSwitch.uuid()

            # Constrain export joint
            #
            rootExportJoint.addConstraint('transformConstraint', [masterCtrl])

        else:

            # Create master control
            #
            masterCtrlName = self.formatName(name='Master', type='control')
            masterCtrl = self.scene.createNode('transform', name=masterCtrlName, parent=controlsGroup)
            masterCtrl.addPointHelper('tearDrop', size=100.0, localRotate=(90.0, 90.0, 0.0), colorRGB=colorRGB, lineWidth=4.0)
            masterCtrl.setWorldMatrix(rootMatrix)
            masterCtrl.addGlobalScale()
            masterCtrl.prepareChannelBoxForAnimation()
            self.publishNode(masterCtrl, alias='Master')

            # Create motion control
            #
            motionCtrlName = self.formatName(name='Motion', type='control')
            motionCtrl = self.scene.createNode('transform', name=motionCtrlName, parent=masterCtrl)
            motionCtrl.addPointHelper('disc', size=80.0, localRotate=(0.0, 90.0, 0.0), colorRGB=lightColorRGB, lineWidth=2.0)
            motionCtrl.prepareChannelBoxForAnimation()
            self.publishNode(motionCtrl, alias='Motion')

            # Create root control
            #
            rootSpaceName = self.formatName(name='Root', type='space')
            rootSpace = self.scene.createNode('transform', name=rootSpaceName, parent=controlsGroup)

            rootCtrlName = self.formatName(name='Root', type='control')
            rootCtrl = self.scene.createNode('transform', name=rootCtrlName, parent=rootSpace)
            rootCtrl.addPointHelper('sphere', size=5.0, colorRGB=darkColorRGB)
            rootCtrl.addDivider('Space')
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

            # Constrain export joint
            #
            rootExportJoint.addConstraint('transformConstraint', [rootCtrl])
    # endregion
