#-------------------------------------------------------------------------------
# Name:        Create Extent Layer from NASIS Project
# Purpose:
#
# Author:      adolfo.diaz
#
# Created:     19/03/2014
# Copyright:   (c) adolfo.diaz 2014
# Licence:     <your licence>

##return geometry as WKT
##SELECT mukey, mupolygongeo.STAsText() AS wktgeom
##FROM mupolygon
##WHERE mukey = 2525746

##This will return the polygon count
## SELECT COUNT(*)
##FROM mupolygon
##WHERE mukey = 2525746

##Vertice count. Faster than using the python tool with gSSURGO!
##SELECT mukey, SUM(mupolygongeo.STNumPoints()) AS vertex_count
##FROM mupolygon
##WHERE mukey = 2525746
##GROUP BY mukey

##SELECT mukey, mupolygongeo.STAsText() FROM mupolygon WHERE mukey IN (mukeylist)

##SELECT mukey, mupolygongeo.STAsText() FROM mupolygon WHERE mukey IN (2525720, 2525769)


## ==============================================================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:

        #print(msg)
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

## ==============================================================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        AddMsgAndPrint(theMsg, 2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

## ==============================================================================================================================
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

                # remove any NULL items from above lists.
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

## ==============================================================================================================================
def GetWorkspace(ssurgoInput):
# Return the workspace of the input
    """ Maybe get rid of this or add it to the main body """

    try:
        desc = arcpy.Describe(ssurgoInput)
        thePath = os.path.dirname(desc.CatalogPath)

        desc = arcpy.Describe(thePath)

        # if path to ssurgoInput is a FD grab the GDB path
        if desc.dataType.upper() == "FEATUREDATASET":
            thePath = os.path.dirname(thePath)

        env.workspace = thePath
        return thePath

    except:
        errorMsg()

## ==============================================================================================================================
def tic():
    """ Returns the current time """

    return time.time()

## ==============================================================================================================================
def toc(_start_time):
    """ Returns the total time by subtracting the start time - finish time"""

    try:

        t_sec = round(time.time() - _start_time)
        (t_min, t_sec) = divmod(t_sec,60)
        (t_hour,t_min) = divmod(t_min,60)

        if t_hour:
            return ('{} hour(s): {} minute(s): {} second(s)'.format(int(t_hour),int(t_min),int(t_sec)))
        elif t_min:
            return ('{} minute(s): {} second(s)'.format(int(t_min),int(t_sec)))
        else:
            return ('{} second(s)'.format(int(t_sec)))

    except:
        errorMsg()

## ==============================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ==============================================================================================================================
def getNasisMukeys(prjMapunit_URL, theProject):
    # Create a list of NASIS MUKEY values (keys) & project names (values)
    # Sometimes having problem getting first mapunit (ex. Adda in IN071)

    try:
        nasisMUKEYs = []  # List of MUKEYs pertaining to the project and parsed from the NASIS report

        # Strictly for formatting.
        if len(selectedProjects) > 1:
            AddMsgAndPrint("\n" + 100 * '*',0)
            AddMsgAndPrint("Retrieving MUKEYs for '" + theProject + "' from NASIS", 0)
        else:
            AddMsgAndPrint("\nRetrieving MUKEYs for '" + theProject + "' from NASIS", 0)

        # replace spaces in the search string with '%20' which is the hexadecimal for a space
        prjMapunit_URL = prjMapunit_URL + '&p1='  + theProject.replace(" ","%20") # + "*"

        # Open a network object using the URL with the search string already concatenated
        theReport = urllib.urlopen(prjMapunit_URL)

        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # removes whitespace characters

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "END":  # written as part of the report; end of lines
                    break

                # Found a valid project record i.e. -- SDJR - MLRA 103 - Kingston silty clay loam, 1 to 3 percent slopes|400036
                else:
                    theRec = theValue.split("|")
                    theMUKEY = theRec[1]

                    # Add MUKEY to the nasisMUKEY list if it doesn't already exist
                    if not theMUKEY in nasisMUKEYs:
                        nasisMUKEYs.append(theMUKEY)

            else:
                if theValue.startswith('<div id="ReportData">BEGIN'):
                    bValidRecord = True

        # if no project record was found from NASIS return an empty list otherwise notify user; Cou
        if len(nasisMUKEYs) == 0:
            AddMsgAndPrint("\tNo matching projects found in NASIS", 2)
            return False
        else:
            AddMsgAndPrint(" \tIdentified " + splitThousands(len(nasisMUKEYs)) + " mapunits associated with this NASIS project", 0)

        """ ------------------Insert code to check missing MUKEYs from SDA ----------------------------------------"""
