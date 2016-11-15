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
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

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
                return ""

        # Create empty temp File Geodatabae
        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])

        # set the pedon schema on the newly created temp Pedon FGDB
        AddMsgAndPrint("\tImporting NCSS Pedon Schema 7.3 into " + GDBname + ".gdb")
        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "DATA", "DEFAULTS")

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

## ===============================================================================================================
def getTableAliases(pedonFGDBloc):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores physical names (key) and aliases (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}
    # Fieldnames are Physical Name = AliasName,IEfilename

    try:

        # Open Metadata table containing information for other pedon tables
        theMDTable = pedonFGDBloc + os.sep + "MetadataTable"
        arcpy.env.workspace = pedonFGDBloc

        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if not arcpy.Exists(theMDTable):
            return False

        tableList = arcpy.ListTables("*")
        tableList.append("site")

        nameOfFields = ["TablePhysicalName","TableLabel"]

        for table in tableList:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            expression = arcpy.AddFieldDelimiters(theMDTable,"TablePhysicalName") + " = '" + table + "'"
            with arcpy.da.SearchCursor(theMDTable,nameOfFields, where_clause = expression) as cursor:

                for row in cursor:
                    # read each table record and assign 'TablePhysicalName' and 'TableLabel' to 2 variables
                    physicalName = row[0]
                    aliasName = row[1]

                    # i.e. {phtexture:'Pedon Horizon Texture',phtexture}; will create a one-to-many dictionary
                    # As long as the physical name doesn't exist in dict() add physical name
                    # as Key and alias as Value.
                    if not tblAliases.has_key(physicalName):
                        tblAliases[physicalName] = aliasName

                    del physicalName,aliasName

        del theMDTable,tableList,nameOfFields

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (GetTableAliases)", 2)
        errorMsg()
        return False

