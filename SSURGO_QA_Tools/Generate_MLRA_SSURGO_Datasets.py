# Import_SSURGO_Datasets_into_FGDB_ArcGIS10
#
# 4/27/2012
#
# Adolfo Diaz, MLRA GIS Specialist
# USDA - Natural Resources Conservation Service
# Madison, WI 53719
# adolfo.diaz@wi.usda.gov
# 608.662.4422 ext. 216
#
# Some subfunctions were directly copied and modified from Steve Peaslee's "Setup_UpdateSurvey_Dev.py."
# Thanks to Steve for doing the leg work on some of these subfunctions.
#
# This script was tested using ArcGIS 10 SP4. No known issues were encountered.
#
# Purpose: Import multiple existing SSURGO datasets, spatial and tabular data, into one File Geodatabase.
#
# The "Import SSURGO Datasets into FGDB ArcGIS10" tool will import SSURGO spatial and tabular data into a File Geodatabase
# and establish the necessary relationships between tables and feature classes in order to query component and horizon
# data and spatially view the distribution of that data at the mapunit level.  The output is a File Geodatabase
# that contains a feature dataset with 6 feature classes: MUPOLYGON, MUPOINT, MULINE, SAPOLYGON, FEATLINE
# and FEATPOINT.  Acres will be calculated if the input Spatial Reference is projected and the linear units
# are feet or meters.
#
# Usage: +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 1) Name of New File Geodatabase:
#        Name of the new File Geodatabase to create. This FGDB will contain the SSURGO spatial and tabular data.
#
#        Any alphanumeric string may be entered as long as the first character is ALPHA. Special characters
#        are not allowed in the name. Blank spaces will be converted to underscores.
#
#        It is recommended that you use an intuitive name that will describe the extent of your output.
#            ex) If your FGDB will contain every SSURGO dataset in Wisconsin than a logical name would be "WI_SSURGO".
#
#        Today's date will be appended to the name of the FGDB in the form of YYYYMMDD.
#            ex) "WI_SSURGO_20120301"
#
#        If a FGDB of the same name, incuding the date, exists, then the tool will attempt to delete it.
#        If deleting fails then the tool will exit.
# 2) Ouput Location:
#        Location where the output File Geodatabase will be created. User may type in a full path in this
#        field or browse to and select a folder.
#
#        The tool will exit if the path is invalid.
# 3) Location where SSURGO datasets_reside:
#        Browse to and select the parent directory that contains the SSURGO datasets you want imported
#        into the output FGDB.
#
#        SSURGO datasets must be structured the same as when they were received from the Soil Data Mart.
#        SSURGO dataset folders that are altered will simply be skipped.
#
#        If the Import Tabular Data option is checked, the tabular folder within the SSURGO dataset folder must
#        be present. If the tabular folder is absent then ONLY the spatial data will be imported for that
#        particular dataset.
# 4) Import Tabular Data (optional)
#        When this option is selected, empty SSURGO attribute tables will be created in the output FGDB.
#        The SSURGO text files will then be directly imported into their designated FGDB table. Text files do NOT
#        need to be imported into a SSURGO Access template since the tool does not utilize a SSURGO dataset's template.
#
#        The national 2002 SSURGO MS Access template database (Template DB version 34) will be used as to provide
#        the necessary table and field parameters when creating the empty tables.
#
#        Due to necessary reformatting of some text files, read AND write permissions are necessary in the SSURGO
#        dataset parent directory.
#
#        This option will also create relationships between tables and featureclasses and will store them in the
#        output geodatabase. These can be used by ArcMap and other ArcGIS applications to query component and horizon
#        information.
#
#        Each relationship class name is prefixed by an "x" so that the listing in ArcCatalog will display tables and
#        featureclasses on top and relationship classes last.
# 5) Output Coordinate System:
#        Output Coordinate System that will define the feature dataset and, subsequently, the feature classes.
#        Currently the tool only handles the following coordinate systems:
#            NAD83 - UTM Zone
#            NAD83 - State Plane (Meters or Feet)
#            NAD83 - Geographic Coordinate System (GRS 1980.prj)
#            NAD83 - USA Contiguous Albers Equal Area Conic USGS
#        The tool does not support datum transformations. If a specific SSURGO dataset's datum differs from
#        the input coordinate system than that SSURGO dataset will simply be skipped.
# 6) Clip Boundary (optional)
#        Optional Polygon layer that will be used to clip the featureclasses in the output FGDB.
#
#        The SAPOLYGON (Survey Area Polygon) feature class will not be clipped.
#
#        The tool first determines if there is overlap between the SSURGO Soil Survey Area layer (soilsa_a_*)
#        and the clip boundary. If overlap exists then the SSURGO dataset will be clipped, if necessary, before
#        importing into the FGDB. If no overlap exists then the SSURGO dataset is simply skipped.
#
#        If a SSURGO dataset is imported into the output FGDB and the Import Tabular Data option is checked,
#        then the entire tabular data is imported, not just for the mapunits that were imported.
#
#        If the clip boundary's coordinate system is different from the output coordinate system then the clip
#        boundary will be projected. If the clip boundary contains multiple features then it will be dissolved
#        into as a single part feature. The newly projected layer and the dissolve layer will be deleted once the
#        tool has executed correctly.
#
#        Depending on the size of your Soil Data Mart Library, you may want to isolate the SSURGO datasets of interest
#        since the tool will inevitably determine if overlap exists between the clip boundary and every SSURGO dataset.
#
# UPDATED: 3/14/2012
#   * removed much of the original code to import tabular data.  Per Steve Peaslee's suggestion, I incorporate CSVreader
#     module to open and read the SSURGO Text files.
#   * Make better use of tuples and dictionaries by creating them early on and passing them thoughout the code rather
#     create them every time I loope through a table.
#
# UPDATED: 4/27/2012
#   * Add functionality to calculate acres
#   * Add better error handling.
#   * Had to remove "print" function from this script otherwise it would fail from toolbox.
#
# Updated 7/27/2012
#   * BUG was found in the importTabular function that wouldn't properly clear rows.
#     As a result, NULL values were being populated with the last value that wasn't NULL.
#     deleting row cursor was added in line 1226 to assure a new line was started and not remain in memory

# UPDATED: 8/3/2012
#    * BUG: Realized that if the extent boundary was a feature class within a feature dataset, the newly projected layer
#      could not be written to the same feature dataset b/c its projection was not the same anymore.  Modified the
#      projectLayer to reproject dependent feature classess to the same geodatbase as a single feature class.
#
# UPDATED: 11/20/2012
#       Eric Wolfbrandt was having inconsistent issues with the script.  Sometimes it would execute correctly
#       and other times it would fail.  Steve Peaslee modified some of the code within the importTabular function
#       to remove continue statements from within if statements.  So many versions were created in an effort to
#       troubleshoot this problem that I decided to print the version of the script in the log file.
#
# Beginning of Functions
## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def print_exception():

    tb = sys.exc_info()[2]
    l = traceback.format_tb(tb)
    l.reverse()
    tbinfo = "".join(l)
    AddMsgAndPrint("\n\n----------ERROR Start-------------------",2)
    AddMsgAndPrint("Traceback Info: \n" + tbinfo + "Error Info: \n    " +  str(sys.exc_type)+ ": " + str(sys.exc_value) + "",2)
    AddMsgAndPrint("----------ERROR End-------------------- \n",2)

## ================================================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    # Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line

    #print msg

    try:

        #for string in msg.split('\n'):

        # Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError(msg)

    except:
        pass

