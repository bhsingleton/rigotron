from dcc.json import psonobject
from six import string_types
from maya.api import OpenMaya as om
from mpy import mpyscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SkeletonSpec(psonobject.PSONObject):
    """
    Overload of `PSONObject` that outlines skeleton specifications.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_name', '_uuid', '_matrix', '_driver', '_children', '_groups', '_enabled')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(SkeletonSpec, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._name = kwargs.get('name', '')
        self._uuid = kwargs.get('uuid', om.MUuid())
        self._matrix = kwargs.get('matrix', None)
        self._driver = kwargs.get('driver', '')
        self._children = kwargs.get('children', [])
        self._groups = kwargs.get('groups', {})
        self._enabled = kwargs.get('enabled', True)
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

        :type uuid: om.MUuid
        :rtype: None
        """

        self._uuid = uuid

    @property
    def matrix(self):
        """
        Getter method that returns the matrix.

        :rtype: Union[om.MMatrix, None]
        """

        return self._matrix

    @matrix.setter
    def matrix(self, matrix):
        """
        Setter method that updates the matrix.

        :type matrix: Union[om.MMatrix, None]
        :rtype: None
        """

        self._matrix = matrix

    @property
    def driver(self):
        """
        Getter method that returns the driver.

        :rtype: str
        """

        return self._driver

    @driver.setter
    def driver(self, driver):
        """
        Setter method that updates the driver.

        :type driver: str
        :rtype: None
        """

        self._driver = driver

    @property
    def children(self):
        """
        Getter method that returns any child specs.

        :rtype: List[SkeletonSpec]
        """

        return self._children

    @children.setter
    def children(self, children):
        """
        Setter method that updates the child specs.

        :type children: List[SkeletonSpec]
        :rtype: None
        """

        self._children.clear()
        self._children.extend(children)

    @property
    def groups(self):
        """
        Getter method that returns any group specs.

        :rtype: Dict[int, List[SkeletonSpec]]
        """

        return self._groups

    @groups.setter
    def groups(self, groups):
        """
        Setter method that updates the group specs.

        :type groups: Dict[int, List[SkeletonSpec]]
        :rtype: None
        """

        self._groups.clear()
        self._groups.update(groups)

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
    # endregion

    # region Methods
    @classmethod
    def isJsonCompatible(cls, T):
        """
        Evaluates whether the given type is json compatible.

        :type T: Union[Callable, Tuple[Callable]]
        :rtype: bool
        """

        if T.__module__ == 'OpenMaya':

            return True

        else:

            return super(SkeletonSpec, cls).isJsonCompatible(T)

    def enable(self):
        """
        Enables this skeleton component.

        :rtype: None
        """

        self.enabled = True

    def disable(self):
        """
        Disables this skeleton component.

        :rtype: Non
        """

        self.enabled = False

    def getNode(self):
        """
        Returns the node associated with this skeleton spec.

        :rtype: mpynode.MPyNode
        """

        if not isinstance(self.uuid, om.MUuid):

            return None

        if self.uuid.valid():

            return self.scene(self.uuid)

        else:

            return None

    def deleteNode(self):
        """
        Deletes the node associated with this skeleton spec.

        :rtype: None
        """

        node = self.getNode()

        if node is not None:

            node.delete()

        else:

            log.warning(f'Unable to find "{self.name}" joint to delete!')

    def getDriver(self):
        """
        Returns the driver associated with this skeleton spec.

        :rtype: mpynode.MPyNode
        """

        if not isinstance(self.driver, string_types):

            return None

        if self.scene.doesNodeExist(self.driver):

            return self.scene(self.driver)

        else:

            return None

    def getMatrix(self, default=om.MMatrix.kIdentity):
        """
        Returns the transform matrix from this skeleton spec.
        If no matrix exists then the default matrix is returned instead.

        :type default: om.MMatrix
        :rtype: om.MMatrix
        """

        if isinstance(self.matrix, om.MMatrix):

            return self.matrix

        else:

            return default

    def cacheMatrix(self, delete=False):
        """
        Caches the current world transform matrix.

        :type delete: bool
        :rtype: None
        """

        # Check if skeleton spec is enabled
        #
        if not self.enabled:

            return

        # Check if node exists
        #
        node = self.getNode()

        if node is not None:

            self.matrix = node.worldMatrix()

            if delete:

                node.delete()

        else:

            log.warning(f'Unable to cache "{self.name}" matrix!')
    # endregion
