from maya.api import OpenMaya as om
from mpy import mpyattribute
from . import leafcomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PlayerAlignComponent(leafcomponent.LeafComponent):
    """
    Overload of `LeafComponent` that implements player-align components.
    """

    # region Dunderscores
    __default_component_name__ = 'PlayerAlign'
    # endregion

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Call parent method
        #
        super(PlayerAlignComponent, self).buildRig()

        # Get leaf control and edit shape
        #
        leafCtrl = self.getPublishedNode(self.componentName)
        rigScale = self.findControlRig().getRigScale()

        leafCtrlShape = leafCtrl.shape()
        leafCtrlShape.size = 15.0 * rigScale
        leafCtrlShape.disc = False
        leafCtrlShape.axisTripod = True
        leafCtrlShape.cross = True