## ===================================================================================
def getMLRAareaSymbolList(mlraTable, userMLRAchoice):
# Returns the actual region number from the first parameter.
# If the value has 1 integer than it should total 8 characters,
# last character will be returned.  Otherwise, value has 2 integers
# and last 2 will be returned.
# [u'WI001, u'WI003']

    try:
        areaSymbolList = []

        whereClause = "\"MLRA_CODE\" = '" + userMLRAchoice + "'"
        fields = ('AREASYMBOL')

        with arcpy.da.SearchCursor(mlraTable, fields, whereClause) as cursor:
            for row in cursor:
                areaSymbolList.append(row[0])

        del whereClause, fields

        return areaSymbolList

    except:
        print_exception
        return ""

## ===================================================================================
def validateSSAs(surveyList, wssLibrary):
# checks for missing SSURGO datasets in the wssLibrary folder.  If any SSURGO dataset is
# missing return "".  All ssurgo datasets must be present in order to reconstruct the
# regional Transactional database.  Also checks for duplicate ssurgo datasets in the
# wssLibrary.  Return "" if duplicates are found.  Cannot have duplicates b/c this will
# cause topology overlap and the duplicate datasets may be of different versions.
# Returns a dictionary containing areasymbol & ssurgo dataset path
#
# Unlike the Regional tool, this validate can have missing SSAs.
#
# {'ID001': 'C:\\Temp\\junk\\soils_id001', 'ID002': 'C:\\Temp\\junk\\wss_SSA_ID002_soildb_ID_2003_[2012-08-13]}'

    try:
        import collections

        ssurgoDatasetDict = dict()  # [AreaSymbol] = C:\Temp\junk\soils_ca688
        wssLibraryList = []  # ['WI025','WI027']

        # get a list of all files in wssLibrary folder
        for file in os.listdir(wssLibrary):

            # Full path to individual file in wssLibrary folder
            filePath = os.path.join(wssLibrary,file)

            # extract areasymbol name if file is a directory and a ssurgo dataset
            if os.path.isdir(filePath):

                # folder is named in WSS 3.0 format i.e. 'wss_SSA_WI063_soildb_WI_2003_[2012-06-27]'
                if file.find("wss_SSA_") > -1:
                    SSA = file[file.find("SSA_") + 4:file.find("soildb")-1].upper()
                    wssLibraryList.append(SSA)

                    if SSA in surveyList:
                        ssurgoDatasetDict[SSA] = os.path.join(wssLibrary,file)
                    del SSA

                # folder is named according to traditional SDM format i.e. 'soils_wa001'
                elif file.find("soil_") > -1 or file.find("soils_") > -1:
                    SSA = file[-5:].upper()
                    wssLibraryList.append(SSA)

                    if SSA in surveyList:
                        ssurgoDatasetDict[SSA] = os.path.join(wssLibrary,file)
                    del SSA

                # Not a SSURGO dataset; some other folder
                else:
                    pass

        # ------------------------------------------------------------------------ No Datasets in Library
        if len(wssLibraryList) < 1:
            AddMsgAndPrint("\n\tNo SSURGO datasets were found in " + os.path.dirname(wssLibrary) + " directory",2)
            return ""

        # ------------------------------------------------------------------------ Missing SSURGO Datasets
        missingSSAList = []

        # check for missing SSURGO datasets in wssLibrary.  Print missing datasets and return False.
        for survey in surveyList:
            if not survey in wssLibraryList:
                missingSSAList.append(survey)

        if len(missingSSAList) > 0:
            AddMsgAndPrint("\n\tThe following SSURGO datasets are missing from your local library:",2)
            for survey in missingSSAList:
                AddMsgAndPrint( "\t\t" + survey,2)
                ssurgoDatasetDict.pop(survey, None)

        # ---------------------------------------------------------------------- Duplicate SSURGO Datasets
        # check for duplicate SSURGO SSAs in wssLibrary.  Print duplicates.  Return False only if the duplicates affects those surveys in the regional list.
        # Cannot have duplicates b/c of different versions and overlap
        if len([x for x, y in collections.Counter(wssLibraryList).items() if y > 1]):

            duplicateSSAs = []

            for survey in [x for x, y in collections.Counter(wssLibraryList).items() if y > 1]:
                if survey in ssurgoDatasetDict:
                    duplicateSSAs.append(survey)

            if len(duplicateSSAs) >  0:
                AddMsgAndPrint("\n\tThe following are duplicate SSURGO datasets found in " + os.path.basename(wssLibrary) + " directory:",2)
                for survey in duplicateSSAs:
                    AddMsgAndPrint( "\t\t" + survey,2)
                    ssurgoDatasetDict.pop(survey, None)

        # -------------------------------------------------------------------- Make sure Datum is either NAD83 or WGS84 and soils layer is not missing
        wrongDatum = []
        missingSoilLayer = []

        for survey in ssurgoDatasetDict:
            soilShpPath = os.path.join(os.path.join(ssurgoDatasetDict[survey],"spatial"),"soilmu_a_" + survey.lower() + ".shp")

            if arcpy.Exists(soilShpPath):
                if not compareDatum(soilShpPath):
                    wrongDatum.append(survey)
                    ssurgoDatasetDict.pop(survey, None)
            else:
                missingSoilLayer.append(survey)

        if len(wrongDatum) > 0:
            AddMsgAndPrint("\n\tThe following local SSURGO datasets have a Datum other than WGS84 or NAD83:",2)
            for survey in wrongDatum:
                AddMsgAndPrint( "\t\t" + survey,2)
                ssurgoDatasetDict.pop(survey, None)

        if len(missingSoilLayer) > 0:
            AddMsgAndPrint("\n\tThe following local SSURGO datasets are missing their soils shapefile:",2)
            for survey in missingSoilLayer:
                AddMsgAndPrint( "\t\t" + survey,2)
                ssurgoDatasetDict.pop(survey, None)

        # --------------------------------------------------------------------  At this point everything checks out; Return Dictionary!
        del wssLibraryList, missingSSAList, wrongDatum, missingSoilLayer
        return ssurgoDatasetDict

    except:
        AddMsgAndPrint("\n\tUnhandled exception (validateSSAs)", 2)
        print_exception()
        return ""


## ================================================================================================================
def parseDatumAndProjection(spatialReference):
    # This functions extracts the Datum and Projection name from the user-defined
    # spatial Reference.  If the Datum is NAD83 then a transformation method will
    # set as an env transformation method other wise none will be applied.
    # Datum and Projection Name are returned.
    #
    # Not sure if this even helps b/c the append tool does not honor env
    # trans method.  Does this mean I have to project?  I tried 3 differnent apppend
    # tests and they all generated the same results leading me that ArcGIS intelligently
    # applies a transformation method but I can't figure out which one.  If I look at the
    # results of the append tool and look at the env settings the trans method is set
    # to NAD27 to NAD83.....WTF???

    try:

        #---------- Gather Spatial Reference info ----------------------------
        # Create the GCS WGS84 spatial reference and datum name using the factory code
        WGS84_sr = arcpy.SpatialReference(4326)
        WGS84_datum = WGS84_sr.datumName

        # Parse Datum and GCS from user spatial reference
        userDatum_Start = spatialReference.find("DATUM") + 7
        userDatum_Stop = spatialReference.find(",", userDatum_Start) - 1
        userDatum = spatialReference[userDatum_Start:userDatum_Stop]

        userProjection_Start = spatialReference.find("[") + 2
        userProjection_Stop = spatialReference.find(",",userProjection_Start) - 1
        userProjectionName = spatialReference[userProjection_Start:userProjection_Stop]

        del userDatum_Start
        del userDatum_Stop
        del userProjection_Start
        del userProjection_Stop

        if userProjectionName != "" or userDatum != "":

            AddMsgAndPrint("\nUser-Defined Spatial Reference System:",0)
            AddMsgAndPrint("\tCoordinate System: " + userProjectionName,0)
            AddMsgAndPrint("\tDatum: " + userDatum,0)

            # user spatial reference is the same as WGS84
            if WGS84_datum == userDatum:
                AddMsgAndPrint("\n\tNo Datum Transformation method required", 1)

                return userDatum,userProjectionName

            # user datum is NAD83; apply trans method based on user input
            elif userDatum == "D_North_American_1983":

                if AOI == "CONUS":
                    tm = "NAD_1983_To_WGS_1984_5"

                elif AOI == "Alaska":
                    tm = "NAD_1983_To_WGS_1984_5"

                elif AOI == "Hawaii":
                    tm = "NAD_1983_To_WGS_1984_3"

                elif AOI == "Puerto Rico and U.S. Virgin Islands":
                    tm = "NAD_1983_To_WGS_1984_5"

                elif AOI == "Other":
                    tm = "NAD_1983_To_WGS_1984_1"
                    PrintMsg(" \n\tWarning! No coordinate shift will being applied", 0)

                else:
                    raise MyError, "Invalid geographic region (" + AOI + ")"

                arcpy.env.outputCoordinateSystem = spatialReference
                arcpy.env.geographicTransformations = tm
                AddMsgAndPrint("\n\tUsing Datum Transformation Method '" + tm + "' for " + AOI, 1)

                return userDatum,userProjectionName

            # user datum was something other than NAD83
            else:
                raise MyError, "\n\tWarning! No Datum Transformation could be applied to " + userProjectionName
                return "",""

        # Could not parse CS name and datum
        else:
            raise MyError, "\n\tCould not extract Spatial Reference Properties........Halting import process"
            return "",""

    except MyError, e:
        AddMsgAndPrint(str(e) + "\n", 2)
        return "",""

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return "",""

    except:
        AddMsgAndPrint(" \nUnhandled exception (parseDatumAndProjection)", 2)
        print_exception()
        return "",""

