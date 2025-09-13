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
        # Without it we can't traverse the component tree for the required components!
        #
        rootComponent = self.findRootComponent()

        if rootComponent is None:

            return

        # Resize skeleton specs
        #
        specCount = len(self.PlayerIKType)
        footSpec, handSpec, propSpec, weaponSpec = self.resizeSkeleton(specCount, skeletonSpecs, hierarchical=False)

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

            footName = component.componentName
            footId = component.componentId
            footSide = self.Side(component.componentSide)
            footDriver = component.skeletonSpecs()[0].name

            spec.name = self.formatName(side=footSide, name=footName, id=footId, kinemat='IK')
            spec.driver = footDriver
            spec.enabled = feetEnabled

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

            handName = component.componentName
            handId = component.componentId
            handSide = self.Side(component.componentSide)
            handDriver = component.skeletonSpecs()[0].name

            spec.name = self.formatName(side=handSide, name=handName, id=handId, kinemat='IK')
            spec.driver = handDriver
            spec.enabled = handsEnabled

        # Check if prop IK trackers are required
        #
        propsEnabled = bool(self.propsEnabled)

        propSpec.name = self.formatName(name='Prop', subname='Root', kinemat='IK')
        propSpec.enabled = propsEnabled
        propSpec.passthrough = True

        propComponents = rootComponent.findComponentDescendants('RootComponent')
        numPropComponents = len(propComponents)

        propSpecs = self.resizeSkeleton(numPropComponents, propSpec.children, hierarchical=False)

        for (spec, component) in zip(propSpecs, propComponents):

            propName = component.componentName
            propId = component.componentId
            propSide = self.Side(component.componentSide)
            propDriver = component.skeletonSpecs()[0].name

            spec.name = self.formatName(side=propSide, name=propName, id=propId, kinemat='IK')
            spec.driver = propDriver
            spec.enabled = propsEnabled

        # Check if weapon IK trackers are required
        #
        weaponsEnabled = bool(self.weaponsEnabled)

        weaponSpec.name = self.formatName(name='Weapon', subname='Root', kinemat='IK')
        weaponSpec.enabled = weaponsEnabled
        propSpec.passthrough = True

        weaponComponents = rootComponent.findComponentDescendants('WeaponComponent')
        numWeaponComponents = len(weaponComponents)

        weaponSpecs = self.resizeSkeleton(numWeaponComponents, weaponSpec.children, hierarchical=False)

        for (spec, component) in zip(weaponSpecs, weaponComponents):

            weaponName = component.componentName
            weaponId = component.componentId
            weaponSide = self.Side(component.componentSide)
            weaponDriver = component.skeletonSpecs()[0].name

            spec.name = self.formatName(side=weaponSide, name=weaponName, id=weaponId, kinemat='IK')
            spec.driver = weaponDriver
            spec.enabled = weaponsEnabled

            subspecs = self.resizeSkeleton(numHandComponents, spec.children, hierarchical=False)

            for (subspec, subcomponent) in zip(subspecs, handComponents):

                handName = subcomponent.componentName
                handId = subcomponent.componentId
                handSide = self.Side(subcomponent.componentSide)
                handDriver = subcomponent.skeletonSpecs()[0].name

                subname = f'{handSide.name.title()}{handName}{handId}'
                subspec.name = self.formatName(side=weaponSide, name=weaponName, id=weaponId, subname=subname, kinemat='IK')
                subspec.driver = handDriver
                subspec.enabled = weaponsEnabled

        # Call parent method
        #
        return super(PlayerIKComponent, self).invalidateSkeleton(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Decompose skeleton specs
        #
        footSpec, handSpec, propSpec, weaponSpec = self.skeletonSpecs()

        # Check if feet are enabled
        #
        hasFootSpecs = len(footSpec.children) > 0
        feetEnabled = footSpec.children[0].enabled if hasFootSpecs else False

        joints = []

        if feetEnabled:

            for (i, spec) in enumerate(footSpec.children):

                joint = self.scene.createNode('joint', name=spec.name)
                joint.displayLocalAxis = True
                spec.uuid = joint.uuid()

                joints.append(joint)

        # Check if hands are enabled
        #
        hasHandSpecs = len(handSpec.children) > 0
        handsEnabled = handSpec.children[0].enabled if hasHandSpecs else False

        if handsEnabled:

            for (i, spec) in enumerate(handSpec.children):

                joint = self.scene.createNode('joint', name=spec.name)
                joint.displayLocalAxis = True
                spec.uuid = joint.uuid()

                joints.append(joint)

        # Check if props are enabled
        #
        hasPropSpecs = len(propSpec.children) > 0
        propsEnabled = propSpec.children[0].enabled if hasPropSpecs else False

        if propsEnabled:

            for (i, spec) in enumerate(propSpec.children):

                joint = self.scene.createNode('joint', name=spec.name)
                joint.displayLocalAxis = True
                spec.uuid = joint.uuid()

                joints.append(joint)

        # Check if weapons are enabled
        #
        hasWeaponSpecs = len(weaponSpec.children) > 0
        weaponsEnabled = weaponSpec.children[0].enabled if hasWeaponSpecs else False

        if weaponsEnabled:

            for (i, spec) in enumerate(weaponSpec.children):

                joint = self.scene.createNode('joint', name=spec.name)
                joint.displayLocalAxis = True
                spec.uuid = joint.uuid()

                joints.append(joint)

                for (j, subspec) in enumerate(spec.children):

                    subjoint = self.scene.createNode('joint', name=subspec.name, parent=joint)
                    subjoint.displayLocalAxis = True
                    subspec.uuid = subjoint.uuid()

                    joints.append(subjoint)

        return joints

    def parentSkeleton(self):
        """
        Parents the skeleton for this component.

        :rtype: None
        """

        # Check if attachment target exists
        #
        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        if parentExportJoint is None:

            return

        # Re-parent export skeleton
        #
        skeletonSpecs = self.skeletonSpecs()

        for skeletonSpec in skeletonSpecs:

            # Check if top-level spec is enabled
            #
            hasChildren = len(skeletonSpec.children)
            isEnabled = skeletonSpec.children[0].enabled if hasChildren else False

            if not isEnabled:

                continue

            # Iterate through child specs
            #
            for childSpec in skeletonSpec.children:

                exportJoint = childSpec.getNode()

                if exportJoint is not None:

                    exportJoint.setParent(parentExportJoint, absolute=True)

                else:

                    log.warning(f'Unable to parent "{childSpec.name}" joint!')
                    continue

    def unparentSkeleton(self):
        """
        Un-parents the skeleton for this component.

        :rtype: None
        """

        # Un-parent export skeleton
        #
        skeletonSpecs = self.skeletonSpecs()

        for skeletonSpec in skeletonSpecs:

            # Check if top-level spec is enabled
            #
            hasChildren = len(skeletonSpec.children)
            isEnabled = skeletonSpec.children[0].enabled if hasChildren else False

            if not isEnabled:

                continue

            # Iterate through child specs
            #
            for childSpec in skeletonSpec.children:

                exportJoint = childSpec.getNode()

                if exportJoint is not None:

                    exportJoint.setParent(None, absolute=True)

                else:

                    log.warning(f'Unable to un-parent "{childSpec.name}" joint!')

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Iterate through skeleton specs
        #
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)

        for skeletonSpec in skeletonSpecs:

            driver = self.scene(skeletonSpec.driver)

            joint = self.scene(skeletonSpec.name)
            joint.type = driver.type
            joint.otherType = f'{driver.otherType}_IK'
            joint.copyTransform(driver, skipScale=True)

            skeletonSpec.cacheMatrix(delete=False)
    # endregion