##        #All MUKEYS are missing from ssurgoInput Layer; Warn user and return False
##        if len(mukeyMissing) == len(nasisMUKEYs):
##            AddMsgAndPrint(" \tAll MUKEYs from this project are missing from your SSURGO MUPOLYGON layer",2)
##
##        # More than one MUKEY is missing from ssurgoInput Layer; Simply warn the user
##        if len(mukeyMissing) > 0:
##            AddMsgAndPrint( "\n\t The following " + str(len(mukeyMissing)) + " MUKEYS are missing from the SSURGO MUPOLYGON layer:", 1)
##            AddMsgAndPrint("\t\t" + str(mukeyMissing),1)

        del prjMapunit_URL, theReport, bValidRecord
        return nasisMUKEYs

    except IOError:
        AddMsgAndPrint("IOError, unable to connect to NASIS server", 2)
        return False

    except:
        errorMsg()
        return False

## ==============================================================================================================================
def createOutputFC():
    # Input theAOI is the original first parameter (usually CLU feature layer)
    #
    # Given the path for the new output featureclass, create it as polygon and add required fields
    # Later it will be populated using a cursor.

    try:

        epsgWGS84 = 4326 # EPSG code for: GCS-WGS-1984
        outputCS = arcpy.SpatialReference(epsgWGS84)

        nasisProjectFC = arcpy.CreateScratchName("nasisProject", workspace=arcpy.env.scratchGDB,data_type="FeatureClass")

        # Create empty polygon featureclass with coordinate system that matches AOI.
        arcpy.CreateFeatureclass_management(env.scratchGDB, os.path.basename(nasisProjectFC), "POLYGON", "", "DISABLED", "DISABLED", outputCS)
        arcpy.AddField_management(nasisProjectFC,"mukey", "TEXT", "", "", "30")   # for outputShp

        if not arcpy.Exists(nasisProjectFC):
            AddMsgAndPrint("\tFailed to create " + nasisProjectFC + " TEMP Layer",2)
            return False

        return nasisProjectFC

    except:
        errorMsg()
        return False


## ==============================================================================================================================
def geometryRequestByMUKEY(nasisMUKEYs,sortedByCount=True):


    try:

        # Only send 5 MUKEYs at a time to SDA
        if not sortedByCount:
           nasisMUKEYs = [nasisMUKEYs[x:x+5] for x in xrange(0, len(nasisMUKEYs), 5)]

        AddMsgAndPrint("\tRequesting Geometry Info from SDA")
        sdaURL = r"https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

        numOfRequests = len(nasisMUKEYs)
        currentRequest = 0

        for mukeyList in nasisMUKEYs:

            AddMsgAndPrint("\tMUKEYs Requested: " + str(mukeyList))

            currentRequest+=1
            startTime = tic()
            mukeys = str(mukeyList).replace("[","").replace("]","").replace("'","")

            sdaQuery = """SELECT mukey, mupolygongeo.STAsText()
                          FROM mupolygon
                          WHERE mukey IN (""" + mukeys + """)"""

            dRequest = dict()
            dRequest["format"] = "JSON"
            dRequest["query"] = sdaQuery

            # Create SDM connection to service using HTTP
            jData = json.dumps(dRequest)

            try:
                # Send request to SDA Tabular service
                req = urllib2.Request(sdaURL, jData)
                resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
                responseStatus = resp.getcode()
                responseMsg = resp.msg
                jsonString = resp.read()
                resp.close()

                data = json.loads(jsonString) # dictionary containing 1 key with a list of lists

            except:
                AddMsgAndPrint("\n\tFailed ----------------- ")
                AddMsgAndPrint(str(mukeys))
                continue
                #errorMsg()

            if not "Table" in data:
               AddMsgAndPrint("\tNo data returned for MUKEYs: " + str(mukeyList),2)
               continue

            # Convert the dictionary to a list of lists. Service returns everything as string.
            # 1 record will contain 2 items: MUKEY and list of coordinates that make up that polygon
            # i.e. [u'357347', u'POLYGON ((-96.57 45.68, -96.57 45.68, -96.57 45.68, -96.57 45.68))']
            dataList = data["Table"]
            del mukeys,sdaQuery,dRequest,jData,jsonString, resp, req

            AddMsgAndPrint("\n\tSDA Geometry request: " + toc(startTime) + " Reqest: " + str(currentRequest) + " of " + str(numOfRequests))

            # Only two fields are used initially, the geometry and MUKEY
            outputFields = ["MUKEY","SHAPE@WKT"]

            startTime = tic()
            with arcpy.da.InsertCursor(nasisProjectFC, outputFields) as cur:

                for rec in dataList:
                    #PrintMsg("\trec: " + str(rec), 1)
                    mukey = rec[0]
                    wktPoly = rec[1]

                    if mukey is None:
                        AddMsgAndPrint("\nFound nodata polygon in soils layer", 1)
                        continue

                    if not mukey is None and not mukey == '':
                        cur.insertRow((mukey,wktPoly))

            AddMsgAndPrint("\tInsert Geometry Time: " + toc(startTime))

