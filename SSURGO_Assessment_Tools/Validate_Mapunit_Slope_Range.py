#-------------------------------------------------------------------------------
# Name:        Validate Mapunit Slope Range
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:        03/02/2015
# Last Modified:  08/19/2016
# Copyright:   (c) Adolfo.Diaz 2015

#-------------------------------------------------------------------------------

## ===================================================================================
class ExitError(Exception):
    pass

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

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
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

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

## ===============================================================================================================
def determineOverlap(muLayer):
    # This function will compute a geometric intersection of the mu polygons and the extent
    # of the slope layer to determine overlap.  If the number of features in the output is greater than
    # the sum of the features of the muLayerPath and the extentboundary then overlap is assumed
    # and TRUE is returned otherwise FALSE is returned.

    try:
        AddMsgAndPrint("\nDeterming overlap between input polygons and slope layer",0)

        # Create a polygon footprint from the slope layer
        outDomain = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

        outGeom = "POLYGON"
        arcpy.RasterDomain_3d(slopeLayer, outDomain, outGeom)

        # Intersect the soils and input layer
        outIntersect = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Intersect_analysis([muLayer,outDomain], outIntersect,"ALL","","INPUT")

        totalMUacres = sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"))]) / 4046.85642
        totalIntAcres = sum([row[0] for row in arcpy.da.SearchCursor(outIntersect, ("SHAPE@AREA"))]) / 4046.85642

        # All features are within the geodata extent
        if int(totalMUacres) == int(totalIntAcres):
            AddMsgAndPrint("\tALL polygons are within Raster extent",0)
            return True

        # some features are outside the geodata extent.  Warn the user
        elif totalIntAcres < totalMUacres and totalIntAcres > 1:
            prctOfCoverage = round((totalIntAcres / totalMUacres) * 100,1)

            if prctOfCoverage > 50:
                AddMsgAndPrint("\tWARNING: There is only " + str(prctOfCoverage) + " % coverage between your area of interest and Raster Layer",1)
                AddMsgAndPrint("\tWARNING: " + splitThousands(round((totalMUacres-totalIntAcres),1)) + " .ac will not be accounted for",1)
                return True
            elif prctOfCoverage < 1:
                AddMsgAndPrint("\tALL polygons are outside of your Raster Extent.  Cannot proceed with analysis",2)
                return False
            else:
                AddMsgAndPrint("\tThere is only " + str(prctOfCoverage) + " % coverage between your area of interest and Raster extent",2)
                return False

        # There is no overlap
        else:
            AddMsgAndPrint("\tALL polygons are ouside of your Raster Extent.  Cannot proceed with analysis",2)
            return False

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        if arcpy.Exists(outDomain):
            arcpy.Delete_management(outDomain)

        del outDomain,outGeom,outIntersect,numOfMulayerPolys,tempMULayer,numOfSelectedPolys

    except:
        errorMsg()
        return False

## ===================================================================================
def getZoneField(muLayerPath, analysisType):
    # This function will return a field name based on the analysis type that
    # was chosen by the user.  If analysis type is MUKEY, then MUKEY is returned if
    # the field exists, otherwise a newly created field "MLRA_Temp" will be returned.
    # "MLRA_Temp" will be returned for MLRA analysis type
    # OID field will be returned for each polygon

    try:

        theDesc = arcpy.Describe(muLayerPath)
        theFields = theDesc.fields
        theField = theFields[0]
        idField = theDesc.OIDFieldName

        if analysisType.find('Mapunit (MUKEY)') > -1:

            if len(arcpy.ListFields(muLayerPath,"MUKEY")) > 0:
                return "MUKEY"
            else:
                AddMsgAndPrint("\nAnalysis Cannot be done by Mapunit since MUKEY is missing.",1)
                AddMsgAndPrint("Proceeding with analysis using MLRA ",1)

                if not len(arcpy.ListFields(muLayerPath, "MLRA_Temp")) > 0:
                    arcpy.AddField_management(muLayer,"MLRA_Temp","TEXT", "", "", 15)

                arcpy.CalculateField_management(muLayer,"MLRA_Temp", "\"MLRA Mapunit\"", "PYTHON_9.3", "")
                return "MLRA_Temp"

        elif analysisType.find('MLRA Mapunit') > -1:
            if not len(arcpy.ListFields(muLayerPath, "MLRA_Temp")) > 0:
                arcpy.AddField_management(muLayer,"MLRA_Temp","TEXT", "", "", 15)

            arcpy.CalculateField_management(muLayer,"MLRA_Temp", "\"MLRA Mapunit\"", "PYTHON_9.3", "")
            return "MLRA_Temp"

        # Analysis Type = Polygon
        else:
            AddMsgAndPrint("\nWARNING Reporting by polygon might be very verbose")
            return idField

    except:
        errorMsg()
        return ""

## ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ===================================================================================
def parseMapunitSlopeValues(projectName):
    # Tries to parse out the Slope low and Slope High of the input name

    try:

        # double checking removing spaces
        projectName = projectName.replace("  "," ")

        # First try looking for basic words such as percent or %
        if projectName.rfind("percent") > -1 or projectName.rfind("%") > -1:

            if projectName.find("percent") > -1:
                searchThis = projectName[0:projectName.rfind("percent")].split()
            else:
                searchThis = projectName[0:projectName.rfind("%")].split()

            integerList = []

            if len(searchThis) > 0:

                for i in range(len(searchThis)-1,0,-1):

                    try:
                        int(searchThis[i].replace("%",""))
                        integerList.append(searchThis[i].replace("%",""))
                    except:
                        continue

                if len(integerList) > 1:
                    return int(integerList[0]),int(integerList[1])
                else:
                    return "",""

            else:
                return "","'"

        else:
            return "","'"


    except:
        errorMsg()
        return "",""


## ===================================================================================
def getAnalysisType(muLayerPath):
    # This function will return a field name based on the analysis type that
    # was chosen by the user.  If analysis type is MUKEY, then MUKEY is returned if
    # it exists, otherwise a newly created field "MLRA_Temp" will be returned.
    # "MLRA_Temp" will be returned for MLRA analysis type
    # OID field will be returned for each polygon

    try:

        mukeyField = FindField(muLayerPath,"MUKEY")

        if mukeyField:
            uniqueMukeys = set([row[0] for row in arcpy.da.SearchCursor(muLayerPath, (mukeyField))])

            if len(uniqueMukeys) > 1:
                return uniqueMukeys,"MUKEY"
            else:
                # If there is only 1 unique MUKEY or its not populated analyze all polygons
                return "","MLRA"

        else:
            return "","MLRA"

        del mukeyField

    except:
        errorMsg()
        return "","MLRA"

## ===================================================================================
def FindField(layer, chkField):
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

            return ""

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def getBinHeight(value,option=1):
    # This function will iterate through the 2nd tuple element returned by the histogram function (bins)
    # and determine the index position that is less than the 'value' being passed in.  This index position
    # directly corresponds to the 1st tuple element returned by the histogram function (n), which records
    # the height of that specific bin.
    # Return the height of the bin normalized on a 1.0 scale

    try:
        binPos = -1

        for bin in bins:

            if value <= bin:
                break

            else:
                binPos+=1

        if n[binPos] < n[binPos+1]:
            binPos += 1

    ##    # binPos is the last element in bins; could be that the value falls in the last bin or
    ##    # value was errorneous
    ##    if binPos == len(bins) - 1:

        # if the value exceed the last value in bins then simply take the last value in the bin.  This is due to the fact
        # that the histogram is created using the stretchedArray and not the slopeArray.
        if binPos == len(n):
            binPos -= 1

        # return the element from the 'n' array
        if option == 1:
            # normalize it by dividing it by the max height of the histogram this way it is at the same scale as the Y-axis.
            #print "\tInside getBinHeight: " + str(plot.yticks()[0][-1:][0])
            return n[binPos] / plot.yticks()[0][-1:][0]
        else:
            return n[binPos]

    except:
        errorMsg()
        return ""

