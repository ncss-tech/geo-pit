#-------------------------------------------------------------------------------
# Name:        Create Extent Layer from NASIS Project
# Purpose:
#
# Author:      adolfo.diaz
#
# Created:     19/03/2014
# Copyright:   (c) adolfo.diaz 2014
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

## ===================================================================================
def GetWorkspace(ssurgoInput):
# Return the workspace of the input
    """ Maybe get rid of this or add it to the main body """

    try:
        desc = arcpy.Describe(ssurgoInput)
        thePath = os.path.dirname(desc.CatalogPath)

        desc = arcpy.Describe(thePath)

        # if path to ssurgoInput is a FD grab the GDB path
        if desc.dataType.upper() == "FEATUREDATASET":
            thePath = os.path.dirname(thePath)

        env.workspace = thePath
        return thePath

    except:
        errorMsg()

## ===================================================================================
def getNasisMukeys(theURL, theProject, ssurgoMUpoly):
    # Create a list of NASIS MUKEY values (keys) & project names (values)
    # Sometimes having problem getting first mapunit (ex. Adda in IN071)

    try:
        nasisMUKEYs = []  # List of MUKEYs pertaining to the project and parsed from the NASIS report
        mukeyMissing = [] # List of missing MUKEYs from ssurgoInput layer
        mukeyAvailable = [] # list of available MUKEYs in ssurgoInput layer

        if len(selectedProjects) > 1:
            AddMsgAndPrint("\n*************************************************************************************************************************",0)
            AddMsgAndPrint("Retrieving mapunits for '" + theProject + "' from NASIS", 0)
        else:
            AddMsgAndPrint("\nRetrieving mapunits for '" + theProject + "' from NASIS", 0)

        # replace spaces in the search string with '%20' which is the hexadecimal for a space
        theURL = theURL + '&p1='  + theProject.replace(" ","%20") # + "*"

        # Open a network object using the URL with the search string already concatenated
        theReport = urllib.urlopen(theURL)

        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project
        mukeyField = FindField(ssurgoMUpoly, "MUKEY")

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

                        # Check if MUKEY is found in ssurgoInput layer; Many projects return missing MUKEYS from SSURGO Input.
                        ''' Need to look into this error '''
                        expression = arcpy.AddFieldDelimiters(ssurgoMUpoly,mukeyField) + " = '" + theMUKEY + "'"
                        if not len([row[0] for row in arcpy.da.SearchCursor(ssurgoMUpoly, (mukeyField), where_clause=expression)]):
                            mukeyMissing.append(theMUKEY)
                        else:
                            mukeyAvailable.append(theMUKEY)

            else:
                if theValue.startswith('<div id="ReportData">BEGIN'):
                    bValidRecord = True

        # if no project record was found from NASIS return an empty list otherwise notify user; Cou
        if len(nasisMUKEYs) == 0:
            AddMsgAndPrint(" \t No matching projects found in NASIS", 2)
            return ""
        else:
            AddMsgAndPrint(" \tIdentified " + Number_Format(len(nasisMUKEYs), 0, True) + " mapunits from NASIS belonging to this project", 0)

        #All MUKEYS are missing from ssurgoInput Layer; Warn user and return False
        if len(mukeyMissing) == len(nasisMUKEYs):
            AddMsgAndPrint(" \tAll MUKEYs from this project are missing from your SSURGO MUPOLYGON layer",2)

        # More than one MUKEY is missing from ssurgoInput Layer; Simply warn the user
        if len(mukeyMissing) > 0:
            AddMsgAndPrint( "\n\t The following " + str(len(mukeyMissing)) + " MUKEYS are missing from the SSURGO MUPOLYGON layer:", 1)
            AddMsgAndPrint("\t\t" + str(mukeyMissing),1)

        del theURL, theReport, bValidRecord
        return mukeyAvailable

    except IOError:
        AddMsgAndPrint("IOError, unable to connect to NASIS server", 2)
        return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def FindField(ssurgoInput, chkField):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that name; otherwise return ""
    # Set workspace before calling FindField

    try:

        if arcpy.Exists(ssurgoInput):

            theDesc = arcpy.Describe(ssurgoInput)
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
def createShapefile(nasisMUKEYs, ssurgoInput, currentProject):

    try:
        arcpy.env.overwriteOutput = True
        ssurgoInputLayer = arcpy.ValidateTableName(currentProject)

        if arcpy.Exists(ssurgoInputLayer):
            arcpy.Delete_management(ssurgoInputLayer)

        # Create query expression from available MUKEYS in SSURGO MUPOLYGON
        bRest = False
        mukeyField = FindField(ssurgoInput, "MUKEY")
        sMUKEYS = ""

        for theMUKEY in nasisMUKEYs:

            if bRest:
                # rest of records only
                sMUKEYS = sMUKEYS + ",'" + theMUKEY + "'"
            else:
                # first record
                sMUKEYS = "('" + theMUKEY + "'"
                bRest = True

        sMUKEYS = sMUKEYS + ")"
        sQuery = '"' + mukeyField + '" IN ' + sMUKEYS
        arcpy.MakeFeatureLayer_management(ssurgoInput, ssurgoInputLayer, sQuery)  # Create feature layer from MUPOLY using the nasis MUKEYs
        projectCnt = int(arcpy.GetCount_management(ssurgoInputLayer).getOutput(0))

        spatialRef = str(arcpy.CreateSpatialReference_management("#",ssurgoInput,"#","#","#","#"))
        env.outputCoordinateSystem = spatialRef

        prjShpFile = outputFolder + os.sep + arcpy.ValidateTableName(currentProject.replace(" ","_")) + ".shp"
        if arcpy.Exists(prjShpFile):
            arcpy.Delete_management(prjShpFile)

        arcpy.CopyFeatures_management(ssurgoInputLayer,prjShpFile)
        AddMsgAndPrint("\n\tSuccessfully created '" + os.path.basename(prjShpFile) + "' shapefile",0)

        # if SSURGO mapunit table exists then add MUNAME and populate it
        muTable = theDB + os.sep + 'mapunit'
        if arcpy.Exists(muTable):

            muTableMukey = FindField(muTable,"MUKEY")
            muNameField = FindField(muTable,"MUNAME")

            if len(muTableMukey):

                # Add MUNAME field to shapefile if it doesn't exist
                if len(arcpy.ListFields(prjShpFile,"MUNAME"))>0:
                    arcpy.DeleteField_management(prjShpFile,"MUNAME")

                # Adding MUNAME to the shapefile and the layer so that they are identical
                arcpy.AddField_management(prjShpFile,"MUNAME", "TEXT", "", "", 175)
                AddMsgAndPrint("\t\tAdding Mapunit Name to shapefile:",0)

                for mukey in nasisMUKEYs:
                    # Get the muname from mapunit table for a speicific MUKEY
                    expression = arcpy.AddFieldDelimiters(muTable, muTableMukey) + " = '" + mukey + "'"
                    muName = [row[0] for row in arcpy.da.SearchCursor(muTable, (muNameField),where_clause = expression)][0]

                    # Strictly for formatting after the MUKEY
                    spaceAfter = " " * (9 - len(mukey))
                    AddMsgAndPrint("\t\t\tMUKEY: " + mukey + spaceAfter + "--  " + muName,0)

                    """ ------  Update the MUNAME in the shapefile --------- """
                    # Assign muname from above to every record in ssurgoInputLayer that has the current MUKEY
                    expression2 = arcpy.AddFieldDelimiters(prjShpFile, mukeyField) + " = '" + mukey + "'"
                    with arcpy.da.UpdateCursor(prjShpFile,("MUNAME"), where_clause = expression2) as cursor:

                        for row in cursor:
                            row[0] = muName
                            cursor.updateRow(row)

                    del expression,expression2, muName

                AddMsgAndPrint("\t\tSuccessfully populated MUNAME field",0)

            else:
                AddMsgAndPrint("\tMapunit Table is present but is missing MUKEY field",2)
                AddMsgAndPrint("\tCannot add MUNAME field",2)

        else:
            AddMsgAndPrint("\tMapunit table is not present; Unable to add MUNAME to shapefile",0)

        if len(arcpy.ListFields(prjShpFile,"Shape_Leng"))>0:
            arcpy.DeleteField_management(prjShpFile,"Shape_Leng")

        if len(arcpy.ListFields(prjShpFile,"Shape_Area"))>0:
            arcpy.DeleteField_management(prjShpFile,"Shape_Area")

        if len(arcpy.ListFields(prjShpFile,"OBJECTID"))>0:
            arcpy.DeleteField_management(prjShpFile,"OBJECTID")

