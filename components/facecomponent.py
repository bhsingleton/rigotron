from maya.api import OpenMaya as om
from mpy import mpynode, mpyattribute
from enum import IntEnum
from itertools import chain
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
    Enum class of all upper-face components.
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
    Enum class of all mid-face components.
    """

    LEFT_EAR = 0
    RIGHT_EAR = 1
    NOSE = 2
    LEFT_CHEEK = 3
    RIGHT_CHEEK = 4


class LowerFaceType(IntEnum):
    """
    Enum class of all lower-face components.
    """

    UPPER_LIPS = 0
    UPPER_TEETH = 1
    JAW = 2
    THROAT = 3


class JawType(IntEnum):
    """
    Enum class of all jaw subcomponents.
    """

    TONGUE = 0
    LOWER_TEETH = 1
    LOWER_LIPS = 2
    CHIN = 3


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
    __default_component_matrices__ = {  # TODO: Populate default component matrices!
        FaceType.UPPER: {
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
        },
        FaceType.MID: {
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
        },
        FaceType.LOWER: {
            LowerFaceType.JAW: om.MMatrix(

            ),

        }
    }
    # endregion

    # region Attributes
    faceEnabled = mpyattribute.MPyAttribute('faceEnabled', attributeType='bool', default=False)
    splitFace = mpyattribute.MPyAttribute('splitFace', attributeType='bool', default=False)

    foreheadEnabled = mpyattribute.MPyAttribute('foreheadEnabled', attributeType='bool', default=True)

    centerBrowCount = mpyattribute.MPyAttribute('centerBrowCount', attributeType='int', min=0, max=5, default=1)
    leftBrowCount = mpyattribute.MPyAttribute('leftBrowCount', attributeType='int', min=0, max=5, default=2)
    rightBrowCount = mpyattribute.MPyAttribute('rightBrowCount', attributeType='int', min=0, max=5, default=2)
    browSettings = mpyattribute.MPyAttribute('browSettings', attributeType='compound', children=('centerBrowCount', 'leftBrowCount', 'rightBrowCount'))

    centerEyeCount = mpyattribute.MPyAttribute('centerEyeCount', attributeType='int', min=0, max=3, default=1)
    leftEyeCount = mpyattribute.MPyAttribute('leftEyeCount', attributeType='int', min=0, max=3, default=1)
    rightEyeCount = mpyattribute.MPyAttribute('rightEyeCount', attributeType='int', min=0, max=3, default=1)
    eyeSettings = mpyattribute.MPyAttribute('eyeSettings', attributeType='compound', children=('centerEyeCount', 'leftEyeCount', 'rightEyeCount', 'eyelidsEnabled'))

    leftCheekCount = mpyattribute.MPyAttribute('leftCheekCount', attributeType='int', min=0, max=5, default=2)
    rightCheekCount = mpyattribute.MPyAttribute('rightCheekCount', attributeType='int', min=0, max=5, default=2)
    cheekSettings = mpyattribute.MPyAttribute('cheekSettings', attributeType='compound', children=('leftCheekCount', 'rightCheekCount'))

    noseEnabled = mpyattribute.MPyAttribute('noseEnabled', attributeType='bool', default=True)
    nostrilsEnabled = mpyattribute.MPyAttribute('nostrilsEnabled', attributeType='bool', default=True)
    noseTipEnabled = mpyattribute.MPyAttribute('noseTipEnabled', attributeType='bool', default=True)
    noseSettings = mpyattribute.MPyAttribute('noseSettings', attributeType='compound', children=('noseEnabled', 'nostrilsEnabled', 'noseTipEnabled'))

    leftEarCount = mpyattribute.MPyAttribute('leftEarCount', attributeType='int', min=0, max=5, default=1)
    rightEarCount = mpyattribute.MPyAttribute('rightEarCount', attributeType='int', min=0, max=5, default=1)
    earSettings = mpyattribute.MPyAttribute('earSettings', attributeType='compound', children=('leftEarCount', 'rightEarCount'))

    jawEnabled = mpyattribute.MPyAttribute('jawEnabled', attributeType='bool', default=True)
    teethEnabled = mpyattribute.MPyAttribute('teethEnabled', attributeType='bool', default=False)
    tongueCount = mpyattribute.MPyAttribute('tongueCount', attributeType='int', min=0, max=9, default=3)
    chinEnabled = mpyattribute.MPyAttribute('chinEnabled', attributeType='bool', default=True)
    throatEnabled = mpyattribute.MPyAttribute('throatEnabled', attributeType='bool', default=True)
    jawSettings = mpyattribute.MPyAttribute('jawSettings', attributeType='compound', children=('jawEnabled', 'teethEnabled', 'tongueCount', 'throatEnabled', 'chinEnabled'))

    @faceEnabled.changed
    def faceEnabled(self, faceEnabled):
        """
        Changed method that notifies of any state changes.

        :type faceEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()

    @splitFace.changed
    def splitFace(self, splitFace):
        """
        Changed method that notifies of any state changes.

        :type splitFace: bool
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

    @throatEnabled.changed
    def throatEnabled(self, throatEnabled):
        """
        Changed method that notifies of any state changes.

        :type throatEnabled: bool
        :rtype: None
        """

        self.markSkeletonDirty()
    # endregion

    # region Methods
    def invalidateSkeleton(self, skeletonSpecs, **kwargs):
        """
        Rebuilds the internal skeleton specs for this component.
        TODO: Copy over lip spec initialization code from notepad++

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
        splitFace = bool(self.splitFace)

        upperFaceSpec.name = self.formatName(name=f'Upper{faceName}')
        upperFaceSpec.passthrough = not splitFace
        upperFaceSpec.side = faceSide
        upperFaceSpec.type = self.Type.HEAD
        upperFaceSpec.driver.name = self.formatName(name=f'Upper{faceName}', type='control')

        upperFaceSize = len(self.UpperFaceType)
        upperFaceSpecs = self.resizeSkeleton(upperFaceSize, upperFaceSpec.children, hierarchical=False)

        # Edit forehead spec
        #
        initialForeheadMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.UPPER][self.UpperFaceType.FOREHEAD])
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
            initialBrowMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.UPPER][browType])

            browSpec.enabled = browEnabled
            browSpec.passthrough = True
            browSpec.name = self.formatName(side=browSide, name='Brow')
            browSpec.side = browSide
            browSpec.type = self.Type.OTHER
            browSpec.otherType = 'Brow'
            browSpec.driver.name = self.formatName(side=browSide, name='Brow', type='control')

            browSpecs = self.resizeSkeletonSpecs(browSize, browSpec)

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
            initialEyeMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.UPPER][eyeType])

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

                upperEyelidSpec, eyeSpec, lowerEyelidSpec = self.resizeSkeletonSpecs(3, eyeSocketSpec)

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
            initialCheekMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.MID][cheekType])

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

        for (earSide, earSize, topLevelEarSpec) in ((self.Side.LEFT, leftEarCount, leftEarSpec), (self.Side.RIGHT, rightEarCount, rightEarSpec)):

            earEnabled = (earSize > 0)
            earType = self.MidFaceType[f'{earSide.name}_EAR']
            initialEarMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.MID][earType])

            earSpecs = self.resizeSkeleton(earSize, topLevelEarSpec, hierarchical=True)
            lastIndex = earSize - 1

            for (i, earSpec) in enumerate((topLevelEarSpec, *earSpecs)):

                earIndex = (i + 1) if (earSize >= 2) else None
                defaultEarMatrix = (initialEarMatrix * defaultParentMatrix) if (i == 0) else transformutils.createTranslateMatrix((5.0, 0.0, 0.0))

                earSpec.enabled = earEnabled
                earSpec.side = earSide
                earSpec.type = self.Type.OTHER
                earSpec.otherType = 'Ear'
                earSpec.defaultMatrix = defaultEarMatrix

                if i == lastIndex:

                    earSpec.name = self.formatName(side=earSide, name='EarTip')
                    earSpec.driver.name = self.formatName(side=earSide, name='EarTip', type='target')

                else:

                    earSpec.name = self.formatName(side=earSide, name='Ear', index=earIndex)
                    earSpec.driver.name = self.formatName(side=earSide, name='Ear', index=earIndex, type='control')

        # Edit nose spec
        #
        noseEnabled = bool(self.noseEnabled)

        noseSpec = midFaceSpecs[self.MidFaceType.NOSE]
        noseSpec.enabled = noseEnabled
        noseSpec.name = self.formatName(name='Nose')
        noseSpec.side = faceSide
        noseSpec.type = self.Type.OTHER
        noseSpec.otherType = 'Nose'
        noseSpec.drawStyle = self.Style.BOX
        noseSpec.defaultMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.MID][self.MidFaceType.NOSE][self.Side.CENTER])
        noseSpec.driver.name = self.formatName(name='Nose', type='control')

        noseTipSpec, leftNostrilSpec, rightNostrilSpec = self.resizeSkeleton(3, noseSpec, hierarchical=False)

        for (nostrilSide, nostrilSpec) in ((self.Side.NONE, noseTipSpec), (self.Side.LEFT, leftNostrilSpec), (self.Side.RIGHT, rightNostrilSpec)):

            nostrilName = 'NoseTip' if (nostrilSide == Side.NONE) else 'Nostril'

            nostrilSpec.enabled = noseEnabled
            nostrilSpec.name = self.formatName(side=nostrilSide, name=nostrilName)
            nostrilSpec.side = nostrilSide
            nostrilSpec.type = self.Type.OTHER
            nostrilSpec.otherType = nostrilName
            nostrilSpec.defaultMatrix = om.MMatrix(self.__default_component_matrices__[self.FaceType.MID][self.MidFaceType.NOSE][nostrilSide])
            nostrilSpec.driver.name = self.formatName(side=nostrilSide, name=nostrilName, type='control')
        
        # Resize lower-face specs
        #
        lowerFaceSpec.name = self.formatName(name=f'Lower{faceName}')
        lowerFaceSpec.passthrough = not splitFace
        lowerFaceSpec.side = faceSide
        lowerFaceSpec.type = self.Type.HEAD
        lowerFaceSpec.driver.name = self.formatName(name=f'Lower{faceName}', type='control')

        lowerFaceSize = len(self.LowerFaceType)
        lowerFaceSpecs = self.resizeSkeleton(lowerFaceSize, lowerFaceSpec.children, hierarchical=False)

        # Edit upper teeth spec
        #
        jawEnabled = bool(self.jawEnabled)
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
        jawSpec = lowerFaceSpecs[self.LowerFaceType.JAW]
        jawSpec.enabled = jawEnabled
        jawSpec.name = self.formatName(name='Jaw')
        jawSpec.side = faceSide
        jawSpec.type = self.Type.OTHER
        jawSpec.otherType = 'Jaw'
        jawSpec.drawStyle = self.Style.BOX
        jawSpec.driver.name = self.formatName(name='Jaw', type='control')

        jawSize = len(self.JawType)
        jawSpecs = self.resizeSkeleton(jawSize, jawSpec.children, hierarchical=False)

        # Edit tongue specs
        #
        tongueCount = int(self.tongueCount)
        tongueEnabled = (tongueCount > 0) and jawEnabled

        tongueBaseSpec = jawSpecs[self.JawType.TONGUE]
        *tongueSpecs, tongueTipSpec = self.resizeSkeletonSpecs(tongueCount, tongueBaseSpec)

        for (i, tongueSpec) in enumerate(tongueSpecs, start=1):

            tongueSpec.enabled = tongueEnabled
            tongueSpec.name = self.formatName(name='Tongue', index=i)
            tongueSpec.side = faceSide
            tongueSpec.type = self.Type.OTHER
            tongueSpec.otherType = 'Tongue'
            tongueSpec.driver.name = self.formatName(name='Tongue', index=i, type='control')

        tongueTipSpec.enabled = False
        tongueTipSpec.name = self.formatName(name='TongueTip')
        tongueTipSpec.side = faceSide
        tongueTipSpec.type = self.Type.OTHER
        tongueTipSpec.otherType = 'Tongue'
        tongueTipSpec.driver.name = self.formatName(name='TongueTip', type='target')

        # Edit lower teeth spec
        #
        teethEnabled = bool(self.teethEnabled) and jawEnabled

        lowerTeethSpec = jawSpecs[self.LowerFaceType.LOWER_TEETH]
        lowerTeethSpec.enabled = teethEnabled
        lowerTeethSpec.name = self.formatName(name='LowerTeeth')
        lowerTeethSpec.side = faceSide
        lowerTeethSpec.type = self.Type.OTHER
        lowerTeethSpec.otherType = 'LowerTeeth'
        lowerTeethSpec.driver.name = self.formatName(name='LowerTeeth', type='control')

        # Edit chin spec
        #
        chinEnabled = bool(self.chinEnabled) and jawEnabled

        chinSpec = lowerFaceSpecs[self.LowerFaceType.CHIN]
        chinSpec.enabled = chinEnabled
        chinSpec.name = self.formatName(name='Chin')
        chinSpec.side = faceSide
        chinSpec.type = self.Type.OTHER
        chinSpec.otherType = 'Chin'
        chinSpec.driver.name = self.formatName(name='Chin', type='control')

        # Edit throat spec
        #
        throatEnabled = bool(self.throatEnabled) and chinEnabled

        throatSpec = lowerFaceSpecs[self.LowerFaceType.THROAT]
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
        layeredTransform.connectPlugs(group['rotateOrder'], 'inputRotateOrder')
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
        referenceNode = self.skeletonReference()
        foreheadExportJoint = foreheadSpec.getNode(referenceNode=referenceNode)
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
        referenceNode = self.skeletonReference()

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

            browExportJoints = [spec.getNode(referenceNode=referenceNode) for spec in browsSpec.children]
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

    def buildEyeRigs(self, centerEyesSpec, leftEyesSpec, rightEyesSpec, scale=1.0, radius=0.5, parent=None):
        """
        Builds the eye rigs.

        :type centerEyesSpec: skeletonspec.SkeletonSpec
        :type leftEyesSpec: skeletonspec.SkeletonSpec
        :type rightEyesSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :type radius: float
        :type parent: mpynode.MPyNode
        :rtype: None
        """

        # Check if eyes were enabled
        #
        if not (centerEyesSpec.enabled or leftEyesSpec.enabled or rightEyesSpec.enabled):

            return

        # Calculate eye look-at origin
        #
        referenceNode = self.skeletonReference()
        boundingBox = om.MBoundingBox()

        for eyesSpec in (centerEyesSpec, leftEyesSpec, rightEyesSpec):

            for eyeSocketSpec in eyesSpec.children:

                eyeSocketExportJoint = eyeSocketSpec.getNode(referenceNode=referenceNode)
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
        eyesLookAtCtrl.addAttr(longName='lookAtOffset', attributeType='distance', min=0.0, default=radius, channelBox=True)
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

                eyeSocketExportJoint = eyeSocketSpec.getNode(referenceNode=referenceNode)
                eyeSocketExportMatrix = eyeSocketExportJoint.worldMatrix()
                eyeSocketMatrix = mirrorMatrix * eyeSocketExportMatrix

                eyeSocketSpace, eyeSocketGroup, eyeSocketCtrl = self.createFaceControl({'side': side, 'name': 'EyeSocket', 'index': index}, matrix=eyeSocketMatrix, parent=parent)
                eyeSocketCtrl.addPointHelper('cross', size=(4.0 * scale), side=side)
                self.publishNode(eyeSocketCtrl, alias=f'{sideChar}_EyeSocket{paddedIndex}')

                # Create eye control
                #
                upperEyelidSpec, eyeSpec, lowerEyelidSpec = eyeSocketSpec.children

                eyeExportJoint = eyeSpec.getNode(referenceNode=referenceNode)
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
                upperEyelidExportJoint = upperEyelidSpec.getNode(referenceNode=referenceNode)
                upperEyelidExportMatrix = upperEyelidExportJoint.worldMatrix()
                upperEyelidMatrix = mirrorMatrix * upperEyelidExportMatrix

                lowerEyelidExportJoint = self.scene(lowerEyelidSpec.uuid)
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
        referenceNode = self.skeletonReference()
        leftEarSpecs = self.flattenSpecs(leftEarSpec)
        rightEarSpecs = self.flattenSpecs(rightEarSpec)

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
                earExportJoint = earSpec.getNode(referenceNode=referenceNode)
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

                    earExportJoint = earSpec.getNode(referenceNode=referenceNode)
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
        referenceNode = self.skeletonReference()
        noseExportJoint = noseSpec.getNode(referenceNode=referenceNode)
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

            nostrilExportJoint = nostrilSpec.getNode(referenceNode=referenceNode)
            nostrilExportMatrix = nostrilExportJoint.worldMatrix()
            nostrilMatrix = mirrorMatrix * nostrilExportMatrix

            nostrilSpace, nostrilGroup, nostrilCtrl = self.createFaceControl({'side': side, 'name': 'Nostril'}, parent=noseCtrl, matrix=nostrilMatrix)
            nostrilCtrl.addPointHelper('sphere', size=(1.5 * scale), side=side)
            nostrilCtrl.tagAsController(parent=noseCtrl)
            self.publishNode(nostrilCtrl, alias=f'{sideChar}_Nostril')

            nostrilCtrls.append(nostrilCtrl)

        # Create nose tip control
        #
        noseTipSpec = noseSpec.groups[self.Side.NONE]
        noseTipExportJoint = noseTipSpec.getNode(referenceNode=referenceNode)
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

                cheekExportJoint = cheekSpec.getNode(referenceNode=referenceNode)
                cheekExportMatrix = cheekExportJoint.worldMatrix()
                cheekMatrix = mirrorMatrix * cheekExportMatrix

                cheekSpaceName, cheekGroup, cheekCtrl = self.createFaceControl({'side': side, 'name': 'Cheek', 'index': index}, matrix=cheekMatrix, parent=parent)
                cheekCtrl.addPointHelper('sphere', size=(2.0 * scale), side=side)
                cheekCtrl.tagAsController(parent=parent)
                self.publishNode(cheekCtrl, alias=f'{sideChar}_Cheek{paddedIndex}')

                cheekCtrls[i] = cheekCtrl

    def buildJawRig(self, jawSpec, teethSpec, tongueSpec, chinSpec, throatSpec, scale=1.0):
        """
        Builds the jaw rig.

        :type jawSpec: skeletonspec.SkeletonSpec
        :type teethSpec: skeletonspec.SkeletonSpec
        :type tongueSpec: skeletonspec.SkeletonSpec
        :type chinSpec: skeletonspec.SkeletonSpec
        :type throatSpec: skeletonspec.SkeletonSpec
        :type rigScale: float
        :rtype: None
        """

        # Check if jaw was enabled
        #
        if not jawSpec.enabled:

            return

        # Create jaw control
        #
        faceCtrl = self.getPublishedNode('Face')
        jawExportJoint = self.scene(jawSpec.uuid)

        jawSpace, jawGroup, jawCtrl = self.createFaceControl({'name': 'Jaw'}, matrix=jawExportJoint, parent=faceCtrl)
        jawCtrl.addShape('WedgeCurve', size=(2.0 * scale), localPosition=(-10.0 * scale, 7.5 * scale, 0.0), localRotate=(0.0, 0.0, 90.0), side=self.Side.CENTER)
        jawCtrl.prepareChannelBoxForAnimation()
        self.publishNode(jawCtrl, alias='Jaw')

        jawCtrl.userProperties['space'] = jawSpace.uuid()
        jawCtrl.userProperties['transform'] = jawGroup.uuid()

        # Check if teeth were enabled
        #
        upperTeethSpec, lowerTeethSpec = teethSpec.children

        if upperTeethSpec.enabled and lowerTeethSpec.enabled:

            upperTeethExportJoint = self.scene(upperTeethSpec.uuid)

            upperTeethSpace, upperTeethGroup, upperTeethCtrl = self.createFaceControl({'name': 'UpperTeeth'}, matrix=upperTeethExportJoint, parent=jawCtrl)
            upperTeethCtrl.addPointHelper('box', size=(2.0 * scale), localScale=(0.5, 1.0, 2.0), localRotate=(0.0, 0.0, 90.0), side=self.Side.CENTER)
            upperTeethCtrl.prepareChannelBoxForAnimation()
            upperTeethCtrl.tagAsController(parent=jawCtrl)
            self.publishNode(upperTeethCtrl, alias='UpperTeeth')

            lowerTeethExportJoint = self.scene(lowerTeethSpec.uuid)

            lowerTeethSpace, lowerTeethGroup, lowerTeethCtrl = self.createFaceControl({'name': 'LowerTeeth'}, matrix=lowerTeethExportJoint, parent=jawCtrl)
            lowerTeethCtrl.addPointHelper('box', size=(2.0 * scale), localScale=(0.5, 1.0, 2.0), side=self.Side.CENTER)
            lowerTeethCtrl.prepareChannelBoxForAnimation()
            lowerTeethCtrl.tagAsController(parent=jawCtrl)
            self.publishNode(lowerTeethCtrl, alias='LowerTeeth')

        # Check if the tongue was enabled
        #
        tongueCount = len(tongueSpec.children)
        tongueEnabled = tongueCount > 0

        if tongueEnabled:

            tongueCtrls = [None] * tongueCount

            for (i, spec) in enumerate(tongueSpec.children):

                exportJoint = self.scene(spec.uuid)
                index = i + 1
                parent = jawCtrl if (i == 0) else tongueCtrls[i - 1]

                tongueSpace, tongueGroup, tongueCtrl = self.createFaceControl({'name': 'Tongue', 'index': index}, matrix=exportJoint, parent=parent)
                tongueCtrl.addPointHelper('box', size=(2.0 * scale), localScale=(1.0, 0.5, 2.0), side=self.Side.CENTER)
                tongueCtrl.prepareChannelBoxForAnimation()
                tongueCtrl.tagAsController(parent=jawCtrl)
                self.publishNode(tongueCtrl, alias=f'Tongue{str(i).zfill(2)}')

        # Check if chin was enabled
        #
        if chinSpec.enabled:

            chinExportJoint = self.scene(chinSpec.uuid)

            chinSpace, chinGroup, chinCtrl = self.createFaceControl({'name': 'Chin'}, matrix=chinExportJoint, parent=jawCtrl)
            chinCtrl.addPointHelper('disc', size=(2.0 * scale), localPosition=(0.0, 4.0 * scale, 0.0), localRotate=(0.0, 0.0, 90.0), side=self.Side.CENTER)
            chinCtrl.prepareChannelBoxForAnimation()
            self.publishNode(chinCtrl, alias='Chin')

            chinCtrl.tagAsController(parent=jawCtrl)

        # Check if throat was enabled
        #
        if throatSpec.enabled:

            # Create throat control
            #
            throatExportJoint = self.scene(throatSpec.uuid)

            throatSpaceName = self.formatName(name='Throat', type='space')
            throatSpace = self.scene.createNode('transform', name=throatSpaceName, parent=faceCtrl)
            throatSpace.copyTransform(throatExportJoint)
            throatSpace.freezeTransform()

            throatGroupName = self.formatName(name='Throat', type='transform')
            throatGroup = self.scene.createNode('transform', name=throatGroupName, parent=throatSpace)

            throatCtrl = self.scene.createNode('transform', name=throatSpec.driver, parent=throatGroup)
            throatCtrl.addShape('CrownCurve', side=self.Side.CENTER)
            throatCtrl.prepareChannelBoxForAnimation()
            throatCtrl.tagAsController(parent=jawCtrl)
            self.publishNode(throatCtrl, alias='Throat')

            throatCtrl.tagAsController(parent=jawCtrl)

            # Constraint throat control
            #
            faceCtrl, chinCtrl = self.getPublishedNode('Face'), self.getPublishedNode('Chin')

            throatSpace.addConstraint('transformConstraint', [faceCtrl, chinCtrl], maintainOffset=True, skipRotate=True)
            throatSpace.addConstraint('aimConstraint', [chinCtrl], aimVector=(1.0, 0.0, 0.0), upVector=(0.0, 0.0, 1.0), worldUpType=2, worldUpVector=(0.0, 0.0, 1.0), worldUpObject=chinCtrl, maintainOffset=True)

        # Tag controls
        #
        jawCtrl.tagAsController(parent=faceCtrl)

    def buildLipRigs(self, lipsSpec, scale=1.0):
        """
        Builds the lip rigs.

        :type lipsSpec: skeletonspec.SkeletonSpec
        :type scale: float
        :rtype: None
        """

        # Check if lips were enabled
        #
        upperLipSpec, lowerLipSpec, cornerLipSpec = lipsSpec.children
        isEnabled = all([spec.enabled for spec in cornerLipSpec.groups.values()])

        if not isEnabled:

            return

        # Decompose lip specs
        #
        leftUpperLipSpecs, centerUpperLipSpecs, rightUpperLipSpecs = upperLipSpec.groups[self.Side.LEFT], upperLipSpec.groups[self.Side.CENTER], upperLipSpec.groups[self.Side.RIGHT]
        leftLowerLipSpecs, centerLowerLipSpecs, rightLowerLipSpecs = lowerLipSpec.groups[self.Side.LEFT], lowerLipSpec.groups[self.Side.CENTER], lowerLipSpec.groups[self.Side.RIGHT]
        leftCornerLipSpec, rightCornerLipSpec = cornerLipSpec.groups[self.Side.LEFT], cornerLipSpec.groups[self.Side.RIGHT]

        # Create lip corner controls
        #
        faceCtrl = self.getPublishedNode('Face')
        jawCtrl = self.getPublishedNode('Jaw')

        leftCornerLipExportJoint = self.scene(leftCornerLipSpec.uuid)
        leftCornerLipSpace, leftCornerLipGroup, leftCornerLipCtrl = self.createFaceControl({'side': self.Side.LEFT, 'name': 'CornerLip'}, parent=faceCtrl, matrix=leftCornerLipExportJoint)
        leftCornerLipSpace.addConstraint('transformConstraint', [faceCtrl, jawCtrl], maintainOffset=True)
        leftCornerLipCtrl.addPointHelper('box', 'cross', size=1.0, side=self.Side.LEFT)
        leftCornerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leftCornerLipCtrl, alias='L_CornerLip')

        leftUpperCornerLipSpace, leftUpperCornerLipGroup, leftUpperCornerLipCtrl = self.createFaceControl({'side': self.Side.LEFT, 'name': 'UpperCornerLip'}, parent=leftCornerLipCtrl)
        leftUpperCornerLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, localPosition=(0.125, 0.0, 0.0), localScale=(0.5, 1.0, 1.0), side=self.Side.LEFT)
        leftUpperCornerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leftUpperCornerLipCtrl, alias='L_UpperCornerLip')
        
        leftLowerCornerLipSpace, leftLowerCornerLipGroup, leftLowerCornerLipCtrl = self.createFaceControl({'side': self.Side.LEFT, 'name': 'LowerCornerLip'}, parent=leftCornerLipCtrl)
        leftLowerCornerLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, localPosition=(-0.125, 0.0, 0.0), localScale=(0.5, 1.0, 1.0), side=self.Side.LEFT)
        leftLowerCornerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leftLowerCornerLipCtrl, alias='L_LowerCornerLip')

        leftCornerLipCtrl.tagAsController(parent=faceCtrl, children=[leftUpperCornerLipCtrl, leftLowerCornerLipCtrl])
        leftUpperCornerLipCtrl.tagAsController(parent=leftCornerLipCtrl)
        leftLowerCornerLipCtrl.tagAsController(parent=leftCornerLipCtrl)

        rightCornerLipExportJoint = self.scene(rightCornerLipSpec.uuid)
        rightCornerLipSpace, rightCornerLipGroup, rightCornerLipCtrl = self.createFaceControl({'side': self.Side.RIGHT, 'name': 'CornerLip'}, parent=faceCtrl, matrix=rightCornerLipExportJoint)
        rightCornerLipSpace.addConstraint('transformConstraint', [faceCtrl, jawCtrl], maintainOffset=True)
        rightCornerLipCtrl.addPointHelper('box', 'cross', size=1.0, side=self.Side.RIGHT)
        rightCornerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(rightCornerLipCtrl, alias='R_CornerLip')
        
        rightUpperCornerLipSpace, rightUpperCornerLipGroup, rightUpperCornerLipCtrl = self.createFaceControl({'side': self.Side.RIGHT, 'name': 'UpperCornerLip'}, parent=rightCornerLipCtrl)
        rightUpperCornerLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, localPosition=(0.125, 0.0, 0.0), localScale=(0.5, 1.0, 1.0), side=self.Side.RIGHT)
        rightUpperCornerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(rightUpperCornerLipCtrl, alias='R_UpperCornerLip')
        
        rightLowerCornerLipSpace, rightLowerCornerLipGroup, rightLowerCornerLipCtrl = self.createFaceControl({'side': self.Side.RIGHT, 'name': 'LowerCornerLip'}, parent=rightCornerLipCtrl)
        rightLowerCornerLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, localPosition=(-0.125, 0.0, 0.0), localScale=(0.5, 1.0, 1.0), side=self.Side.RIGHT)
        rightLowerCornerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(rightLowerCornerLipCtrl, alias='R_LowerCornerLip')
        
        rightCornerLipCtrl.tagAsController(parent=faceCtrl, children=[rightUpperCornerLipCtrl, rightLowerCornerLipCtrl])
        rightUpperCornerLipCtrl.tagAsController(parent=rightCornerLipCtrl)
        rightLowerCornerLipCtrl.tagAsController(parent=rightCornerLipCtrl)
        
        # Create upper-lip macro controls
        #
        centerUpperLipSpec = centerUpperLipSpecs[0]
        centerUpperLipExportJoint = self.scene(centerUpperLipSpec.uuid)

        centerUpperLipSpace, centerUpperLipGroup, centerUpperLipCtrl = self.createFaceControl({'side': self.Side.CENTER, 'name': 'UpperLip'}, parent=faceCtrl, matrix=centerUpperLipExportJoint)
        centerUpperLipCtrl.addPointHelper('box', 'cross', size=1.0, side=self.Side.CENTER)
        centerUpperLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(centerUpperLipCtrl, alias='C_UpperLip')

        leftUpperLipSpace, leftUpperLipGroup, leftUpperLipCtrl = self.createFaceControl({'side': self.Side.LEFT, 'name': 'UpperLip'}, parent=centerUpperLipCtrl)
        leftUpperLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, side=self.Side.LEFT)
        leftUpperLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leftUpperLipCtrl, alias='L_UpperLip')

        rightUpperLipSpace, rightUpperLipGroup, rightUpperLipCtrl = self.createFaceControl({'side': self.Side.RIGHT, 'name': 'UpperLip'}, parent=centerUpperLipCtrl)
        rightUpperLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, side=self.Side.RIGHT)
        rightUpperLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(rightUpperLipCtrl, alias='R_UpperLip')

        centerUpperLipCtrl.tagAsController(parent=faceCtrl, children=[leftUpperLipCtrl, rightUpperLipCtrl])
        leftUpperLipCtrl.tagAsController(parent=centerUpperLipCtrl)
        rightUpperLipCtrl.tagAsController(parent=centerUpperLipCtrl)

        centerUpperLipCurveFromPointName = self.formatName(side=self.Side.CENTER, name='UpperLip', type='curveFromPoint')
        centerUpperLipCurveFromPoint = self.scene.createNode('curveFromPoint', name=centerUpperLipCurveFromPointName)
        centerUpperLipCurveFromPoint.degree = 1

        for (i, ctrl) in enumerate([leftUpperLipCtrl, centerUpperLipCtrl, rightUpperLipCtrl]):

            ctrl.connectPlugs(f'worldMatrix[{ctrl.instanceNumber()}]', centerUpperLipCurveFromPoint[f'inputMatrix[{i}]'])

        centerUpperLipCurve = self.scene.createNode('nurbsCurve', parent=centerUpperLipCtrl)
        centerUpperLipCurve.connectPlugs(f'parentInverseMatrix[{centerUpperLipCurve.instanceNumber()}]', centerUpperLipCurveFromPoint['parentInverseMatrix'])
        centerUpperLipCurve.connectPlugs(centerUpperLipCurveFromPoint['outputCurve'], 'create')
        centerUpperLipCurve.useObjectColor = 2
        centerUpperLipCurve.wireColorRGB = (1.0, 1.0, 0.0)

        centerUpperLipCtrl.renameShapes()

        # Setup upper-lip macro controls
        #
        centerUpperLipBreakMatrix = self.scene.createNode('breakMatrix')
        centerUpperLipBreakMatrix.normalize = True
        centerUpperLipBreakMatrix.connectPlugs(centerUpperLipCtrl[f'parentMatrix[{centerUpperLipCtrl.instanceNumber()}]'], 'inMatrix')

        leftCornerLipBreakMatrixName = self.formatName(side=self.Side.LEFT, name='CornerLip', type='breakMatrix')
        leftCornerLipBreakMatrix = self.scene.createNode('breakMatrix', name=leftCornerLipBreakMatrixName)
        leftCornerLipBreakMatrix.connectPlugs(leftCornerLipCtrl[f'worldMatrix[{leftCornerLipCtrl.instanceNumber()}]'], 'inMatrix')

        leftUpperLipVectorName = self.formatName(side=self.Side.LEFT, name='UpperLip', subname='Vector', type='vectorMath')
        leftUpperLipVector = self.scene.createNode('vectorMath', name=leftUpperLipVectorName)
        leftUpperLipVector.operation = 1  # Subtract
        leftUpperLipVector.normalize = False
        leftUpperLipVector.connectPlugs(leftCornerLipBreakMatrix['row4X'], 'inFloatAX')
        leftUpperLipVector.connectPlugs(leftCornerLipBreakMatrix['row4Y'], 'inFloatAY')
        leftUpperLipVector.connectPlugs(leftCornerLipBreakMatrix['row4Z'], 'inFloatAZ')
        leftUpperLipVector.connectPlugs(centerUpperLipBreakMatrix['row4X'], 'inFloatBX')
        leftUpperLipVector.connectPlugs(centerUpperLipBreakMatrix['row4Y'], 'inFloatBY')
        leftUpperLipVector.connectPlugs(centerUpperLipBreakMatrix['row4Z'], 'inFloatBZ')

        leftUpperLipDotName = self.formatName(side=self.Side.LEFT, name='UpperLip', subname='Dot', type='vectorMath')
        leftUpperLipDot = self.scene.createNode('vectorMath', name=leftUpperLipDotName)
        leftUpperLipDot.operation = 16  # Dot
        leftUpperLipDot.normalize = False
        leftUpperLipDot.connectPlugs(centerUpperLipBreakMatrix['row3X'], 'inFloatAX')
        leftUpperLipDot.connectPlugs(centerUpperLipBreakMatrix['row3Y'], 'inFloatAY')
        leftUpperLipDot.connectPlugs(centerUpperLipBreakMatrix['row3Z'], 'inFloatAZ')
        leftUpperLipDot.connectPlugs(leftUpperLipVector['outFloat'], 'inFloatB')

        leftUpperLipHalfDotName = self.formatName(side=self.Side.LEFT, name='UpperLip', subname='HalfDot', type='floatMath')
        leftUpperLipHalfDot = self.scene.createNode('floatMath', name=leftUpperLipHalfDotName)
        leftUpperLipHalfDot.operation = 6  # Half
        leftUpperLipHalfDot.connectPlugs(leftUpperLipDot['outFloatX'], 'inFloatA')
        leftUpperLipHalfDot.connectPlugs('outFloat', leftUpperLipSpace['translateZ'])

        rightCornerLipBreakMatrixName = self.formatName(side=self.Side.RIGHT, name='CornerLip', type='breakMatrix')
        rightCornerLipBreakMatrix = self.scene.createNode('breakMatrix', name=rightCornerLipBreakMatrixName)
        rightCornerLipBreakMatrix.connectPlugs(rightCornerLipCtrl[f'worldMatrix[{rightCornerLipCtrl.instanceNumber()}]'], 'inMatrix')

        rightUpperLipVectorName = self.formatName(side=self.Side.RIGHT, name='UpperLip', subname='Vector', type='vectorMath')
        rightUpperLipVector = self.scene.createNode('vectorMath', name=rightUpperLipVectorName)
        rightUpperLipVector.operation = 1  # Subtract
        rightUpperLipVector.normalize = False
        rightUpperLipVector.connectPlugs(rightCornerLipBreakMatrix['row4X'], 'inFloatAX')
        rightUpperLipVector.connectPlugs(rightCornerLipBreakMatrix['row4Y'], 'inFloatAY')
        rightUpperLipVector.connectPlugs(rightCornerLipBreakMatrix['row4Z'], 'inFloatAZ')
        rightUpperLipVector.connectPlugs(centerUpperLipBreakMatrix['row4X'], 'inFloatBX')
        rightUpperLipVector.connectPlugs(centerUpperLipBreakMatrix['row4Y'], 'inFloatBY')
        rightUpperLipVector.connectPlugs(centerUpperLipBreakMatrix['row4Z'], 'inFloatBZ')

        rightUpperLipDotName = self.formatName(side=self.Side.RIGHT, name='UpperLip', subname='Dot', type='vectorMath')
        rightUpperLipDot = self.scene.createNode('vectorMath', name=rightUpperLipDotName)
        rightUpperLipDot.operation = 16  # Dot
        rightUpperLipDot.normalize = False
        rightUpperLipDot.connectPlugs(centerUpperLipBreakMatrix['row3X'], 'inFloatAX')
        rightUpperLipDot.connectPlugs(centerUpperLipBreakMatrix['row3Y'], 'inFloatAY')
        rightUpperLipDot.connectPlugs(centerUpperLipBreakMatrix['row3Z'], 'inFloatAZ')
        rightUpperLipDot.connectPlugs(rightUpperLipVector['outFloat'], 'inFloatB')
        
        rightUpperLipHalfDotName = self.formatName(side=self.Side.RIGHT, name='UpperLip', subname='HalfDot', type='floatMath')
        rightUpperLipHalfDot = self.scene.createNode('floatMath', name=rightUpperLipHalfDotName)
        rightUpperLipHalfDot.operation = 6  # Half
        rightUpperLipHalfDot.connectPlugs(rightUpperLipDot['outFloatX'], 'inFloatA')
        rightUpperLipHalfDot.connectPlugs('outFloat', rightUpperLipSpace['translateZ'])
        
        # Create upper-lip proxy curves
        #
        leftUpperLipCurveFromPointName = self.formatName(side=self.Side.LEFT, name='UpperLip', type='curveFromPoint')
        leftUpperLipCurveFromPoint = self.scene.createNode('curveFromPoint', name=leftUpperLipCurveFromPointName)
        leftUpperLipCurveFromPoint.degree = 3

        for (i, ctrl) in enumerate([centerUpperLipCtrl, leftUpperLipCtrl, leftUpperCornerLipCtrl, leftCornerLipCtrl]):

            ctrl.connectPlugs(f'worldMatrix[{ctrl.instanceNumber()}]', leftUpperLipCurveFromPoint[f'inputMatrix[{i}]'])

        leftUpperLipCurve = self.scene.createNode('nurbsCurve', parent=centerUpperLipCtrl)
        leftUpperLipCurve.connectPlugs(f'parentInverseMatrix[{leftUpperLipCurve.instanceNumber()}]', leftUpperLipCurveFromPoint['parentInverseMatrix'])
        leftUpperLipCurve.connectPlugs(leftUpperLipCurveFromPoint['outputCurve'], 'create')
        leftUpperLipCurve.template = True

        centerUpperLipCtrl.renameShapes()

        rightUpperLipCurveFromPointName = self.formatName(side=self.Side.RIGHT, name='UpperLip', type='curveFromPoint')
        rightUpperLipCurveFromPoint = self.scene.createNode('curveFromPoint', name=rightUpperLipCurveFromPointName)
        rightUpperLipCurveFromPoint.degree = 3

        for (i, ctrl) in enumerate([centerUpperLipCtrl, rightUpperLipCtrl, rightUpperCornerLipCtrl, rightCornerLipCtrl]):

            ctrl.connectPlugs(f'worldMatrix[{ctrl.instanceNumber()}]', rightUpperLipCurveFromPoint[f'inputMatrix[{i}]'])

        rightUpperLipCurve = self.scene.createNode('nurbsCurve', parent=centerUpperLipCtrl)
        rightUpperLipCurve.connectPlugs(f'parentInverseMatrix[{rightUpperLipCurve.instanceNumber()}]', rightUpperLipCurveFromPoint['parentInverseMatrix'])
        rightUpperLipCurve.connectPlugs(rightUpperLipCurveFromPoint['outputCurve'], 'create')
        rightUpperLipCurve.template = True

        centerUpperLipCtrl.renameShapes()

        # Create lower-lip macro controls
        #
        centerLowerLipSpec = centerLowerLipSpecs[0]
        centerLowerLipExportJoint = self.scene(centerLowerLipSpec.uuid)

        centerLowerLipSpace, centerLowerLipGroup, centerLowerLipCtrl = self.createFaceControl({'side': self.Side.CENTER, 'name': 'LowerLip'}, parent=faceCtrl, matrix=centerLowerLipExportJoint)
        centerLowerLipSpace.addConstraint('transformConstraint', [jawCtrl], maintainOffset=True)
        centerLowerLipCtrl.addPointHelper('box', 'cross', size=1.0, side=self.Side.CENTER)
        centerLowerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(centerLowerLipCtrl, alias='C_LowerLip')

        leftLowerLipSpace, leftLowerLipGroup, leftLowerLipCtrl = self.createFaceControl({'side': self.Side.LEFT, 'name': 'LowerLip'}, parent=centerLowerLipCtrl)
        leftLowerLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, side=self.Side.LEFT)
        leftLowerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(leftLowerLipCtrl, alias='L_LowerLip')

        rightLowerLipSpace, rightLowerLipGroup, rightLowerLipCtrl = self.createFaceControl({'side': self.Side.RIGHT, 'name': 'LowerLip'}, parent=centerLowerLipCtrl)
        rightLowerLipCtrl.addPointHelper('box', 'centerMarker', size=0.5, side=self.Side.RIGHT)
        rightLowerLipCtrl.prepareChannelBoxForAnimation()
        self.publishNode(rightLowerLipCtrl, alias='R_LowerLip')

        centerLowerLipCtrl.tagAsController(parent=faceCtrl, children=[leftLowerLipCtrl, rightLowerLipCtrl])
        leftLowerLipCtrl.tagAsController(parent=centerLowerLipCtrl)
        rightLowerLipCtrl.tagAsController(parent=centerLowerLipCtrl)

        centerLowerLipCurveFromPointName = self.formatName(side=self.Side.CENTER, name='LowerLip', type='curveFromPoint')
        centerLowerLipCurveFromPoint = self.scene.createNode('curveFromPoint', name=centerLowerLipCurveFromPointName)
        centerLowerLipCurveFromPoint.degree = 1

        for (i, ctrl) in enumerate([leftLowerLipCtrl, centerLowerLipCtrl, rightLowerLipCtrl]):

            ctrl.connectPlugs(f'worldMatrix[{ctrl.instanceNumber()}]', centerLowerLipCurveFromPoint[f'inputMatrix[{i}]'])

        centerLowerLipCurve = self.scene.createNode('nurbsCurve', parent=centerLowerLipCtrl)
        centerLowerLipCurve.connectPlugs(f'parentInverseMatrix[{centerLowerLipCurve.instanceNumber()}]', centerLowerLipCurveFromPoint['parentInverseMatrix'])
        centerLowerLipCurve.connectPlugs(centerLowerLipCurveFromPoint['outputCurve'], 'create')
        centerLowerLipCurve.useObjectColor = 2
        centerLowerLipCurve.wireColorRGB = (1.0, 1.0, 0.0)

        centerLowerLipCtrl.renameShapes()

        # Create lower-lip proxy curves
        #
        leftLowerLipCurveFromPointName = self.formatName(side=self.Side.LEFT, name='LowerLip', type='curveFromPoint')
        leftLowerLipCurveFromPoint = self.scene.createNode('curveFromPoint', name=leftLowerLipCurveFromPointName)
        leftLowerLipCurveFromPoint.degree = 3

        for (i, ctrl) in enumerate([centerLowerLipCtrl, leftLowerLipCtrl, leftLowerCornerLipCtrl, leftCornerLipCtrl]):

            ctrl.connectPlugs(f'worldMatrix[{ctrl.instanceNumber()}]', leftLowerLipCurveFromPoint[f'inputMatrix[{i}]'])

        leftLowerLipCurve = self.scene.createNode('nurbsCurve', parent=centerLowerLipCtrl)
        leftLowerLipCurve.connectPlugs(f'parentInverseMatrix[{leftLowerLipCurve.instanceNumber()}]', leftLowerLipCurveFromPoint['parentInverseMatrix'])
        leftLowerLipCurve.connectPlugs(leftLowerLipCurveFromPoint['outputCurve'], 'create')
        leftLowerLipCurve.template = True

        centerLowerLipCtrl.renameShapes()

        rightLowerLipCurveFromPointName = self.formatName(side=self.Side.RIGHT, name='LowerLip', type='curveFromPoint')
        rightLowerLipCurveFromPoint = self.scene.createNode('curveFromPoint', name=rightLowerLipCurveFromPointName)
        rightLowerLipCurveFromPoint.degree = 3

        for (i, ctrl) in enumerate([centerLowerLipCtrl, rightLowerLipCtrl, rightLowerCornerLipCtrl, rightCornerLipCtrl]):

            ctrl.connectPlugs(f'worldMatrix[{ctrl.instanceNumber()}]', rightLowerLipCurveFromPoint[f'inputMatrix[{i}]'])

        rightLowerLipCurve = self.scene.createNode('nurbsCurve', parent=centerLowerLipCtrl)
        rightLowerLipCurve.connectPlugs(f'parentInverseMatrix[{rightLowerLipCurve.instanceNumber()}]', rightLowerLipCurveFromPoint['parentInverseMatrix'])
        rightLowerLipCurve.connectPlugs(rightLowerLipCurveFromPoint['outputCurve'], 'create')
        rightLowerLipCurve.template = True

        centerLowerLipCtrl.renameShapes()

        # Setup lower-lip macro controls
        #
        centerLowerLipBreakMatrix = self.scene.createNode('breakMatrix')
        centerLowerLipBreakMatrix.normalize = True
        centerLowerLipBreakMatrix.connectPlugs(centerLowerLipCtrl[f'parentMatrix[{centerLowerLipCtrl.instanceNumber()}]'], 'inMatrix')

        leftLowerLipVectorName = self.formatName(side=self.Side.LEFT, name='LowerLip', subname='Vector', type='vectorMath')
        leftLowerLipVector = self.scene.createNode('vectorMath', name=leftLowerLipVectorName)
        leftLowerLipVector.operation = 1  # Subtract
        leftLowerLipVector.normalize = False
        leftLowerLipVector.connectPlugs(leftCornerLipBreakMatrix['row4X'], 'inFloatAX')
        leftLowerLipVector.connectPlugs(leftCornerLipBreakMatrix['row4Y'], 'inFloatAY')
        leftLowerLipVector.connectPlugs(leftCornerLipBreakMatrix['row4Z'], 'inFloatAZ')
        leftLowerLipVector.connectPlugs(centerLowerLipBreakMatrix['row4X'], 'inFloatBX')
        leftLowerLipVector.connectPlugs(centerLowerLipBreakMatrix['row4Y'], 'inFloatBY')
        leftLowerLipVector.connectPlugs(centerLowerLipBreakMatrix['row4Z'], 'inFloatBZ')

        leftLowerLipDotName = self.formatName(side=self.Side.LEFT, name='LowerLip', subname='Dot', type='vectorMath')
        leftLowerLipDot = self.scene.createNode('vectorMath', name=leftLowerLipDotName)
        leftLowerLipDot.operation = 16  # Dot
        leftLowerLipDot.normalize = False
        leftLowerLipDot.connectPlugs(centerLowerLipBreakMatrix['row3X'], 'inFloatAX')
        leftLowerLipDot.connectPlugs(centerLowerLipBreakMatrix['row3Y'], 'inFloatAY')
        leftLowerLipDot.connectPlugs(centerLowerLipBreakMatrix['row3Z'], 'inFloatAZ')
        leftLowerLipDot.connectPlugs(leftLowerLipVector['outFloat'], 'inFloatB')
        
        leftLowerLipHalfDotName = self.formatName(side=self.Side.LEFT, name='LowerLip', subname='HalfDot', type='floatMath')
        leftLowerLipHalfDot = self.scene.createNode('floatMath', name=leftLowerLipHalfDotName)
        leftLowerLipHalfDot.operation = 6  # Half
        leftLowerLipHalfDot.connectPlugs(leftLowerLipDot['outFloatX'], 'inFloatA')
        leftLowerLipHalfDot.connectPlugs('outFloat', leftLowerLipSpace['translateZ'])
        
        rightLowerLipVectorName = self.formatName(side=self.Side.RIGHT, name='LowerLip', subname='Vector', type='vectorMath')
        rightLowerLipVector = self.scene.createNode('vectorMath', name=rightLowerLipVectorName)
        rightLowerLipVector.operation = 1  # Subtract
        rightLowerLipVector.normalize = False
        rightLowerLipVector.connectPlugs(rightCornerLipBreakMatrix['row4X'], 'inFloatAX')
        rightLowerLipVector.connectPlugs(rightCornerLipBreakMatrix['row4Y'], 'inFloatAY')
        rightLowerLipVector.connectPlugs(rightCornerLipBreakMatrix['row4Z'], 'inFloatAZ')
        rightLowerLipVector.connectPlugs(centerLowerLipBreakMatrix['row4X'], 'inFloatBX')
        rightLowerLipVector.connectPlugs(centerLowerLipBreakMatrix['row4Y'], 'inFloatBY')
        rightLowerLipVector.connectPlugs(centerLowerLipBreakMatrix['row4Z'], 'inFloatBZ')

        rightLowerLipDotName = self.formatName(side=self.Side.RIGHT, name='LowerLip', subname='Dot', type='vectorMath')
        rightLowerLipDot = self.scene.createNode('vectorMath', name=rightLowerLipDotName)
        rightLowerLipDot.operation = 16  # Dot
        rightLowerLipDot.normalize = False
        rightLowerLipDot.connectPlugs(centerLowerLipBreakMatrix['row3X'], 'inFloatAX')
        rightLowerLipDot.connectPlugs(centerLowerLipBreakMatrix['row3Y'], 'inFloatAY')
        rightLowerLipDot.connectPlugs(centerLowerLipBreakMatrix['row3Z'], 'inFloatAZ')
        rightLowerLipDot.connectPlugs(rightLowerLipVector['outFloat'], 'inFloatB')
        
        rightLowerLipHalfDotName = self.formatName(side=self.Side.RIGHT, name='LowerLip', subname='HalfDot', type='floatMath')
        rightLowerLipHalfDot = self.scene.createNode('floatMath', name=rightLowerLipHalfDotName)
        rightLowerLipHalfDot.operation = 6  # Half
        rightLowerLipHalfDot.connectPlugs(rightLowerLipDot['outFloatX'], 'inFloatA')
        rightLowerLipHalfDot.connectPlugs('outFloat', rightLowerLipSpace['translateZ'])

        # Create lip micro controls
        #
        lipComponents = {
            'UpperLip': (
                centerUpperLipCtrl,
                {
                    self.Side.LEFT: (leftUpperLipCurve, leftUpperLipSpecs),
                    self.Side.RIGHT: (rightUpperLipCurve, rightUpperLipSpecs)
                }
            ),
            'LowerLip': (
                centerLowerLipCtrl,
                {
                    self.Side.LEFT: (leftLowerLipCurve, leftLowerLipSpecs),
                    self.Side.RIGHT: (rightLowerLipCurve, rightLowerLipSpecs)
                }
            )
        }
        
        for (lipName, (centerLipCtrl, lipSubcomponent)) in lipComponents.items():

            lipSpace, lipGroup, lipCtrl = self.createFaceControl({'side': self.Side.CENTER, 'name': lipName, 'index': 1}, parent=faceCtrl)
            lipSpace.addConstraint('transformConstraint', [centerLipCtrl], maintainOffset=False)
            lipCtrl.addPointHelper('sphere', size=0.25, side=self.Side.CENTER)
            lipCtrl.prepareChannelBoxForAnimation()
            lipCtrl.tagAsController(parent=centerLipCtrl)
            self.publishNode(lipCtrl, alias=f'C_{lipName}01')

            for (side, (lipCurve, lipSpecs)) in lipSubcomponent.items():
                
                sideChar = side.name.upper()[0]
                mirrorSign = -1.0 if (side == self.Side.RIGHT) else 1.0
    
                lipCurveFromPoint = self.scene(lipCurve['create'].source().node())
                lipCtrls = [self.scene(element.source().node()) for element in plugutils.iterElements(lipCurveFromPoint['inputMatrix'])]
                lipStartCtrl, lipEndCtrl = lipCtrls[1], lipCtrls[-2]
    
                startBreakMatrixName = self.formatName(side=side, name=lipName, type='breakMatrix')
                startBreakMatrix = self.scene.createNode('breakMatrix', name=startBreakMatrixName)
                startBreakMatrix.normalize = True
                startBreakMatrix.connectPlugs(lipStartCtrl[f'worldMatrix[{lipStartCtrl.instanceNumber()}]'], 'inMatrix')
    
                endBreakMatrixName = self.formatName(side=side, name=f'{lipName}Corner', type='breakMatrix')
                endBreakMatrix = self.scene.createNode('breakMatrix', name=endBreakMatrixName)
                endBreakMatrix.normalize = True
                endBreakMatrix.connectPlugs(lipEndCtrl[f'worldMatrix[{lipEndCtrl.instanceNumber()}]'], 'inMatrix')
    
                denominator = len(lipSpecs) + 1
    
                for (i, lipSpec) in enumerate(lipSpecs, start=1):
    
                    lipSpace, lipGroup, lipCtrl = self.createFaceControl({'side': side, 'name': lipName, 'index': i}, parent=faceCtrl)
                    lipCtrl.addPointHelper('sphere', size=0.25, side=side)
                    lipCtrl.prepareChannelBoxForAnimation()
                    lipCtrl.tagAsController(parent=centerLipCtrl)
                    self.publishNode(lipCtrl, alias=f'{sideChar}_{lipName}{str(i).zfill(2)}')
    
                    numerator = float(i)
                    parameter = numerator / denominator
    
                    constraint = lipSpace.addConstraint(
                        'pointOnCurveConstraint',
                        [lipCurve],
                        parameter=parameter,
                        useFraction=True,
                        forwardVector=(0.0, 0.0, 1.0 * mirrorSign),
                        upVector=(1.0, 0.0, 0.0),
                        worldUpType=3,  # Vector
                        maintainOffset=False
                    )
    
                    worldUpVectorName = self.formatName(side=side, name='UpperLip', index=i, type='vectorMath')
                    worldUpVector = self.scene.createNode('vectorMath', name=worldUpVectorName)
                    worldUpVector.operation = 19  # Lerp
                    worldUpVector.weight = parameter
                    worldUpVector.connectPlugs(startBreakMatrix['row1X'], 'inFloatAX')
                    worldUpVector.connectPlugs(startBreakMatrix['row1Y'], 'inFloatAY')
                    worldUpVector.connectPlugs(startBreakMatrix['row1Z'], 'inFloatAZ')
                    worldUpVector.connectPlugs(endBreakMatrix['row1X'], 'inFloatBX')
                    worldUpVector.connectPlugs(endBreakMatrix['row1Y'], 'inFloatBY')
                    worldUpVector.connectPlugs(endBreakMatrix['row1Z'], 'inFloatBZ')
    
                    constraint.connectPlugs(worldUpVector['outFloat'], 'worldUpVector')

                    lipExportJoint = self.scene(lipSpec.uuid)
                    lipExportJoint.copyTransform(lipCtrl)

    def buildRig(self):
        """
        Builds the control rig for this component.

        :rtype: None
        """

        # Decompose component
        #
        referenceNode = self.skeletonReference()
        faceSpec, = self.skeletonSpecs()
        upperFaceSpec = faceSpec.children[self.FaceType.UPPER]
        midFaceSpec = faceSpec.children[self.FaceType.MID]
        lowerFaceSpec = faceSpec.children[self.FaceType.LOWER]

        controlsGroup = self.scene(self.controlsGroup)
        privateGroup = self.scene(self.privateGroup)
        jointsGroup = self.scene(self.jointsGroup)

        controlRig = self.findControlRig()
        rigRadius = float(controlRig.rigRadius)
        rigScale = controlRig.getRigScale()

        parentExportJoint, parentExportCtrl = self.getAttachmentTargets()

        # Create face control
        #
        faceEnabled = bool(faceSpec.enabled)
        faceExportJoint = faceSpec.getNode(referenceNode=referenceNode) if faceEnabled else None
        faceExportMatrix = faceExportJoint.worldMatrix() if (faceExportJoint is not None) else parentExportJoint.worldMatrix()

        faceSpaceName = self.formatName(name='Face', type='space')
        faceSpace = self.scene.createNode('transform', name=faceSpaceName, parent=controlsGroup)
        faceSpace.setWorldMatrix(faceExportMatrix, skipScale=True)
        faceSpace.freezeTransform()
        faceSpace.addConstraint('transformConstraint', [parentExportCtrl], maintainOffset=True)

        faceCtrl = self.scene.createNode('transform', name=faceSpec.driver, parent=faceSpace)
        faceCtrl.addPointHelper('tearDrop', size=(5.0 * rigScale), localPosition=(25.0 * rigScale, 0.0, 0.0), localRotate=(-90.0, 0.0, 90.0), side=self.Side.CENTER, lineWidth=4)
        faceCtrl.hideAttr('translate', 'rotate', 'scale', lock=True)
        faceCtrl.prepareChannelBoxForAnimation()
        self.publishNode(faceCtrl, alias='Face')

        # Create face subcontrols
        #
        splitFace = upperFaceSpec.enabled and midFaceSpec.enabled and lowerFaceSpec.enabled
        upperFaceCtrl, midFaceCtrl, lowerFaceCtrl = None, None, None

        if splitFace:

            # Create upper-face control
            #
            upperFaceExportJoint = upperFaceSpec.getNode(referenceNode=referenceNode)
            upperFaceExportMatrix = upperFaceExportJoint.worldMatrix()

            upperFaceSpace, upperFaceGroup, upperFaceCtrl = self.createFaceControl({'name': 'UpperFace'}, parent=faceCtrl, matrix=upperFaceExportMatrix)
            upperFaceCtrl.addPointHelper('disc', size=(50.0 * rigScale), localPosition=(5.0, 0.0, 0.0), side=self.Side.CENTER)
            upperFaceCtrl.prepareChannelBoxForAnimation()
            self.publishNode(upperFaceCtrl, alias='UpperFace')

            # TODO: Build mid control

            # Create lower-face control
            #
            lowerFaceExportJoint = lowerFaceSpec.getNode(referenceNode=referenceNode)
            lowerFaceExportMatrix = lowerFaceExportJoint.worldMatrix()

            lowerFaceSpace, lowerFaceGroup, lowerFaceCtrl = self.createFaceControl({'name': 'LowerFace'}, parent=faceCtrl, matrix=lowerFaceExportMatrix)
            lowerFaceCtrl.addPointHelper('disc', size=(50.0 * rigScale), localPosition=(-5.0, 0.0, 0.0), side=self.Side.CENTER)
            lowerFaceCtrl.prepareChannelBoxForAnimation()
            self.publishNode(lowerFaceCtrl, alias='LowerFace')

        # Create upper-face components
        #
        upperFaceParent = upperFaceCtrl if (upperFaceCtrl is not None) else faceCtrl

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
            scale=rigScale, radius=rigRadius, parent=upperFaceParent
        )

        # Create mid-face components
        #
        midFaceParent = midFaceCtrl if (midFaceCtrl is not None) else faceCtrl

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
        self.buildJawRig(faceSpec.children[self.FaceType.JAW], faceSpec.children[self.FaceType.TEETH], faceSpec.children[self.FaceType.TONGUE], faceSpec.children[self.FaceType.CHIN], faceSpec.children[self.FaceType.THROAT], rigScale=rigScale)
        #self.buildLipRigs(faceSpec.children[self.FaceType.LIPS], rigScale=rigScale)
    # endregion
