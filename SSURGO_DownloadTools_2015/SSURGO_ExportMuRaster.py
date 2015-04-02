# SSURGO_ExportMuRaster.py
#
# Convert MUPOLYGON featureclass to raster for the specified SSURGO geodatabase.
# By default any small NoData areas (< 5000 sq meters) will be filled using
# the Majority value.
#
# Input mupolygon featureclass must have a projected coordinate system or it will skip.
# Input databases and featureclasses must use naming convention established by the
# 'SDM Export By State' tool.
#
# For geographic regions that have USGS NLCD available, the tool wil automatically
# align the coordinate system and raster grid to match.
#
# 10-31-2013 Added gap fill method
#
# 11-05-2014
# 11-22-2013
# 12-10-2013  Problem with using non-unique cellvalues for raster. Going back to
#             creating an integer version of MUKEY in the mapunit polygon layer.
# 12-13-2013 Occasionally see error messages related to temporary GRIDs (g_g*) created
#            under "C:\Users\steve.peaslee\AppData\Local\Temp\a subfolder". These
#            are probably caused by orphaned INFO tables.
# 01-08-2014 Added basic raster metadata (still need process steps)
# 01-12-2014 Restricted conversion to use only input MUPOLYGON featureclass having
#            a projected coordinate system with linear units=Meter
# 01-31-2014 Added progressor bar to 'Saving MUKEY values..'. Seems to be a hangup at this
#            point when processing CONUS geodatabase
# 02-14-2014 Changed FeatureToLayer (CELL_CENTER) to PolygonToRaster (MAXIMUM_COMBINED_AREA)
#            and removed the Gap Fill option.
# 2014-09-27 Added ISO metadata import
#
# 2014-10-18 Noticed that failure to create raster seemed to be related to long
# file names or non-alphanumeric characters such as a dash in the name.
#
# 2014-10-29 Removed ORDER BY MUKEY sql clause because some computers were failing on that line.
#            Don't understand why.
#
# 2014-10-31 Added error message if the MUKEY column is not populated in the MUPOLYGON featureclass
#
# 2014-11-04 Problems occur when the user's gp environment points to Default.gdb for the scratchWorkpace.
#            Added a fatal error message when that occurs.
#
# 2015-01-15 Hopefully fixed some of the issues that caused the raster conversion to crash at the end.
#            Cleaned up some of the current workspace settings and moved the renaming of the final raster.
#
# 2015-02-26 Adding option for tiling raster conversion by areasymbol and then mosaicing. Slower and takes
#            more disk space, but gets the job done when otherwise PolygonToRaster fails on big datasets.

