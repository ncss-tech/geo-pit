# SSURGO_gSSURGO_byState.py
#
# ArcGIS 10.1
#
# Steve Peaslee, August 02, 2011
#
# Revising code to work with ArcGIS 10.1 and new SSURGO Download tools
# Designed to drive "SSURGO_MergeSoilShapefilesbyAreasymbol_GDB.py"
#
# SDM Access query for getting overlap areas (that have spatial data) by state:
# SELECT legend.areasymbol FROM (legend INNER JOIN laoverlap ON legend.lkey = laoverlap.lkey)
# INNER JOIN sastatusmap ON legend.areasymbol = sastatusmap.areasymbol
# WHERE (((laoverlap.areatypename)='State or Territory') AND ((laoverlap.areaname) Like '<statename>%') AND
# ((legend.areatypename)='Non-MLRA Soil Survey Area') AND ((sastatusmap.sapubstatuscode) = 2) );
#
# 2014-01-08
# 2014-01-15  Noticed issue with Pacific Basin surveys in the legendAreaOverlap table. Someone
#             removed the [State or Territory] = 'Pacific Basin' entries so this tool will no
#             longer work for PAC Basin.
# 2014-09-27  sQuery modified to create a geodatabase with ALL surveys including the NOTCOM-only. Implemented
#             with the FY2015 production.

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
        errorMsg()
        #PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return "???"

## ===================================================================================
def StateNames():
    # Create dictionary object containing list of state abbreviations and their names that
    # will be used to name the file geodatabase.
    # For some areas such as Puerto Rico, U.S. Virgin Islands, Pacific Islands Area the
    # abbrevation is

    # NEED TO UPDATE THIS FUNCTION TO USE THE LAOVERLAP TABLE AREANAME. AREASYMBOL IS STATE ABBREV

    try:
        stDict = dict()
        stDict["Alabama"] = "AL"
        stDict["Alaska"] = "AK"
        stDict["American Samoa"] = "AS"
        stDict["Arizona"] =  "AZ"
        stDict["Arkansas"] = "AR"
        stDict["California"] = "CA"
        stDict["Colorado"] = "CO"
        stDict["Connecticut"] = "CT"
        stDict["District of Columbia"] = "DC"
        stDict["Delaware"] = "DE"
        stDict["Florida"] = "FL"
        stDict["Georgia"] = "GA"
        stDict["Hawaii"] = "HI"
        stDict["Idaho"] = "ID"
        stDict["Illinois"] = "IL"
        stDict["Indiana"] = "IN"
        stDict["Iowa"] = "IA"
        stDict["Kansas"] = "KS"
        stDict["Kentucky"] = "KY"
        stDict["Louisiana"] = "LA"
        stDict["Maine"] = "ME"
        stDict["Maryland"] = "MD"
        stDict["Massachusetts"] = "MA"
        stDict["Michigan"] = "MI"
        stDict["Minnesota"] = "MN"
        stDict["Mississippi"] = "MS"
        stDict["Missouri"] = "MO"
        stDict["Montana"] = "MT"
        stDict["Nebraska"] = "NE"
        stDict["Nevada"] = "NV"
        stDict["New Hampshire"] = "NH"
        stDict["New Jersey"] = "NJ"
        stDict["New Mexico"] = "NM"
        stDict["New York"] = "NY"
        stDict["North Carolina"] = "NC"
        stDict["North Dakota"] = "ND"
        stDict["Ohio"] = "OH"
        stDict["Oklahoma"] = "OK"
        stDict["Oregon"] = "OR"
        stDict["Pacific Basin"] = "PB"
        stDict["Pennsylvania"] = "PA"
        stDict["Puerto Rico and U.S. Virgin Islands"] = "PRUSVI"
        stDict["Rhode Island"] = "RI"
        stDict["South Carolina"] = "SC"
        stDict["South Dakota"] = "SD"
        stDict["Tennessee"] = "TN"
        stDict["Texas"] = "TX"
        stDict["Utah"] = "UT"
        stDict["Vermont"] = "VT"
        stDict["Virginia"] = "VA"
        stDict["Washington"] = "WA"
        stDict["West Virginia"] = "WV"
        stDict["Wisconsin"] = "WI"
        stDict["Wyoming"] = "WY"
        return stDict

    except:
        PrintMsg("\tFailed to create list of state abbreviations (CreateStateList)", 2)
        return None

