from maya.api import OpenMaya as om
from mpy import mpyattribute
from . import leafcomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PlayerMantleComponent(leafcomponent.LeafComponent):
    """
    Overload of `LeafComponent` that implements player-mantle components.
    """

    # region Dunderscores
    __default_component_name__ = 'PlayerMantle'
    # endregion

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Call parent method
        #
        super(PlayerMantleComponent, self).buildRig()

        # Get leaf control and edit shape
        #
        leafCtrl = self.getPublishedNode(self.componentName)
        rigScale = self.findControlRig().getRigScale()

        leafCtrlShape = leafCtrl.shape()
        leafCtrlShape.size = 15.0 * rigScale
        leafCtrlShape.disc = False
        leafCtrlShape.axisTripod = True
        leafCtrlShape.cross = True
