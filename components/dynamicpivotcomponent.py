from maya.api import OpenMaya as om
from mpy import mpyattribute
from enum import IntEnum
from dcc.python import stringutils
from dcc.dataclasses.colour import Colour
from dcc.maya.libs import transformutils, shapeutils
from dcc.maya.json import mshapeparser
from . import leafcomponent
from ..libs import Side, setuputils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DynamicPivotComponent(leafcomponent.LeafComponent):
    """
    Overload of `LeafComponent` that implements dynamic pivot components.
    """

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'DynamicPivot'
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0)
        ]
    )
    __default_pivot_degree__ = 1
    __default_pivot_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0)
        ]
    )
    __default_pivot_points__ = [
        om.MVector(0.0, -10.0, -10.0),
        om.MVector(0.0, 10.0, -10.0),
        om.MVector(0.0, 10.0, 10.0),
        om.MVector(0.0, -10.0, 10.0)
    ]
    # endregion

    # region Methods
    def invalidatePivotSpecs(self, pivotSpecs):
        """
        Rebuilds the internal pivot specs for this component.

        :type pivotSpecs: List[pivotspec.PivotSpec]
        :rtype: None
        """

        # Concatenate pivot name
        #
        pivotSpec, = self.resizePivotSpecs(1, pivotSpecs)
        pivotSpec.name = self.formatName(subname='Pivot', type='nurbsCurve')

        # Call parent method
        #
        super(DynamicPivotComponent, self).invalidatePivotSpecs(pivotSpecs)

    def buildPivots(self):
        """
        Builds the pivots for this component.

        :rtype: Union[Tuple[mpynode.MPyNode], None]
        """

        # Create pivot
        #
        pivotSpec, = self.pivotSpecs()

        pivot = self.scene.createNode('transform', name=pivotSpec.name)
        pivot.displayLocalAxis = True
        pivot.displayHandle = True
        pivotSpec.uuid = pivot.uuid()

        matrix = pivotSpec.getMatrix(default=self.__default_pivot_matrix__)
        pivot.setWorldMatrix(matrix)

        # Check if shape data exists
        #
        hasShape = not stringutils.isNullOrEmpty(pivotSpec.shapes)

        if hasShape:

            pivot.loadShapes(pivotSpec.shapes)

        else:

            controlPoints = list(map(om.MVector, self.__default_pivot_points__))
            controlPoints.extend(controlPoints[:self.__default_pivot_degree__])  # Periodic curves require overlapping points equal to the degree!

            pivot.addCurve(controlPoints, degree=self.__default_pivot_degree__, form=om.MFnNurbsCurve.kPeriodic)

        return (pivotSpec,)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        leafSpec, = self.skeletonSpecs()
        leafExportJoint = self.scene(leafSpec.uuid)

        componentSide = self.Side(self.componentSide)
        requiresMirroring = (componentSide == self.Side.RIGHT)
        mirrorSign = -1.0 if requiresMirroring else 1.0
        mirrorMatrix = self.__default_mirror_matrices__[componentSide]

        colorRGB = Colour(*shapeutils.COLOUR_SIDE_RGB[componentSide])
        lightColorRGB = colorRGB.lighter()
        darkColorRGB = colorRGB.darker()

        rigScale = self.findControlRig().getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Decompose foot pivot curve
        #
        pivotSpec, = self.pivotSpecs()
        hasPivotShape = not stringutils.isNullOrEmpty(pivotSpec.shapes)

        if not hasPivotShape:

            raise NotImplementedError(f'buildRig() component expects a valid pivot shape!')

        pivotCurveData = mshapeparser.loads(pivotSpec.shapes)[0]
        fnPivotCurve = om.MFnNurbsCurve(pivotCurveData)

        pivotCurvePoints = [om.MPoint(point) * pivotSpec.matrix for point in fnPivotCurve.cvPositions()]  # World-space points

        # Add intermediate shape to leaf pivot space
        #
        leafPivoterSpaceName = self.formatName(subname='Pivoter', type='space')
        leafPivoterSpace = self.scene.createNode('transform', name=leafPivoterSpaceName, parent=controlsGroup)
        leafPivoterSpace.setWorldMatrix(pivotSpec.matrix, skipScale=True)
        leafPivoterSpace.freezeTransform()
        leafPivoterSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        leafPivoterCtrlName = self.formatName(subname='Pivoter', type='control')
        leafPivoterCtrl = self.scene.createNode('transform', name=leafPivoterCtrlName, parent=leafPivoterSpace)
        leafPivoterCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leafPivoterCtrl, alias='Pivoter')

        leafPivoterInverseMatrix = leafPivoterSpace.worldInverseMatrix()
        leafPivoterCurvePoints = [point * leafPivoterInverseMatrix for point in pivotCurvePoints]

        leafPivoterCurve = leafPivoterCtrl.addCurve(leafPivoterCurvePoints, degree=fnPivotCurve.degree, form=fnPivotCurve.form)
        leafPivoterCurve.setName(f'{leafPivoterCtrl.name()}Shape')
        leafPivoterCurve.objectColor = 2
        leafPivoterCurve.objectColorRGB = colorRGB

        # Add foot control shape
        #
        localMin, localMax = om.MVector(leafPivoterCurve.getAttr('boundingBoxMin')), om.MVector(leafPivoterCurve.getAttr('boundingBoxMax'))
        localCenter = (localMin * 0.5) + (localMax * 0.5)
        localWidth, localHeight, localDepth = leafPivoterCurve.getAttr('boundingBoxSize')

        # Setup leaf pivot controls
        #
        localHalfHeight = localHeight * 0.5
        localHalfDepth = localDepth * 0.5

        leafPivotCtrlName = self.formatName(subname='Pivoter', type='control')
        leafPivotCtrl = self.scene.createNode('transform', name=leafPivoterCtrlName, parent=leafPivoterCtrl)
        leafPivotCtrl.addCurve(
            [
                (0.0, 0.0, 0.0),
                (0.0, 0.0, localHalfDepth),
                (0.0, -localHalfHeight, localHalfDepth),
                (0.0, 0.0, localHalfDepth + localHalfHeight),
                (0.0, localHalfHeight, localHalfDepth),
                (0.0, 0.0, localHalfDepth),
                (0.0, 0.0, 0.0),
                (localHalfDepth, 0.0, 0.0),
                (-localHalfDepth, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, -localHalfDepth),
                (0.0, -localHalfHeight, -localHalfDepth),
                (0.0, 0.0, -localHalfDepth - localHalfHeight),
                (0.0, localHalfHeight, -localHalfDepth),
                (0.0, 0.0, -localHalfDepth),
                (0.0, 0.0, 0.0)
            ],
            degree=1,
            form=om.MFnNurbsCurve.kClosed,
            colorRGB=lightColorRGB
        )
        leafPivotCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leafPivotCtrl, alias='Pivot')

        leafCenterName = self.formatName(subname='Center', type='vectorMath')
        leafCenter = self.scene.createNode('vectorMath', name=leafCenterName)
        leafCenter.operation = 9  # Average
        leafCenter.connectPlugs(leafPivoterCurve['boundingBoxMin'], 'inFloatA')
        leafCenter.connectPlugs(leafPivoterCurve['boundingBoxMax'], 'inFloatB')

        leafPivotMatrixName = self.formatName(subname='Pivot', type='composeMatrix')
        leafPivotMatrix = self.scene.createNode('composeMatrix', name=leafPivotMatrixName)
        leafPivotMatrix.connectPlugs(leafCenter['outFloat'], 'inputTranslate')
        leafPivotMatrix.connectPlugs('outputMatrix', leafPivotCtrl['offsetParentMatrix'])

        leafPivotMultMatrixName = self.formatName(subname='Pivot', type='multMatrix')
        leafPivotMultMatrix = self.scene.createNode('multMatrix', name=leafPivotMultMatrixName)
        leafPivotMultMatrix.connectPlugs(leafPivotCtrl[f'worldMatrix[{leafPivotCtrl.instanceNumber()}]'], 'matrixIn[0]')
        leafPivotMultMatrix.connectPlugs(leafPivoterCurve[f'worldInverseMatrix[{leafPivoterCurve.instanceNumber()}]'], 'matrixIn[1]')

        leafPivotName = self.formatName(subname='Pivot', type='vectorProduct')
        leafPivot = self.scene.createNode('vectorProduct', name=leafPivotName)
        leafPivot.operation = 3  # Vector matrix product
        leafPivot.input1 = (1.0, 0.0, 0.0)
        leafPivot.connectPlugs(leafPivotMultMatrix['matrixSum'], 'matrix')

        leafNormalName = self.formatName(subname='Normal', type='vectorProduct')
        leafNormal = self.scene.createNode('vectorProduct', name=leafNormalName)
        leafNormal.operation = 3  # Vector matrix product
        leafNormal.input1 = (1.0, 0.0, 0.0)
        leafNormal.connectPlugs(leafPivoterCurve['matrix'], 'matrix')

        leafProjectedVectorName = self.formatName(subname='ProjectedVector', type='vectorMath')
        leafProjectedVector = self.scene.createNode('vectorMath', name=leafProjectedVectorName)
        leafProjectedVector.operation = 18  # Project
        leafProjectedVector.normalize = True
        leafProjectedVector.connectPlugs(leafNormal['output'], 'inFloatA')
        leafProjectedVector.connectPlugs(leafPivot['output'], 'inFloatB')

        leafMaxSizeName = self.formatName(subname='MaxSize', type='max')
        leafMaxSize = self.scene.createNode('max', name=leafMaxSizeName)
        leafMaxSize.connectPlugs(leafPivoterCurve['boundingBoxSizeX'], 'input[0]')
        leafMaxSize.connectPlugs(leafPivoterCurve['boundingBoxSizeY'], 'input[1]')
        leafMaxSize.connectPlugs(leafPivoterCurve['boundingBoxSizeZ'], 'input[2]')

        leafScaledVectorName = self.formatName(subname='ScaledVector', type='vectorMath')
        leafScaledVector = self.scene.createNode('vectorMath', name=leafScaledVectorName)
        leafScaledVector.operation = 2  # Multiply
        leafScaledVector.connectPlugs(leafProjectedVector['outFloat'], 'inFloatA')
        leafScaledVector.connectPlugs(leafMaxSize['output'], 'inFloatB')

        leafInputName = self.formatName(subname='Point', type='vectorMath')
        leafInput = self.scene.createNode('vectorMath', name=leafInputName)
        leafInput.operation = 0  # Add
        leafInput.connectPlugs(leafCenter['outFloat'], 'inFloatA')
        leafInput.connectPlugs(leafScaledVector['outFloat'], 'inFloatB')

        leafPointOnCurveName = self.formatName(subname='Pivot', type='nearestPointOnCurve')
        leafPointOnCurve = self.scene.createNode('nearestPointOnCurve', name=leafPointOnCurveName)
        leafPointOnCurve.connectPlugs(leafPivoterCurve['local'], 'inputCurve')
        leafPointOnCurve.connectPlugs(leafInput['outFloat'], 'inPosition')

        leafVectorLengthName = self.formatName(subname='VectorLength', type='length')
        leafVectorLength = self.scene.createNode('length', name=leafVectorLengthName)
        leafVectorLength.connectPlugs(leafProjectedVector['outFloat'], 'input')

        leafPivotConditionName = self.formatName(subname='Pivot', type='condition')
        leafPivotCondition = self.scene.createNode('condition', name=leafPivotConditionName)
        leafPivotCondition.operation = 2  # Greater than
        leafPivotCondition.secondTerm = 0.001  # Super important!
        leafPivotCondition.connectPlugs(leafVectorLength['output'], 'firstTerm')
        leafPivotCondition.connectPlugs(leafPointOnCurve['result.position'], 'colorIfTrue')
        leafPivotCondition.connectPlugs(leafCenter['outFloat'], 'colorIfFalse')

        leafPivotTargetName = self.formatName(subname='Pivot', type='target')
        leafPivotTarget = self.scene.createNode('transform', name=leafPivotTargetName, parent=leafPivoterCtrl)
        leafPivotTarget.connectPlugs(leafPivotCondition['outColor'], 'rotatePivot')
        leafPivotTarget.connectPlugs(leafPivotCtrl['rotateOrder'], 'rotateOrder')
        leafPivotTarget.connectPlugs(leafPivotCtrl['rotate'], 'rotate')
        leafPivotTarget.connectPlugs(leafPivotCondition['outColor'], 'scalePivot')
        leafPivotTarget.connectPlugs(leafPivotCtrl['scale'], 'scale')
        leafPivotTarget.connectPlugs(leafPivotCtrl['translate'], 'translate')

        leafPivotTargetShape = leafPivotTarget.addPointHelper('centerMarker')
        leafPivotTargetShape.template = True

        # Create control
        #
        leafSpaceName = self.formatName(type='space')
        leafSpace = self.scene.createNode('transform', name=leafSpaceName, parent=controlsGroup)
        leafSpace.copyTransform(leafExportJoint)
        leafSpace.freezeTransform()
        leafSpace.addConstraint('transformConstraint', [leafPivotTarget], maintainOffset=True)

        leafCtrl = self.scene.createNode('transform', name=leafSpec.driver, parent=leafSpace)
        leafCtrl.addPointHelper('box', size=(10.0 * rigScale), colorRGB=colorRGB)
        leafCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leafCtrl, alias=self.componentName)

        leafCtrl.userProperties['space'] = leafSpace.uuid()

        # Tag controls
        #
        leafPivoterCtrl.tagAsController(children=[leafPivotCtrl])
        leafPivotCtrl.tagAsController(parent=leafPivoterCtrl, children=[leafCtrl])
        leafCtrl.tagAsController(parent=leafPivotCtrl)
    # endregion
