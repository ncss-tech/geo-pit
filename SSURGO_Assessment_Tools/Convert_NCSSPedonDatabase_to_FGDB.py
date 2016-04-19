#-------------------------------------------------------------------------------
# Name:        Convert NCSS Pedon Database to FGDB
# Purpose:
#
# Author:      Adolfo.Diaz
#              Region 10 GIS Specialist
#              608.662.4422 ext. 216
#              adolfo.diaz@wi.usda.gov
#
# Created:     1/8/2015
# Copyright:   (c) Adolfo.Diaz 2015
# Licence:     <your licence>
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
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = "\t" + tbinfo + "\n\t" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

## ===============================================================================================================
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
    # This Function will create a new File Geodatabase using a pre-established XML workspace
    # schema.  All Tables will be empty and should correspond to that of the access database.
    # Relationships will also be pre-established.
    # Return false if XML workspace document is missing OR an existing FGDB with the user-defined
    # name already exists and cannot be deleted OR an unhandled error is encountered.
    # Return the path to the new Pedon File Geodatabase if everything executes correctly.

    try:
        AddMsgAndPrint("\nCreating New Pedon File Geodatabase",0)

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "Pedons_XMLWorkspace.xml"

        # Return false if xml file is not found and delete targetGDB
        if not arcpy.Exists(pedonXML):
            AddMsgAndPrint("\t" + os.path.basename(pedonXML) + "Workspace document was not found!",2)
            return ""

        tempFGDB = os.path.join(outputFolder,"tempPedon.gdb")

        if arcpy.Exists(tempFGDB):
            arcpy.Delete_management(tempFGDB)

        # Create empty temp File Geodatabae
        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(tempFGDB))[0])

        # output path of the new pedon FGDB to be created
        newPedonFGDB = os.path.join(outputFolder,outputName) + ".gdb"

        if arcpy.Exists(newPedonFGDB):
            try:
                AddMsgAndPrint("\t" + outputName + ".gdb already exists. Deleting and re-creating FGDB",1)
                arcpy.Delete_management(newPedonFGDB)

            except:
                AddMsgAndPrint("\t" + outputName + ".gdb already exists. Failed to delete",2)
                return ""

        # set the pedon schema on the newly created temp Pedon FGDB
        AddMsgAndPrint("\tImporting NCSS Pedon Schema into " + outputName + ".gdb")
        arcpy.ImportXMLWorkspaceDocument_management(tempFGDB, pedonXML, "SCHEMA_ONLY", "DEFAULTS")

        # Rename the tmepPedon to user-defined name
        arcpy.Rename_management(tempFGDB,outputName)
        arcpy.RefreshCatalog(outputFolder)

        AddMsgAndPrint("\tSuccessfully created: " + outputName + ".gdb")

        del pedonXML, tempFGDB
        return newPedonFGDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return ""

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return ""

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

