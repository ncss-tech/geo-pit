# ---------------------------------------------------------------------------
# QA_EdgeMatch_lines.py
# Created on:
#
# Steve Peaslee, National Soil Survey Center
# Whityn Owen, Soil Survey Region 1

# Identifies where node-to-node joins across survey boundaries do NOT occur
# Only spatial data is tested; does not check MUKEY/MUSYM
# If mis-matches are found, they will be copied to a new featureclass and added to the
# ArcMap TOC.
#
# ArcGIS 10.1 compatible
#
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
                arcpy.AddMessage("    ")
                arcpy.AddError(string)

    except:
        pass

## ===================================================================================
# This function is not currently called but is left in for future use

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

try:
    # Check out ArcInfo license for PolygonToLine
    arcpy.SetProduct("ArcInfo")
    arcpy.OverwriteOutput = True

    # Script arguments...
    inLayer = arcpy.GetParameterAsText(0)       # required input soils layer with at least two survey areas to compare
    inField = arcpy.GetParameterAsText (1)      # The field containing AREASYMBOL values
    ssaList = arcpy.GetParameter(2)             # List of AREASYMBOLs from Tool Validation code
    layerName = arcpy.GetParameter(3)           # output featurelayer containing dangling points (not required)


    # Need to remove any joins before converting the polygons to polylines
    try:
        arcpy.RemoveJoin_management(inLayer)

    except:
        pass

    PrintMsg ("\ninLayer is " + inLayer +  "\ninField is " + inField + "\nssaList is" + str(ssaList), 0)

    # Start by getting information about the input layer
    descInput = arcpy.Describe(inLayer)
    inputDT = descInput.dataType.upper()

    if inputDT == "FEATURELAYER":
        inputName = descInput.Name
        inputFC = descInput.FeatureClass.catalogPath

    elif inputDT == "FEATURECLASS":
        inputName = descInput.Name
        inputFC = descInput.catalogPath

    # Get workspace information
    theWorkspace = os.path.dirname(inputFC)
    descW = arcpy.Describe(theWorkspace)
    wkDT = descW.DataType.upper()

    if wkDT == "FEATUREDATASET":
        theWorkspace = os.path.dirname(theWorkspace)

    # Setting workspace to that of the input soils layer
    env.workspace = theWorkspace
    env.overwriteOutput = True

    # Set scratchworkspace and then proceed with processing
    if setScratchWorkspace():


        # get the first input field object
        chkFields = arcpy.ListFields(inputFC, inField + "*")

        if len(chkFields) == 1:
            chkField = chkFields[0]
            fldName = chkField.name
            fldLength = chkField.length

        else:
            raise MyError("Problem getting field info for " + inField)


        # set name and location for temporary and permanent output features
        diss_Bound = os.path.join(env.scratchGDB, "xxDissBound") # temporary featureclass containing survey areas derived from soil poly dissolve
        soil_lines = os.path.join(env.scratchGDB, "xxSoilLines") # temporary featureclass containing soil polys converted to lines
        misMatch = os.path.join(env.scratchGDB, "Survey_Join_Error_p") # temporary output featureclass containing dangling vertices (join errors)
        misMatch2 = os.path.join(env.workspace, "QA_EdgeMatch_Errors_p")
        finalFL = "QA_EdgeMatch_Errors_p"


        # set final output to shapefile if input is shapefile and make the new field name compatible with the database type
        if inputFC.endswith(".shp"):
            misMatch = misMatch + ".shp"
            fldName = fldName[0:10]


        # set output map layer name
        selSoilsFL = "Selected Soils (by " +fldName + ")"


        # Build selection query string from AREASYMBOL list (ssaList)
        try:
            i = 0
            sQuery = ""
            numOfAreas = len(ssaList)
            for area in ssaList :
                i += 1
                if i < numOfAreas :
                    sQuery = sQuery + arcpy.AddFieldDelimiters(inputFC, fldName) + " = '" + area + "' OR "
                else :
                    sQuery = sQuery + arcpy.AddFieldDelimiters(inputFC, fldName) + " = '" + area + "')"
            sQuery = "(" + sQuery
        except:
            raise MyError("Unable to build Selection Query String from Areasymbol Parameter")


        # Make feature layer of selected surveys based on ssaList parameter
        ## THIS IS CREATED IN SOURCE WORKSPACE, NOT scratchWorkspace ##
        arcpy.MakeFeatureLayer_management(inputFC, selSoilsFL, sQuery)


