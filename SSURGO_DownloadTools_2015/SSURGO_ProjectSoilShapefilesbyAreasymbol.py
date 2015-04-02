# SSURGO_ProjectSoilShapefilesbyAreasymbol.py
#
# evolved from SSURGO_MergeSoilShapefilesbyAreasymbol_GDB.py
#
# Purpose: allow batch projection of SSURGO soil shapefiles from Geographic WGS 1984 to a projected CS

# Requires input dataset structures to follow the NRCS standard for geospatial soils data...
#
# There currently is no method for handling inputs with more than one coordinate system,
# especially if there is more than one horizontal datum involved. Should work OK if
# an output coordinate system and datum transformation is set in the GP environment.
#
# Test version 11-10-2013
#
# 11-22-2013
# 12-13-2013 Changed datum transformation to ITRF00
# 2014-09-27

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
def SetOutputCoordinateSystem(inLayer, AOI):
    #
    # Not being used!
    #
    # Set a hard-coded output coordinate system (Geographic WGS 1984)
    # Set an ESRI datum transformation method for NAD1983 to WGS1984
    # Based upon ESRI 10.1 documentation and the methods that were used to
    # project SDM featureclasses during the transition from ArcSDE to SQL Server spatial
    #
    #   CONUS - NAD_1983_To_WGS_1984_5
    #   Hawaii and American Samoa- NAD_1983_To_WGS_1984_3
    #   Alaska - NAD_1983_To_WGS_1984_5
    #   Puerto Rico and U.S. Virgin Islands - NAD_1983_To_WGS_1984_5
    #   Other  - NAD_1983_To_WGS_1984_1 (shouldn't run into this case)

    try:
        outputSR = arcpy.SpatialReference(4326)        # GCS WGS 1984
        # Get the desired output geographic coordinate system name
        outputGCS = outputSR.GCS.name

        # Describe the input layer and get the input layer's spatial reference, other properties
        desc = arcpy.Describe(inLayer)
        dType = desc.dataType
        sr = desc.spatialReference
        srType = sr.type.upper()
        inputGCS = sr.GCS.name

        # Print name of input layer and dataype
        if dType.upper() == "FEATURELAYER":
            #PrintMsg(" \nInput " + dType + ": " + desc.nameString, 1)
            inputName = desc.nameString

        elif dType.upper() == "FEATURECLASS":
            #PrintMsg(" \nInput " + dType + ": " + desc.baseName, 1)
            inputName = desc.baseName

        else:
            #PrintMsg(" \nInput " + dType + ": " + desc.name, 1)
            inputName = desc.name

        if outputGCS == inputGCS:
            # input and output geographic coordinate systems are the same
            # no datum transformation required
            #PrintMsg(" \nNo datum transformation required", 1)
            tm = ""

        #else:
            # Different input and output geographic coordinate systems, set
            # environment to unproject to WGS 1984, matching Soil Data Mart

            #if AOI == "Lower 48 States":
            #    tm = "NAD_1983_To_WGS_1984_5"

            #elif AOI == "Alaska":
            #    tm = "NAD_1983_To_WGS_1984_5"

            #elif AOI == "Hawaii":
            #    tm = "NAD_1983_To_WGS_1984_3"

            #elif AOI == "American Samoa":
            #    tm = "NAD_1983_To_WGS_1984_3"

            #elif AOI == "Puerto Rico and U.S. Virgin Islands":
            #    tm = "NAD_1983_To_WGS_1984_5"

            #elif AOI == "Pacific Islands Area":
            #    tm = ""
            #    PrintMsg(" \nWarning! No coordinate shift is being applied", 0)

            #else:
            #    raise MyError, "Invalid geographic region (" + AOI + ")"

        # These next two lines set the output coordinate system environment
        # using the ITRF00 method for WGS1984 to NAD1983
        arcpy.env.outputCoordinateSystem = outputSR
        tm = "WGS_1984_(ITRF00)_To_NAD_1983"
        arcpy.env.geographicTransformations = tm

        #if tm != "":
        #    PrintMsg(" \n\tUsing datum transformation method '" + tm + "' for " + AOI + " \n ", 1)

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def SetTransformation(AOI):
    # Set appropriate XML Workspace Document according to AOI
    # The xml files referenced in this function must all be stored in the same folder as the
    # Python script and toolbox
    try:

        if AOI in ["Hawaii", "American Samoa", "Pacific Islands Area"] :
            # Output coordinate system will be WGS 1984, no transformation required
            tm = ""

        else:
            # Use ArcGIS 10.1 default value for NAD1983 to WGS1984 datum transformation (12-13-2013)
            tm = "WGS_1984_(ITRF00)_To_NAD_1983"

        # This next line sets the GP environment to use the appropriate transformation method
        # according to the user's AOI choice.
        arcpy.env.geographicTransformations = tm

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def ProjectShapefiles(inputFolder, surveyList, outputWS, AOI, outputCS, bTabular):
    # Primary function. Can only be used for coordinate systems using NAD 1983 or WGS 1984 datums
    try:

        if len(surveyList) == 0:
            # surveyList is a list of 'soil_' folders that exist under the inputFolder
            raise MyError, "At least one input soil survey area is required"

        # Set datum transformation method for all output shapefiles
        bTransformed = SetTransformation(AOI)

        # Set output coordinate system
        env.outputCoordinateSystem = outputCS

        # process each selected soil survey
        iSurveys = len(surveyList)

        if bTabular:
            PrintMsg(" \nProjecting spatial data and copying tabular data for " + str(iSurveys) + " soil surveys", 0)

        else:
            PrintMsg(" \nProjecting spatial data for " + str(iSurveys) + " soil surveys", 0)

        PrintMsg("  Output folder: " + outputWS, 0)
        PrintMsg("  Output coordinate system: " + env.outputCoordinateSystem.name, 0)

        arcpy.SetProgressorLabel("Projecting SSURGO datasets...")
        arcpy.SetProgressor("step", "Projecting SSURGO datasets...",  0, iSurveys, 1)

        for subFolder in surveyList:
            # Define input shapefiles
            # recreate the standard set of SSURGO shapefilenames for each SSURGO featureclass type using the
            # AREASYMBOL then confirm shapefile existence for each survey..
            PrintMsg(" \n\t" + subFolder[-5:].upper() + "...", 0)
            PrintMsg("\t\t" + "Projecting spatial", 0)
            areaSym = subFolder[-5:].encode('ascii')
            env.workspace = os.path.join( inputFolder, os.path.join( subFolder, "spatial"))
            mupolyName = "soilmu_a_" + areaSym + ".shp"
            mulineName = "soilmu_l_" + areaSym + ".shp"
            mupointName = "soilmu_p_" + areaSym + ".shp"
            sflineName = "soilsf_l_" + areaSym + ".shp"
            sfpointName = "soilsf_p_" + areaSym + ".shp"
            sapolyName = "soilsa_a_" + areaSym + ".shp"

            # Define output folder for SSURGO dataset including shapefiles
            outputFolder = os.path.join(os.path.join(outputWS, subFolder), "spatial")

            # Create output folders
            arcpy.CreateFolder_management(outputWS, subFolder)
            arcpy.CreateFolder_management(os.path.join(outputWS, subFolder), "spatial")

            if arcpy.Exists(mupolyName):
                desc = arcpy.Describe(mupolyName)
                sr = desc.spatialReference
                datum = desc.spatialReference.GCS.datumName

                if not datum in ('D_WGS_1984','D_North_American_1983'):
                    raise MyError, "Input shapefile has an invalid coordinate system (" + sr.name + ")"

                if int(arcpy.GetCount_management(mupolyName).getOutput(0)) > 0:
                    arcpy.CopyFeatures_management(mupolyName, os.path.join(outputFolder, mupolyName))

                else:
                    arcpy.CreateFeatureclass_management (os.path.join(os.path.join(outputWS, subFolder), "spatial"), mupolyName, "Polygon", os.path.join(env.workspace, mupolyName))

                if arcpy.Exists(mulineName):
                    if int(arcpy.GetCount_management(mulineName).getOutput(0)) > 0:
                        arcpy.CopyFeatures_management(mulineName, os.path.join(outputFolder, mulineName))

                    else:
                        arcpy.CreateFeatureclass_management (os.path.join(os.path.join(outputWS, subFolder), "spatial"), mulineName, "Polyline", os.path.join(env.workspace, mulineName))

                if arcpy.Exists(mupointName):
                    if int(arcpy.GetCount_management(mupointName).getOutput(0)) > 0:
                        arcpy.CopyFeatures_management(mupointName, os.path.join(outputFolder, mupointName))

                    else:
                        arcpy.CreateFeatureclass_management (os.path.join(os.path.join(outputWS, subFolder), "spatial"), mupointName, "Point", os.path.join(env.workspace, mupointName))

                if arcpy.Exists(sflineName):
                    if int(arcpy.GetCount_management(sflineName).getOutput(0)) > 0:
                        arcpy.CopyFeatures_management(sflineName, os.path.join(outputFolder, sflineName))

                    else:
                        arcpy.CreateFeatureclass_management (os.path.join(os.path.join(outputWS, subFolder), "spatial"), sflineName, "Polyline", os.path.join(env.workspace, sflineName))

                if arcpy.Exists(sfpointName):
                    if int(arcpy.GetCount_management(sfpointName).getOutput(0)) > 0:
                        arcpy.CopyFeatures_management(sfpointName, os.path.join(outputFolder, sfpointName))

                    else:
                        arcpy.CreateFeatureclass_management (os.path.join(os.path.join(outputWS, subFolder), "spatial"), sfpointName, "Point", os.path.join(env.workspace, sfpointName))

                if arcpy.Exists(sapolyName):
                    if int(arcpy.GetCount_management(sapolyName).getOutput(0)) > 0:
                        arcpy.CopyFeatures_management(sapolyName, os.path.join(outputFolder, sapolyName))

                    else:
                        arcpy.CreateFeatureclass_management (os.path.join(os.path.join(outputWS, subFolder), "spatial"), sapolyName, "Point", os.path.join(env.workspace, sapolyName))

                if bTabular:
                    # Move up one level
                    env.workspace = os.path.join( inputFolder, subFolder)

                    # Copy tabular folder
                    PrintMsg("\t\t" + "Copying tabular and metadata")
                    inTab = os.path.join( inputFolder, os.path.join( subFolder, "tabular"))
                    outTab = os.path.join(os.path.join(outputWS, subFolder), "tabular")
                    distutils.dir_util.copy_tree(inTab, outTab)

                    # Copy readme files and metadata files
                    inFile = os.path.join(inputFolder, os.path.join(subFolder, "readme.txt"))
                    outFile = os.path.join(outputWS, os.path.join(subFolder, "readme.txt"))

                    if os.path.isfile(inFile):
                        shutil.copyfile(inFile, outFile)

                    # Copy metadata files
                    metaFiles = arcpy.ListFiles("soil_metadata*")

                    for thisFile in metaFiles:
                        inFile = os.path.join(inputFolder, os.path.join(subFolder, thisFile))
                        outFile = os.path.join(outputWS, os.path.join(subFolder, thisFile))

                        shutil.copyfile(inFile, outFile)

            # end of loop
            arcpy.SetProgressorPosition()

        PrintMsg(" \nNewly projected data has been placed in the " + outputWS + " folder \n ", 0)
        return True

    except MyError, e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return True

## ===================================================================================

# Import system modules
import arcpy, sys, string, os, traceback, locale, shutil
from operator import itemgetter, attrgetter

# Create the Geoprocessor object
from arcpy import env

try:
    inputFolder = arcpy.GetParameterAsText(0)     # location of SSURGO datasets containing spatial folders
    # skip parameter 1.                           # Survey boundary layer (only used within Validation code)
    # The following line references parameter 1 in the other script and is the only change
    surveyList = arcpy.GetParameter(2)            # list of SSURGO dataset folder names to be proccessed (soil_*)
    outputWS = arcpy.GetParameterAsText(3)        # Name of output folder
    AOI = arcpy.GetParameterAsText(4)             # Geographic region used to determine datum transformation method
    outputCS = arcpy.GetParameter(5)              # Output coordinate system
    bTabular = arcpy.GetParameter(6)              # Copy tabular folder contents to new location

    if bTabular:
        import distutils
        from distutils import dir_util

    bProjected = ProjectShapefiles(inputFolder, surveyList, outputWS, AOI, outputCS, bTabular)

    if bProjected:
        PrintMsg(" \nProcess completed successfully \n ", 0)

except MyError, e:
    PrintMsg(str(e), 2)

except:
    errorMsg()
