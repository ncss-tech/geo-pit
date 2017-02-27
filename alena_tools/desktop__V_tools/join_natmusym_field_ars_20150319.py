#Join Field for natmusym column
#Join National Mapunit Symbol table to soils
#A. Stephens
#03/19/2015
#Updated 11/28/2016 to join all databases with natmusym

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class
#workspace = arcpy.GetParameterAsText (0) #Input File Folder
intable = arcpy.GetParameterAsText (1) #Input Table


#Join muname Field

arcpy.JoinField_management(inFC, "mukey", intable, "mukey", ["nationalmusym"])
#arcpy.JoinField_management(workspace+'\\'"MUPOLYGON", "mukey", intable, "mukey", ["natmusym"])
#arcpy.JoinField_management(workspace+"MUPOLYGON", "mukey", intable, "mukey", ["natmusym"])