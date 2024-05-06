from dcc.json import psonobject
from maya.api import OpenMaya as om
from mpy import mpyscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PivotSpec(psonobject.PSONObject):
    """
    Overload of `PSONObject` that outlines pivot specifications.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_name', '_uuid', '_matrix', '_controlPoints', '_enabled')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(PivotSpec, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._name = kwargs.get('name', '')
        self._uuid = kwargs.get('uuid', om.MUuid())
        self._matrix = kwargs.get('matrix', None)
        self._controlPoints = kwargs.get('controlPoints', [])
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

        :rtype: om.MMatrix
        """

        return self._matrix

    @matrix.setter
    def matrix(self, matrix):
        """
        Setter method that updates the matrix.

        :type matrix: om.MMatrix
        :rtype: None
        """

        self._matrix = matrix

    @property
    def controlPoints(self):
        """
        Getter method that returns the control points.

        :rtype: List[om.MPoint]
        """

        return self._controlPoints

    @controlPoints.setter
    def controlPoints(self, controlPoints):
        """
        Setter method that updates the control points.

        :type controlPoints: List[om.MPoint]
        :rtype: None
        """

        self._controlPoints = controlPoints

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

            return super(PivotSpec, cls).isJsonCompatible(T)

    def enable(self):
        """
        Enables this pivot component.

        :rtype: None
        """

        self.enabled = True

    def disable(self):
        """
        Disables this pivot component.

        :rtype: Non
        """

        self.enabled = False

    def getNode(self):
        """
        Returns the node associated with this pivot spec.

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
        Deletes the node associated with this pivot spec.

        :rtype: None
        """

        node = self.getNode()

        if node is not None:

            node.delete()

        else:

            log.warning(f'Unable to find "{self.name}" pivot to delete!')

    def getMatrix(self, default=om.MMatrix.kIdentity):
        """
        Returns the transform matrix from this pivot spec.
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

        # Check if pivot spec is enabled
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
