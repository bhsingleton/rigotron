from . import Side, Status
from ..components import basecomponent
from dcc.maya.decorators import undo

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def metaToSkeleton(component):
    """
    Changes the supplied rig's state from meta to skeleton.

    :type component: basecomponent.BaseComponent
    :rtype: None
    """

    for childComponent in component.walkComponents():

        childComponent.prepareToBuildSkeleton()
        childComponent.buildSkeleton()
        childComponent.skeletonCompleted()

        childComponent.prepareToBuildPivots()
        childComponent.buildPivots()
        childComponent.pivotsCompleted()

        childComponent.componentStatus = Status.SKELETON


def skeletonToRig(component):
    """
    Changes the supplied rig's state from skeleton to rig.

    :type component: basecomponent.BaseComponent
    :rtype: None
    """

    for childComponent in component.walkComponents():

        childComponent.cachePivots(delete=True)

        childComponent.prepareToBuildRig()
        childComponent.buildRig()
        childComponent.rigCompleted()

        childComponent.componentStatus = Status.RIG

    for childComponent in component.walkComponents():

        childComponent.finalizeRig()


def rigToSkeleton(component):
    """
    Changes the supplied rig's state from rig to skeleton.

    :type component: basecomponent.BaseComponent
    :rtype: None
    """

    for childComponent in reversed(list(component.walkComponents())):

        childComponent.deleteRig()

        childComponent.prepareToBuildPivots()
        childComponent.buildPivots()
        childComponent.pivotsCompleted()

        childComponent.componentStatus = Status.SKELETON


def skeletonToMeta(component):
    """
    Changes the supplied rig's state from skeleton to meta.

    :type component: basecomponent.BaseComponent
    :rtype: None
    """

    for childComponent in reversed(list(component.walkComponents())):

        childComponent.cachePivots(delete=True)
        childComponent.cacheSkeleton(delete=True)

        childComponent.componentStatus = Status.META


@undo.Undo(state=False)
def changeState(component, state):
    """
    Changes the state on the supplied control rig.

    :type component: basecomponent.BaseComponent
    :type state: Status
    :rtype: bool
    """

    # Redundancy check
    #
    if not (isinstance(component, basecomponent.BaseComponent) and isinstance(state, Status)):

        raise TypeError('changeState() expects a component and state!')

    # Evaluate state request
    # We must ensure the parent components are already at the requested state!
    #
    currentState = Status(component.componentStatus)
    isValid = all([Status(ancestor.componentStatus) >= state for ancestor in component.iterComponentAncestors()])

    if not isValid:

        return False

    # Process state change
    #
    if currentState == Status.META:

        # Evaluate requested state change
        #
        if state == Status.META:

            pass

        elif state == Status.SKELETON:

            metaToSkeleton(component)

        else:

            metaToSkeleton(component)
            skeletonToRig(component)

        return True

    elif currentState == Status.SKELETON:

        # Evaluate requested state change
        #
        if state == Status.META:

            skeletonToMeta(component)

        elif state == Status.SKELETON:

            pass

        else:

            skeletonToRig(component)

        return True

    elif currentState == Status.RIG:

        # Evaluate requested state change
        #
        if state == Status.META:

            metaToSkeleton(component)
            skeletonToRig(component)

        elif state == Status.SKELETON:

            rigToSkeleton(component)

        else:

            pass

        return True

    else:

        return False
