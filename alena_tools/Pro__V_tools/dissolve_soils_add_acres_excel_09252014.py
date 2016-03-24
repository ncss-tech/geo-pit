#Create a Soil Acres Report in Excel
#Dissolve soils, Add Acres, Sort, and add Table to Excel
#A. Stephens
#09/25/2014

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class
#output = arcpy.GetParameterAsText (1) #Output Workspace
out_xls = arcpy.GetParameterAsText (1) # Output Excel Name (add xls extension)

dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY"]
#Dissolve Features
arcpy.Dissolve_management (inFC, "outFCDISSOLVE", dissolveFields)

#Add Field

arcpy.AddField_management("outFCDISSOLVE", "ACRES", "DOUBLE", )

#Calculate Field

arcpy.CalculateField_management("outFCDISSOLVE", "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )

#Sort

arcpy.Sort_management ("outFCDISSOLVE", "outFCDISSOLVE_SORT", [["MUSYM", "ASCENDING"]])

#outa_xls = "MLRA_INTERSECT.xls"
#Table to Excel
arcpy.TableToExcel_conversion("outFCDISSOLVE_SORT", out_xls)

arcpy.Statistics_analysis("outFCDISSOLVE_SORT", "STATISTICS", [["ACRES", "SUM"]])

#Delete Feature Classes
arcpy.Delete_management ("outFCDISSOLVE")
#arcpy.Delete_management ("outFCDISSOLVE_SORT")

print "Script Completed"