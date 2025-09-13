import maya.cmds as mc
import maya.api.OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.maya.libs import transformutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getBoundingBoxByTypeName(typeName='mesh'):
    """
    Returns the scene bounding-box for the specified node types.

    :type typeName: str
    :rtype: om.MBoundingBox
    """

    scene = mpyscene.MPyScene()
    boundingBox = om.MBoundingBox(om.MPoint(-0.5, -0.5, -0.5), om.MPoint(0.5, 0.5, 0.5))

    for mesh in scene.iterNodesByTypeName(typeName):

        boundingBox.expand(mesh.boundingBox)

    return boundingBox


def createTransformBlends(fkJoint, ikJoint, blendJoint, name=None, blender=None):
    """
    Create the appropriate nodes needed to blend two kinematic chains.

    :type fkJoint: Union[mpynode.MPyNode, None]
    :type ikJoint: Union[mpynode.MPyNode, None]
    :type blendJoint: mpynode.MPyNode
    :type name: Union[str, None]
    :type blender: om.MPlug
    :rtype: mpynode.MPyNode
    """

    # Create transform blend
    #
    scene = mpyscene.MPyScene()
    transformBlend = scene.createNode('blendTransform', name=name)

    # Check if FK joint is valid
    #
    if fkJoint is not None:

        fkJoint.connectPlugs('translate', transformBlend['inTranslate1'])
        fkJoint.connectPlugs('rotateOrder', transformBlend['inRotateOrder1'])
        fkJoint.connectPlugs('rotate', transformBlend['inRotate1'])
        fkJoint.connectPlugs('scale', transformBlend['inScale1'])

    # Check if IK joint is valid
    #
    if ikJoint is not None:

        ikJoint.connectPlugs('translate', transformBlend['inTranslate2'])
        ikJoint.connectPlugs('rotateOrder', transformBlend['inRotateOrder2'])
        ikJoint.connectPlugs('rotate', transformBlend['inRotate2'])
        ikJoint.connectPlugs('scale', transformBlend['inScale2'])

    # Connect output
    #
    transformBlend.connectPlugs('outTranslate', blendJoint['translate'])
    transformBlend.connectPlugs(blendJoint['rotateOrder'], 'outRotateOrder')
    transformBlend.connectPlugs('outRotate', blendJoint['rotate'])
    transformBlend.connectPlugs('outScale', blendJoint['scale'])

    # Check if blend plug was supplied
    #
    if isinstance(blender, om.MPlug):

        transformBlend.connectPlugs(blender, 'blender')

    return transformBlend
