#-------------------------------------------------------------------------------
# Name:        Report Conservation Practices by NASIS Project
# Purpose:
#
# Author:      adolfo.diaz
#
# Created:     2/8/2019
# Copyright:   (c) adolfo.diaz 2019

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

        if theMsg.find("sys.exit") > -1:
            AddMsgAndPrint("\n\n")
            pass
        else:
            AddMsgAndPrint(theMsg,2)

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
def getNasisMukeys(theProject):
    """ This function will create a list of NASIS MUKEYs for a specific NASIS project that is passed in.  The URL returns
        a report that is pipe delimitted with 2 values: project name and mukey.

        Return list of NASIS MUKEYs otherwise return False"""

    try:
        nasisMUKEYs = []  # List of MUKEYs pertaining to the project and parsed from the NASIS report

        AddMsgAndPrint("\tRetrieving MUKEYs from NASIS", 0)

        # URL To the NASIS Report: Web-Projectmapunits.  Show MUKEYs associated with a specific NASIS project
        prjMapunit_URL = r"https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-Projectmapunits"

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
            AddMsgAndPrint("\tNo Mapunits found for this NASIS project", 2)
            return False
        else:
            AddMsgAndPrint("\tIdentified " + splitThousands(len(nasisMUKEYs)) + " mapunits associated with this NASIS project", 0)

        del prjMapunit_URL, theReport, bValidRecord
        return nasisMUKEYs

    except IOError:
        AddMsgAndPrint("IOError, unable to connect to NASIS server", 2)
        return False

    except:
        errorMsg()
        return False

## ==============================================================================================================================
def createOutputFC(dictOfFields,preFix="Temp",shape="POLYGON"):
    """ This function will creat an empty polygon feature class within the scratch FGDB.  The feature class will be in WGS84
        and will have have 2 fields created: mukey and mupolygonkey.  The feature class name will have a prefix of
        'nasisProject.' This feature class is used by the 'requestGeometryByMUKEY' function to write the polygons associated with a NASIS
        project.

        fieldDict ={field:(fieldType,fieldLength,alias)
        fieldDict = {"mukey":("TEXT",30,"Mapunit Key"),"mupolygonkey":("TEXT","",30)}

        Return the new feature class  including the path.  Return False if error ocurred."""

    try:
        epsgWGS84 = 4326 # EPSG code for: GCS-WGS-1984
        outputCS = arcpy.SpatialReference(epsgWGS84)

        newFC = arcpy.CreateScratchName(preFix, workspace=arcpy.env.scratchGDB,data_type="FeatureClass")

        # Create empty polygon featureclass with coordinate system that matches AOI.
        arcpy.CreateFeatureclass_management(env.scratchGDB, os.path.basename(newFC), shape, "", "DISABLED", "DISABLED", outputCS)

        for field,params in dictOfFields.iteritems():
            try:
                fldLength = params[1]
                fldAlias = params[2]
            except:
                fldLength = 0
                pass

            arcpy.AddField_management(newFC,field,params[0],"#","#",fldLength,fldAlias)

##            if len(params[1]) > 0:
##                expression = "\"" + params[1] + "\""
##                arcpy.CalculateField_management(helYesNo,field,expression,"VB")

##        arcpy.AddField_management(nasisProjectFC,"mukey", "TEXT", "", "", "30")
##        arcpy.AddField_management(nasisProjectFC,"mupolygonkey", "TEXT", "", "", "30")   # for outputShp

        if not arcpy.Exists(newFC):
            AddMsgAndPrint("\tFailed to create scratch " + newFC + " Feature Class",2)
            return False

        return newFC

    except:
        errorMsg()
        AddMsgAndPrint("\tFailed to create scratch " + newFC + " Feature Class",2)
        return False

