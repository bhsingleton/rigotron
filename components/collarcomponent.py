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
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit skeleton specs
        #
        collarSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        collarSpec.name = self.formatName()
        collarSpec.side = self.componentSide
        collarSpec.type = self.Type.OTHER
        collarSpec.otherType = self.componentName
        collarSpec.defaultMatrix = om.MMatrix(self.__default_component_matrix__)
        collarSpec.driver.name = self.formatName(type='control')

        # Call parent method
        #
        return super(CollarComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        collarSpec, = self.skeleton()
        collarExportJoint = collarSpec.getNode()
        collarExportMatrix = collarExportJoint.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(0.663, 0.0, 1.0)
        rigScale = self.findControlRig().getRigScale()

        # Create collar control
        #
        collarSpaceName = self.formatName(type='space')
        collarSpace = self.scene.createNode('transform', name=collarSpaceName, parent=controlsGroup)
        collarSpace.setWorldMatrix(collarExportMatrix, skipScale=True)
        collarSpace.freezeTransform()

        collarGroupName = self.formatName(type='transform')
        collarGroup = self.scene.createNode('transform', name=collarGroupName, parent=collarSpace)

        collarCtrlName = self.formatName(type='control')
        collarCtrl = self.scene.createNode('transform', name=collarCtrlName, parent=collarGroup)
        collarCtrl.addStar(20.0 * rigScale, outerRadius=1.0, innerRadius=1.0, numPoints=6, localScale=(1.0, 1.0, 1.5), colorRGB=colorRGB)
        collarCtrl.prepareChannelBoxForAnimation()
        collarCtrl.tagAsController()
        self.publishNode(collarCtrl, alias=self.componentName)

        collarCtrl.userProperties['space'] = collarSpace.uuid()
        collarCtrl.userProperties['group'] = collarGroup.uuid()

    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.

        :rtype: None
        """

        # Check if spine and head components exist
        #
        spineComponents = self.findComponentAncestors('SpineComponent')
        spineExists = len(spineComponents) == 1

        headComponents = spineComponents[0].findComponentDescendants('HeadComponent') if spineExists else []
        headExists = len(headComponents) == 1

        collarCtrl = self.getPublishedNode(self.componentName)
        collarSpace = self.scene(collarCtrl.userProperties['space'])
        collarGroup = self.scene(collarCtrl.userProperties['group'])

        if spineExists and headExists:

            # Decompose components
            #
            spineComponent, headComponent = spineComponents[0], headComponents[0]
            neckCtrl = headComponent.getPublishedNode('Neck01') if (headComponent.numNeckLinks > 1) else headComponent.getPublishedNode('Neck')
            headCtrl = headComponent.getPublishedNode('Head')
            chestCtrl = spineComponent.getPublishedNode('Chest')

            # Constrain collar control
            #
            collarSpace.addConstraint('transformConstraint', [neckCtrl], skipRotate=True, maintainOffset=True)

            orientConstraint = collarSpace.addConstraint('orientConstraint', [chestCtrl, neckCtrl, headCtrl], skipTranslate=True, skipScale=True)
            chestTarget, neckTarget, headTarget = orientConstraint.targets()
            chestTarget.setWeight(0.23)
            neckTarget.setWeight(0.64)
            headTarget.setWeight(0.13)
            orientConstraint.maintainOffset()

            # Add twist attribute to collar control
            #
            collarCtrl.addDivider('Settings')
            collarCtrl.addAttr(longName='inheritsTwist', attributeType='angle', min=0.0, max=1.0, keyable=True)

            # Setup twist solver
            #
            twistSolverName = self.formatName(subname='Twist', type='twistSolver')
            twistSolver = self.scene.createNode('twistSolver', name=twistSolverName)
            twistSolver.forwardAxis = 0  # X
            twistSolver.upAxis = 2  # Z
            twistSolver.inverse = True
            twistSolver.connectPlugs(chestCtrl[f'worldMatrix[{chestCtrl.instanceNumber()}]'], 'startMatrix')
            twistSolver.connectPlugs(collarSpace[f'worldMatrix[{collarSpace.instanceNumber()}]'], 'endMatrix')

            twistReverseName = self.formatName(subname='TwistReverse', type='floatMath')
            twistReverse = self.scene.createNode('floatMath', name=twistReverseName)
            twistReverse.operation = 1  # Subtract
            twistReverse.setAttr('inAngleA', 1.0)
            twistReverse.connectPlugs(collarCtrl['inheritsTwist'], 'inAngleB')

            twistEnvelopeName = self.formatName(subname='TwistEnvelope', type='floatMath')
            twistEnvelope = self.scene.createNode('floatMath', name=twistEnvelopeName)
            twistEnvelope.operation = 2  # Multiply
            twistEnvelope.connectPlugs(twistSolver['roll'], 'inAngleA')
            twistEnvelope.connectPlugs(twistReverse['outAngle'], 'inAngleB')
            twistEnvelope.connectPlugs('outAngle', collarGroup['rotateX'])

            self.organizeNodes(twistSolver, twistReverse, twistEnvelope)

        else:

            # Constrain collar control
            #
            parentExportJoint, parentExportCtrl = self.getAttachmentTargets()
            collarSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)
    # endregion
