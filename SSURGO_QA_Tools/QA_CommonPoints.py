# QA_CommonPoints.py
#
# ArcGIS 10.1
#
# Steve Peaslee, USDA-NRCS, National Soil Survey Center
#
# Original code: 05-09-2013
# Last modified: 10-31-2013
#
# Polygon tool used to identify locations where polygons with the same attribute intersect.
# By definition this will include polygons that self intersect by looping around.
#
class MyError(Exception):
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
                arcpy.AddMessage("    ")
                arcpy.AddError(string)

    except:
        pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    # Format a number according to locality and given places
    import locale

    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') #use locale.format for commafication

    except locale.Error:
        locale.setlocale(locale.LC_ALL, '') #set to default locale (works on windows)

    try:

        import locale


        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)

        else:
            theNumber = locale.format("%.*f", (places, num), False)

        return theNumber

    except:
        PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return False

## ===================================================================================
def MakeOutLayer(inLayer, sr, inField1, inField2, fldLength):
    # Create points shapefile containing error locations
    #
    try:
        # Set workspace to that of the input polygon featureclass
        desc = arcpy.Describe(inLayer)
        theCatalogPath = desc.catalogPath
        loc = os.path.dirname(theCatalogPath)
        desc = arcpy.Describe(loc)
        dt = desc.dataType.upper()

        if dt == "WORKSPACE":
            env.workspace = loc
            ext = ""

        elif dt == "FEATUREDATASET":
            env.workspace = os.path.dirname(loc)
            ext = ""

        elif dt == "FOLDER":
            env.workspace = loc
            ext = ".shp"

        else:
            PrintMsg(" \nError. " + loc + " is a " + dt + " datatype", 2)
            return ""

        # Use input field names to create output featureclass name
        if ext == ".dbf":
            newFld1 = arcpy.ParseFieldName(inField1).split(",")[3].strip()[0:10]

        else:
            newFld1 = arcpy.ParseFieldName(inField1).split(",")[3].strip()

        if inField2 != "":
            if ext == ".dbf":
                newFld2 = arcpy.ParseFieldName(inField2).split(",")[3].strip()[0:10]

            else:
                newFld2 = arcpy.ParseFieldName(inField2).split(",")[3].strip()

            outLayer = "QA_Common_Points_" + newFld1 + "_" + newFld2 + ext

        else:
            outLayer = "QA_Common_Points_" + newFld1 + ext

        # clean up previous runs
        if arcpy.Exists(outLayer):
            arcpy.Delete_management(outLayer)

        PrintMsg(" \nOutput featureclass: " + outLayer + " in " + env.workspace + " " + dt.lower(), 0)

        # Create output point featureclass
        arcpy.CreateFeatureclass_management (env.workspace, outLayer, "POINT", "", "DISABLED", "DISABLED", sr)

        if not arcpy.Exists(os.path.join(env.workspace, outLayer)):
            return "",""

        else:
            # create the appropriate attribute field in the common points featureclass
            #
            # begin by getting all of the original field properties
            theField = arcpy.ListFields(theCatalogPath, newFld1 + "*")[0] # get the input polygon field object
            fieldAlias = theField.aliasName
            fieldType = "TEXT"
            fieldScale = ""
            fieldPrecision = ""
            arcpy.AddField_management(os.path.join(env.workspace, outLayer), newFld1, fieldType, fieldPrecision, fieldScale, fldLength, fieldAlias)

            # Add new field to track status of each point
            arcpy.AddField_management(os.path.join(env.workspace, outLayer), "Status", "TEXT", "", "", 10, "Status")

            return outLayer, newFld1

    except:
        errorMsg()
        return "",""

## ===================================================================================
## main
##

import os, sys, traceback, collections
import arcpy
from arcpy import env

