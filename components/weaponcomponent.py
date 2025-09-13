from . import propcomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class WeaponComponent(propcomponent.PropComponent):
    """
    Overload of `PropComponent` that implements weapon components.
    """

    # region Dunderscores
    __default_component_name__ = 'Weapon'  # That's it, that's all we do!
    # endregion
