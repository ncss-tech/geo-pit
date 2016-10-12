#Add Attribute Index
#10/12/2016
#A. Stephens
#add input as feature dataset in file geodatabase, add other feature classes, and add MUNAME

import arcpy
arcpy.env.overwriteOutput = True

#inFC = arcpy.GetParameterAsText (0)
#Input Feature Dataset from File Geodatabase
workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace

#arcpy.AddIndex_management(inFC, "AREASYMBOL;MUSYM;MUKEY", "M_Att", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "MUSYM", "MUSYM", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "MUKEY", "MUKEY", "UNIQUE", "ASCENDING")
#arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "MUNAME", "MUNAME", "UNIQUE", "ASCENDING")

arcpy.AddIndex_management(workspace+'\\'"FEATPOINT", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATPOINT", "FEATSYM", "FEATSYM", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATPOINT", "FEATKEY", "FEATKEY", "UNIQUE", "ASCENDING")

arcpy.AddIndex_management(workspace+'\\'"FEATLINE", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATLINE", "FEATSYM", "FEATSYM", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATLINE", "FEATKEY", "FEATKEY", "UNIQUE", "ASCENDING")

arcpy.AddIndex_management(workspace+'\\'"SAPOLYGON", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")


print "Script Completed"