from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.dataclasses.colour import Colour
from dcc.naming import namingutils
from enum import IntEnum
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PlayerIKType(IntEnum):
    """
    Enum class of all available player IK types.
    """

    FOOT = 0
    HAND = 1
    PROP = 2
    WEAPON = 3


class PlayerIKComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements player IK components.
    """

    # region Enums
    PlayerIKType = PlayerIKType
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'PlayerIK'
    # endregion

    # region Attributes
    feetEnabled = mpyattribute.MPyAttribute('feetEnabled', attributeType='bool', default=True)
    handsEnabled = mpyattribute.MPyAttribute('handsEnabled', attributeType='bool', default=True)
    propsEnabled = mpyattribute.MPyAttribute('propsEnabled', attributeType='bool', default=False)
    weaponsEnabled = mpyattribute.MPyAttribute('weaponsEnabled', attributeType='bool', default=True)
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Check if root component exists
        # Without it, we can't traverse the component tree for the required components!
        #
        rootComponent = self.findRootComponent()

        if rootComponent is None:

            return skeletonSpecs

        # Resize skeleton specs
        #
        namespace = self.skeletonNamespace()
        size = len(self.PlayerIKType)

        footSpec, handSpec, propSpec, weaponSpec = self.resizeSkeleton(size, skeletonSpecs, hierarchical=False)

        # Check if feet IK trackers are required
        #
        feetEnabled = bool(self.feetEnabled)

        footSpec.name = self.formatName(name='Foot', subname='Root', kinemat='IK')
        footSpec.enabled = feetEnabled
        footSpec.passthrough = True

        footComponents = rootComponent.findComponentDescendants('FootComponent')
        numFootComponents = len(footComponents)

        footSpecs = self.resizeSkeleton(numFootComponents, footSpec.children, hierarchical=False)

        for (spec, component) in zip(footSpecs, footComponents):

            componentName = component.componentName
            componentId = component.componentId
            componentSpec = component.skeleton()[0]
            componentSide = self.Side(component.componentSide)

            spec.enabled = feetEnabled
            spec.name = self.formatName(side=componentSide, name=componentName, id=componentId, kinemat='IK')
            spec.side = componentSide
            spec.type = self.Type.OTHER
            spec.otherType = f'{componentName}_IK'
            spec.driver.name = componentSpec.name
            spec.driver.namespace = namespace

        # Check if hand IK trackers are required
        #
        handsEnabled = bool(self.feetEnabled)

        handSpec.name = self.formatName(name='Hand', subname='Root', kinemat='IK')
        handSpec.enabled = handsEnabled
        handSpec.passthrough = True

        handComponents = rootComponent.findComponentDescendants('HandComponent')
        numHandComponents = len(handComponents)

        handSpecs = self.resizeSkeleton(numHandComponents, handSpec.children, hierarchical=False)

        for (spec, component) in zip(handSpecs, handComponents):

            componentName = component.componentName
            componentId = component.componentId
            componentSpec = component.skeleton()[0]
            componentSide = self.Side(component.componentSide)

            spec.enabled = handsEnabled
            spec.name = self.formatName(side=componentSide, name=componentName, id=componentId, kinemat='IK')
            spec.side = componentSide
            spec.type = self.Type.OTHER
            spec.otherType = f'{componentName}_IK'
            spec.driver.name = componentSpec.name
            spec.driver.namespace = namespace

        # Check if prop IK trackers are required
        #
        propsEnabled = bool(self.propsEnabled)

        propSpec.name = self.formatName(name='Prop', subname='Root', kinemat='IK')
        propSpec.enabled = propsEnabled
        propSpec.passthrough = True

        propComponents = rootComponent.findComponentDescendants('PropComponent')
        numPropComponents = len(propComponents)

        propSpecs = self.resizeSkeleton(numPropComponents, propSpec.children, hierarchical=False)

        for (spec, component) in zip(propSpecs, propComponents):

            componentName = component.componentName
            componentId = component.componentId
            componentSpec = component.skeleton()[0]
            componentSide = self.Side(component.componentSide)

            spec.enabled = propsEnabled
            spec.name = self.formatName(side=componentSide, name=componentName, id=componentId, kinemat='IK')
            spec.side = componentSide
            spec.type = self.Type.OTHER
            spec.otherType = f'{componentName}_IK'
            spec.driver.name = componentSpec.name
            spec.driver.namespace = namespace

        # Check if weapon IK trackers are required
        #
        weaponsEnabled = bool(self.weaponsEnabled)

        weaponSpec.name = self.formatName(name='Weapon', subname='Root', kinemat='IK')
        weaponSpec.enabled = weaponsEnabled
        weaponSpec.passthrough = True

        weaponComponents = rootComponent.findComponentDescendants('WeaponComponent')
        numWeaponComponents = len(weaponComponents)

        weaponSpecs = self.resizeSkeleton(numWeaponComponents, weaponSpec.children, hierarchical=False)

        for (spec, component) in zip(weaponSpecs, weaponComponents):

            componentName = component.componentName
            componentId = component.componentId
            componentSpec = component.skeleton()[0]
            componentSide = self.Side(component.componentSide)

            spec.enabled = weaponsEnabled
            spec.name = self.formatName(side=componentSide, name=componentName, id=componentId, kinemat='IK')
            spec.side = componentSide
            spec.type = self.Type.OTHER
            spec.otherType = f'{componentName}_IK'
            spec.driver.name = componentSpec.name
            spec.driver.namespace = namespace

            subSpecs = self.resizeSkeleton(numHandComponents, spec.children, hierarchical=False)

            for (subSpec, subComponent) in zip(subSpecs, handComponents):

                subComponentName = subComponent.componentName
                subComponentId = subComponent.componentId
                subComponentSpec = subComponent.skeleton()[0]
                subComponentSide = self.Side(subComponent.componentSide)

                subName = f'{subComponentSide.name.title()}{subComponentName}{subComponentId}'
                subSpec.enabled = weaponsEnabled
                subSpec.name = self.formatName(side=componentSide, name=componentName, id=componentId, subname=subName, kinemat='IK')
                subSpec.side = subComponentSide
                subSpec.type = self.Type.OTHER
                subSpec.otherType = f'{componentName}_{subName}_IK'
                subSpec.driver.name = subComponentSpec.name
                subSpec.driver.namespace = namespace

        # Call parent method
        #
        return super(PlayerIKComponent, self).invalidateSkeleton(skeletonSpecs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Iterate through skeleton specs
        #
        skeletonSpecs = self.skeleton(flatten=True, skipDisabled=True)

        for skeletonSpec in skeletonSpecs:

            driver = skeletonSpec.driver.getDriver()

            joint = skeletonSpec.getNode()
            joint.copyTransform(driver, skipScale=True)

            skeletonSpec.cacheNode(delete=False)
    # endregion