## ===================================================================================
def reportSDAgeometryInfoByMUKEY(listOfMUKEYs):
    """ This function will report MUKEY geometry info from soil data access from a list of MUKEYs.
        It was designed to determine what the geometry request limitation would be from SDA.
        The original thought was that there was a polygon record limit of 9,999 records but
        it turns out that the limit is related to a 32MB file size limit that is more than likely
        imposed by NRCS.  There is no limit on JSON request.  The function will print a report similar
        to:

        MUKEY            Polygon Count            Vertice Count            Geometry?            JSON Length            Request Time
        -----            -------------            -------------            ---------            -----------            ------------
        2903473          489                      811,826                  Yes                  31,982,735             1 minute(s): 10 second(s)
        1715499          2,159                    827,960                  No                   0                      5 second(s)
        346259           50                       8,900                    Yes                  354,117                2 second(s)
        522              0                        0                        No                   0                      1 second(s)
        2738636          1,198                    854,076                  No                   0                      5 second(s)

        Geometry? = Geometry request by MUKEY was successful, Yes or NO.
        JSON Length = Numbero of characters associated with request."""

    try:

        # ----------------Sample list of MUKEYS from FY2019 SSURGO used for testing.
        #listOfMUKEYs = ['398029', '428143', '399230', '2945666', '435652', '435966', '357022', '397576', '430262', '398021', '430335', '357018']
        #listOfMUKEYs = ['397580', '399212', '397554', '435967', '428311', '398030', '428530', '398031', '2945667', '396087', '397506', '435969', '401318', '356953', '398066', '399218', '428339', '398074', '396062']
        #listOfMUKEYs = ['397315', '397276', '428128', '401319']
        #listOfMUKEYs = ['2903473','1715499','346259']

        # Dictionary of MUKEYs and number of polygons associated with that MUKEY
        # {'1544915': 337,'1544918': 7,'1544928': 4,'1544929': 8}
        mukeyDict = dict()

        totalPolys = 0
        totalVertices = 0

        mukeyFailed = dict()
        clockStarts = tic()

        ## ===================================================================================
        def submitSDAquery(query,TIME=False,JSONlength=False):

            dRequest = dict()
            dRequest["format"] = "JSON"
            dRequest["query"] = query

            # Create SDM connection to service using HTTP
            jData = json.dumps(dRequest)

            try:
                # Send request to SDA Tabular service
                startTime = tic()
                req = urllib2.Request(sdaURL, jData)
                resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
                responseStatus = resp.getcode()
                responseMsg = resp.msg
                jsonString = resp.read()
                resp.close()
                endTime = toc(startTime)

                data = json.loads(jsonString) # dictionary containing 1 key with a list of lists
                return [data,endTime if TIME else '',splitThousands(len(jsonString)) if JSONlength else '']

            except urllib2.HTTPError, e:
                endTime = toc(startTime)

                if not mukey in mukeyFailed:
                   mukeyFailed[mukey] = int(e.code)

                if int(e.code) >= 500:
                   AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
                   AddMsgAndPrint("t\t" + str(request))
                   pass
                elif int(e.code) >= 400:
                   AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
                   AddMsgAndPrint("\t\t" + getGeometryQuery)
                   pass
                else:
                   AddMsgAndPrint('HTTP ERROR = ' + str(e.code),2)

                return ['',endTime if TIME else '','0']

            except:
                endTime = toc(startTime)
                errorMsg()
                return ['',endTime if TIME else '','0']
        ## ===================================================================================

        header = "MUKEY" + (" " * 12) + "Polygon Count" + (" " * 12) + "Vertice Count" + (" " * 12) + "Geometry?" + (" " * 12) + "JSON Length" + (" " * 12) + "Request Time"
        AddMsgAndPrint(header,0)
        AddMsgAndPrint("-" * 5 + " " * 12 + "-" * 13 + " " * 12 + "-" * 13 + " " * 12 + "-" * 9 +  " " * 12 + "-" * 11 + " " * 12 + "-" * 12,0)

        for mukey in listOfMUKEYs:

            polygonCountQuery = """SELECT COUNT(*) FROM mupolygon WHERE mukey = """ + mukey

            polyAndVerticeCountQuery = """SELECT COUNT(*) AS polycount, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                                          FROM mupolygon WHERE mukey = """ + mukey + """ GROUP BY mukey"""

            sdaGeometryQuery = """SELECT mukey, mupolygongeo.STAsText()
                                  FROM mupolygon
                                  WHERE mukey IN (""" + mukey + """)"""

            # get Polygon and Vertice Count
            data = submitSDAquery(polyAndVerticeCountQuery,TIME=True,JSONlength=False)

            # No polygon or vertice count available; bad MUKEY?
            if not "Table" in data[0]:
               AddMsgAndPrint(mukey + (" " * (17 - len(mukey))) + "0" + (" " * 24) + "0" + (" " * 24) + "No" + (" " * 19) + "0" + (" " * 22) + data[1],0)
               continue

            mukeyPolyCount = int(data[0]['Table'][0][0])
            mukeyVerticeCount = int(data[0]['Table'][0][1])
            totalPolys += mukeyPolyCount
            totalVertices += mukeyVerticeCount

            # get geometry from SDA
            data2 = submitSDAquery(sdaGeometryQuery,TIME=True,JSONlength=True)

            # No polygon geometry was returned
            if not "Table" in data2[0]:
               geometry = "No"
            else:
               geometry = "Yes"

            jsonLength = data2[2]
            responseTime = data2[1]

            AddMsgAndPrint(mukey + (" " * (17 - len(mukey))) + splitThousands(mukeyPolyCount) + (" " * (25 - len(splitThousands(mukeyPolyCount)))) + splitThousands(mukeyVerticeCount) +
                       (" " * (25 - len(splitThousands(mukeyVerticeCount)))) + geometry + (" " * (21 - len(geometry))) + jsonLength +
                        (" " * (23 - len(jsonLength))) + responseTime,0)

            del data,mukeyPolyCount,mukeyVerticeCount,data2

        AddMsgAndPrint("Total Time: " + toc(clockStarts))

        # Report MUKEYs that failed and their HTTP Error
        if len(mukeyFailed) > 0:
           AddMsgAndPrint("\nThe following " + str(len(mukeyFailed)) + " mapunits had HTTP errors",2)
           for item in mukeyFailed.iteritems():
               AddMsgAndPrint("MUKEY " + item[0] + " - HTTP Error: " + str(item[1]))

    except:
        errorMsg()