## ================================================================================================================
def compareDatum(fc):
    # Return True if fc datum is either WGS84 or NAD83

    try:
        # Create Spatial Reference of the input fc. It must first be converted in to string in ArcGIS10
        # otherwise .find will not work.
        fcSpatialRef = str(arcpy.CreateSpatialReference_management("#",fc,"#","#","#","#"))
        FCdatum_start = fcSpatialRef.find("DATUM") + 7
        FCdatum_stop = fcSpatialRef.find(",", FCdatum_start) - 1
        fc_datum = fcSpatialRef[FCdatum_start:FCdatum_stop]

        # Create the GCS WGS84 spatial reference and datum name using the factory code
        WGS84_sr = arcpy.SpatialReference(4326)
        WGS84_datum = WGS84_sr.datumName

        NAD83_datum = "D_North_American_1983"

        # Input datum and output datum are the same, no transformation required
        if fc_datum == WGS84_datum or fc_datum == NAD83_datum:
            del fcSpatialRef
            del FCdatum_start
            del FCdatum_stop
            del fc_datum
            del WGS84_sr
            del WGS84_datum
            del NAD83_datum

            return True

        else:
            del fcSpatialRef
            del FCdatum_start
            del FCdatum_stop
            del fc_datum
            del WGS84_sr
            del WGS84_datum
            del NAD83_datum

            return False

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        print_exception()
        return False

## ================================================================================================================
def createFGDB(ssaOffice,outputFolder):
    # This function will Create the RTSD File Geodatabase by importing an XML workspace schema.
    # Depending on what region is being created is what .xml file will be used.
    # Schema includes 2 feature datasets: FD_RTSD & Project Record. 6 feature classes will be created
    # within FD_RTSD along with a topology.  1 feature class will be created within the ProjectRecord
    # FD.  Return new name of RTSD otherwise return empty string.

    import datetime

    try:
        arcpy.SetProgressor("step", "Creating FGDB for " + ssaOffice, 0, 3, 1)
        arcpy.SetProgressorLabel("Creating FGDB for " + ssaOffice)

        targetGDB = os.path.join(outputFolder,"TempMLRA.gdb")

        # Delete TempMLRA.gdb
        if arcpy.Exists(targetGDB):
            arcpy.Delete_management(targetGDB)

        arcpy.CreateFileGDB_management(outputFolder,"TempMLRA")
        arcpy.SetProgressorPosition()

        # New fiscal year if month October, November and December
        if datetime.datetime.now().strftime("%m") > 9 and datetime.datetime.now().strftime("%m") < 13:
            FY = "FY" + str(datetime.datetime.now().strftime("%y") +1)
        else:
            FY = "FY" + str(datetime.datetime.now().strftime("%y"))

        # Alaska  = NAD_1983_Alaska_Albers
        if ssaOffice in ('1-FAI','1-HOM','1-PAL'):
            xmlFile = os.path.dirname(sys.argv[0]) + os.sep + "MLRA_XMLWorkspace_Alaska.xml"

        # Hawaii - Hawaii_Albers_Equal_Area_Conic WGS84; 1 SSA office for all of Pacific extent
        elif ssaOffice in ('2-KEA'):
            xmlFile = os.path.dirname(sys.argv[0])+ os.sep + "MLRA_XMLWorkspace_Hawaii.xml"

        # CONUS - USA Contiguous Albers Equal Area Conic USGS version NAD83
        else:
            xmlFile = os.path.join(os.path.dirname(sys.argv[0]),"MLRA_XMLWorkspace_CONUS.xml")

        newName = os.path.join(outputFolder,"MLRA_" +  ssaOffice + "_" + FY + ".gdb")

        # Delete newName MLRA gdb if it exists
        if arcpy.Exists(newName):
            try:
                AddMsgAndPrint("\t" + os.path.basename(newName) + " already exists deleting",1)
                arcpy.Delete_management(os.path.join(outputFolder,newName + ".gdb"))

            except:
                AddMsgAndPrint("\t Failed to Delte " + os.path.join(outputFolder,newName + ".gdb",2))
                return ""

        arcpy.Rename_management(targetGDB,newName)

        arcpy.RefreshCatalog(newName)
        arcpy.SetProgressorPosition()

        env.workspace = newName

        # Return false if xml file is not found and delete targetGDB
        if not arcpy.Exists(xmlFile):
            AddMsgAndPrint(os.path.basename(xmlFile) + " was not found!",2)
            arcpy.Delete_management(targetGDB)
            return ""

        arcpy.ImportXMLWorkspaceDocument_management(newName, xmlFile, "SCHEMA_ONLY", "DEFAULTS")
        arcpy.SetProgressorPosition()

        AddMsgAndPrint("\n\tSuccessfully Created MLRA File GDB: " + os.path.basename(newName),0)

        del targetGDB,FY,xmlFile

        # path to where the new MLRA gdb
        return newName

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return ""

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        print_exception()
        return ""

## ===============================================================================================================
def GetTableAliases(ssurgoTemplateLoc, tblAliases):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores physical names (key) and aliases (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}
    # Fieldnames are Physical Name = AliasName,IEfilename

    try:

        # Open mdstattabs table containing information for other SSURGO tables
        theMDTable = "mdstattabs"
        #env.workspace = ssurgoTemplateLoc

        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if arcpy.Exists(os.path.join(ssurgoTemplateLoc,theMDTable)):

            nameOfFields = ["tabphyname","tablabel","iefilename"]
            rows = arcpy.da.SearchCursor(os.path.join(ssurgoTemplateLoc,theMDTable),nameOfFields)

            for row in rows:
                # read each table record and assign 'tabphyname' and 'tablabel' to 2 variables
                physicalName = row[0]
                aliasName = row[1]
                importFileName = row[2]

                # i.e. {chaashto:'Horizon AASHTO',chaashto}; will create a one-to-many dictionary
                # As long as the physical name doesn't exist in dict() add physical name
                # as Key and alias as Value.
                if not tblAliases.has_key(physicalName):
                    tblAliases[physicalName] = (aliasName,importFileName)

                del physicalName
                del aliasName
                del importFileName

            del theMDTable
            del nameOfFields
            del rows
            del row

            return tblAliases

        else:
            # The mdstattabs table was not found
            AddMsgAndPrint("\nMissing \"mdstattabs\" table", 2)
            return tblAliases

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return tblAliases

    except:
        AddMsgAndPrint("Unhandled exception (GetTableAliases)", 2)
        print_exception()
        return tblAliases

