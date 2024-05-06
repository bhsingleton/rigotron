from . import Status
from ..interops import controlrig

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def metaToSkeleton(controlRig):
    """
    Changes the supplied rig's state from meta to skeleton.

    :type controlRig: controlrig.ControlRig
    :rtype: None
    """

    for component in controlRig.walkComponents():

        component.prepareToBuildSkeleton()
        component.buildSkeleton()
        component.finalizeSkeleton()

        component.prepareToBuildPivots()
        component.buildPivots()
        component.finalizePivots()

        component.componentStatus = Status.SKELETON


def skeletonToRig(controlRig):
    """
    Changes the supplied rig's state from skeleton to rig.

    :type controlRig: controlrig.ControlRig
    :rtype: None
    """

    for component in controlRig.walkComponents():

        component.cachePivots(delete=True)
        component.cacheSkeleton(delete=False)

        component.prepareToBuildRig()
        component.buildRig()
        component.rigCompleted()

    for component in controlRig.walkComponents():

        component.finalizeRig()


def rigToSkeleton(controlRig):
    """
    Changes the supplied rig's state from rig to skeleton.

    :type controlRig: controlrig.ControlRig
    :rtype: None
    """

    for component in reversed(list(controlRig.walkComponents())):

        component.deleteRig()
        component.componentStatus = Status.SKELETON


def skeletonToMeta(controlRig):
    """
    Changes the supplied rig's state from skeleton to meta.

    :type controlRig: controlrig.ControlRig
    :rtype: None
    """

    for component in reversed(list(controlRig.walkComponents())):

        component.cachePivots(delete=True)
        component.cacheSkeleton(delete=True)

        component.componentStatus = Status.META


def changeState(controlRig, state):
    """
    Changes the state on the supplied control rig.

    :type controlRig: controlrig.ControlRig
    :type state: int
    :rtype: None
    """

    # Evaluate current state
    #
    rootComponent = controlRig.scene(controlRig.rootComponent)
    currentState = rootComponent.componentStatus

    if currentState == Status.META:

        # Evaluate requested state change
        #
        if state == Status.META:

            pass

        elif state == Status.SKELETON:

            metaToSkeleton(controlRig)

        else:

            metaToSkeleton(controlRig)
            skeletonToRig(controlRig)

    elif currentState == Status.SKELETON:

        # Evaluate requested state change
        #
        if state == Status.META:

            skeletonToMeta(controlRig)

        elif state == Status.SKELETON:

            pass

        else:

            skeletonToRig(controlRig)

    elif currentState == Status.RIG:

        # Evaluate requested state change
        #
        if state == Status.META:

            metaToSkeleton(controlRig)
            skeletonToRig(controlRig)

        elif state == Status.SKELETON:

            rigToSkeleton(controlRig)

        else:

            pass

    else:

        raise TypeError(f'changeState() expects a valid state ({state} given)!')
