#Add fields to feature classes
#A. Stephens
#11/18/2014
#12/11/2014 Updated with Calculate Fields
#10/12/2016 Updated Workspace, added acres field and calculation, add fields for Project_Record

import arcpy

arcpy.env.overwriteOutput = True

#inFC = arcpy.GetParameterAsText (0) #Input polygon Feature Class
#sfpinFC = arcpy.GetParameterAsText (1) #Input special feature point feature class
#sflinFC = arcpy.GetParameterAsText (2) # Input special feature line feature class

workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace

fieldLength = 30

#Add Field
arcpy.AddField_management(workspace+'\\'"MUPOLYGON", "ORIG_MUSYM", "TEXT", "", "", fieldLength)

arcpy.AddField_management (workspace+'\\'"FEATPOINT", "ORIG_FEATSYM", "TEXT", "", "", fieldLength)

arcpy.AddField_management (workspace+'\\'"FEATLINE", "ORIG_FEATSYM", "TEXT", "", "", fieldLength)

#Calculate Fields

arcpy.CalculateField_management(workspace+'\\'"MUPOLYGON", "ORIG_MUSYM", '[MUSYM]', "VB" )
arcpy.CalculateField_management(workspace+'\\'"FEATPOINT", "ORIG_FEATSYM", '[FEATSYM]', "VB" )
arcpy.CalculateField_management(workspace+'\\'"FEATLINE", "ORIG_FEATSYM", '[FEATSYM]', "VB" )

#Add Field
arcpy.AddField_management(workspace+'\\'"MUPOLYGON", "ACRES", "DOUBLE", )

#Calculate Field
arcpy.CalculateField_management(workspace+'\\'"MUPOLYGON", "ACRES", '!Shape.area@acres!', "PYTHON", )

#Add Field
arcpy.AddField_management(workspace+'\\'"Project_Record", "ACRES", "DOUBLE", )

#Calculate Field
arcpy.CalculateField_management(workspace+'\\'"Project_Record", "ACRES", '!Shape.area@acres!', "PYTHON", )

#Add Field
arcpy.AddField_management(workspace+'\\'"Project_Record", "MUKEY", "TEXT", "", "", fieldLength)
arcpy.AddField_management(workspace+'\\'"Project_Record", "MUNAME", "TEXT", "", "", "200")
arcpy.AddField_management(workspace+'\\'"Project_Record", "ORIG_MUSYM", "TEXT", "", "", fieldLength)