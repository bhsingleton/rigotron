from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from enum import IntEnum
from dcc.math import floatmath
from dcc.maya.libs import transformutils, plugutils
from . import basecomponent
from ..libs import Side, skeletonspec

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FaceType(IntEnum):
    """
    Enum class of all available face components.
    """

    UPPER = 0
    MID = 1
    LOWER = 2


class UpperFaceType(IntEnum):
    """
    Enum class of all upper-face subcomponents.
    """

    FOREHEAD = 0
    CENTER_BROW = 1
    LEFT_BROW = 2
    RIGHT_BROW = 3
    CENTER_EYES = 4
    LEFT_EYES = 5
    RIGHT_EYES = 6


class MidFaceType(IntEnum):
    """
    Enum class of all mid-face subcomponents.
    """

    LEFT_EAR = 0
    RIGHT_EAR = 1
    NOSE = 2
    LEFT_CHEEK = 3
    RIGHT_CHEEK = 4


class LowerFaceType(IntEnum):
    """
    Enum class of all lower-face subcomponents.
    """

    UPPER_LIPS = 0
    UPPER_TEETH = 1
    JAW = 2


class JawType(IntEnum):
    """
    Enum class of all jaw subcomponents.
    """

    TONGUE = 0
    LOWER_TEETH = 1
    LEFT_LIP_CORNER = 2
    LOWER_LIPS = 3
    RIGHT_LIP_CORNER = 4
    CHIN = 5
    THROAT = 6


