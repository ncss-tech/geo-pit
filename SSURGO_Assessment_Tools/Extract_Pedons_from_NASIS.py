#-------------------------------------------------------------------------------
# Name:        Extract Pedons from NASIS
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     7/04/2016
# Last Modified: 9/27/2016
# Copyright:   (c) Adolfo.Diaz 2016
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

## ================================================================================================================
def createPedonFGDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to that of the access database.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        AddMsgAndPrint("\nCreating New Pedon File Geodatabase",0)

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "Extract_Pedons_from_NASIS_XMLWorkspace.xml"

        # Return false if xml file is not found and delete targetGDB
        if not arcpy.Exists(pedonXML):
            AddMsgAndPrint("\t" + os.path.basename(pedonXML) + "Workspace document was not found!",2)
            return ""

        newPedonFGDB = os.path.join(outputFolder,GDBname + ".gdb")

        if arcpy.Exists(newPedonFGDB):
            try:
                arcpy.Delete_management(newPedonFGDB)
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Deleting and re-creating FGDB\n",1)
            except:
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Failed to delete\n",2)
                return False

        # Create empty temp File Geodatabae
        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])

        # set the pedon schema on the newly created temp Pedon FGDB
        AddMsgAndPrint("\tImporting NCSS Pedon Schema 7.1 into " + GDBname + ".gdb")
        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "SCHEMA_ONLY", "DEFAULTS")

        arcpy.RefreshCatalog(outputFolder)

        AddMsgAndPrint("\tSuccessfully created: " + GDBname + ".gdb")

        return newPedonFGDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return ""

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return ""

