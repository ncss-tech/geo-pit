# Create_Regional_Transactional_FGDB
#
# 1/16/2014
#
# Adolfo Diaz, Region 10 GIS Specialist
# USDA - Natural Resources Conservation Service
# Madison, WI 53719
# adolfo.diaz@wi.usda.gov
# 608.662.4422 ext. 216
#
#
# Last Modified:  10/24/2017
# Region 11 Modified 20181002 update & add MUKEY, modify for MLRA databases

## ===================================================================================
def print_exception():

    tb = sys.exc_info()[2]
    l = traceback.format_tb(tb)
    l.reverse()
    tbinfo = "".join(l)
    AddMsgAndPrint("\n\n----------ERROR Start-------------------",2)
    AddMsgAndPrint("Traceback Info: \n" + tbinfo + "Error Info: \n    " +  str(sys.exc_type)+ ": " + str(sys.exc_value) + "",2)
    AddMsgAndPrint("----------ERROR End-------------------- \n\n",2)

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
def getRegionalAreaSymbolList(ssurgoSSApath, userRegionChoice):
# Returns the actual region number from the first parameter.
# If the value has 1 integer than it should total 8 characters,
# last character will be returned.  Otherwise, value has 2 integers
# and last 2 will be returned.
# [u'WI001, u'WI003']

    try:
        areaSymbolList = []

        whereClause = "\"MLRA_CODE\" = '" + userRegionChoice + "'"
        fields = ('AREASYMBOL')

        with arcpy.da.SearchCursor(ssurgoSSApath, fields, whereClause) as cursor:
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
# missing return "".  All ssurgo datasets must be present in order to (re)construct the
# regional Transactional database.  Also checks for duplicate ssurgo datasets in the
# wssLibrary.  Return "" if duplicates are found.  Cannot have duplicates b/c this will
# cause topology overlap and the duplicate datasets may be of different versions.
# Returns a dictionary containing areasymbol & ssurgo dataset path
#
# {'ID001': 'C:\\Temp\\junk\\soils_id001', 'ID002': 'C:\\Temp\\junk\\wss_SSA_ID002_soildb_ID_2003_[2012-08-13]'

    try:
        import collections

        ssurgoDatasetDict = dict()  # [AreaSymbol] = C:\Temp\junk\soil_ca688
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
                        ssurgoDatasetDict[SSA] = filePath
                    del SSA

                # folder is named according to traditional SDM format i.e. 'soil_wa001'
                elif file.find("soil_") > -1:
                    SSA = file[-5:].upper()
                    wssLibraryList.append(SSA)

                    if SSA in surveyList:
                        ssurgoDatasetDict[SSA] = filePath
                    del SSA

                # folder is name in plural format instead of singular.  Accident!!!
                elif file.find("soils_") > -1:
                    SSA = file[-5:].upper()
                    wssLibraryList.append(SSA)

                    if SSA in surveyList:
                        ssurgoDatasetDict[SSA] = filePath
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
            AddMsgAndPrint("\n" + "The following Regional SSURGO datasets are missing from your local datasets",2)
            for survey in missingSSAList:
                AddMsgAndPrint("\t" + survey,2)
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
                    AddMsgAndPrint("\t\t" + survey,2)
                    ssurgoDatasetDict.pop(survey, None)

        # -------------------------------------------------------------------- Make sure Datum is either NAD83 or WGS84 and soils layer is not missing
        wrongDatum = []
        missingSoilLayer = []

        for survey in ssurgoDatasetDict:
            soilShpPath = os.path.join(os.path.join(ssurgoDatasetDict[survey],"spatial"),"soilmu_a_" + survey.lower() + ".shp")

            if arcpy.Exists(soilShpPath):
                if not compareDatum(soilShpPath):
                    wrongDatum.append(survey)
            else:
                missingSoilLayer.append(survey)

        if len(wrongDatum) > 0:
            AddMsgAndPrint("\n\tThe following local SSURGO datasets have a Datum other than WGS84 or NAD83:",2)
            for survey in wrongDatum:
                AddMsgAndPrint("\t\t" + survey,2)
                ssurgoDatasetDict.pop(survey, None)

        if len(missingSoilLayer) > 0:
            AddMsgAndPrint("\n\tThe following local SSURGO datasets are missing their soils shapefile:",2)
            for survey in missingSoilLayer:
                AddMsgAndPrint("\t\t" + survey,2)
                ssurgoDatasetDict.pop(survey, None)

        # --------------------------------------------------------------------  At this point everything checks out; Return Dictionary!
        del wssLibraryList, missingSSAList, wrongDatum, missingSoilLayer
        return ssurgoDatasetDict

    except:
        AddMsgAndPrint("\nUnhandled exception (validateSSAs)", 2)
        print_exception()
        return ""

