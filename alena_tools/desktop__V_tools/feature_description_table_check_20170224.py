#Search Feature Description Table for errors and export table results
#A. Stephens
#02/24/2017

import arcpy
arcpy.env.overwriteOutput = True


#Input featdesc table from RTSD
intable = arcpy.GetParameterAsText (0)
#Input file geodatabase
workspace = arcpy.GetParameterAsText (1)

#Select featdesc LIKE '% Typically__to__%'
#arcpy.SelectLayerByAttribute_management (workspace+'\\'"featdesc", "NEW_SELECTION", " featdesc LIKE '% Typically__to__%' ")
arcpy.SelectLayerByAttribute_management (intable, "NEW_SELECTION", " featdesc LIKE '% Typically__to__%' ")

#Select FEATNAME ~ Add to current Selection
#arcpy.SelectLayerByAttribute_management (workspace+'\\'"featdesc", "ADD_TO_SELECTION", " featname = 'FEATNAME' ")
arcpy.SelectLayerByAttribute_management (intable, "ADD_TO_SELECTION", " featname = 'FEATNAME' ")

#Select FEATDESC ~ Add to current Selection
#arcpy.SelectLayerByAttribute_management (workspace+'\\'"featdesc", "ADD_TO_SELECTION", " featdesc = 'FEATDESC' ")
arcpy.SelectLayerByAttribute_management (intable, "ADD_TO_SELECTION", " featdesc = 'FEATDESC' ")

#Export to New Table
#arcpy.CopyFeatures_management(intable, workspace+'\\'+"Small_W")
#arcpy.CopyFeatures_management(workspace+'\\'"featdesc", workspace+'\\'+"FEATDESC_Issues")
arcpy.CopyFeatures_management(intable, workspace+'\\'+"FEATDESC_Issues")