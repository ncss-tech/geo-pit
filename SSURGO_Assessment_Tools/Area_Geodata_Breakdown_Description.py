#-------------------------------------------------------------------------------
# Name:        Generate Mapunit Geodata Report
# Purpose:     This tool serves as an exploratary tool that mines Region 10's MLRA Geodata
#
# Author:      Adolfo.Diaz
#              Region 10 GIS Specialist
#              608.662.4422 ext. 216
#              adolfo.diaz@wi.usda.gov
#
# Created:     8.28.2014
# Copyright:   (c) Adolfo.Diaz 2014
#
#
# Should I add an "Other" line to the processHydro field when percentages don't exceed 0%.  Some results may all be 0%.
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

        f = open(textFilePath,'a+')
        f.write(msg + " \n")
        f.close

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
        AddMsgAndPrint("\nDeterming overlap between input polygon and your Geodata extent",0)
        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\"soils\" folder was not found in your MLRAGeodata Folder -- Cannot determine Overlap\n",2)
            return 0
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
            return True

        # some features are outside the geodata extent.  Warn the user
        elif totalIntAcres < totalMUacres and totalIntAcres > 1:
            prctOfCoverage = round((totalIntAcres / totalMUacres) * 100,1)

            if prctOfCoverage > 50:
                AddMsgAndPrint("\tWARNING: There is only " + str(prctOfCoverage) + " % coverage between your area of interest and MUPOLYGON Layer",1)
                AddMsgAndPrint("\tWARNING: " + splitThousands(round((totalMUacres-totalIntAcres),1)) + " .ac will not be accounted for",1)
                return True
            elif prctOfCoverage < 1:
                AddMsgAndPrint("\tArea of interest is outside of your Geodata Extent.  Cannot proceed with analysis",2)
                return False
            else:
                AddMsgAndPrint("\tThere is only " + str(prctOfCoverage) + " % coverage between your area of interest and Geodata Extent",2)
                return False

        # There is no overlap
        else:
            AddMsgAndPrint("\tALL polygons are ouside of your Geodata Extent.  Cannot proceed with analysis",2)
            return False

        if arcpy.Exists(outIntersect):
            arcpy.Delete_management(outIntersect)

        del soilsFolder, workspaces,saPolygonPath,outIntersect,totalMUacres,totalIntAcres

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

# ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

# ===============================================================================================================
def getMUKEYandCompInfoTable():

    try:
        AddMsgAndPrint("\nAcquiring Mapunit and Component Information for Soils Reports:",0)

        soilsFolder = geoFolder + os.sep + "soils"

        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\t\t\"soils\" folder was not found in your MLRAGeodata Folder -- Cannot get Component Information\n",2)
            return False
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\t\t\"SSURGO.gdb\" was not found in the soils folder -- Cannot get Component Information\n",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\t\t There are muliple \"SSURGO_*.gdb\" in the soils folder -- Cannot get Component Information\n",2)
            return False

        arcpy.env.workspace = workspaces[0]

        """ -------------------------------------- Setup MUPOLYGON or MuRASTER ---------------------------------------- """
        bRaster = False
        rasterList = arcpy.ListRasters("*MuRaster_10m")

        if len(rasterList) == 1:
            muRasterPath = arcpy.env.workspace + os.sep + rasterList[0]
            mukeyField = FindField(rasterList[0],"mukey")

            if mukeyField:
                cellSize = arcpy.Describe(muRasterPath).MeanCellWidth
                arcpy.env.extent = muLayerPath
                arcpy.env.mask = muLayerPath
                bRaster = True

        if not bRaster:
            fcList = arcpy.ListFeatureClasses("MUPOLYGON","Polygon")

            if not len(fcList):
                AddMsgAndPrint("\n\tMUPOLYGON feature class was not found in the SSURGO.gdb File Geodatabase",2)
                return False

            muPolygonPath = arcpy.env.workspace + os.sep + fcList[0]
            mukeyField = FindField(fcList[0],"mukey")

            if not mukeyField:
                AddMsgAndPrint("\n\tMUPOLYGON feature class is missing necessary fields",2)
                return False

        """ --------------------------- Run Tabulate areas between the input layer and the SSURGO polygons or SSURGO Raster --------------------
                                        This is much faster than doing an intersect or doing an mask extraction.  The fields
                                        from the output Tabulate areas tool will have to be transposed"""
        outTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)

        # Get the Object ID from the muLayer; need it for tabulating polygons
        oidField = ""
        fieldList = arcpy.Describe(muLayer).fields
        for field in fieldList:
            if field.type == "OID":
                oidField = field.name

        # Run Tabulate areas to get a list of MUKEYS and area count
        if bRaster:
            arcpy.SetProgressorLabel("Using SSURGO Raster to extract MUKEYs")
            AddMsgAndPrint("\tUsing SSURGO Raster to extract MUKEYs",0)
            TabulateArea(muLayer,oidField,muRasterPath,mukeyField,outTable,cellSize)
        else:
            cellSize = "10"
            arcpy.SetProgressorLabel("Using SSURGO Polygon layer to extract MUKEYs")
            AddMsgAndPrint("\tUsing SSURGO Polygon layer to extract MUKEYs",0)
            TabulateArea(muLayer,oidField,muPolygonPath,mukeyField,outTable)

        # Create the expression to transpose fields.  Tabulate areas will add an
        # "A_" to the beginning.  It needs to be removed
        fieldsToTranspose = ""
        outTableFields = arcpy.ListFields(outTable,"A_*")
        fieldCount = 1
        for field in outTableFields:
            if fieldCount < len(outTableFields):
                fieldsToTranspose = fieldsToTranspose + field.name + " " + field.name[2:] + ";"
            else:
                fieldsToTranspose = fieldsToTranspose + field.name + " " + field.name[2:]
            fieldCount += 1

        outTransposeTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.TransposeFields_management(outTable,fieldsToTranspose,outTransposeTable,mukeyField,"Shape_Area2")

        # Add a Shape_Area Long field b/c the transposed field is a TEXT
        shpAreaFld = "Shape_Area"
        if not arcpy.ListFields(outTransposeTable,shpAreaFld):
            arcpy.AddField_management(outTransposeTable,shpAreaFld,"LONG")

        arcpy.CalculateField_management(outTransposeTable,shpAreaFld,"[Shape_Area2]")
        arcpy.DeleteField_management(outTransposeTable,"Shape_Area2")

        # Get a list of unique Mukeys in order to form a query expression that will be used in the component table
        uniqueMukeys = set([row[0] for row in arcpy.da.SearchCursor(outTransposeTable, (mukeyField))])

        mukeyExpression = mukeyField + " IN ("
        iCount = 0
        for mukey in uniqueMukeys:
            iCount+=1
            if iCount < len(uniqueMukeys):
                mukeyExpression = mukeyExpression + "'" + str(mukey) + "',"
            else:
                mukeyExpression = mukeyExpression + "'" + str(mukey) + "')"

        """ ---------------------------------------- Setup Component Table -----------------------------------
            Make a copy of the component table but limit the new copy to only those fields that are needed and
            only those records that are needed by using SQL expressions.  This will be used to join to the transposed
            table."""

        compTable = arcpy.ListTables("component", "ALL")

        if not len(compTable):
            AddMsgAndPrint("\n\t\tcomponent table was not found in the SSURGO.gdb File Geodatabase",2)
            return False

        compTablePath = arcpy.env.workspace + os.sep + compTable[0]
        compFields = ['comppct_r','compname','compkind','majcompflag','drainagecl','taxorder','taxgrtgroup','taxtempregime','mukey','cokey']

        for field in compFields:
            if not FindField(compTable[0],field):
                AddMsgAndPrint("\n\t\tComponent Table is missing necessary fields: " + field,2)
                return False

        compTablefields = arcpy.ListFields(compTablePath)

        # Create a fieldinfo object
        fieldinfo = arcpy.FieldInfo()

        # Iterate through the fields and set them to fieldinfo
        for field in compTablefields:
            if field.name in compFields:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            else:
                fieldinfo.addField(field.name, field.name, "HIDDEN", "")

        compView = "comp_view"
        if arcpy.Exists(compView):
            arcpy.Delete_management(compView)

        # The created component_view layer will have fields as set in fieldinfo object
        arcpy.MakeTableView_management(compTablePath, compView, mukeyExpression, workspaces[0], fieldinfo)

        # get a record of the compView table; there better be records; possibly using old dataset
        if int(arcpy.GetCount_management(compView).getOutput(0)) < 1:
            AddMsgAndPrint("\tThere was no match between components and soils",2)
            return False
        else:
            AddMsgAndPrint("\t\tThere are " + str(len(uniqueMukeys)) + " unique mapunits",1)
            AddMsgAndPrint("\t\tThere are " + str(int(arcpy.GetCount_management(compView).getOutput(0))) + " unique components",1)

        """ ------------------------------------ Join the component table and summary statistics table ------------------------------------
            Need to write the joined table out b/c you can't calculate a field on a right join and fields are not listing correctly.
            Recalculate acres weighted by comp %;  There may be some comps that don't add to 100% which would create a difference
            between the intersected soils"""

        arcpy.AddJoin_management(compView,mukeyField,outTransposeTable,mukeyField,"KEEP_ALL")

        outJoinTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.CopyRows_management(compView, outJoinTable)
        arcpy.RemoveJoin_management(compView)

        if arcpy.Exists(outTable):arcpy.Delete_management(outTable)

        """ ------------------------------------ Add comp percentage weighted acres ------------------------------------------------------"""
        compPrctFld = [f.name for f in arcpy.ListFields(outJoinTable,"*comppct_r")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outJoinTable,"*Shape_Area")][0]

        acreField = "weighted_Acres"
        if not arcpy.ListFields(outJoinTable,acreField):
            arcpy.AddField_management(outJoinTable,acreField,"DOUBLE")

        expression = "(([" + shpAreaFld + "]/100.0) * [" + compPrctFld + "]) / 4046.85642"
        arcpy.CalculateField_management(outJoinTable,acreField,expression)

        del soilsFolder,workspaces,rasterList,mukeyField,fieldsToTranspose,outTableFields,fieldCount,
        uniqueMukeys,mukeyExpression,iCount,compTable,compTablePath,compFields,compTablefields,fieldinfo,compView, expression

        if bRaster: del muRasterPath,cellSize
        else: fcList,muPolygonPath

        return outJoinTable

    except:
        errorMsg()
        return False

