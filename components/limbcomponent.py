from maya.api import OpenMaya as om
from mpy import mpyattribute
from abc import abstractmethod
from dcc.python import stringutils
from dcc.maya.libs import transformutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LimbComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that outlines limb components.
    """

    # region Dunderscores
    __default_component_name__ = 'Limb'
    # endregion

    # region Attributes
    twistEnabled = mpyattribute.MPyAttribute('twistEnabled', attributeType='bool', default=True)
    numTwistLinks = mpyattribute.MPyAttribute('numTwistLinks', attributeType='int', min=2, default=3)

    @twistEnabled.changed
    def twistEnabled(self, twistEnabled):
        """
        Changed method that notifies any twist state changes.

        :type twistEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numTwistLinks.changed
    def numTwistLinks(self, numTwistLinks):
        """
        Changed method that notifies any twist link size changes.

        :type numTwistLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()

    @basecomponent.BaseComponent.componentChildren.changed
    def componentChildren(self, componentChildren):
        """
        Changed method that notifies any component children changes.

        :type componentChildren: List[om.MObject]
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def connectExtremityToTwistSpaceSwitch(self, extremityComponent):
        """
        Adds the supplied extremity control to the limb's pole space switch.

        :type extremityComponent: rigotron.components.extremitycomponent.ExtremityComponent
        :rtype: None
        """

        # Check if hinge control exists
        #
        hingeCtrls = list(filter(None, map(self.scene.__call__, self.userProperties.get('hingeControls', []))))
        hasHingeCtrls = len(hingeCtrls) > 0

        if not hasHingeCtrls:

            return

        # Check if other limb handles exist
        #
        hingeCtrl = hingeCtrls[-1]
        otherHandles = hingeCtrl.userProperties.get('otherHandles', [])

        hasOtherHandles = len(otherHandles) > 0

        if not hasOtherHandles:

            return

        # Check if handle space switch is up-to-date
        #
        extremitySpec = extremityComponent.skeletonSpecs()[0]
        extremityCtrl = self.scene(extremitySpec.driver)

        handleCtrl = self.scene(otherHandles[-1])
        handleNegate = self.scene(handleCtrl.userProperties['negate'])

        spaceSwitch = self.scene(handleCtrl.userProperties['spaceSwitch'])
        targets = spaceSwitch.targets()
        targetName = extremityCtrl.name()

        found = [target for target in targets if target.name() == targetName]
        exists = len(found) == 1

        index = None

        if exists:

            index = found[0].index

        else:

            index = spaceSwitch.addTarget(extremityCtrl, maintainOffset=False)

        # Update space switch
        #
        spaceSwitch.setAttr(f'target[{index}]', {'targetWeight': (0.0, 0.0, 0.0)})
        spaceSwitch.connectPlugs(handleCtrl['localOrGlobal'], f'target[{index}].targetWeight', force=True)
        spaceSwitch.connectPlugs(handleNegate['outDistance'], f'target[{index}].targetOffsetTranslateX', force=True)

    def connectExtremityToTwistSolver(self, extremityComponent):
        """
        Adds the supplied extremity control to the limb's end twist solver.

        :type extremityComponent: rigotron.components.extremitycomponent.ExtremityComponent
        :rtype: None
        """

        # Check if twist solvers exist
        #
        twistSolvers = list(filter(None, map(self.scene.__call__, self.userProperties.get('twistSolvers', []))))
        hasTwistSolvers = len(twistSolvers) > 0

        if not hasTwistSolvers:

            return

        # Calculate offset matrix
        #
        limbSpec = self.skeletonSpecs()[-2]
        limbJoint = self.scene(limbSpec.uuid)
        limbMatrix = limbJoint.worldMatrix()

        extremitySpec = extremityComponent.skeletonSpecs()[0]
        extremityJoint = self.scene(extremitySpec.uuid)
        extremityCtrl = self.scene(extremitySpec.driver)
        extremityMatrix = extremityJoint.worldMatrix()

        snappedExtremityMatrix = transformutils.alignMatrixToNearestAxes(limbMatrix, extremityMatrix)
        offsetMatrix = snappedExtremityMatrix * extremityCtrl.worldInverseMatrix()

        # Update twist solver connections
        #
        twistSolver = self.scene(twistSolvers[-1])
        twistSolver.endOffsetMatrix = transformutils.createRotationMatrix(offsetMatrix)
        twistSolver.connectPlugs(extremityCtrl[f'worldMatrix[{extremityCtrl.instanceNumber()}]'], 'endMatrix', force=True)

    def connectExtremityToScaleRemapper(self, extremityComponent):
        """
        Adds the supplied extremity control to the limb's scale remapper.

        :type extremityComponent: rigotron.component.extremity.ExtremityComponent
        :rtype: None
        """

        # Check if scale remappers exist
        #
        scaleRemappers = list(filter(None, map(self.scene.__call__, self.userProperties.get('scaleRemappers', []))))
        numScaleRemappers = len(scaleRemappers)

        if numScaleRemappers == 0:

            log.warning('No scale remappers exist!')
            return

        # Check if decompose matrix already exists
        #
        scaleRemapper = self.scene(scaleRemappers[-1])
        sourceNode = self.scene(scaleRemapper['outputMax'].node())
        hasDecomposeMatrix = sourceNode.hasFn(om.MFn.kDecomposeMatrix)

        extremitySpec = extremityComponent.skeletonSpecs()[0]
        extremityCtrl = self.scene(extremitySpec.driver)
        limbIKCtrl = self.scene(self.userProperties['ikControls'][-1])

        if hasDecomposeMatrix:

            decomposeMatrix = sourceNode

            multMatrix = self.scene(decomposeMatrix['inputMatrix'])
            multMatrix.connectPlugs(extremityCtrl['worldMatrix[0]'], 'matrixIn[0]', force=True)
            multMatrix.connectPlugs(limbIKCtrl['parentInverseMatrix[0]'], 'matrixIn[1]', force=True)

        else:

            multMatrixName = self.formatName(subname='Scale', type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(extremityCtrl['worldMatrix[0]'], 'matrixIn[0]')
            multMatrix.connectPlugs(limbIKCtrl['parentInverseMatrix[0]'], 'matrixIn[1]')

            decomposeMatrixName = self.formatName(subname='Scale', type='decomposeMatrix')
            decomposeMatrix = self.scene.createNode('decomposeMatrix', name=decomposeMatrixName)
            decomposeMatrix.connectPlugs(extremityCtrl['rotateOrder'], 'inputRotateOrder')
            decomposeMatrix.connectPlugs(multMatrix['matrixSum'], 'inputMatrix')

            scaleRemapper.connectPlugs(decomposeMatrix['outputScale'], 'outputMax', force=True)

    def connectExtremityToIKHandle(self, extremityComponent):
        """
        Adds the supplied extremity control to the limb's IK softener.

        :type extremityComponent: rigotron.component.extremity.ExtremityComponent
        :rtype: None
        """

        extremityIKTarget = self.scene(extremityComponent.userProperties['ikTarget'])
        usesIKEmulator = 'ikEmulator' in self.userProperties
        usesIKSoftener = 'ikSoftener' in self.userProperties

        if usesIKEmulator:

            usesReverseIK = 'rikEmulator' in self.userProperties
            limbIKEmulator = self.scene(self.userProperties['rikEmulator']) if usesReverseIK else self.scene(self.userProperties['ikEmulator'])

            limbIKEmulator.connectPlugs(extremityIKTarget[f'worldMatrix[{extremityIKTarget.instanceNumber()}]'], 'goal', force=True)

        elif usesIKSoftener:

            usesReverseIK = 'rikSoftener' in self.userProperties
            limbIKSoftener = self.scene(self.userProperties['rikSoftener']) if usesReverseIK else self.scene(self.userProperties['ikSoftener'])

            limbIKSoftener.connectPlugs(extremityIKTarget[f'worldMatrix[{extremityIKTarget.instanceNumber()}]'], 'endMatrix', force=True)

        else:

            raise TypeError('connectExtremityToIKHandle() unable to override IK system!')

    def attachExtremityComponent(self, extremityComponent):
        """
        Attaches the supplied extremity component to this limb.

        :type extremityComponent: rigotron.component.extremity.ExtremityComponent
        :rtype: None
        """

        self.connectExtremityToTwistSpaceSwitch(extremityComponent)
        self.connectExtremityToTwistSolver(extremityComponent)
        self.connectExtremityToScaleRemapper(extremityComponent)
        self.connectExtremityToIKHandle(extremityComponent)

    def findExtremityComponent(self):
        """
        Returns the extremity component related to this limb component.

        :rtype: Union[rigotron.components.extremitycomponent.ExtremityComponent, None]
        """

        components = self.findComponentDescendants('ExtremityComponent')
        numComponents = len(components)

        if numComponents == 0:

            return None

        elif numComponents == 1:

            return components[0]

        else:

            raise TypeError(f'findExtremityComponent() expects 1 extremity component ({numComponents} found)!')

    def hasExtremityComponent(self):
        """
        Evaluates if this limb component has an extremity component.

        :rtype: bool
        """

        return self.findExtremityComponent() is not None

    def extremityMatrix(self):
        """
        Returns theextremity matrix for this component.

        :rtype: om.MMatrix
        """

        component = self.findExtremityComponent()

        if component is not None:

            return component.effectorMatrix()

        else:

            return self.scene(self.skeletonSpecs()[-1].uuid).worldMatrix()

    def effectorMatrix(self):
        """
        Returns the preferred effector matrix for this component.

        :rtype: om.MMatrix
        """

        component = self.findExtremityComponent()

        if component is not None:

            return component.preferredEffectorMatrix()

        else:

            return self.scene(self.skeletonSpecs()[-1].uuid).worldMatrix()
    # endregion