## ================================================================================================================
def createFGDB(regionChoice,outputFolder):
    # This function will Create the RTSD File Geodatabase by importing an XML workspace schema.
    # Depending on what region is being created is what .xml file will be used.
    # Schema includes 2 feature datasets: FD_RTSD & Project Record. 6 feature classes will be created
    # within FD_RTSD along with a topology.  1 feature class will be created within the ProjectRecord
    # FD.  Return new name of RTSD otherwise return empty string.

    try:
        targetGDB = os.path.join(outputFolder,"TempRTSD.gdb")

        if arcpy.Exists(targetGDB):
            arcpy.Delete_management(targetGDB)

        arcpy.CreateFileGDB_management(outputFolder,"TempRTSD")

        # New fiscal year if month October, November and December
        month = int(datetime.now().strftime("%m"))
        if month > 9 and month < 13:
            FY = "FY" + str(int(datetime.now().strftime("%y")) +1)
        else:
            FY = "FY" + str(datetime.now().strftime("%y"))

        # Alaska = Alaska Albers Equal Area Conic (NAD_1983_Alaska_Albers) wkid: 3338
        if regionChoice == "Region 1 - AK":
            xmlFile = os.path.dirname(sys.argv[0]) + os.sep + "RTSD_XMLWorkspace_Alaska.xml"
            newName = "RTSD_Region_1_Alaska_" + FY

        # Hawaii - Hawaii_Albers_Equal_Area_Conic WGS84
        elif regionChoice == "Region 2 - HI":
            xmlFile = os.path.dirname(sys.argv[0])+ os.sep + "RTSD_XMLWorkspace_Hawaii.xml"
            newName = "RTSD_Region_2_Hawaii_" + FY

        # PBSamoa - Hawaii_Albers_Equal_Area_Conic WGS84
        elif regionChoice == "Region 2 - PBSamoa":
            xmlFile = os.path.dirname(sys.argv[0]) + os.sep + "RTSD_XMLWorkspace_Hawaii.xml"
            newName = "RTSD_Region_2_PBSamoa_" + FY

        # Pacific Basin - Western Pacific Albers Equal Area Conic WGS84  Only PB630
        elif regionChoice == "Region 2 - PacBasin":
            xmlFile = os.path.dirname(sys.argv[0]) + os.sep + "RTSD_XMLWorkspace_PacBasin.xml"
            newName ="RTSD_Region_2_PacBasin_" + FY

        # Puerto Rico US Virgin Islands - USA Contiguous Albers Equal Area Conic USGS version NAD83
        elif regionChoice == "Region 3 - PRUSVI":
            xmlFile = os.path.dirname(sys.argv[0]) + os.sep + "RTSD_XMLWorkspace_CONUS.xml"
            newName ="RTSD_Region_3_PRUSVI_" + FY

        # CONUS - USA Contiguous Albers Equal Area Conic USGS version NAD83
        else:
            xmlFile = os.path.dirname(sys.argv[0]) + os.sep + "RTSD_XMLWorkspace_CONUS.xml"
            newName = "RTSD_Region_" + str(regionChoice[regionChoice.find(" ")+1:]) + "_" + FY

        # Return false if xml file is not found and delete targetGDB
        if not arcpy.Exists(xmlFile):
            AddMsgAndPrint(os.path.basename(xmlFile) + " was not found!",2)
            arcpy.Delete_management(targetGDB)
            return ""

        arcpy.ImportXMLWorkspaceDocument_management(targetGDB, xmlFile, "SCHEMA_ONLY", "DEFAULTS")

        # if Transactional Spatial Database exists delete it
        if arcpy.Exists(os.path.join(outputFolder,newName + ".gdb")):

            try:
                AddMsgAndPrint("\n" + newName + ".gdb already exists, deleting",1)
                arcpy.Delete_management(os.path.join(outputFolder,newName + ".gdb"))

            except:
                AddMsgAndPrint("\nFailed to Delte " + os.path.join(outputFolder,newName + ".gdb",2))
                return ""

        arcpy.Rename_management(targetGDB,newName)
        arcpy.RefreshCatalog(os.path.join(outputFolder,newName + '.gdb'))

        AddMsgAndPrint("\nSuccessfully Created RTSD File GDB: " + newName + ".gdb")

        del targetGDB,FY,xmlFile

        return newName + ".gdb"

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return ""

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
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

        del userDatum_Start, userDatum_Stop, userProjection_Start, userProjection_Stop

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
                    PrintMsg("\n\tWarning! No coordinate shift will being applied", 0)

                else:
                    AddMsgAndPrint("Invalid geographic region (" + AOI + ")",2)
                    exit()

                arcpy.env.outputCoordinateSystem = spatialReference
                arcpy.env.geographicTransformations = tm
                AddMsgAndPrint("\n\tUsing Datum Transformation Method '" + tm + "' for " + AOI, 1)

                return userDatum,userProjectionName

            # user datum was something other than NAD83 or WGS84
            else:
                AddMsgAndPrint("\n\tWarning! No Datum Transformation could be applied to " + userProjectionName + ".......EXITING!",2)
                return "",""

        # Could not parse CS name and datum
        else:
            AddMsgAndPrint("\n\tCould not extract Spatial Reference Properties........Halting import process",2)
            return "",""

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return "",""

    except:
        AddMsgAndPrint("\nUnhandled exception (parseDatumAndProjection)", 2)
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

        # Input datum is either WGS84 or NAD83; return true
        if fc_datum == WGS84_datum or fc_datum == NAD83_datum:
            del fcSpatialRef, FCdatum_start, FCdatum_stop,fc_datum,WGS84_sr,WGS84_datum,NAD83_datum
            return True

        # Input Datum is some other Datum; return false
        else:
            del fcSpatialRef, FCdatum_start, FCdatum_stop,fc_datum,WGS84_sr,WGS84_datum,NAD83_datum
            return False

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
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
def createTopology(RTSD_FD):

    try:

        #env.workspace = RTSD_FD
        AddMsgAndPrint("\nCreating Topology and Rules",0)
        arcpy.SetProgressor("step", "Creating Topology", 0, 3, 1)

        # Create New topology
        arcpy.SetProgressorLabel("Creating Topology")
        arcpy.CreateTopology_management(RTSD_FD, "FD_RTSD_Topology", 0.1)
        newTopology = os.path.join(RTSD_FD,"FD_RTSD_Topology")
        AddMsgAndPrint("\tCreated Topology: FD_RTSD_Topology at 0.1m cluster tolerance",0)
        arcpy.SetProgressorPosition()

        # Add feature classes to topology
        arcpy.SetProgressorLabel("Creating Topology: Adding Feature Classes to Topology")
        arcpy.AddFeatureClassToTopology_management(newTopology, os.path.join(RTSD_FD, "MUPOLYGON"), 1, 1)
        arcpy.AddFeatureClassToTopology_management(newTopology, os.path.join(RTSD_FD,"MUPOINT"), 1, 1)
        arcpy.AddFeatureClassToTopology_management(newTopology, os.path.join(RTSD_FD,"MULINE"), 1, 1)
        arcpy.AddFeatureClassToTopology_management(newTopology, os.path.join(RTSD_FD,"FEATPOINT"), 1, 1)
        arcpy.AddFeatureClassToTopology_management(newTopology, os.path.join(RTSD_FD,"FEATLINE"), 1, 1)
        AddMsgAndPrint("\tAdded 5 Feature Classes to participate in the Topology",0)
        arcpy.SetProgressorPosition()

        # Add Topology Rules
        arcpy.SetProgressorLabel("Creating Topology: Adding Rules to Topology")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Overlap (Area)", "MUPOLYGON")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Have Gaps (Area)", "MUPOLYGON")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Overlap (Line)", "FEATLINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Intersect (Line)", "FEATLINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Self-Overlap (Line)", "FEATLINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Have Pseudo-Nodes (Line)", "FEATLINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Self-Intersect (Line)", "FEATLINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Be Single Part (Line)", "FEATLINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Be Disjoint (Point)", "FEATPOINT")
        arcpy.AddRuleToTopology_management(newTopology, "Must Be Disjoint (Point)", "MUPOINT")
        arcpy.AddRuleToTopology_management(newTopology, "Must Be Properly Inside (Point-Area)","FEATPOINT","","MUPOLYGON","")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Overlap (Line)", "MULINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Intersect (Line)", "MULINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Self-Overlap (Line)", "MULINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Have Pseudo-Nodes (Line)", "MULINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Not Self-Intersect (Line)", "MULINE")
        arcpy.AddRuleToTopology_management(newTopology, "Must Be Single Part (Line)", "MULINE")

        AddMsgAndPrint("\tAdded 17 rules to the Topology",0)
        arcpy.SetProgressorPosition()
        arcpy.ResetProgressor()

        arcpy.RefreshCatalog(RTSD_FD)
        del newTopology
        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        print_exception()
        return False