## ================================================================================================================
def createPedonPoints(accessDB,pedonFGDB):
# This function will use an insert cursor to digitize pedon points that have XY coordinates and
# populate all other fields found in the NCSS site Location table.  If pedons do not have XY coordinates a
# default Lat/Long value of 90.0,90.0 will be given to those points in order to add them to the table.
# Total number of imported pedons into the NCSS site location table will be reported as well as the
# number of pedons with no coordinates.  All pedons will be digitized in WGS84.

    try:

        AddMsgAndPrint("\nCreating Pedon Points from the NCSS Site Location Table",0)

        # Make sure the NCSS_Site_Location table is present in the pedon access database
        arcpy.env.workspace = accessDB
        if not arcpy.ListTables("NCSS_Site_Location") > 0:
            AddMsgAndPrint(os.path.basename(accessDB) + " Pedon Database is missing the 'NCSS_Site_Location' Table.  Cannot Proceed with digitizing points",2)
            return False

        # Absolute path of the "NCSS_Site_Location" site table within the acces database
        siteTable = accessDB + os.sep + "NCSS_Site_Location"

        # Make sure Lat and Long fields are present in the pedon access database
        latField = FindField(siteTable,"latitude_decimal_degrees")
        longField = FindField(siteTable,"longitude_decimal_degrees")

        if not latField or not longField:
            AddMsgAndPrint(os.path.basename(accessDB) + " Pedon Database is missing the Lat and Long fields.  Cannot Proceed with digitizing points",2)
            return False

        # Get a total count of the # of records in the NCSS Site Location table in access database
        #numOfRecords = len([row[0] for row in arcpy.da.SearchCursor(siteTable,"*")])
        numOfRecords = int(arcpy.GetCount_management(siteTable).getOutput(0))

        # Make sure the NCSS_Site_Location point feature class is present in the new empty pedon FGDB
        # If this is missing XML workspace is not cooperating.  Someone is messing with my XML workspace!
        arcpy.env.workspace = pedonFGDB
        if not arcpy.ListFeatureClasses("NCSS_Site_Location","Point") > 0:
            AddMsgAndPrint(os.path.basename(pedonFGDB) + " Pedon Database is missing the 'NCSS_Site_Location' Point Feature Class.  Cannot Proceed with digitizing points",2)
            return False

        # Absolute path to the NCSS Site Location table in the new FGDB
        siteTableFC = pedonFGDB + os.sep + "NCSS_Site_Location"

        # ------------------------------------------------------------------------------------------------
        # List of fields in the NCSS_Site_Location Feature Class in the File Geodatabase (exclude ObjectID and Shape)
        # This list will be past to an insert cursor with a lat,long value at the the end to correspond with 'SHAPE@XY'
        siteFCFields = []
        for field in arcpy.ListFields(siteTableFC):
            if not field.type == "OID" and not field.type == "Geometry":
                siteFCFields.append(field.name)
        siteFCFields.append('SHAPE@XY')

        # ------------------------------------------------------------------------------------------------
        # List of fields in the NCSS_Site_Location table in the access pedon
        # Exclude 'site_key' which is set to an indexed field in access
        siteTableFields = [field.name for field in arcpy.ListFields(siteTable)]

        # get the list index position for the lat and long fields. Add 1 to compensate for zero-based
        latFieldIndex = siteTableFields.index('latitude_decimal_degrees')
        longFieldIndex = siteTableFields.index('longitude_decimal_degrees')
        siteKeyIndex = siteTableFields.index('site_key')

        """----------------------------- Start Adding pedon points and records---------------------------------------"""
        arcpy.SetProgressor("step", "Converting Pedon Latitude-Longitude to Points", 0, numOfRecords, 1)
        arcpy.SetProgressorLabel("Converting Pedon Latitude-Longitude to Points")

        # Initiate insert cursor to digitized
        iCursor = arcpy.da.InsertCursor(siteTableFC,siteFCFields)

        # Iterate through the acess NCSS site location table records and digitize a point based on
        # the lat and long field and copy the other record info.
        with arcpy.da.SearchCursor(siteTable,siteTableFields) as cursor:
            for row in cursor:

                newRowValue = []        # list that will contain the record info
                latFieldValue = 90.0    # set Lat field to 90 degrees; updated below if lat field value exists
                longFieldValue = 0.00   # set Long field to 90 degrees; updated below if lat field value exists

                # put all of the values for this record in a list
                for i in range(0,len(siteTableFields)):

                    # set lat (Y) record has latitude populated; else set default
                    #if i == latFieldIndex and row[i] > -90:
                    if i == latFieldIndex:
                        if not row[i] is None:
                            latFieldValue = row[i]
                        else:
                            newRowValue.append(latFieldValue) # populate lat field with default above
                            continue

                    # set long (X) if record has longitude populated;else set default
                    if i == longFieldIndex:
                        if not row[i] is None:
                            longFieldValue = row[i]
                        else:
                            newRowValue.append(longFieldValue) # populate long field with default above
                            continue

                    # Add all of the record info to this list (making a copy of the record)
                    newRowValue.append(row[i])

                # append 3 empty records to account for the pedonName, pedonClass, and pedonType
                # and append (lat,long) to the end of the newRowValue list to correspond with SHAPE@XY

                newRowValue.append(None)
                newRowValue.append(None)
                newRowValue.append(None)
                newRowValue.append((longFieldValue,latFieldValue))

                iCursor.insertRow(newRowValue)

                del newRowValue, latFieldValue, longFieldValue

                arcpy.SetProgressorPosition() # Update the progressor position

            del iCursor

        arcpy.ResetProgressor()  # Resets the progressor back to is initial state
        arcpy.SetProgressorLabel(" ")

        # Get a total count of the # of records in the NCSS Site Location table in access database
        numOfRecordsInserted = int(arcpy.GetCount_management(siteTableFC).getOutput(0))

        if numOfRecords == numOfRecordsInserted:
            AddMsgAndPrint("\tSuccessfully Imported " + str(splitThousands(numOfRecordsInserted)) + " Pedons into " + os.path.basename(pedonFGDB),0)
        else:
            AddMsgAndPrint("\tOnly Imported " + str(splitThousands(numOfRecords - numOfRecordsInserted)) + " out of " + str(splitThousands(numOfRecords)) + " Pedons",1)

        latExpression = arcpy.AddFieldDelimiters(siteTableFC,latField) + " = 90.0 AND " + arcpy.AddFieldDelimiters(siteTableFC,longField) + " = 0.00"
        santaPedons = [row[0] for row in arcpy.da.SearchCursor(siteTableFC, (latField), where_clause = latExpression)]

        if len(santaPedons) > 0:
            AddMsgAndPrint("\t\tThere are " + str(splitThousands(len(santaPedons))) + " pedons that have NO coordinates!",1)
            AddMsgAndPrint("\t\tWARNING: A default value of Lat: 90.0, Long: 0.00 were given to these pedons",1)

        del siteTable, latField, longField, numOfRecords, siteTableFC, siteTableFields, latFieldIndex, longFieldIndex

        return True

    except:
        errorMsg()
        return False

