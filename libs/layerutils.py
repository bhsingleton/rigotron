from mpy import mpyscene, mpynode
from collections import defaultdict
from fnmatch import fnmatchcase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def createDisplayLayers(controlRig, prefix='Controls'):
    """
    Creates display layers for the supplied control rig.

    :type controlRig: rigotron.interop.controlrig.ControlRig
    :type prefix: str
    :rtype: None
    """

    # Organize controls by component groups
    #
    scene = mpyscene.MPyScene()
    groups = defaultdict(list)

    for component in controlRig.walkComponents():

        name = component.componentName
        defaultName = component.__default_component_name__
        nameChanged = name != defaultName

        controls = component.publishedNodes()

        if nameChanged:

            groups[name].extend(controls)

        else:

            groups[defaultName].extend(controls)

    # Consolidate root, spine and clavicle components
    #
    rootCtrls = groups.pop('Root', [])
    spineCtrls = groups.pop('Spine', [])
    clavicleCtrls = groups.pop('Clavicle', [])
    headCtrls = groups.pop('Head', [])
    jawCtrls = groups.pop('Jaw', [])

    groups['Body'] = rootCtrls + spineCtrls + clavicleCtrls + headCtrls + jawCtrls

    # Decompose leg components
    #
    legCtrls = groups.pop('Leg', [])
    legFKCtrls = [ctrl for ctrl in legCtrls if fnmatchcase(ctrl.name(), '*_FK_CTRL')]
    legIKCtrls = [ctrl for ctrl in legCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*_Leg_CTRL', '*_Knee_CTRL', '*_IK_CTRL', '*_PV_CTRL')])]
    legSwitchCtrls = [ctrl for ctrl in legCtrls if fnmatchcase(ctrl.name(), '*_Switch_CTRL')]
    legKinematicCtrls = legFKCtrls + legIKCtrls + legSwitchCtrls
    legExtraCtrls = [ctrl for ctrl in legCtrls if ctrl not in legKinematicCtrls]

    groups['Leg_FK'] = legFKCtrls
    groups['Leg_IK'] = legIKCtrls
    groups['Leg_Extras'] = legExtraCtrls

    groups['Body'].extend(legSwitchCtrls)

    # Decompose arm components
    #
    armCtrls = groups.pop('Arm', [])
    armFKCtrls = [ctrl for ctrl in armCtrls if fnmatchcase(ctrl.name(), '*_FK_CTRL')]
    armIKCtrls = [ctrl for ctrl in armCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*_Arm_CTRL', '*_Elbow_CTRL', '*_IK_CTRL', '*_PV_CTRL')])]
    armSwitchCtrls = [ctrl for ctrl in legCtrls if fnmatchcase(ctrl.name(), '*_Switch_CTRL')]
    armKinematicCtrls = armFKCtrls + armIKCtrls + armSwitchCtrls
    armExtraCtrls = [ctrl for ctrl in armCtrls if ctrl not in armKinematicCtrls]

    groups['Arm_FK'] = armFKCtrls
    groups['Arm_IK'] = armIKCtrls
    groups['Arm_Extras'] = armExtraCtrls

    groups['Body'].extend(armSwitchCtrls)

    # Decompose hand component
    #
    handCtrls = groups.pop('Hand', [])
    fingerCtrls = [ctrl for ctrl in handCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*Metacarpal_CTRL', '*Finger_Master_CTRL', '*Finger??_CTRL', '*Thumb_Master_CTRL', '*Thumb??_CTRL')])]
    fingerExtraCtrls = [ctrl for ctrl in handCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*Finger_IK_CTRL', '*Thumb_IK_CTRL')])]
    allFingerCtrls = fingerCtrls + fingerExtraCtrls
    remainingHandCtrls = [ctrl for ctrl in handCtrls if ctrl not in allFingerCtrls]

    groups['Hand'] = remainingHandCtrls
    groups['Fingers'] = fingerCtrls
    groups['Fingers_Extras'] = fingerExtraCtrls

    # Consolidate prop components
    #
    propCtrls = groups.pop('Prop', [])
    stowedCtrls = groups.pop('Stow', [])

    groups['Props'] = propCtrls + stowedCtrls

    # Create display layers from groups
    #
    layer = None

    for (componentName, controls) in groups.items():

        # Redundancy check
        #
        hasControls = len(controls) > 0

        if not hasControls:

            continue

        # Check if layer exists
        # If not, then create a new layer
        #
        layerName = f'{prefix}_{componentName}'

        if scene.objExists(layerName):

            layer = mpynode.MPyNode(layerName)

        else:

            layer = scene.createDisplayLayer(name=layerName)

        # Add controls to layer
        #
        log.info(f'Organizing {layer} << {controls}')

        for control in controls:

            layer.addNode(control.object())