# 2015-02-27 Make bTiling variable an integer (0, 2, 5) that can be used to slice the areasymbol value. This will
#            give the user an option to tile by state (2) or by survey area (5)
# 2015-03-10 Moved sequence of CheckInExtension. It was at the beginning which seems wrong.
#
# 2015-03-11 Switched tiled raster format from geodatabase raster to TIFF. This should allow the entire
#            temporary folder to be deleted instead of deleting rasters one-at-a-time (slow).
# 2015-03-11 Added attribute index (mukey) to raster attribute table
# 2015-03-13 Modified output raster name by incorporating the geodatabase name (after '_' and before ".gdb")

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # prints message to screen if run as a python script
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
    # The scratch workspace will typically not be defined by the user but the scratchGDB will
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
        # Problems can occur (especially raster gp) when environment ScratchWorkspace = Default.gdb
        if os.path.basename(env.scratchGDB) == "Default.gdb":
            raise MyError, "Please set geoprocessing environment 'Scratch Workspace' to another database. Default.gdb not allowed"

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

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n ", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def SnapToNLCD(inputFC, iRaster):
    # This function will set an output extent that matches the NLCD raster dataset.
    # In effect this is like using NLCD as a snapraster as long as the projections are the same,
    # which is USA_Contiguous_Albers_Equal_Area_Conic_USGS_version
    #
    # Returns empty string if linear units are not 'foot' or 'meter'

    try:
        theDesc = arcpy.Describe(inputFC)
        sr = theDesc.spatialReference
        inputSRName = sr.name
        theUnits = sr.linearUnitName
        pExtent = theDesc.extent

        PrintMsg(" \nCoordinate system: " + inputSRName + " (" + theUnits.lower() + ")", 0)

        if pExtent is None:
            raise MyError, "Failed to get extent from " + inputFC

        x1 = float(pExtent.XMin)
        y1 = float(pExtent.YMin)
        x2 = float(pExtent.XMax)
        y2 = float(pExtent.YMax)

        if 'foot' in theUnits.lower():
            theUnits = "feet"

        elif theUnits.lower() == "meter":
            theUnits = "meters"

        # USA_Contiguous_Albers_Equal_Area_Conic_USGS_version (NAD83)
        xNLCD = 532695
        yNLCD = 1550295

        # Hawaii_Albers_Equal_Area_Conic  -345945, 1753875
        # Western_Pacific_Albers_Equal_Area_Conic  -2390975, -703265 est.
        # NAD_1983_Alaska_Albers  -2232345, 344805
        # WGS_1984_Alaska_Albers  Upper Left Corner:  -366405.000000 meters(X),  2380125.000000 meters(Y)
        # WGS_1984_Alaska_Albers  Lower Right Corner: 517425.000000 meters(X),  2032455.000000 meters(Y)
        # Puerto Rico 3092415, -78975 (CONUS works for both)

        if theUnits != "meters":
            PrintMsg("Projected coordinate system is " + inputSRName + "; units = '" + theUnits + "'", 0)
            raise MyError, "Unable to align raster output with this coordinate system"

        elif inputSRName == "USA_Contiguous_Albers_Equal_Area_Conic_USGS_version":
            xNLCD = 532695
            yNLCD = 1550295

        elif inputSRName == "Hawaii_Albers_Equal_Area_Conic":
            xNLCD = -29805
            yNLCD = 839235

        elif inputSRName == "NAD_1983_Alaska_Albers":
            xNLCD = -368805
            yNLCD = 1362465

        elif inputSRName == "WGS_1984_Albers":
            # New WGS 1984 based coordinate system matching USGS 2001 NLCD for Alaska
            xNLCD = -366405
            yNLCD = 2032455

        elif inputSRName == "Western_Pacific_Albers_Equal_Area_Conic":
            # WGS 1984 Albers for PAC Basin area
            xNLCD = -2390975
            yNLCD = -703265

        else:
            PrintMsg("Projected coordinate system is " + inputSRName + "; units = '" + theUnits + "'", 0)
            raise MyError, "Unable to align raster output with this coordinate system"

        pExtent = theDesc.extent
        x1 = float(pExtent.XMin)
        y1 = float(pExtent.YMin)
        x2 = float(pExtent.XMax)
        y2 = float(pExtent.YMax)

        # Round off coordinates to integer values based upon raster resolution
        # Use +- 5 meters to align with NLCD
        # Calculate snapgrid using 30 meter Kansas NLCD Lower Left coordinates = -532,695 X 1,550,295
        #
        xNLCD = 532695
        yNLCD = 1550295
        iRaster = int(iRaster)

        # Calculate number of columns difference between KS NLCD and the input extent
        # Align with NLCD CONUS
        iCol = int((x1 - xNLCD) / 30)
        iRow = int((y1 - yNLCD) / 30)
        x1 = (30 * iCol) + xNLCD - 30
        y1 = (30 * iRow) + yNLCD - 30

        numCols = int(round(abs(x2 - x1) / 30))
        numRows = int(round(abs(y2 - y1) / 30))

        x2 = numCols * 30 + x1
        y2 = numRows * 30 + y1

        theExtent = str(x1) + " " + str(y1) + " " + str(x2) + " " + str(y2)
        # Format coordinate pairs as string
        sX1 = Number_Format(x1, 0, True)
        sY1 = Number_Format(y1, 0, True)
        sX2 = Number_Format(x2, 0, True)
        sY2 = Number_Format(y2, 0, True)
        sLen = 11
        sX1 = ((sLen - len(sX1)) * " ") + sX1
        sY1 = " X " + ((sLen - len(sY1)) * " ") + sY1
        sX2 = ((sLen - len(sX2)) * " ") + sX2
        sY2 = " X " + ((sLen - len(sY2)) * " ") + sY2

        PrintMsg(" \nAligning output raster to match NLCD:", 0)
        PrintMsg("\tUR: " + sX2 + sY2 + " " + theUnits.lower(), 0)
        PrintMsg("\tLL: " + sX1 + sY1 + " " + theUnits.lower(), 0)
        PrintMsg(" \n\tNumber of rows =    \t" + Number_Format(numRows * 30 / iRaster), 0)
        PrintMsg("\tNumber of columns = \t" + Number_Format(numCols * 30 / iRaster), 0)

        return theExtent

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n ", 2)
        return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def WriteToLog(theMsg, theRptFile):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #print msg
    #
    try:
        fh = open(theRptFile, "a")
        theMsg = "\n" + theMsg
        fh.write(theMsg)
        fh.close()

    except:
        errorMsg()
        pass

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
                eMsg = eMsg + str(eMinute) + " minutes "
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
def ListEnv():
    # List geoprocessing environment settings
    try:
        environments = arcpy.ListEnvironments()

        # Sort the environment list, disregarding capitalization
        #
        environments.sort(key=string.lower)

        for environment in environments:
            # As the environment is passed as a variable, use Python's getattr
            #   to evaluate the environment's value
            #
            envSetting = getattr(arcpy.env, environment)

            # Format and print each environment and its current setting
            #
            #print "{0:<30}: {1}".format(environment, envSetting)
            PrintMsg("\t" + environment + ": " + str(envSetting), 0)

    except:
        errorMsg()

