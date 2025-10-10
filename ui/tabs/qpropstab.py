import os

from dcc.python import stringutils
from dcc.generators.inclusiverange import inclusiveRange
from dcc.maya.decorators import undo
from dcc.collections import weakreflist
from dcc.ui import qsignalblocker
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from enum import IntEnum
from . import qabstracttab
from ...interfaces import referencedproprig

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


class QPropsTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with referenced props.
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
        super(QPropsTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._propComponents = weakreflist.WeakRefList()
        self._stowComponents = weakreflist.WeakRefList()
        self._referencedProps = weakreflist.WeakRefList()
        self._referencedPropCount = 0
        self._selectedRow = None
        self._selectedProp = self.nullWeakReference
        self._selectedReference = self.nullWeakReference

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QPropsTab, self).__setup_ui__(*args, **kwargs)

        # Initialize widget
        #
        self.setObjectName('propsTab')

        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('propsTabLayout')
        self.setLayout(centralLayout)

        # Initialize props group-box
        #
        self.propsLayout = QtWidgets.QGridLayout()
        self.propsLayout.setObjectName('propsLayout')

        self.propsGroupBox = QtWidgets.QGroupBox('Referenced Props:')
        self.propsGroupBox.setObjectName('propsGroupBox')
        self.propsGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.propsGroupBox.setLayout(self.propsLayout)

        self.propTableWidget =  QtWidgets.QTableWidget()
        self.propTableWidget.setObjectName('propTableWidget')
        self.propTableWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.propTableWidget.setStyleSheet('QTableWidget::item { height: 24px; }')
        self.propTableWidget.setWordWrap(False)
        self.propTableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.propTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.propTableWidget.setAlternatingRowColors(True)
        self.propTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.propTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.propTableWidget.itemChanged.connect(self.on_propTableWidget_itemChanged)
        self.propTableWidget.itemSelectionChanged.connect(self.on_propTableWidget_itemSelectionChanged)

        columnCount = len(Columns)
        columnLabels = [key.title().replace('_', ' ') for (key, value) in Columns.__members__.items()]
        self.propTableWidget.setColumnCount(columnCount)
        self.propTableWidget.setHorizontalHeaderLabels(columnLabels)

        horizontalHeader = self.propTableWidget.horizontalHeader()  # type: QtWidgets.QHeaderView
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.resizeSection(0, 200)
        horizontalHeader.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        horizontalHeader.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

        verticalHeader = self.propTableWidget.verticalHeader()  # type: QtWidgets.QHeaderView
        verticalHeader.setVisible(False)

        self.addPropPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/add.svg'), 'Add')
        self.addPropPushButton.setObjectName('addPropPushButton')
        self.addPropPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.addPropPushButton.setFixedHeight(24)
        self.addPropPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addPropPushButton.clicked.connect(self.on_addPropPushButton_clicked)

        self.removePropPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/remove.svg'), 'Remove')
        self.removePropPushButton.setObjectName('removePropPushButton')
        self.removePropPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.removePropPushButton.setFixedHeight(24)
        self.removePropPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removePropPushButton.clicked.connect(self.on_removePropPushButton_clicked)

        self.propsLayout.addWidget(self.propTableWidget, 0, 0, 1, 2)
        self.propsLayout.addWidget(self.addPropPushButton, 1, 0)
        self.propsLayout.addWidget(self.removePropPushButton, 1, 1)

        # Initialize property group-box
        #
        self.propertyLayout = QtWidgets.QGridLayout()
        self.propertyLayout.setObjectName('propertyLayout')

        self.propertyGroupBox = QtWidgets.QGroupBox('Properties:')
        self.propertyGroupBox.setObjectName('propertyGroupBox')
        self.propertyGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.propertyGroupBox.setLayout(self.propertyLayout)

        self.namespaceLabel = QtWidgets.QLabel('Namespace:')
        self.namespaceLabel.setObjectName('namespaceLabel')
        self.namespaceLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.namespaceLabel.setFixedSize(QtCore.QSize(64, 24))
        self.namespaceLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.namespaceLineEdit = QtWidgets.QLineEdit()
        self.namespaceLineEdit.setObjectName('namespaceLineEdit')
        self.namespaceLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.namespaceLineEdit.setFixedHeight(24)
        self.namespaceLineEdit.setToolTip('The namespace for the referenced nodes.')
        self.namespaceLineEdit.returnPressed.connect(self.on_lineEdit_returnPressed)
        self.namespaceLineEdit.editingFinished.connect(self.on_namespaceLineEdit_editingFinished)

        self.propLabel = QtWidgets.QLabel('Prop:')
        self.propLabel.setObjectName('propLabel')
        self.propLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.propLabel.setFixedSize(QtCore.QSize(64, 24))
        self.propLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.propComboBox = QtWidgets.QComboBox()
        self.propComboBox.setObjectName('propComboBox')
        self.propComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.propComboBox.setFixedHeight(24)
        self.propComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.propComboBox.setToolTip('The prop component to attach the referenced rig to.')
        self.propComboBox.currentIndexChanged.connect(self.on_propComboBox_currentIndexChanged)

        self.stowLabel = QtWidgets.QLabel('Stow:')
        self.stowLabel.setObjectName('stowLabel')
        self.stowLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.stowLabel.setFixedSize(QtCore.QSize(64, 24))
        self.stowLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.stowComboBox = QtWidgets.QComboBox()
        self.stowComboBox.setObjectName('stowComboBox')
        self.stowComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.stowComboBox.setFixedHeight(24)
        self.stowComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.stowComboBox.setToolTip('The stow component to attach the referenced rig to.')
        self.stowComboBox.currentIndexChanged.connect(self.on_stowComboBox_currentIndexChanged)

        self.animCurveLabel = QtWidgets.QLabel('Anim-Curve:')
        self.animCurveLabel.setObjectName('animCurveLabel')
        self.animCurveLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.animCurveLabel.setFixedSize(QtCore.QSize(64, 24))
        self.animCurveLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.animCurveLineEdit = QtWidgets.QLineEdit()
        self.animCurveLineEdit.setObjectName('animCurveLineEdit')
        self.animCurveLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.animCurveLineEdit.setFixedHeight(24)
        self.animCurveLineEdit.setToolTip('[Optional] The name for a custom attribute to bake animation onto.')
        self.animCurveLineEdit.returnPressed.connect(self.on_lineEdit_returnPressed)
        self.animCurveLineEdit.editingFinished.connect(self.on_stowLineEdit_editingFinished)

        self.propertySpacerItem = QtWidgets.QSpacerItem(24, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.updatePropPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/refresh.svg'), 'Update')
        self.updatePropPushButton.setObjectName('updatePropPushButton')
        self.updatePropPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.updatePropPushButton.setFixedHeight(24)
        self.updatePropPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.updatePropPushButton.clicked.connect(self.on_updatePropPushButton_clicked)

        self.propertyLayout.addWidget(self.namespaceLabel, 0, 0)
        self.propertyLayout.addWidget(self.namespaceLineEdit, 0, 1)
        self.propertyLayout.addWidget(self.propLabel, 1, 0)
        self.propertyLayout.addWidget(self.propComboBox, 1, 1)
        self.propertyLayout.addWidget(self.stowLabel, 2, 0)
        self.propertyLayout.addWidget(self.stowComboBox, 2, 1)
        self.propertyLayout.addWidget(self.animCurveLabel, 3, 0)
        self.propertyLayout.addWidget(self.animCurveLineEdit, 3, 1)
        self.propertyLayout.addItem(self.propertySpacerItem, 4, 0, 1, 2)
        self.propertyLayout.addWidget(self.updatePropPushButton, 5, 0, 1, 2)

        # Initialize main splitter
        #
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.mainSplitter.setObjectName('mainSplitter')
        self.mainSplitter.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.mainSplitter.addWidget(self.propsGroupBox)
        self.mainSplitter.addWidget(self.propertyGroupBox)

        centralLayout.addWidget(self.mainSplitter)
    # endregion

    # region Properties
    @property
    def selectedRow(self):
        """
        Setter method that returns the selected row.

        :rtype: int
        """

        return self._selectedRow

    @property
    def selectedProp(self):
        """
        Getter method that returns the selected prop.

        :rtype: rigotron.interfaces.referencedproprig.ReferencedPropRig
        """

        return self._selectedProp()

    @property
    def selectedReference(self):
        """
        Getter method that returns the selected prop.

        :rtype: mpy.builtins.referencemixin.ReferenceMixin
        """

        return self._selectedReference()
    # endregion

    # region Callbacks
    def activated(self):
        """
        Notifies the tab that it has been activated.

        :rtype: None
        """

        # Check if control rig exists
        #
        self._propComponents.clear()
        self._stowComponents.clear()

        if self.controlRig is None:

            return

        # Check if root component exists
        #
        rootComponent = self.controlRig.findRootComponent()

        if rootComponent is None:

            return

        # Update internal components
        #
        propComponents = rootComponent.findComponentDescendants('PropComponent')
        self._propComponents.extend(propComponents)

        stowComponents = rootComponent.findComponentDescendants('StowComponent')
        self._stowComponents.extend(stowComponents)

        # Invalidate user interface
        #
        self.invalidateReferencedProps()
    # endregion

    # region Method
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
    def addReferencedProp(self, filePath, namespace=None):
        """
        Adds a new referenced prop to the scene file.

        :type filePath: str
        :type namespace: Union[str, None]
        :rtype:
        """

        # Check if control rig exists
        #
        if self.controlRig is None:

            log.warning('Scene contains no control rig to add referenced prop to!')
            return None

        # Check if reference path is valid
        #
        expandedFilePath = os.path.expandvars(os.path.normpath(filePath))
        isMayaFile = expandedFilePath.endswith('.mb') or expandedFilePath.endswith('.ma')

        if not (os.path.isfile(expandedFilePath) and isMayaFile):

            log.warning(f'Unable to reference from invalid path: {expandedFilePath}')
            return None

        # Check if a namespace was supplied
        #
        if stringutils.isNullOrEmpty(namespace):

            filename = os.path.basename(filePath)
            namespace, extension = os.path.splitext(filename)

        # Create new referenced prop
        #
        parent = self.scene(self.controlRig.propsGroup)
        referencedPropRig = self.interfaceManager.createInterface(
            'ReferencedPropRig',
            filePath=filePath,
            namespace=namespace,
            parent=parent
        )

        self.invalidateReferencedProps()

        return referencedPropRig

    @undo.Undo(state=False)
    def removeReferencedProp(self, *args, **kwargs):
        """
        Removes the referenced prop rig at the specified index.

        :type index: int
        :rtype: None
        """

        # Evaluate argument count
        #
        numArgs = len(args)

        if numArgs != 1:

            raise TypeError(f'removeReferencedProp() expects 1 argument ({numArgs} given)!')

        # Evaluate argument type
        #
        arg = args[0]
        referencedProp = None

        if isinstance(arg, int):

            numReferencedProps = len(self._referencedProps)
            referencedProp = self._referencedProps[arg] if (0 <= arg < numReferencedProps) else None

        elif isinstance(arg, referencedproprig.ReferencedPropRig):

            referencedProp = arg

        else:

            raise TypeError(f'removeReferencedProp() expects either an int or ReferencePropRig ({type(arg).__name__} given)!')

        # Delete reference prop and invalidate
        #
        referencedProp.delete()
        self.invalidateReferencedProps()

    def invalidateReferencedProps(self, *rows, **kwargs):
        """
        Updates the referenced prop list widget.

        :type rows: Union[int, List[int]]
        :rtype: None
        """

        # Cache selected row for later use
        #
        row = self.selectedRow if self.hasSelection() else 0

        # Resize referenced props list widget
        #
        referencedProps = list(self.interfaceManager.iterInterfaces(typeName='ReferencedPropRig'))

        self._referencedProps.clear()
        self._referencedProps.extend(referencedProps)
        self._referencedPropCount = len(self._referencedProps)

        self.resizeTableWidgetItems(self.propTableWidget, self._referencedPropCount)

        # Invalidate requested rows
        #
        rows = list(range(self._referencedPropCount)) if stringutils.isNullOrEmpty(rows) else rows

        for row in rows:

            referencedProp = self._referencedProps[row]
            referenceNode = self.scene(referencedProp.referenceNode)
            referenceName, referencePath, referenceLoaded = referenceNode.name(), referenceNode.filePath(resolvedName=False), referenceNode.isLoaded()

            nameItem, filePathItem = self.propTableWidget.item(row, Columns.NAME), self.propTableWidget.item(row, Columns.FILE_PATH)

            with qsignalblocker.QSignalBlocker(self.propTableWidget):

                nameItem.setText(referenceName)
                nameItem.setCheckState(QtCore.Qt.CheckState.Checked if referenceLoaded else QtCore.Qt.CheckState.Unchecked)

                filePathItem.setText(referencePath)

        # Recreate row selection
        #
        if 0 <= row < self._referencedPropCount:

            self.propTableWidget.setCurrentCell(row, 0)

        elif self._referencedPropCount > 0:

            self.propTableWidget.setCurrentCell(0, 0)

        else:

            pass

    def invalidateProperties(self):
        """
        Updates the property widgets.

        :rtype: None
        """

        # Check if a prop is selected
        #
        if self.selectedProp is None:

            return

        # Update namespace line-edit
        #
        referenceNode = self.scene(self.selectedProp.referenceNode)
        isLoaded = referenceNode.isLoaded()

        namespace = referenceNode.associatedNamespace()

        with qsignalblocker.QSignalBlocker(self.namespaceLineEdit):

            self.namespaceLineEdit.setText(namespace)
            self.namespaceLineEdit.setReadOnly(not isLoaded)

        # Update prop widgets
        #
        with qsignalblocker.QSignalBlocker(self.propComboBox):

            propItems = [propComponent.name() for propComponent in self._propComponents]
            self.propComboBox.clear()
            self.propComboBox.addItems(propItems)

            try:

                propComponent = self.scene(self.selectedProp.propComponent)
                index = self._propComponents.index(propComponent)

                self.propComboBox.setCurrentIndex(index)

            except ValueError:

                pass

        # Update stow widgets
        #
        stowIndex = self.stowComboBox.currentIndex()

        with qsignalblocker.QSignalBlocker(self.animCurveLineEdit, self.stowComboBox):

            self.animCurveLineEdit.setText(self.selectedProp.stowName)

            stowItems = [stowComponent.name() for stowComponent in self._stowComponents]
            self.stowComboBox.clear()
            self.stowComboBox.addItems(stowItems)

            try:

                stowComponent = self.scene(self.selectedProp.stowComponent)
                index = self._stowComponents.index(stowComponent)

                self.stowComboBox.setCurrentIndex(index)

            except ValueError:

                pass
    # endregion

    # region Slots
    @QtCore.Slot(QtWidgets.QTableWidgetItem)
    def on_propTableWidget_itemChanged(self, item):
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
    def on_propTableWidget_itemSelectionChanged(self):
        """
        Slot method for the `skinTableWidget` widget's `itemSelectionChanged` signal.

        :rtype: None
        """

        tableWidget = self.sender()  # type: QtWidgets.QTableWidget
        row = tableWidget.currentRow()

        if 0 <= row < self._referencedPropCount:

            self._selectedRow = row
            self._selectedProp = self._referencedProps[row].weakReference()
            self._selectedReference = self.scene(self._referencedProps[row].referenceNode).weakReference()

        else:

            self._selectedRow = None
            self._selectedProp = self.nullWeakReference
            self._selectedReference = self.nullWeakReference

        self.invalidateProperties()

    @QtCore.Slot()
    def on_addPropPushButton_clicked(self):
        """
        Slot method for the `addPropPushButton` widget's `clicked` signal.

        :rtype: None
        """

        filePath, fileFilter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select Prop Rig',
            self.scene.directory,
            'Maya Scenes (*.mb *.ma)'
        )

        if os.path.isfile(filePath):

            self.addReferencedProp(filePath)

    @QtCore.Slot()
    def on_removePropPushButton_clicked(self):
        """
        Slot method for the `removePropPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectedProp is not None:

            self.removeReferencedProp(self.selectedProp)

    @QtCore.Slot()
    def on_namespaceLineEdit_editingFinished(self):
        """
        Slot method for the `namespaceLineEdit` widget's `editingFinished` signal.

        :rtype: None
        """

        if self.selectedProp is not None:

            lineEdit = self.sender()
            text = lineEdit.text()

            name = f'{text}_PROP'
            self.selectedProp.setName(name)
            self.invalidateReferencedProps(self.selectedRow)

            referenceNode = self.scene(self.selectedProp.referenceNode)
            referenceNode.setAssociatedNamespace(text)

    @QtCore.Slot(int)
    def on_propComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `propComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        numPropComponents = len(self._propComponents)

        if (self.selectedProp is not None) and (0 <= index < numPropComponents):

            self.selectedProp.propComponent = self._propComponents[index].object()

    @QtCore.Slot()
    def on_stowLineEdit_editingFinished(self):
        """
        Slot method for the `stowLineEdit` widget's `editingFinished` signal.

        :rtype: None
        """

        if self.selectedProp is not None:

            lineEdit = self.sender()
            text = lineEdit.text()

            self.selectedProp.stowName = text

    @QtCore.Slot(int)
    def on_stowComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `stowComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        numStowComponents = len(self._stowComponents)

        if (self.selectedProp is not None) and (0 <= index < numStowComponents):

            self.selectedProp.stowComponent = self._stowComponents[index].object()

    @QtCore.Slot()
    def on_lineEdit_returnPressed(self):
        """
        Slot method for the lineEdit's `returnPressed` signal.

        :rtype: None
        """

        lineEdit = self.sender()
        lineEdit.clearFocus()

    @QtCore.Slot()
    def on_updatePropPushButton_clicked(self):
        """
        Slot method for the `updatePropPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectedProp is not None:

            self.selectedProp.invalidate()
    # endregion
