from maya.api import OpenMaya as om
from mpy import mpyattribute
from . import limbcomponent
from enum import IntEnum
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LocomotionType(IntEnum):
    """
    Enum class of locomotion types.
    """

    NONE = -1
    PLANTIGRADE = 0
    DIGITGRADE = 1


class ExtremityComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that outlines extremity components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Extremity'
    # endregion

    # region Enums
    LocomotionType = LocomotionType
    # endregion

    # region Methods
    def getAssociatedLimbComponent(self):
        """
        Returns the associated limb component.

        :rtype: rigotron.components.limbcomponent.LimbComponent
        """

        limbComponents = self.findComponentAncestors('LimbComponent')
        hasLimbComponent = len(limbComponents) == 1

        if hasLimbComponent:

            return limbComponents[0]

        else:

            return None

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Evaluate component parent
        #
        componentParent = self.componentParent()

        if isinstance(componentParent, limbcomponent.LimbComponent):

            componentParent.attachExtremityComponent(self)

        # Call parent method
        #
        return super(ExtremityComponent, self).buildRig()

    def effectorMatrix(self):
        """
        Returns the effector matrix for this component.

        :rtype: om.MMatrix
        """

        skeletonSpecs = self.skeleton()
        hasSkeletonSpecs = len(skeletonSpecs) > 0

        if hasSkeletonSpecs:

            return skeletonSpecs[0].getNode(referenceNode=self.skeletonReference()).worldMatrix()

        else:

            return om.MMatrix.kIdentity

    def preferredEffectorMatrix(self):
        """
        Returns the preferred effector matrix for this component.
        By default, this will return the first skeletal spec matrix!

        :rtype: om.MMatrix
        """

        return self.effectorMatrix()
    # endregion