## ===============================================================================================================
def ImportFeatureFiles(ssurgoDatasetDict):
# This function will import the feature files into the featdesc table within
# RTSD.  Spatial version and FEATKEY are not imported.  Warns user if feature
# file is empty.  Return True if all worked well.

    try:
        AddMsgAndPrint("\n" + "Importing Feature Files",0)
        arcpy.SetProgressor("step", "Importing Feature Files", 0, len(ssurgoDatasetDict), 1)

        featDescTable = os.path.join(FGDBpath,"featdesc")

        # Put all the field names in a list; used to initiate insertCursor object
        fieldList = arcpy.ListFields(featDescTable)
        nameOfFields = []

        for field in fieldList:

            if field.type != "OID":
                nameOfFields.append(field.name)

        # Initiate Cursor to add rows
        cursor = arcpy.da.InsertCursor(featDescTable, nameOfFields)

        missingFiles = []
        importError = []
        importedCorrectly = 0
        emptyFiles = 0

        for SSA in ssurgoDatasetDict:
            arcpy.SetProgressorLabel("Importing Feature File: " + SSA)

            # Paths to individual SSURGO layers
            specFeatDescFile = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilsf_t_" + SSA.lower() + ".txt")

            # check if feature file exists
            if os.path.exists(specFeatDescFile):

                # Continue if the feature file contains values. Not Empty file
                if os.path.getsize(specFeatDescFile) > 0:

                    # Number of records in the feature file
                    textFileRecords = sum(1 for row in csv.reader(open(specFeatDescFile, 'rb'), delimiter='|', quotechar='"'))
                    F = csv.reader(open(specFeatDescFile, 'rb'), delimiter='|', quotechar='"')

                    i = 0 # row counter
                    for rowInF in F:
                        try:
                            i+=1
                            newRow = rowInF[0],rowInF[2],rowInF[3],rowInF[4]
                            cursor.insertRow(newRow)
                            del newRow

                        except:
                            AddMsgAndPrint("\tFailed to import line #" + str(i) + " for " + SSA + " feature file",2)
                            continue

                    #AddMsgAndPrint("\tSuccessfully Imported: " + str(textFileRecords) + " records",0)

                    if i != textFileRecords:
                        AddMsgAndPrint("\tIncorrect # of records inserted for " + SSA,2)
                        AddMsgAndPrint( "\t\tFeature file records: " + str(textFileRecords),2)
                        AddMsgAndPrint( "\t\tRecords Inserted: " + str(i),2)
                        importError.append(SSA)

                    else:
                        importedCorrectly += 1

                    del textFileRecords,F,i

                # feature file is empty, print a warning
                else:
                    AddMsgAndPrint("\t" + SSA + " feature file is empty",1)
                    emptyFiles += 1

            else:
                AddMsgAndPrint("\t" + SSA + " feature file is missing",2)
                missingFiles.append(SSA)

            arcpy.SetProgressorPosition()
            del specFeatDescFile

        # Print any missing surveys
        if len(missingFiles) > 0:
            AddMsgAndPrint("\n\tThe following SSAs had missing feature files:",2)
            for ssa in missingFiles:
                AddMsgAndPrint( "\t\t" + ssa,2)

        # Print any SSAs that had errors importing
        if len(importError) > 0:
            AddMsgAndPrint("\n\tThe following SSAs had errors importing - Feature files should be looked at:",2)
            for ssa in importError:
                AddMsgAndPrint( "\t\t" + ssa,2)

        if (emptyFiles + importedCorrectly) == len(ssurgoDatasetDict):
            AddMsgAndPrint("\tAll " + str(len(ssurgoDatasetDict)) + " Feature Files Successfully Imported",0)
        else:
            AddMsgAndPrint("\tOnly " + str(importedCorrectly) + " Feature Files were successfully imported",2)

        del featDescTable, fieldList, field, nameOfFields, cursor, missingFiles, importError, importedCorrectly, emptyFiles
        arcpy.ResetProgressor()
        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        print_exception()
        return False

