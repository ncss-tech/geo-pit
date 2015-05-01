# QA_MultipartPolygons.py
#
# ArcMap 10.1, arcpy
#
# Steve Peaslee, USDA-NRCS National Soil Survey Center
#
# Adapted from Vertex Report tool
# 11-05-2013

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
def ProcessLayer(inLayer, areaSym):
    # Create a summary for each soil survey
    #
    # inLayer = selected featurelayer or featureclass that will be processed
    try:

        iMultipart = 0
        fieldList = ["OID@","SHAPE@"]
        sql = '"AREASYMBOL" = ' + "'" + areaSym + "'"
        saList = list()
        polyList = list()
        desc = arcpy.Describe(inLayer)
        oidName = desc.OIDFieldName

        with arcpy.da.SearchCursor(inLayer, fieldList, sql) as sCursor:
            # Select polgyons with the current attribute value and process the geometry for each

            for row in sCursor:
                # Process a polygon record. row[1] is the same as feat or SHAPE
                fid, feat = row

                if not feat is None:
                    iPartCnt = feat.partCount

                    if iPartCnt > 1:
                        iMultipart += 1
                        saList.append(fid)
                        polyList.append(fid)

                else:
                    raise MyError, "NULL geometry for polygon #" + str(fid)

        if iMultipart > 0:
            PrintMsg("\t" + areaSym + " has " + Number_Format(iMultipart, 0, True) + " multipart polygons: " + '"' + oidName + '"' + " IN (" + str(polyList)[1:-1] + ")", 1)

        else:
            PrintMsg(" \n\t" + areaSym + " has no multipart polygons", 0)

        return iMultipart, saList

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        return -1, idList

    except:
        errorMsg()
        return -1, idList

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
def elapsedTime(start):
    # Calculate amount of time since "start" and return time string
    try:
        # Stop timer
        #
        end = time.time()

        # Calculate total elapsed seconds
        eTotal = end - start

        # day = 86400 seconds
        # hour = 3600 seconds
        # minute = 60 seconds

        eMsg = ""

        # calculate elapsed days
        eDay1 = eTotal / 86400
        eDay2 = math.modf(eDay1)
        eDay = int(eDay2[1])
        eDayR = eDay2[0]

        if eDay > 1:
          eMsg = eMsg + str(eDay) + " days "
        elif eDay == 1:
          eMsg = eMsg + str(eDay) + " day "

        # Calculated elapsed hours
        eHour1 = eDayR * 24
        eHour2 = math.modf(eHour1)
        eHour = int(eHour2[1])
        eHourR = eHour2[0]

        if eDay > 0 or eHour > 0:
            if eHour > 1:
                eMsg = eMsg + str(eHour) + " hours "
            else:
                eMsg = eMsg + str(eHour) + " hour "

        # Calculate elapsed minutes
        eMinute1 = eHourR * 60
        eMinute2 = math.modf(eMinute1)
        eMinute = int(eMinute2[1])
        eMinuteR = eMinute2[0]

        if eDay > 0 or eHour > 0 or eMinute > 0:
            if eMinute > 1:
                eMsg = eMsg + str(eMinute) + " minutes inLayer"
            else:
                eMsg = eMsg + str(eMinute) + " minute "

        # Calculate elapsed secons
        eSeconds = "%.1f" % (eMinuteR * 60)

        if eSeconds == "1.00":
            eMsg = eMsg + eSeconds + " second "
        else:
            eMsg = eMsg + eSeconds + " seconds "

        return eMsg

    except:
        errorMsg()
        return ""

## ===================================================================================
## MAIN
import sys, string, os, locale, time, math, operator, traceback, collections, arcpy
from arcpy import env

try:
    # Set formatting for numbers
    locale.setlocale(locale.LC_ALL, "")

    # Script parameters

    # Target Featureclass
    inLayer = arcpy.GetParameter(0)

    # Target surveys
    asList = arcpy.GetParameter(1)

    # survey id
    inFieldName = "AREASYMBOL"

    # Start timer
    begin = time.time()
    eMsg = elapsedTime(begin)

    env.overwriteOutput = True

    # Setup: Get all required information from input layer
    #
    # Describe input layer
    desc = arcpy.Describe(inLayer)
    theDataType = desc.dataType.upper()
    theCatalogPath = desc.catalogPath

    if theDataType == "FEATURELAYER":
        # input layer is a FEATURELAYER, get featurelayer specific information
        fc = desc.catalogPath
        PrintMsg(" \nLooking for multipart polygons in featurelayer " + desc.name + "...", 0)

    elif theDataType in ["FEATURECLASS", "SHAPEFILE"]:
        # input layer is a featureclass, get featureclass specific information
        PrintMsg(" \nLooking for multipart polygons in featureclass " + desc.name + "...", 0)
        fc = inLayer

    # End of Setup
    #

    # run process
    errorList = list()
    problemList = list()
    goodList = list()
    idList = list()

    for areaSym in asList:
        #PrintMsg(" \n\tProcessing soil survey: " + areaSym, 0)
        saList = list()

        if theDataType == "FEATURELAYER":
            iMultiPart, saList = ProcessLayer(fc, areaSym)
            idList.extend(saList)

        elif theDataType in ["FEATURECLASS", "SHAPEFILE"]:
            iMultiPart, saList = ProcessLayer(inLayer, areaSym)
            idList.extend(saList)

        if iMultiPart == -1:
            errorList.append(areaSym)

        elif iMultiPart > 0:
            problemList.append(areaSym)

        else:
            goodList.append(areaSym)

    if len(problemList) > 0:
        PrintMsg("The following surveys have multipart polygons: " + ", ".join(problemList) + " \n ", 2)
        # Select the polygons that are multipart
        sql = '"OBJECTID" IN ' + "(" + str(idList)[1:-1] + ")"
        #PrintMsg(" \n" + sql, 0)

        if theDataType == "FEATURELAYER":
            arcpy.SelectLayerByAttribute_management(inLayer, "NEW_SELECTION", sql)
            iSel = int(arcpy.GetCount_management(inLayer).getOutput(0))
            PrintMsg("Selecting all " + Number_Format(iSel, 0, True) + " polygons in the featurelayer that are multipart \n ", 0)

        else:
            inLayer = desc.name + " MultiPolygons"
            arcpy.MakeFeatureLayer_management(fc, inLayer, sql)

    if len(errorList) > 0:
        PrintMsg("The following surveys failed during testing: " + ", ".join(errorList) + " \n ", 2)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()

    try:
        del inLayer

    except NameError:
        pass
