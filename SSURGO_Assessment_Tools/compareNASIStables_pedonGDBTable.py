#-------------------------------------------------------------------------------
# Name:        compareNASIStables_pedonGDBTable.py
# Purpose:     This script will compare the NASIS table and fields from the 'WEB PC
#              MAIN URL' to the tables and fields in the Pedon FGDB that follows the NASIS 7.1
#              Schema. It is primarily for Jason Nemecek to adjust the pedon reports so that
#              they match the 7.1 schema.
#
# Author:      Adolfo.Diaz
#
# Created:     04/08/2016
# Last Modified: 9/28/2016
# Copyright:   (c) Adolfo.Diaz 2016
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
        print msg

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError(msg)

    except:
        pass

## ===================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

# ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

# =========================================================== Main Body =============================================================================
# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    try:
        pedonID = arcpy.GetParameterAsText(0)

        #sampleURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186"
        sampleURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=" + str(pedonID)
        pedonGDB =  os.path.dirname(sys.argv[0]) + os.sep + 'Nasis_Pedons.gdb'

        theReport = urllib.urlopen(sampleURL)

        bFieldNameRecord = False # boolean that marks the starting point of the table and attributes.

        """ ---------------------------------Parse the report to isolate the NASIS tables and fields -------------------------"""
        nasisDict = dict()  # collection of table and field names {'siteobs': ['seqnum','obsdate','obsdatekind'] from the URL report
        tempTableName = ""  # name of the current table

        # iterate through the report until a valid record is found
        for theValue in theReport:
            fieldNames = list()
            theValue = theValue.strip() # remove whitespace characters

            # Iterating through the report
            if bFieldNameRecord:

                nasisDict[tempTableName] = (theValue.split('|'))
                tempTableName = ""
                bFieldNameRecord = False

            elif theValue.find('@begin') > -1:
                bFieldNameRecord = True
                tempTableName = theValue[theValue.find('@begin')+7:]

            else:
                continue

        del bFieldNameRecord,tempTableName

        if not len(nasisDict):
            raise ExitError,"\n\nNo records returned for pedon ID: " + str(pedonID)

        arcpy.env.workspace = pedonGDB
        pedonGDBTables = arcpy.ListTables('*')

        if arcpy.ListFeatureClasses('site'):pedonGDBTables.append('site') # Site is not a table so we will manually add it.
        missingTables = list()

        """ ---------------------------------------- Begin the Comparison between NASIS URL and FGDB -----------------------------"""
        discrepancies = 0
        for nasisTable in nasisDict.keys():

            # Skip any Metadata table
            if nasisTable.find("Metadata") > -1: continue

            # Check if NASIS table exists in Pedon FGDB; log and continue if it doesn't
            if nasisTable not in pedonGDBTables:
                missingTables.append(nasisTable)
                continue

            else:
                pedonGDBTables.remove(nasisTable)

            gdbTableFields = [f.name for f in arcpy.ListFields(pedonGDB + os.sep + nasisTable)]   # List of GDB table fields
            nasisFields = [value for value in nasisDict.get(nasisTable)]                          # List of NASIS table fields
            fieldsMissingGDB = list()                                                             # List of NASIS fields missing from FGDB

            # remove OBJECTID from gdbTableFields list
            if 'OBJECTID' in gdbTableFields:
                gdbTableFields.remove('OBJECTID')

            if 'SHAPE' in gdbTableFields:
                gdbTableFields.remove('SHAPE')

            gdbTableFieldsTotal = len(gdbTableFields)  # number of fields in the FGDB table
            nasisFieldsTotal = len(nasisFields)        # number of fields in the NASIS table

            if gdbTableFieldsTotal == nasisFieldsTotal:
                sameNumOfFields = True
            else:
                sameNumOfFields = False

            # Check for NASIS fields missing in the GDB
            for nasisField in nasisFields:

                if not str(nasisField) in gdbTableFields:
                    fieldsMissingGDB.append(nasisField)
                else:
                    gdbTableFields.remove(nasisField)

            """ -----------------------------------------------Report any tabular field problems to user -------------------------------"""
            AddMsgAndPrint("\n=============================================================================================",0)
            tablePrinted = False

            if not len(fieldsMissingGDB) and not len(gdbTableFields):
                AddMsgAndPrint(nasisTable + " Table:",0)
                AddMsgAndPrint("\tAll NASIS report fields match FGDB")
                continue

            # Notify user of missing fields
            if len(fieldsMissingGDB):
                AddMsgAndPrint(nasisTable + " Table:",2)
                AddMsgAndPrint("\tThe following NASIS report fields do NOT exist in the FGDB table:",1)
                AddMsgAndPrint("\t\t" + str(fieldsMissingGDB))
                tablePrinted = True
                discrepancies += len(fieldsMissingGDB)

            if len(gdbTableFields):
                if not tablePrinted:
                    AddMsgAndPrint(nasisTable + " Table:",2)
                AddMsgAndPrint("\n\tThe following FGDB fields do NOT exist in the NASIS report:",1)
                AddMsgAndPrint("\t\t" + str(gdbTableFields))
                discrepancies += len(gdbTableFields)

            del gdbTableFields,nasisFields,gdbTableFieldsTotal,nasisFieldsTotal,fieldsMissingGDB,tablePrinted

        """ ---------------------------------------------------- Report any missing tables to the user ----------------------------------"""
        if len(missingTables):
            AddMsgAndPrint("\n=============================================================================================",0)
            AddMsgAndPrint("The following NASIS report Tables do NOT exist in the FGDB:",2)
            missingTables.sort()
            AddMsgAndPrint("\t" + str(missingTables))
            discrepancies += len(missingTables)

        if len(pedonGDBTables):
            AddMsgAndPrint("\n=============================================================================================",0)
            AddMsgAndPrint("The following FGDB Tables do NOT exist in the NASIS report:",2)
            pedonGDBTables.sort()
            AddMsgAndPrint("\t" + str(pedonGDBTables))
            discrepancies += len(pedonGDBTables)
        else:
            AddMsgAndPrint("\n\n")

        if discrepancies:
            AddMsgAndPrint("\nTotal # of discrepancies between NASIS report and FGDB: " + str(splitThousands(discrepancies)) + "\n\n",2)
        else:
            AddMsgAndPrint("\nThere are no discrepancies between NASIS report and FGDB....CONGRATULATIONS!\n\n",0)

        del missingTables,pedonGDBTables

    except:
        errorMsg()




