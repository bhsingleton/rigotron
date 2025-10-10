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
    __default_component_matrix__ = {
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
        size = len(self.JawType)

        jawSpec, = self.resizeSkeletonSpecs(size, skeletonSpecs)
        jawSpec.name = self.formatName()
        jawSpec.side = self.componentSide
        jawSpec.type = self.Type.OTHER
        jawSpec.otherType = self.componentName
        jawSpec.defaultMatrix = om.MMatrix(self.__default_component_matrix__)
        jawSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(JawComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        jawSpec, = self.skeleton()
        jawExportJoint = jawSpec.getNode()
        jawExportMatrix = jawExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create control
        #
        jawSpaceName = self.formatName(type='space')
        jawSpace = self.scene.createNode('transform', name=jawSpaceName, parent=controlsGroup)
        jawSpace.setWorldMatrix(jawExportMatrix, skipScale=True)
        jawSpace.freezeTransform()
        jawSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        jawCtrlName = self.formatName(type='control')
        jawCtrl = self.scene.createNode('transform', name=jawCtrlName, parent=jawSpace)
        jawCtrl.addShape('WedgeCurve', localPosition=(10.0 * rigScale, 7.5 * rigScale, 0.0), size=(2.0 * rigScale), side=componentSide)
        jawCtrl.prepareChannelBoxForAnimation()
        jawCtrl.tagAsController()
        self.publishNode(jawCtrl, alias='Jaw')

        jawCtrl.userProperties['space'] = jawSpace.uuid()
    # endregion
