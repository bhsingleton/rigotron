import os

from dcc.python import stringutils
from dcc.perforce import clientutils
from dcc.maya.decorators import undo
from dcc.generators.inclusiverange import inclusiveRange
from dcc.ui import qsignalblocker, qdivider
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from enum import IntEnum
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Columns(IntEnum):
    """
    Enum class of skin-tab columns.
    """

    NAME = 0
    FILE_PATH = 1


class QSkinsTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with referenced skins.
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
        super(QSkinsTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._referenceNodes = []
        self._referenceCount = 0
        self._selectedRow = None
        self._selectedReference = self.nullWeakReference

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QSkinsTab, self).__setup_ui__(*args, **kwargs)

        # Initialize widget
        #
        self.setObjectName('skinsTab')

        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('skinsTabLayout')
        self.setLayout(centralLayout)

        # Initialize skins group-box
        #
        self.skinsLayout = QtWidgets.QGridLayout()
        self.skinsLayout.setObjectName('skinsLayout')

        self.skinsGroupBox = QtWidgets.QGroupBox('Referenced Skins:')
        self.skinsGroupBox.setObjectName('skinsGroupBox')
        self.skinsGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.skinsGroupBox.setLayout(self.skinsLayout)

        self.skinTableWidget = QtWidgets.QTableWidget()
        self.skinTableWidget.setObjectName('skinTableWidget')
        self.skinTableWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.skinTableWidget.setStyleSheet('QTableWidget::item { height: 24px; }')
        self.skinTableWidget.setWordWrap(False)
        self.skinTableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.skinTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.skinTableWidget.setAlternatingRowColors(True)
        self.skinTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.skinTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.skinTableWidget.itemChanged.connect(self.on_skinTableWidget_itemChanged)
        self.skinTableWidget.itemSelectionChanged.connect(self.on_skinTableWidget_itemSelectionChanged)

        columnCount = len(Columns)
        columnLabels = [key.title().replace('_', ' ') for (key, value) in Columns.__members__.items()]
        self.skinTableWidget.setColumnCount(columnCount)
        self.skinTableWidget.setHorizontalHeaderLabels(columnLabels)

        horizontalHeader = self.skinTableWidget.horizontalHeader()  # type: QtWidgets.QHeaderView
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.resizeSection(0, 200)
        horizontalHeader.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        horizontalHeader.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.skinsLayout.addWidget(self.skinTableWidget, 0, 0)

        centralLayout.addWidget(self.skinsGroupBox)

        # Initialize edit group-box
        #
        self.editLayout = QtWidgets.QGridLayout()
        self.editLayout.setObjectName('editLayout')

        self.editGroupBox = QtWidgets.QGroupBox('Edit:')
        self.editGroupBox.setObjectName('editGroupBox')
        self.editGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.editGroupBox.setLayout(self.editLayout)

        self.createSkinPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/new_file.svg'), 'Create')
        self.createSkinPushButton.setObjectName('createSkinPushButton')
        self.createSkinPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.createSkinPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createSkinPushButton.clicked.connect(self.on_createSkinPushButton_clicked)

        self.addSkinPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/add.svg'), 'Add')
        self.addSkinPushButton.setObjectName('addSkinPushButton')
        self.addSkinPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.addSkinPushButton.setFixedHeight(24)
        self.addSkinPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addSkinPushButton.clicked.connect(self.on_addSkinPushButton_clicked)

        self.removeSkinPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/remove.svg'), 'Remove')
        self.removeSkinPushButton.setObjectName('removeSkinPushButton')
        self.removeSkinPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.removeSkinPushButton.setFixedHeight(24)
        self.removeSkinPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removeSkinPushButton.clicked.connect(self.on_removeSkinPushButton_clicked)

        self.renameSkinPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/rename.svg'), 'Rename')
        self.renameSkinPushButton.setObjectName('renameSkinPushButton')
        self.renameSkinPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.renameSkinPushButton.setFixedHeight(24)
        self.renameSkinPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.renameSkinPushButton.clicked.connect(self.on_renameSkinPushButton_clicked)

        self.reloadSkinPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/refresh.svg'), 'Reload')
        self.reloadSkinPushButton.setObjectName('reloadSkinPushButton')
        self.reloadSkinPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.reloadSkinPushButton.setFixedHeight(24)
        self.reloadSkinPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.reloadSkinPushButton.clicked.connect(self.on_reloadSkinPushButton_clicked)

        self.divider = qdivider.QDivider(QtCore.Qt.Orientation.Vertical)

        self.moveSkinUpPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/item_up.png'), 'Move Up')
        self.moveSkinUpPushButton.setObjectName('moveSkinUpPushButton')
        self.moveSkinUpPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.moveSkinUpPushButton.setFixedHeight(24)
        self.moveSkinUpPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.moveSkinUpPushButton.clicked.connect(self.on_moveSkinUpPushButton_clicked)

        self.moveSkinDownPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/item_down.png'), 'Move Down')
        self.moveSkinDownPushButton.setObjectName('moveSkinDownPushButton')
        self.moveSkinDownPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.moveSkinDownPushButton.setFixedHeight(24)
        self.moveSkinDownPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.moveSkinDownPushButton.clicked.connect(self.on_moveSkinDownPushButton_clicked)

        self.editLayout.addWidget(self.createSkinPushButton, 0, 0, 2, 1)
        self.editLayout.addWidget(self.addSkinPushButton, 0, 1)
        self.editLayout.addWidget(self.removeSkinPushButton, 0, 2)
        self.editLayout.addWidget(self.divider, 0, 3, 2, 1)
        self.editLayout.addWidget(self.moveSkinUpPushButton, 0, 4)
        self.editLayout.addWidget(self.renameSkinPushButton, 1, 1)
        self.editLayout.addWidget(self.reloadSkinPushButton, 1, 2)
        self.editLayout.addWidget(self.moveSkinDownPushButton, 1, 4)

        centralLayout.addWidget(self.editGroupBox)
    # endregion

    # region Properties
    @property
    def referenceNodes(self):
        """
        Getter method that returns the current reference nodes.

        :rtype: List[mpy.builtins.referencemixin.ReferenceMixin]
        """

        return tuple(self._referenceNodes)

    @property
    def referenceCount(self):
        """
        Getter method that returns the number of references.

        :rtype: int
        """

        return self._referenceCount

    @property
    def selectedReference(self):
        """
        Getter method that returns the selected reference.

        :rtype: Union[mpy.builtins.referencemixin.ReferenceMixin, None]
        """

        return self._selectedReference()

    @property
    def selectedRow(self):
        """
        Getter method that returns the selected row.

        :rtype: int
        """

        return self._selectedRow
    # endregion

    # region Callbacks
    def activated(self):
        """
        Notifies the tab that it has been activated.

        :rtype: None
        """

        self.invalidateSkins()
    # endregion

    # region Methods
    @classmethod
    def createTableWidgetItems(cls, name, filePath, loaded=False):
        """
        Returns a row of table widget items based on the supplied parameters.

        :type name: str
        :type filePath: str
        :type loaded: bool
        :rtype: Tuple[QtWidgets.QTableWidgetItem, QtWidgets.QTableWidgetItem, QtWidgets.QTableWidgetItem]
        """

        nameItem = QtWidgets.QTableWidgetItem(QtGui.QIcon(':/reference.svg'), name)
        nameItem.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        nameItem.setCheckState(QtCore.Qt.CheckState.Checked if loaded else QtCore.Qt.CheckState.Unchecked)

        filePathItem = QtWidgets.QTableWidgetItem(filePath)
        filePathItem.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled)

        return nameItem, filePathItem

    @classmethod
    def resizeTableWidgetItems(cls, tableWidget, size):
        """
        Resizes the supplied table widget to the specified size.

        :type tableWidget: QtWidgets.QTableWidget
        :type size: int
        :rtype: QtWidgets.QTableWidget
        """

        count = tableWidget.rowCount()

        with qsignalblocker.QSignalBlocker(tableWidget):

            if size > count:

                tableWidget.setRowCount(size)

                for row in inclusiveRange(count, size - 1):

                    items = cls.createTableWidgetItems('', '')

                    for (column, item) in enumerate(items):

                        tableWidget.setItem(row, column, item)

            elif size < count:

                tableWidget.setRowCount(size)

            else:

                pass

        return tableWidget

    def hasSelection(self):
        """
        Evaluates if there is a valid selection.

        :rtype: bool
        """

        return isinstance(self._selectedRow, int)

    @undo.Undo(state=False)
    def createSkin(self, filePath, namespace=None):
        """
        Creates a new skin and adds it to the scene file.

        :type filePath: str
        :type namespace: Union[str, None]
        :rtype: mpy.builtins.referencemixin.ReferenceMixin
        """

        # Check if path is absolute
        #
        client = clientutils.getCurrentClient()
        clientExists = client is not None
        isRelativeToClient = client.hasAbsoluteFile(filePath) if clientExists else False

        resolvedPath = filePath

        if isRelativeToClient:

            relativePath = client.mapToRoot(filePath)
            resolvedPath = os.path.join('$P4ROOT', relativePath)

        # Check if a namespace was supplied
        #
        if stringutils.isNullOrEmpty(namespace):

            filename = os.path.basename(filePath)
            name, extension = os.path.splitext(filename)

            namespace = name.replace('SKL_', '').replace('_ExportRig', '')

        # Create new scene file
        #
        referenceNode = self.scene(self.controlRig.skeletonReference)
        referencePath = referenceNode.filePath(resolvedName=False)

        self.standaloneClient.new()
        self.standaloneClient.file(referencePath, reference=True, namespace=':')
        self.standaloneClient.saveAs(filePath)

        # Create reference to scene file
        #
        return self.controlRig.addSkin(resolvedPath, namespace=namespace)

    @undo.Undo(state=False)
    def addSkin(self, filePath, namespace=None):
        """
        Adds a pre-existing skin to the scene file.

        :type filePath: str
        :type namespace: Union[str, None]
        :rtype: mpy.builtins.referencemixin.ReferenceMixin
        """

        # Check if path is absolute
        #
        client = clientutils.getCurrentClient()
        clientExists = client is not None
        isRelativeToClient = client.hasAbsoluteFile(filePath) if clientExists else False

        resolvedPath = filePath

        if isRelativeToClient:

            relativePath = client.mapToRoot(filePath)
            resolvedPath = os.path.join('$P4ROOT', relativePath)

        # Check if a namespace was supplied
        #
        if stringutils.isNullOrEmpty(namespace):

            filename = os.path.basename(filePath)
            name, extension = os.path.splitext(filename)

            namespace = name.replace('SKL_', '').replace('_ExportRig', '')

        # Create reference to scene file
        #
        return self.controlRig.addSkin(resolvedPath, namespace=namespace)

    @undo.Undo(state=False)
    def removeSkin(self, index):
        """
        Removes the skin at the specified index.

        :type index: int
        :rtype: bool
        """

        return self.controlRig.removeSkin(index)

    def clear(self):
        """
        Resets the user interface.

        :rtype: None
        """

        # Clear internal references
        #
        self._referenceNodes.clear()
        self._referenceCount = 0

        self._selectedRow = None
        self._selectedReference = self.nullWeakReference

        # Invalidate table widget
        #
        self.invalidateSkins()

    def invalidate(self):
        """
        Refreshes the user interface.

        :rtype: None
        """

        # Check if control-rig exists
        #
        if self.controlRig is None:

            return

        # Update internal references
        #
        self._referenceNodes.clear()
        self._referenceNodes.extend(tuple(map(self.scene, self.controlRig.skinReference)))
        self._referenceCount = len(self._referenceNodes)

        # Invalidate table widget
        #
        self.invalidateSkins()

    def invalidateSkins(self):
        """
        Refreshes the table widget.

        :rtype: None
        """

        # Iterate through rows
        #
        self.resizeTableWidgetItems(self.skinTableWidget, self._referenceCount)

        for (row, referenceNode) in enumerate(self._referenceNodes):

            referenceName = referenceNode.name()
            referencePath = referenceNode.filePath(resolvedName=False)
            referenceLoaded = referenceNode.isLoaded()

            nameItem, filePathItem = self.skinTableWidget.item(row, Columns.NAME), self.skinTableWidget.item(row, Columns.FILE_PATH)

            with qsignalblocker.QSignalBlocker(self.skinTableWidget):

                nameItem.setText(referenceName)
                nameItem.setCheckState(QtCore.Qt.CheckState.Checked if referenceLoaded else QtCore.Qt.CheckState.Unchecked)

                filePathItem.setText(referencePath)
    # endregion

    # region Slots
    @QtCore.Slot(QtWidgets.QTableWidgetItem)
    def on_skinTableWidget_itemChanged(self, item):
        """
        Slot method for the `skinTableWidget` widget's `itemChanged` signal.

        :type item: QtWidgets.QTableWidgetItem
        :rtype: None
        """

        # Evaluate item's column
        #
        column = item.column()
        isNameColumn = (column == Columns.NAME)

        if not isNameColumn:

            return

        # Check if item is selected
        #
        tableWidget = self.sender()

        if not item.isSelected():

            tableWidget.setCurrentItem(item)

        # Evaluate check state
        #
        isChecked = (item.checkState() == QtCore.Qt.CheckState.Checked)

        if isChecked:

            self.selectedReference.load()

        else:

            self.selectedReference.unload()

    @QtCore.Slot()
    def on_skinTableWidget_itemSelectionChanged(self):
        """
        Slot method for the `skinTableWidget` widget's `itemSelectionChanged` signal.

        :rtype: None
        """

        tableWidget = self.sender()
        row = tableWidget.currentRow()

        if 0 <= row < self._referenceCount:

            self._selectedRow = row
            self._selectedReference = self._referenceNodes[row].weakReference()

        else:

            self._selectedRow = None
            self._selectedReference = self.nullWeakReference

    @QtCore.Slot()
    def on_createSkinPushButton_clicked(self):
        """
        Slot method for the `createSkinPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if control rig exists
        #
        if self.controlRig is None:

            return QtWidgets.QMessageBox.warning(self, 'Create Skin', 'No control rig available to add skin to!')

        # Check if control rig has a referenced skeleton
        #
        hasReferencedSkeleton = self.controlRig.hasReferencedSkeleton()

        if not hasReferencedSkeleton:

            return QtWidgets.QMessageBox.warning(self, 'Create Skin', 'Control rig requires a referenced skeleton!')

        # Prompt user for save location
        #
        filePath, fileFilter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Create New Skin',
            self.scene.directory,
            'Maya Scenes (*.ma)'
        )

        if not stringutils.isNullOrEmpty(filePath):

            self.createSkin(filePath)
            self.invalidate()

    @QtCore.Slot()
    def on_addSkinPushButton_clicked(self):
        """
        Slot method for the `addSkinPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if control rig exists
        #
        if self.controlRig is None:

            return QtWidgets.QMessageBox.warning(self, 'Add Skin', 'No control rig available to add skin to!')

        # Check if control rig has a referenced skeleton
        #
        hasReferencedSkeleton = self.controlRig.hasReferencedSkeleton()

        if not hasReferencedSkeleton:

            return QtWidgets.QMessageBox.warning(self, 'Add Skin', 'Control rig requires a referenced skeleton!')

        # Prompt user for save location
        #
        filePath, fileFilter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Add New Skin',
            self.scene.directory,
            'Maya Scenes (*.ma)'
        )

        if not stringutils.isNullOrEmpty(filePath):

            self.addSkin(filePath)
            self.invalidate()

    @QtCore.Slot()
    def on_removeSkinPushButton_clicked(self):
        """
        Slot method for the `removeSkinPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.hasSelection():

            self.removeSkin(self._selectedRow)
            self.invalidate()

        else:

            QtWidgets.QMessageBox.warning(self, 'Remove Skin', 'No skin selected to remove!')

    @QtCore.Slot()
    def on_moveSkinUpPushButton_clicked(self):
        """
        Slot method for the `moveSkinUpPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectedReference is None:

            return

        # Check if reference can be moved
        #
        currentIndex = self._referenceNodes.index(self.selectedReference)
        previousIndex = currentIndex - 1

        if 0 <= previousIndex < self._referenceCount:

            currentReference, previousReference = self._referenceNodes[currentIndex], self._referenceNodes[previousIndex]
            self.controlRig.connectPlugs(currentReference['message'], f'skinReference[{previousIndex}]', force=True)
            self.controlRig.connectPlugs(previousReference['message'], f'skinReference[{currentIndex}]', force=True)

            self.invalidateSkins()

        else:

            log.debug(f'Unable to move {self.selectedReference} to index: {previousIndex}')

    @QtCore.Slot()
    def on_moveSkinDownPushButton_clicked(self):
        """
        Slot method for the `moveSkinDownPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectedReference is None:

            return

        # Check if reference can be moved
        #
        currentIndex = self._referenceNodes.index(self.selectedReference)
        nextIndex = currentIndex + 1

        if 0 <= nextIndex < self._referenceCount:

            currentReference, nextReference = self._referenceNodes[currentIndex], self._referenceNodes[nextIndex]
            self.controlRig.connectPlugs(currentReference['message'], f'skinReference[{nextIndex}]', force=True)
            self.controlRig.connectPlugs(nextReference['message'], f'skinReference[{currentIndex}]', force=True)

            self.invalidateSkins()

        else:

            log.debug(f'Unable to move {self.selectedReference} to index: {nextIndex}')

    @QtCore.Slot()
    def on_renameSkinPushButton_clicked(self):
        """
        Slot method for the `renameSkinPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if not self.hasSelection():

            return QtWidgets.QMessageBox.warning(self, 'Rename Skin', 'No skin selected to rename!')

        # Check if selected reference is loaded
        #
        isLoaded = self.selectedReference.isLoaded()

        if not isLoaded:

            return QtWidgets.QMessageBox.warning(self, 'Rename Skin', 'Reference must be loaded before renaming!')

        # Prompt user for new name
        #
        namespace = self.selectedReference.associatedNamespace()

        text, response = QtWidgets.QInputDialog.getText(
            self,
            'Rename Skin',
            'Enter namespace for skin:',
            text=namespace
        )

        if not response:

            return

        # Evaluate user input
        #
        safeText = stringutils.slugify(text)

        isDifferent = (namespace != safeText)
        isEmpty = stringutils.isNullOrEmpty(safeText)

        if not isEmpty and isDifferent:

            self.controlRig.renameSkin(self._selectedRow, safeText)
            self.invalidateSkins()

    @QtCore.Slot()
    def on_reloadSkinPushButton_clicked(self):
        """
        Slot method for the `reloadSkinPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.hasSelection():

            self.controlRig.refreshSkin(self._selectedRow, clearEdits=True)

        else:

            QtWidgets.QMessageBox.warning(self, 'Reload Skin', 'No skin selected to reload!')
    # endregion
