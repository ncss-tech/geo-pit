# gSSURGO_CheckValuTable.py
#
# Steve Peaslee, National Soil Survey Center
#
# 2015-01-12. Problem encountered when comparing CONUS and ALL databases. After record 1,442 the
# comparison is incorrectly reporting a discrepancy between the two tables (NormValu and Valu2).
# Rewrote CompareTables to use dictionaries to store data and used list comparison to create
# sorted list of mukeys.
#
# In the 2015 data, there were no valid map units missing from Norm's subset version of the VALU1 table.
# There are 63 map units (including NOTCOMs) that have NO component data at all.
#
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
def CompareTables(input_1, input_2, diffTbl, aFields):

    try:
        # All processing involves sorting both tables on mukey to keep them in sync as
        # much as possible.

        iRec = 0

        if arcpy.Exists(diffTbl):
            arcpy.Delete_management(diffTbl)

        # End of cleanup

        # Field list for cursors, includes mukey and numeric fields
        qFields = ["mukey"]
        qFields.extend(aFields)
        idx = len(aFields)
        noneList = len(aFields) * [None]   # use for records with no data

        iCnt1 = int(arcpy.GetCount_management(input_1).getOutput(0))
        PrintMsg(" \nThe first table contains " + Number_Format(iCnt1, 0, True) + " map unit records", 0)

        QueryTable_2 = "QueryTable_2"
        arcpy.MakeQueryTable_management(input_2, QueryTable_2, "ADD_VIRTUAL_KEY_FIELD", "", qFields, "OBJECTID = 1")
        iCnt2 = int(arcpy.GetCount_management(input_2).getOutput(0))
        PrintMsg(" \nThe second table contains " + Number_Format(iCnt2, 0, True) + " map unit records", 0)

        PrintMsg(" \nReading input tables...", 0)
        muOrder1 = list()
        data1 = dict()
        arcpy.SetProgressor("step", "Reading data from first table (" + os.path.basename(input_1) + ")...", 0, iCnt1, 1)

        with arcpy.da.SearchCursor(input_1, qFields) as mucur:
            for rec in mucur:
                newrec = list(rec)
                mukey = newrec[0]
                newrec.pop(0)
                muOrder1.append(int(mukey))
                data1[mukey] = newrec
                arcpy.SetProgressorPosition()

        muOrder2 = list()
        data2 = dict()
        arcpy.SetProgressor("step", "Reading data from second table (" + os.path.basename(input_2) + ")...", 0, iCnt2, 1)

        with arcpy.da.SearchCursor(input_2, qFields) as mucur:
            for rec in mucur:
                newrec = list(rec)
                mukey = newrec[0]
                newrec.pop(0)
                muOrder2.append(int(mukey))
                data2[mukey] = newrec
                arcpy.SetProgressorPosition()

        # Get mapunit keys for those common to both tables
        muCommon = list(set(muOrder1).intersection(muOrder2))
        muCommon.sort()
        iCommon = len(muCommon)

        # Get mapunit keys for those records that are in the second table but not the second
        muDiff = list(set(muOrder2).difference(muCommon))

        if len(muDiff) > 0:
            muDiff.sort()
            muDiff2 = list()
            for mukey in muDiff:
                muDiff2.append(str(mukey))

            PrintMsg(" \nThere are " + Number_Format(len(muDiff), 0, True) + " mapunits in the second table that have no match in the first:", 1)
            #PrintMsg(" \n(" + str(muDiff2)[1:-1] + ") \n ", 0)

            # Save data issues to permanent files for later review
            # output folder will be set to the location of the 'new' table
            inputDB = os.path.dirname(input_2)

            if len(muDiff2) > 0:
                fileCo = os.path.basename(inputDB)[:-4] + "_MissingMapunits.txt"
                fileCo = os.path.join(os.path.dirname(inputDB), fileCo)
                fh = open(fileCo, "w")
                fh.write(inputDB + "\n")
                fh.write("Map units in the " + os.path.basename(input_2) + " table with no matching MUKEY in " + os.path.basename(input_2) + " table \n\n")
                fh.write("MUKEY IN ('" + "', '".join(muDiff2) + "') \n")
                fh.close()
                PrintMsg(" \nMap units missing (" + Number_Format(len(muDiff2), 0, True) + ") from the first table saved to:\t" + fileCo, 0)


        else:
            PrintMsg(" \nAll mapunits in the second table will be compared")

        if iCommon > 0:
            arcpy.SetProgressor("step", "Saving differences to " + os.path.basename(diffTbl) + "...",  0, iCommon, 1)
            arcpy.CreateTable_management(os.path.dirname(diffTbl), os.path.basename(diffTbl), QueryTable_2)
            arcpy.Delete_management(QueryTable_2)
            PrintMsg(" \nCalculating differences for " + Number_Format(iCommon, 0, True) + " common mapunits", 0)

            # initialize list to contain sum of differences
            sumList = list()
            for i in range(len(qFields) - 1):
                sumList.append(0)

            with arcpy.da.InsertCursor(diffTbl, qFields) as dfcur:
                arcpy.SetProgressor("step", "Saving calculated differences to " + os.path.basename(diffTbl), 0, iCommon, 1)

                for mukey in muCommon:
                    rec1 = data1[str(mukey)]
                    rec2 = data2[str(mukey)]

                    for i in range(idx):
                        if rec1[i] is None:
                            rec1[i] = 0

                        if rec2[i] is None:
                            rec2[i] = 0

                    # Problem where maxArray values are small and diffArray values are less than one.
                    # Returns an artificially large percentage due to roundoff differences

                    # Trying to figure out why 3 mapunits in WV come up with a negative difference
                    # of twice the orinal values instead of zero

                    array1 = np.rint(np.array(rec1))
                    array2 = np.rint(np.array(rec2))

                    #diffArray = np.rint(array1) - np.rint(array2)  # Difference rounded up to integer
                    diffArray = array1 - array2

                    #if mukey == 0:
                    #    PrintMsg(" \nREC1" + str(mukey) + ": " + str(rec1), 1)
                    #    PrintMsg(" \nREC2" + str(mukey) + ": " + str(rec2), 1)
                    #    PrintMsg(" \n" + str(mukey) + ": " + str(array1), 1)
                    #    PrintMsg(" \n" + str(mukey) + ": " + str(array2), 1)
                    #    PrintMsg(" \nDIFF:    " + ": " + str(array2), 1)

                    diffArray2 = np.absolute(np.divide(diffArray, array1))               # Divide difference by first table
                    rec3 = np.rint(np.multiply(diffArray2, 100.0))                   #
                    newrec = [mukey]

                    for val in rec3:
                        # Round off floats and write integer values to final output table table
                        #newrec.append(round(val, 0))
                        if str(val) in ['nan', 'inf']:
                            val = 0

                        newrec.append(val)

                    #PrintMsg("Rec: " + str(newrec), 1)
                    dfcur.insertRow(newrec) # add record to final output table

                    arcpy.SetProgressorPosition()

            PrintMsg(" \nFinished calculating differences...", 0)
            PrintMsg("Output table: " + diffTbl + " \n ", 0)

            return True

        else:
            raise MyError, "There are no map units common to both tables"

        # Other statistics....
        #
        # numpy.mean(a, axis=None, dtype=None, out=None, keepdims=False)

        # numpy.std(a, axis=None, dtype=None, out=None, ddof=0, keepdims=False)

        # numpy.var(a, axis=None, dtype=None, out=None, ddof=0, keepdims=False)

        # numpy.amin(a, axis=None, out=None, keepdims=False)

        # numpy.amax(a, axis=None, out=None, keepdims=False)

        # Try creating other types of arrays
        # Mean
        #meanArray = np.mean(oldArray, axis=0)
        #PrintMsg(" \nMean array shape: " + str(meanArray.shape), 1)
        #PrintMsg(" \nMean: " + str(meanArray), 1)

        # Min
        #minArray = np.amin(oldArray, axis=0)
        #PrintMsg(" \nMin array shape: " + str(meanArray.shape), 1)
        #PrintMsg(" \nMin: " + str(minArray), 1)

        # Max
        #maxArray = np.amax(oldArray, axis=0)
        #PrintMsg(" \nMin array shape: " + str(meanArray.shape), 1)
        #PrintMsg(" \nMax: " + str(maxArray), 1)

        # Range
        #rngArray = np.subtract(maxArray, minArray)
        #PrintMsg(" \nRange: " + str(rngArray), 1)

    except MyError, e:
        # Example: raise MyError("this is an error message")
        PrintMsg(str(e) + " \n", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import os, sys, string, re, locale, arcpy, traceback, time
from arcpy import env
import numpy as np

input_1 = arcpy.GetParameterAsText(0)  # original valu1 table from FY2014
input_2 = arcpy.GetParameterAsText(1)     # new valu2 table from ArcTool
diffTbl = arcpy.GetParameterAsText(2)    # output table containing differences
aFields = arcpy.GetParameter(3)          # list of common fields to be compared (new)

env.overwriteOutput = True

try:

    PrintMsg(" \nComparing tables", 0)

    bProcessed = CompareTables(input_1, input_2, diffTbl, aFields)



    PrintMsg(" \nProcess completed", 0)

except MyError, e:
    # Example: raise MyError("this is an error message")
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()
