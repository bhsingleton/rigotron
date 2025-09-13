from . import Side, Status
from ..components import basecomponent
from dcc.maya.decorators import undo, animate

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

    controlRig = component.findControlRig()
    controlRig.saveSkeleton()
    controlRig.loadSkeleton(clearEdits=True)

    for childComponent in component.walkComponents():

        childComponent.prepareToBuildPivots()
        childComponent.buildPivots()
        childComponent.pivotsCompleted()

        childComponent.componentStatus = Status.SKELETON  # Setting this too early prevents pivot specs from invalidating!


def skeletonToRig(component):
    """
    Changes the supplied rig's state from skeleton to rig.

    :type component: basecomponent.BaseComponent
    :rtype: None
    """

    for childComponent in component.walkComponents():

        childComponent.cachePivots(delete=False)

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

        childComponent.componentStatus = Status.SKELETON


def skeletonToMeta(component):
    """
    Changes the supplied rig's state from skeleton to meta.

    :type component: basecomponent.BaseComponent
    :rtype: None
    """

    for childComponent in reversed(list(component.walkComponents())):

        childComponent.cachePivots(delete=True)
        childComponent.cacheSkeleton()

        childComponent.componentStatus = Status.META

    controlRig = component.findControlRig()
    controlRig.unloadSkeleton()
    controlRig.saveSkeleton()


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
    with animate.Animate(state=False):

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
