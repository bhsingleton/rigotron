import os
import shutil

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from dcc.maya.decorators import undo
from dcc.maya.models import qplugitemmodel, qplugstyleditemdelegate, qplugitemfiltermodel
from dcc.python import stringutils
from dcc.perforce import clientutils
from dcc.ui import qdivider, qsignalblocker
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from itertools import chain
from . import qabstracttab
from ..dialogs import qinputdialog
from ..models import qcomponentitemmodel, qpropertyitemmodel
from ...libs import Status, stateutils, layerutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QRigTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with control rigs.
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
        super(QRigTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._selectedComponent = self.nullWeakReference
        self._currentStatus = 0

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigTab, self).__setup_ui__(*args, **kwargs)

        # Initialize widget
        #
        self.setObjectName('rigTab')

        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('rigTabLayout')
        self.setLayout(centralLayout)

        # Initialize main toolbar
        #
        self.mainToolBar = QtWidgets.QToolBar(parent=self)
        self.mainToolBar.setObjectName('mainToolBar')
        self.mainToolBar.setAllowedAreas(QtCore.Qt.TopToolBarArea)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setOrientation(QtCore.Qt.Horizontal)
        self.mainToolBar.setIconSize(QtCore.QSize(20, 20))
        self.mainToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.mainToolBar.setFloatable(True)

        self.addRootComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/RootComponent.svg'), 'Root', parent=self.mainToolBar)
        self.addRootComponentAction.setObjectName('addRootComponentAction')
        self.addRootComponentAction.setWhatsThis('RootComponent')
        self.addRootComponentAction.setToolTip('Adds a root to the selected component.')
        self.addRootComponentAction.triggered.connect(self.on_addRootComponentAction_triggered)

        self.addSpineComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/SpineComponent.svg'), 'Spine', parent=self.mainToolBar)
        self.addSpineComponentAction.setObjectName('addSpineComponentAction')
        self.addSpineComponentAction.setWhatsThis('SpineComponent')
        self.addSpineComponentAction.setToolTip('Adds a spine to the selected component.')
        self.addSpineComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addBeltComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/BeltComponent.svg'), 'Belt', parent=self.mainToolBar)
        self.addBeltComponentAction.setObjectName('addBeltComponentAction')
        self.addBeltComponentAction.setWhatsThis('BeltComponent')
        self.addBeltComponentAction.setToolTip('Adds a belt to the selected component.')
        self.addBeltComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addTailComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/TailComponent.svg'), 'Tail', parent=self.mainToolBar)
        self.addTailComponentAction.setObjectName('addTailComponentAction')
        self.addTailComponentAction.setWhatsThis('TailComponent')
        self.addTailComponentAction.setToolTip('Adds a tail to the selected component.')
        self.addTailComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addLegComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/LegComponent.svg'), 'Leg', parent=self.mainToolBar)
        self.addLegComponentAction.setObjectName('addLegComponentAction')
        self.addLegComponentAction.setWhatsThis('LegComponent')
        self.addLegComponentAction.setToolTip('Adds a leg to the selected component.')
        self.addLegComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addHindLegComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/LegComponent.svg'), 'Hind-Leg', parent=self.mainToolBar)
        self.addHindLegComponentAction.setObjectName('addHindLegComponentAction')
        self.addHindLegComponentAction.setWhatsThis('HindLegComponent')
        self.addHindLegComponentAction.setToolTip('Adds a hind-leg to the selected component.')
        self.addHindLegComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addFootComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/FootComponent.svg'), 'Foot', parent=self.mainToolBar)
        self.addFootComponentAction.setObjectName('addFootComponentAction')
        self.addFootComponentAction.setWhatsThis('FootComponent')
        self.addFootComponentAction.setToolTip('Adds a foot to the selected component.')
        self.addFootComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addClavicleComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/ClavicleComponent.svg'), 'Clavicle', parent=self.mainToolBar)
        self.addClavicleComponentAction.setObjectName('addClavicleComponentAction')
        self.addClavicleComponentAction.setWhatsThis('ClavicleComponent')
        self.addClavicleComponentAction.setToolTip('Adds a clavicle to the selected component.')
        self.addClavicleComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addArmComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/ArmComponent.svg'), 'Arm', parent=self.mainToolBar)
        self.addArmComponentAction.setObjectName('addArmComponentAction')
        self.addArmComponentAction.setWhatsThis('ArmComponent')
        self.addArmComponentAction.setToolTip('Adds an arm to the selected component.')
        self.addArmComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addHandComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/HandComponent.svg'), 'Hand', parent=self.mainToolBar)
        self.addHandComponentAction.setObjectName('addHandComponentAction')
        self.addHandComponentAction.setWhatsThis('HandComponent')
        self.addHandComponentAction.setToolTip('Adds a hand to the selected component.')
        self.addHandComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addHeadComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/HeadComponent.svg'), 'Head', parent=self.mainToolBar)
        self.addHeadComponentAction.setObjectName('addHeadComponentAction')
        self.addHeadComponentAction.setWhatsThis('HeadComponent')
        self.addHeadComponentAction.setToolTip('Adds a head to the selected component.')
        self.addHeadComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addInsectLegComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/InsectLegComponent.svg'), 'Insect\nLeg', parent=self.mainToolBar)
        self.addInsectLegComponentAction.setObjectName('addInsectLegComponentAction')
        self.addInsectLegComponentAction.setWhatsThis('InsectLegComponent')
        self.addInsectLegComponentAction.setToolTip('Adds an insect-leg to the selected component.')
        self.addInsectLegComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addInsectFootComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/InsectFootComponent.svg'), 'Insect\nFoot', parent=self.mainToolBar)
        self.addInsectFootComponentAction.setObjectName('addInsectFootComponentAction')
        self.addInsectFootComponentAction.setWhatsThis('InsectFootComponent')
        self.addInsectFootComponentAction.setToolTip('Adds an insect-foot to the selected component.')
        self.addInsectFootComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addFaceComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/FaceComponent.svg'), 'Face', parent=self.mainToolBar)
        self.addFaceComponentAction.setObjectName('addFaceComponentAction')
        self.addFaceComponentAction.setWhatsThis('FaceComponent')
        self.addFaceComponentAction.setToolTip('Adds a face to the selected component.')
        self.addFaceComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addCollarComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/CollarComponent.svg'), 'Collar', parent=self.mainToolBar)
        self.addCollarComponentAction.setObjectName('addCollarComponentAction')
        self.addCollarComponentAction.setWhatsThis('CollarComponent')
        self.addCollarComponentAction.setToolTip('Adds a collar to the selected component.')
        self.addCollarComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addPropComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/PropComponent.svg'), 'Prop', parent=self.mainToolBar)
        self.addPropComponentAction.setObjectName('addPropComponentAction')
        self.addPropComponentAction.setWhatsThis('PropComponent')
        self.addPropComponentAction.setToolTip('Adds a prop to the selected component.')
        self.addPropComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addWeaponComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/WeaponComponent.svg'), 'Weapon', parent=self.mainToolBar)
        self.addWeaponComponentAction.setObjectName('addWeaponComponentAction')
        self.addWeaponComponentAction.setWhatsThis('WeaponComponent')
        self.addWeaponComponentAction.setToolTip('Adds a weapon to the selected component.')
        self.addWeaponComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addStowComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/StowComponent.svg'), 'Stow', parent=self.mainToolBar)
        self.addStowComponentAction.setObjectName('addStowComponentAction')
        self.addStowComponentAction.setWhatsThis('StowComponent')
        self.addStowComponentAction.setToolTip('Adds a stow to the selected component.')
        self.addStowComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addLeafComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/LeafComponent.svg'), 'Leaf', parent=self.mainToolBar)
        self.addLeafComponentAction.setObjectName('addLeafComponentAction')
        self.addLeafComponentAction.setWhatsThis('LeafComponent')
        self.addLeafComponentAction.setToolTip('Adds a leaf to the selected component.')
        self.addLeafComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addDynamicPivotComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/DynamicPivotComponent.svg'), 'Pivot', parent=self.mainToolBar)
        self.addDynamicPivotComponentAction.setObjectName('addDynamicPivotComponentAction')
        self.addDynamicPivotComponentAction.setWhatsThis('DynamicPivotComponent')
        self.addDynamicPivotComponentAction.setToolTip('Adds a dynamic-pivot to the selected component.')
        self.addDynamicPivotComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addChainComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/ChainComponent.svg'), 'Chain', parent=self.mainToolBar)
        self.addChainComponentAction.setObjectName('addChainComponentAction')
        self.addChainComponentAction.setWhatsThis('ChainComponent')
        self.addChainComponentAction.setToolTip('Adds a chain to the selected component.')
        self.addChainComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addPlayerAlignComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/PlayerAlignComponent.svg'), 'Align', parent=self.mainToolBar)
        self.addPlayerAlignComponentAction.setObjectName('addPlayerAlignComponentAction')
        self.addPlayerAlignComponentAction.setWhatsThis('PlayerAlignComponent')
        self.addPlayerAlignComponentAction.setToolTip('Adds player alignment to the selected component.')
        self.addPlayerAlignComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addPlayerIKComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/PlayerIKComponent.svg'), 'IK', parent=self.mainToolBar)
        self.addPlayerIKComponentAction.setObjectName('addPlayerIKComponentAction')
        self.addPlayerIKComponentAction.setWhatsThis('PlayerIKComponent')
        self.addPlayerIKComponentAction.setToolTip('Adds player IK to the selected component.')
        self.addPlayerIKComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.mainToolBar.addAction(self.addRootComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addSpineComponentAction)
        self.mainToolBar.addAction(self.addBeltComponentAction)
        self.mainToolBar.addAction(self.addTailComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addLegComponentAction)
        self.mainToolBar.addAction(self.addHindLegComponentAction)
        self.mainToolBar.addAction(self.addFootComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addInsectLegComponentAction)
        self.mainToolBar.addAction(self.addInsectFootComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addClavicleComponentAction)
        self.mainToolBar.addAction(self.addArmComponentAction)
        self.mainToolBar.addAction(self.addHandComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addHeadComponentAction)
        self.mainToolBar.addAction(self.addFaceComponentAction)
        self.mainToolBar.addAction(self.addCollarComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addPropComponentAction)
        self.mainToolBar.addAction(self.addWeaponComponentAction)
        self.mainToolBar.addAction(self.addStowComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addLeafComponentAction)
        self.mainToolBar.addAction(self.addDynamicPivotComponentAction)
        self.mainToolBar.addAction(self.addChainComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addPlayerAlignComponentAction)
        self.mainToolBar.addAction(self.addPlayerIKComponentAction)

        centralLayout.addWidget(self.mainToolBar)

        # Initialize outliner widget
        #
        self.outlinerLayout = QtWidgets.QVBoxLayout()
        self.outlinerLayout.setObjectName('outlinerLayout')

        self.outlinerGroupBox = QtWidgets.QGroupBox('Outliner:')
        self.outlinerGroupBox.setObjectName('outlinerGroupBox')
        self.outlinerGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.outlinerGroupBox.setLayout(self.outlinerLayout)

        self.nameLabel = QtWidgets.QLabel('Rig:')
        self.nameLabel.setObjectName('nameLabel')
        self.nameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.nameLabel.setFixedSize(QtCore.QSize(40, 24))
        self.nameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.nameLineEdit = QtWidgets.QLineEdit()
        self.nameLineEdit.setObjectName('nameLineEdit')
        self.nameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nameLineEdit.setFixedHeight(24)
        self.nameLineEdit.setReadOnly(True)

        self.newPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/new_file.svg'), '')
        self.newPushButton.setObjectName('renamePushButton')
        self.newPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.newPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.newPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.newPushButton.setToolTip('Creates a new control rig.')
        self.newPushButton.clicked.connect(self.on_newPushButton_clicked)

        self.renamePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/rename.svg'), '')
        self.renamePushButton.setObjectName('renamePushButton')
        self.renamePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.renamePushButton.setFixedSize(QtCore.QSize(24, 24))
        self.renamePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.renamePushButton.setToolTip('Renames the current control rig.')
        self.renamePushButton.clicked.connect(self.on_renamePushButton_clicked)

        self.updatePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/rigidBind.png'), '')
        self.updatePushButton.setObjectName('updatePushButton')
        self.updatePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.updatePushButton.setFixedSize(QtCore.QSize(24, 24))
        self.updatePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.updatePushButton.setToolTip("Updates any legacy rigs that are no longer compatible with Rig o'Tron.")
        self.updatePushButton.clicked.connect(self.on_updatePushButton_clicked)

        self.referencePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/reference.svg'), '')
        self.referencePushButton.setObjectName('referencePushButton')
        self.referencePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.referencePushButton.setFixedSize(QtCore.QSize(24, 24))
        self.referencePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.referencePushButton.setToolTip('Converts the control rig to a referenced skeleton.')
        self.referencePushButton.clicked.connect(self.on_referencePushButton_clicked)

        self.nameLayout = QtWidgets.QHBoxLayout()
        self.nameLayout.setObjectName('nameLayout')
        self.nameLayout.setContentsMargins(0, 0, 0, 0)
        self.nameLayout.addWidget(self.nameLabel)
        self.nameLayout.addWidget(self.nameLineEdit)
        self.nameLayout.addWidget(self.newPushButton)
        self.nameLayout.addWidget(self.renamePushButton)
        self.nameLayout.addWidget(self.updatePushButton)
        self.nameLayout.addWidget(self.referencePushButton)

        self.outlinerTreeView = QtWidgets.QTreeView()
        self.outlinerTreeView.setObjectName('outlinerTreeView')
        self.outlinerTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.outlinerTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.outlinerTreeView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.outlinerTreeView.setDragEnabled(True)
        self.outlinerTreeView.setDragDropOverwriteMode(False)
        self.outlinerTreeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.outlinerTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.outlinerTreeView.setAlternatingRowColors(True)
        self.outlinerTreeView.setRootIsDecorated(True)
        self.outlinerTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.outlinerTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.outlinerTreeView.setUniformRowHeights(True)
        self.outlinerTreeView.clicked.connect(self.on_outlinerTreeView_clicked)

        self.outlinerHeader = self.outlinerTreeView.header()
        self.outlinerHeader.setDefaultSectionSize(200)
        self.outlinerHeader.setMinimumSectionSize(50)
        self.outlinerHeader.setStretchLastSection(True)

        self.outlinerModel = qcomponentitemmodel.QComponentItemModel(parent=self.outlinerTreeView)
        self.outlinerModel.setObjectName('outlinerModel')

        self.outlinerTreeView.setModel(self.outlinerModel)

        self.deleteShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('delete'), self.outlinerTreeView, self.on_outlinerTreeView_deleteKeyPressed)

        self.attachmentLabel = QtWidgets.QLabel('Parent:')
        self.attachmentLabel.setObjectName('attachmentLabel')
        self.attachmentLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.attachmentLabel.setFixedSize(QtCore.QSize(40, 24))
        self.attachmentLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.attachmentComboBox = QtWidgets.QComboBox()
        self.attachmentComboBox.setObjectName('attachmentComboBox')
        self.attachmentComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.attachmentComboBox.setFixedHeight(24)
        self.attachmentComboBox.currentIndexChanged.connect(self.on_attachmentComboBox_currentIndexChanged)

        self.attachmentLayout = QtWidgets.QHBoxLayout()
        self.attachmentLayout.setObjectName('attachmentLayout')
        self.attachmentLayout.setContentsMargins(0, 0, 0, 0)
        self.attachmentLayout.addWidget(self.attachmentLabel)
        self.attachmentLayout.addWidget(self.attachmentComboBox)

        self.outlinerLayout.addLayout(self.nameLayout)
        self.outlinerLayout.addWidget(self.outlinerTreeView)
        self.outlinerLayout.addLayout(self.attachmentLayout)

        # Initialize property widget
        #
        self.propertyLayout = QtWidgets.QVBoxLayout()
        self.propertyLayout.setObjectName('propertyLayout')

        self.propertyGroupBox = QtWidgets.QGroupBox('Properties:')
        self.propertyGroupBox.setObjectName('propertyGroupBox')
        self.propertyGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.propertyGroupBox.setLayout(self.propertyLayout)

        self.filterPropertyLineEdit = QtWidgets.QLineEdit()
        self.filterPropertyLineEdit.setObjectName('filterPropertyLineEdit')
        self.filterPropertyLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.filterPropertyLineEdit.setFixedHeight(24)
        self.filterPropertyLineEdit.setPlaceholderText('Filter Properties...')

        self.propertyTreeView = QtWidgets.QTreeView()
        self.propertyTreeView.setObjectName('propertyTreeView')
        self.propertyTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.propertyTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.propertyTreeView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.propertyTreeView.setDragEnabled(False)
        self.propertyTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.propertyTreeView.setAlternatingRowColors(True)
        self.propertyTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.propertyTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.propertyTreeView.setUniformRowHeights(True)

        self.propertyHeader = self.propertyTreeView.header()
        self.propertyHeader.setDefaultSectionSize(200)
        self.propertyHeader.setMinimumSectionSize(50)
        self.propertyHeader.setStretchLastSection(True)

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

        self.propertyLayout.addWidget(self.filterPropertyLineEdit)
        self.propertyLayout.addWidget(self.propertyTreeView)

        # Initialize main splitter
        #
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.mainSplitter.setObjectName('mainSplitter')
        self.mainSplitter.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.mainSplitter.addWidget(self.outlinerGroupBox)
        self.mainSplitter.addWidget(self.propertyGroupBox)

        centralLayout.addWidget(self.mainSplitter)

        # Initialize edit group-box
        #
        self.editLayout = QtWidgets.QVBoxLayout()
        self.editLayout.setObjectName('editLayout')

        self.editGroupBox = QtWidgets.QGroupBox('Edit:')
        self.editGroupBox.setObjectName('editGroupBox')
        self.editGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.editGroupBox.setLayout(self.editLayout)

        self.alignPushButton = QtWidgets.QPushButton('Align Joints')
        self.alignPushButton.setObjectName('alignPushButton')
        self.alignPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.alignPushButton.setFixedHeight(24)
        self.alignPushButton.clicked.connect(self.on_alignPushButton_clicked)

        self.mirrorPushButton = QtWidgets.QPushButton('Mirror Joint(s)')
        self.mirrorPushButton.setObjectName('mirrorPushButton')
        self.mirrorPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.mirrorPushButton.setFixedHeight(24)
        self.mirrorPushButton.clicked.connect(self.on_mirrorPushButton_clicked)

        self.sanitizePushButton = QtWidgets.QPushButton('Sanitize Joint(s)')
        self.sanitizePushButton.setObjectName('sanitizePushButton')
        self.sanitizePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.sanitizePushButton.setFixedHeight(24)
        self.sanitizePushButton.clicked.connect(self.on_sanitizePushButton_clicked)

        self.organizePushButton = QtWidgets.QPushButton('Organize Layers')
        self.organizePushButton.setObjectName('organizePushButton')
        self.organizePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.organizePushButton.setFixedHeight(24)
        self.organizePushButton.clicked.connect(self.on_organizePushButton_clicked)

        self.detectPushButton = QtWidgets.QPushButton('Detect Mirroring')
        self.detectPushButton.setObjectName('alignPushButton')
        self.detectPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.detectPushButton.setFixedHeight(24)
        self.detectPushButton.clicked.connect(self.on_detectPushButton_clicked)

        self.blackBoxPushButton = QtWidgets.QPushButton('Black-Box')
        self.blackBoxPushButton.setObjectName('blackBoxPushButton')
        self.blackBoxPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.blackBoxPushButton.setFixedHeight(24)
        self.blackBoxPushButton.clicked.connect(self.on_blackBoxPushButton_clicked)

        self.buttonsLayout = QtWidgets.QGridLayout()
        self.buttonsLayout.setObjectName('buttonsLayout')
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.addWidget(self.alignPushButton, 0, 0)
        self.buttonsLayout.addWidget(self.mirrorPushButton, 0, 1)
        self.buttonsLayout.addWidget(self.sanitizePushButton, 0, 2)
        self.buttonsLayout.addWidget(self.organizePushButton, 1, 0)
        self.buttonsLayout.addWidget(self.detectPushButton, 1, 1)
        self.buttonsLayout.addWidget(self.blackBoxPushButton, 1, 2)

        self.editLayout.addLayout(self.buttonsLayout)

        # Initialize status layout
        #
        self.statusLabel = QtWidgets.QLabel('Status:')
        self.statusLabel.setObjectName('statusLabel')
        self.statusLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        self.statusLine = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.statusLine.setObjectName('statusLine')
        self.statusLine.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        self.statusDividerLayout = QtWidgets.QHBoxLayout()
        self.statusDividerLayout.setObjectName('statusDividerLayout')
        self.statusDividerLayout.setContentsMargins(0, 0, 0, 0)
        self.statusDividerLayout.addWidget(self.statusLabel)
        self.statusDividerLayout.addWidget(self.statusLine)

        self.metaStatusPushButton = QtWidgets.QPushButton('Meta')
        self.metaStatusPushButton.setObjectName('metaStatusPushButton')
        self.metaStatusPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.metaStatusPushButton.setFixedHeight(24)
        self.metaStatusPushButton.setStyleSheet('QPushButton:hover:checked { background-color: green; }\nQPushButton:checked { background-color: darkgreen; border: none; }')
        self.metaStatusPushButton.setCheckable(True)
        self.metaStatusPushButton.setChecked(True)

        self.skeletonStatusPushButton = QtWidgets.QPushButton('Skeleton')
        self.skeletonStatusPushButton.setObjectName('skeletonStatusPushButton')
        self.skeletonStatusPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.skeletonStatusPushButton.setFixedHeight(24)
        self.skeletonStatusPushButton.setStyleSheet('QPushButton:hover:checked { background-color: green; }\nQPushButton:checked { background-color: darkgreen; border: none; }')
        self.skeletonStatusPushButton.setCheckable(True)
        self.skeletonStatusPushButton.setChecked(True)

        self.rigStatusPushButton = QtWidgets.QPushButton('Rig')
        self.rigStatusPushButton.setObjectName('rigStatusPushButton')
        self.rigStatusPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rigStatusPushButton.setFixedHeight(24)
        self.rigStatusPushButton.setStyleSheet('QPushButton:hover:checked { background-color: green; }\nQPushButton:checked { background-color: darkgreen; border: none; }')
        self.rigStatusPushButton.setCheckable(True)
        self.rigStatusPushButton.setChecked(True)

        self.statusButtonGroup = QtWidgets.QButtonGroup(self.editGroupBox)
        self.statusButtonGroup.setExclusive(True)
        self.statusButtonGroup.addButton(self.metaStatusPushButton, id=0)
        self.statusButtonGroup.addButton(self.skeletonStatusPushButton, id=1)
        self.statusButtonGroup.addButton(self.rigStatusPushButton, id=2)
        self.statusButtonGroup.idClicked.connect(self.on_statusButtonGroup_idClicked)

        self.statusButtonLayout = QtWidgets.QGridLayout()
        self.statusButtonLayout.setObjectName('statusButtonLayout')
        self.statusButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.statusButtonLayout.addWidget(self.metaStatusPushButton, 1, 0)
        self.statusButtonLayout.addWidget(self.skeletonStatusPushButton, 1, 1)
        self.statusButtonLayout.addWidget(self.rigStatusPushButton, 1, 2)

        self.editLayout.addLayout(self.statusDividerLayout)
        self.editLayout.addLayout(self.statusButtonLayout)

        centralLayout.addWidget(self.editGroupBox)
    # endregion

    # region Properties
    @property
    def selectedComponent(self):
        """
        Getter method that returns the current component.

        :rtype: rigotron.components.basecomponent.BaseComponent
        """

        return self._selectedComponent()
    # endregion

    # region Methods
    def cacheSkins(self):
        """
        Caches the influences from any active skin clusters.

        :rtype: None
        """

        for mesh in self.scene.iterNodesByApiType(om.MFn.kMesh):

            skinClusters = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)
            numSkinClusters = len(skinClusters)

            if not (numSkinClusters == 1):

                continue

            skinCluster = skinClusters[0]
            skinCluster.cacheInfluences()

    def updateSkins(self):
        """
        Repairs any broken influences from inactive skin clusters.

        :rtype: None
        """

        for mesh in self.scene.iterNodesByApiType(om.MFn.kMesh):

            skinClusters = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)
            numSkinClusters = len(skinClusters)

            if not (numSkinClusters == 1):

                continue

            skinCluster = skinClusters[0]
            skinCluster.repairInfluences()

    def cacheShapes(self):
        """
        Caches the shapes from the current control rig.

        :rtype: None
        """

        # Check if selected component is valid
        #
        if self.selectedComponent is None:

            return

        # Iterate through components
        #
        for component in self.selectedComponent.walkComponents(includeSelf=True):

            component.cacheShapes()

    def updateShapes(self):
        """
        Updates the shapes on current control rig.

        :rtype: None
        """

        # Check if selected component is valid
        #
        if self.selectedComponent is None:

            return

        # Iterate through components
        #
        for component in self.selectedComponent.walkComponents(includeSelf=True):

            component.repairShapes()

    def untitledScenePath(self):
        """
        Returns the untitled scene path to copy from for new rigs.

        :rtype: str
        """

        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scenes', 'untitled.ma'))

    def guessReferencePath(self, create=False):
        """
        Attempts to guess the location for a new referenced skeleton.

        :type create: bool
        :rtype: str
        """

        # Concatenate reference path
        #
        untitledScenePath = self.untitledScenePath()
        referenceName = self.scene.filename.replace('RIG', 'SKL').replace('AnimRig', 'ExportRig')
        referencePath = os.path.join(self.scene.directory, referenceName)

        if self.scene.filePath != referencePath and create:

            log.info(f'Creating new export skeleton @ {referencePath}')
            shutil.copyfile(untitledScenePath, referencePath)

        # Check if reference path can be simplified
        #
        client = clientutils.getCurrentClient()
        clientExists = client is not None

        isRelativeToClient = client.hasAbsoluteFile(referencePath) if clientExists else False

        if isRelativeToClient:

            relativePath = client.mapToRoot(referencePath)
            referencePath = os.path.join('$P4ROOT', relativePath)

        return referencePath

    @undo.Undo(state=False)
    def createControlRig(self, name, referenced=False):
        """
        Creates a new control-rig with the specified name.
        TODO: Find a better way for users to specify the reference path!

        :type name: str
        :type referenced: bool
        :rtype: controlrig.ControlRig
        """

        # Check if referenced skeleton is required
        #
        referencePath = ''

        if referenced:

            referencePath = self.guessReferencePath(create=True)

        # Return new control rig
        #
        return self.interfaceManager.createControlRig(name, referencePath=referencePath)

    @undo.Undo(state=False)
    def addComponent(self, typeName, componentParent=None, componentSide=None, componentId=None):
        """
        Adds a component, of the specified typename, to the current control-rig.

        :type typeName: str
        :type componentParent: abstractcomponent.AbstractComponent
        :type componentSide: Side
        :type componentId: str
        :rtype: Union[abstractcomponent.AbstractComponent, None]
        """

        # Redundancy check
        #
        if self.controlRig is None:

            log.warning(f'No valid control rig found!')
            return

        # Check if a parent was supplied
        #
        if componentParent is None:

            componentParent = self.selectedComponent

        # Check if a side was supplied
        #
        if componentSide is None:

            componentSide = componentParent.componentSide

        # Check if an ID was supplied
        #
        if componentId is None:

            componentId = componentParent.componentId

        # Get class constructor
        #
        Component = self.componentManager.getClass(typeName)

        if callable(Component):

            log.debug(f'Adding "{typeName}" to {componentParent}!')
            component = Component.create(
                componentSide=componentSide,
                componentId=componentId,
                parent=self.controlRig.componentsGroup
            )

            parentIndex = self.outlinerModel.indexFromComponent(componentParent)
            self.outlinerModel.appendRow(component, parent=parentIndex)

            return component

        else:

            log.warning(f'Unable to locate "{typeName}" constructor!')
            return None

    def clear(self):
        """
        Resets the user interface.

        :rtype: None
        """

        # Reset internal trackers
        #
        self._selectedComponent = self.nullWeakReference

        self.nameLineEdit.setText('')
        self.outlinerModel.rootComponent = None

        # Update component status
        #
        self.invalidateProperties()
        self.invalidateAttachments()
        self.invalidateStatus()

    def invalidate(self):
        """
        Updates all control-rig related widgets.

        :rtype: None
        """

        # Update user interface
        #
        if self.controlRig is not None:

            self.nameLineEdit.setText(self.controlRig.rigName)
            self.outlinerModel.rootComponent = self.scene(self.controlRig.rootComponent)

        elif self.legacyRig is not None:

            self.nameLineEdit.setText(self.legacyRig.rigName)

        else:

            pass

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
        if self.selectedComponent is None:

            self.propertyModel.invisibleRootItem = None
            return

        # Check if current component still exists
        #
        if self.selectedComponent.isAlive():

            self.propertyModel.invisibleRootItem = self.selectedComponent.object()
            self.propertyModel.readOnly = Status(self.selectedComponent.componentStatus) != Status.META

        else:

            self.propertyModel.invisibleRootItem = None

    def invalidateAttachments(self):
        """
        Updates the attachment drop-down menu.

        :rtype: None
        """

        # Check if current component is valid
        #
        if self.selectedComponent is not None:

            skeletonSpecs = self.selectedComponent.getAttachmentOptions()
            jointNames = [skeletonSpec.name for skeletonSpec in skeletonSpecs]

            with qsignalblocker.QSignalBlocker(self.attachmentComboBox):

                self.attachmentComboBox.clear()
                self.attachmentComboBox.addItems(jointNames)
                self.attachmentComboBox.setCurrentIndex(self.selectedComponent.attachmentId)

        else:

            with qsignalblocker.QSignalBlocker(self.attachmentComboBox):

                self.attachmentComboBox.clear()

    def invalidateStatus(self):
        """
        Updates the status buttons.

        :rtype: None
        """

        self._currentStatus = Status(self.selectedComponent.componentStatus) if (self.selectedComponent is not None) else Status.META

        with qsignalblocker.QSignalBlocker(self.statusButtonGroup):

            buttons = self.statusButtonGroup.buttons()
            buttons[self._currentStatus].setChecked(True)

    @undo.Undo(name='Align Nodes')
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

    @undo.Undo(name='Mirror Nodes')
    def mirrorNodes(self, *nodes):
        """
        Mirrors the transforms on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Evaluate node type
            #
            isTransform = node.hasFn(om.MFn.kTransform)

            if not isTransform:

                continue

            # Evaluate opposite node
            #
            oppositeNode = node.getOppositeNode()
            requiresMirroring = node is not oppositeNode and oppositeNode is not None

            if not requiresMirroring:

                continue

            # Evaluate pre-rotations
            #
            preEulerRotation = node.preEulerRotation()  # type: om.MEulerRotation
            hasPreEulerRotations = not preEulerRotation.isEquivalent(om.MEulerRotation.kIdentity, tolerance=1e-3)

            if hasPreEulerRotations:

                node.unfreezePivots()
                oppositeNode.unfreezePivots()

            # Evaluate offset parent matrix
            #
            offsetParentMatrix = node.offsetParentMatrix()
            hasOffset = not offsetParentMatrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3)

            if hasOffset:

                node.unfreezeTransform()
                oppositeNode.unfreezeTransform()

            # Evaluate joint's parent space
            # This will impact which attributes get inverted!
            #
            parent = node.parent()
            parentMatrix = parent.worldMatrix() if (parent is not None) else om.MMatrix.kIdentity
            isIdentityMatrix = parentMatrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3)

            if isIdentityMatrix:

                matrix = node.matrix()
                xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)

                mirrorXAxis = transformutils.mirrorVector(xAxis)
                mirrorYAxis = transformutils.mirrorVector(yAxis)
                mirrorZAxis = -transformutils.mirrorVector(zAxis)
                mirrorPos = om.MPoint(-pos.x, pos.y, pos.z, pos.w)
                mirrorMatrix = transformutils.makeMatrix(mirrorXAxis, mirrorYAxis, mirrorZAxis, mirrorPos)

                oppositeNode = node.getOppositeNode()
                oppositeNode.setMatrix(mirrorMatrix, skipScale=True)

            else:  # World space

                node.mirrorAttr(node['translateX'], inverse=False)
                node.mirrorAttr(node['translateY'], inverse=False)
                node.mirrorAttr(node['translateZ'], inverse=True)

                node.mirrorAttr(node['rotateX'], inverse=True)
                node.mirrorAttr(node['rotateY'], inverse=True)
                node.mirrorAttr(node['rotateZ'], inverse=False)

            # Evaluate shapes
            #
            nurbsCurves = node.shapes(apiType=om.MFn.kNurbsCurve)
            hasNurbsCurves = len(nurbsCurves) > 0

            if hasNurbsCurves:

                nurbsCurve = nurbsCurves[0]
                controlPoints = nurbsCurve.controlPoints()
                mirroredControlPoints = [om.MPoint(point.x, point.y, -point.z) for point in controlPoints]

                oppositeNurbsCurve = oppositeNode.shape()
                oppositeNurbsCurve.setControlPoints(mirroredControlPoints)

    @undo.Undo(name='Sanitize Joints')
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
    @QtCore.Slot()
    def on_newPushButton_clicked(self):
        """
        Slot method for the `newPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if file has been saved
        #
        if self.scene.isNew():

            return QtWidgets.QMessageBox.warning(self, 'Create New Rig', 'Please save the scene before continuing!')

        # Check if control rig exists
        #
        if self.controlRig is not None:

            return QtWidgets.QMessageBox.warning(self, 'Create New Rig', 'Control rig already exists!')

        # Prompt user for name input
        #
        text, referenced, success = qinputdialog.QInputDialog.getText(
            self,
            'Create New Rig',
            'Enter name:',
            QtWidgets.QLineEdit.Normal
        )

        if success and not stringutils.isNullOrEmpty(text):

            self.createControlRig(text, referenced=referenced)
            self.window().invalidate()

        else:

            log.info('Operation aborted...')

    @QtCore.Slot()
    def on_renamePushButton_clicked(self):
        """
        Slot method for the `renamePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if control-rig exists
        #
        if self.controlRig is None:

            QtWidgets.QMessageBox.warning(self, 'Rename Rig', 'No rig exists to rename!')
            return

        # Prompt user
        #
        newName, response = QtWidgets.QInputDialog.getText(
            self,
            'Change Rig Name',
            'Enter Name:',
            text=self.controlRig.rigName
        )

        if not response:

            log.info('Operation aborted...')
            return

        # Check if name is unique
        # Be sure to slugify the name before processing!
        #
        newName = stringutils.slugify(newName)
        isValid = not stringutils.isNullOrEmpty(newName)

        if isValid:

            self.controlRig.rigName = newName
            self.nameLineEdit.setText(newName)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot()
    def on_updatePushButton_clicked(self):
        """
        Slot method for the `updatePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if legacy rig exists
        #
        if self.legacyRig is None:

            return QtWidgets.QMessageBox.information(self, 'Update Control Rig', 'Scene contains no outdated control rigs!')

        # Check if legacy rig is in the skeleton or rig state
        #
        rigStatus = self.legacyRig.getRigStatus()

        if rigStatus != self.legacyRig.Status.RIG:

            return QtWidgets.QMessageBox.warning(self, 'Update Control Rig', 'Rig can only be updated from the rig state!')

        # Prompt user input
        #
        response = QtWidgets.QMessageBox.question(
            self,
            'Update Control Rig',
            'Would you like to update this control rig?',
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )

        if response != QtWidgets.QMessageBox.Yes:

            return

        # Try and update rig
        #
        success = self.legacyRig.update(force=True)

        if success:

            return self.window().invalidate()

        else:

            return QtWidgets.QMessageBox.warning(self, 'Update Control Rig', 'Unable to update control rig.\nDo not save changes to the scene file!')

    @QtCore.Slot()
    def on_referencePushButton_clicked(self):
        """
        Slot method for the `referencePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if control rig exists
        #
        if self.controlRig is None:

            return QtWidgets.QMessageBox.warning(self, 'Convert Control Rig', 'Scene contains no control rigs to convert!')

        # Check if control rig is in the meta state
        #
        rigStatus = self.controlRig.getRigStatus()

        if rigStatus != self.controlRig.Status.META:

            return QtWidgets.QMessageBox.warning(self, 'Convert Control Rig', 'Rig can only be converted from the meta state!')

        # Prompt user input
        #
        response = QtWidgets.QMessageBox.question(
            self,
            'Convert Control Rig',
            'Would you like to convert this control rig to a referenced skeleton?',
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )

        if response != QtWidgets.QMessageBox.Yes:

            return

        # Try and update rig
        #
        referencePath = self.guessReferencePath(create=True)
        success = self.controlRig.convertToReferencedSkeleton(referencePath)

        if success:

            self.invalidate()

        else:

            QtWidgets.QMessageBox.warning(self, 'Convert Control Rig', 'Unable to convert control rig.\nDo not save changes to the scene file!')

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

            self._selectedComponent = component.weakReference()

        else:

            self._selectedComponent = self.nullWeakReference

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

        for index in reversed(selectedIndices):

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

        # Update current component
        #
        selectionModel = self.outlinerTreeView.selectionModel()
        selectedIndexes = selectionModel.selectedIndexes()

        numSelectedIndexes = len(selectedIndexes)

        if numSelectedIndexes > 0:

            selectedIndex = selectedIndexes[0]
            component = self.outlinerModel.componentFromIndex(selectedIndex)

            self._selectedComponent = component.weakReference()

        else:

            self._selectedComponent = self.nullWeakReference

        # Update property model
        #
        self.invalidateProperties()

    @QtCore.Slot(int)
    def on_attachmentComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `attachmentComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        if self.selectedComponent is not None:

            self.selectedComponent.attachmentId = index

    @QtCore.Slot()
    def on_addRootComponentAction_triggered(self):
        """
        Slot method for the `addRootComponentAction` widget's `triggered` signal.

        :rtype: None
        """

        # Check if file has been saved
        #
        if self.scene.isNew():

            return QtWidgets.QMessageBox.warning(self, 'Create New Rig', 'Please save the scene before continuing!')

        # Check if control rig exists
        #
        if self.controlRig is not None:

            return QtWidgets.QMessageBox.warning(self, 'Create New Rig', 'Control rig already exists!')

        # Prompt user for name input
        #
        text, referenced, success = qinputdialog.QInputDialog.getText(
            self,
            'Create New Rig',
            'Enter name:',
            QtWidgets.QLineEdit.Normal
        )

        if success and not stringutils.isNullOrEmpty(text):

            self.createControlRig(text, referenced=referenced)
            self.window().invalidate()

        else:

            log.info('Operation aborted...')

    @QtCore.Slot()
    def on_addComponentAction_triggered(self):
        """
        Slot method for the `addComponentAction` widget's `triggered` signal.

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

        nodes = list(self.scene.iterSelection(apiType=om.MFn.kTransform))
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ShiftModifier:

            nodes = list(chain(*[node.descendants(apiType=om.MFn.kTransform, includeSelf=True) for node in nodes]))

        self.mirrorNodes(*nodes)

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

        for component in self.controlRig.walkComponents():

            for node in component.publishedNodes():

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
        if self.selectedComponent is None:

            log.warning('No component selected to update!')
            self.invalidateStatus()

        # Check if skins require caching
        #
        status = Status(index)
        currentStatus = Status(self.selectedComponent.componentStatus)

        skeletonToMeta = currentStatus == Status.SKELETON and status == Status.META

        if skeletonToMeta:

            self.cacheSkins()

        # Check if shapes require caching
        #
        rigToSkeleton = currentStatus == Status.RIG and status == Status.SKELETON

        if rigToSkeleton:

            self.cacheShapes()

        # Update rig state
        #
        success = stateutils.changeState(self.selectedComponent, status)

        if success:

            # Check if skins require updating
            #
            metaToSkeleton = currentStatus == Status.META and status == Status.SKELETON

            if metaToSkeleton:

                self.updateSkins()

            # Check if shapes require updating
            #
            skeletonToRig = currentStatus == Status.SKELETON and status == Status.RIG

            if skeletonToRig:

                self.updateShapes()

        else:

            QtWidgets.QMessageBox.warning(self, 'Change Rig Status', 'Cannot change status while parent is in a different state!')

        # Invalidate rig status
        #
        self.invalidateStatus()
    # endregion