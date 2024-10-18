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
    @abstractmethod
    def locomotionType(self):
        """
        Returns the locomotion type for this component.

        :rtype: LocomotionType
        """

        return self.LocomotionType.NONE

    def overrideLimbPoleVector(self, extremityCtrl, limbPVCtrl):
        """
        Overrides the space switch options on the supplied limb PV control.

        :type extremityCtrl: mpynode.MPyNode
        :type limbPVCtrl: mpynode.MPyNode
        :rtype: None
        """

        limbPVSpaceSwitch = self.scene(limbPVCtrl.userProperties['spaceSwitch'])
        index = limbPVSpaceSwitch.addTarget(extremityCtrl)
        attributeName = f'transformSpaceW{index}'

        limbPVCtrl.addAttr(
            longName=attributeName,
            niceName=f'Transform Space ({self.componentName})',
            attributeType='float',
            min=0.0,
            max=1.0,
            keyable=True
        )

        limbPVSpaceSwitch.connectPlugs(limbPVCtrl[attributeName], f'target[{index}].targetWeight')

    def overrideLimbHandle(self, extremityCtrl, inHandleCtrl):
        """
        Overrides the space switch on the supplied limb in-handle control.

        :type extremityCtrl: mpynode.MPyNode
        :type inHandleCtrl: mpynode.MPyNode
        :rtype: None
        """

        inHandleSpaceSwitch = self.scene(inHandleCtrl.userProperties['spaceSwitch'])
        insetNegate = self.scene(inHandleCtrl.userProperties['negate'])

        index = inHandleSpaceSwitch.addTarget(extremityCtrl, maintainOffset=False)
        inHandleSpaceSwitch.setAttr(f'target[{index}]', {'targetWeight': (0.0, 0.0, 0.0)})
        inHandleSpaceSwitch.connectPlugs(inHandleCtrl['localOrGlobal'], f'target[{index}].targetWeight')
        inHandleSpaceSwitch.connectPlugs(insetNegate['outDistance'], f'target[{index}].targetOffsetTranslateX')

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

    def overrideLimbRemapper(self, extremityCtrl, scaleRemapper):
        """
        Overrides the end-value on the supplied scale remapper.

        :type extremityCtrl: mpynode.MPyNode
        :type scaleRemapper: mpynode.MPyNode
        :rtype: None
        """

        limbTipCtrl = self.scene(scaleRemapper['outputMaxX'].source().node())

        multMatrixName = self.formatName(subname='Scale', type='multMatrix')
        multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
        multMatrix.connectPlugs(extremityCtrl['worldMatrix[0]'], 'matrixIn[0]')
        multMatrix.connectPlugs(limbTipCtrl['parentInverseMatrix[0]'], 'matrixIn[1]')

        decomposeMatrixName = self.formatName(subname='Scale', type='decomposeMatrix')
        decomposeMatrix = self.scene.createNode('decomposeMatrix', name=decomposeMatrixName)
        decomposeMatrix.connectPlugs(extremityCtrl['rotateOrder'], 'inputRotateOrder')
        decomposeMatrix.connectPlugs(multMatrix['matrixSum'], 'inputMatrix')

        scaleRemapper.connectPlugs(decomposeMatrix['outputScale'], 'outputMax', force=True)
    # endregion