## ==============================================================================================================================
def createGeometryFromKeys(dictOfKEYs):
    """ This function will request soil geometry from Soil Data Access and write it to a feature class or shapefile.  The
         function takes in a list of SSURGO MUKEYs or a dictionary of grouped MUKEYs created from the 'groupMUKEYsByCount'
         function.  If a list is passed than the list will be passed over to the groupMUKEYsByCount function to restructured
         to ensure the mukeys are grouped together based on the maximum vertice limit.

         The dictionary will contain lists of either MUKEYs or MUPOLYGONKEYs.  Keys beginning with MUKEY* will have a list
         of MUKEYs as their item.  Keys beginning with MUPOLYGONKEY* will have a list of mupolygonkeys as their item.
         i.e. {'MUKEY0': ['408342'], 'MUPOLYGONKEY0': ['228419267','228421430','217139720','228419274','217125974','217139721']}
         The number of items in the dictionary translates into the number of SDA requests that will be submitted.  Geometry will
         either be requested by MUKEY or MUPOLYGONKEY, which are 2 different queries determined by the function.

         Geometry will be written to a feature class or shapefile along with MUKEY and MUPOLYGONKEY.  MUPOLYGONKEY represents
         the unique polygon ID in SQL Server.

         Return True if no errors are encountered; otherwise return False"""

    try:
        AddMsgAndPrint("\tRequesting Soil Geometry from SDA")

        if not str(type(dictOfKEYs)).find('dict') > -1:
           dictOfMUKEYs = groupMUKEYsByCount(dictOfKEYs)
           if not dictOfKEYs: return False

        sampleKey = re.sub(r'[0-9]+', '', dictOfKEYs.items()[0][0])
        if not sampleKey in ('MUKEY','MUPOLYGONKEY'):
           AddMsgAndPrint("\t\tInput MUKEYs are incorrectly formatted",2)
           return False

        numOfRequests = len(dictOfKEYs)
        currentRequest = 0

        for request in dictOfKEYs.items():
            requestType = re.sub(r'[0-9]+', '', request[0])  # MUKEY or MUPOLYGONKEY
            requestList = request[1]                         # list of mukeys or mupolygonkeys

            listOfKeys = str(requestList).replace("[","").replace("]","").replace("'","")

            if requestType == 'MUKEY':
                # query geometry by list of MUKEYs
                getGeometryQuery = """SELECT mukey, MuPolygonKey, mupolygongeo.STAsText()
                                        FROM mupolygon
                                        WHERE mukey IN (""" + listOfKeys + """)"""
            else:
                # query geometry by list of mupolygonkeys
                getGeometryQuery = """SELECT mukey, MuPolygonKey, mupolygongeo.STAsText()
                                      FROM mupolygon
                                      WHERE MuPolygonKey IN (""" + listOfKeys + """)"""

            # Post.rest request parameters in dict format
            dRequest = dict()
            dRequest["format"] = "JSON"
            dRequest["query"] = getGeometryQuery

            # Convert to JSON formatted string
            jData = json.dumps(dRequest)

            try:
                # Send request to SDA Tabular service
                req = urllib2.Request(sdaURL, jData)
                resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
                responseStatus = resp.getcode()
                responseMsg = resp.msg
                jsonString = resp.read()
                resp.close()

                # dictionary containing 1 key with a list of lists
                data = json.loads(jsonString)

            except urllib2.HTTPError, e:
                if int(e.code) >= 500:
                   AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
                   #AddMsgAndPrint("t\t" + str(request))
                elif int(e.code) >= 400:
                   AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
                   AddMsgAndPrint("\t\t" + getGeometryQuery)
                else:
                   AddMsgAndPrint('HTTP ERROR = ' + str(e.code),2)
                continue

            except:
                errorMsg()

            if not "Table" in data:
               AddMsgAndPrint("\t\tNo data returned for " + requestType + ": " + str(requestList),2)
               continue

            # Convert the dictionary to a list of lists. Service returns everything as string.
            # 1 record will contain 2 items: KEY and list of coordinates that make up that polygon
            # i.e. [u'357347', u'POLYGON ((-96.57 45.68, -96.57 45.68, -96.57 45.68, -96.57 45.68))']
            dataList = data["Table"]
            del listOfKeys,getGeometryQuery,dRequest,jData,jsonString,resp,req

            #AddMsgAndPrint("\n\tSDA Geometry request: " + toc(startTime) + " Reqest: " + str(currentRequest) + " of " + str(numOfRequests))

            # Only two fields are used initially, the geometry and MUKEY
            fields = ["mukey","mupolygonkey","SHAPE@WKT"]

            startTime = tic()
            with arcpy.da.InsertCursor(nasisProjectFC, fields) as cur:

                for rec in dataList:
                    mukey = rec[0]
                    mupolygonkey = rec[1]
                    wktPoly = rec[2]

                    if not mukey is None and not mukey == '':
                        cur.insertRow((mukey,mupolygonkey,wktPoly))
            del cur

            currentRequest+=1
            return True

    except:
        errorMsg()
        return False

