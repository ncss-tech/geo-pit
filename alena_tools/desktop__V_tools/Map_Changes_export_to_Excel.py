#Map Changes Export to Excel
#A. Stephens
#08/25/2016
#works better when your Default.gdb is NOT C:/Users/YOUR USERNAME/Documents/ArcGIS
#need to add selection MUSYM <> ORIG_MUSYM - so only have to add in MUPOLYGON
#need to add editor field selection? would have to wild card

import arcpy


arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class

out_xls = arcpy.GetParameterAsText (1) # Output Excel Name (add xls extension)

#Dissolve Soils feature class


dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY", "MUNAME", "ORIG_MUSYM"]
#dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY_1", "MUNAME"]
#dissolveFields = ["AREASYMBOL", "MUSYM", "Mapunit Key", "Mapunit Name"]
#dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY", "muname"]

#Dissolve Features
arcpy.Dissolve_management (inFC, "outFCDISSOLVE", dissolveFields)

#Add Acres Field

arcpy.AddField_management("outFCDISSOLVE", "ACRES", "DOUBLE", )

#Calculate Acres Field

arcpy.CalculateField_management("outFCDISSOLVE", "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )

#Sort MUNAME

arcpy.Sort_management ("outFCDISSOLVE", "outFCDISSOLVE_SORT", [["muname", "ASCENDING"]])

#outa_xls = "MLRA_INTERSECT.xls"
#Table to Excel
arcpy.TableToExcel_conversion("outFCDISSOLVE_SORT", out_xls)

arcpy.Statistics_analysis("outFCDISSOLVE_SORT", "STATISTICS", [["ACRES", "SUM"]])

#Delete Feature Classes
#arcpy.Delete_management ("outFCDISSOLVE")
#arcpy.Delete_management ("outFCDISSOLVE_SORT")

print "Script Completed"