## ================================================================================================================
def getBoundingCoordinates(feature):
    """ This function will return WGS coordinates in Lat-Long format that will be passed over to
        the 'WEB_EXPORT_PEDON_BOX_COUNT' report.  The coordinates are generated by creating
        a minimum bounding box around the input features.  The box is then converted to vertices
        and the SW Ycoord, NE Ycoord, SW Xcoord and NE Ycoord are return in that order.
        Geo-Processing Environments are set to WGS84 in order to return coords in Lat/Long."""

    try:

        AddMsgAndPrint("\nCalculating bounding coordinates of features",0)

        """ Set Projection and Geographic Transformation environments in order
            to post process everything in WGS84.  This will force all coordinates
            to be in Lat/Long"""

        inputSR = arcpy.Describe(feature).spatialReference                # Get Spatial Reference of input features
        inputDatum = inputSR.GCS.datumName                                # Get Datum name of input features

        if inputSR == "Unkown":
            AddMsgAndPrint("\tInput layer needs a spatial reference defined to determine bounding envelope",2)
            return False

        if inputDatum == "D_North_American_1983":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"
        elif inputDatum == "D_North_American_1927":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1927"
        elif inputDatum == "D_WGS_1984":
            arcpy.env.geographicTransformations = ""
        else:
            AddMsgAndPrint("\tGeo Transformation of Datum could not be set",2)
            return False

        # Factory code for WGS84 Coordinate System
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

        """ ------------ Create Minimum Bounding Envelope of features ------------"""
        envelope = arcpy.CreateScratchName("envelope",data_type="FeatureClass",workspace=scratchWS)
        envelopePts = arcpy.CreateScratchName("envelopePts",data_type="FeatureClass",workspace=scratchWS)

        # create minimum bounding geometry enclosing all features
        arcpy.MinimumBoundingGeometry_management(feature,envelope,"ENVELOPE","ALL","#","MBG_FIELDS")

        if int(arcpy.GetCount_management(envelope).getOutput(0)) < 1:
            AddMsgAndPrint("\tFailed to create minimum bounding area. \n\tArea of interest is potentially too small",2)
            return False

        arcpy.FeatureVerticesToPoints_management(envelope, envelopePts, "ALL")

        """ ------------ Get X and Y coordinates from envelope ------------"""
        coordList = []
        with arcpy.da.SearchCursor(envelopePts,['SHAPE@XY']) as cursor:
            for row in cursor:
                if abs(row[0][0]) > 0 and abs(row[0][1]) > 0:

                    # Don't add duplicate coords; Last coord will also be the starting coord
                    if not row[0] in coordList:
                        coordList.append(row[0])

        # Delete temp spatial files
        for tempFile in [envelope,envelopePts]:
            if arcpy.Exists(tempFile):
                arcpy.Delete_management(tempFile)

        if len(coordList) == 4:
            AddMsgAndPrint("\tBounding Box Coordinates:")
            AddMsgAndPrint("\t\tSouth Latitude: " + str(coordList[0][1]))
            AddMsgAndPrint("\t\tNorth Latitude: " + str(coordList[2][1]))
            AddMsgAndPrint("\t\tEast Longitude: " + str(coordList[0][0]))
            AddMsgAndPrint("\t\tWest Longitude: " + str(coordList[2][0]))
            return coordList[0][1],coordList[2][1],coordList[0][0],coordList[2][0]

        else:
            AddMsgAndPrint("\tCould not get Latitude-Longitude coordinates from bounding area",2)
            return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def getWebExportPedon(URL):
    """ This function will send the bounding coordinates to the 'Web Export Pedon Box' NASIS report
        and return a list of pedons within the bounding coordinates.  Pedons include regular
        NASIS pedons and LAB pedons.  Each record in the report will contain the following values:

            Row_Number,upedonid,peiid,pedlabsampnum,Longstddecimaldegrees,latstddecimaldegrees
            24|S1994MN161001|102861|94P0697|-93.5380936|44.0612717

        A dictionary will be returned containing something similar:
        {'102857': ('S1954MN161113A', '40A1694', '-93.6499481', '43.8647194'),
        '102858': ('S1954MN161113B', '40A1695', '-93.6455002', '43.8899956')}
        theURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&lat1=43&lat2=45&long1=-90&long2=-88'"""

    try:
        AddMsgAndPrint("\nRequesting a list of pedons from NASIS using bounding coordinates")

        totalPedonCnt = 0
        labPedonCnt = 0

        # Open a network object using the URL with the search string already concatenated
        theReport = urllib.urlopen(URL)

        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # removes whitespace characters

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "STOP":  # written as part of the report; end of lines
                    break

                # Found a valid project record i.e. -- SDJR - MLRA 103 - Kingston silty clay loam, 1 to 3 percent slopes|400036
                else:
                    theRec = theValue.split("|")

                    if len(theRec) != 6:
                        AddMsgAndPrint("\tNASIS Report: Web Export Pedon Box is not returning the correct amount of values per record",2)
                        return False

                    rowNumber = theRec[0]
                    userPedonID = theRec[1]
                    pedonID = theRec[2]

                    if theRec[3] == 'Null' or theRec[3] == '':
                        labSampleNum = None
                    else:
                        labSampleNum = theRec[3]
                        labPedonCnt += 1

                    longDD = theRec[4]
                    latDD = theRec[5]

                    if not pedonDict.has_key(pedonID):
                        pedonDict[pedonID] = (userPedonID,labSampleNum,longDD,latDD)
                        totalPedonCnt += 1

            else:
                if theValue.startswith('<div id="ReportData">START'):
                    bValidRecord = True

        if len(pedonDict) == 0:
            AddMsgAndPrint("\tThere were no pedons found in this area; Try using a larger extent",1)
            return False

        else:
            AddMsgAndPrint("\tThere are a total of " + str(totalPedonCnt) + " pedons found in this area:")
            AddMsgAndPrint("\t\tLAB Pedons: " + str(labPedonCnt))
            AddMsgAndPrint("\t\tNASIS Pedons: " + str(totalPedonCnt - labPedonCnt))
            return True

    except:
        errorMsg()
        return False

