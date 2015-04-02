# SSURGO_MergeSoilShapefiles.py
#
# Purpose: allow batch appending of SSURGO soil polygon shapefiles into a single shapefile
# Requires input dataset structures to follow the NRCS standard for Geospatial data...
#
# There currently is no method for handling inputs with more than one coordinate system,
# especially if there is more than one horizontal datum involved.
#
# Merge order is based upon sorted extent coordinates
#
# Test version 09-30-2013
# Beta version 10-31-2013
# 11-22-2013
# 01-08-2014
# 2014-09-27

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + " \n"
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                arcpy.AddMessage(string)

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                arcpy.AddError(" \n" + string)

    except:
        pass

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    try:
    # Format a number according to locality and given places
        #locale.setlocale(locale.LC_ALL, "")
        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)

        else:
            theNumber = locale.format("%.*f", (places, num), False)
        return theNumber

    except:
        errorMsg()
        #PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return "???"

## ===================================================================================

# Import system modules
import arcpy, sys, string, os, traceback, locale

# Create the Geoprocessor object
from arcpy import env

try:
    inputFolder = arcpy.GetParameterAsText(0)  # location of SSURGO datasets containing spatial folders
    surveyList = arcpy.GetParameter(1)            # list of folder names to be proccessed
    outputShape = arcpy.GetParameterAsText(2)  # Name of final output shapefile

    if len(surveyList) < 2:
        raise MyError, "At least 2 input surveys are required"

    # check outputShape filename
    fName, fExt = os.path.splitext(outputShape)

    if fExt == "":
        outputShape += ".shp"

    elif fExt != ".shp":
        outputShape = fName + ".shp"

    if arcpy.Exists(os.path.join(inputFolder, outputShape)):
        arcpy.Delete_management(os.path.join(inputFolder, outputShape))

    dList = dict()
    extentList = list()
    shpList = list()

    # process each selected soil survey
    PrintMsg(" \nValidating " + str(len(surveyList)) + " selected surveys...", 0)

    for subFolder in surveyList:
        # confirm shapefile existence for each survey and append to input list
        shpName = "soilmu_a_" + subFolder[-5:] + ".shp"
        shpPath = os.path.join( os.path.join( inputFolder, os.path.join( subFolder, "spatial")), shpName)

        if arcpy.Exists(shpPath):
            desc = arcpy.Describe(shpPath)
            shpExtent = desc.extent
            XCntr = ( shpExtent.XMin + shpExtent.XMax) / 2.0
            YCntr = ( shpExtent.YMin + shpExtent.YMax) / 2.0
            sortKey = XCntr * YCntr
            PrintMsg("\tAppending " + shpName + " to list", 0)
            dList[sortKey] = shpPath
            extentList.append(sortKey)

        else:
            raise MyError, "Error. Missing soil polygon shapefile: " + shpName

    # Sort shapefiles by extent so that the drawing order is a little more effecient
    extentList.sort()

    for sortKey in extentList:
        shpList.append(dList[sortKey])

    PrintMsg(" \nMerging listed shapefiles to create new shapefile: " + outputShape + " \n ", 0)
    arcpy.Merge_management(shpList, os.path.join(inputFolder, outputShape))
    PrintMsg("Output folder:  " + inputFolder + "  \n ", 0)

except MyError, e:
    PrintMsg(str(e), 2)

except:
    errorMsg()
