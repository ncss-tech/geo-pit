# QA_MapunitCheck.py
#
# Purpose:  compare MUSYM values in selected featurelayer with MUSYM
# values from NASIS. Adapted from Kevin Godsey's VBA tool. Sends
# query to the LIMS report server.
#
# Inputs:
#        AREASYMBOL
#        TABLE OR FEATURECLASS
#
#
# 11-18-2009 Steve Peaslee, NSSC

# 04-01-2010 - major revision to make the script compatible with NASIS 6.0
#              Also works with a table such as MAPUNIT and LEGEND as an
#              alternative to NASIS.
# 04-19-2010 - Bug fix. Incorrect parsing of the return from NASIS skipped
#              the first mapunit.
# 04-30-2010 - Removed references to MUKEY from documentation
# 06-09-2010 - Fixed a few minor problems such as featurelayer/featureclass issues
#
# 06-19-2013 - Updating to use arcpy  and da cursors
# 06-24-2013 - Revamped html handling for NASIS
# 06-24-2013 - Added exclusion for NOTCOM. It is the only mismatch allowed for now.
# 09-06-2013 - Major performance increase. Moved spatial mapunit list to a single function
#              that stores up front the entire mapunit list by areasymbol in a Python dictionary.
# 09-07-2013 - Altering operation to always run against the underlying featureclass to prevent any records being skipped
#
# 10-21-2013 - Using new NASIS report that allows specification of the different MUSTATUS types
# 10-31-2013 - Renamed this script from 'Get_Mukey.py'...

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

# create a subclass and override the data handler methods

class MyHTMLParser(HTMLParser):
    # create an HTMLParser class, mainly designed to get the data block within
    # the html returned by the NASIS Online report.

    # initialize the data block variable
    dataDict = dict()

    def handle_data(self, data):

        if str(data).strip():
            # load the data into a dictionary
            musym, mukey = data.split()
            musym = musym.strip()
            mukey = mukey.replace(",","").strip()
            self.dataDict[musym] = mukey

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor

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
                #arcpy.AddMessage("    ")

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
        PrintMsg("Unhandled error in unHandledException method", 2)
        pass