## ================================================================================================================
def getPedonHorizonOLD(URL):
    """ Example of phorizon report for 1 pedon:
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>
        </title><link href="basepage.css" rel="stylesheet" type="text/css" />
        	<title></title>
        </head>
        <body>
        	<form name="aspnetForm" method="post" action="./limsreport.aspx?report_name=TEST_sub_pedon_pc_6.1_phorizon&amp;pedonid_list=36186" id="aspnetForm">
        <input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPDwUKLTM2NDk4NDg3MA9kFgJmD2QWAgIDD2QWAgIBD2QWAgIDDw8WAh4HVmlzaWJsZWdkZGSXwAn7Hr8Ukd9anjbL9XSl6aCmiPociSQIHE2w0AyWNg==" />
        <input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="DCF944DC" />
        	<div>
        	<div id="ctl00_ContentPlaceHolder1_pnlReportOutput">
        	<div id="ReportData">@begin phorizon
        seqnum,obsmethod,hzname,hzname_s,desgndisc,desgnmaster,desgnmasterprime,
        1,,"A",,,,,,0,28,,,,"GR-L",1,0,,,,,,,,0,,,,3,,,,,,,,,,,,,,,7.2,14,,,,,,,,,,       ------ START Here
        2,,"Bw",,,,,,28,36,,,,"GR-L",1,0,,,,,,,,0,,,,3,,,,,,,,,,,,,,,7.8,14,,3,,,,,
        3,,"C",,,,,,36,152,,,,"GRV-S GRV-LS",1,0,,,,,,,,0,,,,1,,,,,,,,,,,,,,,8.0,14
        @end                                                                              ------- PAUSE Here
        desgnvert,hzdept,hzdepb,hzthk_l,hzthk_r,hzthk_h,texture,texture_s,                ------- PAUSE Here
        ,,,,,,0,2,4,,,,,,,36186,166637
        ,,,,,,,,,0,1,4,,,,,,,36186,166638
        ,,3,,,,,,,,,,,,,,0,,,,,,,,,36186,166639
        stratextsflag,claytotest,claycarbest,silttotest,sandtotest,carbdevstagefe,        ------- STOP Here
        carbdevstagecf,fragvoltot,horcolorvflag,fiberrubbedpct,fiberunrubbedpct,
        obssoimoiststat,rupresblkmst,rupresblkdry,rupresblkcem,rupresplate,
        mannerfailure,stickiness,plasticity,toughclass,penetrres,penetorient,
        ksatpedon,ksatstddev,ksatrepnum,horzpermclass,obsinfiltrationrate,phfield,
        phdetermeth,phnaf,effclass,efflocation,effagent,mneffclass,mneffagent,
        reactadipyridyl,dipyridylpct,dipyridylloc,ecmeasured,ecdeterminemeth,ec15,
        excavdifcl,soilodor,soilodorintensity,rmonosulfidep,bounddistinct,boundtopo
        ,horzvoltotpct_l,horzvoltotpct_r,horzvoltotpct_h,horzlatareapct_l,
        horzlatareapct_r,horzlatareapct_h,peiidref,phiid
        </div>
        </div>
        	</div>
        	</form>
        </body>
        </html>
        """
    try:

        # Open a network object using the URL with the search string already concatenated
        theReport = urllib.urlopen(URL)

        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project
        bFirstString = False
        bSecondString = False
        pHorizonList = list()
        i = 0

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # remove whitespace characters

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue.startswith('</div>'):  # this report doesn't really have a hard stop or stopping indicator.
                    break

                # The line after this is where the first half of data begins
                elif theValue.startswith("seqnum,obsmethod,hzname"):
                    bFirstString = True
                    continue

                # benchmark indicators of when to stop appending to pHorizonlist
                elif theValue.startswith(("@end","stratextsflag,claytotest,claycarbest,silttotest")):
                    bFirstString = False
                    bSecondString = False
                    continue

                # The line after this is where the second half of data begins
                elif theValue.startswith("desgnvert,hzdept,hzdepb,hzthk_l"):
                    bSecondString = True
                    continue

                # Add the first set of pHorizon data to the pHorizonList
                elif bFirstString:
                    tempList = list()

                    for val in theValue.split(","):
                        if val is None:
                            tempList.append(None)
                        else:
                            tempList.append(val.strip("\""))

                    pHorizonList.append(tempList)
                    del tempList

                # Add the second set of pHorizon data to the last list in pHorizonList
                elif bSecondString:

                    for val in theValue.split(","):
                        if val is None:
                            pHorizonList[i].append(None)
                        else:
                            pHorizonList[i].append(val.strip("\""))

                    i+=1
                    if i+1 == len(pHorizonList):
                        break

            else:
                # This is where the real report starts; earlier lines are html fluff
                if theValue.startswith('<div id="ReportData">@begin phorizon'):
                    bValidRecord = True

        if not pHorizonList:
            AddMsgAndPrint("\tThere were no Pedon Horizon records returned from the web report",2)
            return False
        else:
            AddMsgAndPrint("\tThere are " + str(len(pHorizonList)) + " pedon horizon records that will be added",0)

        del theReport,bValidRecord,bFirstString,bSecondString,pHorizonList,i
        return True

    except:
        errorMsg()
        return False