try:

    # single polygon featurelayer as input parameter
    inLayer = arcpy.GetParameterAsText(0)

    # attribute column used in selection
    inField1 = arcpy.GetParameterAsText(1)

    # secondary attribute column (usually AREASYMBOL)
    inField2 = arcpy.GetParameterAsText(2)
    #inField2 = "AREASYMBOL"

    # single point featurelayer as output parameter
    #xx = arcpy.GetParameter(2)

    # open da searchcursor on featurelayer
    flds = ["OID@","SHAPE@"]
    #allDupsList = []
    dDups = dict()

    iSelection = int(arcpy.GetCount_management(inLayer).getOutput(0))

    # define output featureclass
    desc = arcpy.Describe(inLayer)
    dt = desc.dataType.upper()
    sr = desc.spatialReference
    env.workspace = os.path.dirname(desc.catalogPath)

    # input layer needs to be a featurelayer. If it is a featureclass, do a switch.
    if dt == "FEATURECLASS":
        # swap out the input featureclass for a new featurelayer based upon that featureclass
        inLayer = desc.name + " Layer"
        PrintMsg(" \nCreating new featurelayer named: " + inLayer, 0)
        inputFC = desc.catalogPath
        arcpy.MakeFeatureLayer_management(inputFC, inLayer)

    elif dt == "FEATURELAYER":
        inputName = desc.Name
        inputFC = desc.FeatureClass.catalogPath

    # Use a searchcursor to create a list of unique values for the specified input field or column
    PrintMsg(" \nGetting unique values for " + inField1 + "...", 0)

    # get the first input field object
    #chkFields = arcpy.ListFields(inputFC)
    chkFields = arcpy.ListFields(inLayer)

    for fld in chkFields:
        fldLength = 0

        if fld.name.upper() == inField1.upper():
            fld1Name = fld.name
            fld1NameU = fld.baseName
            fldLength = fld.length
            #PrintMsg("Getting length for " + fld1Name + " length: " + str(fldLength), 0)


    # get the optional second input field object
    if inField2 != "":
        for fld in chkFields:

            if fld.name.upper() == inField2.upper():
                fld2Name = fld.name
                fld2NameU = fld.baseName
                fldLength += fld.length
                #PrintMsg("Getting total length for both fields " + fld2Name + ", " + fld1Name + " length: " + str(fldLength), 0)

    else:
        fld2Name = ""
        fld2NameU = ""

    # Create list of values
    fldList = [fld1Name]

    if inField2 == "":
        valList = [row[0] for row in arcpy.da.SearchCursor(inLayer, fldList)]

    else:
        fldList = [fld2Name, fld1Name]
        valList = [row[0] + ":" + row[1] for row in arcpy.da.SearchCursor(inLayer, fldList)]


    valUnique = set(valList)   # remove duplicate attribute values
    valList = list(valUnique)
    valList.sort()    # sort the list to control the processing order, this is not really necessary
    PrintMsg(" \nFound " + Number_Format(len(valList), 0, True) + " unique values", 0)
    iVals = len(valList)

    # Process records using a series of search cursors while tracking progress
    arcpy.SetProgressorLabel("Reading polygon geometry...")
    arcpy.SetProgressor("step", "Reading polygon geometry...",  0, iVals, 1)
    PrintMsg(" \nProcessing " + Number_Format(iSelection, 0, True) + " polygons in '" + inLayer + "'", 0)

    iCnt = 0

    # Create a selection on the input featurelayer for each unique value
    for val in valList:
        #arcpy.SetProgressorLabel("Reading polygon geometry for '" + str(val) + "'...")

        if inField2 != "":
            val1, val2 = val.split(":")
            theSQL = arcpy.AddFieldDelimiters(inLayer, inField1) + " = '" + val2 + "' AND " + arcpy.AddFieldDelimiters(inLayer, inField2) + " = '" + val1 + "'" # create SQL for each value

        else:
            theSQL = arcpy.AddFieldDelimiters(inLayer, inField1) + " = '" + val + "'" # create SQL for each value


        pntList = []  # clear point list for the new value

        with arcpy.da.SearchCursor(inLayer, flds, theSQL) as cursor:
            for row in cursor:

                for part in row[1]:
                    # look for duplicate points within each polygon part
                    #
                    bRing = True  # helps prevent from-node from being counted as a duplicate of to-node

                    for pnt in part:
                        if pnt:
                            if not bRing:
                                # add vertice or to-node coordinates to list
                                pntList.append((pnt.X,pnt.Y))

                            bRing = False

                        else:
                            # interior ring encountered
                            ring = pntList.pop()  # removes first node from list
                            bRing = True  # prevents island from-node from being identified as a duplicate of the to-node

            # get duplicate coordinate pairs within the list of vertices for the current attribute value
            dupList = [x for x, y in collections.Counter(pntList).items() if y > 1]

            if len(dupList) > 0:
                # if duplicate vertices are found in this polygon, add the list to the dictionary.
                # dictionary key is the attribute value
                dDups[val] = dupList
                iCnt += len(dupList)   # keep track of the total number of common-points

                if val == " ":
                    PrintMsg(" \n\tFound common points for " + inField1 + ":  <NULL>", 0)

                else:
                    PrintMsg(" \n\tFound common points for " + inField1 + ":  '" + val + "'", 0)

                arcpy.SetProgressorLabel("Reading polygon geometry ( flagged " + Number_Format(iCnt) + " locations )...")

        arcpy.SetProgressorPosition()

    arcpy.ResetProgressor()  # completely finished reading all polygon geometry

    # if common-points were found, create a point shapefile containing the attribute value for each point
    #
    if len(dDups) > 0:
        PrintMsg("Total of " + Number_Format(iCnt, 0, True) + " 'common points' found in " + inLayer, 2)

        # create output points layer to store common-point locations
        outLayer, newFld1 =  MakeOutLayer(inLayer, sr, inField1, inField2, fldLength)

        if outLayer == "":
            raise MyError, "Failed to create common-points layer"

        # Process records using cursor, track progress
        arcpy.SetProgressorLabel("Opening output featureclass...")
        arcpy.SetProgressor("step", "Writing point geometry..." , 0, iCnt, 1)

        # open new output points featureclass and add common point locations
        with arcpy.da.InsertCursor(outLayer, ["SHAPE@XY", newFld1]) as cursor:
            # for each value that has a reported common-point, get the list of coordinates from
            # the dDups dictionary and write to the output Common_Points featureclass
            for val in dDups.keys():

                for coords in dDups[val]:
                    cursor.insertRow([coords, val]) # write both geometry and the single attribute value to the output layer
                    arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel("Process complete...")

        try:
            # if this is ArcMap and if geoprocessing setting automatically adds layer, then
            # import symbology from layer fill
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layerPath = os.path.dirname(sys.argv[0])
            layerFile = os.path.join(layerPath,"GreenDot.lyr")

            if fld2Name != "":
                outLayerName = "QA Common Points (" + fld2NameU.title() + ":" + fld1NameU.title() + ")"

            else:
                outLayerName = "QA Common Points (" + fld1NameU.title() + ")"

            arcpy.env.addOutputsToMap = True
            arcpy.MakeFeatureLayer_management(outLayer, outLayerName)
            arcpy.ApplySymbologyFromLayer_management (outLayerName, layerFile)
            arcpy.SetParameter(3, outLayerName)
            PrintMsg(" \nAdded " + outLayerName + " to ArcMap TOC", 0)

        except:
            pass

        PrintMsg(" \n ", 0)

    else:
        PrintMsg(" \nNo common-point issues found with '" + inLayer + "' \n ", 0)

except MyError, e:
    # Example: raise MyError, "this is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()

