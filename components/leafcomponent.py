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
        leafMatrix = leafSpec.getMatrix(default=om.MMatrix.kIdentity)
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

        leafSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        leafCtrlName = self.formatName(type='control')
        leafCtrl = self.scene.createNode('transform', name=leafCtrlName, parent=leafSpace)
        leafCtrl.addPointHelper('disc', size=(10.0 * rigScale), side=componentSide)
        leafCtrl.prepareChannelBoxForAnimation()
        leafCtrl.tagAsController()
        self.publishNode(leafCtrl, alias=self.componentName)

        leafCtrl.userProperties['space'] = leafSpace.uuid()
    # endregion
