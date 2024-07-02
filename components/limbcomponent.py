from mpy import mpyattribute
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LimbComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that outlines limb components.
    """

    # region Dunderscores
    __default_component_name__ = 'Limb'
    # endregion

    # region Attributes
    twistEnabled = mpyattribute.MPyAttribute('twistEnabled', attributeType='bool', default=True)
    numTwistLinks = mpyattribute.MPyAttribute('numTwistLinks', attributeType='int', min=2, default=3)
    # endregion

    # region Properties
    @twistEnabled.changed
    def twistEnabled(self, twistEnabled):
        """
        Changed method that notifies any twist state changes.

        :type twistEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numTwistLinks.changed
    def numTwistLinks(self, numTwistLinks):
        """
        Changed method that notifies any twist link size changes.

        :type numTwistLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion
