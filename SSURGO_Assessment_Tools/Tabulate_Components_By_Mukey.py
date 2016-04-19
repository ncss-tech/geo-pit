#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     03/08/2015
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
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def setScratchWorkspace():
    # This function will set the scratchGDB environment based on the scratchWorkspace environment.
    #
    # The scratch workspac will typically not be defined by the user but the scratchGDB will
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
        # Scratch Workspace is defined by user or default is set
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

        arcpy.Compact_management(arcpy.env.scratchGDB)

        return True

    except:
        errorMsg()
        return False

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

## ===================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ====================================== Main Body ==================================
# Import modules
import arcpy, os, traceback, sys, re
from arcpy import env

if __name__ == '__main__':

    try:
##        muLayer = arcpy.GetParameter(0) # D:\MLRA_Workspace_Stanton\MLRAprojects\layers\MLRA_102C___Moody_silty_clay_loam__0_to_2_percent_slopes.shp
##        compTable = arcpy.GetParameter(1) # D:\MLRA_Workspace_Stanton\MLRAGeodata

        muLayer = r'K:\SSURGO_FY15\SSURGO_SSR10.gdb\MUPOLYGON'
        compTable = r'K:\SSURGO_FY15\SSURGO_SSR10.gdb\component'

        # Start by getting information about the input layer
        descInput = arcpy.Describe(muLayer)
        muLayerDT = descInput.dataType.upper()

        if muLayerDT == "FEATURELAYER":
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

        if setScratchWorkspace():

            mukeyField = FindField(muLayer,"MUKEY")

            if not mukeyField:
                raise ExitError, "\nInput Polygon layer is missing necessary fields -- Cannot get MUKEY Information\n"

            numOfRecords = int(arcpy.GetCount_management(muLayer).getOutput(0))

##            outSummary = env.scratchGDB + os.sep + "outSummary"
##            arcpy.Statistics_analysis(muLayer, outSummary, [[mukeyField, "FIRST"]])

            """ ----------- Verify Component table fields ----------- """
            compMukeyField = FindField(compTable,"MUKEY")
            compNameField = FindField(compTable,"compname")
            compPctField = FindField(compTable,"comppct_r")
            majCompFlag = FindField(compTable,"majcompflag")

            compTableFields = [compMukeyField,compNameField,compPctField,majCompFlag]

            for field in compTableFields:
                if not field:
                    raise ExitError, "\nComponent Table is missing " + field + " from component table.....PLEASE COME AGAIN\n"

            """ ----------- Add the following fields to the muLayer feature class if they don't already exist----------- """
            fieldsToPopulate = [mukeyField,"Comp1_Name","Comp1_Prct","Comp2_Name","Comp2_Prct","Comp3_Name","Comp3_Prct","CompName_Merge"]

            i = 1
            for field in fieldsToPopulate:
                if not FindField(muLayer,field):
                    AddMsgAndPrint("\nAdding '" + field + "' field to " + muLayerName)

                    # Make all component percent fields short integer
                    if i == 8:  # 'Comp_merge' Field
                        arcpy.AddField_management(muLayer,field,"TEXT","","",100)
                    elif i%2 == 0:
                        arcpy.AddField_management(muLayer,field,"SHORT")
                    else:
                        arcpy.AddField_management(muLayer,field,"TEXT","","",75)
            del i

            """ ----------- Iterate through each MUKEY in muLayer and query component table to update muLayer new fields----------- """
            arcpy.SetProgressor("step", "Populating Component Names and Percentages", 0, numOfRecords, 1)
            with arcpy.da.UpdateCursor(muLayer,fieldsToPopulate) as cursor:

                for row in cursor:

                    # SQL expression to filter by major component and list results descendingly by comp percentages
                    expression = arcpy.AddFieldDelimiters(compTable,majCompFlag) + " = 'Yes' AND " + arcpy.AddFieldDelimiters(compTable,compMukeyField) + " = '" + str(row[0]) + "'"
                    sql = (None,'ORDER BY ' + compPctField.upper() + ' DESC')

                    # Search component table and create a list of tuples made of component name and component percentage
                    # [('Longpine',45),('McKelvie',30),('Tall',55)]
                    majorCompInfo = [(compRow[1],compRow[2]) for compRow in arcpy.da.SearchCursor(compTable, compTableFields, where_clause=expression,sql_clause=sql)]

                    # No major components were returned!  Set all new fields to NULL
                    if not len(majorCompInfo):

                        for i in range(1,7):
                            row[i] = None

                        cursor.updateRow(row)
                        AddMsgAndPrint("\n" + str(row[0]) + " MUKEY does not exist in Component Table",2)

                    # Major components were found; populate rows in mulayer accordingly
                    else:
                        i = 1               # will only go up to 6 b/c there are only 6 possible combinations within the majorCompInfo list
                        compMerge = ""

                        for j in range(0,3):       # take 3 tuples from majorCompInfo list
                            for k in range(0,2):   # for each item in the tuple (compname and compprct)
                                try:
                                    row[i] = majorCompInfo[j][k]

                                    # Append component Name
                                    if k == 0:
                                        if not len(compMerge):
                                            compMerge = majorCompInfo[j][k]
                                        else:
                                            compMerge = compMerge + "_" + majorCompInfo[j][k]

                                    i += 1

                                except:
                                    row[i] = None
                                    i += 1

                        row[7] = compMerge
                        del i, compMerge
                        cursor.updateRow(row)

                    arcpy.SetProgressorPosition()

##                    # Update 'CompName_Merge' field
##                    compMerge = ""
##                    for h in range(0,len(majorCompInfo)):
##                        if h == 0:
##                            compMerge = majorCompInfo[h][0]
##                        else:
##                            compMerge = compMerge + "_" + majorCompInfo[h][0]
##
##                    row[7] = compMerge
##                    cursor.updateRow(row)

                    del expression, sql, majorCompInfo
        raw_input("\nCompleted Downloading.  Enter to Exit")

    except:
        errorMsg()
        raw_input("\nError Message.  Enter to Exit")