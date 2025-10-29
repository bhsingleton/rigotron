from fnmatch import fnmatchcase
from dcc.python import stringutils
from dcc.ui import qsignalblocker
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QLogsTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that outputs logs from the remote standalone process.
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
        super(QLogsTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._process = None

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QLogsTab, self).__setup_ui__(*args, **kwargs)

        # Initialize widget
        #
        self.setObjectName('logsTab')

        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('logsTabLayout')
        self.setLayout(centralLayout)

        # Initialize text edit
        #
        self.logEdit = QtWidgets.QPlainTextEdit('')
        self.logEdit.setObjectName('logEdit')
        self.logEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.logEdit.setReadOnly(True)

        centralLayout.addWidget(self.logEdit)
    # endregion

    # region Properties
    @property
    def process(self):
        """
        Getter method that returns the standalone process.

        :rtype: Union[QtCore.QProcess, None]
        """

        return self._process

    @process.setter
    def process(self, process):
        """
        Setter method that updates the standalone process.

        :type process: QtCore.QProcess
        :rtype: None
        """

        if isinstance(self._process, QtCore.QProcess):

            self._process.readyReadStandardOutput.disconnect(self.on_process_readyReadStandardOutput)
            self._process.readyReadStandardError.disconnect(self.on_process_readyReadStandardError)

        if isinstance(process, QtCore.QProcess):

            self._process = process
            self._process.readyReadStandardOutput.connect(self.on_process_readyReadStandardOutput)
            self._process.readyReadStandardError.connect(self.on_process_readyReadStandardError)

        else:

            raise TypeError(f'process.setter() expects a QProcess ({type(process).__name__} given)!')
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_process_readyReadStandardOutput(self):
        """
        Slot method for the process widget's `readyReadStandardOutput` signal.

        :rtype: None
        """

        # Decode standard output
        #
        sender = self.sender()
        data = sender.readAllStandardOutput()

        stdout = bytes(data).decode("utf8")

        # Iterate through output lines
        #
        lines = stdout.splitlines()

        for line in lines:

            # Ignore any empty lines
            #
            line = line.strip(stringutils.__escape_chars__)

            if stringutils.isNullOrEmpty(line):

                continue

            # Ignore any redundant logs
            #
            if any(line.startswith(level) for level in ('DEBUG', 'INFO', 'WARNING', 'ERROR')):

                continue

            # Append line to text-edit
            #
            self.logTextEdit.appendHtml(f'<p style="font-size:14px; color:white;">{line}</p>')

    @QtCore.Slot()
    def on_process_readyReadStandardError(self):
        """
        Slot method for the process widget's `readyReadStandardError` signal.

        :rtype: None
        """

        # Decode standard error
        #
        sender = self.sender()
        data = sender.readAllStandardError()

        stderr = bytes(data).decode("utf8")

        # Iterate through output lines
        #
        lines = stderr.splitlines()

        for line in lines:

            # Ignore any empty lines
            #
            line = line.strip(stringutils.__escape_chars__)

            if stringutils.isNullOrEmpty(line):

                continue

            # Ignore any redundant logs
            #
            if any(line.startswith(level) for level in ('DEBUG', 'INFO', 'WARNING', 'ERROR')):

                continue

            # Append line to text-edit
            #
            isWarning = fnmatchcase(line, f'*:WARNING:')
            isError = fnmatchcase(line, f'*:ERROR:')
            color = 'orange' if isWarning else 'red' if isError else 'white'

            self.logEdit.appendHtml(f'<p style="font-size:14px; color:{color};">{line}</p>')
    # endregion