## ===================================================================================
def StateNames():
    # Create dictionary object containing list of state abbreviations and their names that
    # will be used to name the file geodatabase.
    # For some areas such as Puerto Rico, U.S. Virgin Islands, Pacific Islands Area the
    # abbrevation is

    # NEED TO UPDATE THIS FUNCTION TO USE THE LAOVERLAP TABLE AREANAME. AREASYMBOL IS STATE ABBREV

    try:
        stDict = dict()
        stDict["AL"] = "Alabama"
        stDict["AK"] = "Alaska"
        stDict["AS"] = "American Samoa"
        stDict["AZ"] = "Arizona"
        stDict["AR"] = "Arkansas"
        stDict["CA"] = "California"
        stDict["CO"] = "Colorado"
        stDict["CT"] = "Connecticut"
        stDict["DC"] = "District of Columbia"
        stDict["DE"] = "Delaware"
        stDict["FL"] = "Florida"
        stDict["GA"] = "Georgia"
        stDict["HI"] = "Hawaii"
        stDict["ID"] = "Idaho"
        stDict["IL"] = "Illinois"
        stDict["IN"] = "Indiana"
        stDict["IA"] = "Iowa"
        stDict["KS"] = "Kansas"
        stDict["KY"] = "Kentucky"
        stDict["LA"] = "Louisiana"
        stDict["ME"] = "Maine"
        stDict["MD"] = "Maryland"
        stDict["MA"] = "Massachusetts"
        stDict["MI"] = "Michigan"
        stDict["MN"] = "Minnesota"
        stDict["MS"] = "Mississippi"
        stDict["MO"] = "Missouri"
        stDict["MT"] = "Montana"
        stDict["NE"] = "Nebraska"
        stDict["NV"] = "Nevada"
        stDict["NH"] = "New Hampshire"
        stDict["NJ"] = "New Jersey"
        stDict["NM"] = "New Mexico"
        stDict["NY"] = "New York"
        stDict["NC"] = "North Carolina"
        stDict["ND"] = "North Dakota"
        stDict["OH"] = "Ohio"
        stDict["OK"] = "Oklahoma"
        stDict["OR"] = "Oregon"
        stDict["PA"] = "Pennsylvania"
        stDict["PRUSVI"] = "Puerto Rico and U.S. Virgin Islands"
        stDict["RI"] = "Rhode Island"
        stDict["Sc"] = "South Carolina"
        stDict["SD"] ="South Dakota"
        stDict["TN"] = "Tennessee"
        stDict["TX"] = "Texas"
        stDict["UT"] = "Utah"
        stDict["VT"] = "Vermont"
        stDict["VA"] = "Virginia"
        stDict["WA"] = "Washington"
        stDict["WV"] = "West Virginia"
        stDict["WI"] = "Wisconsin"
        stDict["WY"] = "Wyoming"
        return stDict

    except:
        PrintMsg("\tFailed to create list of state abbreviations (CreateStateList)", 2)
        return stDict

## ===================================================================================
def CheckStatistics(outputRaster):
    # For no apparent reason, sometimes ArcGIS fails to build statistics. Might work one
    # time and then the next time it may fail without any error message.
    #
    try:
        #PrintMsg(" \n\tChecking raster statistics", 0)

        for propType in ['MINIMUM', 'MAXIMUM', 'MEAN', 'STD']:
            statVal = arcpy.GetRasterProperties_management (outputRaster, propType).getOutput(0)
            #PrintMsg("\t\t" + propType + ": " + statVal, 1)

        return True

    except:
        return False