## ==============================================================================================================================
def groupMUKEYsByCount(listOfMUKEYs,feature="VERTICE"):
    """ This function takes in a list of MUKEYS and groups them based on maximum POLYGON or VERTICE thresholds so that SDA
        geometry requests are efficient and successful.  Second parameter to this function is optional.  User has the choice
        of grouping MUKEYs by VERTICE or POLYGON.  POLYGON Threshold is set to 9,999 records which is the default with
        SDA (I haven't seen this to be a limitation).  VERTICE Threshold is set to 811,000
        (determined by MUKEY: 2903473 - OH161 - FY19)

        Polygon and Vertice counts are collected from SDA by MUKEY.  The MUKEYs are then sorted ascendingly by vertice or
        polgyon county (user-determined) and then grouped into lists that don't exceed the feature threshold.  These sub-lists
        can then be sent to SDA for to return geometry in JSON format.  If vertice counts are not asseessed then groups of mukeys
        that exceed the vertice threshold will fail.  Individual MUKEYs that exceed the vertice threshold will be broken into
        groups of associated polygons whose vertice count is below the threshold.

        A dictionary containing lists of either MUKEYs or MUPOLYGONKEYs will be returned.  Keys beginning with MUKEY* will have a list
        of MUKEYs as their item.  Keys beginning with MUPOLYGONKEY* will have a list of mupolygonkeys as their item.
        i.e. {'MUKEY0': ['408342'], 'MUPOLYGONKEY0': ['228419267','228421430','217139720','228419274','217125974','217139721']}
        The number of items in the dictionary translates into the number of SDA requests that will be submitted.  Geometry will
        either be requested by MUKEY or MUPOLYGONKEY

        Return False if errors are encountered."""

    try:
        AddMsgAndPrint("\tGrouping MUKEYs together by " + feature.lower() + " thresholds")

        if not len(listOfMUKEYs) > 0:
           AddMsgAndPrint("\t\tEmpty list of MUKEYs was passed",2)
           return False

        if feature == "POLYGON":
           countThreshold = 9999    # Max Polygon records per subList
           countFeatureID = 1
        elif feature == "VERTICE":
           countThreshold = 811000  # Max number Vertices per subList
           countFeatureID = 2
        else:
           AddMsgAndPrint("\n\t\tInvalid feature type parameter passed",2)
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
        getPolygonCountByMukey = """SELECT COUNT(*) FROM mupolygon WHERE mukey = """ + mukey

        getVerticeCountByMukey = """SELECT mukey, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                                  FROM mupolygon
                                  WHERE mukey = """ + mukey + """GROUP BY mukey"""

        getPolyAndVerticeCountByMUKEY = """SELECT mukey, COUNT(*) AS polycount, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                                         FROM mupolygon WHERE mukey IN (""" + mukey + """)
                                         GROUP BY mukey
                                         ORDER BY vertex_count ASC"""

        # Post.rest request parameters in dict format
        dRequest = dict()
        dRequest["format"] = "JSON"
        dRequest["query"] = getPolyAndVerticeCountByMUKEY

        # Convert to JSON formatted string
        jData = json.dumps(dRequest)

        try:
            # Send request to SDA Tabular service
            req = urllib2.Request(sdaURL, jData)  # Create SDM connection to service using HTTP
            resp = urllib2.urlopen(req)           # A failure here will probably throw an HTTP exception
            responseStatus = resp.getcode()
            responseMsg = resp.msg
            jsonString = resp.read()
            resp.close()

            # dictionary containing 1 key with a list of lists
            data = json.loads(jsonString)

        except urllib2.HTTPError, e:
            if int(e.code) >= 500:
               AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
               #AddMsgAndPrint("t\t" + str(request))
            elif int(e.code) >= 400:
               AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
               AddMsgAndPrint("\t\t" + getPolyAndVerticeCountByMUKEY)
            else:
               AddMsgAndPrint('HTTP ERROR = ' + str(e.code),2)
            return False

        except:
            errorMsg()
            return False

        # This would only happen if the mukeys didn't exist
        if not "Table" in data:
           AddMsgAndPrint("\n\t\tNo data returned for MUKEY: " + str(mukeyList),2)
           return False

        del getPolyAndVerticeCountByMUKEY,dRequest,jData,req,resp,jsonString

        # Tally up the counts
        mukeyPolyCount = sum([int(item[1]) for item in data['Table']])
        mukeyVerticeCount = sum([int(item[2]) for item in data['Table']])
        totalPolys += mukeyPolyCount
        totalVertices += mukeyVerticeCount

        # MUKEY that have no polygons associated
        mukeysReturned = [item[0] for item in data['Table']]
        mukeyNoPolygon = [item for item in listOfMUKEYs if item not in mukeysReturned]

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
            AddMsgAndPrint("\t\tThere are " + str(len(mukeysExceedThreshold)) + " MUKEYs that exceed the SDA JSON limit.  Retrieving list MU Polygon Keys.")
            mupolygonkeyGroupList = groupMupolygonkeyByVertexCount(mukeysExceedThreshold)

            if mupolygonkeyGroupList:
                iCount = 0
                for polykeyList in mupolygonkeyGroupList:
                    mukeySubsetsDict['MUPOLYGONKEY' + str(iCount)] = polykeyList
                    iCount+=1
            else:
                 AddMsgAndPrint("\t\t\tNo geometry will be available for MUKEYs: " + str(mukeysExceedThreshold),2)

        # Make sure all MUKEYs were accounted; Number of valid MUKEYs processed and MUKEYs with
        # no polygons and excessive vertices should be the same as the # of MUKEYs submitted
        if not len(listOfMUKEYs) == validMukeys + len(mukeyNoPolygon) + len(mukeysExceedThreshold):
            AddMsgAndPrint("\t\tThere is a discrepancy with the MUKEYs bein grouped by vertice count:",2)
            AddMsgAndPrint("\t\t\tOriginal Number of MUKEYs: " + str(len(listOfMUKEYs)),2)
            AddMsgAndPrint("\t\t\tProcessed Number of MUKEYs: " + str(validMukeys),2)
            AddMsgAndPrint("\t\t\tNumber of MUKEYs with no polygons: " + str(len(mukeyNoPolygon)),2)
            AddMsgAndPrint("\t\t\tNumber of MUKEYs with excessive vertices: " + str(len(mukeysExceedThreshold)),2)

        if len(mukeyNoPolygon):
            AddMsgAndPrint("\t\tThe following " + str(len(mukeyNoPolygon)) + " MUKEY(s) have no geometry data available:",1)
            AddMsgAndPrint("\t\t\t" + str(mukeyNoPolygon),1)

        if not len(mukeySubsetsDict):
            AddMsgAndPrint("\n\t\tGrouping MUKEYS by " + feature + " Failed.  Empty Final List",2)
            return False

        AddMsgAndPrint("\tTotal Polygons asociated with mapunits: " + splitThousands(totalPolys))
        #AddMsgAndPrint("\tTotal " + feature + " Count: " + (splitThousands(totalPolys) if countFeatureID == 0 else splitThousands(totalVertices)))

        return mukeySubsetsDict

    except:
        errorMsg()
        return False

