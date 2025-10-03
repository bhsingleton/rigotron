from maya.api import OpenMaya as om
from ..abstract import abstractspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PivotSpec(abstractspec.AbstractSpec):
    """
    Overload of `MELSONObject` that outlines pivot specifications.
    """

    # region Dunderscores
    __slots__ = ('_parentMatrix', '_shapes',)
    __default_name__ = 'pivot'

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
        self._parentMatrix = om.MMatrix.kIdentity
        self._shapes = None
    # endregion

    # region Properties
    @property
    def parentMatrix(self):
        """
        Getter method that returns the parent matrix.

        :rtype: om.MMatrix
        """

        return self._parentMatrix

    @parentMatrix.setter
    def parentMatrix(self, parentMatrix):
        """
        Setter method that updates the parent matrix.

        :type parentMatrix: om.MMatrix
        :rtype: None
        """

        self._parentMatrix = parentMatrix

    @property
    def worldMatrix(self):
        """
        Getter method that returns the world matrix.

        :rtype: om.MMatrix
        """

        return self.matrix.asMatrix() * self.parentMatrix

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
    # endregion

    # region Methods
    def cacheNode(self, **kwargs):
        """
        Caches the associated node's transformation matrix.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :type delete: bool
        :rtype: bool
        """

        # Check if spec is enabled
        #
        if not self.enabled:

            return False

        # Check if node exists
        #
        referenceNode = kwargs.get('referenceNode', None)
        node = self.getNode(referenceNode=referenceNode)

        if node is None:

            log.warning(f'Unable to locate "{self.name}" node to cache!')
            return False

        # Cache parent matrix
        # This will also include the offset parent matrix!
        #
        self.parentMatrix = node.parentMatrix()

        # Cache any customizable shapes
        #
        nurbsCurves = node.shapes(apiType=om.MFn.kNurbsCurve)
        hasNurbsCurves = len(nurbsCurves) > 0

        if hasNurbsCurves:

            self.shapes = node.dumpShapes()

        # Call parent method
        #
        return super(PivotSpec, self).cacheNode(**kwargs)
    # endregion