## ================================================================================================================
def getPedonHorizon(URL):

    """ Example of phorizon report for 1 pedon:
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>
        </title><link href="basepage.css" rel="stylesheet" type="text/css" />
        <title></title>
        </head>
        <body>
        <form name="aspnetForm" method="post" action="./limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&amp;pedonid_list=36186" id="aspnetForm">
        <input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPDwUKLTM2NDk4NDg3MA9kFgJmD2QWAgIDD2QWAgIBD2QWAgIDDw8WAh4HVmlzaWJsZWdkZGSw4UyY2tA6B555egB7tpATxNUfl13LgVfcZNwmy2YnRQ==" />
        <input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="DCF944DC" />
        <div>
        <div id="ctl00_ContentPlaceHolder1_pnlReportOutput">
        <div id="ReportData">@begin site
        siteiid,siteuid,usiteid,latdegrees,latminutes,latseconds,latdir,latdir_s,longdegrees,longminutes,longseconds,longdir,longdir_s,horizdatnm,horizdatnm_s,locdesc,plsssdetails,plsssection,plsstownship,plssrange,plssmeridian,utmzone,utmnorthing,utmeasting,elev,geomposhill,geomposmntn,geompostrce,geomposflats,hillslopeprof,geomslopeseg,slope,aspect,slopelenusle,shapeacross,shapedown,slopecomplex,locphysnm,geoform,bedrckdepth,bedrckkind,bedrckhardness,bedrckfractint,bedrckweather,bedrckstrike,bedrckdip_h,bedrckdip_l,drainagecl,siteperm,runoff,pmgroupname,plantassocnm,climstaid,climstanm,climstatype,ffd,map,reannualprecip,airtempa,soiltempa,airtemps,soiltemps,airtempw,soiltempw,flodfreqcl,floddurcl,flodmonthbeg,pondfreqcl,ponddurcl,pondmonthbeg,wtabledur,sdbsidref,sdbiidref,grpiidref,useriidref,wlupdated
        36242,36242,"94IL111028",42,18,45.00,1,"North",88,13,43.00,2,"West",1,"North American Datum of 1927","500 feet south and 2,600 feet east of the northwest corner of sec. 7, T. 44 N., R. 9 E.",,,,,,,,,229.0,"Side Slope",,,,"Backslope",,27.0,270,,"Linear","Linear",,,,,,,,,,,,"Excessively drained","Very rapid","Very high",,,,,,,,,,,,,,,,,,,,,,139,139,1298,1237,8/14/2013 2:46:24 AM
        @end
        @begin siteobs
        seqnum,obsdate,obsdatekind,photoid,swaterkind,swaterdepth,geomicrorelief,geommicelev,geommicpat,yldstudyid,sdbsidref,siteiidref,siteobsiid,siteobsuid
        ,"10/14/1994 12:00:00 AM","Actual Site Observation Date","BXA-2-41",,,,,,,139,36242,36165,36165
        @end
        @begin siteerosionacc
        seqnum,erokind,sdbsidref,siteobsiidref,siteeroacciid
        ,"Water erosion",139,36165,4703
        @end
        @begin siteexistveg
        seqnum,lplantdbsidref,lplantiidref,sdbsidref,siteobsiidref,siteexistvegiid,lplantuidref
        @end
        @begin sitegeomordesc
        seqnum,geomftdbsidref,geomftname,geofname,geomfmod,geomfeatid,existsonfeat,sdbsidref,siteiidref,sitegeomdiid
        ,1,"Landform","kame terrace",,,,139,36242,52245
        @end
        @begin siteobstext
        seqnum,recdate,recauthor,siteobstextkind,textcat,textsubcat,text,sdbsidref,siteobsiidref,siteobstextiid
        @end
        @begin siteaoverlap
        seqnum,atdbsidref,areatypename,areaname,sdbsidref,siteiidref,sareaoviid
        ,1,"Non-MLRA Soil Survey Area","La Salle County, Illinois",139,36242,1050900
        ,1,"Non-MLRA Soil Survey Area","McHenry County, Illinois",139,36242,1050901
        ,1,"Country","United States",139,36242,1050899
        @end
        @begin sitemuoverlap
        seqnum,musym,muname,sdbsidref,sareaoviidref,smuoviid
        ,"969F","Casco-Rodman complex, 20 to 30 percent slopes",139,36242,124012
        @end
        @begin sitepm
        seqnum,pmorder,pmmodifier,pmgenmod,pmkind,pmorigin,pmweathering,sdbsidref,siteiidref,sitepmiid
        @end
        @begin sitesoilmoist
        seqnum,soimoistdept,soimoistdepb,obssoimoiststat,obssoimoist,soimoistten,sdbsidref,siteobsiidref,sitesmiid
        @end
        @begin sitesoiltemp
        seqnum,soitempdep,soitemp,sdbsidref,siteobsiidref,sitestiid
        @end
        @begin sitetext
        seqnum,recdate,recauthor,sitetextkind,textcat,textsubcat,text,sdbsidref,siteiidref,sitetextiid
        ,"9/5/2000 12:00:00 AM",,"Conversion problem",,,"Obsolete Landscape: Glaciofluvial Landform *
        Obsolete Landuse: forest land not grazed
        Invalid county symbol and name combination
        County symbol:  County name: McHenry
        Invalid Quad Name: 42088C2
        Invalid SSA symbol and name combination
        SSA symbol: 111 SSA name: McHenry",139,36242,71202
        ,"9/5/2000 12:00:00 AM",,"Pedon conversion","Map Unit Symbol/Name",,"Map Unit Symbol: 93F
        Map Unit Name:   Rodman gravelly loam, 20 to 30 percent slopes",139,36242,71352
        ,"4/6/2012 12:00:00 AM","Tonie Endres","Miscellaneous notes",,,"Site ownership changed from Illinois 108A_108B Shared to 11-04 Aurora MLRA in order to assign ownership to an established MLRA SSO.",139,36242,494955
        @end
        @begin transect
        tsectdbsidref,tsectiid,utransectid,tsectauth,tsectkind,tsectselmeth,tsectdelinsize,tsectdir,tsectdbiidref,grpiidref,useriidref,wlupdated,tsectuid
        @end
        @begin transecttext
        seqnum,recdate,recauthor,transecttextkind,textcat,textsubcat,text,tsectdbsidref,tsectiidref,transecttextiid
        @end
        @begin pediagfeatures
        seqnum,featkind,featdept,featdepb,featthick_l,featthick_r,featthick_h,pedbsidref,peiidref,pediagfeatiid
        @end
        @begin pefmp
        seqnum,fmpname,fmpvalue,fmpunits,pedbsidref,peiidref,pefmpiid
        @end
        @begin pedon
        upedonid,pedrecorigin,descname,sdbsidref,siteiidref,siteobsiidref,tsectdbsidref,tsectiidref,tsectstopnum,tsectinterval,soinmassamp,soinmascorr,compkind,pedontype,pedonpurpose,pedonunit,relexpsize,relexpuom,earthcovkind1,earthcovkind2,erocl,taxclname,taxorder,taxsuborder,taxgrtgroup,taxsubgrp,taxpartsize,taxpartsizemod,taxceactcl,taxreaction,taxtempcl,taxmoistscl,taxtempregime,soiltaxedition,psctopdepth,pscbotdepth,currweathcond,currairtemp,labsourceid,pedlabsampnum,pedbiidref,grpiidref,useriidref,wlupdated,pedbsidref,peiid,peuid,siteobsuidref,tsectuidref
        "94IL111028","Converted from PDP 3.x","JAD, DEC",139,36242,36165,,,,,"Rodman","Rodman",,,"Full pedon description",,,,,,"Class 1","Sandy-skeletal, mixed, mesic Typic Hapludolls","Mollisols","Udolls","Hapludolls","Typic Hapludolls","sandy-skeletal",,,,"mesic",,"mesic","tenth edition",,,,,,,139,1298,1216,4/6/2012 11:42:51 AM,139,36186,36186,36165,
        @end
        @begin perestrictions
        seqnum,reskind,reshard,resdept,resdepb,resthk_l,resthk_r,resthk_h,pedbsidref,peiidref,perestrictiid
        @end
        @begin pesurffrags
        seqnum,sfragcov,distrocks,sfragkind,sfragsize_l,sfragsize_r,sfragsize_h,sfragshp,sfraground,sfraghard,pedbsidref,peiidref,pesurffragsiid
        @end
        @begin petaxfmmin
        seqnum,taxminalogy,pedbsidref,peiidref,petaxfmminiid
        ,"mixed",139,36186,32434
        @end
        @begin petxfmother
        seqnum,taxfamother,pedbsidref,peiidref,petaxfoiid
        @end
        @begin petaxmoistcl
        seqnum,taxmoistcl,pedbsidref,peiidref,petaxmciid
        ,"Udic",139,36186,33763
        @end
        @begin petext
        seqnum,recdate,recauthor,pedontextkind,textcat,textsubcat,text,pedbsidref,peiidref,petextiid
        ,4/6/2012 12:00:00 AM,"Tonie Endres","Miscellaneous notes",,,"Pedon ownership changed from Illinois 108A_108B Shared to 11-04 Aurora MLRA PO in order to assign ownership to an established MLRA SSO.",139,36186,511099
        @end
        @begin phcemagent
        seqnum,ruprescem,pedbsidref,phiidref,phcemagentiid
        @end
        @begin phcolor
        seqnum,colorpct,colorphysst,colorhue,colorvalue,colorchroma,colormoistst,pedbsidref,phiidref,phcoloriid
        1,,,"10YR","3","1","Moist",139,166637,220346
        2,,,"10YR","4","2","Dry",139,166637,220347
        2,50,,"10YR","4","3","Moist",139,166638,220335
        1,50,,"10YR","3","3","Moist",139,166638,220348
        1,,,"10YR","4","4","Moist",139,166639,220336
        @end
        @begin phconccolor
        seqnum,colorpct,colorhue,colorvalue,colorchroma,colormoistst,pedbsidref,phconceniidref,phconcencoloriid
        @end
        @begin phconcs
        seqnum,concpct,concsize,conccntrst,conchardness,concshape,conckind,conclocation,concboundary,pedbsidref,phiidref,phconceniid
        @end
        @begin phdesgnsuffix
        seqnum,desgnsuffix,pedbsidref,phiidref,phdesgnsfxiid
        @end
        @begin phfeatures
        seqnum,horfeatkind,horfeatvtpct_l,horfeatvtpct_r,horfeatvtpct_h,horfeatlapct_l,horfeatlapct_r,horfeatlapct_h,pedbsidref,phiidref,phfeatsiid
        @end
        @begin phfeatcolor
        seqnum,colorpct,colorhue,colorvalue,colorchroma,colormoistst,pedbsidref,phfeatiidref,phfeatcoloriid
        @end
        @begin phfmp
        seqnum,fmpname,fmpvalue,fmpunits,pedbsidref,phiidref,phfmpiid
        @end
        @begin phfrags
        seqnum,fragvol,fragkind,fragsize_l,fragsize_r,fragsize_h,fragshp,fraground,fraghard,pedbsidref,phiidref,phfragsiid
        1,17.0,,2,39,75,,,,139,166637,26160
        1,25.0,,2,39,75,,,,139,166638,26161
        1,50.0,,2,39,75,,,,139,166639,26162
        @end
        @begin phmottles
        seqnum,mottlepct,mottlesize,mottlecntrst,colorhue,colorvalue,colorchroma,mottleshape,colormoistst,mottleloc,pedbsidref,phiidref,phmottlesiid
        @end
        @begin phpores
        seqnum,poreqty,poresize,porecont,poreshp,pedbsidref,phiidref,phporesiid
        @end
        @begin phpvsf
        seqnum,pvsfpct,pvsfdistinct,pvsfcont,pvsfkind,pvsflocation,pedbsidref,phiidref,phpvsfiid
        1,50,"Distinct",,"Organic stains","On faces of peds",139,166638,57799
        @end
        @begin phpvsfcolor
        seqnum,colorpct,colorhue,colorvalue,colorchroma,colormoistst,pedbsidref,phpvsfiidref,phpvsfcoloriid
        ,,"10YR","3","2",,139,57799,33932
        @end
        @begin phrdxfeatures
        seqnum,rdxfeatpct,rdxfeatsize,rdxfeatcntrst,rdxfeathardness,rdxfeatshape,rdxfeatkind,rdxfeatlocation,rdxfeatboundary,pedbsidref,phiidref,phrdxfiid
        @end
        @begin phroots
        seqnum,rootsquantity,rootssize,rootslocation,pedbsidref,phiidref,phrootsiid
        1,14.0,"Very fine and fine",,139,166637,52228
        1,4.0,"Very fine",,139,166638,52241
        1,2.0,"Very fine",,139,166639,51616
        @end
        @begin phsample
        seqnum,labsampnum,pedbsidref,phiidref,phlabsampiid
        @end
        @begin phstructure
        seqnum,structgrade,structsize,structtype,structid,structpartsto,pedbsidref,phiidref,phstructureiid
        2,"Strong","Fine and medium","Granular",,,139,166637,176463
        2,"Weak","Fine","Granular",,,139,166638,176464
        2,,,"Single grain",,,139,166639,176465
        @end
        @begin phtext
        seqnum,recdate,recauthor,phorizontextkind,textcat,textsubcat,text,pedbsidref,phiidref,phtextiid
        @end
        </div>
        </div>
        </div>
        </form>
        </body>
        </html>"""

    try:

        # Open a network object using the URL with the search string already concatenated
        theReport = urllib.urlopen(URL)

        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project
        bFirstString = False
        bSecondString = False
        pHorizonList = list()
        i = 0

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # remove whitespace characters

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue.startswith('</div>'):  # this report doesn't really have a hard stop or stopping indicator.
                    break

                # The line after this is where the first half of data begins
                elif theValue.startswith("seqnum,obsmethod,hzname"):
                    bFirstString = True
                    continue

                # benchmark indicators of when to stop appending to pHorizonlist
                elif theValue.startswith(("@end","stratextsflag,claytotest,claycarbest,silttotest")):
                    bFirstString = False
                    bSecondString = False
                    continue

                # The line after this is where the second half of data begins
                elif theValue.startswith("desgnvert,hzdept,hzdepb,hzthk_l"):
                    bSecondString = True
                    continue

                # Add the first set of pHorizon data to the pHorizonList
                elif bFirstString:
                    tempList = list()

                    for val in theValue.split(","):
                        if val is None:
                            tempList.append(None)
                        else:
                            tempList.append(val.strip("\""))

                    pHorizonList.append(tempList)
                    del tempList

                # Add the second set of pHorizon data to the last list in pHorizonList
                elif bSecondString:

                    for val in theValue.split(","):
                        if val is None:
                            pHorizonList[i].append(None)
                        else:
                            pHorizonList[i].append(val.strip("\""))

                    i+=1
                    if i+1 == len(pHorizonList):
                        break

            else:
                # This is where the real report starts; earlier lines are html fluff
                if theValue.startswith('<div id="ReportData">@begin phorizon'):
                    bValidRecord = True

        if not pHorizonList:
            AddMsgAndPrint("\tThere were no Pedon Horizon records returned from the web report",2)
            return False
        else:
            AddMsgAndPrint("\tThere are " + str(len(pHorizonList)) + " pedon horizon records that will be added",0)

        del theReport,bValidRecord,bFirstString,bSecondString,pHorizonList,i
        return True

    except:
        errorMsg()
        return False

