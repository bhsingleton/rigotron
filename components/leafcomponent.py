from enum import IntEnum
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
        rootSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        rootSpec['name'] = self.formatName()
        rootSpec['driver'] = self.formatName(type='control')

        # Call parent method
        #
        super(LeafComponent, self).invalidateSkeletonSpecs(skeletonSpecs)
    # endregion
