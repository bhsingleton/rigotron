from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.maya.json import melsonobject
from enum import IntEnum
from ..abstract import abstractspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DriverType(IntEnum):
    """
    Enum class of all available driver types.
    """

    NONE = -1
    CONSTRAINT = 0
    PARENT = 1
    OFFSET_PARENT_MATRIX = 2


class DriverSpec(melsonobject.MELSONObject):
    """
    Overload of `MELSONObject` that interfaces with export skeleton drivers.
    """

    # region Enums
    Type = DriverType
    # endregion

    # region Dunderscores
    __slots__ = (
        '__weakref__',
        '_scene',
        '_driven',
        '_name',
        '_namespace',
        '_type',
        '_maintainOffset',
        '_skipTranslate',
        '_skipRotate',
        '_skipScale'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(DriverSpec, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._driven = kwargs.get('driven', self.nullWeakReference)
        self._name = ''
        self._namespace = ''
        self._type = DriverType.CONSTRAINT
        self._maintainOffset = False
        self._skipTranslate = [False, False, False]
        self._skipRotate = [False, False, False]
        self._skipScale = [False, False, False]
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def driven(self):
        """
        Getter method that returns the driven node.

        :rtype: abstractspec.AbstractSpec
        """

        return self._driven()

    @property
    def name(self):
        """
        Getter method that returns the name.

        :rtype: str
        """

        return self._name

    @name.setter
    def name(self, name):
        """
        Setter method that updates the name.

        :type name: str
        :rtype: None
        """

        self._name = name

    @property
    def namespace(self):
        """
        Getter method that returns the namespace.

        :rtype: str
        """

        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        """
        Setter method that updates the namespace.

        :type namespace: str
        :rtype: None
        """

        self._namespace = namespace

    @property
    def type(self):
        """
        Getter method that returns the type.

        :rtype: str
        """

        return self._type

    @type.setter
    def type(self, type):
        """
        Setter method that updates the type.

        :type type: Union[int, DriverType]
        :rtype: None
        """

        self._type = self.Type(type)

    @property
    def maintainOffset(self):
        """
        Getter method that returns the `maintainOffset` flag.

        :rtype: bool
        """

        return self._maintainOffset

    @maintainOffset.setter
    def maintainOffset(self, maintainOffset):
        """
        Setter method that updates the `maintainOffset` flag.

        :type maintainOffset: bool
        :rtype: None
        """

        self._maintainOffset = maintainOffset
    
    @property
    def skipTranslate(self):
        """
        Getter method that returns the `skipTranslate` flags.

        :rtype: bool
        """

        return self._skipTranslate

    @skipTranslate.setter
    def skipTranslate(self, skipTranslate):
        """
        Setter method that updates the `skipTranslate` flags.

        :type skipTranslate: Union[bool, Tuple[bool, bool, bool], List[bool]]
        :rtype: None
        """
        
        if isinstance(skipTranslate, bool):
            
            self._skipTranslate[0] = skipTranslate
            self._skipTranslate[1] = skipTranslate
            self._skipTranslate[2] = skipTranslate

        elif isinstance(skipTranslate, (list, tuple)):
            
            for (i, item) in enumerate(skipTranslate):
                
                if isinstance(item, (bool, int)):
                    
                    self._skipTranslate[i] = bool(skipTranslate[i])
                
                else:
                    
                    continue
                    
        else:
            
            raise TypeError(f'skipTranslate.setter() expects a boolean ({type(skipTranslate).__name__} given)!')
    
    @property
    def skipRotate(self):
        """
        Getter method that returns the `skipRotate` flags.

        :rtype: bool
        """

        return self._skipRotate

    @skipRotate.setter
    def skipRotate(self, skipRotate):
        """
        Setter method that updates the `skipRotate` flags.

        :type skipRotate: Union[bool, Tuple[bool, bool, bool], List[bool]]
        :rtype: None
        """
        
        if isinstance(skipRotate, bool):
            
            self._skipRotate[0] = skipRotate
            self._skipRotate[1] = skipRotate
            self._skipRotate[2] = skipRotate

        elif isinstance(skipRotate, (list, tuple)):
            
            for (i, item) in enumerate(skipRotate):
                
                if isinstance(item, (bool, int)):
                    
                    self._skipRotate[i] = bool(skipRotate[i])
                
                else:
                    
                    continue
                    
        else:
            
            raise TypeError(f'skipRotate.setter() expects a boolean ({type(skipRotate).__name__} given)!')
    
    @property
    def skipScale(self):
        """
        Getter method that returns the `skipScale` flags.

        :rtype: bool
        """

        return self._skipScale

    @skipScale.setter
    def skipScale(self, skipScale):
        """
        Setter method that updates the `skipScale` flags.

        :type skipScale: Union[bool, Tuple[bool, bool, bool], List[bool]]
        :rtype: None
        """
        
        if isinstance(skipScale, bool):
            
            self._skipScale[0] = skipScale
            self._skipScale[1] = skipScale
            self._skipScale[2] = skipScale

        elif isinstance(skipScale, (list, tuple)):
            
            for (i, item) in enumerate(skipScale):
                
                if isinstance(item, (bool, int)):
                    
                    self._skipScale[i] = bool(skipScale[i])
                
                else:
                    
                    continue
                    
        else:
            
            raise TypeError(f'skipScale.setter() expects a boolean ({type(skipScale).__name__} given)!')
    # endregion

    # region Methods
    def getDriven(self, **kwargs):
        """
        Returns the node associated with the driver.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :rtype: Union[mpynode.MPyNode, None]
        """

        # Check if driven exists
        #
        if isinstance(self.driven, abstractspec.AbstractSpec):

            return self.driven.getNode(**kwargs)

        else:

            return None

    def getDriver(self):
        """
        Returns the node associated with this driver.

        :rtype: Union[mpynode.MPyNode, None]
        """

        return self.scene.getNodeByName(f'{self.namespace}:{self.name}')

    def bind(self, referenceNode=None):
        """
        Binds the driven node to this driver.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :rtype: None
        """

        # Check if driver and driven exist
        #
        driven = self.getDriven(referenceNode=referenceNode)
        driver = self.getDriver()

        if not (isinstance(driven, mpynode.MPyNode) and isinstance(driver, mpynode.MPyNode)):

            log.warning(f'Unable to bind "{self.namespace}:{self.name}" > {getattr(self.driven, "name", "")}!')
            return

        # Evaluate driver type
        #
        if self.type == self.Type.CONSTRAINT:

            # Add constraint to driven
            #
            driven.removeConstraints()
            driven.unfreezePivots()

            skipTranslateX, skipTranslateY, skipTranslateZ = self.skipTranslate
            skipRotateX, skipRotateY, skipRotateZ = self.skipRotate
            skipScaleX, skipScaleY, skipScaleZ = self.skipScale

            log.info(f'Constraining "{driver}" > "{driven}"')
            constraint = driven.addConstraint(
                'transformConstraint',
                [driver],
                maintainOffset=self.maintainOffset,
                skipTranslateX=skipTranslateX,
                skipTranslateY=skipTranslateY,
                skipTranslateZ=skipTranslateZ,
                skipRotateX=skipRotateX,
                skipRotateY=skipRotateY,
                skipRotateZ=skipRotateZ,
                skipScaleX=skipScaleX,
                skipScaleY=skipScaleY,
                skipScaleZ=skipScaleZ
            )
            constraint.hiddenInOutliner = True

            return constraint

        elif self.type == self.Type.PARENT:

            # Reparent driven
            #
            log.info(f'Parenting "{driven}" > "{driver}"')
            driven.setParent(driver, absolute=True)

        elif self.type == self.Type.OFFSET_PARENT_MATRIX:

            # Override driven `offsetParentMatrix` connection
            #
            log.info(f'Connecting "{driver}.worldMatrix[0]" > "{driven}.offsetParentMatrix"')
            driven.connectPlugs(driver[f'worldMatrix[{driver.instanceNumber()}]'], 'offsetParentMatrix', force=True)

        else:

            pass

    def unbind(self, referenceNode=None):
        """
        Unbinds the driven node from this driver.

        :type referenceNode: Union[mpynode.MPyNode, None]
        :rtype: None
        """

        # Check if driven exists
        #
        driven = self.getDriven(referenceNode=referenceNode)

        if not isinstance(driven, mpynode.MPyNode):

            log.warning(f'Unable to unbind {self.name} driver!')
            return

        # Evaluate driver type
        #
        if self.type == self.Type.CONSTRAINT:

            driven.removeConstraints()

        elif self.type == self.Type.PARENT:

            driven.setParent(None, absolute=True)

        elif self.type == self.Type.OFFSET_PARENT_MATRIX:

            driven.breakConnections('offsetParentMatrix', source=True, destination=False)

        else:

            pass

        # Reassign driven matrix
        #
        driven.setMatrix(self.driven.matrix, skipScale=False)
    # endregion