## ===================================================================================
def setScratchWorkspace():
    # This function will set the scratchGDB environment based on the scratchWorkspace environment.
    #
    # The scratch workspac will typically not be defined by the user but the scratchGDB will
    # always be defined.  The default location for the scratchGDB is at C:\Users\<user>\AppData\Local\Temp
    # on Windows 7 or C:\Documents and Settings\<user>\Localsystem\Temp on Windows XP.  Inside this
    # directory, scratch.gdb will be created.
    #
    # If scratchWorkspace is set to something other than a GDB or Folder than the scratchWorkspace
    # will be set to C:\temp.  If C:\temp doesn't exist than the ESRI scratchWorkspace locations will be used.
    #
    # If scratchWorkspace is an SDE GDB than the scratchWorkspace will be set to C:\temp.  If
    # C:\temp doesn't exist than the ESRI scratchWorkspace locations will be used.

    try:
        # -----------------------------------------------
        # Scratch Workspace is defined by user or default is set
        if arcpy.env.scratchWorkspace is not None:

            # describe scratch workspace
            scratchWK = arcpy.env.scratchWorkspace
            descSW = arcpy.Describe(scratchWK)
            descDT = descSW.dataType.upper()

            # scratch workspace is geodatabase
            if descDT == "WORKSPACE":
                progID = descSW.workspaceFactoryProgID

                # scratch workspace is a FGDB
                if  progID == "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
                    arcpy.env.scratchWorkspace = os.path.dirname(scratchWK)
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                # scratch workspace is a Personal GDB -- set scratchWS to folder of .mdb
                elif progID == "esriDataSourcesGDB.AccessWorkspaceFactory.1":
                    arcpy.env.scratchWorkspace = os.path.dirname(scratchWK)
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                # scratch workspace is an SDE GDB.
                elif progID == "esriDataSourcesGDB.SdeWorkspaceFactory.1":

                    # set scratch workspace to C:\Temp; avoid the server
                    if os.path.exists(r'C:\Temp'):

                        arcpy.env.scratchWorkspace = r'C:\Temp'
                        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                    # set scratch workspace to default ESRI location
                    else:
                        arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
                        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

            # scratch workspace is simply a folder
            elif descDT == "FOLDER":
                arcpy.env.scratchWorkspace = scratchWK
                arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

            # scratch workspace is set to something other than a GDB or folder; set to C:\Temp
            else:
                # set scratch workspace to C:\Temp
                if os.path.exists(r'C:\Temp'):

                    arcpy.env.scratchWorkspace = r'C:\Temp'
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                # set scratch workspace to default ESRI location
                else:
                    arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

        # -----------------------------------------------
        # Scratch Workspace is not defined. Attempt to set scratch to C:\temp
        elif os.path.exists(r'C:\Temp'):

            arcpy.env.scratchWorkspace = r'C:\Temp'
            arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

        # set scratch workspace to default ESRI location
        else:

            arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
            arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def NASIS_List(theAreasymbol, theURL, theParameters, muStatus):
    # Create a dictionary of NASIS MUSYM values
    # Sometimes having problem getting first mapunit (ex. Adda in IN071)
    try:
        #PrintMsg(" \nRetrieving MUSYM values for survey area '" + theAreasymbol + "' from NASIS", 1)

        # Problem with NASIS 6.0. It doesn't recognize the parameter for some unknown reason
        # Seems to work if we put the entire URL and Parameter into one string and set
        # the Parameter value to None
        #
        # Use muStatus to set the mapunit status option for the report
        # 1:provisional, 2:approved, 3:correlated, 4:additional
        # In theory, should only be #3 correlated for SSURGO downloads
        #
        theURL = theURL + theParameters + theAreasymbol + muStatus
        #PrintMsg(" \n" + theURL + " \n", 0)
        theParameters = None
        resp = urlopen(theURL, None )
        thePage = resp.read()
        parser = MyHTMLParser()
        parser.dataDict.clear()
        parser.feed(thePage)
        parser.close()
        dNASIS = parser.dataDict

        mapunitCnt = 0

        if len(dNASIS) == 0:
            PrintMsg("\tRetrieved zero mapunit records from NASIS online report (check criteria in NASIS?)", 2)

        else:
            PrintMsg(" \n\tRetrieved " + str(len(dNASIS)) + " correlated mapunits from NASIS", 1)

        return dNASIS

    except IOError:
        errorMsg()
        return dict()

    except:
        errorMsg()
        return dict()

