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
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit clavicle spec
        #
        clavicleSide = self.Side(self.componentSide)

        clavicleSpec, = self.resizeSkeleton(1, skeletonSpecs)
        clavicleSpec.name = self.formatName()
        clavicleSpec.side = clavicleSide
        clavicleSpec.type = self.Type.COLLAR
        clavicleSpec.defaultMatrix = om.MMatrix(self.__default_component_matrices__[clavicleSide])
        clavicleSpec.driver.name = self.formatName(type='control')

        # Call parent method
        #
        return super(ClavicleComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def getAttachmentTargets(self):
        """
        Returns the attachment targets for this component.
        If we're attaching to a spine component then we want to use an alternative target!

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
        attachmentSpecs = self.getAttachmentOptions()
        numAttachmentSpecs = len(attachmentSpecs)

        attachmentIndex = int(self.attachmentId)
        lastIndex = numAttachmentSpecs - 1

        if attachmentIndex == lastIndex:

            attachmentSpec = attachmentSpecs[attachmentIndex]
            exportJoint = attachmentSpec.getNode(referenceNode=self.skeletonReference())
            exportDriver = self.scene(componentParent.userProperties['spineTipIKTarget'])

            return exportJoint, exportDriver

        elif 0 <= attachmentIndex < numAttachmentSpecs:

            attachmentSpec = attachmentSpecs[attachmentIndex]
            exportJoint = attachmentSpec.getNode(referenceNode=self.skeletonReference())
            exportDriver = attachmentSpec.driver.getDriver()

            return exportJoint, exportDriver

        else:

            return None, None

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        clavicleSpec, = self.skeleton()
        clavicleExportJoint = self.scene(clavicleSpec.name)
        clavicleExportMatrix = clavicleExportJoint.worldMatrix()

        componentSide = self.Side(self.componentSide)
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        mirrorMatrix = self.__default_mirror_matrices__[componentSide]
        requiresMirroring = componentSide == Side.RIGHT
        mirrorSign = -1.0 if requiresMirroring else 1.0

        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create clavicle control
        #
        clavicleMatrix = mirrorMatrix * clavicleExportMatrix

        clavicleSpaceName = self.formatName(type='space')
        clavicleSpace = self.scene.createNode('transform', name=clavicleSpaceName, parent=controlsGroup)
        clavicleSpace.setWorldMatrix(clavicleMatrix, skipScal=True)
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