######## ----- Main Algorithm for Checking MisMatches Begins Here ----- ##
        try:
            # Dissolve soils to create boundaries
            arcpy.Dissolve_management(selSoilsFL, diss_Bound, inField)
            PrintMsg("Dissolved input to create boundary", 0)

            # Convert Soil polys to line for Selected surveys
            arcpy.PolygonToLine_management(selSoilsFL, soil_lines, "IDENTIFY_NEIGHBORS")
            PrintMsg("Converted Soils to lines", 0)

            # Make soil_lines a Feature Layer
            arcpy.MakeFeatureLayer_management(soil_lines, "soil_linesFL")

            # Build whereclause for Select by Attribute
            whereclause = """%s = -1""" % arcpy.AddFieldDelimiters("soil_linesFL", 'LEFT_FID')
            PrintMsg("Built where clause " + whereclause, 0)

            # Select soil_lines cooincident with dissolved boundary layer
            arcpy.SelectLayerByLocation_management("soil_linesFL", "SHARE_A_LINE_SEGMENT_WITH", diss_Bound)
            PrintMsg("Selected lines based on boundary", 0)

            selBoundaryLines = str(arcpy.GetCount_management("soil_linesFL").getOutput(0))

            PrintMsg("Select by location selected " + selBoundaryLines + " features", 0)

            if selBoundaryLines > 0 :
                arcpy.SelectLayerByAttribute_management("soil_linesFL","REMOVE_FROM_SELECTION", whereclause)
                PrintMsg("Removed perimeter lines from selection", 0)

                # Delete interior soil survey boundaries in soil_lines feature layer
                arcpy.DeleteFeatures_management("soil_linesFL")
                PrintMsg("Deleted features",0)

                # Convert only dangling vertices to permanent feature class
                arcpy.FeatureVerticesToPoints_management(soil_lines, misMatch,"DANGLE")
                PrintMsg("Converted dangling vertices to points")

            else :
                raise myError("Trouble selecting boundaries in soil lines layer")


            iProblems = int(arcpy.GetCount_management(misMatch).getOutput(0))
            PrintMsg("Errors found: " + str(iProblems),1)

            if iProblems > 0:
                # Found at least one dangling node problem.
                # Report finding, create MisMatch featureclass and display in ArcMap
                arcpy.CopyFeatures_management(misMatch, misMatch2)
                PrintMsg("copied to misMatch2", 0)

                # Add new field to track 'fixes'
                arcpy.Delete_management(misMatch)
                PrintMsg("Deleted misMatch", 0)

                arcpy.AddField_management(misMatch2, "Status", "TEXT", "", "", 10, "Status")
                PrintMsg("Added Fields")

                try:
                    arcpy.mapping.MapDocument("Current")
                    arcpy.MakeFeatureLayer_management(misMatch2, finalFL)
                    PrintMsg("Made feature layer")

                    arcpy.SetParameter(3, finalFL)
                    PrintMsg("Set Param")

                    lyrFile = os.path.join(os.path.dirname(sys.argv[0]), "RedDot.lyr")
                    PrintMsg("Made layer file")

                    arcpy.ApplySymbologyFromLayer_management(finalFL, lyrFile)
                    PrintMsg("Applied symbology")

                    PrintMsg("\n Adding 'QA_EdgeMatch_Errors_p' layer with " + str(iProblems) + " features to ArcMap", 1)
                    PrintMsg(theWorkspace + " \n ", 1)
                except:
                    PrintMsg("Feature class 'QA_EdgeMatch_Errors_p' created in " + theWorkspace)


            else:
                PrintMsg(" \nNo common-attribute line problems found for " + inputName, 1)
                arcpy.Delete_management(misMatch)


        except:
            errorMsg()

    else:
        PrintMsg(" \nFailed to set scratchworkspace \n", 2)





except MyError, e:
    # Example: raise MyError("this is an error message")
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()