## ===============================================================================================================
def importTabularData(tabularFolder, tblAliases):
    # This function will import the SSURGO .txt files from the tabular folder.
    # tabularFolder is the absolute path to the tabular folder.
    # tblAliases is a list of the physical name of the .txt file along with the Alias name.
    # Return False if error occurs, true otherwise.  there is a list of files that will not be
    # imported under "doNotImport".  If the tabular folder is empty or there are no text files
    # the survey will be skipped.

    try:
        env.workspace = FGDBpath

        # Loops through the keys in the tblAliases dict() and puts the 2nd value
        # (iefilename) and key (tabphyname) in a list.  The list is then sorted
        # so that SSURGO text files can be imported in alphabetical sequence.
        GDBTables = tblAliases.keys()
        GDBTables.sort()

        # Do not import the following SSURGO text files.  Most are metadata text files that are
        # used within the access template and/or SDV.  No need to import them into GDB.
        doNotImport = ["featline","featpoint","month","msdomdet","msdommas","msidxdet","msidxmas","msrsdet",
                       "msrsmas","mstab","mstabcol","mupoint","muline","sapolygon""version"]

        # if the tabular directory is empty return False
        if len(os.listdir(tabularFolder)) < 1:
            AddMsgAndPrint("\t\tTabular Folder is Empty!",1)
            return False

        # Static Metadata Table that records the metadata for all columns of all tables
        # that make up the tabular data set.
        mdstattabsTable = FGDBpath + os.sep + "mdstattabs"

        #AddMsgAndPrint(" \tImporting Tabular Data for: " + SSA,0)

        # set progressor object which allows progress information to be passed for every merge complete
        arcpy.SetProgressor("step", "Importing Tabular Data for " + SSA, 0, len(GDBTables), 1)

        # For each item in sorted keys
        for GDBtable in GDBTables:

            # physicalName (tablabel,iefilename)
            # i.e. {chaashto:'Horizon AASHTO',chaashto}
            x = tblAliases[GDBtable]

            # Alias Name: tablabel field (Table Label field)
            # x[0] = Horizon AASHTO
            aliasName = x[0]

            # Import Export File Name: iefilename
            # x[1] = chaashto
            iefileName = x[1]

            if not iefileName in doNotImport:

                # Absolute Path to SSURGO text file
                txtPath = tabularFolder + os.sep + iefileName + ".txt"

                # continue if SSURGO text file exists.
                if os.path.exists(txtPath):

                    # Next 4 lines are strictly for printing formatting to figure out the spacing between.
                    # the short and full name.  8 is the max num of chars from the txt tables + 2 = 10
                    # Played around with numbers until I liked the formatting.
                    theTabLength = 20 - len(iefileName)
                    theTab = " " * theTabLength
                    theAlias = theTab + "(" + aliasName + ")"
                    theRecLength = " " * (48 - len(aliasName))

                    del theTabLength
                    del theTab

                    # Continue if the text file contains values. Not Empty file
                    if os.path.getsize(txtPath) > 0:

                        # Put all the field names in a list; used to initiate insertCursor object
                        fieldList = arcpy.ListFields(GDBtable)
                        nameOfFields = []

                        for field in fieldList:

                            if field.type != "OID":
                                nameOfFields.append(field.name)

                        del fieldList, field

                        # The csv file might contain very huge fields, therefore increase the field_size_limit:
                        # Exception thrown with IL177 in legend.txt.  Not sure why, only 1 record was present
                        csv.field_size_limit(sys.maxsize)

                        # Number of records in the SSURGO text file
                        textFileRecords = sum(1 for row in csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"'))

                        # Initiate Cursor to add rows
                        cursor = arcpy.da.InsertCursor(GDBtable,nameOfFields)

                        # counter for number of records successfully added; used for reporting
                        numOfRowsAdded = 0
                        reader = csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"')

                        try:

                            # Return a reader object which will iterate over lines in txtPath
                            for rowInFile in reader:

                                # replace all blank values with 'None' so that the values are properly inserted
                                # into integer values otherwise insertRow fails
                                newRow = [None if value =='' else value for value in rowInFile]

                                cursor.insertRow(newRow)
                                numOfRowsAdded += 1

                                del newRow

                        except:
                            AddMsgAndPrint("\n\t\tError inserting record in table: " + GDBtable,2)
                            AddMsgAndPrint("\t\t\tRecord # " + str(numOfRowsAdded + 1),2)
                            AddMsgAndPrint("\t\t\tValue: " + str(newRow),2)
                            print_exception()

                        #AddMsgAndPrint(" \t\t\t--> " + iefileName + theAlias + theRecLength + " Records Added: " + str(splitThousands(numOfRowsAdded)),0)

                        # compare the # of rows inserted with the number of valid rows in the text file.
                        if numOfRowsAdded != textFileRecords:
                            AddMsgAndPrint("\t\t\t Incorrect # of records inserted into: " + GDBtable, 2 )
                            AddMsgAndPrint("\t\t\t\t TextFile records: " + str(textFileRecords),2)
                            AddMsgAndPrint("\t\t\t\t Records Inserted: " + str(numOfRowsAdded),2)

                        del GDBtable, x, aliasName, iefileName, txtPath, theAlias, theRecLength, nameOfFields, textFileRecords, rowInFile, numOfRowsAdded, cursor, reader

##                    else:
##                        #AddMsgAndPrint(" \t\t\t--> " + iefileName + theAlias + theRecLength + " Records Added: 0",0)

                else:
                    AddMsgAndPrint("\t\t\t--> " + iefileName + " does NOT exist tabular folder.....SKIPPING ",2)

            arcpy.SetProgressorPosition()

        # Resets the progressor back to is initial state
        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel(" ")

        del GDBTables, doNotImport, mdstattabsTable

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + SSA,2)
        return False

    except csv.Error, e:
        AddMsgAndPrint('\nfile %s, line %d: %s' % (txtPath, reader.line_num, e))
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + SSA,2)
        print_exception()
        return False

    except IOError as (errno, strerror):
        AddMsgAndPrint("\nI/O error({0}): {1}".format(errno, strerror) + " File: " + txtPath + " \n",2)
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + SSA,2)
        print_exception()
        return False

    except:
        AddMsgAndPrint("\nUnhandled exception (importTabularData) \n", 2)
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + SSA,2)
        print_exception()
        return False
## ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        print_exception()
        return someNumber