## ===============================================================================================================
def updateAliasNames(regionChoice,fdPath):
# Update the alias name of every feature class in the RTSD including the project record.
# i.e. alias name for MUPOLYGON = Region 11 - Mapunit Polygon

    try:

        aliasUpdate = 0
        regionNumber = str([int(s) for s in regionChoice.split() if s.isdigit()][0])

        if arcpy.Exists(os.path.join(fdPath,'FEATLINE')):
            arcpy.AlterAliasName(os.path.join(fdPath,'FEATLINE'), "RTSD MLRA" + regionNumber + " - Special Feature Lines")  #FEATLINE
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fdPath,'FEATPOINT')):
            arcpy.AlterAliasName(os.path.join(fdPath,'FEATPOINT'), "RTSD MLRA" + regionNumber + " - Special Feature Points")  #FEATPOINT
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fdPath,'MUPOLYGON')):
            arcpy.AlterAliasName(os.path.join(fdPath,'MUPOLYGON'), "RTSD MLRA" + regionNumber + " - Mapunit Polygon")  #MUPOLYGON
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fdPath,'SAPOLYGON')):
            arcpy.AlterAliasName(os.path.join(fdPath,'SAPOLYGON'), "RTSD MLRA" + regionNumber + " - Survey Area Polygon")  #SAPOLYGON
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fdPath,'MULINE')):
            arcpy.AlterAliasName(os.path.join(fdPath,'MULINE'), "RTSD MLRA" + regionNumber + " - Mapunit Line")  #MULINE
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(fdPath,'MUPOINT')):
            arcpy.AlterAliasName(os.path.join(fdPath,'MUPOINT'), "RTSD MLRA" + regionNumber + " - Mapunit Point")  #MUPOINT
            aliasUpdate += 1

        if arcpy.Exists(os.path.join(FGDBpath + os.sep + 'ProjectRecord' + os.sep + 'Project_Record')):
            arcpy.AlterAliasName(os.path.join(FGDBpath + os.sep + 'ProjectRecord' + os.sep + 'Project_Record'), "RTSD MLRA" + regionNumber + " - Project Record")  #Project_Record
            aliasUpdate += 1

        if aliasUpdate == 7:
            return True
        else:
            return False

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        print_exception()
        return False

## ===============================================================================================================
def addAttributeIndex(table,fieldList,verbose=True):
# Attribute indexes can speed up attribute queries on feature classes and tables.
# This function adds an attribute index(es) for the fields passed to the table that
# is passed in. This function takes in 2 parameters:
#   1) Table - full path to an existing table or feature class
#   2) List of fields that exist in table
# This function will make sure an existing index is not associated with that field.
# Does not return anything.

    try:
        # Make sure table exists. - Just in case
        if not arcpy.Exists(table):
            AddMsgAndPrint("Attribute index cannot be created for: " + os.path.basename(table) + " TABLE DOES NOT EXIST",2)
            return False

        else:
            if verbose: AddMsgAndPrint("Adding Indexes to Table: " + os.path.basename(table))

        # iterate through every field
        for fieldToIndex in fieldList:

            # Make sure field exists in table - Just in case
            if not len(arcpy.ListFields(table,"*" + fieldToIndex))>0:
                if verbose:
                    AddMsgAndPrint("\tAttribute index cannot be created for: " + fieldToIndex + ". FIELD DOES NOT EXIST",2)
                    continue

            # list of indexes (attribute and spatial) within the table that are
            # associated with the field or a field that has the field name in it.
            # Important to inspect all associated fields b/c they could be using
            # a differently named index
            existingIndexes = arcpy.ListIndexes(table,"*" + fieldToIndex)
            bFieldIndexExists = False

            # check existing indexes to see if fieldToIndex is already associated
            # with an index
            if existingIndexes > 0:

                # iterate through the existing indexes looking for a field match
                for index in existingIndexes:
                    associatedFlds = index.fields

                    # iterate through the fields associated with existing index.
                    # Should only be 1 field since multiple fields are not allowed
                    # in a single FGDB.
                    for fld in associatedFlds:

                        # Field is already part of an existing index - Notify User
                        if fld.name == fieldToIndex:
                            if verbose:
                                AddMsgAndPrint("\tAttribute Index for " + fieldToIndex + " field already exists",1)
                                bFieldIndexExists = True

                    # Field is already part of an existing index - Proceed to next field
                    if bFieldIndexExists:
                        break

            # Attribute field index does not exist.  Add one.
            if not bFieldIndexExists:
                newIndex = "IDX_" + fieldToIndex

                # UNIQUE setting is not used in FGDBs - comment out
                arcpy.AddIndex_management(table,fieldToIndex,newIndex,"#","ASCENDING")

                if verbose:
                    AddMsgAndPrint("\tSuccessfully added attribute index for " + fieldToIndex)

    except:
        print_exception()
        return False