## ===================================================================================
def StateAOI():
    # Create dictionary object containing list of state abbreviations and their geographic regions

    try:
        # "Lower 48 States":
        # "Alaska":
        # "Hawaii":
        # "American Samoa":
        # "Puerto Rico and U.S. Virgin Islands"
        # "Pacific Islands Area"
        #
        dAOI = dict()
        dAOI['Alabama'] = 'Lower 48 States'
        dAOI['Alaska'] = 'Alaska'
        dAOI['American Samoa'] = 'Hawaii'
        dAOI['Arizona'] = 'Lower 48 States'
        dAOI['Arkansas'] = 'Lower 48 States'
        dAOI['California'] = 'Lower 48 States'
        dAOI['Colorado'] = 'Lower 48 States'
        dAOI['Connecticut'] = 'Lower 48 States'
        dAOI['Delaware'] = 'Lower 48 States'
        dAOI['District of Columbia'] = 'Lower 48 States'
        dAOI['Florida'] = 'Lower 48 States'
        dAOI['Georgia'] = 'Lower 48 States'
        dAOI['Hawaii'] = 'Hawaii'
        dAOI['Idaho'] = 'Lower 48 States'
        dAOI['Illinois'] = 'Lower 48 States'
        dAOI['Indiana'] = 'Lower 48 States'
        dAOI['Iowa'] = 'Lower 48 States'
        dAOI['Kansas'] = 'Lower 48 States'
        dAOI['Kentucky'] = 'Lower 48 States'
        dAOI['Louisiana'] = 'Lower 48 States'
        dAOI['Maine'] = 'Lower 48 States'
        dAOI['Maryland'] = 'Lower 48 States'
        dAOI['Massachusetts'] = 'Lower 48 States'
        dAOI['Michigan'] = 'Lower 48 States'
        dAOI['Minnesota'] = 'Lower 48 States'
        dAOI['Mississippi'] = 'Lower 48 States'
        dAOI['Missouri'] = 'Lower 48 States'
        dAOI['Montana'] = 'Lower 48 States'
        dAOI['Nebraska'] = 'Lower 48 States'
        dAOI['Nevada'] = 'Lower 48 States'
        dAOI['New Hampshire'] = 'Lower 48 States'
        dAOI['New Jersey'] = 'Lower 48 States'
        dAOI['New Mexico'] = 'Lower 48 States'
        dAOI['New York'] = 'Lower 48 States'
        dAOI['North Carolina'] = 'Lower 48 States'
        dAOI['North Dakota'] = 'Lower 48 States'
        dAOI['Ohio'] = 'Lower 48 States'
        dAOI['Oklahoma'] = 'Lower 48 States'
        dAOI['Oregon'] = 'Lower 48 States'
        dAOI['Pacific Basin'] = 'Pacific Islands Area'
        dAOI['Pennsylvania'] = 'Lower 48 States'
        dAOI['Puerto Rico and U.S. Virgin Islands'] = 'Lower 48 States'
        dAOI['Rhode Island'] = 'Lower 48 States'
        dAOI['South Carolina'] = 'Lower 48 States'
        dAOI['South Dakota'] = 'Lower 48 States'
        dAOI['Tennessee'] = 'Lower 48 States'
        dAOI['Texas'] = 'Lower 48 States'
        dAOI['Utah'] = 'Lower 48 States'
        dAOI['Vermont'] = 'Lower 48 States'
        dAOI['Virginia'] = 'Lower 48 States'
        dAOI['Washington'] = 'Lower 48 States'
        dAOI['West Virginia'] = 'Lower 48 States'
        dAOI['Wisconsin'] = 'Lower 48 States'
        dAOI['Wyoming'] = 'Lower 48 States'
        return dAOI

    except:
        PrintMsg("\tFailed to create list of state abbreviations (CreateStateList)", 2)
        return dAOI

## ===================================================================================
def GetFieldList(tbi_1):
    # Create field list for MakeQueryTable

    try:
        fldList = ""

        pFld = arcpy.ParseTableName(os.path.basename(tbi_1)).split(",")
        db = pFld[0].strip()
        dbo = pFld[1].strip()
        tbl = pFld[2].strip()
        fldList = ""  # intialize fields string for MakeQuery Table
        # Create list of fields for export
        #PrintMsg("\nGetting fields for " + theTbl, 0)
        flds = arcpy.ListFields(tbi_1) # 9.3

        for fld in flds:              # 9.3
            fldp = fld.name
            fldq = db + "." + dbo + "."  + tbl + "." + fldp

            if fld.type != "OID":
                #PrintMsg("\nGetting name for field " + fldp, 0)

                if fldList != "":
                    fldList = fldList + ";" + fldq + " " + fldp

                else:
                    fldList = fldq + " " + fldp

        #PrintMsg(" \nOutput Fields: " + fldList, 0)
        return fldList

    except:
        errorMsg()
        return ""

