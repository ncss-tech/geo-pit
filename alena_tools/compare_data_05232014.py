#Compare Data Tool
#A. Stephens
#5/23/2014 Tool can compare 2 soil feature classes. Compare UPDATED SOILS to ORIGINAL SSURGO SOILS. It compares attributes and edited polygons. It reads attributes from the MUSYM column. For best results, the ORIGINAL soil polygon feature class should reside in a File Geodatabase. It can be in a different File Geodatabase than the UPDATED soil polygon feature class. Run this tool in an ArcMap Session.
#9/18/2014 Added the dissolve tool and acres calculation field. 

import arcpy
arcpy.env.overwriteOutput = True
inFC = arcpy.GetParameterAsText(0)
#outFC = arcpy.GetParameterAsText(1)
#outFCDISSOLVE = arcpy.GetParameterAsText(2)


#Union update soils and original soils
arcpy.Union_analysis(inFC, "union_compare_data", "ALL")

#Make Feature Layer from Union soils
arcpy.MakeFeatureLayer_management("union_compare_data", "union_compare_data_lyr")

#Select Layer By Attribute NEW_SELECTION "MUSYM" <> "MUSYM_1"
arcpy.SelectLayerByAttribute_management("union_compare_data_lyr", "NEW_SELECTION", ' "MUSYM" <> "MUSYM_1" ')

#Copy Features
arcpy.CopyFeatures_management ("union_compare_data_lyr", "outFC")

dissolveFields = ["AREASYMBOL", "MUSYM", "MUSYM_1"]
#Dissolve Features
arcpy.Dissolve_management ("outFC", "COMPARE", dissolveFields)


#Delete Features
arcpy.Delete_management("union_compare_data")
arcpy.Delete_management("outFC")

#Add Field

arcpy.AddField_management("COMPARE", "ACRES", "DOUBLE", )

#Calculate Field

arcpy.CalculateField_management("COMPARE", "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )


print "Script Completed"