## ===================================================================================
def closeFile(file):
    # This function will close a specific file if it is currently opened in windows
    # by killing its process ID (PID).  Takes in 1 argument: the file (path and name)
    # In python 3.0 or higher try using the psutil to obtain list of processes and IDs
    # and kill processes as well.

    try:
        import subprocess, signal

        fileName = os.path.basename(file)

        # command that will be passed
        # WMIC = Windows Management Instrumentation Command-line (command line and scripting interface)
        # PROCESS = list all currently running Processes
        # get "Caption,Commandline,Processid" properties from processes
        cmd = 'WMIC PROCESS get Caption,Commandline,Processid'

        # connect to all currently running window processes by executing a child program
        # through a new process using the Popen constructor
        # The shell argument (which defaults to False) specifies whether to use the shell as the program
        # to execute. If shell is True, it is recommended to pass args as a string rather than as a sequence.
        # The only time you need to specify shell=True on Windows is when the command you wish to execute is
        # built into the shell (e.g. dir or copy). You do not need shell=True to run a batch file or console-based executable.
        # I set it to true b/c 'WMIC PROCESS...etc' is built into the CMD.exe shell
        # subprocess.PIPE = Special value that can be used as the stdin, stdout or stderr argument to Popen and indicates
        # that a pipe to the standard stream should be opened.
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        for line in proc.stdout:

            if str(line).find(file) > -1:

                # Capture the program, file path, PID
                # ['notepad.exe', '"C:\\Windows\\system32\\NOTEPAD.EXE"', 'C:\\Temp\\SuperfishCertificateCheck.txt', '4836']
                process = line.split()
                processID = int(process[len(process)-1])

                AddMsgAndPrint(fileName + " is currently open.  Automatically closing file!",2)
                time.sleep(3)

                try:
                    # Signals are an operating system feature that provide a means of notification of an event,
                    # and having it handled asynchronously.  Send Signal to the process ID.
                    os.kill(processID, signal.SIGTERM)
                    time.sleep(3)

                    # terminate the Popen construct (should get rid of WMIC and cmd.exe processes)
                    proc.kill()
                except:
                    proc.kill()
                    AddMsgAndPrint("\tCould not close file",2)
                    errorMsg()
                    return False

                del process, processID
                return True

        del fileName,cmd,proc
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def getElevationSource():
# This function will provide a breakdown of original Elevation Source information
# by intersecting the mulayer with the SSR10_Elevation_Source feature class.
# i.e. LiDAR 1M - 1,000 acres - 80%
# i.e. LiDAR 3M - 300 acres - 20%

    try:
        if slopeLayerPath.find('.gdb') > 0:
            if os.path.basename(os.path.dirname(os.path.dirname(slopeLayerPath))) == 'elevation':
                elevFolder = os.path.dirname(os.path.dirname(slopeLayerPath))
            else:
                return False
        else:
            return False

        if not os.path.exists(elevFolder):
            AddMsgAndPrint("\nOriginal Elevation Source Information:",0)
            AddMsgAndPrint("\t\"elevation\" folder was not found in your MLRAGeodata Folder",2)
            return False

        arcpy.env.workspace = elevFolder

        workspaces = arcpy.ListWorkspaces("Elevation.gdb", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\nOriginal Elevation Source Information:",0)
            AddMsgAndPrint("\tElevation data was not found in the elevation folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        elevSource = arcpy.ListFeatureClasses("SSR10_Elevation*","Polygon")

        if not len(elevSource):
            AddMsgAndPrint("\nOriginal Elevation Source Information:",0)
            AddMsgAndPrint("\tSSR10_Elevation_Source feature class was not found in the Elevation File Geodatabase",2)
            return False

        AddMsgAndPrint("\nOriginal Elevation Source Information:",0)

        sourceField = FindField(elevSource[0],"Source")

        if not sourceField:
            AddMsgAndPrint("\t feature class is missing necessary fields",2)
            return False

        outIntersect = scratchWS + os.sep + "elevIntersect"
        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        # Intersect the mulayer with the SSR10 Elevation Source
        arcpy.Intersect_analysis([[tempMuLayer,1],[elevSource[0],2]],outIntersect,"ALL","","")

        # Make sure there are output polygons as a result of intersection
        if not int(arcpy.GetCount_management(outIntersect).getOutput(0)) > 0:
            AddMsgAndPrint("\tThere is no overlap between layers " + os.path.basename(muLayerPath) + " and 'SSR10 Elevation Source' layer" ,2)

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
        sourceList = list()

        for sourceInfo in sourceAcresSorted:
            source = sourceInfo[0]
            sourceAcres = sourceInfo[1][1]
            sourcePercent = sourceInfo[1][2]
            firstSpace = " " * (maxSourceNameLength - len(source))
            secondSpace = " " * (maxSourceAcreLength - sourceInfo[1][3])

            AddMsgAndPrint("\t" + source + firstSpace + " -- " + sourceAcres + " ac." + secondSpace + " -- " + str(sourcePercent) + " %" ,0)
            sourceList.append(str(source + firstSpace + " -- " + sourceAcres + " ac." + secondSpace + " -- " + str(sourcePercent) + " %"))

        del elevFolder, workspaces, elevSource, sourceField, elevSourceDict, uniqueSource, maxSourceNameLength, maxSourceAcreLength, sourceAcresSorted

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        return sourceList

    except:
        errorMsg()
        return False

## ===================================================================================
def createShapefile(below5,above95,zsTable):

    try:
        arcpy.env.overwriteOutput = True

        # There are polys below the 5th and above the 95th percentile
        if len(below5) and len(above95):
            newShape = outputFolder + os.sep + "polysBelow" + str(int(percentile5)) + "_polysAbove" + str(int(percentile95)) + ".shp"
            mergedList = below5 + above95
            sQuery = arcpy.AddFieldDelimiters(muLayerPath,idField) + " IN (" + str(mergedList)[1:-1] + ")"
            lyrPath = os.path.dirname(sys.argv[0]) + os.sep + "polysBelow_polysAboveSymbology.lyr"
            AddMsgAndPrint("\nCreating Shapefile of polygons with a mean slope < than " + str(percentile5) + "% slope and > than " + str(percentile95) + "% slope",0)

        # There are only polys below the 5th percentile
        elif len(below5) and not len(above95):
            newShape = outputFolder + os.sep + "polysBelow" + str(int(percentile5)) + ".shp"
            sQuery = arcpy.AddFieldDelimiters(muLayerPath,idField) + " IN (" + str(below5)[1:-1] + ")"
            lyrPath = os.path.dirname(sys.argv[0]) + os.sep + "polysBelowSymbology.lyr"
            AddMsgAndPrint("\nCreating Shapefile of polygons with a mean slope < than " + str(percentile5) + "% slope",0)

        # There are only polys above the 95th percentile
        elif not len(below5) and len(above95):
            newShape = outputFolder + os.sep + "polysAbove" + str(int(percentile95)) + ".shp"
            sQuery = arcpy.AddFieldDelimiters(muLayerPath,idField) + " IN (" + str(above95)[1:-1] + ")"
            lyrPath = os.path.dirname(sys.argv[0]) + os.sep + "polysAboveSymbology.lyr"
            AddMsgAndPrint("\nCreating Shapefile of polygons with a mean slope > than " + str(percentile95) + "% slope",0)

        # There are no polys below the 5th and above the 95th percentile
        else:
            AddMsgAndPrint("\nThere were no polygons below the 5th Percentile or above the 95th Percentile",0)
            return False, False

        # Isolate anomaly polygons using the query from above
        arcpy.SelectLayerByAttribute_management(tempMuLayer,"NEW_SELECTION",sQuery)
        lyrField = "Layer"
        symbField = "Symbology"

        """ Add 2 fields for symbology purposes and calculate them depending on whether the poly is below or above percentile threshold """
        # Add a Layer field if it doesn't exist
        if arcpy.ListFields(tempMuLayer, lyrField) > 0:
            arcpy.DeleteField_management(tempMuLayer,lyrField)
        arcpy.AddField_management(tempMuLayer,lyrField,"TEXT","#","#",len(muLayerName) +3)

        # Add a Symbol field if it doesn't exist
        if arcpy.ListFields(tempMuLayer,symbField) > 0:
            arcpy.DeleteField_management(tempMuLayer,symbField)
        arcpy.AddField_management(tempMuLayer,symbField,"TEXT","#","25",)

        # Calculate the new fields
        with arcpy.da.UpdateCursor(tempMuLayer,(idField,lyrField,symbField)) as cursor:
            for row in cursor:
                row[1] = muLayerName
                row[2] = ""

                if len(below5):
                    if row[0] in below5:
                        row[2] = "Below 5th Percentile"

                if len(above95):
                    if row[0] in above95:
                        row[2] = "Above 95th Percentile"

                cursor.updateRow(row)

        """ ---- Transfer fields from zonal stats table to shapefile --------  """
        zsFields = arcpy.Describe(zsTable).fields
        ignoreFields = ("Rowid","OID","FID","COUNT","AREA","Shape","OBJECTID")
        newFields = [idField]

        for field in zsFields:
            if field.name in [f.name for f in arcpy.ListFields(tempMuLayer)] or field.name in ignoreFields:
                continue

            if field.type =="Integer":
                arcpy.AddField_management(tempMuLayer,field.name,"SHORT")
                newFields.append(field.name)

            if field.type == "String":
                arcpy.AddField_management(tempMuLayer,field.name,"TEXT","#","#",field.length)
                newFields.append(field.name)

            if field.type == "Double":
                arcpy.AddField_management(tempMuLayer,field.name,"DOUBLE")
                newFields.append(field.name)

        """ -------------- Capture attributes from zsTable in dictionary --------------"""
        zsDict = dict()
        with arcpy.da.SearchCursor(zsTable,newFields) as cursor:
            for row in cursor:
                if row[0] in below5 or row[0] in above95:
                    valList = list()
                    for i in range(1,len(newFields)):
                        valList.append(row[i])

                    zsDict[row[0]] = valList

        """ -------------- Update tempMuLayer using dictionary lookup by keys -------- """
        with arcpy.da.UpdateCursor(tempMuLayer,newFields) as cursor:
            for row in cursor:
                for i in range(1,len(newFields)):
                    row[i] = zsDict.get(row[0])[i-1]

                cursor.updateRow(row)

        AddMsgAndPrint("\tLocation: " + newShape)

        arcpy.CopyFeatures_management(tempMuLayer,newShape)
        arcpy.SelectLayerByAttribute_management(tempMuLayer, "CLEAR_SELECTION")
        return newShape,lyrPath

    except:
        errorMsg()
        return False, False

## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, traceback, re, arcpy, operator, numpy, time, getpass
import matplotlib.pyplot as plot
from matplotlib.backends.backend_pdf import PdfPages
from arcpy import env
from arcpy.sa import *

if __name__ == '__main__':

    muLayer = arcpy.GetParameter(0) # D:\MLRA_Workspace_Stanton\MLRAprojects\layers\MLRA_102C___Moody_silty_clay_loam__0_to_2_percent_slopes.shp
    slopeLayer = arcpy.GetParameter(1)
    lowSlope = arcpy.GetParameter(2)
    highSlope = arcpy.GetParameter(3)
##    analysisType = arcpy.GetParameterAsText(4)

##    muLayer = r'C:\flex\histogramTest\HistTest.gdb\mukey_1690935'
##    slopeLayer = r'C:\MLRA_Workspace_AlbertLea\MLRAGeodata\elevation\Elevation.gdb\Slope_10m_MLRA'
##    lowSlope = 8
##    highSlope = 18

##    muLayer = r'P:\MLRA_Geodata\MLRA_Workspace_Onalaska\MLRAprojects\layers\SDJR___MLRA_105___Plainfield_loamy_sand__0_to_3_percent_slopes.shp'
##    slopeLayer = r'P:\MLRA_Geodata\MLRA_Workspace_Onalaska\MLRAGeodata\elevation\Elevation.gdb\Slope_10m_MLRA'
##    lowSlope = 0
##    highSlope = 3

    try:

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Check Availability of Spatial Analyst and 3D Analyst Extension +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-"""
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
            else:
                raise ExitError,"\n\nSpatial Analyst license is unavailable.  May need to turn it on!"

        except LicenseError:
            raise ExitError,"\n\nSpatial Analyst license is unavailable.  May need to turn it on!"
        except arcpy.ExecuteError:
            raise ExitError, arcpy.GetMessages(2)

        try:
            if arcpy.CheckExtension("3D") == "Available":
                arcpy.CheckOutExtension("3D")
            else:
                raise ExitError,"\n\n3D Analyst license is unavailable.  May need to turn it on!"

        except LicenseError:
            raise ExitError,"\n\n3d Analyst license is unavailable.  May need to turn it on!"
        except arcpy.ExecuteError:
            raise ExitError, arcpy.GetMessages(2)

        # Set overwrite option
        arcpy.env.overwriteOutput = True

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Get information about the input layers  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-"""
        # Collect info on the muLayer
        descInput = arcpy.Describe(muLayer)
        muLayerDT = descInput.dataType.upper()
        idField = descInput.OIDFieldName # will be used to with zonal statistics

        if muLayerDT == "FEATURELAYER":
            muLayerName = descInput.Name
            muLayerPath = descInput.FeatureClass.catalogPath

            if muLayerPath.find(".gdb") > 1:
                outputFolder = os.path.dirname(muLayerPath[:muLayerPath.find(".gdb")+4])
            else:
                outputFolder = os.path.dirname(muLayerPath)

        elif muLayerDT in ("FEATURECLASS"):
            muLayerName = descInput.Name
            muLayerPath = descInput.catalogPath
            if arcpy.Describe(os.path.dirname(muLayerPath)).datatype == "FeatureDataset":
                outputFolder = os.path.dirname(os.path.dirname(os.path.dirname(muLayerPath)))
            else:
                outputFolder = os.path.dirname(os.path.dirname(muLayerPath))

        elif muLayerDT in ("SHAPEFILE"):
            muLayerName = descInput.Name
            muLayerPath = descInput.catalogPath
            outputFolder = os.path.dirname(muLayerPath)

        else:
            raise ExitError,"Invalid input data type (" + muLayerDT + ")"

        del descInput, muLayerDT

        scratchWS = setScratchWorkspace()
        arcpy.env.scratchWorkspace = scratchWS

        if not scratchWS:
            raise ExitError, "\nCould not set scratch workspace! Try setting it manually"

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Collect info about the slope layer +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-"""
        descRaster = arcpy.Describe(slopeLayer)
        slopeLayerPath = descRaster.catalogPath
        #slopeLayerName = descRaster.baseName
        slopeLayerName = os.path.basename(slopeLayerPath)  #couldn't use descRaster.baseName b/c it removes raster ext from name i.e. .img
        sr = descRaster.SpatialReference

        units = sr.LinearUnitName

        if units == "Meter":
            units = "M"
        elif units == "Foot":
            units = "Ft"
        else:
            raise ExitError, "\nCould not determine linear units of Slope....Exiting!"

        cellSize = descRaster.MeanCellWidth
        res = str(int(cellSize)) + units

        # Isolate the name of the input layers and remove and double blanks and underscores and extentions.
        projectName = ((os.path.basename(muLayerPath).replace("_"," ")).split('.')[0]).replace("  "," ")
        rasterName = os.path.basename(slopeLayerPath).replace("_"," ")

        AddMsgAndPrint("\nProcessing Layer: " + projectName,0)
        arcpy.SetProgressor("step", "Processing Layer: " + projectName, 0, 8, 1)

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Print basic info +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-"""
        totalPolys = int(arcpy.GetCount_management(muLayerPath).getOutput(0))
        selectedPolys = int(arcpy.GetCount_management(muLayer).getOutput(0))
        totalAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"))]) / 4046.85642))

        if selectedPolys < totalPolys:
            assessedPolys = str(splitThousands(selectedPolys)) + " out of " + str(splitThousands(totalPolys)) + " polygons will be assessed"
            bSubset = True
            AddMsgAndPrint("\t" + assessedPolys,0)
        else:
            assessedPolys = str(splitThousands(totalPolys)) + " polygons will be assessed"
            bSubset = False
            AddMsgAndPrint("\t" + assessedPolys,0)

        AddMsgAndPrint("\tTotal Acres: " + str(splitThousands(totalAcres)),0)
        AddMsgAndPrint("\nMapunit Slope Range Values:",0)
        AddMsgAndPrint("\tLow Slope: " + str(lowSlope),0)
        AddMsgAndPrint("\tHigh Slope: " + str(highSlope),0)

        """ ----------------------   Determine Analysis Type    ----------------------"""
##        uniqueMukeys,analysisType = getAnalysisType(muLayerPath)

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        """ ---------------------------------------- Create Numpy Array from extracted slope values  -----------------------------------"""
        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        """ ----------------------   Extract Slope values for all polygons OR by MUKEY; depending on analysis type    ----------------------"""
    ##    AddMsgAndPrint("\nExtracting Slope for unique mapunits")
    ##    mukeyRasters = []

##        if analysisType == "MUKEY":
##            for mukey in uniqueMukeys:
##
##                # Make a feature layer with the mukey subset delineations
##                featureLayer = scratchWS + os.sep + "temp_" + str(mukey)
##                if arcpy.Exists(featureLayer):
##                    arcpy.Delete_management(featureLayer)
##
##                where_clause = arcpy.AddFieldDelimiters(muLayerPath,"MUKEY") + " = '" + mukey + "'"
##                arcpy.MakeFeatureLayer_management(muLayerPath,featureLayer,where_clause)
##
##                rasterMask = scratchWS + os.sep + "tempRast_" + str(mukey)
##                if arcpy.Exists(rasterMask):
##                    arcpy.Delete_management(rasterMask)
##
##                outExtractByMask = ExtractByMask(slopeLayer,featureLayer)
##                outExtractByMask.save(rasterMask)
##                mukeyRasters.append(rasterMask)
        # Create a feature layer from input; had trouble using the input directly
        tempMuLayer = "tempMuLayer"
        if arcpy.Exists(tempMuLayer):
            arcpy.Delete_management(tempMuLayer)
        arcpy.MakeFeatureLayer_management(muLayer,tempMuLayer)

        # In order for the slope extraction process to go faster whenever a subset of
        # polygons was selected an extent environment needed to be set.
        if bSubset:
            muLayerExtent = os.path.join(scratchWS, "muLayerExtent")
            if arcpy.Exists(muLayerExtent):
                arcpy.Delete_management(muLayerExtent)
            arcpy.CopyFeatures_management(tempMuLayer, muLayerExtent)
            arcpy.env.extent = muLayerExtent
            arcpy.env.mask = muLayerExtent

        else:
            arcpy.env.extent = tempMuLayer
            arcpy.env.mask = tempMuLayer

        arcpy.env.cellSize = cellSize
        arcpy.env.snapRaster = slopeLayerPath
        arcpy.SetProgressorLabel("Extracting Slope")
        env.workspace = os.path.dirname(slopeLayerPath)
        outSlope = scratchWS + os.sep + "outSlope"

        if arcpy.Exists(outSlope):
            arcpy.Delete_management(outSlope)

        # Add 0.5 to slope layer and convert to Integer
        if not descRaster.isInteger:
            outExtractByMask = Int(Plus(slopeLayerName,0.5))
            outExtractByMask.save(outSlope)

        # slope layer is already in Integer; extract by mask
        else:
            if bSubset:
                outExtractByMask = ExtractByMask(slopeLayerName,muLayerExtent)
            else:
                outExtractByMask = ExtractByMask(slopeLayerName,tempMuLayer)
            outExtractByMask.save(outSlope)

        arcpy.SetProgressorPosition()

        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+   Convert extracted slope to Array    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        """Convert Raster to points.  There is a 32-bit limitation to go straight to an array
        from a raster depending on its size.  The problem with RasterToNumPyArray is that
        NULL values are also part of the array and contributes to the size limiation.  NULL
        values are set to a user-defined value or the NoData value set in the properties.
        http://help.arcgis.com/EN/arcgisdesktop/10.0/help/index.html#//000v0000012z000000 """

        arcpy.SetProgressorLabel("Converting Extracted Slope to Points")

        rasterPoint = scratchWS + os.sep + "rasterPoint"
        if arcpy.Exists(rasterPoint):
            arcpy.Delete_management(rasterPoint)

        env.workspace = os.path.dirname(outSlope)

        try:
            arcpy.RasterToPoint_conversion(os.path.basename(outSlope),rasterPoint)
        except:
            errorMsg()
            raise ExitError, "\n\tThere is NO overlap between mulayer and Slope Raster Layer, EXITING!"

        totalPixels = int(arcpy.GetCount_management(rasterPoint).getOutput(0))

        # Make sure the input slope fully covers the muLayer area by comparing the area
        # of both.  If the difference in area is greater than 1% of the mulayer area then exit.
        muLayerArea = sum([row[0] for row in arcpy.da.SearchCursor(tempMuLayer, ("SHAPE@AREA"))])
        areaDiff = abs((totalPixels * (cellSize**2)) - muLayerArea)

        if areaDiff > (0.01 * muLayerArea):
            if areaDiff > muLayerArea:
                AddMsgAndPrint("\nWARNING: There is only " + str(int(round((muLayerArea/areaDiff)*100))) + "% overlap between your mapunit layer and slope layer",1)
            else:
                AddMsgAndPrint("\nWARNING: There is only " + str(int(round((areaDiff/muLayerArea)*100))) + "% overlap between your mapunit layer and slope layer",1)
            #raise ExitError, "The input slope raster layer does not fully cover the mapunit layer"

        arcpy.SetProgressorPosition()

        arcpy.SetProgressorLabel("Creating Array from slope value points")
        gridCodeField = FindField(rasterPoint,"grid_code")

        if not gridCodeField:
            raise ExitError, "\nRaster Point layer is missing necessary fields -- Cannot get 'Grid_Code' Information\n"

        slopeArray = arcpy.da.FeatureClassToNumPyArray(rasterPoint, [gridCodeField])
        arcpy.SetProgressorPosition()

        """No need to seperate NoData values b/c FeatureClassToNumpyArray will
        only grab non-NULL values"""
    ##    # represent all NoData values (-3.40282346639e+038) as -1
    ##    noDataValue = -1
    ##
    ##    # Convert the raster to a Numpy Array setting all NoData values to -1
    ##    slopeArray = arcpy.RasterToNumPyArray(outSlope,"","","",noDataValue)
    ##
    ##    # drop all of the NoData values
    ##    slopeArrayPos = slopeArray[slopeArray>0]


        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ capture basic statistics from the slope array and report +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        arcpy.SetProgressorLabel("Computing basic statistics")
        slopeMin = numpy.min(slopeArray[gridCodeField])
        slopeMax = numpy.max(slopeArray[gridCodeField])
        slopeMedian = numpy.median(slopeArray[gridCodeField])
        slopeMean = numpy.mean(slopeArray[gridCodeField])
        slopeStd = numpy.std(slopeArray[gridCodeField])


        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Get Slope Mode  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # Flatten the array from -- array([(4,), (6,), (8,), ..., (6,), (3,), (4,)] ----> array([4, 6, 8, ..., 6, 3, 4])
        slopeArrayInt = (slopeArray.astype(int)).flatten()  # convert the array from a float to an int array (truncating) and flatten to a 1D array
        slopeArrayInt_uniqueKeys = numpy.unique(slopeArrayInt) # get a list of unique keys in the array

        # ----------------- Option #1
        # Use arrays
        slopeArrayInt_bins = numpy.bincount(slopeArrayInt_uniqueKeys.searchsorted(slopeArrayInt))
        maxFrequency = numpy.max(slopeArrayInt_bins)
        maxFrequencyPos = numpy.where(slopeArrayInt_bins == maxFrequency)[0][0]
        slopeMode = slopeArrayInt_uniqueKeys[maxFrequencyPos]

        # ----------------- Option #2
        # Create a dictionary to capture the unique values and counts of each value
    ##    d = dict([(i,len(numpy.where(slopeArrayInt == i)[0])) for i in numpy.unique(slopeArrayInt_uniqueKeys)])  # i.e. {0: 7500, 1:17920, 2:28404}
    ##    maxFrequency2 = sorted([count for value,count in d.iteritems()],reverse=True)[0]  # 28404
    ##    slopeMode2 =  d.keys()[d.values().index(maxFrequency)]  # 2


        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Get Percentiles +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        percentile25 = numpy.percentile(slopeArray[gridCodeField],25)       # Low percentile for 50%
        percentile75 = numpy.percentile(slopeArray[gridCodeField],75)       # High percentile for 50%
        percentile5 = numpy.percentile(slopeArray[gridCodeField],5)         # Low percentile for 90%
        percentile95 = numpy.percentile(slopeArray[gridCodeField],95)       # High percentile for 90%

        AddMsgAndPrint("\nMapunit Slope Statistics:")
        AddMsgAndPrint("\tSlope Mean: " + str(round(slopeMean)) + " %",0)
        AddMsgAndPrint("\tSlope Mode: " + str(round(slopeMode)) + " %",0)
        AddMsgAndPrint("\tSlope Median: " + str(round(slopeMedian)) + " %",0)
        AddMsgAndPrint("\tSlope Standard Deviation: " + str(round(slopeStd)),0)
        AddMsgAndPrint("\tSlope Min: " + str(slopeMin) + " %",0)
        AddMsgAndPrint("\tSlope Max: " + str(slopeMax) + " %",0)
        arcpy.SetProgressorPosition()


        """ +-+-+-+-+-+-+-+-+-+-+-+-+ Calculate amount of area below the user lowSlope, above the user highSlope and in between +-+-+-+-+-+-+-+-+-+-+-+"""
        arcpy.SetProgressorLabel("Calculating amount of area < than " + str(lowSlope) + " and > than " + str(highSlope) + "% slope")
        AddMsgAndPrint("\nArea Summary",0)

        if lowSlope > 0:
            areaBelowLowSlope = int(round((float(len(numpy.where(slopeArray[gridCodeField] < lowSlope)[0])) / float(totalPixels)) * 100))
            msgBelowLow = str(areaBelowLowSlope) + "% of area is below " + str(lowSlope) + "% slope"
            AddMsgAndPrint("\t" + msgBelowLow ,0)

        areaAboveHighSlope = int(round((float(len(numpy.where(slopeArray[gridCodeField] > highSlope)[0])) / float(totalPixels)) * 100))
        msgAboveHigh = str(areaAboveHighSlope) + "% of area is above " + str(highSlope) + "% slope"
        AddMsgAndPrint("\t" + msgAboveHigh,0)

        # I don't know how to query an array using greater than AND less than so I took the difference
        areaInBetween = int(round(float(totalPixels - (len(numpy.where(slopeArray[gridCodeField] < lowSlope)[0]) + len(numpy.where(slopeArray[gridCodeField] > highSlope)[0]))) / float(totalPixels) * 100))
        msgInBetween = str(areaInBetween) + "% of area is between " + str(lowSlope) + " - " + str(highSlope) + "% slope"

        if areaInBetween >= 50:
            AddMsgAndPrint("\t" + msgInBetween,0)
        else:
            AddMsgAndPrint("\tWARNING: Only " + msgInBetween + "\n",1)


        """ +-+-+-+-+-+-+-+-+-+-+-+ Isolate polygons below the 5th Percentile and above the 95th Percentile - Anomolies -+-+-+-+-+-+-+-+-+-+-+"""
        # Run Zonal Statistics on the input layer and slope using ID to find
        # polygons below and above the 5th and 95th Percentile
        arcpy.SetProgressorLabel("Isolating any polygons with a mean slope < than " + str(lowSlope) + "% and > than " + str(highSlope) + "% slope")
        outZStable = outputFolder + os.sep + "outZStable"
        if arcpy.Exists(outZStable):
            arcpy.Delete_management(outZStable)

        outZonalStatistics = ZonalStatisticsAsTable(tempMuLayer,idField,outSlope,outZStable, "DATA", "MEAN")

        # Get a count of the number of polygons below the 5th Percentile
        wherePolysBelow5 = arcpy.AddFieldDelimiters(outZStable,"MEAN") + " <= " + str(percentile5)
        polysBelow5 = [row[0] for row in arcpy.da.SearchCursor(outZStable, (idField), where_clause = wherePolysBelow5)] # list of oids below the 5th

        # Get a count of the number of polygons above the 95th Percentile
        wherePolysAbove95 = arcpy.AddFieldDelimiters(outZStable,"MEAN") + " >= " + str(percentile95)
        polysAbove95 = [row[0] for row in arcpy.da.SearchCursor(outZStable, (idField), where_clause = wherePolysAbove95)] # remove brackets from list

        # Log if there are any polygons below the 5th Percentile and print SQL statement; Report at the bottom
        if len(polysBelow5):

            percentBelow5 = int(round((float(len(polysBelow5))/float(selectedPolys))*100)) # percent of polygons below the 5th percentile
            if percentBelow5 < 1:
                percentBelow5Msg = " (Less than 1%) polygons that have a slope mean below " + str(round(percentile5,1)) + " % slope (5th Percentile)"
            else:
                percentBelow5Msg =  " polygons that have a slope mean below " + str(round(percentile5,1)) + " % slope (5th Percentile)"

            if len(polysBelow5) == 1:
                msgBelow5 = "There is 1 out of " + str(splitThousands(selectedPolys)) + percentBelow5Msg
                #AddMsgAndPrint(msgBelow5,0)
            else:
                msgBelow5 = "There are " + str(splitThousands(len(polysBelow5))) + " (" + str(percentBelow5) + " %) out of " + str(splitThousands(selectedPolys)) + percentBelow5Msg
                #AddMsgAndPrint(msgBelow5,0)

        # Log if there are any polygons above the 95th Percentile and print SQL statement; Report at the bottom
        if len(polysAbove95):

            percentAbove95 = int(round((float(len(polysAbove95))/float(selectedPolys))*100)) # percent of polygons above the 95th percentile
            if percentAbove95 < 1:
                percentAbove95Msg = " (Less than 1%) polygons that have a slope mean above " + str(round(percentile95,1)) + " % slope (95th Percentile)"
            else:
                percentAbove95Msg =  " polygons that have a slope mean above " + str(round(percentile95,1)) + " % slope (95th Percentile)"

            if len(polysAbove95) == 1:
                msgAbove95 = "There is 1 out of " + str(splitThousands(selectedPolys)) + percentAbove95Msg
            else:
                msgAbove95 = "There are " + str(splitThousands(len(polysAbove95))) + " (" + str(percentAbove95) + "%) out of " + str(splitThousands(selectedPolys)) + percentAbove95Msg
        arcpy.SetProgressorPosition()


        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        """ ----------------------------------------------- Create Histogram Figure ----------------------------------------------------"""
        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Check if PDF exists +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        arcpy.SetProgressorLabel("Computing and plotting histogram to a PDF - Page1")
        # Supported formats: eps, pdf, pgf, png, ps, raw, rgba, svg, svgz.
        histogramFile = outputFolder + os.sep + projectName + " Histogram " + str(lowSlope) + "_" + str(highSlope) + ".pdf"

        # Check if the histogram file exists; if so, try deleting it first.
        if os.path.exists(histogramFile):
            try:
                os.remove(histogramFile)
                #AddMsgAndPrint("\nOutput PDF File: " + os.path.basename(histogramFile) + " will be overwritten",1)

            except:
                # histogramFile could not be deleted; try closing it; raise error if file cannot be closed
                if not closeFile(histogramFile):
                    raise ExitError,os.path.basename(histogramFile) + " Exists or is currently open and cannot be deleted."
                os.remove(histogramFile)
                #AddMsgAndPrint(os.path.basename(histogramFile) + " will be overwritten",1)

        pdf_pages = PdfPages(histogramFile)

        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Configure and Plot the histogram +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # create new figure; This one will hold the histogram
        fig = plot.figure(num=None,figsize=(11,8.5),dpi=200)

        # Only plot a small portion of data above the 90th percentile; round x-axis to the nearest 20th.
        # This will help remove extraneous anomolies from the graph
        #maxSlopeHistogram = ((highSlope * 2) - ((highSlope * 2)%20)) + 10
        percentile90 = numpy.percentile(slopeArray[gridCodeField],90)
        maxSlopeHistogram = ((percentile90 * 2) - ((percentile90 * 2)%20)) + 15

        while maxSlopeHistogram > slopeMax:
            maxSlopeHistogram -= 5

        # normed=True: the first element of the return tuple (n) will be the counts normalized to form a probability density, i.e., n/(len(x)`dbin), i.e.,
        # the integral of the histogram will sum to 1. If stacked is also True, the sum of the histograms is normalized to 1.
        stretchedArray = slopeArray[numpy.where(slopeArray[gridCodeField] <= maxSlopeHistogram)[0]]
        n, bins, patches = plot.hist(stretchedArray[gridCodeField],maxSlopeHistogram,normed=True,edgecolor='darkgray',facecolor='lightsalmon')


        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Text labels to Histogram  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # plot.text takes in data coordinates
        # Add Labels to X and Y axis
        plot.xlabel(rasterName,{'fontsize':'medium','verticalalignment':'top','horizontalalignment':'center'})
        plot.ylabel('% of Total Area',{'fontsize':'medium','verticalalignment':'center'})#,'horizontalalignment':'right'})

        if len(projectName) > 70:
            plot.suptitle(projectName,fontsize=15,fontweight='bold',verticalalignment='center')
        else:
            plot.suptitle(projectName,fontsize=18,fontweight='bold',verticalalignment='center')

        # Add upper right histogram statistics
        startingY = .86
        msg50Percent = "50% of area is between: " + str(round(percentile25)) + " - " + str(round(percentile75)) + " % slope"
        msg90Percent = "90% of area is between: " + str(round(percentile5)) + " - " + str(round(percentile95)) + " % slope"
        plot.text(0.58,startingY, msg50Percent,color='cornflowerblue',multialignment='right',fontsize='11',transform=fig.transFigure);startingY-=0.022
        plot.text(0.58,startingY, msg90Percent,color='blue',multialignment='right',fontsize='11',transform=fig.transFigure)
        yCoordFirstComment = startingY  # represent the height between the 2 comments; only used below in percentile code

        startingY-=0.04
        if lowSlope > 0:
            plot.text(0.66,startingY,msgBelowLow, multialignment='right', fontsize='11',transform=fig.transFigure);startingY-=0.022
        plot.text(0.66,startingY,msgAboveHigh, multialignment='right', fontsize='11',transform=fig.transFigure);startingY-=0.022

        # if area in between user slope range is below 50% then print in red otherwise print in green
        if areaInBetween > 49:
            plot.text(0.62,startingY,msgInBetween,color='limegreen', multialignment='right', fontsize='11',transform=fig.transFigure)
        else:
            plot.text(0.62,startingY,msgInBetween,color='red', multialignment='right', fontsize='11',transform=fig.transFigure)

        # Add Statistic box to upper right of page
        yCoordLastComment = startingY  # represent the height between the statistics box and previous comment; only used below in percentile code
        startingY-=0.16
        statistics = '$\mu = %.1f$\n$\mathrm{median} = %.1f$\n$M$o = %.1f\n$\sigma = %.1f$\n$\min = %.1f$\n$\max = %.1f$'%(round(slopeMean),slopeMedian,slopeMode,round(slopeStd),slopeMin,slopeMax)
        plot.text(0.78,startingY,statistics,fontsize=13, transform=fig.transFigure, bbox=dict(facecolor='wheat',edgecolor='darkgrey', boxstyle='round,pad=.5'))

        date = time.ctime().split()
        info = getpass.getuser() + '\n' + date[0] + " " + date[1] + " " + date[2] + ", " + date[4]
        plot.text(0.85,0.03,info,fontsize='9',transform=fig.transFigure)


        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Change the Y-axis Labels  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # Change the Y-Axis tick Labels from decimal to %
        # return locs, labels where locs is an array of tick locations and labels is an array of tick labels.
        locs, labels = plot.yticks() # locs will represent an array of tick locations i.e. array([ 0.  ,  0.01,  0.02,  0.03,  0.04,  0.05,  0.06,  0.07,  0.08,  0.09])

        # create a new label for the existing Y-axis tick marks by multiplying by 10 for percent
        yTickLabels = list()
        newLocs = list()

        for i in locs:
            yTickLabels.append(int(i * 100))
            newLocs.append(i)

        # if the difference between the max bin height and the highest Y tick is less than 0.5
        # than the graph may be too tight above and obstruct other graphics; If this is the case
        # add another tick (integer) to the Y ticks.
        xAxisIncrement = yTickLabels[-1] - yTickLabels[-2]  # represent the integer at which the xAxis is increasing by (0,5,10,15)

        if (locs[-1]*100) - (n.max()*100) <= float(xAxisIncrement) / 2:
            nextYtick = xAxisIncrement + yTickLabels[-1] # Add another xAxis Increment; Sometimes the Y axis legend will be increments of more than 1
            yTickLabels.append(nextYtick)
            newLocs.append(float(nextYtick)/100)

        # set the new locations and labels of the yticks
        plot.yticks(newLocs,yTickLabels)

        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Add Percentile vertical lines to Histogram  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # plot.axvline and plot.axhline take in coordinates ranging from 0 to 1 in both directions
        # Add vertical lines for the 50% and 90 area low and high; line properties are kwargs
        # Determine line height of vertical lines; line height must be normalized.  Line height of 1
        # will be at the top of vertical extent where as .5 will be the middle.
        # Determine half the distance from the top of the curve to the max value in graph and add that
        # to the top of the curve and divide by the max to get a percentage.
        #lineHeight95 = round((((plot.axis()[3] - n.max()) / 2) + n.max()) / plot.axis()[3],2)
        #lineHeight50 = round((((plot.axis()[3] - n.max()) / 2) + n.max()) / plot.axis()[3],2)

        percentile5Height = getBinHeight(percentile5)
        percentile25Height = getBinHeight(percentile25)
        percentile75Height = getBinHeight(percentile75)
        percentile95Height = getBinHeight(percentile95)

        if percentile25Height > -1 and percentile75Height > -1:

            if percentile25Height > percentile75Height:
                lineHeight50 = ((1 - percentile25Height)/3) + percentile25Height
            else:
                lineHeight50 = ((1 - percentile75Height)/3) + percentile75Height

            plot.axvline(x=percentile25, ymin=0, ymax=lineHeight50, color='cornflowerblue', linewidth=1.25)  # 50 % area low
            plot.axvline(x=percentile75, ymin=0, ymax=lineHeight50, color='cornflowerblue', linewidth=1.25)  # 50 % area High

        if percentile5Height > -1 and percentile95Height > -1:

            if percentile5Height > percentile95Height:
                lineHeight95 = ((1 - percentile5Height)/2) + percentile5Height
            else:
                lineHeight95 = ((1 - percentile95Height)/2) + percentile95Height

            # Convert the xCoord for the percentile95 into display coords in order to determine if
            # the second (far right) percentile line will interfere with any graphics from the upper right.
            # 0.78 represents the xCoord of the start of the statistics box
            # 0.62 represents the xCoord of the start of the last comment before the statistics box
            xDisplayCoord = percentile95 / plot.xticks()[0][-1:][0]
            second_lineHeight95 = lineHeight95

            # Check interference between the first comment and the "area in between" comment
            if xDisplayCoord > 0.58 and xDisplayCoord < 0.62:
                if lineHeight95 > yCoordFirstComment:
                    second_lineHeight95 = yCoordFirstComment

            # Check interference between the last line and the beginning of the statistics box
            elif xDisplayCoord > 0.62 and xDisplayCoord < 0.78:
                if lineHeight95 > yCoordLastComment:
                    second_lineHeight95 = yCoordLastComment

            # Check interference with the statistics box
            elif xDisplayCoord > 0.78:
                if lineHeight95 > startingY:
                    second_lineHeight95 = startingY

            plot.axvline(x=percentile5, ymin=0, ymax=lineHeight95, color='blue', linewidth=1.75)  # 95 % area low
            plot.axvline(x=percentile95, ymin=0, ymax=second_lineHeight95, color='blue', linewidth=1.75)  # 95 % area High

        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Add Mean and Median vertical lines to Histogram  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # Add vertical lines for the mean and median but first determine which has a higher bin height.
        # The one with the higher bin height will have the longer vertical line which will be drawn up to
        # the half way mark between the max bin height and the top of the graph (50%).  The shorter one will
        # be drawn 20% above its bin height.
        meanLineHeight = getBinHeight(slopeMean)
        medianLineHeight = getBinHeight(slopeMedian)

        if meanLineHeight > medianLineHeight:
            meanPercent = .50
            medianPercent = .20
        else:
            meanPercent = .20
            medianPercent = .50

        if meanLineHeight > -1:
            yCoordLine = meanLineHeight + ((1-meanLineHeight)*meanPercent) # Add meanPercent% to the yCoord value: 1 - (ycoord of Line Height (0.849206349206))
            yCoordText = yCoordLine * plot.yticks()[0][-1:][0]             # Covert the above coordinate from display coordinates to data source coordinates for the text.
            plot.axvline(x=slopeMean, ymin=0, ymax=yCoordLine,color='red',linewidth=1.2) # Y is in normalized coordinates #1.10
            plot.text(slopeMean,yCoordText,"$\mu$",fontsize=12,color='red') # Y is in axis coordinates #1.1

        if medianLineHeight > -1:
            yCoordLine = medianLineHeight + ((1-medianLineHeight)*medianPercent)
            yCoordText = yCoordLine * plot.yticks()[0][-1:][0]
            plot.axvline(x=slopeMedian, ymin=0, ymax=yCoordLine, color='seagreen',linewidth=1.4) #1.10
            plot.text(slopeMedian,yCoordText,r'$\mathrm{median}$',fontsize=12,color='seagreen') #1.12

        """ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+   Add Horizontal line for Mode to Histogram  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        # Add a horizontal dashed line starting at the slope mode and extending beyond the first existing
        # vertical line that has room to fit the annotation
        verticalLines = (percentile5,percentile25,percentile75,percentile95)

        xModeMax = ""
        i = 0
        for line in verticalLines:

            # text will be on the right side
            if slopeMode < line:

                if abs(line - slopeMode) > 3:
                    xModeMax = (slopeMode + ((line - slopeMode) * .60))/plot.xticks()[0][-1:][0]
                    plot.axhline(y=(n.max()), xmin=slopeMode/plot.xticks()[0][-1:][0], xmax=xModeMax, color='dimgray', linewidth=1.0,linestyle='--')
                    plot.annotate('$M$o',xy=(xModeMax*plot.xticks()[0][-1:][0],n.max()),xycoords='data',color='dimgray',fontsize=11)
                    scenario = 1
                    break

                else:
                    i+=1

            # text will be on the left side; Dividing by plot.ticks()[0][-1:][0] will convert the units to graph coordinates b
            elif (slopeMode > line) and abs(slopeMode - line) > 3:
                xModeMax = (line + ((slopeMode - line) * .60)) / plot.xticks()[0][-1:][0]
                plot.axhline(y=(n.max()), xmin=xModeMax, xmax=slopeMode/plot.xticks()[0][-1:][0], color='dimgray', linewidth=1.0,linestyle='--')
                plot.annotate('$M$o',xy=(xModeMax*plot.xticks()[0][-1:][0],n.max()),xycoords='data',color='dimgray',fontsize=11)
                scenario = 2
                break
            else:
                i+=1

        if xModeMax == "":
            xModeMax = (percentile95 + (percentile95 * .1)) / bins[-1:][0]
            plot.axhline(y=(n.max()), xmin=slopeMode, xmax=xModeMax, color='dimgray', linewidth=1.0,linestyle='--')
            plot.annotate('$M$o',xy=(xModeMax*bins[-1:][0],n.max()),xycoords='data',color='dimgray',fontsize=11)
            scenario = 3

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Add Low and High Slope X-Axis  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
##        # locsX = array([  0.,  10.,  20.,  30.,  40.,  50.,  60.])  -- X axis location
##        # labelsX = Text(10,0,u'10') --  a list of text properties related to the labels
##        locsX, labelsX = plot.xticks()
##
##        newXaxisLabels = list()
##        newLocsX = list()
##
##        # Check if the high slope exists as an X-axis label
##        for label in locsX:
##            # Text(10,0,u'10')
##            #xIsolated = str(label).split(',')[2][2:-2]
##            newXaxisLabels.append(int(label))
##
##        # Check if the low slope exists as an X-axis label; if not add it to the newXaxisLabels List
##        if not lowSlope in newXaxisLabels:
##            newXaxisLabels.append(lowSlope)
##        if not highSlope in newXaxisLabels:
##            newXaxisLabels.append(highSlope)
##
##        # in case lowSlope or highSlope was added to the list
##        newXaxisLabels.sort()
##
##        for label in newXaxisLabels:
##            newLocsX.append(float(label))
##
##        plot.xticks(newLocsX,newXaxisLabels)
##
##        plot.text(lowSlope,-0.03,str(lowSlope),color='red')

        # Add a 'Best-Fit' Line denoted by dashes
    ##    bestFitLine = mlab.normpdf(bins, slopeMean, slopeStd)
    ##    plot.plot(bins,bestFitLine,'r--')

        # add a line showing the expected distribution
    ##    y = P.normpdf( bins, mu, sigma2).cumsum()
    ##    y /= y[-1]
    ##    l = P.plot(bins, y, 'r--', linewidth=1.5)

        # plot histogram to file using the following properties
        # plot.savefig(histogramFile,dpi=200,facecolor='lightgrey', orientation='landscape', papertype='letter')
        pdf_pages.savefig(dpi=200,facecolor='lightgrey', orientation='landscape', papertype='letter')
        arcpy.SetProgressorPosition()


        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        """ ---------------------------------------------- Create 2nd Page Summary -----------------------------------------------------"""
        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        arcpy.SetProgressorLabel("Writing summary report to PDF - Page2")
        plot.figure(figsize=(11,8.5), dpi=200)#, facecolor='lightgrey', edgecolor='lightgrey')

        # ------------------------------ Remove the X and Y axis labels, minor and major tickmarks
        plot.gca().xaxis.set_major_locator(plot.NullLocator())
        plot.gca().yaxis.set_major_locator(plot.NullLocator())


        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Layer Information +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        if len(projectName) > 70:
            plot.suptitle(projectName,fontsize=15,fontweight='bold',verticalalignment='center')
        else:
            plot.suptitle(projectName,fontsize=18,fontweight='bold',verticalalignment='center')

        if len(slopeLayerPath) > 95 or len(muLayerPath) > 95:
            font=9
        else:
            font=10

        yStart = 0.96 # This represents the y-coord in display coordinates
        #plot.text(0.01,0.96,"Layer Information: " + projectName,color='k', multialignment='right', fontsize='11',fontweight='bold')
        plot.text(0.01,yStart,"Layer Information: ",color='k', multialignment='right', fontsize='11',fontweight='bold'); yStart-=0.03
        plot.text(0.04,yStart,"Mapunit Layer Workspace: " + os.path.dirname(muLayerPath),color='k', multialignment='right', fontsize=font); yStart-=0.03
        plot.text(0.09,yStart,assessedPolys + " --- Total Acres: " + str(splitThousands(totalAcres)),color='k', multialignment='right', fontsize=font); yStart-=0.03
        plot.text(0.04,yStart,"Slope Layer: " + slopeLayerPath,color='k', multialignment='right', fontsize=font); yStart-=0.03
        plot.text(0.09,yStart,"Resolution: " + str(cellSize) + " " + units ,color='k', multialignment='right', fontsize=font);


        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add User-Input Low Slope and High Slope +-++-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        yStart-=0.05
        plot.text(0.01,yStart,"Mapunit Slope Range Values:",color='k', multialignment='right', fontsize='11',fontweight='bold'); yStart-=0.03
        plot.text(0.05,yStart,"Low Slope: " + str(lowSlope) + " %",color='k', multialignment='right', fontsize='11'); yStart-=0.03
        plot.text(0.05,yStart,"High Slope: " + str(highSlope) + " %",color='k', multialignment='right', fontsize='11')


        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Basic Statistics +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        yStart-=0.05 # around 0.68
        plot.text(0.01,yStart,"Mapunit Slope Statistics:",color='k', multialignment='right', fontsize='11',fontweight='bold'); yStart-=0.03
        plot.text(0.05,yStart,"Mean: " + str(round(slopeMean)) + " %",color='k', multialignment='right', fontsize='11'); yStart-=0.03
        plot.text(0.05,yStart,"Median: " + str(round(slopeMedian)) + " %",color='k', multialignment='right', fontsize='11'); yStart-=0.03
        plot.text(0.05,yStart,"Mode: " + str(round(slopeMode)) + " %",color='k', multialignment='right', fontsize='11'); yStart-=0.03
        plot.text(0.05,yStart,"Std. Deviation: " + str(round(slopeStd)),color='k', multialignment='right', fontsize='11')


        """+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Messages about % of area below and above user Low and High Slope +-+-+-+-+-+-+-+-+-+"""
        yStart-=0.05
        if lowSlope > 0:
            plot.text(0.05,yStart,msgBelowLow,color='k', multialignment='right', fontsize='11');yStart-=0.03

        plot.text(0.05,yStart,msgAboveHigh,color='k', multialignment='right', fontsize='11');yStart-=0.03

        if areaInBetween >= 50:
            plot.text(0.05,yStart,msgInBetween,color='limegreen', multialignment='right', fontsize='11')
        else:
            plot.text(0.05,yStart,"WARNING: ",color='red', multialignment='right', fontsize='11')
            plot.text(0.16,yStart,"Only " + msgInBetween,color='red', multialignment='right', fontsize='11')


        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Add Area Summary verbiage +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        yStart-=0.05
        percentMsgList = [(25,75,50),(20,80,60),(15,85,70),(10,90,80),(5,95,90)]
        plot.text(0.01,yStart,"Area Summary: ",color='k', multialignment='right', fontsize='11',fontweight='bold');yStart-=0.03
        #AddMsgAndPrint("\n")
        for low,high,percent in percentMsgList:
            percentileMsg = str(percent) + "th percentile = " + str(round(numpy.percentile(slopeArray[gridCodeField],percent))) + "% slope"
            msg = str(percent) + "% of area is between " + str(round(numpy.percentile(slopeArray[gridCodeField],low))) + "% and " + str(round(numpy.percentile(slopeArray[gridCodeField],high))) + "% slope -- " + percentileMsg
            AddMsgAndPrint("\t" + msg)
            plot.text(0.05,yStart,msg,color='k', multialignment='right', fontsize='11')

            if percent < 90:
                yStart-=0.03


        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Message about anomaly polygons +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        AddMsgAndPrint("\n")
        if len(polysBelow5):
            AddMsgAndPrint(msgBelow5,1)
        if len(polysAbove95):
            AddMsgAndPrint(msgAbove95,1)

        yStart-=0.05
        polysBelow5Exists = False
        polysAbove95Exists = False
        if len(polysBelow5):
            plot.text(0.01,yStart,msgBelow5,color='k', multialignment='right', fontsize='10');yStart-=0.03
            polysBelow5Exists = True

        if len(polysAbove95):
            plot.text(0.01,yStart,msgAbove95,color='k', multialignment='right', fontsize='10')
            polysAbove95Exists = True


        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        """ ----------------------- Create Shapefiles of polygons below and above threshold percentiles --------------------------------"""
        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        if len(polysBelow5) or len(polysAbove95):
            arcpy.SetProgressorLabel("Creating Shapefile of anamoly polygons")
            shapePath, symbologyLyr = createShapefile(polysBelow5,polysAbove95,outZStable)

            if shapePath:
                try:
                    # If ArcMap is open try adding the shapefile layer
                    mxd = arcpy.mapping.MapDocument("CURRENT")
                    newLayer = os.path.basename(shapePath)[:-4] + ".lyr" # Name of in-memory layer file to create
                    saveLayerFile = shapePath[:-4] + ".lyr"              # Path to disk saved .lyr file (needed in order to add into ArcMap)

                    if arcpy.Exists(saveLayerFile):
                        arcpy.Delete_management(saveLayerFile)

                    arcpy.MakeFeatureLayer_management(shapePath,newLayer)
                    arcpy.SaveToLayerFile_management(newLayer,saveLayerFile)
                    arcpy.ApplySymbologyFromLayer_management(saveLayerFile,symbologyLyr)

                    # Remove the newLayer from ArcMap if it exists; Go through all Dataframes to be sure
                    for df in arcpy.mapping.ListDataFrames(mxd):
                        for lyr in arcpy.mapping.ListLayers(mxd, "", df):
                            if lyr.name == newLayer:
                                arcpy.mapping.RemoveLayer(df, lyr)

                    df = arcpy.mapping.ListDataFrames(mxd)[0]
                    addLayer = arcpy.mapping.Layer(saveLayerFile)
                    arcpy.mapping.AddLayer(df, addLayer, "TOP")

                except:
                    pass

                yStart -= 0.03
                outputMsg = "Output File: " + shapePath
                if len(outputMsg) > 95:
                    font=9
                else:
                    font=10
                plot.text(0.05,yStart,outputMsg,color='k', multialignment='right', fontsize=font)

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Elevation Source Information if available +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-"""
        elevSource = getElevationSource()
        if elevSource:
            yStart-=0.05
            plot.text(0.01,yStart,"Original Elevation Source information:",color='k', multialignment='right', fontsize='11',fontweight='bold'); yStart-=0.03

            for source in elevSource:
                plot.text(0.05,yStart,source,color='k',multialignment='right',fontsize='11')
                yStart-=0.03

        """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Add Username and Date +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
        plot.text(0.305,0.014,info,fontsize='9',transform=fig.transFigure)

        pdf_pages.savefig(dpi=200,facecolor='lightgrey', orientation='landscape', papertype='letter')
        pdf_pages.close()
        arcpy.SetProgressorPosition()

        """ ------------------  Clean up Time ------------------- """
        AddMsgAndPrint("\n\n")
        if arcpy.Exists(outSlope):
            arcpy.Delete_management(outSlope)

        if arcpy.Exists(tempMuLayer):
            arcpy.Delete_management(tempMuLayer)

        if bSubset and arcpy.Exists(muLayerExtent):
            arcpy.Delete_management(muLayerExtent)

        if arcpy.Exists(rasterPoint):
            arcpy.Delete_management(rasterPoint)

        if arcpy.Exists(outZStable):
            arcpy.Delete_management(outZStable)

        arcpy.Compact_management(scratchWS)
        os.startfile(histogramFile)

        del plot
        del muLayer,slopeLayer,lowSlope,highSlope,muLayerName, muLayerPath, outputFolder, projectName, rasterName, totalPolys
        del outSlope, outExtractByMask, rasterPoint, totalPixels, gridCodeField, slopeArray, slopeMin, slopeMax,
        del slopeMedian, slopeMean, slopeArrayInt, slopeArrayInt_uniqueKeys, slopeArrayInt_bins, maxFrequency, maxFrequencyPos, slopeMode
        del slopeStd, percentile5, percentile25, percentile75, percentile95, outZStable, outZonalStatistics, wherePolysBelow5, polysBelow5
        del wherePolysAbove95, msg50Percent, msg90Percent, fig, startingY, date, info, locs, labels, yTickLabels
        del percentile5Height, percentile25Height, percentile75Height, percentile95Height, meanLineHeight, medianLineHeight, meanPercent, medianPercent, yCoordLine, yCoordText
        del verticalLines, xModeMax, i, histogramFile, pdf_pages, yStart, percentMsgList, polysBelow5Exists, polysAbove95Exists, elevSource

    except:
        errorMsg()