from maya.api import OpenMaya as om
from dcc.vendor.six import string_types
from . import Side, Type, Style
from ..abstract import abstractspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SkeletonSpec(abstractspec.AbstractSpec):
    """
    Overload of `AbstractSpec` that outlines skeleton specifications.
    """

    # region Dunderscores
    __slots__ = (
        '_passthrough',
        '_side',
        '_type',
        '_otherType',
        '_drawStyle'
    )

    __default_name__ = 'joint'

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
        self._passthrough = False
        self._side = Side.NONE
        self._type = Type.NONE
        self._otherType = ''
        self._drawStyle = Style.BONE
    # endregion

    # region Properties
    @abstractspec.AbstractSpec.parent.getter
    def parent(self):
        """
        Getter method that returns the parent.
        If the parent is marked as passthrough then the grandparent will be returned instead!

        :rtype: bool
        """

        # Check if parent exists
        #
        parent = super(SkeletonSpec, self).parent
        
        if parent is None:

            return parent

        # Check if parent is set to passthrough
        #
        if parent.passthrough:

            return parent.parent

        else:

            return parent

    @property
    def passthrough(self):
        """
        Getter method that returns the passthrough flag.

        :rtype: bool
        """

        return self._passthrough

    @passthrough.setter
    def passthrough(self, passthrough):
        """
        Setter method that updates the passthrough flag.

        :type passthrough: bool
        :rtype: None
        """

        self._passthrough = passthrough

    @property
    def side(self):
        """
        Getter method that returns the side.

        :rtype: Side
        """

        return self._side

    @side.setter
    def side(self, side):
        """
        Setter method that updates the side.

        :type side: Union[int, Side]
        :rtype: None
        """

        self._side = Side(side)
        self._driver.maintainOffset = (self._side == Side.RIGHT)

    @property
    def type(self):
        """
        Getter method that returns the type.

        :rtype: Type
        """

        return self._type

    @type.setter
    def type(self, type):
        """
        Setter method that updates the type.

        :type type: Union[Type, int]
        :rtype: None
        """

        self._type = Type(type)

    @property
    def otherType(self):
        """
        Getter method that returns the other type.

        :rtype: str
        """

        return self._otherType

    @otherType.setter
    def otherType(self, otherType):
        """
        Setter method that updates the other type.

        :type otherType: str
        :rtype: None
        """

        self._otherType = otherType

    @property
    def drawStyle(self):
        """
        Getter method that returns the draw style.

        :rtype: Style
        """

        return self._drawStyle

    @drawStyle.setter
    def drawStyle(self, drawStyle):
        """
        Setter method that updates the draw style.

        :type drawStyle: Union[Style, int]
        :rtype: None
        """

        self._drawStyle = Style(drawStyle)
    # endregion