## ===================================================================================
def UpdateMetadata(outputWS, target, surveyInfo, iRaster):
    #
    # Used for non-ISO metadata
    #
    # Search words:  xxSTATExx, xxSURVEYSxx, xxTODAYxx, xxFYxx
    #
    try:
        PrintMsg("\tUpdating metadata...")
        arcpy.SetProgressor("default", "Updating metadata")

        # Set metadata translator file
        dInstall = arcpy.GetInstallInfo()
        installPath = dInstall["InstallDir"]
        prod = r"Metadata/Translator/ARCGIS2FGDC.xml"
        mdTranslator = os.path.join(installPath, prod)

        # Define input and output XML files
        mdImport = os.path.join(env.scratchFolder, "xxImport.xml")  # the metadata xml that will provide the updated info
        xmlPath = os.path.dirname(sys.argv[0])
        mdExport = os.path.join(xmlPath, "gSSURGO_MapunitRaster.xml") # original template metadata in script directory

        # Cleanup output XML files from previous runs
        if os.path.isfile(mdImport):
            os.remove(mdImport)

        # Get replacement value for the search words
        #
        stDict = StateNames()
        st = os.path.basename(outputWS)[8:-4]

        if st in stDict:
            # Get state name from the geodatabase
            mdState = stDict[st]

        else:
            # Leave state name blank. In the future it would be nice to include a tile name when appropriate
            mdState = ""

        # Set date strings for metadata, based upon today's date
        #
        d = datetime.date.today()
        today = str(d.isoformat().replace("-",""))

        # Set fiscal year according to the current month. If run during January thru September,
        # set it to the current calendar year. Otherwise set it to the next calendar year.
        #
        if d.month > 9:
            fy = "FY" + str(d.year + 1)

        else:
            fy = "FY" + str(d.year)

        # Convert XML to tree format
        tree = ET.parse(mdExport)
        root = tree.getroot()

        # new citeInfo has title.text, edition.text, serinfo/issue.text
        citeInfo = root.findall('idinfo/citation/citeinfo/')

        if not citeInfo is None:
            # Process citation elements
            # title, edition, issue
            #
            for child in citeInfo:
                #PrintMsg("\t\t" + str(child.tag), 0)
                if child.tag == "title":
                    if child.text.find('xxSTATExx') >= 0:
                        child.text = child.text.replace('xxSTATExx', mdState)

                    elif mdState != "":
                        child.text = child.text + " - " + mdState

                elif child.tag == "edition":
                    if child.text == 'xxFYxx':
                        child.text = fy

                elif child.tag == "serinfo":
                    for subchild in child.iter('issue'):
                        if subchild.text == "xxFYxx":
                            subchild.text = fy

        # Update place keywords
        ePlace = root.find('idinfo/keywords/place')

        if not ePlace is None:
            #PrintMsg("\t\tplace keywords", 0)

            for child in ePlace.iter('placekey'):
                if child.text == "xxSTATExx":
                    child.text = mdState

                elif child.text == "xxSURVEYSxx":
                    child.text = surveyInfo

        # Update credits
        eIdInfo = root.find('idinfo')
        if not eIdInfo is None:
            #PrintMsg("\t\tcredits", 0)

            for child in eIdInfo.iter('datacred'):
                sCreds = child.text

                if sCreds.find("xxSTATExx") >= 0:
                    #PrintMsg("\t\tcredits " + mdState, 0)
                    child.text = child.text.replace("xxSTATExx", mdState)

                if sCreds.find("xxFYxx") >= 0:
                    #PrintMsg("\t\tcredits " + fy, 0)
                    child.text = child.text.replace("xxFYxx", fy)

                if sCreds.find("xxTODAYxx") >= 0:
                    #PrintMsg("\t\tcredits " + today, 0)
                    child.text = child.text.replace("xxTODAYxx", today)

        idPurpose = root.find('idinfo/descript/purpose')
        if not idPurpose is None:
            ip = idPurpose.text

            if ip.find("xxFYxx") >= 0:
                idPurpose.text = ip.replace("xxFYxx", fy)
                #PrintMsg("\t\tpurpose", 0)

        #  create new xml file which will be imported, thereby updating the table's metadata
        tree.write(mdImport, encoding="utf-8", xml_declaration=None, default_namespace=None, method="xml")

        # import updated metadata to the geodatabase table
        # Using three different methods with the same XML file works for ArcGIS 10.1
        #
        #PrintMsg("\t\tApplying metadata translators...")
        arcpy.MetadataImporter_conversion (mdImport, target)
        arcpy.ImportMetadata_conversion(mdImport, "FROM_FGDC", target, "DISABLED")
        #arcpy.ImportMetadata_conversion(mdImport, "FROM_FGDC", target, "DISABLED")

        # delete the temporary xml metadata file
        if os.path.isfile(mdImport):
            os.remove(mdImport)
            pass

        # delete metadata tool logs
        logFolder = os.path.dirname(env.scratchFolder)
        logFile = os.path.basename(mdImport).split(".")[0] + "*"


        currentWS = env.workspace
        env.workspace = logFolder
        logList = arcpy.ListFiles(logFile)

        for lg in logList:
            arcpy.Delete_management(lg)

        env.workspace = currentWS

        return True

    except:
        errorMsg()
        False

