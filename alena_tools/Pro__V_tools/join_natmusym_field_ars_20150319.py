#Join Field for natmusym column
#Join National Mapunit Symbol table to soils
#A. Stephens
#03/19/2015

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class
intable = arcpy.GetParameterAsText (1) #Input Table


#Join muname Field

arcpy.JoinField_management(inFC, "mukey", intable, "mukey", ["natmusym"])