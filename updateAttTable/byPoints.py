#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Charles.Ferguson
#
# Created:     12/06/2015
# Copyright:   (c) Charles.Ferguson 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
class ForceExit(Exception):
    pass

def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        arcpy.AddError(theMsg)

    except:
        arcpy.AddError("Unhandled error in errorMsg method")
        pass


import sys, os, arcpy, traceback



inPoints = arcpy.GetParameterAsText(0)
xstsFld = arcpy.GetParameterAsText(1)
updateFld = arcpy.GetParameterAsText(2)
spTbl = arcpy.GetParameterAsText(3)

arcpy.env.addOutputsToMap = False
arcpy.AddMessage('\n')

try:

    inPointsSR = arcpy.Describe(inPoints).spatialReference
    spTblSR = arcpy.Describe(spTbl).spatialReference

    if inPointsSR != spTblSR:
        ForceExit('Update - Points Layer\'s spatial reference does not match the Soil Polygon\'s ')


    #find the workspace of the soil polys
    cp = arcpy.Describe(spTbl).catalogPath
    bName = os.path.dirname(cp)

    if cp.endswith('.shp'):
        aWS = os.path.dirname(cp)

    elif [any(ext) for ext in ('.gdb', '.mdb', '.sde') if ext in os.path.splitext(bName)]:
        aWS =  bName

    else:
        aWS = os.path.dirname(bName)

    #get list of object ids to build query with
    oidSet = [x[0] for x in arcpy.da.SearchCursor(inPoints, "OID@")]

    #get oid field name
    oidFld = arcpy.Describe(inPoints).oidFieldName

    #iterate for every point in the update points layer
    for oid in oidSet:

        #start edit session
        #I think 'with' manager automatically kills the point feature layer as I don't
        #have to explicitly call arcpy.Delete(ftrRow)???
        with arcpy.da.Editor(aWS) as edit:

            #create where clause
            wc = """{0} = {1}""".format(arcpy.AddFieldDelimiters(inPoints, oidFld),oid)

            #search through points in order to have areasymbol and musym to validate against soil polygons
            with arcpy.da.SearchCursor(inPoints, ["areasymbol", xstsFld, updateFld], where_clause = wc) as rows:

                for row in rows:

                    #create a fature layer to use in select by location
                    arcpy.management.MakeFeatureLayer(inPoints, "ftrRow", wc)

                    #find the polygon that intersects point feature layer
                    fields = ["AREASYMBOL", "MUSYM"]
                    with arcpy.da.UpdateCursor(arcpy.management.SelectLayerByLocation(spTbl, "", "ftrRow"), fields) as cursor:
                        for record in cursor:
                            if record[0] + record[1] == rows[0] + row[2]:
                                arcpy.AddWarning("""{0} - the provided {1} already has musym = {2}, not updating the intersecting polygon. {3} = {4} """.format(record[0], row[2], record[1], oidFld, oid))
                            elif not record[0] + record[1] == rows[0] + row[1]:
                                arcpy.AddWarning("""The AREASYMBOL and existing musym for update points {0} - {1} do not match the soil polygon at this location: {2} - {3}. {4} = {5}""".format(row[0], row[1], record[0], record[1], oidFld, oid))
                            elif record[0] + record[1] == rows[0] + row[1]:
                                record[1] = row[2]
                                cursor.updateRow(record)
                                arcpy.AddMessage("""{0} - successfully updated the provided {1} to {2} for the intersecting polygon""".format(record[0], row[1], row[2]))


        del row, rows, record, cursor

    arcpy.management.SelectLayerByAttribute(spTbl, "CLEAR_SELECTION")
    arcpy.AddMessage('\n')

except:
    errorMsg()