#===================================================================================================================================
""" ----------------------------------------My Notes -------------------------------------------------"""

""" --------------- Column Headers
Column order
1.	Row_Number2,
2.	upedonid,
3.	peiid,
4.	pedlabsampnum,
5.	longstddecimaldegrees ,
6.	latstddecimaldegrees
                    ----------------------"""

""" 1st Report """
# Used to get a list of peiid which will be passed over to the 2nd report0
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&lat1=43&lat2=45&long1=-90&long2=-88

""" 2nd Report """
# This report will contain pedon information to be parsed into a FGDB.

# Raw URL
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=TEST_sub_pedon_pc_6.1_phorizon&pedonid_list=    OLD one
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=    NEW one

# Sample complete URL with pedonIDs:
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186,59976,60464,60465,101219,102867,106105,106106
#===================================================================================================================================


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    #inputFeatures = arcpy.GetParameter(0)
    inputFeatures = r'O:\scratch\scratch.gdb\Pedon_boundary_Test'
    GDBname = arcpy.GetParameter(1)
    outputFolder = arcpy.GetParameterAsText(2)

    """ ------------------------------------- Set Scratch Workspace -------------------------------------------"""
    scratchWS = setScratchWorkspace()
    arcpy.env.scratchWorkspace = scratchWS

    if not scratchWS:
        raise ExitError, "\n Failed to scratch workspace; Try setting it manually"


    """ ---------------------------------------------- Get Bounding box coordinates -------------------------------------------"""
    #Lat1 = 43.8480050291613;Lat2 = 44.196269661256736;Long1 = -93.76788085724957;Long2 = -93.40649833646484
    Lat1,Lat2,Long1,Long2 = getBoundingCoordinates(inputFeatures)

    if not Lat1:
        raise ExitError, "\nFailed to acquire Lat/Long coordinates to pass over; Try a new input feature"


    """ ---------------------------- Get a list of PedonIDs that are within the bounding box from NASIS -----------------------"""
    coordStr = "&Lat1=" + str(Lat1) + "&Lat2=" + str(Lat2) + "&Long1=" + str(Long1) + "&Long2=" + str(Long2)
    getPedonIDURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordStr

    #{'122647': ('84IA0130011', '85P0558', '-92.3241653', '42.3116684'), '883407': ('2014IA013003', None, '-92.1096600', '42.5332000'), '60914': ('98IA013011', None, '-92.4715271', '42.5718880')}
    pedonDict = dict()

    if not getWebExportPedon(getPedonIDURL):
        raise ExitError, "\t Failed to get a list of pedonIDs from NASIS"


    """ ------------------------------------- Get Pedon information using 2nd report -------------------------------"""
    i = 1  ## Total Count
    j = 1  ## Intermediate Count
    pedonIDstr = ""
    getPedonHorizonURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list="

    AddMsgAndPrint("\nRequesting pedon horizon information")

