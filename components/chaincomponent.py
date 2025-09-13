from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from dcc.maya.libs import transformutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ChainComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements chain components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Chain'
    __default_component_matrix__ = om.MMatrix(
        [
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ]
    )
    __default_component_spacing__ = 10.0
    # endregion

    # region Attributes
    numLinks = mpyattribute.MPyAttribute('numLinks', attributeType='int', min=2, default=2)

    @numLinks.changed
    def numLinks(self, numLinks):
        """
        Changed method that notifies of any state changes.

        :type numLinks: bool
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Resize skeleton specs
        #
        chainSize = int(self.numLinks) + 1  # Save space for chain tip spec!
        *chainSpecs, chainTipSpec = self.resizeSkeleton(chainSize, skeletonSpecs, hierarchical=True)

        # Edit chain specs
        #
        for (i, chainSpec) in enumerate(chainSpecs, start=1):

            isFirstChainSpec = (i == 1)
            defaultMatrix = om.MMatrix(self.__default_component_matrix__) if isFirstChainSpec else transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))

            chainSpec.name = self.formatName(index=i)
            chainSpec.side = self.componentSide
            chainSpec.type = self.Type.OTHER
            chainSpec.otherType = self.componentName
            chainSpec.defaultMatrix = defaultMatrix
            chainSpec.driver.name = self.formatName(index=i, type='control')

        # Edit chain tip spec
        #
        chainTipSpec.name = self.formatName(name=f'{self.componentName}Tip')
        chainTipSpec.side = self.componentSide
        chainTipSpec.type = self.Type.OTHER
        chainTipSpec.otherType = self.componentName
        chainTipSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))
        chainTipSpec.driver.name = self.formatName(name=f'{self.componentName}Tip', type='target')

        # Call parent method
        #
        return super(ChainComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        referenceNode = self.skeletonReference()
        *chainSpecs, chainTipSpec = self.skeletonSpecs(flatten=True)
        chainExportJoints = [chainSpec.getNode(referenceNode=referenceNode) for chainSpec in chainSpecs]
        chainTipExportJoint = chainTipSpec.getNode(referenceNode=referenceNode)

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        requiresMirroring = (componentSide == self.Side.RIGHT)
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create controls
        #
        numCtrls = len(chainSpecs)
        chainCtrls = [None] * numCtrls

        for (i, chainExportJoint) in enumerate(chainExportJoints):

            # Evaluate position in chain
            #
            chainIndex = i + 1
            chainMatrix = mirrorMatrix * chainExportJoint.worldMatrix()
            chainSpace, chainCtrl = None, None

            if i == 0:

                chainSpaceName = self.formatName(index=chainIndex, type='space')
                chainSpace = self.scene.createNode('transform', name=chainSpaceName, parent=controlsGroup)
                chainSpace.setWorldMatrix(chainMatrix, skipScale=True)
                chainSpace.freezeTransform()

                chainSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

                chainCtrlName = self.formatName(index=chainIndex, type='control')
                chainCtrl = self.scene.createNode('transform', name=chainCtrlName, parent=chainSpace)
                chainCtrl.addPointHelper('box', size=(10.0 * rigScale), side=componentSide)
                chainCtrl.prepareChannelBoxForAnimation()

                chainCtrl.userProperties['space'] = chainSpace.uuid()

            else:

                chainCtrlName = self.formatName(index=chainIndex, type='control')
                chainCtrl = self.scene.createNode('transform', name=chainCtrlName, parent=chainCtrls[i - 1])
                chainCtrl.addPointHelper('box', size=(10.0 * rigScale), side=componentSide)
                chainCtrl.setWorldMatrix(chainMatrix, skipScale=True)
                chainCtrl.freezeTransform()
                chainCtrl.prepareChannelBoxForAnimation()

            # Publish control
            #
            self.publishNode(chainCtrl, alias=f'{self.componentName}{str(chainIndex).zfill(2)}')

            # Store reference to control
            #
            chainCtrls[i] = chainCtrl

        # Create tip target
        #
        firstChainCtrl, lastChainCtrl = chainCtrls[0], chainCtrls[-1]

        chainTipTargetName = self.formatName(name=f'{self.componentName}Tip', type='target')
        chainTipTarget = self.scene.createNode('transform', name=chainTipTargetName, parent=lastChainCtrl)
        chainTipTarget.displayLocalAxis = True
        chainTipTarget.visibility = False
        chainTipTarget.copyTransform(chainTipExportJoint)
        chainTipTarget.freezeTransform()

        # Reorient controller shapes
        #
        nodes = chainCtrls + [chainTipTarget]

        for (startCtrl, endCtrl) in zip(nodes[:-1], nodes[1:]):

            startCtrl.shape().reorientAndScaleToFit(endCtrl)

        # Tag controls
        #
        lastIndex = numCtrls - 1

        for (i, chainCtrl) in enumerate(chainCtrls):

            parent = chainCtrls[i - 1] if (i > 0) else parentExportCtrl
            children = [chainCtrls[i + 1]] if (i < lastIndex) else []

            chainCtrl.tagAsController(parent=parent, children=children)
    # endregion
