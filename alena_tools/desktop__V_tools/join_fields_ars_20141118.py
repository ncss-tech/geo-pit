#Join Field for MUNAME column
#Join mapunit table to soils
#A. Stephens
#11/18/2014
#10/12/2016 updated workspace

import arcpy

arcpy.env.overwriteOutput = True

#inFC = arcpy.GetParameterAsText (0) #Input Feature Class
workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace
intable = arcpy.GetParameterAsText (1) #Input Table

#Add Join
#arcpy.AddJoin_management(inFC, "mukey", intable, "mukey")

#Join muname Field

#arcpy.JoinField_management(inFC, "mukey", intable, "mukey", ["muname"])
#arcpy.JoinField_management(inFC, "MUKEY", intable, "MUKEY", ["muname"])
arcpy.JoinField_management(workspace+'\\'"MUPOLYGON", "MUKEY", intable, "MUKEY", ["muname"])