##    requestNum = 0
##    urlLength = 123
##    i=1
##    for pedonID in pedonDict:
##        if urlLength < 1860:
##            urlLength += len(pedonID) + 1;i+=1
##        elif i == len(pedonDict) or urlLength > 1860:
##            requestNum +=1;urlLength = 123

    # There is an inherent URL character limit of 2,083.  The report URL is 123 characters long which leaves 1,960 characters
    # available. I arbitrarily chose to have a max URL of 1,860 characters long to avoid problems.  Most pedonIDs are about
    # 6 characters.  This would mean an average max request of 265 pedons at a time.
    for pedonID in pedonDict:

        ## End of pedon list has been reached
        if i == len(pedonDict):
            pedonIDstr = pedonIDstr + str(pedonID)

        else:
            ## Max URL length reached - retrieve pedon data and start over
            if len(pedonIDstr) > 1860:
                pedonIDstr = pedonIDstr + str(pedonID)

                if not getPedonHorizon(getPedonHorizonURL + pedonIDstr):
				    raise ExitError, "\t Failed to receive pedon horizon info from NASIS"

                pedonIDstr = ""
                i+=1;j=1

            ## concatenate pedonID to string and continue
            else:
                pedonIDstr = pedonIDstr + str(pedonID) + ",";i+=1;j+=1

##    getPedonHorizonURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=" + pedonIDstr
##    AddMsgAndPrint("\nLength of characters for URL: " + str(len(getPedonHorizonURL)),1)
##    AddMsgAndPrint("\n\n\n" + getPedonHorizonURL + "\n\n\n")
##    pedonInfoDict = dict()
##
##    if not getPedonHorizon(getPedonHorizonURL):
##        raise ExitError, "\t Failed to receive pedon horizon info from NASIS"

##    """ ---------------------------------------------- Create New File Geodatabaes --------------------------------------------
##        This should only be invoked if there are pedons in the report."""
##    pedonFGDB = createPedonFGDB()
##
##    if pedonFGDB == "":
##        raise ExitError, "\n Failed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!"


