import os
import math

from mpy import mpyscene, mpynode
from maya.api import OpenMaya as om
from dcc.maya.libs import dagutils
from dcc.maya.standalone import rpc
from dcc.python import stringutils
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SkeletonManager(object):
    """
    Base class for interfacing with export skeletons.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_controlRig', '_referenceNode',)

    def __init__(self, controlRig, referenceNode=None):
        """
        Private method called after a new instance is created.

        :type controlRig: rigotron.interfaces.controlrig.ControlRig
        :rtype: None
        """
        # Call parent method
        #
        super(SkeletonManager, self).__init__()

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._controlRig = controlRig.weakReference()
        self._referenceNode = self.nullWeakReference

        # Check if a reference node was supplied
        #
        if isinstance(referenceNode, mpynode.MPyNode):

            self._referenceNode = referenceNode.weakReference()
    # endregion

    # region Properties
    @classproperty
    def nullWeakReference(cls):
        """
        Getter method that returns a null weak reference.

        :rtype: Callable
        """

        return lambda: None

    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def controlRig(self):
        """
        Getter method that returns the control rig.

        :rtype: rigotron.interfaces.controlrig.ControlRig
        """

        return self._controlRig()

    @property
    def isFromReferencedFile(self):
        """
        Getter method that returns the reference state.

        :rtype: bool
        """

        return self.referenceNode is not None

    @property
    def referenceNode(self):
        """
        Getter method that returns the reference node.

        :rtype: Union[mpy.builtins.referencemixin.ReferenceMixin, None]
        """

        return self._referenceNode()

    @property
    def referencedScene(self):
        """
        Getter method that returns the referenced scene interface.

        :rtype: rpc.RPCClient
        """

        return rpc.__client__
    # endregion

    # region Methods
    def prepare(self):
        """
        Notifies the manager to prepare to build joints.

        :rtype: None
        """

        # Check if skeleton was referenced
        #
        if not self.isFromReferencedFile:

            return

        # Check if referenced skeleton is already open
        #
        referencePath = os.path.abspath(self.referenceNode.filePath())
        currentPath = os.path.abspath(self.referencedScene.file(query=True, sceneName=True))

        isOpen = (referencePath == currentPath)

        if not isOpen:

            log.info(f'Opening referenced skeleton: {referencePath}')
            self.referencedScene.open(referencePath)

        else:

            log.debug(f'Referenced skeleton is already open...')

    def load(self, clearEdits=False, force=False):
        """
        Loads the referenced skeleton.

        :type clearEdits: bool
        :type force: bool
        :rtype: None
        """

        # Check if skeleton was referenced
        #
        if not self.isFromReferencedFile:

            return

        # Check if edits require clearing
        #
        if clearEdits:

            self.referenceNode.clearEdits()

        # Check if reference requires loading
        #
        isLoaded = self.referenceNode.isLoaded()

        if not isLoaded or force:

            self.referenceNode.reload()

    def unload(self, clearEdits=False):
        """
        Unloads the referenced skeleton.

        :type clearEdits: bool
        :rtype: None
        """

        # Check if skeleton was referenced
        #
        if not self.isFromReferencedFile:

            return

        # Check if reference requires unloading
        #
        if self.referenceNode.isLoaded():

            self.referenceNode.unload()

        # Check if edits require clearing
        #
        if clearEdits:

            self.referenceNode.clearEdits()

    def save(self):
        """
        Saves any changes made by the manager.

        :rtype: None
        """

        if self.isFromReferencedFile:

            self.referencedScene.save()

    def getNodeNameByUUID(self, uuid, long=False):
        """
        Returns the name of the node associated with the supplied UUID.

        :type uuid: om.MUuid
        :type long: bool
        :rtype: str
        """

        # Check if UUID is valid
        #
        isValid = uuid.valid()

        if not isValid:

            return ''

        # Evaluate skeleton type
        #
        if self.isFromReferencedFile:

            nodes = self.referencedScene.ls(uuid.asString(), long=long)

            if not stringutils.isNullOrEmpty(nodes):

                return nodes[0]

            else:

                return ''

        else:

            node = self.scene.getNodeByUuid(uuid)

            if long:

                return node.fullPathName()

            else:

                return node.name()

    def doesNodeExist(self, uuid):
        """
        Evaluates if a node with the supplied UUID exists.

        :type uuid: om.MUuid
        :rtype: bool
        """

        # Evaluate if UUID is valid
        #
        isValid = uuid.valid()

        if not isValid:

            return False

        # Evaluate if UUID is derived from a referenced scene file
        #
        if self.isFromReferencedFile:

            return self.referencedScene.doesNodeExist(uuid.asString())

        else:

            return self.scene.doesNodeExist(uuid)

    def createJoint(self, name, parent=om.MUuid()):
        """
        Returns the name and UUID of a new joint with the supplied name.

        :type name: str
        :type parent: om.MUuid
        :rtype: Tuple[str, str]
        """

        if self.isFromReferencedFile:

            # Compose command arguments
            #
            kwargs = {'asNameAndUUID': True}

            if not stringutils.isNullOrEmpty(name):

                kwargs['name'] = name

            if parent.valid():

                kwargs['parent'] = self.getNodeNameByUUID(parent, long=True)

            # Create new export joint
            #
            log.info(f'Creating "{name}" export joint!')
            name, uuid = self.referencedScene.createNode('joint', **kwargs)

            return name, uuid

        else:

            # Create new export joint
            #
            parent = self.scene.getNodeByUuid(parent)
            joint = self.scene.createNode('joint', name=name, parent=parent)

            return joint.name(), joint.uuid()

    def renameJoint(self, uuid, name):
        """
        Renames the joint associated with the supplied UUID.

        :type uuid: om.MUuid
        :type name: str
        :rtype: str
        """

        if self.isFromReferencedFile:

            fullPathName = self.getNodeNameByUUID(uuid, long=True)
            currentName = dagutils.stripAll(fullPathName)

            if currentName != name and not stringutils.isNullOrEmpty(name):

                return self.referencedScene.renameNode(currentName, name)

            else:

                return currentName

        else:

            node = self.scene.getNodeByUuid(uuid)
            currentName = node.name()

            if currentName != name and not stringutils.isNullOrEmpty(name):

                return node.setName(name)

            else:

                return currentName

    def parentJoint(self, childUUID, parentUUID, absolute=False):
        """
        Reparents the joint associated with the supplied UUID.

        :type childUUID: om.MUuid
        :type parentUUID: om.MUuid
        :type absolute: bool
        :rtype: None
        """

        if self.isFromReferencedFile:

            child = self.getNodeNameByUUID(childUUID, long=True)
            parent = self.getNodeNameByUUID(parentUUID, long=True)

            currentParents = self.referencedScene.listRelatives(child, parent=True, fullPath=True)
            currentParent = currentParents[0] if not stringutils.isNullOrEmpty(currentParents) else ''

            if currentParent == parent:

                return

            matrix = self.referencedScene.xform(child, query=True, matrix=True, worldSpace=True)

            if stringutils.isNullOrEmpty(parent):

                self.referencedScene.parentNode(child, world=True, relative=True)

            else:

                self.referencedScene.parentNode(child, parent, relative=True)

            child = self.getNodeNameByUUID(childUUID, long=True)
            self.referencedScene.xform(child, matrix=matrix, worldSpace=True)

        else:

            child = self.scene.getNodeByUuid(childUUID)
            parent = self.scene.getNodeByUuid(parentUUID)

            if child.parent() is not parent:

                child.setParent(parent, absolute=True)

    def deleteJoint(self, uuid, absolute=True):
        """
        Deletes the joint associated with the supplied UUID.

        :type uuid: om.MUuid
        :type absolute: bool
        :rtype: None
        """

        if self.isFromReferencedFile:

            fullPathName = self.getNodeNameByUUID(uuid, long=True)
            name = dagutils.stripAll(fullPathName)
            children = self.referencedScene.listRelatives(fullPathName, children=True, path=True)

            if not stringutils.isNullOrEmpty(children):

                self.referencedScene.parentNode(*children, world=True, absolute=absolute)

            log.info(f'Deleting "{name}" export joint!')
            self.referencedScene.deleteNode(fullPathName)

        else:

            joint = self.scene(uuid)
            children = joint.children()

            for child in reversed(children):

                child.setParent(None, absolute=absolute)

            log.info(f'Deleting "{joint}" export joint!')
            joint.delete()

    def syncJoint(self, skeletonSpec, **kwargs):
        """
        Synchronizes the joint associated with the supplied skeleton spec.
        If no joint exists then a new one created in its place!

        :type skeletonSpec: skeletonspec.SkeletonSpec
        :rtype: None
        """

        # Check if skeleton spec is enabled
        #
        if skeletonSpec.enabled:

            # Check if associated export joint exists
            # If not, go ahead and bind a new export joint to the skeleton spec!
            #
            exists = self.doesNodeExist(skeletonSpec.uuid)

            if exists:

                # Rename export joint
                #
                skeletonSpec.name = self.renameJoint(skeletonSpec.uuid, skeletonSpec.name)

                # Reparent export joint
                #
                parentUUID = getattr(skeletonSpec.parent, 'uuid', om.MUuid())
                self.parentJoint(skeletonSpec.uuid, parentUUID, absolute=True)

            else:

                # Create new export joint
                #
                parentUUID = getattr(skeletonSpec.parent, 'uuid', om.MUuid())
                name, uuid = self.createJoint(skeletonSpec.name, parent=parentUUID)

                # Update skeleton spec
                #
                skeletonSpec.name = name
                skeletonSpec.uuid = uuid

            # Update attributes
            #
            if self.isFromReferencedFile:

                # Update display properties
                #
                fullPathName = self.getNodeNameByUUID(skeletonSpec.uuid, long=True)

                self.referencedScene.setAttr(f'{fullPathName}.side', skeletonSpec.side.value)
                self.referencedScene.setAttr(f'{fullPathName}.type', skeletonSpec.type.value)
                self.referencedScene.setAttr(f'{fullPathName}.otherType', skeletonSpec.otherType, type='string')
                self.referencedScene.setAttr(f'{fullPathName}.drawStyle', skeletonSpec.drawStyle.value)
                self.referencedScene.setAttr(f'{fullPathName}.displayLocalAxis', kwargs.get('displayLocalAxis', True))

                # Update transformation matrix
                #
                translation = skeletonSpec.matrix.translation(om.MSpace.kTransform)
                rotateOrder = skeletonSpec.matrix.rotationOrder() - 1
                eulerRotation = skeletonSpec.matrix.rotation(asQuaternion=False)
                eulerRotation.reorderIt(rotateOrder)

                self.referencedScene.setAttr(f'{name}.translate', *tuple(translation), type='double3')
                self.referencedScene.setAttr(f'{name}.rotate', *tuple(map(math.degrees, eulerRotation)), type='double3')

            else:

                # Update display properties
                #
                node = self.scene.getNodeByUuid(skeletonSpec.uuid)

                node.setAttr('side', skeletonSpec.side.value)
                node.setAttr('type', skeletonSpec.type.value)
                node.setAttr('otherType', skeletonSpec.otherType)
                node.setAttr('drawStyle', skeletonSpec.drawStyle.value)
                node.setAttr('displayLocalAxis', kwargs.get('displayLocalAxis', True))

                # Update transformation matrix
                #
                node.setMatrix(skeletonSpec.matrix, skipScale=True)

        else:

            # Check if the associated export joint still exists
            # If so, go ahead and delete the export joint and reset the UUID!
            #
            exists = self.doesNodeExist(skeletonSpec.uuid)

            if exists:

                self.deleteJoint(skeletonSpec.uuid)
                del skeletonSpec.uuid

        return skeletonSpec

    def cacheJoint(self, skeletonSpec, **kwargs):
        """
        Caches the transformation matrix for the supplied skeleton spec.

        :type skeletonSpec: skeletonspec.SkeletonSpec
        :type delete: bool
        :type push: bool
        :type save: bool
        :rtype: bool
        """

        # Copy transformation matrix to skeleton spec
        #
        success = skeletonSpec.cacheNode(**kwargs)

        if not success:

            log.error(f'Unable to cache "{skeletonSpec.name}" skeleton spec!')
            return False

        # Check if transformation matrix require pushing to source reference
        #
        push = kwargs.get('push', False)

        if not (push and self.isFromReferencedFile):

            return True

        # Check if referenced export joint exists
        #
        fullPathName = self.getNodeNameByUUID(skeletonSpec.uuid, long=True)

        if not stringutils.isNullOrEmpty(fullPathName):

            # Update transform attributes
            #
            translation = skeletonSpec.matrix.translation(om.MSpace.kTransform)
            rotateOrder = skeletonSpec.matrix.rotationOrder() - 1
            eulerRotation = skeletonSpec.matrix.rotation(asQuaternion=False)
            eulerRotation.reorderIt(rotateOrder)

            self.referencedScene.setAttr(f'{fullPathName}.translate', *tuple(translation), type='double3')
            self.referencedScene.setAttr(f'{fullPathName}.rotate', *tuple(map(math.degrees, eulerRotation)), type='double3')

            # Check if changes require saving
            #
            save = kwargs.get('save', False)

            if save:

                self.save()

            return True

        else:

            log.error(f'Unable to cache "{skeletonSpec.name}" export joint @ <{skeletonSpec.uuid.asString()}>!')
            return False

    def flushJoints(self, queue, save=False):
        """
        Deletes any pending joints from the queue.

        :type queue: deque
        :type save: bool
        :rtype: None
        """

        # Iterate through queue
        #
        while len(queue) > 0:

            # Check if skeleton spec is valid
            #
            skeletonSpec = queue.pop()
            isValid = skeletonSpec.uuid.valid()

            if not isValid:

                continue

            # Check if export joint still exists
            #
            exists = self.doesNodeExist(skeletonSpec.uuid)

            if not exists:

                continue

            # Delete export joint
            #
            self.deleteJoint(skeletonSpec.uuid, absolute=True)
            del skeletonSpec.uuid

        # Check if changes require saving
        #
        if save and self.isFromReferencedFile:

            self.referencedScene.save()

    def bindJoint(self, skeletonSpec):
        """
        Binds the export joint, associated with the supplied skeleton spec, to its driver.

        :type skeletonSpec: skeletonspec.SkeletonSpec
        :rtype: None
        """

        skeletonSpec.driver.bind(referenceNode=self.referenceNode)

    def unbindJoint(self, skeletonSpec, reset=False):
        """
        Unbinds the export joint, associated with the supplied skeleton spec, from its driver.

        :type skeletonSpec: skeletonspec.SkeletonSpec
        :type reset: bool
        :rtype: None
        """

        skeletonSpec.driver.unbind(referenceNode=self.referenceNode)

        if reset:

            self.resetJoint(skeletonSpec)

    def resetJoint(self, skeletonSpec):
        """
        Resets the transformation matrix on the joint associated with the supplied skeleton spec.

        :type skeletonSpec: skeletonspec.SkeletonSpec
        :rtype: None
        """

        joint = skeletonSpec.getNode(referenceNode=self.referenceNode)
        joint.setMatrix(skeletonSpec.matrix)
    # endregion
