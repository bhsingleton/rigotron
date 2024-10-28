from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.dataclasses.colour import Colour
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CollarComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements collar components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Collar'
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 200.0, 1.0)
        ]
    )
    # endregion

    # region Methods
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Edit skeleton specs
        #
        collarSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        collarSpec.name = self.formatName()
        collarSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(CollarComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        collarSpec, = self.skeletonSpecs()

        # Create joint
        #
        collarJoint = self.scene.createNode('joint', name=collarSpec.name)
        collarJoint.side = self.componentSide
        collarJoint.type = self.Type.OTHER
        collarJoint.otherType = self.componentName
        collarJoint.displayLocalAxis = True
        collarSpec.uuid = collarJoint.uuid()

        # Update joint transform
        #
        collarMatrix = collarSpec.getMatrix(default=self.__default_component_matrix__)
        collarJoint.setWorldMatrix(collarMatrix)

        return (collarJoint,)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        collarSpec, = self.skeletonSpecs()
        collarExportJoint = self.scene(collarSpec.uuid)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(0.663, 0.0, 1.0)
        rigScale = self.findControlRig().getRigScale()

        # Create collar control
        #
        collarSpaceName = self.formatName(type='space')
        collarSpace = self.scene.createNode('transform', name=collarSpaceName, parent=controlsGroup)
        collarSpace.copyTransform(collarExportJoint)
        collarSpace.freezeTransform()

        collarCtrl = self.scene.createNode('transform', name=collarSpec.driver, parent=collarSpace)
        collarCtrl.addStar(20.0 * rigScale, outerRadius=1.0, innerRadius=1.0, numPoints=6, localScale=(1.0, 1.0, 1.5), colorRGB=colorRGB)
        collarCtrl.prepareChannelBoxForAnimation()
        collarCtrl.tagAsController()
        self.publishNode(collarCtrl, alias=self.componentName)

        collarCtrl.userProperties['space'] = collarSpace.uuid()

    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.

        :rtype: None
        """

        # Find spine component
        #
        spineComponents = self.findComponentAncestors('SpineComponent')
        numSpineComponents = len(spineComponents)

        if numSpineComponents == 0:

            raise NotImplementedError('buildRig() spineless collar components have not been implemented!')

        # Find head component
        #
        spineComponent = spineComponents[0]
        headComponents = spineComponent.findComponentDescendants('HeadComponent')

        numHeadComponents = len(headComponents)

        if numHeadComponents == 0:

            raise NotImplementedError('buildRig() headless collar components have not been implemented!')

        # Constrain collar control
        #
        headComponent = headComponents[0]
        neckCtrl = headComponent.getPublishedNode('Neck')
        headCtrl = headComponent.getPublishedNode('Head')
        chestCtrl = spineComponent.getPublishedNode('Chest')

        collarCtrl = self.getPublishedNode(self.componentName)
        collarSpace = self.scene(collarCtrl.userProperties['space'])
        collarSpace.addConstraint('transformConstraint', [neckCtrl], skipRotate=True, maintainOffset=True)

        orientConstraint = collarSpace.addConstraint('orientConstraint', [chestCtrl, neckCtrl, headCtrl], skipTranslate=True, skipScale=True)
        chestTarget, neckTarget, headTarget = orientConstraint.targets()
        chestTarget.setWeight(0.23)
        neckTarget.setWeight(0.64)
        headTarget.setWeight(0.13)
        orientConstraint.maintainOffset()
    # endregion
