from maya.api import OpenMaya as om
from mpy import mpynode
from dcc.maya.models import qplugitemmodel


class QPropertyItemModel(qplugitemmodel.QPlugItemModel):
    """
    Overload of `QPlugItemModel` that overrides the plug mutator logic with `MPyAttribute` properties.
    Without this we can't trigger an internal invalidate with the component classes!
    """

    def setDetail(self, index, value):
        """
        Updates the detail for the supplied index.

        :type index: QtCore.QModelIndex
        :type value: Any
        :rtype: bool
        """

        # Check if plug is editable
        #
        path = self.decodeInternalId(index.internalId())
        plug = path.plug()

        isReadOnly = plug.isFreeToChange() == om.MPlug.kNotFreeToChange

        if isReadOnly:

            return False

        # Check if node has property
        #
        node = mpynode.MPyNode(plug.node())
        plugName = plug.partialName(
            includeNodeName=False,
            useLongNames=True,
            includeInstancedIndices=True,
            includeNonMandatoryIndices=True,
            useFullAttributePath=False
        )

        if hasattr(node, plugName):

            setattr(node, plugName, value)  # This will trigger any custom `changed` property decorators!

        else:

            node.setAttr(plug, value)

        return True
