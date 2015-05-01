# ---------------------------------------------------------------------------
# QA_CommonLines.py
# Created on: May 20, 2013
#
# Steve Peaslee, National Soil Survey Center

# Identifies adjacent polygons with the same, specified attribute
# If common lines are found, they will be copied to a new featureclass and added to the
# ArcMap TOC.
#
# ArcGIS 10.1 compatible

# 06-03-2013. Fixed handling for some coverages, depending upon attribute fields
# 06-04-2013. Added XYTolerance setting to allow snapping of overlapping survey boundaries
#
# 06-18-2013. Changed script to use the featurelayer and to use AREASYMBOL. Quick-and-dirty test!
#
# 08-02-2013. Adolfo is still having problems with performance and a tendancy to fail after 18-20 hours
#             when run against Region 10 geodatabase in 64 bit background.
#             I have seen occasions when the cursor fails because of a lock. I think this is on the scratchGDB version.
#             May try moving scratchGDB to a 'Geodatabase' folder to avoid antivirus.
#
# 08-05-2013. Changed processing mode to use a list of AREASYMBOL values. This uses less resources.
#
# 10-25-2013
#
# 10-31-2013

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + " \n"
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def PrintMsg(msg, severity=0):
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
                arcpy.AddError(" \n" + string)

    except:
        pass

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
        #PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return "???"

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

        return True

    except:
        errorMsg()
        return False

## ===================================================================================

# Import system modules
import sys, string, os, traceback, locale, tempfile, time

# Create the Geoprocessor object
import arcpy
from arcpy import env
from time import sleep

