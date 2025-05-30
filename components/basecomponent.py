from maya.api import OpenMaya as om
from abc import abstractmethod
from collections import deque
from ..abstract import abstractcomponent
from ..libs import Side, skeletonspec, pivotspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BaseComponent(abstractcomponent.AbstractComponent):
    """
    Overload of `AbstractComponent` that outlines rig component construction.
    """

    # region Dunderscores
    __default_mirror_matrices__ = {
        Side.CENTER: om.MMatrix.kIdentity,
        Side.LEFT: om.MMatrix.kIdentity,
        Side.RIGHT: om.MMatrix(
            [
                (-1.0, 0.0, 0.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        ),
        Side.NONE: om.MMatrix.kIdentity
    }

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
    # endregion

    # region Methods
    def save(self):
        """
        Commits any changes made to the internal properties.

        :rtype: None
        """

        self.userProperties.pushBuffer()

    @staticmethod
    def resizeSpecs(size, specs, cls=None):
        """
        Resizes the supplied skeleton specs to the specified size.

        :type size: int
        :type specs: List[Any]
        :type cls: Callable
        :rtype: List[Any]
        """

        # Check if class is callable
        #
        if not callable(cls):

            return

        # Evaluate current size
        #
        currentSize = len(specs)

        if size > currentSize:

            difference = size - currentSize
            newSpecs = [cls(i) for i in range(difference)]

            specs.extend(newSpecs)

        elif size < currentSize:

            del specs[size:]

        else:

            pass

        return specs

    @classmethod
    def flattenSpecs(cls, skeletonSpecs, **kwargs):
        """
        Returns a generator that yields all skeleton specs.

        :type skeletonSpecs: Union[skeletonspec.SkeletonSpec, List[skeletonspec.SkeletonSpec]]
        :key skipDisabled: bool
        :rtype: Iterator[skeletonspec.SkeletonSpec]
        """

        # Evaluate supplied argument
        #
        if isinstance(skeletonSpecs, skeletonspec.SkeletonSpec):

            skeletonSpecs = [skeletonSpecs]

        # Iterate through skeleton specs
        #
        skipDisabled = kwargs.get('skipDisabled', True)

        for skeletonSpec in skeletonSpecs:

            # Evaluate item type
            #
            if not isinstance(skeletonSpec, skeletonspec.SkeletonSpec):

                continue

            # Check if skeleton spec is enabled
            #
            if (skeletonSpec.enabled and skipDisabled) or not skipDisabled:

                yield skeletonSpec

            # Repeat for children and group skeleton specs!
            #
            yield from cls.flattenSpecs(skeletonSpec.children, **kwargs)

            for (groupId, groupSpecs) in skeletonSpec.groups.items():

                yield from cls.flattenSpecs(groupSpecs, **kwargs)

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

    def skeletonSpecs(self, **kwargs):
        """
        Returns the current skeleton specs.

        :key flatten: bool
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Check if skeleton specs are clean
        #
        isDirty = self.userProperties.get(self.SKELETON_DIRTY_KEY, True)
        skeletonSpecs = self.userProperties[self.SKELETON_KEY]

        if isDirty:

            self.invalidateSkeletonSpecs(skeletonSpecs)

        # Check if skeleton specs require flattening
        #
        flatten = kwargs.pop('flatten', False)

        if flatten:

            skeletonSpecs = list(self.flattenSpecs(skeletonSpecs, **kwargs))

        return skeletonSpecs

    def resizeSkeletonSpecs(self, size, specs):
        """
        Resizes the supplied skeleton specs to the specified size.

        :type size: int
        :type specs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        return self.resizeSpecs(size, specs, cls=skeletonspec.SkeletonSpec)

    @abstractmethod
    def invalidateSkeletonSpecs(self, skeletonSpecs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: None
        """

        self.markSkeletonClean()
        self.save()

    def prepareToBuildSkeleton(self):
        """
        Notifies the component that a skeleton is about to be built.

        :rtype: None
        """

        pass

    @abstractmethod
    def buildSkeleton(self):
        """
        Builds the skeleton for this component.

        :rtype: Tuple[mpynode.MPyNode]
        """

        pass

    def skeletonCompleted(self):
        """
        Notifies the component that the skeleton is complete.

        :rtype: None
        """

        self.componentStatus = self.Status.SKELETON
        self.save()

    def cacheSkeleton(self, delete=False):
        """
        Updates the internal skeleton specs.

        :type delete: bool
        :rtype: None
        """

        # Update skeleton matrices
        #
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)

        for skeletonSpec in skeletonSpecs:

            log.info(f'Caching "{skeletonSpec.name}" skeleton spec...')
            skeletonSpec.cacheMatrix()

        # Check if skeleton should be deleted
        #
        if delete:

            for skeletonSpec in reversed(skeletonSpecs):

                skeletonSpec.deleteNode()

        # Save changes
        #
        self.save()

    def parentSkeleton(self):
        """
        Parents the skeleton for this component.

        :rtype: None
        """

        # Check if attachment target exists
        #
        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        if parentExportJoint is None:

            return

        # Re-parent export skeleton
        #
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)
        firstSkeletonSpec = skeletonSpecs[0]

        exportJoint = firstSkeletonSpec.getNode()

        if exportJoint is not None:

            exportJoint.setParent(parentExportJoint, absolute=True)

        else:

            log.warning(f'Unable to parent "{firstSkeletonSpec.name}" joint!')

    def unparentSkeleton(self):
        """
        Un-parents the skeleton for this component.

        :rtype: None
        """

        # Un-parent export skeleton
        #
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)
        firstSkeletonSpec = skeletonSpecs[0]

        exportJoint = firstSkeletonSpec.getNode()

        if exportJoint is not None:

            exportJoint.setParent(None, absolute=True)

        else:

            log.warning(f'Unable to un-parent "{firstSkeletonSpec.name}" joint!')

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
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)
        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        for skeletonSpec in skeletonSpecs:

            # Check if export joint exists
            #
            exportJoint = skeletonSpec.getNode()

            if exportJoint is None:

                log.error(f'Cannot locate export joint: {skeletonSpec.driver}')
                continue

            # Remove any pre-rotations
            #
            exportJoint.removeConstraints()
            exportJoint.unfreezePivots()

            # Check if export driver exists
            #
            exportDriver = skeletonSpec.getDriver()

            if exportDriver is None:

                log.error(f'Cannot locate export driver: {skeletonSpec.driver}')
                continue

            # Constrain export joint
            #
            log.info(f'Constraining "{skeletonSpec.driver}" > "{skeletonSpec.name}"')
            maintainOffset = self.Side(exportJoint.side) == self.Side.RIGHT

            constraint = exportJoint.addConstraint('transformConstraint', [exportDriver], maintainOffset=maintainOffset)
            constraint.hiddenInOutliner = True

    def unbindSkeleton(self):
        """
        Un-binds the skeleton for this component.

        :rtype: None
        """

        # De-constrain export skeleton
        #
        skeletonSpecs = self.skeletonSpecs(flatten=True, skipDisabled=True)

        for skeletonSpec in skeletonSpecs:

            # Check if export joint still exists
            #
            exportJoint = skeletonSpec.getNode()

            if exportJoint is None:

                log.warning(f'Unable to locate export joint: {skeletonSpec.name}')
                continue

            # Remove constraints
            #
            exportJoint.removeConstraints()

            # Reassign transform matrix
            #
            matrix = skeletonSpec.getMatrix(asTransformationMatrix=True)
            exportJoint.setMatrix(matrix)

        # Un-parent export skeleton
        #
        self.unparentSkeleton()

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

    def pivotSpecs(self):
        """
        Returns the current pivot specs.

        :rtype: Dict[str, Any]
        """

        # Check if pivot specs are clean
        #
        isDirty = self.userProperties.get(self.PIVOTS_DIRTY_KEY, True)
        pivotSpecs = self.userProperties[self.PIVOTS_KEY]

        if isDirty:

            self.invalidatePivotSpecs(pivotSpecs)

        # Return clean skeleton specs
        #
        return pivotSpecs

    def resizePivotSpecs(self, size, specs):
        """
        Resizes the supplied pivot specs to the specified size.

        :type size: int
        :type specs: List[pivotspec.PivotSpec]
        :rtype: List[pivotspec.PivotSpec]
        """

        return self.resizeSpecs(size, specs, cls=pivotspec.PivotSpec)

    def invalidatePivotSpecs(self, pivotSpecs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: None
        """

        self.markPivotsClean()
        self.save()

    def prepareToBuildPivots(self):
        """
        Notifies the component that pivots are about to be built.

        :rtype: None
        """

        pass

    def buildPivots(self):
        """
        Builds the pivots for this component.

        :rtype: Union[Tuple[mpynode.MPyNode], None]
        """

        pass

    def pivotsCompleted(self):
        """
        Notifies the component that the pivots are complete.

        :rtype: None
        """

        self.save()

    def cachePivots(self, delete=False):
        """
        Updates the internal pivot specs.

        :type delete: bool
        :rtype: None
        """

        # Update pivot matrices
        #
        pivotSpecs = self.pivotSpecs()

        for pivotSpec in pivotSpecs:

            pivotSpec.cacheMatrix(delete=delete)

        # Save changes
        #
        self.save()

    def getAttachmentOptions(self):
        """
        Returns the attachment options for this component.

        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Check if parent exists
        #
        componentParent = self.componentParent()

        if componentParent is not None:

            return componentParent.skeletonSpecs(flatten=True)

        else:

            return []

    def getAttachmentTargets(self):
        """
        Returns the attachment targets for this component.

        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
        """

        # Check if attachment index is in range
        #
        skeletonSpecs = self.getAttachmentOptions()
        numSkeletonSpecs = len(skeletonSpecs)

        attachmentIndex = int(self.attachmentId)

        if 0 <= attachmentIndex < numSkeletonSpecs:

            skeletonSpec = skeletonSpecs[attachmentIndex]
            return self.scene(skeletonSpec.uuid), self.scene(skeletonSpec.driver)

        else:

            return None, None

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
        self.cacheSkeleton(delete=False)

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
