from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.ui import qsingletonwindow
from dcc.maya.standalone import rpc
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from functools import partial
from . import resources
from .tabs import qrigtab, qpropstab, qskinstab, qlogstab
from ..libs import componentfactory, interfacefactory

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def onSceneOpening(*args, **kwargs):
    """
    Callback method for any pre-scene open delegation.

    :rtype: None
    """

    # Check if instance exists
    #
    instance = QRigotron.getInstance()

    if instance is None:

        return

    # Evaluate if instance is still valid
    #
    if QtCompat.isValid(instance):

        instance.sceneOpening(*args, **kwargs)

    else:

        log.warning('Unable to process scene changed callback!')


def onSceneOpened(*args, **kwargs):
    """
    Callback method for any post-scene openi delegation.

    :rtype: None
    """

    # Check if instance exists
    #
    instance = QRigotron.getInstance()

    if instance is None:

        return

    # Evaluate if instance is still valid
    #
    if QtCompat.isValid(instance):

        mc.evalDeferred(partial(instance.sceneOpened, *args, **kwargs))  # Allows scene to fully load before processing changes!

    else:

        log.warning('Unable to process scene changed callback!')


class QRigotron(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QUicWindow` that interfaces with control rigs.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._standaloneProcess, self._standaloneClient = None, None
        self._interfaceManager = interfacefactory.InterfaceFactory.getInstance(asWeakReference=True)
        self._componentManager = componentfactory.ComponentFactory.getInstance(asWeakReference=True)
        self._legacyRig = self.nullWeakReference
        self._controlRig = self.nullWeakReference
        self._callbackIds = om.MCallbackIdArray()

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).__setup_ui__(*args, **kwargs)

        # Initialize main window
        #
        self.setWindowTitle("|| Rig o'Tron")
        self.setMinimumSize(QtCore.QSize(600, 400))

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')
        centralLayout.setContentsMargins(1, 1, 1, 1)

        centralWidget = QtWidgets.QWidget(parent=self)
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize tab-control
        #
        self.tabControl = QtWidgets.QTabWidget(parent=self)
        self.tabControl.setObjectName('tabControl')
        self.tabControl.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.tabControl.currentChanged.connect(self.on_tabControl_currentChanged)

        self.rigTab = qrigtab.QRigTab(parent=self.tabControl)
        self.propsTab = qpropstab.QPropsTab(parent=self.tabControl)
        self.skinsTab = qskinstab.QSkinsTab(parent=self.tabControl)
        self.logsTab = qlogstab.QLogsTab(parent=self.tabControl)

        self.tabControl.addTab(self.rigTab, 'Control-Rig')
        self.tabControl.addTab(self.propsTab, 'Props')
        self.tabControl.addTab(self.skinsTab, 'Skins')
        self.tabControl.addTab(self.logsTab, 'Logs')

        centralLayout.addWidget(self.tabControl)
    # endregion

    # region Properties
    @property
    def nullWeakReference(self):
        """
        Getter method that returns a null weak reference.

        :rtype: Callable
        """

        return lambda: None

    @property
    def scene(self):
        """
        Returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def standaloneClient(self):
        """
        Getter method that returns the standalone client.

        :rtype: rpc.RPCClient
        """

        return self._standaloneClient

    @property
    def interfaceManager(self):
        """
        Returns the interface interface.

        :rtype: interfacefactory.InterfaceFactory
        """

        return self._interfaceManager()

    @property
    def componentManager(self):
        """
        Returns the component interface.

        :rtype: componentfactory.ComponentFactory
        """

        return self._componentManager()

    @property
    def legacyRig(self):
        """
        Getter method that returns the active legacy rig.

        :rtype: rigotron.interops.controlrig.ControlRig
        """

        return self._legacyRig()

    @property
    def controlRig(self):
        """
        Getter method that returns the active control rig.

        :rtype: rigotron.interops.controlrig.ControlRig
        """

        return self._controlRig()
    # endregion

    # region Callbacks
    def sceneOpening(self, *args, **kwargs):
        """
        Notifies the component item model a scene is being opened.

        :key clientData: Any
        :rtype: None
        """

        self.clear()

    def sceneOpened(self, *args, **kwargs):
        """
        Notifies the component item model a scene has been opened.

        :key clientData: Any
        :rtype: None
        """

        self.invalidate()
    # endregion

    # region Methods
    def opening(self):
        """
        Performs all the necessary actions during startup.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).opening()

        # Initialize remote standalone server
        #
        self._standaloneProcess, self._standaloneClient = rpc.initializeRemoteStandalone()

        if isinstance(self._standaloneProcess, QtCore.QProcess):

            self.logsTab.process = self._standaloneProcess

        # Force callback update
        #
        self.sceneOpened()

    def closing(self):
        """
        Performs all the necessary actions during shutdown.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).closing()

        # Uninitialize remote standalone server
        #
        if rpc.isRemoteStandaloneRunning():

            self._standaloneClient.quit()
            self._standaloneProcess, self._standaloneClient = None, None

    def addCallbacks(self):
        """
        Adds any callbacks required by this window.

        :rtype: None
        """

        # Add callbacks
        #
        hasCallbacks = len(self._callbackIds) > 0

        if not hasCallbacks:

            callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeNew, onSceneOpening)
            self._callbackIds.append(callbackId)

            callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeOpen, onSceneOpening)
            self._callbackIds.append(callbackId)

            callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kSceneUpdate, onSceneOpened)
            self._callbackIds.append(callbackId)

    def removeCallbacks(self):
        """
        Removes any callbacks created by this window.

        :rtype: None
        """

        # Remove callbacks
        #
        hasCallbacks = len(self._callbackIds) > 0

        if hasCallbacks:

            om.MMessage.removeCallbacks(self._callbackIds)
            self._callbackIds.clear()

    def iterTabs(self):
        """
        Returns a generator that yields tabs.

        :rtype: Iterator[qabstracttab.QAbstractTab]
        """

        tabCount = self.tabControl.count()

        for i in range(tabCount):

            yield self.tabControl.widget(i)

    def clear(self):
        """
        Resets the user interface.

        :rtype: None
        """

        # Reset internal references
        #
        self._controlRig = self.nullWeakReference
        self._legacyRig = self.nullWeakReference

        # Iterate through tabs and notify
        #
        for tab in self.iterTabs():

            tab.clear()

    def invalidate(self):
        """
        Refresh the user interface.

        :rtype: None
        """

        # Evaluate scene contents
        #
        controlRigs = self.interfaceManager.controlRigs()
        hasControlRig = len(controlRigs) == 1

        if hasControlRig:

            # Check if control rig is up-to-date
            #
            controlRig = controlRigs[0]
            isUpToDate = (controlRig.rigVersion >= 1.0)

            if isUpToDate:

                self._controlRig = controlRig.weakReference()

            else:

                self._legacyRig = controlRig.weakReference()

            # Check if control rig has a referenced skeleton
            #
            hasReferencedSkeleton = controlRig.hasReferencedSkeleton()

            if hasReferencedSkeleton:

                referenceNode = self.scene(controlRig.skeletonReference)
                referencePath = referenceNode.filePath()

                self.standaloneClient.open(referencePath)

        else:

            log.debug('Scene contains no control-rigs...')

        # Iterate through tabs and notify
        #
        for tab in self.iterTabs():

            tab.invalidate()
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_tabControl_currentChanged(self, index):
        """
        Slot method for the `tabControl` widget's `currentChanged` signal.

        :type index: int
        :rtype: None
        """

        tabControl = self.sender()  # type: QtWidgets.QTabWidget

        tabWidget = tabControl.widget(index)
        tabWidget.activated()
    # endregion
