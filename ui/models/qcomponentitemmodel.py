from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from enum import IntEnum
from dcc import fnqt
from dcc.python import stringutils
from ...components import rootcomponent
from mpy import mpyscene, mpynode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ViewDetails(IntEnum):
    """
    Overload of `IntEnum` that contains all the displayable data.
    """

    Name = 0
    Type = 1
    Hash = 2
    Uuid = 3


class QComponentItemModel(QtCore.QAbstractItemModel):
    """
    Overload of `QAbstractItemModel` used to represent rig components.
    """

    # region Dunderscores
    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QComponentItemModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._qt = fnqt.FnQt()
        self._invisibleRootItem = lambda: None
        self._viewDetails = [ViewDetails.Name, ViewDetails.Type, ViewDetails.Uuid]
        self._headerLabels = [stringutils.pascalize(x.name, separator=' ') for x in self._viewDetails]
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def qt(self):
        """
        Getter method that returns the qt function set.

        :rtype: fnqt.FnQt
        """

        return self._qt

    @property
    def invisibleRootItem(self):
        """
        Getter method that returns the invisible root item.

        :rtype: mpynode.MPyNode
        """

        return self._invisibleRootItem()

    @invisibleRootItem.setter
    def invisibleRootItem(self, invisibleRootItem):
        """
        Setter method that updates the invisible root item.

        :type invisibleRootItem: mpynode.MPyNode
        :rtype: None
        """

        # Signal model reset in progress
        #
        self.beginResetModel()

        # Evaluate invisible root item
        #
        if isinstance(invisibleRootItem, rootcomponent.RootComponent):

            self._invisibleRootItem = invisibleRootItem.weakReference()

        else:

            self._invisibleRootItem = lambda: None

        # Signal end of model reset
        #
        self.endResetModel()

    @property
    def viewDetails(self):
        """
        Getter method that returns the view details for this model.

        :rtype: List[ViewDetails]
        """

        return self._viewDetails

    @viewDetails.setter
    def viewDetails(self, viewDetails):
        """
        Setter method that updates the view details for this model.

        :type viewDetails: List[ViewDetails]
        :rtype: None
        """

        # Signal reset in progress
        #
        self.beginResetModel()

        # Update view details
        #
        self._viewDetails = viewDetails
        self._headerLabels = [stringutils.pascalize(x.name, separator=' ') for x in self._viewDetails]

        # Signal reset complete
        #
        self.endResetModel()

    @property
    def headerLabels(self):
        """
        Getter method that returns the header labels.

        :rtype: List[str]
        """

        return self._headerLabels
    # endregion

    # region Methods
    def decodeInternalId(self, internalId):
        """
        Returns an item path from the supplied internal ID.

        :type internalId: int
        :rtype: mpynode.MPyNode
        """

        return mpynode.MPyNode.__instances__.get(internalId, None)

    def componentFromIndex(self, index):
        """
        Returns the path associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: mpynode.MPyNode
        """

        return self.decodeInternalId(index.internalId())

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        if parent.isValid():

            component = self.decodeInternalId(parent.internalId())
            return len(component.componentChildren)

        elif self.invisibleRootItem is not None:

            return 1

        else:

            return 0

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of columns under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return len(self.headerLabels)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        """
        Returns the index of the item in the model specified by the given row, column and parent index.

        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Evaluate parent index
        #
        componentParent = self.decodeInternalId(parent.internalId())

        if componentParent is None:

            return self.createIndex(row, column, id=self.invisibleRootItem.hashCode())

        # Check if row is in range
        #
        componentChildren = list(componentParent.iterComponentChildren())
        componentChildrenCount = len(componentChildren)

        if 0 <= row < componentChildrenCount:

            return self.createIndex(row, column, id=componentChildren[row].hashCode())

        else:

            return QtCore.QModelIndex()

    def parent(self, *args):
        """
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.

        :type index: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Inspect number of arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            return super(QtCore.QAbstractItemModel, self).parent()

        # Evaluate internal id
        #
        index = args[0]
        component = self.decodeInternalId(index.internalId())

        if component is self.invisibleRootItem:

            return QtCore.QModelIndex()

        else:

            componentParent = component.componentParent()
            row = componentParent.componentSiblings(includeSelf=True).index(componentParent)

            return self.createIndex(row, 0, id=componentParent.hashCode())

    def hasChildren(self, parent=None):
        """
        Returns true if parent has any children; otherwise returns false.
        Use rowCount() on the parent to find out the number of children.
        Note that it is undefined behavior to report that a particular index hasChildren with this method if the same index has the flag Qt::ItemNeverHasChildren set!

        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return True  # All components can have children!

    def flags(self, index):
        """
        Returns the item flags for the given index.

        :type index: QtCore.QModelIndex
        :rtype: int
        """

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def supportedDragActions(self):
        """
        Returns the drag actions supported by this model.

        :rtype: int
        """

        return QtCore.Qt.MoveAction

    def supportedDropActions(self):
        """
        Returns the drop actions supported by this model.

        :rtype: int
        """

        return QtCore.Qt.MoveAction

    def mimeTypes(self):
        """
        Returns a list of supported mime types.

        :rtype: List[str]
        """

        return ['text/plain']

    def canDropMimeData(self, data, action, row, column, parent):
        """
        Evaluates if mime data can be dropped on the requested row.

        :type data: QtCore.QMimeData
        :type action: int
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return True

    def insertRow(self, row, item, parent=QtCore.QModelIndex()):
        """
        Inserts a single row before the given row in the child items of the parent specified.

        :type row: int
        :type item: object
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return self.insertRows(row, [item], parent=parent)

    def insertRows(self, row, items, parent=QtCore.QModelIndex()):
        """
        Inserts multiple rows before the given row in the child items of the parent specified.

        :type row: int
        :type items: List[object]
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Signal start of insertion
        #
        count = len(items)
        firstRow = row if row > 0 else self.rowCount(parent)
        lastRow = (firstRow + count) - 1

        self.beginInsertRows(parent, firstRow, lastRow)

        # Insert items into list
        #
        componentParent = self.componentFromIndex(parent)

        for (index, item) in zip(range(firstRow, lastRow + 1), items):

            componentParent.insertComponentChild(index, item)

        # Signal end of insertion
        #
        self.endInsertRows()

        return True

    def moveRow(self, sourceParent, sourceRow, destinationParent, destinationRow):
        """
        Moves the sourceRow, from the sourceParent, to the destinationRow, under destinationParent.
        Returns true if the rows were successfully moved; otherwise returns false.

        :type sourceParent: QtCore.QModelIndex
        :type sourceRow: int
        :type destinationParent: QtCore.QModelIndex
        :type destinationRow: int
        :rtype: bool
        """

        return self.moveRows(sourceParent, sourceRow, 1, destinationParent, destinationRow)

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationRow):
        """
        Moves the sourceRow count, from the sourceParent, to the destinationRow, under destinationParent.
        Returns true if the rows were successfully moved; otherwise returns false.

        :type sourceParent: QtCore.QModelIndex
        :type sourceRow: int
        :type count: int
        :type destinationParent: QtCore.QModelIndex
        :type destinationRow: int
        :rtype: bool
        """

        # Signal start of move
        #
        lastSourceRow = (sourceRow + count) - 1
        lastDestinationRow = (destinationRow + count) - 1

        self.beginMoveRows(sourceParent, sourceRow, lastSourceRow, destinationParent, destinationRow)

        # Check if indices are valid
        #
        if not sourceParent.isValid() or not destinationParent.isValid():

            self.endMoveRows()
            return False

        # Get parent items
        #
        sourceComponent = self.componentFromIndex(sourceParent)
        destinationComponent = self.componentFromIndex(destinationParent)

        if sourceComponent is None or destinationComponent is None:

            self.endMoveRows()
            return False

        # Insert source items under destination parent
        #
        sourceChildren = sourceComponent.popComponentChild(slice(sourceRow, lastSourceRow + 1))

        for (i, sourceChild) in zip(range(destinationRow, lastDestinationRow + 1), sourceChildren):

            destinationComponent.insertComponentChild(i, sourceChild)

        # Signal end of move
        #
        self.endMoveRows()

        return True

    def details(self, index):
        """
        Returns the details for the given index.
        This method is intended to be used with indices derived from the details view mode.

        :type index: QtCore.QModelIndex
        :rtype: Any
        """

        component = self.decodeInternalId(index.internalId())
        column = index.column()
        viewDetail = self.viewDetails[column]

        if viewDetail == ViewDetails.Name:

            return component.name()

        elif viewDetail == ViewDetails.Type:

            return component.className

        elif viewDetail == ViewDetails.Hash:

            return component.hashCode()

        elif viewDetail == ViewDetails.Uuid:

            return component.uuid().asString()

        else:

            return None

    def icon(self, index):
        """
        Returns the icon for the given index.

        :type index: QtCore.QModelIndex
        :rtype: Any
        """

        # Verify this is the name column
        #
        column = index.column()
        component = self.decodeInternalId(index.internalId())
        isNameColumn = self.viewDetails.index(ViewDetails.Name) == column

        if isNameColumn:

            return component.icon()

        else:

            return None

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: int
        :rtype: Any
        """

        # Evaluate data role
        #
        if role == QtCore.Qt.DisplayRole:

            return str(self.details(index))

        elif role == QtCore.Qt.DecorationRole:

            return self.icon(index)

        else:

            return None

    def headerData(self, section, orientation, role=None):
        """
        Returns the data for the given role and section in the header with the specified orientation.

        :type section: int
        :type orientation: int
        :type role: int
        :rtype: Any
        """

        # Evaluate orientation type
        #
        if orientation == QtCore.Qt.Horizontal:

            # Evaluate data role
            #
            if role == QtCore.Qt.DisplayRole:

                return self.headerLabels[section]

            else:

                return super(QComponentItemModel, self).headerData(section, orientation, role=role)

        elif orientation == QtCore.Qt.Vertical:

            # Evaluate data role
            #
            if role == QtCore.Qt.DisplayRole:

                return str(section)

            else:

                return super(QComponentItemModel, self).headerData(section, orientation, role=role)

        else:

            return super(QComponentItemModel, self).headerData(section, orientation, role=role)
    # endregion
