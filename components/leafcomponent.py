from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LeafComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements leaf components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Leaf'
    __default_component_matrix = om.MMatrix.kIdentity
    # endregion

    # region Attributes
    spaceSwitchEnabled = mpyattribute.MPyAttribute('spaceSwitchEnabled', attributeType='bool', default=False)
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
        leafSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        leafSpec.name = self.formatName()
        leafSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(LeafComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        leafSpec, = self.skeletonSpecs()

        # Create joint
        #
        leafJoint = self.scene.createNode('joint', name=leafSpec.name)
        leafJoint.side = self.componentSide
        leafJoint.type = self.Type.OTHER
        leafJoint.otherType = self.componentName
        leafJoint.displayLocalAxis = True
        leafSpec.uuid = leafJoint.uuid()

        # Update joint transform
        #
        leafMatrix = leafSpec.getMatrix(default=self.__default_component_matrix)
        leafJoint.setWorldMatrix(leafMatrix)

        return (leafJoint,)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        leafSpec, = self.skeletonSpecs()
        leafExportJoint = self.scene(leafSpec.uuid)

        componentSide = self.Side(self.componentSide)
        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create control
        #
        leafSpaceName = self.formatName(type='space')
        leafSpace = self.scene.createNode('transform', name=leafSpaceName, parent=controlsGroup)
        leafSpace.copyTransform(leafExportJoint)
        leafSpace.freezeTransform()

        leafCtrl = self.scene.createNode('transform', name=leafSpec.driver, parent=leafSpace)
        leafCtrl.addPointHelper('disc', size=(10.0 * rigScale), side=componentSide)
        leafCtrl.prepareChannelBoxForAnimation()
        leafCtrl.tagAsController()
        self.publishNode(leafCtrl, alias=self.componentName)

        leafCtrl.userProperties['space'] = leafSpace.uuid()

        # Setup space switching
        #
        requiresSpaceSwitch = bool(self.spaceSwitchEnabled)

        if requiresSpaceSwitch:

            leafCtrl.addDivider('Spaces')
            leafCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)

            rootComponent = self.findComponentAncestors('RootComponent')[0]
            motionCtrl = rootComponent.getPublishedNode('Motion')

            spaceSwitch = leafSpace.addSpaceSwitch([parentExportCtrl, motionCtrl], weighted=True, maintainOffset=True)
            spaceSwitch.setAttr('target[0].targetReverse', (True, True, True))
            spaceSwitch.connectPlugs(leafCtrl['localOrGlobal'], 'target[0].targetWeight')
            spaceSwitch.connectPlugs(leafCtrl['localOrGlobal'], 'target[1].targetWeight')

            leafCtrl.userProperties['spaceSwitch'] = spaceSwitch.uuid()

        else:

            leafSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)
    # endregion
