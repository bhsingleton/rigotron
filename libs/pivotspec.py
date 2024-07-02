from maya.api import OpenMaya as om
from mpy import mpyscene
from dcc.maya.json import melsonobject

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PivotSpec(melsonobject.MELSONObject):
    """
    Overload of `MELSONObject` that outlines pivot specifications.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_name', '_uuid', '_matrix', '_shapes', '_enabled')

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
        self._shapes = kwargs.get('shapes', None)
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
    def shapes(self):
        """
        Getter method that returns the shapes.

        :rtype: Union[str, None]
        """

        return self._shapes

    @shapes.setter
    def shapes(self, shapes):
        """
        Setter method that updates the shapes.

        :type shapes: Union[str, None]
        :rtype: None
        """

        self._shapes = shapes

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

        # Evaluate UUID exists
        #
        if not isinstance(self.uuid, om.MUuid):

            return None

        # Check if UUID is valid
        #
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

        if node is None:

            log.warning(f'Unable to cache "{self.name}" matrix!')
            return

        # Cache world matrix
        #
        self.matrix = node.worldMatrix()

        # Cache any customizable shapes
        #
        shapes = node.shapes()
        hasShapes = len(shapes)

        if hasShapes:

            shape = shapes[0]
            hasNurbsCurve = shape.hasFn(om.MFn.kNurbsCurve)

            self.shapes = node.dumpShapes() if hasNurbsCurve else None

        # Check if pivot requires deleting
        #
        if delete:

            node.removeConstraints()
            node.delete()
    # endregion
