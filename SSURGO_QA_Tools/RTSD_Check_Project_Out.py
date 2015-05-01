#-------------------------------------------------------------------------------
# Name:        module1
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
def RTSDprojectExists(prjRecordFCpath,selectedProjects):
# This function will compare the user selected projects to the existing projects
# in the project_record feature class.  If the user-selected project already exists
# it will be removed from the user-selected project list.
# If all projects are removed, there is nothing to check out, script will terminate.

    try:
        projectsToCheckout = list()
        selectedProjectsCnt = len(selectedProjects)
        AddMsgAndPrint(" \nVerifying if " + str(len(selectedProjects)) + " project(s) exist in the " + os.path.basename(prjRecordFC) + " feature class", 0)

        if arcpy.Exists(prjRecordFCpath):

            # 'PROJECT_NAME' field needs to be found
            if len(arcpy.ListFields(prjRecordFCpath, "PROJECT_NAME")) > 0:

                # Create a unique list of projects found in the project Record FC
                allProjects = [row[0] for row in arcpy.da.SearchCursor(prjRecordFCpath, ("PROJECT_NAME"))]
                uniqueProjects = set(allProjects)

                del allProjects

                # remove user-selected projects if it exists in the project record fc
                for project in selectedProjects:

                    if project in uniqueProjects:
                        AddMsgAndPrint(" \t\"" + project + "\" already exists.",1)
                    else:
                        projectsToCheckout.append(project)

                # All projects already exist in RTSD
                if len(projectsToCheckout) == 0:
                    return ""

                # Some projects already existed in RTSD
                elif len(projectsToCheckout) < selectedProjectsCnt:
                    AddMsgAndPrint(" \n\t" + str(len(projectsToCheckout)) + " out of " + str(selectedProjectsCnt) + " projects will be checked out.",1)
                    return projectsToCheckout

                # No projects exist in RTSD
                else:
                    return projectsToCheckout

            else:
                AddMsgAndPrint("\n\n \"PROJECT_NAME\" field is missing from " + os.path.basename(prjRecordFC),2)
                raise ExitError, "Cannot proceed to check-out projects!"

        else:
            ExitError("Project_Record feature class not found...EXITING")

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

        AddMsgAndPrint(" \nRetrieving mapunits for '" + theProject + "' from NASIS", 0)

        # replace spaces in the search string with '%20' which is the hexadecimal for a space
        theURL = theURL + '&p1='  + theProject.replace(" ","%20") # + "*"

        # Open a network object using the URL with the search string already concatenated
        theReport = urllib.urlopen(theURL)

        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project
        mukeyField = FindField(ssurgoMUpoly, "MUKEY")

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # removes whitespace characters

            # Iterating through the report
            if bValidRecord:
                if theValue == "END":  # written as part of the report; end of lines
                    break

                # Found a valid project record i.e. -- SDJR - MLRA 103 - Kingston silty clay loam, 1 to 3 percent slopes|400036
                else:
                    theRec = theValue.split("|")
                    #thisProject = theRec[0]
                    theMUKEY = theRec[1]

                    # Add MUKEY to the nasisMUKEY list if it doesn't already exist
                    if not theMUKEY in nasisMUKEYs:
                        nasisMUKEYs.append(theMUKEY)

                        # Check if MUKEY is found in ssurgoInput layer
                        expression = arcpy.AddFieldDelimiters(ssurgoMUpoly,mukeyField) + " = '" + theMUKEY + "'"
                        if not len([row[0] for row in arcpy.da.SearchCursor(ssurgoMUpoly, (mukeyField), where_clause=expression)]):
                            mukeyMissing.append(theMUKEY)
                        else:
                            mukeyAvailable.append(theMUKEY)

            else:
                if theValue.startswith('<div id="ReportData">BEGIN'):
                    bValidRecord = True

        # if no project record was found from NASIS return an empty list otherwise notify user
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
            AddMsgAndPrint( " \t The following " + str(len(mukeyMissing)) + " MUKEYS are missing from the SSURGO MUPOLYGON layer:", 1)
            AddMsgAndPrint(" \t\t" + str(mukeyMissing),1)

        del theURL, theReport, bValidRecord
        return mukeyAvailable

    except IOError:
        AddMsgAndPrint("IOError, unable to connect to NASIS server", 2)
        return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def appendToProjectRecord(nasisMUKEYs, prjRecordFC, regionOwnership, ssurgoInput, currentProject):

    try:
        arcpy.env.overwriteOutput = True
        rtsdDB = GetWorkspace(prjRecordFC)
        rtsdDir = os.path.dirname(rtsdDB)
        ssurgoInputLayer = currentProject
        env.workspace = rtsdDB

        # Parse Region # from the RTSD FGDB name
        try:
            userRegion = int(rtsdDB[rtsdDB.find("RTSD_Region_") + 12:rtsdDB.find("_FY")])
        except:
            userRegion = "XX"   # could not parse number; set it to XX

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

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Intersect the mapunits and the region ownership to determine if mapunits extend beyond user's region
        arcpy.FeatureToPoint_management(ssurgoInputLayer, "tempPnt", "INSIDE")
        arcpy.Intersect_analysis(["tempPnt",regionOwnership], "tempInt", "ALL")
        regionValues = set([row[0] for row in arcpy.da.SearchCursor("tempInt", ("Region"))])   #set([10, 5])

        # notify user if mapunits extend beyond user's region
        if len(regionValues) > 1:

            for region in regionValues:

                if not region == userRegion:
                    expression = arcpy.AddFieldDelimiters("tempInt", "Region") + " = " + str(region)
                    regionCount = [row[0] for row in arcpy.da.SearchCursor("tempInt", ("Region"), where_clause=expression)]
                    AddMsgAndPrint(" \tThere are " + str(Number_Format(len(regionCount), 0, True)) + " out of " + str(Number_Format(projectCnt, 0, True)) + " project mapunit polygons that extend into Region " + str(region),1)
                    del expression, regionCount

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Intersect the mapunits and the project record fc to determine if there is overlapping mapunits from a different project
        arcpy.Intersect_analysis([ssurgoInputLayer,prjRecordFC], "tempInt2", "ALL")
        prjRecValues = set([row[0] for row in arcpy.da.SearchCursor("tempInt2", ("PROJECT_NAME"))])   #set(['SDJR - MLRA 53B - Williams-Bowbells loams (Complexes > 3 percent slope)','SDJR - MLRA 53B - Wabek Complexes'])

        if len(prjRecValues) > 0:

            for project in prjRecValues:

                if not project == currentProject:
                    expression = arcpy.AddFieldDelimiters("tempInt2", "PROJECT_NAME") + " = '" + project + "'"
                    prjMuCnt = [row[0] for row in arcpy.da.SearchCursor("tempInt2", ("PROJECT_NAME"), where_clause=expression)]
                    AddMsgAndPrint(" \tThere are " + str(Number_Format(len(prjMuCnt), 0, True)) + " mapunit polygons that overlap with '" + project + "'",1)
                    del expression, prjMuCnt

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Need to write the SSURGO project mapunits to a fc in order to add fields otherwise schema locks are encountered
        # Need to write the SSURGO project mapunits to a fc in order to add fields otherwise schema locks are encountered
        tempPrjMapunits = theDB + os.sep + arcpy.ValidateTableName(currentProject.replace(" ","_"))

        if arcpy.Exists(tempPrjMapunits):
            arcpy.Delete_management(tempPrjMapunits)

        arcpy.CopyFeatures_management(ssurgoInputLayer, tempPrjMapunits)
        arcpy.AddField_management(tempPrjMapunits,"PROJECT_NAME", "TEXT", "", "", 254)
        arcpy.AddField_management(tempPrjMapunits,"STATUS", "TEXT", "", "", 20)
        arcpy.AddField_management(tempPrjMapunits,"RECERT_NEEDED", "TEXT", "", "", 5)

        arcpy.CalculateField_management(tempPrjMapunits, "PROJECT_NAME", "\"" + currentProject + "\"", "PYTHON_9.3")
        arcpy.CalculateField_management(tempPrjMapunits,"STATUS", "\"In Progress\"","PYTHON_9.3")
        arcpy.CalculateField_management(tempPrjMapunits, "RECERT_NEEDED", "\"No\"","PYTHON_9.3")

        fieldMap = GetFieldInfo(tempPrjMapunits)

        arcpy.Append_management(tempPrjMapunits, prjRecordFC, "NO_TEST",fieldMap)
        outLayer = theDir + os.sep + currentProject

        if arcpy.Exists(outLayer):
            arcpy.Delete_management(outLayer)
        #arcpy.SaveToLayerFile_management(ssurgoInputLayer,theDir + os.sep + arcpy.ValidateTableName(currentProject), "ABSOLUTE")
        arcpy.SaveToLayerFile_management(ssurgoInputLayer,theDir + os.sep + currentProject, "ABSOLUTE")

        AddMsgAndPrint(" \tSuccessfully added " + str(Number_Format(projectCnt, 0, True)) + " mapunit polygons to the ProjectRecord feature class", 0)

        del rtsdDB, rtsdDir, bRest, sMUKEYS, mukeyField, sQuery, spatialRef, regionValues

        if arcpy.Exists("tempPnt"):
            arcpy.Delete_management("tempPnt")

        if arcpy.Exists("tempInt"):
            arcpy.Delete_management("tempInt")

        if arcpy.Exists("tempInt2"):
            arcpy.Delete_management("tempInt2")

        if arcpy.Exists(tempPrjMapunits):
            arcpy.Delete_management(tempPrjMapunits)

        if arcpy.Exists(ssurgoInputLayer):
            arcpy.Delete_management(ssurgoInputLayer)

        return True

    except:
        errorMsg()

        if arcpy.Exists("tempPnt"):
            arcpy.Delete_management("tempPnt")

        if arcpy.Exists("tempInt"):
            arcpy.Delete_management("tempInt")

        if arcpy.Exists("tempInt2"):
            arcpy.Delete_management("tempInt2")

        if arcpy.Exists(tempPrjMapunits):
            arcpy.Delete_management(tempPrjMapunits)

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
        prjRecordFC = arcpy.GetParameterAsText(1)          # Project Record Feature class layer
        searchString = arcpy.GetParameterAsText(2)         # search string for NASIS project names
        selectedProjects = arcpy.GetParameter(3)           # selected project names in a list

        regionOwnership = os.path.join(os.path.join(os.path.dirname(sys.argv[0]),"SSURGO_Soil_Survey_Area.gdb"),"Region_ownership_WGS84")

        if not arcpy.Exists(regionOwnership):
            raise ExitError, "Region ownership layer was not found under " + os.path.dirname(sys.argv[0])

        searchString = searchString.replace("&","?")   # Replace '&' for '?';ampersand in project named messed up URL parameter

        # Hardcode NASIS-LIMS Report Webservice
        # Runs SDJR Status Report: Returns projects with similar name
        theURL = r"https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-Projectmapunits"

        # Get the database and location of the SSURGO mapunit
        theDB = GetWorkspace(ssurgoInput) # more than likely it will return a GDB or FD path
        theDir = os.path.dirname(theDB)

        prjRecordFCpath = arcpy.Describe(prjRecordFC).CatalogPath
        verifiedProjects = RTSDprojectExists(prjRecordFCpath, selectedProjects) #

        if verifiedProjects == "":
            raise ExitError, " \n\tAll selected projects are already checked out!"

        for project in verifiedProjects:

            # Create dictionary of MUKEY & project name values based on the project
            nasisMUKEYs = getNasisMukeys(theURL, project, ssurgoInput)

            if len(nasisMUKEYs):

                bCheckOut = appendToProjectRecord(nasisMUKEYs, prjRecordFC, regionOwnership, ssurgoInput, project)

                if bCheckOut:
                    try:
                        mxd = arcpy.mapping.MapDocument("CURRENT")
                        df = arcpy.mapping.ListDataFrames(mxd)[0]
                        lyr = os.path.join(theDir,project) + ".lyr"
                        newLayer = arcpy.mapping.Layer(lyr)
                        arcpy.mapping.AddLayer(df, newLayer, "TOP")
                    except:
                        AddMsgAndPrint(project + ".lyr file was created for reference",0)

        AddMsgAndPrint(" \n",0)

except ExitError, e:
    AddMsgAndPrint(str(e) + " \n", 2)

except:
    errorMsg()