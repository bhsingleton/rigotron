from mpy import mpyattribute
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LimbComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that outlines limb components.
    """

    # region Dunderscores
    __default_component_name__ = 'Limb'
    # endregion

    # region Attributes
    twistEnabled = mpyattribute.MPyAttribute('twistEnabled', attributeType='bool', default=True)
    numTwistLinks = mpyattribute.MPyAttribute('numTwistLinks', attributeType='int', min=2, default=3)

    @twistEnabled.changed
    def twistEnabled(self, twistEnabled):
        """
        Changed method that notifies any twist state changes.

        :type twistEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numTwistLinks.changed
    def numTwistLinks(self, numTwistLinks):
        """
        Changed method that notifies any twist link size changes.

        :type numTwistLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()

    @basecomponent.BaseComponent.componentChildren.changed
    def componentChildren(self, componentChildren):
        """
        Changed method that notifies any component children changes.

        :type componentChildren: List[om.MObject]
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def findExtremityComponent(self):
        """
        Returns the extremity component related to this limb component.

        :rtype: Union[rigotron.components.extremitycomponent.ExtremityComponent, None]
        """

        components = self.findComponentDescendants('ExtremityComponent')
        numComponents = len(components)

        if numComponents == 0:

            return None

        elif numComponents == 1:

            return components[0]

        else:

            raise TypeError(f'findExtremityComponent() expects 1 extremity component ({numComponents} found)!')

    def hasExtremityComponent(self):
        """
        Evaluates if this limb component has an extremity component.

        :rtype: bool
        """

        return self.findExtremityComponent() is not None

    def extremityMatrix(self):
        """
        Returns theextremity matrix for this component.

        :rtype: om.MMatrix
        """

        component = self.findExtremityComponent()

        if component is not None:

            return component.effectorMatrix()

        else:

            return self.scene(self.skeletonSpecs()[-1].uuid).worldMatrix()

    def effectorMatrix(self):
        """
        Returns the preferred effector matrix for this component.

        :rtype: om.MMatrix
        """

        component = self.findExtremityComponent()

        if component is not None:

            return component.preferredEffectorMatrix()

        else:

            return self.scene(self.skeletonSpecs()[-1].uuid).worldMatrix()
    # endregion
