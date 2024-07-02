from maya.api import OpenMaya as om
from mpy import mpyattribute
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import shapeutils
from . import basecomponent
from ..libs import Side

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class StowedComponent(basecomponent.BaseComponent):
    """
    Overload of `BaseComponent` that implements stowed prop components.
    """

    # region Dunderscores
    __default_component_name__ = 'StowedProp'
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
        stowedSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        stowedSpec.name = self.formatName()
        stowedSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(StowedComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        componentSide = self.Side(self.componentSide)
        stowSpec, = self.skeletonSpecs()

        # Create upper joint
        #
        jointType = self.Type.PROP_A if (componentSide == self.Side.LEFT) else self.Type.PROP_B if (componentSide == self.Side.RIGHT) else self.Type.PROP_C

        stowJoint = self.scene.createNode('joint', name=stowSpec.name)
        stowJoint.side = componentSide
        stowJoint.type = jointType
        stowJoint.drawStyle = self.Style.JOINT
        stowJoint.displayLocalAxis = True
        stowSpec.uuid = stowJoint.uuid()

        stowMatrix = stowSpec.getMatrix(default=om.MMatrix.kIdentity)
        stowJoint.setWorldMatrix(stowMatrix)

        return (stowMatrix,)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        stowSpec, = self.skeletonSpecs()
        stowExportJoint = self.scene(stowSpec.uuid)

        componentSide = self.Side(self.componentSide)
        requiresMirroring = componentSide == self.Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create stow control
        #
        stowCtrlMatrix = mirrorMatrix * stowExportJoint.worldMatrix()

        stowSpaceName = self.formatName(type='space')
        stowSpace = self.scene.createNode('transform', name=stowSpaceName, parent=controlsGroup)
        stowSpace.setWorldMatrix(stowCtrlMatrix)
        stowSpace.freezeTransform()
        stowSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        stowCtrlName = self.formatName(type='control')
        stowCtrl = self.scene.createNode('transform', name=stowCtrlName, parent=stowSpace)
        stowCtrl.addPointHelper('box', size=5.0, side=componentSide, lineWidth=1.0)
        stowCtrl.tagAsController()
        stowCtrl.prepareChannelBoxForAnimation()
        self.publishNode(stowCtrl, alias='Stowed')
    # endregion
