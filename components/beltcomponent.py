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
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Edit skeleton specs
        #
        beltSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)
        beltSpec.name = self.formatName()
        beltSpec.driver = self.formatName(type='control')

        # Call parent method
        #
        super(BeltComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        beltSpec, = self.skeletonSpecs()

        # Create joint
        #
        beltJoint = self.scene.createNode('joint', name=beltSpec.name)
        beltJoint.side = self.componentSide
        beltJoint.type = self.Type.OTHER
        beltJoint.otherType = self.componentName
        beltJoint.displayLocalAxis = True
        beltSpec.uuid = beltJoint.uuid()

        # Update joint transform
        #
        beltMatrix = beltSpec.getMatrix(default=self.__default_component_matrix__)
        beltJoint.setWorldMatrix(beltMatrix)

        return (beltJoint,)

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

        beltSpec, = self.skeletonSpecs()
        beltExportJoint = self.scene(beltSpec.uuid)

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
        beltSpace.copyTransform(beltExportJoint)
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
