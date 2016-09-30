#-------------------------------------------------------------------------------
# Name:        Extract Pedons from NASIS - update Table Aliases
# Purpose:     This script will update the Table and field aliases for the FGDB whose schema
#              will be used in an XML workspace.  All aliases are coming from the 'MetadataTable'
#              and 'MetadataTableColumn'tables.  They must be present.  This schema reflects the
#              nasis 7.3.3 model.  If everything goes haywire use the 'NASIS_Schema_ODBC.mdb'
#              access database that was created using and ODBC connection to NASIS.
#
#              This script is not intended for distribution.  It is intended for prepartion of the
#              XML workspace
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     9/29/2016
# Last Updated: 9/30/2016
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

# ===================================================================================
def FindField(layer,chkField):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that name; otherwise return ""
    # Set workspace before calling FindField

    try:

        if arcpy.Exists(layer):

            theDesc = arcpy.Describe(layer)
            theFields = theDesc.fields
            theField = theFields[0]

            for theField in theFields:

                # Parses a fully qualified field name into its components (database, owner name, table name, and field name)
                parseList = arcpy.ParseFieldName(theField.name) # (null), (null), (null), MUKEY

                # choose the last component which would be the field name
                theFieldname = parseList.split(",")[len(parseList.split(','))-1].strip()  # MUKEY

                if theFieldname.upper() == chkField.upper():
                    return theField.name

            return False

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return False

    except:
        errorMsg()
        return False

# =========================================================== Main Body =============================================================================
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

if __name__ == '__main__':

    nasisPedons = os.path.dirname(sys.argv[0]) + os.sep + "Nasis_Pedons.gdb"
    aliasTable = nasisPedons + os.sep + "MetadataTable"
    aliasFieldTbl = nasisPedons + os.sep + "MetadataTableColumn"

    if not arcpy.Exists(aliasTable):
        raise ExitError, "\nTable to extract table aliases does NOT exist: Metadata Table"

    if not arcpy.Exists(aliasFieldTbl):
        raise ExitError, "\nTable to extract field aliases does NOT exist: Metadata Table Column"

    arcpy.env.workspace = nasisPedons
    nasisPedonsTables = arcpy.ListTables()

    # manually add the site table b/c ListTables does not recognize it.
    if arcpy.Exists(nasisPedons + os.sep + "site"):
        nasisPedonsTables.append("site")

    textFilePath = os.path.dirname(sys.argv[0]) + os.sep + "NASIS_Pedons_Table_Field_Aliases.txt"

    if os.path.exists(textFilePath):
        os.remove(textFilePath)

    """ --------------------------------------- Create a dictionary of Table Aliases --------------------------------"""
    tblName = FindField(aliasTable,"TablePhysicalName")
    tblAlias = FindField(aliasTable,"TableLabel")
    tblID = FindField(aliasTable,"TableID")

    if not tblName or not tblAlias:
        raise ExitError, "\nNecessary fields are missing from alias table " + tblName + " OR " + tblAlias

    tblAliasDict = dict() # i.e.{u'MetadataDomainMaster': (u'Domain Master Metadata', 4987)}
    with arcpy.da.SearchCursor(aliasTable, [tblName,tblAlias]) as cursor:
        for row in cursor:
            if not tblAliasDict.has_key(row[0]):
                tblAliasDict[row[0]] = (row[1])

    """ --------------------------------------- Create a dictionary of Field Aliases --------------------------------"""
    fldName = FindField(aliasFieldTbl,"ColumnPhysicalName")
    fldAlias = FindField(aliasFieldTbl,"ColumnLabel")

    if not fldName or not fldAlias:
        raise ExitError, "\nNecessary fields are missing from field alias table: " + fldName + " OR " + fldAlias

    fldAliasDict = dict()
    with arcpy.da.SearchCursor(aliasFieldTbl, [fldName,fldAlias]) as cursor:
        for row in cursor:
            if not fldAliasDict.has_key(row[0]):
                fldAliasDict[row[0]] = row[1]

    """ ------------------------------------------ Update Table and Field Aliases ------------------------------------"""
    missingAliases = dict()
    for table in nasisPedonsTables:

        if tblAliasDict.has_key(table):
            arcpy.AlterAliasName(table,tblAliasDict.get(table))
            AddMsgAndPrint("\n" + table + ": " + tblAliasDict.get(table)) # first value represents Alias name
        else:
            AddMsgAndPrint("\n" + table + ": No alias found!")

        i = 1
        fields = arcpy.ListFields(table)
        for field in fields:

            if field.name == "OBJECTID" or field.name == "SHAPE":continue

            if fldAliasDict.has_key(field.name):
                alias = fldAliasDict.get(field.name)
                arcpy.AlterField_management(table,field.name,"#",alias)
                AddMsgAndPrint("\t\t" + str(i) + ". " + field.name + " - " + alias)
                i += 1

            else:
                AddMsgAndPrint("\t\t" + str(i) + ". " + field.name + " - NO ALIAS FOUND")

                if not missingAliases.has_key(table):
                    missingAliases[table] = [field.name]
                else:
                    missingAliases[table].append(field.name)
                i+=1

    if len(missingAliases):
        AddMsgAndPrint("\nSummary of Missing aliases:")
