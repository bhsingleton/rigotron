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

        groups[component.__default_component_name__].extend(component.publishedNodes())

    # Consolidate root, spine and clavicle components
    #
    rootCtrls = groups.pop('Root', [])
    spineCtrls = groups.pop('Spine', [])
    clavicleCtrls = groups.pop('Clavicle', [])
    headCtrls = groups.pop('Head', [])

    groups['Body'] = rootCtrls + spineCtrls + clavicleCtrls + headCtrls

    # Decompose leg components
    #
    legCtrls = groups.pop('Leg', [])
    legFKCtrls = [ctrl for ctrl in legCtrls if fnmatchcase(ctrl.name(), '*_FK_CTRL')]
    legIKCtrls = [ctrl for ctrl in legCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*_Leg_CTRL', '*_Knee_CTRL', '*_IK_CTRL', '*_PV_CTRL')])]
    legExtraCtrls = [ctrl for ctrl in legCtrls if ctrl not in legFKCtrls and ctrl not in legIKCtrls]

    groups['Leg_FK'] = legFKCtrls
    groups['Leg_IK'] = legIKCtrls
    groups['Leg_Extras'] = legExtraCtrls

    # Decompose arm components
    #
    armCtrls = groups.pop('Arm', [])
    armFKCtrls = [ctrl for ctrl in armCtrls if fnmatchcase(ctrl.name(), '*_FK_CTRL')]
    armIKCtrls = [ctrl for ctrl in armCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*_Arm_CTRL', '*_Elbow_CTRL', '*_IK_CTRL', '*_PV_CTRL')])]
    armExtraCtrls = [ctrl for ctrl in armCtrls if ctrl not in armFKCtrls and ctrl not in armIKCtrls]

    groups['Arm_FK'] = armFKCtrls
    groups['Arm_IK'] = armIKCtrls
    groups['Arm_Extras'] = armExtraCtrls

    # Decompose hand component
    #
    handCtrls = groups.pop('Hand', [])
    digitCtrls = [ctrl for ctrl in handCtrls if any([fnmatchcase(ctrl.name(), pattern) for pattern in ('*Metacarpal_CTRL', '*Finger_Master_CTRL', '*Finger??_CTRL', '*Finger_IK_CTRL', '*Thumb_Master_CTRL', '*Thumb??_CTRL', '*Thumb_IK_CTRL')])]
    extremityCtrls = [ctrl for ctrl in handCtrls if ctrl not in digitCtrls]

    groups['Hand'] = extremityCtrls
    groups['Fingers'] = digitCtrls

    # Consolidate prop components
    #
    propCtrls = groups.pop('Prop', [])
    stowedCtrls = groups.pop('StowedProp', [])

    groups['Props'] = propCtrls + stowedCtrls

    # Create display layers from groups
    #
    layer = None

    for (componentName, controls) in groups.items():

        layerName = f'{prefix}_{componentName}'

        if scene.objExists(layerName):

            layer = mpynode.MPyNode(layerName)

        else:

            layer = scene.createDisplayLayer(name=layerName)

        log.info(f'Organizing {layer} << {controls}')

        for control in controls:

            layer.addNode(control.object())
