from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.dataclasses.colour import Colour
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BeltComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements belt components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Belt'
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 120.0, 1.0)
        ]
    )
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit skeleton specs
        #
        beltSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        beltSpec.name = self.formatName()
        beltSpec.side = self.componentSide
        beltSpec.type = self.Type.OTHER
        beltSpec.otherType = self.componentName
        beltSpec.defaultMatrix = om.MMatrix(self.__default_component_matrix__)
        beltSpec.driver.name = self.formatName(type='control')

        # Call parent method
        #
        return super(BeltComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        referenceNode = self.skeletonReference()
        beltSpec, = self.skeletonSpecs()
        beltExportJoint = beltSpec.getNode(referenceNode=referenceNode)
        beltExportMatrix = beltExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(0.663, 0.0, 1.0)
        rigScale = self.findControlRig().getRigScale()

        # Find spine component
        #
        spineComponents = self.findComponentAncestors('SpineComponent')
        numSpineComponents = len(spineComponents)

        if numSpineComponents == 0:

            raise NotImplementedError('buildRig() spineless belt components have not been implemented!')

        # Create belt control
        #
        spineComponent = spineComponents[0]
        hipsCtrl = spineComponent.getPublishedNode('Hips')
        firstSpineCtrl = spineComponent.getPublishedNode('Spine01_FK_Rot')

        beltSpaceName = self.formatName(type='space')
        beltSpace = self.scene.createNode('transform', name=beltSpaceName, parent=controlsGroup)
        beltSpace.setWorldMatrix(beltExportMatrix, skipScale=True)
        beltSpace.freezeTransform()

        beltCtrl = self.scene.createNode('transform', name=beltSpec.driver, parent=beltSpace)
        beltCtrl.addPointHelper('cylinder', size=(25.0 * rigScale), localScale=(0.25, 1.0, 1.5), colorRGB=colorRGB)
        beltCtrl.prepareChannelBoxForAnimation()
        beltCtrl.tagAsController()
        self.publishNode(beltCtrl, alias=self.componentName)

        beltCtrl.userProperties['space'] = beltSpace.uuid()

        # Setup constraints
        #
        pointConstraint = beltSpace.addConstraint('pointConstraint', [hipsCtrl, firstSpineCtrl])
        hipsTarget, spineTarget = pointConstraint.targets()
        hipsTarget.setWeight(0.5)
        spineTarget.setWeight(0.5)
        pointConstraint.maintainOffset()

        orientConstraint = beltSpace.addConstraint('orientConstraint', [hipsCtrl, firstSpineCtrl])
        hipsTarget, spineTarget = orientConstraint.targets()
        hipsTarget.setWeight(0.65)
        spineTarget.setWeight(0.35)
        orientConstraint.maintainOffset()

        scaleConstraint = beltSpace.addConstraint('scaleConstraint', [hipsCtrl, firstSpineCtrl])
        hipsTarget, spineTarget = scaleConstraint.targets()
        hipsTarget.setWeight(0.5)
        spineTarget.setWeight(0.5)
    # endregion
