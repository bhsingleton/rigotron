from dcc.abstract import proxyfactory
from mpy import mpyscene
from .. import components
from ..abstract import abstractcomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ComponentFactory(proxyfactory.ProxyFactory):
    """
    Overload of `ProxyFactory` that interfaces with rig components.
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
        super(ComponentFactory, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self.__scene__ = mpyscene.MPyScene.getInstance(asWeakReference=True)

    def __call__(self, typeName, **kwargs):
        """
        Returns a new component based on the supplied type name.

        :type typeName: str
        :rtype: abstractcomponent.AbstractComponent
        """

        return self.createComponent(typeName, **kwargs)
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

        return [components]

    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: Callable
        """

        return abstractcomponent.AbstractComponent

    def createComponent(self, typeName, **kwargs):
        """
        Returns a new component based on the supplied type name.

        :type typeName: str
        :rtype: abstractcomponent.AbstractComponent
        """

        # Check if type is valid
        #
        cls = self.getClass(typeName)

        if cls is not None:

            return cls.create(**kwargs)

        else:

            log.warning(f'createComponent() expects a valid type name ({typeName} given)!')
            return None

    def iterComponents(self, typeName='BaseComponent'):
        """
        Returns a generator that yields components from the scene file.

        :type typeName: str
        :rtype: Iterator[abstractcomponent.AbstractComponent]
        """

        return self.scene.iterExtensionsByTypeName(typeName)
    # endregion
