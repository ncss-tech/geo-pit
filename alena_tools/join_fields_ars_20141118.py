#Join Field for MUNAME column
#Join mapunit table to soils
#A. Stephens
#11/18/2014

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class
intable = arcpy.GetParameterAsText (1) #Input Table

#Add Join
#arcpy.AddJoin_management(inFC, "mukey", intable, "mukey")

#Join muname Field

arcpy.JoinField_management(inFC, "mukey", intable, "mukey", ["muname"])