## ===================================================================================
def getSoilsOrder(outJoinTable):
# This function will report the top 3 taxonomic orders in a given area of interest along
# with their associated component series.  Only those components that are greater than
# 5% of their taxonomic order will be reported.  This function takes in the
# component-mapunit joined table that was created by the function 'getMUKEYandCompInfoTable()'.

    try:
        AddMsgAndPrint("\nSoils Taxonomic Order Information:",0)

        mukeyField = [f.name for f in arcpy.ListFields(outJoinTable,"*mukey")][0]
        compNameFld = [f.name for f in arcpy.ListFields(outJoinTable,"*compname")][0]
        compPrctFld = [f.name for f in arcpy.ListFields(outJoinTable,"*comppct_r")][0]
        compKindFld = [f.name for f in arcpy.ListFields(outJoinTable,"*compkind")][0]
        taxOrderFld = [f.name for f in arcpy.ListFields(outJoinTable,"*taxorder")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outJoinTable,"*Shape_Area")][0]
        acreFld = [f.name for f in arcpy.ListFields(outJoinTable,"*weighted_Acres")][0]

        # Total component weighted acres; may not match the AOI acres
        whereClause = acreFld + " IS NOT NULL"
        totalSoilIntAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=whereClause)])))

        """ ------------------------------- Create a dictionary of unique taxorders and their total acre sum -------------------------------
            Exclude components and taxorders records that are NULL.  Taxorder NULLS will be accounted for at the bottom"""

        # {u'Alfisols': 232.52185224210945, u'Entisols': 9.87166917356607, u'Mollisols': 13.63258202871674}
        taxOrderDict = dict()
        compPrctExpression = arcpy.AddFieldDelimiters(outJoinTable,compPrctFld) + " IS NOT NULL"
        whereClause = compPrctExpression + " AND " + taxOrderFld + " IS NOT NULL"
        for row in arcpy.da.SearchCursor(outJoinTable,[compPrctFld,acreFld,taxOrderFld],where_clause=whereClause,sql_clause=(None,'ORDER BY ' + acreFld + ' DESC')):

            if not taxOrderDict.has_key(row[2]):
                taxOrderDict[row[2]] = row[1]
            else:
                taxOrderDict[row[2]] += row[1]

        if not taxOrderDict:
            AddMsgAndPrint("\n\tAll Taxonmic Order Values are NULL",2)
            return False

        # ---------------------------------- Strictly Formatting for Tax Order printing
        taxOrderFormattingDict = dict()
        for order in taxOrderDict:
            taxOrderFormattingDict[order] = (len(str(splitThousands(round(taxOrderDict[order],1)))))

        maxOrderAcreLength = sorted([orderAcreLength for order,orderAcreLength in taxOrderFormattingDict.iteritems()],reverse=True)[0]
        #maxOrderNameLength = max(sorted([len(order)+1 for order,orderAcreLength in taxOrderFormattingDict.iteritems()],reverse=True)[:3])  # max order name length from the top 3

        """ ------------------------------- Report Taxonomic Order and their comp series -------------------------------
            Report the top 3 Taxonomic Orders that are greater than 10% in coverage.  Only print the component
            series that are above 5%."""
        # [(u'Alfisols', 129.35453762808402), (u'Mollisols', 96.10388326877232), (u'Entisols', 37.445368094602095), (None, 0.0017223240957696508)]
        ordersPrinted = 0
        otherOrdersAcres = 0
        for taxInfo in sorted(taxOrderDict.items(), key=operator.itemgetter(1),reverse=True):

            taxOrderName = taxInfo[0]
            taxOrderAcres = taxInfo[1]

            # Don't report taxorders that are not populated; accounted for above already
            if taxOrderName == 'None' or not taxOrderName:
                continue

            # taxonomic order percent of total area
            taxOrderPrctOfTotal = float("%.1f" %(((taxOrderAcres / totalSoilIntAcres) * 100)))

            if ordersPrinted >= 3:
                otherOrdersAcres += taxOrderAcres
                continue

            # Print Taxonomic Order, Order Acres, Percent of total Area
            taxOrderAcreFormatLength = len(str(splitThousands(round(taxOrderAcres,1))))
            firstDash = ("-" * (60 - len(taxOrderName))) + " "
            secondDash = ("-" * (45 - maxOrderAcreLength)) + " "
            AddMsgAndPrint("\n\t" + taxOrderName + ": " + firstDash + str(splitThousands(round(taxOrderAcres,1))) + " .ac " + secondDash + str(taxOrderPrctOfTotal) + " %" ,1)

            """ ------------------------------- Collect component series information ----------------------------------------"""
            expression = arcpy.AddFieldDelimiters(outJoinTable,taxOrderFld) + " = '" + taxOrderName + "' AND " + compPrctExpression
            with arcpy.da.SearchCursor(outJoinTable,[compPrctFld,compNameFld,compKindFld,acreFld],where_clause=expression) as cursor:

                compDict = dict()        #{u'Bertrand Series': 4.126611328239694, u'Yellowriver Series': 26.780026433416218}
                for row in cursor:

                    compAcres = row[3]

                    if row[2]:
                        mergeCompName = row[1] + " " + row[2]
                    else:
                        # compKind was NULL; WTF!! Talk about data integrity!
                        mergeCompName = row[1]

                    if not compDict.has_key(mergeCompName):
                        compDict[mergeCompName] = compAcres
                    else:
                        compDict[mergeCompName] += compAcres

                    del compAcres,mergeCompName

                if not compDict:
                    AddMsgAndPrint("\t\tThere are NO components associated with this Taxonomic Order")
                    continue

                compPctSorted = sorted(compDict.items(), key=operator.itemgetter(1),reverse=True)[:4]  # [(u'Yellowriver Series', 26.780026433416218), (u'Village Series', 18.838143614081368)]

                # Strictly formatting; get maximum character length for the Acres and Component name
                maxCompAcreLength = sorted([len(splitThousands(round(compAcre,1))) for compName,compAcre in compPctSorted],reverse=True)[0]
                maxCompNameLength = sorted([len(compName) for compName,compAcre in compPctSorted],reverse=True)[0]

                compCount = 1
                for compinfo in compPctSorted:

                    firstSpace = " " * (maxCompNameLength - len(compinfo[0]))
                    secondSpace = " "  * (maxCompAcreLength - len(splitThousands(round(compinfo[1],1))))
                    compAcresPrctOfTotal = str(round((compinfo[1]/taxOrderAcres)*100,1))

                    if compCount < 4:
                        AddMsgAndPrint("\t\t" + compinfo[0] + firstSpace + " --- " + str(splitThousands(round(compinfo[1],1))) + " .ac" + secondSpace + " --- " + compAcresPrctOfTotal + " %",1)
                        compCount+=1
                    else:
                        break

                del compDict,compPctSorted,maxCompNameLength,maxCompAcreLength
            del taxOrderName,taxOrderAcres,expression

            ordersPrinted += 1

        """ ------------------------------ Report Other Taxon Orders that did not get reported for acre accountability purposes --------------"""
        if otherOrdersAcres > 0:
            otherAcresPrct = str(float("%.1f" %(((otherOrdersAcres / totalSoilIntAcres) * 100))))
            secondDash = ((" " * (maxOrderAcreLength-len(splitThousands(round(otherOrdersAcres,1))))) + ((45 - maxOrderAcreLength) * "-")) + " "
            firstDash = (48 * "-") + " "
            AddMsgAndPrint("\n\tOther Orders: " + firstDash + splitThousands(round(otherOrdersAcres,1)) + " .ac " + secondDash + otherAcresPrct + " %",1)
            del otherAcresPrct,firstDash,secondDash

        """ ------------------------------ Report Acres where Taxonomic Orders is NULL for acre accountability purposes --------------"""
        nullTaxOrderAcres = sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=taxOrderFld + " IS NULL AND " + compPrctExpression)])

        if nullTaxOrderAcres > 0:
            nullTaxOrderPrctOfTotal = str(float("%.1f" %(((nullTaxOrderAcres / totalSoilIntAcres) * 100)))) + " %"
            firstDash = (31 * "-") + " "
            secondDash = ((" " * (maxOrderAcreLength-len(splitThousands(round(nullTaxOrderAcres,1))))) + ((45 - maxOrderAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tTaxonomic Order NOT Populated: " + firstDash + str(splitThousands(round(nullTaxOrderAcres,1))) + " .ac " + secondDash + nullTaxOrderPrctOfTotal ,1)
            del nullTaxOrderPrctOfTotal,firstDash,secondDash

        """ ------------------------------ Report Acres where comp percentages don't add up to 100% ----------------------------------
            If components for a specific mapunit only add up to 90% than 10% of the mapunit's acres will be reported.
            Summarize the join table by component percent and then select those mukeys where the summed comp percent
            are less than 100%.  Do not exclude NULL taxon records b/c eventhough they have been accounted for their shortage of 100% has not."""

        outStatsTable2 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(outJoinTable,outStatsTable2,[[compPrctFld,"SUM"],[shpAreaFld,"FIRST"]],mukeyField)

        compPrctFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*comppct_r")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*Shape_Area")][0]

        missingAcres = 0
        for row in arcpy.da.SearchCursor(outStatsTable2,(compPrctFld,shpAreaFld),where_clause=compPrctFld + " < 100"):
            missingAcres += (((100 - row[0])/100) * row[1]) / 4046.85642

        if missingAcres:
            firstDash = (23 * "-") + " "
            secondDash = ((" " * (maxOrderAcreLength-len(splitThousands(round(missingAcres,1))))) + ((45 - maxOrderAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tComponents that do NOT add up to 100%: " + firstDash + splitThousands(round(missingAcres,1)) + " .ac " + secondDash + str(round(((missingAcres/totalSoilIntAcres)*100),1)) + " %",1)

        """ ------------------------------- Clean up time! --------------------------------------------"""
        if arcpy.Exists(outStatsTable2):arcpy.Delete_management(outStatsTable2)

        del mukeyField,compNameFld,compPrctFld,compKindFld,taxOrderFld,shpAreaFld,totalSoilIntAcres,taxOrderDict,compPrctExpression,whereClause
        taxOrderFormattingDict,maxOrderAcreLength,ordersPrinted,otherOrdersAcres,nullTaxOrderAcres,outStatsTable2,missingAcres

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def getSoilsGreatGroup(outJoinTable):
# This function will report the top 3 taxonomic great groups in a given area of interest along
# with their associated component series.  Only those components that are greater than
# 5% of their taxonomic order will be reported.  This function takes in the
# component-mapunit joined table that was created by the function 'getMUKEYandCompInfoTable()'.

    try:
        AddMsgAndPrint("\nSoils Taxonomic Great Group Information:",0)

        mukeyField = [f.name for f in arcpy.ListFields(outJoinTable,"*mukey")][0]
        compNameFld = [f.name for f in arcpy.ListFields(outJoinTable,"*compname")][0]
        compPrctFld = [f.name for f in arcpy.ListFields(outJoinTable,"*comppct_r")][0]
        compKindFld = [f.name for f in arcpy.ListFields(outJoinTable,"*compkind")][0]
        greatGrpFld = [f.name for f in arcpy.ListFields(outJoinTable,"*taxgrtgroup")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outJoinTable,"*Shape_Area")][0]
        acreFld = [f.name for f in arcpy.ListFields(outJoinTable,"*weighted_Acres")][0]

        # Total component weighted acres; may not match the AOI acres
        whereClause = acreFld + " IS NOT NULL"
        totalSoilIntAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=whereClause)])))

        """ ------------------------------- Create a dictionary of unique Tax Great Groups and their total acre sum -------------------------------
            Exclude components and great group records that are NULL.  Great Group NULLS will be accounted for at the bottom"""

        # {u'Alfisols': 232.52185224210945, u'Entisols': 9.87166917356607, u'Mollisols': 13.63258202871674}
        greatGrpDict = dict()
        compPrctExpression = arcpy.AddFieldDelimiters(outJoinTable,compPrctFld) + " IS NOT NULL"
        whereClause = compPrctExpression + " AND " + greatGrpFld + " IS NOT NULL"
        for row in arcpy.da.SearchCursor(outJoinTable,[compPrctFld,acreFld,greatGrpFld],where_clause=whereClause,sql_clause=(None,'ORDER BY ' + acreFld + ' DESC')):

            if not greatGrpDict.has_key(row[2]):
                greatGrpDict[row[2]] = row[1]
            else:
                greatGrpDict[row[2]] += row[1]

        if not greatGrpDict:
            AddMsgAndPrint("\n\tAll Taxonmic Great Group Values are NULL",2)
            return False

        # ---------------------------------- Strictly Formatting for Tax Great Group printing
        greatGrpFormattingDict = dict()
        for group in greatGrpDict:
            greatGrpFormattingDict[group] = (len(str(splitThousands(round(greatGrpDict[group],1)))))

        maxGroupAcreLength = sorted([groupAcreLength for group,groupAcreLength in greatGrpFormattingDict.iteritems()],reverse=True)[0]
        #maxOrderNameLength = max(sorted([len(order)+1 for order,orderAcreLength in taxOrderFormattingDict.iteritems()],reverse=True)[:3])  # max order name length from the top 3

        """ ------------------------------- Report Taxonomic Great Groups and their comp series -------------------------------
            Report the top 3 Taxonomic Great Groups that are greater than 10% in coverage.  Only print the component
            series that are above 5%."""
        # [(u'Alfisols', 129.35453762808402), (u'Mollisols', 96.10388326877232), (u'Entisols', 37.445368094602095), (None, 0.0017223240957696508)]
        groupsPrinted = 0
        otherGroupAcres = 0
        for groupInfo in sorted(greatGrpDict.items(), key=operator.itemgetter(1),reverse=True):

            greatGrpName = groupInfo[0]
            greatGrpAcres = groupInfo[1]

            # Don't report great groups that are not populated; accounted for above already
            if greatGrpName == 'None' or not greatGrpName:
                continue

            # taxonomic great group percent of total area
            greatGrpPrctOfTotal = float("%.1f" %(((greatGrpAcres / totalSoilIntAcres) * 100)))

            if groupsPrinted >= 3:
                otherGroupAcres += greatGrpAcres
                continue

            # Print Taxonomic Great Group, Acres, Percent of total Area
            greatGrpAcreFormatLength = len(str(splitThousands(round(greatGrpAcres,1))))
            firstDash = ("-" * (60 - len(greatGrpName))) + " "
            secondDash = ("-" * (45 - maxGroupAcreLength)) + " "
            AddMsgAndPrint("\n\t" + greatGrpName + ": " + firstDash + str(splitThousands(round(greatGrpAcres,1))) + " .ac " + secondDash + str(greatGrpPrctOfTotal) + " %" ,1)

            """ ------------------------------- Collect component series information ----------------------------------------"""
            expression = arcpy.AddFieldDelimiters(outJoinTable,greatGrpFld) + " = '" + greatGrpName + "' AND " + compPrctExpression
            with arcpy.da.SearchCursor(outJoinTable,[compPrctFld,compNameFld,compKindFld,acreFld],where_clause=expression) as cursor:

                compDict = dict()        #{u'Bertrand Series': 4.126611328239694, u'Yellowriver Series': 26.780026433416218}
                for row in cursor:

                    compAcres = row[3]

                    if row[2]:
                        mergeCompName = row[1] + " " + row[2]
                    else:
                        # compKind was NULL; WTF!! Talk about data integrity!
                        mergeCompName = row[1]

                    if not compDict.has_key(mergeCompName):
                        compDict[mergeCompName] = compAcres
                    else:
                        compDict[mergeCompName] += compAcres

                    del compAcres,mergeCompName

                if not compDict:
                    AddMsgAndPrint("\t\tThere are NO components associated with this Taxonomic Great Group")
                    continue

                compPctSorted = sorted(compDict.items(), key=operator.itemgetter(1),reverse=True)[:4]  # [(u'Yellowriver Series', 26.780026433416218), (u'Village Series', 18.838143614081368)]

                # Strictly formatting; get maximum character length for the Acres and Component name
                maxCompAcreLength = sorted([len(splitThousands(round(compAcre,1))) for compName,compAcre in compPctSorted],reverse=True)[0]
                maxCompNameLength = sorted([len(compName) for compName,compAcre in compPctSorted],reverse=True)[0]

                compCount = 1
                for compinfo in compPctSorted:

                    firstSpace = " " * (maxCompNameLength - len(compinfo[0]))
                    secondSpace = " "  * (maxCompAcreLength - len(splitThousands(round(compinfo[1],1))))
                    compAcresPrctOfTotal = str(round((compinfo[1]/greatGrpAcres)*100,1))

                    if compCount < 4:
                        AddMsgAndPrint("\t\t" + compinfo[0] + firstSpace + " --- " + str(splitThousands(round(compinfo[1],1))) + " .ac" + secondSpace + " --- " + compAcresPrctOfTotal + " %",1)
                        compCount+=1
                    else:
                        break

                del compDict,compPctSorted,maxCompNameLength,maxCompAcreLength
            del greatGrpName,greatGrpAcres,expression

            groupsPrinted += 1

        """ ------------------------------ Report Other Taxon Great Groups that did not get reported for acre accountability purposes --------------"""
        if otherGroupAcres > 0:
            otherAcresPrct = str(float("%.1f" %(((otherGroupAcres / totalSoilIntAcres) * 100))))
            secondDash = ((" " * (maxGroupAcreLength-len(splitThousands(round(otherGroupAcres,1))))) + ((45 - maxGroupAcreLength) * "-")) + " "
            firstDash = (48 * "-") + " "
            AddMsgAndPrint("\n\tOther Orders: " + firstDash + splitThousands(round(otherGroupAcres,1)) + " .ac " + secondDash + otherAcresPrct + " %",1)
            del otherAcresPrct,firstDash,secondDash

        """ ------------------------------ Report Acres where Taxonomic Great Group is NULL for acre accountability purposes --------------"""
        nullGreatGrpAcres = sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=greatGrpFld + " IS NULL AND " + compPrctExpression)])

        if nullGreatGrpAcres > 0:
            nullGreatGrpPrctOfTotal = str(float("%.1f" %(((nullGreatGrpAcres / totalSoilIntAcres) * 100)))) + " %"
            firstDash = (25 * "-") + " "
            secondDash = ((" " * (maxGroupAcreLength-len(splitThousands(round(nullGreatGrpAcres,1))))) + ((45 - maxGroupAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tTaxonomic Great Group NOT Populated: " + firstDash + str(splitThousands(round(nullGreatGrpAcres,1))) + " .ac " + secondDash + nullGreatGrpPrctOfTotal ,1)
            del nullGreatGrpPrctOfTotal,firstDash,secondDash

        """ ------------------------------ Report Acres where comp percentages don't add up to 100% ----------------------------------
            If components for a specific mapunit only add up to 90% than 10% of the mapunit's acres will be reported.
            Summarize the join table by component percent and then select those mukeys where the summed comp percent
            are less than 100%.  Do not exclude NULL taxon records b/c eventhough they have been accounted for their shortage of 100% has not."""

        outStatsTable2 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(outJoinTable,outStatsTable2,[[compPrctFld,"SUM"],[shpAreaFld,"FIRST"]],mukeyField)

        compPrctFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*comppct_r")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*Shape_Area")][0]

        missingAcres = 0
        for row in arcpy.da.SearchCursor(outStatsTable2,(compPrctFld,shpAreaFld),where_clause=compPrctFld + " < 100"):
            missingAcres += (((100 - row[0])/100) * row[1]) / 4046.85642

        if missingAcres:
            firstDash = (23 * "-") + " "
            secondDash = ((" " * (maxGroupAcreLength-len(splitThousands(round(missingAcres,1))))) + ((45 - maxGroupAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tComponents that do NOT add up to 100%: " + firstDash + splitThousands(round(missingAcres,1)) + " .ac " + secondDash + str(round(((missingAcres/totalSoilIntAcres)*100),1)) + " %",1)

        """ ------------------------------- Clean up time! --------------------------------------------"""
        if arcpy.Exists(outStatsTable2):arcpy.Delete_management(outStatsTable2)

        del mukeyField, compNameFld,compPrctFld,compKindFld,greatGrpFld,shpAreaFld,acreFld,whereClause,totalSoilIntAcres,greatGrpDict,
        compPrctExpression,greatGrpFormattingDict,maxGroupAcreLength,groupsPrinted,otherGroupAcres,nullGreatGrpAcres,outStatsTable2,missingAcres

        return True

    except:
        errorMsg()
        return False


## ===================================================================================
def getDrainageClass(outJoinTable):
# This function will report the top 3 taxonomic orders in a given area of interest along
# with their associated component series.  Only those components that are greater than
# 5% of their taxonomic order will be reported.  This function takes in the
# component-mapunit joined table that was created by the function 'getMUKEYandCompInfoTable()'.
# This pre-processed table will get joined to the parent material group table and eventually
# the parent material table.

    try:
        AddMsgAndPrint("\nSoils Drainage Class Information:",0)

        mukeyField = [f.name for f in arcpy.ListFields(outJoinTable,"*mukey")][0]
        compNameFld = [f.name for f in arcpy.ListFields(outJoinTable,"*compname")][0]
        compPrctFld = [f.name for f in arcpy.ListFields(outJoinTable,"*comppct_r")][0]
        compKindFld = [f.name for f in arcpy.ListFields(outJoinTable,"*compkind")][0]
        drainageFld = [f.name for f in arcpy.ListFields(outJoinTable,"*drainagecl")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outJoinTable,"*Shape_Area")][0]
        acreFld = [f.name for f in arcpy.ListFields(outJoinTable,"*weighted_Acres")][0]

        # Total component weighted acres; may not match the AOI acres
        whereClause = acreFld + " IS NOT NULL"
        totalSoilIntAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=whereClause)])))

        """ ------------------------------- Create a dictionary of unique drainage classes and their total acre sum -------------------------------
            Exclude components and drainage records that are NULL.  Taxorder NULLS will be accounted for at the bottom"""

        # {u'Alfisols': 232.52185224210945, u'Entisols': 9.87166917356607, u'Mollisols': 13.63258202871674}
        drainageDict = dict()
        compPrctExpression = arcpy.AddFieldDelimiters(outJoinTable,compPrctFld) + " IS NOT NULL"
        whereClause = compPrctExpression + " AND " + drainageFld + " IS NOT NULL"
        for row in arcpy.da.SearchCursor(outJoinTable,[compPrctFld,acreFld,drainageFld],where_clause=whereClause,sql_clause=(None,'ORDER BY ' + acreFld + ' DESC')):

            if not drainageDict.has_key(row[2]):
                drainageDict[row[2]] = row[1]
            else:
                drainageDict[row[2]] += row[1]

        # ---------------------------------- Strictly Formatting for Drainage Class printing
        drainageFormattingDict = dict()
        for drainClass in drainageDict:
            drainageFormattingDict[drainClass] = (len(str(splitThousands(round(drainageDict[drainClass],1)))))

        maxDrainAcreLength = sorted([classAcreLength for drainClass,classAcreLength in drainageFormattingDict.iteritems()],reverse=True)[0]
        #maxOrderNameLength = max(sorted([len(order)+1 for order,orderAcreLength in taxOrderFormattingDict.iteritems()],reverse=True)[:3])  # max order name length from the top 3

        """ ------------------------------- Report Drainage Class and their comp series -------------------------------
            Report the top 3 Drainage classes that are greater than 10% in coverage.  Only print the component
            series that are above 5%."""
        # [(u'Alfisols', 129.35453762808402), (u'Mollisols', 96.10388326877232), (u'Entisols', 37.445368094602095), (None, 0.0017223240957696508)]
        drainagesPrinted = 0
        otherDrainageAcres = 0
        for drainInfo in sorted(drainageDict.items(), key=operator.itemgetter(1),reverse=True):

            drainClassName = drainInfo[0]
            drainClassAcres = drainInfo[1]

            # Don't report drainage classes that are not populated; accounted for above already
            if drainClassName == 'None' or not drainClassName:
                continue

            # Drainage class percent of total area
            drainClassPrctOfTotal = float("%.1f" %(((drainClassAcres / totalSoilIntAcres) * 100)))

            if drainagesPrinted >= 3:
                otherDrainageAcres += drainClassAcres
                continue

            # Print Drainage class, class Acres, Percent of total Area
            drainAcreFormatLength = len(str(splitThousands(round(drainClassAcres,1))))
            firstDash = ("-" * (60 - len(drainClassName))) + " "
            secondDash = ("-" * (45 - maxDrainAcreLength)) + " "
            AddMsgAndPrint("\n\t" + drainClassName + ": " + firstDash + str(splitThousands(round(drainClassAcres,1))) + " .ac " + secondDash + str(drainClassPrctOfTotal) + " %" ,1)

            """ ------------------------------- Collect component series information ----------------------------------------"""
            expression = arcpy.AddFieldDelimiters(outJoinTable,drainageFld) + " = '" + drainClassName + "' AND " + compPrctExpression
            with arcpy.da.SearchCursor(outJoinTable,[compPrctFld,compNameFld,compKindFld,acreFld],where_clause=expression) as cursor:

                compDict = dict()        #{u'Bertrand Series': 4.126611328239694, u'Yellowriver Series': 26.780026433416218}
                for row in cursor:

                    compAcres = row[3]

                    if row[2]:
                        mergeCompName = row[1] + " " + row[2]
                    else:
                        # compKind was NULL; WTF!! Talk about data integrity!
                        mergeCompName = row[1]

                    if not compDict.has_key(mergeCompName):
                        compDict[mergeCompName] = compAcres
                    else:
                        compDict[mergeCompName] += compAcres

                    del compAcres,mergeCompName

                if not compDict:
                    AddMsgAndPrint("\t\tThere are NO components associated with this Drainage Class")
                    continue

                compPctSorted = sorted(compDict.items(), key=operator.itemgetter(1),reverse=True)[:4]  # [(u'Yellowriver Series', 26.780026433416218), (u'Village Series', 18.838143614081368)]

                # Strictly formatting; get maximum character length for the Acres and Component name
                maxCompAcreLength = sorted([len(splitThousands(round(compAcre,1))) for compName,compAcre in compPctSorted],reverse=True)[0]
                maxCompNameLength = sorted([len(compName) for compName,compAcre in compPctSorted],reverse=True)[0]

                compCount = 1
                for compinfo in compPctSorted:

                    firstSpace = " " * (maxCompNameLength - len(compinfo[0]))
                    secondSpace = " "  * (maxCompAcreLength - len(splitThousands(round(compinfo[1],1))))
                    compAcresPrctOfTotal = str(round((compinfo[1]/drainClassAcres)*100,1))

                    if compCount < 4:
                        AddMsgAndPrint("\t\t" + compinfo[0] + firstSpace + " --- " + str(splitThousands(round(compinfo[1],1))) + " .ac" + secondSpace + " --- " + compAcresPrctOfTotal + " %",1)
                        compCount+=1
                    else:
                        break

                del compDict,compPctSorted,maxCompNameLength,maxCompAcreLength
            del drainClassName,drainClassAcres,expression

            drainagesPrinted += 1

        """ ------------------------------ Report Other Drainage Classes that did not get reported for acre accountability purposes --------------"""
        if otherDrainageAcres > 0:
            otherAcresPrct = str(float("%.1f" %(((otherDrainageAcres / totalSoilIntAcres) * 100))))
            secondDash = ((" " * (maxDrainAcreLength-len(splitThousands(round(otherDrainageAcres,1))))) + ((45 - maxDrainAcreLength) * "-")) + " "
            firstDash = (47 * "-") + " "
            AddMsgAndPrint("\n\tOther Orders: " + firstDash + splitThousands(round(otherDrainageAcres,1)) + " .ac " + secondDash + otherAcresPrct + " %",1)
            del otherAcresPrct,firstDash,secondDash

        """ ------------------------------ Report Acres where Drainage Class is NULL for acre accountability purposes --------------"""
        nullDrainAcres = sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=drainageFld + " IS NULL AND " + compPrctExpression)])

        if nullDrainAcres > 0:
            nullDrainPrctOfTotal = str(float("%.1f" %(((nullDrainAcres / totalSoilIntAcres) * 100)))) + " %"
            firstDash = (31 * "-") + " "
            secondDash = ((" " * (maxDrainAcreLength-len(splitThousands(round(nullDrainAcres,1))))) + ((45 - maxDrainAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tDrainage Class NOT Populated: " + firstDash + str(splitThousands(round(nullDrainAcres,1))) + " .ac " + secondDash + nullDrainPrctOfTotal ,1)
            del nullDrainPrctOfTotal,firstDash,secondDash

        """ ------------------------------ Report Acres where comp percentages don't add up to 100% ----------------------------------
            If components for a specific mapunit only add up to 90% than 10% of the mapunit's acres will be reported.
            Summarize the join table by component percent and then select those mukeys where the summed comp percent
            are less than 100%.  Do not exclude NULL drainage class records b/c eventhough they have been accounted for their shortage of 100% has not."""

        outStatsTable2 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(outJoinTable,outStatsTable2,[[compPrctFld,"SUM"],[shpAreaFld,"FIRST"]],mukeyField)

        compPrctFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*comppct_r")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*Shape_Area")][0]

        missingAcres = 0
        for row in arcpy.da.SearchCursor(outStatsTable2,(compPrctFld,shpAreaFld),where_clause=compPrctFld + " < 100"):
            missingAcres += (((100 - row[0])/100) * row[1]) / 4046.85642

        if missingAcres:
            firstDash = (23 * "-") + " "
            secondDash = ((" " * (maxDrainAcreLength-len(splitThousands(round(missingAcres,1))))) + ((45 - maxDrainAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tComponents that do NOT add up to 100%: " + firstDash + splitThousands(round(missingAcres,1)) + " .ac " + secondDash + str(round(((missingAcres/totalSoilIntAcres)*100),1)) + " %",1)

        """ ------------------------------- Clean up time! --------------------------------------------"""
        if arcpy.Exists(outStatsTable2):arcpy.Delete_management(outStatsTable2)

        del mukeyField,compNameFld,compPrctFld,compKindFld,drainageFld,shpAreaFld,totalSoilIntAcres,drainageDict,compPrctExpression,whereClause
        drainageFormattingDict,maxDrainAcreLength,drainagesPrinted,otherDrainageAcres,nullDrainAcres,outStatsTable2,missingAcres

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def getTempRegime(outJoinTable):
# This function will report all Temperarture regimes in a given area of interest
# This function takes in the component-mapunit joined table that was created by the function
# 'getMUKEYandCompInfoTable()'.

    try:
        AddMsgAndPrint("\nSoils Temperature Regime Information:",0)

        mukeyField = [f.name for f in arcpy.ListFields(outJoinTable,"*mukey")][0]
        compPrctFld = [f.name for f in arcpy.ListFields(outJoinTable,"*comppct_r")][0]
        tempFld = [f.name for f in arcpy.ListFields(outJoinTable,"*taxtempregime")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outJoinTable,"*Shape_Area")][0]
        acreFld = [f.name for f in arcpy.ListFields(outJoinTable,"*weighted_Acres")][0]

        # Total component weighted acres; may not match the AOI acres
        whereClause = acreFld + " IS NOT NULL"
        totalSoilIntAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=whereClause)])))

        """ ------------------------------- Create a dictionary of unique temp regimes and their total acre sum -------------------------------
            Exclude components and temp regime records that are NULL.  temp regime NULLS will be accounted for at the bottom"""

        # {u'Alfisols': 232.52185224210945, u'Entisols': 9.87166917356607, u'Mollisols': 13.63258202871674}
        tempDict = dict()
        compPrctExpression = arcpy.AddFieldDelimiters(outJoinTable,compPrctFld) + " IS NOT NULL"
        whereClause = compPrctExpression + " AND " + tempFld + " IS NOT NULL"
        for row in arcpy.da.SearchCursor(outJoinTable,[compPrctFld,acreFld,tempFld],where_clause=whereClause,sql_clause=(None,'ORDER BY ' + acreFld + ' DESC')):

            if not tempDict.has_key(row[2]):
                tempDict[row[2]] = row[1]
            else:
                tempDict[row[2]] += row[1]

        if not tempDict:
            AddMsgAndPrint("\n\tAll Temperature Regime Values are NULL",2)
            return False

        # ---------------------------------- Strictly Formatting for Temp Regime printing
        tempFormattingDict = dict()
        for temp in tempDict:
            tempFormattingDict[temp] = (len(str(splitThousands(round(tempDict[temp],1)))))

        maxTempAcreLength = sorted([tempAcreLength for temp,tempAcreLength in tempFormattingDict.iteritems()],reverse=True)[0]

        """ ------------------------------- Report All Temperature Regimes with percentages  -------------------------------"""

        # [(u'Alfisols', 129.35453762808402), (u'Mollisols', 96.10388326877232), (u'Entisols', 37.445368094602095), (None, 0.0017223240957696508)]
        for tempInfo in sorted(tempDict.items(), key=operator.itemgetter(1),reverse=True):

            tempName = tempInfo[0]
            tempAcres = tempInfo[1]

            # Don't report temp regimes that are not populated; accounted for above already
            if tempName == 'None' or not tempName:
                continue

            # temperature regime as a percent of total area
            tempPrctOfTotal = float("%.1f" %(((tempAcres / totalSoilIntAcres) * 100)))

            # Print Temp Regime, Regime Acres, Percent of total Area
            tempAcreFormatLength = len(str(splitThousands(round(tempAcres,1))))
            firstDash = ("-" * (60 - len(tempName))) + " "
            secondDash = ("-" * (45 - maxTempAcreLength)) + " "
            AddMsgAndPrint("\t" + tempName + ": " + firstDash + str(splitThousands(round(tempAcres,1))) + " .ac " + secondDash + str(tempPrctOfTotal) + " %" ,1)

            del tempName,tempAcres,tempPrctOfTotal,tempAcreFormatLength,firstDash,secondDash

        """ ------------------------------ Report Acres where Temperature Regime is NULL for acre accountability purposes --------------"""
        nullTempAcres = sum([row[0] for row in arcpy.da.SearchCursor(outJoinTable,(acreFld),where_clause=tempFld + " IS NULL AND " + compPrctExpression)])

        if nullTempAcres > 0:
            nullTempPrctOfTotal = str(float("%.1f" %(((nullTempAcres / totalSoilIntAcres) * 100)))) + " %"
            firstDash = (28 * "-") + " "
            secondDash = ((" " * (maxTempAcreLength-len(splitThousands(round(nullTempAcres,1))))) + ((45 - maxTempAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tTemperature Regime NOT Populated: " + firstDash + str(splitThousands(round(nullTempAcres,1))) + " .ac " + secondDash + nullTempPrctOfTotal ,1)
            del nullTempPrctOfTotal,firstDash,secondDash

        """ ------------------------------ Report Acres where comp percentages don't add up to 100% ----------------------------------
            If components for a specific mapunit only add up to 90% than 10% of the mapunit's acres will be reported.
            Summarize the join table by component percent and then select those mukeys where the summed comp percent
            are less than 100%.  Do not exclude NULL taxon records b/c eventhough they have been accounted for their shortage of 100% has not."""

        outStatsTable2 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(outJoinTable,outStatsTable2,[[compPrctFld,"SUM"],[shpAreaFld,"FIRST"]],mukeyField)

        compPrctFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*comppct_r")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outStatsTable2,"*Shape_Area")][0]

        missingAcres = 0
        for row in arcpy.da.SearchCursor(outStatsTable2,(compPrctFld,shpAreaFld),where_clause=compPrctFld + " < 100"):
            missingAcres += (((100 - row[0])/100) * row[1]) / 4046.85642

        if missingAcres:
            firstDash = (23 * "-") + " "
            secondDash = ((" " * (maxTempAcreLength-len(splitThousands(round(missingAcres,1))))) + ((45 - maxTempAcreLength) * "-")) + " "
            AddMsgAndPrint("\n\tComponents that do NOT add up to 100%: " + firstDash + splitThousands(round(missingAcres,1)) + " .ac " + secondDash + str(round(((missingAcres/totalSoilIntAcres)*100),1)) + " %",1)
            del firstDash,secondDash

        """ ------------------------------- Clean up time! --------------------------------------------"""
        if arcpy.Exists(outStatsTable2):arcpy.Delete_management(outStatsTable2)

        del mukeyField,compPrctFld,tempFld,shpAreaFld,acreFld,whereClause,totalSoilIntAcres,tempDict,compPrctExpression,
        tempFormattingDict,maxTempAcreLength,nullTempAcres,outStatsTable2,missingAcres

        return True

    except:
        errorMsg()
        return False


## ===================================================================================
def getParentMaterial(outJoinTable):
# This function will report the top 5 Parent Material kinds in a given area of interest
# This function takes in the component-mapunit joined table that was created by the
# function 'getMUKEYandCompInfoTable()'.  This pre-processed table will get joined to
# the parent material group table and eventually the parent material table.

    try:
        AddMsgAndPrint("\nSoils Parent Material Kind Information:\n",0)

        # Path to soils folder
        soilsFolder = geoFolder + os.sep + "soils"

        # Check if soils folder exists
        if not os.path.exists(soilsFolder):
            AddMsgAndPrint("\n\t\"soils\" folder was not found in your MLRAGeodata Folder -- Cannot get Component Information\n",2)
            return False
        else:
            arcpy.env.workspace = soilsFolder

        # List all file geodatabases in the current workspace
        workspaces = arcpy.ListWorkspaces("SSURGO_*", "FileGDB")

        if len(workspaces) == 0:
            AddMsgAndPrint("\n\t\"SSURGO.gdb\" was not found in the soils folder -- Cannot get Component Parent Material Information\n",2)
            return False

        if len(workspaces) > 1:
            AddMsgAndPrint("\n\t There are muliple \"SSURGO_*.gdb\" in the soils folder -- Cannot get Component Information\n",2)
            return False

        # Set the environment workspace to the SSURGO FGDB
        arcpy.env.workspace = workspaces[0]

        # Get field names from the input join table
        comppctField = [f.name for f in arcpy.ListFields(outJoinTable,"*comppct_r")][0]
        cokeyField = [f.name for f in arcpy.ListFields(outJoinTable,"*cokey")][0]
        acreFld = [f.name for f in arcpy.ListFields(outJoinTable,"*weighted_Acres")][0]
        shpAreaFld = [f.name for f in arcpy.ListFields(outJoinTable,"*Shape_Area")][0]

        """ ---------------------------------------- Setup Component Parent Material Group Table -----------------------------------
            Make a copy of the component table but limit the new copy to only those fields that are needed and
            only those records that are needed by using SQL expressions"""

        # Create expression to isolate component parent material group keys
        uniqueCokeys = set([row[0] for row in arcpy.da.SearchCursor(outJoinTable, (cokeyField))])

        cokeyExpression = "cokey IN ("
        iCount = 0
        for cokey in uniqueCokeys:
            iCount+=1
            if iCount < len(uniqueCokeys):
                cokeyExpression = cokeyExpression + "'" + str(cokey) + "',"
            else:
                cokeyExpression = cokeyExpression + "'" + str(cokey) + "')"

        copmgrpTable = arcpy.ListTables("copmgrp", "ALL")

        if not len(copmgrpTable):
            AddMsgAndPrint("\n\tComponent Parent Material Group (copmgrp) table was not found in the SSURGO.gdb File Geodatabase",2)
            return False

        copmgrpTablePath = arcpy.env.workspace + os.sep + copmgrpTable[0]
        copmgrpFields = ['cokey','copmgrpkey']

        for field in copmgrpFields:
            if not FindField(copmgrpTable[0],field):
                AddMsgAndPrint("\n\tComponent Parent Material Group Table is missing necessary fields: " + field,2)
                return False

        copmgrpTablefields = arcpy.ListFields(copmgrpTablePath)

        # Create a fieldinfo object
        fieldinfo = arcpy.FieldInfo()

        # Iterate through the fields and set them to fieldinfo
        for field in copmgrpTablefields:
            if field.name in copmgrpFields:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            else:
                fieldinfo.addField(field.name, field.name, "HIDDEN", "")

        copmgrpView = "copmgrp_view"
        if arcpy.Exists(copmgrpView):
            arcpy.Delete_management(copmgrpView)

        # The created copmgrp_view layer will have fields as set in fieldinfo object
        arcpy.MakeTableView_management(copmgrpTablePath, copmgrpView, cokeyExpression, workspaces[0], fieldinfo)

        # get a record of the compView table; there better be records; possibly using old dataset
        if int(arcpy.GetCount_management(copmgrpView).getOutput(0)) < 1:
            AddMsgAndPrint("\n\tThere was no match between component and copmgrp tables",2)
            return False

        """ --------------------------- 2nd Join - Component Parent Material Group table and Component Table ------------------------
            Need to write the joined table out b/c you can't calculate a field on a right join and fields are not listing correctly.
            Recalculate acres weighted by comp %"""

        arcpy.AddJoin_management(copmgrpView,"cokey",outJoinTable,cokeyField,"KEEP_ALL")

        outJoinTable2 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.CopyRows_management(copmgrpView, outJoinTable2)
        arcpy.RemoveJoin_management(copmgrpView)

        """ ---------------------------------------- Setup Component Parent Material Table -----------------------------------"""
        # Create expression to isolate component parent material group keys
        copmgrpkeyField = [f.name for f in arcpy.ListFields(outJoinTable2,"*copmgrpkey")][0]
        uniqueCopmgrpkey = set([row[0] for row in arcpy.da.SearchCursor(outJoinTable2, (copmgrpkeyField))])

        copmgrpkeyExpression = "copmgrpkey IN ("
        iCount = 0
        for copmgrpkey in uniqueCopmgrpkey:
            iCount+=1
            if iCount < len(uniqueCopmgrpkey):
                copmgrpkeyExpression = copmgrpkeyExpression + "'" + str(copmgrpkey) + "',"
            else:
                copmgrpkeyExpression = copmgrpkeyExpression + "'" + str(copmgrpkey) + "')"

        copmTable = arcpy.ListTables("copm", "ALL")

        if not len(copmTable):
            AddMsgAndPrint("\n\tComponent Parent Material (copm) table was not found in the SSURGO.gdb File Geodatabase",2)
            return False

        copmTablePath = arcpy.env.workspace + os.sep + copmTable[0]
        copmFields = ['pmkind','copmgrpkey']

        for field in copmFields:
            if not FindField(copmTable[0],field):
                AddMsgAndPrint("\n\tComponent Parent Material Table is missing necessary fields: " + field,2)
                return False

        copmTablefields = arcpy.ListFields(copmTablePath)

        # Create a fieldinfo object
        fieldinfo = arcpy.FieldInfo()

        # Iterate through the fields and set them to fieldinfo
        for field in copmTablefields:
            if field.name in copmFields:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            else:
                fieldinfo.addField(field.name, field.name, "HIDDEN", "")

        copmView = "copm_view"
        if arcpy.Exists(copmView):
            arcpy.Delete_management(copmView)

        # The created copmgrp_view layer will have fields as set in fieldinfo object
        arcpy.MakeTableView_management(copmTablePath, copmView, copmgrpkeyExpression, workspaces[0], fieldinfo)

        # get a record of the compView table; there better be records; possibly using old dataset
        if int(arcpy.GetCount_management(copmView).getOutput(0)) < 1:
            AddMsgAndPrint("\n\tThere was no match between component and copmgrp tables",2)
            return False

        """ --------------------------- 3rd Join - Component Parent Material Group table and Component Table ------------------------
            Need to write the joined table out b/c you can't calculate a field on a right join and fields are not listing correctly.
            Recalculate acres weighted by comp %"""

        arcpy.AddJoin_management(copmView,"copmgrpkey",outJoinTable2,copmgrpkeyField,"KEEP_ALL")

        outJoinTable3 = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.CopyRows_management(copmView, outJoinTable3)
        arcpy.RemoveJoin_management(copmView)

        acreFld = [f.name for f in arcpy.ListFields(outJoinTable3,"*weighted_Acres")][0]
        pmKindFld = [f.name for f in arcpy.ListFields(outJoinTable3,"*pmkind")][0]

        outPmTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
        arcpy.Statistics_analysis(outJoinTable3,outPmTable,[[acreFld, "SUM"]],pmKindFld)

        """ ------------------------------- Report Parent Material Kind -------------------------------
            Report the top 3 Parent Material Kind that are greater than 10% in coverage.  Only print the component
            series that are above 5%."""

        acreFld = [f.name for f in arcpy.ListFields(outPmTable,"*weighted_Acres")][0]
        pmKindFld = [f.name for f in arcpy.ListFields(outPmTable,"*pmkind")][0]
        totalPMkindAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(outPmTable, (acreFld))])))

        pmCount = 1
        pmDict = dict()
        for row in arcpy.da.SearchCursor(outPmTable,[pmKindFld,acreFld],sql_clause=(None,'ORDER BY ' + acreFld + ' DESC')):
            if pmCount < 6:
                pmDict[row[0]] = (round((row[1]/totalPMkindAcres)*100,1),len(row[0]))
            pmCount += 1

        maxPMLength = sorted([pmInfo[1] for pmKind,pmInfo in pmDict.iteritems()],reverse=True)[0]
        pmDictSorted = sorted(pmDict.items(), key=operator.itemgetter(1),reverse=True)

        totalPercent = 0.0
        for pmInfo in pmDictSorted:
            pmKind = pmInfo[0]
            pmPercent = pmInfo[1][0]
            pmLength = pmInfo[1][1]
            theSpace = " " * (maxPMLength - pmLength)

            AddMsgAndPrint("\t" + pmKind + theSpace + " ---- " + str(pmPercent) + " %",1)

            totalPercent += pmPercent
            del pmKind,pmPercent,pmLength,theSpace

        if totalPercent < 100:
            theSpace = " " * (maxPMLength - 5)
            AddMsgAndPrint("\tOther" + theSpace + " ---- " + str(100.0 - totalPercent) + " %",1)

        """ ------------------------------- Clean up time! --------------------------------------------"""
        for table in [outJoinTable2,outJoinTable3,outPmTable]:
            if arcpy.Exists(table):
                arcpy.Delete_management(table)

        del soilsFolder,workspaces,comppctField,cokeyField,acreFld,shpAreaFld,uniqueCokeys,cokeyExpression,iCount,
        copmgrpTable,copmgrpTablePath,copmgrpFields,copmgrpTablefields,fieldinfo,copmgrpView,outJoinTable2,copmgrpkeyField
        uniqueCopmgrpkey,copmgrpkeyExpression,copmTable,copmTablePath,copmFields,copmTablefields,copmView,pmKindFld,
        totalPMkindAcres,pmCount,pmDict,maxPMLength,pmDictSorted,totalPercent

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

        if not len(DEMraster):
            AddMsgAndPrint("\tDEM Grid was not found in the Elevation File Geodatabase",2)
            return False

        # Get the linear unit of the DEM (Feet or Meters)
        rasterUnit = arcpy.Describe(DEMraster[0]).SpatialReference.LinearUnitName

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
        outZoneTable = scratchWS + os.sep +"demZoneTable"

        # Delete Zonal Statistics Table if it exists
        if arcpy.Exists(outZoneTable):
            arcpy.Delete_management(outZoneTable)

        # Run Zonal Statistics on the muLayer agains the DEM
        # NODATA cells are not ignored;
        try:
            outZSaT = ZonalStatisticsAsTable(muLayer, zoneField, DEMraster[0], outZoneTable, "DATA", "ALL")
        except:
            if bFeatureLyr:
                outZSaT = ZonalStatisticsAsTable(muLayerExtent, zoneField, DEMraster[0], outZoneTable, "DATA", "ALL")
            else:
                outZSaT = ZonalStatisticsAsTable(tempMuLayer, zoneField, DEMraster[0], outZoneTable, "DATA", "ALL")

        zoneTableFields = [zoneField,"MIN","MAX","MEAN"]
        with arcpy.da.SearchCursor(outZoneTable, zoneTableFields) as cursor:

            for row in cursor:

                min = splitThousands(round(row[1],1))
                max = splitThousands(round(row[2],1))
                mean = splitThousands(round(row[3],1))
                minConv = str(splitThousands(round((row[1] * conversion[0]),1)) + " (" + conversion[1] + ")")
                maxConv = str(splitThousands(round((row[2] * conversion[0]),1)) + " (" + conversion[1] + ")")
                meanConv = str(splitThousands(round((row[3] * conversion[0]),1)) + " (" + conversion[1] + ")")

                if munamePresent and areasymPresent and mukeyPresent and zoneField != "MLRA_Temp":
                    spaceAfter = " " * (maxMukeyLength - len(row[0]))
                    muName = muDict.get(row[0])[0]
                    areaSymbol = muDict.get(row[0])[5]
                    AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + str(row[0]) + spaceAfter + "  --  " + muName,0)
                    theTab = "\t" * 2
                    del spaceAfter, muName, areaSymbol

                # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                elif (not munamePresent or not areasymPresent) and mukeyPresent and zoneField != "MLRA_Temp":
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
        climateLyrs = ["TempAvg_Annual","TempMax_AvgAnnual","TempMin_AvgAnnual","PrecipAvg_Annual"]
        climateLyrDef = ["Average Annual Temperature:","Average Max Annual Temp:","Average Min Annual Temp:","Average Annual Precipitation:"]
        uniqueZones = set([row[0] for row in arcpy.da.SearchCursor(muLayer, (zoneField))])

        """ ---------------------  Run Zonal Statistics ------------------------------ """
        for climateLyr in climateLyrs:

            raster = arcpy.ListRasters(climateLyr + "*","GRID")

            if not len(raster):
                AddMsgAndPrint("\t\"" + climateLyr + "\" raster was not found in the Climate.gdb File Geodatabase",2)
                return False

            # output Zonal Statistics Table
            outZoneTable = scratchWS + os.sep + climateLyr
            #outZoneTable = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB + os.sep + climateLyr)

            # Delete Zonal Statistics Table if it exists
            if arcpy.Exists(outZoneTable):
                arcpy.Delete_management(outZoneTable)

            # Run Zonal Statistics on the muLayer agains the climate layer
            # NODATA cells are not ignored;
            try:
                outZSaT = ZonalStatisticsAsTable(muLayer, zoneField, raster[0], outZoneTable, "DATA", "ALL")
            except:
                if bFeatureLyr:
                    outZSaT = ZonalStatisticsAsTable(muLayerExtent, zoneField, raster[0], outZoneTable, "DATA", "ALL")
                else:
                    outZSaT = ZonalStatisticsAsTable(tempMuLayer, zoneField, raster[0], outZoneTable, "DATA", "ALL")

            zoneTableFields = [zoneField,"MEAN"]
            del raster, outZoneTable

        """ ---------------------  Report by Zone b/c there are multiple tables ------------------------------ """

        for zone in uniqueZones:

            # Add heading if analysis is done by MUKEY
            if munamePresent and areasymPresent and mukeyPresent and zoneField != "MLRA_Temp":
                spaceAfter = " " * (maxMukeyLength - len(zone))
                muName = muDict.get(zone)[0]
                areaSymbol = muDict.get(zone)[5]
                AddMsgAndPrint("\n\t" + areaSymbol + "  --  " + str(zone) + spaceAfter + "  --  " + muName,0)
                theTab = "\t" * 2
                del muName,spaceAfter, areaSymbol

            # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
            elif (not munamePresent or not areasymPresent) and mukeyPresent and zoneField != "MLRA_Temp":
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
                        value = row[1]
                        firstSpace = " " * (30 - len(climateLyrDef[i]))

                        if i < 3:
                            field1 = str(round(((float(value) / 100) * 1.8) + 32)) + " F"   # Temp Fehrenheit
                            field2 = str(round(float(value) / 100)) + " C"                         # Temp Celsius converted from values

                        else:
                            field1 = str(int(round(float(value) / 100))) + " mm"                 # Precip units in MM rounded to the nearest mm
                            field2 = str(int(round((float(value) / 100) * 0.0393701))) + " inches"    # Precip units in inches

                        AddMsgAndPrint(theTab + climateLyrDef[i] + firstSpace + "  --  " + field1 + "  --  " + field2,1)
                        del value,firstSpace,field1,field2

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
                    if munamePresent and areasymPresent and mukeyPresent and zoneField != "MLRA_Temp":
                        firstSpace = " " * (maxMukeyLength - len(mukey))
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + firstSpace + "  --  " + muName)
                        theTab = "\t" * 3

                    # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not munamePresent or not areasymPresent) and mukeyPresent and zoneField != "MLRA_Temp":
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

                            """ Actual Reporting of acres and mapunit % --  What a formatting nightmare  """
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
                    if munamePresent and areasymPresent and mukeyPresent and zoneField != "MLRA_Temp":
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + "  --  " + muName)
                        theTab = "\t" * 3

                     # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not munamePresent or not areasymPresent) and mukeyPresent and zoneField != "MLRA_Temp":
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
                TabulateArea(muLayer, zoneField, raster, theValueField, outTAtable, cellSize)
            except:
                if bFeatureLyr:
                    TabulateArea(muLayerExtent, zoneField, raster, theValueField, outTAtable, cellSize)
                else:
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
                    if munamePresent and areasymPresent and mukeyPresent and zoneField != "MLRA_Temp":
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + "  --  " + muName)
                        theTab = "\t" * 3

                    # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not munamePresent or not areasymPresent) and mukeyPresent and zoneField != "MLRA_Temp":
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
                TabulateArea(muLayer, zoneField, raster, theValueField, outTAtable, cellSize)
            except:
                if bFeatureLyr:
                    TabulateArea(muLayerExtent, zoneField, raster, theValueField, outTAtable, cellSize)
                else:
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
                    if munamePresent and areasymPresent and mukeyPresent and zoneField != "MLRA_Temp":
                        muName = muDict.get(zone)[0]
                        areaSymbol = muDict.get(zone)[5]
                        AddMsgAndPrint("\n\t\t" + areaSymbol + "  --  " + zone + "  --  " + muName)
                        theTab = "\t" * 3

                    # Only MUKEY was present and soils FGDB was not available to retrieve Areasymbol and MuNAME
                    elif (not munamePresent or not areasymPresent) and mukeyPresent and zoneField != "MLRA_Temp":
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
                if munamePresent and areasymPresent and mukeyPresent:
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
            AddMsgAndPrint("\t\"Wetlands.gdb\" was not found in the hydrography folder",2)
            return False

        arcpy.env.workspace = workspaces[0]

        fcList = arcpy.ListFeatureClasses("wetlands_a_*","Polygon")

        if not len(fcList):
            AddMsgAndPrint("\twetlands_a feature class was not found in the Wetlands.gdb File Geodatabase",2)
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
                if munamePresent and areasymPresent and mukeyPresent:
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
        analysisType = "MLRA Mapunit" # MLRA (Object ID)

