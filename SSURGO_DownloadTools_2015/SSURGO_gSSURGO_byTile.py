# SSURGO_gSSURGO_byTile.py
#
# Steve Peaslee, August 02, 2011
#
# Purpose: drive the SDM_Export_GDB.py script by looping through Tiles
#
# input selection layer must have user-specified tile attribute and CONUS flag to
# allow OCONUS areas to use a different output projection.
#
# Tile polygons use Select by Attribute (user-specified field and CONUS attributes)
# SSA polygons use Select by Location (intersect with tile polygons)
#
# 01-30-2012 - Revising to work with any polygon tile and a user specified
# attribute column. The ArcTool validator provides a method to get a unique
# list of attribute values and presents those to the user for
#
# 02-15-2012 Ported back to ArcGIS 9.3.1
#
# 07-02-2012 Fixed Jennifer's problem with use of featureclass for input Soil Survey Boundaries.
#
# 11-13-2012 Moved to arcpy
#
# 01-08-2014
#
# 2014-09-27

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    # Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
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
def CheckWSS(missingList):
    # If some of the selected soil survey downloads are not available in the download
    # folder, confirm with Soil Data Access service to make sure that WSS does not have them.
    # This could be problematic considering WSS problems as of December 2013 with zero-byte
    # zip files, etc.
    #
    # This should use SASTATUSMAP table instead of SACATALOG
    # Add 'AND SAPUBSTATUSCODE = 2' for finding spatial only
    import time, datetime, httplib, urllib2
    import xml.etree.cElementTree as ET

    missingAS = list()

    for subFolder in missingList:
        missingAS.append(subFolder[-5:].upper())

    missingQuery = "'" + "','".join(missingAS) + "'"

    try:
        sQuery = "SELECT AREASYMBOL FROM SASTATUSMAP WHERE AREASYMBOL IN (" + missingQuery + ") AND SAPUBSTATUSCODE = 2"

        # Send XML query to SDM Access service
        #
        sXML = """<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <RunQuery xmlns="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
          <Query>""" + sQuery + """</Query>
        </RunQuery>
      </soap12:Body>
    </soap12:Envelope>"""

        dHeaders = dict()
        dHeaders["Host"] = "sdmdataaccess.nrcs.usda.gov"
        dHeaders["Content-Type"] = "text/xml; charset=utf-8"
        dHeaders["SOAPAction"] = "http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx/RunQuery"
        dHeaders["Content-Length"] = len(sXML)
        sURL = "SDMDataAccess.nrcs.usda.gov"

        # Create SDM connection to service using HTTP
        conn = httplib.HTTPConnection(sURL, 80)

        # Send request in XML-Soap
        conn.request("POST", "/Tabular/SDMTabularService.asmx", sXML, dHeaders)

        # Get back XML response
        response = conn.getresponse()
        xmlString = response.read()

        # Close connection to SDM
        conn.close()

        # Convert XML to tree format
        tree = ET.fromstring(xmlString)

        iCnt = 0
        # Create empty value list
        valList = list()

        # Iterate through XML tree, finding required elements...
        for rec in tree.iter():

            if rec.tag == "AREASYMBOL":
                # get the YYYYMMDD part of the datetime string
                # then reformat to match SQL query
                a = rec.text
                valList.append(a)

        reallyMissing = list()

        for areaSym in missingAS:
            if areaSym in valList:
                # According to Soil Data Access, this survey is available for download, user needs to
                # download all missing surveys from Web Soil Survey and then rerun this tool
                reallyMissing.append(areaSym)

        if len(reallyMissing) > 0:
            PrintMsg("These missing surveys are available for download from Web Soil Survey: " + ", ".join(reallyMissing), 2)
            return False

        else:
            PrintMsg("Problem confirming missing surveys from download folder", 2)
            return False

    except:
        errorMsg()
        return False

## ===================================================================================
## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import sys, string, os, locale, traceback, arcpy
from arcpy import env

