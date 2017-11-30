#-------------------------------------------------------------------------------
# Name:        Generate Mapunit Geodata Report
# Purpose:     This tool will generate a compositional or statistical breakdown
#              of various MLRAGeodata layers for a user-defined polygon layer.
#              The output information will be written to a text file for future
#              reference located in the same directory as the input mapunit layer.
#
# Author:      Adolfo.Diaz
#              Region 10 GIS Specialist
#              608.662.4422 ext. 216
#              adolfo.diaz@wi.usda.gov
#
# Created:     8.28.2014
# Last Modified 02.17.2017
# Copyright:   (c) Adolfo.Diaz 2014
#
#
# Should I add an "Other" line to the processHydro field when percentages don't exceed 0%.  Some results may all be 0%.
#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        #print msg

        f = open(textFilePath,'a+')
        f.write(msg + " \n")
        f.close()

        del f

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

## ===================================================================================
def logBasicSettings():
    # record basic user inputs and settings to log file for future purposes

    try:

        import getpass, time

        f = open(textFilePath,'a+')
        f.write("User Name: " + getpass.getuser() + "\n")
        f.write("Date Executed: " + time.ctime() + "\n")
        f.write("User Parameters:\n")
        f.write("\tMapunit Layer: " + os.path.basename(muLayerPath) + "\n")
        f.write("\tAnalysis Type: " + analysisType + "\n\n")

        f.close
        del f

    except:
        errorMsg()

## ===================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

##        tb = sys.exc_info()[2] # return a tuple of type, value, traceback
##        tbinfo = traceback.format_tb(tb)[0]
##        theMsg = "\t" + tbinfo + "\n\t" + str(sys.exc_type)+ ": " + str(sys.exc_value)
##        AddMsgAndPrint(theMsg,2)

#""" ------------------Just for Testing -----------------------"""
##        exc_type, exc_value, exc_traceback = sys.exc_info()
##
##        AddMsgAndPrint("\n\t***** print_tb:",2)
##        AddMsgAndPrint(traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
##
##        AddMsgAndPrint("\n\t***** print_exception:",2)
##        AddMsgAndPrint(traceback.print_exception(exc_type, exc_value, exc_traceback,
##                                  limit=2, file=sys.stdout))
##        AddMsgAndPrint("\n\t***** print_exc:",2)
##        AddMsgAndPrint(traceback.print_exc())
##
##        AddMsgAndPrint("\n\t***** format_exc, first and last line:",2)
##        formatted_lines = traceback.format_exc().splitlines()
##        AddMsgAndPrint(formatted_lines[0])
##        AddMsgAndPrint(formatted_lines[-1])
##
##        AddMsgAndPrint("\n\t***** format_exception:",2)
##        AddMsgAndPrint(repr(traceback.format_exception(exc_type, exc_value,
##                                              exc_traceback)))
##        AddMsgAndPrint("\n\t***** extract_tb:",2)
##        AddMsgAndPrint(repr(traceback.extract_tb(exc_traceback)))
##
##        AddMsgAndPrint("\n\t***** format_tb:",2)
##        AddMsgAndPrint(repr(traceback.format_tb(exc_traceback)))
##
##        AddMsgAndPrint("\n\t***** tb_lineno:", exc_traceback.tb_lineno,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

### ===================================================================================
def setScratchWorkspace():
    """ This function will set the scratchWorkspace for the interim of the execution
        of this tool.  The scratchWorkspace is used to set the scratchGDB which is
        where all of the temporary files will be written to.  The path of the user-defined
        scratchWorkspace will be compared to existing paths from the user's system
        variables.  If there is any overlap in directories the scratchWorkspace will
        be set to C:\TEMP, assuming C:\ is the system drive.  If all else fails then
        the packageWorkspace Environment will be set as the scratchWorkspace. This
        function returns the scratchGDB environment which is set upon setting the scratchWorkspace"""

    try:
        AddMsgAndPrint("\nSetting Scratch Workspace")
        scratchWK = arcpy.env.scratchWorkspace

        # -----------------------------------------------
        # Scratch Workspace is defined by user or default is set
        if scratchWK is not None:

            # dictionary of system environmental variables
            envVariables = os.environ

            # get the root system drive
            if envVariables.has_key('SYSTEMDRIVE'):
                sysDrive = envVariables['SYSTEMDRIVE']
            else:
                sysDrive = None

            varsToSearch = ['ESRI_OS_DATADIR_LOCAL_DONOTUSE','ESRI_OS_DIR_DONOTUSE','ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE',
                            'ESRI_OS_DATADIR_ROAMING_DONOTUSE','TEMP','LOCALAPPDATA','PROGRAMW6432','COMMONPROGRAMFILES','APPDATA',
                            'USERPROFILE','PUBLIC','SYSTEMROOT','PROGRAMFILES','COMMONPROGRAMFILES(X86)','ALLUSERSPROFILE']

            """ This is a printout of my system environmmental variables - Windows 7
            -----------------------------------------------------------------------------------------
            ESRI_OS_DATADIR_LOCAL_DONOTUSE C:\Users\adolfo.diaz\AppData\Local\
            ESRI_OS_DIR_DONOTUSE C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\6\arc3765\
            ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE C:\Users\adolfo.diaz\Documents\
            ESRI_OS_DATADIR_COMMON_DONOTUSE C:\ProgramData\
            ESRI_OS_DATADIR_ROAMING_DONOTUSE C:\Users\adolfo.diaz\AppData\Roaming\
            TEMP C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\6\arc3765\
            LOCALAPPDATA C:\Users\adolfo.diaz\AppData\Local
            PROGRAMW6432 C:\Program Files
            COMMONPROGRAMFILES :  C:\Program Files (x86)\Common Files
            APPDATA C:\Users\adolfo.diaz\AppData\Roaming
            USERPROFILE C:\Users\adolfo.diaz
            PUBLIC C:\Users\Public
            SYSTEMROOT :  C:\Windows
            PROGRAMFILES :  C:\Program Files (x86)
            COMMONPROGRAMFILES(X86) :  C:\Program Files (x86)\Common Files
            ALLUSERSPROFILE :  C:\ProgramData
            ------------------------------------------------------------------------------------------"""

            bSetTempWorkSpace = False

            """ Iterate through each Environmental variable; If the variable is within the 'varsToSearch' list
                list above then check their value against the user-set scratch workspace.  If they have anything
                in common then switch the workspace to something local  """
            for var in envVariables:

                if not var in varsToSearch:
                    continue

                # make a list from the scratch and environmental paths
                varValueList = (envVariables[var].lower()).split(os.sep)          # ['C:', 'Users', 'adolfo.diaz', 'AppData', 'Local']
                scratchWSList = (scratchWK.lower()).split(os.sep)                 # [u'C:', u'Users', u'adolfo.diaz', u'Documents', u'ArcGIS', u'Default.gdb', u'']

                # remove any blanks items from lists
                if '' in varValueList: varValueList.remove('')
                if '' in scratchWSList: scratchWSList.remove('')

                # First element is the drive letter; remove it if they are
                # the same otherwise review the next variable.
                if varValueList[0] == scratchWSList[0]:
                    scratchWSList.remove(scratchWSList[0])
                    varValueList.remove(varValueList[0])

                # obtain a similarity ratio between the 2 lists above
                #sM = SequenceMatcher(None,varValueList,scratchWSList)

                # Compare the values of 2 lists; order is significant
                common = [i for i, j in zip(varValueList, scratchWSList) if i == j]

                if len(common) > 0:
                    bSetTempWorkSpace = True
                    break

            # The current scratch workspace shares 1 or more directory paths with the
            # system env variables.  Create a temp folder at root
            if bSetTempWorkSpace:
                AddMsgAndPrint("\tCurrent Workspace: " + scratchWK,0)

                if sysDrive:
                    tempFolder = sysDrive + os.sep + "TEMP"

                    if not os.path.exists(tempFolder):
                        os.makedirs(tempFolder,mode=777)

                    arcpy.env.scratchWorkspace = tempFolder
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                else:
                    packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                    if arcpy.env[packageWS[0]]:
                        arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
                    else:
                        AddMsgAndPrint("\tCould not set any scratch workspace",2)
                        return False

            # user-set workspace does not violate system paths; Check for read/write
            # permissions; if write permissions are denied then set workspace to TEMP folder
            else:
                arcpy.env.scratchWorkspace = scratchWK

                if arcpy.env.scratchGDB == None:
                    AddMsgAndPrint("\tCurrent scratch workspace: " + scratchWK + " is READ only!",0)

                    if sysDrive:
                        tempFolder = sysDrive + os.sep + "TEMP"

                        if not os.path.exists(tempFolder):
                            os.makedirs(tempFolder,mode=777)

                        arcpy.env.scratchWorkspace = tempFolder
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                    else:
                        packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                        if arcpy.env[packageWS[0]]:
                            arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                            AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                        else:
                            AddMsgAndPrint("\tCould not set any scratch workspace",2)
                            return False

                else:
                    AddMsgAndPrint("\tUser-defined scratch workspace is set to: "  + arcpy.env.scratchGDB,0)

        # No workspace set (Very odd that it would go in here unless running directly from python)
        else:
            AddMsgAndPrint("\tNo user-defined scratch workspace ",0)
            sysDrive = os.environ['SYSTEMDRIVE']

            if sysDrive:
                tempFolder = sysDrive + os.sep + "TEMP"

                if not os.path.exists(tempFolder):
                    os.makedirs(tempFolder,mode=777)

                arcpy.env.scratchWorkspace = tempFolder
                AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

            else:
                packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                if arcpy.env[packageWS[0]]:
                    arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                else:
                    return False

        arcpy.Compact_management(arcpy.env.scratchGDB)
        return arcpy.env.scratchGDB

    except:

        # All Failed; set workspace to packageWorkspace environment
        try:
            packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
            if arcpy.env[packageWS[0]]:
                arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                arcpy.Compact_management(arcpy.env.scratchGDB)
                return arcpy.env.scratchGDB
            else:
                AddMsgAndPrint("\tCould not set scratchWorkspace. Not even to default!",2)
                return False
        except:
            errorMsg()
            return False

# ===============================================================================================================
def determineOverlap(muLayer):
    # This function will compute a geometric intersection of the SSA boundary and the extent
    # boundary to determine overlap.  If the number of features in the output is greater than
    # the sum of the features of the muLayer and the extentboundary then overlap is assumed
    # and TRUE is returned otherwise FALSE is returned.

    try:
        # -------------- Get the SAPOLYGON ----------- Layer
        AddMsgAndPrint("\nDetermining overlap between input polygon and your Geodata extent",0)
        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\"soils\" folder was not found in your MLRAGeodata Folder -- Cannot determine Overlap\n",2)
            return False
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"SSURGO.gdb\" was not found in the soils folder -- Cannot determine Overlap\n",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\t There are muliple \"SSURGO_*.gdb\" in the soils folder -- Cannot determine Overlap\n",2)
            return False

        arcpy.env.workspace = workspaces[0]
        saPolygonPath = arcpy.env.workspace + os.sep + "SAPOLYGON"
        if not arcpy.Exists(saPolygonPath):
            AddMsgAndPrint("\t The SSURGO SAPOLYGON layer was not found -- Cannot determine Overlap\n",2)
            return False

        # Intersect the soils and input layer
        outIntersect = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Intersect_analysis([muLayer,saPolygonPath], outIntersect,"ALL","","INPUT")

        totalMUacres = sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"))]) / 4046.85642
        totalIntAcres = sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"))]) / 4046.85642

        # All features are within the geodata extent
        if int(totalMUacres) == int(totalIntAcres):
            AddMsgAndPrint("\tALL polygons are within Geodata Extent",0)

            if arcpy.Exists(outIntersect):arcpy.Delete_management(outIntersect)
            del soilsFolder, workspaces,saPolygonPath,totalMUacres,totalIntAcres
            return True

        # some features are outside the geodata extent.  Warn the user
        elif totalIntAcres < totalMUacres and totalIntAcres > 1:
            prctOfCoverage = round((totalIntAcres / totalMUacres) * 100,1)

            if prctOfCoverage > 50:
                AddMsgAndPrint("\tWARNING: There is only " + str(prctOfCoverage) + " % coverage between your area of interest and MUPOLYGON Layer",1)
                AddMsgAndPrint("\tWARNING: " + splitThousands(round((totalMUacres-totalIntAcres),1)) + " .ac will not be accounted for",1)

                if arcpy.Exists(outIntersect):arcpy.Delete_management(outIntersect)
                del soilsFolder, workspaces,saPolygonPath,totalMUacres,totalIntAcres
                return True

            elif prctOfCoverage < 1:
                AddMsgAndPrint("\tArea of interest is outside of your Geodata Extent.  Cannot proceed with analysis",2)

                if arcpy.Exists(outIntersect):arcpy.Delete_management(outIntersect)
                del soilsFolder, workspaces,saPolygonPath,outIntersect,totalMUacres,totalIntAcres
                return False

            else:
                AddMsgAndPrint("\tThere is only " + str(prctOfCoverage) + " % coverage between your area of interest and Geodata Extent",2)

                if arcpy.Exists(outIntersect):arcpy.Delete_management(outIntersect)
                del soilsFolder, workspaces,saPolygonPath,outIntersect,totalMUacres,totalIntAcres
                return False

        # There is no overlap
        else:
            AddMsgAndPrint("\tALL polygons are ouside of your Geodata Extent.  Cannot proceed with analysis",2)

            if arcpy.Exists(outIntersect):arcpy.Delete_management(outIntersect)
            del soilsFolder, workspaces,saPolygonPath,outIntersect,totalMUacres,totalIntAcres
            return False

    except:
        AddMsgAndPrint(" \nFailed to determine overlap with " + muLayer + ". (determineOverlap)",1)
        errorMsg()

# ===================================================================================
def getZoneField(analysisType):
    # This function will return a field name based on the analysis type that
    # was chosen by the user.  If analysis type is MUKEY, then MUKEY is returned if
    # it exists, otherwise a newly created field "MLRA_Temp" will be returned.
    # "MLRA_Temp" will be returned for MLRA analysis type
    # OID field will be returned for each polygon

    try:
        mlraTempFld = "MLRA_Temp"

        if analysisType.find('Mapunit (MUKEY)') > -1:

            if len(arcpy.ListFields(muLayer,"MUKEY")) > 0:
                return "MUKEY"
            else:
                AddMsgAndPrint("\nAnalysis Cannot be done by Mapunit since MUKEY is missing.",1)
                AddMsgAndPrint("Proceeding with analysis using MLRA ",1)

                if not len(arcpy.ListFields(muLayer,mlraTempFld)) > 0:
                    arcpy.AddField_management(muLayer,mlraTempFld,"TEXT", "", "", 15)

            # Calculate the new field using an UpdateCursor b/c Calc tool threw an 000728 error
            with arcpy.da.UpdateCursor(muLayer,mlraTempFld) as cursor:
                for row in cursor:
                    row[0] = "MLRA_Mapunit"
                    cursor.updateRow(row)

            return "MLRA_Temp"

        elif analysisType.find('MLRA Mapunit') > -1:
            if not len(arcpy.ListFields(muLayer,mlraTempFld)) > 0:
                arcpy.AddField_management(muLayer,mlraTempFld,"TEXT", "", "", 15)
                arcpy.RefreshCatalog(outputFolder)

            # Calculate the new field using an UpdateCursor b/c Calc tool threw an 000728 error
            with arcpy.da.UpdateCursor(muLayer,mlraTempFld) as cursor:
                for row in cursor:
                    row[0] = "MLRA_Mapunit"
                    cursor.updateRow(row)

            return "MLRA_Temp"

        # Analysis Type = Polygon
        else:
            AddMsgAndPrint("\nWARNING Reporting by polygon might be very verbose")
            return idField

    except:
        errorMsg()
        return False

# ===================================================================================
def FindField(layer,chkField):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that name; otherwise return ""
    # Set workspace before calling FindField

    try:

        if arcpy.Exists(layer):

            theDesc = arcpy.Describe(layer)
            theFields = theDesc.fields
            theField = theFields[0]

            for theField in theFields:

                # Parses a fully qualified field name into its components (database, owner name, table name, and field name)
                parseList = arcpy.ParseFieldName(theField.name) # (null), (null), (null), MUKEY

                # choose the last component which would be the field name
                theFieldname = parseList.split(",")[len(parseList.split(','))-1].strip()  # MUKEY

                if theFieldname.upper() == chkField.upper():
                    return theField.name

            return False

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return False

    except:
        errorMsg()
        return False

# ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

# ===================================================================================
def getMapunitInfo(muDict,mukeyList):
# This function will try to retrieve the MUNAME and AREASYMBOL from the most current
# SSURGO dataset in MLRAGeodata.  The function returns a dictionary with the following
# attributes:  '23569':("Dubuque silt loam, 0 to 10 percent slopes",43546.6,10,43,5,WI025)
# If MUKEY is not found then a dictionary should still be passed over but will not contain
# MUNAME and AREASYMBOL

    try:

        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\"soils\" folder was not found in your MLRAGeodata Folder -- Cannot get MUNAME & AREASYMBOL Information\n",2)
            return False
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"SSURGO.gdb\" was not found in the soils folder -- Cannot get MUNAME & AREASYMBOL Information\n",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\tThere are muliple \"SSURGO_*.gdb\" in the soils folder -- Cannot get MUNAME & AREASYMBOL Information\n",2)
            return False

        arcpy.env.workspace = workspaces[0]

        """ --------------------- Setup MUPOLYGON ------------------------------ """
        fcList = arcpy.ListFeatureClasses("MUPOLYGON","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\tMUPOLYGON feature class was not found in the SSURGO.gdb File Geodatabase -- Cannot get AREASYMBOL Information\n",2)
            return False

        mukeyField = FindField(fcList[0],"MUKEY")
        areaSymField = FindField(fcList[0],"AREASYMBOL")

        if not mukeyField or not areaSymField:
            AddMsgAndPrint("\MUPOLYGON layer is missing necessary fields -- Cannot get AREASYMBOL Information\n",2)
            return False

        muPolyPath = arcpy.env.workspace + os.sep + fcList[0]

        """ --------------------- Setup Mapunit Table ------------------------------ """
        muTable = arcpy.ListTables("mapunit", "ALL")

        if not len(muTable):
            AddMsgAndPrint("\Mapunit table was not found in the SSURGO.gdb File Geodatabase -- Cannot get MUNAME Information\n",2)
            return False

        munameField = FindField(muTable[0],"MUNAME")

        if not munameField:
            AddMsgAndPrint("\mapunit table is missing necessary fields -- Cannot get MUNAME Information\n",2)
            return False

        muTablePath = arcpy.env.workspace + os.sep + muTable[0]

        for key in mukeyList:

            if not muDict.has_key(key):
                muPolyexpression = arcpy.AddFieldDelimiters(muPolyPath,mukeyField) + " = '" + key + "'"  # expression to select the MUKEY from mupolygon layer
                areasym = [row[0] for row in arcpy.da.SearchCursor(muPolyPath, ("AREASYMBOL"), where_clause = muPolyexpression)]  # This will also serve as an MU count

                # MUKEY was not found in MUPOLYGON so muname and areasym cannot be retrieved
                if len(areasym) == 0:
                    AddMsgAndPrint("\t\tMUKEY: " + str(key) + " does not exist",1)
                    acres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"), where_clause = muPolyexpression)]) / 4046.85642))

                    # since the index position for the muDict also serves as the polygon count but
                    tempExpression = arcpy.AddFieldDelimiters(muLayer,zoneField) + " = '" + key + "'"  # expression to select the MUKEY from mupolygon layer
                    mukeyCount = [row[0] for row in arcpy.da.SearchCursor(muLayer, (zoneField), where_clause = muPolyexpression)]  # This will also serve as an MU count
                    areasym = " N/A "
                    muname = "Mapunit Name NOT Available"
                    muDict[key] = (muname,acres,len(mukeyCount),len(muname),len(key),areasym)  # '23569':("",43546.6,10,0,5,"")
                    del acres,tempExpression,mukeyCount,areasym,muname
                    continue

                acres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"), where_clause = muPolyexpression)]) / 4046.85642))
                muTableExpression = arcpy.AddFieldDelimiters(muTablePath,mukeyField) + " = '" + key + "'"
                muname = [row[0] for row in arcpy.da.SearchCursor(muTablePath, ("MUNAME"), where_clause = muTableExpression)]
                muDict[key] = (muname[0],acres,len(areasym),len(muname[0]),len(key),areasym[0])  # '23569':("Dubuque silt loam, 0 to 10 percent slopes",43546.6,10,43,5,WI025)
                del muPolyexpression, areasym, acres, muTableExpression, muname

        if len(muDict) > 0:
            return muDict
        else:
            return False

    except:
        errorMsg()
        return False