## ===============================================================================================================
def CreateTableRelationships(tblAliases):
    # Create relationship classes between standalone attribute tables.
    # Relate parameters are pulled from the mdstatrhipdet and mdstatrshipmas tables,
    # thus it is required that the tables must have been copied from the template database.

    # Test option of getting aliases from original template database vs. output database
    # set workspace to original template database
    # env.workspace = InputDB
    # or
    # set workspace to output database.....This script uses output database as workspace
    # WAIT, take that back.  Using the GDB as a workspace creates locks.  Specifically, the
    # MakeQueryTable tool creates .rd and .sr locks that are only deleted if Arc is restarted.
    # Currently use the ssurgoTemplate to create a query table so that it doesn't lock the .GDB
    # Subfunction is written by Steve Peaslee and modified by Adolfo Diaz.
    #
    #Modified From Steve Peaslee's Setup_UpdateSurvey

    #AddMsgAndPrint(" \n**********************************************************************************************************************",1)
    #AddMsgAndPrint(" \n\tVerifying relationships",0)
    AddMsgAndPrint("\tCreating Relationships between Featureclasses and Tables", 0)

    # set progressor object which allows progress information to be passed for every relationship complete

    if arcpy.Exists(os.path.join(FGDBpath, "mdstatrshipdet")) and arcpy.Exists(os.path.join(FGDBpath,"mdstatrshipmas")):
        try:
        # Create new Table View to contain results of join between relationship metadata tables

            fld1 = "mdstatrshipmas.ltabphyname"
            fld2 = "mdstatrshipdet.ltabphyname"
            fld3 = "mdstatrshipmas.rtabphyname"
            fld4 = "mdstatrshipdet.rtabphyname"
            fld5 = "mdstatrshipmas.relationshipname"
            fld6 = "mdstatrshipdet.relationshipname"

            # GDB format
            SQLtxt = "" + fld1 + " = " + fld2 + " AND " + fld3 + " = " + fld4 + " AND " + fld5 + " = " + fld6 + ""

            # ssurgoTemplate Format (.mdb)
            #SQLtxt = "[" + fld1 + "] = [" + fld2 + "] AND [" + fld3 + "] = [" + fld4 + "] AND [" + fld5 + "] = [" + fld6 + "]"

            # Create in-memory table view to supply parameters for each relationshipclasses (using SSURGO 2.0 mdstatrshipdet and mdstatrshipmas tables)
            inputTables = FGDBpath + os.sep + "mdstatrshipdet;" + FGDBpath + os.sep + "mdstatrshipmas"
            queryTableName = "RelshpInfo"

            # Use this one for env.workspace = FGDBpath: includes objectID but I don't think it is needed
            #fieldsList = "mdstatrshipdet.OBJECTID OBJECTID;mdstatrshipdet.ltabphyname LTABPHYNAME;mdstatrshipdet.rtabphyname RTABPHYNAME;mdstatrshipdet.relationshipname RELATIONSHIPNAME;mdstatrshipdet.ltabcolphyname LTABCOLPHYNAME;mdstatrshipdet.rtabcolphyname RTABCOLPHYNAME;mdstatrshipmas.cardinality CARDINALITY"
            fieldsList = "mdstatrshipdet.ltabphyname LTABPHYNAME;mdstatrshipdet.rtabphyname RTABPHYNAME;mdstatrshipdet.relationshipname RELATIONSHIPNAME;mdstatrshipdet.ltabcolphyname LTABCOLPHYNAME;mdstatrshipdet.rtabcolphyname RTABCOLPHYNAME;mdstatrshipmas.cardinality CARDINALITY"

            arcpy.MakeQueryTable_management(inputTables, queryTableName, "NO_KEY_FIELD", "", fieldsList, SQLtxt)

            if not arcpy.Exists(queryTableName):
                AddMsgAndPrint("\nFailed to create metadata table required for creation of relationshipclasses",2)
                return False

            # Fields in RelshpInfo table view
            # OBJECTID, LTABPHYNAME, RTABPHYNAME, RELATIONSHIPNAME, LTABCOLPHYNAME, RTABCOLPHYNAME, CARDINALITY
            # Open table view and step through each record to retrieve relationshipclass parameters
            rows = arcpy.SearchCursor(queryTableName)

            arcpy.SetProgressor("step", "Verifying Tabular Relationships", 0, int(arcpy.GetCount_management(FGDBpath + os.sep + "mdstatrshipdet").getOutput(0)), 1)
            arcpy.SetProgressorLabel("Verifying Tabular Relationships")

            recNum = 0

            #env.workspace = FGDBpath

            for row in rows:

                # Get relationshipclass parameters from current table row
                # Syntax for CreateRelationshipClass_management (origin_table, destination_table,
                # out_relationship_class, relationship_type, forward_label, backward_label,
                # message_direction, cardinality, attributed, origin_primary_key,
                # origin_foreign_key, destination_primary_key, destination_foreign_key)
                #
                #AddMsgAndPrint("Reading record " + str(recNum), 1)
                originTable = row.LTABPHYNAME
                destinationTable = row.RTABPHYNAME

                originTablePath = FGDBpath + os.sep + row.LTABPHYNAME
                destinationTablePath = FGDBpath + os.sep + row.RTABPHYNAME

                # Use table aliases for relationship labels
                relName = "x" + originTable.capitalize() + "_" + destinationTable.capitalize()

                originPKey = row.LTABCOLPHYNAME
                originFKey = row.RTABCOLPHYNAME

                # create Forward Label i.e. "> Horizon AASHTO Table"
                if tblAliases.has_key(destinationTable):
                    fwdLabel = "> " + tblAliases.get(destinationTable)[0] + " Table"

                else:
                    fwdLabel = destinationTable + " Table"
                    AddMsgAndPrint("Missing key: " + destinationTable, 2)

                # create Backward Label i.e. "< Horizon Table"
                if tblAliases.has_key(originTable):
                    backLabel = "<  " + tblAliases.get(originTable)[0] + " Table"

                else:
                    backLabel = "<  " + originTable + " Table"
                    AddMsgAndPrint("Missing key: " + originTable, 2)

                theCardinality = row.CARDINALITY.upper().replace(" ", "_")

                # Check if origin and destination tables exist
                if arcpy.Exists(originTablePath) and arcpy.Exists(destinationTablePath):

                    # The following 6 lines are for formatting only
                    formatTab1 = 15 - len(originTable)
                    formatTabLength1 = " " * formatTab1 + "--> "

                    formatTab2 = 19 - len(destinationTable)
                    formatTabLength2 = " " * formatTab2 + "--> "

                    formatTab3 = 12 - len(str(theCardinality))
                    formatTabLength3 = " " * formatTab3 + "--> "

                    # relationship already exists; print out the relationship name
                    if arcpy.Exists(relName):
                        AddMsgAndPrint(" \t" + originTable +  formatTabLength1 + destinationTable + formatTabLength2 + theCardinality + formatTabLength3 + relName, 0)

                    # relationship does not exist; create it and print out
                    else:
                        arcpy.CreateRelationshipClass_management(originTablePath, destinationTablePath, relName, "SIMPLE", fwdLabel, backLabel, "NONE", theCardinality, "NONE", originPKey, originFKey, "","")
                        AddMsgAndPrint(" \t" + originTable +  formatTabLength1 + destinationTable + formatTabLength2 + theCardinality + formatTabLength3 + relName, 0)

                    # delete formatting variables
                    del formatTab1, formatTabLength1, formatTab2, formatTabLength2, formatTab3, formatTabLength3
                else:
                    AddMsgAndPrint("        <-- " + relName + ": Missing input tables (" + originTable + " or " + destinationTable + ")", 0)

                del originTable, destinationTable, originTablePath, destinationTablePath, relName, originPKey, originFKey, fwdLabel, backLabel, theCardinality

                recNum = recNum + 1

                arcpy.SetProgressorPosition() # Update the progressor position

            arcpy.ResetProgressor()  # Resets the progressor back to is initial state
            arcpy.SetProgressorLabel(" ")

            del fld2, fld1, fld3, fld4, fld5, fld6, SQLtxt, inputTables, fieldsList, queryTableName, rows, recNum

            # Establish Relationship between tables and Spatial layers
            # The following lines are for formatting only
            formatTab1 = 15 - len(soilFC)
            formatTabLength1 = " " * formatTab1 + "--> "

            #AddMsgAndPrint(" \nCreating Relationships between Featureclasses and Tables:", 1)

            # Relationship between MUPOLYGON --> Mapunit Table
            if not arcpy.Exists("xSpatial_MUPOLYGON_Mapunit"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + soilFC, FGDBpath + os.sep + "mapunit", FGDBpath + os.sep + "xSpatial_MUPOLYGON_Mapunit", "SIMPLE", "> Mapunit Table", "< MUPOLYGON_Spatial", "NONE","ONE_TO_ONE", "NONE","MUKEY","mukey", "","")
            #AddMsgAndPrint(" \t" + soilFC + formatTabLength1 + "mapunit" + "            --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_MUPOLYGON_Mapunit", 0)

            # Relationship between MUPOLYGON --> Mapunit Aggregate Table
            if not arcpy.Exists("xSpatial_MUPOLYGON_Muaggatt"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + soilFC, FGDBpath + os.sep + "muaggatt", FGDBpath + os.sep + "xSpatial_MUPOLYGON_Muaggatt", "SIMPLE", "> Mapunit Aggregate Table", "< MUPOLYGON_Spatial", "NONE","ONE_TO_ONE", "NONE","MUKEY","mukey", "","")
            #AddMsgAndPrint(" \t" + soilFC + formatTabLength1 + "muaggatt" + "           --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_MUPOLYGON_Muaggatt", 0)

            # Relationship between SAPOLYGON --> Legend Table
            if not arcpy.Exists("xSpatial_SAPOLYGON_Legend"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + soilSaFC, FGDBpath + os.sep + "legend", FGDBpath + os.sep + "xSpatial_SAPOLYGON_Legend", "SIMPLE", "> Legend Table", "< SAPOLYGON_Spatial", "NONE","ONE_TO_ONE", "NONE","LKEY","lkey", "","")
            #AddMsgAndPrint(" \t" + soilSaFC + formatTabLength1 + "legend" + "             --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_SAPOLYGON_Legend", 0)

            # Relationship between MULINE --> Mapunit Table
            if not arcpy.Exists("xSpatial_MULINE_Mapunit"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + muLineFC, FGDBpath + os.sep + "mapunit", FGDBpath + os.sep + "xSpatial_MULINE_Mapunit", "SIMPLE", "> Mapunit Table", "< MULINE_Spatial", "NONE","ONE_TO_ONE", "NONE","MUKEY","mukey", "","")
            #AddMsgAndPrint(" \t" + muLineFC + "         --> mapunit" + "            --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_MULINE_Mapunit", 0)

            # Relationship between MUPOINT --> Mapunit Table
            if not arcpy.Exists("xSpatial_MUPOINT_Mapunit"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + muPointFC, FGDBpath + os.sep + "mapunit", FGDBpath + os.sep + "xSpatial_MUPOINT_Mapunit", "SIMPLE", "> Mapunit Table", "< MUPOINT_Spatial", "NONE","ONE_TO_ONE", "NONE","MUKEY","mukey", "","")
            #AddMsgAndPrint(" \t" + muPointFC + "        --> mapunit" + "            --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_MUPOINT_Mapunit", 0)

            # Relationship between FEATLINE --> Featdesc Table
            if not arcpy.Exists("xSpatial_FEATLINE_Featdesc"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + featLineFC, FGDBpath + os.sep + "featdesc", FGDBpath + os.sep + "xSpatial_FEATLINE_Featdesc", "SIMPLE", "> Featdesc Table", "< FEATLINE_Spatial", "NONE","ONE_TO_ONE", "NONE","FEATKEY","featkey", "","")
            #AddMsgAndPrint(" \t" + featLineFC + "       --> featdesc" + "           --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_FEATLINE_Featdesc", 0)

            # Relationship between FEATPOINT --> Featdesc Table
            if not arcpy.Exists("xSpatial_FEATPOINT_Featdesc"):
                arcpy.CreateRelationshipClass_management(FGDBpath + os.sep + featPointFC, FGDBpath + os.sep + "featdesc", FGDBpath + os.sep + "xSpatial_FEATPOINT_Featdesc", "SIMPLE", "> Featdesc Table", "< FEATPOINT_Spatial", "NONE","ONE_TO_ONE", "NONE","FEATKEY","featkey", "","")
            #AddMsgAndPrint(" \t" + featPointFC + formatTabLength1 + "featdesc" + "           --> " + "ONE_TO_ONE" + "  --> " + "xSpatial_FEATPOINT_Featdesc", 0)

            del formatTab1, formatTabLength1

            #AddMsgAndPrint(" \n\tSuccessfully Created Table Relationships", 1)
            return True

        except arcpy.ExecuteError:
            AddMsgAndPrint(arcpy.GetMessages(2),2)
            return False

        except:
            print_exception()
            return False

    else:
        AddMsgAndPrint("\tMissing at least one of the relationship metadata tables", 2)

        return False