##                        # immediately create polygon from WKT
##                        newPolygon = arcpy.FromWKT(wktPoly, inputCS)
##                        rec = [newPolygon, mukey]
##                        cur.insertRow(rec)
##                        polyCnt += 1
##                        #arcpy.SetProgressorLabel("Imported polygon " +  str(polyCnt))
##
##                        #if showStatus:
##                        arcpy.SetProgressorPosition()

    except:
        errorMsg()
        return False

## ==============================================================================================================================
def groupMUKEYsByVertexCount(listOfMUKEYs,feature="VERTICE"):
    """ This function takes in a list of MUKEYS and groups them based on maximum POLYGON or VERTICE thresholds so that SDA
        geometry requests are efficient and successful.  POLYGON Threshold is set to 9,999 records which is the default with
        SDA (I haven't seen this to be a limitation).  VERTICE Threshold is set to 811,000
        (determined by MUKEY: 2903473 - OH161 - FY19)

        Polygon and Vertice counts are collected from SDA by MUKEY.  The MUKEYs are then sorted ascendingly by vertice or
        polgyon county (user-determined) and then grouped into lists that don't exceed the feature threshold.  These sub-lists
        can then be sent to SDA for to return geometry in JSON format.  If vertice counts are not asseessed then groups of mukeys
        that exceed the vertice threshold will fail.  Individual MUKEYs that exceed the vertice threshold will be broken into
        groups of associated polygons whose vertice count is below the threshold.

        A dictionary containing lists of either MUKEYs or MUPOLYGONKEYs are returned.  Keys beginning with MUKEY* will have a list
        of MUKEYs as their item.  Keys beginning with MUPOLYGONKEY* will have a list of mupolygonkeys as their item.
        i.e. {'MUKEY0': ['408342'], 'MUPOLYGONKEY0': ['228419267','228421430','217139720','228419274','217125974','217139721']}"""

    try:
        if not len(listOfMUKEYs):
           AddMsgAndPrint("\tEmpty list of MUKEYs was passed",2)
           return False

        if feature == "POLYGON":
           countThreshold = 9999    # Max Polygon records per subList
           countFeatureID = 1
        elif feature == "VERTICE":
           countThreshold = 811000  # Max number Vertices per subList
           countFeatureID = 2
        else:
           AddMsgAndPrint("\n\t parseMUKEYsByCount ERROR -- Invalid feature type passed",2)
           return False

        # Dictionary containng list of MUKEY subset lists that will be used to
        # request SDA Geometry.  KEY = MUKEY or MUPOLYGONKEY
        mukeySubsetsDict = dict()

        # list of MUKEYs that exceed vertice threshold.  This list needs to be
        # further evaluated by polygon.
        mukeysExceedThreshold = list()

        totalPolys = 0
        totalVertices = 0
        startTime = tic()

        mukey = str(listOfMUKEYs).replace("[","").replace("]","").replace("'","")

        """ ---------------------------------------------- Get Polygon and Vertice Counts from SDA -------------------------"""
        getPolygonCountQuery = """SELECT COUNT(*) FROM mupolygon WHERE mukey = """ + mukey

        getVerticeCountQuery = """SELECT mukey, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                               FROM mupolygon
                               WHERE mukey = """ + mukey + """GROUP BY mukey"""

        getPolyAndVerticeCountQuery = """SELECT mukey, COUNT(*) AS polycount, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                                      FROM mupolygon WHERE mukey IN (""" + mukey + """)
                                      GROUP BY mukey
                                      ORDER BY vertex_count ASC"""

        dRequest = dict()
        dRequest["format"] = "JSON"
        dRequest["query"] = getPolyAndVerticeCountQuery

        # Create SDM connection to service using HTTP
        jData = json.dumps(dRequest)

        try:
            # Send request to SDA Tabular service
            req = urllib2.Request(sdaURL, jData)
            resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
            responseStatus = resp.getcode()
            responseMsg = resp.msg
            jsonString = resp.read()
            resp.close()

            data = json.loads(jsonString) # dictionary containing 1 key with a list of lists

        except:
            errorMsg()
            return False

        if not "Table" in data:
           AddMsgAndPrint("\tNo data returned for MUKEY: " + str(mukeyList),2)

        del getPolyAndVerticeCountQuery,dRequest,jData,req,resp,jsonString

        # Tally up the counts
        mukeyPolyCount = sum([int(item[1]) for item in data['Table']])
        mukeyVerticeCount = sum([int(item[2]) for item in data['Table']])
        totalPolys += mukeyPolyCount
        totalVertices += mukeyVerticeCount

        # MUKEY that have no polygons associated
        mukeysReturned = [item[0] for item in data['Table']]
        mukeyNoPolygon =  list(set(mukeysReturned) - set(listOfMUKEYs))

        """ -------------------------------------- Sort MUKEYs by Polygon or Vertice Counts -------------------------------"""
        # sort the mukeyDict based on polygon or vertice count; converts the dictionary into a tuple
        # by default since a dictionary cannot be reordered.
        tempMUKEYList = list()
        tempFeatureCount = 0
        validMukeys = 0
        iCount = 0

        for rec in data['Table']:
            mukey = str(rec[0])
            featureCount = int(rec[countFeatureID])

            # individual feature exceeds threshold.  If vertice count exceeds 811,000 it
            # needs to be handled differently.
            if featureCount > countThreshold and countFeatureID == 2:
               mukeysExceedThreshold.append(mukey)

            # total feature count is still under threshold; Add MUKEY to the tempMUKEYList
            elif not (featureCount + tempFeatureCount) > countThreshold:
               tempMUKEYList.append(mukey)
               validMukeys+=1
               tempFeatureCount+=featureCount

            # feature count will exceed threshold; Do not add
            # anymore MUKEYs to the list.  Add current list of
            # MUKEYs to final list and clear the tempList
            else:
                mukeySubsetsDict['MUKEY' + str(iCount)] = tempMUKEYList

                tempMUKEYList = list()
                tempMUKEYList.append(mukey)
                validMukeys+=1
                iCount+=1
                tempFeatureCount = featureCount

           # this is the last record; add it
            if mukey == data['Table'][-1][0] and len(tempMUKEYList):
                mukeySubsetsDict['MUKEY' + str(iCount)] = tempMUKEYList
                iCount+=1

            del mukey,featureCount

        # There are mukeys that exceed vertice threshold.  Evaluate vertice count
        # by polygon instead of mukey.
        if len(mukeysExceedThreshold):
            AddMsgAndPrint("\tThere are " + str(len(mukeysExceedThreshold)) + " MUKEYs that exceed the vertice limit.  Retrieving subset of polygons")
            mupolygonkeyGroupList = groupMupolygonkeyByVertexCount(mukeysExceedThreshold)

            if len(mupolygonkeyGroupList):
                iCount = 0
                for polykeyList in mupolygonkeyGroupList:
                    mukeySubsetsDict['MUPOLYGONKEY' + str(iCount)] = polykeyList
                    iCount+=1

        # Make sure all MUKEYs were accounted; Number of valid MUKEYs processed and MUKEYs with
        # no polygons and excessive vertices should be the same as the # of MUKEYs submitted
        if not len(listOfMUKEYs) == validMukeys + len(mukeyNoPolygon) + len(mukeysExceedThreshold):
            AddMsgAndPrint("\tThere is a discrepancy with the MUKEYs bein grouped by vertice count:",2)
            AddMsgAndPrint("\t\tOriginal Number of MUKEYs: " + str(len(listOfMUKEYs)),2)
            AddMsgAndPrint("\t\tProcessed Number of MUKEYs: " + str(validMukeys),2)
            AddMsgAndPrint("\t\tNumber of MUKEYs with no polygons: " + str(len(mukeyNoPolygon)),2)
            AddMsgAndPrint("\t\tNumber of MUKEYs with excessive vertices: " + str(len(mukeysExceedThreshold)),2)

        if len(mukeyNoPolygon):
            AddMsgAndPrint("\tThe following " + str(len(mukeyNoPolygon)) + " MUKEYs have no geometry data available:",1)
            AddMsgAndPrint("\t\t" + str(mukeyNoPolygon),1)

        if not len(mukeySubsetsDict):
            AddMsgAndPrint("\t\tGrouping MUKEYS by " + feature + " Failed.  Empty Final List",2)
            return False

        AddMsgAndPrint("\tTotal " + feature + " Count: " + (splitThousands(totalPolys) if countFeatureID == 0 else splitThousands(totalVertices)))

        return mukeySubsetsDict

    except:
        errorMsg()
        return False