## ===================================================================================
def GetAreasymbols(attName, theTile):
    # Get list of areasymbol values from Soil Data Access laoverlap and legend tables
    #
    # NEW QUERY COMBINES StateName and Spatial Status. This needs to be used and then the check can be dropped.
    #
    # SELECT legend.areasymbol
    # FROM (legend INNER JOIN laoverlap ON legend.lkey = laoverlap.lkey) INNER JOIN sastatusmap ON legend.areasymbol = sastatusmap.areasymbol
    # WHERE (((laoverlap.areatypename)='State or Territory') AND ((laoverlap.areaname) Like 'Delaware%') AND ((legend.areatypename)='Non-MLRA Soil Survey Area') AND ((sastatusmap.sapubstatuscode) = 2) );

    import time, datetime, httplib, urllib2
    import xml.etree.cElementTree as ET

    try:

        # Create empty value list to contain the filtered list of areasymbol values
        valList = list()

        # Old query returned just survey areas with spatial data
        sQuery = "SELECT legend.areasymbol FROM (legend INNER JOIN laoverlap ON legend.lkey = laoverlap.lkey) " + \
        "INNER JOIN sastatusmap ON legend.areasymbol = sastatusmap.areasymbol " + \
        "WHERE (((laoverlap.areatypename)='State or Territory') AND ((laoverlap.areaname) Like '" + theTile + "%') AND " + \
        "((legend.areatypename)='Non-MLRA Soil Survey Area') AND ((sastatusmap.sapubstatuscode) = 2) );"

        # Now using this query to retrieve All surve areas including NOTCOM-only
        sQuery = "SELECT legend.areasymbol FROM (legend INNER JOIN laoverlap ON legend.lkey = laoverlap.lkey) " + \
        "INNER JOIN sastatusmap ON legend.areasymbol = sastatusmap.areasymbol " + \
        "WHERE (((laoverlap.areatypename)='State or Territory') AND ((laoverlap.areaname) Like '" + theTile + "%') AND " + \
        "((legend.areatypename)='Non-MLRA Soil Survey Area')) ;"

        #PrintMsg(" \n" + sQuery, 0)

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

        # Iterate through XML tree, finding required elements...
        for rec in tree.iter():

            if rec.tag == attName:
                # get the target attribute value
                val = str(rec.text)
                #PrintMsg("\tFound " + val, 0)
                valList.append(val)

        return valList

    except:
        errorMsg()
        return []

## ===================================================================================
def GetFolders(inputFolder, valList, bRequired, theTile):
    # get a list of all matching folders under the input folder, assuming 'soil_' naming convention

    try:
        env.workspace = inputFolder
        surveyList = list()
        folderList = arcpy.ListWorkspaces("soil_*", "Folder")
        missingList = list()

        # check each subfolder to make sure it is a valid SSURGO dataset
        # validation: has 'soil_' prefix and contains a spatial folder and a soilsmu_a shapefile
        # and matches one of the AREASYMBOL values in the legend table
        #PrintMsg(" \nLooking for these SSURGO datasets: " + ", ".join(valList), 0)

        for shpAS in valList:
            # this should be one of the target SSURGO dataset folder
            # add it to the choice list
            subFolder = "soil_" + shpAS.lower()
            shpName = "soilmu_a_" + shpAS + ".shp"
            shpPath = os.path.join( os.path.join( inputFolder, os.path.join(subFolder, "spatial")), shpName)

            if arcpy.Exists(shpPath):
                surveyList.append(os.path.basename(subFolder))

            else:
                # Missing soil polygon shapefile for a required SSURGO dataset
                missingList.append(shpAS)

        if len(missingList) > 0 and bRequired:
            raise MyError, "Failed to find one or more required SSURGO datasets for " + theTile + ": " + ", ".join(missingList)

        return surveyList

    except MyError, err:
        PrintMsg(str(err), 2)
        return []

    except:
        errorMsg()
        return []

## ===================================================================================
## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import sys, string, os, arcpy, locale, traceback, time
from arcpy import env