## ===============================================================================================================
def updateAliasNames(mlraName,fgdbPath):
# Update the alias name of every feature class in the RTSD including the project record.
# i.e. alias name for MUPOLYGON = Region 10 - Mapunit Polygon

    try:
        aliasUpdate = 0

        if arcpy.Exists(os.path.join(fgdbPath,'FEATLINE')):
            arcpy.AlterAliasName(os.path.join(fgdbPath,'FEATLINE'), mlraName + " - Special Feature Lines")  #FEATLINE
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fgdbPath,'FEATPOINT')):
            arcpy.AlterAliasName(os.path.join(fgdbPath,'FEATPOINT'), mlraName + " - Special Feature Points")  #FEATPOINT
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fgdbPath,'MUPOLYGON')):
            arcpy.AlterAliasName(os.path.join(fgdbPath,'MUPOLYGON'), mlraName + " - Mapunit Polygon")  #MUPOLYGON
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fgdbPath,'SAPOLYGON')):
            arcpy.AlterAliasName(os.path.join(fgdbPath,'SAPOLYGON'), mlraName + " - Survey Area Polygon")  #SAPOLYGON
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fgdbPath,'MULINE')):
            arcpy.AlterAliasName(os.path.join(fgdbPath,'MULINE'), mlraName + " - Mapunit Line")  #MULINE
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fgdbPath,'MUPOINT')):
            arcpy.AlterAliasName(os.path.join(fgdbPath,'MUPOINT'), mlraName + " - Mapunit Point")  #MUPOINT
            aliasUpdate += 1

        if aliasUpdate == 6:
            return True
        else:
            return False

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        print_exception()
        return False

## ====================================== Main Body ===========================================================
# Import modules
import arcpy, sys, string, os, time, datetime, re, csv, traceback, shutil
from arcpy import env
# ---------------------------------------------------------------------------------------Input Arguments
#
# Parameter # 1: (Required) Input Directory where the new FGDB will be created.
#outputFolder = r'C:\Temp\export'
outputFolder = arcpy.GetParameterAsText(0)

# Parameter # 2: (Required) Input Directory where the original SDM spatial and tabular data exist.
#sdmLibrary = r'G:\2014_SSURGO_Region10'
sdmLibrary = arcpy.GetParameterAsText(1)

# Parameter # 3: list of SSA datasets to be proccessed
#mlraList = 1-OLY;1-ONT;1-PAL
mlraList = arcpy.GetParameter(2)

# SSURGO FGDB template that contains empty SSURGO Tables and relationships
# and will be copied over to the output location
ssurgoTemplate = os.path.dirname(sys.argv[0]) + os.sep + "SSURGO_Table_Template.gdb"

# Path to the Master Regional table that contains SSAs by region with extra extent
mlraBufferTable = os.path.join(os.path.join(os.path.dirname(sys.argv[0]),"SSURGO_Soil_Survey_Area.gdb"),"SSA_by_MLRA_buffer")

if not os.path.exists(ssurgoTemplate):
    raise MyError, "\nSSURGO_Table_Template.gdb does not exist in " + os.path.dirname(sys.argv[0])

# Bail if reginal master table is not found
if not arcpy.Exists(mlraBufferTable):
    raise MyError, "\nMLRA Buffer Table is missing from " + os.path.dirname(sys.argv[0])

env.overwriteOutput = True