## ===================================================================================
def getComponents(mukeyID):

    try:
        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\t\"soils\" folder was not found in your MLRAGeodata Folder -- Cannot get Component Information\n",2)
            return ""
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\t\"SSURGO.gdb\" was not found in the soils folder -- Cannot get Component Information\n",2)
            return ""

        if len(workspaces) > 1:
            AddMsgAndPrint("\t\t There are muliple \"SSURGO_*.gdb\" in the soils folder -- Cannot get Component Information\n",2)
            return ""

        arcpy.env.workspace = workspaces[0]

        compTable = arcpy.ListTables("component", "ALL")

        if not len(compTable):
            AddMsgAndPrint("\t\t\"component\" table was not found in the SSURGO.gdb File Geodatabase -- Cannot get Component Information \n",2)
            return ""

        cokeyField = FindField(compTable[0],"cokey")

        if not cokeyField:
            AddMsgAndPrint("\t\t\"component\" table is missing necessary fields -- Cannot get Component Information \n",2)
            return ""

        compFields = ["compname","comppct_r","slope_r","cokey"]

        compDict = dict()
        compTablePath = arcpy.env.workspace + os.sep + compTable[0]
        expression = arcpy.AddFieldDelimiters(compTablePath,zoneField) + " = '" + mukeyID + "'"
        cokeyField = FindField(compTablePath,"cokey")
        cokeys = set([row[0] for row in arcpy.da.SearchCursor(compTablePath, (cokeyField), where_clause = expression)])

        # No components were selected using the mukeyID that was passed in
        if not len(cokeys) > 0:
            return ""

        for key in cokeys:

            if not compDict.has_key(key):
                expression = arcpy.AddFieldDelimiters(compTablePath,cokeyField) + " = '" + key + "'"

                with arcpy.da.SearchCursor(compTablePath, (compFields), where_clause = expression) as cursor:

                    for row in cursor:
                        compname = row[0]
                        compPct = row[1]
                        slopeRV = row[2]
                        compDict[key] = (compPct,compname,slopeRV,len(compname),len(str(compPct)))  #compPct goes first in order to order descendingly
                        del compname,compPct,slopeRV

        # strictly for formatting
        # sort the compDict based on compPct; converts the dictionary into a tuple by default since you can't order a dictionary.
        # in essence what you get is a representation of a dictionary in the form of a tuple
        compPctSorted = sorted(compDict.items(), key=operator.itemgetter(1),reverse=True)  # [(u'9006369', (65, u'Hillon', 17.0, 6, 2)), (u'9006370', (30, u'Joplin', 12.0, 6, 2)), (u'9006372', (2, u'Rock outcrop', None, 12, 1))]
        maxCompNameLength = sorted([coinfo[3] for cokey,coinfo in compDict.iteritems()],reverse=True)[0]
        maxCompPctLength = sorted([coinfo[4] for cokey,coinfo in compDict.iteritems()],reverse=True)[0]

        del soilsFolder, workspaces, compTable, cokeyField, compFields, compTablePath, expression, cokeys

        # if compDict has values in it reformat them
        if len(compDict):
            finalCompList = list()

            for compinfo in compPctSorted:

                # i.e. (u'9006369', (65, u'Hillon', 17.0, 6, 2))
                firstSpace = " " * (maxCompNameLength - len(compinfo[1][1]))
                secondSpace = " "  * (2 - len(str(compinfo[1][0])))
                thirdSpace = " " * (maxCompPctLength - len(str(compinfo[1][0])))

                if compinfo[1][2] is None:
                    compSlp = "Slope N/A"
                else:
                    compSlp = str(int(compinfo[1][2])) + "% Slope RV"

                #finalCompList.append(compinfo[1][1] + firstSpace + " -- " + str(compinfo[1][0]) + secondSpace + " comp% " + thirdSpace + " -- " + compSlp)
                finalCompList.append(compinfo[1][1] + firstSpace + " -- " + str(compinfo[1][0]) + secondSpace + " comp% " + " -- " + compSlp)
                del firstSpace,secondSpace,compSlp

            del compDict
            return finalCompList

        else:
            return ""

    except:
        errorMsg()
        return ""

# ===================================================================================
def getSlopeMode_ORIGINAL(field,zoneID,slopeRaster):
# This version of getSlopeMode was not used.  NumPy proved to be less efficient.

    try:

        # Isolate polygons to that will have their slope mode calculated
        if field != 'MLRA_Temp':
            where_clause = arcpy.AddFieldDelimiters(muLayerPath,field) + " = '" + zoneID + "'"
            arcpy.MakeFeatureLayer_management(muLayer, "modeLyr", where_clause)

            outModeFC = scratchWS + os.sep + "outMode"

            if arcpy.Exists(outModeFC):
                arcpy.Delete_management(outModeFC)

            arcpy.CopyFeatures_management("modeLyr",outModeFC)
            del where_clause

        else:
            outModeFC = muLayer

        # Extract slope values that correspond to the mukey or AOI above
        arcpy.env.extent = outModeFC
        arcpy.env.snapRaster = slopeRaster
        extract = ExtractByMask(slopeRaster,outModeFC)

        # Convert the slope extraction to Int
        intExtract = Int(extract)
        intOut = scratchWS + os.sep + "intExtract"

        if arcpy.Exists(intOut):
            arcpy.Delete_management(intOut)

        intExtract.save(intOut)

        # Build Raster Attribute table......just in case
        arcpy.BuildRasterAttributeTable_management(intOut, "Overwrite")

        # Make sure both VALUE and COUNT fields are present
        valueField = FindField(intOut,"VALUE")
        countField = FindField(intOut,"COUNT")

        if not valueField:
            AddMsgAndPrint("\tVALUE field is missing from intExtract Raster",2)
            return ""

        if not countField:
            AddMsgAndPrint("\tCOUNT field is missing from intExtract Raster",2)
            return ""

        # Extract the highest Integer Slope value
        fields = [valueField, countField]
        sql_expression = (None, 'ORDER BY COUNT DESC')
        maxModeInt = [row[0] for row in arcpy.da.SearchCursor(intOut, (fields),sql_clause=sql_expression)][0]

        trueStatement = "\"" + valueField + "\" >= " + str(maxModeInt) + " AND \"" + valueField + "\" <" + str(maxModeInt + 1)
        outCon = Con(intOut, slopeRaster, "", trueStatement)

        # dict will contain only the slope values that
        modeDict = dict()  #{41.3: 2, 41.6: 1, 41.7: 4}
        myArray = arcpy.RasterToNumPyArray(outCon)
        [rows,cols] = myArray.shape

        """ -------------------------------- Evaluate All Cells in an NUMPY Array ----------------------- """
        # Go throuch each cell in the extracted raster and count how many cells
        # are greater than or equal to the maxModeInt but less than the maxModeInt + 1
        for j in range(0,rows-1):
            for i in range(0,cols-1):

                if myArray[j,i] >= maxModeInt and myArray[j,i] < maxModeInt + 1:

                    # converts 41.34569 to 41.3
                    key = float(str(myArray[j,i])[:str(myArray[j,i]).find(".") + 2])

                    if not modeDict.has_key(key):
                        modeDict[key] = 1
                    else:
                        modeDict[key] += 1

                    del key

        # sort the modeDict based on the highest frequency; converts the dictionary into a tuple by default since you can't order a dictionary.
        # {41.3: 2, 41.6: 1, 41.7: 4, 41.9: 4, 41.1: 4}  --->   [(41.9, 4), (41.1, 4), (41.7, 4), (41.3, 2), (41.6, 1)]
        sortByOccurence = sorted(modeDict.items(), key=operator.itemgetter(1),reverse=True)

        # Do a second level sort to assure that the HIGHEST Slope mode is chosen
        # [(41.9, 4), (41.7, 4), (41.1, 4), (41.3, 2), (41.6, 1)]
        maxModeFloat = sorted(sortByOccurence, key=lambda x: x[1], reverse=True)

        # Delete everything necessary
        if arcpy.Exists(outModeFC):
            arcpy.Delete_management(outModeFC)

        if arcpy.Exists(intOut):
            arcpy.Delete_management(intOut)

        del outModeFC, extract, intExtract, intOut, valueField, countField, fields, sql_expression, modeDict, myArray, [rows,cols], sortByOccurence

        if maxModeFloat[0][0] > 0:
            return maxModeFloat[0][0]

        else:
            AddMsgAndPrint("\n\t\tMax Mode Float is less than 0",2)
            return ""

    except:
        errorMsg()
        return ""

# ===================================================================================
def getSlopeMode(field,zoneID,slopeRaster):

    try:
        bMlraTemp = False

        # Analysis Mode is MUKEY
        if field != 'MLRA_Temp':
            arcpy.SetProgressorLabel("Computing Slope Mode for MUKEY: " + str(zoneID))

            # Isolate polygons to a layer that will have their slope mode calculated
            if bFeatureLyr:
                arcpy.MakeFeatureLayer_management(muLayerExtent,"tempMUKEYlayer")
            else:
                arcpy.MakeFeatureLayer_management(muLayer, "tempMUKEYlayer")

            where_clause = arcpy.AddFieldDelimiters("tempMUKEYlayer",field) + " = '" + zoneID + "'"
            arcpy.SelectLayerByAttribute_management("tempMUKEYlayer","NEW_SELECTION",where_clause)

            # Convert the mapunit polys from the layer above and convert it to a temporary FC
            #outModeFC = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
            outModeFC = arcpy.env.scratchGDB + os.sep + "mode_" + str(zoneID)
            arcpy.CopyFeatures_management("tempMUKEYlayer",outModeFC)

            arcpy.SelectLayerByAttribute_management("tempMUKEYlayer","CLEAR_SELECTION")
            arcpy.Delete_management("tempMUKEYlayer")
            bMlraTemp = True

        # Analysis Mode is MLRA
        else:
            # set outModeFC the same as muLayerPath
            arcpy.SetProgressorLabel("Computing Slope Mode")
            if bFeatureLyr:
                outModeFC = muLayerExtent
            else:
                outModeFC = muLayerPath

        # slope raster extraction by the polys of interest
        outExtract = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.env.extent = outModeFC
        arcpy.env.mask = outModeFC

        if arcpy.Exists(outExtract):
            arcpy.Delete_management(outExtract)

        descRaster = arcpy.Describe(slopeRaster)

        # Add 0.5 to slope layer and convert to Integer if slopeRaster is floating
        if not descRaster.isInteger:
            arcpy.env.mask = outModeFC
            arcpy.env.cellSize = descRaster.MeanCellWidth
            arcpy.env.snapRaster = slopeRaster

            outExtractByMask = Int(Plus(slopeLayerName,0.5))
            outExtractByMask.save(outExtract)

        # slope layer is already in Integer; extract by mask
        else:
            outExtractByMask = ExtractByMask(slopeRaster,outModeFC)
            outExtractByMask.save(outExtract)

        # Build Raster Attribute table......just in case
        arcpy.BuildRasterAttributeTable_management(outExtract, "Overwrite")

        # Make sure both VALUE and COUNT fields are present
        valueField = FindField(outExtract,"VALUE")
        countField = FindField(outExtract,"COUNT")

        if not valueField:
            AddMsgAndPrint("\tVALUE field is missing from intExtract Raster",2)
            return ""

        if not countField:
            AddMsgAndPrint("\tCOUNT field is missing from intExtract Raster",2)
            return ""

        # Extract the highest Integer Slope value
        fields = [valueField, countField]
        sql_expression = (None, 'ORDER BY COUNT DESC')
        maxModeInt = [row[0] for row in arcpy.da.SearchCursor(outExtract, (fields),sql_clause=sql_expression)][0]
        del fields, sql_expression

        if bMlraTemp:
            if arcpy.Exists(outModeFC):
                arcpy.Delete_management(outModeFC)

        if arcpy.Exists(outExtract):
            arcpy.Delete_management(outExtract)

        return maxModeInt

    except:
        AddMsgAndPrint("\n\nCheck out: " + outModeFC + " : " + str(zoneID),2)
        errorMsg()
        return ""

