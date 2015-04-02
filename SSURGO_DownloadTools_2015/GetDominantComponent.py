# GetDominantComponent.py
#
# Steve Peaslee, USDA-NRCS
#
# Uses simplest method of determining dominant componet for each map unit. Takes
# the first component with the highest representative component percent.
#
# One weakness in this method is that it does not handle 'ties' where two components
# have the same comppct_r. This simplistic method does not take into account
# what kind of data is behind either (nulls or higher-lower values).
#
## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
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
                #arcpy.AddMessage("    ")

    except:
        pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
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
        PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcpy, traceback
from arcpy import env
inputDB = arcpy.GetParameterAsText(0)    # Input database. Assuming SSURGO or gSSURGO soils database
outputTbl = arcpy.GetParameterAsText(1)  # Output table containing dominant component for each map unit

try:
    PrintMsg(" \nGetting dominant component for each map unit in " + os.path.basename(inputDB), 0)

    coTbl = os.path.join(inputDB, "component")

    if not arcpy.Exists(coTbl):
        raise MyError, "COMPONENT table not found for " + inputDB

    # Open component table sorted by cokey and comppct_r
    iCnt = int(arcpy.GetCount_management(coTbl).getOutput(0))

    dComp = dict()

    sqlClause = "ORDER BY MUKEY DESC, COMPPCT_R DESC, COKEY DESC"
    arcpy.SetProgressor("step", "Reading component table...",  0, iCnt, 1)

    with arcpy.da.SearchCursor(coTbl, ["mukey", "cokey", "comppct_r"], "", "", "", (None, sqlClause)) as incur:
        for inrec in incur:
            if not inrec[0] in dComp:
                # this is the dominant component
                dComp[inrec[0]] = inrec[1], inrec[2]

            arcpy.SetProgressorPosition()

    if len(dComp) > 0:
        arcpy.ResetProgressor()
        # write values to new table
        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        arcpy.CreateTable_management(os.path.dirname(outputTbl), os.path.basename(outputTbl))
        arcpy.AddField_management(outputTbl, "mukey", "Text", "", "", 30)
        arcpy.AddField_management(outputTbl, "cokey", "Text", "", "", 30)
        arcpy.AddField_management(outputTbl, "comppct_r", "Short")

    arcpy.SetProgressor("step", "Saving dominant component information...",  0, len(dComp), 1)

    with arcpy.da.InsertCursor(outputTbl, ["mukey", "cokey", "comppct_r"]) as outcur:
        for mukey, val in dComp.items():
            cokey, comppct_r = val
            outrec = [mukey, cokey, comppct_r]
            outcur.insertRow(outrec)
            arcpy.SetProgressorPosition()

    arcpy.AddIndex_management(outputTbl, "mukey", "Indx_dcMukey", "UNIQUE")
    PrintMsg(" \nFinished writing dominant component information to " + os.path.basename(outputTbl) + " \n ", 0)

except MyError, e:
    # Example: raise MyError("this is an error message")
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()
