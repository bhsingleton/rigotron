from maya.api import OpenMaya as om
from mpy import mpyattribute
from dcc.naming import namingutils
from ..abstract import abstractinterface, abstractcomponent
from ..libs import Status

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ControlRig(abstractinterface.AbstractInterface):
    """
    Overload of `AbstractInterop` that interfaces with control rigs.
    """

    # region Enums
    Status = Status
    # endregion

    # region Attributes
    rigName = mpyattribute.MPyAttribute('rigName', attributeType='str')
    rigHeight = mpyattribute.MPyAttribute('rigHeight', attributeType='float')
    rigRadius = mpyattribute.MPyAttribute('rigRadius', attributeType='float')
    rootComponent = mpyattribute.MPyAttribute('rootComponent', attributeType='message')
    componentsGroup = mpyattribute.MPyAttribute('componentsGroup', attributeType='message')
    propsGroup = mpyattribute.MPyAttribute('propsGroup', attributeType='message')
    meshesGroup = mpyattribute.MPyAttribute('meshesGroup', attributeType='message')

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

        # Cache rig bounds for component use
        # We can use these values to derive the scale factor for controller shapes!
        #
        rigBounds = cls.getRigBounds()

        controlRig.rigHeight = rigBounds.depth
        controlRig.rigRadius = max(rigBounds.width, rigBounds.height) * 0.5

        # Create root component
        #
        controlRig.createRootComponent()

        return controlRig

    @classmethod
    def getRigBounds(cls):
        """
        Estimates the size of the rig based on the global bounding-box.

        :rtype: om.MBoundingBox
        """

        boundingBox = om.MBoundingBox(om.MPoint(-0.5, -0.5, -0.5), om.MPoint(0.5, 0.5, 0.5))

        for mesh in cls.scene.iterNodesByTypeName('mesh'):

            boundingBox.expand(mesh.boundingBox)

        return boundingBox

    def getRigScale(self, decimals=2):
        """
        Returns the scalar difference for this rig.

        :type decimals: bool
        :rtype: float
        """

        scale = round(self.rigHeight / 221.51626014709473, decimals)  # This value comes from the first rig I built!

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
