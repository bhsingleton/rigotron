from mpy import mpyscene, mpynode
from collections import defaultdict
from itertools import chain
from fnmatch import fnmatch, fnmatchcase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__spine_controls__ = (
    'COG_CTRL',
    'Waist_CTRL',
    'Hips_CTRL',
    '*_FK??_Rot_CTRL',
    'Chest_FK_Rot_CTRL',
    'Chest_IK_CTRL'
)
__leg_fk_controls__ = ('*_FK_CTRL',)
__leg_ik_controls__ = (
    '?_Leg_CTRL',
    '?_Knee_CTRL',
    '?_Ankle_IK_CTRL',
    '?_Ankle_IK_Rot_CTRL',
    '?_Ankle_IK_Trans_CTRL',
    '*_PV_CTRL'
)
__leg_switch_controls__ = ('*_Switch_CTRL',)
__arm_fk_controls__ = ('*_FK_CTRL',)
__arm_ik_controls__ = (
    '?_Elbow_CTRL',
    '?_Wrist_IK_CTRL',
    '*_PV_CTRL'
)
__arm_controls__ = ('?_Arm_CTRL', '*_Switch_CTRL',)
__hand_controls__ = ('?_Hand_CTRL', '?_Hand*_Knuckle_CTRL')
__finger_controls__ = (
    '*Metacarpal_CTRL',
    '*Finger_Master_CTRL',
    '*Finger??_CTRL',
    '*Thumb_Master_CTRL',
    '*Thumb??_CTRL'
)
__finger_ik_controls__ = ('*Finger_IK_CTRL', '*Thumb_IK_CTRL')


def matchPattern(name, *patterns, ignoreCase=False):
    """
    Evaluates if the supplied name matches any of the specified patterns.

    :type name: str
    :type patterns: Union[str, List[str]]
    :type ignoreCase: bool
    :rtype: bool
    """

    if ignoreCase:

        return any([fnmatch(name, pattern) for pattern in patterns])

    else:

        return any([fnmatchcase(name, pattern) for pattern in patterns])


def filterNodesByPattern(nodes, *patterns, ignoreCase=False):
    """
    Filters the supplied nodes according to the specified patterns.

    :type nodes: List[mpynode.MPyNode]
    :type patterns: Union[str, List[str]]
    :type ignoreCase: bool
    :rtype: List[mpynode.MPyNode]
    """

    return [node for node in nodes if matchPattern(node.name(), *patterns, ignoreCase=ignoreCase)]


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
    spineKinematicCtrls = filterNodesByPattern(spineCtrls, *__spine_controls__)
    remainingSpineCtrls = [ctrl for ctrl in spineCtrls if ctrl not in spineKinematicCtrls]
    clavicleCtrls = groups.pop('Clavicle', [])
    headCtrls = groups.pop('Head', [])
    jawCtrls = groups.pop('Jaw', [])

    groups['Body'] = rootCtrls + spineKinematicCtrls + clavicleCtrls + headCtrls + jawCtrls
    groups['Body_Extras'] = remainingSpineCtrls

    # Decompose leg components
    #
    legCtrls = groups.pop('Leg', groups.pop('HindLeg', []))
    legFKCtrls = filterNodesByPattern(legCtrls, *__leg_fk_controls__)
    legIKCtrls = filterNodesByPattern(legCtrls, *__leg_ik_controls__)
    legSwitchCtrls = filterNodesByPattern(legCtrls, *__leg_switch_controls__)
    legKinematicCtrls = legFKCtrls + legIKCtrls + legSwitchCtrls
    legExtraCtrls = [ctrl for ctrl in legCtrls if ctrl not in legKinematicCtrls]

    groups['Leg_FK'] = legFKCtrls
    groups['Leg_IK'] = legIKCtrls
    groups['Leg_Extras'] = legExtraCtrls

    groups['Body'].extend(legSwitchCtrls)

    # Decompose arm components
    #
    armCtrls = groups.pop('Arm', [])
    armFKCtrls = filterNodesByPattern(armCtrls, *__arm_fk_controls__)
    armIKCtrls = filterNodesByPattern(armCtrls, *__arm_ik_controls__)
    armSharedCtrls = filterNodesByPattern(armCtrls, *__arm_controls__)
    armKinematicCtrls = armFKCtrls + armIKCtrls + armSharedCtrls
    armExtraCtrls = [ctrl for ctrl in armCtrls if ctrl not in armKinematicCtrls]

    groups['Arm_FK'] = armFKCtrls
    groups['Arm_IK'] = armIKCtrls
    groups['Arm_Extras'] = armExtraCtrls

    groups['Body'].extend(armSharedCtrls)

    # Decompose hand component
    #
    handCtrls = groups.pop('Hand', [])
    fingerFKCtrls = filterNodesByPattern(handCtrls, *__finger_controls__)
    fingerIKCtrls = filterNodesByPattern(handCtrls, *__finger_ik_controls__)
    fingerKinematicCtrls = fingerFKCtrls + fingerIKCtrls
    remainingHandCtrls = [ctrl for ctrl in handCtrls if ctrl not in fingerKinematicCtrls]

    groups['Hand'] = remainingHandCtrls
    groups['Fingers'] = fingerFKCtrls
    groups['Fingers_Extras'] = fingerIKCtrls

    # Consolidate prop components
    #
    groups['Props'] = groups.pop('Prop', [])

    keys = [key for key in groups.keys() if key.endswith('Stow')]
    groups['Stows'] = list(chain(*[groups.pop(key, []) for key in keys]))

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
