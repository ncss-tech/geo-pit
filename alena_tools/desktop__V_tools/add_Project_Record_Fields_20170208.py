#Add fields to feature classes
#A. Stephens

#02/08/2017 Updated Workspace, add fields for Project_Record
#helps for queries and making maps for ArcGIS Online


import arcpy

arcpy.env.overwriteOutput = True

#inFC = arcpy.GetParameterAsText (0) #Input polygon Feature Class

workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace
fieldLength = 30
#Add Field
arcpy.AddField_management(workspace+'\\'"Project_Record", "MUKEY", "TEXT", "", "", fieldLength)
arcpy.AddField_management(workspace+'\\'"Project_Record", "MUNAME", "TEXT", "", "", "200")
arcpy.AddField_management(workspace+'\\'"Project_Record", "ORIG_MUSYM", "TEXT", "", "", fieldLength)