## ================================================================================================================
def importTabularData(accessDB,pedonFGDB):
# This function will append the records from all access database tables into the new
# file geodatabase.  Uses the append function to add records; Experimented with the copyrows
# fuction but I get warnings since the target table already exists.
# Reports the number of records added from each table.
# Return True if tables are appended correctly; otherwise False

    try:

        AddMsgAndPrint("\nImporting Tabular Data",0)

        # Set workspace to the access database to read all the tables
        env.workspace = accessDB

        # Use ListTables to generate a list of tables from the workspace above;sort it
        tableList = arcpy.ListTables()
        tableList.sort()

        maxTableChar = max([len(table) for table in tableList])

        # set progressor object which allows progress information to be passed for every complete table
        arcpy.SetProgressor("step", "Importing Tabular Data into " + os.path.basename(pedonFGDB), 0, len(tableList), 1)
        sleep(2)

        for accessTable in tableList:

            # Skip the NCSS Site Location table since it is a feature class
            if accessTable == "NCSS_Site_Location":
                arcpy.SetProgressorPosition()
                continue

            arcpy.SetProgressorLabel("Importing Records into: " + accessTable.replace("_"," ") + " Table")

            # Full path to the access Table
            accessTablePath = os.path.join(env.workspace,accessTable)

            # Determine the new output feature class path and name
            targetTable = pedonFGDB + os.sep + accessTable

            # Check if access Table exists.  Skip if it doesn't
            if not arcpy.Exists(targetTable):
                AddMsgAndPrint("\t--> " + accessTable + " table does NOT exist in " + os.path.basename(pedonFGDB) + ".....Skipping",2)
                arcpy.SetProgressorPosition()
                continue

            # Next 4 lines are strictly for printing formatting to figure out the spacing between.
            # the full table name and the number of records added.
            # Played around with numbers until I liked the formatting.
            #theTabLength = 58 - len(accessTable)
            theTabLength = (maxTableChar + 3) - len(accessTable)
            theTab = " " * theTabLength

            numOfRecords = int(arcpy.GetCount_management(accessTable).getOutput(0))

            # Table contains no records; Report no records were added
            if not numOfRecords > 0:
                AddMsgAndPrint("\t--> " + accessTable.replace("_", " ") + theTab + "Records Added: 0",0)

            # Append access table records to new table
            else:
                try:
                    # Use 'CopyRows' function on the Data_Elements table since 'Append' fails on this table
                    # b/c of the 'order' field present.  It is a reserved word and it gets renamed to 'order_'
                    # causing a mismatch between the 2 tables.
                    if accessTable == "Data_Elements":
                        arcpy.CopyRows_management(accessTablePath,targetTable)
                    else:
                        arcpy.Append_management(accessTablePath,targetTable,"TEST")
                    AddMsgAndPrint("\t--> " + accessTable.replace("_", " ") + theTab + " Records Added: " + str(splitThousands(numOfRecords)),0)

                except:
                    AddMsgAndPrint("\t" + accessTable + " --- " + arcpy.GetMessages(2),2)
                    arcpy.SetProgressorPosition()
                    continue

            del accessTablePath,targetTable,theTabLength,theTab,numOfRecords

            arcpy.SetProgressorPosition()

        # Resets the progressor back to is initial state
        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel(" ")

        del tableList

        return True

    except:
        errorMsg()
        return False