class FaceComponent(basecomponent.BaseComponent):
    """
    Overload of `AbstractComponent` that implements face components.
    """

    # region Enums
    FaceType = FaceType
    UpperFaceType = UpperFaceType
    MidFaceType = MidFaceType
    LowerFaceType = LowerFaceType
    JawType = JawType
    # endregion

    # region Dunderscores
    __version__ = 1.0
    __default_component_name__ = 'Face'
    __default_component_matrix__ = om.MMatrix(
        [
            (0.0, 0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 210.0, 1.0)
        ]
    )
    __default_upperface_matrices__ = {
        UpperFaceType.FOREHEAD: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (40.0, 20.0, 0.0, 1.0)
            ]
        ),
        UpperFaceType.CENTER_BROW: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (30.0, 20.0, 0.0, 1.0)
            ]
        ),
        UpperFaceType.LEFT_BROW: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (30.0, 20.0, 5.0, 1.0)
            ]
        ),
        UpperFaceType.RIGHT_BROW: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (30.0, 20.0, -5.0, 1.0)
            ]
        ),
        UpperFaceType.CENTER_EYES: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (25.0, 20.0, 0.0, 1.0)
            ]
        ),
        UpperFaceType.LEFT_EYES: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (25.0, 20.0, 10.0, 1.0)
            ]
        ),
        UpperFaceType.RIGHT_EYES: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (25.0, 20.0, -10.0, 1.0)
            ]
        )
    }
    __default_midface_matrices__ = {
        MidFaceType.LEFT_EAR: om.MMatrix(
            [
                (0.0, -0.707107, 0.707107, 0.0),
                (0.0, 0.707107, 0.707107, 0.0),
                (-1.0, 0.0, 0.0, 0.0),
                (20.0, 0.0, 15.0, 1.0)
            ]
        ),
        MidFaceType.RIGHT_EAR: om.MMatrix(
            [
                (0.0, -0.707107, -0.707107, 0.0),
                (0.0, -0.707107, 0.707107, 0.0),
                (-1.0, 0.0, 0.0, 0.0),
                (20.0, 0.0, -15.0, 1.0)
            ]
        ),
        MidFaceType.NOSE: {
            Side.CENTER: om.MMatrix(
                [
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (10.0, 20.0, 0.0, 1.0)
                ]
            ),
            Side.LEFT: om.MMatrix(
                [
                    (0.0, 0.0, 1.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, -1.0, 0.0, 0.0),
                    (0.0, 0.0, 2.5, 1.0)
                ]
            ),
            Side.RIGHT: om.MMatrix(
                [
                    (0.0, 0.0, -1.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, -2.5, 1.0)
                ]
            ),
            Side.NONE: om.MMatrix(
                [
                    (0.0, 1.0, 0.0, 0.0),
                    (-1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, 2.5, 0.0, 1.0)
                ]
            )
        },
        MidFaceType.LEFT_CHEEK: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (15.0, 20.0, 5.0, 1.0)
            ]
        ),
        MidFaceType.RIGHT_CHEEK: om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (15.0, 20.0, -5.0, 1.0)
            ]
        )
    }
    __default_lowerface_matrices__ = {  # TODO: Populate default lower-face matrices!
        LowerFaceType.UPPER_LIPS: om.MMatrix.kIdentity,
        LowerFaceType.UPPER_TEETH: om.MMatrix.kIdentity,
        LowerFaceType.JAW: om.MMatrix.kIdentity
    }
    __default_jaw_matrices__ = {  # TODO: Populate default jaw matrices!
        JawType.TONGUE: om.MMatrix.kIdentity,
        JawType.LOWER_TEETH: om.MMatrix.kIdentity,
        JawType.LEFT_LIP_CORNER: om.MMatrix.kIdentity,
        JawType.LOWER_LIPS: om.MMatrix.kIdentity,
        JawType.RIGHT_LIP_CORNER: om.MMatrix.kIdentity,
        JawType.CHIN: om.MMatrix.kIdentity,
        JawType.THROAT: om.MMatrix.kIdentity
    }
    # endregion

    # region Attributes
    faceEnabled = mpyattribute.MPyAttribute('faceEnabled', attributeType='bool', default=False)
    splitFaceEnabled = mpyattribute.MPyAttribute('splitFaceEnabled', attributeType='bool', default=False)

    foreheadEnabled = mpyattribute.MPyAttribute('foreheadEnabled', attributeType='bool', default=True)

    centerBrowCount = mpyattribute.MPyAttribute('centerBrowCount', attributeType='int', min=0, max=5, default=1)
    leftBrowCount = mpyattribute.MPyAttribute('leftBrowCount', attributeType='int', min=0, max=5, default=2)
    rightBrowCount = mpyattribute.MPyAttribute('rightBrowCount', attributeType='int', min=0, max=5, default=2)

    centerEyeCount = mpyattribute.MPyAttribute('centerEyeCount', attributeType='int', min=0, max=3)
    leftEyeCount = mpyattribute.MPyAttribute('leftEyeCount', attributeType='int', min=0, max=3, default=1)
    rightEyeCount = mpyattribute.MPyAttribute('rightEyeCount', attributeType='int', min=0, max=3, default=1)

    leftCheekCount = mpyattribute.MPyAttribute('leftCheekCount', attributeType='int', min=0, max=5, default=2)
    rightCheekCount = mpyattribute.MPyAttribute('rightCheekCount', attributeType='int', min=0, max=5, default=2)

    noseEnabled = mpyattribute.MPyAttribute('noseEnabled', attributeType='bool', default=True)
    nostrilsEnabled = mpyattribute.MPyAttribute('nostrilsEnabled', attributeType='bool', default=True)
    noseTipEnabled = mpyattribute.MPyAttribute('noseTipEnabled', attributeType='bool', default=True)

    leftEarCount = mpyattribute.MPyAttribute('leftEarCount', attributeType='int', min=0, max=5, default=1)
    rightEarCount = mpyattribute.MPyAttribute('rightEarCount', attributeType='int', min=0, max=5, default=1)

    jawEnabled = mpyattribute.MPyAttribute('jawEnabled', attributeType='bool', default=True)
    teethEnabled = mpyattribute.MPyAttribute('teethEnabled', attributeType='bool', default=False)
    tongueCount = mpyattribute.MPyAttribute('tongueCount', attributeType='int', min=0, max=9, default=3)
    lipsEnabled = mpyattribute.MPyAttribute('lipsEnabled', attributeType='bool', default=True)
    lipSubdivisions = mpyattribute.MPyAttribute('lipSubdivisions', attributeType='int', min=1, max=9, default=3)
    chinEnabled = mpyattribute.MPyAttribute('chinEnabled', attributeType='bool', default=True)
    throatEnabled = mpyattribute.MPyAttribute('throatEnabled', attributeType='bool', default=True)

    @faceEnabled.changed
    def faceEnabled(self, faceEnabled):
        """
        Changed method that notifies of any state changes.

        :type faceEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @splitFaceEnabled.changed
    def splitFaceEnabled(self, splitFaceEnabled):
        """
        Changed method that notifies of any state changes.

        :type splitFaceEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @foreheadEnabled.changed
    def foreheadEnabled(self, foreheadEnabled):
        """
        Changed method that notifies of any state changes.

        :type foreheadEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @leftBrowCount.changed
    def leftBrowCount(self, leftBrowCount):
        """
        Changed method that notifies of any state changes.

        :type leftBrowCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @rightBrowCount.changed
    def rightBrowCount(self, rightBrowCount):
        """
        Changed method that notifies of any state changes.

        :type rightBrowCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @centerBrowCount.changed
    def centerBrowCount(self, centerBrowCount):
        """
        Changed method that notifies of any state changes.

        :type centerBrowCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @leftEyeCount.changed
    def leftEyeCount(self, leftEyeCount):
        """
        Changed method that notifies of any state changes.

        :type leftEyeCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @rightEyeCount.changed
    def rightEyeCount(self, rightEyeCount):
        """
        Changed method that notifies of any state changes.

        :type rightEyeCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @centerEyeCount.changed
    def centerEyeCount(self, centerEyeCount):
        """
        Changed method that notifies of any state changes.

        :type centerEyeCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @leftCheekCount.changed
    def leftCheekCount(self, leftCheekCount):
        """
        Changed method that notifies of any state changes.

        :type leftCheekCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @rightCheekCount.changed
    def rightCheekCount(self, rightCheekCount):
        """
        Changed method that notifies of any state changes.

        :type rightCheekCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @noseEnabled.changed
    def noseEnabled(self, noseEnabled):
        """
        Changed method that notifies of any state changes.

        :type noseEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @leftEarCount.changed
    def leftEarCount(self, leftEarCount):
        """
        Changed method that notifies of any state changes.

        :type leftEarCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @rightEarCount.changed
    def rightEarCount(self, rightEarCount):
        """
        Changed method that notifies of any state changes.

        :type rightEarCount: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @jawEnabled.changed
    def jawEnabled(self, jawEnabled):
        """
        Changed method that notifies of any state changes.

        :type jawEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.

        :type skeletonSpecs: List[skeletonspec.SkeletonSpec]
        :rtype: List[skeletonspec.SkeletonSpec]
        """

        # Resize skeleton specs
        #
        faceName = str(self.componentName)
        faceSide = self.Side(self.componentSide)
        faceEnabled = bool(self.faceEnabled)
        defaultFaceMatrix = om.MMatrix(self.__default_component_matrix__)
        defaultParentMatrix = defaultFaceMatrix if (not faceEnabled) else om.MMatrix.kIdentity

        faceSpec, = self.resizeSkeleton(1, skeletonSpecs, hierarchical=False)
        faceSpec.enabled = True
        faceSpec.name = self.formatName()
        faceSpec.passthrough = not faceEnabled
        faceSpec.side = faceSide
        faceSpec.type = self.Type.HEAD
        faceSpec.defaultMatrix = defaultFaceMatrix
        faceSpec.driver.name = self.formatName(type='control')

        faceSize = len(self.FaceType)
        upperFaceSpec, midFaceSpec, lowerFaceSpec, = self.resizeSkeleton(faceSize, faceSpec.children, hierarchical=False)

        # Edit upper-face spec
        #
        splitFace = bool(self.splitFaceEnabled)

        upperFaceSpec.enabled = True
        upperFaceSpec.name = self.formatName(name=f'Upper{faceName}')
        upperFaceSpec.passthrough = not splitFace
        upperFaceSpec.side = faceSide
        upperFaceSpec.type = self.Type.HEAD
        upperFaceSpec.driver.name = self.formatName(name=f'Upper{faceName}', type='control')

        upperFaceSize = len(self.UpperFaceType)
        upperFaceSpecs = self.resizeSkeleton(upperFaceSize, upperFaceSpec.children, hierarchical=False)

        # Edit forehead spec
        #
        initialForeheadMatrix = om.MMatrix(self.__default_upperface_matrices__[self.UpperFaceType.FOREHEAD])
        defaultForeheadMatrix = initialForeheadMatrix * defaultParentMatrix

        foreheadSpec = upperFaceSpecs[self.UpperFaceType.FOREHEAD]
        foreheadSpec.enabled = bool(self.foreheadEnabled)
        foreheadSpec.name = self.formatName(name='Forehead')
        foreheadSpec.side = faceSide
        foreheadSpec.type = self.Type.OTHER
        foreheadSpec.otherType = 'Forehead'
        foreheadSpec.defaultMatrix = defaultForeheadMatrix
        foreheadSpec.driver.name = self.formatName(name='Forehead', type='control')

        # Edit brow specs
        #
        centerBrowCount, leftBrowCount, rightBrowCount = int(self.centerBrowCount), int(self.leftBrowCount), int(self.rightBrowCount)

        centerBrowSpec = upperFaceSpecs[self.UpperFaceType.CENTER_BROW]
        leftBrowSpec = upperFaceSpecs[self.UpperFaceType.LEFT_BROW]
        rightBrowSpec = upperFaceSpecs[self.UpperFaceType.RIGHT_BROW]

        for (browSide, browSize, browSpec) in ((self.Side.CENTER, centerBrowCount, centerBrowSpec), (self.Side.LEFT, leftBrowCount, leftBrowSpec), (self.Side.RIGHT, rightBrowCount, rightBrowSpec)):

            browEnabled = (browSize > 0)
            browType = self.UpperFaceType[f'{browSide.name}_BROW']
            initialBrowMatrix = om.MMatrix(self.__default_upperface_matrices__[browType])

            browSpec.enabled = browEnabled
            browSpec.passthrough = True
            browSpec.name = self.formatName(side=browSide, name='Brow')
            browSpec.side = browSide
            browSpec.type = self.Type.OTHER
            browSpec.otherType = 'Brow'
            browSpec.driver.name = self.formatName(side=browSide, name='Brow', type='control')

            browSpecs = self.resizeSkeleton(browSize, browSpec)

            for (i, spec) in enumerate(browSpecs):

                browIndex = (i + 1) if (browSize >= 2) else None
                browSign = -1.0 if (browSide == self.Side.RIGHT) else 1.0
                offsetBrowMatrix = transformutils.createTranslateMatrix((0.0, 0.0, (5.0 * i) * browSign))
                defaultBrowMatrix = (offsetBrowMatrix * initialBrowMatrix) * defaultParentMatrix

                spec.enabled = browEnabled
                spec.name = self.formatName(side=browSide, name='Brow', index=browIndex)
                spec.side = faceSide
                spec.type = self.Type.OTHER
                spec.otherType = 'Brow'
                spec.defaultMatrix = defaultBrowMatrix
                spec.driver.name = self.formatName(side=browSide, name='Brow', index=browIndex, type='control')

        # Edit eyes spec
        #
        centerEyeCount, leftEyeCount, rightEyeCount = int(self.centerEyeCount), int(self.leftEyeCount), int(self.rightEyeCount)

        centerEyesSpec = upperFaceSpecs[self.UpperFaceType.CENTER_EYES]
        leftEyesSpec = upperFaceSpecs[self.UpperFaceType.LEFT_EYES]
        rightEyesSpec = upperFaceSpecs[self.UpperFaceType.RIGHT_EYES]

        for (eyeSide, eyeCount, eyesSpec) in ((self.Side.CENTER, centerEyeCount, centerEyesSpec), (self.Side.LEFT, leftEyeCount, leftEyesSpec), (self.Side.RIGHT, rightEyeCount, rightEyesSpec)):

            eyeEnabled = (eyeCount > 0)
            eyeType = self.UpperFaceType[f'{eyeSide.name}_EYES']
            initialEyeMatrix = om.MMatrix(self.__default_upperface_matrices__[eyeType])

            eyesSpec.enabled = eyeEnabled
            eyesSpec.passthrough = True
            eyesSpec.name = self.formatName(side=eyeSide, name='Eyes')
            eyesSpec.side = eyeSide
            eyesSpec.type = self.Type.OTHER
            eyesSpec.otherType = 'Eyes'
            eyesSpec.driver.name = self.formatName(side=eyeSide, name='Eyes', type='control')

            eyeSocketSpecs = self.resizeSkeleton(eyeCount, eyesSpec.children, hierarchical=False)

            for (i, eyeSocketSpec) in enumerate(eyeSocketSpecs):

                eyeIndex = (i + 1) if (eyeCount >= 2) else None
                offsetEyeMatrix = transformutils.createTranslateMatrix((5.0 * i, 0.0, 0.0))
                defaultEyeMatrix = (offsetEyeMatrix * initialEyeMatrix) * defaultParentMatrix

                eyeSocketSpec.enabled = eyeEnabled
                eyeSocketSpec.name = self.formatName(side=eyeSide, name='EyeSocket', index=eyeIndex)
                eyeSocketSpec.side = eyeSide
                eyeSocketSpec.type = self.Type.OTHER
                eyeSocketSpec.otherType = 'EyeSocket'
                eyeSocketSpec.drawStyle = self.Style.BOX
                eyeSocketSpec.defaultMatrix = defaultEyeMatrix
                eyeSocketSpec.driver.name = self.formatName(side=eyeSide, name='EyeSocket', index=eyeIndex, type='control')

                upperEyelidSpec, eyeSpec, lowerEyelidSpec = self.resizeSkeleton(3, eyeSocketSpec)

                upperEyelidSpec.enabled = eyeSocketSpec.enabled
                upperEyelidSpec.name = self.formatName(side=eyeSide, name='UpperEyelid', index=eyeIndex)
                upperEyelidSpec.side = eyeSide
                upperEyelidSpec.type = self.Type.OTHER
                upperEyelidSpec.otherType = 'UpperEyelid'
                upperEyelidSpec.defaultMatrix = transformutils.createRotationMatrix((0.0, 0.0, 45.0))
                upperEyelidSpec.driver.name = self.formatName(side=eyeSide, name='UpperEyelid', index=eyeIndex, type='control')

                eyeSpec.enabled = eyeSocketSpec.enabled
                eyeSpec.name = self.formatName(side=eyeSide, name='Eye', index=eyeIndex)
                eyeSpec.side = eyeSide
                eyeSpec.type = self.Type.OTHER
                eyeSpec.otherType = 'Eye'
                eyeSpec.defaultMatrix = transformutils.createRotationMatrix((0.0, 0.0, 90.0))
                eyeSpec.driver.name = self.formatName(side=eyeSide, name='Eye', index=eyeIndex, type='control')

                lowerEyelidSpec.enabled = eyeSocketSpec.enabled
                lowerEyelidSpec.name = self.formatName(side=eyeSide, name='LowerEyelid', index=eyeIndex)
                lowerEyelidSpec.side = eyeSide
                lowerEyelidSpec.type = self.Type.OTHER
                lowerEyelidSpec.otherType = 'LowerEyelid'
                lowerEyelidSpec.defaultMatrix = transformutils.createRotationMatrix((0.0, 0.0, 135.0))
                lowerEyelidSpec.driver.name = self.formatName(side=eyeSide, name='LowerEyelid', index=eyeIndex, type='control')
        
        # Resize mid-face specs
        #
        midFaceSpec.enabled = True
        midFaceSpec.name = self.formatName(name=f'Mid{faceName}')
        midFaceSpec.passthrough = not splitFace
        midFaceSpec.side = faceSide
        midFaceSpec.type = self.Type.HEAD
        midFaceSpec.driver.name = self.formatName(name=f'Mid{faceName}', type='control')

        midFaceSize = len(self.MidFaceType)
        midFaceSpecs = self.resizeSkeleton(midFaceSize, midFaceSpec.children, hierarchical=False)
        
        # Edit cheeks spec
        #
        leftCheekCount, rightCheekCount = int(self.leftCheekCount), int(self.rightCheekCount)

        leftCheekSpec = midFaceSpecs[self.MidFaceType.LEFT_CHEEK]
        rightCheekSpec = midFaceSpecs[self.MidFaceType.RIGHT_CHEEK]

        for (cheekSide, cheekCount, cheekSpec) in ((self.Side.LEFT, leftCheekCount, leftCheekSpec), (self.Side.RIGHT, rightCheekCount, rightCheekSpec)):

            cheekEnabled = (cheekCount > 0)
            cheekType = self.MidFaceType[f'{cheekSide.name}_CHEEK']
            cheekSign = -1.0 if (cheekSide == self.Side.RIGHT) else 1.0
            initialCheekMatrix = om.MMatrix(self.__default_midface_matrices__[cheekType])

            cheekSpec.enabled = cheekEnabled
            cheekSpec.passthrough = True
            cheekSpec.name = self.formatName(side=cheekSide, name='Cheek')
            cheekSpec.side = cheekSide
            cheekSpec.type = self.Type.OTHER
            cheekSpec.otherType = 'Cheek'
            cheekSpec.driver.name = self.formatName(side=cheekSide, name='Cheek', type='control')

            cheekSpecs = self.resizeSkeleton(cheekCount, cheekSpec.children, hierarchical=False)

            for (i, spec) in enumerate(cheekSpecs):

                cheekIndex = (i + 1)
                offsetCheekMatrix = transformutils.createTranslateMatrix((0.0, 0.0, (5.0 * i) * cheekSign))
                defaultCheekMatrix = (offsetCheekMatrix * initialCheekMatrix) * defaultParentMatrix

                spec.name = self.formatName(side=cheekSide, name='Cheek', index=cheekIndex)
                spec.side = cheekSide
                spec.type = self.Type.OTHER
                spec.otherType = 'Cheek'
                spec.defaultMatrix = defaultCheekMatrix
                spec.driver.name = self.formatName(side=cheekSide, name='Cheek', index=cheekIndex, type='control')

        # Edit ears spec
        #
        leftEarCount, rightEarCount = int(self.leftEarCount), int(self.rightEarCount)

        leftEarSpec = midFaceSpecs[self.MidFaceType.LEFT_EAR]
        rightEarSpec = midFaceSpecs[self.MidFaceType.RIGHT_EAR]

        for (earSide, earCount, earBaseSpec) in ((self.Side.LEFT, leftEarCount, leftEarSpec), (self.Side.RIGHT, rightEarCount, rightEarSpec)):

            earEnabled = (earCount > 0)
            earSize = floatmath.clamp(earCount, 1, None)
            isEarChain = (earSize >= 2)
            earType = self.MidFaceType[f'{earSide.name}_EAR']
            initialEarMatrix = om.MMatrix(self.__default_midface_matrices__[earType])

            *earSpecs, earTipSpec = self.resizeSkeleton(earSize, earBaseSpec, hierarchical=True)

            for (i, earSpec) in enumerate((earBaseSpec, *earSpecs, earTipSpec)):

                earIndex = (i + 1) if isEarChain else None
                defaultEarMatrix = (initialEarMatrix * defaultParentMatrix) if (i == 1) else transformutils.createTranslateMatrix((5.0, 0.0, 0.0))

                earSpec.side = earSide
                earSpec.type = self.Type.OTHER
                earSpec.otherType = 'Ear'
                earSpec.defaultMatrix = defaultEarMatrix

                if i == earSize:

                    earSpec.enabled = earEnabled and isEarChain
                    earSpec.name = self.formatName(side=earSide, name='EarTip')
                    earSpec.driver.name = self.formatName(side=earSide, name='EarTip', type='target')

                else:

                    earSpec.enabled = earEnabled
                    earSpec.name = self.formatName(side=earSide, name='Ear', index=earIndex)
                    earSpec.driver.name = self.formatName(side=earSide, name='Ear', index=earIndex, type='control')

        # Edit nose spec
        #
        noseEnabled = bool(self.noseEnabled)

        initialNoseMatrix = om.MMatrix(self.__default_midface_matrices__[self.MidFaceType.NOSE][self.Side.CENTER])
        defaultNoseMatrix = initialNoseMatrix * defaultParentMatrix

        noseSpec = midFaceSpecs[self.MidFaceType.NOSE]
        noseSpec.enabled = noseEnabled
        noseSpec.name = self.formatName(name='Nose')
        noseSpec.side = faceSide
        noseSpec.type = self.Type.OTHER
        noseSpec.otherType = 'Nose'
        noseSpec.drawStyle = self.Style.BOX
        noseSpec.defaultMatrix = defaultNoseMatrix
        noseSpec.driver.name = self.formatName(name='Nose', type='control')

        noseTipSpec, leftNostrilSpec, rightNostrilSpec = self.resizeSkeleton(3, noseSpec, hierarchical=False)

        for (nostrilSide, nostrilSpec) in ((self.Side.NONE, noseTipSpec), (self.Side.LEFT, leftNostrilSpec), (self.Side.RIGHT, rightNostrilSpec)):

            nostrilName = 'NoseTip' if (nostrilSide == Side.NONE) else 'Nostril'

            nostrilSpec.enabled = noseEnabled
            nostrilSpec.name = self.formatName(side=nostrilSide, name=nostrilName)
            nostrilSpec.side = nostrilSide
            nostrilSpec.type = self.Type.OTHER
            nostrilSpec.otherType = nostrilName
            nostrilSpec.defaultMatrix = om.MMatrix(self.__default_midface_matrices__[self.MidFaceType.NOSE][nostrilSide])
            nostrilSpec.driver.name = self.formatName(side=nostrilSide, name=nostrilName, type='control')

        # Resize lower-face specs
        #
        lowerFaceSpec.enabled = True
        lowerFaceSpec.name = self.formatName(name=f'Lower{faceName}')
        lowerFaceSpec.passthrough = not splitFace
        lowerFaceSpec.side = faceSide
        lowerFaceSpec.type = self.Type.HEAD
        lowerFaceSpec.driver.name = self.formatName(name=f'Lower{faceName}', type='control')

        lowerFaceSize = len(self.LowerFaceType)
        lowerFaceSpecs = self.resizeSkeleton(lowerFaceSize, lowerFaceSpec.children, hierarchical=False)

        # Edit uper lip specs
        #
        jawEnabled = bool(self.jawEnabled)
        lipsEnabled = bool(self.lipsEnabled) and jawEnabled
        lipSubdivisions = int(self.lipSubdivisions)

        upperLipsSpec = lowerFaceSpec.children[self.LowerFaceType.UPPER_LIPS]
        upperLipsSpec.enabled = lipsEnabled
        upperLipsSpec.passthrough = True
        upperLipsSpec.name = self.formatName(name='UpperLips')
        upperLipsSpec.side = faceSide
        upperLipsSpec.type = self.Type.OTHER
        upperLipsSpec.otherType = 'UpperLips'
        upperLipsSpec.driver.name = self.formatName(name='UpperLips', type='control')

        upperLipSize = lipSubdivisions + 1 + lipSubdivisions
        upperLipSpecs = self.resizeSkeleton(upperLipSize, upperLipsSpec, hierarchical=False)
        leftUpperLipSpecs, centerUpperLipSpecs, rightUpperLipSpecs = self.unpackSpecs(lipSubdivisions, 1, lipSubdivisions, upperLipSpecs)

        for (lipSide, upperLipSpecs) in ((self.Side.LEFT, leftUpperLipSpecs), (self.Side.CENTER, centerUpperLipSpecs), (self.Side.RIGHT, rightUpperLipSpecs)):

            for (i, upperLipSpec) in enumerate(upperLipSpecs, start=1):

                upperLipSpec.enabled = lipsEnabled
                upperLipSpec.name = self.formatName(side=lipSide, name='UpperLip', index=i)
                upperLipSpec.side = lipSide
                upperLipSpec.type = self.Type.OTHER
                upperLipSpec.otherType = 'UpperLip'
                upperLipSpec.driver.name = self.formatName(side=lipSide, name='UpperLip', index=i, type='control')

        # Edit upper teeth spec
        #
        teethEnabled = bool(self.teethEnabled) and jawEnabled

        upperTeethSpec = lowerFaceSpecs[self.LowerFaceType.UPPER_TEETH]
        upperTeethSpec.enabled = teethEnabled
        upperTeethSpec.name = self.formatName(name='UpperTeeth')
        upperTeethSpec.side = faceSide
        upperTeethSpec.type = self.Type.OTHER
        upperTeethSpec.otherType = 'UpperTeeth'
        upperTeethSpec.driver.name = self.formatName(name='UpperTeeth', type='control')

        # Edit jaw spec
        #
        initialJawMatrix = om.MMatrix(self.__default_lowerface_matrices__[self.LowerFaceType.JAW])
        defaultJawMatrix = initialJawMatrix * defaultParentMatrix

        jawSpec = lowerFaceSpecs[self.LowerFaceType.JAW]
        jawSpec.enabled = jawEnabled
        jawSpec.name = self.formatName(name='Jaw')
        jawSpec.side = faceSide
        jawSpec.type = self.Type.OTHER
        jawSpec.otherType = 'Jaw'
        jawSpec.drawStyle = self.Style.BOX
        jawSpec.defaultMatrix = defaultJawMatrix
        jawSpec.driver.name = self.formatName(name='Jaw', type='control')

        jawSize = len(self.JawType)
        jawSpecs = self.resizeSkeleton(jawSize, jawSpec.children, hierarchical=False)

        # Edit tongue specs
        #
        tongueEnabled = bool(self.tongueCount) and jawEnabled
        tongueSize = floatmath.clamp(self.tongueCount, 1, None)
        isTongueChain = (tongueSize >= 2)
        initialTongueMatrix = om.MMatrix(self.__default_jaw_matrices__[self.JawType.TONGUE])

        tongueBaseSpec = jawSpecs[self.JawType.TONGUE]
        *tongueSpecs, tongueTipSpec = self.resizeSkeleton(tongueSize, tongueBaseSpec, hierarchical=True)

        for (i, tongueSpec) in enumerate((tongueBaseSpec, *tongueSpecs, tongueTipSpec)):

            tongueIndex = (i + 1) if isTongueChain else None
            defaultTongueMatrix = (initialTongueMatrix * defaultParentMatrix) if (i == 0) else transformutils.createTranslateMatrix((1.5, 0.0, 0.0))

            tongueSpec.side = faceSide
            tongueSpec.type = self.Type.OTHER
            tongueSpec.otherType = 'Tongue'
            tongueSpec.defaultMatrix = defaultTongueMatrix

            if i == tongueSize:

                tongueSpec.enabled = tongueEnabled and isTongueChain
                tongueSpec.name = self.formatName(name='TongueTip')
                tongueSpec.driver.name = self.formatName(name='TongueTip', type='target')

            else:

                tongueSpec.enabled = tongueEnabled
                tongueSpec.name = self.formatName(name='Tongue', index=tongueIndex)
                tongueSpec.driver.name = self.formatName(name='Tongue', index=tongueIndex, type='control')

        # Edit corner lip specs
        #
        leftCornerLipSpec, rightCornerLipSpec = jawSpecs[self.JawType.LEFT_LIP_CORNER], jawSpecs[self.JawType.RIGHT_LIP_CORNER]

        for (lipSide, cornerLipSpec) in ((self.Side.LEFT, leftCornerLipSpec), (self.Side.RIGHT, rightCornerLipSpec)):

            cornerLipSpec.enabled = lipsEnabled
            cornerLipSpec.name = self.formatName(side=lipSide, name='CornerLip')
            cornerLipSpec.side = lipSide
            cornerLipSpec.type = self.Type.OTHER
            cornerLipSpec.otherType = 'CornerLip'
            cornerLipSpec.driver.name = self.formatName(side=lipSide, name='CornerLip', type='control')

            upperCornerLipSpec, lowerCornerLipSpec = self.resizeSkeleton(2, cornerLipSpec, hierarchical=False)

            upperCornerLipSpec.enabled = lipsEnabled
            upperCornerLipSpec.name = self.formatName(side=lipSide, name='UpperCornerLip')
            upperCornerLipSpec.side = lipSide
            upperCornerLipSpec.type = self.Type.OTHER
            upperCornerLipSpec.otherType = 'UpperCornerLip'
            upperCornerLipSpec.driver.name = self.formatName(side=lipSide, name='UpperCornerLip', type='control')

            lowerCornerLipSpec.enabled = lipsEnabled
            lowerCornerLipSpec.name = self.formatName(side=lipSide, name='LowerCornerLip')
            lowerCornerLipSpec.side = lipSide
            lowerCornerLipSpec.type = self.Type.OTHER
            lowerCornerLipSpec.otherType = 'LowerCornerLip'
            lowerCornerLipSpec.driver.name = self.formatName(side=lipSide, name='LowerCornerLip', type='control')

        # Edit lower lip specs
        #
        lowerLipsSpec = jawSpecs[self.JawType.LOWER_LIPS]
        lowerLipsSpec.enabled = lipsEnabled
        lowerLipsSpec.passthrough = True
        lowerLipsSpec.name = self.formatName(name='LowerLips')
        lowerLipsSpec.side = faceSide
        lowerLipsSpec.type = self.Type.OTHER
        lowerLipsSpec.otherType = 'LowerLips'
        lowerLipsSpec.driver.name = self.formatName(name='LowerLips', type='control')

        lowerLipSize = lipSubdivisions + 1 + lipSubdivisions
        lowerLipSpecs = self.resizeSkeleton(lowerLipSize, lowerLipsSpec, hierarchical=False)
        leftLowerLipSpecs, centerLowerLipSpecs, rightLowerLipSpecs = self.unpackSpecs(lipSubdivisions, 1, lipSubdivisions, lowerLipSpecs)

        for (lipSide, lowerLipSpecs) in ((self.Side.LEFT, leftLowerLipSpecs), (self.Side.CENTER, centerLowerLipSpecs), (self.Side.RIGHT, rightLowerLipSpecs)):

            for (i, lowerLipSpec) in enumerate(lowerLipSpecs, start=1):

                lowerLipSpec.enabled = lipsEnabled
                lowerLipSpec.name = self.formatName(side=lipSide, name='LowerLip', index=i)
                lowerLipSpec.side = lipSide
                lowerLipSpec.type = self.Type.OTHER
                lowerLipSpec.otherType = 'LowerLip'
                lowerLipSpec.driver.name = self.formatName(side=lipSide, name='LowerLip', index=i, type='control')

        # Edit lower teeth spec
        #
        lowerTeethSpec = jawSpecs[self.JawType.LOWER_TEETH]
        lowerTeethSpec.enabled = teethEnabled
        lowerTeethSpec.name = self.formatName(name='LowerTeeth')
        lowerTeethSpec.side = faceSide
        lowerTeethSpec.type = self.Type.OTHER
        lowerTeethSpec.otherType = 'LowerTeeth'
        lowerTeethSpec.driver.name = self.formatName(name='LowerTeeth', type='control')

        # Edit chin spec
        #
        chinEnabled = bool(self.chinEnabled) and jawEnabled

        chinSpec = jawSpecs[self.JawType.CHIN]
        chinSpec.enabled = chinEnabled
        chinSpec.name = self.formatName(name='Chin')
        chinSpec.side = faceSide
        chinSpec.type = self.Type.OTHER
        chinSpec.otherType = 'Chin'
        chinSpec.driver.name = self.formatName(name='Chin', type='control')

        # Edit throat spec
        #
        throatEnabled = bool(self.throatEnabled) and chinEnabled

        throatSpec = jawSpecs[self.JawType.THROAT]
        throatSpec.enabled = throatEnabled
        throatSpec.name = self.formatName(name='Throat')
        throatSpec.side = faceSide
        throatSpec.type = self.Type.OTHER
        throatSpec.otherType = 'Throat'
        throatSpec.driver.name = self.formatName(name='Throat', type='control')

        # Call parent method
        #
        return super(FaceComponent, self).invalidateSkeleton(skeletonSpecs, **kwargs)

    def createFaceControl(self, name, parent=None, matrix=None):
        """
        Creates a face control with the required space and group nodes.
        # TODO: Add support for mirror matrix!

        :type name: dict
        :type parent: Union[mpynode.MPyNode, None]
        :type matrix: Union[om.MMatrix, None]
        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode, mpynode.MPyNode]
        """

        # Create nodes
        #
        space = self.scene.createNode('transform', name=self.formatName(**name, type='space'), parent=parent)
        group = self.scene.createNode('transform', name=self.formatName(**name, type='transform'), parent=space)
        control = self.scene.createNode('transform', name=self.formatName(**name, type='control'), parent=group)

        control.prepareChannelBoxForAnimation()

        # Check if a transform matrix was supplied
        #
        if isinstance(matrix, om.MMatrix):

            space.setWorldMatrix(matrix, skipScale=True)
            space.freezeTransform()

        elif isinstance(matrix, mpynode.MPyNode):

            space.copyTransform(matrix, skipScale=True)
            space.freezeTransform()

        else:

            pass

        # Connect layered transform
        #
        layeredTransform = self.scene.createNode('layeredTransform', name=self.formatName(**name, type='layeredTransform'))
        layeredTransform.connectPlugs(group['rotateOrder'], 'outputRotateOrder')
        layeredTransform.connectPlugs('outputTranslate', group['translate'])
        layeredTransform.connectPlugs('outputRotate', group['rotate'])
        layeredTransform.connectPlugs('outputScale', group['scale'])

        # Update user properties
        #
        control.userProperties['space'] = space.uuid()
        control.userProperties['group'] = group.uuid()
        control.userProperties['layers'] = layeredTransform.uuid()

        return space, group, control

    def buildForeheadRig(self, foreheadSpec, scale=1.0, parent=None):
        """
        Builds the forehead rig.

        :type foreheadSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if forehead was enabled
        #
        if not foreheadSpec.enabled:

            return

        # Create forehead control
        #
        foreheadExportJoint = foreheadSpec.getNode()
        foreheadExportMatrix = foreheadExportJoint.worldMatrix()

        foreheadSpace, foreheadGroup, foreheadCtrl = self.createFaceControl({'name': 'Forehead'}, matrix=foreheadExportMatrix, parent=parent)
        foreheadCtrl.addPointHelper('sphere', size=(2.0 * scale), side=self.Side.CENTER)
        foreheadCtrl.tagAsController(parent=parent)
        self.publishNode(foreheadCtrl, alias='Forehead')

    def buildBrowRigs(self, centerBrowsSpec, leftBrowsSpec, rightBrowsSpec, scale=1.0, parent=None):
        """
        Builds the brow rigs.

        :type centerBrowsSpec: skeletonspec.SkeletonSpec
        :type leftBrowsSpec: skeletonspec.SkeletonSpec
        :type rightBrowsSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if brows were enabled
        #
        if not (centerBrowsSpec.enabled or leftBrowsSpec.enabled or rightBrowsSpec.enabled):

            return

        # Iterate through brow specs
        #
        for (side, browsSpec) in ((self.Side.CENTER, centerBrowsSpec), (self.Side.LEFT, leftBrowsSpec), (self.Side.RIGHT, rightBrowsSpec)):

            # Check if brow was enabled
            #
            if not browsSpec.enabled:

                continue

            # Calculate brow center
            #
            side = self.Side(side)
            sideChar = side.name[0].upper()
            mirrorSign = -1.0 if (side == self.Side.RIGHT) else 1.0
            mirrorMatrix = self.__default_mirror_matrices__[side]

            browExportJoints = [spec.getNode() for spec in browsSpec.children]
            browExportPoints = [om.MPoint(browExportJoint.translation(space=om.MSpace.kWorld)) for browExportJoint in browExportJoints]

            boundingBox = om.MBoundingBox()

            for (i, browExportPoint) in enumerate(browExportPoints):

                boundingBox.expand(browExportPoint)

            browCenter = om.MPoint(boundingBox.center)
            browVector = (browExportPoints[-1] - browExportPoints[0]).normal() * mirrorSign
            browMatrix = mirrorMatrix * transformutils.createAimMatrix(0, om.MVector.kZaxisVector, 2, browVector, startPoint=browCenter)

            # Create master brow control
            #
            masterBrowSpace, masterBrowGroup, masterBrowCtrl = self.createFaceControl({'side': side, 'name': 'Brow'}, matrix=browMatrix, parent=parent)
            self.publishNode(masterBrowCtrl, alias=f'{sideChar}_Brow')

            # Create brow controls
            #
            numBrowCtrls = len(browExportJoints)
            browCtrls = [None] * numBrowCtrls

            for (i, browExportJoint) in enumerate(browExportJoints):

                index = i + 1
                paddedIndex = str(index).zfill(2)
                browExportMatrix = browExportJoint.worldMatrix()
                browMatrix = mirrorMatrix * browExportMatrix

                browSpace, browGroup, browCtrl = self.createFaceControl({'side': side, 'name': 'Brow', 'index': index}, parent=masterBrowCtrl, matrix=browMatrix)
                browCtrl.addPointHelper('sphere', size=(2.0 * scale), side=side)
                browCtrl.tagAsController(parent=masterBrowCtrl)
                self.publishNode(browCtrl, alias=f'{sideChar}_Brow{paddedIndex}')

                browCtrls[i] = browCtrl

            # Add shape to master brow control
            #
            shape = masterBrowCtrl.addPointHelper('box', side=side)
            shape.resizeToFitContents()
            shape.localScaleY = 0.0

            # Tag master brow control
            #
            masterBrowCtrl.tagAsController(parent=parent, children=browCtrls)

    def buildEyeRigs(self, centerEyesSpec, leftEyesSpec, rightEyesSpec, scale=1.0, diameter=0.5, parent=None):
        """
        Builds the eye rigs.

        :type centerEyesSpec: skeletonspec.SkeletonSpec
        :type leftEyesSpec: skeletonspec.SkeletonSpec
        :type rightEyesSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type diameter: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if eyes were enabled
        #
        if not (centerEyesSpec.enabled or leftEyesSpec.enabled or rightEyesSpec.enabled):

            return

        # Calculate eye look-at origin
        #
        boundingBox = om.MBoundingBox()

        for eyesSpec in (centerEyesSpec, leftEyesSpec, rightEyesSpec):

            for eyeSocketSpec in eyesSpec.children:

                eyeSocketExportJoint = eyeSocketSpec.getNode()
                eyeSocketPoint = om.MPoint(transformutils.breakMatrix(eyeSocketExportJoint.worldMatrix())[3])

                boundingBox.expand(eyeSocketPoint)

        eyesLookAtMatrix = transformutils.createTranslateMatrix(boundingBox.center)

        # Create master eye look-at control
        #
        rootComponent = self.findRootComponent()
        motionCtrl = rootComponent.getPublishedNode('Motion')
        controlsGroup = self.scene(self.controlsGroup)

        eyesLookAtSpaceName = self.formatName(name='Eyes', subname='LookAt', type='space')
        eyesLookAtSpace = self.scene.createNode('transform', name=eyesLookAtSpaceName, parent=controlsGroup)
        eyesLookAtSpace.setWorldMatrix(eyesLookAtMatrix, skipRotate=True, skipScale=True)
        eyesLookAtSpace.freezeTransform()

        eyesLookAtGroupName = self.formatName(name='Eyes', subname='LookAt', type='transform')
        eyesLookAtGroup = self.scene.createNode('transform', name=eyesLookAtGroupName, parent=eyesLookAtSpace)

        eyesLookAtCtrlName = self.formatName(name='Eyes', subname='LookAt', type='control')
        eyesLookAtCtrl = self.scene.createNode('transform', name=eyesLookAtCtrlName, parent=eyesLookAtGroup)
        eyesLookAtCtrl.addDivider('Settings')
        eyesLookAtCtrl.addAttr(longName='lookAtOffset', attributeType='distance', min=0.0, default=diameter, channelBox=True)
        eyesLookAtCtrl.addDivider('Spaces')
        eyesLookAtCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
        eyesLookAtCtrl.prepareChannelBoxForAnimation()
        self.publishNode(eyesLookAtCtrl, alias='Eyes_LookAt')

        eyesLookAtSpaceSwitch = eyesLookAtSpace.addSpaceSwitch([parent, motionCtrl], weighted=True, maintainOffset=True)
        eyesLookAtSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
        eyesLookAtSpaceSwitch.connectPlugs(eyesLookAtCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
        eyesLookAtSpaceSwitch.connectPlugs(eyesLookAtCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

        eyesLookAtOffsetName = self.formatName(name='Eyes', subname='LookAtOffset', type='floatMath')
        eyesLookAtOffset = self.scene.createNode('floatMath', name=eyesLookAtOffsetName)
        eyesLookAtOffset.setAttr('operation', 5)  # Negate
        eyesLookAtOffset.connectPlugs(eyesLookAtCtrl['lookAtOffset'], 'inDistanceA')
        eyesLookAtOffset.connectPlugs('outDistance', eyesLookAtGroup['translateY'])

        # Create eye controls
        #
        for (side, eyesSpec) in ((self.Side.CENTER, centerEyesSpec), (self.Side.LEFT, leftEyesSpec), (self.Side.RIGHT, rightEyesSpec)):

            # Check eyes were enabled
            #
            if not eyesSpec.enabled:

                continue

            # Iterate through eyes
            #
            eyeCount = len(eyesSpec.children)
            sideChar = side.name[0].upper()
            isRightSided = (side == self.Side.RIGHT)
            mirrorSign = -1.0 if isRightSided else 1.0
            mirrorMatrix = self.__default_mirror_matrices__[side]

            for (i, eyeSocketSpec) in enumerate(eyesSpec.children):

                # Create eye socket control
                #
                index = (i + 1) if (eyeCount > 1) else None
                paddedIndex = str(index).zfill(2)

                eyeSocketExportJoint = eyeSocketSpec.getNode()
                eyeSocketExportMatrix = eyeSocketExportJoint.worldMatrix()
                eyeSocketMatrix = mirrorMatrix * eyeSocketExportMatrix

                eyeSocketSpace, eyeSocketGroup, eyeSocketCtrl = self.createFaceControl({'side': side, 'name': 'EyeSocket', 'index': index}, matrix=eyeSocketMatrix, parent=parent)
                eyeSocketCtrl.addPointHelper('cross', size=(4.0 * scale), side=side)
                self.publishNode(eyeSocketCtrl, alias=f'{sideChar}_EyeSocket{paddedIndex}')

                # Create eye control
                #
                upperEyelidSpec, eyeSpec, lowerEyelidSpec = eyeSocketSpec.children

                eyeExportJoint = eyeSpec.getNode()
                eyeExportMatrix = eyeExportJoint.worldMatrix()
                eyeMatrix = mirrorMatrix * eyeExportMatrix

                eyeSpace, eyeGroup, eyeCtrl = self.createFaceControl({'side': side, 'name': 'Eye', 'index': index}, matrix=eyeMatrix, parent=eyeSocketCtrl)
                eyeCtrl.addPointHelper('sphere', size=(4.0 * scale), side=side)
                eyeCtrl.addDivider('Settings')
                eyeCtrl.addAttr(longName='lookAt', attributeType='float', min=0.0, max=1.0, default=1.0, keyable=True)
                eyeCtrl.addAttr(longName='eyelidInfluence', attributeType='float', min=0.0, max=1.0, default=0.1, keyable=True)
                eyeCtrl.addDivider('Spaces')
                eyeCtrl.addAttr(longName='localOrGlobal', attributeType='float', min=0.0, max=1.0, keyable=True)
                eyeCtrl.prepareChannelBoxForAnimation()
                self.publishNode(eyeCtrl, alias=f'{sideChar}_Eye{paddedIndex}')

                eyeLookAtName = self.formatName(side=side, name='Eye', index=index, type='lookAt')
                eyeLookAt = self.scene.createNode('transform', name=eyeLookAtName, parent=eyeSpace)
                eyeGroup.setParent(eyeLookAt)

                eyeSpaceSwitch = eyeSpace.addSpaceSwitch([eyeSocketCtrl, motionCtrl], weighted=True, maintainOffset=True)
                eyeSpaceSwitch.setAttr('target', [{'targetWeight': (1.0, 0.0, 1.0), 'targetReverse': (False, True, False)}, {'targetWeight': (0.0, 0.0, 0.0)}])
                eyeSpaceSwitch.connectPlugs(eyeCtrl['localOrGlobal'], 'target[0].targetRotateWeight')
                eyeSpaceSwitch.connectPlugs(eyeCtrl['localOrGlobal'], 'target[1].targetRotateWeight')

                eyeCtrl.userProperties['spaceSwitch'] = eyeSpaceSwitch.uuid()
                eyeCtrl.userProperties['lookAt'] = eyeLookAt.uuid()

                # Create soft eyelid group
                #
                upperEyelidExportJoint = upperEyelidSpec.getNode()
                upperEyelidExportMatrix = upperEyelidExportJoint.worldMatrix()
                upperEyelidMatrix = mirrorMatrix * upperEyelidExportMatrix

                lowerEyelidExportJoint = lowerEyelidSpec.getNode()
                lowerEyelidExportMatrix = lowerEyelidExportJoint.worldMatrix()
                lowerEyelidMatrix = mirrorMatrix * lowerEyelidExportMatrix

                eyelidSpaceName = self.formatName(side=side, name='Eyelid', index=index, type='space')
                eyelidSpace = self.scene.createNode('transform', name=eyelidSpaceName, parent=eyeSocketCtrl)
                eyelidSpace.setWorldMatrix(eyeMatrix, skipScale=True)
                eyelidSpace.freezeTransform()

                eyelidMultMatrixName = self.formatName(side=side, name='Eyelid', index=index, type='multMatrix')
                eyelidMultMatrix = self.scene.createNode('multMatrix', name=eyelidMultMatrixName)
                eyelidMultMatrix.connectPlugs(eyeCtrl[f'worldMatrix[{eyeCtrl.instanceNumber()}]'], 'matrixIn[0]')
                eyelidMultMatrix.connectPlugs(eyeSpace[f'worldInverseMatrix[{eyeSpace.instanceNumber()}]'], 'matrixIn[1]')

                eyelidDecomposeMatrix = self.scene.createNode('decomposeMatrix')
                eyelidDecomposeMatrix.connectPlugs(eyelidSpace['rotateOrder'], 'inputRotateOrder')
                eyelidDecomposeMatrix.connectPlugs(eyelidMultMatrix['matrixSum'], 'inputMatrix')

                eyelidEnvelopeName = self.formatName(side=side, name='Eyelid', subname='Envelope', index=index, type='vectorMath')
                eyelidEnvelope = self.scene.createNode('vectorMath', name=eyelidEnvelopeName)
                eyelidEnvelope.operation = 19  # Lerp
                eyelidEnvelope.connectPlugs(eyelidDecomposeMatrix['outputRotate'], 'inAngleB')
                eyelidEnvelope.connectPlugs(eyeCtrl['eyelidInfluence'], 'weight')
                eyelidEnvelope.connectPlugs('outAngle', eyelidSpace['rotate'])

                # Create upper eyelid control
                #
                upperEyelidSpace, upperEyelidGroup, upperEyelidCtrl = self.createFaceControl({'side': side, 'name': 'UpperEyelid', 'index': index}, matrix=upperEyelidMatrix, parent=eyelidSpace)
                upperEyelidCtrl.addPointHelper('pyramid', size=(6.0 * scale), localRotate=(0.0, 0.0, 180.0 * isRightSided), localScale=(1.0, 0.25, 0.75), side=side)
                self.publishNode(upperEyelidCtrl, alias=f'{sideChar}_UpperEyelid{paddedIndex}')

                # Create lower eyelid control
                #
                lowerEyelidSpace, lowerEyelidGroup, lowerEyelidCtrl = self.createFaceControl({'side': side, 'name': 'LowerEyelid', 'index': index}, matrix=lowerEyelidMatrix, parent=eyelidSpace)
                lowerEyelidCtrl.addPointHelper('pyramid', size=(6.0 * scale), localRotate=(0.0, 0.0, 180.0 * isRightSided), localScale=(1.0, 0.25, 0.75), side=side)
                self.publishNode(lowerEyelidCtrl, alias=f'{sideChar}_LowerEyelid{paddedIndex}')

                # Tag eye controls
                #
                eyeSocketCtrl.tagAsController(parent=parent, children=[eyeCtrl, upperEyelidCtrl, lowerEyelidCtrl])
                eyeCtrl.tagAsController(parent=eyeSocketCtrl)
                upperEyelidCtrl.tagAsController(parent=eyeSocketCtrl)
                lowerEyelidCtrl.tagAsController(parent=eyeSocketCtrl)

                # Create eye look-at control
                #
                eyeLookAtSpaceName = self.formatName(side=side, name='Eye', subname='LookAt', index=index, type='space')
                eyeLookAtSpace = self.scene.createNode('transform', name=eyeLookAtSpaceName, parent=eyesLookAtCtrl)
                eyeLookAtSpace.setWorldMatrix(eyeMatrix, skipTranslateY=True, skipRotate=True)
                eyeLookAtSpace.freezeTransform()

                eyeLookAtCtrlName = self.formatName(side=side, name='Eye', subname='LookAt', index=index, type='control')
                eyeLookAtCtrl = self.scene.createNode('transform', name=eyeLookAtCtrlName, parent=eyeLookAtSpace)
                eyeLookAtCtrl.addPointHelper('disc', 'centerMarker', size=5.0, localRotate=(0.0, 0.0, 90.0), side=side)
                eyeLookAtCtrl.prepareChannelBoxForAnimation()
                self.publishNode(eyeLookAtCtrl, alias=f'{sideChar}_Eye{paddedIndex}_LookAt')

                eyeLookAtMatrixName = self.formatName(side=side, name='Eye', subname='LookAt', index=index, type='aimMatrix')
                eyeLookAtMatrix = self.scene.createNode('aimMatrix', name=eyeLookAtMatrixName)
                eyeLookAtMatrix.connectPlugs(eyeCtrl['lookAt'], 'envelope')
                eyeLookAtMatrix.connectPlugs(eyeLookAt[f'parentMatrix[{eyeLookAt.instanceNumber()}]'], 'inputMatrix')
                eyeLookAtMatrix.setAttr('primary', {'primaryInputAxis': (1.0 * mirrorSign, 0.0, 0.0), 'primaryMode': 1})  # Aim
                eyeLookAtMatrix.connectPlugs(eyeLookAtCtrl[f'worldMatrix[{eyeLookAtCtrl.instanceNumber()}]'], 'primaryTargetMatrix')
                eyeLookAtMatrix.setAttr('secondary', {'secondaryInputAxis': (0.0, 0.0, 1.0), 'secondaryTargetVector': (0.0, 0.0, 1.0), 'secondaryMode': 2})  # Align
                eyeLookAtMatrix.connectPlugs(eyeLookAtCtrl[f'worldMatrix[{eyeLookAtCtrl.instanceNumber()}]'], 'secondaryTargetMatrix')

                eyeLookAtOffsetMatrix = eyeLookAt.worldMatrix() * eyeLookAtMatrix.getAttr('outputMatrix').inverse()
                eyeLookAtOffsetRotation = transformutils.decomposeTransformMatrix(eyeLookAtOffsetMatrix)[1]

                eyeLookAtComposeMatrixName = self.formatName(side=side, name='Eye', subname='LookAt', index=index, type='composeMatrix')
                eyeLookAtComposeMatrix = self.scene.createNode('composeMatrix', name=eyeLookAtComposeMatrixName)
                eyeLookAtComposeMatrix.setAttr('inputRotate', eyeLookAtOffsetRotation, convertUnits=False)

                eyeLookAtMultMatrixName = self.formatName(side=side, name='Eye', subname='LookAt', type='multMatrix')
                eyeLookAtMultMatrix = self.scene.createNode('multMatrix', name=eyeLookAtMultMatrixName)
                eyeLookAtMultMatrix.connectPlugs(eyeLookAtComposeMatrix['outputMatrix'], 'matrixIn[0]')
                eyeLookAtMultMatrix.connectPlugs(eyeLookAtMatrix['outputMatrix'], 'matrixIn[1]')
                eyeLookAtMultMatrix.connectPlugs(eyeLookAt[f'parentInverseMatrix[{eyeLookAt.instanceNumber()}]'], 'matrixIn[2]')

                eyeLookAtDecomposeMatrixName = self.formatName(side=side, name='Eye', subname='LookAt', index=index, type='decomposeMatrix')
                eyeLookAtDecomposeMatrix = self.scene.createNode('decomposeMatrix', name=eyeLookAtDecomposeMatrixName)
                eyeLookAtDecomposeMatrix.connectPlugs(eyeLookAt['rotateOrder'], 'inputRotateOrder')
                eyeLookAtDecomposeMatrix.connectPlugs(eyeLookAtMultMatrix['matrixSum'], 'inputMatrix')
                eyeLookAtDecomposeMatrix.connectPlugs('outputRotate', eyeLookAt['rotate'])

                eyeLookAtCtrl.userProperties['space'] = eyeLookAtSpace.uuid()
                eyeLookAtCtrl.userProperties['aimMatrix'] = eyeLookAtMatrix.uuid()
                eyeLookAtCtrl.userProperties['decomposeMatrix'] = eyeLookAtDecomposeMatrix.uuid()

                # Create eye look-at curve
                #
                eyeLookAtCurveFromPointName = self.formatName(side=side, name='Eye', subname='LookAt', index=index, type='curveFromPoint')
                eyeLookAtCurveFromPoint = self.scene.createNode('curveFromPoint', name=eyeLookAtCurveFromPointName)
                eyeLookAtCurveFromPoint.degree = 1

                for (j, node) in enumerate([eyeLookAt, eyeLookAtCtrl]):

                    eyeLookAtCurveFromPoint.connectPlugs(node[f'worldMatrix[{node.instanceNumber()}]'], f'inputMatrix[{j}]')

                eyeLookAtCurve = self.scene.createNode('nurbsCurve', parent=eyeLookAtCtrl)
                eyeLookAtCurve.connectPlugs(f'parentInverseMatrix[{eyeLookAtCurve.instanceNumber()}]', eyeLookAtCurveFromPoint['parentInverseMatrix'])
                eyeLookAtCurve.connectPlugs(eyeLookAtCurveFromPoint['outputCurve'], 'create')
                eyeLookAtCurve.useObjectColor = 2
                eyeLookAtCurve.wireColorRGB = eyeLookAtCtrl.shape().wireColorRGB

                eyeLookAtCtrl.renameShapes()

        # Add shape to eyes look-at control and resize to fit children
        #
        eyeLookAtShape = eyesLookAtCtrl.addPointHelper('box', size=1.0, side=self.Side.CENTER)
        eyeLookAtShape.resizeToFitContents()
        eyeLookAtShape.localPositionY = 0.0
        eyeLookAtShape.localScaleY = 0.0

    def buildEarRigs(self, leftEarSpec, rightEarSpec, scale=1.0, parent=None):
        """
        Builds the ear rigs.

        :type leftEarSpec: skeletonspec.SkeletonSpec
        :type rightEarSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if ears were enabled
        #
        if not (leftEarSpec.enabled or rightEarSpec.enabled):

            return

        # Create ear controls
        #
        leftEarSpecs = list(self.flattenSpecs(leftEarSpec))
        rightEarSpecs = list(self.flattenSpecs(rightEarSpec))

        for (side, earSpecs) in ((self.Side.LEFT, leftEarSpecs), (self.Side.RIGHT, rightEarSpecs)):

            # Evaluate ear type
            #
            sideChar = side.name[0].upper()
            mirrorSign = -1.0 if (side == self.Side.RIGHT) else 1.0
            mirrorMatrix = self.__default_mirror_matrices__[side]

            earCount = len(earSpecs)

            if earCount == 1:

                # Create ear control
                #
                earSpec = earSpecs[0]
                earExportJoint = earSpec.getNode()
                earExportMatrix = earExportJoint.worldMatrix()
                earMatrix = mirrorMatrix * earExportMatrix

                earSpace, earGroup, earCtrl = self.createFaceControl({'side': side, 'name': 'Ear'}, matrix=earMatrix, parent=parent)
                earCtrl.addPointHelper('box', size=(6.0 * scale), localPosition=(((6.0 * scale) * 0.25) * mirrorSign, 0.0, 0.0), localScale=(0.5, 0.25, 1.0), side=side)
                earCtrl.tagAsController(parent=parent)
                self.publishNode(earCtrl, alias=f'{sideChar}_Ear01')

            else:

                # Create ear controls
                #
                lastIndex = earCount - 1
                numEarCtrls = lastIndex - 1

                earCtrls = [None] * numEarCtrls

                for (i, earSpec) in enumerate(earSpecs):

                    index = i + 1
                    paddedIndex = str(index).zfill(2)
                    previousEarCtrl = earCtrls[i - 1] if (i > 0) else parent

                    earExportJoint = earSpec.getNode()
                    earExportMatrix = earExportJoint.worldMatrix()
                    earMatrix = mirrorMatrix * earExportMatrix

                    if i == lastIndex:

                        earTarget = self.scene.createNode('transform', name=earSpec.driver, parent=parent)
                        earTarget.displayLocalAxis = True
                        earTarget.visibility = False
                        earTarget.setWorldMatrix(earMatrix, skipScale=True)
                        earTarget.freezeTransform()

                    else:

                        earSpace, earGroup, earCtrl = self.createFaceControl({'side': side, 'name': 'Ear', 'index': index}, matrix=earMatrix, parent=previousEarCtrl)
                        earCtrl.addPointHelper('box', size=6.0, localScale=(1.0, 0.25, 1.0), side=side)
                        earCtrl.tagAsController(parent=parent)
                        self.publishNode(earCtrl, alias=f'{sideChar}_Ear{paddedIndex}')

                        earCtrl.userProperties['space'] = earSpace.uuid()
                        earCtrl.userProperties['transform'] = earGroup.uuid()

                        earCtrls[i] = earCtrl

                # Resize ear controls
                #
                for earCtrl in earCtrls:

                    earCtrl.shape().reorientAndScaleToFit()

    def buildNoseRig(self, noseSpec, scale=1.0, parent=None):
        """
        Builds the nose rig.

        :type noseSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if nose was enabled
        #
        if not noseSpec.enabled:

            return

        # Create nose control
        #
        noseExportJoint = noseSpec.getNode()
        noseExportMatrix = noseExportJoint.worldMatrix()

        noseSpace, noseGroup, noseCtrl = self.createFaceControl({'name': 'Nose'}, parent=parent, matrix=noseExportMatrix)
        noseCtrl.addPointHelper('pyramid', size=(5.0 * scale), localRotate=(0.0, 0.0, 180.0), side=self.Side.CENTER)
        self.publishNode(noseCtrl, alias='Nose')

        # Create nostril controls
        #
        noseTipSpec, leftNostrilSpec, rightNostrilSpec = noseSpec.children
        nostrilCtrls = []
        
        for (side, nostrilSpec) in ((self.Side.LEFT, leftNostrilSpec), (self.Side.RIGHT, rightNostrilSpec)):

            sideChar = side.name[0].upper()
            mirrorMatrix = self.__default_mirror_matrices__[side]

            nostrilExportJoint = nostrilSpec.getNode()
            nostrilExportMatrix = nostrilExportJoint.worldMatrix()
            nostrilMatrix = mirrorMatrix * nostrilExportMatrix

            nostrilSpace, nostrilGroup, nostrilCtrl = self.createFaceControl({'side': side, 'name': 'Nostril'}, parent=noseCtrl, matrix=nostrilMatrix)
            nostrilCtrl.addPointHelper('sphere', size=(1.5 * scale), side=side)
            nostrilCtrl.tagAsController(parent=noseCtrl)
            self.publishNode(nostrilCtrl, alias=f'{sideChar}_Nostril')

            nostrilCtrls.append(nostrilCtrl)

        # Create nose tip control
        #
        noseTipExportJoint = noseTipSpec.getNode()
        noseTipExportMatrix = noseTipExportJoint.worldMatrix()

        noseTipSpace, noseTipGroup, noseTipCtrl = self.createFaceControl({'name': 'NoseTip'}, parent=noseCtrl, matrix=noseTipExportMatrix)
        noseTipCtrl.addPointHelper('disc', size=(1.0 * scale), localPosition=(1.0 * scale, 0.0, 0.0), side=self.Side.CENTER)
        noseTipCtrl.tagAsController(parent=noseCtrl)
        self.publishNode(noseTipCtrl, alias='NoseTip')

        # Tag nose control
        #
        noseCtrl.tagAsController(parent=parent, children=[*nostrilCtrls, noseTipCtrl])

    def buildCheekRigs(self, leftCheeksSpec, rightCheeksSpec, scale=1.0, parent=None):
        """
        Builds the cheek rigs.

        :type leftCheeksSpec: skeletonspec.SkeletonSpec
        :type rightCheeksSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if cheeks were enabled
        #
        if not (leftCheeksSpec.enabled or rightCheeksSpec.enabled):
            
            return

        # Iterate through brow groups
        #
        referenceNode = self.skeletonReference()

        for (side, cheeksSpec) in ((self.Side.LEFT, leftCheeksSpec), (self.Side.RIGHT, rightCheeksSpec)):

            # Create cheek controls
            #
            sideChar = side.name[0].upper()
            mirrorMatrix = self.__default_mirror_matrices__[side]

            numCheekCtrls = len(cheeksSpec.children)
            cheekCtrls = [None] * numCheekCtrls

            for (i, cheekSpec) in enumerate(cheeksSpec.children):
                
                index = i + 1
                paddedIndex = str(index).zfill(2)

                cheekExportJoint = cheekSpec.getNode()
                cheekExportMatrix = cheekExportJoint.worldMatrix()
                cheekMatrix = mirrorMatrix * cheekExportMatrix

                cheekSpaceName, cheekGroup, cheekCtrl = self.createFaceControl({'side': side, 'name': 'Cheek', 'index': index}, matrix=cheekMatrix, parent=parent)
                cheekCtrl.addPointHelper('sphere', size=(2.0 * scale), side=side)
                cheekCtrl.tagAsController(parent=parent)
                self.publishNode(cheekCtrl, alias=f'{sideChar}_Cheek{paddedIndex}')

                cheekCtrls[i] = cheekCtrl

    def buildJawRig(self, jawSpec, scale=1.0, parent=None):
        """
        Builds the jaw rig.

        :type jawSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if jaw was enabled
        #
        if not jawSpec.enabled:

            return

        # Create jaw control
        #
        jawExportJoint = jawSpec.getNode()
        jawExportMatrix = jawExportJoint.worldMatrix()

        jawSpace, jawGroup, jawCtrl = self.createFaceControl({'name': 'Jaw'}, matrix=jawExportMatrix, parent=parent)
        jawCtrl.addShape('WedgeCurve', size=(2.0 * scale), localPosition=(-10.0 * scale, 7.5 * scale, 0.0), localRotate=(0.0, 0.0, 90.0), side=self.Side.CENTER)
        self.publishNode(jawCtrl, alias='Jaw')

        jawCtrl.userProperties['space'] = jawSpace.uuid()
        jawCtrl.userProperties['transform'] = jawGroup.uuid()

        # Check if teeth were enabled
        #
        lowerTeethSpec = jawSpec.children[self.JawType.LOWER_TEETH]

        if lowerTeethSpec.enabled:

            lowerTeethExportJoint = lowerTeethSpec.getNode()
            lowerTeethExportMatrix = lowerTeethExportJoint.worldMatrix()

            lowerTeethSpace, lowerTeethGroup, lowerTeethCtrl = self.createFaceControl({'name': 'LowerTeeth'}, matrix=lowerTeethExportMatrix, parent=jawCtrl)
            lowerTeethCtrl.addPointHelper('box', size=(2.0 * scale), localScale=(0.5, 1.0, 2.0), side=self.Side.CENTER)
            lowerTeethCtrl.tagAsController(parent=jawCtrl)
            self.publishNode(lowerTeethCtrl, alias='LowerTeeth')

        # Check if the tongue was enabled
        #
        tongueBaseSpec = jawSpec.children[self.JawType.TONGUE]

        if tongueBaseSpec.enabled:

            *tongueSpecs, tongueTipSpec = list(self.flattenSpecs(tongueBaseSpec))
            tongueCount = len(tongueSpecs)

            tongueCtrls = [None] * tongueCount

            for (i, spec) in enumerate(tongueSpecs):

                index = i + 1
                previousTongueCtrl = jawCtrl if (i == 0) else tongueCtrls[i - 1]

                tongueExportJoint = spec.getNode()
                tongueExportMatrix = tongueExportJoint.worldMatrix()

                tongueSpace, tongueGroup, tongueCtrl = self.createFaceControl({'name': 'Tongue', 'index': index}, matrix=tongueExportMatrix, parent=previousTongueCtrl)
                tongueCtrl.addPointHelper('box', size=(2.0 * scale), localScale=(1.0, 0.5, 2.0), side=self.Side.CENTER)
                tongueCtrl.tagAsController(parent=jawCtrl)
                self.publishNode(tongueCtrl, alias=f'Tongue{str(index).zfill(2)}')

                tongueCtrls[i] = tongueCtrl

            tongueTipExportJoint = tongueTipSpec.getNode()
            tongueTipExportMatrix = tongueTipExportJoint.worldMatrix()

            tongueTipTargetName = self.formatName(name='TongueTip', type='target')
            tongueTipTarget = self.scene.createNode('transform', name=tongueTipTargetName, parent=tongueCtrls[-1])
            tongueTipTarget.setWorldMatrix(tongueTipExportMatrix, skipScale=True)
            tongueTipTarget.displayLocalAxis = True
            tongueTipTarget.visibility = False
            tongueTipTarget.freezeTransform()
            tongueTipTarget.lock()

        # Check if chin was enabled
        #
        chinSpec = jawSpec.children[self.JawType.CHIN]

        if chinSpec.enabled:

            chinExportJoint = chinSpec.getNode()
            chinExportMatrix = chinExportJoint.worldMatrix()

            chinSpace, chinGroup, chinCtrl = self.createFaceControl({'name': 'Chin'}, matrix=chinExportMatrix, parent=jawCtrl)
            chinCtrl.addPointHelper('disc', size=(2.0 * scale), localPosition=(0.0, 4.0 * scale, 0.0), localRotate=(0.0, 0.0, 90.0), side=self.Side.CENTER)
            self.publishNode(chinCtrl, alias='Chin')

            chinCtrl.tagAsController(parent=jawCtrl)

        # Check if throat was enabled
        #
        throatSpec = jawSpec.children[self.JawType.THROAT]

        if throatSpec.enabled:

            # Create throat control
            #
            throatExportJoint = throatSpec.getNode()
            throatExportMatrix = throatExportJoint.worldMatrix()

            throatSpace, throatGroup, throatCtrl = self.createFaceControl({'name': 'Throat'}, matrix=throatExportMatrix, parent=jawCtrl)
            throatCtrl.addShape('CrownCurve', side=self.Side.CENTER)
            throatCtrl.tagAsController(parent=jawCtrl)
            self.publishNode(throatCtrl, alias='Throat')

            # Constraint throat control
            #
            chinCtrl = self.getPublishedNode('Chin')

            throatSpace.addConstraint('transformConstraint', [parent, chinCtrl], maintainOffset=True, skipRotate=True)
            throatSpace.addConstraint('aimConstraint', [chinCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=chinCtrl, maintainOffset=True)

        # Tag controls
        #
        jawCtrl.tagAsController(parent=parent)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        faceSpec, = self.skeleton()
        upperFaceSpec = faceSpec.children[self.FaceType.UPPER]
        midFaceSpec = faceSpec.children[self.FaceType.MID]
        lowerFaceSpec = faceSpec.children[self.FaceType.LOWER]

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        controlRig = self.findControlRig()
        rigWidth, rigHeight = controlRig.getRigWidthAndHeight()
        rigScale = controlRig.getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create face control
        #
        faceEnabled = not faceSpec.passthrough
        faceExportJoint = faceSpec.getNode() if faceEnabled else None
        faceExportMatrix = faceExportJoint.worldMatrix() if (faceExportJoint is not None) else parentExportJoint.worldMatrix()

        faceSpaceName = self.formatName(name='Face', type='space')
        faceSpace = self.scene.createNode('transform', name=faceSpaceName, parent=controlsGroup)
        faceSpace.setWorldMatrix(faceExportMatrix, skipScale=True)
        faceSpace.freezeTransform()
        faceSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        faceCtrlName = self.formatName(name='Face', type='control')
        faceCtrl = self.scene.createNode('transform', name=faceCtrlName, parent=faceSpace)
        faceCtrl.addPointHelper('tearDrop', size=(5.0 * rigScale), localPosition=(25.0 * rigScale, 0.0, 0.0), localRotate=(-90.0, 0.0, 90.0), side=self.Side.CENTER, lineWidth=4)
        faceCtrl.hideAttr('translate', 'rotateOrder', 'rotate', 'scale', lock=True)
        faceCtrl.prepareChannelBoxForAnimation()
        self.publishNode(faceCtrl, alias='Face')

        # Create face subcontrols
        #
        splitFace = not (upperFaceSpec.passthrough and midFaceSpec.passthrough and lowerFaceSpec.passthrough)
        upperFaceCtrl, midFaceCtrl, lowerFaceCtrl = None, None, None

        if splitFace:

            # Create upper-face control
            #
            upperFaceExportJoint = upperFaceSpec.getNode()
            upperFaceExportMatrix = upperFaceExportJoint.worldMatrix()

            upperFaceSpace, upperFaceGroup, upperFaceCtrl = self.createFaceControl({'name': 'UpperFace'}, parent=faceCtrl, matrix=upperFaceExportMatrix)
            upperFaceCtrl.addPointHelper('disc', size=(50.0 * rigScale), localPosition=(5.0, 0.0, 0.0), side=self.Side.CENTER)
            upperFaceCtrl.prepareChannelBoxForAnimation()
            self.publishNode(upperFaceCtrl, alias='UpperFace')

            # Create lower-face control
            #
            lowerFaceExportJoint = lowerFaceSpec.getNode()
            lowerFaceExportMatrix = lowerFaceExportJoint.worldMatrix()

            lowerFaceSpace, lowerFaceGroup, lowerFaceCtrl = self.createFaceControl({'name': 'LowerFace'}, parent=faceCtrl, matrix=lowerFaceExportMatrix)
            lowerFaceCtrl.addPointHelper('disc', size=(50.0 * rigScale), localPosition=(-5.0, 0.0, 0.0), side=self.Side.CENTER)
            lowerFaceCtrl.prepareChannelBoxForAnimation()
            self.publishNode(lowerFaceCtrl, alias='LowerFace')

            # Create mid-face control
            #
            midFaceExportJoint = midFaceSpec.getNode()
            midFaceExportMatrix = midFaceExportJoint.worldMatrix()

            midFaceSpace, midFaceGroup, midFaceCtrl = self.createFaceControl({'name': 'MidFace'}, parent=faceCtrl, matrix=midFaceExportMatrix)
            midFaceCtrl.addPointHelper('disc', size=(50.0 * rigScale), localPosition=(0.0, 0.0, 0.0), side=self.Side.CENTER)
            midFaceCtrl.addDivider('Settings')
            midFaceCtrl.addAttr(longName='bias', attributeType='float', min=0.0, max=1.0, default=0.5, keyable=True)
            midFaceCtrl.prepareChannelBoxForAnimation()
            self.publishNode(midFaceCtrl, alias='MidFace')

            spaceSwitch = midFaceSpace.addSpaceSwitch([lowerFaceCtrl, upperFaceCtrl], weighted=True, maintainOffset=True)
            spaceSwitch.setAttr('target[0].targetReverse', (True, True, True))
            spaceSwitch.connectPlugs(midFaceCtrl['bias'], 'target[0].targetWeight')
            spaceSwitch.connectPlugs(midFaceCtrl['bias'], 'target[1].targetWeight')

            midFaceCtrl.userProperties['spaceSwitch'] = spaceSwitch.uuid()

        # Create upper-face components
        #
        upperFaceParent = upperFaceCtrl if splitFace else faceCtrl

        self.buildForeheadRig(
            upperFaceSpec.children[self.UpperFaceType.FOREHEAD],
            scale=rigScale, parent=upperFaceParent
        )

        self.buildBrowRigs(
            upperFaceSpec.children[self.UpperFaceType.CENTER_BROW],
            upperFaceSpec.children[self.UpperFaceType.LEFT_BROW],
            upperFaceSpec.children[self.UpperFaceType.RIGHT_BROW],
            scale=rigScale, parent=upperFaceParent
        )

        self.buildEyeRigs(
            upperFaceSpec.children[self.UpperFaceType.CENTER_EYES],
            upperFaceSpec.children[self.UpperFaceType.LEFT_EYES],
            upperFaceSpec.children[self.UpperFaceType.RIGHT_EYES],
            scale=rigScale, diameter=rigWidth, parent=upperFaceParent
        )

        # Create mid-face components
        #
        midFaceParent = midFaceCtrl if splitFace else faceCtrl

        self.buildEarRigs(
            midFaceSpec.children[self.MidFaceType.LEFT_EAR],
            midFaceSpec.children[self.MidFaceType.RIGHT_EAR],
            scale=rigScale, parent=midFaceParent
        )

        self.buildNoseRig(
            midFaceSpec.children[self.MidFaceType.NOSE],
            scale=rigScale, parent=midFaceParent
        )

        self.buildCheekRigs(
            midFaceSpec.children[self.MidFaceType.LEFT_CHEEK],
            midFaceSpec.children[self.MidFaceType.RIGHT_CHEEK],
            scale=rigScale, parent=midFaceParent
        )

        # Create lower-face components
        #
        lowerFaceParent = lowerFaceCtrl if splitFace else faceCtrl

        self.buildJawRig(
            lowerFaceSpec.children[self.LowerFaceType.JAW],
            scale=rigScale, parent=lowerFaceParent
        )
    # endregion
