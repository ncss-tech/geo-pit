#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     19/08/2016
# Copyright:   (c) Adolfo.Diaz 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def updateAlias(tableToUpdate,lookUP):

    aliasTable ="Field_Aliases"
    pass

import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    nasisPedons = r'G:\ESRI_stuff\python_scripts\SSR10\SSR10\Nasis_Pedons.gdb'
    aliasTable = nasisPedons + os.sep + "Field_Aliases"

    arcpy.env.workspace = nasisPedons
    nasisPedonsTables = arcpy.ListTables()

    aliasDict = dict()
    with arcpy.da.SearchCursor(aliasTable, ["Physical_Name","Label"]) as cursor:
        for row in cursor:
            if not aliasDict.has_key(row[0]):
                aliasDict[row[0]] = row[1]

    missingAliases = dict()

    for table in nasisPedonsTables:

        print "\nProcessing: " + table

        fields = arcpy.ListFields(table)
        for field in fields:

            if field.name == "OBJECTID":continue

            if aliasDict.has_key(field.name):
                alias = aliasDict.get(field.name)
                arcpy.AlterField_management(table,field.name,"#",alias)
                print "\t" + field.name + " - " + alias

            else:
                print "\t" + field.name + " - NO ALIAS"

                if not missingAliases.has_key(table):
                    missingAliases[table] = [field.name]
                else:
                    missingAliases[table].append(field.name)
