from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.ui import qsingletonwindow, qsignalblocker
from dcc.python import stringutils
from dcc.maya.libs import transformutils
from dcc.maya.models import qplugitemmodel, qplugstyleditemdelegate, qplugitemfiltermodel
from dcc.maya.decorators import undo
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from functools import partial
from itertools import chain
from . import resources
from .models import qcomponentitemmodel, qpropertyitemmodel
from ..libs import Status, Side, componentfactory, interfacefactory, stateutils, layerutils

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
        self._rigManager = interfacefactory.InterfaceFactory.getInstance(asWeakReference=True)
        self._componentManager = componentfactory.ComponentFactory.getInstance(asWeakReference=True)
        self._controlRig = self.nullWeakReference
        self._currentComponent = self.nullWeakReference
        self._currentStatus = 0
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

        # Initialize main toolbar
        #
        self.mainToolBar = QtWidgets.QToolBar(parent=self)
        self.mainToolBar.setObjectName('mainToolBar')
        self.mainToolBar.setAllowedAreas(QtCore.Qt.TopToolBarArea)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setOrientation(QtCore.Qt.Horizontal)
        self.mainToolBar.setIconSize(QtCore.QSize(24, 24))
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

        self.addFootComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/SpineComponent.svg'), 'Foot', parent=self.mainToolBar)
        self.addFootComponentAction.setObjectName('addFootComponentAction')
        self.addFootComponentAction.setWhatsThis('SpineComponent')
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

        self.addJawComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/JawComponent.svg'), 'Jaw', parent=self.mainToolBar)
        self.addJawComponentAction.setObjectName('addJawComponentAction')
        self.addJawComponentAction.setWhatsThis('JawComponent')
        self.addJawComponentAction.setToolTip('Adds a jaw to the selected component.')
        self.addJawComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.addPropComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/PropComponent.svg'), 'Prop', parent=self.mainToolBar)
        self.addPropComponentAction.setObjectName('addPropComponentAction')
        self.addPropComponentAction.setWhatsThis('PropComponent')
        self.addPropComponentAction.setToolTip('Adds a prop to the selected component.')
        self.addPropComponentAction.triggered.connect(self.on_addComponentAction_triggered)

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

        self.addChainComponentAction = QtWidgets.QAction(QtGui.QIcon(':/rigotron/icons/ChainComponent.svg'), 'Stow', parent=self.mainToolBar)
        self.addChainComponentAction.setObjectName('addChainComponentAction')
        self.addChainComponentAction.setWhatsThis('ChainComponent')
        self.addChainComponentAction.setToolTip('Adds a chain to the selected component.')
        self.addChainComponentAction.triggered.connect(self.on_addComponentAction_triggered)

        self.mainToolBar.addAction(self.addRootComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addSpineComponentAction)
        self.mainToolBar.addAction(self.addTailComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addLegComponentAction)
        self.mainToolBar.addAction(self.addFootComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addClavicleComponentAction)
        self.mainToolBar.addAction(self.addArmComponentAction)
        self.mainToolBar.addAction(self.addHandComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addHeadComponentAction)
        self.mainToolBar.addAction(self.addJawComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addPropComponentAction)
        self.mainToolBar.addAction(self.addStowComponentAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addLeafComponentAction)
        self.mainToolBar.addAction(self.addChainComponentAction)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        centralWidget = QtWidgets.QWidget(parent=self)
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize outliner widget
        #
        self.outlinerLayout = QtWidgets.QVBoxLayout()
        self.outlinerLayout.setObjectName('outlinerLayout')
        self.outlinerLayout.setContentsMargins(0, 0, 0, 0)

        self.outlinerWidget = QtWidgets.QWidget()
        self.outlinerWidget.setObjectName('outlinerWidget')
        self.outlinerWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.outlinerWidget.setLayout(self.outlinerLayout)

        self.outlinerHeader = QtWidgets.QGroupBox('Outliner')
        self.outlinerHeader.setObjectName('outlinerHeader')
        self.outlinerHeader.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.outlinerHeader.setAlignment(QtCore.Qt.AlignCenter)
        self.outlinerHeader.setFlat(True)

        self.nameLineEdit = QtWidgets.QLineEdit()
        self.nameLineEdit.setObjectName('nameLineEdit')
        self.nameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nameLineEdit.setFixedHeight(24)
        self.nameLineEdit.setReadOnly(True)
        self.nameLineEdit.setPlaceholderText('Click Root to Create a New Rig!')

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

        headerView = self.outlinerTreeView.header()  # type: QtWidgets.QHeaderView
        headerView.setDefaultSectionSize(200)
        headerView.setMinimumSectionSize(50)
        headerView.setStretchLastSection(True)

        self.outlinerModel = qcomponentitemmodel.QComponentItemModel(parent=self.outlinerTreeView)
        self.outlinerModel.setObjectName('outlinerModel')

        self.outlinerTreeView.setModel(self.outlinerModel)

        self.deleteShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('delete'), self.outlinerTreeView, self.on_outlinerTreeView_deleteKeyPressed)

        self.attachmentComboBox = QtWidgets.QComboBox()
        self.attachmentComboBox.setObjectName('attachmentComboBox')
        self.attachmentComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.attachmentComboBox.setFixedHeight(24)
        self.attachmentComboBox.currentIndexChanged.connect(self.on_attachmentComboBox_currentIndexChanged)

        self.outlinerLayout.addWidget(self.outlinerHeader)
        self.outlinerLayout.addWidget(self.nameLineEdit)
        self.outlinerLayout.addWidget(self.outlinerTreeView)
        self.outlinerLayout.addWidget(self.attachmentComboBox)

        # Initialize property widget
        #
        self.propertyLayout = QtWidgets.QVBoxLayout()
        self.propertyLayout.setObjectName('propertyLayout')
        self.propertyLayout.setContentsMargins(0, 0, 0, 0)

        self.propertyWidget = QtWidgets.QWidget()
        self.propertyWidget.setObjectName('propertyWidget')
        self.propertyWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.propertyWidget.setLayout(self.propertyLayout)

        self.propertyHeader = QtWidgets.QGroupBox('Outliner')
        self.propertyHeader.setObjectName('propertyHeader')
        self.propertyHeader.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.propertyHeader.setAlignment(QtCore.Qt.AlignCenter)
        self.propertyHeader.setFlat(True)

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

        headerView = self.propertyTreeView.header()  # type: QtWidgets.QHeaderView
        headerView.setDefaultSectionSize(200)
        headerView.setMinimumSectionSize(50)
        headerView.setStretchLastSection(True)

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

        self.propertyLayout.addWidget(self.propertyHeader)
        self.propertyLayout.addWidget(self.filterPropertyLineEdit)
        self.propertyLayout.addWidget(self.propertyTreeView)

        # Initialize main splitter
        #
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.mainSplitter.setObjectName('mainSplitter')
        self.mainSplitter.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.mainSplitter.addWidget(self.outlinerWidget)
        self.mainSplitter.addWidget(self.propertyWidget)

        centralLayout.addWidget(self.mainSplitter)

        # Initialize button layout
        #
        self.buttonLayout = QtWidgets.QGridLayout()
        self.buttonLayout.setObjectName('buttonLayout')
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)

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

        self.buttonLayout.addWidget(self.alignPushButton, 0, 0)
        self.buttonLayout.addWidget(self.mirrorPushButton, 0, 1)
        self.buttonLayout.addWidget(self.sanitizePushButton, 0, 2)
        self.buttonLayout.addWidget(self.organizePushButton, 1, 0)
        self.buttonLayout.addWidget(self.detectPushButton, 1, 1)
        self.buttonLayout.addWidget(self.blackBoxPushButton, 1, 2)

        centralLayout.addLayout(self.buttonLayout)

        # Initialize status widget
        #
        self.statusLayout = QtWidgets.QGridLayout()
        self.statusLayout.setObjectName('statusLayout')
        self.statusLayout.setContentsMargins(0, 0, 0, 0)

        self.statusWidget = QtWidgets.QWidget()
        self.statusWidget.setObjectName('interopWidget')
        self.statusWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.statusWidget.setLayout(self.statusLayout)

        self.statusHeader = QtWidgets.QGroupBox('Status:')
        self.statusHeader.setObjectName('statusHeader')
        self.statusHeader.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.statusHeader.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.statusHeader.setFlat(True)

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

        self.statusButtonGroup = QtWidgets.QButtonGroup(self.statusWidget)
        self.statusButtonGroup.setExclusive(True)
        self.statusButtonGroup.addButton(self.metaStatusPushButton, id=0)
        self.statusButtonGroup.addButton(self.skeletonStatusPushButton, id=1)
        self.statusButtonGroup.addButton(self.rigStatusPushButton, id=2)
        self.statusButtonGroup.idClicked.connect(self.on_statusButtonGroup_idClicked)

        self.statusLayout.addWidget(self.statusHeader, 0, 0, 1, 3)
        self.statusLayout.addWidget(self.metaStatusPushButton, 1, 0)
        self.statusLayout.addWidget(self.skeletonStatusPushButton, 1, 1)
        self.statusLayout.addWidget(self.rigStatusPushButton, 1, 2)

        centralLayout.addWidget(self.statusWidget)
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
    def sceneOpening(self, *args, **kwargs):
        """
        Notifies the component item model a scene is being opened.

        :key clientData: Any
        :rtype: None
        """

        self.clearControlRig()

    def sceneOpened(self, *args, **kwargs):
        """
        Notifies the component item model a scene has been opened.

        :key clientData: Any
        :rtype: None
        """

        self.invalidateControlRig()
    # endregion

    # region Methods
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

        # Force scene update
        #
        self.sceneOpened()

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
        self.sceneOpened()

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

    def clearControlRig(self):
        """
        Resets the user interface.

        :rtype: None
        """

        # Reset internal trackers
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

    def invalidateControlRig(self):
        """
        Updates all control-rig related widgets.

        :rtype: None
        """

        # Check if control rig exists
        #
        controlRigs = self.rigManager.controlRigs()
        numControlRigs = len(controlRigs)

        if numControlRigs == 0:

            return

        # Update user interface
        #
        self._controlRig = controlRigs[0].weakReference()
        self._currentComponent = self.nullWeakReference

        self.nameLineEdit.setText(self.controlRig.rigName)
        self.outlinerModel.rootComponent = self.scene(self.controlRig.rootComponent)

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

    @undo.Undo(name='Mirror Joints')
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

    @QtCore.Slot()
    def on_addRootComponentAction_triggered(self):
        """
        Slot method for the `addRootComponentAction` widget's `triggered` signal.

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
