#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     04/08/2016
# Last Modified: 9/27/2016
# Copyright:   (c) Adolfo.Diaz 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

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
            arcpy.AddError("\n" + msg)

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

# =========================================================== Main Body ==================================================
# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    try:

        sampleURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186"
        pedonGDB =  os.path.dirname(sys.argv[0]) + os.sep + 'Nasis_Pedons.gdb'

        theReport = urllib.urlopen(sampleURL)

        bFieldNameRecord = False # boolean that marks the starting point of the mapunits listed in the project
        bFirstString = False
        bSecondString = False
        pHorizonList = list()
        i = 0

        nasisDict = dict()
        tempTableName = ""

        # iterate through the report until a valid record is found
        for theValue in theReport:

            fieldNames = list()
            theValue = theValue.strip() # remove whitespace characters

            # Iterating through the report
            if bFieldNameRecord:

                nasisDict[tempTableName] = (theValue.split(','))
                tempTableName = ""
                bFieldNameRecord = False

            elif theValue.startswith('@begin'):
                bFieldNameRecord = True
                tempTableName = theValue[7:]

            else:
                continue

        arcpy.env.workspace = pedonGDB
        pedonGDBTables = arcpy.ListTables('*')
        missingTables = list()

        for nasisTable in nasisDict.keys():

            # Check if NASIS table exists in Pedon FGDB
            if nasisTable not in pedonGDBTables:
                missingTables.append(nasisTable)
                continue

            gdbTableFields = [f.name for f in arcpy.ListFields(pedonGDB + os.sep + nasisTable)]   # List of GDB table fields
            nasisFields = [value for value in nasisDict.get(nasisTable)]                          # List of NASIS table fields

            # remove OBJECTID from gdbTableFields list
            if 'OBJECTID' in gdbTableFields:
                gdbTableFields.remove('OBJECTID')

            gdbTableFieldsTotal = len(gdbTableFields)
            nasisFieldsTotal = len(nasisFields)

            if gdbTableFieldsTotal == nasisFieldsTotal:
                sameNumOfFields = True
            else:
                sameNumOfFields = False

            # Check for NASIS fields missing in the GDB
            fieldsMissingGDB = list()
            for nasisField in nasisDict.get(nasisTable):

                if not str(nasisField) in gdbTableFields:
                    fieldsMissingGDB.append(nasisField)
                else:
                    gdbTableFields.remove(nasisField)

            # Notify user of missing fields
            if len(fieldsMissingGDB):
                print "\n============================================================================================="
                print nasisTable + " Table:"
                print "\tThe following NASIS report fields do NOT exist in the GDB"
                print "\t\t" + str(fieldsMissingGDB)

            if len(gdbTableFields):
                print "\n\tThese GDB fields were not present in the NASIS report but exist in the GDB:"
                print "\t\t" + str(gdbTableFields)

            #del gdbTableFields, fieldsMissingGDB

        if len(missingTables):
            print "\nThe following Tables are missing from the GDB:"
            print "\t" + str(missingTables)

    except:
        errorMsg()




