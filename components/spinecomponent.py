from collections.abc import MutableSequence

from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from typing import List, Union
from enum import IntEnum
from collections import namedtuple
from dcc.dataclasses.colour import Colour
from dcc.math import floatmath
from dcc.maya.libs import transformutils, shapeutils
from rigomatic.libs import kinematicutils
from . import basecomponent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


SpineFKPair = namedtuple('SpineFKPair', ('rot', 'trans'))


class SpinePivotType(IntEnum):
    """
    Collection of all available spine pivots.
    """

    COG = 0


class SpineComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements spine components.
    """

    # region Enums
    SpinePivotType = SpinePivotType
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Spine'
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 100.0, 1.0)
        ]
    )
    __default_component_spacing__ = 20.0
    __default_pivot_matrices__ = {
        SpinePivotType.COG: om.MMatrix(
            [
                (0.0, 0.0, 1.0, 0.0),
                (0.0, -1.0, 0.0, 0.0),
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )
    }
    # endregion

    # region Attributes
    spineEnabled = mpyattribute.MPyAttribute('spineEnabled', attributeType='bool', default=True)
    numSpineLinks = mpyattribute.MPyAttribute('numSpineLinks', attributeType='int', min=2, default=3)

    @spineEnabled.changed
    def spineEnabled(self, spineEnabled):
        """
        Changed method that notifies any spine state changes.

        :type spineEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @numSpineLinks.changed
    def numSpineLinks(self, numSpineLinks):
        """
        Changed method that notifies any spine-link size changes.

        :type numSpineLinks: int
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def invalidatePivots(self, pivotSpecs, **kwargs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: List[pivotspec.PivotSpec]
        """

        # Resize pivot specs
        #
        pivotTypes = self.SpinePivotType.__members__
        numPivotTypes = len(pivotTypes)

        cogSpec, = self.resizePivots(numPivotTypes, pivotSpecs)

        # Edit COG spec
        #
        pelvisSpec, nullSpec, *spineSpecs = self.skeleton(flatten=True)

        cogSpec.name = self.formatName(subname='COG', type='locator')
        cogSpec.defaultMatrix = self.__default_pivot_matrices__[self.SpinePivotType.COG]
        cogSpec.driver.name = nullSpec.name if nullSpec.enabled else pelvisSpec.name
        cogSpec.driver.namespace = self.skeletonNamespace()
        cogSpec.driver.type = cogSpec.driver.Type.OFFSET_PARENT_MATRIX

        # Call parent method
        #
        return super(SpineComponent, self).invalidatePivots(pivotSpecs, **kwargs)

    def repairPivots(self, force=False):
        """
        Repairs the internal pivot specs for this component.

        :rtype: None
        """

        # Evaluate parent matrix
        #
        cogSpec, = self.pivots(force=True)
        cogSpec.enabled = True

        requiresUpdating = cogSpec.parentMatrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3)

        if requiresUpdating or force:

            # Update parent matrix
            #
            driver = cogSpec.driver.getDriver()
            parentMatrix = driver.worldMatrix()

            cogSpec.parentMatrix = parentMatrix

            # Check if transformation matrix requires updating
            #
            matrix = cogSpec.matrix.asMatrix()
            isIdentityMatrix = matrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3)

            if not isIdentityMatrix:

                cogSpec.matrix = matrix * parentMatrix.inverse()

        # Call parent method
        #
        return super(SpineComponent, self).repairPivots(force=force)

    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Resize skeleton specs
        #
        numSpineLinks = int(self.numSpineLinks)
        skeletonSize = 2 + numSpineLinks

        pelvisSpec, nullSpec, *spineSpecs = self.resizeSkeleton(skeletonSize, skeletonSpecs, hierarchical=True)

        # Edit pelvis spec
        #
        pelvisSpec.name = self.formatName(name='Pelvis')
        pelvisSpec.side = self.componentSide
        pelvisSpec.type = self.Type.HIP
        pelvisSpec.defaultMatrix = om.MMatrix(self.__default_component_matrix__)
        pelvisSpec.driver.name = self.formatName(name='Pelvis', type='control')

        # Edit null spec
        #
        spineEnabled = bool(self.spineEnabled)

        nullSpec.enabled = spineEnabled
        nullSpec.name = self.formatName(name='Null', subname='Spine')
        nullSpec.side = self.componentSide
        nullSpec.type = self.Type.SPINE
        nullSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_component_spacing__, 0.0, 0.0))
        nullSpec.driver.name = self.formatName(name='UpperBody', subname='Align', type='control')

        # Edit spine specs
        #
        for (i, spineSpec) in enumerate(spineSpecs, start=1):

            isFirstSpineSpec = (i == 1)
            isLastSpineSpec = (i == numSpineLinks)
            spineSign = 0.0 if isFirstSpineSpec else 1.0

            spineSpec.enabled = spineEnabled
            spineSpec.name = self.formatName(name='Spine', index=i)
            spineSpec.side = self.componentSide
            spineSpec.type = self.Type.SPINE
            spineSpec.defaultMatrix = transformutils.createTranslateMatrix((self.__default_component_spacing__ * spineSign, 0.0, 0.0))

            if isLastSpineSpec:

                spineSpec.driver.name = self.formatName(name='Chest', type='control')

            else:

                spineSpec.driver.name = self.formatName(name='Spine', index=i, type='control')

        # Call parent method
        #
        return super(SpineComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def buildFullRig(self):
        """
        Builds the full spine rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        pelvisSpec, nullSpec, *spineSpecs = self.skeleton(flatten=True, skipDisabled=False)
        pelvisExportJoint = pelvisSpec.getNode()
        spineNullJoint = nullSpec.getNode()
        spineExportJoints = [spineSpec.getNode() for spineSpec in spineSpecs if spineSpec.enabled]
        firstSpineExportJoint, lastSpineExportJoint = spineExportJoints[0], spineExportJoints[-1]

        cogSpec, = self.pivots()
        cogMatrix = om.MMatrix(cogSpec.worldMatrix)

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Find world-space control
        #
        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        # Check if spine tip exists
        #
        headComponents = [component for component in self.findComponentDescendants('HeadComponent') if component.neckEnabled]
        headExists = len(headComponents) == 1
        neckEnabled = headComponents[0].neckEnabled if headExists else False

        spineTipPoint = None

        if neckEnabled:

            headComponent = headComponents[0]
            neckSpec, = headComponent.skeleton()
            neckExportJoint = neckSpec.getNode()

            spineTipPoint = neckExportJoint.translation(space=om.MSpace.kWorld)

        # Create COG controller
        #
        cogSpaceName = self.formatName(name='COG', type='space')
        cogSpace = self.scene.createNode('transform', name=cogSpaceName, parent=controlsGroup)
        cogSpace.setWorldMatrix(cogMatrix, skipScale=True)
        cogSpace.freezeTransform()
        cogSpace.addConstraint('transformConstraint', [motionCtrl], maintainOffset=True)

        cogCtrlName = self.formatName(name='COG', type='control')
        cogCtrl = self.scene.createNode('transform', name=cogCtrlName, parent=cogSpace)
        cogCtrl.addPointHelper('square', size=(50.0 * rigScale), localRotate=(45.0, 90.0, 0.0), lineWidth=4.0, colorRGB=colorRGB)
        cogCtrl.prepareChannelBoxForAnimation()
        self.publishNode(cogCtrl, alias='COG')

        cogPivotCtrlName = self.formatName(name='COG', subname='Pivot', type='control')
        cogPivotCtrl = self.scene.createNode('transform', name=cogPivotCtrlName, parent=cogSpace)
        cogPivotCtrl.addPointHelper('axisTripod', 'cross', size=(10.0 * rigScale), colorRGB=darkColorRGB)
        cogPivotCtrl.connectPlugs('translate', cogCtrl['rotatePivot'])
        cogPivotCtrl.connectPlugs('translate', cogCtrl['scalePivot'])
        cogPivotCtrl.hideAttr('rotate', 'scale', lock=True)
        cogPivotCtrl.prepareChannelBoxForAnimation()
        self.publishNode(cogPivotCtrl, alias='COG_Pivot')

        cogPivotMatrixName = self.formatName(name='COG', subname='Pivot', type='composeMatrix')
        cogPivotMatrix = self.scene.createNode('composeMatrix', name=cogPivotMatrixName)
        cogPivotMatrix.connectPlugs(cogCtrl['translate'], 'inputTranslate')
        cogPivotMatrix.connectPlugs('outputMatrix', cogPivotCtrl['offsetParentMatrix'])

        cogCtrl.userProperties['space'] = cogSpace.uuid()
        cogCtrl.userProperties['pivot'] = cogPivotCtrl.uuid()

        # Create waist control
        #
        legComponents = self.findComponentDescendants('LegComponent')
        numLegComponents = len(legComponents)
        hasLegComponents = numLegComponents >= 2

        waistMatrix = transformutils.createRotationMatrix(self.__default_component_matrix__) * transformutils.createTranslateMatrix(pelvisExportJoint.worldMatrix())

        if hasLegComponents:

            legJoints = [legComponent.skeleton()[0].getNode() for legComponent in legComponents]
            weight = 1.0 / numLegComponents

            waistCenter = sum([legJoint.translation(space=om.MSpace.kWorld) * weight for legJoint in legJoints], start=om.MVector.kZeroVector)
            waistMatrix = transformutils.createRotationMatrix(self.__default_component_matrix__) * transformutils.createTranslateMatrix([0.0, waistCenter.y, waistCenter.z])

        preEulerRotation = transformutils.decomposeTransformMatrix(waistMatrix)[1]

        waistSpaceName = self.formatName(name='Waist', type='space')
        waistSpace = self.scene.createNode('transform', name=waistSpaceName, parent=controlsGroup)
        waistSpace.setWorldMatrix(waistMatrix, skipRotate=True)
        waistSpace.freezeTransform()
        waistSpace.addConstraint('transformConstraint', [cogCtrl], maintainOffset=True)

        waistCtrlName = self.formatName(name='Waist', type='control')
        waistCtrl = self.scene.createNode('freeform', name=waistCtrlName, parent=waistSpace)
        waistCtrl.addShape('CradleCurve', size=(40.0 * rigScale), localScale=(1.0, 1.0, 1.25), lineWidth=4.0, colorRGB=colorRGB)
        waistCtrl.setPreEulerRotation(preEulerRotation)
        waistCtrl.prepareChannelBoxForAnimation()
        self.publishNode(waistCtrl, alias='Waist')

        waistCtrl.userProperties['space'] = waistSpace.uuid()

        # Create hips control
        #
        firstSpineMatrix = spineExportJoints[0].worldMatrix()
        hipsMatrix = transformutils.alignMatrixToNearestAxes(firstSpineMatrix, om.MMatrix.kIdentity)
        hipsShapeMatrix = waistMatrix * hipsMatrix.inverse()
        localPosition, localRotate, localScale = transformutils.decomposeTransformMatrix(hipsShapeMatrix)

        hipsSpaceName = self.formatName(name='Hips', type='space')
        hipsSpace = self.scene.createNode('transform', name=hipsSpaceName, parent=controlsGroup)
        hipsSpace.setWorldMatrix(hipsMatrix)
        hipsSpace.freezeTransform()

        hipsCtrlName = self.formatName(name='Hips', type='control')
        hipsCtrl = self.scene.createNode('transform', name=hipsCtrlName, parent=hipsSpace)
        hipsCtrl.addShape('HandleBarCurve', size=(45.0 * rigScale), localPosition=localPosition, localRotate=localRotate, localScale=(0.25, 0.25, 1.25), colorRGB=lightColorRGB)
        hipsCtrl.addDivider('Settings')
        hipsCtrl.addAttr(longName='spineInfluence', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
        hipsCtrl.addDivider('Spaces')
        hipsCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
        hipsCtrl.prepareChannelBoxForAnimation()
        self.publishNode(hipsCtrl, alias='Hips')

        hipsSpaceSwitch = hipsSpace.addSpaceSwitch([waistCtrl, motionCtrl], weighted=True, maintainOffset=True)
        hipsSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        hipsSpaceSwitch.connectPlugs(hipsCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        hipsSpaceSwitch.connectPlugs(hipsCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

        hipsCtrl.userProperties['space'] = hipsSpace.uuid()
        hipsCtrl.userProperties['spaceSwitch'] = hipsSpaceSwitch.uuid()

        pelvisSpaceName = self.formatName(name='Pelvis', type='space')
        pelvisSpace = self.scene.createNode('transform', name=pelvisSpaceName, parent=controlsGroup)
        pelvisSpace.copyTransform(pelvisExportJoint)
        pelvisSpace.freezeTransform()
        pelvisSpace.addConstraint('transformConstraint', [hipsCtrl], maintainOffset=True)

        pelvisCtrlName = self.formatName(name='Pelvis', type='control')
        pelvisCtrl = self.scene.createNode('transform', name=pelvisCtrlName, parent=pelvisSpace)
        pelvisCtrl.addPointHelper('diamond', size=(12.0 * rigScale), colorRGB=darkColorRGB)
        pelvisCtrl.prepareChannelBoxForAnimation()
        self.publishNode(pelvisCtrl, alias='Pelvis')

        pelvisCtrl.userProperties['space'] = pelvisSpace.uuid()

        # Create spine FK controls
        #
        spineCount = len(spineExportJoints)
        lastSpineIndex = spineCount - 1

        spineFKCtrls = [None] * spineCount  # type: List[SpineFKPair]

        for (i, spineJoint) in enumerate(spineExportJoints):

            # Evaluate position in chain
            #
            if 0 <= i < lastSpineIndex:

                # Create spine FK rotate control
                #
                index = str(i + 1).zfill(2)

                spineFKRotSpaceName = self.formatName(name='Spine', subname='FK', index=index, kinemat='Rot', type='space')
                spineFKRotSpace = self.scene.createNode('transform', name=spineFKRotSpaceName, parent=controlsGroup)
                spineFKRotSpace.copyTransform(spineJoint)
                spineFKRotSpace.freezeTransform()

                spineFKRotCtrlName = self.formatName(name='Spine', subname='FK', index=index, kinemat='Rot', type='control')
                spineFKRotCtrl = self.scene.createNode('transform', name=spineFKRotCtrlName, parent=spineFKRotSpace)
                spineFKRotCtrl.addPointHelper('disc', size=(24.0 * rigScale), localScale=(1.0, 1.0, 1.5), colorRGB=lightColorRGB, lineWidth=2.0)
                spineFKRotCtrl.addDivider('Spaces')
                spineFKRotCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
                spineFKRotCtrl.prepareChannelBoxForAnimation()
                self.publishNode(spineFKRotCtrl, alias=f'Spine{index}_FK_Rot')

                localSpaceCtrl = spineFKCtrls[i - 1].rot if (i > 0) else waistCtrl
                targets = (localSpaceCtrl, motionCtrl)

                spineFKRotSpaceSwitch = spineFKRotSpace.addSpaceSwitch(targets, weighted=True)
                spineFKRotSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                spineFKRotSpaceSwitch.connectPlugs(spineFKRotCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                spineFKRotSpaceSwitch.connectPlugs(spineFKRotCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                spineFKRotCtrl.userProperties['space'] = spineFKRotSpace.uuid()
                spineFKRotCtrl.userProperties['spaceSwitch'] = spineFKRotSpaceSwitch.uuid()

                # Check if spine FK translate control is required
                #
                spineFKTransCtrl = None

                if i > 0:

                    index = str(i).zfill(2)

                    spineFKTransCtrlName = self.formatName(name='Spine', subname='FK', index=index, kinemat='Trans', type='control')
                    spineFKTransCtrl = self.scene.createNode('transform', name=spineFKTransCtrlName, parent=spineFKRotCtrl)
                    spineFKTransCtrl.addShape('LollipopCurve', size=(28.0 * rigScale), localRotate=(0.0, 90.0, 0.0), colorRGB=lightColorRGB)
                    spineFKTransCtrl.prepareChannelBoxForAnimation()
                    self.publishNode(spineFKTransCtrl, alias=f'Spine{index}_FK_Trans')

                    spineFKRotCtrl.userProperties['translate'] = spineFKTransCtrl.uuid()
                    spineFKTransCtrl.userProperties['rotate'] = spineFKRotCtrl.uuid()

                spineFKCtrls[i] = SpineFKPair(spineFKRotCtrl, spineFKTransCtrl)

            else:

                # Create chest FK rotate control
                #
                chestFKRotSpaceName = self.formatName(name='Chest', subname='FK', kinemat='Rot', type='space')
                chestFKRotSpace = self.scene.createNode('transform', name=chestFKRotSpaceName, parent=controlsGroup)
                chestFKRotSpace.copyTransform(spineJoint)
                chestFKRotSpace.freezeTransform()

                chestFKRotCtrlName = self.formatName(name='Chest', subname='FK', kinemat='Rot', type='control')
                chestFKRotCtrl = self.scene.createNode('transform', name=chestFKRotCtrlName, parent=chestFKRotSpace)
                chestFKRotCtrl.addPointHelper('disc', size=(24.0 * rigScale), localScale=(1.0, 1.0, 1.5), colorRGB=lightColorRGB, lineWidth=2.0)
                chestFKRotCtrl.addDivider('Spaces')
                chestFKRotCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
                chestFKRotCtrl.prepareChannelBoxForAnimation()
                self.publishNode(chestFKRotCtrl, alias='Chest_FK_Rot')

                targets = (spineFKCtrls[i - 1].rot, motionCtrl)

                chestFKRotSpaceSwitch = chestFKRotSpace.addSpaceSwitch(targets, weighted=True)
                chestFKRotSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                chestFKRotSpaceSwitch.connectPlugs(chestFKRotCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                chestFKRotSpaceSwitch.connectPlugs(chestFKRotCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                chestFKRotCtrl.userProperties['space'] = chestFKRotSpace.uuid()
                chestFKRotCtrl.userProperties['spaceSwitch'] = chestFKRotSpaceSwitch.uuid()

                # Create chest FK translate control
                #
                chestFKTransCtrlName = self.formatName(name='Chest', subname='FK', kinemat='Trans', type='control')
                chestFKTransCtrl = self.scene.createNode('transform', name=chestFKTransCtrlName, parent=chestFKRotCtrl)
                chestFKTransCtrl.addShape('LollipopCurve', size=(28.0 * rigScale), localRotate=(0.0, 90.0, 0.0), colorRGB=lightColorRGB)
                chestFKTransCtrl.prepareChannelBoxForAnimation()
                self.publishNode(chestFKTransCtrl, alias=f'Chest_FK_Trans')

                chestFKRotCtrl.userProperties['translate'] = chestFKTransCtrl.uuid()
                chestFKTransCtrl.userProperties['rotate'] = chestFKRotCtrl.uuid()

                spineFKCtrls[i] = SpineFKPair(chestFKRotCtrl, chestFKTransCtrl)

        # Create spine FK tip target
        #
        spineFKTipTarget = None

        if neckEnabled:

            spineTipMatrix = transformutils.createTranslateMatrix(spineTipPoint)

            spineFKTipTargetName = self.formatName(name=f'{self.componentName}Tip', subname='FK', type='target')
            spineFKTipTarget = self.scene.createNode('transform', name=spineFKTipTargetName, parent=spineFKCtrls[-1].rot)
            spineFKTipTarget.displayLocalAxis = True
            spineFKTipTarget.visibility = False
            spineFKTipTarget.setWorldMatrix(spineTipMatrix, skipRotate=True, skipScale=True)
            spineFKTipTarget.freezeTransform()

            self.userProperties['spineTipFKTarget'] = spineFKTipTarget.uuid()

        # Create chest IK control
        #
        clavicleComponents = self.findComponentDescendants('ClavicleComponent')
        hasClavicles = len(clavicleComponents) > 0

        chestShapeOffset = om.MPoint.kOrigin

        if hasClavicles:

            clavicleJoints = [clavicleComponent.skeleton()[0].getNode() for clavicleComponent in clavicleComponents]
            clavicleWeight = 1.0 / len(clavicleJoints)
            clavicleCenter = sum([clavicleJoint.translation(space=om.MSpace.kWorld) * clavicleWeight for clavicleJoint in clavicleJoints], start=om.MVector.kZeroVector)

            chestShapeOffset = om.MPoint(clavicleCenter) * lastSpineExportJoint.worldInverseMatrix()

        chestIKSpaceName = self.formatName(name='Chest', subname='IK', type='space')
        chestIKSpace = self.scene.createNode('transform', name=chestIKSpaceName, parent=controlsGroup)
        chestIKSpace.copyTransform(lastSpineExportJoint)
        chestIKSpace.freezeTransform()
        chestIKSpace.addConstraint('transformConstraint', [spineFKCtrls[-1].rot])

        chestIKCtrlName = self.formatName(name='Chest', subname='IK', type='control')
        chestIKCtrl = self.scene.createNode('transform', name=chestIKCtrlName, parent=chestIKSpace)
        chestIKCtrl.addShape('CradleCurve', size=(25.0 * rigScale), localPosition=(chestShapeOffset.x, 0.0, 0.0), colorRGB=colorRGB, lineWidth=4.0)
        chestIKCtrl.addDivider('Settings')
        chestIKCtrl.addAttr(longName='stretch', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        chestIKCtrl.prepareChannelBoxForAnimation()
        self.publishNode(chestIKCtrl, alias='Chest_IK')

        chestIKCtrl.userProperties['space'] = chestIKSpace.uuid()

        # Create spine IK base and tip joints
        #
        firstSpineFKCtrl = spineFKCtrls[0].rot
        firstSpineFKSpace = self.scene(firstSpineFKCtrl.userProperties['space'])

        spineFKGlobalVectorName = self.formatName(subname='FK', index=1, kinemat='Global', type='multiplyVectorByMatrix')
        spineFKGlobalVector = self.scene.createNode('multiplyVectorByMatrix', name=spineFKGlobalVectorName)
        spineFKGlobalVector.connectPlugs(firstSpineFKCtrl['translate'], 'input')
        spineFKGlobalVector.connectPlugs(firstSpineFKCtrl[f'parentMatrix[{firstSpineFKCtrl.instanceNumber()}]'], 'matrix')

        spineFKLocalVectorName = self.formatName(subname='FK', index=1, kinemat='Local', type='multiplyVectorByMatrix')
        spineFKLocalVector = self.scene.createNode('multiplyVectorByMatrix', name=spineFKLocalVectorName)
        spineFKLocalVector.connectPlugs(spineFKGlobalVector['output'], 'input')
        spineFKLocalVector.connectPlugs(hipsCtrl[f'parentInverseMatrix[{hipsCtrl.instanceNumber()}]'], 'matrix')

        spineIKBaseJointName = self.formatName(subname='IK', kinemat='Base', type='joint')
        spineIKBaseJoint = self.scene.createNode('joint', name=spineIKBaseJointName, parent=jointsGroup)
        spineIKBaseJoint.copyTransform(firstSpineFKCtrl)

        spineIKBaseSpaceSwitch = spineIKBaseJoint.addSpaceSwitch([hipsCtrl, firstSpineFKCtrl, firstSpineFKSpace], weighted=True, maintainOffset=True)
        spineIKBaseSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 0.0)}, {'targetWeight': (0.0, 1.0, 0.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 1.0)}])
        spineIKBaseSpaceSwitch.connectPlugs(spineFKLocalVector['output'], 'target[0].targetOffsetTranslate')
        spineIKBaseSpaceSwitch.connectPlugs(hipsCtrl['spineInfluence'], 'target[0].targetRotateWeight')
        spineIKBaseSpaceSwitch.connectPlugs(hipsCtrl['spineInfluence'], 'target[1].targetRotateWeight')

        lastSpineFKCtrl = spineFKCtrls[-1].rot

        spineIKTipJointName = self.formatName(subname='IK', kinemat='Tip', type='joint')
        spineIKTipJoint = self.scene.createNode('joint', name=spineIKTipJointName, parent=jointsGroup)
        spineIKTipJoint.copyTransform(lastSpineFKCtrl)

        spineIKTipSpaceSwitch = spineIKTipJoint.addSpaceSwitch([chestIKCtrl, chestIKSpace], weighted=True, maintainOffset=True)
        spineIKTipSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 1.0, 0.0)}, {'targetWeight': (0.0, 0.0, 1.0)}])

        # Create spine IK curve
        #
        curveName = self.formatName(type='nurbsCurve')
        curve = self.scene.createNode('transform', name=curveName, subname='IK', parent=privateGroup)
        curve.inheritsTransform = False
        curve.lockAttr('translate', 'rotate', 'scale')

        controlPoints = [spineExportJoint.translation(space=om.MSpace.kWorld) for spineExportJoint in spineExportJoints]

        if spineTipPoint is not None:

            controlPoints.append(spineTipPoint)

        curveShape = curve.addCurve(controlPoints, degree=1)
        curveShape.dispCV = True
        curveShape.template = True

        # Add skin deformer to curve
        #
        influences = (spineIKBaseJoint.object(), spineIKTipJoint.object())

        skinCluster = curveShape.addDeformer('skinCluster')
        skinCluster.skinningMethod = 0  # Linear
        skinCluster.maxInfluences = 2
        skinCluster.maintainMaxInfluences = True
        skinCluster.addInfluences(*influences)

        firstSpineFKCtrl.connectPlugs(f'worldInverseMatrix[{firstSpineFKCtrl.instanceNumber()}]', skinCluster['bindPreMatrix[0]'])
        chestIKCtrl.connectPlugs(f'parentInverseMatrix[{chestIKCtrl.instanceNumber()}]', skinCluster['bindPreMatrix[1]'])

        # Collect spine curve source nodes
        #
        controlNodes = [spineFKTransCtrl if (spineFKTransCtrl is not None) else spineFKRotCtrl for (spineFKRotCtrl, spineFKTransCtrl) in spineFKCtrls]

        if neckEnabled:

            controlNodes.append(spineFKTipTarget)

        # Get curve length to derive initial skin weights from
        #
        intermediateCurve = skinCluster.intermediateObject()
        numControlPoints = int(intermediateCurve.numCVs)

        curveLength = 0.0

        if neckEnabled:

            chestPoint = intermediateCurve.cvPosition(numControlPoints - 2)
            maxParameter = intermediateCurve.getParamAtPoint(chestPoint)
            curveLength = intermediateCurve.findLengthFromParam(maxParameter)

        else:

            curveLength = intermediateCurve.length()

        # Create remap for skin weights
        #
        weightRemapName = self.formatName(subname='Weights', type='remapArray')
        weightRemap = self.scene.createNode('remapArray', name=weightRemapName)
        weightRemap.clamp = True
        weightRemap.setAttr('value', [{'value_FloatValue': 0.0, 'value_Interp': 2}, {'value_FloatValue': 1.0, 'value_Interp': 2}])

        parameters = [None] * numControlPoints

        for (i, controlNode) in enumerate(controlNodes):

            # Calculate parameter for point
            #
            point = intermediateCurve.cvPosition(i)
            param = intermediateCurve.getParamAtPoint(point)
            paramLength = intermediateCurve.findLengthFromParam(param)

            parameter = floatmath.clamp(paramLength / curveLength, 0.0, 1.0)
            parameters[i] = parameter

            # Add parameter to control node
            #
            controlNode.addAttr(longName='parameter', attributeType='float', min=0.0, max=1.0, hidden=True)
            controlNode.setAttr('parameter', parameter)
            controlNode.lockAttr('parameter')

            # Connect remap parameter
            #
            index = i + 1

            weightRemap.connectPlugs(controlNode['parameter'], f'parameter[{i}]')
            weightRemap.connectPlugs(f'outValue[{i}].outValueX', skinCluster[f'weightList[{i}].weights[1]'])

            reverseWeightName = self.formatName(subname='Weights', index=index, type='revDoubleLinear')
            reverseWeight = self.scene.createNode('revDoubleLinear', name=reverseWeightName)
            reverseWeight.connectPlugs(weightRemap[f'outValue[{i}].outValueX'], 'input')
            reverseWeight.connectPlugs('output', skinCluster[f'weightList[{i}].weights[0]'])

        self.userProperties['curve'] = curveShape.uuid()
        self.userProperties['intermediateCurve'] = intermediateCurve.uuid()
        self.userProperties['skinCluster'] = skinCluster.uuid()

        # Override control-points on intermediate-object
        #
        controlMatrices = [None] * numControlPoints  # type: List[mpynode.MPyNode]

        for (i, controlNode) in enumerate(controlNodes):

            index = i + 1

            multMatrixName = self.formatName(subname='ControlPoint', index=index, type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(controlNode[f'worldMatrix[{controlNode.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(intermediateCurve[f'parentInverseMatrix[{intermediateCurve.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(subname='ControlPoint', index=index, type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', intermediateCurve[f'controlPoints[{i}].xValue'], force=True)
            breakMatrix.connectPlugs('row4Y', intermediateCurve[f'controlPoints[{i}].yValue'], force=True)
            breakMatrix.connectPlugs('row4Z', intermediateCurve[f'controlPoints[{i}].zValue'], force=True)

            controlMatrices[i] = breakMatrix

        # Create spine IK joints
        #
        spineIKJoints = [None] * numControlPoints  # type: List[mpynode.MPyNode]

        for (i, (startNode, endNode)) in enumerate(zip(controlNodes[:-1], controlNodes[1:])):

            # Create IK joint
            #
            index = i + 1
            parent = spineIKJoints[i - 1] if (i > 0) else jointsGroup

            spineIKJointName = self.formatName(subname='IK', index=index, type='joint')
            spineIKJoint = self.scene.createNode('joint', name=spineIKJointName, parent=parent)

            # Re-orient IK joint
            #
            spineIKOrigin = startNode.translation(space=om.MSpace.kWorld)
            spineIKTarget = endNode.translation(space=om.MSpace.kWorld)
            spineIKMatrix = transformutils.createAimMatrix(
                0, (spineIKTarget - spineIKOrigin).normal(),
                1, transformutils.breakMatrix(startNode.worldMatrix(), normalize=True)[1],
                startPoint=spineIKOrigin
            )

            spineIKJoint.setWorldMatrix(spineIKMatrix)
            spineIKJoints[i] = spineIKJoint

            # Check if this is the last pair
            # If so, create tip joint from previous aim matrix
            #
            if endNode is controlNodes[-1]:

                lastSpineIKJointName = self.formatName(subname='IK', index=(index + 1), type='joint')
                lastSpineIKJoint = self.scene.createNode('joint', name=lastSpineIKJointName, parent=spineIKJoint)

                lastSpineIKMatrix = transformutils.createRotationMatrix(spineIKMatrix) * transformutils.createTranslateMatrix(spineIKTarget)
                lastSpineIKJoint.setWorldMatrix(lastSpineIKMatrix)

                spineIKJoints[-1] = lastSpineIKJoint

        spineIKTipTargetName = self.formatName(name=f'{self.componentName}Tip', subname='IK', type='target')
        spineIKTipTarget = self.scene.createNode('transform', name=spineIKTipTargetName, parent=privateGroup)
        spineIKTipTarget.displayLocalAxis = True

        spineIKTipTarget.addConstraint('pointConstraint', [spineIKJoints[-1]])
        spineIKTipTarget.addConstraint('orientConstraint', [chestIKCtrl])
        spineIKTipTarget.addConstraint('scaleConstraint', [chestIKCtrl])

        self.userProperties['spineTipIKTarget'] = spineIKTipTarget.uuid()

        # Setup spline IK solver
        #
        splineIKHandle, splineIKEffector = kinematicutils.applySplineSolver(spineIKJoints[0], spineIKJoints[-1], curveShape)
        splineIKHandle.setName(self.formatName(type='ikHandle'))
        splineIKHandle.setParent(privateGroup)
        splineIKHandle.visibility = False
        splineIKHandle.rootOnCurve = True
        splineIKHandle.rootTwistMode = True
        splineIKHandle.dTwistControlEnable = True
        splineIKHandle.dWorldUpType = 4  # Object Rotation Up (Start/End)
        splineIKHandle.dForwardAxis = 0  # Positive X
        splineIKHandle.dWorldUpAxis = 0  # Positive Y
        splineIKHandle.dWorldUpVector = (0.0, 1.0, 0.0)
        splineIKHandle.dWorldUpVectorEnd = (0.0, 1.0, 0.0)
        splineIKHandle.connectPlugs(spineIKBaseJoint[f'worldMatrix[{spineIKBaseJoint.instanceNumber()}]'], 'dWorldUpMatrix')
        splineIKHandle.connectPlugs(spineIKTipJoint[f'worldMatrix[{spineIKTipJoint.instanceNumber()}]'], 'dWorldUpMatrixEnd')

        self.userProperties['ikHandle'] = splineIKHandle.uuid()
        self.userProperties['ikEffector'] = splineIKEffector.uuid()

        # Setup spline IK stretch
        #
        curveInfoName = self.formatName(type='curveInfo')
        curveInfo = self.scene.createNode('curveInfo', name=curveInfoName)
        curveInfo.connectPlugs(curveShape[f'worldSpace[{curveShape.instanceNumber()}]'], 'inputCurve')

        intermediateInfoName = self.formatName(subname='Intermediate', type='curveInfo')
        intermediateInfo = self.scene.createNode('curveInfo', name=intermediateInfoName)
        intermediateInfo.connectPlugs(intermediateCurve[f'worldSpace[{intermediateCurve.instanceNumber()}]'], 'inputCurve')

        for (i, (startJoint, endJoint)) in enumerate(zip(spineIKJoints[:-1], spineIKJoints[1:])):

            # Create distance-between nodes
            #
            index = i + 1

            baseDistanceName = self.formatName(subname='Length', index=index, type='distanceBetween')
            baseDistance = self.scene.createNode('distanceBetween', name=baseDistanceName)
            baseDistance.connectPlugs(intermediateInfo[f'controlPoints[{i}]'], 'point1')
            baseDistance.connectPlugs(intermediateInfo[f'controlPoints[{i + 1}]'], 'point2')

            stretchDistanceName = self.formatName(subname='IntermediateLength', index=index, type='distanceBetween')
            stretchDistance = self.scene.createNode('distanceBetween', name=stretchDistanceName)
            stretchDistance.connectPlugs(curveInfo[f'controlPoints[{i}]'], 'point1')
            stretchDistance.connectPlugs(curveInfo[f'controlPoints[{i + 1}]'], 'point2')

            # Create spine-length multiplier
            #
            spineBlendName = self.formatName(subname='Length', index=index, type='blendTwoAttr')
            spineBlend = self.scene.createNode('blendTwoAttr', name=spineBlendName)
            spineBlend.connectPlugs(chestIKCtrl['stretch'], 'attributesBlender')
            spineBlend.connectPlugs(baseDistance['distance'], 'input[0]')
            spineBlend.connectPlugs(stretchDistance['distance'], 'input[1]')
            spineBlend.connectPlugs('output', endJoint['translateX'])

        # Setup scale remap
        #
        scaleRemapName = self.formatName(subname='Scale', type='remapArray')
        scaleRemap = self.scene.createNode('remapArray', name=scaleRemapName)
        scaleRemap.clamped = True
        scaleRemap.setAttr('parameter', parameters)
        scaleRemap.connectPlugs(hipsCtrl['scale'], 'outputMin')
        scaleRemap.connectPlugs(chestIKCtrl['scale'], 'outputMax')

        # Create spine controls
        #
        spineCtrls = [None] * spineCount

        for (i, (spineIKJoint, spineExportJoint)) in enumerate(zip(spineIKJoints, spineExportJoints)):  # It's okay if these mismatch since there is no tip export joint!

            # Evaluate position in loop
            #
            if i == lastSpineIndex:

                chestSpaceName = self.formatName(name='Chest', type='space')
                chestSpace = self.scene.createNode('transform', name=chestSpaceName, parent=controlsGroup)
                chestSpace.copyTransform(spineExportJoint)
                chestSpace.freezeTransform()
                chestSpace.addConstraint('parentConstraint', [spineIKJoint], maintainOffset=True)

                chestCtrlName = self.formatName(name='Chest', type='control')
                chestCtrl = self.scene.createNode('transform', name=chestCtrlName, parent=chestSpace)
                chestCtrl.addPointHelper('sphere', size=(6.0 * rigScale), colorRGB=darkColorRGB)
                chestCtrl.prepareChannelBoxForAnimation()
                self.publishNode(chestCtrl, alias=f'Chest')
                spineCtrls[i] = chestCtrl

                scaleConstraint = chestSpace.addConstraint('scaleConstraint', [spineFKCtrls[i].rot])
                scaleConstraint.connectPlugs(scaleRemap[f'outValue[{i}]'], 'offset')

            else:

                index = str(i + 1).zfill(2)

                spineSpaceName = self.formatName(index=index, type='space')
                spineSpace = self.scene.createNode('transform', name=spineSpaceName, parent=controlsGroup)
                spineSpace.copyTransform(spineExportJoint)
                spineSpace.freezeTransform()
                spineSpace.addConstraint('parentConstraint', [spineIKJoint], maintainOffset=True)

                spineCtrlName = self.formatName(index=index, type='control')
                spineCtrl = self.scene.createNode('transform', name=spineCtrlName, parent=spineSpace)
                spineCtrl.addPointHelper('sphere', size=(6.0 * rigScale), colorRGB=darkColorRGB)
                spineCtrl.prepareChannelBoxForAnimation()
                self.publishNode(spineCtrl, alias=f'Spine{index}')
                spineCtrls[i] = spineCtrl

                scaleConstraint = spineSpace.addConstraint('scaleConstraint', [spineFKCtrls[i].rot])
                scaleConstraint.connectPlugs(scaleRemap[f'outValue[{i}]'], 'offset')

        # Create upper-body align control
        #
        firstSpineCtrl = spineCtrls[0]

        upperBodySpaceName = self.formatName(name='UpperBody', subname='Align', type='space')
        upperBodySpace = self.scene.createNode('transform', name=upperBodySpaceName, parent=controlsGroup)
        upperBodySpace.setWorldMatrix(hipsMatrix)
        upperBodySpace.freezeTransform()

        upperBodyCtrlName = self.formatName(name='UpperBody', subname='Align', type='control')
        upperBodyCtrl = self.scene.createNode('transform', name=upperBodyCtrlName, parent=upperBodySpace)
        upperBodyCtrl.addShape('DoubleArrowCurve', size=(50.0 * rigScale), localRotate=(0.0, 90.0, 0.0), colorRGB=darkColorRGB)
        upperBodyCtrl.addDivider('Spaces')
        upperBodyCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, default=0.0, keyable=True)
        upperBodyCtrl.prepareChannelBoxForAnimation()
        self.publishNode(upperBodyCtrl, alias='UpperBody_Align')

        upperBodySpaceSwitch = upperBodySpace.addSpaceSwitch([firstSpineCtrl, hipsCtrl, motionCtrl], weighted=True)
        upperBodySpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, False, False)}, {'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        upperBodySpaceSwitch.connectPlugs(upperBodyCtrl['localOrGlobal'], 'target[1].targetRotateWeight')
        upperBodySpaceSwitch.connectPlugs(upperBodyCtrl['localOrGlobal'], 'target[2].targetRotateWeight')

        upperBodyCtrl.userProperties['space'] = upperBodySpace.uuid()
        upperBodyCtrl.userProperties['spaceSwitch'] = upperBodySpaceSwitch.uuid()

        # Tag controllers
        #
        cogCtrl.tagAsController(children=[waistCtrl])
        waistCtrl.tagAsController(parent=cogCtrl, children=[hipsCtrl, firstSpineFKCtrl, upperBodyCtrl])
        hipsCtrl.tagAsController(parent=waistCtrl, children=[pelvisCtrl, upperBodyCtrl])
        upperBodyCtrl.tagAsController(parent=hipsCtrl, children=[spineCtrls[0]])
        pelvisCtrl.tagAsController(parent=hipsCtrl)

        firstSpineFKCtrl.tagAsController(parent=waistCtrl)
        lastSpineFKCtrl.tagAsController(children=[chestIKCtrl])
        chestIKCtrl.tagAsController(parent=lastSpineFKCtrl)

        for (i, (spineFKPair, nextSpineFKPair)) in enumerate(zip(spineFKCtrls[:-1], spineFKCtrls[1:])):

            if i == 0:

                spineFKPair.rot.tagAsController(parent=parent, children=[nextSpineFKPair.rot])
                nextSpineFKPair.rot.tagAsController(parent=spineFKPair.rot)

            else:

                spineFKPair.rot.tagAsController(parent=parent, children=[nextSpineFKPair.rot, spineFKPair.trans])
                spineFKPair.trans.tagAsController(parent=spineFKPair.rot)
                nextSpineFKPair.rot.tagAsController(parent=spineFKPair.rot)

        for (i, (spineCtrl, nextSpineCtrl)) in enumerate(zip(spineCtrls[:-1], spineCtrls[1:])):

            parent = spineCtrls[i - 1] if (i > 0) else upperBodyCtrl

            spineCtrl.tagAsController(parent=parent, children=[nextSpineCtrl])
            nextSpineCtrl.tagAsController(parent=spineCtrl)

    def buildPartialRig(self):
        """
        Builds just the pelvis rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        pelvisSpec, nullSpec, *spineSpecs = self.skeleton(flatten=True, skipDisabled=False)
        pelvisExportJoint = pelvisSpec.getNode()
        pelvisMatrix = pelvisExportJoint.worldMatrix()

        cogSpec, = self.pivotSpecs()
        cogPivot = cogSpec.getNode()
        cogMatrix = cogPivot.worldMatrix()

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        componentSide = self.Side(self.componentSide)
        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        controlRig = self.findControlRig()
        rigDiameter = float(controlRig.rigRadius) * 2.0
        rigScale = controlRig.getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Find world-space control
        #
        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')

        # Create COG controller
        #
        cogSpaceName = self.formatName(name='COG', type='space')
        cogSpace = self.scene.createNode('transform', name=cogSpaceName, parent=controlsGroup)
        cogSpace.setWorldMatrix(cogMatrix, skipScale=True)
        cogSpace.freezeTransform()
        cogSpace.addConstraint('transformConstraint', [motionCtrl], maintainOffset=True)

        cogCtrlName = self.formatName(name='COG', type='control')
        cogCtrl = self.scene.createNode('transform', name=cogCtrlName, parent=cogSpace)
        cogCtrl.addPointHelper('square', size=(50.0 * rigScale), localRotate=(45.0, 90.0, 0.0), lineWidth=4.0, colorRGB=colorRGB)
        cogCtrl.prepareChannelBoxForAnimation()
        self.publishNode(cogCtrl, alias='COG')

        cogPivotCtrlName = self.formatName(name='COG', subname='Pivot', type='control')
        cogPivotCtrl = self.scene.createNode('transform', name=cogPivotCtrlName, parent=cogSpace)
        cogPivotCtrl.addPointHelper('axisTripod', 'cross', size=(10.0 * rigScale), colorRGB=darkColorRGB)
        cogPivotCtrl.connectPlugs('translate', cogCtrl['rotatePivot'])
        cogPivotCtrl.connectPlugs('translate', cogCtrl['scalePivot'])
        cogPivotCtrl.hideAttr('rotate', 'scale', lock=True)
        cogPivotCtrl.prepareChannelBoxForAnimation()

        cogPivotMatrixName = self.formatName(name='COG', subname='Pivot', type='composeMatrix')
        cogPivotMatrix = self.scene.createNode('composeMatrix', name=cogPivotMatrixName)
        cogPivotMatrix.connectPlugs(cogCtrl['translate'], 'inputTranslate')
        cogPivotMatrix.connectPlugs('outputMatrix', cogPivotCtrl['offsetParentMatrix'])

        cogCtrl.userProperties['space'] = cogSpace.uuid()
        cogCtrl.userProperties['pivot'] = cogPivotCtrl.uuid()

        # Create waist control
        #
        legComponents = self.findComponentDescendants('LegComponent')
        numLegComponents = len(legComponents)
        hasLegComponents = numLegComponents >= 2

        waistMatrix = transformutils.createRotationMatrix(self.__default_component_matrix__) * transformutils.createTranslateMatrix(pelvisExportJoint.worldMatrix())

        if hasLegComponents:

            legJoints = [legComponent.skeleton()[0].getNode() for legComponent in legComponents]
            weight = 1.0 / numLegComponents
            waistCenter = sum([legJoint.translation(space=om.MSpace.kWorld) * weight for legJoint in legJoints], start=om.MVector.kZeroVector)
            waistMatrix = transformutils.createRotationMatrix(self.__default_component_matrix__) * transformutils.createTranslateMatrix([0.0, waistCenter.y, waistCenter.z])

        preEulerRotation = transformutils.decomposeTransformMatrix(waistMatrix)[1]

        waistSpaceName = self.formatName(name='Waist', type='space')
        waistSpace = self.scene.createNode('transform', name=waistSpaceName, parent=controlsGroup)
        waistSpace.setWorldMatrix(waistMatrix, skipRotate=True)
        waistSpace.freezeTransform()
        waistSpace.addConstraint('transformConstraint', [cogCtrl], maintainOffset=True)

        waistCtrlName = self.formatName(name='Waist', type='control')
        waistCtrl = self.scene.createNode('freeform', name=waistCtrlName, parent=waistSpace)
        waistCtrl.addShape('CradleCurve', size=(40.0 * rigScale), localScale=(1.0, 1.0, 1.25), lineWidth=4.0, colorRGB=colorRGB)
        waistCtrl.setPreEulerRotation(preEulerRotation)
        waistCtrl.prepareChannelBoxForAnimation()
        self.publishNode(waistCtrl, alias='Waist')

        waistCtrl.userProperties['space'] = waistSpace.uuid()

        # Create hips control
        #
        pelvisShapeMatrix = waistMatrix * pelvisMatrix.inverse()
        localPosition, localRotate, localScale = transformutils.decomposeTransformMatrix(pelvisShapeMatrix)

        pelvisSpaceName = self.formatName(name='pelvis', type='space')
        pelvisSpace = self.scene.createNode('transform', name=pelvisSpaceName, parent=controlsGroup)
        pelvisSpace.setWorldMatrix(pelvisMatrix)
        pelvisSpace.freezeTransform()

        pelvisCtrlName = self.formatName(name='pelvis', type='control')
        pelvisCtrl = self.scene.createNode('transform', name=pelvisCtrlName, parent=pelvisSpace)
        pelvisCtrl.addShape('HandleBarCurve', size=(45.0 * rigScale), localPosition=localPosition, localRotate=localRotate, localScale=(0.25, 0.25, 1.25), colorRGB=lightColorRGB)
        pelvisCtrl.addDivider('Settings')
        pelvisCtrl.addAttr(longName='lookAt', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
        pelvisCtrl.addAttr(longName='lookAtOffset', niceName='Look-At Offset', attributeType='distance', min=1.0, default=rigDiameter, channelBox=True)
        pelvisCtrl.addDivider('Spaces')
        pelvisCtrl.addAttr(longName='positionSpaceW0', niceName='Position Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        pelvisCtrl.addAttr(longName='positionSpaceW1', niceName='Position Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        pelvisCtrl.addAttr(longName='positionSpaceW2', niceName='Position Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True, default=1.0)
        pelvisCtrl.addAttr(longName='rotationSpaceW0', niceName='Rotation Space (World)', attributeType='float', min=0.0, max=1.0, keyable=True)
        pelvisCtrl.addAttr(longName='rotationSpaceW1', niceName='Rotation Space (COG)', attributeType='float', min=0.0, max=1.0, keyable=True)
        pelvisCtrl.addAttr(longName='rotationSpaceW2', niceName='Rotation Space (Waist)', attributeType='float', min=0.0, max=1.0, keyable=True, default=1.0)
        pelvisCtrl.prepareChannelBoxForAnimation()
        self.publishNode(pelvisCtrl, alias='Pelvis')

        pelvisDefaultTargetName = self.formatName(name='Pelvis', subname='Default', type='target')
        pelvisDefaultTarget = self.scene.createNode('transform', name=pelvisDefaultTargetName, parent=privateGroup)
        pelvisDefaultTarget.displayLocalAxis = True
        pelvisDefaultTarget.visibility = False
        pelvisDefaultTarget.setWorldMatrix(pelvisMatrix)
        pelvisDefaultTarget.freezeTransform()

        pelvisDefaultSpaceSwitch = pelvisDefaultTarget.addSpaceSwitch([motionCtrl, cogCtrl, waistCtrl], weighted=True, maintainOffset=True)
        pelvisDefaultSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (0.0, 0.0, 0.0)}, {'targetWeight': (1.0, 1.0, 1.0)}])
        pelvisDefaultSpaceSwitch.connectPlugs(pelvisCtrl['positionSpaceW0'], 'target[0].targetTranslateWeight')
        pelvisDefaultSpaceSwitch.connectPlugs(pelvisCtrl['positionSpaceW1'], 'target[1].targetTranslateWeight')
        pelvisDefaultSpaceSwitch.connectPlugs(pelvisCtrl['positionSpaceW2'], 'target[2].targetTranslateWeight')
        pelvisDefaultSpaceSwitch.connectPlugs(pelvisCtrl['rotationSpaceW0'], 'target[0].targetRotateWeight')
        pelvisDefaultSpaceSwitch.connectPlugs(pelvisCtrl['rotationSpaceW1'], 'target[1].targetRotateWeight')
        pelvisDefaultSpaceSwitch.connectPlugs(pelvisCtrl['rotationSpaceW2'], 'target[2].targetRotateWeight')

        pelvisCtrl.userProperties['space'] = pelvisSpace.uuid()
        pelvisCtrl.userProperties['target'] = pelvisDefaultTarget.uuid()

        # Create pelvis look-at control
        #
        pelvisLookAtSpaceName = self.formatName(name='Pelvis', subname='LookAt', type='space')
        pelvisLookAtSpace = self.scene.createNode('transform', name=pelvisLookAtSpaceName, parent=controlsGroup)
        pelvisLookAtSpace.copyTransform(waistCtrl, skipRotate=True, skipScale=True)
        pelvisLookAtSpace.freezeTransform()

        pelvisLookAtGroupName = self.formatName(name='Pelvis', subname='LookAt', type='transform')
        pelvisLookAtGroup = self.scene.createNode('transform', name=pelvisLookAtGroupName, parent=pelvisLookAtSpace)
        pelvisLookAtGroup.setWorldMatrix(pelvisMatrix, skipRotate=True, skipScale=True)
        pelvisLookAtGroup.freezeTransform()

        pelvisLookAtCtrlName = self.formatName(name='Pelvis', subname='LookAt', type='control')
        pelvisLookAtCtrl = self.scene.createNode('transform', name=pelvisLookAtCtrlName, parent=pelvisLookAtGroup)
        pelvisLookAtCtrl.addPointHelper('sphere', 'centerMarker', size=(20.0 * rigScale), colorRGB=colorRGB)
        pelvisLookAtCtrl.addDivider('Spaces')
        pelvisLookAtCtrl.addAttr(longName='localOrGlobal',attributeType='float', min=0.0, max=1.0, keyable=True)
        pelvisLookAtCtrl.prepareChannelBoxForAnimation()
        self.publishNode(pelvisLookAtCtrl, alias='LookAt')
        
        pelvisLookAtSpaceSwitch = pelvisLookAtSpace.addSpaceSwitch([waistCtrl, motionCtrl], weighted=True, maintainOffset=True)
        pelvisLookAtSpaceSwitch.setAttr('target', [{'targetReverse': (True, False, False), 'targetWeight': (0.0, 0.0, 1.0)}, {'targetWeight': (0.0, 1.0, 0.0)}])
        pelvisLookAtSpaceSwitch.connectPlugs(pelvisLookAtCtrl['localOrGlobal'], 'target[0].targetTranslateWeight')
        pelvisLookAtSpaceSwitch.connectPlugs(pelvisLookAtCtrl['localOrGlobal'], 'target[1].targetTranslateWeight')
        
        # Setup head look-at offset
        #
        pelvisLookAtMatrix = pelvisLookAtGroup.getAttr('offsetParentMatrix')
        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(pelvisLookAtMatrix)

        pelvisLookAtComposeMatrixName = self.formatName(name='Pelvis', subname='LookAt', type='composeMatrix')
        pelvisLookAtComposeMatrix = self.scene.createNode('composeMatrix', name=pelvisLookAtComposeMatrixName)
        pelvisLookAtComposeMatrix.setAttr('inputTranslate', translation)
        pelvisLookAtComposeMatrix.setAttr('inputRotate', eulerRotation, convertUnits=False)

        pelvisLookAtOffsetInverseName = self.formatName(subname='LookAt', type='floatMath')
        pelvisLookAtOffsetInverse = self.scene.createNode('floatMath', name=pelvisLookAtOffsetInverseName)
        pelvisLookAtOffsetInverse.setAttr('operation', 5)  # Negate
        pelvisLookAtOffsetInverse.connectPlugs(pelvisCtrl['lookAtOffset'], 'inDistanceA')

        pelvisLookAtOffsetComposeMatrixName = self.formatName(subname='LookAtOffset', type='composeMatrix')
        pelvisLookAtOffsetComposeMatrix = self.scene.createNode('composeMatrix', name=pelvisLookAtOffsetComposeMatrixName)
        pelvisLookAtOffsetComposeMatrix.connectPlugs(pelvisLookAtOffsetInverse['outDistance'], 'inputTranslateY')

        pelvisLookAtMultMatrixName = self.formatName(subname='LookAt', type='multMatrix')
        pelvisLookAtMultMatrix = self.scene.createNode('multMatrix', name=pelvisLookAtMultMatrixName)
        pelvisLookAtMultMatrix.connectPlugs(pelvisLookAtOffsetComposeMatrix['outputMatrix'], 'matrixIn[0]')
        pelvisLookAtMultMatrix.connectPlugs(pelvisLookAtComposeMatrix['outputMatrix'], 'matrixIn[1]')
        pelvisLookAtMultMatrix.connectPlugs('matrixSum', pelvisLookAtGroup['offsetParentMatrix'])

        # Create pelvis look-at curve
        #
        curveData = shapeutils.createCurveFromPoints([om.MPoint.kOrigin, om.MPoint.kOrigin], degree=1)

        pelvisLookAtShapeName = self.formatName(subname='LookAtHandle', type='control')
        pelvisLookAtShape = self.scene.createNode('nurbsCurve', name=f'{pelvisLookAtShapeName}Shape', parent=pelvisLookAtCtrl)
        pelvisLookAtShape.setAttr('cached', curveData)
        pelvisLookAtShape.useObjectColor = 2
        pelvisLookAtShape.wireColorRGB = lightColorRGB

        for (i, node) in enumerate([pelvisLookAtCtrl, pelvisCtrl]):

            index = i + 1

            multMatrixName = self.formatName(name='Pelvis', subname='ControlPoint', index=index, type='multMatrix')
            multMatrix = self.scene.createNode('multMatrix', name=multMatrixName)
            multMatrix.connectPlugs(node[f'worldMatrix[{node.instanceNumber()}]'], 'matrixIn[0]')
            multMatrix.connectPlugs(pelvisLookAtShape[f'parentInverseMatrix[{pelvisLookAtShape.instanceNumber()}]'], 'matrixIn[1]')

            breakMatrixName = self.formatName(name='Pelvis', subname='ControlPoint', index=index, type='breakMatrix')
            breakMatrix = self.scene.createNode('breakMatrix', name=breakMatrixName)
            breakMatrix.connectPlugs(multMatrix['matrixSum'], 'inMatrix')
            breakMatrix.connectPlugs('row4X', pelvisLookAtShape[f'controlPoints[{i}].xValue'])
            breakMatrix.connectPlugs('row4Y', pelvisLookAtShape[f'controlPoints[{i}].yValue'])
            breakMatrix.connectPlugs('row4Z', pelvisLookAtShape[f'controlPoints[{i}].zValue'])

        # Create pelvis look-at target
        #
        pelvisLookAtTargetName = self.formatName(name='Pelvis', subname='LookAt', type='target')
        pelvisLookAtTarget = self.scene.createNode('transform', name=pelvisLookAtTargetName, parent=privateGroup)
        pelvisLookAtTarget.displayLocalAxis = True
        pelvisLookAtTarget.addConstraint('transformConstraint', [waistCtrl], skipRotate=True)
        pelvisLookAtTarget.addConstraint(
            'aimConstraint',
            [pelvisLookAtCtrl],
            aimVector=(0.0, 1.0, 0.0),
            upVector=(1.0, 0.0, 0.0),
            worldUpType=2,
            worldUpVector=(0.0, 0.0, 1.0),
            worldUpObject=pelvisLookAtCtrl
        )

        pelvisLookAtCtrl.userProperties['space'] = pelvisLookAtSpace.uuid()
        pelvisLookAtCtrl.userProperties['spaceSwitch'] = pelvisLookAtSpaceSwitch.uuid()
        pelvisLookAtCtrl.userProperties['group'] = pelvisLookAtGroup.uuid()
        pelvisLookAtCtrl.userProperties['target'] = pelvisLookAtTarget.uuid()

        # Setup pelvis space switching
        #
        pelvisSpaceSwitch = pelvisSpace.addSpaceSwitch([pelvisDefaultTarget, pelvisLookAtTarget], weighted=True, maintainOffset=True)
        pelvisSpaceSwitch.setAttr('target', [{'targetWeight': (0.0, 0.0, 0.0), 'targetReverse': (True, True, True)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        pelvisSpaceSwitch.connectPlugs(pelvisCtrl['lookAt'], 'target[0].targetRotateWeight')
        pelvisSpaceSwitch.connectPlugs(pelvisCtrl['lookAt'], 'target[1].targetRotateWeight')

        pelvisCtrl.userProperties['spaceSwitch'] = pelvisSpaceSwitch.uuid()

        # Tag controllers
        #
        cogCtrl.tagAsController(children=[waistCtrl])
        waistCtrl.tagAsController(parent=cogCtrl, children=[pelvisCtrl, pelvisLookAtCtrl])
        pelvisCtrl.tagAsController(parent=waistCtrl)
        pelvisLookAtCtrl.tagAsController(parent=waistCtrl)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        spineEnabled = bool(self.spineEnabled)

        if spineEnabled:

            return self.buildFullRig()

        else:

            return self.buildPartialRig()
    # endregion
