from abc import abstractmethod
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from dcc.ui.abstract import qabcmeta

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QAbstractTab(QtWidgets.QWidget, metaclass=qabcmeta.QABCMeta):
    """
    Overload of `QWidget` that outlines Rig o'Tron tab behaviour.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.pop('parent', None)
        f = kwargs.pop('f', QtCore.Qt.WindowFlags())

        super(QAbstractTab, self).__init__(parent=parent, f=f)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        self.__setup_ui__(*args, **kwargs)

    @abstractmethod
    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        pass
    # endregion

    # region Properties
    @property
    def nullWeakReference(self):
        """
        Getter method that returns a null weak reference.

        :rtype: Callable
        """

        return self.window().nullWeakReference

    @property
    def scene(self):
        """
        Returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self.window().scene

    @property
    def standaloneClient(self):
        """
        Getter method that returns the standalone client.

        :rtype: dcc.maya.standalone.rpc.RPCClient
        """

        return self.window().standaloneClient

    @property
    def interfaceManager(self):
        """
        Returns the interface manager.

        :rtype: interfacefactory.InterfaceFactory
        """

        return self.window().interfaceManager

    @property
    def componentManager(self):
        """
        Returns the component interface.

        :rtype: componentfactory.ComponentFactory
        """

        return self.window().componentManager

    @property
    def legacyRig(self):
        """
        Getter method that returns the active legacy rig.

        :rtype: rigotron.interops.controlrig.ControlRig
        """

        return self.window().legacyRig

    @property
    def controlRig(self):
        """
        Getter method that returns the active control rig.

        :rtype: rigotron.interops.controlrig.ControlRig
        """

        return self.window().controlRig
    # endregion

    # region Callbacks
    def activated(self):
        """
        Notifies the tab that it has been activated.

        :rtype: None
        """

        pass

    def clear(self):
        """
        Resets the user interface.

        :rtype: None
        """

        pass

    def invalidate(self):
        """
        Refresh the user interface.

        :rtype: None
        """

        pass
    # endregion