## ==============================================================================================================================
def groupMupolygonkeyByVertexCount(listOfMUKEYs):
    """ This function takes in a list of MUKEYS and groups the associated polygons based on the maximum VERTICE threshold of
        811,000 vertices so that SDA geometry requests are efficient and successful.  VERTICE Threshold is set to 811,000
        (determined by MUKEY: 2903473 - OH161 - FY19)

        This function can be called independently OR by the groupMUKEYsByCount function. MUKEY, MUPOLYGONKEY and Vertice
        count are collected from SDA and stored in a dictionary.  The MUPOLYGONKEYs are then sorted ascendingly by vertice count
        and then grouped into lists that don't exceed the vertice threshold.  MUPOLYGONKEYs are the unique polygon identifier
        assigned by SQL Server.  It is the equivalent of OID or FID.

        A list of MUPOLYGONKEY lists is returned.  The user will be warned of individual polygons that exceed the vertice
        threshold.  Those MUPOLYGONKEYs will not be included in the returned list."""

    try:
        if not len(listOfMUKEYs):
           AddMsgAndPrint("\t\t\tEmpty list of MUKEYs was passed",2)
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

        except urllib2.HTTPError, e:
            if int(e.code) >= 500:
               AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
               #AddMsgAndPrint("t\t" + str(request))
            elif int(e.code) >= 400:
               AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
               AddMsgAndPrint("\t\t" + getVerticeCountByMuPolygonKey)
            else:
               AddMsgAndPrint('HTTP ERROR = ' + str(e.code),2)
            return False

        except:
            errorMsg()
            return False

        # This would only happen if the mukeys didn't exist
        if not "Table" in data:
           AddMsgAndPrint("\t\t\tNo Polygon information returned for MUKEYs: " + str(mukey),2)
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
            AddMsgAndPrint("\t\t\tVertice limitation is exceeded by the following " + str(len(exceedVerticeLimit)) + " polygon(s):",1)
            for polykey in exceedVerticeLimit:
                mukey = str([item[0] for item in data['Table'] if item[2] == polykey][0]).replace(' ','')
                vertexCount = splitThousands([item[1] for item in data['Table'] if item[2] == polykey][0])
                AddMsgAndPrint("\t\t\t\tMUKEY: " + mukey + " -- MUPOLYGONKEY: " + str(polykey) + " -- Vertice Count: " + vertexCount,1)
                del mukey,vertexCount

        # Make sure all polykeys were accounted; Number of valid polykeys processed and
        # polykeys with exceeded vertices should be the same as the # of polykeys
        if not totalPolyKeys == validPolyKeys + len(exceedVerticeLimit):
            AddMsgAndPrint("\t\t\tThere is a discrepancy with the number of polygons for MUKEY: " + str(mukey),2)
            AddMsgAndPrint("\t\t\t\tOriginal Number of Polygons: " + str(totalPolyKeys),2)
            AddMsgAndPrint("\t\t\t\tProcessed Number of Polygons: " + str(validPolyKeys),2)

        if not len(polygonSubsetList):
            AddMsgAndPrint("\n\t\t\tSorting MUPOLYGONKEYS by Vertice count Failed.  Empty Final List",2)
            return False

        return polygonSubsetList

    except:
        errorMsg()

## ===================================================================================
def submitFSquery(url,paramaters):

# This is returned by url
# {u'error': {u'code': 498, u'details': [], u'message': u'Invalid Token'}}

    try:
        req = urllib2.Request(url,paramaters)
        resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
        responseStatus = resp.getcode()
        responseMsg = resp.msg
        jsonString = resp.read()

        # dictionary containing 1 key with a list of lists
        return json.loads(jsonString)

    except urllib2.HTTPError, e:

        if int(e.code) >= 500:
           #AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
           #AddMsgAndPrint("t\t" + str(request))
           pass
        elif int(e.code) >= 400:
           #AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
           #AddMsgAndPrint("\t\t" + getGeometryQuery)
           pass
        else:
           AddMsgAndPrint('HTTP ERROR = ' + str(e.code),2)

