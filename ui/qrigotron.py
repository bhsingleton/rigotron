from Qt import QtCore, QtWidgets, QtGui, QtCompat
from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.ui import quicwindow, qsignalblocker
from dcc.python import stringutils
from dcc.maya.models import qplugitemmodel, qplugstyleditemdelegate, qplugitemfiltermodel
from . import resources
from .models import qcomponentitemmodel
from ..libs import componentfactory, interopfactory, stateutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def onSceneChanged(*args, **kwargs):
    """
    Callback method after a scene IO operation has occurred.

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

        instance.sceneChanged(*args, **kwargs)

    else:

        log.warning('Unable to process scene changed callback!')


class QRigotron(quicwindow.QUicWindow):
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
        self._rigManager = interopfactory.InteropFactory.getInstance(asWeakReference=True)
        self._componentManager = componentfactory.ComponentFactory.getInstance(asWeakReference=True)
        self._controlRig = lambda: None
        self._callbackIds = om.MCallbackIdArray()

        # Declare public variables
        #
        self.mainSplitter = None
        self.outlinerWidget = None
        self.outlinerHeader = None
        self.nameLineEdit = None
        self.outlinerTreeView = None
        self.outlinerModel = None
        self.outlinerFooter = None
        self.propertyWidget = None
        self.propertyHeader = None
        self.filterPropertyLineEdit = None
        self.propertyTreeView = None
        self.propertyModel = None
        self.propertyItemDelegate = None
        self.propertyFilterModel = None
        self.propertyFooter = None

        self.statusWidget = None
        self.metaStatusPushButton = None
        self.skeletonStatusPushButton = None
        self.rigStatusPushButton = None
        self.statusButtonGroup = None

        self.addSpineComponentAction = None
        self.addLegComponentAction = None
        self.addArmComponentAction = None
        self.addHeadComponentAction = None
        self.addTailComponentAction = None
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def rigManager(self):
        """
        Returns the scene interface.

        :rtype: interopfactory.InteropFactory
        """

        return self._rigManager()

    @property
    def componentManager(self):
        """
        Returns the scene interface.

        :rtype: componentfactory.ComponentFactory
        """

        return self._componentManager()

    @property
    def controlRig(self):
        """
        Getter method that returns the active control rig.

        :rtype: rigotron.interops.controlrig.ControlRig
        """

        return self._controlRig()
    # endregion

    # region Callbacks
    def sceneChanged(self, *args, **kwargs):
        """
        Callback method that notifies the window of a scene change.

        :key clientData: Any
        :rtype: None
        """

        # Check if control rig exists
        #
        controlRigs = self.rigManager.controlRigs()
        numControlRigs = len(controlRigs)

        if numControlRigs == 1:

            # Update item models
            #
            self._controlRig = controlRigs[0].weakReference()

            self.nameLineEdit.setText(self.controlRig.rigName)
            self.outlinerModel.invisibleRootItem = self.scene(self.controlRig.rootComponent)
            self.propertyModel.invisibleRootItem = None

            # Update rig status
            #
            rigStatus = self.controlRig.getRigStatus()

            with qsignalblocker.QSignalBlocker(self.statusButtonGroup):

                self.statusButtonGroup.buttons()[rigStatus].setChecked(True)

        else:

            # Reset item models
            #
            self.nameLineEdit.setText('')
            self.outlinerModel.invisibleRootItem = None
            self.propertyModel.invisibleRootItem = None

            # Reset rig status
            #
            with qsignalblocker.QSignalBlocker(self.statusButtonGroup):

                self.statusButtonGroup.buttons()[0].setChecked(True)
    # endregion

    # region Events
    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).showEvent(event)

        # Add scene callback
        #
        callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, onSceneChanged)
        self._callbackIds.append(callbackId)

        callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, onSceneChanged)
        self._callbackIds.append(callbackId)

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).closeEvent(event)

        # Remove scene callback
        #
        om.MSceneMessage.removeCallbacks(self._callbackIds)
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigotron, self).postLoad(*args, **kwargs)

        # Initialize outliner tree view
        #
        self.outlinerModel = qcomponentitemmodel.QComponentItemModel(parent=self.outlinerTreeView)
        self.outlinerModel.setObjectName('outlinerModel')

        self.outlinerTreeView.setModel(self.outlinerModel)

        # Initialize property tree view
        #
        self.propertyModel = qplugitemmodel.QPlugItemModel(parent=self.propertyTreeView)
        self.propertyModel.setObjectName('propertyModel')

        self.propertyItemDelegate = qplugstyleditemdelegate.QPlugStyledItemDelegate(parent=self.propertyTreeView)
        self.propertyItemDelegate.setObjectName('propertyItemDelegate')

        self.propertyFilterModel = qplugitemfiltermodel.QPlugItemFilterModel(parent=self.propertyTreeView)
        self.propertyFilterModel.setObjectName('propertyFilterModel')
        self.propertyFilterModel.setSourceModel(self.propertyModel)
        self.propertyFilterModel.setIgnoreStaticAttributes(True)

        self.propertyTreeView.setModel(self.propertyFilterModel)
        self.propertyTreeView.setItemDelegate(self.propertyItemDelegate)

        # Initialize status button group
        #
        self.statusButtonGroup = QtWidgets.QButtonGroup(self.statusWidget)
        self.statusButtonGroup.addButton(self.metaStatusPushButton, id=0)
        self.statusButtonGroup.addButton(self.skeletonStatusPushButton, id=1)
        self.statusButtonGroup.addButton(self.rigStatusPushButton, id=2)
        self.statusButtonGroup.idClicked.connect(self.on_statusButtonGroup_idClicked)

        # Force scene change
        #
        self.sceneChanged()

    def selectedComponent(self):
        """
        Returns the current selected component.
        If no component is selected then the root component is returned instead!

        :rtype: Union[abstractcomponent.AbstractComponent, None]
        """

        indices = [index for index in self.outlinerTreeView.selectedIndexes() if index.column() == 0]
        numIndices = len(indices)

        if numIndices == 1:

            return self.outlinerModel.componentFromIndex(indices[0])

        elif self.controlRig is not None:

            return self.scene(self.controlRig.rootComponent)

        else:

            return None

    def createControlRig(self, name):
        """
        Creates a new control-rig with the specified name.

        :type name: str
        :rtype: controlrig.ControlRig
        """

        controlRig = self.rigManager.createControlRig(name)
        self.sceneChanged()

        return controlRig

    def addComponent(self, typeName, componentParent=None, componentSide=None):
        """
        Adds a component, of the specified typename, to the current control-rig.

        :type typeName: str
        :type componentParent: abstractcomponent.AbstractComponent
        :type componentSide: Side
        :rtype: abstractcomponent.AbstractComponent
        """

        # Redundancy check
        #
        if self.controlRig is None:

            log.warning(f'No valid control rig found!')
            return

        # Check if a parent was supplied
        #
        if componentParent is None:

            componentParent = self.selectedComponent()

        # Check if a side was supplied
        #
        if componentSide is None:

            componentSide = componentParent.componentSide

        # Get class constructor
        #
        cls = self.componentManager.getClass(typeName)

        if callable(cls):

            log.debug(f'Adding "{typeName}" to {componentParent}!')
            component = cls.create(componentParent=componentParent, componentSide=componentSide, parent=self.controlRig.componentsGroup)

            return component

        else:

            log.warning(f'Unable to locate "{typeName}" constructor!')
            return None
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_newAction_triggered(self, checked=False):
        """
        Slot method for the newAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Redundancy check
        #
        if self.controlRig is not None:

            log.warning('Control rig already exists!')
            return

        # Prompt user for folder name
        #
        name, response = QtWidgets.QInputDialog.getText(
            self,
            'Create New Rig',
            'Enter Name:',
            QtWidgets.QLineEdit.Normal
        )

        if not stringutils.isNullOrEmpty(name):

            self.createControlRig(name)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot()
    def on_nameLineEdit_returnPressed(self):
        """
        Slot method for the nameLineEdit's `returnPressed` signal.

        :rtype: None
        """

        # Check if control rig exists
        #
        sender = self.sender()
        text = sender.text()

        if self.controlRig is None:

            self.createControlRig(text)

        else:

            self.controlRig.rigName = text

    @QtCore.Slot(QtCore.QModelIndex)
    def on_outlinerTreeView_clicked(self, index):
        """
        Slot method for the outlinerTreeView's `clicked` signal.

        :type index: QtCore.QModelIndex
        :rtype: None
        """

        if index.isValid():

            component = self.outlinerModel.componentFromIndex(index)
            self.propertyModel.invisibleRootItem = component.object()
            self.propertyTreeView.expandAll()

    @QtCore.Slot(bool)
    def on_addSpineComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addSpineComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addLegComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addLegComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addFootComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addFootComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addClavicleComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addClavicleComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addArmComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addArmComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addHandComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addHandComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addHeadComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addHeadComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addTailComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addTailComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot()
    def on_alignPushButton_clicked(self):
        """
        Slot method for the `alignPushButton` widget's `clicked` signal.

        :rtype: None
        """

        pass

    @QtCore.Slot()
    def on_mirrorPushButton_clicked(self):
        """
        Slot method for the `mirrorPushButton` widget's `clicked` signal.

        :rtype: None
        """

        pass

    @QtCore.Slot()
    def on_freezePushButton_clicked(self):
        """
        Slot method for the `freezePushButton` widget's `clicked` signal.

        :rtype: None
        """

        pass

    @QtCore.Slot()
    def on_organizePushButton_clicked(self):
        """
        Slot method for the `organizePushButton` widget's `clicked` signal.

        :rtype: None
        """

        pass

    @QtCore.Slot()
    def on_detectPushButton_clicked(self):
        """
        Slot method for the `detectPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.scene.iterNodesByPattern('*_CTRL', apiType=om.MFn.kTransform):

            log.info(f'Detecting mirror settings: {node}')
            node.detectMirroring()

    @QtCore.Slot(bool)
    def on_blackBoxPushButton_clicked(self, checked=False):
        """
        Slot method for the `detectPushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        for container in self.scene.iterNodesByApiType(om.MFn.kDagContainer):

            container.blackBox = checked

    @QtCore.Slot(int)
    def on_statusButtonGroup_idClicked(self, index):
        """
        Slot method for the `statusButtonGroup` widget's `idClicked` signal.

        :type index: int
        :rtype: None
        """

        stateutils.changeState(self.controlRig, index)
    # endregion
