#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     04/08/2016
# Copyright:   (c) Adolfo.Diaz 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    sampleURL = "https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186"
    pedonGDB = r'G:\ESRI_stuff\python_scripts\SSR10\SSR10\Nasis_Pedons.gdb'

    theReport = urllib.urlopen(sampleURL)

    bFieldNameRecord = False # boolean that marks the starting point of the mapunits listed in the project
    bFirstString = False
    bSecondString = False
    pHorizonList = list()
    i = 0

    tableDict = dict()
    tempTableName = ""

    # iterate through the report until a valid record is found
    for theValue in theReport:

        fieldNames = list()
        theValue = theValue.strip() # remove whitespace characters

        # Iterating through the report
        if bFieldNameRecord:

            tableDict[tempTableName] = (theValue.split(','))
            tempTableName = ""
            bFieldNameRecord = False

        elif theValue.startswith('@begin'):
            bFieldNameRecord = True
            tempTableName = theValue[7:]

        else:
            continue

    arcpy.env.workspace(pedonGDBTables)
    pedonGDBTables = arcpy.ListTables('*')

    for nasisTable in tableDict.keys():

        # Check if NASIS table exists in Pedon FGDB
        if nasisTable not in pedonGDBTables:
            print nasisTable + " does NOT exist in the GDB"
            continue

        tableFields = arcpy.ListFields(pedonGDB + os.sep + nasisTable)





