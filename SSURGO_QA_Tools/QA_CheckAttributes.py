# QA_CheckAttributes.py
#
# ArcMap 10.1, arcpy
#
# Steve Peaslee, USDA-NRCS National Soil Survey Center
#
# Check all spatial AREASYMBOL and other specified attribute values for correct formatting
# Check all spatial AREASYMBOL values to confirm that they exist in Web Soil Survey

# 11-07-2013

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
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def CheckAreasymbols(asList):
    # Query SDM (SD Access Service which requires internet access)
    # Compare local spatial areasymbols with those in Web Soil Survey
    # Please note that surveys with a new AREASYMBOL may exist in NASIS, but not
    # in Web Soil Survey. These will be flagged incorrectly.

    try:
        import httplib, urllib2
        import xml.etree.cElementTree as ET
        # Handle choice list according to the first two parameter values

        # select by list of Areasymbols only
        sQuery = "SELECT AREASYMBOL FROM SASTATUSMAP WHERE AREASYMBOL IN (" + str(asList)[1:-1] + ") AND SAPUBSTATUSCODE = 2 ORDER BY AREASYMBOL"

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
        #dHeaders["User-Agent"] = "NuSOAP/0.7.3 (1.114)"
        #dHeaders["Content-Type"] = "application/soap+xml; charset=utf-8"
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
        valList = list()

        # Iterate through XML tree, finding required elements...
        for rec in tree.iter():

            if rec.tag == "AREASYMBOL":
                areasym = str(rec.text)
                valList.append(areasym)

        if len(valList) > 0:
            # Got at least one match back from Soil Data Access
            # Loop through and compare to the original list from the spatial
            if len(asList) > len(valList):
                # Incomplete match, look at each to find the problem(s)
                PrintMsg("Areasymbols with no match in Web Soil Survey: " + ", ".join(asList), 2)

                return False

            else:
                # Number of areasymbols match, should be good
                PrintMsg(" \nAll areasymbol values in spatial data have a match in Web Soil Survey", 0)
                return True

        else:
            # Failed to find a match for any surveys
            PrintMsg(" \nFailed to find a match for any of the input Areasymbols", 2)
            return False

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        err = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + " \n"
        PrintMsg(err, 2)
        return False

