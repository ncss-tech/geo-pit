#Find Changes in MUPOLYGON
#09/23/2016
#Alena Stephens
#9/30/2016 Updated by adding Acres Column and dissolving fields feature Class to create a minimized list (convert to a table?)

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

#Add Field

arcpy.AddField_management('lyr', "ACRES", "DOUBLE", )

#Calculate Field

arcpy.CalculateField_management('lyr', "ACRES", '!Shape.area@acres!', "PYTHON", )

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("lyr", out_FGB+'\\'+"MUPOLYGON_MUSYM_VS_ORIGMUSYM")

dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY", "muname", "ORIG_MUSYM"]
#Dissolve Features
arcpy.Dissolve_management ("lyr", out_FGB+'\\'+"MUPOLYGON_MUSYM_VS_ORIGMUSYM_DIS", dissolveFields)


#arcpy.TableToGeodatabase_conversion(["MUPOLYGON_MUSYM_VS_ORIGMUSYM_DIS"], out_FGB)

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")

#Select By Attributes
arcpy.SelectLayerByAttribute_management('lyr', "NEW_SELECTION", " Editor_Field LIKE '%' ")

#Add Field
arcpy.AddField_management('lyr', "ACRES", "DOUBLE", )

#Calculate Field
arcpy.CalculateField_management('lyr', "ACRES", '!Shape.area@acres!', "PYTHON", )

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("lyr", out_FGB+'\\'+"MUPOLYGON__Editor_Field")

dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY", "muname", "ORIG_MUSYM"]
#Dissolve Features
arcpy.Dissolve_management ("lyr", out_FGB+'\\'+"MUPOLYGON__Editor_Field_DIS", dissolveFields)

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")

#Select By Attributes
arcpy.SelectLayerByAttribute_management('lyr', "NEW_SELECTION", " Creator_Field LIKE '%' ")

#Add Field

arcpy.AddField_management('lyr', "ACRES", "DOUBLE", )

#Calculate Field

arcpy.CalculateField_management('lyr', "ACRES", '!Shape.area@acres!', "PYTHON", )

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("lyr", out_FGB+'\\'+"MUPOLYGON_Creator_Editor")

dissolveFields = ["AREASYMBOL", "MUSYM", "MUKEY", "muname", "ORIG_MUSYM"]
#Dissolve Features
arcpy.Dissolve_management ("lyr", out_FGB+'\\'+"MUPOLYGON_Creator_Editor_DIS", dissolveFields)

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")

print "Script Completed"