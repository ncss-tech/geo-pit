#Join Field for SA Region & MLRA owndership column
#Join mapunit table to soils
#A. Stephens
#09/30/22016

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input Feature Class
intable = arcpy.GetParameterAsText (1) #Input Table

#Add Join
#arcpy.AddJoin_management(inFC, "mukey", intable, "mukey")

#Join muname Field

#arcpy.JoinField_management(inFC, "mukey", intable, "mukey", ["muname"])
arcpy.JoinField_management(inFC, "AREASYMBOL", intable, "AREASYMBOL", ["Region", "MLRA_CODE"])