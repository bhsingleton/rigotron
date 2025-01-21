import os
import math

from maya.api import OpenMaya as om
from maya.app.flux.attrUtils import niceName
from mpy import mpyattribute
from dcc.python import stringutils
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
    handednessName = mpyattribute.MPyAttribute('handednessName', attributeType='str')
    primaryPropComponent = mpyattribute.MPyAttribute('primaryPropComponent', attributeType='message')
    secondaryPropComponent = mpyattribute.MPyAttribute('secondaryPropComponent', attributeType='message')
    stowName = mpyattribute.MPyAttribute('stowName', attributeType='str')
    stowComponent = mpyattribute.MPyAttribute('stowComponent', attributeType='message')
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

        controlRig = kwargs.get('controlRig', None)

        if controlRig is not None:

            referencedPropRig.controlRig = controlRig

        # Check if a prop component was supplied
        #
        handednessName = kwargs.get('handednessName', '')
        referencedPropRig.handednessName = handednessName

        primaryPropComponent = kwargs.pop('primaryPropComponent', None)

        if primaryPropComponent is not None:

            referencedPropRig.primaryPropComponent = primaryPropComponent.object()

        secondaryPropComponent = kwargs.pop('secondaryPropComponent', None)

        if secondaryPropComponent is not None:

            referencedPropRig.secondaryPropComponent = secondaryPropComponent.object()

        # Check if a stowed component was supplied
        #
        stowName = kwargs.get('stowName', '')
        referencedPropRig.stowName = stowName

        stowComponent = kwargs.pop('stowComponent', None)

        if stowComponent is not None:

            referencedPropRig.stowComponent = stowComponent.object()

        return referencedPropRig

    def findControlRig(self):
        """
        Returns the control rig associated with this interface.

        :rtype: rigotron.interfaces.controlrig.ControlRig
        """

        primaryPropComponent = self.scene(self.primaryPropComponent)
        secondaryPropComponent = self.scene(self.secondaryPropComponent)
        stowComponent = self.scene(self.stowComponent)

        if primaryPropComponent is not None:

            return primaryPropComponent.findControlRig()

        elif secondaryPropComponent is not None:

            return secondaryPropComponent.findControlRig()

        elif stowComponent is not None:

            return stowComponent.findControlRig()

        else:

            return None

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

        # Re-parent referenced prop rig
        #
        referenceNode, referencedRig = self.findReferencedPropRig()
        referencedRig.setParent(self)

        referencedRootComponent = self.scene(referencedRig.rootComponent)
        referencedRootSpec, = referencedRootComponent.skeletonSpecs()
        referencedRootJoint = self.scene.getNodeByUuid(referencedRootSpec.uuid, referenceNode=referenceNode)
        referencedRootJoint.setParent(self)

        # Find referenced root control and space switches
        #
        referencedRootCtrl = referencedRootComponent.getPublishedNode('Root')

        handednessSpaceSwitch = self.scene.getNodeByUuid(referencedRootCtrl.userProperties['handednessSpaceSwitch'], referenceNode=referenceNode)
        stowSpaceSwitch = self.scene.getNodeByUuid(referencedRootCtrl.userProperties['stowSpaceSwitch'], referenceNode=referenceNode)

        # Connect referenced root control to control rig's export root
        #
        controlRig = self.findControlRig()
        rootComponent = controlRig.findRootComponent()

        rootSpec, = rootComponent.skeletonSpecs()
        rootJoint = self.scene(rootSpec.uuid)

        if not stringutils.isNullOrEmpty(self.handednessName):

            if not rootJoint.hasAttr(self.handednessName):

                rootJoint.addAttr(longName=self.handednessName, niceName=self.handednessName, attributeType='float', min=0.0, max=1.0, keyable=True)

            referencedRootCtrl.connectPlugs('handedness', rootJoint[self.handednessName], force=True)

        else:

            log.debug('Skipping handedness custom attribute...')

        if not stringutils.isNullOrEmpty(self.stowName):

            if not rootJoint.hasAttr(self.stowName):

                rootJoint.addAttr(longName=self.stowName, niceName=self.stowName, attributeType='float', min=0.0, max=1.0, keyable=True)

            referencedRootCtrl.connectPlugs('stowed', rootJoint[self.stowName], force=True)

        else:

            log.debug('Skipping stow custom attribute...')

        # Connect prop offset controls to handedness space switch
        #
        primaryPropComponent = self.scene(self.primaryPropComponent)

        if primaryPropComponent is not None:

            propOffsetCtrl = primaryPropComponent.getPublishedNode('Offset')
            handednessSpaceSwitch.connectPlugs(propOffsetCtrl[f'worldMatrix[{propOffsetCtrl.instanceNumber()}]'], 'target[0].targetMatrix', force=True)

            propSide = Side(primaryPropComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (propSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            handednessSpaceSwitch.setAttr('target[0].targetOffsetRotate', offsetEulerRotation, convertUnits=False)

        secondaryPropComponent = self.scene(self.secondaryPropComponent)

        if secondaryPropComponent is not None:

            propOffsetCtrl = secondaryPropComponent.getPublishedNode('Offset')
            handednessSpaceSwitch.connectPlugs(propOffsetCtrl[f'worldMatrix[{propOffsetCtrl.instanceNumber()}]'], 'target[1].targetMatrix', force=True)

            propSide = Side(secondaryPropComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (propSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            handednessSpaceSwitch.setAttr('target[1].targetOffsetRotate', offsetEulerRotation, convertUnits=False)

        # Connect stowed control to space switch
        #
        stowComponent = self.scene(self.stowComponent)

        if stowComponent is not None:

            stowCtrl = stowComponent.getPublishedNode('Stow')
            stowCtrl.connectPlugs('stowed', referencedRootCtrl['stowed'])

            stowOffsetCtrl = stowComponent.getPublishedNode('Offset')
            stowSpaceSwitch.connectPlugs(stowOffsetCtrl[f'worldMatrix[{stowOffsetCtrl.instanceNumber()}]'], 'target[1].targetMatrix', force=True)

            stowSide = Side(stowComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (stowSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            stowSpaceSwitch.setAttr('target[1].targetOffsetRotate', offsetEulerRotation, convertUnits=False)
    # endregion
