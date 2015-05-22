#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      charles.ferguson
#
# Created:     20/05/2015
# Copyright:   (c) charles.ferguson 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        arcpy.AddError(theMsg)
    except:
        arcpy.AddError("Unhandled error in errorMsg method")
        pass


import sys, os, traceback, arcpy

changeTblParam = arcpy.GetParameterAsText(0)
areaParam = arcpy.GetParameterAsText(1)
xstFldParam = arcpy.GetParameterAsText(2)
newFldParam = arcpy.GetParameterAsText(3)
musymParam = arcpy.GetParameterAsText(4)
spTblParam = arcpy.GetParameterAsText(5)

updateDict = {}

musymLst = str(musymParam).split(';')

arcpy.AddMessage('\n\n')

try:

    for musym in musymLst:
        wc = 'AREASYMBOL = ' "'" + areaParam + "' AND MUSYM = '" + musym + "'"
        #arcpy.AddMessage(wc)
        with arcpy.da.SearchCursor(changeTblParam, newFldParam, where_clause = wc) as rows:
            for row in rows:
                updateDict[musym] = str(row[0])
        del row, rows, wc

    #for k,v in updateDict.iteritems():
        #arcpy.AddMessage(k + v)

    for key in updateDict:
        upVal = updateDict.get(key)
        if len(upVal) > 6:
            arcpy.AddWarning('Illegal value for ' + key + ' greater than 6 characters (' + upVal + ')')
        elif upVal == 'None':
            arcpy.AddWarning('No update value specified for ' + key)
        else:
            n=0
            wc = '"AREASYMBOL" = ' "'" + areaParam + "' AND \"MUSYM\" = '" + key + "'"
            with arcpy.da.UpdateCursor(spTblParam, "MUSYM", where_clause=wc) as rows:
                for row in rows:
                    row[0] = str(upVal)
                    rows.updateRow(row)
                    n=n+1
                if n > 0:
                    arcpy.AddMessage('Successfully updated ' + key + ' to ' + upVal +  ", " + str(n) + " occurances")

            try:
                del row, rows
            except:
               arcpy.AddMessage('No rows were found for ' + key)

    arcpy.AddMessage('\n\n')

except:
    errorMsg()




