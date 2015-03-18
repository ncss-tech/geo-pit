#Project Record to Excel Table
#A. Stephens
#11/3/2014

import arcpy
arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText(0) #Input Project Record Feature Class from RTSD_Region File Geodatabase
out_xls = arcpy.GetParameterAsText (1) #Output Project Records into Excel table


dissolveFields = ["AREASYMBOL", "MUSYM", "PROJECT_NAME", "STATUS", "RECERT_NEEDED"]
#Dissolve Features
arcpy.Dissolve_management (inFC, "outFCDISSOLVE", dissolveFields)

#Add Field

arcpy.AddField_management("outFCDISSOLVE", "ACRES", "DOUBLE", )

#Calculate Field

arcpy.CalculateField_management("outFCDISSOLVE", "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )

#Sort

arcpy.Sort_management ("outFCDISSOLVE", "outFCDISSOLVE_SORT", [["Project_Name", "ASCENDING"]])

#Table to Excel
arcpy.TableToExcel_conversion("outFCDISSOLVE_SORT", out_xls)