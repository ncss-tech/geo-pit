#split soils by MLRA with Acres
#A. Stephens
#09/18/2014
#This tool splits soils by MLRA, calculates acres, and exports to excel spreadsheet.

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0)
output = arcpy.GetParameterAsText (1)
out_xls = arcpy.GetParameterAsText (2)



#INTERSECT
arcpy.Intersect_analysis (inFC, "outFC", "ALL", "","") 

dissolveFields = ["AREASYMBOL", "MUSYM", "MLRARSYM"]
#Dissolve Features
arcpy.Dissolve_management ("outFC", "outFCDISSOLVE", dissolveFields)

#Add Field

arcpy.AddField_management("outFCDISSOLVE", "ACRES", "SHORT", )

#Calculate Field

arcpy.CalculateField_management("outFCDISSOLVE", "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )

#Sort

arcpy.Sort_management ("outFCDISSOLVE", "outFCDISSOLVE_SORT", [["MLRARSYM", "ASCENDING"], ["MUSYM", "ASCENDING"]])


#outa_xls = "MLRA_INTERSECT.xls"
#Table to Excel
arcpy.TableToExcel_conversion("outFCDISSOLVE_SORT", out_xls)

#Delete Fields
#arcpy.DeleteField_management(out_xls, ["OBJECTID", "Shape_Length", "Shape_Area"])

#Delete Feature Classes
arcpy.Delete_management ("outFC")
arcpy.Delete_management ("outFCDISSOLVE")

print "Script Completed"


                        