try:
    # SSURGO layer Name
    soilFC = "MUPOLYGON"
    muLineFC = "MULINE"
    muPointFC = "MUPOINT"
    soilSaFC = "SAPOLYGON"
    featPointFC = "FEATPOINT"
    featLineFC = "FEATLINE"

    tblAliases = dict()
    tblAliases = GetTableAliases(ssurgoTemplate, tblAliases)

    # Create a new MLRA GDB for every MLRA in the list
    for mlra in mlraList:

        AddMsgAndPrint("\n------------------------------------------------------------------------",1)
        AddMsgAndPrint("Creating SSURGO dataset for Soil Survey Office: " + mlra,0)

        # get a list of SSAs that make up this SSA office, inlcuding a wider footprint
        mlraAS = getMLRAareaSymbolList(mlraBufferTable,mlra)
        mlraDatasetDict = validateSSAs(mlraAS,sdmLibrary)

        # if all SSAs are locally missing skip this MLRA
        if len(mlraDatasetDict) == 0:
            AddMsgAndPrint("\n\tAll SSURGO datasets needed for this SSA are missing from your local library. SKIPPING\n")
            continue

        # There are some SSAs missing from local library
        if len(mlraAS) != len(mlraDatasetDict):
            AddMsgAndPrint("\n\t" + str(len(mlraDatasetDict)) + " out of " + str(len(mlraAS)) + " surveys will be imported to create the " + mlra + " SSA SSURGO Dataset",1)
        else:
            AddMsgAndPrint("\n\t" + str(len(mlraDatasetDict)) + " surveys will be imported to create the " + mlra + " SSA SSURGO Dataset", 0)

        # Create Empty FGDB for SSA office
        mlraGDB = createFGDB(mlra, outputFolder)

        if mlraGDB == "":
            AddMsgAndPrint("\nFailed to Initiate MLRA FGDB....skipping this MLRA\n",2)
            continue

        # Path to MLRA FGDB; set as workspace
        FGDBpath = mlraGDB
        env.workspace = FGDBpath

        # Parse Datum from MUPOLYGON; can only get datum from a GCS not a projected CS
        spatialRef = str(arcpy.CreateSpatialReference_management("#",soilFC,"#","#","#","#"))

        userDatum_Start = spatialRef.find("DATUM") + 7
        userDatum_Stop = spatialRef.find(",", userDatum_Start) - 1
        userDatum = spatialRef[userDatum_Start:userDatum_Stop]

        AddMsgAndPrint("\n\tOutput Coordinate System: " + arcpy.Describe(soilFC).spatialReference.name,0)
        AddMsgAndPrint("\tOutput Datum: " + userDatum,0)

        if userDatum == "D_North_American_1983":
            AddMsgAndPrint("\tGeographic Transformation: WGS_1984_(ITRF00)_To_NAD_1983",0 )

        env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"  # WKID 108190
        env.outputCoordinateSystem = spatialRef

        # -------------------------------------------------------------------------------- Establish Dictionaries, lists and Fieldmappings
        # Dictionary containing approx center of SSA (key) and the SSURGO layer path (value)
        soilShpDict = dict()  # {-4002.988250799742: 'K:\\FY2014_SSURGO_R10_download\\soils_wi063\\spatial\\soilmu_a_wi063.shp'}
        muLineShpDict = dict()
        muPointShpDict = dict()
        soilSaShpDict = dict()
        featPointShpDict = dict()
        featLineShpDict = dict()

        # lists containing SSURGO layer paths sorted according to the survey center key
        # This list will be passed over to the Merge command
        soilShpList = list() #['G:\\2014_SSURGO_Region10\\soils_ia005\\spatial\\soilmu_a_ia005.shp']
        muLineShpList = list()
        muPointShpList = list()
        soilSaShpList = list()
        featPointShpList = list()
        featLineShpList = list()

        # list containing the (Xcenter * Ycenter) for every SSURGO soil layer
        extentList = list()

        # Calculate survey Centers, assign directory paths to SSURGO layers
        for SSA in mlraDatasetDict:

            # Paths to individual SSURGO layers
            soilShpPath = os.path.join(os.path.join(mlraDatasetDict[SSA],"spatial"),"soilmu_a_" + SSA.lower() + ".shp")
            muLineShpPath = os.path.join(os.path.join(mlraDatasetDict[SSA],"spatial"),"soilmu_l_" + SSA.lower() + ".shp")
            muPointShpPath = os.path.join(os.path.join(mlraDatasetDict[SSA],"spatial"),"soilmu_p_" + SSA.lower() + ".shp")
            soilSaShpPath = os.path.join(os.path.join(mlraDatasetDict[SSA],"spatial"),"soilsa_a_" + SSA.lower() + ".shp")
            featPointShpPath = os.path.join(os.path.join(mlraDatasetDict[SSA],"spatial"),"soilsf_p_" + SSA.lower() + ".shp")
            featLineShpPath = os.path.join(os.path.join(mlraDatasetDict[SSA],"spatial"),"soilsf_l_" + SSA.lower() + ".shp")

            # Calculate the approximate center of a given survey
            desc = arcpy.Describe(soilShpPath)
            shpExtent = desc.extent
            XCntr = (shpExtent.XMin + shpExtent.XMax) / 2.0
            YCntr = (shpExtent.YMin + shpExtent.YMax) / 2.0
            surveyCenter = XCntr * YCntr

            # Assign {-4002.988250799742: 'K:\\FY2014_SSURGO_R10_download\\soils_wi063\\spatial\\soilmu_a_wi063.shp'}
            soilShpDict[surveyCenter] = soilShpPath
            muLineShpDict[surveyCenter] = muLineShpPath
            muPointShpDict[surveyCenter] = muPointShpPath
            soilSaShpDict[surveyCenter] = soilSaShpPath
            featPointShpDict[surveyCenter] = featPointShpPath
            featLineShpDict[surveyCenter] = featLineShpPath

            extentList.append(surveyCenter)
            del soilShpPath, muLineShpPath, muPointShpPath, soilSaShpPath, featPointShpPath, featLineShpPath, desc, shpExtent, XCntr, YCntr, surveyCenter

        # ----------------------------------------------------------------------------------------------------------------------------- Begin the Merging Process
        # Sort shapefiles by extent so that the drawing order is a little more effecient
        extentList.sort()

        # There should be at least 1 survey to merge into the MUPOLYGON
        if len(soilShpDict) > 0:

            # Add SSURGO paths to their designated lists according to the sortedKey
            for surveyCenter in extentList:

                soilShpList.append(soilShpDict[surveyCenter])
                soilSaShpList.append(soilSaShpDict[surveyCenter])

                if int(arcpy.GetCount_management(muLineShpDict[surveyCenter]).getOutput(0)) > 0:
                    muLineShpList.append(muLineShpDict[surveyCenter])

                if int(arcpy.GetCount_management(muPointShpDict[surveyCenter]).getOutput(0)) > 0:
                    muPointShpList.append(muPointShpDict[surveyCenter])

                if int(arcpy.GetCount_management(featPointShpDict[surveyCenter]).getOutput(0)) > 0:
                    featPointShpList.append(featPointShpDict[surveyCenter])

                if int(arcpy.GetCount_management(featLineShpDict[surveyCenter]).getOutput(0)) > 0:
                    featLineShpList.append(featLineShpDict[surveyCenter])

        # No surveys to merge
        else:
            if arcpy.Exists(FGDBpath):
                arcpy.Delete_management(FGDBpath)

            AddMsgAndPrint("No Shapefiles to append. Skipping " + mlra,2)
            continue

        # set progressor object which allows progress information to be passed for every merge complete
        arcpy.SetProgressor("step", "Beginning the merge process...", 0, 6, 1)
        AddMsgAndPrint("\n\tBeginning the merge process",0)

        # --------------------------------------------------------------------------Merge Soil Mapunit Polygons
        arcpy.SetProgressorLabel("Merging " + str(len(soilShpList)) + " SSURGO Soil Mapunit Polygon Layers")

        try:
            arcpy.Merge_management(soilShpList, os.path.join(FGDBpath, soilFC))
            #arcpy.Append_management(soilShpList, os.path.join(FGDBpath, soilFC), "NO_TEST")

            AddMsgAndPrint("\t\tSuccessfully merged SSURGO Soil Mapunit Polygons",0)
            arcpy.SetProgressorPosition()

        except:
            print_exception()

        # --------------------------------------------------------------------------Merge Soil Mapunit Line
        if len(muLineShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(muLineShpList)) + " SSURGO Soil Mapunit Line Layers")

            arcpy.Merge_management(muLineShpList, os.path.join(FGDBpath, muLineFC))
            #arcpy.Append_management(muLineShpList, os.path.join(FGDBpath, muLineFC), "NO_TEST")

            AddMsgAndPrint("\t\tSuccessfully merged SSURGO Soil Mapunit Lines",0)

        else:
            AddMsgAndPrint("\t\tNo SSURGO Soil Mapunit Lines to merge",0)

        arcpy.SetProgressorPosition()

        # --------------------------------------------------------------------------Merge Soil Mapunit Points
        if len(muPointShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(muPointShpList)) + " SSURGO Soil Mapunit Point Layers")

            arcpy.Merge_management(muPointShpList, os.path.join(FGDBpath, muPointFC))
            #arcpy.Append_management(muPointShpList, os.path.join(FGDBpath, muPointFC), "NO_TEST", muPointFM)

            AddMsgAndPrint("\t\tSuccessfully merged SSURGO Soil Mapunit Points",0)

        else:
            AddMsgAndPrint("\t\tNo SSURGO Soil Mapunit Points to merge",0)

        arcpy.SetProgressorPosition()

        # --------------------------------------------------------------------------Merge Soil Survey Area
        arcpy.SetProgressorLabel("Merging " + str(len(soilSaShpList)) + " SSURGO Soil Survey Area Layers")

        arcpy.Merge_management(soilSaShpList, os.path.join(FGDBpath, soilSaFC))
        #arcpy.Append_management(soilSaShpList, os.path.join(FGDBpath, soilSaFC), "NO_TEST")

        AddMsgAndPrint("\t\tSuccessfully merged SSURGO Soil Survey Area Polygons",0)
        arcpy.SetProgressorPosition()

        # --------------------------------------------------------------------------Merge Special Point Features
        if len(featPointShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(featPointShpList)) + " SSURGO Special Point Feature Layers")

            arcpy.Merge_management(featPointShpList, os.path.join(FGDBpath, featPointFC))
            #arcpy.Append_management(featPointShpList, os.path.join(FGDBpath, featPointFC), "NO_TEST")

            AddMsgAndPrint("\t\tSuccessfully merged SSURGO Special Point Features",0)

        else:
            AddMsgAndPrint("\t\tNo SSURGO Soil Special Point Features to merge",0)

        arcpy.SetProgressorPosition()

        # --------------------------------------------------------------------------Merge Special Line Features
        if len(featLineShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(featLineShpList)) + " SSURGO Special Line Feature Layers")

            arcpy.Merge_management(featLineShpList, os.path.join(FGDBpath, featLineFC))
            #arcpy.Append_management(featLineShpList, os.path.join(FGDBpath, featLineFC), "NO_TEST")

            AddMsgAndPrint("\t\tSuccessfully merged SSURGO Special Line Features \n",0)

        else:
            AddMsgAndPrint("\t\tNo SSURGO Special Line Features to merge \n",0)

        arcpy.SetProgressorPosition()

        # Resets the progressor back to is initial state
        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel(" ")

        # -----------------------------------------------------------------------------------------------------------------Importing Tabular Data
        i = 0
        AddMsgAndPrint("\tImporting Tabular Data for " + str(len(mlraDatasetDict)) + " surveys",0)
        for SSA in mlraDatasetDict:

            tabularFolder = os.path.join(mlraDatasetDict[SSA],"tabular")
            spatialFolder = os.path.join(mlraDatasetDict[SSA],"spatial")

            if os.path.exists(tabularFolder):

                arcpy.SetProgressorLabel("Importing Tabular Data for: " + SSA)

                # Make a temp copy of the special feature description in the spatial folder and put it in the
                # tabular folder so that it can be imported.  It will be named "featdesc"
                specFeatDescFile = spatialFolder + os.sep + "soilsf_t_" + SSA.lower() + ".txt"

                # change copy to shutil
                if os.path.exists(specFeatDescFile):
                    #os.system("copy %s %s" % (specFeatDescFile, tabularFolder + os.sep + "featdesc.txt"))
                    shutil.copy2(specFeatDescFile, tabularFolder + os.sep + "featdesc.txt")

                importFailed = 0

                # Import the text files into the FGDB tables
                if not importTabularData(tabularFolder,tblAliases):
                    AddMsgAndPrint("\n\t\tFailed to import tabular data for: " + SSA,2)
                    os.remove(tabularFolder + os.sep + "featdesc.txt")
                    continue
                    importFailed += 1

                # remove the featdesc file from the tabular folder regardless of import success or not
                try:
                    os.remove(tabularFolder + os.sep + "featdesc.txt")
                except:
                    AddMsgAndPrint("\n\t\t Could not remove feature file from tabular folder for: " + SSA,2)
                    pass

                del SSA, specFeatDescFile

            # Tabular folder not present for this SSA
            else:
                AddMsgAndPrint("\t\tTabular Folder is missing for: " + SSA,2)
                continue

            del tabularFolder, spatialFolder

            i += 1

        del i

        # establish relationships if mapunit Table is not empty
        if arcpy.GetCount_management(FGDBpath + os.sep + "mapunit").getOutput(0) > 0:

            # establish Relationships
            if not CreateTableRelationships(tblAliases):
                AddMsgAndPrint("\n\tCreateTableRelationships failed", 2)

        if updateAliasNames(mlra, FGDBpath):
            AddMsgAndPrint("\tSuccessfully Updated Alias Names for Feature Classes within " + os.path.basename(FGDBpath))
        else:
            AddMsgAndPrint("\tUnable to Update Alias Names for Feature Classes within " + os.path.basename(FGDBpath),2)

        # -----------------------------------------------------------------------------------------
        AddMsgAndPrint("\n\tTotal # of SSURGO Datasets Appended: " + str(splitThousands(len(soilShpList))),0)
        AddMsgAndPrint("\t\tTotal # of Mapunit Polygons: " + str(splitThousands(arcpy.GetCount_management(FGDBpath + os.sep + soilFC).getOutput(0))),0)
        AddMsgAndPrint("\t\tTotal # of Mapunit Lines: " + str(splitThousands(arcpy.GetCount_management(FGDBpath + os.sep + muLineFC).getOutput(0))),0)
        AddMsgAndPrint("\t\tTotal # of Mapunit Points: " + str(splitThousands(arcpy.GetCount_management(FGDBpath + os.sep + muPointFC).getOutput(0))),0)
        AddMsgAndPrint("\t\tTotal # of Special Feature Points: " + str(splitThousands(arcpy.GetCount_management(FGDBpath + os.sep + featPointFC).getOutput(0))),0)
        AddMsgAndPrint("\t\tTotal # of Special Feature Lines: " + str(splitThousands(arcpy.GetCount_management(FGDBpath + os.sep + featLineFC).getOutput(0))),0)
        AddMsgAndPrint("\n",0)

        del mlraAS, mlraDatasetDict, mlraGDB, FGDBpath, spatialRef, userDatum_Start, userDatum_Stop, userDatum
        del soilShpDict, muLineShpDict, muPointShpDict, soilSaShpDict, featPointShpDict, featLineShpDict
        del soilShpList, muLineShpList, muPointShpList, soilSaShpList, featPointShpList, featLineShpList, extentList

        arcpy.RefreshCatalog(outputFolder)

    del outputFolder
    del sdmLibrary
    del mlraList
    del ssurgoTemplate
    del mlraBufferTable
    del soilFC
    del muLineFC
    del muPointFC
    del soilSaFC
    del featPointFC
    del featLineFC
    del tblAliases

# This is where the fun ends!
except arcpy.ExecuteError:
    AddMsgAndPrint(arcpy.GetMessages(2),2)

except:
    print_exception()
