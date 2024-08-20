from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from enum import IntEnum
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class JawType(IntEnum):
    """
    Enum class of all available jaw subtypes.
    """

    JAW = 0


class JawComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements jaw components.
    """

    # region Enums
    JawType = JawType
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Jaw'
    __default_component_matrices__ = {
        JawType.JAW: om.MMatrix(
          [
              (0.0, -1.0, 0.0, 0.0),
              (0.0, 0.0, -1.0, 0.0),
              (1.0, 0.0, 0.0, 0.0),
              (0.0, -10.0, 200.0, 1.0)
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
        jawSpec, = self.resizeSkeletonSpecs(len(self.JawType), skeletonSpecs)
        jawSpec.name = self.formatName()
        jawSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(JawComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        jawSpec, = self.skeletonSpecs()

        # Create joint
        #
        jawJoint = self.scene.createNode('joint', name=jawSpec.name)
        jawJoint.side = self.componentSide
        jawJoint.type = self.Type.OTHER
        jawJoint.otherType = self.componentName
        jawJoint.displayLocalAxis = True
        jawSpec.uuid = jawJoint.uuid()

        # Update joint transform
        #
        jawMatrix = jawSpec.getMatrix(default=self.__default_component_matrices__[self.JawType.JAW])
        jawJoint.setWorldMatrix(jawMatrix)

        return (jawJoint,)

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

        jawSpec, = self.skeletonSpecs()
        jawExportJoint = self.scene(jawSpec.uuid)

        componentSide = self.Side(self.componentSide)
        rigScale = self.findControlRig().getRigScale()
        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create control
        #
        jawSpaceName = self.formatName(type='space')
        jawSpace = self.scene.createNode('transform', name=jawSpaceName, parent=controlsGroup)
        jawSpace.copyTransform(jawExportJoint)
        jawSpace.freezeTransform()

        jawSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        jawCtrl = self.scene.createNode('transform', name=jawSpec.driver, parent=jawSpace)
        jawCtrl.addShape('WedgeCurve', localPosition=(10.0 * rigScale, 7.5 * rigScale, 0.0), size=(2.0 * rigScale), side=componentSide)
        jawCtrl.prepareChannelBoxForAnimation()
        jawCtrl.tagAsController()
        self.publishNode(jawCtrl, alias='Jaw')

        jawCtrl.userProperties['space'] = jawSpace.uuid()
    # endregion
