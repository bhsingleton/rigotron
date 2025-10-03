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
    propComponent = mpyattribute.MPyAttribute('propComponent', attributeType='message')
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
        :rtype: ReferencedPropRig
        """

        # Check if a reference path was supplied
        #
        filePath = kwargs.pop('filePath', '')
        expandedPath = os.path.normpath(os.path.expandvars(filePath))

        exists = os.path.isfile(expandedPath)

        if not exists:

            log.warning(f'Unable to locate prop @ {expandedPath}')
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

        # Check if a stow component was supplied
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

        propComponent = self.scene(self.propComponent)
        stowComponent = self.scene(self.stowComponent)

        if propComponent is not None:

            return propComponent.findControlRig()

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

            return None, None

        elif numControlRigs == 1:

            return referenceNode, self.scene(controlRigs[0])

        else:

            raise TypeError(f'findReferencedPropRig() expects 1 unique control rig ({numControlRigs} found)!')

    def invalidate(self):
        """
        Updates the connections to the associated prop rig.

        :rtype: None
        """

        # Check if referenced prop rig exists
        #
        referenceNode, referencedRig = self.findReferencedPropRig()

        if referenceNode is None or referencedRig is None:

            log.warning('Unable to locate referenced prop rig!')
            return

        # Re-parent referenced prop rig
        #
        referencedRig.setParent(self)

        referencedRootComponent = self.scene(referencedRig.rootComponent)
        referencedRootSpec, = referencedRootComponent.skeleton()
        referencedRootJoint = self.scene.getNodeByUuid(referencedRootSpec.uuid, referenceNode=referenceNode)
        referencedRootJoint.setParent(self)

        # Check if prop component exists
        #
        referencedRootCtrl = referencedRootComponent.getPublishedNode('Root')
        referencedStowSpaceSwitch = self.scene.getNodeByUuid(referencedRootCtrl.userProperties['stowSpaceSwitch'], referenceNode=referenceNode)

        propComponent = self.scene(self.propComponent)

        if propComponent is not None:

            # Update referenced stow space switch
            #
            propOffsetCtrl = propComponent.getPublishedNode('Offset')
            referencedStowSpaceSwitch.connectPlugs(propOffsetCtrl[f'worldMatrix[{propOffsetCtrl.instanceNumber()}]'], 'target[0].targetMatrix', force=True)

            propSide = Side(propComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (propSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            referencedStowSpaceSwitch.setAttr('target[0].targetOffsetRotate', offsetEulerRotation, convertUnits=False)

        else:

            log.debug('No prop component specified to attach to!')

        # Check if stow component exists
        #
        stowComponent = self.scene(self.stowComponent)

        if stowComponent is not None:

            # Check if a stow attribute is required
            #
            stowCtrl = stowComponent.getPublishedNode('Stow')

            if not stringutils.isNullOrEmpty(self.stowName):

                # Find root joint and ensure attribute exists
                # Finally, connect stow attributes
                #
                controlRig = self.findControlRig()
                rootComponent = controlRig.findRootComponent()
                rootSpec, = rootComponent.skeleton()

                rootJoint = self.scene(rootSpec.uuid)

                if not rootJoint.hasAttr(self.stowName):

                    rootJoint.addAttr(
                        longName=self.stowName,
                        niceName=self.stowName,
                        attributeType='float',
                        min=0.0,
                        max=1.0,
                        keyable=True
                    )

                stowCtrl.connectPlugs('stowed', rootJoint[self.stowName], force=True)

            # Update referenced stow space switch
            #
            referencedStowSpaceSwitch.connectPlugs(stowCtrl['stowed'], 'target[0].targetWeight', force=True)
            referencedStowSpaceSwitch.connectPlugs(stowCtrl['stowed'], 'target[1].targetWeight', force=True)

            stowOffsetCtrl = stowComponent.getPublishedNode('Offset')
            referencedStowSpaceSwitch.connectPlugs(stowOffsetCtrl[f'worldMatrix[{stowOffsetCtrl.instanceNumber()}]'], 'target[1].targetMatrix', force=True)

            stowSide = Side(stowComponent.componentSide)
            offsetEulerRotation = om.MEulerRotation(0.0, 0.0, math.pi) if (stowSide == Side.RIGHT) else om.MEulerRotation.kIdentity
            referencedStowSpaceSwitch.setAttr('target[1].targetOffsetRotate', offsetEulerRotation, convertUnits=False)

        else:

            log.debug('No stow component specified to attach to!')
    # endregion
