#
#09/23/2016
#Alena Stephens

import arcpy
import os

arcpy.env.overwriteOutput = True

#Input MUPOLGYON
inFC = arcpy.GetParameterAsText (0) #Input soil polygons, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
#Input File Geodatabase
out_FGB = arcpy.GetParameterAsText (1)#Output Folder, Workspace, Required


#Make a feature from the feature class
arcpy.MakeFeatureLayer_management(inFC, 'lyr')

#Select By Attributes MUSYM <> ORIG_MUSYM
arcpy.SelectLayerByAttribute_management('lyr', "NEW_SELECTION", " MUSYM <> ORIG_MUSYM ")

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("lyr", out_FGB+'\\'+"MUPOLYGON_MUSYM_VS_ORIGMUSYM")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")

#Select By Attributes
arcpy.SelectLayerByAttribute_management('lyr', "NEW_SELECTION", " Editor_Field LIKE '%' ")

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("lyr", out_FGB+'\\'+"MUPOLYGON__Editor_Field")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")

#Select By Attributes
arcpy.SelectLayerByAttribute_management('lyr', "NEW_SELECTION", " Creator_Field LIKE '%' ")

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("lyr", out_FGB+'\\'+"MUPOLYGON_Creator_Editor")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")

print "Script Completed"