import FreeCAD
import FreeCADGui
from pivy import coin
import math
import arch_texture_utils.py2_utils as py2_utils

GEOMETRY_COORDINATES = ['Radius', 'Length', 'Height']
TRANSFORM_PARAMETERS = ['ZOffset', 'Rotation']
ROTATION_VECTOR = coin.SbVec3f(0, 0, -1)

PANORAMA_TYPE_THIRDS = 'Thirds'
PANORAMA_TYPE_360 = '360'


def noTexture(image):
    if image is None or image == '':
        return True

    return False


def containsNode(parent, node):
    childs = parent.getChildren()

    return node in childs


def addNode(parent, node):
    if not containsNode(parent, node):
        parent.addChild(node)


def removeNode(parent, node):
    if containsNode(parent, node):
        parent.removeChild(node)


class EnvironmentConfig():
    def __init__(self, obj):
        obj.Proxy = self

        self.isEnvironmentConfig = True
        self.setProperties(obj)

    def setProperties(self, obj):

        pl = obj.PropertiesList

        if not 'Radius' in pl:
            obj.addProperty("App::PropertyLength", "Radius", "Geometry",
                            "The Distance from the center of the coordinate system to the environment textures").Radius = 50000
        if not 'Length' in pl:
            obj.addProperty("App::PropertyLength", "Length", "Geometry",
                            "The overall Length of the environment panorama texture").Length = 150000
        if not 'Height' in pl:
            obj.addProperty("App::PropertyLength", "Height", "Geometry",
                            "The overall Height of the environment panorama texture").Height = 50000
        if not 'SkyOverlap' in pl:
            obj.addProperty("App::PropertyLength", "SkyOverlap", "Geometry",
                            "The distance the sky overlaps with the panorama texture").SkyOverlap = 25000
        if not 'Rotation' in pl:
            obj.addProperty("App::PropertyAngle", "Rotation", "Geometry",
                            "The rotation for the environment").Rotation = 0
        if not 'ZOffset' in pl:
            obj.addProperty("App::PropertyDistance", "ZOffset", "Geometry",
                            "The offset of the environment on the Z-Axis").ZOffset = -1
        if not 'PanoramaImage' in pl:
            obj.addProperty("App::PropertyFile", "PanoramaImage", "Texture",
                            "The image of the panorama to show as environment texture").PanoramaImage = ''
        if not 'PanoramaType' in pl:
            obj.addProperty("App::PropertyEnumeration", "PanoramaType",
                            "Geometry", "The type of panorama to display")
            obj.PanoramaType = [PANORAMA_TYPE_THIRDS, PANORAMA_TYPE_360]
            obj.PanoramaType = PANORAMA_TYPE_THIRDS

        if not 'SkyImage' in pl:
            obj.addProperty("App::PropertyFile", "SkyImage", "Texture",
                            "The image of the sky to show as environment texture").SkyImage = ''
        if not 'GroundImage' in pl:
            obj.addProperty("App::PropertyFile", "GroundImage", "Texture",
                            "The image of the ground to show as environment texture").GroundImage = ''

    def execute(self, fp):
        pass

    def onDocumentRestored(self, obj):
        self.setProperties(obj)


