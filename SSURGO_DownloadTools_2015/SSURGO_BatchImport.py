# SSURGO_BatchImport.py
#
# For gSSURGO production only.
#
# Quick and dirty method for unzipping WSS Cache and renaming folders to soil_[Areasymbol]
# This folder naming convention is required for the rest of the gSSURGO related tools.
#
# These datasets will NOT run the Tabular Import regardless of whether the Template
# databases are present.
#
# Will work with either version of the WSS Cache (with-or-without Template DB), but the
# version 'without' will run a little faster because of smaller filesize.
#
# Designed to create gSSURGO databases from the tabular text files and shapefiles.
#
# New datasets are unzipped and copied to a new location, leaving the original cache files untouched.

# 2015-02-19

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
        return ""

## ===================================================================================
# def ProcessSurvey(inputFolder, outputFolder, importDB, areaSym, bRemoveTXT):
def ProcessSurvey(inputFolder, outputFolder, areaSym):
    # Download and import the specified SSURGO dataset

    try:
        # New code
        env.workspace = inputFolder
        wc = "wss_SSA_" + areaSym + "*.zip"
        zipFiles = arcpy.ListFiles(wc)

        if len(zipFiles) == 0:
            raise MyError, "Unable to find matching file in cache directory (" + wc + ")"

        else:
            if len(zipFiles) == 1:
                # get the only zip file
                zipName = zipFiles[0]

            else:
                # if there is more than one match to the wildcard, grab the second one.
                # hopefully this is the one without the Template database.
                zipName = zipFiles[1]

        surveyDate = zipName[-15:-15].encode('ascii')

        # set standard final path and name for template database
        newFolder = os.path.join(outputFolder, "soil_" + areaSym.lower())

        # Get new SSURGO download or replace an older version of the same survey
        # Otherwise skip download
        #
        PrintMsg(" \nProcessing survey " + areaSym, 0)

        bZip = UnzipDownload(inputFolder, outputFolder, newFolder, zipName, areaSym)

        if not bZip:
            return MyError, ""

        env.workspace = outputFolder
        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def UnzipDownload(inputFolder, outputFolder, newFolder, zipName, areaSym ):
    # inputFolder, zipName, outputFolder, areaSym, newFolder
    # Given zip file name, try to unzip it

    try:
        #local_zip = os.path.join(outputFolder, zipName)
        local_zip = os.path.join(inputFolder, zipName)

        if os.path.isfile(local_zip):
            # got a zip file, go ahead and extract it
            zipSize = (os.stat(local_zip).st_size / (1024.0 * 1024.0))

            if zipSize > 0:
                PrintMsg("\tUnzipping " + zipName + " (" + Number_Format(zipSize, 3, True) + " MB)...", 0)

                # remove output folder if it exists from a previous run
                if os.path.isdir(newFolder):
                    shutil.rmtree(newFolder, True)

                with zipfile.ZipFile(local_zip, "r") as z:
                    # a bad zip file returns exception zipfile.BadZipfile
                    z.extractall(outputFolder)
                    time.sleep(0.2)   # Saw a Windows Error: 'Access denied' when renaming

                # rename output folder to: soil_[areasymbol.lowercase]
                if os.path.isdir(os.path.join(outputFolder, zipName[:-4])):
                    # this is an older zip file that has the 'wss_' directory structure
                    os.rename(os.path.join(outputFolder, zipName[:-4]), newFolder)

                elif os.path.isdir(os.path.join(outputFolder, areaSym.upper())):
                    # this must be a newer zip file using the uppercase AREASYMBOL directory
                    os.rename(os.path.join(outputFolder, areaSym.upper()), newFolder)

                elif os.path.isdir(newFolder):
                    # this is a folder using the correct field office naming convention (soil_ne109)
                    # it does not require renaming.
                    pass

                else:
                    # none of the subfolders within the zip file match any of the expected names
                    raise MyError, "Subfolder within the zip file does not match any of the standard names"

            else:
                # Zero-byte zip file in WSS Cache
                PrintMsg("\tEmpty zip file for " + areaSym + ": " + surveyName, 1)

            return True

        else:
            # Don't have a zip file, need to find out circumstances and document
            # rename downloaded database using standard convention, skip import
            raise MyError, "Missing zip file (" + local_zip + ")"
            return False

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except zipfile.BadZipfile:
        PrintMsg("\tBad zip file (" + zipName + ")", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
# main
# Import system modules
import arcpy, sys, os, locale, string, traceback, shutil, zipfile
from arcpy import env
#from _winreg import *
from time import sleep

try:
    arcpy.OverwriteOutput = True

    # Script arguments...
    wc = arcpy.GetParameter(0)                  # UI parameter, not being used in the script
    inputFolder = arcpy.GetParameterAsText(1)   # folder where SSURGO zip files are located
    asList = arcpy.GetParameter(2)              # list of Areasymbols to be processed
    outputFolder = arcpy.GetParameterAsText(3)  # folder where output SSURGO will be placed

    # initialize error and status trackers
    failedList = list()  # track list of failed downloads
    failedCnt = 0        # track consecutive failures
    iGet = 0

    PrintMsg(" \n" + str(len(asList)) + " soil survey(s) selected for processing", 0)

    # set workspace to output folder
    env.workspace = outputFolder

    # Create ordered list by Areasymbol
    asDict = dict()

    #asList.sort(reverse = bReverse)
    asList.sort()

    arcpy.SetProgressor("step", "Unzipping SSURGO data...",  0, len(asList), 1)

    # Proccess list of areasymbols
    #
    for areaSym in asList:
        # Run import process in order of listed Areasymbol values
        iGet += 1

        arcpy.SetProgressorLabel("Unzipping survey " + areaSym + " (number " + str(iGet) + " of " + str(len(asList)) + " total)")
        time.sleep(1)
        bProcessed = ProcessSurvey(inputFolder, outputFolder, areaSym)

        if bProcessed == False:
            failedList.append(areaSym)
            failedCnt += 1

        if failedCnt > 4:
            raise MyError, "Five consecutive failures, bailing out"

        if len(failedList) > 24:
            raise MyError, "Twenty-five total failures, bailing out"

        arcpy.SetProgressorPosition()

    if len(failedList) == 0:
        PrintMsg(" \nDownload process complete with no problems \n ", 0)

    else:
        PrintMsg(" \nThese surveys failed to be processed: " + ", ".join(failedList) + " \n ", 2)

    arcpy.SetProgressorLabel("Processing complete...")
    env.workspace = outputFolder

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e), 2)

except:
    errorMsg()