## ================================================================================================================
def addPedonName(pedonFGDB):
# This function will add 3 new fields to the NCSS Site Location table.
# Pedon Name, Pedon Class Type and Pedon Name Type.  Pedon Name will be the
# correlated_as name, if available.  If not available, the sampled_as name will
# be passed over. If the sampled_as name is not available the field will remain
# empty.  Pedon Class Type will contain the value 'correlated as' vs 'sampled as'
# depending on how the pedon name was obtained.  Pedon Name Type will contain the
# values from the 'samp_class_typ' or 'corr_class_typ' field from the NCSS Pedon Taxonomy
# table, depending on how pedon_name was obtained.

    try:

        AddMsgAndPrint("\nPopulating fields in the 'NCSS Site Location' feature class",0)

        """ --------------------- Get NCSS Pedon Taxonomy Info ------------------------------ """

        taxTable = pedonFGDB + os.sep + 'NCSS_Pedon_Taxonomy'

        if not arcpy.Exists(taxTable):
            AddMsgAndPrint("\t'NCSS Pedon Taxonomy' table was not found in the " + os.path.basename(pedonFGDB) + " database",2)
            return False

        siteKeyTaxTableField = FindField(taxTable,"site_key")
        sampleNameField = FindField(taxTable,"samp_name")
        correlatedNameField = FindField(taxTable,"corr_name")
        sampClassType = FindField(taxTable,"samp_class_type")
        corrClassType = FindField(taxTable,"corr_class_type")

        taxTableFields = [siteKeyTaxTableField,correlatedNameField,sampleNameField,corrClassType,sampClassType]
        for field in taxTableFields:
            if not FindField(taxTable,field):
                AddMsgAndPrint("\tNCSS Pedon Taxonomy table is missing necessary fields -- Cannot get Pedon Name\n",2)
                return False

        """ --------------------- Get NCSS Site Location Info ------------------------------ """
        pedonFC = pedonFGDB + os.sep + 'NCSS_Site_Location'

        if not arcpy.Exists(pedonFC):
            AddMsgAndPrint("\t'NCSS Site Location' feature class was not found in the " + os.path.basename(pedonFGDB) + " database",2)
            return False

        siteKeyPedonField = FindField(pedonFC,"site_key")
        pedonNameField = FindField(pedonFC,"PedonName")            # will contain the values from the 'samp_name' or 'corr_name' field
        pedonNameTypeField = FindField(pedonFC,"PedonNameType")    # will contain the values from the 'samp_class_typ' or 'corr_class_typ'
        pedonClassTypeField = FindField(pedonFC,"PedonClassType")  # will contain 'correlated as' vs 'sampled as'

        if not siteKeyPedonField or not pedonNameField or not pedonNameTypeField or not pedonClassTypeField:
            AddMsgAndPrint("\tNCSS Site Location Feature class is missing necessary fields -- Cannot get Pedon Name\n",2)
            return False