# ===================================================================================
def processAdjacentComponents(zoneField):

    try:
        AddMsgAndPrint("\nMajor Components mapped in adjacent polygons:",0)

        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\"soils\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"SSURGO.gdb\" was not found in the elevation folder",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\tThere are multiple \"SSURGO_*.gdb\" in the soils folder",2)
            return False

        # Set workspace to the SSURGO FGDB
        arcpy.env.workspace = workspaces[0]

        """ -------------------------------------- Setup MUPOLYGON ---------------------------------------- """
        fcList = arcpy.ListFeatureClasses("MUPOLYGON","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\tMUPOLYGON feature class was not found in the SSURGO.gdb File Geodatabase",2)
            return False

        muPolygonPath = arcpy.env.workspace + os.sep + fcList[0]
        mukeyField = FindField(fcList[0],"mukey")

        if not mukeyField:
            AddMsgAndPrint("\tMUPOLYGON feature class is missing necessary fields",2)
            return False

        """ ---------------------------------------- Setup Component Table ----------------------------------- """
        compTable = arcpy.ListTables("component", "ALL")

        if not len(compTable):
            AddMsgAndPrint("\tcomponent table was not found in the SSURGO.gdb File Geodatabase",2)
            return False

        compName = FindField(compTable[0],"compname")
        compMukey = FindField(compTable[0],"mukey")
        majorField = FindField(compTable[0],"majcompflag")

        if not compName:
            AddMsgAndPrint("\tComponent Table is missing necessary fields",2)
            return False

        if not compMukey:
            AddMsgAndPrint("\tComponent Table is missing necessary fields",2)
            return False

        if not majorField:
            AddMsgAndPrint("\tComponent Table is missing necessary fields",2)
            return False

        compTablePath = arcpy.env.workspace + os.sep + compTable[0]
        compFields = ["compname"]

        compTablefields = arcpy.ListFields(compTablePath)

        # Create a fieldinfo object
        fieldinfo = arcpy.FieldInfo()

        # Iterate through the fields and set them to fieldinfo
        for field in compTablefields:
            if field.name == compName:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            elif field.name == compMukey:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            else:
                fieldinfo.addField(field.name, field.name, "HIDDEN", "")

        majCompFlagYes = arcpy.AddFieldDelimiters(compTablePath,majorField) + " = 'Yes'"

        compView = "comp_view"
        if arcpy.Exists(compView):
            arcpy.Delete_management(compView)

        # The created component_view layer will have fields as set in fieldinfo object
        arcpy.MakeTableView_management(compTablePath, compView, majCompFlagYes, "", fieldinfo)

        """ ------------------------------------ Buffer muLayer by 1m -------------------------------------- """
        # Create an outer buffer of 1m around the muLayer to get a list of adjacent MUKEYs
        outBuffer = scratchWS + os.sep + "soilBuffer"
        if arcpy.Exists(outBuffer):
            arcpy.Delete_management(outBuffer)

        arcpy.Buffer_analysis(muLayer,outBuffer,"1 Meter","OUTSIDE_ONLY")

        # Add MUKEY_OG b/c MUKEY will be added after the interstect from the MUPOLYGON
        if arcpy.ListFields(outBuffer, "MUKEY") > 0:
            mukeyOGfield = "MUKEY_OG"
            arcpy.AddField_management(outBuffer,mukeyOGfield,"TEXT", "", "" , 30)
            expression = "!" + zoneField + "!"
            arcpy.CalculateField_management(outBuffer,mukeyOGfield,expression,"PYTHON_9.3")
            arcpy.DeleteField_management(outBuffer,"MUKEY")
            del mukeyOGfield, expression

        """ --------------------------- Intersect the buffered output with SSURGO polygons -------------------- """
        outIntersect = scratchWS + os.sep + "soilIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        arcpy.Intersect_analysis([muPolygonPath,outBuffer], outIntersect,"ALL","","INPUT")

        # Explore the "Polygon Neighbors tool"

        # Return False if intersect resulted in empty geometry
        totalIntPolys = int(arcpy.GetCount_management(outIntersect).getOutput(0))

        if not totalIntPolys > 0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayer) + " and 'MUPOLYGON' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)
            return False

        if zoneField != "MLRA_Temp":
            mukeyField = "MUKEY_OG"
        else:
            mukeyField = "MUKEY"

        """ --------------------- Report Adjacent Mapunit Components by MUKEY ------------------------------ """
        # Report by MUKEY
        if zoneField != "MLRA_Temp":

            muLayerUniqueMukeys = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (mukeyField))])

            # iterate through every unique muLayer MUKE
            for mukey in muLayerUniqueMukeys:

                # Report results by MUNAME - MUKEY - Areasymbol
                if bMunamePresent and bAreasymPresent and bMukeyPresent:
                    spaceAfter = " " * (maxMukeyLength - len(mukey))
                    muName = muDict.get(mukey)[0]
                    areaSymbol = muDict.get(mukey)[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + mukey + spaceAfter + "  --  " + muName,0)
                    theTab = "\t" * 2
                    del spaceAfter, muName, areaSymbol

                # Report results only by MUKEY
                else:
                    AddMsgAndPrint("\n\t" + mukey,0)
                    theTab = "\t" * 2

                intersectLayer = "intersectLayer"
                if arcpy.Exists(intersectLayer):
                    arcpy.Delete_management(intersectLayer)

                arcpy.MakeFeatureLayer_management(outIntersect,intersectLayer)

                where_clause = '"MUKEY_OG"' + " = '" + mukey + "'"
                arcpy.SelectLayerByAttribute_management(intersectLayer, "NEW_SELECTION", where_clause)

                """ ------------  First summary Statistics to summarize # of unique mukeys in the intersected layer ------------ """
                outStatsTable = scratchWS + os.sep + "summary1"

                if arcpy.Exists(outStatsTable):
                    arcpy.Delete_management(outStatsTable)

                # Get the ShapeArea field from the joined table
                shpAreaFld = [f.name for f in arcpy.ListFields(intersectLayer,"*Shape_Area")][0]
                caseField = [f.name for f in arcpy.ListFields(intersectLayer,"MUKEY")][0]
                statsField = [[shpAreaFld, "SUM"]]

                # Do a summary statistics on the joined table. Sum up the acres of all unique components
                arcpy.Statistics_analysis(intersectLayer, outStatsTable, statsField, caseField)

                # Delete these 3 variables since they will be declared again.
                del shpAreaFld, caseField, statsField

                # Join summarized table above to get component name
                outCompView_joined = scratchWS + os.sep + "outCompView_" + str(mukey)

                if arcpy.Exists(outCompView_joined):
                    arcpy.Delete_management(outCompView_joined)

                # join the 1st summary and components to get component name and ALL Major components, not just 1.
                arcpy.AddJoin_management(compView,"MUKEY",outStatsTable,"MUKEY","KEEP_COMMON")
                arcpy.CopyRows_management(compView, outCompView_joined)
                arcpy.RemoveJoin_management(compView)

                """ -----------------  Clear the selection of the Intersect Layer and delete it --------------------------- """
                arcpy.SelectLayerByAttribute_management(intersectLayer, "CLEAR_SELECTION")

                if arcpy.Exists(intersectLayer):
                    arcpy.Delete_management(intersectLayer)

                """ ----------------------  Second summary Statistics to summarize joined table --------------------------- """
                outStatsTable2 = scratchWS + os.sep + "summary2"
                compField = [f.name for f in arcpy.ListFields(outCompView_joined,"*compname")][0]
                shpAreaFld = [f.name for f in arcpy.ListFields(outCompView_joined,"*Shape_Area")][0]
                statsField = [[shpAreaFld, "SUM"]]

                if arcpy.Exists(outStatsTable2):
                    arcpy.Delete_management(outStatsTable2)

                # Do a summary statistics on the joined table. Sum up the acres of all unique components
                arcpy.Statistics_analysis(outCompView_joined, outStatsTable2, statsField, compField)

                if arcpy.Exists(outCompView_joined):
                    arcpy.Delete_management(outCompView_joined)

                # Delete these 3 variables since they will be declared again.
                del compField, shpAreaFld, statsField

                # Dict to collect necessary comp information
                #{u'Absher': (6, 3),'Hillon': (6, 22),'Joplin': (6, 37)}
                compDict = dict()

                compField = [f.name for f in arcpy.ListFields(outStatsTable2,"*compname")][0]
                shpAreaFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*Shape_Area")][0]

                # Sum up all of the acres for this MUKEY_OG value
                totalMukeyCompAcres = sum([row[0] for row in arcpy.da.SearchCursor(outStatsTable2, (shpAreaFld))]) / 4046.85642

                sql_expression = (None, 'ORDER BY ' + shpAreaFld + ' DESC')
                fields = [compField,shpAreaFld]

                # Go through each record in outStatsTable and get only the 10 highest comps and name lengths.

                with arcpy.da.SearchCursor(outStatsTable2, (fields),sql_clause=sql_expression) as cursor:
                    for row in cursor:

                        if not compDict.has_key(row[0]):
                            adjCompPercent = int(round(float("%.1f" %(((row[1] / 4046.85642) / totalMukeyCompAcres) * 100))))
                            compDict[row[0]] = (len(row[0]),adjCompPercent)

                if len(compDict) > 10:
                    compPercentSorted = sorted(compDict.items(), key=lambda comp: comp[1][1],reverse=True)[0:10]  # [(u'Joplin', (6, 37)),(u'Hillon', (6, 22)), (u'Gerdrum', (7, 4))]
                else:
                    compPercentSorted = sorted(compDict.items(), key=lambda comp: comp[1][1],reverse=True)

                maxCompNameLength = sorted([len(comp[0]) for comp in compPercentSorted],reverse=True)[0]

                for compinfo in compPercentSorted:

                    compname = compinfo[0]
                    frequencyPrct = compinfo[1][1]
                    firstSpace = " " * (maxCompNameLength - len(compname))
                    AddMsgAndPrint(theTab + compname + firstSpace + " -- " + str(frequencyPrct) + " %",1)
                    del compname, frequencyPrct, firstSpace

                # inform the user that there are additional components not listed here
                if len(compDict) > 10:
                    AddMsgAndPrint("\n\t" + "WARNING: There are " + str(len(compDict) - 10) + " additional unique Major Components that neighbor this mapunit.",1)

                # remove unnecessary layers and variables
                if arcpy.Exists(outStatsTable):
                    arcpy.Delete_management(outStatsTable)

                if arcpy.Exists(outStatsTable2):
                    arcpy.Delete_management(outStatsTable2)

                del intersectLayer, where_clause, outStatsTable, outCompView_joined, outStatsTable2, compDict, compField
                del shpAreaFld, totalMukeyCompAcres, sql_expression, fields, compPercentSorted, maxCompNameLength
            del muLayerUniqueMukeys

            """ ------------------------------------------------------- Report Adjacent Mapunit Components by MLRA Mapunit ------------------------------ """
        else:

            """ ------------ Run a frequency on the intersect results  ------------"""
            outFrequency = scratchWS + os.sep + "outFrquency"
            outCompView_joined = scratchWS + os.sep + "outCompView_Joined"

            if arcpy.Exists(outFrequency):
                arcpy.Delete_management(outFrequency)

            if arcpy.Exists(outCompView_joined):
                arcpy.Delete_management(outCompView_joined)

            # get a frequency on the number of unique adjacent mukeys
            arcpy.Frequency_analysis(outIntersect, outFrequency,["MUKEY"],["Shape_Area"])

            arcpy.AddJoin_management(compView,"MUKEY",outFrequency,"MUKEY","KEEP_COMMON")
            arcpy.CopyRows_management(compView, outCompView_joined)
            arcpy.RemoveJoin_management(compView)

            outStatsTable = scratchWS + os.sep + "adjComp_reportByMapunit"

            if arcpy.Exists(outStatsTable):
                arcpy.Delete_management(outStatsTable)

            # Get the ShapeArea field from the joined table
            shpAreaFld = [f.name for f in arcpy.ListFields(outCompView_joined,"*Shape_Area")][0]
            caseField = [f.name for f in arcpy.ListFields(outCompView_joined,"*compname")][0]
            statsField = [[shpAreaFld, "SUM"]]

            # Sum up all of the component acres
            totalCompAcres = sum([row[0] for row in arcpy.da.SearchCursor(outCompView_joined, (shpAreaFld))]) / 4046.85642

            # Do a summary statistics on the joined table. Sum up the acres of all unique components
            arcpy.Statistics_analysis(outCompView_joined, outStatsTable, statsField, caseField)

            # Dict to collect necessary comp information
            #{u'Absher': (6, 3),'Hillon': (6, 22),'Joplin': (6, 37)}
            compDict = dict()

            # Get the ShapeArea field for the outStats table i.e. SUM_test_buffer_int_freq_Shape_Area
            outStatsshpAreaFld = [f.name for f in arcpy.ListFields(outStatsTable,"*Shape_Area")][0]

            sql_expression = (None, 'ORDER BY ' + outStatsshpAreaFld + ' DESC')
            fields = [caseField,outStatsshpAreaFld]

            # Go through each record in outStatsTable and get only the 10 highest comps and name lengths.

            with arcpy.da.SearchCursor(outStatsTable, (fields),sql_clause=sql_expression) as cursor:
                for row in cursor:

                    if not compDict.has_key(row[0]):
                        adjCompPercent = int(round(float("%.1f" %(((row[1] / 4046.85642) / totalCompAcres) * 100))))
                        compDict[row[0]] = (len(row[0]),adjCompPercent)

            if len(compDict) > 10:
                compPercentSorted = sorted(compDict.items(), key=lambda comp: comp[1][1],reverse=True)[0:10]  # [(u'Joplin', (6, 37)),(u'Hillon', (6, 22)), (u'Gerdrum', (7, 4))]
            else:
                compPercentSorted = sorted(compDict.items(), key=lambda comp: comp[1][1],reverse=True)

            maxCompNameLength = sorted([len(comp[0]) for comp in compPercentSorted],reverse=True)[0]

            for compinfo in compPercentSorted:

                compname = compinfo[0]
                frequencyPrct = compinfo[1][1]
                firstSpace = " " * (maxCompNameLength - len(compname))
                AddMsgAndPrint("\t" + compname + firstSpace + " -- " + str(frequencyPrct) + " %",1)
                del compname, frequencyPrct, firstSpace

            # inform the user that there are additional components not listed here
            if len(compDict) > 10:
                AddMsgAndPrint("\n\t" + "WARNING: There are " + str(len(compDict) - 10) + " additional unique Major Components that neighbor this mapunit.",1)

            for layer in [outStatsTable,outFrequency,outCompView_joined]:
                if arcpy.Exists(layer):
                    arcpy.Delete_management(layer)

            del outFrequency, outCompView_joined, outStatsTable, shpAreaFld, caseField, statsField, totalCompAcres
            del compDict, outStatsshpAreaFld, sql_expression, fields, compPercentSorted, maxCompNameLength

        for layer in [compView,outBuffer,outIntersect]:
            if arcpy.Exists(layer):
                arcpy.Delete_management(layer)

        if len(arcpy.ListFields(muLayer,"acres")) > 0:
            arcpy.DeleteField_management(muLayer,"acres")

        del soilsFolder,workspaces,fcList,muPolygonPath,mukeyField,compTable,compName,compMukey,majorField,compTablePath,
        compFields,compTablefields,fieldinfo,majCompFlagYes,compView,outBuffer,outIntersect,totalIntPolys,zoneField

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processComponentComposition():
# This function will calculate a component composition % of total acres based on the
# SDJR mapunits.  Mapunit acres are first weighted by their component percents and then
# summarized by component name and their new acre sum.  The new acre sum is divided by the
# total acres of all mapunits to compute new component percent.  All components are calculated!

    try:
        AddMsgAndPrint("\nComponent Composition Percent -- Weighted by Area",0)

        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\"soils\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"SSURGO.gdb\" was not found in the elevation folder",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\tThere are multiple \"SSURGO_*.gdb\" in the soils folder",2)
            return False

        # Set workspace to the SSURGO FGDB
        arcpy.env.workspace = workspaces[0]

        """ ---------------------------------------- Setup Component Table ----------------------------------- """
        compTable = arcpy.ListTables("component", "ALL")

        if not len(compTable):
            AddMsgAndPrint("\tcomponent table was not found in the SSURGO.gdb File Geodatabase",2)
            return False

        compName = FindField(compTable[0],"compname")
        compMukey = FindField(compTable[0],"mukey")
        compPrcnt = FindField(compTable[0],"comppct_r")

        if not compName:
            AddMsgAndPrint("\tComponent Table is missing 'compname' field",2)
            return False

        if not compMukey:
            AddMsgAndPrint("\tComponent Table is missing 'mukey' field",2)
            return False

        if not compPrcnt:
            AddMsgAndPrint("\tComponent Table is missing 'comppct_r' field",2)
            return False

        compTablePath = arcpy.env.workspace + os.sep + compTable[0]
        compFields = ["compname"]

        compTablefields = arcpy.ListFields(compTablePath)

        # Create a fieldinfo object
        fieldinfo = arcpy.FieldInfo()

        # Iterate through the fields and set them to fieldinfo
        for field in compTablefields:
            if field.name == compName:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            elif field.name == compMukey:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            elif field.name == compPrcnt:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            else:
                fieldinfo.addField(field.name, field.name, "HIDDEN", "")

        compView = "comp_view"

        # The created component_view layer will have fields as set in fieldinfo object
        arcpy.MakeTableView_management(compTablePath, compView, "", "", fieldinfo)

        """ ---------------------------------------- Setup MuLayer ----------------------------------- """
        # Make a layer from the input muLayer
        tempLayer = "tempLayer"
        if arcpy.Exists(tempLayer):arcpy.Delete_management(tempLayer)

        if bFeatureLyr:
            arcpy.MakeFeatureLayer_management(muLayerExtent,tempLayer)
        else:
            arcpy.MakeFeatureLayer_management(muLayer,tempLayer)

        # Add an acre field if it doesn't exist
        if arcpy.ListFields(tempLayer, "acres") > 0:
            arcpy.DeleteField_management(tempLayer,"acres")
        arcpy.AddField_management(tempLayer,"acres","DOUBLE")

        # Calculate the acres
        acreExpression = "!shape.area@acres!"
        arcpy.CalculateField_management(tempLayer,"acres",acreExpression,"PYTHON_9.3")

        # summarize acres by MUKEY for temp layer; Result will be the unique MUKEYS in the layer with their acres
        statsField = [["acres", "SUM"]]
        outStatsTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(tempLayer, outStatsTable, statsField, "MUKEY")

        # Add 'compacre' field if it doesn't exist to the outStatsTable; This field will contain the
        # acres based on comp% RV.
        if arcpy.ListFields(outStatsTable, "compacres") > 0:
            arcpy.DeleteField_management(outStatsTable,"compacres")
        arcpy.AddField_management(outStatsTable,"compacres","DOUBLE")

        """ ---------------------------------------- Join to component table ----------------------------------- """
        # Join the outStatsTable to the compview table in order to compute new component acres by comp % RV
        arcpy.AddJoin_management(compView,"MUKEY",outStatsTable,"MUKEY","KEEP_COMMON")

        # Need to write the joined table out b/c you can't calculate a field on a right join
        outCompView_joined = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.CopyRows_management(compView, outCompView_joined)
        arcpy.RemoveJoin_management(compView)

        # find fields; field names might have been altered due to a join
        compNameFld = [f.name for f in arcpy.ListFields(outCompView_joined,"*compname")][0]
        compAcresFld = [f.name for f in arcpy.ListFields(outCompView_joined,"*_compacres")][0]
        compPercentFld = [f.name for f in arcpy.ListFields(outCompView_joined,"*comppct_r")][0]
        sumAcreFld = [f.name for f in arcpy.ListFields(outCompView_joined,"*SUM_acres")][0]

        # calculate the compacres field by the individual mapunit acres by their comp percentages
        compAcresExpression = "(float(!" + compPercentFld + "!) / 100) * !" + sumAcreFld + "!"
        arcpy.CalculateField_management(outCompView_joined,compAcresFld,compAcresExpression,"PYTHON_9.3")

        # summarize the outCompView_joined" table by compacres and component name.  This will give the total weighted acres
        # by component %RV for each unique component
        statsField = [[compAcresFld, "SUM"]]
        outStatsTable2 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(outCompView_joined, outStatsTable2, statsField, compNameFld)
        del compNameFld,compAcresFld,compPercentFld,sumAcreFld

        """ ---------------------------------------- Report Results ----------------------------------- """
        # Report the results from the compAcreSummary table. Will use different method to report.

        # find the "SUM_compacres" field
        compAcresFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*compacres")][0]
        compNameFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*compname")][0]

        # Strictly for formatting.  Get the max char length of component name.
        maxCompNameLength = max([len(row[0]) for row in arcpy.da.SearchCursor(outStatsTable2, (compNameFld))])

        # Establish search cursor to iterate through the compname and compacres and sort by comp acres
        sql_expression = (None, 'ORDER BY ' + compAcresFld + ' DESC')
        with arcpy.da.SearchCursor(outStatsTable2, (compNameFld,compAcresFld),sql_clause=sql_expression) as cursor:
            for row in cursor:

                firstSpace = " " * (maxCompNameLength - len(row[0]))

                # Some components may not have comp% RV populated so can't calculate weighted acres
                try:
                    acres = splitThousands(float("%.1f" %(row[1])))
                    compPercent = str(float("%.1f" %((row[1]/totalAcres) * 100))) + " %"
                except:
                    AddMsgAndPrint("\t" + row[0] + firstSpace + " -- " + "Comp % RV NOT Populated",1)
                    continue

                secondSpace = " " * (7 - len(str(compPercent))) # 100.0 %
                AddMsgAndPrint("\t" + row[0] + firstSpace + " -- " + compPercent + secondSpace + " -- " + str(acres) + " ac.",1)
                del firstSpace, acres, compPercent, secondSpace

        """ ---------------------------------------- Clean up ----------------------------------- """
        # Delete temp tables and layers that were used
        toDelete = [compView, tempLayer, outStatsTable, outCompView_joined, outStatsTable2]
        for layer in toDelete:
            if arcpy.Exists(layer):
                arcpy.Delete_management(layer)

        del soilsFolder,workspaces,compTable,compName,compMukey,compPrcnt,compTablePath,compFields
        del fieldinfo,compView,tempLayer,acreExpression,statsField,outStatsTable,outCompView_joined,compAcresExpression
        del outStatsTable2,compAcresFld,compNameFld,maxCompNameLength

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def getElevationSource():
# This function will provide a breakdown of original Elevation Source information
# by intersecting the mulayer with the SSR10_Elevation_Source feature class.
# i.e. LiDAR 1M - 1,000 acres - 80%
# i.e. LiDAR 3M - 300 acres - 20%

    try:
        AddMsgAndPrint("\nOriginal Elevation Source Information:\n",0)

        elevFolder = geoFolder + os.sep + "elevation"

        if not os.path.exists(elevFolder):
            AddMsgAndPrint("\t\"elevation\" folder was not found in your MLRAGeodata Folder",2)
            return False

        arcpy.env.workspace = elevFolder

        workspaces = arcpy.ListWorkspaces("Elevation.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\tElevation data was not found in the elevation folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        elevSource = arcpy.ListFeatureClasses("SSR10_Elevation*","Polygon")

        if not len(elevSource):
            AddMsgAndPrint("\tSSR10_Elevation_Source feature class was not found in the Elevation File Geodatabase",2)
            return False

        sourceField = FindField(elevSource[0],"Source")

        if not sourceField:
            AddMsgAndPrint("\t feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "elevIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        # Intersect the mulayer with the SSR10 Elevation Source
        arcpy.Intersect_analysis([[muLayer,1],[elevSource[0],2]],outIntersect,"ALL","","")

        # Make sure there are output polygons as a result of intersection
        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'Ecoregion' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return False

        elevSourceDict = dict()
        uniqueSource = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (sourceField))])  # List containing unique 'Source' values

        # iterate through each unique value and get an area sum in order to compute % of total area; add everything to a dictionary for reporting and formatting
        for source in uniqueSource:

            if not elevSourceDict.has_key(source):

                expression = arcpy.AddFieldDelimiters(outIntersect,sourceField) + " = '" + source + "'"
                sourceAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))
                sourcePcntAcres = float("%.1f" %((sourceAcres / totalAcres) * 100))
                elevSourceDict[source] = (len(source),str(splitThousands(sourceAcres)),sourcePcntAcres,len(str(splitThousands(sourceAcres))))
                del expression, sourceAcres, sourcePcntAcres

        # strictly for formatting
        maxSourceNameLength = sorted([sourceinfo[0] for source,sourceinfo in elevSourceDict.iteritems()],reverse=True)[0]
        maxSourceAcreLength = sorted([sourceinfo[3] for source,sourceinfo in elevSourceDict.iteritems()],reverse=True)[0]

        # sort the elevSourceDict based on the highest % acres; converts the dictionary into a tuple by default since you can't order a dictionary.
        # item #1 becomes len(source) and NOT str(splitThousands(sourceAcres)) as in the dictionary
        sourceAcresSorted = sorted(elevSourceDict.items(), key=lambda source: source[1][2],reverse=True)

        for sourceInfo in sourceAcresSorted:
            source = sourceInfo[0]
            sourceAcres = sourceInfo[1][1]
            sourcePercent = sourceInfo[1][2]
            firstSpace = " " * (maxSourceNameLength - len(source))
            secondSpace = " " * (maxSourceAcreLength - sourceInfo[1][3])

            AddMsgAndPrint("\t" + source + firstSpace + " -- " + sourceAcres + " ac." + secondSpace + " -- " + str(sourcePercent) + " %" ,1)
            del source, sourceAcres, sourcePercent, firstSpace, secondSpace

        del elevFolder, workspaces, elevSource, sourceField, elevSourceDict, uniqueSource, maxSourceNameLength, maxSourceAcreLength, sourceAcresSorted

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processElevation():

    try:
        elevFolder = geoFolder + os.sep + "elevation"

        if not os.path.exists(elevFolder):
            AddMsgAndPrint("\t\"elevation\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = elevFolder

##        # Look for High Resolution elevation data if available
##        workspaces = arcpy.ListWorkspaces("Elevation_HR.gdb", "FileGDB")
##
##        if not len(workspaces) == 0:
##            arcpy.env.workspace = workspaces[0]
##            AddMsgAndPrint("\nElevation Information -- High Resolution:",0)

        # Otherwise use 10m NED
        workspaces = arcpy.ListWorkspaces("Elevation.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\nElevation Information:",0)
            AddMsgAndPrint("\tElevation data was not found in the elevation folder",2)
            return False
        else:
            AddMsgAndPrint("\nElevation Information:",0)
            arcpy.env.workspace = workspaces[0]

        DEMraster = arcpy.ListRasters("DEM_*","GRID")
        DEMrasterPath = arcpy.env.workspace + os.sep + DEMraster[0]  # introduced to substitute DEMraster[0]

        if not len(DEMraster):
            AddMsgAndPrint("\tDEM Grid was not found in the Elevation File Geodatabase",2)
            return False

        # Get the linear unit of the DEM (Feet or Meters)
        rasterUnit = arcpy.Describe(DEMrasterPath).SpatialReference.LinearUnitName

        # Get Linear Units of DEM
        if rasterUnit == "Meter":
            units = "Meters"
            conversion = (3.280839896,"Feet")
        elif rasterUnit == "Foot" or rasterUnit == "Foot_US":
            units = "Feet"
            conversion = (0.3048,"Meters")
        else:
            AddMsgAndPrint("\tCould not determine linear units of DEM",1)
            units = "$$"

        # output Zonal Statistics Table
        outZoneTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

        # Run Zonal Statistics on the muLayer agains the DEM
        # NODATA cells are not ignored;
        # converted DEMraster[0] to DEMrasterPath
        try:
            arcpy.env.extent = muLayer
            arcpy.env.mask = muLayer
            outZSaT = ZonalStatisticsAsTable(muLayer, zoneField, DEMrasterPath, outZoneTable, "DATA", "ALL")
        except:
            if bFeatureLyr:
                arcpy.env.extent = muLayerExtent
                arcpy.env.mask = muLayerExtent
                outZSaT = ZonalStatisticsAsTable(muLayerExtent, zoneField, DEMrasterPath, outZoneTable, "DATA", "ALL")
            else:
                arcpy.env.extent = tempMuLayer
                arcpy.env.mask = tempMuLayer
                outZSaT = ZonalStatisticsAsTable(tempMuLayer, zoneField, DEMrasterPath, outZoneTable, "DATA", "ALL")

        zoneTableFields = [zoneField,"MIN","MAX","MEAN"]
        with arcpy.da.SearchCursor(outZoneTable, zoneTableFields) as cursor:

            for row in cursor:

                min = splitThousands(round(row[1],1))
                max = splitThousands(round(row[2],1))
                mean = splitThousands(round(row[3],1))
                minConv = str(splitThousands(round((row[1] * conversion[0]),1)) + " (" + conversion[1] + ")")
                maxConv = str(splitThousands(round((row[2] * conversion[0]),1)) + " (" + conversion[1] + ")")
                meanConv = str(splitThousands(round((row[3] * conversion[0]),1)) + " (" + conversion[1] + ")")

                if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                    spaceAfter = " " * (maxMukeyLength - len(row[0]))
                    muName = muDict.get(row[0])[0]
                    areaSymbol = muDict.get(row[0])[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + str(row[0]) + spaceAfter + "  --  " + muName,0)
                    theTab = "\t" * 2
                    del spaceAfter, muName, areaSymbol

                # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                    AddMsgAndPrint("\n\t" + row[0],0)
                    theTab = "\t" * 2

                # Zone field was MLRA_Temp
                else:
                    #AddMsgAndPrint("\n")
                    theTab = "\t"

                AddMsgAndPrint(theTab + "MIN:  " + str(min) + " (" + units + ") -- " + minConv,1)
                AddMsgAndPrint(theTab + "MAX:  " + str(max) + " (" + units + ") -- " + maxConv,1)
                AddMsgAndPrint(theTab + "MEAN: "+ str(mean) + " (" + units + ") -- " + meanConv,1)
                del min,max,mean,minConv,maxConv,meanConv,theTab

        if arcpy.Exists(outZoneTable):
            arcpy.Delete_management(outZoneTable)

        del elevFolder,workspaces,DEMraster,rasterUnit,units,outZoneTable,outZSaT,zoneTableFields
        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processSlope():

    try:
        elevFolder = geoFolder + os.sep + "elevation"

        if not os.path.exists(elevFolder):
            AddMsgAndPrint("\t\"elevation\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = elevFolder

##        # Look for High Resolution elevation data if available
##        workspaces = arcpy.ListWorkspaces("Elevation_HR.gdb", "FileGDB")
##
##        if not len(workspaces) == 0:
##            arcpy.env.workspace = workspaces[0]
##            AddMsgAndPrint("\nSlope Information -- High Resolution:",0)

        # Otherwise use 10m NED
        workspaces = arcpy.ListWorkspaces("Elevation.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\nSlope Information:",0)
            AddMsgAndPrint("\tElevation data was not found in the elevation folder",2)
            return False
        else:
            AddMsgAndPrint("\nSlope Information:",0)
            arcpy.env.workspace = workspaces[0]

        slopeRaster = arcpy.ListRasters("Slope_*","GRID")

        if not len(slopeRaster):
            AddMsgAndPrint("\tSlope Raster was not found in the Elevation.gdb File Geodatabase",2)
            return False

        if len(slopeRaster) > 1:
            AddMsgAndPrint("\tMultiple Slope Rasters were found inthe Elevation.gdb File Geodatabase",2)
            return False

        slopeRasterPath = workspaces[0] + os.sep + slopeRaster[0]

        # output Zonal Statistics Table
        outZoneTable = scratchWS + os.sep +"slopeZoneTable"

        # Delete Zonal Statistics Table if it exists
        if arcpy.Exists(outZoneTable):
            arcpy.Delete_management(outZoneTable)

        # Run Zonal Statistics on the muLayer against the DEM
        # NODATA cells are not ignored;
        try:
            arcpy.env.extent = muLayer
            arcpy.env.mask = muLayer
            outZSaT = ZonalStatisticsAsTable(muLayer, zoneField, slopeRaster[0], outZoneTable, "DATA", "ALL")
        except:
            if bFeatureLyr:
                arcpy.env.extent = muLayerExtent
                arcpy.env.mask = muLayerExtent
                outZSaT = ZonalStatisticsAsTable(muLayerExtent, zoneField, slopeRaster[0], outZoneTable, "DATA", "ALL")
            else:
                arcpy.env.extent = tempMuLayer
                arcpy.env.mask = tempMuLayer
                outZSaT = ZonalStatisticsAsTable(tempMuLayer, zoneField, slopeRaster[0], outZoneTable, "DATA", "ALL")

        zoneTableFields = [zoneField,"MIN","MAX","MEAN","STD"]
        with arcpy.da.SearchCursor(outZoneTable, zoneTableFields) as cursor:

            for row in cursor:

                zone = row[0]
                min = round(row[1],1)
                max = round(row[2],1)
                mean = round(row[3],1)
                std = round(row[4],1)

                mode = getSlopeMode(zoneField, zone, slopeRasterPath)

                # Failed to calculate mode
                if not mode > -1:
                    mode = "N/A"

                if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                    spaceAfter = " " * (maxMukeyLength - len(zone))
                    muName = muDict.get(zone)[0]
                    areaSymbol = muDict.get(zone)[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + str(zone) + spaceAfter + "  --  " + muName,0)
                    theTab = "\t" * 2
                    del muName,spaceAfter, areaSymbol

                # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                    AddMsgAndPrint("\n\t" + zone,0)
                    theTab = "\t" * 2

                # Zone field was MLRA_Temp
                else:
                    #AddMsgAndPrint("\n")
                    theTab = "\t"

                #AddMsgAndPrint(theTab + "MIN:  " + str(min) + " % Slope",1)
                #AddMsgAndPrint(theTab + "MAX:  " + str(max) + " % Slope",1)
                AddMsgAndPrint(theTab + "MEAN: "+ str(mean) + " % Slope",1)
                AddMsgAndPrint(theTab + "MODE: "+ str(mode) + " % Slope",1)
                AddMsgAndPrint(theTab + "ST.DEV: "+ str(std),1)
                del zone,min,max,mean,mode,std,theTab

        if arcpy.Exists(outZoneTable):
            arcpy.Delete_management(outZoneTable)

##        # delete feature layer if created; can't delete the original muLayer
##        if arcCatalog and arcpy.Exists(tempMuLayer):
##            arcpy.Delete_management(tempMuLayer)

        del elevFolder,workspaces,slopeRaster,slopeRasterPath,outZoneTable,outZSaT,zoneTableFields
        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processAspect():

    try:
        AddMsgAndPrint("\nAspect Information:",0)

        elevFolder = geoFolder + os.sep + "elevation"

        if not os.path.exists(elevFolder):
            AddMsgAndPrint("\t\"elevation\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = elevFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Elevation.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Elevation.gdb\" was not found in the elevation folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        aspectRaster = arcpy.ListRasters("Aspect_10m_*","GRID")

        if not len(aspectRaster):
            AddMsgAndPrint("\t10m Aspect Raster Layer was not found in the Elevation.gdb File Geodatabase",2)
            return False

        if len(aspectRaster) > 1:
            AddMsgAndPrint("\tMultiple Aspect Raster Layer were found inthe Elevation.gdb File Geodatabase",2)
            return False

        # output Zonal Statistics Table
        outTAtable = scratchWS + os.sep +"aspectTAtable"

        # Delete Zonal Statistics Table if it exists
        if arcpy.Exists(outTAtable):
            arcpy.Delete_management(outTAtable)

        # Get the linear unit of the DEM (Feet or Meters)
        rasterUnit = arcpy.Describe(aspectRaster[0]).SpatialReference.LinearUnitName

        # Get Linear Units of DEM
        if rasterUnit == "Meter":
            acreConv = 4046.85642
        elif rasterUnit == "Foot" or rasterUnit == "Foot_US":
            acreConv = 43560
        else:
            AddMsgAndPrint("\tCould not determine linear units of " + aspectRaster[0],1)
            acreConv = 1

        theValueField = FindField(aspectRaster[0],"Value")
        if not theValueField:
            AddMsgAndPrint("\tAspect Raster Layer is Missing the Value Field",2)
            return False

        cellSize = arcpy.Describe(aspectRaster[0]).meanCellWidth

        try:
            arcpy.env.extent = muLayer
            TabulateArea(muLayer, zoneField, aspectRaster[0], theValueField, outTAtable, cellSize)
        except:
            if bFeatureLyr:
                arcpy.env.extent = muLayerExtent
                TabulateArea(muLayerExtent, zoneField, aspectRaster[0], theValueField, outTAtable, cellSize)
            else:
                arcpy.env.extent = tempMuLayer
                TabulateArea(tempMuLayer, zoneField, aspectRaster[0], theValueField, outTAtable, cellSize)

        # list of unique VALUE fields generated from tabulate areas
        valueFields = [f.name for f in arcpy.ListFields(outTAtable,"VALUE*")]  #[u'VALUE_11', u'VALUE_21', u'VALUE_22']

        """ Generate look up table with value number and Aspect attribute """
        aspectLU = dict() # {u'VALUE_1': u'N', u'VALUE_2': u'NNW'}
        aspectField = FindField(aspectRaster[0],"ASPECT")

        if aspectField:

            for value in valueFields:
                valueNumber = value[value.find("_")+1:]  #strip the 'VALUE' off
                expression = arcpy.AddFieldDelimiters(aspectRaster[0],theValueField) + " = " + str(valueNumber)
                aspectDir = [row[0] for row in arcpy.da.SearchCursor(aspectRaster[0], (aspectField),expression)][0]
                aspectLU[value] = (aspectDir)
                del valueNumber, expression, aspectDir

        # list of unique zones used...ideally MUKEY
        ta_zoneFields = set([row[0] for row in arcpy.da.SearchCursor(outTAtable, (zoneField))]) #[u'2228988', u'426680', u'427731']

        """ iterate through output TA table for each unique zone (MUKEY or 1 record) and analyze and report Values """
        if len(valueFields):

            for zone in ta_zoneFields:

                # if Muname and AreaSymbol are present print both; this is only valid for MUKEY zone
                if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                    firstSpace = " " * (maxMukeyLength - len(mukey))
                    muName = muDict.get(zone)[0]
                    areaSymbol = muDict.get(zone)[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + zone + firstSpace + "  --  " + muName,0)
                    theTab = "\t" * 2

                # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                    AddMsgAndPrint("\n\t" + zone,0)
                    theTab = "\t" * 2

                # Zone field was MLRA_Temp
                else:
                    theTab = "\t"

                expression = arcpy.AddFieldDelimiters(outTAtable,zoneField) + " = '" + zone + "'"
                with arcpy.da.SearchCursor(outTAtable, valueFields, where_clause=expression) as cursor:

                    for row in cursor:

                        # Get Total number of pixel area for each zone in order to calculate acres and % of each zone
                        totalArea = 0
                        valueList = []  # [53100.0, 5869800.0, 1771200.0]
                        for i in range(0,len(valueFields)):
                            totalArea = totalArea + row[i]
                            valueList.append(row[i])

                        # Sort the list descending to get the 4 highest values
                        valueListSorted = sorted(valueList,reverse=True) #[103867200.0, 10187100.0, 5869800.0]

                        # Get the max length of digits for only the 4 highest aspect attributes.  if 4 aspect values don't
                        # exist then grab the max length of all land cover attributes; strictly formatting
                        if aspectField:
                            maxLClength = sorted([len(aspectLU.get(valueFields[valueList.index(valueListSorted[i])])) for i in range(0,4 if len(valueFields) > 4 else len(valueFields))],reverse=True)[0]

                        maxAcreLength = len(splitThousands(round((valueListSorted[0] / acreConv),1))) # Grab the max digit length of the highest acreage; strictly formatting

                        """ Actual Reporting of acres and mapunit % --  What a formatting nightmare  """
                        # if there are more than 4 classes exist in output table than print those otherwise print the classes
                        # that are available; Maximum of 4
                        #for i in range(0,4 if len(valueFields) > 4 else len(valueFields)):
                        for i in range(0,len(valueFields)):

                            valueAcres = splitThousands(round((valueListSorted[i] / acreConv),1))  # 103867200.0 / 4046.85642
                            muPercent = round(((valueListSorted[i] / totalArea) * 100),1)
                            acreFormat = str(valueAcres) + str((maxAcreLength - len(str(valueAcres))) * " ")

                            # if "Aspect" field exists than print their value
                            if aspectField:
                                aspectValue = aspectLU.get(valueFields[valueList.index(valueListSorted[i])])
                                aspectValueFormat = aspectValue + str((maxLClength - len(aspectValue)) * " ")
                                AddMsgAndPrint(theTab + str(aspectValueFormat) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)
                                del aspectValue, aspectValueFormat

                            # "Aspect" field does not exist; print generica value
                            else:
                                AddMsgAndPrint(theTab + str(valueListSorted[i]) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)

                            del valueAcres, muPercent, acreFormat
                        del totalArea, valueList, valueListSorted, maxAcreLength
                del expression

        if arcpy.Exists(outTAtable):
            arcpy.Delete_management(outTAtable)

        del elevFolder, workspaces, aspectRaster, outTAtable, rasterUnit,  cellSize, acreConv, valueFields, aspectLU, aspectField, ta_zoneFields

        return True

    except:
        if arcpy.Exists(outTAtable):
            arcpy.Delete_management(outTAtable)

        errorMsg()
        return False

# ===================================================================================
def processClimate():

    try:
        AddMsgAndPrint("\nClimate Information:",0)

        elevFolder = geoFolder + os.sep + "climate"

        if not os.path.exists(elevFolder):
            AddMsgAndPrint("\t\"climate\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = elevFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Climate.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Climate.gdb\" was not found in the elevation folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        climateDict = dict()
        climateLyrs = ["TempAvg_Annual","PrecipAvg_Annual"]
        climateLyrDef = ["Min Average Annual Temp:","Mean Average Annual Temperature:","Max Average Annual Temp:","Average Annual Precipitation:"]
        zoneTableFields = ["MIN","MEAN","MAX"]
        uniqueZones = set([row[0] for row in arcpy.da.SearchCursor(muLayer, (zoneField))])

        """ --------------------------------------------  Run Zonal Statistics ------------------------------------------- """
        for climateLyr in climateLyrs:

            raster = arcpy.ListRasters(climateLyr + "*","GRID")

            if not len(raster):
                AddMsgAndPrint("\t\"" + climateLyr + "\" raster was not found in the Climate.gdb File Geodatabase",2)
                return False

            # output Zonal Statistics Table; Don't use the createScrachName here
            outZoneTable = scratchWS + os.sep + climateLyr
            if arcpy.Exists(outZoneTable): arcpy.Delete_management(outZoneTable)

            # Run Zonal Statistics on the muLayer against the climate layer
            # NODATA cells are not ignored;
            try:
                arcpy.env.extent = muLayer
                arcpy.env.mask = muLayer
                outZSaT = ZonalStatisticsAsTable(muLayer, zoneField, raster[0], outZoneTable, "DATA", "ALL")
            except:
                if bFeatureLyr:
                    arcpy.env.extent = muLayerExtent
                    arcpy.env.mask = muLayerExtent
                    outZSaT = ZonalStatisticsAsTable(muLayerExtent, zoneField, raster[0], outZoneTable, "DATA", "ALL")
                else:
                    arcpy.env.extent = tempMuLayer
                    arcpy.env.mask = tempMuLayer
                    outZSaT = ZonalStatisticsAsTable(tempMuLayer, zoneField, raster[0], outZoneTable, "DATA", "ALL")

            del raster, outZoneTable

        """ -----------------------------------------  Report by Zone b/c there are multiple tables -------------------------------- """
        for zone in uniqueZones:

            # Add heading if analysis is done by MUKEY
            if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                spaceAfter = " " * (maxMukeyLength - len(zone))
                muName = muDict.get(zone)[0]
                areaSymbol = muDict.get(zone)[5]
                AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + str(zone) + spaceAfter + "  --  " + muName,0)
                theTab = "\t" * 2
                del muName,spaceAfter, areaSymbol

            # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
            elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                AddMsgAndPrint("\n\t" + zone,0)
                theTab = "\t" * 2

            # Zone field was MLRA_Temp
            else:
                #AddMsgAndPrint("\n")
                theTab = "\t"

            i = 0 # Layer counter to reference climate definitions
            for climateLyr in climateLyrs:

                # path to the zonal stat table
                outZoneTable = scratchWS + os.sep + climateLyr
                expression = arcpy.AddFieldDelimiters(outZoneTable,zoneField) + " = '" + zone + "'"
                climateZoneCount = [row[0] for row in arcpy.da.SearchCursor(outZoneTable, (zoneField), where_clause = expression)]

                if not len(climateZoneCount) > 0:
                    AddMsgAndPrint(theTab + "Polygon(s) are too small to assess against Climate Layers",1)
                    break

                with arcpy.da.SearchCursor(outZoneTable, (zoneTableFields), where_clause = expression) as cursor:

                    for row in cursor:

                        # Report Temperatures in F and C
                        if i < 1:

                            # iterate through the zoneTableFields of min,mean,max,mean which correspond to the climateLyrDef
                            # only for MLRA analysis
                            if zoneField == "MLRA_Temp":
                                for j in range(0,3):
                                    firstSpace = " " * (32 - len(climateLyrDef[j]))
                                    field1 = str(round(((float(row[j]) / 100) * 1.8) + 32,1)) + " F"   # Temp Fehrenheit
                                    field2 = str(round(float(row[j]) / 100,1)) + " C"                  # Temp Celsius converted from values
                                    AddMsgAndPrint(theTab + climateLyrDef[j] + firstSpace + "  --  " + field1 + "  --  " + field2,1)

                            # Only report the average for MUKEY analysis; Not enough variation between min and max
                            else:
                                firstSpace = " " * (32 - len(climateLyrDef[1]))
                                field1 = str(round(((float(row[1]) / 100) * 1.8) + 32,1)) + " F"   # Temp Fehrenheit
                                field2 = str(round(float(row[1]) / 100,1)) + " C"                  # Temp Celsius converted from values
                                AddMsgAndPrint(theTab + climateLyrDef[1] + firstSpace + "  --  " + field1 + "  --  " + field2,1)

                        # Report Precipitation in mm and inches
                        else:
                            firstSpace = " " * (32 - len(climateLyrDef[3]))
                            field1 = str(int(round(float(row[1]) / 100,1))) + " mm"                      # Precip units in MM rounded to the nearest mm
                            field2 = str(int(round((float(row[1]) / 100) * 0.0393701,1))) + " inches"    # Precip units in inches
                            AddMsgAndPrint(theTab + climateLyrDef[3] + firstSpace + "  --  " + field1 + "  --  " + field2,1)

                        del firstSpace,field1,field2

                    i += 1
                del outZoneTable, expression

        del elevFolder,workspaces,climateDict, climateLyrDef, uniqueZones

        # Delete all zonal stats table if they exist
        for climateLyr in climateLyrs:
            outZoneTable = scratchWS + os.sep + climateLyr
            if arcpy.Exists(outZoneTable):
                arcpy.Delete_management(outZoneTable)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processNLCD():

    try:
        AddMsgAndPrint("\nLand Cover (NLCD) Information:",0)

        nlcdFolder = geoFolder + os.sep + "land_use_land_cover"

        if not os.path.exists(nlcdFolder):
            AddMsgAndPrint("\t\"land_use_land_cover\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = nlcdFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("NLCD.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"NLCD.gdb\" was not found in the land_use_land_cover folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        nlcdRasters = arcpy.ListRasters("NLCD*","GRID")

        if not len(nlcdRasters):
            AddMsgAndPrint("\tNLCD Grids were not found in the Land_Use_Land_Cover.gdb File Geodatabase",2)
            return False

        for nlcd in nlcdRasters:

            AddMsgAndPrint("\n\t" + nlcd.replace("_"," "),0)

            # Get the linear unit of the DEM (Feet or Meters)
            rasterUnit = arcpy.Describe(nlcd).SpatialReference.LinearUnitName

            # Get Linear Units of DEM
            if rasterUnit == "Meter":
                acreConv = 4046.85642
            elif rasterUnit == "Foot" or rasterUnit == "Foot_US":
                acreConv = 43560
            else:
                AddMsgAndPrint("\tCould not determine linear units of " + nlcd,1)
                acreConv = 1

            # output Zonal Statistics Table
            #outTAtable = scratchWS + os.sep + "nlcdTAtable"
            outTAtable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

            # Delete Zonal Statistics Table if it exists
            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            theValueField = FindField(nlcd,"VALUE")
            if not theValueField:
                AddMsgAndPrint("\tNLCD Raster Layer is Missing the Value Field",2)
                return False

            cellSize = arcpy.Describe(nlcd).meanCellWidth

            try:
                arcpy.env.extent = muLayer
                arcpy.env.mask = muLayer
                TabulateArea(muLayer, zoneField, nlcd, theValueField, outTAtable, cellSize)
            except:
                if bFeatureLyr:
                    arcpy.env.extent = muLayerExtent
                    arcpy.env.mask = muLayerExtent
                    TabulateArea(muLayerExtent, zoneField, nlcd, theValueField, outTAtable, cellSize)
                else:
                    arcpy.env.extent = tempMuLayer
                    arcpy.env.mask = tempMuLayer
                    TabulateArea(tempMuLayer, zoneField, nlcd, theValueField, outTAtable, cellSize)

            # list of unique VALUE fields generated from tabulate areas
            classFields = [f.name for f in arcpy.ListFields(outTAtable,"VALUE*")]  #[u'VALUE_11', u'VALUE_21', u'VALUE_22']

            """ Generate look up table with value number and land cover attribute """
            nlcdLU = dict() # {u'VALUE_11': u'Open Water', u'VALUE_24': u'Developed}
            landCoverField = FindField(nlcd,"Land_Cover_Class")

            if landCoverField:

                for clsField in classFields:
                    valueNumber = clsField[clsField.find("_")+1:]  #strip the 'VALUE' off
                    expression = arcpy.AddFieldDelimiters(nlcd,theValueField) + " = " + str(valueNumber)
                    nlcdClass = [row[0] for row in arcpy.da.SearchCursor(nlcd, (landCoverField),expression)][0]
                    nlcdLU[clsField] = (nlcdClass)
                    del valueNumber, expression, nlcdClass

            # list of unique zones used...ideally MUKEY
            ta_zoneFields = set([row[0] for row in arcpy.da.SearchCursor(outTAtable, (zoneField))]) #[u'2228988', u'426680', u'427731']

            """ iterate through output TA table for each unique zone (MUKEY or 1 record) and analyze and report Values """
            if len(classFields):

                for zone in ta_zoneFields:

                    # if Muname is present; Print the Mapunit Name; this is only valid for MUKEY zone
                    if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                        firstSpace = " " * (maxMukeyLength - len(mukey))
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + firstSpace + "  --  " + muName)
                        theTab = "\t" * 3

                    # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                        AddMsgAndPrint("\n\t\t" + zone,0)
                        theTab = "\t" * 3

                    # Zone field was MLRA_Temp
                    else:
                        #AddMsgAndPrint("\n")
                        theTab = "\t" * 2

                    expression = arcpy.AddFieldDelimiters(outTAtable,zoneField) + " = '" + zone + "'"
                    with arcpy.da.SearchCursor(outTAtable, classFields, where_clause=expression) as cursor:

                        for row in cursor:

                            # Get Total number of pixel area for each zone in order to calculate acres and % of each zone
                            totalArea = 0
                            valueList = []  # [53100.0, 5869800.0, 1771200.0]
                            for i in range(0,len(classFields)):
                                totalArea = totalArea + row[i]
                                valueList.append(row[i])

                            # Sort the list descending to get the 4 highest values
                            valueListSorted = sorted(valueList,reverse=True) #[103867200.0, 10187100.0, 5869800.0]

                            # Get the max length of digits for only the 4 highest land cover attributes.  if 4 classes don't
                            # exist then grab the max length of all land cover attributes; strictly formatting
                            if landCoverField:
                                maxLClength = sorted([len(nlcdLU.get(classFields[valueList.index(valueListSorted[i])])) for i in range(0,4 if len(classFields) > 4 else len(classFields))],reverse=True)[0]

                            maxAcreLength = len(splitThousands(round((valueListSorted[0] / acreConv),1))) # Grab the max digit length of the highest acreage; strictly formatting

                            """ Actual Reporting of acres and mapunit % --  What a F'n formatting nightmare  """
                            # if there are more than 4 classes exist in output table than print those otherwise print the classes
                            # that are available; Maximum of 4
                            for i in range(0,4 if len(classFields) > 4 else len(classFields)):

                                valueAcres = splitThousands(round((valueListSorted[i] / acreConv),1))  # 103867200.0 / 4046.85642
                                muPercent = round(((valueListSorted[i] / totalArea) * 100),1)
                                acreFormat = str(valueAcres) + str((maxAcreLength - len(str(valueAcres))) * " ")

                                # if "Land_Cover_Class" field exists than print them
                                if landCoverField:
                                    lcValue = nlcdLU.get(classFields[valueList.index(valueListSorted[i])])
                                    lcValueFormat = lcValue + str((maxLClength - len(lcValue)) * " ")
                                    AddMsgAndPrint(theTab + str(lcValueFormat) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)
                                    del lcValue, lcValueFormat

                                # "Land_Cover_Class" field does not exist; print generica value
                                else:
                                    AddMsgAndPrint(theTab + str(valueListSorted[i]) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)

                                del valueAcres, muPercent, acreFormat
                            del totalArea, valueList, valueListSorted, maxAcreLength
                    del expression

            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            del rasterUnit, cellSize, acreConv, outTAtable, classFields, nlcdLU, landCoverField, ta_zoneFields
        del nlcdFolder, workspaces, nlcdRasters

        return True

    except:
        if arcpy.Exists(outTAtable):
            arcpy.Delete_management(outTAtable)

        errorMsg()
        return False

# ===================================================================================
def processNASS():

    try:
        AddMsgAndPrint("\nAgricultural Land Cover (NASS-CDL) Information:",0)

        nlcdFolder = geoFolder + os.sep + "land_use_land_cover"

        if not os.path.exists(nlcdFolder):
            AddMsgAndPrint("\t\"land_use_land_cover\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = nlcdFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("NASS.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"NASS.gdb\" was not found in the land_use_land_cover folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        nassRasters = arcpy.ListRasters("*","GRID")

        if not len(nassRasters):
            AddMsgAndPrint("\tNASS Grids were not found in the NASS.gdb File Geodatabase",2)
            return False

        for nass in sorted(nassRasters,reverse=True):

            AddMsgAndPrint("\n\t" + nass.replace("_"," "),0)

            # Get the linear unit of the DEM (Feet or Meters)
            rasterUnit = arcpy.Describe(nass).SpatialReference.LinearUnitName

            # Get Linear Units of DEM
            if rasterUnit == "Meter":
                acreConv = 4046.85642
            elif rasterUnit == "Foot" or rasterUnit == "Foot_US":
                acreConv = 43560
            else:
                AddMsgAndPrint("\tCould not determine linear units of " + nass,1)
                acreConv = 1

            # output Tabulate Areas Table
            #outTAtable = scratchWS + os.sep + "nassTAtable"
            outTAtable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

            # Delete Tabulate Areas Table if it exists
            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            theValueField = FindField(nass,"VALUE")
            if not theValueField:
                AddMsgAndPrint("\tNASS Raster Layer is Missing the Value Field",2)
                return False

            cellSize = arcpy.Describe(nass).meanCellWidth

            try:
                arcpy.env.extent = muLayer
                arcpy.env.mask = muLayer
                TabulateArea(muLayer, zoneField, nass, theValueField, outTAtable, cellSize)
            except:
                if bFeatureLyr:
                    arcpy.env.extent = muLayerExtent
                    arcpy.env.mask = muLayerExtent
                    TabulateArea(muLayerExtent, zoneField, nass, theValueField, outTAtable, cellSize)
                else:
                    arcpy.env.extent = tempMuLayer
                    arcpy.env.mask = tempMuLayer
                    TabulateArea(tempMuLayer, zoneField, nass, theValueField, outTAtable, cellSize)

            # list of unique VALUE fields generated from tabulate areas
            classFields = [f.name for f in arcpy.ListFields(outTAtable,"VALUE*")]  #[u'VALUE_11', u'VALUE_21', u'VALUE_22']

            """ Generate look up table with value number and land cover attribute """
            nassLU = dict() # {u'VALUE_11': u'Open Water', u'VALUE_24': u'Developed}
            classNameField = FindField(nass,"CLASS_NAME")

            if not classNameField:
                classNameField = FindField(nass,"Class_Names")

            if classNameField:

                for clsField in classFields:
                    valueNumber = clsField[clsField.find("_")+1:]  #strip the 'VALUE' off
                    expression = arcpy.AddFieldDelimiters(nass,theValueField) + " = " + str(valueNumber)
                    fireClass = [row[0] for row in arcpy.da.SearchCursor(nass, (classNameField),expression)][0]
                    nassLU[clsField] = (fireClass)

            # list of unique zones used...ideally MUKEY
            ta_zoneFields = set([row[0] for row in arcpy.da.SearchCursor(outTAtable, (zoneField))]) #[u'2228988', u'426680', u'427731']

            """ iterate through output TA table for each unique zone (MUKEY or 1 record) and analyze and report Values """
            if len(classFields):

                for zone in ta_zoneFields:

                    # if Muname is present; Print the Mapunit Name; this is only valid for MUKEY zone
                    if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + "  --  " + muName)
                        theTab = "\t" * 3

                     # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                        AddMsgAndPrint("\n\t" + zone,0)
                        theTab = "\t" * 2

                    # Zone field was MLRA_Temp
                    else:
                        #AddMsgAndPrint("\n")
                        theTab = "\t" * 2

                    expression = arcpy.AddFieldDelimiters(outTAtable,zoneField) + " = '" + zone + "'"
                    with arcpy.da.SearchCursor(outTAtable, classFields, where_clause=expression) as cursor:

                        for row in cursor:

                            # Get Total number of pixel area for each zone in order to calculate acres and % of each zone
                            totalArea = 0
                            valueList = []  # [53100.0, 5869800.0, 1771200.0]
                            for i in range(0,len(classFields)):
                                totalArea = totalArea + row[i]
                                valueList.append(row[i])

                            # Sort the list descending to get the 4 highest values
                            valueListSorted = sorted(valueList,reverse=True) #[103867200.0, 10187100.0, 5869800.0]

                            # Get the max length of digits for only the 4 highest land cover attributes.  if 4 classes don't
                            # exist then grab the max length of all land cover attributes; strictly formatting
                            if classNameField:
                                maxLClength = sorted([len(nassLU.get(classFields[valueList.index(valueListSorted[i])])) for i in range(0,4 if len(classFields) > 4 else len(classFields))],reverse=True)[0]

                            maxAcreLength = len(splitThousands(round((valueListSorted[0] / acreConv),1))) # Grab the max digit length of the highest acreage; strictly formatting

                            """ Actual Reporting of acres and mapunit % --  What a formatting nightmare  """
                            # if there are more than 4 classes exist in output table than print those otherwise print the classes
                            # that are available; Maximum of 4
                            for i in range(0,4 if len(classFields) > 4 else len(classFields)):

                                valueAcres = splitThousands(round((valueListSorted[i] / acreConv),1))  # 103867200.0 / 4046.85642
                                muPercent = round(((valueListSorted[i] / totalArea) * 100),1)
                                acreFormat = str(valueAcres) + str((maxAcreLength - len(str(valueAcres))) * " ")

                                # if "Class_Name" field exists than print them
                                if classNameField:
                                    lcValue = nassLU.get(classFields[valueList.index(valueListSorted[i])])
                                    lcValueFormat = lcValue + str((maxLClength - len(lcValue)) * " ")
                                    AddMsgAndPrint(theTab + str(lcValueFormat) + "  ---  " + acreFormat + " ac. --- " + str(muPercent) + " %",1)
                                    del lcValue, lcValueFormat

                                # "Class_Name" field does not exist; print generic value
                                else:
                                    AddMsgAndPrint(theTab + str(valueListSorted[i]) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)

                                del valueAcres, muPercent, acreFormat
                            del totalArea, valueList, valueListSorted, maxAcreLength
                    del expression

            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            del rasterUnit, cellSize, acreConv, classFields, nassLU, classNameField, ta_zoneFields

        del nlcdFolder, workspaces,nassRasters

        if arcpy.Exists(outTAtable):
            arcpy.Delete_management(outTAtable)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processNatureServe():

    try:
        AddMsgAndPrint("\nTerrestrial Ecological Systems (NatureServ) Information",0)

        nlcdFolder = geoFolder + os.sep + "land_use_land_cover"

        if not os.path.exists(nlcdFolder):
            AddMsgAndPrint("\t\"land_use_land_cover\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = nlcdFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("NatureServe.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"NatureServe.gdb\" was not found in the land_use_land_cover folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        rasters = arcpy.ListRasters("*","GRID")

        if not len(rasters):
            AddMsgAndPrint("\tEcosystem Grid(s) were not found in the NatureServe.gdb File Geodatabase",2)
            return False

        for raster in rasters:

            AddMsgAndPrint("\n\t" + raster.replace("_"," "),0)

            # Get the linear unit of the DEM (Feet or Meters)
            rasterUnit = arcpy.Describe(raster).SpatialReference.LinearUnitName

            # Get Linear Units of DEM
            if rasterUnit == "Meter":
                acreConv = 4046.85642
            elif rasterUnit == "Foot" or rasterUnit == "Foot_US":
                acreConv = 43560
            else:
                AddMsgAndPrint("\tCould not determine linear units of " + raster,1)
                acreConv = 1

            # output Zonal Statistics Table
            #outTAtable = scratchWS + os.sep + "rasterTAtable"
            outTAtable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

            # Delete Zonal Statistics Table if it exists
            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            theValueField = FindField(raster,"VALUE")
            if not theValueField:
                AddMsgAndPrint("\tEcosystems Raster Layer is Missing the Value Field",2)
                return False

            cellSize = arcpy.Describe(raster).meanCellWidth

            try:
                arcpy.env.extent = muLayer
                arcpy.env.mask = muLayer
                TabulateArea(muLayer, zoneField, raster, theValueField, outTAtable, cellSize)
            except:
                if bFeatureLyr:
                    arcpy.env.extent = muLayerExtent
                    arcpy.env.mask = muLayerExtent
                    TabulateArea(muLayerExtent, zoneField, raster, theValueField, outTAtable, cellSize)
                else:
                    arcpy.env.extent = tempMuLayer
                    arcpy.env.mask = tempMuLayer
                    TabulateArea(tempMuLayer, zoneField, raster, theValueField, outTAtable, cellSize)

            # list of unique VALUE fields generated from tabulate areas
            classFields = [f.name for f in arcpy.ListFields(outTAtable,"VALUE*")]  #[u'VALUE_11', u'VALUE_21', u'VALUE_22']

            """ Generate look up table with value number and land cover attribute """
            rasterLU = dict() # {u'VALUE_11': u'Open Water', u'VALUE_24': u'Developed}
            classNameField = FindField(raster,"LABEL")

            if classNameField:

                for clsField in classFields:
                    valueNumber = clsField[clsField.find("_")+1:]  #strip the 'VALUE' off
                    expression = arcpy.AddFieldDelimiters(raster,theValueField) + " = " + str(valueNumber)
                    nassClass = [row[0] for row in arcpy.da.SearchCursor(raster, (classNameField),expression)][0]
                    rasterLU[clsField] = (nassClass)

            # list of unique zones used...ideally MUKEY
            ta_zoneFields = set([row[0] for row in arcpy.da.SearchCursor(outTAtable, (zoneField))]) #[u'2228988', u'426680', u'427731']

            """ iterate through output TA table for each unique zone (MUKEY or 1 record) and analyze and report Values """
            if len(classFields):

                for zone in ta_zoneFields:

                    # if Muname is present; Print the Mapunit Name; this is only valid for MUKEY zone
                    if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + "  --  " + muName)
                        theTab = "\t" * 3

                    # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                        AddMsgAndPrint("\n\t" + zone,0)
                        theTab = "\t" * 3

                    # Zone field was MLRA_Temp
                    else:
                        #AddMsgAndPrint("\n")
                        theTab = "\t" * 2

                    expression = arcpy.AddFieldDelimiters(outTAtable,zoneField) + " = '" + zone + "'"
                    with arcpy.da.SearchCursor(outTAtable, classFields, where_clause=expression) as cursor:

                        for row in cursor:

                            # Get Total number of pixel area for each zone in order to calculate acres and % of each zone
                            totalArea = 0
                            valueList = []  # [53100.0, 5869800.0, 1771200.0]
                            for i in range(0,len(classFields)):
                                totalArea = totalArea + row[i]
                                valueList.append(row[i])

                            # Sort the list descending to get the 4 highest values
                            valueListSorted = sorted(valueList,reverse=True) #[103867200.0, 10187100.0, 5869800.0]

                            # Get the max length of digits for only the 4 highest land cover attributes.  if 4 classes don't
                            # exist then grab the max length of all land cover attributes; strictly formatting
                            if classNameField:
                                maxLClength = sorted([len(rasterLU.get(classFields[valueList.index(valueListSorted[i])])) for i in range(0,4 if len(classFields) > 4 else len(classFields))],reverse=True)[0]

                            maxAcreLength = len(splitThousands(round((valueListSorted[0] / acreConv),1))) # Grab the max digit length of the highest acreage; strictly formatting

                            """ Actual Reporting of acres and mapunit % --  What a formatting nightmare  """
                            # if there are more than 4 classes exist in output table than print those otherwise print the classes
                            # that are available; Maximum of 4
                            for i in range(0,4 if len(classFields) > 4 else len(classFields)):

                                valueAcres = splitThousands(round((valueListSorted[i] / acreConv),1))  # 103867200.0 / 4046.85642
                                muPercent = round(((valueListSorted[i] / totalArea) * 100),1)
                                acreFormat = str(valueAcres) + str((maxAcreLength - len(str(valueAcres))) * " ")

                                # if "Class_Name" field exists than print them
                                if classNameField:
                                    lcValue = rasterLU.get(classFields[valueList.index(valueListSorted[i])])
                                    lcValueFormat = lcValue + str((maxLClength - len(lcValue)) * " ")
                                    AddMsgAndPrint(theTab + str(lcValueFormat) + "  ---  " + acreFormat + " ac. --- " + str(muPercent) + " %",1)
                                    del lcValue, lcValueFormat

                                # "Class_Name" field does not exist; print generic value
                                else:
                                    AddMsgAndPrint(theTab + str(valueListSorted[i]) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)

                                del valueAcres, muPercent, acreFormat
                            del totalArea, valueList, valueListSorted, maxAcreLength
                    del expression

            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            del rasterUnit, cellSize, acreConv, outTAtable, classFields, rasterLU, classNameField, ta_zoneFields

        return True

    except:
        if arcpy.Exists(outTAtable):
            arcpy.Delete_management(outTAtable)

        errorMsg()
        return False

# ===================================================================================
def processLandFire():

    try:
        AddMsgAndPrint("\nAcquiring LANDFIRE Vegetation (LANDFIRE - USGS) Information",0)

        nlcdFolder = geoFolder + os.sep + "land_use_land_cover"

        if not os.path.exists(nlcdFolder):
            AddMsgAndPrint("\t\"land_use_land_cover\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = nlcdFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("LandFire.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"LandFire.gdb\" was not found in the land_use_land_cover folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        rasters = arcpy.ListRasters("*","GRID")

        if not len(rasters):
            AddMsgAndPrint("\tExisting Vegetation Grids were not found in the LandFire.gdb File Geodatabase",2)
            return False

        for raster in rasters:

            if raster.find("EVH") > -1:
                continue

            AddMsgAndPrint("\n\t" + raster.replace("_"," "),0)

            # Get the linear unit of the DEM (Feet or Meters)
            rasterUnit = arcpy.Describe(raster).SpatialReference.LinearUnitName

            # Get Linear Units of DEM
            if rasterUnit == "Meter":
                acreConv = 4046.85642
            elif rasterUnit == "Foot" or rasterUnit == "Foot_US":
                acreConv = 43560
            else:
                AddMsgAndPrint("\tCould not determine linear units of " + raster,1)
                acreConv = 1

            # output Zonal Statistics Table
            #outTAtable = scratchWS + os.sep + "rasterTAtable"
            outTAtable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

            # Delete Zonal Statistics Table if it exists
            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            theValueField = FindField(raster,"VALUE")
            if not theValueField:
                AddMsgAndPrint("\tEcosystems Raster Layer is Missing the Value Field",2)
                return False

            cellSize = arcpy.Describe(raster).meanCellWidth

            try:
                arcpy.env.extent = muLayer
                arcpy.env.mask = muLayer
                TabulateArea(muLayer, zoneField, raster, theValueField, outTAtable, cellSize)
            except:
                if bFeatureLyr:
                    arcpy.env.extent = muLayerExtent
                    arcpy.env.mask = muLayerExtent
                    TabulateArea(muLayerExtent, zoneField, raster, theValueField, outTAtable, cellSize)
                else:
                    arcpy.env.extent = tempMuLayer
                    arcpy.env.mask = tempMuLayer
                    TabulateArea(tempMuLayer, zoneField, raster, theValueField, outTAtable, cellSize)

            # list of unique VALUE fields generated from tabulate areas
            classFields = [f.name for f in arcpy.ListFields(outTAtable,"VALUE*")]  #[u'VALUE_11', u'VALUE_21', u'VALUE_22']

            """ Generate look up table with value number and land cover attribute """
            rasterLU = dict() # {u'VALUE_11': u'Open Water', u'VALUE_24': u'Developed}
            classNameField = FindField(raster,"CLASSNAMES")

            # This is used for the EVT_2010 Grid
            if not classNameField:
                classNameField = FindField(raster,"EVT_NAME")

            if classNameField:

                for clsField in classFields:
                    valueNumber = clsField[clsField.find("_")+1:]  #strip the 'VALUE' off

                    # Handle LandFire data with NoData values of -999
                    if valueNumber.find('999')>-1:
                        rasterLU[clsField] = ("NoData")
                        continue

                    expression = arcpy.AddFieldDelimiters(raster,theValueField) + " = " + str(valueNumber)
                    fireClass = [row[0] for row in arcpy.da.SearchCursor(raster, (classNameField),expression)][0]
                    rasterLU[clsField] = (fireClass)
                    del expression,fireClass

            # list of unique zones used...ideally MUKEY
            ta_zoneFields = set([row[0] for row in arcpy.da.SearchCursor(outTAtable, (zoneField))]) #[u'2228988', u'426680', u'427731']

            """ iterate through output TA table for each unique zone (MUKEY or 1 record) and analyze and report Values """
            if len(classFields):

                for zone in ta_zoneFields:

                    # if Muname is present; Print the Mapunit Name; this is only valid for MUKEY zone
                    if bMunamePresent and bAreasymPresent and bMukeyPresent and zoneField != "MLRA_Temp":
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + "  --  " + muName)
                        theTab = "\t" * 3

                    # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not bMunamePresent or not bAreasymPresent) and bMukeyPresent and zoneField != "MLRA_Temp":
                        AddMsgAndPrint("\n\t" + zone,0)
                        theTab = "\t" * 3

                    # Zone field was MLRA_Temp
                    else:
                        #AddMsgAndPrint("\n")
                        theTab = "\t" * 2

                    expression = arcpy.AddFieldDelimiters(outTAtable,zoneField) + " = '" + zone + "'"
                    with arcpy.da.SearchCursor(outTAtable, classFields, where_clause=expression) as cursor:

                        for row in cursor:

                            # Get Total number of pixel area for each zone in order to calculate acres and % of each zone
                            totalArea = 0
                            valueList = []  # [53100.0, 5869800.0, 1771200.0]
                            for i in range(0,len(classFields)):
                                totalArea = totalArea + row[i]
                                valueList.append(row[i])

                            # Sort the list descending to get the 4 highest values
                            valueListSorted = sorted(valueList,reverse=True) #[103867200.0, 10187100.0, 5869800.0]

                            # Get the max length of digits for only the 4 highest land cover attributes.  if 4 classes don't
                            # exist then grab the max length of all land cover attributes; strictly formatting
                            if classNameField:
                                maxLClength = sorted([len(rasterLU.get(classFields[valueList.index(valueListSorted[i])])) for i in range(0,4 if len(classFields) > 4 else len(classFields))],reverse=True)[0]

                            maxAcreLength = len(splitThousands(round((valueListSorted[0] / acreConv),1))) # Grab the max digit length of the highest acreage; strictly formatting

                            """ Actual Reporting of acres and mapunit % --  What a formatting nightmare  """
                            # if there are more than 4 classes exist in output table than print those otherwise print the classes
                            # that are available; Maximum of 4
                            for i in range(0,4 if len(classFields) > 4 else len(classFields)):

                                valueAcres = splitThousands(round((valueListSorted[i] / acreConv),1))  # 103867200.0 / 4046.85642
                                muPercent = round(((valueListSorted[i] / totalArea) * 100),1)
                                acreFormat = str(valueAcres) + str((maxAcreLength - len(str(valueAcres))) * " ")

                                # if "Class_Name" field exists than print them
                                if classNameField:
                                    lcValue = rasterLU.get(classFields[valueList.index(valueListSorted[i])])
                                    lcValueFormat = lcValue + str((maxLClength - len(lcValue)) * " ")
                                    AddMsgAndPrint(theTab + str(lcValueFormat) + "  ---  " + acreFormat + " ac. --- " + str(muPercent) + " %",1)
                                    del lcValue, lcValueFormat

                                # "Class_Name" field does not exist; print generic value
                                else:
                                    AddMsgAndPrint(theTab + str(valueListSorted[i]) + " --- " + acreFormat + " ac. --- " + str(muPercent) + " %",1)

                                del valueAcres, muPercent, acreFormat
                            del totalArea, valueList, valueListSorted, maxAcreLength
                    del expression

            if arcpy.Exists(outTAtable):
                arcpy.Delete_management(outTAtable)

            del rasterUnit, cellSize, acreConv, outTAtable, classFields, rasterLU, classNameField, ta_zoneFields

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processMLRAInfo():

    try:
        AddMsgAndPrint("\nMLRA Information:\n",0)

        ecoFolder = geoFolder + os.sep + "ecological"

        if not os.path.exists(ecoFolder):
            AddMsgAndPrint("\t\"ecological\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = ecoFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Ecological.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Ecological.gdb\" was not found in the ecological folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("mlra_a_*","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\tMLRA feature class was not found in the Ecological.gdb File Geodatabase",2)
            return False

        mlraSymField = FindField(fcList[0],"MLRARSYM")
        mlraNameField = FindField(fcList[0],"MLRA_NAME")

        if not mlraSymField or not mlraNameField:
            AddMsgAndPrint("\tMLRA feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "mlraIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        arcpy.Intersect_analysis([[muLayer,1],[fcList[0],2]], outIntersect,"ALL","","")

        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'MLRA' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return False

        mlraDict = dict()

        #mlraSyms = set([str(row[0]).strip(' ') for row in arcpy.da.SearchCursor(outIntersect, (mlraSymField))])
        mlraSyms = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (mlraSymField))])

        for mlraSym in mlraSyms:

            if not mlraDict.has_key(mlraSym):
                expression = arcpy.AddFieldDelimiters(outIntersect,mlraSymField) + " = '" + mlraSym + "'"
                mlraName = [row[0] for row in arcpy.da.SearchCursor(outIntersect, (mlraNameField), where_clause = expression)][0]
                mlraAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))
                mlraPcntAcres = float("%.1f" %((mlraAcres / totalAcres) * 100))
                mlraDict[mlraSym] = (mlraName,str(splitThousands(mlraAcres)),mlraPcntAcres,len(mlraSym),len(mlraName),len(str(splitThousands(mlraAcres))))
                del expression, mlraName, mlraAcres, mlraPcntAcres
        del mlraSym

        # strictly for formatting
        maxmlraSymLength = sorted([mlrainfo[3] for mlraSym,mlrainfo in mlraDict.iteritems()],reverse=True)[0]
        maxmlraNameLength= sorted([mlrainfo[4] for mlraSym,mlrainfo in mlraDict.iteritems()],reverse=True)[0]
        maxmlraAcreLength = sorted([mlrainfo[5] for mlraSym,mlrainfo in mlraDict.iteritems()],reverse=True)[0]

        # sort the mlraDict based on the highest acres; converts the dictionary into a tuple by default since you can't order a dictionary.
        # item #1 becomes mlraName and NOT str(splitThousands(mlraAcres)) as in the dictionary
        MuMLRAacresSorted = sorted(mlraDict.items(), key=lambda mlra: mlra[1][2],reverse=True)

        for mlraInfo in MuMLRAacresSorted:
            mlraName = mlraInfo[1][0]
            mlraAcres = mlraInfo[1][1]
            mlraPercent = mlraInfo[1][2]
            firstSpace = " " * (maxmlraSymLength - len(mlraInfo[0]))
            secondSpace = " " * (maxmlraNameLength - len(mlraName))
            thirdSpace = " " * (maxmlraAcreLength - len(mlraAcres))

            AddMsgAndPrint("\tMLRA: " + str(mlraInfo[0]) + firstSpace + " -- " + mlraName + secondSpace + " -- " + mlraAcres + " ac." + thirdSpace + " -- " + str(mlraPercent) + " %" ,1)
            del mlraName, mlraAcres, mlraPercent, firstSpace, secondSpace, thirdSpace

        del ecoFolder, workspaces, fcList, mlraSymField, mlraNameField, mlraDict, mlraSyms, maxmlraSymLength, maxmlraNameLength, maxmlraAcreLength, MuMLRAacresSorted, mlraInfo

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processLRRInfo():

    try:
        AddMsgAndPrint("\nLand Resource Region Information:\n",0)

        ecoFolder = geoFolder + os.sep + "ecological"

        if not os.path.exists(ecoFolder):
            AddMsgAndPrint("\t\"ecological\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = ecoFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Ecological.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Ecological.gdb\" was not found in the ecological folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("lrr_a_*","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\tLRR feature class was not found in the Ecological.gdb File Geodatabase",2)
            return False

        lrrField = FindField(fcList[0],"LRR_NAME")

        if not lrrField:
            AddMsgAndPrint("\tLRR feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "lrrIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        arcpy.Intersect_analysis([[muLayer,1],[fcList[0],2]], outIntersect,"ALL","","")

        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'LRR' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return False

        lrrDict = dict()

        lrrSyms = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (lrrField))])

        for lrr in lrrSyms:

            if not lrrDict.has_key(lrr):

                expression = arcpy.AddFieldDelimiters(outIntersect,lrrField) + " = '" + lrr + "'"
                lrrAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))
                lrrPcntAcres = float("%.1f" %((lrrAcres / totalAcres) * 100))
                lrrDict[lrr] = (len(lrr),str(splitThousands(lrrAcres)),lrrPcntAcres,len(str(splitThousands(lrrAcres))))
                del lrrAcres, lrrPcntAcres

        # strictly for formatting
        maxLRRnameLength = sorted([lrrinfo[0] for lrr,lrrinfo in lrrDict.iteritems()],reverse=True)[0]
        maxLRRacreLength = sorted([lrrinfo[3] for lrr,lrrinfo in lrrDict.iteritems()],reverse=True)[0]

        # sort the lrrDict based on the highest acres; converts the dictionary into a tuple by default since you can't order a dictionary.
        # item #1 becomes len(lrr) and NOT str(splitThousands(lrrAcres)) as in the dictionary
        muLrrAcresSorted = sorted(lrrDict.items(), key=lambda lrr: lrr[1][2], reverse=True)

        for lrrInfo in muLrrAcresSorted:
            lrr = lrrInfo[0]
            lrrAcres = lrrInfo[1][1]
            lrrPercent = str(lrrInfo[1][2])
            firstSpace = " " * (maxLRRnameLength - lrrInfo[1][0])
            secondSpace = " " * (maxLRRacreLength - lrrInfo[1][3])

            AddMsgAndPrint("\tLRR: " + str(lrr) + firstSpace + " -- " + lrrAcres + " ac." + secondSpace + " -- " + lrrPercent + " %" ,1)
            del lrr, lrrAcres, lrrPercent, firstSpace, secondSpace

        del ecoFolder, workspaces, fcList, lrrField, lrrDict, lrrSyms, maxLRRnameLength, maxLRRacreLength, muLrrAcresSorted

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processEcoregions():

    try:
        AddMsgAndPrint("\nEcoregion Subsection Information:\n",0)

        ecoFolder = geoFolder + os.sep + "ecological"

        if not os.path.exists(ecoFolder):
            AddMsgAndPrint("\t\"ecological\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = ecoFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Ecological.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Ecological.gdb\" was not found in the ecological folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("ecoregions_subsection_*","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\tecoregions_subsection feature class was not found in the Ecological.gdb File Geodatabase",2)
            return False

        ecoregField = FindField(fcList[0],"subsection_name")

        if not ecoregField:
            AddMsgAndPrint("\ecoregion feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "ecoIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        arcpy.Intersect_analysis([[muLayer,1],[fcList[0],2]], outIntersect,"ALL","","")

        # Make sure there are output polygons as a result of intersection
        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'Ecoregion' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return False

        ecoDict = dict()
        ecoSyms = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (ecoregField))])

        for eco in ecoSyms:

            if not ecoDict.has_key(eco):

                expression = arcpy.AddFieldDelimiters(outIntersect,ecoregField) + " = '" + eco + "'"
                ecoAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))
                ecoPcntAcres = float("%.1f" %((ecoAcres / totalAcres) * 100))
                ecoDict[eco] = (len(eco),str(splitThousands(ecoAcres)),ecoPcntAcres,len(str(splitThousands(ecoAcres))))
                del expression, ecoAcres, ecoPcntAcres

        # strictly for formatting
        maxEcoNameLength = sorted([ecoinfo[0] for eco,ecoinfo in ecoDict.iteritems()],reverse=True)[0]
        maxEcoAcreLength = sorted([ecoinfo[3] for eco,ecoinfo in ecoDict.iteritems()],reverse=True)[0]

        # sort the ecoDict based on the highest % acres; converts the dictionary into a tuple by default since you can't order a dictionary.
        # item #1 becomes len() and NOT str(splitThousands(lrrAcres)) as in the dictionary
        muEcoAcresSorted = sorted(ecoDict.items(), key=lambda eco: eco[1][2],reverse=True)

        for ecoInfo in muEcoAcresSorted:
            eco = ecoInfo[0]
            ecoAcres = ecoInfo[1][1]
            ecoPercent = ecoInfo[1][2]
            firstSpace = " " * (maxEcoNameLength - len(eco))
            secondSpace = " " * (maxEcoAcreLength - ecoInfo[1][3])

            AddMsgAndPrint("\t" + eco + firstSpace + " -- " + ecoAcres + " ac." + secondSpace + " -- " + str(ecoPercent) + " %" ,1)
            del eco, ecoAcres, ecoPercent, firstSpace, secondSpace

        del ecoFolder, workspaces, fcList, ecoregField, ecoDict, ecoSyms, maxEcoAcreLength, maxEcoNameLength, muEcoAcresSorted

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processLandOwnership():

    try:

        AddMsgAndPrint("\nLand Ownership Information:\n",0)

        cadastralFolder = geoFolder + os.sep + "cadastral"

        if not os.path.exists(cadastralFolder):
            AddMsgAndPrint("\t\"cadastral\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = cadastralFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Land_Ownership.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Land_Ownership.gdb\" was not found in the Cadastral folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("padus_a_*","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\"padus\" feature class was not found in the Cadastral.gdb File Geodatabase",2)
            return False

        # field that contains custom NASIS ownership category
        nasisField = FindField(fcList[0],"NASIS")

        # Check for the presence of NASIS field in padus layer; return false if not present
        if not nasisField:
            AddMsgAndPrint("\t\"padus\" feature class is missing necessary fields",2)
            return False

        # if temp intersect layer exists delete it
        outIntersect = scratchWS + os.sep + "padusIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        # Intersect muLayer with the land ownership layer
        arcpy.Intersect_analysis([[muLayer,1],[fcList[0],2]], outIntersect,"ALL","","")

        # Check if there is any overlap; return false if no intersect exists.
        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0:
            AddMsgAndPrint("\t Private Lands -- " + str(splitThousands(totalAcres)) + " ac. -- 100%",1)
            #AddMsgAndPrint("\tThere is no overlap between " + os.path.basename(muLayer) + " and 'padus' layer",2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return True

        # dictionary that will contain info related to ownership
        ownerDict = dict()

        # list of unique ownership occurences
        ownership = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (nasisField))])
        totalOutIntersectAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"))]) / 4046.85642))

        for owner in ownership:

            if not ownerDict.has_key(owner):
                expression = arcpy.AddFieldDelimiters(outIntersect,nasisField) + " = '" + owner + "'"
                ownerAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))
                ownerPcntAcres = float("%.1f" %((ownerAcres / totalAcres) * 100))
                ownerDict[owner] = (str(splitThousands(ownerAcres)),ownerAcres,ownerPcntAcres,len(owner))
                del expression, ownerAcres, ownerPcntAcres

        # strictly for formatting
        maxOwnerLength = sorted([ownerInfo[3] for owner,ownerInfo in ownerDict.iteritems()],reverse=True)[0]
        maxOwnerAcreLength = sorted([len(ownerInfo[0]) for owner,ownerInfo in ownerDict.iteritems()],reverse=True)[0]
        #maxOwnerAcreLength = len(str(splitThousands(float("%.1f" %(totalAcres)))))

        # sort the ownerDict based on the highest % acres; converts the dictionary into a tuple by default since you can't order a dictionary.
        # item #1 becomes len(lrr) and NOT str(splitThousands(lrrAcres)) as in the dictionary
        muOwnerAcresSorted = sorted(ownerDict.items(), key=lambda lrr: lrr[1][1], reverse=True)

        for ownerInfo in muOwnerAcresSorted:
            owner = ownerInfo[0]
            ownerAcres = ownerInfo[1][0]
            ownerPercent = ownerInfo[1][2]
            firstSpace = " " * (maxOwnerLength - len(owner))
            secondSpace = " " * (maxOwnerAcreLength - len(ownerAcres))

            AddMsgAndPrint("\t" + owner + firstSpace + " -- " + ownerAcres + " ac. " + secondSpace + " -- " + str(ownerPercent) + " %" ,1)
            del owner, ownerAcres, ownerPercent, firstSpace, secondSpace

        if not float("%.1f" %(totalAcres)) == totalOutIntersectAcres:
            firstSpace = " " * (maxOwnerLength - len("Private Lands"))
            privateAcres = float("%.1f" %(totalAcres)) - totalOutIntersectAcres
            secondSpace = " " * (maxOwnerAcreLength - len(str(privateAcres)))
            privatePcntAcres = float("%.1f" %((privateAcres / totalAcres) * 100))
            AddMsgAndPrint("\tPrivate Lands" + firstSpace + " -- " + str(splitThousands(privateAcres)) + " ac." + secondSpace + " -- " + str(privatePcntAcres) + " %",1)

        del cadastralFolder, workspaces, fcList, nasisField, ownerDict, ownership, maxOwnerLength, maxOwnerAcreLength, muOwnerAcresSorted

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processHydro():

    try:
        AddMsgAndPrint("\n24k Hydro Information:",0)

        hydroFolder = geoFolder + os.sep + "hydrography"

        if not os.path.exists(hydroFolder):
            AddMsgAndPrint("\t\"hydrography\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = hydroFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Hydrography.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Hydrography.gdb\" was not found in the hydrography folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("hydro24k_l_*","Line")

        if not len(fcList):
            AddMsgAndPrint("\thydro24k_l_MLRA feature class was not found in the Hydrography.gdb File Geodatabase",2)
            return False

        fcodeField = FindField(fcList[0],"FType_desc")

        if not fcodeField:
            AddMsgAndPrint("\tHydro feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "hydroIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        arcpy.Intersect_analysis([[muLayer,1],[fcList[0],2]], outIntersect,"ALL","","")

        # Represents the total hydro length of every intersected feature
        totalHydroLength = float("%.3f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@LENGTH"))])))
        totalHydroLengthClean = str(splitThousands(int(round(totalHydroLength)))) + " Meters"

        # Check amount of intersections or if total length is 0 meters; Inform user of no overlap
        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0 or totalHydroLength == 0.0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'Hydro' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return True

        """ --------------------- Report Hydro info by MUKEY ------------------------------ """
        # Report by MUKEY
        if zoneField != "MLRA_Temp":

            # unique list of MUKEYs in intersect output
            muLayerUniqueMukeys = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (zoneField))])

            AddMsgAndPrint("\n\tTotal Hydro Length: " + totalHydroLengthClean,0)

            # iterate through every unique MUKEY to
            for mukey in muLayerUniqueMukeys:

                # Select all of the intersect streams with the unique mukey and capture its total length and calc % of total
                expression = arcpy.AddFieldDelimiters(outIntersect,zoneField) + " = '" + mukey + "'"
                muHydroLength = float("%.3f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@LENGTH"),where_clause=expression)])))
                muHydroLengthClean = str(splitThousands(int(round(muHydroLength)))) + " Meters"   # 263,729 Meters
                muHydroPercent = str(int(round(float("%.1f" %((muHydroLength / totalHydroLength) * 100))))) + " %"

                # Report results by MUNAME - MUKEY - Areasymbol - Length - %
                if bMunamePresent and bAreasymPresent and bMukeyPresent:
                    firstSpace = " " * (maxMukeyLength - len(mukey))
                    muName = muDict.get(mukey)[0]
                    areaSymbol = muDict.get(mukey)[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + mukey + firstSpace + "  --  " + muName + " -- " + muHydroLengthClean + " -- " + muHydroPercent,0)
                    theTab = "\t" * 2
                    del firstSpace, muName, areaSymbol

                # Report results only by MUKEY - Length - %
                else:
                    AddMsgAndPrint("\n\t" + mukey + " -- " + muHydroLengthClean + " -- " + muHydroPercent,0)
                    theTab = "\t" * 2

                hydroDict = dict()

                muUniqueFcodes = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (fcodeField), expression)])
                del expression

                if muHydroLength == 0.0:
                    continue

                for muFcode in muUniqueFcodes:

                    if not hydroDict.has_key(muFcode):

                        expression = arcpy.AddFieldDelimiters(outIntersect,zoneField) + " = '" + mukey + "' AND " + arcpy.AddFieldDelimiters(outIntersect,fcodeField) + " = '" + muFcode + "'"
                        fcodeHydroLength = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect,("SHAPE@LENGTH"),where_clause=expression)])))  # 263729.8023
                        fcodeHydroLengthClean = str(splitThousands(int(round(fcodeHydroLength)))) + " Meters"   # 263,729 Meters
                        fcodeHydroPercent = str(int(round(float("%.1f" %((fcodeHydroLength / muHydroLength) * 100))))) + " %"   # 30 %

                        # 'Artificial Path':(263,729 Meters,14,30 %,4,15)
                        hydroDict[muFcode] = (fcodeHydroLength,fcodeHydroLengthClean, len(fcodeHydroLengthClean), fcodeHydroPercent, len(fcodeHydroPercent), len(muFcode))
                        del expression, fcodeHydroLength, fcodeHydroLengthClean, fcodeHydroPercent

                # strictly for formatting
                maxFcodeNameLength = sorted([hydroinfo[5] for fcode,hydroinfo in hydroDict.items()],reverse=True)[0]
                maxHydroLengthChars = sorted([hydroinfo[2] for fcode,hydroinfo in hydroDict.items()],reverse=True)[0]
                maxHydroPercentChars = sorted([hydroinfo[4] for fcode,hydroinfo in hydroDict.items()],reverse=True)[0]

                # sort the hydroDict based on largest length; converts the dictionary into a tuple by default since you can't order a dictionary.
                # item #1 becomes fcodeHydroLength and NOT fcodeHydroLengthClean as in the dictionary
                muHydroLengthSorted = sorted(hydroDict.items(), key=operator.itemgetter(1),reverse=True)

                # ('Artificial Path':(263,729 Meters,14,30 %,4,15))
                for hydroInfo in muHydroLengthSorted:

                    hydroPrct = hydroInfo[1][3]

                    # Only print out if hydro percent is greater than 1%; What if ALL fcodes are 0%?
                    if not hydroPrct == "0 %":
                        fcode = hydroInfo[0]
                        hydroLength = hydroInfo[1][1]
                        firstSpace = " " * (maxFcodeNameLength - len(fcode))
                        secondSpace = " " * (maxHydroLengthChars - hydroInfo[1][2])
                        AddMsgAndPrint(theTab + fcode + firstSpace + " -- " + hydroLength + secondSpace + " -- " + hydroPrct,1)
                        del fcode, hydroLength,hydroPrct,firstSpace,secondSpace

                del muHydroLength, muHydroLengthClean, muHydroPercent, hydroDict, muUniqueFcodes, maxFcodeNameLength, maxHydroLengthChars, maxHydroPercentChars
            del muLayerUniqueMukeys

            """ --------------------- Report Hydro info by Fcodes (hydro descriptions) only  ------------------------------ """
        else:
            AddMsgAndPrint("\n\tTotal Hydro Length: " + totalHydroLengthClean + "\n",0)

            hydroDict = dict()
            uniqueFcodes = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (fcodeField))])

            for fcode in uniqueFcodes:

                if not hydroDict.has_key(fcode):

                    expression = arcpy.AddFieldDelimiters(outIntersect,fcodeField) + " = '" + fcode + "'"
                    fcodeHydroLength = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect,("SHAPE@LENGTH"), where_clause=expression)])))  # 263729.8023
                    fcodeHydroLengthClean = str(splitThousands(int(round(fcodeHydroLength)))) + " Meters"   # 263,729 Meters
                    fcodeHydroPercent = str(int(round(float("%.1f" %((fcodeHydroLength / totalHydroLength) * 100))))) + " %"   # 30 %

                    # 'Artificial Path':(263,729 Meters,14,30 %,4,15)
                    hydroDict[fcode] = (fcodeHydroLength,fcodeHydroLengthClean, len(fcodeHydroLengthClean), fcodeHydroPercent, len(fcodeHydroPercent), len(fcode))
                    del expression, fcodeHydroLengthClean, fcodeHydroPercent

            # strictly for formatting
            maxFcodeNameLength = sorted([hydroinfo[5] for code,hydroinfo in hydroDict.items()],reverse=True)[0]
            maxHydroLengthChars = sorted([hydroinfo[2] for code,hydroinfo in hydroDict.items()],reverse=True)[0]
            maxHydroPercentChars = sorted([hydroinfo[4] for code,hydroinfo in hydroDict.items()],reverse=True)[0]

            # sort the hydroDict based on largest length; converts the dictionary into a tuple by default since you can't order a dictionary.
            # item #1 becomes fcodeHydroLength and NOT fcodeHydroLengthClean as in the dictionary
            fcHydroLengthSorted = sorted(hydroDict.items(), key=operator.itemgetter(1),reverse=True)

            # ('Artificial Path':(263,729 Meters,14,30 %,4,15))
            for hydroInfo in fcHydroLengthSorted:

                hydroPrct = hydroInfo[1][3]

                # Only print out if hydro percent is greater than 1%; What if ALL fcodes are 0%?
                if not hydroPrct == "0 %":
                    fcode = hydroInfo[0]
                    hydroLength = hydroInfo[1][1]
                    hydroPrct = hydroInfo[1][3]
                    firstSpace = " " * (maxFcodeNameLength - len(fcode))
                    secondSpace = " " * (maxHydroLengthChars - hydroInfo[1][2])
                    AddMsgAndPrint("\t\t" + fcode + firstSpace + " -- " + hydroLength + secondSpace + " -- " + hydroPrct,1)
                    del fcode, hydroLength,hydroPrct,firstSpace,secondSpace

            del hydroDict, uniqueFcodes, maxFcodeNameLength, maxHydroLengthChars, maxHydroPercentChars, fcHydroLengthSorted

        del hydroFolder, workspaces, fcList, fcodeField, totalHydroLength, totalHydroLengthClean

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
        errorMsg()
        return False

