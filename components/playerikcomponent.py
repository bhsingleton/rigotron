from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.dataclasses.colour import Colour
from dcc.naming import namingutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PlayerIKComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements player IK components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'PlayerIK'
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

        # Find extremity components
        #
        components = rootComponent.findComponentDescendants('ExtremityComponent')
        numComponents = len(components)

        skeletonSpecs = self.resizeSkeletonSpecs(numComponents, skeletonSpecs)

        for (skeletonSpec, component) in zip(skeletonSpecs, components):

            componentName = component.componentName
            componentId = component.componentId
            componentSide = self.Side(component.componentSide)
            componentSpecs = component.skeletonSpecs()

            skeletonSpec.name = self.formatName(side=componentSide, name=componentName, id=componentId, subname='IK')
            skeletonSpec.driver = componentSpecs[0].name

        # Call parent method
        #
        super(PlayerIKComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Iterate through skeleton specs
        #
        skeletonSpecs = self.skeletonSpecs()
        numSkeletonSpecs = len(skeletonSpecs)

        joints = [None] * numSkeletonSpecs

        for (i, skeletonSpec) in enumerate(skeletonSpecs):

            joint = self.scene.createNode('joint', name=skeletonSpec.name)
            joint.displayLocalAxis = True
            skeletonSpec.uuid = joint.uuid()

            joints[i] = joint

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
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)

        for skeletonSpec in skeletonSpecs:

            exportJoint = skeletonSpec.getNode()

            if exportJoint is not None:

                exportJoint.setParent(parentExportJoint, absolute=True)

            else:

                log.warning(f'Unable to parent "{skeletonSpec.name}" joint!')
                continue

    def unparentSkeleton(self):
        """
        Un-parents the skeleton for this component.

        :rtype: None
        """

        # Un-parent export skeleton
        #
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)

        for skeletonSpec in skeletonSpecs:

            exportJoint = skeletonSpec.getNode()

            if exportJoint is not None:

                exportJoint.setParent(None, absolute=True)

            else:

                log.warning(f'Unable to un-parent "{skeletonSpec.name}" joint!')

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Iterate through skeleton specs
        #
        skeletonSpecs = self.skeletonSpecs()

        for skeletonSpec in skeletonSpecs:

            driver = self.scene(skeletonSpec.driver)

            joint = self.scene(skeletonSpec.name)
            joint.type = driver.type
            joint.otherType = f'{driver.otherType}_IK'
            joint.copyTransform(driver)

            skeletonSpec.cacheMatrix(delete=False)
    # endregion