##        # Make a feature layer out of the site location fc; Join Purposes
##        pedonFCLayer = "pedonFC_lyr"
##        if arcpy.Exists(pedonFCLayer):
##            arcpy.Delete_management(pedonFCLayer)
##
##        AddMsgAndPrint("\tCreating Layer to Join")
##        arcpy.MakeFeatureLayer_management(pedonFC,pedonFCLayer)
##
##        # Make a Table view out of NCSS Pedon Taxonomy Table; Join Purposes
##        taxTableLayer ="taxTable_lyr"
##        if arcpy.Exists(taxTableLayer):
##            arcpy.Delete_management(taxTableLayer)
##
##        AddMsgAndPrint("\tCreating table to Join")
##        fields = arcpy.ListFields(taxTable)
##        fieldinfo = arcpy.FieldInfo()
##
##        for field in fields:
##            if field.name.upper() in ["SITE_KEY","SAMP_NAME","CORR_NAME","SAMP_CLASS_TYPE","CORR_CLASS_TYPE"]:
##                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
##            else:
##                fieldinfo.addField(field.name, field.name, "HIDDEN", "")
##
##        arcpy.MakeTableView_management(taxTable,taxTableLayer,"","",fieldinfo)
##
##        del fields, fieldinfo
##
##        # Join the NCSS_Pedon_Taxonomy to the NCSS_Site_Location feature class
##        arcpy.AddJoin_management(pedonFCLayer,siteKeyPedonField,taxTableLayer,siteKeyTaxTableField,"KEEP_COMMON")
##        arcpy.CopyRows_management(pedonFCLayer,pedonFGDB + os.sep + "JOIN_junk")

        AddMsgAndPrint("\tJoining to 'NCSS Pedon Taxonomy' Table",0)
        arcpy.SetProgressorLabel("Joining to 'NCSS Pedon Taxonomy' Table")
        arcpy.JoinField_management(pedonFC, siteKeyPedonField, taxTable, siteKeyTaxTableField, taxTableFields)

        # update the field names after the join b/c the field names change after a join
        pedonName = [f.name for f in arcpy.ListFields(pedonFC,"PedonName")][0]
        pedonNameType = [f.name for f in arcpy.ListFields(pedonFC,"PedonNameType")][0]
        pedonClassType = [f.name for f in arcpy.ListFields(pedonFC,"PedonClassType")][0]
        sampleName = [f.name for f in arcpy.ListFields(pedonFC,"samp_name")][0]
        sampleClassType = [f.name for f in arcpy.ListFields(pedonFC,"samp_class_type")][0]
        correlatedName = [f.name for f in arcpy.ListFields(pedonFC,"corr_name")][0]
        correlatedClassType = [f.name for f in arcpy.ListFields(pedonFC,"corr_class_type")][0]

        arcpy.SetProgressor("step", "Updating New fields in NCSS_Site_Location feature class", 0, int(arcpy.GetCount_management(pedonFC).getOutput(0)), 1)
        AddMsgAndPrint("\nUpdating New fields in NCSS_Site_Location feature class")

        fieldsToPopulate = [pedonName,pedonNameType,pedonClassType,sampleName,sampleClassType,correlatedName,correlatedClassType,"site_key"]
        with arcpy.da.UpdateCursor(pedonFC,fieldsToPopulate) as cursor:

            for row in cursor:

                """ --- Calculate the Pedon Name [0], Pedon Name Type [1], Pedon Class Type [2] ---"""
                if not row[5] is None:
                    row[0] = row[5]
                    row[1] = row[5]
                    row[2] = row[6]

                elif not row[3] is None:
                    row[0] = row[3]
                    row[1] = row[3]
                    row[2] = row[4]
                else:
                    row[0] = None
                    row[1] = None
                    row[2] = None

                try:
                    arcpy.SetProgressorPosition()
                    cursor.updateRow(row)
                except:
                    errorMsg()
                    AddMsgAndPrint("\n\tFailed to update site key: " + str(row[7]),1)

