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
    __slots__ = ('_shapes',)
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
        self._shapes = None
    # endregion

    # region Properties
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
    def cacheNode(self, delete=False, referenceNode=None):
        """
        Caches the associated node's transformation matrix.

        :type delete: bool
        :type referenceNode: Union[mpynode.MPyNode, None]
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

        # Cache any customizable shapes
        #
        nurbsCurves = node.shapes(apiType=om.MFn.kNurbsCurve)
        hasNurbsCurves = len(nurbsCurves) > 0

        if hasNurbsCurves:

            self.shapes = node.dumpShapes()

        # Call parent method
        #
        return super(PivotSpec, self).cacheNode(delete=delete, referenceNode=referenceNode)
    # endregion