## ===================================================================================
def GetExtent(tmpPolys, iRaster):
    # Set output extent to that of the temporary 'tile' featurelayer, snapping
    # it to the appropriate NLCD coordinates
    try:

        # User searchcursor on polygon geometry to get extent
        #
        # Set default extent values
        xMin =  1000000000
        yMin =  1000000000
        xMax = -1000000000
        yMax = -1000000000

        # Assuming that input cooordinate system is Albers
        with arcpy.da.SearchCursor(tmpPolys, ["SHAPE@"]) as srcCursor:
            for row in srcCursor:
                pExtent = row[0].extent
                a1 = pExtent.XMin
                b1 = pExtent.YMin
                a2 = pExtent.XMax
                b2 = pExtent.YMax

                if a1 < xMin:
                    xMin = a1

                if b1 < yMin:
                    yMin = b1

                if a2 > xMax:
                    xMax = a2

                if b2 > yMax:
                    yMax = b2


        x1 = float(xMin)
        y1 = float(yMin)
        x2 = float(xMax)
        y2 = float(yMax)

        sExtent = str(x1) + " " + str(y1) + " " + str(x2) + " " + str(y2)

        # Begin SnapToNLCD Code
        theDesc = arcpy.Describe(tmpPolys)
        sr = theDesc.spatialReference
        inputSRName = sr.name
        theUnits = sr.linearUnitName

        if 'foot' in theUnits.lower():
            theUnits = "feet"

        elif theUnits.lower() == "meter":
            theUnits = "meters"

        # USA_Contiguous_Albers_Equal_Area_Conic_USGS_version (NAD83)
        #xNLCD = 532695
        #yNLCD = 1550295

        # Hawaii_Albers_Equal_Area_Conic  -345945, 1753875
        # Western_Pacific_Albers_Equal_Area_Conic  -2390975, -703265 est.
        # NAD_1983_Alaska_Albers  -2232345, 344805
        # WGS_1984_Alaska_Albers  Upper Left Corner:  -366405.000000 meters(X),  2380125.000000 meters(Y)
        # WGS_1984_Alaska_Albers  Lower Right Corner: 517425.000000 meters(X),  2032455.000000 meters(Y)
        # Puerto Rico 3092415, -78975 (CONUS works for both)

        if theUnits != "meters":
            PrintMsg("Projected coordinate system is " + inputSRName + "; units = '" + theUnits + "'", 0)
            raise MyError, "Unable to align raster output with this coordinate system"

        elif inputSRName == "USA_Contiguous_Albers_Equal_Area_Conic_USGS_version":
            xNLCD = 532695
            yNLCD = 1550295

        elif inputSRName == "Hawaii_Albers_Equal_Area_Conic":
            xNLCD = -29805
            yNLCD = 839235

        elif inputSRName == "NAD_1983_Alaska_Albers":
            xNLCD = -368805
            yNLCD = 1362465

        elif inputSRName == "WGS_1984_Albers":
            # New WGS 1984 based coordinate system matching USGS 2001 NLCD for Alaska
            xNLCD = -366405
            yNLCD = 2032455

        elif inputSRName == "Western_Pacific_Albers_Equal_Area_Conic":
            # WGS 1984 Albers for PAC Basin area
            xNLCD = -2390975
            yNLCD = -703265

        else:
            PrintMsg("Projected coordinate system is " + inputSRName + "; units = '" + theUnits + "'", 0)
            raise MyError, "Unable to align raster output with this coordinate system"

        # Calculate number of columns difference between KS NLCD and the input extent
        # Align with NLCD CONUS
        iCol = int((x1 - xNLCD) / 30)
        iRow = int((y1 - yNLCD) / 30)

        x1 = (30 * iCol) + xNLCD - 30
        y1 = (30 * iRow) + yNLCD - 30

        numCols = int(round(abs(x2 - x1) / 30))
        numRows = int(round(abs(y2 - y1) / 30))

        x2 = numCols * 30 + x1
        y2 = numRows * 30 + y1

        theExtent = str(x1) + " " + str(y1) + " " + str(x2) + " " + str(y2)
        # Format coordinate pairs as string
        sX1 = Number_Format(x1, 0, True)
        sY1 = Number_Format(y1, 0, True)
        sX2 = Number_Format(x2, 0, True)
        sY2 = Number_Format(y2, 0, True)
        sLen = 11
        sX1 = ((sLen - len(sX1)) * " ") + sX1
        sY1 = " X " + ((sLen - len(sY1)) * " ") + sY1
        sX2 = ((sLen - len(sX2)) * " ") + sX2
        sY2 = " X " + ((sLen - len(sY2)) * " ") + sY2

        env.extent = theExtent
        return theExtent
        # End of SnapToNLCD code

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def CheckSpatialReference(inputFC):
    # Make sure that the coordinate system is projected and units are meters
    try:
        desc = arcpy.Describe(inputFC)
        inputSR = desc.spatialReference

        if inputSR.type.upper() == "PROJECTED":
            if inputSR.linearUnitName.upper() == "METER":
                env.outputCoordinateSystem = inputSR
                return True

            else:
                raise MyError, os.path.basename(theGDB) + ": Input soil polygon layer does not have a valid coordinate system for gSSURGO"

        else:
            raise MyError, os.path.basename(theGDB) + ": Input soil polygon layer must have a projected coordinate system"

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def ConvertToRaster(theGDB, outputWS, theSnapRaster, iRaster, bTiled):
    # main function
    try:
        # Set geoprocessing environment
        #
        #bScratch = setScratchWorkspace()
        env.overwriteOutput = True
        env.workspace = theGDB
        arcpy.CheckOutExtension("Spatial")
        arcpy.env.compression = "LZ77"
        import shutil

        # Make sure that the env.scratchGDB is NOT Default.gdb. This causes problems for
        # some unknown reason.
        if os.path.basename(env.scratchGDB).lower() == "default.gdb" or os.path.basename(env.scratchWorkspace).lower() == "default.gdb":
            raise MyError, "Invalid scratch workspace setting (" + env.scratchWorkspace + ")"

        # turn off automatic Pyramid creation and Statistics calculation
        env.rasterStatistics = "NONE"
        env.pyramid = "PYRAMIDS 0"

        if bTiled:
            # Try creating a temporary folder for holding temporary rasters
            # This may allow the entire folder to be deleted at once instead of one raster at-a-time
            tmpFolder = os.path.join(env.scratchFolder, "TmpRasters")

            if arcpy.Exists(tmpFolder):
                shutil.rmtree(tmpFolder)

        if outputWS != "":
            # determine type of output workspace and use it to set the output raster format
            if outputWS[-4:].lower() in ['.gdb','.mdb']:
                rasterExt = ""

            else:
                rasterExt = ".img"

            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
                tileName = os.path.basename(theGDB)[os.path.basename(theGDB).rfind("_") + 1:os.path.basename(theGDB).rfind(".gdb")]
                outputRaster = os.path.join(outputWS, "MapunitRaster_" + tileName + "_" + str(iRaster) + "m" + rasterExt)

            else:
                raise MyError, "Required Spatial Analyst extension is not available"

        else:
            # create final raster in same workspace as input polygon featureclass
            outputWS = theGDB
            tileName = os.path.basename(theGDB)[os.path.basename(theGDB).rfind("_") + 1:os.path.basename(theGDB).rfind(".gdb")]
            outputRaster = os.path.join(theGDB, "MapunitRaster_"    + tileName + "_" + str(iRaster) + "m")

        inputFC = os.path.join(theGDB, "MUPOLYGON")

        if not arcpy.Exists(inputFC):
            raise MyError, "Could not find input featureclass: " + inputFC

        # Check input layer's coordinate system to make sure horizontal units are meters
        # set the output coordinate system for the raster (neccessary for PolygonToRaster)
        if CheckSpatialReference(inputFC) == False:
            return False

        # For rasters named using an attribute value, some attribute characters can result in
        # 'illegal' names.
        outputRaster = outputRaster.replace("-", "")

        if arcpy.Exists(outputRaster):
            arcpy.Delete_management(outputRaster)
            time.sleep(1)

        if arcpy.Exists(outputRaster):
            err = "Output raster (" + os.path.basename(outputRaster) + ") already exists"
            raise MyError, err

        start = time.time()   # start clock to measure total processing time
        #begin = time.time()   # start clock to measure set up time
        time.sleep(2)

        PrintMsg(" \nBeginning raster conversion process", 0)

        # Create Lookup table for storing MUKEY values
        #
        if bTiled:
            lu = os.path.join(theGDB, "Lookup")

        else:
            lu = os.path.join(env.scratchGDB, "Lookup")

        if arcpy.Exists(lu):
            arcpy.Delete_management(lu)

        # worked
        arcpy.CreateTable_management(os.path.dirname(lu), "Lookup")
        arcpy.AddField_management(lu, "CELLVALUE", "LONG")
        arcpy.AddField_management(lu, "MUKEY", "TEXT", "#", "#", "30")

        # Create list of MUKEY values from the MUPOLYGON featureclass
        #
        if not bTiled:
            # Create a list of map unit keys present in the MUPOLYGON featureclass
            #
            PrintMsg("\tGetting feature count and list of mukeys from input soil polygon layer...", 0)
            arcpy.SetProgressor("default", "Getting inventory of map units...")
            tmpPolys = "SoilPolygons"

            with arcpy.da.SearchCursor(inputFC, ("MUKEY",)) as srcCursor:
                # Create a unique, sorted list of MUKEY values in the MUPOLYGON featureclass
                mukeyList = [row[0] for row in srcCursor]
                polyCnt = len(mukeyList)
                mukeySet = set(mukeyList)
                mukeyList = sorted(list(mukeySet))
                del mukeySet

            if len(mukeyList) == 0:
                raise MyError, "Failed to get MUKEY values from " + inputFC

        # Create list of map unit keys AND areasymbols present in the MUPOLYGON featureclass
        #
        if bTiled:
            PrintMsg("\tGetting feature count and list of mukeys from input soil polygon layer...", 0)
            arcpy.SetProgressor("default", "Creating map unit inventory...")
            tileList = list()
            mukeyList = list()

            with arcpy.da.SearchCursor(inputFC, ["MUKEY", "AREASYMBOL"]) as cur:
                # Create a unique, sorted list of MUKEY values in the MUPOLYGON featureclass

                for rec in cur:
                    # get mukey
                    mukeyList.append(rec[0])

                    # get areasymbol for tile value
                    if not rec[1] in tileList:
                        tileList.append(rec[1])

                # create sorted and unique list of mukeys
                polyCnt = len(mukeyList)
                mukeySet = set(mukeyList)
                mukeyList = sorted(list(mukeySet))
                del mukeySet

            if len(mukeyList) == 0:
                raise MyError, "Failed to get MUKEY values from " + inputFC

            if len(tileList) == 1:
                # Only one tile in list
                # Switch to the 'un-tiled' mode
                bTiled = 0

        muCnt = len(mukeyList)

        # Load MUKEY values into Lookup table
        #
        PrintMsg("\tSaving " + Number_Format(muCnt, 0, True) + " MUKEY values for " + Number_Format(polyCnt, 0, True) + " polygons"  , 0)
        arcpy.SetProgressorLabel("Creating lookup table...")

        with arcpy.da.InsertCursor(lu, ("CELLVALUE", "MUKEY") ) as inCursor:
            for mukey in mukeyList:
                rec = mukey, mukey
                inCursor.insertRow(rec)

        # Add attribute index here.
        arcpy.AddIndex_management(lu, ["mukey"], "Indx_LU")
        #
        # End of Lookup table code

        # Match NLCD raster (snapraster)
        if theSnapRaster == "":
            fullExtent = SnapToNLCD(inputFC, iRaster)

            if fullExtent == "":
                err = "Please specify a Snap Raster"
                raise MyError, err

        else:
            PrintMsg(" \nSetting snap raster environment to: " + os.path.basename(theSnapRaster), 0)
            arcpy.snapRaster = theSnapRaster

        # Raster conversion process...
        #
        if bTiled:
            # Tiled raster process...
            #
            # Reset stopwatch for measuring the raster tile conversion plus mosaic

            #theMsg = "\tRaster conversion setup: " + elapsedTime(begin)
            #PrintMsg(theMsg, 1)

            #begin = time.time()
            PrintMsg(" \n\tCreating " + Number_Format(len(tileList), 0, True) + " raster tiles from " + os.path.join(os.path.basename(os.path.dirname(inputFC)), os.path.basename(inputFC)) + " featureclass", 0)

            # Create output folder
            arcpy.CreateFolder_management(env.scratchFolder, os.path.basename(tmpFolder))
            rasterList = list()
            i = 0

            for tile in tileList:
                i += 1
                tmpPolys = "poly_" + tile
                #tileRaster = os.path.join(env.scratchGDB, "r" + tile.lower())
                tileRaster = os.path.join(tmpFolder, tile.lower() + ".tif")
                rasterList.append(tileRaster)
                arcpy.SetProgressor("default", "Performing raster conversion for " + tile + "  (tile " + str(i) + " of " + str(len(tileList)) + ")...")
                wc = "AREASYMBOL = '" + tile + "'"
                arcpy.MakeFeatureLayer_management (inputFC, tmpPolys, wc)
                tileExtent = GetExtent(tmpPolys, iRaster)

                if tileExtent == "":
                    raise MyError, "Bad extent for " + tile

                arcpy.AddJoin_management (tmpPolys, "MUKEY", lu, "MUKEY", "KEEP_ALL")
                arcpy.PolygonToRaster_conversion(tmpPolys, "Lookup.CELLVALUE", tileRaster, "MAXIMUM_COMBINED_AREA", "", iRaster)
                arcpy.Delete_management(tmpPolys)
                del tmpPolys

            del tileRaster
            PrintMsg("\tMosaicing tiles to a single raster...", 0)
            env.extent = fullExtent
            arcpy.MosaicToNewRaster_management (rasterList, os.path.dirname(outputRaster), os.path.basename(outputRaster), "", "32_BIT_UNSIGNED", iRaster, 1, "MAXIMUM")

            # Cleanup the temporary tiled rasters
            # Should probably compact the scratchGDB afterwards...
            #
            arcpy.SetProgressor("step", "Cleaning up temporary raster tiles...", 1, len(rasterList), 1)
            #PrintMsg("\tCleaning up raster tiles...", 0)

            #for ras in rasterList:
            #    arcpy.Delete_management(ras)
            #    arcpy.SetProgressorPosition()


            del rasterList
            # Compact the scratch geodatabase after deleting all the rasters
            arcpy.Compact_management(env.scratchGDB)
            #theMsg = "\tPolygonToRaster conversion and mosaic: " + elapsedTime(begin)
            #PrintMsg(theMsg, 1)

        else:
            # Create a single raster, no tiles
            #
            # Reset stopwatch for measuring just the single raster conversion
            #begin = time.time()
            #PrintMsg(" \n" + (65 * "*"), 0)
            PrintMsg(" \nConverting featureclass " + os.path.join(os.path.basename(os.path.dirname(inputFC)), os.path.basename(inputFC)) + " to raster (" + str(iRaster) + " meter)", 0)
            #PrintMsg(" \n" + (65 * "*"), 0)
            tmpPolys = "poly_tmp"
            arcpy.MakeFeatureLayer_management (inputFC, tmpPolys)
            arcpy.AddJoin_management (tmpPolys, "MUKEY", lu, "MUKEY", "KEEP_ALL")

            arcpy.SetProgressor("default", "Running PolygonToRaster conversion...")
            #theMsg = "\tRaster conversion setup: " + elapsedTime(begin)
            #PrintMsg(theMsg, 1)

            env.extent = fullExtent
            arcpy.PolygonToRaster_conversion(tmpPolys, "Lookup.CELLVALUE", outputRaster, "MAXIMUM_COMBINED_AREA", "", iRaster)
            #theMsg = " \n\tPolygonToRaster conversion: " + elapsedTime(begin)
            #PrintMsg(theMsg, 1)

            # immediately delete temporary polygon layer to free up memory for the rest of the process
            arcpy.Delete_management(tmpPolys)

            # End of single raster process

        # Now finish up the single temporary raster
        #
        PrintMsg(" \nCompleting conversion process:", 0)
        # Reset the stopwatch for the raster post-processing
        #begin = time.time()

        # Remove lookup table
        if arcpy.Exists(lu):
            arcpy.Delete_management(lu)

        # ****************************************************
        # Build pyramids and statistics
        # ****************************************************
        if arcpy.Exists(outputRaster):
        #if arcpy.Exists(tmpRaster):
            time.sleep(3)
            arcpy.SetProgressor("default", "Calculating raster statistics...")
            PrintMsg("\tCalculating raster statistics...", 0)
            env.pyramid = "PYRAMIDS -1 NEAREST"
            arcpy.env.rasterStatistics = 'STATISTICS 100 100'
            #arcpy.BuildPyramidsandStatistics_management(os.path.dirname(outputRaster), "NONE", "BUILD_PYRAMIDS", "CALCULATE_STATISTICS")
            arcpy.CalculateStatistics_management (outputRaster, 1, 1, "", "OVERWRITE" )

            if CheckStatistics(outputRaster) == False:
                # For some reason the BuildPyramidsandStatistics command failed to build statistics for this raster.
                #
                # Try using CalculateStatistics while setting an AOI
                PrintMsg("\tInitial attempt to create statistics failed, trying another method...", 0)
                time.sleep(3)

                if arcpy.Exists(os.path.join(outputWS, "SAPOLYGON")):
                    # Try running CalculateStatistics with an AOI to limit the area that is processed
                    # if we have to use SAPOLYGON as an AOI, this will be REALLY slow
                    #arcpy.CalculateStatistics_management (outputRaster, 1, 1, "", "OVERWRITE", os.path.join(outputWS, "SAPOLYGON") )
                    arcpy.CalculateStatistics_management (outputRaster, 1, 1, "", "OVERWRITE" )

                if CheckStatistics(outputRaster) == False:
                    time.sleep(3)
                    PrintMsg("\tFailed in both attempts to create statistics for raster layer", 1)

            arcpy.SetProgressor("default", "Building pyramids...")
            PrintMsg("\tBuilding pyramids...", 0)
            arcpy.BuildPyramids_management(outputRaster, "-1", "NONE", "NEAREST", "DEFAULT", "", "SKIP_EXISTING")

            # ****************************************************
            # Add MUKEY to final raster
            # ****************************************************
            # Build attribute table for final output raster. Sometimes it fails to automatically build.
            PrintMsg("\tBuilding raster attribute table and updating MUKEY values", )
            arcpy.SetProgressor("default", "Building raster attrribute table...")
            arcpy.BuildRasterAttributeTable_management(outputRaster)

            # Add MUKEY values to final mapunit raster
            #
            arcpy.SetProgressor("default", "Adding MUKEY attribute to raster...")
            arcpy.AddField_management(outputRaster, "MUKEY", "TEXT", "#", "#", "30")
            with arcpy.da.UpdateCursor(outputRaster, ["VALUE", "MUKEY"]) as cur:
                for rec in cur:
                    rec[1] = rec[0]
                    cur.updateRow(rec)

            # Add attribute index (MUKEY) for raster
            arcpy.AddIndex_management(outputRaster, ["mukey"], "Indx_RasterMukey")

        else:
            err = "Missing output raster (" + outputRaster + ")"
            raise MyError, err

        # Compare list of original mukeys with the list of raster mukeys
        # Report discrepancies. These are usually thin polygons along survey boundaries,
        # added to facilitate a line-join.
        #
        arcpy.SetProgressor("default", "Looking for missing map units...")
        rCnt = int(arcpy.GetRasterProperties_management (outputRaster, "UNIQUEVALUECOUNT").getOutput(0))

        if rCnt <> muCnt:
            missingList = list()
            rList = list()

            # Create list of raster mukeys...
            with arcpy.da.SearchCursor(outputRaster, ("MUKEY",)) as rcur:
                for rec in rcur:
                    mukey = rec[0]
                    rList.append(mukey)

            missingList = list(set(mukeyList) - set(rList))
            queryList = list()
            for mukey in missingList:
                queryList.append("'" + mukey + "'")

            PrintMsg("\tDiscrepancy in mapunit count for new raster", 1)
            PrintMsg("\t\tInput polygon mapunits: " + Number_Format(muCnt, 0, True), 0)
            PrintMsg("\t\tOutput raster mapunits: " + Number_Format(rCnt, 0, True), 0)
            PrintMsg("\t\tMUKEY IN (" + ", ".join(queryList) + ") \n ", 0)

        # Update metadata file for the geodatabase
        #
        # Query the output SACATALOG table to get list of surveys that were exported to the gSSURGO
        #
        saTbl = os.path.join(theGDB, "sacatalog")
        expList = list()

        with arcpy.da.SearchCursor(saTbl, ("AREASYMBOL", "SAVEREST")) as srcCursor:
            for rec in srcCursor:
                expList.append(rec[0] + " (" + str(rec[1]).split()[0] + ")")

        surveyInfo = ", ".join(expList)
        time.sleep(2)
        arcpy.SetProgressorLabel("Updating metadata...")

        bMetaData = UpdateMetadata(outputWS, outputRaster, surveyInfo, iRaster)

        arcpy.SetProgressorLabel("Compacting metadata...")
        PrintMsg("\tCompacting geodatabase...", 0)
        arcpy.Compact_management(theGDB)
        arcpy.RefreshCatalog(os.path.dirname(outputRaster))

        if bTiled:

            if arcpy.Exists(tmpFolder):
                PrintMsg("\tCleaning up raster tiles...", 0)
                shutil.rmtree(tmpFolder)

        #theMsg = "\tPost-processing: " + elapsedTime(begin)
        #PrintMsg(theMsg, 1)

        theMsg = " \nProcessing time for " + outputRaster + ": " + elapsedTime(start) + " \n "
        PrintMsg(theMsg, 0)

        del outputRaster
        del inputFC

        #WriteToLog(theMsg, theRptFile)
        arcpy.CheckInExtension("Spatial")

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False
        arcpy.CheckInExtension("Spatial")

    except:
        errorMsg()
        return False
        arcpy.CheckInExtension("Spatial")

## ===================================================================================
## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import sys, string, os, arcpy, locale, traceback, math, time, datetime
import xml.etree.cElementTree as ET
from arcpy import env
from arcpy.sa import *

# Create the Geoprocessor object
try:
    if __name__ == "__main__":
        # get parameters
        theGDB = arcpy.GetParameterAsText(0)                   # required geodatabase containing MUPOLYGON featureclass
        outputWS = arcpy.GetParameterAsText(1)                # optional output workspace. If not set, output raster will be created in the same workspace
        theSnapRaster = arcpy.GetParameterAsText(2)           # optional snap raster. If not set, uses NLCD Albers USGS NAD83 for CONUS
        iRaster = arcpy.GetParameter(3)                       # output raster resolution
        bTiled = arcpy.GetParameter(4)                                         # boolean - split raster into survey-tiles and then mosaic

        env.overwriteOutput= True
        # Call function that does all of the work
        bRaster = ConvertToRaster(theGDB, outputWS, theSnapRaster, iRaster, bTiled)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e), 2)

except:
    errorMsg()
