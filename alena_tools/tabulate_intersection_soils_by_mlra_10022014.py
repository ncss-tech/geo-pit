#Tabulate Intersection, 
#10/02/2014


import arcpy

arcpy.env.overwriteOutput = True

inFCzone = arcpy.GetParameterAsText (0)
inFCsoils = arcpy.GetParameterAsText (1)
out_xls = arcpy.GetParameterAsText (2)

dissolveFields = ["AREASYMBOL", "MUSYM"]
#Dissolve Features
arcpy.Dissolve_management (inFCsoils, "outFCDISSOLVE", dissolveFields)

#Add Field

arcpy.AddField_management("outFCDISSOLVE", "ACRES", "DOUBLE", )

#Calculate Field

arcpy.CalculateField_management("outFCDISSOLVE", "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )

#Tabulate Intersection
arcpy.TabulateIntersection_analysis(inFCzone, "MLRARSYM", "outFCDISSOLVE", "tab_int", 'MUSYM', 'ACRES', '','')

#Table to Excel
arcpy.TableToExcel_conversion("tab_int", out_xls)

#arcpy.Statistics_analysis("tab_int", "STATISTICS", [["ACRES", "SUM"]])