## ==============================================================================================================================
def groupMupolygonkeyByVertexCount(listOfMUKEYs):
    """ This function takes in a list of MUKEYS and groups the associated polygons based on the maximum VERTICE threshold of
        811,000 vertices so that SDA geometry requests are efficient and successful.  VERTICE Threshold is set to 811,000
        (determined by MUKEY: 2903473 - OH161 - FY19)

        This function can be called independently OR by the groupMUKEYsByVertexCount function. MUKEY, MUPOLYGONKEY and Vertice
        count are collected from SDA and stored in a dictionary.  The MUPOLYGONKEYs are then sorted ascendingly by vertice count
        and then grouped into lists that don't exceed the vertice threshold.  MUPOLYGONKEYs are the unique polygon identifier
        assigned by SQL Server.  It is the equivalent of OID or FID.

        A list of MUPOLYGONKEY lists is returned.  The user will be warned of individual polygons that exceed the vertice
        threshold.  Those MUPOLYGONKEYs will not be included in the returned list."""

    try:
        if not len(listOfMUKEYs):
           AddMsgAndPrint("\tEmpty list of MUKEYs was passed",2)
           return False

        # Vertice Limit before there is a SDA JSON limitation
        countThreshold = 811000

        # list containing subset lists of polygons
        polygonSubsetList = list()

        mukey = str(listOfMUKEYs).replace("[","").replace("]","").replace("'","")

        getVerticeCountByMuPolygonKey = """DROP TABLE IF EXISTS #vertexCount;

        -- Set number of partitions
        --declare @numberOfPartitions INT ; -- use for managment studio
        --~DeclareInt(@numberOfPartitions)~;  --use for python and SDA
        --SELECT @numberOfPartitions = 5

        -- Create variable for current partition number

        --declare @partitionNumber INT ; -- use for managment studio
        --~DeclareInt(@partitionNumber)~;  --use for python and SDA

        CREATE TABLE #vertexCount
        (mukey CHAR(30), vertex_count int, polykey int);

        INSERT INTO #vertexCount (mukey, vertex_count, polykey)
        SELECT mukey, SUM(mupolygongeo.STNumPoints()) AS vertex_count, MuPolygonKey
        FROM mupolygon
        WHERE mukey IN (""" + mukey + """)
        GROUP BY mukey, MuPolygonKey

        SELECT  mukey, vertex_count, polykey FROM #vertexCount
        ORDER BY vertex_count ASC, mukey"""

        dRequest = dict()
        dRequest["format"] = "JSON"
        dRequest["query"] = getVerticeCountByMuPolygonKey

        # Create SDM connection to service using HTTP
        jData = json.dumps(dRequest)

        try:
            # Send request to SDA Tabular service
            req = urllib2.Request(sdaURL, jData)
            resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
            responseStatus = resp.getcode()
            responseMsg = resp.msg
            jsonString = resp.read()
            resp.close()

            data = json.loads(jsonString) # dictionary containing 1 key with a list of lists

        except:
            errorMsg()
            return False

        if not "Table" in data:
           AddMsgAndPrint("\tNo polygon information returned for MUKEY: " + str(mukeyList),2)
           return False

        totalPolyKeys = len(data['Table'])
        exceedVerticeLimit = list()
        tempPolyList = list()
        tempVertexCount = 0
        validPolyKeys = 0

        """ -------------------------------------- Sort Polygons by Vertice Counts -------------------------------"""
        for rec in data['Table']:
            muKey = str(rec[0])
            vertexCount = int(rec[1])
            polyKey = str(rec[2])

            # This should only be 1 polygon in all of SSURGO but you never know.
            if vertexCount > countThreshold:
                exceedVerticeLimit.append(polyKey)

           # total vertice count is still under threshold; Add polykey to the tempPolyList
            elif not (vertexCount + tempVertexCount) > countThreshold:
                tempPolyList.append(polyKey)
                validPolyKeys+=1
                tempVertexCount+=vertexCount

           # vertice count will exceed threshold; Do not add
           # anymore polyKeys to the list.  Add current list of
           # polyKeys to final list and clear the tempList
            else:
                polygonSubsetList.append(tempPolyList)

                tempPolyList = list()
                tempPolyList.append(polyKey)
                validPolyKeys+=1
                tempVertexCount = vertexCount

           # this is the last record; add tempPolyList to final list
           # if tempPolyList contains polykeys.
            if polyKey == data['Table'][-1][2] and len(tempPolyList):
                polygonSubsetList.append(tempPolyList)

            del muKey,vertexCount,polyKey

        # There are polygons that individually exceed the 811,000 limit; Nothing we can do but skip it.
        if len(exceedVerticeLimit):
            AddMsgAndPrint("\t\tVertice limitation is exceeded by the following " + str(len(exceedVerticeLimit)) + " polygon(s):",1)
            for polykey in exceedVerticeLimit:
                mukey = str([item[0] for item in data['Table'] if item[2] == polykey][0]).replace(' ','')
                vertexCount = splitThousands([item[1] for item in data['Table'] if item[2] == polykey][0])
                AddMsgAndPrint("\t\t\tMUKEY: " + mukey + " -- MUPOLYGONKEY: " + str(polykey) + " -- Vertice Count: " + vertexCount,1)
                del mukey,vertexCount

        # Make sure all polykeys were accounted; Number of valid polykeys processed and
        # polykeys with exceeded vertices should be the same as the # of polykeys
        if not totalPolyKeys == validPolyKeys + len(exceedVerticeLimit):
            AddMsgAndPrint("\t\tThere is a discrepancy with the number of polygons for MUKEY: " + str(mukey),2)
            AddMsgAndPrint("\t\t\tOriginal Number of Polygons: " + str(totalPolyKeys),2)
            AddMsgAndPrint("\t\t\tProcessed Number of Polygons: " + str(validPolyKeys),2)

        if not len(polygonSubsetList):
            AddMsgAndPrint("\t\tSorting MUPOLYGONKEYS by Vertice count Failed.  Empty Final List",2)
            return False

        return polygonSubsetList

    except:
        errorMsg()

## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, traceback, operator
import urllib, urllib2, re, time, json
import arcgisscripting, arcpy
from arcpy import env

try:
    if __name__ == '__main__':

        searchString = arcpy.GetParameterAsText(0)         # search string for NASIS project names
        selectedProjects = arcpy.GetParameter(1)           # selected project names in a list
        outputFolder = arcpy.GetParameterAsText(2)

        # define and set the scratch workspace
        #scratchWS = setScratchWorkspace()
        scratchWS = r'D:\Temp\scratch.gdb'
        arcpy.env.scratchWorkspace = scratchWS

        # Hardcode NASIS-LIMS Report Webservice
        # Runs SDJR Status Report: Returns projects with similar name
        prjMapunit_URL = r"https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-Projectmapunits"

        sdaURL = r"https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

        selectedProjects = ['MLRA 102 - Fergus Falls Till Plain Formdale Catena Study, Re-correlation and Investigations']

        for project in selectedProjects:

##            # get a list of MUKEYs for NASIS project
##            nasisMUKEYs = getNasisMukeys(prjMapunit_URL, project)

            # create feature class
            nasisProjectFC = createOutputFC()
            if not nasisProjectFC: continue

            mukeys = ['3114927','2903473','408342']
             = groupMUKEYsByVertexCount(mukeys,feature="VERTICE")

            if not geometryRequestByMUKEY(nasisMUKEYsSorted):
               AddMsgAndPrint("WTF",2)

                #someDict = geometryRequestByMUKEY(nasisMUKEYs)
                #AddMsgAndPrint(str(nasisMUKEYs),1)

        AddMsgAndPrint("\n",0)

except:
    errorMsg()