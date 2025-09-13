from maya.api import OpenMaya as om
from mpy import mpyscene
from dcc.maya.libs import dagutils
from dcc.maya.json import melsonobject
from dcc.collections import notifylist
from dcc.vendor.six import string_types
from abc import ABCMeta, abstractmethod
from ..libs import driverspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractSpec(melsonobject.MELSONObject, metaclass=ABCMeta):
    """
    Overload of `MELSONObject` that outlines node specifications.
    """

    # region Dunderscores
    __slots__ = (
        '__weakref__',
        '_scene',
        '_enabled',
        '_name',
        '_uuid',
        '_matrix',
        '_defaultMatrix',
        '_driver',
        '_parent',
        '_children'
    )

    __default_name__ = 'transform'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(AbstractSpec, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._name = str(self.__default_name__)
        self._uuid = om.MUuid()
        self._matrix = None
        self._defaultMatrix = om.MTransformationMatrix.kIdentity
        self._driver = driverspec.DriverSpec(driven=self.weakReference())
        self._parent = self.nullWeakReference
        self._children = notifylist.NotifyList()
        self._enabled = True

        # Register callbacks
        #
        self._children.addCallback('itemAdded', self.childAdded)
        self._children.addCallback('itemRemoved', self.childRemoved)
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
    def enabled(self):
        """
        Getter method that returns the enabled state.

        :rtype: bool
        """

        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        """
        Setter method that updates the enabled state.

        :type enabled: bool
        :rtype: None
        """

        self._enabled = enabled

    @property
    def name(self):
        """
        Getter method that returns the name.

        :rtype: str
        """

        return self._name

    @name.setter
    def name(self, name):
        """
        Setter method that updates the name.

        :type name: str
        :rtype: None
        """

        self._name = name

    @name.deleter
    def name(self):
        """
        Deleter method that resets the name.

        :rtype: None
        """

        self._name = ''

    @property
    def uuid(self):
        """
        Getter method that returns the UUID.

        :rtype: om.MUuid
        """

        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        """
        Setter method that updates the UUID.

        :type uuid: Union[str, om.MUuid]
        :rtype: None
        """

        if isinstance(uuid, om.MUuid):

            self._uuid.copy(uuid)

        elif isinstance(uuid, string_types):

            self.uuid = om.MUuid(uuid)

        else:

            raise TypeError(f'uuid.setter() expects a valid UUID ({type(uuid).__name__} given)!')

    @uuid.deleter
    def uuid(self):
        """
        Deleter method that resets the UUID.

        :rtype: None
        """

        self._uuid.__init__()

    @property
    def matrix(self):
        """
        Getter method that returns the matrix.

        :rtype: Union[om.MTransformationMatrix, None]
        """

        if isinstance(self._matrix, om.MTransformationMatrix):

            return self._matrix

        else:

            return self._defaultMatrix  # This makes it super easy to define initial matrices!

    @matrix.setter
    def matrix(self, matrix):
        """
        Setter method that updates the matrix.

        :type matrix: Union[om.MTransformationMatrix, om.MMatrix]
        :rtype: None
        """

        if isinstance(matrix, om.MTransformationMatrix):

            self._matrix = matrix

        elif isinstance(matrix, om.MMatrix):

            self._matrix = om.MTransformationMatrix(matrix)

        else:

            raise TypeError(f'matrix.setter() expects an transformation matrix ({type(matrix).__name__} given)!')

    @matrix.deleter
    def matrix(self):
        """
        Deleter method that resets the matrix.

        :rtype: None
        """

        self._matrix = None

    @property
    def defaultMatrix(self):
        """
        Getter method that returns the default matrix.

        :rtype: om.MTransformationMatrix
        """

        return self._defaultMatrix

    @defaultMatrix.setter
    def defaultMatrix(self, defaultMatrix):
        """
        Setter method that updates the default matrix.

        :type defaultMatrix: Union[om.MTransformationMatrix, om.MMatrix]
        :rtype: None
        """

        if isinstance(defaultMatrix, om.MTransformationMatrix):

            self._defaultMatrix = defaultMatrix

        elif isinstance(defaultMatrix, om.MMatrix):

            self._defaultMatrix = om.MTransformationMatrix(defaultMatrix)

        else:

            raise TypeError(f'matrix.setter() expects an transformation matrix ({type(defaultMatrix).__name__} given)!')

    @defaultMatrix.deleter
    def defaultMatrix(self):
        """
        Deleter method that resets the default matrix.

        :rtype: None
        """

        self._defaultMatrix = om.MMatrix.kIdentity

    @property
    def driver(self):
        """
        Getter method that returns the driver.

        :rtype: driverspec.DriverSpec
        """

        return self._driver

    @driver.setter
    def driver(self, driver):
        """
        Setter method that updates the driver.

        :type driver: Union[str, driverspec.DriverSpec]
        :rtype: None
        """

        if isinstance(driver, driverspec.DriverSpec):

            self._driver = driver
            self._driver._driven = self.weakReference()

        elif isinstance(driver, string_types):

            self._driver.name = driver

        else:

            raise TypeError(f'driver.setter() expects a valid driver ({type(driver).__name__} given)!')

    @property
    def parent(self):
        """
        Getter method that returns the parent.

        :rtype: AbstractSpec
        """

        return self._parent()

    @property
    def children(self):
        """
        Getter method that returns any child specs.

        :rtype: List[AbstractSpec]
        """

        return self._children

    @children.setter
    def children(self, children):
        """
        Setter method that updates the child specs.

        :type children: List[AbstractSpec]
        :rtype: None
        """

        self._children.clear()
        self._children.extend(children)
    # endregion

    # region Callbacks
    def childAdded(self, index, child):
        """
        Callback method that updates the child's parent reference.

        :type index: int
        :type child: SkeletonSpec
        :rtype: None
        """

        child._parent = self.weakReference()

    def childRemoved(self, child):
        """
        Callback method that removes the child's parent reference.

        :type child: SkeletonSpec
        :rtype: None
        """

        child._parent = self.nullWeakReference
    # endregion

    # region Methods
    def enable(self):
        """
        Enables this spec.

        :rtype: None
        """

        self.enabled = True

    def disable(self):
        """
        Disables this spec.

        :rtype: Non
        """

        self.enabled = False

    def exists(self):
        """
        Evaluates whether the associated node exists.

        :rtype: bool
        """

        return self.scene.doesNodeExist(self.uuid)

    def getNode(self, referenceNode=None):
        """
        Returns the node associated with this spec.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :rtype: Union[mpynode.MPyNode, None]
        """

        # Check if spec is enabled
        #
        if not self.enabled:

            return None

        # Check if UUID is valid
        #
        if dagutils.isValidUUID(self.uuid):

            return self.scene.getNodeByUuid(self.uuid, referenceNode=referenceNode)

        else:

            return None

    def deleteNode(self, referenceNode=None):
        """
        Deletes the node associated with this spec.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :rtype: bool
        """

        # Check if spec is enabled
        #
        if not self.enabled:

            return False

        # Check if node exists
        #
        node = self.getNode(referenceNode=referenceNode)

        if node is None:

            log.warning(f'Unable to locate "{self.name}" node to delete!')
            return False

        # Check if node can be deleted
        #
        if not node.isFromReferencedFile:

            node.removeConstraints()
            node.delete()
            return True

        else:

            log.warning(f'Unable to delete "{self.name}" referenced node!')
            return False

    def cacheNode(self, referenceNode=None, delete=False):
        """
        Caches the associated node's transformation matrix.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :type delete: bool
        :rtype: None
        """

        # Check if spec is enabled
        #
        if not self.enabled:

            return

        # Check if node exists
        #
        node = self.getNode(referenceNode=referenceNode)

        if node is None:

            log.warning(f'Unable to locate "{self.name}" node to cache!')
            return

        # Cache world matrix
        #
        self.matrix = node.matrix(asTransformationMatrix=True)

        # Check if node requires deleting
        #
        if delete:

            self.deleteNode(referenceNode=referenceNode)
    # endregion