## ===================================================================================
def CompareMusym(dNASIS, musymList, theAreasymbol, dBadSurveys):
    #
    # Compare database contents with layer contents
    #
    # Save errors to a dictionary: key=Areasymbol, SpatialCount, NASISCount, Note, NASISExtra, SpatialExtra
    #
    try:
        #
        # Compare database MUSYM values with Layer MUSYM values
        #
        missingLayer = list()

        for theMUSYM in dNASIS:
            if not theMUSYM in musymList:
                #PrintMsg("\tMissing map layer musym: '" + theMUSYM + "'", 0)
                missingLayer.append(theMUSYM)

        musymCnt = len(missingLayer)

        if musymCnt > 0:
            PrintMsg("\tNASIS legend for " + theAreasymbol  + " has " + str(musymCnt) + " MUSYM value(s) not present in the spatial layer:", 2)

            if musymCnt > 1:
                PrintMsg("\t" + ", ".join(missingLayer), 0)

            else:
                PrintMsg("\t" + missingLayer[0])

        else:
            PrintMsg(" \n\tAll MUSYM values in NASIS legend matched those in the spatial layer", 1)


        # Compare layer MUSYM values with NASIS legend, granting an exception for NOTCOM
        #
        missingNASIS = list()

        for theMUSYM in musymList:
            if not theMUSYM in dNASIS:
                if theMUSYM.strip() == "":
                    raise MyError, "\tInput spatial layer contains one or more features with a missing MUSYM value"

                elif theMUSYM != "NOTCOM":                  # Remove this if NOTCOMs are NOT excluded from the check
                    missingNASIS.append(theMUSYM)

        dbCnt = len(missingNASIS)

        if dbCnt > 0:
            PrintMsg("\tSpatial layer has " + str(dbCnt) + " MUSYM value(s) not present in NASIS:", 2)

            if dbCnt > 1:
                PrintMsg("\t" + ", ".join(missingNASIS), 0)

            else:
                PrintMsg("\t" + missingNASIS[0])

        else:
            PrintMsg(" \n\tAll MUSYM values in spatial layer match the NASIS legend for " + theAreasymbol, 1)

        if dbCnt > 0 or musymCnt > 0:
            # Save errors to a dictionary
            dBadSurveys[theAreasymbol] =(len(musymList), len(dNASIS), "",", ".join(missingLayer), ", ".join(missingNASIS) )
            return False, dBadSurveys

        else:
            return True, dBadSurveys

    except MyError, e:
        # Example: raise MyError, "this is an error message"
        PrintMsg(str(e) + " \n", 2)
        # SpatialCount, NASISCount, Note, NASISExtra, SpatialExtra
        dBadSurveys[theAreasymbol] = (0, 0, e, "","")
        return False, dBadSurveys

    except:
        errorMsg()
        return False, dBadSurveys

## ===================================================================================
def UpdateMukeys(theInput, dNASIS, theAreasymbol):
    # Update layer MUKEY values for the specified AREASYMBOL value
    try:

        fieldList = ["MUSYM", "MUKEY"]
        queryField = arcpy.AddFieldDelimiters(theInput, "AREASYMBOL")
        sql = ""

        if theAreasymbol != "":
            sql = queryField + " = '" + theAreasymbol + "'"

        else:
            return False

        with arcpy.da.UpdateCursor (theInput, fieldList, sql) as outCursor:

            for outRow in outCursor:
                musym = outRow[0]

                if musym in dNASIS:             # Remove this to if NOTCOMs are NOT excluded from the check
                    outRow[1] = dNASIS[musym]
                    outCursor.updateRow(outRow)

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def CreateMapunitDictionary(theInput, sql):
    try:
        # Load mapunit dictionary with entire contents of input layer or featureclass
        #
        dMapunits = dict()
        fieldList = ('AREASYMBOL','MUSYM')
        PrintMsg(" \nGetting mapunit information from spatial layer (" + os.path.basename(theInput) + ")", 1)
        arcpy.SetProgressorLabel("Getting mapunit information from spatial layer (" + os.path.basename(theInput) + ")")

        with arcpy.da.SearchCursor(theInput, fieldList, sql) as cursor:  # 30 seconds faster when only running one out of many
        #with arcpy.da.SearchCursor(theInput, fieldList) as cursor:      # a little faster when doing it all

            for row in cursor:
                areasym = row[0].encode('ascii').strip()
                musym = row[1].encode('ascii').strip()

                if areasym in dMapunits:
                    if not musym in dMapunits[areasym]:
                        dMapunits[areasym].append(musym)

                else:
                    dMapunits[areasym] = [musym]

        #PrintMsg(" \nFinished loading mapunit dictionary", 1)


        return dMapunits

    except:
        errorMsg()
        return dMapunits

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
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcpy, traceback,  collections
from urllib2 import Request, urlopen, URLError, HTTPError

from arcpy import env