## =========================================================== Main Body =========================================================================
# Import modules
import arcpy, sys, string, os, time, datetime, re, traceback, csv
from arcpy import env
from datetime import datetime

if __name__ == '__main__':

    # ---------------------------------------------------------------------------------------Input Arguments
    # Parameter # 1: (Required) Name of new file geodatabase to create
    regionChoice = arcpy.GetParameterAsText(0)  # User selects what region to create MRSD
    #regionChoice = "Region 13"

    # Parameter # 2: (Required) Input Directory where the new FGDB will be created.
    outputFolder = arcpy.GetParameterAsText(1)
    #outputFolder = r'C:\Temp\export'

    # Parameter # 2: (Required) Input Directory where the original SDM spatial and tabular data exist.
    wssLibrary = arcpy.GetParameterAsText(2)
    #wssLibrary = r'K:\FY2014_SSURGO_R11_download'

    # Path to the Master Regional table that contains SSAs by region with extra extent
    #regionalTable = os.path.dirname(sys.argv[0]) + os.sep + "SSURGO_Soil_Survey_Area.gdb\junkTable"
    regionalTable = os.path.join(os.path.join(os.path.dirname(sys.argv[0]),"SSURGO_Soil_Survey_Area.gdb"),"SSA_by_MLRA_buffer")

    # Bail if reginal master table is not found
    if not arcpy.Exists(regionalTable):
        AddMsgAndPrint("\nRegional Master Table is missing from " + os.path.dirname(sys.argv[0]),2)
        exit()

    startTime = datetime.now()
    env.overwriteOutput = True

    # The entire Main code in a try statement....Let the fun begin!
    try:

        # Get a list of Regional areasymbols to download from the Regional Master Table.  [u'WI001, u'WI003']
        regionalASlist = getRegionalAreaSymbolList(regionalTable,regionChoice)
        #regionalASlist = ['WI021','WI025','WI027','WI029']

        # Exit if list of regional areasymbol list is empty
        if not len(regionalASlist) > 0:
            AddMsgAndPrint("\n\nNo Areasymbols were selected from Regional SSA Ownership table. Possible problem with table.....EXITING",2)
            exit()

        # sort the regional list
        regionalASlist.sort()

        # check for missing Regional SSURGO Datasets or duplicates; Exit if any are found
        AddMsgAndPrint("\n" + "Validating local Regional SSURGO datasets.......",0)
        ssurgoDatasetDict = validateSSAs(regionalASlist,wssLibrary)

        if len(ssurgoDatasetDict) < 1:
            AddMsgAndPrint("\nAll " + regionChoice + " SSURGO datasets are missing from " + os.path.basename(wssLibrary) + " directory \n\tThere must also not be duplicate SSURGO datasets",2)
            exit()

        # There are some SSAs missing from local library
        elif len(regionalASlist) != len(ssurgoDatasetDict):
            AddMsgAndPrint("\n" + regionChoice + " is assigned " + str(len(regionalASlist)) + " SSAs --- Missing " + str(len(regionalASlist) - len(ssurgoDatasetDict)) + " SSAs" ,2)
            AddMsgAndPrint("\nALL SSURGO datasets assigned to " + regionChoice + " must be present to continue",2)
            AddMsgAndPrint("Download the missing SSURGO Datasets using the 'Download SSURGO by Region' tool",2)
            exit()

        else:
            AddMsgAndPrint("\n" + str(len(regionalASlist)) + " surveys will be merged to create the " + regionChoice + " Transactional Spatial Database", 0)

        # -------------------------------------------------------------------------------------- Create Empty Regional Transactional File Geodatabase
        RTSDname = createFGDB(regionChoice, outputFolder)

        if RTSDname == "":
            AddMsgAndPrint("\nFailed to Initiate Empty Regional Transactional Database.  Error in createFGDB() function. Exiting!",2)

        # Path to Regional FGDB
        FGDBpath = os.path.join(outputFolder,RTSDname)

        # Path to feature dataset that contains SSURGO feature classes
        FDpath = os.path.join(FGDBpath,"FD_RTSD")

        # SSURGO layer Name
        soilFC = "MUPOLYGON"
        muLineFC = "MULINE"
        muPointFC = "MUPOINT"
        soilSaFC = "SAPOLYGON"
        featPointFC = "FEATPOINT"
        featLineFC = "FEATLINE"

        # Set environment variables
        env.workspace = FDpath

        # Parse Datum from MUPOLYGON; can only get datum from a GCS not a projected CS
        spatialRef = str(arcpy.CreateSpatialReference_management("#",soilFC,"#","#","#","#"))

        userDatum_Start = spatialRef.find("DATUM") + 7
        userDatum_Stop = spatialRef.find(",", userDatum_Start) - 1
        userDatum = spatialRef[userDatum_Start:userDatum_Stop]

        AddMsgAndPrint("\tOutput Coordinate System: " + arcpy.Describe(soilFC).spatialReference.name,0)
        AddMsgAndPrint("\tOutput Datum: " + userDatum,0)

        if userDatum == "D_North_American_1983":
            AddMsgAndPrint("\tGeographic Transformation: WGS_1984_(ITRF00)_To_NAD_1983",0 )

        env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"  # WKID 108190
        env.outputCoordinateSystem = spatialRef

        arcpy.SetProgressorLabel("Gathering information about Soil Survey datasets...")

        # ------------------------------------------------------------------------------------- Establish Dictionaries, lists and Fieldmappings
        # Dictionary containing approx center of SSA (key) and the SSURGO layer path (value)
        soilShpDict = dict()   # {-4002.988250799742: 'K:\\FY2014_SSURGO_R10_download\\soil_wi063\\spatial\\soilmu_a_wi063.shp'}
        muLineShpDict = dict()
        muPointShpDict = dict()
        soilSaShpDict = dict()
        featPointShpDict = dict()
        featLineShpDict = dict()

        # lists containing SSURGO layer paths sorted according to the survey center key
        # This list will be passed over to the Merge command
        soilShpList = list()
        muLineShpList = list()
        muPointShpList = list()
        soilSaShpList = list()
        featPointShpList = list()
        featLineShpList = list()

        # Create FieldMappings objects that will contain all of the fields from each survey
        # (fieldmap).  FMs will be used to remove every field but AREASYMBOL, FEATSYM, MUSYM
        soilsFM = arcpy.FieldMappings()
        muLineFM = arcpy.FieldMappings()
        muPointFM = arcpy.FieldMappings()
        soilSaFM = arcpy.FieldMappings()
        featPointFM = arcpy.FieldMappings()
        featLineFM = arcpy.FieldMappings()

        # Field map object that will contain the original MUSYM; it will be calculated from musym field
        origMUSYMfm = arcpy.FieldMap()

        # list containing the (Xcenter * Ycenter) for every SSURGO soil layer
        extentList = list()

        # ------------------------------------------------------------------------------------- Populate Dictionaries, lists and Fieldmappings
        for SSA in ssurgoDatasetDict:

            # Paths to individual SSURGO layers
            soilShpPath = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilmu_a_" + SSA.lower() + ".shp")
            muLineShpPath = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilmu_l_" + SSA.lower() + ".shp")
            muPointShpPath = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilmu_p_" + SSA.lower() + ".shp")
            soilSaShpPath = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilsa_a_" + SSA.lower() + ".shp")
            featPointShpPath = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilsf_p_" + SSA.lower() + ".shp")
            featLineShpPath = os.path.join(os.path.join(ssurgoDatasetDict[SSA],"spatial"),"soilsf_l_" + SSA.lower() + ".shp")

            # Calculate the approximate center of a given survey
            desc = arcpy.Describe(soilShpPath)
            shpExtent = desc.extent
            XCntr = (shpExtent.XMin + shpExtent.XMax) / 2.0
            YCntr = (shpExtent.YMin + shpExtent.YMax) / 2.0
            surveyCenter = XCntr * YCntr  # approximate center of survey

            # Assign {-4002.988250799742: 'K:\\FY2014_SSURGO_R10_download\\soil_wi063\\spatial\\soilmu_a_wi063.shp'}
            soilShpDict[surveyCenter] = soilShpPath
            muLineShpDict[surveyCenter] = muLineShpPath
            muPointShpDict[surveyCenter] = muPointShpPath
            soilSaShpDict[surveyCenter] = soilSaShpPath
            featPointShpDict[surveyCenter] = featPointShpPath
            featLineShpDict[surveyCenter] = featLineShpPath

            extentList.append(surveyCenter)

            # Add all fields from all of the SSURGO layers into their respective fieldMappings
            soilsFM.addTable(soilShpPath)
            muLineFM.addTable(muLineShpPath)
            muPointFM.addTable(muPointShpPath)
            soilSaFM.addTable(soilSaShpPath)
            featPointFM.addTable(featPointShpPath)
            featLineFM.addTable(featLineShpPath)


            origMUSYMfm.addInputField(soilShpPath,"musym")
            del soilShpPath, muLineShpPath, muPointShpPath, soilSaShpPath, featPointShpPath, featLineShpPath, desc, shpExtent, XCntr, YCntr, surveyCenter

        # Add 'orig_musym' to field map
        origMusym = origMUSYMfm.outputField
        origMusym.name = 'orig_musym'
        origMusym.aliasName = 'Original_MUSYM'
        origMUSYMfm.outputField = origMusym

        origMUSYMfm.mergeRule = 'First'
        soilsFM.addFieldMap(origMUSYMfm)

        # ---------------------------------------------------------------------------------------------------------- Begin the Merge Process
        # Sort shapefiles by extent so that the drawing order is continous
        extentList.sort()

        # number of soil layers to merge should be equal to number of Regional SSAs
        #if len(soilShpDict) == len(regionalASlist):
        if len(soilShpDict) > 0:

            # Add SSURGO paths to their designated lists according to the survey's center so that they draw continously
            # If the layer has features then add it to the merge list otherwise skip it.  This was added b/c it turns
            # out that empty mapunit point .shp are in line geometry and not point geometry
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

        # Some reason some surveys are missing......Exit
        else:
            if arcpy.Exists(FGDBpath):
                arcpy.Delete_management(FGDBpath)

            AddMsgAndPrint("\n\nAll surveys had incompatible datums! Datum needs to be in NAD83 or WGS84.",2)
            exit()

        # set progressor object which allows progress information to be passed for every merge complete
        arcpy.SetProgressor("step", "Beginning the merge process...", 0, 6, 1)
        AddMsgAndPrint("\n" + "Beginning the merge process",0)

        # ------------------------------------------------------------------------------------------------ Merge Soil Mapunit Polygons
        arcpy.SetProgressorLabel("Merging " + str(len(soilShpList)) + " Soil Mapunit Layers")

        try:
            for field in soilsFM.fields:
                if field.name not in ['AREASYMBOL','MUSYM','MUKEY', 'MUNAME', 'orig_musym']:
                    soilsFM.removeFieldMap(soilsFM.findFieldMapIndex(field.name))

            soilFCpath = os.path.join(FDpath, soilFC)
            arcpy.Merge_management(soilShpList, soilFCpath, soilsFM)
            #arcpy.Append_management(soilShpList, os.path.join(FDpath, soilFC), "NO_TEST", soilsFM)

            AddMsgAndPrint("\tSuccessfully merged SSURGO Soil Mapunit Polygons",0)

            if not addAttributeIndex(soilFCpath,["AREASYMBOL","MUSYM"],False): pass

            arcpy.SetProgressorPosition()

        except:
            print_exception()

        # ---------------------------------------------------------------------------------------------- Merge Soil Mapunit Lines
        muLineFCpath = os.path.join(FDpath, muLineFC)
        if len(muLineShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(muLineShpList)) + " SSURGO Soil Mapunit Line Layers")

            # Transactional FGDB; remove any field other than AREASYMBOL and MUSYM
            for field in muLineFM.fields:
                if field.name not in ["AREASYMBOL","MUSYM"]:
                    muLineFM.removeFieldMap(muLineFM.findFieldMapIndex(field.name))

            arcpy.Merge_management(muLineShpList, muLineFCpath, muLineFM)
            #arcpy.Append_management(muLineShpList, os.path.join(FDpath, muLineFC), "NO_TEST", muLineFM)

            AddMsgAndPrint("\tSuccessfully merged SSURGO Soil Mapunit Lines",0)
            if not addAttributeIndex(muLineFCpath,["AREASYMBOL","MUSYM"],False): pass

        else:
            AddMsgAndPrint("\tNo SSURGO Soil Mapunit Lines to merge",0)

        arcpy.SetProgressorPosition()

        # ----------------------------------------------------------------------------------------------- Merge Soil Mapunit Points
        muPointFCpath = os.path.join(FDpath, muPointFC)
        if len(muPointShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(muPointShpList)) + "SSURGO Soil Mapunit Point Layers")

            # Transactional FGDB; remove any field other than AREASYMBOL and MUSYM
            for field in muPointFM.fields:
                if field.name not in ["AREASYMBOL","MUSYM"]:
                    muPointFM.removeFieldMap(muPointFM.findFieldMapIndex(field.name))

            arcpy.Merge_management(muPointShpList, muPointFCpath, muPointFM)
            #arcpy.Append_management(muPointShpList, os.path.join(FDpath, muPointFC), "NO_TEST", muPointFM)

            AddMsgAndPrint("\tSuccessfully merged SSURGO Soil Mapunit Points",0)
            if not addAttributeIndex(muPointFCpath,["AREASYMBOL","MUSYM"],False): pass

        else:
            AddMsgAndPrint("\tNo SSURGO Soil Mapunit Points to merge",0)

        arcpy.SetProgressorPosition()

        # ---------------------------------------------------------------------------------------------- Merge Soil Survey Area
        arcpy.SetProgressorLabel("Merging " + str(len(soilSaShpList)) + " SSURGO Soil Survey Area Layers")

        # Transactional FGDB; remove any field other than AREASYMBOL and MUSYM
        for field in soilSaFM.fields:
            if field.name not in ["AREASYMBOL"]:
                soilSaFM.removeFieldMap(soilSaFM.findFieldMapIndex(field.name))

        soilSaFCpath = os.path.join(FDpath, soilSaFC)
        arcpy.Merge_management(soilSaShpList, soilSaFCpath, soilSaFM)
        #arcpy.Append_management(soilSaShpList, os.path.join(FDpath, soilSaFC), "NO_TEST", soilSaFM)

        AddMsgAndPrint("\tSuccessfully merged SSURGO Soil Survey Area Polygons",0)
        if not addAttributeIndex(soilSaFCpath,["AREASYMBOL"],False): pass

        arcpy.SetProgressorPosition()

        # --------------------------------------------------------------------------------------------- Merge Special Point Features
        featPointFCpath = os.path.join(FDpath, featPointFC)
        if len(featPointShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(featPointShpList)) + " SSURGO Special Point Feature Layers")

            # Transactional FGDB; remove any field other than AREASYMBOL and FEATSYM
            for field in featPointFM.fields:
                if field.name not in ["AREASYMBOL", "FEATSYM", "FEATKEY"]:
                    featPointFM.removeFieldMap(featPointFM.findFieldMapIndex(field.name))

            arcpy.Merge_management(featPointShpList, featPointFCpath, featPointFM)
            #arcpy.Append_management(featPointShpList, os.path.join(FDpath, featPointFC), "NO_TEST", featPointFM)

            AddMsgAndPrint("\tSuccessfully merged SSURGO Special Point Features",0)
            if not addAttributeIndex(featPointFCpath,["AREASYMBOL", "FEATSYM"],False): pass

        else:
            AddMsgAndPrint("\tNo SSURGO Soil Special Point Features to merge",0)

        arcpy.SetProgressorPosition()

        # -------------------------------------------------------------------------------------------- Merge Special Line Features
        featLineFCpath = os.path.join(FDpath, featLineFC)
        if len(featLineShpList) > 0:

            arcpy.SetProgressorLabel("Merging " + str(len(featLineShpList)) + " SSURGO Special Line Feature Layers")

            # Transactional FGDB; remove any field other than AREASYMBOL and FEATSYM
            for field in featLineFM.fields:
                if field.name not in ["AREASYMBOL", "FEATSYM", "FEATKEY"]:
                    featLineFM.removeFieldMap(featLineFM.findFieldMapIndex(field.name))

            arcpy.Merge_management(featLineShpList, featLineFCpath, featLineFM)
            #arcpy.Append_management(featLineShpList, os.path.join(FDpath, featLineFC), "NO_TEST", featLineFM)

            AddMsgAndPrint("\tSuccessfully merged SSURGO Special Line Features",0)
            if not addAttributeIndex(featLineFCpath,["AREASYMBOL", "FEATSYM"],False): pass

        else:
            AddMsgAndPrint("\tNo SSURGO Special Line Features to merge",0)

        arcpy.SetProgressorPosition()
        arcpy.ResetProgressor()

        # ---------------------------------------------------------------------------------------------------------- Import Feature descriptions
        if not ImportFeatureFiles(ssurgoDatasetDict):
            AddMsgAndPrint("\nError importing feature files into the featdesc table",2)

        # ---------------------------------------------------------------------------------------------------------- Setup Topology
        # Validate Topology with a cluster of 0.1 meters
        if createTopology(FDpath):
            arcpy.SetProgressorLabel("Validating Topology at 0.1 meters")
            arcpy.ValidateTopology_management(os.path.join(FDpath,"FD_RTSD_Topology"))
            AddMsgAndPrint("\tValidated Topology at 0.1 meters",0)

        else:
            AddMsgAndPrint("\n\tFailed to Create Topology. Create Topology Manually",2)

        # ---------------------------------------------------------------- Create Relationship class between project_record and SAPOLYGON feature class
        arcpy.SetProgressorLabel("Creating Relationship Class between Project_Record & SAPOLYGON")
        prjRecTable = os.path.join(FGDBpath,'ProjectRecord' + os.sep + 'Project_Record')
        saPolyPath = os.path.join(FDpath,soilSaFC)
        relName = "x" + os.path.basename(prjRecTable).replace("_","") + "_" + soilSaFC
        arcpy.CreateRelationshipClass_management(prjRecTable, saPolyPath, relName, "SIMPLE", "> SAPOLYGON", "< Project_Record", "NONE", "ONE_TO_ONE", "NONE", "AREASYMBOL", "AREASYMBOL", "", "")
        AddMsgAndPrint("\nSuccessfully Created Relationship Class")

        arcpy.SetProgressorLabel("Compacting " + os.path.basename(FGDBpath))
        arcpy.Compact_management(FGDBpath)
        AddMsgAndPrint("\nSuccessfully Compacted " + os.path.basename(FGDBpath))

        # --------------------------------------------------------------------------------------------------------  Add Field Aliases to Spatial Layers -tabular already has aliases embedded.
        if updateAliasNames(regionChoice, FDpath):
            AddMsgAndPrint("\nSuccessfully Updated Alias Names for Feature Classes within " + os.path.basename(FGDBpath))
        else:
            AddMsgAndPrint("\nUnable to Update Alias Names for Feature Classes within " + os.path.basename(FGDBpath),2)

        # -------------------------------------------------------------------------------------------------------- Enable Tracking
        for fc in [soilFCpath,muLineFCpath,muPointFCpath,featPointFCpath,featPointFCpath]:
            arcpy.EnableEditorTracking_management(fc,'Creator','Creation_Date','Editor','Last_Edit_Date','ADD_FIELDS')

        # -----------------------------------------------------------------------------------------
        AddMsgAndPrint("\n*****************************************************************************************",1)
        AddMsgAndPrint("Total # of SSURGO Datasets Appended: " + str(splitThousands(len(soilShpList))),1)
        AddMsgAndPrint("\tTotal # of Mapunit Polygons: " + str(splitThousands(arcpy.GetCount_management(FDpath + os.sep + soilFC).getOutput(0))),1)
        AddMsgAndPrint("\tTotal # of Mapunit Lines: " + str(splitThousands(arcpy.GetCount_management(FDpath + os.sep + muLineFC).getOutput(0))),1)
        AddMsgAndPrint("\tTotal # of Mapunit Points: " + str(splitThousands(arcpy.GetCount_management(FDpath + os.sep + muPointFC).getOutput(0))),1)
        AddMsgAndPrint("\tTotal # of Special Feature Points: " + str(splitThousands(arcpy.GetCount_management(FDpath + os.sep + featPointFC).getOutput(0))),1)
        AddMsgAndPrint("\tTotal # of Special Feature Lines: " + str(splitThousands(arcpy.GetCount_management(FDpath + os.sep + featLineFC).getOutput(0))),1)

        arcpy.RefreshCatalog(outputFolder)

        endTime = datetime.now()
        AddMsgAndPrint("\nTotal Time: " + str(endTime - startTime),0)

    # This is where the fun ends!
    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)

    except:
        print_exception()
