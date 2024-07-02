from mpy import mpynodeextension
from mpy.abstract import mabcmeta
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractInterface(mpynodeextension.MPyNodeExtension, metaclass=mabcmeta.MABCMeta):
    """
    Overload of `MPyNodeExtension` that outlines the rig interface behaviour.
    """

    # region Dunderscores
    __interface_factory__ = None
    __component_factory__ = None
    # endregion

    # region Properties
    @classproperty
    def rigManager(cls):
        """
        Returns the rig interop manager.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: rigotron.libs.interfacefactory.InterfaceFactory
        """

        # Check if factory exists
        #
        if cls.__interface_factory__ is None:

            from ..libs import interfacefactory
            cls.__interface_factory__ = interfacefactory.InterfaceFactory.getInstance(asWeakReference=True)

        return cls.__interface_factory__()

    @classproperty
    def componentManager(cls):
        """
        Returns the rig interop manager.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: rigotron.libs.componentfactory.ComponentFactory
        """

        # Check if factory exists
        #
        if cls.__component_factory__ is None:

            from ..libs import componentfactory
            cls.__component_factory__ = componentfactory.ComponentFactory.getInstance(asWeakReference=True)

        return cls.__component_factory__()
    # endregion
