import maya.cmds as mc
import maya.api.OpenMaya as om

from mpy import mpyscene, mpynode
from dcc.maya.libs import transformutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def createTransformBlends(fkJoint, ikJoint, blendJoint, blender=None):
    """
    Create the appropriate nodes needed to blend two kinematic chains.

    :type fkJoint: mpynode.MPyNode
    :type ikJoint: mpynode.MPyNode
    :type blendJoint: mpynode.MPyNode
    :type blender: om.MPlug
    :rtype: mpynode.MPyNode
    """

    # Create color blend nodes
    #
    scene = mpyscene.MPyScene()
    transformBlend = scene.createNode('blendTransform')

    fkJoint.connectPlugs('translate', transformBlend['inTranslate1'])
    fkJoint.connectPlugs('rotateOrder', transformBlend['inRotateOrder1'])
    fkJoint.connectPlugs('rotate', transformBlend['inRotate1'])
    fkJoint.connectPlugs('jointOrient', transformBlend['inJointOrient1'])
    fkJoint.connectPlugs('scale', transformBlend['inScale1'])

    ikJoint.connectPlugs('translate', transformBlend['inTranslate2'])
    ikJoint.connectPlugs('rotateOrder', transformBlend['inRotateOrder2'])
    ikJoint.connectPlugs('rotate', transformBlend['inRotate2'])
    ikJoint.connectPlugs('jointOrient', transformBlend['inJointOrient2'])
    ikJoint.connectPlugs('scale', transformBlend['inScale2'])

    # Connect result
    #
    transformBlend.connectPlugs('outTranslate', blendJoint['translate'])
    transformBlend.connectPlugs(blendJoint['rotateOrder'], 'outRotateOrder')
    transformBlend.connectPlugs('outRotate', blendJoint['rotate'])
    transformBlend.connectPlugs('outJointOrient', blendJoint['jointOrient'])
    transformBlend.connectPlugs('outScale', blendJoint['scale'])

    # Check if blend plug was supplied
    #
    if isinstance(blender, om.MPlug):

        transformBlend.connectPlugs(blender, 'blender')

    return transformBlend