# Create the Geoprocessor object
try:

    ssaFC = arcpy.GetParameterAsText(0)            # input Survey Area layer containing AREASYMBOL (featurelayer)
    tileFC = arcpy.GetParameterAsText(1)           # input polygon layer containing tile value and CONUS attribute
    tileField = arcpy.GetParameter(2)              # featureclass column that contains the tiling attribute (MO, MLRASYM, AREASYMBOL, etc)
    tileList = arcpy.GetParameterAsText(3)         # list of tile values to process (string or long, derived from tileField)
    tileName = arcpy.GetParameterAsText(4)         # string used to identify type of tile (MO, MLRA, SSA, etc) used in geodatabase name
    inputFolder = arcpy.GetParameter(5)            # input folder containing SSURGO downloads
    outputFolder = arcpy.GetParameterAsText(6)     # output folder to contain new geodatabases (system folder)
    #bExportLayers = arcpy.GetParameter(7)         # export SSURGO featureclasses (boolean)
    theAOI = arcpy.GetParameter(7)                 # geographic region for output GDB. Used to determine coordinate system.
    useTextFiles = arcpy.GetParameter(8)           # Unchecked: import tabular data from Access database. Checked: import text files

    # import python script that actually exports the SSURGO
    #import SDM_Export_GDB10
    import SSURGO_Convert_to_Geodatabase

    # Set workspace environment to the folder containing the SSURGO downloads
    # Escape back-slashes in path
    inputFolder = str(inputFolder).encode('string-escape')

    # Make sure SSA layer exists. If connection is lost, it may still show up in ArcMap TOC
    if not arcpy.Exists(ssaFC):
        err = "Input selection layer missing"
        raise MyError, err

    else:
        sDesc = arcpy.Describe(ssaFC)

    saDesc = arcpy.Describe(ssaFC)
    saDataType = saDesc.dataSetType

    if saDataType.upper() == "FEATURECLASS":
        ssaLayer = "SSA Layer"
        arcpy.MakeFeatureLayer_management(ssaFC, ssaLayer)

    tileDesc = arcpy.Describe(tileFC)
    tileDataType = tileDesc.dataSetType

    if tileDataType.upper() == "FEATURECLASS":
        tileLayer = "Tile Layer"
        arcpy.MakeFeatureLayer_management(tileFC, tileLayer)

    else:
        tileLayer = tileFC

    tileList = tileList.split(";")

    # Get tile field information
    #PrintMsg(" \nGetting input field information", 1)
    tileField = arcpy.ListFields(tileLayer, "*" + str(tileField))[0]
    fldType = tileField.type.upper()
    fldName = tileField.name
    exportList = list() # list of successfully exported gSSURGO databases

    for theTile in tileList:

        PrintMsg(" \n" + (50 * "*"), 0)
        PrintMsg("Processing " + tileName + ": " + str(theTile), 0)
        #PrintMsg(" \nDataType for input field (" + fldName +  "): " + fldType, 0)

        if fldType != "STRING":
            theTile = int(theTile)
            sQuery = arcpy.AddFieldDelimiters(tileLayer, fldName) + " = " + str(theTile)

        else:
            sQuery = arcpy.AddFieldDelimiters(tileLayer, fldName) + " = '" + str(theTile) + "'"

        # Select tile polygon by the current value from the choice list
        arcpy.SelectLayerByAttribute_management(tileLayer, "NEW_SELECTION", sQuery)
        iCnt = int(arcpy.GetCount_management(tileLayer).getOutput(0))

        if iCnt == 0:
            # bailout
            err = "Attribute selection failed for " + sQuery
            raise MyError, err

        #PrintMsg(" \n\tTile layer has " + str(iCnt) + " polygons selected", 0)

        # Select Survey Area polygons that intersect this tile (CONUS)
        # The operation was attempted on an empty geometry. Occurring in every third tile with 10.1
        arcpy.SelectLayerByAttribute_management(ssaLayer, "CLEAR_SELECTION")
        arcpy.SelectLayerByLocation_management(ssaLayer, "INTERSECT", tileLayer, "", "NEW_SELECTION")
        iCnt = int(arcpy.GetCount_management(ssaLayer).getOutput(0))

        if iCnt == 0:
            # bailout
            err = "Select layer by location failed"
            raise MyError, err

        else:
            #PrintMsg(" \n\tSelected " + str(iCnt) + " survey area polygons in " + ssaLayer, 1)
            # get list of unique areasymbol values from survey boundary layer (param 1)
            fieldList = ["AREASYMBOL"]
            asList = [("soil_" + row[0].encode('ascii').lower()) for row in arcpy.da.SearchCursor(ssaLayer, fieldList)]
            asSet = set(asList)   # remove duplicate attribute values
            surveyList = list(sorted(asSet))

            # Before proceeding further, confirm the existence of each SSURGO download
            # Important note. You cannot use os.path.join with inputFolder and subFolder without escaping.
            missingList = list()
            #PrintMsg(" \nConfirming existence of SSURGO downloads in: " + inputFolder, 0)

            for subFolder in surveyList:
                if not arcpy.Exists(os.path.join(inputFolder, subFolder)):
                    #PrintMsg("\t" + os.path.join(env.workspace, inputFolder), 0)
                    missingList.append(subFolder)

            if len(missingList) > 0:

                if CheckWSS(missingList):
                    PrintMsg("\tNot all surveys were available in Web Soil Survey", 1)

                else:
                    err = ""
                    raise MyError, err

        # Create output Geodatabase for tile
        if fldType != "STRING":
            # if tile value is numeric, insert leading zeros
            if theTile < 10:
                theDB = "gSSURGO_" + tileName + "_0" + str(theTile) + ".gdb"

            else:
                theDB = "gSSURGO_" + tileName  + "_" + str(theTile) + ".gdb"

        else:
            theDB = "gSSURGO_" + tileName + "_" + theTile + ".gdb"

        outputWS = os.path.join(outputFolder, theDB)

        if arcpy.Exists(outputWS):
            arcpy.Delete_management(outputWS)

        # Call SDM Export script
        aliasName = tileName + " " + str(theTile)
        bExported = SSURGO_Convert_to_Geodatabase.gSSURGO(inputFolder, surveyList, outputWS, theAOI, (aliasName, aliasName), useTextFiles)

        if bExported:
            exportList.append(os.path.basename(outputWS))

        else:
            err = "gSSURGO export failed for " + fldName + " value: " + str(theTile)
            raise MyError, err

        # end of for loop

    arcpy.RefreshCatalog(outputFolder)
    del outputFolder

    PrintMsg(" \nFinished creating the following gSSURGO databases: " + ", ".join(exportList) + " \n ", 0)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()