try:
    # Check out ArcInfo license for PolygonToLine
    arcpy.SetProduct("ArcInfo")
    arcpy.OverwriteOutput = True

    # Script arguments...
    inLayer = arcpy.GetParameter(0)                # required input soils layer, need to make sure it has MUKEY field
    inField1 = arcpy.GetParameterAsText(1)         # primary attribute field whose values will be compared
    inField2 = arcpy.GetParameterAsText(2)         # optional secondary attribute field whose values will be compared
    asList = arcpy.GetParameter(3)                 # list of AREASYMBOL values to be processed
    #layerName = arcpy.GetParameterAsText(4)       # output featurelayer containing common soil lines (not required)

    xyTol = 0

    # Need to remove any joins before converting the polygons to polylines
    try:
        arcpy.RemoveJoin_management(inLayer)

    except:
        pass

    # Then get the unqualified field name
    inField1 = arcpy.ParseFieldName(inField1).split(",")[3].strip()

    if inField2 != "":
        inField2 = arcpy.ParseFieldName(inField2).split(",")[3].strip()
    #PrintMsg(" \ninField1 parsed = " + inField1, 0)

    # Start by getting information about the input layer
    descInput = arcpy.Describe(inLayer)
    inputDT = descInput.dataType.upper()

    if inputDT == "FEATURELAYER":
        inputName = descInput.Name
        inputFC = descInput.FeatureClass.catalogPath

    elif inputDT in ("FEATURECLASS", "SHAPEFILE"):
        inputName = descInput.Name
        inputFC = descInput.catalogPath

    else:
        raise MyError,"Invalid input data type (" + inputDT + ")"

    # Get workspace information
    theWorkspace = os.path.dirname(inputFC)
    descW = arcpy.Describe(theWorkspace)
    wkDT = descW.DataType.upper()
    arcpy.env.addOutputsToMap = False

    if wkDT == "FEATUREDATASET":
        theWorkspace = os.path.dirname(theWorkspace)

    # Setting workspace to that of the input soils layer
    env.workspace = theWorkspace
    env.overwriteOutput = True

    # Set scratchworkspace and then proceed with processing
    if setScratchWorkspace():

        # get the first input field object
        chkFields = arcpy.ListFields(inputFC)

        for fld in chkFields:
            fldLength = 0

            if fld.name.upper() == inField1.upper():
                fld1Name = fld.name
                fldLength = fld.length
                #PrintMsg("Getting length for " + fld1Name + " length: " + str(fldLength), 0)

        # get the optional second input field object
        if inField2 != "":
            for fld in chkFields:

                if fld.name.upper() == inField2.upper():
                    fld2Name = fld.name
                    fldLength += fld.length
                    #PrintMsg("Getting total length for both fields " + fld2Name + ", " + fld1Name + " length: " + str(fldLength), 0)

        else:
            fld2Name = ""

        if len(asList) == 0:
            asList = ["*"]
            PrintMsg(" \nProcessing all survey areas contained in the input layer...", 0)

        else:
            PrintMsg(" \nProcessing " + Number_Format(len(asList), 0, True) + " survey areas...", 0)

        iVals = len(asList)

        # set name and location for temporary output features
        comFC = os.path.join(env.scratchGDB, "xxComLines")      # temporary featureclass containing all lines

        # set name and location for permanent QA featureclass
        comFC2 = os.path.join(theWorkspace, "QA_CommonLines")   # permanent output featureclass containing common-lines

        # set final output to shapefile if input is shapefile and make the new field name compatible with the database type
        #
        # need to test shapefile option some more
        #
        if inputFC.endswith(".shp"):
            comFC2 = comFC2 + ".shp"
            fld1Name = fld1Name[0:10]

        if arcpy.Exists(comFC2):
            # Having problems removing this when two successive runs are made with this tool.
            #
            try:
                sleep(3)

                if arcpy.TestSchemaLock(comFC2):
                    arcpy.Delete_management(comFC2)

                else:
                    raise MyError, "Unable to overwrite existing featureclass '" + comFC2+ "' (schemalock)"

            except:
                errorMsg()
                raise MyError, "Unable to overwrite existing featureclass '" + comFC2

        if arcpy.Exists(comFC):
            # Having problems removing this when two successive runs are made with this tool.
            #
            try:
                sleep()

                if arcpy.TestSchemaLock(comFC):
                    arcpy.Delete_management(comFC)

                else:
                    raise MyError, "Unable to overwrite existing featureclass '" + comFC + "' (schemalock)"

            except:
                raise MyError, "Unable to overwrite existing featureclass '" + comFC

        # set output map layer name
        comFL = "QA Common Lines  (" + fld1Name.title() + ")"                                  # common-line featurelayer added to ArcMap

        # Use a temporary featureclass to make selections against
        selLayer = "SelectLayer"

        # Counter for total number of common-line problems
        iCL = 0

        # Initialize counters and lists
        #
        iCnt = 0
        missList = list()
        comList = list()

        # Iterate through the list of soil survey areas by AREASYMBOL
        #

        for AS in asList:
            iCnt += 1
            iProblems = 0

            if arcpy.Exists(comFL):
                arcpy.Delete_management(comFL)

            # clean up output from previous runs
            if arcpy.Exists(comFC):
                try:
                    sleep(3)
                    if arcpy.TestSchemaLock (comFC):
                        arcpy.Delete_management(comFC, "Featureclass")

                    else:
                        PrintMsg(" \nFailed to get schemalock on " + comFC, 0)

                except:
                    errorMsg()
                    raise MyError, "Unable to overwrite existing featureclass '" + comFC + "'"

            if arcpy.Exists(selLayer):
                #
                #
                try:
                    arcpy.Delete_management(selLayer, "Featurelayer")

                except:
                    raise MyError, "Failed to delete temporary layer"

            # Read soils layer to get polygon OID and associated attribute value,
            # load this information into 'dAtt' dictionary. This will be used to
            # populate the left and right attributes of the new polyline featureclass.

            dAtt = dict()
            theFields = ["OID@",fld1Name]

            if AS == "*":
                # Processing entire layer instead of by AREASYMBOL
                fldQuery = ""
                AS = descInput.baseName

            else:
                # Processing just this AREASYMBOL
                fldQuery = arcpy.AddFieldDelimiters(comFC, fld2Name) + " = '" + AS + "'"

            arcpy.MakeFeatureLayer_management(inputFC, selLayer, fldQuery)
            iSel = int(arcpy.GetCount_management(selLayer).getOutput(0))

            # format spacing for message
            if iSel > 0:
                # Go ahead and process this survey

                # format lead spacing for console message
                sp = " " * (4 -  len(str(iCnt)))
                PrintMsg(" \n" + sp + str(iCnt) + ". " + fld2Name + " " + AS + ": processing " + Number_Format(iSel, 0, True) + " features", 0)

                # Populating dAtt dictionary from a featurelayer causes problems because it may not include the
                # neccesary information for the adjacent polygon. This may slow things down a bit, but
                # it will prevent errors. WAIT! This shouldn't matter if we are only checking within the
                # survey area.

                # Save primary values for each polygon in the entire featureclass
                with arcpy.da.SearchCursor(selLayer, ["OID@",fld1Name]) as cursor:
                    for row in cursor:
                        dAtt[row[0]] = row[1]

                # Convert the selected mapunit polygon features to a temporary polyline featurelayer
                PrintMsg("\t\tConverting polygon input to a polyline featureclass...", 0)
                env.XYTolerance = xyTol
                arcpy.PolygonToLine_management(selLayer, comFC, "IDENTIFY_NEIGHBORS")
                # Assign field names for left polygon id and right polygon id
                lPID = "LEFT_FID"
                rPID = "RIGHT_FID"
                theQuery = "(" + arcpy.AddFieldDelimiters(comFC, "LEFT_FID") + " > -1 AND " + arcpy.AddFieldDelimiters(comFC, "RIGHT_FID") + " > -1 )" # include these records for copying to final
                sQuery = "(" + arcpy.AddFieldDelimiters(comFC, "LEFT_FID") + " > -1 AND " + arcpy.AddFieldDelimiters(comFC, "RIGHT_FID") + " > -1 )"  # exclude these records from cursor
                PrintMsg("\t\tIdentifying adjacent polygon boundaries with the same '" +  fld1Name + "' value...", 0)

                # Add left and right fields for common line test attribute
                if inputFC.endswith(".shp"):
                    # Need to limit fieldname to 10 characters because of DBF restrictions
                    lFld = "L_" + fld1Name[0:8]
                    rFld = "R_" + fld1Name[0:8]

                else:
                    lFld = "L_" + fld1Name
                    rFld = "R_" + fld1Name

                # modified addfield items to allow for width of Areasymbol values
                arcpy.AddField_management(comFC, lFld, "TEXT", "", "", fldLength, lFld, "NULLABLE")
                arcpy.AddField_management(comFC, rFld, "TEXT", "", "", fldLength, rFld, "NULLABLE")

                # Open common line featureclass and use cursor to add original polygon attributes from dictionary
                #
                theFields = [lPID,rPID,lFld,rFld]
                #PrintMsg(" \n" + comFC + " specified cursor fields: " + str(theFields), 0)

                with arcpy.da.UpdateCursor(comFC, theFields, sQuery) as cursor:
                    #iCnt = 0

                    for row in cursor:
                        #PrintMsg("\tUpdating " + rFld + " and " + lFld + " with " + str(dAtt[row[0]]) + " and " + str(dAtt[row[1]]), 0)
                        row[2] = dAtt[row[0]]
                        row[3] = dAtt[row[1]]
                        cursor.updateRow(row)

                #
                # Identify outer boundary and lines that are common lines and copy them to
                # the final featureclass.
                # This query will select commonlines only internal to the survey area
                #sQuery = theQuery + " AND " + lFld + " = " + rFld

                # Using the xxComLines featureclass, this query will select commonlines plus
                # overlapping boundaries between adjacent surveys
                sQuery = theQuery + " AND " + arcpy.AddFieldDelimiters(comFC, lFld) + " = " + arcpy.AddFieldDelimiters(comFC, rFld)

                #PrintMsg(" \nSelecting commonlines in " + comFC + " using query: " + sQuery, 0)
                tmpFL = "Temp Featurelayer"
                arcpy.MakeFeatureLayer_management(comFC, tmpFL, sQuery)

                # Get featurecount for final output
                iProblems = int(arcpy.GetCount_management(tmpFL).getOutput(0))

                if iProblems > 0:
                    # Found at least one common-line problem.
                    # Report finding, create CommonLine featureclass and display in ArcMap
                    iCL += iProblems
                    comList.append(AS)
                    PrintMsg("\t\tFound " + str(iProblems) + " common line problems for " + inputName + " " + inputDT.lower(), 2)

                    if arcpy.Exists(comFC2):
                        # output featureclass already exists with common lines from another survey area
                        arcpy.Append_management(tmpFL, comFC2)

                    else:
                        # first set of common lines identified, use them to create a new featureclass
                        arcpy.CopyFeatures_management(tmpFL, comFC2)

                    if arcpy.Exists(tmpFL):
                        arcpy.Delete_management(tmpFL)

                if arcpy.Exists(comFC):
                    # Having problems removing this when two successive runs are made with this tool.
                    #
                    try:
                        sleep(3)

                        if arcpy.TestSchemaLock(comFC):
                            arcpy.Delete_management(comFC)

                        else:
                            raise MyError, "Unable to overwrite existing featureclass '" + comFC + "' (schemalock)"

                    except:
                        errorMsg()
                        raise MyError, "Unable to overwrite existing featureclass '" + comFC

            else:
                # Skip this survey, no match for AREASYMBOL
                missList.append(AS)
                PrintMsg(" \n" + sp + str(iCnt) + ". " + fld2Name + " " + AS + ": no features found for this survey", 0)

        # End of iteration through AREASYMBOL list

        PrintMsg(" \nCommon Lines check complete \n ", 0)

        if len(missList) > 0:
            PrintMsg("The following surveys were not found in the input layer: " + ", ".join(missList), 2)

        if len(comList) > 0:
            PrintMsg("The following survey(s) had common-line errors: " + ", ".join(comList), 2)

        if iCL > 0 and arcpy.Exists(comFC2):
            try:
                # Add new field to track 'fixes'
                arcpy.AddField_management(comFC2, "Status", "TEXT", "", "", 10, "Status")
                arcpy.env.addOutputsToMap = True
                arcpy.SetParameter(3, comFL)

                # Put this section in a try-except. It will fail if run from ArcCatalog
                mxd = arcpy.mapping.MapDocument("CURRENT")
                arcpy.MakeFeatureLayer_management(comFC2, comFL)
                lyrFile = os.path.join( os.path.dirname(sys.argv[0]), "RedLine.lyr")
                arcpy.ApplySymbologyFromLayer_management(comFL, lyrFile)
                PrintMsg("Adding 'QA Common Lines' layer with " + str(iCL) + " errors to ArcMap \n ", 1)

            except:
                pass

        else:
            PrintMsg("No commonlines detected \n ", 0)

    else:
        PrintMsg(" \nFailed to set scratchworkspace \n", 2)

except MyError, e:
    # Example: raise MyError, "this is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()


