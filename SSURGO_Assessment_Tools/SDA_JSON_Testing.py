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

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        AddMsgAndPrint(theMsg, 2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
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

## ================================================================================================================
def getObjectSize(obj, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}
    """

    try:
        # lamda function to iterate through a dictionary
        dict_handler = lambda d: chain.from_iterable(d.items())

    #     Use the following lines if you want to determine the size for ANY object
    ##    all_handlers = {tuple: iter,
    ##                    list: iter,
    ##                    deque: iter,
    ##                    dict: dict_handler,
    ##                    set: iter,
    ##                    frozenset: iter,
    ##                   }

        # Limit the focus to just dictionaries since that is the only thing I will pass
        all_handlers = {dict: dict_handler}

        all_handlers.update(handlers)     # user handlers take precedence
        seen = set()                      # unique list of Object's memory ID
        default_size = getsizeof(0)       # estimate sizeof object without __sizeof__; a dict will always be 140 bytes

        def sizeof(obj):

            if id(obj) in seen:       # do not double count the same object's memory ID
                return 0

            seen.add(id(obj))
            s = getsizeof(obj, default_size)

            if verbose:
                print(s, type(obj), repr(obj))

            # iterate through all itemized objects (tuple,list) 'all_handlers' including their content
            for typ, handler in all_handlers.items():

                # check if the object is associated with the type at hand.  i.e. if the current
                # type is dict then check if the object 'o' is a dict. ({'a': 1, 'c': 3, 'b': 2, 'e': 'a string of chars', 'd': [4, 5, 6, 7]})
                # if True, go thru and add the bytes for each eleement
                if isinstance(obj, typ):
                    s += sum(map(sizeof, handler(obj)))   # Iterates through this function
                    break

            return s

        byteSize = sizeof(obj)

        if byteSize < 1024:
            return splitThousands(byteSize) + " bytes"
        elif byteSize > 1023 and byteSize < 1048576:
            return splitThousands(round((byteSize / 1024.0),1)) + " KB"
        elif byteSize > 1048575 and byteSize < 1073741824:
            return splitThousands(round((byteSize / (1024*1024.0)),1)) + " MB"
        elif byteSize > 1073741823:
            return splitThousands(round(byteSize / (1024*1024*1024.0),1)) + " GB"

    except:
        errorMsg()
        pass

## ================================================================================================================
def tic():
    """ Returns the current time """

    return time.time()

## ================================================================================================================
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

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ===================================================================================
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
            AddMsgAndPrint(" \tIdentified " + Number_Format(len(nasisMUKEYs), 0, True) + " mapunits associated with this NASIS project", 0)

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

## ===================================================================================
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


## ===================================================================================
def geometryRequestByMUKEYLists(nasisMUKEYs,sortedByCount=True):

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

            # Following 3 lines represents reduced geometry from SDA
##            sdaQuery = """SELECT mukey, mupolygongeo.Reduce(0.0001).STAsText()
##                          FROM mupolygon
##                          WHERE mukey IN (""" + mukeys + """)"""

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

                text_file = open(r'D:\Temp\MUKEY_SDA.txt', "w")
                text_file.write(jsonString)
                text_file.close()

                AddMsgAndPrint("\tSUCCESS....NEXT..........jSON String: " + splitThousands(len(jsonString)))
                AddMsgAndPrint("\tSize of string: " + str(getObjectSize(data)))
                AddMsgAndPrint("\tSystem Size: " + str(sys.getsizeof(jsonString)))
                return data

##            except:
##                AddMsgAndPrint("\n\tFailed ----------------- ")
##                AddMsgAndPrint(str(mukeys))

            except urllib2.HTTPError, e:
                AddMsgAndPrint('HTTPError = ' + str(e.code))
                AddMsgAndPrint("5000000000",2)
                return False

            except:
                errorMsg()
                continue

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

## ===================================================================================
def geometryRequestByMUKEYLists_Phil(nasisMUKEYs,sortedByCount=True):

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

            sdaQuery = """
DROP TABLE IF EXISTS #MuNoAdolfo;
~DeclareInt(@numberOfPartitions)~; --use for python and SDA
SELECT @numberOfPartitions = 5
~DeclareInt(@partitionNumber)~;  --use for python and SDA
CREATE TABLE #MuNoAdolfo
(mukey CHAR(30), soilgeom geometry);
SELECT @partitionNumber = 0;
INSERT INTO #MuNoAdolfo (mukey, soilgeom)
SELECT mukey, mupolygongeo.STAsText() AS soilgeom
FROM mupolygon
WHERE mukey IN (""" + (mukeys) + """) and (mukey % @numberOfPartitions) = @partitionNumber;
SELECT @partitionNumber = 1;
INSERT INTO #MuNoAdolfo (mukey, soilgeom)
SELECT mukey, mupolygongeo.STAsText() AS soilgeom
FROM mupolygon
WHERE mukey IN (""" + (mukeys) + """) and (mukey % @numberOfPartitions) = @partitionNumber;
SELECT @partitionNumber = 2;
INSERT INTO #MuNoAdolfo (mukey, soilgeom)
SELECT mukey, mupolygongeo.STAsText() AS soilgeom
FROM mupolygon
WHERE mukey IN (""" + (mukeys) + """) and (mukey % @numberOfPartitions) = @partitionNumber;
SELECT @partitionNumber = 3;
INSERT INTO #MuNoAdolfo (mukey, soilgeom)
SELECT mukey, mupolygongeo.STAsText() AS soilgeom
FROM mupolygon
WHERE mukey IN (""" + (mukeys) + """) and (mukey % @numberOfPartitions) = @partitionNumber;
SELECT @partitionNumber = 4;
INSERT INTO #MuNoAdolfo (mukey, soilgeom)
SELECT mukey, mupolygongeo.STAsText() AS soilgeom
FROM mupolygon
WHERE mukey IN (""" + (mukeys) + """) and (mukey % @numberOfPartitions) = @partitionNumber;
SELECT  mukey, soilgeom FROM #MuNoAdolfo
ORDER BY mukey"""

            dRequest = dict()
            dRequest["format"] = "JSON"
            dRequest["query"] = sdaQuery

            # Create SDM connection to service using HTTP
            jData = json.dumps(dRequest)

            try:
                # Send request to SDA Tabular service
                AddMsgAndPrint("1")
                req = urllib2.Request(sdaURL, jData)
                AddMsgAndPrint("2")
                resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
                AddMsgAndPrint("3")
                responseStatus = resp.getcode()
                AddMsgAndPrint("4")
                responseMsg = resp.msg
                AddMsgAndPrint("5")
                jsonString = resp.read()
                AddMsgAndPrint("6")
                resp.close()

                data = json.loads(jsonString) # dictionary containing 1 key with a list of lists
                return data

            except:
                AddMsgAndPrint("\n\tFailed ----------------- ")
                AddMsgAndPrint(str(mukeys))
                errorMsg()
                print "\n\n" + sdaQuery
                continue

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


## ===================================================================================
def geometryRequestTest(nasisMUKEYs):


    try:

        AddMsgAndPrint("Requesting Geometry Info from SDA")
        sdaURL = r"https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

        ## --------------------------------------------------------------------------------------------------------------------Method #1
        AddMsgAndPrint("\nMethod 1 ---------1 MUKEY at a time ------------------------------")

        startTime = tic()
        i =1
        for mukey in nasisMUKEYs:

            AddMsgAndPrint("\tRequesting MUKEY #: " + str(i))
            sdaQuery = """SELECT mukey, mupolygongeo.STAsText() AS wktgeom
                          FROM mupolygon
                          WHERE mukey = """ + mukey

            dRequest = dict()
            dRequest["format"] = "JSON"
            dRequest["query"] = sdaQuery

            # Create SDM connection to service using HTTP
            jData = json.dumps(dRequest)

            # Send request to SDA Tabular service
            req = urllib2.Request(sdaURL, jData)
            resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
            responseStatus = resp.getcode()
            responseMsg = resp.msg
            jsonString = resp.read()
            resp.close()

            try:
                data = json.loads(jsonString)

            except:
                errorMsg()

            i+=1

        AddMsgAndPrint(toc(startTime))

        ## --------------------------------------------------------------------------------------------------------------------Method #2
        AddMsgAndPrint("\nMethod 2 ---------send list of " + str(len(nasisMUKEYs)) + " MUKEYs ------------------------------")
        startTime = tic()

        mukeys = str(nasisMUKEYs).replace("[","").replace("]","").replace("'","")

        sdaQuery = """SELECT mukey, mupolygongeo.STAsText()
                      FROM mupolygon
                      WHERE mukey IN (""" + mukeys + """)"""

        dRequest = dict()
        dRequest["format"] = "JSON"
        dRequest["query"] = sdaQuery

        # Create SDM connection to service using HTTP
        jData = json.dumps(dRequest)

        # Send request to SDA Tabular service
        req = urllib2.Request(sdaURL, jData)
        resp = urllib2.urlopen(req)  # A failure here will probably throw an HTTP exception
        responseStatus = resp.getcode()
        responseMsg = resp.msg
        jsonString = resp.read()
        resp.close()

        try:
            data = json.loads(jsonString)

        except:
            errorMsg()

        AddMsgAndPrint(toc(startTime))

    except:
        errorMsg()
        return ""


## ===================================================================================
def parseMUKEYsByCount(listOfMUKEYs,feature="POLYGON"):
    """ This function takes in a list of MUKEYS and groups them
        based on maximum POLYGON or VERTICE thresholds so that SDA
        geometry requests are efficient and successful.
        POLYGON Threshold is set to 9,999 records
        VERTICE Threshold is set to 811,000 (determined by MUKEY: 2903473)

       MUKEY polygon and Vertice counts are collected from SDA and stored
       in a dictionary.  The MUKEYs are then sorted ascendingly by user-determined
       feature.  MUKEYs are then grouped by maximum feature threshold

       2 lists are returned"""

    try:
        if feauture == "POLYGON":
           countThreshold = 9999    # Max Polygon records per subList
           countFeatureID = 0
        elif feature == "VERTICE":
           countThreshold = 811000  # Max number Vertices per subList
           countFeatureID = 1
        else:
           AddMsgAndPrint("\n\t parseMUKEYsByCount ERROR -- Invalid feature type passed",2)
           return False

        # Dictionary of MUKEYs and number of features associated with that MUKEY
        # {'1544915': 337,'1544918': 7,'1544928': 4,'1544929': 8}
        mukeyDict = dict()

        # list of MUKEY subset lists that will be used to request SDA Geometry
        finalList = list()

        # list of MUKEYs that exceed vertice threshold.  This list needs to be
        # further evaluated by polygon.
        mukeysExceedThreshold = list()

        # List of MUKEYs that have no polygon geometry.  These are probably new
        # MUKEYs assigned by NASIS that are not available in SSURGO yet.
        mukeyNoPolygon = list()

        totalPolys = 0
        totalVertices = 0
        startTime = tic()

        """ ---------------------------------------------- Get Polygon and Vertice Counts from SDA -------------------------"""
        for mukey in listOfMUKEYs:

            polygonCountQuery = """SELECT COUNT(*) FROM mupolygon WHERE mukey = """ + mukey

            verticeCountQuery = """SELECT mukey, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                                   FROM mupolygon
                                   WHERE mukey = """ + mukey + """GROUP BY mukey"""

            polyAndVerticeCountQuery = """SELECT COUNT(*) AS polycount, SUM(mupolygongeo.STNumPoints()) AS vertex_count
                                          FROM mupolygon WHERE mukey = """ + mukey + """" GROUP BY mukey"""

            dRequest = dict()
            dRequest["format"] = "JSON"
            dRequest["query"] = polyAndVerticeCountQuery

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
                continue
                errorMsg()

            if not "Table" in data:
               AddMsgAndPrint("\tNo data returned for MUKEY: " + str(mukeyList),2)
               continue

            del polygonCountQuery,dRequest,jData,req,resp,jsonString

            # Tally up the counts
            mukeyPolyCount = int(data['Table'][0][0])
            mukeyVerticeCount = int(data['Table'][0][1])
            totalPolys += mukeyPolyCount
            totalVertices += mukeyVerticeCount

            # MUKEY has no polygons associated
            if not mukeyPolyCount > 0:
               mukeyNoPolygon.append(mukey)
               continue

            if not mukey in mukeyDict:
               mukeyDict[mukey] = mukeyPolyCount

        """ -------------------------------------- Sort MUKEYs by Polygon or Vertice Counts -------------------------------"""
        # sort the mukeyDict based on polygon or vertice count; converts the dictionary into a tuple
        # by default since a dictionary cannot be reordered.
        if len(mukeyDict):
           sortedMUKEYbyCount = sorted(mukeyDict.items(), key=lambda polyInfo: polyInfo[1][countFeatureID])

           tempMUKEYList = list()
           tempFeatureCount = 0
           validMukeys = 0

           for val in sortedMUKEYbyCount:
               mukey = val[0]
               featureCount = val[1][countFeatureID]

               # individual feature exceeds threshold.  If vertice count exceeds 811,000 it
               # needs to be handled differently.
               if featureCount > countThreshold and countFeatureID == 1:
                  mukeysExceedThreshold.append(mukey)
                  continue

               # total feature count is still under threshold; Add MUKEY to the tempMUKEYList
               if not (featureCount + tempFeatureCount) > countThreshold:
                  tempMUKEYList.append(mukey)
                  validMukeys+=1
                  tempFeatureCount+=featureCount

               # feature count will exceed threshold; Do not add
               # anymore MUKEYs to the list.  Add current list of
               # MUKEYs to final list and clear the tempList
               else:
                   finalList.append(tempMUKEYList)

                   tempMUKEYList = list()
                   tempMUKEYList.append(mukey)
                   validMukeys+=1
                   tempFeatureCount = featureCount

               # this is the last record; add it
               if mukey == sortedMUKEYbyCount[-1][0] and len(tempMUKEYList):
                  finalList.append(tempMUKEYList)

               del mukey,featureCount

        # Make sure all MUKEYs were accounted; Number of valid MUKEYs processed and
        # MUKEYs with no polygons should be the same as the # of MUKEYs submitted
        if not len(mukeyDict) == validMukeys + len(mukeyNoPolygon):
           AddMsgAndPrint("\tThere is a discrepancy with the number of NASIS Project MUKEYs:",2)
           AddMsgAndPrint("\t\tOriginal Number of MUKEYs: " + str(len(mukeyDict)),2)
           AddMsgAndPrint("\t\tProcessed Number of MUKEYS: " + str(validMukeys),2)
           AddMsgAndPrint("\t\tNumber of MUKEYS with no polygons: " + str(len(mukeyNoPolygon)),2)

        if len(mukeyNoPolygon):
           AddMsgAndPrint("\tThere are " + str(len(mukeyNoPolygon)) + " MUKEYs with no geometry data available",1)

        if not len(finalList):
           AddMsgAndPrint("\t\tSorting MUKEYS by " + feature + " Failed.  Empty Final List",2)
           return False

        AddMsgAndPrint("\tTotal " + feature + " Count: " + (splitThousands(totalPolys) if countFeatureID == 0 else splitThousands(totalVertices)))

        return finalList

    except:
        errorMsg()

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
                   #AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
                   #AddMsgAndPrint("t\t" + str(request))
                   pass
                elif int(e.code) >= 400:
                   #AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
                   #AddMsgAndPrint("\t\t" + getGeometryQuery)
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
## ===================================================================================


## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, traceback, operator
import urllib, urllib2, re, time, json
import arcgisscripting, arcpy
from arcpy import env
from sys import getsizeof, stderr
from itertools import chain

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

            listOfMUKEYs = ['2903473','1715499','346259','522','2738636','3114927','397315', '397276', '428128', '401319','2798206', '357379', '352266','2920731']
            reportSDAgeometryInfoByMUKEY(listOfMUKEYs)
            exit()

##            testList = [['346928']]
##            data = geometryRequestByMUKEYLists_Phil(testList)
##            exit()

            testList = [['2903473']]
            data = geometryRequestByMUKEYLists(testList)
            exit()

            polyList,verticeList = jsonSDAverticeTest()
            exit()

            # get a list of MUKEYs for NASIS project
            nasisMUKEYs = getNasisMukeys(prjMapunit_URL, project)

            nasisProjectFC = createOutputFC()
            if not nasisProjectFC: continue

            if len(nasisMUKEYsSorted):
                if not geometryRequestByMUKEY(nasisMUKEYsSorted):
                   AddMsgAndPrint("WTF",2)

                #someDict = geometryRequestByMUKEY(nasisMUKEYs)
                #AddMsgAndPrint(str(nasisMUKEYs),1)

        AddMsgAndPrint("\n",0)

except ExitError, e:
    AddMsgAndPrint(str(e) + "\n", 2)

except:
    errorMsg()