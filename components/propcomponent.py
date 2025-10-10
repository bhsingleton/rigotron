from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import transformutils, shapeutils
from . import basecomponent
from ..libs import Side, Type

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PropComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements prop components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Prop'
    __default_component_matrices__ = {
        Side.LEFT: om.MMatrix(
            [
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (100.0, 0.0, 150.0, 1.0)
            ]
        ),
        Side.RIGHT: om.MMatrix(
            [
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (-100.0, 0.0, 150.0, 1.0)
            ]
        ),
        Side.CENTER: om.MMatrix(
            [
                (0.0, -1.0, 0.0, 0.0),
                (0.0, 0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (0.0, -50.0, 150.0, 1.0)
            ]
        ),
        Side.NONE: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )
    }
    # endregion

    # region Attributes
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Edit skeleton specs
        #
        propSide = self.Side(self.componentSide)
        propType = self.Type.PROP_A if (propSide == self.Side.LEFT) else self.Type.PROP_B if (propSide == self.Side.RIGHT) else self.Type.PROP_C

        propSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        propSpec.name = self.formatName()
        propSpec.side = propSide
        propSpec.type = propType
        propSpec.defaultMatrix = self.__default_component_matrices__[propSide]
        propSpec.driver.name = self.formatName(subname='Offset', type='control')

        # Call parent method
        #
        return super(PropComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def isWeapon(self):
        """
        Evaluates if this prop is used as a weapon.

        :rtype: bool
        """

        return False

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        propSpec, = self.skeleton()
        propExportJoint = propSpec.getNode()
        propExportMatrix = propExportJoint.worldMatrix()

        componentSide = self.Side(self.componentSide)
        requiresMirroring = (componentSide == self.Side.RIGHT)
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        # Create prop control
        #
        propMatrix = mirrorMatrix * propExportMatrix

        propSpaceName = self.formatName(type='space')
        propSpace = self.scene.createNode('transform', name=propSpaceName, parent=controlsGroup)
        propSpace.setWorldMatrix(propMatrix)
        propSpace.freezeTransform()

        propSpaceSwitch = propSpace.addSpaceSwitch([], weighted=True, maintainOffset=True)

        propCtrlName = self.formatName(type='control')
        propCtrl = self.scene.createNode('transform', name=propCtrlName, parent=propSpace)
        propCtrl.addPointHelper('cross', size=15.0, colorRGB=colorRGB, lineWidth=4.0)
        propCtrl.prepareChannelBoxForAnimation()
        self.publishNode(propCtrl, alias='Prop')

        propOffsetCtrlName = self.formatName(subname='Offset', type='control')
        propOffsetCtrl = self.scene.createNode('transform', name=propOffsetCtrlName, parent=propCtrl)
        propOffsetCtrl.addPointHelper('cylinder', size=15.0, colorRGB=lightColorRGB, lineWidth=2.0)
        propOffsetCtrl.prepareChannelBoxForAnimation()
        self.publishNode(propOffsetCtrl, alias='Offset')

        propCtrl.userProperties['space'] = propSpace.uuid()
        propCtrl.userProperties['offset'] = propOffsetCtrl.uuid()
        propCtrl.userProperties['spaceSwitch'] = propSpaceSwitch.uuid()

    def repairOppositeRig(self):
        """
        Repairs any broken connections on the opposite prop component.

        :rtype: None
        """

        # Check if opposite control exists
        #
        propCtrl = self.getPublishedNode('Prop')
        oppositePropCtrl = propCtrl.getOppositeNode()

        hasOpposite = (oppositePropCtrl is not self) and (oppositePropCtrl is not None)

        if not hasOpposite:

            return

        # Get opposite space switch
        #
        oppositePropSpaceSwitch = self.scene(oppositePropCtrl.userProperties['spaceSwitch'])
        oppositePropSpaceSwitch.repair()

    def finalizeRig(self):
        """
        Notifies the component that the rig requires finalizing.
        Please note that some of the targets are out of order to preserve animation data on older rigs!

        :rtype: None
        """

        # Find spine space targets
        #
        rootComponent = self.findRootComponent()
        worldCtrl = rootComponent.getPublishedNode('Motion')

        spineComponents = rootComponent.findComponentDescendants('SpineComponent')
        spineComponent = spineComponents[0] if (len(spineComponents) == 1) else None
        pelvisCtrl, chestCtrl = None, None

        if spineComponent is not None:

            pelvisCtrl = spineComponent.getPublishedNode('Pelvis')
            chestCtrl = spineComponent.getPublishedNode('Chest')

        # Find hand space targets
        #
        parentComponent = spineComponent if (spineComponent is not None) else rootComponent
        handComponents = parentComponent.findComponentDescendants('HandComponent')

        leftHandComponents = [component for component in handComponents if component.componentSide == self.Side.LEFT and component.componentId == self.componentId]
        leftHandComponent = leftHandComponents[0] if (len(leftHandComponents) > 0) else None
        rightHandComponents = [component for component in handComponents if component.componentSide == self.Side.RIGHT and component.componentId == self.componentId]
        rightHandComponent = rightHandComponents[0] if (len(rightHandComponents) > 0) else None

        hasLeftHand = getattr(leftHandComponent, 'componentStatus', self.Status.META) == self.Status.RIG
        leftHandCtrl = leftHandComponent.getPublishedNode('Hand') if hasLeftHand else None
        leftForearmCtrl = leftHandComponent.componentParent().getPublishedNode('Forearm_Twist02') if hasLeftHand else None

        hasRightHand = getattr(rightHandComponent, 'componentStatus', self.Status.META) == self.Status.RIG
        rightHandCtrl = rightHandComponent.getPublishedNode('Hand') if hasRightHand else None
        rightForearmCtrl = rightHandComponent.componentParent().getPublishedNode('Forearm_Twist02') if hasRightHand else None

        isWeapon = self.isWeapon()
        hasLeftForearm, hasRightForearm = (hasLeftHand and isWeapon), (hasRightHand and isWeapon)

        # Evaluate component side
        #
        propCtrl = self.getPublishedNode('Prop')
        propOffsetCtrl = self.scene(propCtrl.userProperties['offset'])
        propSpaceSwitch = self.scene(propCtrl.userProperties['spaceSwitch'])

        componentSide = self.Side(self.componentSide)

        if componentSide == self.Side.LEFT:

            # Add position space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW5', niceName='Position Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))
            propCtrl.addAttr(longName='positionSpaceW6', niceName='Position Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHand, hidden=(not hasRightHand))

            # Add position space attributes
            #
            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW5', niceName='Rotation Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))
            propCtrl.addAttr(longName='rotationSpaceW6', niceName='Rotation Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHand, hidden=(not hasRightHand))

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl, leftHandCtrl, rightHandCtrl, leftForearmCtrl, rightForearmCtrl])
            propSpaceSwitch.setAttr(
                'target',
                [
                    {'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetRotate': (-90.0, 0.0, -90.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 1.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)}
                ]
            )
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW5'], 'target[5].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW6'], 'target[6].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW5'], 'target[5].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW6'], 'target[6].targetRotateWeight')

            if hasRightHand:

                propSpaceSwitch.mirrorTarget(3)
                propSpaceSwitch.mirrorTarget(5)

        elif componentSide == self.Side.RIGHT:

            # Add position space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW5', niceName='Position Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=hasRightHand, hidden=(not hasRightHand))
            propCtrl.addAttr(longName='positionSpaceW6', niceName='Position Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))

            # Add rotation space attributes
            #
            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW5', niceName='Rotation Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=hasRightHand, hidden=(not hasRightHand))
            propCtrl.addAttr(longName='rotationSpaceW6', niceName='Rotation Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl, rightHandCtrl, leftHandCtrl, rightForearmCtrl, leftForearmCtrl])
            propSpaceSwitch.setAttr(
                'target',
                [
                    {'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetRotate': (90.0, 0.0, 90.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 1.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)}
                ]
            )
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW5'], 'target[5].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW6'], 'target[6].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW5'], 'target[5].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW6'], 'target[6].targetRotateWeight')

            if hasLeftHand:

                propSpaceSwitch.mirrorTarget(3)
                propSpaceSwitch.mirrorTarget(5)

        elif componentSide == self.Side.CENTER:

            # Add position space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW5', niceName='Position Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))
            propCtrl.addAttr(longName='positionSpaceW6', niceName='Position Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHand, hidden=(not hasRightHand))

            # Add rotation space attributes
            #
            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW5', niceName='Rotation Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))
            propCtrl.addAttr(longName='rotationSpaceW6', niceName='Rotation Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHand, hidden=(not hasRightHand))

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl, leftHandCtrl, rightHandCtrl, leftForearmCtrl, rightForearmCtrl])
            propSpaceSwitch.setAttr(
                'target',
                [
                    {'targetWeight': (0.0, 0.0, 0.0), 'targetOffsetRotate': (-90.0, 0.0, -90.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 1.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)}
                ]
            )
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW5'], 'target[5].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW6'], 'target[6].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW5'], 'target[5].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW6'], 'target[6].targetRotateWeight')

            propPosition = propCtrl.translation(space=om.MSpace.kWorld)
            isLeftSided = propPosition.x > 1e-3
            isRightSided = propPosition.x < -1e-3

            if isLeftSided and (hasLeftHand and hasRightHand):

                propSpaceSwitch.mirrorTarget(3)
                propSpaceSwitch.mirrorTarget(5)

            elif isRightSided and (hasLeftHand and hasRightHand):

                propSpaceSwitch.mirrorTarget(4)
                propSpaceSwitch.mirrorTarget(6)

            else:

                pass

        else:

            # Add space attributes
            #
            propCtrl.addDivider('Spaces')
            propCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='positionSpaceW5', niceName='Position Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='positionSpaceW3', niceName='Position Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))
            propCtrl.addAttr(longName='positionSpaceW6', niceName='Position Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='positionSpaceW4', niceName='Position Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHand, hidden=(not hasRightHand))

            propCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (Pelvis)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Chest)', attributeType='float', min=0.0, max=1.0, keyable=True)
            propCtrl.addAttr(longName='rotationSpaceW5', niceName='Rotation Space (L_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftForearm, hidden=(not hasLeftForearm))
            propCtrl.addAttr(longName='rotationSpaceW3', niceName='Rotation Space (L_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasLeftHand, hidden=(not hasLeftHand))
            propCtrl.addAttr(longName='rotationSpaceW6', niceName='Rotation Space (R_Forearm)', attributeType='float', min=0.0, max=1.0, keyable=hasRightForearm, hidden=(not hasRightForearm))
            propCtrl.addAttr(longName='rotationSpaceW4', niceName='Rotation Space (R_Hand)', attributeType='float', min=0.0, max=1.0, keyable=hasRightHand, hidden=(not hasRightHand))

            # Add targets to space switch
            #
            propSpaceSwitch.addTargets([worldCtrl, pelvisCtrl, chestCtrl, leftHandCtrl, rightHandCtrl, leftForearmCtrl, rightForearmCtrl], maintainOffset=True)
            propSpaceSwitch.setAttr(
                'target',
                [
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 1.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)},
                    {'targetWeight': (0.0, 0.0, 0.0)}
                ]
            )
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW3'], 'target[3].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW4'], 'target[4].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW5'], 'target[5].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['positionSpaceW6'], 'target[6].targetTranslateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW3'], 'target[3].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW4'], 'target[4].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW5'], 'target[5].targetRotateWeight')
            propSpaceSwitch.connectPlugs(propCtrl['rotationSpaceW6'], 'target[6].targetRotateWeight')

        # Check if opposite rig requires repairs
        #
        self.repairOppositeRig()
    # endregion
