from abc import abstractmethod
from mpy import mpyattribute
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExtremityComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that outlines extremity components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Extremity'
    # endregion

    # region Methods
    def overrideLimbPVSpace(self, extremityCtrl, limbPVCtrl):
        """
        Overrides the space switch options on the supplied limb PV control.

        :type extremityCtrl: mpynode.MPyNode
        :type limbPVCtrl: mpynode.MPyNode
        :rtype: None
        """

        limbPVCtrl.addAttr(
            longName='transformSpaceW5',
            niceName=f'Transform Space ({self.componentName})',
            attributeType='float',
            min=0.0,
            max=1.0,
            keyable=True
        )

        limbPVSpaceSwitch = self.scene(limbPVCtrl.userProperties['spaceSwitch'])
        limbPVSpaceSwitch.addSpace(extremityCtrl)
        limbPVSpaceSwitch.connectPlugs(limbPVCtrl['transformSpaceW5'], 'target[5].targetWeight')

    def overrideLimbTwist(self, extremityCtrl, extremityJoint, twistSolver):
        """
        Overrides the end-twist matrix on the supplied twist solver.

        :type extremityCtrl: mpynode.MPyNode
        :type extremityJoint: mpynode.MPyNode
        :type twistSolver: mpynode.MPyNode
        :rtype: None
        """

        twistSolver.endOffsetMatrix = extremityJoint.worldMatrix() * extremityCtrl.worldInverseMatrix()
        twistSolver.connectPlugs(extremityCtrl[f'worldMatrix[{extremityCtrl.instanceNumber()}]'], 'endMatrix', force=True)
    # endregion