# Create the Geoprocessor object
try:
    inputFolder = arcpy.GetParameterAsText(0)      # Change this to the SSURGO Download folder (inputFolder)
    outputFolder = arcpy.GetParameterAsText(1)     # output folder to contain new geodatabases
    theTileValues = arcpy.GetParameter(2)          # list of state names
    bOverwriteOutput = arcpy.GetParameter(3)       # overwrite existing geodatabases
    bRequired = arcpy.GetParameter(4)              # require that all available SSURGO be present in the input folder
    useTextFiles = arcpy.GetParameter(5)           # checked: use text files for attributes; unchecked: use Access database for attributes

    #import SSURGO_MergeSoilShapefilesbyAreasymbol_GDB
    import SSURGO_Convert_to_Geodatabase

    # Get dictionary containing 'state abbreviations'
    stDict = StateNames()

    # Get dictionary containing the geographic region for each state
    dAOI = StateAOI()

    # Target attribute. Note that is this case it is lowercase. Thought it was uppercase for SAVEREST?
    # Used for XML parser
    attName = "areasymbol"

    # Track success or failure for each exported geodatabase
    goodExports = list()
    badExports = list()

    for theTile in theTileValues:
        stAbbrev = stDict[theTile]
        tileInfo = (stAbbrev, theTile)

        PrintMsg(" \n***************************************************************", 0)
        PrintMsg("Processing state: " + theTile, 0)
        PrintMsg("***************************************************************", 0)

        # Get list of AREASYMBOLs for this state tile from LAOVERLAP table in Soil Data Mart DB
        if theTile == "Puerto Rico and U.S. Virgin Islands":
            valList = GetAreasymbols(attName, "Puerto Rico")
            valList = valList + GetAreasymbols(attName, "Virgin Islands")

        else:
            valList = GetAreasymbols(attName, theTile)

        if len(valList) == 0:
            raise MyError, "Soil Data Access web service failed to retrieve list of areasymbols for " + theTile

        # If the state tile is "Pacific Basin", remove the Areasymbol for "American Samoa"
        # from the list. American Samoa will not be grouped with the rest of the PAC Basin
        if theTile == "Pacific Basin":
            #PrintMsg(" \nRemoving  areasymbol for American Samoa", 1)
            rmVal = GetAreasymbols(attName, "American Samoa")[0]
            PrintMsg(" \nAreaSymbol for American Samoa: " + rmVal, 1)

            if rmVal in valList:
                valList.remove(rmVal)

        #PrintMsg(" \nFinal Areasymbol List: " + ", ".join(valList), 0)

        # Get the AOI for this state. This is needed later to set the correct XML and coordinate system
        theAOI = dAOI[theTile]

        # Get list of matching folders containing SSURGO downloads
        surveyList = GetFolders(inputFolder, valList, bRequired, theTile)

        if len(surveyList) > 0:

            # Set path and name of Geodatabase for this state tile
            outputWS = os.path.join(outputFolder, "gSSURGO_" + stAbbrev + ".gdb")

            if arcpy.Exists(outputWS):
                if bOverwriteOutput:
                    PrintMsg(" \nRemoving existing geodatabase for " + theTile, 0)
                    arcpy.Delete_management(outputWS)
                    time.sleep(1)

                    if arcpy.Exists(outputWS):
                        # Failed to delete existing geodatabase
                        raise MyError, "Failed to delete " + outputWS

            # Call SDM Export script
            # 12-25-2013 try passing more info through the stAbbrev parameter
            #
            bExported = SSURGO_Convert_to_Geodatabase.gSSURGO(inputFolder, surveyList, outputWS, theAOI, tileInfo, useTextFiles)

            if bExported == False:
                PrintMsg("\tAdding " + theTile + " to list if failed conversions", 0)
                badExports.append(theTile)
                err = "Passed - Export failed for " + theTile

                if arcpy.Exists(outputWS):
                    # Delete failed geodatabase which is probably empty
                    #arcpy.Delete_management(outputWS)
                    pass

            else:
                # Successful export of the current tile
                #PrintMsg("\tAdding " + theTile + " to good list", 0)
                goodExports.append(theTile)

        else:
            # Failed to find any SSURGO downloads for this tile
            PrintMsg("None of the input surveys (" + ", ".join(valList) + ") were found for " + theTile, 2)
            badExports.append(theTile)

        # end of tile for loop

    PrintMsg(" \n" + (60 * "*"), 0)
    PrintMsg(" \n" + (60 * "*"), 0)
    PrintMsg("\nFinshed state exports", 0)

    if len(goodExports) > 0:
        PrintMsg(" \nSuccessfully created geodatabases for the following areas: " + ", ".join(goodExports) + " \n ", 0)

    if len(badExports) > 0:
        PrintMsg("Failed to create geodatabases for the following areas: " + ", ".join(badExports) + " \n ", 2)

except MyError, err:
    PrintMsg(str(err), 2)

except:
    errorMsg()
