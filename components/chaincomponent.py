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
    __default_component_spacing__ = 10.0
    # endregion

    # region Attributes
    numLinks = mpyattribute.MPyAttribute('numLinks', attributeType='int', min=2)
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
        numLinks = int(self.numLinks) + 1
        *chainSpecs, chainTipSpec = self.resizeSkeletonSpecs(numLinks, skeletonSpecs)

        for (i, chainSpec) in enumerate(chainSpecs, start=1):

            chainSpec.name = self.formatName(index=i)
            chainSpec.driver = self.formatName(index=i, type='control')

        chainTipSpec.name = self.formatName(name=f'{self.componentName}Tip')
        chainTipSpec.driver = self.formatName(name=f'{self.componentName}Tip', type='target')

        # Call parent method
        #
        super(ChainComponent, self).invalidateSkeletonSpecs(skeletonSpecs)

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Get skeleton specs
        #
        chainSpecs = self.skeletonSpecs()

        # Iterate through skeleton specs
        #
        numJoints = len(chainSpecs)
        chainJoints = [None] * numJoints

        for (i, chainSpec) in enumerate(chainSpecs):

            # Create joint
            #
            parent = chainJoints[i - 1] if (i > 0) else None

            chainJoint = self.scene.createNode('joint', name=chainSpec.name, parent=parent)
            chainJoint.side = self.componentSide
            chainJoint.type = self.Type.OTHER
            chainJoint.otherType = self.componentName
            chainJoint.displayLocalAxis = True
            chainSpec.uuid = chainJoint.uuid()

            chainJoints[i] = chainJoint

            # Update joint transform
            #
            defaultChainMatrix = transformutils.createTranslateMatrix([i * self.__default_component_spacing__, 0.0, 0.0])
            chainMatrix = chainSpec.getMatrix(default=defaultChainMatrix)
            chainJoint.setWorldMatrix(chainMatrix)

        return chainJoints

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

        *chainSpecs, chainTipSpec = self.skeletonSpecs()
        chainExportJoints = [self.scene(chainSpec.uuid) for chainSpec in chainSpecs]
        chainTipExportJoint = self.scene(chainTipSpec.uuid)

        componentSide = self.Side(self.componentSide)
        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create controls
        #
        numCtrls = len(chainSpecs)
        chainCtrls = [None] * numCtrls

        for (i, chainExportJoint) in enumerate(chainExportJoints):

            # Evaluate position in chain
            #
            index = i + 1
            chainCtrl = None

            if i == 0:

                chainSpaceName = self.formatName(index=index, type='space')
                chainSpace = self.scene.createNode('transform', name=chainSpaceName, parent=controlsGroup)
                chainSpace.copyTransform(chainExportJoint)
                chainSpace.freezeTransform()

                chainSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

                chainCtrlName = self.formatName(index=index, type='control')
                chainCtrl = self.scene.createNode('transform', name=chainCtrlName, parent=chainSpace)
                chainCtrl.addPointHelper('box', size=(10.0 * rigScale), side=componentSide)
                chainCtrl.prepareChannelBoxForAnimation()

                chainCtrl.userProperties['space'] = chainSpace.uuid()

            else:

                chainCtrlName = self.formatName(index=index, type='control')
                chainCtrl = self.scene.createNode('transform', name=chainCtrlName, parent=chainCtrls[i - 1])
                chainCtrl.addPointHelper('box', size=(10.0 * rigScale), side=componentSide)
                chainCtrl.copyTransform(chainExportJoint)
                chainCtrl.freezeTransform()
                chainCtrl.prepareChannelBoxForAnimation()

            # Publish control
            #
            self.publishNode(chainCtrl, alias=f'{self.componentName}{str(index).zfill(2)}')

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