## ===================================================================================
def getPlanLandUnitsByGeometry(fc):

    try:
        AddMsgAndPrint("\tQuerying GeoPortal for Planned Land Units")

        """ -------------------------------------- get Feature Service Info -------------------------------"""
        # URL for Feature Service Metadata (Service Definition) - Dictionary of ;
        pluURL = """https://geoportal.sc.egov.usda.gov/arcgis/rest/services/Hosted/WI_Plan_Land_Units_TEST_copyAllData/FeatureServer/1?"""

        # Used for admin or feature service info
        params = urllib.urlencode({'f': 'json','token': tokenInfo['token']})

        # request info about the feature service
        metadata = submitFSquery(pluURL,params)

        # Get the Max record count the fs can return
        if not 'maxRecordCount' in metadata:
           AddMsgAndPrint('\t\tCould not determine FS maximum record count: Setting default to 1,000 records',1)
           maxRecordCount = 1000
        else:
           maxRecordCount = metadata['maxRecordCount']

        # fields associated with feature service
        fsFields = metadata['fields']   # {u'domain': None, u'name': u'land_unit_id', u'nullable': True, u'editable': True, u'alias': u'LAND_UNIT_ID', u'length': 38, u'type': u'esriFieldTypeString'}
        fieldDict = dict()

        # lookup list for fields that are in DATE field; Date values need to be converted
        # from Unix Epoch format to mm/dd/yyyy format in order to populate a table
        dateFields = list()

        # Collect field info to pass to new fc
        for fieldInfo in fsFields:

            # skip the OID field
            if fieldInfo['type'] == 'esriFieldTypeOID':
               continue

            # cross-reference portal attribute description with ArcGIS attribute description
            fldTypeDict = {'esriFieldTypeString':'TEXT','esriFieldTypeDouble':'DOUBLE','esriFieldTypeSingle':'FLOAT',
                           'esriFieldTypeInteger':'LONG','esriFieldTypeSmallInteger':'SHORT','esriFieldTypeDate':'DATE',
                           'esriFieldTypeGUID':'GUID','esriFieldTypeGlobalID':'GUID'}

            fldType = fldTypeDict[fieldInfo['type']]
            fldAlias = fieldInfo['alias']
            fldName = fieldInfo['name']

            if fldType == 'TEXT':
               fldLength = fieldInfo['length']
            elif fldType == 'DATE':
                 dateFields.append(fldName)
            else:
               fldLength = ""

            fieldDict[fldName] = (fldType,fldLength,fldAlias)

        """ ----------------------------------- request PLU Geometry for envelope -----------------------------------"""
        # Create envelope from fc; this was introduced b/c the extent can be
        # incorrect from the incoming fc due to editing. Extent is in JSON
        outEnvelope = "in_memory" + os.sep + os.path.basename(arcpy.CreateScratchName("envelope",data_type="FeatureClass",workspace=scratchWS))
        arcpy.MinimumBoundingGeometry_management(fc,outEnvelope,"ENVELOPE", "NONE")
        desc = arcpy.Describe(outEnvelope)
        extent = desc.extent.JSON
        arcpy.Delete_management(outEnvelope)

        pluURL = """https://geoportal.sc.egov.usda.gov/arcgis/rest/services/Hosted/WI_Plan_Land_Units_TEST_copyAllData/FeatureServer/1/query?"""

        # Get Object IDs of features within bounding box; No Geometry returned.
        params = urllib.urlencode({'f': 'json','geometry':extent,'returnGeometry':'false','returnIdsOnly':'true','token': tokenInfo['token']})

        # Get Record count of bounding box; No Geometry returned.
