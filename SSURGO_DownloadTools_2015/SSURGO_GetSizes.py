# SSURGO_GetSizes.py
#
# Steve Peaslee, USDA-NRCS NCSS
#
# Gets directory size and file count
#
# Updated 2014-11-25
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
        errorMsg()
        return False

## ===================================================================================
def GetSize(d):
    try:
        dirSize = 0
        fileCnt = 0

        for dirpath, dirnames, filenames in os.walk(d):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                dirSize += os.path.getsize(fp)
                fileCnt += 1

        #PrintMsg("\t" + os.path.basename(d) + ": " + Number_Format(dir_size, 0, True))
        return dirSize, fileCnt

    except:
        errorMsg()
        return -1

## ===================================================================================
# main
import string, os, sys, traceback, locale, arcpy
from arcpy import env

try:
    # Script arguments...
    topDir = arcpy.GetParameterAsText(0)          # top-level input folder
    dataType = arcpy.GetParameter(1)              # list file geodatabases or any folder

    totalSize = 0
    minSize = 999999999999999999
    dList = [os.path.join(topDir, o) for o in os.listdir(topDir) if os.path.isdir(os.path.join(topDir, o))]
    dSizes = dict()
    PrintMsg(" \nInventorying " + dataType.lower() + " for " + topDir + " \n ", 0)
    arcpy.SetProgressor("step", "Getting directory listing...", 0, len(dList), 1)

    if dataType == "File Geodatabases":
        for d in dList:
            arcpy.SetProgressorPosition()
            # Only processing file geodatabases
            if d.endswith(".gdb"):
                arcpy.SetProgressorLabel(os.path.basename(d))
                dirSize, fileCnt = GetSize(d)  # bytes

                if dirSize >= 0:
                    totalSize += dirSize
                    dSizes[d] = float(dirSize), fileCnt

                    if dirSize < minSize:
                        minSize = dirSize

    else:
        for d in dList:
            # Processing all folders and file geodatabases
            arcpy.SetProgressorLabel(os.path.basename(d))
            arcpy.SetProgressorPosition()
            dirSize, fileCnt = GetSize(d)  # bytes

            if dirSize >= 0:
                totalSize += dirSize
                dSizes[d] = float(dirSize), fileCnt

                if dirSize < minSize:
                    minSize = dirSize

            else:
                raise MyError, " \n"



    # Decide whether to print results as KB, MB or GB using minimum directory size
    dec = 1

    if (minSize//(1024**4)) > 0:
        # minimum directory size is in terabyte range
        divisor = 1024.0**4
        units ="TB"

    elif (minSize//(1024.0**3)) > 0:
        # minimum directory size is in gigabyte range
        divisor = 1024.0**3
        units ="GB"

    elif (minSize//(1024**2)) > 0:
        # minimum directory size is in megabyte range
        divisor = 1024**2
        units = "MB"

    elif (minSize//1024) > 0:
        # minimum directory size is in kilobyte range
        divisor = 1024.0**2
        units = "MB"
        dec = 3

    else:
        # minimum directory size is in the byte range
        divisor = 1024**2
        units = "MB"
        dec = 6


    if len(dSizes) > 0:
        if dataType == "File Geodatabases":
            PrintMsg("FGDB, " + "SIZE_" + units + ", FILECOUNT")

        else:
            PrintMsg("FOLDER, " + "SIZE_" + units + ", FILECOUNT")

        for d in dList:
            try:
                dirSize, fileCnt = dSizes[d]
                sSize = Number_Format((dirSize/divisor), dec, False)
                PrintMsg(os.path.basename(d) + ", " + sSize + ", " + str(fileCnt), 0)

            except:
                pass

    else:
        raise MyError, "No matching data found in " + topDir

    # Decide whether to print the total as KB, MB or GB using minimum directory size
    if (totalSize//(1024**4)) > 0:
        divisor = 1024.0**4
        units ="TB"

    elif (totalSize//(1024**3)) > 0:
        divisor = 1024.0**3
        units ="GB"

    elif (totalSize//(1024**2)) > 0:
        divisor = 1024.0**2
        units = "MB"

    elif (totalSize//1024) > 0:
        divisor = 1024.0
        units = "KB"

    else:
        divisor = 1024**2
        units = "MB"

    if dataType == "File Geodatabases":
        PrintMsg(" \nTotal size of the inventoried geodatabases: " + Number_Format((totalSize/divisor), 3, True) + " " + units + " \n ", 0)

    else:
        PrintMsg(" \nTotal size of the input folder contents: " + Number_Format((totalSize/divisor), 3, True) + " " + units + " \n ", 0)



except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n ", 2)

except:
    errorMsg()
