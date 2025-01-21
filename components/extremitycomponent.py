from maya.api import OpenMaya as om
from mpy import mpyattribute
from abc import abstractmethod
from enum import IntEnum
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LocomotionType(IntEnum):
    """
    Enum class of locomotion types.
    """

    NONE = -1
    PLANTIGRADE = 0
    DIGITGRADE = 1


class ExtremityComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that outlines extremity components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Extremity'
    # endregion

    # region Enums
    LocomotionType = LocomotionType
    # endregion

    # region Methods
    def effectorMatrix(self):
        """
        Returns the effector matrix for this component.

        :rtype: om.MMatrix
        """

        skeletonSpecs = self.skeletonSpecs()
        hasSkeletonSpecs = len(skeletonSpecs) > 0

        if hasSkeletonSpecs:

            return self.scene(skeletonSpecs[0].uuid).worldMatrix()

        else:

            return om.MMatrix.kIdentity

    def preferredEffectorMatrix(self):
        """
        Returns the preferred effector matrix for this component.
        By default, this will return the first skeletal spec matrix!

        :rtype: om.MMatrix
        """

        return self.effectorMatrix()

    def overrideLimbPoleVector(self, extremityCtrl, limbPVCtrl):
        """
        Overrides the space switch options on the supplied limb PV control.

        :type extremityCtrl: mpynode.MPyNode
        :type limbPVCtrl: mpynode.MPyNode
        :rtype: None
        """

        # Check if space switch target already exists
        #
        spaceSwitch = self.scene(limbPVCtrl.userProperties['spaceSwitch'])
        targets = spaceSwitch.targets()
        targetName = extremityCtrl.name()

        found = [target for target in targets if target.name() == targetName]
        exists = len(found) == 1

        if exists:

            # Reconnect target to space switch
            #
            target = found[0]
            extremityCtrl.connectPlugs(f'worldMatrix[{extremityCtrl.instanceNumber()}]', spaceSwitch[f'target[{target.index}].targetMatrix'], force=True)

        else:

            # Add target to space switch
            #
            index = spaceSwitch.addTarget(extremityCtrl)
            attributeName = f'transformSpaceW{index}'

            limbPVCtrl.addAttr(
                longName=attributeName,
                niceName=f'Transform Space ({self.componentName})',
                attributeType='float',
                min=0.0,
                max=1.0,
                keyable=True
            )

            spaceSwitch.connectPlugs(limbPVCtrl[attributeName], f'target[{index}].targetWeight')

    def overrideLimbHandle(self, extremityCtrl, inHandleCtrl):
        """
        Overrides the space switch on the supplied limb in-handle control.

        :type extremityCtrl: mpynode.MPyNode
        :type inHandleCtrl: mpynode.MPyNode
        :rtype: None
        """

        # Check if space switch target already exists
        #
        negate = self.scene(inHandleCtrl.userProperties['negate'])

        spaceSwitch = self.scene(inHandleCtrl.userProperties['spaceSwitch'])
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
        spaceSwitch.connectPlugs(inHandleCtrl['localOrGlobal'], f'target[{index}].targetWeight', force=True)
        spaceSwitch.connectPlugs(negate['outDistance'], f'target[{index}].targetOffsetTranslateX', force=True)

    def overrideLimbTwist(self, extremityCtrl, twistSolver, offsetMatrix=om.MMatrix.kIdentity):
        """
        Overrides the end-twist matrix on the supplied twist solver.

        :type extremityCtrl: mpynode.MPyNode
        :type twistSolver: mpynode.MPyNode
        :type offsetMatrix: om.MMatrix
        :rtype: None
        """

        twistSolver.endOffsetMatrix = offsetMatrix
        twistSolver.connectPlugs(extremityCtrl[f'worldMatrix[{extremityCtrl.instanceNumber()}]'], 'endMatrix', force=True)

    def overrideLimbRemapper(self, limbIKCtrl, extremityCtrl, scaleRemapper):
        """
        Overrides the end-value on the supplied scale remapper.

        :type limbIKCtrl: mpynode.MPyNode
        :type extremityCtrl: mpynode.MPyNode
        :type scaleRemapper: mpynode.MPyNode
        :rtype: None
        """

        multMatrixName = self.formatName(subname='Scale', type='multMatrix')
        multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
        multMatrix.connectPlugs(extremityCtrl['worldMatrix[0]'], 'matrixIn[0]')
        multMatrix.connectPlugs(limbIKCtrl['parentInverseMatrix[0]'], 'matrixIn[1]')

        decomposeMatrixName = self.formatName(subname='Scale', type='decomposeMatrix')
        decomposeMatrix = self.scene.createNode('decomposeMatrix', name=decomposeMatrixName)
        decomposeMatrix.connectPlugs(extremityCtrl['rotateOrder'], 'inputRotateOrder')
        decomposeMatrix.connectPlugs(multMatrix['matrixSum'], 'inputMatrix')

        scaleRemapper.connectPlugs(decomposeMatrix['outputScale'], 'outputMax', force=True)
    # endregion
