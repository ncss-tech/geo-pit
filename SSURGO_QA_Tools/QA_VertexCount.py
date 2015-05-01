# QA_VertexCount.py
#
# 05-29-2013
# Steve Peaslee USDA-NRCS, National Soil Survey Center
#
# 10-31-2013
# Input: Polygon layer
#
# Returns total vertice count for input layer
#

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                arcpy.AddMessage(string)
                print string

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                arcpy.AddMessage("    ")
                arcpy.AddError(string)

    except:
        pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
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
        PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return False

## ===================================================================================
def ProcessPolygons(theInputLayer, bUseSelected):
    # Process either the selected set or the entire featureclass into a single set of summary statistics
    # bUseSelected determines whether the featurelayer or featureclass gets processed

    try:

        # Describe input layer
        desc = arcpy.Describe(theInputLayer)
        theDataType = desc.dataType.lower()

        if theDataType == "featurelayer":
            theInputName = desc.nameString

        else:
            theInputName = desc.baseName

        theFC = desc.catalogPath
        featureType = desc.shapeType.lower()
        iVertCnt = 0
        PrintMsg(" \nProcessing input " + featureType + " " + theDataType.lower() + " '" + theInputName + "'", 0)
        iParts = 0

        if bUseSelected:
            # Process input (featurelayer?)
            # open cursor with exploded geometry
            PrintMsg("If selected set or query definition is present, only those features will be processed", 0)

            with arcpy.da.SearchCursor(theInputLayer, ["OID@","SHAPE@"], "","",False) as theCursor:
                for fid, feat in theCursor:

                    if not feat is None:
                        iVertCnt += feat.pointCount
                        iParts += feat.partCount

                    else:
                        PrintMsg("Empty geometry found for polygon #" + str(fid) + " \n ", 2)
                        return -1


            PrintMsg(" \n" + Number_Format(iVertCnt, 0, True) + " vertices in featurelayer \n " , 0)

        else:
            # Process all polygons using the source featureclass regardless of input datatype.
            # Don't really see a performance difference, but this way all features get counted.
            # Using 'exploded' geometry option for cursor

            with arcpy.da.SearchCursor(theFC, ["OID@","SHAPE@"], "","",False) as theCursor:
                for fid, feat in theCursor:

                    if not feat is None:
                      iVertCnt += feat.pointCount
                      iParts += feat.partCount

                    else:
                        raise MyError, "NULL geometry for polygon #" + str(fid)

            PrintMsg(" \n" + Number_Format(iVertCnt, 0, True) + " vertices present in the entire " + theDataType.lower() + " \n ", 0)


        return iVertCnt


    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        return -1

    except:
        errorMsg()
        return -1

## ===================================================================================
## ===================================================================================
## MAIN
## ===================================================================================

import sys, string, os, arcpy, locale, traceback, time, math, operator

try:
    # Set formatting for numbers
    locale.setlocale(locale.LC_ALL, "")

    # Target FeatureLayer or Featureclass
    theInputLayer = arcpy.GetParameter(0)

    # Use all features or selected set? Boolean.
    bUseSelected = arcpy.GetParameter(1)

    iVertCnt = ProcessPolygons(theInputLayer, bUseSelected)

except:
    print "Error in Setup function"
    errorMsg()


