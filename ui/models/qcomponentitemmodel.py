import json

from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from enum import IntEnum
from dcc.python import stringutils
from ...libs import Status
from ...components import rootcomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ViewDetail(IntEnum):
    """
    Overload of `IntEnum` that contains all displayable data.
    """

    NAME = 0
    TYPE = 1
    HASH = 2
    UUID = 3


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
        self._rootComponent = self.nullWeakReference
        self._viewDetails = [ViewDetail.NAME, ViewDetail.TYPE]
        self._headerLabels = [detail.name.title() for detail in self._viewDetails]
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
        Getter method that returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def rootComponent(self):
        """
        Getter method that returns the root component.

        :rtype: rootcomponent.RootComponent
        """

        return self._rootComponent()

    @rootComponent.setter
    def rootComponent(self, rootComponent):
        """
        Setter method that updates the root component.

        :type rootComponent: rootcomponent.RootComponent
        :rtype: None
        """

        # Signal model reset in progress
        #
        self.beginResetModel()

        # Evaluate invisible root item
        #
        if isinstance(rootComponent, rootcomponent.RootComponent):

            self._rootComponent = rootComponent.weakReference()

        elif rootComponent is None:

            self._rootComponent = self.nullWeakReference

        else:

            raise TypeError(f'rootComponent.setter() expects a RootComponent ({type(rootComponent).__name__} given)!')

        # Signal end of model reset
        #
        self.endResetModel()

    @property
    def viewDetails(self):
        """
        Getter method that returns the view details for this model.

        :rtype: List[ViewDetail]
        """

        return self._viewDetails

    @viewDetails.setter
    def viewDetails(self, viewDetails):
        """
        Setter method that updates the view details for this model.

        :type viewDetails: List[ViewDetail]
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

    def indexFromComponent(self, component, column=0):
        """
        Returns an index from the supplied component.

        :type component: mpynode.MPyNode
        :type column: int
        :rtype: QtCore.QModelIndex
        """

        componentParent = component.componentParent()
        hashCode = component.hashCode()

        if componentParent is not None:

            componentChildren = list(componentParent.iterComponentChildren())
            row = componentChildren.index(component)

            return self.createIndex(row, column, id=hashCode)

        else:

            return self.createIndex(0, column, id=hashCode)

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        isTopLevel = not parent.isValid()

        if isTopLevel:

            hasValidRoot = self.rootComponent is not None
            return 1 if hasValidRoot else 0

        else:

            component = self.decodeInternalId(parent.internalId())
            return component.componentChildCount()

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

            return self.createIndex(row, column, id=self.rootComponent.hashCode())

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

        if component is self.rootComponent:

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

        isRoot = not parent.isValid()

        if isRoot:

            return self.rootComponent is not None

        else:

            return True  # All components can have children!

    def flags(self, index):
        """
        Returns the item flags for the given index.

        :type index: QtCore.QModelIndex
        :rtype: int
        """

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

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

    def mimeData(self, indexes):
        """
        Returns an object that contains serialized items of data corresponding to the list of indexes specified.

        :type indexes: List[QtCore.QModelIndex]
        :rtype: QtCore.QMimeData
        """

        # Collect valid components
        #
        filteredIndexes = [index for index in indexes if index.column() == 0]
        hashCodes = []

        for index in filteredIndexes:

            component = self.componentFromIndex(index)
            componentStatus = Status(component.componentStatus)

            if componentStatus == Status.META:

                hashCodes.append(component.hashCode())

            else:

                continue

        # Populate mime data with UUIDs
        #
        mimeData = QtCore.QMimeData()
        mimeData.setText(json.dumps(hashCodes))

        return mimeData

    def canDropMimeData(self, data, action, row, column, parent):
        """
        Evaluates if mime data can be dropped on the requested row.

        :type data: QtCore.QMimeData
        :type action: QtCore.Qt.DropAction
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Get component from index
        #
        index = self.index(row, column, parent=parent) if (row >= 0) else parent
        component = self.componentFromIndex(index)

        if component is None:

            return False

        # Evaluate component status
        #
        componentStatus = Status(component.componentStatus)

        if componentStatus == Status.META:

            return True  # TODO: Test if incoming components are also in the meta state!

        else:

            return False

    def dropMimeData(self, data, action, row, column, parent):
        """
        Handles the data supplied by a drag and drop operation that ended with the given action.
        Returns true if the data and action were handled by the model; otherwise returns false.

        :type data: QtCore.QMimeData
        :type action: int
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Load mime data
        #
        hashCodes = []

        try:

            hashCodes = json.loads(data.text())

        except json.JSONDecodeError as exception:

            log.error(exception)
            return False

        finally:

            for hashCode in reversed(sorted(hashCodes)):

                sourceComponent = self.decodeInternalId(hashCode)
                sourceIndex = self.indexFromComponent(sourceComponent)
                sourceRow = sourceIndex.row()
                sourceParent = self.parent(sourceIndex)

                success = self.moveRow(sourceParent, sourceRow, parent, row)

                if not success:

                    break

            return False  # Returning true causes Qt to call `removeRows` which is not desirable!

    def appendRow(self, item, parent=QtCore.QModelIndex()):
        """
        Appends a single row before the given row in the child items of the parent specified.

        :type item: object
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return self.insertRow(self.rowCount(parent), item, parent=parent)

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

    def removeRow(self, row, parent=QtCore.QModelIndex()):
        """
        Removes the given row from the child items of the parent specified.
        Returns true if the row is removed; otherwise returns false.

        :type row: int
        :type count: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return self.removeRows(row, 1, parent=parent)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        """
        On models that support this, removes count rows starting with the given row under parent from the model.
        Returns true if the rows were successfully removed; otherwise returns false.

        :type row: int
        :type count: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """
        
        # Signal start of removal
        #
        lastRow = (row + count) - 1
        self.beginRemoveRows(parent, row, lastRow)

        # Check if indices are valid
        #
        if not parent.isValid():

            self.endRemoveRows()
            return False

        # Get parent items
        #
        parentComponent = self.componentFromIndex(parent)
        childComponents = parentComponent.popComponentChild(slice(row, lastRow + 1))

        for childComponent in childComponents:

            childComponent.delete()

        # Signal end of removal
        #
        self.endRemoveRows()

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

        if viewDetail == ViewDetail.NAME:

            return component.name()

        elif viewDetail == ViewDetail.TYPE:

            return component.className

        elif viewDetail == ViewDetail.HASH:

            return component.hashCode()

        elif viewDetail == ViewDetail.UUID:

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
        isNameColumn = self.viewDetails.index(ViewDetail.NAME) == column

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
        :type orientation: QtCore.Qt.Orientation
        :type role: QtCore.Qt.ItemDataRole
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
