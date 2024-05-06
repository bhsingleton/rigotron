import os
import re
import getpass

from abc import abstractmethod
from collections import deque
from time import strftime, gmtime
from maya.api import OpenMaya as om
from dcc.naming import namingutils
from dcc.maya.libs import plugutils
from mpy import mpynodeextension, mpyattribute
from mpy.abstract import mabcmeta
from ..libs import Side, Type, Style, Status, componentfactory

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractComponent(mpynodeextension.MPyNodeExtension, metaclass=mabcmeta.MABCMeta):
    """
    Overload of `MPyNodeExtension` that outlines rig component parent/child relationships.
    """

    # region Constants
    PIVOTS_KEY = 'pivots'
    PIVOTS_DIRTY_KEY = 'isPivotsDirty'
    SKELETON_KEY = 'skeleton'
    SKELETON_DIRTY_KEY = 'isSkeletonDirty'
    # endregion

    # region Enums
    Side = Side
    Type = Type
    Style = Style
    Status = Status
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = ''
    __default_mirror_matrices__ = {
        Side.LEFT: om.MMatrix.kIdentity,
        Side.RIGHT: om.MMatrix(
            [
                (-1.0, 0.0, 0.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(AbstractComponent, self).__init__(*args, **kwargs)

        # Declare class variables
        #
        self._componentManager = componentfactory.ComponentFactory.getInstance(asWeakReference=True)
    # endregion

    # region Attributes
    componentName = mpyattribute.MPyAttribute('componentName', attributeType='str')
    componentVersion = mpyattribute.MPyAttribute('componentVersion', attributeType='float')
    componentId = mpyattribute.MPyAttribute('componentId', attributeType='str')
    componentSide = mpyattribute.MPyAttribute('componentSide', attributeType='enum', fields=Side, default=Side.NONE)
    componentChildren = mpyattribute.MPyAttribute('componentChildren', attributeType='message', array=True, hidden=True)
    componentStatus = mpyattribute.MPyAttribute('componentStatus', attributeType='enum', fields=Status, default=Status.META)
    controlsGroup = mpyattribute.MPyAttribute('controlsGroup', attributeType='message')
    privateGroup = mpyattribute.MPyAttribute('privateGroup', attributeType='message')
    jointsGroup = mpyattribute.MPyAttribute('jointsGroup', attributeType='message')
    # endregion

    # region Properties
    @property
    def componentManager(self):
        """
        Getter method that returns the rig component manager.

        :rtype: componentfactory.ComponentFactory
        """

        return self._componentManager()

    @componentName.changed
    def componentName(self, value):
        """
        Changed method that notifies any component name changes.

        :type value: str
        :rtype: None
        """

        self.invalidateName()
        self.markSkeletonDirty()
        self.markPivotsDirty()

    @componentSide.changed
    def componentSide(self, value):
        """
        Changed method that notifies any component side changes.

        :type value: int
        :rtype: None
        """

        self.invalidateName()
        self.markSkeletonDirty()
        self.markPivotsDirty()

    @componentId.changed
    def componentId(self, value):
        """
        Getter method that notifies any component id changes.

        :type value: int
        :rtype: Status
        """

        self.invalidateName()
        self.markSkeletonDirty()
        self.markPivotsDirty()
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
        name = kwargs.get('name', None)
        parent = kwargs.get('parent', None)

        component = super(AbstractComponent, cls).create('dagContainer', name=name, parent=parent)

        # Update component attributes
        #
        component.owner = getpass.getuser()
        component.creationDate = strftime("%m/%d/%Y", gmtime())
        component.iconName = os.path.join('$AIRSHIP_MAYA_PATH', 'python', 'rigotron', 'ui', 'icons', f'{cls.className}.svg')
        component.componentName = kwargs.get('componentName', cls.__default_component_name__)
        component.componentVersion = kwargs.get('componentVersion', cls.__version__)
        component.componentId = kwargs.get('componentId', '')
        component.componentStatus = Status.META
        component.componentSide = kwargs.get('componentSide', Side.NONE)
        component.invalidateName()

        # Update component parent
        #
        componentParent = kwargs.get('componentParent', None)

        if isinstance(componentParent, AbstractComponent):

            componentParent.appendComponentChild(component)

        # Update user properties
        #
        component.userProperties[cls.SKELETON_KEY] = []
        component.userProperties[cls.PIVOTS_KEY] = []

        return component

    def defaultNameFormat(self):
        """
        Returns the default naming configuration for this component.

        :rtype: Dict[str, Any]
        """

        return {'name': self.componentName, 'id': self.componentId, 'side': Side(self.componentSide)}

    def formatName(self, **kwargs):
        """
        Returns a name based on the supplied keyword arguments.

        :rtype: str
        """

        config = self.defaultNameFormat()
        config.update(kwargs)

        return namingutils.formatName(**config)

    def invalidateName(self):
        """
        Invalidates the name of this component.

        :rtype: None
        """

        self.setName(self.formatName(type=self.typeName))

    def doesComponentExist(self):
        """
        Getter method used to evaluate if this component has been built.

        :rtype: bool
        """

        return not self.controlsGroup.isNull()

    def hasComponentParent(self):
        """
        Evaluates if this component has a parent.

        :rtype: bool
        """

        return self.componentParent() is not None

    def componentParent(self):
        """
        Returns the parent of this component.

        :rtype: AbstractComponent
        """

        # Iterate through destination plugs
        #
        plug = self.findPlug('message')
        otherPlugs = plug.destinations()

        for otherPlug in otherPlugs:

            # Check if this a rig component
            #
            otherNode = self.scene(otherPlug.node())

            if isinstance(otherNode, AbstractComponent) and re.fullmatch(r'^[a-zA-Z0-9_]+\.componentChildren\[[0-9]+\]$', otherPlug.info):

                return otherNode

            else:

                continue

        return None

    def iterComponentAncestors(self):
        """
        Returns a generator that iterates over all the parents relative to this node.

        :rtype: iter
        """

        ancestor = self.componentParent()

        while ancestor is not None:

            yield ancestor
            ancestor = ancestor.componentParent()

    def findComponentAncestors(self, typeName):
        """
        Returns a list of ancestor components derived from the specified type name.

        :type typeName: str
        :rtype: List[AbstractComponent]
        """

        return [component for component in self.iterComponentAncestors() if any(cls.__name__.endswith(typeName) for cls in component.iterBases())]

    def iterComponentChildren(self):
        """
        Returns a generator that yields components that are parented to this component.

        :rtype: Iterator[AbstractComponent]
        """

        # Iterate through destination plugs
        #
        plug = self.findPlug('componentChildren')
        elementCount = plug.numElements()

        for i in range(elementCount):

            # Check if element is connected
            #
            element = plug.elementByPhysicalIndex(i)

            if element.isDestination:

                yield self.scene(element.source().node())

            else:

                continue

    def popComponentChild(self, index):
        """
        Removes and returns the child component at the specified index.

        :type index: Union[int, slice]
        :rtype: Union[AbstractComponent, List[AbstractComponent]]
        """

        # Evaluate index type
        #
        if isinstance(index, int):

            # Check if element is connected
            #
            destination = self.findPlug(f'componentChildren[{index}]')

            if not destination.isDestination:

                return None

            # Disconnect source component from element
            #
            source = destination.source()
            component = self.scene(source.node())

            self.disconnectPlugs(source, destination)
            plugutils.removeMultiInstances(destination, [index])

            return component

        elif isinstance(index, slice):

            # Expand slice into logical indices
            #
            plug = self.findPlug(f'componentChildren')
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else plug.numElements()
            step = index.step if index.step is not None else 1

            logicalIndices = list(range(start, stop, step))

            # Iterate through logical indices
            #
            components = []

            for logicalIndex in logicalIndices:

                # Check if element is connected
                #
                destination = plug.elementByLogicalIndex(logicalIndex)

                if not destination.isDestination:

                    continue

                # Disconnect source component from element
                #
                source = destination.source()
                component = self.scene(source.node())
                components.append(component)

                self.disconnectPlugs(source, destination)

            # Remove elements from sparse array
            #
            plugutils.removeMultiInstances(plug, logicalIndices)

            return components

        else:

            raise TypeError(f'popComponentChild() expects an int ({type(index).__name__} given)!')

    def insertComponentChild(self, insertAt, child):
        """
        Inserts a child, at the specified index, to this component.

        :type insertAt: int
        :type child: AbstractComponent
        :rtype: None
        """

        # Check if elements require moving
        #
        plug = self.findPlug('componentChildren')
        destination = plug.elementByLogicalIndex(insertAt)

        if destination.isDestination:

            plugutils.moveConnectedElements(plug, insertAt)

        # Connect child to component
        #
        source = child.findPlug('message')
        self.connectPlugs(source, destination)

    def appendComponentChild(self, child):
        """
        Appends a child to this component.

        :type child: AbstractComponent
        :rtype: None
        """

        plug = self.findPlug('componentChildren')
        index = self.getNextAvailableConnection(plug)

        self.insertComponentChild(index, child)

    def iterComponentDescendants(self):
        """
        Returns a generator that yields components descended from this component.

        :rtype: Iterator[AbstractComponent]
        """

        queue = deque(self.iterComponentChildren())

        while len(queue) > 0:

            descendant = queue.popleft()
            yield descendant

            queue.extend(descendant.iterComponentChildren())

    def iterComponentSiblings(self, includeSelf=False):
        """
        Returns a generator that yields components that are siblings of this component.

        :type includeSelf: bool
        :rtype: Iterator[AbstractComponent]
        """

        # Check if parent exists
        #
        parent = self.componentParent()

        if parent is not None:

            # Iterate through parent's children
            #
            for child in parent.iterComponentChildren():

                # Ensure child is not this component
                #
                if child is not self or includeSelf:

                    yield child

                else:

                    continue

        elif includeSelf:

            yield from iter([self])

        else:

            yield from iter([])

    def componentSiblings(self, includeSelf=False):
        """
        Returns a list of components that are siblings of this component.

        :type includeSelf: bool
        :rtype: List[AbstractComponent]
        """

        return list(self.iterComponentSiblings(includeSelf=includeSelf))

    def findComponentDescendants(self, typeName):
        """
        Returns a list of descended components with the specified type name.

        :type typeName: str
        :rtype: List[AbstractComponent]
        """

        return [component for component in self.iterComponentDescendants() if any(cls.__name__.endswith(typeName) for cls in component.iterBases())]

    def findComponents(self, typeName, upstream=True, downstream=True):
        """
        Collects any components that match the specified criteria.

        :type typeName: str
        :type upstream: bool
        :type downstream: bool
        :rtype: List[AbstractComponent]
        """

        # Check if upstream components should be collected
        #
        components = []

        if upstream:

            components.extend(self.findComponentAncestors(typeName))

        # Check if downstream components should be collected
        #
        if downstream:

            components.extend(self.findComponentDescendants(typeName))

        return components

    def findRootComponent(self):
        """
        Returns the root component relative to this instance.
        If this component is a root then it will return itself.

        :rtype: rigotron.components.rootcomponent.RootComponent
        """

        # Redundancy check
        #
        if self.className == 'RootComponent':

            return self

        # Collect ancestors derived from root
        #
        components = self.findComponents('RootComponent', upstream=True, downstream=False)
        numComponents = len(components)

        if numComponents == 0:

            return None

        elif numComponents == 1:

            return components[0]

        else:

            raise TypeError(f'findRootComponent() expects a unique root components ({numComponents} found)!')

    def findControlRig(self):
        """
        Returns the control rig associated with this component.

        :rtype: rigotron.interops.controlrig.ControlRig
        """

        # Get root component
        #
        root = self.findRootComponent()

        if root is None:

            return None

        # Iterate through message destinations
        #
        plug = root.findPlug('message')

        for otherPlug in plug.destinations():

            # Check if connected plug is a pyNode
            #
            node = self.scene(otherPlug.node())
            partialName = otherPlug.partialName(useLongNames=True)

            if isinstance(node, mpynodeextension.MPyNodeExtension) and partialName == 'rootComponent':

                return node

            else:

                continue

        return None

    def isUpToDate(self):
        """
        Evaluates if this component is up-to-date.

        :rtype: bool
        """

        return self.componentVersion == self.__version__
