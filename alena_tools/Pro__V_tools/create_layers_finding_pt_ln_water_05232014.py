#Create layers for finding Point & Line features in Water Bodies
#2/26/2015


import arcpy

arcpy.env.overwriteOutput = True

#Input Feature Classes
inpolyFC = arcpy.GetParameterAsText(0)
insfptsFC = arcpy.GetParameterAsText(1)
insflnFC = arcpy.GetParameterAsText(2)
workspace = arcpy.GetParameterAsText (3)


#Select all Water bodies
arcpy.SelectLayerByAttribute_management (inpolyFC, "NEW_SELECTION", " MUSYM = 'W' ")
#Make a layer from the feature class
arcpy.MakeFeatureLayer_management (inpolyFC, "soil_w_lyr")

#Select points in Water polygons
arcpy.SelectLayerByLocation_management (insfptsFC, "COMPLETELY_WITHIN", "soil_w_lyr", "", "ADD_TO_SELECTION")

#Write the selected features to a new featureclass
arcpy.CopyFeatures_management(insfptsFC, workspace+'\\'+"SFP_in_W")

#Select Lines in Water polygons
arcpy.SelectLayerByLocation_management (insflnFC, "INTERSECT", "soil_w_lyr", "", "ADD_TO_SELECTION")

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management(insflnFC, workspace+'\\'+"SFL_in_W")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inpolyFC, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insfptsFC, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insflnFC, "CLEAR_SELECTION")
    

    

    

    


