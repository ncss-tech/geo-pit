#Create a Soil Acres Report in Excel
#Dissolve soils, Add Acres, Sort, and add Table to Excel
#A. Stephens
#09/25/2014

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class
#output = arcpy.GetParameterAsText (1) #Output Workspace
out_xls = arcpy.GetParameterAsText (1) # Output Excel Name (add xls extension)

dissolveFields = ["AREASYMBOL", "MUSYM"]
#Dissolve Features
arcpy.Dissolve_management (inFC, "outFCDISSOLVE", dissolveFields)

#Add Field

arcpy.AddField_management("outFCDISSOLVE", "New_MUSYM", "TEXT", )

#Sort

arcpy.Sort_management ("outFCDISSOLVE", "outFCDISSOLVE_SORT", [["AREASYMBOL", "ASCENDING"]])

#outa_xls = "MLRA_INTERSECT.xls"
#Table to Excel
arcpy.TableToExcel_conversion("outFCDISSOLVE_SORT", out_xls)

#Delete Feature Classes
arcpy.Delete_management ("outFCDISSOLVE")
#arcpy.Delete_management ("outFCDISSOLVE_SORT")

print "Script Completed"