##        outLayer = outputFolder + os.sep + currentProject
##
##        if arcpy.Exists(outLayer):
##            arcpy.Delete_management(outLayer)
##
##        arcpy.SaveToLayerFile_management(ssurgoInputLayer,outLayer, "ABSOLUTE")

        if arcpy.Exists(ssurgoInputLayer):
            arcpy.Delete_management(ssurgoInputLayer)

        return True

    except:
        errorMsg()

        if arcpy.Exists(ssurgoInputLayer):
            arcpy.Delete_management(ssurgoInputLayer)

        return False

## ===================================================================================
def GetFieldInfo(fc):

    # Create and return FieldMapping object containing valid project record fields. Fields
    # that are not part of project record feature class will not be appended to the project
    # record fc.

    try:

        outFields = ['AREASYMBOL','MUSYM','PROJECT_NAME','STATUS','RECERT_NEEDED']

        # Create required FieldMappings object and add the fc table as a
        # FieldMap object
        fms = arcpy.FieldMappings()
        fms.addTable(fc)

        # loop through each field in FieldMappings object
        for fm in fms.fieldMappings:

            # Field object containing the properties for the field (aliasName...)
            outFld = fm.outputField

            # Name of the field
            fldName = outFld.name

            # remove field from FieldMapping object if it is 'OID' or 'Geometry'
            # or not in dFieldInfo dictionary (SSURGO schema)
            if not fldName in outFields:
                fms.removeFieldMap(fms.findFieldMapIndex(fldName))

        for fldName in outFields:
            newFM = fms.getFieldMap(fms.findFieldMapIndex(fldName))
            fms.removeFieldMap(fms.findFieldMapIndex(fldName))
            fms.addFieldMap(newFM)

        return fms

    except:
        errorMsg()
        fms = arcpy.FieldMappings()
        return fms

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

## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcgisscripting, traceback, urllib, re, arcpy
from arcpy import env

try:
    if __name__ == '__main__':
        ssurgoInput = arcpy.GetParameterAsText(0)          # Input mapunit polygon layer; this must contain MUKEY
        searchString = arcpy.GetParameterAsText(1)         # search string for NASIS project names
        selectedProjects = arcpy.GetParameter(2)           # selected project names in a list
        outputFolder = arcpy.GetParameterAsText(3)

        searchString = searchString.replace("&","?").replace("*","%")   # Replace '&' for '?';ampersand in project named messed up URL parameter

        # Hardcode NASIS-LIMS Report Webservice
        # Runs SDJR Status Report: Returns projects with similar name
        theURL = r"https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-Projectmapunits"

        # Get the database and location of the SSURGO mapunit
        theDB = GetWorkspace(ssurgoInput) # more than likely it will return a GDB or FD path
        theDir = os.path.dirname(theDB)

        for project in selectedProjects:

            # Create dictionary of MUKEY & project name values based on the project
            nasisMUKEYs = getNasisMukeys(theURL, project, ssurgoInput)

            if len(nasisMUKEYs):

                bCheckOut = createShapefile(nasisMUKEYs, ssurgoInput, project)

                if bCheckOut:

                    try:
                        mxd = arcpy.mapping.MapDocument("CURRENT")
                        df = arcpy.mapping.ListDataFrames(mxd)[0]
                        lyr = os.path.join(outputFolder,arcpy.ValidateTableName(project.replace(" ","_"))) + ".shp"
                        newLayer = arcpy.mapping.Layer(lyr)
                        arcpy.mapping.AddLayer(df, newLayer, "TOP")
                        AddMsgAndPrint("\n\tSuccessfully added \"" + project + ".shp\" to your ArcMap Session",0)
                    except:
                        AddMsgAndPrint("\n\t" + project + ".shp file was created for future reference in the output folder",0)

        AddMsgAndPrint("\n",0)

except ExitError, e:
    AddMsgAndPrint(str(e) + "\n", 2)

except:
    errorMsg()