# ===================================================================================
def processNWI():

    try:
        AddMsgAndPrint("\nWetlands (NWI) Information:",0)

        wetlandFolder = geoFolder + os.sep + "wetlands"

        if not os.path.exists(wetlandFolder):
            AddMsgAndPrint("\t\"wetlands\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = wetlandFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("Wetlands.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"Wetlands.gdb\" was not found in the Wetlands folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("wetlands_a_*","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\twetlands_a feature class was not found in the Wetlands.gdb File Geodatabase",2)
            return False

        if len(fcList) > 1:
            AddMsgAndPrint("\tThere is more than one wetlands feature class in your Wetlands.gdb",2)
            return False

        fcodeField = FindField(fcList[0],"NRCS")

        if not fcodeField:
            AddMsgAndPrint("\tWetlands feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "wetlandIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        arcpy.Intersect_analysis([[muLayer,1],[fcList[0],2]], outIntersect,"ALL","","")

        # Represents the total hydro length of every intersected feature
        totalWetlandAcres = float("%.3f" % ((sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"))])) / 4046.85642))
        totalWetlandAcresClean = str(splitThousands(int(round(totalWetlandAcres)))) + " Acres"

        if int(round(float("%.1f" %((totalWetlandAcres / totalAcres) * 100)))) > 0:
            projectPercent = str(int(round(float("%.1f" %((totalWetlandAcres / totalAcres) * 100))))) + " %"
        else:
            projectPercent = "Less than 1 %"

        # Check amount of intersections or if total acres is 0 acres; Inform user of no overlap
        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0 or totalWetlandAcres == 0.0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'Wetlands' layer" ,2)

            if arcpy.Exists(outIntersect):
                arcpy.Delete_management(outIntersect)

            return True

        """ --------------------- Report Wetlands info by MUKEY ------------------------------ """
        # Report by MUKEY
        if zoneField != "MLRA_Temp":

            # unique list of MUKEYs in intersect output
            muLayerUniqueMukeys = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (zoneField))])

            AddMsgAndPrint("\n\tTotal Wetlands Acres: " + totalWetlandAcresClean + " (" + projectPercent + " of total project area)",0)

            # iterate through every unique MUKEY to
            for mukey in muLayerUniqueMukeys:

                # Select all of the intersect streams with the unique mukey and capture its total length and calc % of total
                expression = arcpy.AddFieldDelimiters(outIntersect,zoneField) + " = '" + mukey + "'"
                muWetlandAcres = float("%.3f" % ((sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"),where_clause=expression)])) / 4046.85642))
                muWetlandAcresClean = str(splitThousands(int(round(muWetlandAcres)))) + " Wetland Acres"   # 263,729 Meters
                #muWetlandPercent = str(int(round(float("%.1f" %((muWetlandAcres / totalWetlandAcres) * 100))))) + " %"
                muAcres = muDict.get(mukey)[1] # Acres for MUKEY at hand
                muWetlandPercent = str(float("%.1f" %((muWetlandAcres / muAcres) * 100))) + " % of mapunit"  # Wetland percent relative to total mapunit acres

                # Report results by MUNAME - MUKEY - Areasymbol - Length - %
                if bMunamePresent and bAreasymPresent and bMukeyPresent:
                    firstSpace = " " * (maxMukeyLength - len(mukey))
                    muName = muDict.get(mukey)[0]
                    areaSymbol = muDict.get(mukey)[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + mukey + firstSpace + "  --  " + muName + " -- " + muWetlandAcresClean + " -- " + muWetlandPercent,0)
                    theTab = "\t" * 2
                    del firstSpace, muName, areaSymbol

                # Report results only by MUKEY - Length - %
                else:
                    AddMsgAndPrint("\n\t" + mukey + " -- " + muWetlandAcresClean + " -- " + muWetlandPercent,0)
                    theTab = "\t" * 2

                wetlandDict = dict()

                muUniqueFcodes = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (fcodeField), expression)])
                del expression

                # continue to the next mukey if there are no wetlands to report
                if muWetlandAcres == 0.0:
                    continue

                for muFcode in muUniqueFcodes:

                    if not wetlandDict.has_key(muFcode):

                        expression = arcpy.AddFieldDelimiters(outIntersect,zoneField) + " = '" + mukey + "' AND " + arcpy.AddFieldDelimiters(outIntersect,fcodeField) + " = '" + muFcode + "'"
                        fcodeWetlandAcres = float("%.3f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect,("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))  # 263729.8023
                        fcodeWetlandAcresClean = str(splitThousands(int(round(fcodeWetlandAcres)))) + " ac."   # 263,729 Meters
                        fcodeWetlandAcresPercent = str(int(round(float("%.1f" %((fcodeWetlandAcres / muWetlandAcres) * 100))))) + " %"   # 30 %

                        # {u'Freshwater Pond_Permanently Flooded': (0.9, '1 ac.', 5, '100 %', 5, 35)}
                        wetlandDict[muFcode] = (fcodeWetlandAcres,fcodeWetlandAcresClean, len(fcodeWetlandAcresClean), fcodeWetlandAcresPercent, len(fcodeWetlandAcresPercent), len(muFcode))
                        del expression, fcodeWetlandAcres, fcodeWetlandAcresClean, fcodeWetlandAcresPercent

                # strictly for formatting
                maxFcodeNameLength = sorted([hydroinfo[5] for fcode,hydroinfo in wetlandDict.items()],reverse=True)[0]
                maxWetlandAcreChars = sorted([hydroinfo[2] for fcode,hydroinfo in wetlandDict.items()],reverse=True)[0]
                maxWetlandPercentChars = sorted([hydroinfo[4] for fcode,hydroinfo in wetlandDict.items()],reverse=True)[0]

                # sort the wetlandDict based on highest Acres; converts the dictionary into a tuple by default since you can't order a dictionary.
                # item #1 becomes fcodeWetlandAcres and NOT fcodeWetlandAcresClean as in the dictionary
                muWetlandAcresSorted = sorted(wetlandDict.items(), key=operator.itemgetter(1),reverse=True)
                wetlandCounter = 0

                # ('Artificial Path':(263,729 Meters,14,30 %,4,15))
                for wetlandInfo in muWetlandAcresSorted:

                    wetlandPrct = wetlandInfo[1][3]

                    # Only print out if wetlaned percent is greater than 1%; What if ALL fcodes are 0%?
                    if not wetlandPrct == "0 %":
                        wetlandCounter += 1
                        fcode = wetlandInfo[0]
                        wetlandAcres = wetlandInfo[1][1]
                        firstSpace = " " * (maxFcodeNameLength - len(fcode))
                        secondSpace = " " * (maxWetlandPercentChars - wetlandInfo[1][2])
                        AddMsgAndPrint(theTab + fcode + firstSpace + " -- " + wetlandAcres + secondSpace + " -- " + wetlandPrct,1)
                        del fcode, wetlandAcres,wetlandPrct,firstSpace,secondSpace

                del muWetlandAcres, muWetlandAcresClean, muWetlandPercent, wetlandDict, muUniqueFcodes, maxFcodeNameLength, maxWetlandAcreChars, maxWetlandPercentChars, muWetlandAcresSorted
            del muLayerUniqueMukeys

            """ --------------------- Report Wetlands info by Fcodes (hydro descriptions) only  ------------------------------ """
        else:
            AddMsgAndPrint("\n\tTotal Wetland Acres: " + totalWetlandAcresClean + " (" + projectPercent + " of total project area)\n",0)

            wetlandDict = dict()

            uniqueFcodes = set([row[0] for row in arcpy.da.SearchCursor(outIntersect, (fcodeField))])

            for fcode in uniqueFcodes:

                if not wetlandDict.has_key(fcode):

                    expression = arcpy.AddFieldDelimiters(outIntersect,fcodeField) + " = '" + fcode + "'"
                    fcodeWetlandAcres = float("%.3f" % (sum([row[0] for row in arcpy.da.SearchCursor(outIntersect,("SHAPE@AREA"),where_clause=expression)]) / 4046.85642))  # 263729.8023
                    fcodeWetlandAcresClean = str(splitThousands(int(round(fcodeWetlandAcres)))) + " ac."   # 263,729 Meters
                    fcodeWetlandAcresPercent = str(int(round(float("%.3f" %((fcodeWetlandAcres / totalWetlandAcres) * 100))))) + " %"   # 30 %

                    # 'Artificial Path':(263,729 Meters,14,30 %,4,15)
                    wetlandDict[fcode] = (fcodeWetlandAcres, fcodeWetlandAcresClean, len(fcodeWetlandAcresClean), fcodeWetlandAcresPercent, len(fcodeWetlandAcresPercent), len(fcode))
                    del expression, fcodeWetlandAcres, fcodeWetlandAcresClean, fcodeWetlandAcresPercent

            # strictly for formatting
            maxFcodeNameLength = sorted([hydroinfo[5] for fcode,hydroinfo in wetlandDict.items()],reverse=True)[0]
            maxWetlandAcreChars = sorted([hydroinfo[2] for fcode,hydroinfo in wetlandDict.items()],reverse=True)[0]
            maxWetlandPercentChars = sorted([hydroinfo[4] for fcode,hydroinfo in wetlandDict.items()],reverse=True)[0]

            # sort the hydroDict based on largest length; converts the dictionary into a tuple by default since you can't order a dictionary.
            # item #1 becomes fcodeHydroLength and NOT fcodeHydroLengthClean as in the dictionary
            fcWetlandAcresSorted = sorted(wetlandDict.items(), key=operator.itemgetter(1),reverse=True)

            # ('Artificial Path':(263,729 Meters,14,30 %,4,15))
            for wetlandInfo in fcWetlandAcresSorted:

                wetlandPrct = wetlandInfo[1][3]

                # Only print out if hydro percent is greater than 1%; What if ALL fcodes are 0%?
                if not wetlandPrct == "0 %":

                    fcode = wetlandInfo[0]
                    wetlandAcres = wetlandInfo[1][1]
                    firstSpace = " " * (maxFcodeNameLength - len(fcode))
                    secondSpace = " " * (maxWetlandPercentChars - wetlandInfo[1][2])

                    AddMsgAndPrint("\t\t" + fcode + firstSpace + " -- " + wetlandAcres + secondSpace + " -- " + wetlandPrct,1)
                    del fcode, wetlandAcres,wetlandPrct,firstSpace,secondSpace

            del wetlandDict, uniqueFcodes, maxFcodeNameLength, maxWetlandAcreChars, maxWetlandPercentChars, fcWetlandAcresSorted

        del wetlandFolder, workspaces, fcList, fcodeField, totalWetlandAcres, totalWetlandAcresClean

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return True

    except:
##        exc_type, exc_value, exc_traceback = sys.exc_info()
##
##        AddMsgAndPrint("\n\t***** print_tb:",2)
##        AddMsgAndPrint(traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
##
##        AddMsgAndPrint("\n\t***** print_exception:",2)
##        AddMsgAndPrint(traceback.print_exception(exc_type, exc_value, exc_traceback,
##                                  limit=2, file=sys.stdout))
##        AddMsgAndPrint("\n\t***** print_exc:",2)
##        AddMsgAndPrint(traceback.print_exc())
##
##        AddMsgAndPrint("\n\t***** format_exc, first and last line:",2)
##        formatted_lines = traceback.format_exc().splitlines()
##        AddMsgAndPrint(formatted_lines[0])
##        AddMsgAndPrint(formatted_lines[-1])
##
##        AddMsgAndPrint("\n\t***** format_exception:",2)
##        AddMsgAndPrint(repr(traceback.format_exception(exc_type, exc_value,
##                                              exc_traceback)))
##        AddMsgAndPrint("\n\t***** extract_tb:",2)
##        AddMsgAndPrint(repr(traceback.extract_tb(exc_traceback)))
##
##        AddMsgAndPrint("\n\t***** format_tb:",2)
##        AddMsgAndPrint(repr(traceback.format_tb(exc_traceback)))
##
##        AddMsgAndPrint("\n\t***** tb_lineno:", exc_traceback.tb_lineno,2)

        errorMsg()
        return False

# ===================================================================================
def processPedons():
# This function will query the NCSS_Soil_Characterization_Database for all pedons within
# the muLayer and a limited number of pedons outside of the muLayer.  All queried pedons will
# be printed out.

    try:
        AddMsgAndPrint("\nNCSS Soil Characterization Information:",0)

        pedonFolder = geoFolder + os.sep + "pedons"

        if not os.path.exists(pedonFolder):
            AddMsgAndPrint("\t\"pedons\" folder was not found in your MLRAGeodata Folder",2)
            return False
        else:
            arcpy.env.workspace = pedonFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("NCSS*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\"NCSS_Soil_Characterizaton_Database\" FGDB was not found in the pedons folder",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\tThere are more than 1 FGDB that begin with \"NCSS_Soil_Characterizaton_Database\" Only 1 can be present",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("NCSS_Site_Location","Point")  # Should only be one feature class

        if not len(fcList):
            AddMsgAndPrint("\tNCSS_Site_Location feature class was not found in the NCSS_Soil_Characterizaton_Database",2)
            return False

        userSiteField = FindField(fcList[0],"usiteid")
        pedonName = FindField(fcList[0],"PedonName")

        if not userSiteField:
            AddMsgAndPrint("\tPedons feature class is missing necessary fields -- usiteid",2)
            return False

        if not pedonName:
            AddMsgAndPrint("\tPedons feature class is missing necessary fields -- PedonName",2)
            return False

        pedonPath = fcList[0]
        arcpy.env.extent = pedonPath

        tempPedonLayer = "tempPedon"
        if arcpy.Exists(tempPedonLayer):
            arcpy.Delete_management(tempPedonLayer)
        arcpy.MakeFeatureLayer_management(pedonPath,tempPedonLayer)

        # Make feature layer was only making a layer for the points within the extent of the muLayer despite having a
        # national extent.  Not sure why!  I was forced to count the # of pedons to make sure the layer was correct.
        # A 2nd attempt at making a layer in case the pedon count is extremely low.
        if int(arcpy.GetCount_management(tempPedonLayer).getOutput(0)) < 500:
            AddMsgAndPrint("\tFailed to properly create feature layer from " + fcList[0],2)
            AddMsgAndPrint("\tCount is: " + str(int(arcpy.GetCount_management(tempPedonLayer).getOutput(0))))
            AddMsgAndPrint("\tCount should be: " + str(int(arcpy.GetCount_management(pedonPath).getOutput(0))))
##            AddMsgAndPrint("\tPedon Path: " + pedonPath)

            arcpy.Delete_management(tempPedonLayer)
            arcpy.CopyFeatures_management(pedonPath,scratchWS + os.sep + "tempPedonLayer")
            AddMsgAndPrint("\n\tMade a copy to " + scratchWS + os.sep + "tempPedonLayer",2)
            arcpy.MakeFeatureLayer_management(scratchWS + os.sep + "tempPedonLayer",tempPedonLayer)

            if int(arcpy.GetCount_management(tempPedonLayer).getOutput(0)) < 500:
                AddMsgAndPrint("\tFailed to properly create feature layer from " + scratchWS + os.sep + "tempPedonLayer",2)
                AddMsgAndPrint("\tCount is: " + str(int(arcpy.GetCount_management(tempPedonLayer).getOutput(0))))
                AddMsgAndPrint("\tPedon Path: " + scratchWS + os.sep + "tempPedonLayer")
                return False

        # Select all polys that intersect with the SAPOLYGON
        if bFeatureLyr:
            arcpy.SelectLayerByLocation_management(tempPedonLayer,"INTERSECT",muLayer,"", "NEW_SELECTION")
        else:
            arcpy.SelectLayerByLocation_management(tempPedonLayer,"INTERSECT",tempMuLayer,"", "NEW_SELECTION")

        # Count the # of features of select by location
        numOfPedons = int(arcpy.GetCount_management(tempPedonLayer).getOutput(0))

        if numOfPedons == 1:
            AddMsgAndPrint("\n\tThere is 1 LAB pedon that is completely within your layer:",0)
        elif numOfPedons > 1:
            AddMsgAndPrint("\n\tThere are " + str(numOfPedons) + " LAB pedons that are completely within this layer:",0)
        else:
            AddMsgAndPrint("\n\tThere are no LAB pedons that are completely within this layer",0)

        """ There are pedons that are within the muLayer; print them out """
        pedonDict = dict()
        if numOfPedons:
            with arcpy.da.SearchCursor(tempPedonLayer,[userSiteField,pedonName]) as cursor:
                for row in cursor:
                    pedonDict[row[0]] = (row[1],len(row[0])) # 1983MN079004 = (Angus,12)

            maxUserSiteLength = sorted([pedonInfo[1] for userSite,pedonInfo in pedonDict.iteritems()],reverse=True)[0]

            for pedon in pedonDict:
                firstSpace = " " * (maxUserSiteLength - len(pedon))
                AddMsgAndPrint("\t\t" + pedon + firstSpace + " --  " + pedonDict[pedon][0],1)

            del maxUserSiteLength

        """ I would like a minimum of 10 pedons that are outside of the layer to be printed.  Keep increasing
         the number of miles to look beyond the mulayer until at least 10 pedons are captured."""
        miles = 1
        b_morePedons = True

        while b_morePedons:
            distExpression = str(miles) + " Miles"
            arcpy.SelectLayerByAttribute_management(tempPedonLayer,"CLEAR_SELECTION")

            if bFeatureLyr:
                arcpy.SelectLayerByLocation_management(tempPedonLayer,"WITHIN_A_DISTANCE",muLayer, distExpression, "NEW_SELECTION")
            else:
                arcpy.SelectLayerByLocation_management(tempPedonLayer,"WITHIN_A_DISTANCE",tempMuLayer, distExpression, "NEW_SELECTION")

            numOfDistantPedons = int(arcpy.GetCount_management(tempPedonLayer).getOutput(0))

            # Pedon count is still less than 10; increase miles by 1
            if numOfDistantPedons < 10:
                miles += 1
                continue

            # Print Pedon user siteID and Pedon Name; exclude pedons printed above
            distantPedonDict = dict()
            uniquePedons = 0
            with arcpy.da.SearchCursor(tempPedonLayer,[userSiteField,pedonName]) as cursor:
                for row in cursor:
                    if not pedonDict.has_key(row[0]):
                        distantPedonDict[row[0]] = (row[1],len(row[0])) # 1983MN079004 = (Angus,12)
                        uniquePedons += 1

            maxUserSiteLength = sorted([pedonInfo[1] for userSite,pedonInfo in distantPedonDict.iteritems()],reverse=True)[0]

            AddMsgAndPrint("\n\tThere are " + str(uniquePedons) + " LAB pedons that are within " + distExpression + " of your layer:",0)

            for pedon in distantPedonDict:
                firstSpace = " " * (maxUserSiteLength - len(pedon))
                AddMsgAndPrint("\t\t" + str(pedon) + firstSpace + " --  " + str(distantPedonDict[pedon][0]),1)  #need to str() the pedon and

            del distExpression, numOfDistantPedons, distantPedonDict, uniquePedons, maxUserSiteLength
            b_morePedons = False

        if arcpy.Exists(tempPedonLayer):
            arcpy.Delete_management(tempPedonLayer)

        del pedonFolder, workspaces, fcList, userSiteField, pedonName, pedonPath, tempPedonLayer, numOfPedons, pedonDict, miles, b_morePedons

        return True

    except:
        errorMsg()
        return False

## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, traceback, urllib, re, arcpy, operator, getpass
from arcpy import env
from arcpy.sa import *

if __name__ == '__main__':

    try:
        muLayer = arcpy.GetParameter(0) # D:\MLRA_Workspace_Stanton\MLRAprojects\layers\MLRA_102C___Moody_silty_clay_loam__0_to_2_percent_slopes.shp
        geoFolder = arcpy.GetParameterAsText(1) # D:\MLRA_Workspace_Stanton\MLRAGeodata
        analysisType = arcpy.GetParameterAsText(2) # MLRA (Object ID)

##        muLayer = r'P:\MLRA_Geodata\MLRA_Workspace_AlbertLea\MLRAprojects\layers\SDJR___MLRA_103___Lester_Storden_complex__6_to_10_percent_slopes__moderately_eroded.shp'
##        geoFolder = r'P:\MLRA_Geodata\MLRA_Workspace_AlbertLea\MLRAGeodata'
##        #analysisType = 'Mapunit (MUKEY)'
##        analysisType = 'MLRA Mapunit'

        # Check Availability of Spatial Analyst Extension
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
            else:
                AddMsgAndPrint("\n\nSpatial Analyst license is unavailable.  May need to turn it on!",2)
                exit()

        except LicenseError:
            AddMsgAndPrint("\n\nSpatial Analyst license is unavailable.  May need to turn it on!",2)
            exit()
        except arcpy.ExecuteError:
            AddMsgAndPrint(arcpy.GetMessages(2),2)
            exit()

        # Set overwrite option
        arcpy.env.overwriteOutput = True

        # Start by getting information about the input layer
        descInput = arcpy.Describe(muLayer)
        muLayerDT = descInput.dataType.upper()
        muLayerName = descInput.Name
        bFeatureLyr = False

        if muLayerDT == "FEATURELAYER":
            bFeatureLyr = True
            muLayerPath = descInput.FeatureClass.catalogPath
            if muLayerPath.find(".gdb") > 1:
                outputFolder = os.path.dirname(muLayerPath[:muLayerPath.find(".gdb")+4])
            else:
                outputFolder = os.path.dirname(muLayerPath)
            textFilePath = outputFolder + os.sep + str(muLayer)+ ("_MUKEY.txt" if analysisType == "Mapunit (MUKEY)" else "_MLRA.txt")

        elif muLayerDT in ("FEATURECLASS"):
            muLayerPath = descInput.catalogPath
            if arcpy.Describe(os.path.dirname(muLayerPath)).datatype == "FeatureDataset":
                outputFolder = os.path.dirname(os.path.dirname(os.path.dirname(muLayerPath)))
            else:
                outputFolder = os.path.dirname(os.path.dirname(muLayerPath))
            textFilePath = outputFolder + os.sep + muLayerName + ("_MUKEY.txt" if analysisType == "Mapunit (MUKEY)" else "_MLRA.txt")

        elif muLayerDT in ("SHAPEFILE"):
            muLayerPath = descInput.catalogPath
            outputFolder = os.path.dirname(muLayerPath)
            textFilePath = outputFolder + os.sep + muLayerName[0:len(muLayerName)-4] + ("_MUKEY.txt" if analysisType == "Mapunit (MUKEY)" else "_MLRA.txt")

        else:
            AddMsgAndPrint("Invalid input data type (" + muLayerDT + ")",2)
            exit()

        if os.path.isfile(textFilePath):
            os.remove(textFilePath)

        # record basic user inputs and settings to log file for future purposes
        logBasicSettings()

        # define and set the scratch workspace
        scratchWS = setScratchWorkspace()
        arcpy.env.scratchWorkspace = scratchWS

        if scratchWS:

            # determine overlap using input and SAPOLYGON
            if not determineOverlap(muLayer):
                AddMsgAndPrint("\n\tNo Overlap with geodata extent.  Come Back Later!",2)
                exit()

            zoneField = getZoneField(analysisType)

            # set the zone field depending on analysis type
            if not zoneField:
                AddMsgAndPrint("\nCould not determine Zone field",2)
                exit()

            # ------------- Report how many polygons will be processed; exit if input is empty -------------------------
            totalPolys = int(arcpy.GetCount_management(muLayerPath).getOutput(0))
            selectedPolys = int(arcpy.GetCount_management(muLayer).getOutput(0))

            if totalPolys == 0:
                AddMsgAndPrint("\nNo Polygons found to process.  Empty Feature layer",2)
                exit()

            elif selectedPolys < totalPolys:
                AddMsgAndPrint("\n" + str(splitThousands(selectedPolys)) + " out of " + str(splitThousands(totalPolys)) + " polygons will be assessed",0)

            else:
                AddMsgAndPrint("\n" + str(splitThousands(totalPolys)) + " polygons will be assessed",0)

            """ if muLayer input is a feature layer (ArcMap) then copy the features into a feature class in the scratch.gdb.
                if muLayer input is a feature class (ArcCatalog) create a feature layer from it.  These will be used in case
                Tabulate Areas fails to execute.  I was continously having grid reading errors with Tabulate area
                and could not figure out why.  This is a workaround"""

            tempMuLayer = "tempMuLayer"
            if bFeatureLyr:
                muLayerExtent = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
                arcpy.CopyFeatures_management(muLayer, muLayerExtent)
                muLayerPath = muLayerExtent
                arcpy.env.extent = muLayerExtent
                arcpy.env.mask = muLayerExtent

            else:
                if arcpy.Exists(tempMuLayer):
                    arcpy.Delete_management(tempMuLayer)
                arcpy.MakeFeatureLayer_management(muLayer,tempMuLayer)
                arcpy.env.extent = tempMuLayer
                arcpy.env.mask = tempMuLayer

            bMunamePresent = FindField(muLayerPath,"MUNAME")
            bAreasymPresent = FindField(muLayerPath,"AREASYMBOL")
            bMukeyPresent = FindField(muLayerPath,"MUKEY")

            totalAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"))]) / 4046.85642))
            AddMsgAndPrint("\tTotal Acres = " + str(splitThousands(float("%.1f" %(totalAcres)))) + " ac.",0)

            """ ---------------------------- if analysisType is by Mapunit MUKEY, create a list of unique MUKEYs to inform the user -------------------------"""
            muDict = dict()
            if zoneField != "MLRA_Temp":

                mukeys = set([row[0] for row in arcpy.da.SearchCursor(muLayer, (zoneField))])

                if len(mukeys) > 1:
                    AddMsgAndPrint("\nThere are " + str(len(mukeys)) + " unique mapunits found:")
                else:
                    AddMsgAndPrint("\nThere is " + str(len(mukeys)) + " unique mapunit found:")

                # Get muname and areasym from input shapefile if they are present
                if bMunamePresent and bAreasymPresent:
                    for key in mukeys:
                        if not muDict.has_key(key):
                            expression = arcpy.AddFieldDelimiters(muLayer,zoneField) + " = '" + key + "'" # expression to select the MUKEY from muLayer layer
                            muname = [row[0] for row in arcpy.da.SearchCursor(muLayer, ("MUNAME"), where_clause = expression)]
                            areasym = [row[0] for row in arcpy.da.SearchCursor(muLayer, ("AREASYMBOL"), where_clause = expression)]
                            acres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"), where_clause = expression)]) / 4046.85642))

                            # muname was not found in muLayer so muname cannot be retrieved; Field exists but records are not populated
                            if len(muname) == 0:
                                AddMsgAndPrint("\n\tMap Unit Name for MUKEY: " + str(key) + " is not populated in " + muLayerName,1)
                                muname = ""

                            # areasymbol was not populated in muLayer so areasym cannot be retrieved; Field exists but records are not populated
                            if len(areasym) == 0:
                                AddMsgAndPrint("\n\tMap Unit Name for MUKEY: " + str(key) + " is not populated in " + muLayerName,1)
                                areasym = ""

                            muDict[key] = (muname[0],acres,len(muname),len(muname[0]),len(key),areasym[0])  # '23569':("Dubuque silt loam, 0 to 10 percent slopes",43546.6,10,43,5,WI025)
                            del expression, muname, areasym, acres

                # Try getting muname and areasym from SSURGO dataset bc they are not present in muLayer
                else:
                    AddMsgAndPrint("\n\tMapunit Name and/or Area Symbol are not present in " + muLayerName + ". Attempting to retrieve from MLRAGeodata MUPOLYGON layer",0)
                    muDict = getMapunitInfo(muDict,mukeys)

                # muname & areasymbol & mukey were all present, report mapunit breakdown -- Ideal Scenario
                if len(muDict) > 0:

                    bMunamePresent = True
                    bAreasymPresent = True

                    # strictly for formatting
                    maxMunameLength = sorted([muinfo[3] for mukey,muinfo in muDict.iteritems()],reverse=True)[0]
                    maxMukeyLength = sorted([muinfo[4] for mukey,muinfo in muDict.iteritems()],reverse=True)[0]
                    maxAcreLength = len(splitThousands(sorted([muinfo[1] for mukey,muinfo in muDict.iteritems()],reverse=True)[0]))
                    maxMUcountLength = len(str(sorted([muinfo[2] for mukey,muinfo in muDict.iteritems()],reverse=True)[0]))

                    for mukey,muinfo in muDict.iteritems():

                        areasym = muinfo[5]
                        muName = muinfo[0]
                        acres = muinfo[1]
                        muCount = muinfo[2]

                        firstSpace = " " * (maxMUcountLength - len(str(muCount)))
                        secondSpace = " " * (maxMukeyLength - len(mukey))
                        thirdSpace = " " * (maxMunameLength - len(muName))
                        fourthSpace = " " * (maxAcreLength - len(splitThousands(acres)))
                        muPcntAcres = float("%.1f" %((acres / totalAcres) * 100))

                        AddMsgAndPrint("\n\t" + firstSpace + str(muCount) + " polygons  --  "  + areasym + "  --  " + str(mukey) + secondSpace + "  --  " + muName + thirdSpace + "  --  " + splitThousands(acres) + fourthSpace + " ac. -- " + str(muPcntAcres) + " %",0)

                        # Print Components if SSURGO dataset is available and MUKEY
                        compList = getComponents(mukey)
                        if len(compList) > 0:
                            for compMsg in compList:
                                AddMsgAndPrint("\t\t" + compMsg,1)

                        del areasym,muName,acres,muCount,firstSpace,secondSpace,thirdSpace,fourthSpace,muPcntAcres,compList
                    del maxMunameLength, maxAcreLength

                # Report mukey breakdown -- muname & areasymbol were not present AND SSURGO FGDB was missing as well.
                else:
                    for key in mukeys:
                        expression = arcpy.AddFieldDelimiters(muLayer,zoneField) + " = '" + key + "'"
                        muCount = len([row[0] for row in arcpy.da.SearchCursor(muLayer, (zoneField), where_clause=expression)])
                        acres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"), where_clause = expression)]) / 4046.85642))
                        muPcntAcres = float("%.1f" %((acres / totalAcres) * 100))
                        AddMsgAndPrint("\t" + str(key) + " -- " + str(muCount) + " polygons  --  " + splitThousands(acres) + " ac. -- " + str(muPcntAcres) + " %",0)
                        del expression,muCount,acres,muPcntAcres
                del mukeys

            """----------------------------- Start Adding pedon points and records---------------------------------------"""
            arcpy.SetProgressor("step", "Beginning Rapid Mapunit Assesment", 0, 18, 1)

            """ -------------------- Climate Data ------------------------------------ """
            arcpy.SetProgressorLabel("Acquiring Climate Data")
            if not processClimate():
                AddMsgAndPrint("\n\tFailed to Acquire Climate Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ --------------------  NLCD Data ------------------------------------ """
            arcpy.SetProgressorLabel("Computing Land Use - Land Cover (NLCD) Information ")
            if not processNLCD():
                AddMsgAndPrint("\n\tFailed to Acquire Land Use - Land Cover (NLCD) Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ --------------------  NASS Data ------------------------------------ """
            arcpy.SetProgressorLabel("Computing Agricultural Land Cover (NASS-CDL) Information")
            if not processNASS():
                AddMsgAndPrint("\n\tFailed to Acquire Agricultural Land Cover (NASS) Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ --------------------  EcoSystem Data ------------------------------------ """
            arcpy.SetProgressorLabel("Computing Terrestrial Ecological Systems (NatureServ) Information")
            if not processNatureServe():
                AddMsgAndPrint("\n\tFailed to Acquire Terrestrial Ecological Systems (NatureServ) Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ --------------------  LandFire Data ------------------------------------ """
            arcpy.SetProgressorLabel("Acquiring LANDFIRE Vegetation (LANDFIRE - USGS) Information")
            if not processLandFire():
                AddMsgAndPrint("\n\tFailed to Acquire LANDFIRE Vegetation (LANDFIRE - USGS) Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ ---------------------  Get Original Elevation Source ------------------------------ """
            arcpy.SetProgressorLabel("Getting Original Elevation Source Information")
            if not getElevationSource():
                AddMsgAndPrint("\n\tFailed to Acquire Original Elevation Source Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Elevation Data ------------------------------ """
            arcpy.SetProgressorLabel("Gathering Elevation Information")
            if not processElevation():
                AddMsgAndPrint("\n\tFailed to Acquire Elevation Information",2)
            arcpy.SetProgressorPosition()

            """ -------------------- Aspect Data ------------------------------------ """
            arcpy.SetProgressorLabel("Calculating Aspect Information")
            if not processAspect():
                AddMsgAndPrint("\n\tFailed to Acquire Aspect Information",2)
            arcpy.SetProgressorPosition()

            """ -------------------- Slope Data ------------------------------------ """
            arcpy.SetProgressorLabel("Calculating Slope Information")
            if not processSlope():
                AddMsgAndPrint("\n\tFailed to Acquire Slope Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Component Composition % - Total Area ------------------------------ """
            arcpy.SetProgressorLabel("Calculating Component Composition Percent -- Weighted by Area")
            if arcpy.ListFields(muLayerPath, "MUKEY") > 0:
                if not processComponentComposition():
                    AddMsgAndPrint("\n\tFailed to Calculate Component Composition % of all mapunits",2)
                arcpy.SetProgressorPosition()
            else:
                AddMsgAndPrint("\nCannot calculate component composition % -- MUKEY is missing from " + muLayerName,2)
                arcpy.SetProgressorPosition()

            """ ---------------------  Adjacent Component Data ------------------------------ """
            arcpy.SetProgressorLabel("Itemizing Major Components mapped in adjacent polygons")
            if not processAdjacentComponents(zoneField):
                AddMsgAndPrint("\n\tFailed to Acquire Adjacent Mapunit Information",2)
            arcpy.SetProgressorPosition()

            """ --------------------  NCSS Characterization Data ------------------------------------ """
            arcpy.SetProgressorLabel("Acquiring NCSS Lab Pedon Information")
            if not processPedons():
                AddMsgAndPrint("\n\tFailed to Acquire NCSS Lab Pedon Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ ---------------------  LRR Data ------------------------------ """
            arcpy.SetProgressorLabel("Gathering Land Resource Region (LRR) Information")
            if not processLRRInfo():
                AddMsgAndPrint("\n\tFailed to Acquire LRR Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  MLRA Data ------------------------------ """
            arcpy.SetProgressorLabel("Gathering Major Land Resource Region (MLRA) Information")
            if not processMLRAInfo():
                AddMsgAndPrint("\n\tFailed to Acquire MLRA Information",2)
            arcpy.SetProgressorPosition() # Update the progressor position

            """ ---------------------  EcoRegion Subsection Data ------------------------------ """
            arcpy.SetProgressorLabel("Ecoregion Subsection Information")
            if not processEcoregions():
                AddMsgAndPrint("\n\tFailed to Acquire Ecoregion Subsection Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Ownership Data ------------------------------ """
            arcpy.SetProgressorLabel("Acquiring Land Ownership Information")
            if not processLandOwnership():
                AddMsgAndPrint("\n\tFailed to Acquire Land Ownership Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Hydro Data ------------------------------ """
            arcpy.SetProgressorLabel("Processing 24k Hydro Information")
            if not processHydro():
                AddMsgAndPrint("\n\tFailed to Acquire 24k Hydro Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Wetland Data ------------------------------ """
            arcpy.SetProgressorLabel("Processing Wetland (NWI) Hydro Information")
            if not processNWI():
                AddMsgAndPrint("\n\tFailed to Acquire Wetlands (NWI) Information",2)
            arcpy.SetProgressorPosition()

            arcpy.ResetProgressor()
            arcpy.SetProgressorLabel(" ")

            # Delete the MLRA_temp field from the feature classes if they exist
            if zoneField == "MLRA_Temp":
                if arcpy.ListFields(muLayerPath, "MLRA_Temp") > 0:
                    arcpy.DeleteField_management(muLayerPath, "MLRA_Temp")
                if arcpy.ListFields(muLayer, "MLRA_Temp") > 0:
                    arcpy.DeleteField_management(muLayer, "MLRA_Temp")

            # Delete the muLayer copy from the scratch workspace
            if bFeatureLyr and arcpy.Exists(muLayerExtent):
                arcpy.Delete_management(muLayerExtent)

            # Delete the feature layer created in memory
            if not bFeatureLyr and arcpy.Exists(tempMuLayer):
                arcpy.Delete_management(tempMuLayer)

            AddMsgAndPrint("\nThis Report is saved in the following path: " + textFilePath + "\n",0)
            arcpy.Compact_management(arcpy.env.scratchGDB)

        else:
            AddMsgAndPrint("\nFailed to set scratchworkspace\n",2)
            exit()

        arcpy.CheckInExtension("Spatial Analyst")

    except:
        errorMsg()