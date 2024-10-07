from maya.api import OpenMaya as om
from mpy import mpyscene
from dcc.abstract import proxyfactory
from .. import interfaces
from ..abstract import abstractinterface

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class InterfaceFactory(proxyfactory.ProxyFactory):
    """
    Overload of `ProxyFactory` that interfaces with rig interfaces.
    I've purposely chosen to separate this class from the `ComponentFactory` for the sake of abstraction.
    """

    # region Dunderscores
    __slots__ = ('__scene__',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(InterfaceFactory, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self.__scene__ = mpyscene.MPyScene.getInstance(asWeakReference=True)

    def __call__(self, typeName, **kwargs):
        """
        Returns a new component based on the supplied type name.

        :type typeName: str
        :rtype: abstractinterface.AbstractInterface
        """

        return self.createInterface(typeName, **kwargs)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self.__scene__()
    # endregion

    # region Methods
    def packages(self):
        """
        Returns a list of packages to be searched for factory classes.

        :rtype: List[module]
        """

        return [interfaces]

    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: Callable
        """

        return abstractinterface.AbstractInterface

    def createInterface(self, typeName, **kwargs):
        """
        Returns a new interop based on the supplied type name.

        :type typeName: str
        :rtype: abstractinterface.AbstractInterface
        """

        # Check if type is valid
        #
        cls = self.getClass(typeName)

        if cls is not None:

            return cls.create(**kwargs)

        else:

            log.warning(f'createInterface() expects a valid type name ({typeName} given)!')
            return None

    def iterInterfaces(self, typeName='AbstractInterface'):
        """
        Returns a generator that yields interops derived from the specified type name.

        :type typeName: str
        :rtype: Iterator[abstractinterface.AbstractInterface]
        """

        return self.scene.iterExtensionsByTypeName(typeName)

    def iterControlRigs(self):
        """
        Returns a generator that yields all the control rigs in the scene.

        :rtype: Iterator[controlrig.ControlRig]
        """

        return self.iterInterfaces(typeName='ControlRig')

    def controlRigs(self):
        """
        Returns a list of control rigs in the scene.

        :rtype: List[controlrig.ControlRig]
        """

        return list(self.iterControlRigs())

    def createControlRig(self, name):
        """
        Returns a new control rig.

        :type name: str
        :rtype: controlrig.ControlRig
        """

        return self.createInterface('ControlRig', rigName=name)
    # endregion
