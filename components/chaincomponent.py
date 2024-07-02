from enum import IntEnum
from mpy import mpynode, mpyattribute
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ChainComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements chain components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Chain'
    # endregion

    # region Attributes
    numLinks = mpyattribute.MPyAttribute('numLinks', attributeType='int', min=2)
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
        chainSpecs = self.resizeSkeletonSpecs(self.numLinks, skeletonSpecs)

        for (i, chainSpec) in enumerate(chainSpecs, start=1):

            chainSpec['name'] = self.formatName(index=i)
            chainSpec['driver'] = self.formatName(index=i, type='control')

        # Call parent method
        #
        super(ChainComponent, self).invalidateSkeletonSpecs(skeletonSpecs)
    # endregion
