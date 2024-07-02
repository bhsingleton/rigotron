from Qt import QtCore, QtWidgets, QtGui, QtCompat
from itertools import chain
from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.ui import quicwindow, qsignalblocker
from dcc.python import stringutils
from dcc.maya.libs import transformutils
from dcc.maya.models import qplugitemmodel, qplugstyleditemdelegate, qplugitemfiltermodel
from dcc.maya.decorators.undo import undo
from . import resources
from .models import qcomponentitemmodel, qpropertyitemmodel
from ..libs import Status, Side, componentfactory, interfacefactory, stateutils, layerutils

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
        self._rigManager = interfacefactory.InterfaceFactory.getInstance(asWeakReference=True)
        self._componentManager = componentfactory.ComponentFactory.getInstance(asWeakReference=True)
        self._controlRig = self.nullWeakReference
        self._currentComponent = self.nullWeakReference
        self._currentStatus = 0
        self._callbackIds = om.MCallbackIdArray()

        # Declare public variables
        #
        self.mainSplitter = None
        self.outlinerWidget = None
        self.outlinerHeader = None
        self.nameLineEdit = None
        self.outlinerTreeView = None
        self.outlinerModel = None  # type: qcomponentitemmodel.QComponentItemModel
        self.deleteShortcut = None
        self.attachmentComboBox = None

        self.propertyWidget = None
        self.propertyHeader = None
        self.filterPropertyLineEdit = None
        self.propertyTreeView = None
        self.propertyModel = None  # type: qpropertyitemmodel.QPropertyItemModel
        self.propertyItemDelegate = None  # type: qplugstyleditemdelegate.QPlugStyledItemDelegate
        self.propertyFilterModel = None  # type: qplugitemfiltermodel.QPlugItemFilterModel

        self.interopWidget = None
        self.alignPushButton = None
        self.mirrorPushButton = None
        self.sanitizePushButton = None
        self.organizePushButton = None
        self.detectPushButton = None
        self.blackBoxPushButton = None

        self.statusWidget = None
        self.metaStatusPushButton = None
        self.skeletonStatusPushButton = None
        self.rigStatusPushButton = None
        self.statusButtonGroup = None

        self.addSpineComponentAction = None
        self.addLegComponentAction = None
        self.addFootComponentAction = None
        self.addArmComponentAction = None
        self.addHandComponentAction = None
        self.addHeadComponentAction = None
        self.addTailComponentAction = None
        self.addPropComponentAction = None
        self.addStowedComponentAction = None
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
    def rigManager(self):
        """
        Returns the scene interface.

        :rtype: interfacefactory.InterfaceFactory
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

    @property
    def currentComponent(self):
        """
        Getter method that returns the current component.

        :rtype: rigotron.components.basecomponent.BaseComponent
        """

        return self._currentComponent()
    # endregion

    # region Callbacks
    def sceneChanged(self, *args, **kwargs):
        """
        Callback method that notifies the window of a scene change.

        :key clientData: Any
        :rtype: None
        """

        self.invalidateControlRig()
    # endregion

    # region Events
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

        # Add shortcuts to outliner tree view
        #
        self.deleteShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('delete'), self.outlinerTreeView, self.on_outlinerTreeView_deleteKeyPressed)

        # Initialize property tree view
        #
        self.propertyModel = qpropertyitemmodel.QPropertyItemModel(parent=self.propertyTreeView)
        self.propertyModel.setObjectName('propertyModel')

        self.propertyItemDelegate = qplugstyleditemdelegate.QPlugStyledItemDelegate(parent=self.propertyTreeView)
        self.propertyItemDelegate.setObjectName('propertyItemDelegate')

        self.propertyFilterModel = qplugitemfiltermodel.QPlugItemFilterModel(parent=self.propertyTreeView)
        self.propertyFilterModel.setObjectName('propertyFilterModel')
        self.propertyFilterModel.setSourceModel(self.propertyModel)
        self.propertyFilterModel.setHideStaticAttributes(True)

        self.propertyTreeView.setModel(self.propertyFilterModel)
        self.propertyTreeView.setItemDelegate(self.propertyItemDelegate)

        # Initialize status button group
        #
        self.statusButtonGroup = QtWidgets.QButtonGroup(self.statusWidget)
        self.statusButtonGroup.addButton(self.metaStatusPushButton, id=0)
        self.statusButtonGroup.addButton(self.skeletonStatusPushButton, id=1)
        self.statusButtonGroup.addButton(self.rigStatusPushButton, id=2)
        self.statusButtonGroup.idClicked.connect(self.on_statusButtonGroup_idClicked)

        # Add scene changed callbacks
        #
        callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, onSceneChanged)
        self._callbackIds.append(callbackId)

        callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, onSceneChanged)
        self._callbackIds.append(callbackId)

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
        Component = self.componentManager.getClass(typeName)

        if callable(Component):

            log.debug(f'Adding "{typeName}" to {componentParent}!')
            component = Component.create(componentSide=componentSide, parent=self.controlRig.componentsGroup)

            parentIndex = self.outlinerModel.indexFromComponent(componentParent)
            self.outlinerModel.appendRow(component, parent=parentIndex)

            return component

        else:

            log.warning(f'Unable to locate "{typeName}" constructor!')
            return None

    def invalidateControlRig(self):
        """
        Invalidates the control rig related widgets.

        :rtype: None
        """

        # Check if control rig exists
        #
        controlRigs = self.rigManager.controlRigs()
        numControlRigs = len(controlRigs)

        if numControlRigs == 1:

            # Update user interface
            #
            self._controlRig = controlRigs[0].weakReference()
            self._currentComponent = self.nullWeakReference

            self.nameLineEdit.setText(self.controlRig.rigName)
            self.outlinerModel.rootComponent = self.scene(self.controlRig.rootComponent)

        else:

            # Reset user interface
            #
            self._controlRig = self.nullWeakReference
            self._currentComponent = self.nullWeakReference

            self.nameLineEdit.setText('')
            self.outlinerModel.rootComponent = None

        # Update component status
        #
        self.invalidateProperties()
        self.invalidateAttachments()
        self.invalidateStatus()

    def invalidateProperties(self):
        """
        Updates the property item model.

        :rtype: None
        """

        # Check if current component is valid
        #
        if self.currentComponent is None:

            self.propertyModel.invisibleRootItem = None
            return

        # Check if current component still exists
        #
        if self.currentComponent.isAlive():

            self.propertyModel.invisibleRootItem = self.currentComponent.object()
            self.propertyModel.readOnly = Status(self.currentComponent.componentStatus) != Status.META

        else:

            self.propertyModel.invisibleRootItem = None

    def invalidateAttachments(self):
        """
        Updates the attachment drop-down menu.

        :rtype: None
        """

        # Check if current component is valid
        #
        if self.currentComponent is not None:

            skeletonSpecs = self.currentComponent.getAttachmentOptions()
            jointNames = [skeletonSpec.name for skeletonSpec in skeletonSpecs]

            with qsignalblocker.QSignalBlocker(self.attachmentComboBox):

                self.attachmentComboBox.clear()
                self.attachmentComboBox.addItems(jointNames)
                self.attachmentComboBox.setCurrentIndex(self.currentComponent.attachmentId)

        else:

            with qsignalblocker.QSignalBlocker(self.attachmentComboBox):

                self.attachmentComboBox.clear()

    def invalidateStatus(self):
        """
        Updates the status buttons.

        :rtype: None
        """

        self._currentStatus = Status(self.currentComponent.componentStatus) if (self.currentComponent is not None) else Status.META

        with qsignalblocker.QSignalBlocker(self.statusButtonGroup):

            buttons = self.statusButtonGroup.buttons()
            buttons[self._currentStatus].setChecked(True)

    @undo(name='Align Nodes')
    def alignNodes(self, *nodes):
        """
        Aligns the transforms on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Check if enough nodes were supplied
        #
        numNodes = len(nodes)

        if not (numNodes >= 2):

            log.warning('Not enough joints selected to align!')
            return

        # Evaluate node count
        #
        if numNodes == 2:

            firstNode, lastNode = nodes
            lastNode.copyTransform(firstNode, skipScale=True)

        else:

            *firstNodes, lastNode = nodes
            numFirstNodes = len(firstNodes)

            weight = 1.0 / numFirstNodes
            averagedMatrix = firstNodes[0].worldMatrix()

            for firstNode in firstNodes[1:]:

                worldMatrix = firstNode.worldMatrix()
                averagedMatrix = transformutils.lerpMatrix(averagedMatrix, worldMatrix, weight=weight)

            lastNode.setWorldMatrix(averagedMatrix, skipScale=True)

    @undo(name='Mirror Joints')
    def mirrorJoints(self, *joints):
        """
        Mirrors the transforms on the supplied joints.

        :type joints: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through joints
        #
        for joint in joints:

            # Evaluate joint side
            #
            side = Side(joint.side)

            if side not in (Side.LEFT, Side.RIGHT):

                continue

            # Evaluate joint orients
            #
            preEulerRotation = joint.preEulerRotation()  # type: om.MEulerRotation

            if not preEulerRotation.isEquivalent(om.MEulerRotation.kIdentity):

                joint.unfreezePivots()
                joint.mirrorAttr(joint['jointOrientX'])
                joint.mirrorAttr(joint['jointOrientY'])
                joint.mirrorAttr(joint['jointOrientZ'])

            # Evaluate joint parent
            # This will impact which attributes get inversed!
            #
            parent = joint.parent()
            hasParent = parent is not None

            if hasParent:

                joint.mirrorAttr(joint['translateX'], inverse=False)
                joint.mirrorAttr(joint['translateY'], inverse=False)
                joint.mirrorAttr(joint['translateZ'], inverse=True)

                joint.mirrorAttr(joint['rotateX'], inverse=True)
                joint.mirrorAttr(joint['rotateY'], inverse=True)
                joint.mirrorAttr(joint['rotateZ'], inverse=False)

            else:  # World space

                matrix = joint.matrix()
                xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)

                mirrorXAxis = transformutils.mirrorVector(xAxis)
                mirrorYAxis = transformutils.mirrorVector(yAxis)
                mirrorZAxis = -transformutils.mirrorVector(zAxis)
                mirrorPos = om.MPoint(-pos.x, pos.y, pos.z, pos.w)
                mirrorMatrix = transformutils.composeMatrix(mirrorXAxis, mirrorYAxis, mirrorZAxis, mirrorPos)

                oppositeJoint = joint.getOppositeNode()
                oppositeJoint.setMatrix(mirrorMatrix, skipScale=True)

    @undo(name='Sanitize Joints')
    def sanitizeJoints(self, *joints):
        """
        Sanitizes the transform on the supplied joints.

        :type joints: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        for joint in joints:

            joint.unfreezePivots()
    # endregion

    # region Slots
    @QtCore.Slot(QtCore.QModelIndex)
    def on_outlinerTreeView_clicked(self, index):
        """
        Slot method for the `outlinerTreeView` widget's `clicked` signal.

        :type index: QtCore.QModelIndex
        :rtype: None
        """

        # Check if index is valid
        #
        if not index.isValid():

            return

        # Update current component
        #
        component = self.outlinerModel.componentFromIndex(index)

        if component is not None:

            self._currentComponent = component.weakReference()

        else:

            self._currentComponent = self.nullWeakReference

        # Invalidate user interface
        #
        self.invalidateProperties()
        self.invalidateAttachments()
        self.invalidateStatus()

    @QtCore.Slot()
    def on_outlinerTreeView_deleteKeyPressed(self):
        """
        Slot method for the `outlinerTreeView` widget's `delete` key shortcut.

        :rtype: None
        """

        # Iterate through selected indices
        #
        selectedIndices = [index for index in self.outlinerTreeView.selectedIndexes() if index.column() == 0]

        for index in selectedIndices:

            # Check if component is meta
            #
            component = self.outlinerModel.componentFromIndex(index)
            componentStatus = Status(component.componentStatus)

            isMeta = componentStatus == Status.META

            if not isMeta:

                log.warning(f'{component} must be in the meta state before deleting!')
                continue

            # Check if component has no children
            #
            componentChildren = list(component.iterComponentChildren())
            hasChildren = len(componentChildren) > 0

            if hasChildren:

                log.warning(f'{component} must have no children before deleting!')
                continue

            # Remove component from rig
            #
            self.outlinerModel.removeRow(index.row(), parent=index.parent())

    @QtCore.Slot(int)
    def on_attachmentComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `attachmentComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        if self.currentComponent is not None:

            self.currentComponent.attachmentId = index

    @QtCore.Slot(bool)
    def on_addRootComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addRootComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if control rig exists
        #
        if self.controlRig is not None:

            return QtWidgets.QMessageBox.warning(self, 'Create New Rig', 'Control rig already exists!')

        # Prompt user for name input
        #
        text, success = QtWidgets.QInputDialog.getText(
            self,
            'Create New Rig',
            'Enter name:',
            QtWidgets.QLineEdit.Normal
        )

        if success and not stringutils.isNullOrEmpty(text):

            self.createControlRig(text)

        else:

            log.info('Operation aborted...')

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

    @QtCore.Slot(bool)
    def on_addPropComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addPropComponentAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.addComponent(self.sender().whatsThis())

    @QtCore.Slot(bool)
    def on_addStowedComponentAction_triggered(self, checked=False):
        """
        Slot method for the `addStowedComponentAction` widget's `triggered` signal.

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

        nodes = list(self.scene.iterSelection(apiType=om.MFn.kTransform))
        self.alignNodes(*nodes)

    @QtCore.Slot()
    def on_mirrorPushButton_clicked(self):
        """
        Slot method for the `mirrorPushButton` widget's `clicked` signal.

        :rtype: None
        """

        joints = list(self.scene.iterSelection(apiType=om.MFn.kJoint))
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ShiftModifier:

            joints = list(chain(*[joint.descendants(apiType=om.MFn.kJoint, includeSelf=True) for joint in joints]))

        self.mirrorJoints(*joints)

    @QtCore.Slot()
    def on_sanitizePushButton_clicked(self):
        """
        Slot method for the `sanitizePushButton` widget's `clicked` signal.

        :rtype: None
        """

        joints = list(self.scene.iterSelection(apiType=om.MFn.kJoint))
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ShiftModifier:

            joints = list(chain(*[joint.descendants(apiType=om.MFn.kJoint, includeSelf=True) for joint in joints]))

        self.sanitizeJoints(*joints)

    @QtCore.Slot()
    def on_organizePushButton_clicked(self):
        """
        Slot method for the `organizePushButton` widget's `clicked` signal.

        :rtype: None
        """

        layerutils.createDisplayLayers(self.controlRig)

    @QtCore.Slot()
    def on_detectPushButton_clicked(self):
        """
        Slot method for the `detectPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for container in self.scene.iterNodesByApiType(om.MFn.kDagContainer):

            for node in container.publishedNodes():

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

        # Evaluate current component
        #
        if self.currentComponent is None:

            log.warning('No component selected to update!')
            self.invalidateStatus()

        # Try and process state change
        #
        status = Status(index)

        try:

            stateutils.changeState(self.currentComponent, status)

        except stateutils.StateError:

            QtWidgets.QMessageBox.warning(self, 'Change Rig Status', 'Cannot change status while parent is in a different state!')

        finally:

            self.invalidateStatus()
    # endregion
