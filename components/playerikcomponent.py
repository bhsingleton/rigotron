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
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Find root component
        #
        rootComponent = self.findRootComponent()

        if rootComponent is None:

            return

        # Resize specs
        #
        specCount = len(PlayerIKType)
        footSpec, handSpec, propSpec, weaponSpec = self.resizeSkeletonSpecs(specCount, skeletonSpecs)

        # Check if feet IK trackers are required
        #
        footSpec.name = self.formatName(name='Foot', subname='Root', kinemat='IK')
        footSpec.enabled = False

        footComponents = rootComponent.findComponentDescendants('FootComponent')
        numFootComponents = len(footComponents)

        feetEnabled = bool(self.feetEnabled)

        if feetEnabled and numFootComponents > 0:

            footSpecs = self.resizeSkeletonSpecs(numFootComponents, footSpec.children)

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
        handSpec.name = self.formatName(name='Hand', subname='Root', kinemat='IK')
        handSpec.enabled = False

        handComponents = rootComponent.findComponentDescendants('HandComponent')
        numHandComponents = len(handComponents)

        handsEnabled = bool(self.feetEnabled)

        if handsEnabled and numHandComponents > 0:

            handSpecs = self.resizeSkeletonSpecs(numHandComponents, handSpec.children)

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
        propSpec.name = self.formatName(name='Prop', subname='Root', kinemat='IK')
        propSpec.enabled = False

        propComponents = rootComponent.findComponentDescendants('RootComponent')
        numPropComponents = len(propComponents)

        propsEnabled = bool(self.propsEnabled)

        if propsEnabled and numPropComponents > 0:

            propSpecs = self.resizeSkeletonSpecs(numPropComponents, propSpec.children)

            for (spec, component) in zip(propSpecs, propComponents):

                propName = component.componentName
                propId = component.componentId
                propSide = self.Side(component.componentSide)
                propDriver = component.skeletonSpecs()[0].name

                spec.name = self.formatName(side=propSide, name=propName, id=propId, kinemat='IK')
                spec.driver = propDriver
                spec.enabled = handsEnabled

        # Check if weapon IK trackers are required
        #
        weaponSpec.name = self.formatName(name='Weapon', subname='Root', kinemat='IK')
        weaponSpec.enabled = False

        weaponComponents = rootComponent.findComponentDescendants('WeaponComponent')
        numWeaponComponents = len(weaponComponents)

        weaponsEnabled = bool(self.weaponsEnabled)

        if weaponsEnabled and numWeaponComponents > 0:

            weaponSpecs = self.resizeSkeletonSpecs(numWeaponComponents, weaponSpec.children)

            for (spec, component) in zip(weaponSpecs, weaponComponents):

                weaponName = component.componentName
                weaponId = component.componentId
                weaponSide = self.Side(component.componentSide)
                weaponDriver = component.skeletonSpecs()[0].name

                spec.name = self.formatName(side=weaponSide, name=weaponName, id=weaponId, kinemat='IK')
                spec.driver = weaponDriver
                spec.enabled = weaponsEnabled

                subspecs = self.resizeSkeletonSpecs(numHandComponents, spec.children)

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
        super(PlayerIKComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

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
