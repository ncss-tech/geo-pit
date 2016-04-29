#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     27/04/2016
# Copyright:   (c) Adolfo.Diaz 2016
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
        #print msg

        f = open(textFilePath,'a+')
        f.write(msg + " \n")
        f.close

        del f

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

## ================================================================================================================
def createPedonFGDB():
    # This Function will create a new File Geodatabase using a pre-established XML workspace
    # schema.  All Tables will be empty and should correspond to that of the access database.
    # Relationships will also be pre-established.
    # Return false if XML workspace document is missing OR an existing FGDB with the user-defined
    # name already exists and cannot be deleted OR an unhandled error is encountered.
    # Return the path to the new Pedon File Geodatabase if everything executes correctly.

    try:
        AddMsgAndPrint("\nCreating New Pedon File Geodatabase",0)

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "NASIS_Pedons_XMLWorkspace.xml"

        # Return false if xml file is not found and delete targetGDB
        if not arcpy.Exists(pedonXML):
            AddMsgAndPrint("\t" + os.path.basename(pedonXML) + "Workspace document was not found!",2)
            return ""

        newPedonFGDB = os.path.join(outputFolder,GDBname)

        if arcpy.Exists(newPedonFGDB):
            try:
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Deleting and re-creating FGDB",1)
                arcpy.Delete_management(newPedonFGDB)

            except:
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Failed to delete",2)
                return ""

        # Create empty temp File Geodatabae
        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])

        # set the pedon schema on the newly created temp Pedon FGDB
        AddMsgAndPrint("\tImporting NCSS Pedon Schema into " + GDBname + ".gdb")
        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "SCHEMA_ONLY", "DEFAULTS")

        arcpy.RefreshCatalog(outputFolder)

        AddMsgAndPrint("\tSuccessfully created: " + GDBname + ".gdb")

        return newPedonFGDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return ""

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return ""


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, locale, traceback, urllib, re, arcpy, operator, getpass
from arcpy import env
from arcpy.sa import *

if __name__ == '__main__':

    inputFeatures = arcpy.GetParameter(0)
    GDBname = arcpy.GetParameter(1)
    outputFolder = arcpy.GetParameterAsText(2)

    pedonFGDB = createPedonFGDB()

    if pedonFGDB == "":
        raise ExitError, " \n Failed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!"