class ViewProviderEnvironmentConfig():
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

        self.transformNode = coin.SoTransform()

        self.coinNode = coin.SoSeparator()
        self.coinNode.addChild(self.transformNode)

        self.panoramaNode = self.setupPanoramaNode()
        self.skyNode = self.setupSkyNode()
        self.groundNode = self.setupGroundNode()

        self.updatePanoramaCoordinates()
        self.updatePanoramaTextureCoordinates()
        self.updateSkyCoordinates()
        self.updateGroundCoordinates()

        self.updateTransformNode()
        self.updateNodeVisibility()

        vobj.addDisplayMode(self.coinNode, "Standard")

    def updateNodeVisibility(self):
        if noTexture(self.Object.PanoramaImage):
            removeNode(self.coinNode, self.panoramaNode)
        else:
            addNode(self.coinNode, self.panoramaNode)

        if noTexture(self.Object.SkyImage):
            removeNode(self.coinNode, self.skyNode)
        else:
            addNode(self.coinNode, self.skyNode)

        if noTexture(self.Object.GroundImage):
            removeNode(self.coinNode, self.groundNode)
        else:
            addNode(self.coinNode, self.groundNode)

    def updateTransformNode(self):
        rotation = math.radians(self.Object.Rotation.Value)
        translation = coin.SoSFVec3f()
        translation.setValue(coin.SbVec3f(0, 0, self.Object.ZOffset.Value))

        self.transformNode.rotation.setValue(ROTATION_VECTOR, rotation)
        self.transformNode.translation.setValue(translation)

    def setupPanoramaNode(self):
        panoramaNode = coin.SoSeparator()

        self.panoramaCoordinates = coin.SoCoordinate3()

        self.panoramaTextureCoordinates = coin.SoTextureCoordinate2()

        self.panoramaTexture = coin.SoTexture2()
        self.panoramaTexture.filename = py2_utils.textureFileString(
            self.Object.PanoramaImage)
        self.panoramaTexture.model = coin.SoMultiTextureImageElement.REPLACE

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)
        faceset.numVertices.set1Value(1, 4)
        faceset.numVertices.set1Value(2, 4)

        panoramaNode.addChild(self.panoramaCoordinates)
        panoramaNode.addChild(self.panoramaTextureCoordinates)
        panoramaNode.addChild(self.panoramaTexture)
        panoramaNode.addChild(faceset)

        return panoramaNode

    def setupSkyNode(self):
        skyNode = coin.SoSeparator()

        self.skyCoordinates = coin.SoCoordinate3()

        self.skyTexture = coin.SoTexture2()
        self.skyTexture.filename = py2_utils.textureFileString(
            self.Object.SkyImage)
        self.skyTexture.model = coin.SoMultiTextureImageElement.REPLACE

        self.skyTextureCoordinates = coin.SoTextureCoordinate2()

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)
        faceset.numVertices.set1Value(1, 4)
        faceset.numVertices.set1Value(2, 4)
        faceset.numVertices.set1Value(3, 4)
        faceset.numVertices.set1Value(4, 3)
        faceset.numVertices.set1Value(5, 4)

        skyNode.addChild(self.skyCoordinates)
        skyNode.addChild(self.skyTextureCoordinates)
        skyNode.addChild(self.skyTexture)
        skyNode.addChild(faceset)

        return skyNode

    def setupGroundNode(self):
        groundNode = coin.SoSeparator()

        self.groundCoordinates = coin.SoCoordinate3()

        self.groundTexture = coin.SoTexture2()
        self.groundTexture.filename = py2_utils.textureFileString(
            self.Object.GroundImage)
        self.groundTexture.model = coin.SoMultiTextureImageElement.REPLACE

        groundTextureCoordinates = coin.SoTextureCoordinate2()
        groundTextureCoordinates.point.set1Value(0, 0, 0)
        groundTextureCoordinates.point.set1Value(1, 1, 0)
        groundTextureCoordinates.point.set1Value(2, 1, 1)
        groundTextureCoordinates.point.set1Value(3, 0, 1)

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)

        groundNode.addChild(self.groundCoordinates)
        groundNode.addChild(groundTextureCoordinates)
        groundNode.addChild(self.groundTexture)
        groundNode.addChild(faceset)

        return groundNode

    def calculateCoordinateBounds(self, radius, length):
        lengthThirds = length / 3  # the panorama consists of 3 planes

        alpha = self.calculateAlpha(radius, lengthThirds)
        connectionPointX = math.sin(alpha) * radius
        connectionPointY = math.cos(alpha) * radius

        leftX = -connectionPointX
        middleX = -connectionPointY
        rightX = middleX + lengthThirds

        backY = connectionPointX
        middleY = connectionPointY
        frontY = middleY - lengthThirds

        return (leftX, middleX, rightX, backY, middleY, frontY)

    def updatePanoramaCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value
        height = self.Object.Height.Value

        panoramaCoordinates = self.panoramaCoordinates

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(
            radius, length)

        # left face of panorama
        panoramaCoordinates.point.set1Value(0, leftX, frontY, 0)
        panoramaCoordinates.point.set1Value(1, leftX, middleY, 0)
        panoramaCoordinates.point.set1Value(2, leftX, middleY, height)
        panoramaCoordinates.point.set1Value(3, leftX, frontY, height)

        # Center face of panorama
        panoramaCoordinates.point.set1Value(4, leftX, middleY, 0)
        panoramaCoordinates.point.set1Value(5, middleX, backY, 0)
        panoramaCoordinates.point.set1Value(6, middleX, backY, height)
        panoramaCoordinates.point.set1Value(7, leftX, middleY, height)

        # back face of panorama
        panoramaCoordinates.point.set1Value(8, middleX, backY, 0)
        panoramaCoordinates.point.set1Value(9, rightX, backY, 0)
        panoramaCoordinates.point.set1Value(10, rightX, backY, height)
        panoramaCoordinates.point.set1Value(11, middleX, backY, height)

    def updatePanoramaTextureCoordinates(self):
        panoramaType = self.Object.PanoramaType

        if panoramaType == PANORAMA_TYPE_THIRDS:
            self.updateThirdsPanoramaTextureCoordinates()
        elif panoramaType == PANORAMA_TYPE_360:
            self.update360PanoramaTextureCoordinates()
        else:
            raise ValueError('Unkown panorama type ' + panoramaType)

    def update360PanoramaTextureCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value
        singlePlaneLength = length / 3

        rotation = self.Object.Rotation.Value

        if rotation >= 0:
            rotation = rotation - 360

        rotation = rotation * -1

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(
            radius, length)

        displayAmount = 1 / 4
        # We want to display 1/4 of the panorama between negative x and positive y axis
        # So that north of panorama is positive y, south is negative y, east is positive x and west is negative x
        #
        # Default case is that the geometry start of geometry is exactly at the x asis and end is
        # exactly at the y axis
        # Then exactly 1 / 4 of the image is shown and every plane has 1 / 3 of the visilbe image

        startOffset = displayAmount
        secondOffset = displayAmount / 3
        thirdOffset = secondOffset
        endOffset = secondOffset

        if rightX > 0:
            # When the geometry overshoots the axis we have to display more of the image, so that the
            # north, south, east and west are still touching the axis
            # One fourth of the panorama image should be displayed between the axis
            # to the right and bottom we overshoot by rightX so subtract this
            oneFourthOfImageLength = length - rightX * 2
            overshootRatio = rightX / oneFourthOfImageLength

            # The length of the partial plane that is between the middle plane and the axis
            shortPlaneLength = middleX * -1

            # Ratios of the middle plane and the short planes between the axis
            middlePlaneRatio = singlePlaneLength / oneFourthOfImageLength * displayAmount
            shortPlaneRatio = shortPlaneLength / oneFourthOfImageLength * displayAmount

            # Ratio of the panorama outside of the axis
            displayAmountOvershootRatio = overshootRatio * displayAmount

            startOffset = displayAmount + displayAmountOvershootRatio
            secondOffset = displayAmountOvershootRatio + shortPlaneRatio
            thirdOffset = middlePlaneRatio
            endOffset = secondOffset
        elif rightX < 0:
            # When the geometry does not touch the axis we have to display less of the image, so that the
            # north, south, east and west are still touching the axis
            # One fourth of the panorama image should be displayed between the axis
            # but we don't touch the axis so we have to add the missing bits
            oneFourthOfImageLength = length + rightX * -2

            # as rightX is negative multiply with -1
            # overshootRatio = rightX / oneFourthOfImageLength * -1

            realDisplayAmount = (displayAmount * length) / \
                oneFourthOfImageLength
            realThirds = realDisplayAmount / 3
            missingRatio = (displayAmount - realDisplayAmount) / 2

            # We display less of the image at once. overshoot ratio is negative so this works
            startOffset = missingRatio + realDisplayAmount
            secondOffset = realThirds
            thirdOffset = realThirds
            endOffset = realThirds - missingRatio

        start = 0 - startOffset - (rotation / 360)
        second = start + secondOffset
        third = second + thirdOffset
        end = third + endOffset

        # # left face
        self.panoramaTextureCoordinates.point.set1Value(0, start, 0)
        self.panoramaTextureCoordinates.point.set1Value(1, second, 0)
        self.panoramaTextureCoordinates.point.set1Value(2, second, 1)
        self.panoramaTextureCoordinates.point.set1Value(3, start, 1)

        # # middle face
        self.panoramaTextureCoordinates.point.set1Value(4, second, 0)
        self.panoramaTextureCoordinates.point.set1Value(5, third, 0)
        self.panoramaTextureCoordinates.point.set1Value(6, third, 1)
        self.panoramaTextureCoordinates.point.set1Value(7, second, 1)

        # right face
        self.panoramaTextureCoordinates.point.set1Value(8, third, 0)
        self.panoramaTextureCoordinates.point.set1Value(9, end, 0)
        self.panoramaTextureCoordinates.point.set1Value(10, end, 1)
        self.panoramaTextureCoordinates.point.set1Value(11, third, 1)

    def updateThirdsPanoramaTextureCoordinates(self):
        oneThird = 1 / 3
        twoThirds = 2 * oneThird

        # left face
        self.panoramaTextureCoordinates.point.set1Value(0, 0, 0)
        self.panoramaTextureCoordinates.point.set1Value(1, oneThird, 0)
        self.panoramaTextureCoordinates.point.set1Value(2, oneThird, 1)
        self.panoramaTextureCoordinates.point.set1Value(3, 0, 1)

        self.panoramaTextureCoordinates.point.set1Value(4, oneThird, 0)
        self.panoramaTextureCoordinates.point.set1Value(5, twoThirds, 0)
        self.panoramaTextureCoordinates.point.set1Value(6, twoThirds, 1)
        self.panoramaTextureCoordinates.point.set1Value(7, oneThird, 1)

        self.panoramaTextureCoordinates.point.set1Value(8, twoThirds, 0)
        self.panoramaTextureCoordinates.point.set1Value(9, 1, 0)
        self.panoramaTextureCoordinates.point.set1Value(10, 1, 1)
        self.panoramaTextureCoordinates.point.set1Value(11, twoThirds, 1)

    def updateSkyCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value
        height = self.Object.Height.Value
        skyOverlap = self.Object.SkyOverlap.Value
        skyOffset = 1000  # sky is 1 meter behind the panorama

        skyCoordinates = self.skyCoordinates

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(
            radius + skyOffset, length + skyOffset)

        alpha = math.radians(45)
        a = leftX if leftX >= 0 else leftX * -1
        c = a / math.sin(alpha)
        topZOffset = a / math.tan(alpha)
        topZ = height + topZOffset

        self.fullSkyLength = skyOverlap + c

        # left face of sky
        skyCoordinates.point.set1Value(0, leftX, frontY, height - skyOverlap)
        skyCoordinates.point.set1Value(1, leftX, middleY, height - skyOverlap)
        skyCoordinates.point.set1Value(2, leftX, middleY, height)
        skyCoordinates.point.set1Value(3, leftX, frontY, height)

        # Center face of sky
        skyCoordinates.point.set1Value(4, leftX, middleY, height - skyOverlap)
        skyCoordinates.point.set1Value(5, middleX, backY, height - skyOverlap)
        skyCoordinates.point.set1Value(6, middleX, backY, height)
        skyCoordinates.point.set1Value(7, leftX, middleY, height)

        # back face of sky
        skyCoordinates.point.set1Value(8, middleX, backY, height - skyOverlap)
        skyCoordinates.point.set1Value(9, rightX, backY, height - skyOverlap)
        skyCoordinates.point.set1Value(10, rightX, backY, height)
        skyCoordinates.point.set1Value(11, middleX, backY, height)

        # left top face
        skyCoordinates.point.set1Value(12, leftX, frontY, height)
        skyCoordinates.point.set1Value(13, leftX, middleY, height)
        skyCoordinates.point.set1Value(14, 0, 0, topZ)
        skyCoordinates.point.set1Value(15, 0, frontY, topZ)

        # middle top face
        skyCoordinates.point.set1Value(16, leftX, middleY, height)
        skyCoordinates.point.set1Value(17, middleX, backY, height)
        skyCoordinates.point.set1Value(18, 0, 0, topZ)

        # back top face
        skyCoordinates.point.set1Value(19, middleX, backY, height)
        skyCoordinates.point.set1Value(20, rightX, backY, height)
        skyCoordinates.point.set1Value(21, rightX, 0, topZ)
        skyCoordinates.point.set1Value(22, 0, 0, topZ)

        self.updateSkyTextureCoordinates()

    def updateGroundCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value

        groundCoordinates = self.groundCoordinates

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(
            radius, length)

        groundCoordinates.point.set1Value(0, leftX, frontY, 0)
        groundCoordinates.point.set1Value(1, rightX, frontY, 0)
        groundCoordinates.point.set1Value(2, rightX, backY, 0)
        groundCoordinates.point.set1Value(3, leftX, backY, 0)

    def calculateAlpha(self, radius, lengthThirds):
        # lets calculate alpha1. Then we only have to subtract it from 135 degrees and have our final alpha

        halfLength = lengthThirds / 2
        alpha1 = math.acos(halfLength / radius)
        alpha = math.radians(135) - alpha1

        return alpha

    def updateSkyTextureCoordinates(self):
        textureOverlapRatio = self.calculateSkyOverlapRatio()

        oneThird = 1 / 3
        twoThirds = oneThird * 2

        # left face
        self.skyTextureCoordinates.point.set1Value(0, 0, 0)
        self.skyTextureCoordinates.point.set1Value(1, oneThird, 0)
        self.skyTextureCoordinates.point.set1Value(
            2, oneThird, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(3, 0, textureOverlapRatio)

        # middle face
        self.skyTextureCoordinates.point.set1Value(4, oneThird, 0)
        self.skyTextureCoordinates.point.set1Value(5, twoThirds, 0)
        self.skyTextureCoordinates.point.set1Value(
            6, twoThirds, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(
            7, oneThird, textureOverlapRatio)

        # back face
        self.skyTextureCoordinates.point.set1Value(8, twoThirds, 0)
        self.skyTextureCoordinates.point.set1Value(9, 1, 0)
        self.skyTextureCoordinates.point.set1Value(10, 1, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(
            11, twoThirds, textureOverlapRatio)

        # left top face
        self.skyTextureCoordinates.point.set1Value(12, 0, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(
            13, oneThird, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(14, 0.5, 1)
        self.skyTextureCoordinates.point.set1Value(15, 0, 1)

        # middle top face
        self.skyTextureCoordinates.point.set1Value(
            16, oneThird, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(
            17, twoThirds, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(18, 0.5, 1)

        # # back top face
        self.skyTextureCoordinates.point.set1Value(
            19, twoThirds, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(20, 1, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(21, 1, 1)
        self.skyTextureCoordinates.point.set1Value(22, 0.5, 1)

    def calculateSkyOverlapRatio(self):
        if self.Object.SkyOverlap.Value == 0:
            return 0

        return 1 / (self.fullSkyLength / self.Object.SkyOverlap.Value)

    def onChanged(self, vp, prop):
        pass

    def doubleClicked(self, vobj):
        pass

    def getDisplayModes(self, obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def updateData(self, fp, prop):
        if prop in GEOMETRY_COORDINATES:
            self.updatePanoramaCoordinates()
            self.updateSkyCoordinates()
            self.updateGroundCoordinates()
            self.updatePanoramaTextureCoordinates()
        elif prop == 'SkyOverlap':
            self.updateSkyCoordinates()
        elif prop == 'PanoramaType':
            self.updatePanoramaTextureCoordinates()
        elif prop in TRANSFORM_PARAMETERS:
            self.updateTransformNode()
            self.updatePanoramaTextureCoordinates()
        elif prop == 'PanoramaImage':
            self.panoramaTexture.filename = py2_utils.textureFileString(
                self.Object.PanoramaImage)
            self.updateNodeVisibility()
        elif prop == 'SkyImage':
            self.skyTexture.filename = py2_utils.textureFileString(
                self.Object.SkyImage)
            self.updateNodeVisibility()
        elif prop == 'GroundImage':
            self.groundTexture.filename = py2_utils.textureFileString(
                self.Object.GroundImage)
            self.updateNodeVisibility()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def createEnvironmentConfig():
    environmentConfigObject = FreeCAD.ActiveDocument.addObject(
        "App::FeaturePython", "EnvironmentConfig")
    environmentConfig = EnvironmentConfig(environmentConfigObject)
    ViewProviderEnvironmentConfig(environmentConfigObject.ViewObject)

    return environmentConfigObject


if __name__ == "__main__":

    def createThirdsPanorama():
        environmentConfigObject = createEnvironmentConfig()
        environmentConfigObject.PanoramaImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/Panorama_wood_transparency.png'
        environmentConfigObject.SkyImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/sky.jpg'
        environmentConfigObject.GroundImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/grass.jpg'

    def create360Panorama():
        environmentConfigObject = createEnvironmentConfig()
        environmentConfigObject.PanoramaImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/360/360.png'
        environmentConfigObject.SkyImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/sky.jpg'
        environmentConfigObject.GroundImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/grass.jpg'
        environmentConfigObject.PanoramaType = PANORAMA_TYPE_360
        environmentConfigObject.SkyOverlap = 5000
        environmentConfigObject.Height = 10000
        environmentConfigObject.Length = 45000
        environmentConfigObject.Radius = 30000

    # createThirdsPanorama()
    create360Panorama()