##        muLayer = r'C:\Temp\scratch.gdb\MLRA94D'
##        geoFolder = r'D:\MLRA_Geodata\MLRA_Workspace_Rhinelander\MLRAGeodata'
##        analysisType = 'MLRA Mapunit'

        # Check Availability of Spatial Analyst Extension
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
            else:
                raise ExitError,"\n\nSpatial Analyst license is unavailable.  May need to turn it on!"

        except LicenseError:
            raise ExitError,"\n\nSpatial Analyst license is unavailable.  May need to turn it on!"
        except arcpy.ExecuteError:
            raise ExitError, arcpy.GetMessages(2)

        # Set overwrite option
        arcpy.env.overwriteOutput = True

        mukeyPresent = False
        munamePresent = False
        areasymPresent = False
        muDict = dict()

        # Start by getting information about the input layer
        descInput = arcpy.Describe(muLayer)
        muLayerDT = descInput.dataType.upper()
        bFeatureLyr = False

        if muLayerDT == "FEATURELAYER":
            bFeatureLyr = True
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

        #textFilePath = outputFolder + os.sep + os.path.basename(os.path.splitext(str(muLayer))[0]) + ("_MUKEY.txt" if analysisType == "Mapunit (MUKEY)" else "_MLRA.txt")
        textFilePath = outputFolder + os.sep + muLayerName + ("_MUKEY.txt" if analysisType == "Mapunit (MUKEY)" else "_LRA_Assessment.txt")
        if os.path.isfile(textFilePath):
            os.remove(textFilePath)

        # record basic user inputs and settings to log file for future purposes
        logBasicSettings()

        scratchWS = setScratchWorkspace()
        arcpy.env.scratchWorkspace = scratchWS

        if scratchWS:

            # determine overlap using input and SAPOLYGON
            if not determineOverlap(muLayer):
                raise ExitError, "\n\tNo Overlap with geodata extent.  Come Back Later!"

            zoneField = getZoneField(analysisType)

            # set the zone field depending on analysis type
            if not zoneField:
                raise ExitError, "\nCould not determine Zone field"

            # ------------- Report how many polygons will be processed; exit if input is empty -------------------------
            totalPolys = int(arcpy.GetCount_management(muLayerPath).getOutput(0))
            selectedPolys = int(arcpy.GetCount_management(muLayer).getOutput(0))
            bSubset = False

            if totalPolys == 0:
                raise ExitError, "\nNo Polygons found to process.  Empty Feature layer"

            elif selectedPolys < totalPolys:
                AddMsgAndPrint("\n" + str(splitThousands(selectedPolys)) + " out of " + str(splitThousands(totalPolys)) + " polygons will be assessed",0)

            else:
                AddMsgAndPrint("\n" + str(splitThousands(totalPolys)) + " polygons will be assessed",0)

            """ if muLayer input is a feature layer then copy the features into a feature class in the scratch.gdb.
                if muLayer input is a feature class create a feature layer from it.  These will be used in case
                Tabulate Areas fails to execute.  I was continously having grid reading errors with Tabulate area
                and could not figure out why.  This is a workaround"""

            tempMuLayer = "tempMuLayer"

            if bFeatureLyr:
                muLayerExtent = arcpy.CreateScratchName(workspace=arcpy.env.scratchGDB)
                arcpy.CopyFeatures_management(muLayer, muLayerExtent)
                #muLayerPath = muLayerExtent
                arcpy.env.extent = muLayerPath
                arcpy.env.mask = muLayerPath

            else:
                if arcpy.Exists(tempMuLayer):
                    arcpy.Delete_management(tempMuLayer)
                arcpy.MakeFeatureLayer_management(muLayer,tempMuLayer)
                arcpy.env.extent = tempMuLayer
                arcpy.env.mask = tempMuLayer

            if FindField(muLayerPath,"MUNAME"): munamePresent = True
            if FindField(muLayerPath,"AREASYMBOL"): areasymPresent = True
            if FindField(muLayerPath,"MUKEY"): mukeyPresent = True

            totalAcres = float("%.1f" % (sum([row[0] for row in arcpy.da.SearchCursor(muLayer, ("SHAPE@AREA"))]) / 4046.85642))
            AddMsgAndPrint("\tTotal Acres = " + str(splitThousands(float("%.1f" %(totalAcres)))) + " ac.",0)

            """----------------------------- Start the Rapid LRA Assessment ---------------------------------------"""
            arcpy.SetProgressor("step", "Beginning Rapid LRA Assessment", 0, 13, 1)

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

            """ ---------------------  Elevation Data ------------------------------ """
            arcpy.SetProgressorLabel("Gathering Elevation Information")
            if not processElevation():
                AddMsgAndPrint("\n\tFailed to Acquire Elevation Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------  Get list of MUKEYS and Area from SSURGO raster ----------- """
            arcpy.SetProgressorLabel("Acquiring Mapunit and Component Information for Soils Reports")
            bMUKEYtable = True
            outCompJoinTable = getMUKEYandCompInfoTable()
            if not outCompJoinTable:
                AddMsgAndPrint("\n\tFailed to Acquire Mapunit and Component Information for Soils Reports",2)
                bMUKEYtable = False
            arcpy.SetProgressorPosition()
            #outCompJoinTable = r'C:\Temp\scratch.gdb\xx8'

            """ ---------------------  Soils Tax Order Data ------------------------------ """
            arcpy.SetProgressorLabel("Soils Taxonomic Order Information")
            if bMUKEYtable:
                if not getSoilsOrder(outCompJoinTable):
                    AddMsgAndPrint("\n\tFailed to Acquire Soils Taxonomic Order Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Soils Tax Great Group Data ------------------------------ """
            arcpy.SetProgressorLabel("Soils Taxonomic Great Group Information")
            if bMUKEYtable:
                if not getSoilsGreatGroup(outCompJoinTable):
                    AddMsgAndPrint("\n\tFailed to Acquire Soils Taxonomic Great Group Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Soils Temperature Regime Data ------------------------------ """
            arcpy.SetProgressorLabel("Soils Temperature Regime Information")
            if bMUKEYtable:
                if not getTempRegime(outCompJoinTable):
                    AddMsgAndPrint("\n\tFailed to Acquire Soils Temperature Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Soils Drainage Class Data ------------------------------ """
            arcpy.SetProgressorLabel("Soils Drainage Class Information")
            if bMUKEYtable:
                if not getDrainageClass(outCompJoinTable):
                    AddMsgAndPrint("\n\tFailed to Acquire Soils Drainage Class Information",2)
            arcpy.SetProgressorPosition()

            """ ---------------------  Soils Parent Material Data ------------------------------ """
            arcpy.SetProgressorLabel("Soils Parent Material Kind Information")
            if bMUKEYtable:
                if not getParentMaterial(outCompJoinTable):
                    AddMsgAndPrint("\n\tFailed to Acquire Soils Parent Material Information",2)
            arcpy.SetProgressorPosition()

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

            AddMsgAndPrint("\nThis Report is saved in the following path: " + textFilePath + "\n",0)

            arcpy.ResetProgressor()
            arcpy.SetProgressorLabel(" ")

            if zoneField == "MLRA_Temp" and arcpy.ListFields(muLayerPath, "MLRA_Temp") > 0:
                arcpy.DeleteField_management(muLayerPath, "MLRA_Temp")

            if bSubset and arcpy.Exists(muLayerExtent):
                arcpy.Delete_management(muLayerExtent)

            if not bSubset and arcpy.Exists(tempMuLayer):
                arcpy.Delete_management(tempMuLayer)

            # Add blank line for formatting
            AddMsgAndPrint("\n",0)
            arcpy.Compact_management(arcpy.env.scratchGDB)

        else:
            raise ExitError, "\nFailed to set scratchworkspace\n"

        arcpy.CheckInExtension("Spatial Analyst")

        #if arcpy.Exists(outMUKEYtable):arcpy.Delete_management(outMUKEYtable)
        #if arcpy.Exists(outCompJoinTable):arcpy.Delete_management(outCompJoinTable)

        if bFeatureLyr:
            if arcpy.Exists(muLayerExtent):arcpy.Delete_management(muLayerExtent)

    except:
        errorMsg()