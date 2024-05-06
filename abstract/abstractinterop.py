from dcc.decorators.classproperty import classproperty
from mpy import mpynodeextension
from mpy.abstract import mabcmeta

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractInterop(mpynodeextension.MPyNodeExtension, metaclass=mabcmeta.MABCMeta):
    """
    Overload of `MPyNodeExtension` that outlines rig interoperability behaviour.
    """

    # region Dunderscores
    __interop_factory__ = None
    __component_factory__ = None
    # endregion

    # region Properties
    @classproperty
    def interopManager(cls):
        """
        Returns the rig interop manager.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: rigotron.libs.interopfactory.InteropFactory
        """

        # Check if factory exists
        #
        if cls.__interop_factory__ is None:

            from ..libs import interopfactory
            cls.__interop_factory__ = interopfactory.InteropFactory.getInstance(asWeakReference=True)

        return cls.__interop_factory__()

    @classproperty
    def componentManager(cls):
        """
        Returns the rig interop manager.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: rigotron.libs.interopfactory.InteropFactory
        """

        # Check if factory exists
        #
        if cls.__component_factory__ is None:

            from ..libs import componentfactory
            cls.__component_factory__ = componentfactory.ComponentFactory.getInstance(asWeakReference=True)

        return cls.__component_factory__()
    # endregion
