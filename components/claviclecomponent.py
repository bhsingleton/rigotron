from maya.api import OpenMaya as om
from rigomatic.libs import kinematicutils
from . import basecomponent
from ..libs import Side

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ClavicleComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements clavicle components.
    """

    # region Dunderscores
    __default_component_name__ = 'Clavicle'
    __default_component_matrices__ = {
        Side.LEFT: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (5.0, 0.0, 160.0, 1.0)
            ]
        ),
        Side.RIGHT: om.MMatrix(
            [
                (-1.0, 0.0, 0.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (-5.0, 0.0, 160.0, 1.0)
            ]
        )
    }
    __default_mirror_matrices__ = {
        Side.LEFT: om.MMatrix.kIdentity,
        Side.RIGHT: om.MMatrix(
            [
                (-1.0, 0.0, 0.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )
    }
    # endregion

    # region Methods
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[Dict[str, Any]]
        :rtype: None
        """

        # Resize skeleton specs
        #
        clavicleSpec, = self.resizeSkeletonSpecs(1, skeletonSpecs)

        # Edit clavicle spec
        #
        clavicleSpec.name = self.formatName()
        clavicleSpec.driver = self.formatName(type='control')

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: List[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        side = self.Side(self.componentSide)
        clavicleSpec, = self.skeletonSpecs()

        # Create foot joint
        #
        clavicleJoint = self.scene.createNode('joint', name=clavicleSpec.name)
        clavicleJoint.side = side
        clavicleJoint.type = self.Type.COLLAR
        clavicleJoint.displayLocalAxis = True
        clavicleSpec.uuid = clavicleJoint.uuid()

        clavicleMatrix = clavicleSpec.getMatrix(default=self.__default_component_matrices__[side])
        clavicleJoint.setWorldMatrix(clavicleMatrix)

        return (clavicleJoint,)

    def getAttachmentTargets(self):
        """
        Returns the attachment targets for this component.
        If we're attaching to a spine component then we wanna use a different target!

        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
        """

        # Evaluate component parent
        #
        componentParent = self.componentParent()
        isSpineComponent = componentParent.className.endswith('SpineComponent')

        if not isSpineComponent:

            return super(ClavicleComponent, self).getAttachmentTargets()

        # Evaluate attachment position
        #
        skeletonSpecs = self.getAttachmentOptions()
        numSkeletonSpecs = len(skeletonSpecs)

        attachmentIndex = int(self.attachmentId)
        lastIndex = numSkeletonSpecs - 1

        if attachmentIndex == lastIndex:

            skeletonSpec = skeletonSpecs[attachmentIndex]
            return self.scene(skeletonSpec.uuid), self.scene(componentParent.userProperties['spineTipIKTarget'])

        elif 0 <= attachmentIndex < numSkeletonSpecs:

            skeletonSpec = skeletonSpecs[attachmentIndex]
            return self.scene(skeletonSpec.uuid), self.scene(skeletonSpec.driver)

        else:

            return None, None

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        clavicleSpec, = self.skeletonSpecs()
        clavicleExportJoint = self.scene(clavicleSpec.name)
        clavicleMatrix = clavicleExportJoint.worldMatrix()

        componentSide = self.Side(self.componentSide)
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create clavicle control
        #
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]
        requiresMirroring = componentSide == Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0

        clavicleSpaceName = self.formatName(type='space')
        clavicleSpace = self.scene.createNode('transform', name=clavicleSpaceName, parent=controlsGroup)
        clavicleSpace.setWorldMatrix(mirrorMatrix * clavicleMatrix)
        clavicleSpace.freezeTransform()
        clavicleSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        clavicleCtrlName = self.formatName(type='control')
        clavicleCtrl = self.scene.createNode('transform', name=clavicleCtrlName, parent=clavicleSpace)
        clavicleCtrl.addShape('LollipopCurve', size=(30.0 * rigScale), localRotate=(45.0 * mirrorSign, 0.0, 90.0 * mirrorSign), side=componentSide, lineWidth=4.0)
        clavicleCtrl.prepareChannelBoxForAnimation()
        clavicleCtrl.tagAsController()
        self.publishNode(clavicleCtrl, alias='Clavicle')

        clavicleCtrl.userProperties['space'] = clavicleSpace.uuid()
    # endregion
