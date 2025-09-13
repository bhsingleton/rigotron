import math
import os

from maya.api import OpenMaya as om

from airship_syndicate.ui.interop import referenceFile
from mpy import mpynode, mpyattribute
from dcc.maya.libs import dagutils
from dcc.maya.standalone import rpc
from dcc.python import stringutils
from abc import abstractmethod
from collections import deque
from collections.abc import MutableSequence
from ..abstract import abstractcomponent
from ..libs import skeletonspec, pivotspec
from ..abstract import abstractspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BaseComponent(abstractcomponent.AbstractComponent):
    """
    Overload of `AbstractComponent` that outlines rig component construction.
    """

    # region Constants
    SKELETON_KEY = 'skeleton'
    SKELETON_DIRTY_KEY = 'isSkeletonDirty'
    PIVOTS_KEY = 'pivots'
    PIVOTS_DIRTY_KEY = 'arePivotsDirty'
    # endregion

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(BaseComponent, self).__init__(*args, **kwargs)

        # Declare class variables
        #
        self._callbackID = None
        self._pending = deque()
        self._bin = deque()
    # endregion

    # region Methods
    @classmethod
    def create(cls, *args, **kwargs):
        """
        Returns a new dependency node of the specified type with this extension.

        :key name: Union[str, Dict[str, Any]]
        :key parent: Union[str, om.MObject, om.MDagPath, MPyNode]
        :key componentName: str
        :key componentVersion: float
        :rtype: AbstractComponent
        """

        # Call parent method
        #
        component = super(BaseComponent, cls).create(*args, **kwargs)

        # Update component attributes
        #
        component.userProperties[cls.SKELETON_DIRTY_KEY] = True
        component.userProperties[cls.SKELETON_KEY] = []
        component.userProperties[cls.PIVOTS_DIRTY_KEY] = True
        component.userProperties[cls.PIVOTS_KEY] = []
        component.userProperties.pushBuffer()

        return component

    def delete(self):
        """
        Removes this instance from the scene file.

        :rtype: None
        """

        # Evaluate component state
        #
        status = self.Status(self.componentStatus)
        isMeta = (status == self.Status.META)

        if not isMeta:

            raise RuntimeError(f'delete() expects to be in the meta state ({status.name} given)!')

        # Flush entire skeleton
        #
        self._bin.extend(self.skeleton(flatten=True, skipDisabled=False, skipPassthrough=False))
        self.flushSkeleton(save=True)

        # Call parent method
        #
        return super(BaseComponent, self).delete()

    @classmethod
    def flattenSpecs(cls, specs, **kwargs):
        """
        Returns a generator that yields all skeleton specs.
        By default, this method ignores disabled specs and skips over passthrough specs!

        :type specs: Union[skeletonspec.SkeletonSpec, List[skeletonspec.SkeletonSpec]]
        :type skipDisabled: bool
        :type skipPassthrough: bool
        :rtype: Iterator[skeletonspec.SkeletonSpec]
        """

        # Evaluate supplied specs
        #
        if isinstance(specs, abstractspec.AbstractSpec):

            specs = [specs]

        # Iterate through specs
        #
        skipDisabled = kwargs.get('skipDisabled', True)
        skipPassthrough = kwargs.get('skipPassthrough', True)

        for spec in specs:

            # Evaluate item type
            #
            if not isinstance(spec, abstractspec.AbstractSpec):

                continue

            # Check if spec is enabled
            # If so, go ahead and skip it and ignore children
            #
            enabled = getattr(spec, 'enabled', False)

            if skipDisabled and not enabled:

                continue

            # Check if spec is marked to passthrough
            # If so, go ahead and continue and move onto children
            #
            passthrough = getattr(spec, 'passthrough', False)

            if skipPassthrough and passthrough:

                yield from cls.flattenSpecs(spec.children, **kwargs)

            else:

                yield spec
                yield from cls.flattenSpecs(spec.children, **kwargs)

    @classmethod
    def unpackSpecs(cls, *args):
        """
        Unpacks the supplied specs based on the predicated sizes.

        :type args: List[Union[int, List[abstractspec.AbstractSpec]]]
        :rtype: List[List[abstractspec.AbstractSpec]]
        """

        # Evaluate supplied arguments
        #
        numArgs = len(args)

        if not (numArgs >= 2):

            raise TypeError(f'unpackSpecs() expects at least 2 args ({numArgs} given)!')

        # Evaluate argument types
        #
        *sizes, specs = args

        if not (all(isinstance(size, int) for size in sizes) and isinstance(specs, MutableSequence)):

            raise TypeError(f'unpackSpecs() expects a sequence of sizes and specs!')

        # Evaluate sizes with array size
        #
        size = sum(sizes)
        count = len(specs)

        if size != count:

            raise TypeError(f'unpackSpecs() mismatch found between sizes and specs!')

        # Unpack specs
        #
        startIndex, endIndex = 0, 0
        unpacked = [None] * len(sizes)

        for (i, size) in enumerate(sizes):

            startIndex += sizes[i - 1] if (i > 0) else 0
            endIndex = startIndex + size

            unpacked[i] = specs[startIndex:endIndex]

        return unpacked

    def resizeChildSpecs(self, size, parentSpec, cls=None):
        """
        Resizes the children for the supplied parent skeleton spec.

        :type size: int
        :type parentSpec: Union[skeletonspec.SkeletonSpec, List[skeletonspec.SkeletonSpec]]
        :type cls: Callable
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Evaluate supplied parent spec
        #
        childSpecs = None

        if isinstance(parentSpec, abstractspec.AbstractSpec):

            childSpecs = parentSpec.children

        elif isinstance(parentSpec, MutableSequence):

            childSpecs, parentSpec = parentSpec, None

        else:

            raise TypeError(f'resizeSkeletalChildren() expects a node spec ({type(parentSpec).__name__} given!)')

        # Evaluate supplied class constructor
        #
        if not callable(cls):

            raise TypeError(f'resizeChildSpecs() expects a callable constructor ({type(cls).__name__} given)!')

        # Evaluate current size
        #
        currentSize = len(childSpecs)

        if size > currentSize:

            # Iterate through expanded size range
            #
            for i in range(currentSize, size, 1):

                skeletonSpec = cls()
                childSpecs.append(skeletonSpec)

        elif size < currentSize:

            # Iterate through contracted size range
            #
            for i in range(currentSize - 1, size - 1, -1):

                skeletonSpec = childSpecs.pop(i)
                self._bin.append(skeletonSpec)

        else:

            pass

        return childSpecs

    def resizeHierarchicalSpecs(self, size, topLevelSpec, cls=None):
        """
        Resizes the hierarchy for the supplied parent skeleton spec.
        This method is only intended for single chain hierarchies with no branches!

        :type size: int
        :type topLevelSpec: Union[skeletonspec.SkeletonSpec, List[skeletonspec.SkeletonSpec]]
        :type cls: Callable
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Evaluate supplied top-level spec
        #
        topLevelSpecs = None

        if isinstance(topLevelSpec, abstractspec.AbstractSpec):

            topLevelSpecs = topLevelSpec.children

        elif isinstance(topLevelSpec, MutableSequence):

            topLevelSpecs, topLevelSpec = topLevelSpec, None

        else:

            raise TypeError(f'resizeHierarchicalSpecs() expects a node spec ({type(topLevelSpec).__name__} given!)')

        # Evaluate supplied class constructor
        #
        if not callable(cls):

            raise TypeError(f'resizeHierarchicalSpecs() expects a callable constructor ({type(cls).__name__} given)!')

        # Resize hierarchy
        #
        parentSpec = topLevelSpecs
        hierarchy = []

        while len(hierarchy) != size:

            parentSpec, = self.resizeChildSpecs(1, parentSpec, cls=cls)
            hierarchy.append(parentSpec)

        # Remove all out-of-range descendants
        #
        lastSpec = hierarchy[-1]
        childSpecs = tuple(self.flattenSpecs(lastSpec.children, skipDisabled=False, skipPassthrough=False))

        for childSpec in reversed(childSpecs):

            parentSpec = childSpec.parent

            if isinstance(parentSpec, cls):

                index = parentSpec.children.index(childSpec)
                del parentSpec.children[index]

            log.info(f'Moving "{childSpec.name}" spec to bin for deletion!')
            self._bin.append(childSpec)

        return hierarchy

    def getAttachmentOptions(self):
        """
        Returns the attachment options for this component.

        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Check if parent exists
        #
        componentParent = self.componentParent()

        if componentParent is not None:

            return componentParent.skeleton(flatten=True)

        else:

            return []

    def getAttachmentSpec(self):
        """
        Returns the current attachment spec for this component.

        :rtype: skeletonspec.SkeletonSpec
        """

        attachmentSpecs = self.getAttachmentOptions()
        numAttachmentSpecs = len(attachmentSpecs)

        attachmentIndex = int(self.attachmentId)

        if 0 <= attachmentIndex < numAttachmentSpecs:

            return attachmentSpecs[attachmentIndex]

        else:

            return None

    def getAttachmentTargets(self):
        """
        Returns the attachment targets for this component.

        :rtype: Union[Tuple[mpynode.MPyNode, mpynode.MPyNode], Tuple[None, None]]
        """

        # Check if attachment spec exists
        #
        attachmentSpec = self.getAttachmentSpec()

        if isinstance(attachmentSpec, skeletonspec.SkeletonSpec):

            exportJoint = attachmentSpec.getNode(referenceNode=self.skeletonReference())
            exportDriver = attachmentSpec.driver.getDriver()

            return exportJoint, exportDriver

        else:

            return None, None

    def skeletonManager(self):
        """
        Returns an interface for the referenced skeleton.

        :rtype: rpc.MRPCClient
        """

        return rpc.__client__  # It's the responsibility of the dev to manage the remote standalone server!

    def skeletonReference(self):
        """
        Returns the skeleton reference node.

        :rtype: mpy.builtins.referencemixin.ReferenceMixin
        """

        return self.findControlRig().getSkeletonReference()

    def skeletonNamespace(self):
        """
        Returns the namespace for the referenced skeleton.

        :rtype: str
        """

        return self.skeletonReference().associatedNamespace()

    def isSkeletonDirty(self):
        """
        Evaluates if the skeleton specs are outdated.

        :rtype: bool
        """

        return self.userProperties.get(self.SKELETON_DIRTY_KEY, True)

    def markSkeletonDirty(self):
        """
        Marks the internal skeleton specs as dirty.

        :rtype: None
        """

        self.userProperties[self.SKELETON_DIRTY_KEY] = True

    def markSkeletonClean(self):
        """
        Marks the internal skeleton specs as clean.

        :rtype: None
        """

        self.userProperties[self.SKELETON_DIRTY_KEY] = False

    def skeleton(self, **kwargs):
        """
        Returns the skeleton specs for this component.

        :type flatten: bool
        :type topLevelOnly: bool
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Check if skeleton specs are clean
        #
        isDirty = self.isSkeletonDirty()
        isMeta = (self.componentStatus == self.Status.META)
        skeletonSpecs = self.userProperties.get(self.SKELETON_KEY, [])

        if isDirty and isMeta:

            log.info(f'Invalidating "{self}" skeleton specs...')
            skeletonSpecs = self.invalidateSkeleton(skeletonSpecs)

        # Check if skeleton specs require reorganizing
        #
        topLevelOnly = kwargs.pop('topLevelOnly', False)
        flatten = kwargs.pop('flatten', False)

        if topLevelOnly:

            flattenedSpecs = [list(self.flattenSpecs(skeletonSpec, **kwargs)) for skeletonSpec in skeletonSpecs]
            skeletonSpecs = [specs[0] for specs in flattenedSpecs if len(specs) >= 1]

        elif flatten:

            skeletonSpecs = list(self.flattenSpecs(skeletonSpecs, **kwargs))

        else:

            pass

        return skeletonSpecs

    def resizeSkeleton(self, size, parentSpec, hierarchical=False):
        """
        Resizes the supplied skeleton specs.

        :type size: int
        :type parentSpec: Union[skeletonspec.SkeletonSpec, List[skeletonspec.SkeletonSpec]]
        :type hierarchical: bool
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        if hierarchical:

            return self.resizeHierarchicalSpecs(size, parentSpec, cls=skeletonspec.SkeletonSpec)

        else:

            return self.resizeChildSpecs(size, parentSpec, cls=skeletonspec.SkeletonSpec)

    @abstractmethod
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        self.userProperties.pushBuffer()
        self.markSkeletonClean()

        return skeletonSpecs

    def reloadSkeleton(self):
        """
        Reloads the referenced skeleton for this component.

        :rtype: None
        """

        controlRig = self.findControlRig()
        controlRig.reloadSkeleton()

    def syncJoint(self, skeletonSpec, **kwargs):
        """
        Synchronizes the supplied skeleton spec with the associated joint from the referenced skeleton.

        :type skeletonSpec: skeletonspec.SkeletonSpec
        :key manager: rpc.MRPCClient
        :rtype: skeletonspec.SkeletonSpec
        """

        # Evaluate skeleton spec state
        #
        manager = kwargs.get('manager', self.skeletonManager())

        if skeletonSpec.enabled:

            # Check if associated export joint exists
            # If not, go ahead and bind a new export joint to the skeleton spec!
            #
            uuid = skeletonSpec.uuid.asString()
            exists = manager.doesNodeExist(uuid) if not stringutils.isNullOrEmpty(uuid) else False

            name = ''

            if exists:

                # Check if export joint requires renaming
                #
                fullPathName = manager.ls(uuid, long=True)[0]
                currentName = dagutils.stripAll(fullPathName)
                name = str(skeletonSpec.name)

                if currentName != name and not stringutils.isNullOrEmpty(name):

                    name = manager.renameNode(currentName, name)

                # Check if export joint requires reparenting
                #
                currentParents = manager.listRelatives(name, parent=True)
                currentParent = currentParents[0] if not stringutils.isNullOrEmpty(currentParents) else ''
                parent = getattr(skeletonSpec.parent, 'name', '')

                if currentParent != parent and not stringutils.isNullOrEmpty(parent):

                    manager.parentNode(name, parent, absolute=True)

            else:

                # Compose create arguments
                #
                kwargs = {'asNameAndUUID': True}

                if not stringutils.isNullOrEmpty(skeletonSpec.name):

                    kwargs['name'] = skeletonSpec.name

                parentSpec = skeletonSpec.parent
                parent = getattr(parentSpec, 'name', '')

                if not stringutils.isNullOrEmpty(parent):

                    kwargs['parent'] = parent

                # Create new export joint and bind to skeleton spec
                #
                log.info(f'Creating "{skeletonSpec.name}" skeleton spec!')
                name, uuid = manager.createNode('joint', **kwargs)
                skeletonSpec.name = name
                skeletonSpec.uuid = uuid

            # Update attributes
            #
            manager.setAttr(f'{name}.side', skeletonSpec.side.value)
            manager.setAttr(f'{name}.type', skeletonSpec.type.value)
            manager.setAttr(f'{name}.otherType', skeletonSpec.otherType, type='string')
            manager.setAttr(f'{name}.drawStyle', skeletonSpec.drawStyle.value)
            manager.setAttr(f'{name}.displayLocalAxis', kwargs.get('displayLocalAxis', True))

            # Update transform matrix
            #
            translation = skeletonSpec.matrix.translation(om.MSpace.kTransform)
            rotateOrder = manager.getAttr(f'{name}.rotateOrder')
            eulerRotation = skeletonSpec.matrix.rotation(asQuaternion=False)
            eulerRotation.reorderIt(rotateOrder)

            manager.setAttr(f'{name}.translate', *tuple(translation), type='double3')
            manager.setAttr(f'{name}.rotate', *tuple(map(math.degrees, eulerRotation)), type='double3')

        else:

            # Check if associated export joint still exists
            # If yes, go ahead and delete the export joint associated with the skeleton spec!
            #
            uuid = skeletonSpec.uuid.asString()
            exists = manager.doesNodeExist(uuid) if not stringutils.isNullOrEmpty(uuid) else False

            if exists:

                fullPathName = manager.ls(uuid, long=True)[0]
                children = manager.listRelatives(fullPathName, children=True, path=True)

                if not stringutils.isNullOrEmpty(children):

                    manager.parentNode(*children, world=True, absolute=True)

                log.info(f'Deleting "{fullPathName}" export joint!')
                manager.deleteNode(fullPathName)
                del skeletonSpec.uuid

        return skeletonSpec

    def cacheSkeleton(self):
        """
        Goes through and ensures the referenced skeleton matches the internal skeleton specs.

        :rtype: None
        """

        # Iterate through skeleton specs
        #
        skeletonSpecs = self.skeleton(flatten=True, skipDisabled=True)
        referenceNode = self.skeletonReference()

        for skeletonSpec in skeletonSpecs:

            skeletonSpec.cacheNode(referenceNode=referenceNode)

    def parentSkeleton(self):
        """
        Parents the skeleton for this component.

        :rtype: None
        """

        # Check if skeleton exists
        #
        skeletonSpecs = self.skeleton(topLevelOnly=True)
        hasSkeleton = len(skeletonSpecs) > 0

        if not hasSkeleton:

            return

        # Check if attachment spec exists
        #
        attachmentSpec = self.getAttachmentSpec()
        hasAttachment = isinstance(attachmentSpec, skeletonspec.SkeletonSpec)

        if not hasAttachment:

            return

        # Iterate through top-level skeleton specs
        #
        manager = self.skeletonManager()

        for skeletonSpec in skeletonSpecs:

            # Check if associated export joint exists
            #
            skeletonExists = manager.doesNodeExist(skeletonSpec.uuid.asString())
            attachmentExists = manager.doesNodeExist(attachmentSpec.uuid.asString())

            if not (skeletonExists and attachmentExists):

                log.warning(f'Unable to parent "{skeletonSpec.name}" export joint to "{attachmentSpec.name}" target!')
                return

            # Unparent export joint
            #
            manager.parentNode(skeletonSpec.name, attachmentSpec.name, absolute=True)

    def unparentSkeleton(self):
        """
        Un-parents the skeleton for this component.

        :rtype: None
        """

        # Check if skeleton exists
        #
        skeletonSpecs = self.skeleton(topLevelOnly=True)
        hasSkeleton = len(skeletonSpecs) > 0

        if not hasSkeleton:

            return

        # Iterate through top-level skeletons specs
        #
        manager = self.skeletonManager()

        for skeletonSpec in skeletonSpecs:

            # Check if associated export joint exists
            #
            uuid = skeletonSpec.uuid.asString()
            exists = manager.doesNodeExist(uuid)

            if not exists:

                log.warning(f'Unable to unparent "{skeletonSpec.name}" export joint!')
                return

            # Parent export joint
            #
            fullPathName = manager.ls(uuid, long=True)[0]
            manager.parentNode(fullPathName, world=True, absolute=True)

    def bindSkeleton(self):
        """
        Binds the skeleton for this component.

        :rtype: None
        """

        # Reparent export skeleton
        #
        self.parentSkeleton()

        # Constrain export skeleton
        #
        referenceNode = self.skeletonReference()

        for skeletonSpec in self.skeleton(flatten=True):

            skeletonSpec.driver.bind(referenceNode=referenceNode)

    def unbindSkeleton(self):
        """
        Un-binds the skeleton for this component.

        :rtype: None
        """

        # Unconstrain export skeleton
        #
        referenceNode = self.skeletonReference()

        for skeletonSpec in self.skeleton(flatten=True):

            skeletonSpec.driver.unbind(referenceNode=referenceNode)

        # Un-parent export skeleton
        #
        self.unparentSkeleton()

    def flushSkeleton(self, save=False):
        """
        Deletes any joints that are waiting in the bin.

        :type save: boolean
        :rtype: None
        """

        # Empty skeleton bin
        #
        manager = self.skeletonManager()

        while len(self._bin) > 0:

            # Check if skeleton spec is valid
            #
            skeletonSpec = self._bin.pop()
            isValid = skeletonSpec.uuid.valid()

            if not isValid:

                continue

            # Check if export joint still exists
            #
            uuid = skeletonSpec.uuid.asString()
            exists = manager.doesNodeExist(uuid)

            if not exists:

                continue

            # Unparent children from export joint and delete it
            #
            fullPathName = manager.ls(uuid, long=True)[0]
            children = manager.listRelatives(fullPathName, children=True, path=True)

            if not stringutils.isNullOrEmpty(children):

                manager.parentNode(*children, world=True, absolute=True)

            log.info(f'Flushing "{fullPathName}" skeleton spec!')
            manager.deleteNode(fullPathName)
            del skeletonSpec.uuid

        # Check if changes require saving
        #
        if save:

            manager.save()

    def prepareToBuildSkeleton(self):
        """
        Notifies the component that a skeleton is about to be built.

        :rtype: None
        """

        # Get skeleton reference path
        #
        controlRig = self.findControlRig()
        referenceNode =controlRig.getSkeletonReference()

        referencePath = os.path.abspath(referenceNode.filePath())

        # Check if referenced skeleton is already open
        #
        manager = self.skeletonManager()
        currentPath = os.path.abspath(manager.file(query=True, sceneName=True))

        isOpen = referencePath == currentPath

        if not isOpen:

            log.info(f'Opening referenced skeleton: {referencePath}')
            manager.open(referencePath)

        else:

            log.debug(f'Referenced skeleton is already open...')

    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        # Iterate through skeleton specs and sync export joints
        #
        manager = self.skeletonManager()
        skeletonSpecs = self.skeleton(flatten=True, skipDisabled=False, skipPassthrough=True)

        for skeletonSpec in skeletonSpecs:

            self.syncJoint(skeletonSpec, manager=manager)

    def skeletonCompleted(self):
        """
        Notifies the component that the skeleton is complete.

        :rtype: None
        """

        self.flushSkeleton(save=True)
        self.userProperties.pushBuffer()

    def arePivotsDirty(self):
        """
        Evaluates if the pivot specs are outdated.

        :rtype: bool
        """

        return self.userProperties.get(self.PIVOTS_DIRTY_KEY, True)

    def markPivotsDirty(self):
        """
        Marks the internal pivot specs as dirty.

        :rtype: None
        """

        self.userProperties[self.PIVOTS_DIRTY_KEY] = True

    def markPivotsClean(self):
        """
        Marks the internal pivot specs as clean.

        :rtype: None
        """

        self.userProperties[self.PIVOTS_DIRTY_KEY] = False

    def resizePivots(self, size, pivotSpecs):
        """
        Resizes the supplied pivot specs to the specified size.

        :type size: int
        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: List[pivotspec.PivotSpec]
        """

        return self.resizeChildSpecs(size, pivotSpecs, cls=pivotspec.PivotSpec)

    def pivots(self, **kwargs):
        """
        Returns the pivot specs for this component.

        :type flatten: bool
        :type skipDisabled: bool
        :rtype: List[pivotspec.PivotSpec]
        """

        # Check if pivot specs are clean
        #
        isDirty = self.arePivotsDirty()
        isMeta = (self.componentStatus == self.Status.META)
        pivotSpecs = self.userProperties.get(self.PIVOTS_KEY, [])

        if isDirty and isMeta:

            pivotSpecs = self.invalidatePivots(pivotSpecs, **kwargs)

        # Check if pivot specs require reorganizing
        #
        flatten = kwargs.pop('flatten', False)
        skipDisabled = kwargs.get('skipDisabled', False)

        if flatten:

            pivotSpecs = list(self.flattenSpecs(pivotSpecs, **kwargs))

        elif skipDisabled:

            pivotSpecs = list(filter(lambda spec: spec.enabled, pivotSpecs))

        else:

            pass

        return pivotSpecs

    def invalidatePivots(self, pivotSpecs, **kwargs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: List[pivotspec.PivotSpec]
        """

        self.userProperties.pushBuffer()
        self.markPivotsClean()

        return pivotSpecs

    def prepareToBuildPivots(self):
        """
        Notifies the component that pivots are about to be built.

        :rtype: None
        """

        # Create organizational group
        #
        if self.pivotsGroup.isNull():

            pivotsGroupName = self.formatName(subname='Pivots', type='transform')
            pivotsGroup = self.scene.createNode('transform', name=pivotsGroupName, parent=self)
            self.pivotsGroup = pivotsGroup.object()

            pivotsGroup.lock()

    def buildPivots(self):
        """
        Builds the pivots for this component.

        :rtype: Union[Tuple[mpynode.MPyNode], None]
        """

        # Iterate through pivot specs
        #
        pivotSpecs = self.pivots(flatten=True, skipDisable=True)
        pivotsGroup = self.scene(self.pivotsGroup)
        referenceNode = self.skeletonReference()

        numPivots = len(pivotSpecs)
        pivots = [None] * numPivots

        for (i, pivotSpec) in enumerate(pivotSpecs):

            # Check if pivot already exists
            #
            if pivotSpec.exists():

                pivots[i] = pivotSpec.getNode(referenceNode=referenceNode)
                continue

            # Create new pivot
            #
            parent = pivotSpec.parent.getNode() if isinstance(pivotSpec.parent, pivotspec.PivotSpec) else pivotsGroup

            pivot = self.scene.createNode('transform', name=pivotSpec.name, parent=parent)
            pivot.displayLocalAxis = True
            pivot.displayHandle = True
            pivot.setMatrix(pivotSpec.matrix, skipScale=True)
            pivotSpec.uuid = pivot.uuid()

            pivots[i] = pivot

            # Check if shape data exists
            # If not, go ahead and create a default point helper
            #
            hasShape = not stringutils.isNullOrEmpty(pivotSpec.shapes)

            if hasShape:

                pivot.loadShapes(pivotSpec.shapes)

            else:

                pivot.addPointHelper('cross', 'axisTripod', size=20.0)

            # Bind pivot
            #
            pivotSpec.driver.bind(referenceNode=referenceNode)

        return pivots

    def pivotsCompleted(self):
        """
        Notifies the component that the pivots are complete.

        :rtype: None
        """

        self.userProperties.pushBuffer()

    def cachePivots(self, delete=False):
        """
        Updates the internal pivot specs.

        :type delete: bool
        :rtype: None
        """

        # Iterate through pivot specs
        #
        pivotSpecs = self.pivots(flatten=True, skipDisabled=True)
        referenceNode = self.skeletonReference()

        for pivotSpec in pivotSpecs:

            pivotSpec.cacheNode(referenceNode=referenceNode, delete=delete)

    def addNodeAddedCallback(self):
        """
        Creates a node added callback to capture any newly created nodes.

        :rtype: None
        """

        # Check for redundancy
        #
        if self._callbackID is not None:

            self.removeNodeAddedCallback()

        # Create new callback
        #
        self._callbackID = om.MDGMessage.addNodeAddedCallback(self.nodeAdded, 'dependNode')

    def removeNodeAddedCallback(self):
        """
        Removes the node added callback.

        :rtype: None
        """

        # Check for redundancy
        #
        if self._callbackID is None:

            return

        # Try and remove callback
        #
        try:

            om.MDGMessage.removeCallback(self._callbackID)

        except RuntimeError as exception:

            log.debug(exception)

        finally:

            self._callbackID = None

    def nodeAdded(self, dependNode, clientData=None):
        """
        Callback method responsible for archiving any non-DAG nodes within the hyper layout node.

        :type dependNode: om.MObject
        :type clientData: object
        :rtype: None
        """

        # Check for none type
        #
        if dependNode is None:

            return

        # Check if this is a non-DAG node
        #
        if not dependNode.hasFn(om.MFn.kDagNode) and not dependNode.hasFn(om.MFn.kHyperLayout):

            self._pending.append(om.MObjectHandle(dependNode))

        else:

            log.debug('Skipping DAG node: %s' % om.MFnDependencyNode(dependNode).name())

    def organizeNodes(self):
        """
        Commits any pending dependency nodes to this container.

        :rtype: None
        """

        # Add pending members to this container
        #
        hyperLayout = self.getHyperLayout()

        while len(self._pending):

            # Check if node is still alive
            #
            handle = self._pending.popleft()

            if not handle.isAlive():

                continue

            # Check if node is an IK solver
            # If so, go ahead and skip it since these are meant to be shared!
            #
            node = handle.object()
            isIKSolver = node.hasFn(om.MFn.kIkSolver)

            if isIKSolver:

                continue

            # Add new member
            #
            hyperLayout.addMember(node)

    def prepareToBuildRig(self):
        """
        Notifies the component that the rig is about to be built.

        :rtype: None
        """

        # Create node added callback
        #
        self.addNodeAddedCallback()

        # Create organizational groups
        #
        if self.controlsGroup.isNull():

            controlsGroupName = self.formatName(subname='Controls', type='transform')
            controlsGroup = self.scene.createNode('transform', name=controlsGroupName, parent=self)
            self.controlsGroup = controlsGroup.object()

        if self.jointsGroup.isNull():

            jointsGroupName = self.formatName(subname='Joints', type='transform')
            jointsGroup = self.scene.createNode('transform', name=jointsGroupName, parent=self)
            jointsGroup.visibility = False
            self.jointsGroup = jointsGroup.object()

        if self.privateGroup.isNull():

            privateGroupName = self.formatName(subname='Private', type='transform')
            privateGroup = self.scene.createNode('transform', name=privateGroupName, parent=self)
            privateGroup.visibility = False
            self.privateGroup = privateGroup.object()

        if not self.pivotsGroup.isNull():

            pivotsGroup = self.scene(self.privateGroup)
            pivotsGroup.visibility = False

    @abstractmethod
    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        pass

    def rigCompleted(self):
        """
        Notifies the component that the rig is completed.

        :rtype: None
        """

        self.removeNodeAddedCallback()
        self.organizeNodes()
        self.bindSkeleton()
        self.cacheSkeleton()

    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.

        :rtype: None
        """

        pass

    def deleteRig(self):
        """
        Removes all control rig related nodes.

        :rtype: None
        """

        self.unbindSkeleton()
        self.deleteMembers()
    # endregion