##        arcpy.SetProgressor("step", "Adding Pedon Name to NCSS_Site_Location feature class", 0, 4, 1)
##        arcpy.SetProgressorLabel("Adding Pedon Name to NCSS_Site_Location feature class")
##        AddMsgAndPrint("Starting the calc process1")
##
##        """ -----------------------------------    Calculate the Pedon Name  ---------------------------"""
##        arcpy.SetProgressorLabel("Adding Pedon Name from NCSS_Pedon_Taxonomy Table")
##        getPedonNameExpression = "getPedonName(!" + sampleNameJoinField + "!, !" + correlatedNameJoineField + "!)"
##
##        codeblock = """def getPedonName(sampleName,correlatedName):
##            if not correlatedName is None:
##                return correlatedName.upper()
##            elif not sampleName is None:
##                return sampleName.upper()
##            else:
##                return None"""
##
##        arcpy.CalculateField_management(pedonFCLayer,pedonNameJoinField,getPedonNameExpression,"PYTHON_9.3", codeblock)
##        del getPedonNameExpression, codeblock
##
##        AddMsgAndPrint("\tSuccessfully populated 'PedonName' field in the NCSS_Site_Location Table")
##        arcpy.SetProgressorPosition()
##        AddMsgAndPrint("Starting the calc process2")
##
##        """ -----------------------------------    Calculate the Pedon Name Type  ---------------------------"""
##        arcpy.SetProgressorLabel("Determining Pedon Name Type: 'correlated_as' or 'sampled_as'")
##        getPedonNameTypeExpression = "getPedonNameType(!" + sampleNameJoinField + "!, !" + correlatedNameJoineField + "!)"
##
##        codeblock = """def getPedonNameType(sampleName,correlatedName):
##            if not correlatedName is None:
##                return "correlated_as"
##            elif not sampleName is None:
##                return "sampled_as"
##            else:
##                return None"""
##
##        arcpy.CalculateField_management(pedonFCLayer,pedonNameTypeJoinField,getPedonNameTypeExpression,"PYTHON_9.3", codeblock)
##        del getPedonNameTypeExpression,codeblock
##        AddMsgAndPrint("\tSuccessfully populated 'PedonNameType' field in the NCSS_Site_Location Table")
##        arcpy.SetProgressorPosition()
##        AddMsgAndPrint("Starting the calc process3")
##
##        """ -----------------------------------    Calculate the Pedon Class Type  ---------------------------"""
##        arcpy.SetProgressorLabel("Determining Pedon Class Type (series, tax adjunct, taxon above family....etc")
##        getClassTypeExpression = "getClassType(!" + sampleNameJoinField + "!, !" + correlatedNameJoineField + "!, !" + sampleClassTypeJoinField + "!, !" + correlatedClassTypeJoinField + "!)"
##
##        codeblock = """def getClassType(sampleName,correlatedName,sampType,corrType):
##            if not correlatedName is None:
##                return corrType
##            elif not sampleName is None:
##                return sampType
##            else:
##                return None"""
##
##        arcpy.CalculateField_management(pedonFCLayer,pedonClassTypeJoinField,getClassTypeExpression,"PYTHON_9.3", codeblock)
##        AddMsgAndPrint("\tSuccessfully populated 'PedonClassType' field in the NCSS_Site_Location Table")
##        del getClassTypeExpression,codeblock
##
##        # Remove join between NCSS_Pedon_Taxonomy and the NCSS_Site_Location feature class
##        arcpy.RemoveJoin_management(pedonFCLayer)
##
##        updatedPedonFC = pedonFC + "2"
##        if arcpy.Exists(updatedPedonFC):
##            arcpy.Delete_management(updatedPedonFC)
##
##        # Need to copy the layer features to another feature class
##        arcpy.CopyFeatures_management(pedonFCLayer,updatedPedonFC)
##
##        if arcpy.Exists(pedonFC):
##            arcpy.Delete_management(pedonFC)
##
##        if arcpy.Exists(pedonFCLayer):
##            arcpy.Delete_management(pedonFCLayer)
##
##        if arcpy.Exists(taxTableLayer):
##            arcpy.Delete_management(taxTableLayer)
##
##        env.workspace = pedonFGDB
##        arcpy.Rename_management(os.path.basename(updatedPedonFC),os.path.basename(pedonFC))

        for field in taxTableFields:
            if arcpy.ListFields(pedonFC, field) > 0 and not field == 'site_key':
                arcpy.DeleteField_management(pedonFC,field)

        if arcpy.ListFields(pedonFC, "site_key_1") > 0:
            arcpy.DeleteField_management(pedonFC,"site_key_1")

