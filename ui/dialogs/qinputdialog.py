from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from dcc.ui.dialogs import qmaindialog

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QInputDialog(qmaindialog.QMainDialog):
    """
    Overload of `QMainDialog` that prompts users for rig related inputs.
    """

    # region Dunderscores
    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Call parent method
        #
        super(QInputDialog, self).__post_init__(*args, **kwargs)

        # Modify dialog title
        #
        title = kwargs.get('title', 'Create Rig:')
        self.setWindowTitle(title)

        # Update label
        #
        label = kwargs.get('label', 'Enter Name:')
        self.label.setText(label)

        # Update line-edit
        #
        text = kwargs.get('text', '')
        mode = kwargs.get('mode', QtWidgets.QLineEdit.Normal)

        self.lineEdit.setText(text)
        self.lineEdit.setEchoMode(mode)

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Initialize dialog
        #
        self.setWindowTitle("Create Animation:")
        self.setMinimumSize(QtCore.QSize(376, 100))

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)

        # Initialize line-edit
        #
        self.label = QtWidgets.QLabel('Enter Name:')
        self.label.setObjectName('label')
        self.label.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.label.setFixedHeight(24)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setObjectName('lineEdit')
        self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.lineEdit.setFixedHeight(24)

        self.checkBox = QtWidgets.QCheckBox('Referenced')
        self.checkBox.setObjectName('checkBox')
        self.checkBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.checkBox.setFixedHeight(24)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setObjectName('layout')
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.checkBox)

        centralLayout.addWidget(self.label)
        centralLayout.addLayout(self.layout)

        # Initialize button-box widget
        #
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setObjectName('buttonBox')
        self.buttonBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.buttonBox.setFixedHeight(24)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        centralLayout.addWidget(self.buttonBox)
    # endregion

    # region Methods
    def textValue(self):
        """
        Returns the text value.

        :rtype: str
        """

        return self.lineEdit.text()

    def referencedValue(self):
        """
        Returns the referenced value

        :rtype: bool
        """

        return self.checkBox.isChecked()

    @classmethod
    def getText(cls, parent, title, label, mode, **kwargs):
        """
        Prompts the user for a text input.

        :type parent: QtWidgets.QWidget
        :type title: str
        :type label: str
        :type mode: int
        :rtype: Tuple[str, Tuple[int, int]]
        """

        instance = cls(title=title, label=label, mode=mode, parent=parent)
        response = instance.exec_()

        return instance.textValue(), instance.referencedValue(), response
    # endregion