##        params = urllib.urlencode({'f': 'json', 'geometryType': 'esriGeometryEnvelope','geometry':extent,
##        'spatialRel': 'esriSpatialRelIntersects','returnCountOnly':'true','returnGeometry':'false','token': tokenInfo['token']})

        # Send request to feature service
        objectIDs = submitFSquery(pluURL,params)

        if not 'objectIds' in objectIDs:
           AddMsgAndPrint('\t\tCould not determine PLU polygon count from project extent',2)

        listOfObjectIDs = objectIDs['objectIds']   # Number of OIDs returned
        OIDfld = objectIDs['objectIdFieldName']    # Object ID field name

        # Bail if there is no overlap
        if not len(listOfObjectIDs):
           AddMsgAndPrint("\t\tThere are no PLUs that overlap this AOI",1)
           return False,False

        # Slice Object IDs into lists not exceeding the feature service maxRecordCount.
        # This may or may not be needed but it doesn't hurt and I avoid a seperate query
        oidSubsetLists = [listOfObjectIDs[i:i+maxRecordCount] for i in range(0, len(listOfObjectIDs), maxRecordCount)]

        """ ----------------------------------- write PLU Geometry for envelope ----------------------------------- """
        pluPolyFC = createOutputFC(fieldDict,"pluPolyFC")
        landUnitIDs = list()  # list containing lists of Land Unit IDs

        for subsetList in oidSubsetLists:
            oids = str(subsetList).replace("[","").replace("]","")
            landUnitIDsubList = list()  # sublist of land Unit IDs

            # Get geometry by OID
            params = urllib.urlencode({'f': 'json','returnGeometry':'true','objectIds': oids,'token': tokenInfo['token']})

            # Send request to feature service
            geometry = submitFSquery(pluURL,params)

            # Isolate the fields that were inserted into new fc
            fields = fieldDict.keys()
            fields.append("SHAPE@JSON")

            # Insert Geometry
            with arcpy.da.InsertCursor(pluPolyFC, fields) as cur:

                # Iterenate through records returned from FS
                for rec in geometry['features']:
                    values = list()    # list of attributes

                    polygon = unicode(json.dumps(rec['geometry']))   # u'geometry': {u'rings': [[[-89.407702228, 43.334059191999984], [-89.40769642800001, 43.33560779300001]}
                    attributes = rec['attributes']                   # u'attributes': {u'land_unit_id': u'73F53BC1-E3F8-4747-B51F-E598EE445E47'}}

                    for fld in fields:
                        if fld == "SHAPE@JSON":
                            continue
                        elif fld == "land_unit_id":
                            landUnitIDsubList.append(attributes[fld])
                            values.append(attributes[fld])

                        # DATE values need to be converted from Unix Epoch format
                        # to dd/mm/yyyy format so that it can be inserted into fc.
                        elif fieldDict[fld][0] == 'DATE':
                            dateVal = attributes[fld]
                            if not dateVal in (None,'null','','Null'):
                                epochFormat = float(attributes[fld])                                    # 1609459200000

                                # Convert to seconds from milliseconds and reformat
                                localFormat = time.strftime('%m/%d/%Y',time.gmtime(epochFormat/1000))   # 01/01/2021
                                values.append(localFormat)
                            else:
                                values.append(None)
                        else:
                            values.append(attributes[fld])

                    # geometry goes at the the end
                    values.append(polygon)
                    cur.insertRow(values)

            landUnitIDs.append(landUnitIDsubList)
            del landUnitIDsubList,geometry,cur

        return pluPolyFC,landUnitIDs

        # Login error
        # {"error":{"code":499,"message":"Token Required","details":[]}}

        # Token geoportal site
        # https://geoportal.sc.egov.usda.gov/portal/sharing/rest/generateToken

        #arcpy.SignInToPortal(arcpy.GetActivePortalURL(), 'username', 'password')

    except:
        errorMsg()
        return False,False

# ===================================================================================
def getPracticePointsByID(listOfPLUIDs):

    try:

        AddMsgAndPrint("\tQuerying GeoPortal for Practice Points")

        pluPntURL = """https://geoportal.sc.egov.usda.gov/arcgis/rest/services/Hosted/WI_Practice_Points_TEST_copyAllData/FeatureServer/1?"""

        # Used for admin or feature service info
        params = urllib.urlencode({'f': 'json','token': tokenInfo['token']})

        # request info about the feature service
        metadata = submitFSquery(pluPntURL,params)

        # fields associated with feature service
        fsFields = metadata['fields']   # {u'domain': None, u'name': u'land_unit_id', u'nullable': True, u'editable': True, u'alias': u'LAND_UNIT_ID', u'length': 38, u'type': u'esriFieldTypeString'}
        fieldDict = dict()

        # Collect field info to pass to new fc
        for fieldInfo in fsFields:

            # skip the OID field
            if fieldInfo['type'] == 'esriFieldTypeOID':
               continue

            # cross-reference portal attribute description with ArcGIS attribute description
            fldTypeDict = {'esriFieldTypeString':'TEXT','esriFieldTypeDouble':'DOUBLE','esriFieldTypeSingle':'FLOAT',
                           'esriFieldTypeInteger':'LONG','esriFieldTypeSmallInteger':'SHORT','esriFieldTypeDate':'DATE',
                           'esriFieldTypeGUID':'GUID','esriFieldTypeGlobalID':'GUID'}

            fldType = fldTypeDict[fieldInfo['type']]
            fldAlias = fieldInfo['alias']
            fldName = fieldInfo['name']

            if fldType == 'TEXT':
               fldLength = fieldInfo['length']
            else:
               fldLength = ""

            fieldDict[fldName] = (fldType,fldLength,fldAlias)

        pluPntFC = createOutputFC(fieldDict,"pluPntFC","POINT")

        pluPntURL = """https://geoportal.sc.egov.usda.gov/arcgis/rest/services/Hosted/WI_Practice_Points_TEST_copyAllData/FeatureServer/1/query?"""

        for pluIDList in listOfPLUIDs:
            # SQL statement isolating list of land unit IDs;
            # LAND_UNIT_ID IN ('EE5F293F-0F1E-4598-9FAE-B606D3DFD626', 'F9A11F75-DEE2-4174-8C78-1EEEE4A9DCE9')
            whereClause = 'LAND_UNIT_ID IN ' + str(pluIDList).replace("[","(").replace("]",")").replace("u","")

            # Get geometry by land unit ID
            params = urllib.urlencode({'f': 'json','returnGeometry':'true','where': whereClause,'outFields':'*','token': tokenInfo['token']})

             # Send request to feature service
            geometry = submitFSquery(pluPntURL,params)

            # Isolate the fields that were inserted into new fc
            fields = fieldDict.keys()
            fields.append("SHAPE@XY")

            # Insert Geometry
            with arcpy.da.InsertCursor(pluPntFC, fields) as cur:

                 # Iterenate through records returned from FS
                for rec in geometry['features']:
                    values = list()    # list of attributes

                    xyPoint = (rec['geometry']['x'],rec['geometry']['y'])     # u'geometry': {u'y': 43.317420449999986, u'x': -89.49036579300002}
                    attributes = rec['attributes']                            # u'attributes': {u'land_unit_id': u'73F53BC1-E3F8-4747-B51F-E598EE445E47'}}

                    # collect list of attributes
                    for fld in fields:
                        if fld == "SHAPE@XY":
                            continue

                        # DATE values need to be converted from Unix Epoch format
                        # to dd/mm/yyyy format so that it can be inserted into fc.
                        elif fieldDict[fld][0] == 'DATE':
                            dateVal = attributes[fld]
                            if not dateVal in (None,'null','','Null'):
                                epochFormat = float(attributes[fld])                                    # 1609459200000

                                # Convert to seconds from milliseconds and reformat
                                localFormat = time.strftime('%m/%d/%Y',time.gmtime(epochFormat/1000))   # 01/01/2021
                                values.append(localFormat)
                            else:
                                 values.append(None)
                        else:
                            values.append(attributes[fld])

                    # geometry goes at the the end
                    values.append(xyPoint)
                    cur.insertRow(values)
            del cur
        return pluPntFC

    except:
        errorMsg()
        return False


## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, traceback, operator
import urllib, urllib2, re, time, json
import arcgisscripting, arcpy
from arcpy import env
from datetime import datetime

try:
    if __name__ == '__main__':

       startTime = tic()

       # -------------------Need to add code to make sure user is logged into portal.
       # Returns token information when signed in to ArcGIS.com or a local portal
       # Token info will also be added to URL when querying feature service.
       # Add this to validate code as well Returns token information when signed in to ArcGIS.com or a local portal
       tokenInfo = arcpy.GetSigninToken()

       searchString = arcpy.GetParameterAsText(0)         # search string for NASIS project names
       selectedProjects = arcpy.GetParameter(1)           # selected project names in a list
       outputFolder = arcpy.GetParameterAsText(2)

       # define and set the scratch workspace
       scratchWS = r'M:\IDEA\scratch.gdb'
#      scratchWS = setScratchWorkspace()
       arcpy.env.scratchWorkspace = scratchWS

       sdaURL = r"https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

       selectedProjects = ['MLRA 102 - Fergus Falls Till Plain Formdale Catena Study, Re-correlation and Investigations']
       selectedProjects= [r'M:\IDEA\WI_PLU_test.gdb\test2']#,r'M:\IDEA\WI_PLU_test.gdb\test']

       """ Iterate through user selected NASIS Projects to report Conservation practice names"""
       for project in selectedProjects:
##           startTime = tic()
##           AddMsgAndPrint("\n" + 110 * '*',0)
##           AddMsgAndPrint("Processing: " + project)
##
##           """----------- get a list of MUKEYs associated to this NASIS project ----------"""
##           nasisProjectMUKEYs = getNasisMukeys(project)
##           if not len(nasisProjectMUKEYs):
##              continue
##
##           """-------------- create empty polygon feature class for NASIS project ---------------"""
##           fieldDict = {"mukey":("TEXT",30,"Mapunit Key"),"mupolygonkey":("TEXT",30,"Mapunit Poly Key")}
##           nasisProjectFC = createOutputFC(fieldDict,"nasisProject")
##           if not nasisProjectFC:
##               AddMsgAndPrint("\tFailed to create a scratch feature class for: " + project + " SKIPPING This Project!",2)
##               continue
##
##           """----------------------- group MUKEYs by vertice threshold --------------------------"""
##           #nasisProjectMUKEYs = ['3114927','2903473','408342']
##           groupedKeys = groupMUKEYsByCount(nasisProjectMUKEYs,feature="VERTICE")
##
##           """---------------------------- Create geometry from MUKEYs ---------------------------"""
##           if not createGeometryFromKeys(groupedKeys):
##              AddMsgAndPrint("\nError Creating geometry",2)
##              continue

           """---------------------------- Get PLU Data from GeoPortal --------------------"""
           pluPolys,pluIDs = getPlanLandUnitsByGeometry(project)
           if not pluPolys:
              AddMsgAndPrint("\nError Acquiring PLU Data from GeoPortal",2)
              continue

           """---------------------------- Get Practice Point Data from GeoPortal --------------------"""
           ##pluIDs = [['78A0ED6B-DD1C-4CE5-9299-E14FD11EFF10', '11BA6371-CE4D-481B-82BC-D1240C3180DB', '6224D83F-98DE-40B8-B59F-C92A840E8A7B'],['D572AF7E-80ED-4F35-BE22-A9838D17B643','34812EF8-5C7E-4F24-B4A6-52F95A7BFDA9']]
           #pluIDs = [['11BA6371-CE4D-481B-82BC-D1240C3180DB']]
           pluPntFC = getPracticePointsByID(pluIDs)
           if not pluPntFC:
              AddMsgAndPrint("\nError Acquiring Practice Points Data from GeoPortal",2)
              continue

           AddMsgAndPrint("\n\tProcessing Time: " + toc(startTime))

       AddMsgAndPrint("\n",0)

except:
    errorMsg()