##        # Create Relationship between NCSS_Site_Location table and NCSS_PedonTaxonomy table
##        arcpy.SetProgressorLabel("Creating Relationship between NCSS_Site_Location table and NCSS_PedonTaxonomy table")
##
##        if not arcpy.Exists(pedonFGDB + os.sep + "xNCSSSiteLocation_NCSSPedonTaxonomy"):
##            arcpy.CreateRelationshipClass_management(pedonFC, taxTable, "xNCSSSiteLocation_NCSSPedonTaxonomy", "SIMPLE", "> NCSS Pedon Taxonomy", "< NCSS Site Location", "NONE", "ONE_TO_ONE", "NONE", siteKeyPedonField, siteKeyTaxTableField, "","")
##            AddMsgAndPrint("\nSuccessfully created relationship class between NCSS_Site_Location table and NCSS_PedonTaxonomy table", 0)

        arcpy.SetProgressorPosition()
        arcpy.ResetProgressor()

        del taxTable, siteKeyTaxTableField,sampleNameField,correlatedNameField,sampClassType,corrClassType,taxTableFields,pedonFC
        del siteKeyPedonField,pedonNameField,pedonClassTypeField,pedonNameTypeField,pedonName,pedonNameType
        del pedonClassType,sampleName,sampleClassType,correlatedName,correlatedClassType

        return True

    except:
        errorMsg()
        return False
## ====================================== Main Body ===========================================================
# Import modules
import arcpy, sys, string, os, re, traceback, time
from time import sleep
from arcpy import env

if __name__ == '__main__':

    accessDB = arcpy.GetParameterAsText(0)     # Input pedon access database to convert
    outputName = arcpy.GetParameterAsText(1)   # User defined output name

##    accessDB = r'N:\flex\NCSS_pedons\NCSS_Soil_Characterization_Database_6_30_2015.mdb'    # Input pedon access database to convert
##    outputName = "Junk"   # User defined output name
##    pedonFGDB = r'N:\flex\NCSS_pedons\test.gdb'

    # parent folder of the input pedon access database
    outputFolder = os.path.dirname(accessDB)

    # ---------------------------------------------------------------------------------- Create Empty Pedon Database
    pedonFGDB = createPedonFGDB()

    if pedonFGDB == "":
        raise ExitError, " \n Failed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!"

    if not createPedonPoints(accessDB,pedonFGDB):
        raise ExitError, " \n Failed to create points from Lat/Long.  Error in createPedonPoints() function. Exiting!"

    if not importTabularData(accessDB,pedonFGDB):
        raise ExitError, " \n Failed to import tabular data from " + os.path.basename(accessDB) + " to " + os.path.basename(pedonFGDB) + ". Exiting!"

    if not addPedonName(pedonFGDB):
        raise ExitError, " \n Failed to add data from the NCSS Pedon Taxonomy table to NCSS Site Location Feature class. Exiting!"

    AddMsgAndPrint("\n\n",0)
    del accessDB, outputName, outputFolder, pedonFGDB