try:
    # Create geoprocessor object
    progLoc = "Main Setup"

    # Get input parameters
    #
    theInput = arcpy.GetParameterAsText(0)
    asValues = arcpy.GetParameter(1)    # value list containing Areasymbol
    bUpdate = arcpy.GetParameter(2)
    mx1 = arcpy.GetParameter(3)   # provisional
    mx2 = arcpy.GetParameter(4)   # approved
    mx3 = arcpy.GetParameter(5)   # correlated
    mx4 = arcpy.GetParameter(6)   # additional

    # Set scratchworkspace and scratchfolder environment
    if not setScratchWorkspace():
        raise MyError, "Failure to set ArcGIS scratch environment"

    # Describe input layer and get workspace location
    desc = arcpy.Describe(theInput)
    theDataType = desc.dataType.upper()
    theCatalogPath = desc.catalogPath

    if theDataType == "FEATURELAYER":
        # input layer is a FEATURELAYER, get featurelayer specific information
        ws = os.path.dirname(desc.catalogPath)
        wDesc = arcpy.Describe(ws)

        if wDesc.dataType.upper() == "FEATUREDATASET":
            ws = os.path.dirname(ws)

        rptFolder = os.path.dirname(ws)
        PrintMsg(" \nWorkspace for input featurelayer: " + ws, 0)


    elif theDataType == "FEATURECLASS":
        ws = os.path.dirname(desc.catalogPath)
        wDesc = arcpy.Describe(ws)

        if wDesc.dataType.upper() == "FEATUREDATASET":
            ws = os.path.dirname(ws)

        rptFolder = os.path.dirname(ws)
        PrintMsg(" \nWorkspace for input featureclass: " + ws, 0)

    elif theDataType == "SHAPEFILE":
        ws = os.path.dirname(inLayer)
        rptFolder = ws
        PrintMsg(" \nFolder for input shapefile: " + ws, 0)

    # Hardcode NASIS-LIMS Report Webservice for retrieving MUSYM and MUKEY values for a specified AREASYMBOL
    #
    # New NASIS report that allows user to specify any of the MUSTATUS values
    theURL = r"https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?"
    theParameters = "report_name=WEB-MapunitsAreaMustatus&area_sym="

    if mx1 is True:
        mx1 = "1"

    else:
        mx1 = "0"

    if mx2 is True:
        mx2 = "2"

    else:
        mx2 = "0"

    if mx3 is True:
        mx3 = "3"

    else:
        mx3 = "0"

    if mx4 is True:
        mx4 = "4"

    else:
        mx4 = "0"

    muStatus = "&mx1=" + mx1 + "&mx2=" + mx2 + "&mx3=" + mx3 + "&mx4=" + mx4

    # If the input is a featurelayer, switch to the featureclass so that every record gets checked
    desc = arcpy.Describe(theInput)
    dT = desc.dataType.upper()

    if dT == "FEATURELAYER":
        theInput = desc.catalogPath

    # Create a list of surveys that fail the test
    badSurveys = list()
    # Create a dictionary with information for surveys that fail the test
    dBadSurveys = dict()

    # Create dictionary containing list of mapunits for each soil survey area (AREASYMBOL)
    asList = list()
    for theAreasymbol in asValues:
        asList.append("'" + theAreasymbol + "'")

    sql = '"AREASYMBOL" in (' + ','.join(asList) + ')'
    iNum = len(asList)

    dMapunits = CreateMapunitDictionary(theInput, sql)

    if len(dMapunits) == 0:
        raise MyError, "Failed to get mapunit information from " + theInput

    elif len(dMapunits) > 0:
        # open a report file to dump errors to
        rptFile = os.path.join(rptFolder, "QA_MapunitCheck_" + os.path.basename(ws.replace(".","_")) + ".txt")

        if arcpy.Exists(rptFile):
            os.remove(rptFile)

    arcpy.ResetProgressor()
    arcpy.SetProgressor("step", "Comparing NASIS information with spatial layer...",  0, (iNum -1), 1)
    iCnt = 0

    for theAreasymbol in asValues:
        # Process each soil survey identified by Areasymbol
        PrintMsg(" \n" + theAreasymbol + ": Comparing spatial layer and NASIS legend for this non-MLRA soil survey...", 0)
        PrintMsg("---------------------------------------------------------------------------------------", 0)
        iCnt += 1
        arcpy.SetProgressorLabel("Checking survey " + theAreasymbol.upper() + "  (" + Number_Format(iCnt, 0, True) + " of " + Number_Format(len(asList), 0, True) + ")")

        # Create dictionary of MUSYM values retrieved from input layer
        musymList = dMapunits[theAreasymbol]

        if len(musymList) > 0:
            PrintMsg("\tFound " + str(len(musymList)) + " mapunits in spatial layer", 1)

            # Create dictionary of MUSYM values retrieved from NASIS
            #
            dNASIS = NASIS_List(theAreasymbol, theURL, theParameters, muStatus)

            if len(dNASIS) > 0:

                # Compare MUSYM values in each dictionary
                #
                bGood, dBadSurveys = CompareMusym(dNASIS, musymList, theAreasymbol, dBadSurveys)

                if bGood == False:
                    badSurveys.append(theAreasymbol)

                if bUpdate:
                    if bGood:
                        # go ahead and update MUKEY values for the specified AREASYMBOL
                        PrintMsg(" \n\tUpdating MUKEY values...", 0)
                        bUpdated = UpdateMukeys(theInput, dNASIS, theAreasymbol)

                    else:
                        # mismatch between NASIS and the maplayer MUSYM values! skip the update
                        PrintMsg(" \nMUKEY update cannot occur until legend mismatch has been fixed", 0)

            else:
                PrintMsg("\tUnable to run comparison for " + theAreasymbol, 2)
                badSurveys.append(theAreasymbol)
                dBadSurveys[theAreasymbol] = (len(musymList), 0, "Unable to retrieve mapunit information from NASIS", "","")


        else:
            PrintMsg(" \nFailed to get list of mapunits from input layer for " + theAreasymbol, 2)
            badSurveys.append(theAreasymbol)
            dBadSurveys[theAreasymbol] = (0, 0, "Unable to retrieve mapunit information from spatial layer", "","")

        arcpy.SetProgressorPosition()

    arcpy.SetProgressorLabel("Processing complete for all " + Number_Format(len(asList), 0, True) + " surveys")

    if len(badSurveys) > 0:
        PrintMsg(" \n---------------------------------------------------------------------------------------", 0)

        if len(badSurveys) == 1:
            PrintMsg("The following survey has problems that must be addressed: " + badSurveys[0], 2)

        else:
            PrintMsg("The following surveys have problems that must be addressed: " + ", ".join(badSurveys), 2)

    if len(dBadSurveys) > 0:
        PrintMsg(" \nWriting summary info to tab-delimited text file: " + rptFile, 0)

        # sort dictionary by Areasymbol
        sortedList = dBadSurveys

        with open(rptFile, 'w') as f:
            hdr = "SurveyID\tSPATIAL_COUNT\tNASIS_COUNT\tNOTES\tEXTRA_SPATIAL\tEXTRA_NASIS" + " \n"
            f.write(hdr)

            #for survey, info in dBadSurveys.items():
            for survey in badSurveys:
                info = dBadSurveys[survey]
                errorLine = survey + "\t" + str(info[0]) + "\t" + str(info[1]) + "\t" + info[2] + "\t" + info[4] +  "\t" + info[3] + "\n"
                f.write(errorLine)
                #PrintMsg(survey + "|" + str(info[0]) + "|" + str(info[1]) + "|" + info[2] + "|" + info[3] +  "|" + info[4], 1)

    PrintMsg(" \n" + os.path.basename(sys.argv[0]) + " script finished \n " , 1)

except MyError, e:
    PrintMsg(e, 2)

except:
    errorMsg()


