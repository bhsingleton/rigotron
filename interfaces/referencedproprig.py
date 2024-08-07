import os
import math

from maya.api import OpenMaya as om
from mpy import mpyattribute
from ..abstract import abstractinterface
from ..libs import Side

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ReferencedPropRig(abstractinterface.AbstractInterface):
    """
    Overload of `AbstractInterface` that interfaces with referenced prop rigs.
    """

    # region Attributes
    referenceNode = mpyattribute.MPyAttribute('referenceNode', attributeType='message')
    propComponent = mpyattribute.MPyAttribute('propComponent', attributeType='message')
    stowedComponent = mpyattribute.MPyAttribute('stowedComponent', attributeType='message')
    # endregion

    # region Dunderscores
    __default_prop_path__ = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'scenes', 'untitled.ma'))
    # endregion

    # region Methods
    @classmethod
    def create(cls, *args, **kwargs):
        """
        Returns a new dependency node of the specified type with this extension.

        :key name: Union[str, Dict[str, Any]]
        :key parent: Union[str, om.MObject, om.MDagPath, None]
        :key filePath: str
        :rtype: PropRig
        """

        # Check if a reference path was supplied
        #
        filePath = kwargs.pop('filePath', '')
        exists = os.path.isfile(filePath)

        if not exists:

            log.warning(f'Unable to locate prop @ {filePath}')
            log.info(f'Defaulting to: {cls.__default_prop_path__}')

            filePath = cls.__default_prop_path__

        # Call parent method
        #
        directory, filename = os.path.split(filePath)
        defaultName = os.path.splitext(filename)[0]

        namespace = kwargs.get('namespace', defaultName)
        name = kwargs.pop('name', f'{namespace}_PROP')
        parent = kwargs.pop('parent', None)

        referencedPropRig = super(ReferencedPropRig, cls).create('transform', name=name, parent=parent)

        # Create reference to prop
        #
        reference = cls.scene.createReference(filePath, namespace=namespace)
        referencedPropRig.referenceNode = reference.object()

        # Check if a prop component was supplied
        #
        propComponent = kwargs.pop('propComponent', None)

        if propComponent is not None:

            referencedPropRig.propComponent = propComponent.object()

        # Check if a stowed component was supplied
        #
        stowedComponent = kwargs.pop('stowedComponent', None)

        if stowedComponent is not None:

            referencedPropRig.stowedComponent = stowedComponent.object()

        return referencedPropRig

    def findReferencedPropRig(self):
        """
        Returns the referenced prop associated with this component.

        :rtype: Tuple[mpy.builtins.referencemixin.ReferenceMixin, rigotron.interfaces.controlrig.ControlRig]
        """

        referenceNode = self.scene(self.referenceNode)
        referencedNodes = list(map(self.scene.__call__, referenceNode.nodes()))

        cls = self.rigManager.getClass('ControlRig')
        controlRigs = [node for node in referencedNodes if isinstance(node, cls)]
        numControlRigs = len(controlRigs)

        if numControlRigs == 0:

            return None

        elif numControlRigs == 1:

            return referenceNode, self.scene(controlRigs[0])

        else:

            raise TypeError(f'findReferencedPropRig() expects 1 unique control rig ({numControlRigs} found)!')

    def invalidate(self):
        """
        Updates the connections to the associated prop rig.

        :rtype: None
        """

        # Find referenced prop
        #
        referenceNode, referencedRig = self.findReferencedPropRig()
        referencedRig.setParent(self)

        rootComponent = self.scene(referencedRig.rootComponent)
        masterCtrl = rootComponent.getPublishedNode('Master')

        masterSpaceSwitchUuid = masterCtrl.userProperties['spaceSwitch']
        masterSpaceSwitch = self.scene.getNodeByUuid(masterSpaceSwitchUuid, referenceNode=referenceNode)

        # Connect prop control to space switch
        #
        propComponent = self.scene(self.propComponent)

        if propComponent is not None:

            propCtrl = propComponent.getPublishedNode('Offset')
            masterSpaceSwitch.connectPlugs(propCtrl[f'worldMatrix[{propCtrl.instanceNumber()}]'], 'target[0].targetMatrix')

            propSide = Side(propComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (propSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            masterSpaceSwitch.setAttr('target[0].targetOffsetRotate', offsetEulerRotation, convertUnits=False)

        # Connect stowed control to space switch
        #
        stowedComponent = self.scene(self.stowedComponent)

        if stowedComponent is not None:

            stowCtrl = stowedComponent.getPublishedNode('Stowed')
            masterSpaceSwitch.connectPlugs(stowCtrl[f'worldMatrix[{stowCtrl.instanceNumber()}]'], 'target[1].targetMatrix')

            stowedSide = Side(stowedComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (stowedSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            masterSpaceSwitch.setAttr('target[1].targetOffsetRotate', offsetEulerRotation, convertUnits=False)
    # endregion