## ===================================================================================
def ProcessLayer(inLayer, inFields, bValidate):
    # Create a summary for each survey
    #
    # inLayer = selected featurelayer or featureclass that will be processed
    #
    # length of 5
    # Check for [0:2] is text and [2:5] is integer
    # Check for uppercase
    # Check for spaces or other non-printable characters
    # string.letters, string.punctuation and string.digits.

    # valid format

    try:
        bGood = True

        validText = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        validNum = "0123456789"
        validMusym = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-+._"
        fieldList = ["OID@"]

        for fld in inFields:
            fieldList.append(fld.value.upper())

        polygonList = list()
        asList = list()

        iCnt = int(arcpy.GetCount_management(inLayer).getOutput(0))
        arcpy.SetProgressor("step", "Checking input features...", 0, iCnt, 1)

        with arcpy.da.SearchCursor(inLayer, fieldList) as sCursor:
            # Select polgyons with the current attribute value and process the geometry for each
            for row in sCursor:
                # Process a polygon record
                fid = row[0]
                chk1 = ""   # L = wrong length; BF = bad format (2C3I); C = wrong case
                chk2 = ""

                for i in range(1, len(fieldList)):
                    # Skip first field which is OBJECTID
                    fld = fieldList[i]
                    val = row[i]


                    if not val is None:

                        if fld == "AREASYMBOL":
                            # Handle Areasymbol differently because it has more specific criteria
                            if len(val) == 5:
                                # length is OK
                                if not val[0] in validText or not val[1] in validText:
                                    # First 2 characters should be text
                                    chk1 = "BF"

                                elif not val[2] in validNum or not val[3] in validNum or not val[3] in validNum:
                                    # Last 3 characters should be integer
                                    chk1 = "BF"

                                elif val.upper() != val:
                                    chk1 = "C"
                            else:
                                # Bad length, should be 5 characters
                                chk1 = "L"

                            if chk1 != "":
                                bGood = False
                                PrintMsg("\tBad " + fld + " for polygon " + str(fid) + ": '" + val + "'", 0)
                                polygonList.append(fid)

                            else:
                                # Should be a correctly formatted areasymbol value
                                if not val in asList:
                                    asList.append(val.encode('ascii'))

                        # Check other attribute
                        # All we know is it is text field, don't know specifics
                        else:
                            chk2 = ""

                            if len(val) > 0:
                                # length is OK

                                if len(val) > len(val.strip()):
                                    #PrintMsg("\tsym for polygon " + str(fid)  + str(fid) + ":  '" + str(muSym) + "'", 0)
                                    chk2 = False
                                    polygonList.append(fid)

                                else:
                                    for c in val:
                                        if not c in validMusym:
                                            bGood2 = False
                                            #PrintMsg("\tBad musym for polygon " + str(fid) + ":  '" + str(muSym) + "'", 0)
                                            polygonList.append(fid)
                                            chk2 = False
                                            break

                            else:
                                # Blank value for musym
                                #PrintMsg("\tMissing musym for polygon " + str(fid), 0)
                                chk2 = "L"

                            if chk2 != "":
                                bGood = False
                                PrintMsg("\tBad " + fld + " for polygon " + str(fid) + ": '" + val + "'", 0)

                                if not fid in polygonList:
                                    # Add problem polygon to list for end report
                                    polygonList.append(fid)

                    else:
                        PrintMsg("\tBad " + fld + " for polygon " + str(fid) + ": '" + str(val) + "'", 0)
                        polygonList.append(fid)

                arcpy.SetProgressorPosition()

        if bGood == False:
            PrintMsg(" \nPolygons with attribute formatting errors: " + str(polygonList)[1:-1] + " \n ", 0)

        if bValidate:
            # Run the list of correctly formatted areasymbol values to make sure they exist in Web Soil Survey
            # What about Initial Soil Surveys with a new AREASYMBOL?
            #
            PrintMsg(" \nValidating Areasymbol list against Web Soi Survey: " + str(asList), 0)
            bValid = CheckAreasymbols(asList)

        return bGood

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        bGood = False

    except:
        errorMsg()
        bGood = False

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
        return FalseoutputPoin

## ===================================================================================
## MAIN
import sys, string, os, locale, time, math, operator, traceback, collections, arcpy
from arcpy import env

try:
    # Set formatting for numbers
    locale.setlocale(locale.LC_ALL, "")

    # Script parameters

    # Target Layer
    inLayer = arcpy.GetParameter(0)

    # Target attribute column
    inFields = arcpy.GetParameter(1)

    # Setup: Get all required information from input layer
    #
    # Describe input layer
    desc = arcpy.Describe(inLayer)
    theDataType = desc.dataType.upper()
    theCatalogPath = desc.catalogPath

    if theDataType == "FEATURELAYER":
        # input layer is a FEATURELAYER, get featurelayer specific information
        fc = desc.catalogPath
        PrintMsg(" \nLooking for attribute value problems in featurelayer " + desc.name + "...", 0)

    elif theDataType in ["FEATURECLASS", "SHAPEFILE"]:
        # input layer is a featureclass, get featureclass specific information
        PrintMsg(" \nLooking for attribute value problems in featureclass " + desc.name + "...", 0)
        fc = inLayer

    # End of Setup
    #

    bValidate = True

    bGood = ProcessLayer(fc, inFields, bValidate)

    if bGood:
        PrintMsg(" \nProcessing complete with no attribute formatting errors found\n ", 0)

    else:
        PrintMsg("Processing complete, but attribute formatting errors found\n ", 2)


except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()

    try:
        del inLayer

    except NameError:
        pass