## ================================================================================================================
def getBoundingCoordinates(feature):
    """ This function will return WGS coordinates in Lat-Long format that will be passed over to
        the 'WEB_EXPORT_PEDON_BOX_COUNT' report.  The coordinates are generated by creating
        a minimum bounding box around the input features.  The box is then converted to vertices
        and the SW Ycoord, NE Ycoord, SW Xcoord and NE Ycoord are return in that order.
        Geo-Processing Environments are set to WGS84 in order to return coords in Lat/Long."""

    try:

        AddMsgAndPrint("\nCalculating bounding coordinates of input features",0)

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

            Row_Number,upedonid,peiid,pedlabsampnum,Longstddecimaldegrees,latstddecimaldegrees,Undisclosed Pedon
            24|S1994MN161001|102861|94P0697|-93.5380936|44.0612717|'Y'

        A dictionary will be returned containing something similar:
        {'102857': ('S1954MN161113A', '40A1694', '-93.6499481', '43.8647194',Y'),
        '102858': ('S1954MN161113B', '40A1695', '-93.6455002', '43.8899956','N')}
        theURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&lat1=43&lat2=45&long1=-90&long2=-88'"""

    try:
        AddMsgAndPrint("\nRequesting a list of pedonIDs from NASIS using the above bounding coordinates")

        totalPedonCnt = 0
        labPedonCnt = 0

        # Open a network object using the URL with the search string already concatenated
        theReport = urlopen(URL)

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

                    if len(theRec) != 7:
                        AddMsgAndPrint("\tNASIS Report: Web Export Pedon Box is not returning the correct amount of values per record",2)
                        return False

                    # Undisclosed Record
                    if theRec[6] == "Y":continue

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
            AddMsgAndPrint("\tThere are a total of " + splitThousands(totalPedonCnt) + " pedons found in this area:")
            AddMsgAndPrint("\t\tLAB Pedons: " + splitThousands(labPedonCnt))
            AddMsgAndPrint("\t\tNASIS Pedons: " + splitThousands(totalPedonCnt - labPedonCnt))
            return True

    except URLError, e:
        if hasattr(e, 'reason'):
            AddMsgAndPrint("\n\t" + URL)
            AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

        elif hasattr(e, 'code'):
            AddMsgAndPrint("\n\t" + URL)
            AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

        return False

    except socket.timeout, e:
        AddMsgAndPrint("\n\t" + URL)
        AddMsgAndPrint("\tServer Timeout Error", 2)
        return False

    except socket.error, e:
        AddMsgAndPrint("\n\t" + URL)
        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
        return False

    except httplib.BadStatusLine:
        AddMsgAndPrint("\n\t" + URL)
        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
        return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def getPedonHorizon(URL):

    # Here is an example of the output report

    """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head><title>

    </title><link href="basepage.css" rel="stylesheet" type="text/css" />
    <title></title>
    </head>
    <body>
    <form name="aspnetForm" method="post" action="./limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&amp;pedonid_list=858228" id="aspnetForm">
    <input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPDwUKLTM2NDk4NDg3MA9kFgJmD2QWAgIDD2QWAgIBD2QWAgIDDw8WAh4HVmlzaWJsZWdkZGSUb7I+zHdW44zIPCkM7ZFBSiDdf2H2sAAzb9wyFx83uQ==" />

    <input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="DCF944DC" />
    <div>


    <div id="ctl00_ContentPlaceHolder1_pnlReportOutput">

    <div id="ReportData">@begin ncsspedonlabdata
    pedlabsampnum,peiidref,psctopdepth,psctopdepth_s,pscbotdepth,pscbotdepth_s,noncarbclaywtavg,claytotwtavg,le0to100,wf0175wtavgpsc,volfractgt2wtavg,cec7clayratiowtavg,labdatasheeturl,ncsspedbiidref,grpiidref,objwlupdated,objuseriidref,recwlupdated,recuseriidref,ncsspedonlabdataiid
    @end
    @begin ncsslayerlabdata
    wtpctgt2ws,wtpct0175,fragwt2075,fragwt25,fragwt275,fragwt520,basesatnh4oac,cecsumcations,basesatsumcations,ncsspedonlabdataiidref,layerseqnum,labsampnum,hzdept,hzdepb,layertype,hzname,hznameoriginal,stratextsflag,moistprepstate,texcl,sandvcmeasured,sandcomeasured,sandmedmeasured,sandfinemeasured,sandvfmeasured,sandtotmeasured,siltcomeasured,siltfinemeasured,silttotmeasured,claycarbmeasured,clayfinemeasured,claytotmeasured,carbonorganicpctmeasured,carbontotalpctmeasured,ompctest,fiberrubbedpct,fiberunrubbedpct,ph1to1h2o,ph01mcacl2,phnaf,phoxidized,resistivity,ecmeasured,esp,sar,cec7,ecec,sumbases,caco3equivmeasured,caco3lt20measured,gypsumequivlt2measured,gypsumequivmeasured,feoxalatemeasured,feextractable,fetotal,sioxalatemeasured,extracid,extral,aloxalatemeasured,altotal,pmehlich3,ph2osolublemeasured,poxalatemeasured,polsenmeasured,ptotalmeasured,nzpretention,dbthirdbar,dbovendry,aggstabpct,wtenthbarclod,wtenthbarsieve,wthirdbarclod,wthirdbarsieve,wfifteenbarmeasured,wretentiondiffws,wfifteenbartoclay,adod,lep,cole,liquidlimitmeasured,pi,recwlupdated,recuseriidref,ncsslayerlabdataiid
    @end
    @begin site
    usiteid,latdegrees,latminutes,latseconds,latdir,longdegrees,longminutes,longseconds,longdir,horizdatnm,locdesc,plsssdetails,plsssection,plsstownship,plssrange,plssmeridian,utmzone,utmnorthing,utmeasting,geocoordsource,elev,geomposhill,geomposmntn,geompostrce,geomposflats,hillslopeprof,geomslopeseg,slope,aspect,slopelenusle,slopelenuptro,shapeacross,shapedown,slopecomplex,locphysnm,siteksatclassupper,siteksatclasslower,drainagecl,runoff,drainagepattern,pmgroupname,pmgroupname_s,climstaid,climstanm,climstatype,ffd,map,reannualprecip,airtempa,soiltempa,airtemps,soiltemps,airtempw,soiltempw,benchmarksoilflag,flodfreqcl,floddurcl,flodmonthbeg,pondfreqcl,ponddurcl,pondmonthbeg,wtabledur,latstddecimaldegrees,longstddecimaldegrees,gpspositionalerror,gpspdop,elevcorrected,sdbiidref,siteiid
    "2001WI025052","43","7","58.75","North","89","2","28.4599990844727","West","World Geodetic System 1984",,,,,,"Fourth Principal Extended","16","4777605.24","333978.92","Auto-populated from survey grade GPS","307",,,,,"Summit",,"3","135",,,"Linear","Convex","simple",,,,,,,,"1",,,,,,,,,,,,,"0",,,,,,,,"43.1329863","-89.0412387",,,,"117","873866"
    @end
    @begin siteobs
    seqnum,obsdate,obsdatekind,datacollector,photoid,swaterkind,swaterdepth,hydrologystatus,geomicrorelief,geommicelev,geommicpat,ecostateid,ecostatename,commphaseid,commphasename,plantassocnm,earthcovkind1,earthcovkind2,resourceretentionclass,bareareamaxwidth,pedodermclass,pedodermcovind,biolcrusttypedom,biolcrusttypesecond,physcrustsubtype,crustdevcl,soilredistributionclass,exposedsoilpct,localdisturbancedistance,localdisturbancedescription,drainedflag,beddingflag,plantationflag,forestrotationstage,yldstudyid,currweathcond,currairtemp,tidalperiod,bottomtype,saswatertempupper,saswatertemplower,saswaterphupper,saswaterphlower,phdetermeth,sasdissolvedoxyupper,sasdissolvedoxylower,saswatersalinityupper,saswatersalinitylower,siteiidref,siteobsiid
    "1","4/5/2001 12:00:00 AM","Actual Site Observation Date","John Campbell",,,,,,,,,,,,,"Grass/herbaceous cover","Tame pastureland",,,,"0",,,,,,,,,"0","0","0",,,,,,,,,,,,,,,,"873866","849283"
    @end
    @begin siteerosionacc
    seqnum,erokind,siteobsiidref,siteeroacciid
    @end
    @begin sitegeomordesc
    seqnum,geomfiidref,geomfmod,geomfeatid,existsonfeat,siteiidref,sitegeomdiid
    ,"39",,,,"873866","907703"
    @end
    @begin siteobstext
    seqnum,recdate,recauthor,siteobstextkind,textcat,textsubcat,textentry,siteobsiidref,siteobstextiid
    @end
    @begin siteaoverlap
    seqnum,areaiidref,siteiidref,sareaoviid
    ,"1748","873866","3056979"
    ,"69629","873866","3058980"
    ,"76952","873866","3058981"
    ,"75037","873866","3059200"
    ,"68910","873866","3059277"
    ,"6796","873866","3059355"
    @end
    @begin sitemuoverlap
    siteiidref,seqnum,lmapunitiidref,recwlupdated,recuseriidref,smuoviid
    @end
    @begin sitepm
    seqnum,pmorder,pmdept,pmdepb,pmmodifier,pmgenmod,pmkind,pmorigin,pmweathering,siteiidref,sitepmiid
    @end
    @begin sitesoilmoist
    seqnum,soimoistdept,soimoistdepb,soilmoistsensordepth,soilmoistsensorkind,obssoimoiststat,obssoimoist,obsgrsoimoist,soimoistten,siteobsiidref,sitesmiid
    @end
    @begin sitesoiltemp
    seqnum,soitempdep,soiltempsensorkind,soitemp,siteobsiidref,sitestiid
    @end
    @begin sitetext
    seqnum,recdate,recauthor,sitetextkind,textcat,textsubcat,textentry,siteiidref,sitetextiid
    @end
    @begin transect
    utransectid,tsectauth,tsectkind,tsectselmeth,tsectdelinsize,tsectdir,tsectcertstatus,tsectdbiidref,tsectiid
    @end
    @begin transecttex
    seqnum,recdate,recauthor,transecttextkind,textcat,textsubcat,textentry,tsectiidref,transecttextiid
    @end
    @begin pediagfeatures
    peiidref,seqnum,featdept,featdepb,featthick_l,featthick_r,featthick_h,featkind,recwlupdated,recuseriidref,pediagfeatiid
    @end
    @begin pefmp
    peiidref,seqnum,fmpname,fmpvalue,fmpunits,recwlupdated,recuseriidref,pefmpiid
    @end
    @begin pedon
    siteobsiidref,upedonid,pedrecorigin,descname,taxonname,taxonname_s,localphase,taxclname,taxclname_s,taxonkind,taxonkind_s,pedontype,pedonpurpose,pedonunit,labdatadescflag,relexpsize,relexpuom,earthcovkind1,earthcovkind2,erocl,labsourceid,pedlabsampnum,tsectiidref,tsectstopnum,tsectinterval,rcapointnumber,soilreplicatenumber,azimuthfromplotcenter,distancefromplotcenter,rectangularplotlinenumber,distancefrombaseline,pedodermclass,pedodermcovind,biolcrusttypedom,biolcrusttypesecond,physcrustsubtype,crustdevcl,rangevegcanopytypedom,rangevegcanopytypesec,forestoverstoryvegtype,forestunderstoryvegtype,forestgroundcovvegtypedom,forestgroundcovvegtypesec,agronomicfeature,otherfeaturedescription,currentcropname,littercoverpct,residuedescription,pedonhydricrating,pecertstatus,peqcstatus,peqastatus,saspipelengthtot,saspipelengthext,saspipelengthunfilled,sascoresettlement,sascorelength,sascorestoragesite,sasexposurebegin,sasexposureend,pedbiidref,grpiidref,objwlupdated,objuseriidref,recwlupdated,recuseriidref,peiid
    "849283","2001WI025052","Pedon PC 5.1","John Campbell, Ned English","Kidder","1",,,"1","Series","1","Undefined observation","Research site","2","No",,,"Grass/herbaceous cover","Tame pastureland",,,,,,,,,,,,,,"0",,,,,,,,,,,,,,,,"No","Not certified","Not reviewed","Not reviewed",,,,,,,,,"117","16238","7/18/2016 9:26:16 PM","2944","4/5/2013 3:45:27 PM","2944","858228"
    @end
    @begin perestrictions
    seqnum,soimoistdept,soimoistdepb,soilmoistsensordepth,soilmoistsensorkind,obssoimoiststat,obssoimoist,obsgrsoimoist,soimoistten,siteobsiidref,sitesmiid,
    @end
    @begin sitesurffrags
    seqnum,sfragcov,distrocks,sfragkind,sfragsize_l,sfragsize_r,sfragsize_h,sfragshp,sfraground,sfraghard,siteobsiidref,sitesurffragsiid
    @end
    @begin petaxhistfmmin
    pedtaxhistoryiidref,seqnum,minorder,taxminalogy,recwlupdated,recuseriidref,petaxfmminiid
    @end
    @begin petxhistfmother
    pedtaxhistoryiidref,seqnum,taxfamother,recwlupdated,recuseriidref,petaxfoiid
    @end
    @begin petaxhistmoistcl
    pedtaxhistoryiidref,seqnum,taxmoistcl,recwlupdated,recuseriidref,petaxmciid
    @end
    @begin petext
    peiidref,seqnum,recdate,recauthor,pedontextkind,textcat,textsubcat,textentry,recwlupdated,recuseriidref,petextiid
    @end
    @begin phcemagent
    phiidref,seqnum,ruprescem,recwlupdated,recuseriidref,phcemagentiid
    @end
    @begin phcolor
    phiidref,seqnum,colorpct,colorhue,colorvalue,colorchroma,colorphysst,colormoistst,recwlupdated,recuseriidref,phcoloriid
    "4202332","1","100","7.5YR","4","6",,"Moist","4/5/2013 3:42:23 PM","2944","5395098"
    "4202330","1","100","10YR","3","2",,"Moist","4/5/2013 3:42:23 PM","2944","5395096"
    "4202333","1","100","7.5YR","5","6",,"Moist","4/5/2013 3:42:23 PM","2944","5395099"
    "4202331","1","100","7.5YR","4","6",,"Moist","4/5/2013 3:42:23 PM","2944","5395097"
    @end
    @begin phconccolor
    phconceniidref,seqnum,colorpct,colorhue,colorvalue,colorchroma,colormoistst,recwlupdated,recuseriidref,phconcencoloriid
    @end
    @begin phconcs
    phiidref,seqnum,concpct,concsize,conccntrst,conchardness,concshape,conckind,conclocation,concboundary,recwlupdated,recuseriidref,phconceniid
    @end
    @begin phdesgnsuffix
    phiidref,seqnum,desgnsuffix,recwlupdated,recuseriidref,phdesgnsfxiid
    "4202332","1","t","4/5/2013 3:42:23 PM","2944","2066448"
    "4202331","1","w","4/5/2013 3:42:23 PM","2944","2066447"
    @end
    @begin phfeatures
    phiidref,seqnum,horfeatkind,horfeatvtpct_l,horfeatvtpct_r,horfeatvtpct_h,horfeatlapct_l,horfeatlapct_r,horfeatlapct_h,recwlupdated,recuseriidref,phfeatsiid
    @end
    @begin phfeatcolor
    phiidref,seqnum,horfeatkind,horfeatvtpct_l,horfeatvtpct_r,horfeatvtpct_h,horfeatlapct_l,horfeatlapct_r,horfeatlapct_h,recwlupdated,recuseriidref,phfeatsiid
    @end
    @begin phfmp
    phiidref,seqnum,fmpname,fmpvalue,fmpunits,recwlupdated,recuseriidref,phfmpiid
    @end
    @begin phfrags
    phiidref,seqnum,fragvol,fragweight,fragsize_l,fragsize_r,fragsize_h,fragkind,fragshp,fraground,fraghard,fragestmethod,recwlupdated,recuseriidref,phfragsiid
    "4202332",,"2",,"2","20","76",,"Nonflat",,,"Visual inspection","4/5/2013 3:42:23 PM","2944","2340983"
    "4202333",,"11",,"2","20","76",,"Nonflat",,,"Visual inspection","4/5/2013 3:42:23 PM","2944","2340984"
    @end
    @begin phmottles
    phiidref,seqnum,mottlepct,mottlesize,mottlecntrst,colorhue,colorvalue,colorchroma,mottleshape,colormoistst,mottleloc,recwlupdated,recuseriidref,phmottlesiid
    @end
    @begin phpores
    phiidref,seqnum,poreqty,poreqtyclass,poresize,porecont,poreshp,recwlupdated,recuseriidref,phporesiid
    @end
    @begin phpvsf
    phiidref,seqnum,pvsfpct,pvsfkind,pvsfdistinct,pvsfcont,pvsflocation,recwlupdated,recuseriidref,phpvsfiid
    @end
    @begin phpvsfcolor
    phpvsfiidref,seqnum,colorpct,colorhue,colorvalue,colorchroma,colormoistst,recwlupdated,recuseriidref,phpvsfcoloriid
    @end
    @begin phrdxfeatures
    phiidref,seqnum,rdxfeatpct,rdxfeatsize,rdxfeatcntrst,rdxfeathardness,rdxfeatshape,rdxfeatkind,rdxfeatlocation,rdxfeatboundary,recwlupdated,recuseriidref,phrdxfiid
    @end
    @begin phroots
    phiidref,seqnum,rootsquantity,rootsquantityclass,rootssize,rootslocation,recwlupdated,recuseriidref,phrootsiid
    @end
    @begin phsample
    phiidref,seqnum,labsampnum,fldsampid,layerdepthtop,layerdepthbottom,numberofbulksampbags,numberofbulkdensityclods,numberofnaturalfabricclods,numberofothersamples,recwlupdated,recuseriidref,phlabsampiid
    @end
    @begin phstructure
    phiidref,seqnum,structgrade,structsize,structtype,structid,structpartsto,recwlupdated,recuseriidref,phstructureiid
    @end
    @begin phtext
    phiidref,seqnum,recdate,recauthor,phorizontextkind,textcat,textsubcat,textentry,recwlupdated,recuseriidref,phtextiid
    @end
    @begin phtexture
    phiidref,seqnum,texcl,lieutex,recwlupdated,recuseriidref,phtiid
    "4202332",,"Clay loam",,"4/5/2013 3:42:23 PM","2944","4091977"
    "4202332",,"Loam",,"4/5/2013 3:42:23 PM","2944","4091978"
    "4202330",,"Loam",,"4/5/2013 3:42:23 PM","2944","4091974"
    "4202330",,"Sandy loam",,"4/5/2013 3:42:23 PM","2944","4091975"
    "4202333",,"Sandy loam",,"4/5/2013 3:42:23 PM","2944","4091979"
    "4202331",,"Loam",,"4/5/2013 3:42:23 PM","2944","4091976"
    @end
    @begin phtexturemod
    phtiidref,seqnum,texmod,recwlupdated,recuseriidref,phtexmodiid
    @end
    @begin sitesoilmoist
    peiidref,seqnum,hzdept,hzdepb,hzthk_l,hzthk_r,hzthk_h,obsmethod,hzname,hzname_s,desgndisc,desgnmaster,desgnmasterprime,desgnvert,texture,texture_s,stratextsflag,claytotest,claycarbest,silttotest,sandtotest,fragvoltot,horcolorvflag,obssoimoiststat,rupresblkmst,rupresblkdry,rupresblkcem,rupresplate,mannerfailure,stickiness,plasticity,toughclass,penetrres,penetorient,ksatpedon,ksatstddev,ksatrepnum,horzpermclass,obsinfiltrationrate,phfield,phdetermeth,effclass,efflocation,effagent,carbdevstagefe,carbdevstagecf,mneffclass,mneffagent,reactadipyridyl,dipyridylpct,dipyridylloc,excavdifcl,soilodor,soilodorintensity,rmonosulfidep,bounddistinct,boundtopo,horzvoltotpct_l,horzvoltotpct_r,horzvoltotpct_h,horzlatareapct_l,horzlatareapct_r,horzlatareapct_h,dspcomplayerid,aashtocl,unifiedcl,recwlupdated,recuseriidref,phiid
    "858228",,"30","66",,"36",,,"Bt","1",,"B",,,"CL L","1","0",,,,,"2","0",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"0",,,,,,,,,,,,"7/18/2016 9:24:59 PM","2944","4202332"
    "858228",,"0","13",,"13",,,"A","1",,"A",,,"L SL","1","0",,,,,"0","0",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"0",,,,,,,,,,,,"7/18/2016 9:24:59 PM","2944","4202330"
    "858228",,"66","67",,"1",,,"C","1",,"C",,,"SL","1","0",,,,,"11","0",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"0",,,,,,,,,,,,"7/18/2016 9:24:59 PM","2944","4202333"
    "858228",,"13","30",,"17",,,"Bw","1",,"B",,,"L","1","0",,,,,"0","0",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"0",,,,,,,,,,,,"7/18/2016 9:24:59 PM","2944","4202331"
    @end
    @begin petaxhistory
    peiidref,seqnum,classdate,classtype,classifier,taxonname,localphase,taxonkind,seriesstatus,taxclname,taxclname_s,taxorder,taxsuborder,taxgrtgroup,taxsubgrp,taxpartsize,taxpartsizemod,taxceactcl,taxreaction,taxtempcl,taxmoistscl,taxtempregime,taxfamhahatmatcl,soiltaxedition,psctopdepth,pscbotdepth,osdtypelocflag,recwlupdated,recuseriidref,petaxhistoryiid
    "858228","1","4/5/2001 12:00:00 AM","Sampled as","John Campbell","Kidder",,"Series","Established",,"1",,,,,,,,,,,,,,,,"0","4/5/2013 3:45:17 PM","2944","886518"
    "858228","2","4/5/2001 12:00:00 AM","Correlated","John Campbell","Kidder",,"Series","Established",,"1",,,,,,,,,,,,,,,,"0","4/5/2013 3:45:17 PM","2944","886519"
    @end
    </div>
    </div>


    </div>
    </form>
    </body>
    </html> """

    try:

        """ ---------------------- Create a dictionary of number of fields per table -----------------"""
        ''' Create a dictionary that will contain table:number of fields in order
            to double check that the values from the web report are correct
            this was added b/c there were text fields that were getting disconnected in the report
            and being read as 2 lines -- Jason couldn't address this issue in NASIS '''
        arcpy.env.workspace = pedonFGDB

        tableFldDict = dict()    # petext:11
        validTables = arcpy.ListTables("*")
        validTables.append('site')

        for table in validTables:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            numOfFields = arcpy.Describe(os.path.join(pedonFGDB,table)).fields
            numOfValidFlds = 0

            for field in numOfFields:
                if not field.type.lower() in ("oid","geometry"):
                    numOfValidFlds +=1

            tableFldDict[table] = numOfValidFlds
            del numOfFields;numOfValidFlds

        """----------------------------------- Open a network object --------------------------------"""
        ''' Open a network object using the URL with the search string already concatenated.
            As soon as the url is opened it needs to be read otherwise there will be a socket
            error raised.  Experienced this when the url was being opened before the above
            dictionary was created.  Bizarre'''
        theReport = urlopen(URL)

        invalidTable = 0    # represents tables that don't correspond with the GDB
        invalidRecord = 0  # represents records that were not added
        validRecord = 0

        bHeader = False         # flag indicating if value is html junk
        currentTable = ""       # The table found in the report
        numOfFields = ""        # The number of fields a specific table should contain
        partialValue = ""       # variable containing part of a value that is not complete
        originalValue = ""      # variable containing the original incomplete value
        bPartialValue = False   # flag indicating if value is incomplete; append next record

        """ ------------------- Begin Adding data from URL into a dictionary of lists ---------------"""
        # iterate through the lines in the report
        for theValue in theReport:

            theValue = theValue.strip() # remove whitespace characters

            # represents the start of valid table
            if theValue.find('@begin') > -1:
                theTable = theValue[theValue.find('@') + 7:]  ## Isolate the table
                numOfFields = tableFldDict[theTable]

                # Check if the table name exists in the list of dictionaries
                # if so, set the currentTable variable and bHeader
                if pedonGDBtables.has_key(theTable):
                    currentTable = theTable
                    bHeader = True  ## Next line will be the header

                else:
                    AddMsgAndPrint("\t" + theTable + " Does not exist in the FGDB schema!  Figure this out Jason Nemecek!",2)
                    invalidTable += 1

            # end of the previous table has been reached; reset currentTable
            elif theValue.find('@end') > -1:
                currentTable = ""
                bHeader = False

            # represents header line; skip this line
            elif bHeader:
                bHeader = False

            # this is a valid record that should be collected
            elif not bHeader and currentTable:
                numOfValues = len(theValue.split('|'))

                # Add the record to its designated list within the dictionary
                # Do not remove the double quotes b/c doing so converts the object
                # to a list which increases its object size.  Remove quotes before
                # inserting into table

                # this should represent the 2nd half of a valid value
                if bPartialValue:
                    partialValue += theValue  # append this record to the previous record

                    # This value completed the previous value
                    if len(partialValue.split('|')) == numOfFields:
                        pedonGDBtables[currentTable].append(partialValue)
                        validRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = "",""

                    # appending this value still falls short of number of possible fields
                    # add another record; this would be the 3rd record appended and may
                    # exceed number of values.
                    elif len(partialValue.split('|')) < numOfFields:
                        continue

                    # appending this value exceeded the number of possible fields
                    else:
                        AddMsgAndPrint("\n\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(len(partialValue.split('|'))),2)
                        AddMsgAndPrint("\t\t\tOriginal Record: " + originalValue,2)
                        AddMsgAndPrint("\t\t\tAppended Record: " + partialValue,2)
                        invalidRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = ""

                # number of values do not equal the number of fields in the corresponding tables
                elif numOfValues != numOfFields:

                    # number of values exceed the number of fields; Big Error
                    if numOfValues > numOfFields:
                        AddMsgAndPrint("\n\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(numOfValues),2)
                        AddMsgAndPrint("\t\t\tRecord: " + theValue,2)
                        invalidRecord += 1
                        continue

                    # number of values falls short of the number of correct fields
                    else:
                        partialValue,originalValue = theValue,theValue
                        bPartialValue = True

                else:
                    pedonGDBtables[currentTable].append(theValue)
                    validRecord += 1
                    bPartialValue = False
                    partialValue = ""

            elif theValue.find("ERROR") > -1:
                AddMsgAndPrint("\n\t\t" + theValue[theValue.find("ERROR"):],2)
                return False

            else:
                invalidRecord += 1

        if not validRecord:
            AddMsgAndPrint("\t\tThere were no valid records captured from NASIS request",2)
            return False

        # Report any invalid tables found in report; This should take care of itself as Jason perfects the report.
        if invalidTable and invalidRecord:
            AddMsgAndPrint("\t\tThere were " + splitThousands(invalidTable) + " invalid table(s) included in the report with " + splitThousands(invalidRecord) + " invalid record(s)",1)

        # Report any invalid records found in report; There are 27 html lines reserved for headers and footers
        if invalidRecord > 28:
            AddMsgAndPrint("\t\tThere were " + splitThousands(invalidRecord) + " invalid record(s) not captured",1)

        return True

    except URLError, e:
        if hasattr(e, 'reason'):
            AddMsgAndPrint("\n\t" + URL)
            AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

        elif hasattr(e, 'code'):
            AddMsgAndPrint("\n\t" + URL)
            AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

        return False

    except socket.timeout, e:
        AddMsgAndPrint("\n\t" + URL)
        AddMsgAndPrint("\tServer Timeout Error", 2)
        return False

    except socket.error, e:
        AddMsgAndPrint("\n\t" + URL)
        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
        return False

    except httplib.BadStatusLine:
        AddMsgAndPrint("\n\t" + URL)
        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
        return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def importPedonData(tblAliases):


    try:
        AddMsgAndPrint("\nImporting Pedon Data into FGDB")

        # use the tblAliases so that tables are imported in alphabetical order
        if bAliasName:
            tblKeys = tblAliases.keys()
            maxCharTable = max([len(table) for table in tblKeys]) + 1
            maxCharAlias = max([len(value[1]) for value in tblAliases.items()])

            firstTab = (maxCharTable - len("Table Physical Name")) * " "
            headerName = "\n\tTable Physical Name" + firstTab + "Table Alias Name"
            AddMsgAndPrint(headerName,0)
            AddMsgAndPrint("\t" + len(headerName) * "=",0)

        else:
            maxCharTable = max([len(table) for table in tblKeys]) + 1
            tblKeys = pedonGDBtables.keys()

        tblKeys.sort()

        """ ---------------------------------------------------"""
        for table in tblKeys:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            # Capture the alias name of the table
            if bAliasName:
                aliasName = tblAliases[table]

            # Strictly for standardizing reporting
            firstTab = (maxCharTable - len(table)) * " "

            # check if list contains records to be added
            if len(pedonGDBtables[table]):

                numOfRowsAdded = 0
                GDBtable = pedonFGDB + os.sep + table # FGDB Pyhsical table path

                """ -------------------------------- Collect field information -----------------------"""
                ''' For the current table, get the field length if the field is a string.  I do this b/c
                the actual value may exceed the field length and error out as has happened in SSURGO.  If
                the value does exceed the field length then the value will be truncated to the max length
                of the field '''

                # Put all the field names in a list
                fieldList = arcpy.Describe(GDBtable).fields
                nameOfFields = []
                fldLengths = list()

                for field in fieldList:

                    # Skip Object ID field Shape field (only for site)
                    if not field.type.lower() in ("oid","geometry"):
                        nameOfFields.append(field.name)

                        if field.type.lower() == "string":
                            fldLengths.append(field.length)
                        else:
                            fldLengths.append(0)

                # Site feature class will have X,Y geometry added; Add XY token to list
                if table == 'site':
                    #print"\n\tsite table"
                    #print "\nrec = " + str(rec)
                    nameOfFields.append('SHAPE@XY')

                    latField = [f.name for f in arcpy.ListFields(table,'latstddecimaldegrees')][0]
                    longField = [f.name for f in arcpy.ListFields(table,'longstddecimaldegrees')][0]
                    latFieldIndex = nameOfFields.index(latField)
                    longFieldIndex = nameOfFields.index(longField)

                # Initiate the insert cursor object using all of the fields
                cursor = arcpy.da.InsertCursor(GDBtable,nameOfFields)
                recNum = 0

                """ -------------------------------- Insert Rows -------------------------------------"""
                # '"S1962WI025001","43","15","9","North","89","7","56","West",,"Dane County, Wisconsin. 100 yards south of road."'
                for rec in pedonGDBtables[table]:

                    newRow = list()  # list containing the values that will populate a new row
                    fldNo = 0        # list position to reference the field lengths in order to compare

                    for value in rec.replace('"','').split('|'):

                        value = value.strip()
                        fldLen = fldLengths[fldNo]

                        if value == '':   ## Empty String
                            value = None

                        elif fldLen > 0:  ## record is a string, truncate it
                            value = value[0:fldLen]

                        else:             ## record is a number, keep it
                            value = value

                        newRow.append(value)
                        fldNo += 1

                    if table == 'site':
                        # Combine the X,Y value from the existing record and append it at the
                        # of the list to be associated with the X,Y token
                        xValue = float([rec.replace('"','').split('|')][0][longFieldIndex])
                        yValue = float([rec.replace('"','').split('|')][0][latFieldIndex])
                        newRow.append((xValue,yValue))

                    try:
                        cursor.insertRow(newRow)
                        numOfRowsAdded += 1;recNum += 1

                    except arcpy.ExecuteError:
                        AddMsgAndPrint("\n\tError in :" + table + " table: Field No: " + str(fldNo) + " : " + str(rec),2)
                        AddMsgAndPrint("\n\t" + arcpy.GetMessages(2),2)
                        break
                    except:
                        AddMsgAndPrint("\n\tError in :" + table + " table")
                        print "\n\t" + str(rec)
                        print "\n\tRecord Number: " + str(recNum)
                        AddMsgAndPrint("\tNumber of Fields in GDB: " + str(len(nameOfFields)))
                        AddMsgAndPrint("\tNumber of fields in report: " + str(len([rec.split('|')][0])))
                        errorMsg()
                        break

                    del newRow,fldNo

                # Report the # of records added to the table
                if bAliasName:
                    secondTab = (maxCharAlias - len(aliasName)) * " "
                    AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: " + splitThousands(numOfRowsAdded),1)
                else:
                    AddMsgAndPrint("\t" + table + firstTab + " Records Added: " + splitThousands(numOfRowsAdded),1)

                del numOfRowsAdded,GDBtable,fieldList,nameOfFields,fldLengths,cursor

            # Table had no records; still print it out
            else:
                if bAliasName:
                    secondTab = (maxCharAlias - len(aliasName)) * " "
                    AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: 0",1)
                else:
                    AddMsgAndPrint("\t" + table + firstTab + " Records Added: 0",1)

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
##        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
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
import sys, string, os, traceback, re, arcpy, socket, httplib
from arcpy import env
from urllib2 import urlopen, URLError, HTTPError, time

if __name__ == '__main__':

    print "start time: " + time.asctime() + "\n"

    #inputFeatures = arcpy.GetParameter(0)
    inputFeatures = r'C:\Temp\scratch.gdb\US'
    #inputFeatures = r'C:\Temp\scratch.gdb\DaneCounty'

    GDBname = "WI"
    #GDBname = arcpy.GetParameter(1)
    outputFolder = r'C:\Temp'
    #outputFolder = arcpy.GetParameterAsText(2)

    """ ------------------------------------------------ Set Scratch Workspace ------------------------------------------------"""
    scratchWS = setScratchWorkspace()
    arcpy.env.scratchWorkspace = scratchWS

    if not scratchWS:
        AddMsgAndPrint("\n Failed to scratch workspace; Try setting it manually",2)
        sys.exit()

    """ ---------------------------------------------- Get Bounding box coordinates -------------------------------------------"""
    #Lat1 = 43.8480050291613;Lat2 = 44.196269661256736;Long1 = -93.76788085724957;Long2 = -93.40649833646484;
    Lat1,Lat2,Long1,Long2 = getBoundingCoordinates(inputFeatures)

    if not Lat1:
        AddMsgAndPrint("\nFailed to acquire Lat/Long coordinates to pass over; Try a new input feature",2)
        sys.exit()


    """ ---------------------------- Get a list of PedonIDs that are within the bounding box from NASIS -----------------------"""
    coordStr = "&Lat1=" + str(Lat1) + "&Lat2=" + str(Lat2) + "&Long1=" + str(Long1) + "&Long2=" + str(Long2)
    getPedonIDURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordStr

    # peiid: siteID,Labnum,X,Y
    #{'122647': ('84IA0130011', '85P0558', '-92.3241653', '42.3116684'), '883407': ('2014IA013003', None, '-92.1096600', '42.5332000'), '60914': ('98IA013011', None, '-92.4715271', '42.5718880')}
    pedonDict = dict()

    if not getWebExportPedon(getPedonIDURL):
        AddMsgAndPrint("\n\t Failed to get a list of pedonIDs from NASIS",2)
    sys.exit()

    """ ---------------------------------------------- Create New File Geodatabaes -------------------------------------------- """
    ''' Create a new FGDB using a pre-established XML workspace schema.  All tables will be empty
        and relationships established.  A dictionary of empty lists will be created as a placeholder
        for the values from the XML report.  The name and quantity of lists will be the same as the FGDB'''

    pedonFGDB = createPedonFGDB()
    #pedonFGDB = r'C:\Temp\Dane.gdb'

    if pedonFGDB == "":
        AddMsgAndPrint("\n Failed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!",2)
        sys.exit()

    arcpy.env.workspace = pedonFGDB
    tables = arcpy.ListTables()
    tables.append(arcpy.ListFeatureClasses('site','Point')[0])  ## site is a feature class and gets excluded by the ListTables function

    ## {'area': [],'areatype': [],'basalareatreescounted': [],'beltdata': [],'belttransectsummary': []........}
    pedonGDBtables = dict()
    for table in tables:

        # Skip any Metadata files
        if table.find('Metadata') > -1: continue

        pedonGDBtables[str(table)] = []

    # Acquire Aliases.  This is only used for printing purposes
    tblAliases = dict()
    bAliasName = True

    if not getTableAliases(pedonFGDB):
        AddMsgAndPrint("\nCould not retrieve alias names from \'MetadataTable\'",1)

    if not len(tblAliases):
        bAliasName = False

    """ ------------------------------------------ Get Pedon information using 2nd report -------------------------------------"""

    getPedonHorizonURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list="

    i = 1  ## Total Count
    listOfPedonStrings = list()  ## List containing pedonIDstring lists; individual lists are comprised of about 265 pedons
    pedonIDstr = ""

    # There is an inherent URL character limit of 2,083.  The report URL is 123 characters long which leaves 1,960 characters
    # available. I arbitrarily chose to have a max URL of 1,860 characters long to avoid problems.  Most pedonIDs are about
    # 6 characters.  This would mean an average max request of 265 pedons at a time.

    for pedonID in pedonDict:

        ## End of pedon list has been reached
        if i == len(pedonDict):
            pedonIDstr = pedonIDstr + str(pedonID)
            listOfPedonStrings.append(pedonIDstr)

        ## End of pedon list NOT reached
        else:
            ## Max URL length reached - retrieve pedon data and start over
            if len(pedonIDstr) > 1860:
                pedonIDstr = pedonIDstr + str(pedonID)
                listOfPedonStrings.append(pedonIDstr)

                ## reset the pedon ID string to empty
                pedonIDstr = ""
                i+=1

            ## concatenate pedonID to string and continue
            else:
                pedonIDstr = pedonIDstr + str(pedonID) + ",";i+=1

    if not len(listOfPedonStrings):
        AddMsgAndPrint("\n\t Something Happened here.....WTF!",2)
        sys.exit()

    if len(listOfPedonStrings) > 1:
        AddMsgAndPrint("\nDue to URL limitations there will be " + str(len(listOfPedonStrings))+ " seperate requests to NASIS:",0)
    else:
        AddMsgAndPrint("\n")

    i = 1
    for pedonString in listOfPedonStrings:

        AddMsgAndPrint("Retrieving pedon data from NASIS for " + str(len(pedonString.split(','))) + " pedons. (Request " + str(i) + " of " + str(len(listOfPedonStrings)) + ")",1)

        #temp = '215823,140717,836581,140711,140710,140713,140712,246369,246368,309023,309021,246363,246362,528520,246360,246367,246366,246365,338798,304162,168910,59177,314159,292746,271905,271907,314150,314151,314152,314153,597650,597651,597652,597653,179137,146675,56386,263287,338942,290579,204309,274267,204306,214231,258681,570978,772323,111457,248359,772322,218474,134152,772321,248807,772320,135903,295782,972372,972373,972370,972371,972374,972375,1049049,1049048,146677,772325,366921,1049041,1049040,1049043,1049042,1049045,1049044,1049047,1049046,356989,366923,212899,250206,366924,184591,366925,250204,1111359,1111358,1111357,1111356,1111355,1111354,135905,295784,350748,197236,290633,254784,346474,669678,337370,295787,669679,241184,254785,1068099,1068098,263286,273779,1068093,1068092,1068091,1068090,1068097,1068096,1068095,1068094,313313,313312,313311,313310,1080169,1080168,313315,313314,1080165,1080164,1080167,1080166,1080161,1080160,1080163,1080162,322534,245694,256199,212895,312683,1067517,1067516,1067515,1068326,1067513,1068320,1067511,1068322,147237,312681,1068329,1068328,1067519,1067518,197530,291535,147682,291532,291533,63816,821710,896205,172119,421942,896204,1121624,1121625,1121626,1121627,1121620,1121621,1121622,1121623,212897,307500,1121628,1121629,1197339,1197338,934257,421943,1197333,1197332,1197331,1197330,1197337,1197336,1197335,1197334,47287,47284,47285,47282,1201526,135943,1068861,47288,47289,290884,421940,406381,248808,406380,318428,318429,318426,318427,318420,318421,318422,60810,493099,493098,612714,375341,378772,378773,378770,378771,493097,1069054,1069055,1069056,1069057,1069050,1069051,1069052,1069053,364863,364862,364861,364860,1069058,1069059,364865,364864,284875,284877,406388,155788,284873,375692,218826,264711,290638,421947,1018274,1018275,1018276,1018277,1018270,1018271,1018272,1018273,329344,276376,925958,925959,1018278,1018279'
        if not getPedonHorizon(getPedonHorizonURL + pedonString):
        #if not getPedonHorizon(getPedonHorizonURL + temp):
            AddMsgAndPrint("\n\tFailed to receive pedon horizon info from NASIS",2)
        i+=1

    """ ------------------------------------------ Import Pedon Information into Pedon FGDB -------------------------------------"""
    # if the site table has records, proceed to transerring them to the FGDB
    if len(pedonGDBtables['site']):
        if not importPedonData(tblAliases):
            sys.exit()

    print "End time: " + time.asctime() + "\n"