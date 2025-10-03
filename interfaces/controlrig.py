import os

from maya.api import OpenMaya as om
from mpy import mpyattribute
from dcc.naming import namingutils
from ..abstract import abstractinterface, abstractcomponent
from ..libs import Status, skeletonmanager, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ControlRig(abstractinterface.AbstractInterface):
    """
    Overload of `AbstractInterface` that interfaces with control rigs.
    """

    # region Enums
    Status = Status
    # endregion

    # region Dunderscores
    __version__ = 1.0
    # endregion

    # region Attributes
    rigName = mpyattribute.MPyAttribute('rigName', attributeType='str')
    rigVersion = mpyattribute.MPyAttribute('rigVersion', attributeType='float', min=0.0)
    rigBoundingBoxMinX = mpyattribute.MPyAttribute('rigBoundingBoxMinX', attributeType='float')
    rigBoundingBoxMinY = mpyattribute.MPyAttribute('rigBoundingBoxMinY', attributeType='float')
    rigBoundingBoxMinZ = mpyattribute.MPyAttribute('rigBoundingBoxMinZ', attributeType='float')
    rigBoundingBoxMin = mpyattribute.MPyAttribute('rigBoundingBoxMin', attributeType='compound', children=('rigBoundingBoxMinX', 'rigBoundingBoxMinY', 'rigBoundingBoxMinZ'))
    rigBoundingBoxMaxX = mpyattribute.MPyAttribute('rigBoundingBoxMaxX', attributeType='float')
    rigBoundingBoxMaxY = mpyattribute.MPyAttribute('rigBoundingBoxMaxY', attributeType='float')
    rigBoundingBoxMaxZ = mpyattribute.MPyAttribute('rigBoundingBoxMaxZ', attributeType='float')
    rigBoundingBoxMax = mpyattribute.MPyAttribute('rigBoundingBoxMax', attributeType='compound', children=('rigBoundingBoxMaxX', 'rigBoundingBoxMaxY', 'rigBoundingBoxMaxZ'))
    rootComponent = mpyattribute.MPyAttribute('rootComponent', attributeType='message')
    componentsGroup = mpyattribute.MPyAttribute('componentsGroup', attributeType='message')
    propsGroup = mpyattribute.MPyAttribute('propsGroup', attributeType='message')
    meshesGroup = mpyattribute.MPyAttribute('meshesGroup', attributeType='message')
    skeletonReference = mpyattribute.MPyAttribute('skeletonReference', attributeType='message')
    skinReference = mpyattribute.MPyAttribute('skinReference', attributeType='message', array=True)

    @rigName.changed
    def rigName(self, rigName):
        """
        Changed method that notifies any rig name changes.

        :type rigName: str
        :rtype: None
        """

        name = namingutils.formatName(name=rigName, type='transform')
        self.setName(name)
    # endregion

    # region Methods
    @classmethod
    def create(cls, *args, **kwargs):
        """
        Returns a new dependency node of the specified type with this extension.

        :key name: Union[str, Dict[str, Any]]
        :key parent: Union[str, om.MObject, om.MDagPath, None]
        :key filePath: str
        :rtype: ControlRig
        """

        # Call parent method
        #
        parent = kwargs.get('parent', None)

        controlRig = super(ControlRig, cls).create('transform', parent=parent)
        controlRig.rigName = kwargs.get('rigName', '')
        controlRig.rigVersion = kwargs.get('rigVersion', cls.__version__)

        # Create organizational groups and lock them
        # Locking them will prevent Maya from deleting any empty groups!
        #
        componentsGroup = cls.scene.createNode('transform', name='Components_GRP', parent=controlRig)
        propsGroup = cls.scene.createNode('transform', name='Props_GRP', parent=controlRig)
        meshesGroup = cls.scene.createNode('transform', name='Meshes_GRP', parent=controlRig)

        controlRig.componentsGroup = componentsGroup.object()
        controlRig.propsGroup = propsGroup.object()
        controlRig.meshesGroup = meshesGroup.object()

        componentsGroup.lock()
        propsGroup.lock()
        meshesGroup.lock()

        # Create skeleton reference
        #
        referencePath = kwargs.get('referencePath', '')

        if os.path.isfile(referencePath):

            skeletonReference = cls.scene.createReference(referencePath, namespace=':')  # Please Lord...forgive me for what I am about to do...
            skeletonReference.unload()

            controlRig.skeletonReference = skeletonReference.object()

        # Create root component
        #
        controlRig.createRootComponent()

        return controlRig

    def update(self, force=False):
        """
        Updates the control rig's component's internal specs.

        :type force: bool
        :rtype: bool
        """

        # Evaluate rig version
        #
        isUpToDate = self.rigVersion >= 1.0

        if isUpToDate and not force:

            return True

        # Evaluate rig state
        #
        rootComponent = self.findRootComponent()
        isRig = (rootComponent.componentStatus == self.Status.RIG)

        if not isRig:

            log.warning('Components can only be updated from the rig state!')
            return False

        # Iterate through components and repair skeleton specs
        #
        for component in self.walkComponents():

            component.repairSkeleton(force=force)
            component.repairPivots(force=force)

        # Update rig version
        #
        self.rigVersion = 1.0

        return True

    def getRigBounds(self):
        """
        Returns the bounding box for this rig.

        :rtype: om.MBoundingBox
        """

        rigBoundingBoxMin = om.MPoint(self.rigBoundingBoxMin)
        rigBoundingBoxMax = om.MPoint(self.rigBoundingBoxMax)
        difference = (rigBoundingBoxMax - rigBoundingBoxMin)  # type: om.MVector

        if difference.isEquivalent(om.MVector.kZeroVector):

            rigBoundingBox = setuputils.getBoundingBoxByTypeName(typeName='mesh')
            self.rigBoundingBoxMin = rigBoundingBox.min
            self.rigBoundingBoxMax = rigBoundingBox.max

            return self.getRigBounds()

        else:

            return om.MBoundingBox(rigBoundingBoxMin, rigBoundingBoxMax)

    def getRigWidthAndHeight(self):
        """
        Returns the width and height for this rig.
        TODO: Add support for Y-Up rigs!

        :rtype: Tuple[float, float]
        """

        rigBounds = self.getRigBounds()
        width, height = max(rigBounds.width, rigBounds.height), rigBounds.depth  # Rigs are built in Z-Up and Z correlates with depth!

        return width, height

    def getRigScale(self, decimals=2):
        """
        Returns the scalar difference for this rig.

        :type decimals: bool
        :rtype: float
        """

        width, height = self.getRigWidthAndHeight()
        scale = round(height / 221.51626014709473, decimals)  # This value comes from the first rig I built!

        if scale > 0.0:

            return scale

        else:

            return 1.0

    def getRigStatus(self):
        """
        Returns the current rig status.

        :rtype: Status
        """

        return self.Status(self.findRootComponent().componentStatus)

    def getSkeletonManager(self):
        """
        Returns an interface for the referenced skeleton.

        :rtype: skeletonmanager.SkeletonManager
        """

        return skeletonmanager.SkeletonManager(self, referenceNode=self.getSkeletonReference())

    def hasReferencedSkeleton(self):
        """
        Evaluates if this control rig has a referenced skeleton.

        :rtype: bool
        """

        return not self.skeletonReference.isNull()

    def getSkeletonReference(self):
        """
        Returns the skeleton reference node.

        :rtype: Union[mpy.builtins.referencemixin.ReferenceMixin, None]
        """

        if self.hasReferencedSkeleton():

            return self.scene(self.skeletonReference)

        else:

            return None

    def loadSkeleton(self, clearEdits=False):
        """
        Reloads the referenced skeleton for this component.

        :type clearEdits: bool
        :rtype: None
        """

        manager = self.getSkeletonManager()
        manager.load(clearEdits=clearEdits)

    def unloadSkeleton(self, clearEdits=False):
        """
        Reloads the referenced skeleton for this component.

        :type clearEdits: bool
        :rtype: None
        """

        manager = self.getSkeletonManager()
        manager.unload(clearEdits=clearEdits)

    def saveSkeleton(self):
        """
        Pushes any skeleton spec changes to the referenced skeleton.

        :rtype: None
        """

        manager = self.getSkeletonManager()
        manager.save()

    def hasRootComponent(self):
        """
        Evaluates whether this control rig has a root component.

        :rtype: bool
        """

        return not self.rootComponent.isNull()

    def createRootComponent(self):
        """
        Creates a new root component for this control rig.
        If a root component already exists then that instance is returned instead!

        :rtype: rigotron.components.rootComponent.RootComponent
        """

        # Redundancy check
        #
        if self.hasRootComponent():

            return self.scene(self.rootComponent)

        # Create new root component
        #
        rootComponent = self.componentManager.createComponent('RootComponent', parent=self.componentsGroup)
        self.rootComponent = rootComponent.object()

        return rootComponent

    def findRootComponent(self):
        """
        Returns the root component for this control rig.

        :rtype: rigotron.components.rootComponent.RootComponent
        """

        if self.hasRootComponent():

            return self.scene(self.rootComponent)

        else:

            return None

    def createComponent(self, typeName, parent=None):
        """
        Adds a new component to this control rig.

        :type typeName: str
        :type parent: abstractcomponent.AbstractComponent
        :rtype: abstractcomponent.AbstractComponent
        """

        # Create new component
        #
        component = self.componentFactory.createComponent(typeName)

        # Assign to supplied parent
        # If there is no parent then use the root component
        #
        if parent is not None:

            component.parent = parent.object()

        else:

            component.parent = self.rootComponent.object()

        return component

    def walkComponents(self):
        """
        Returns a generator that yields all components derived from this rig.

        :rtype: Iterator[abstractcomponent.AbstractComponent]
        """

        rootComponent = self.scene(self.rootComponent)

        yield rootComponent
        yield from rootComponent.iterComponentDescendants()
    # endregion
