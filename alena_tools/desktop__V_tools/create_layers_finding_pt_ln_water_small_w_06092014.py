#Create layers for Finding Point and Line Features in Water Bodies and Water smaller than 1.4 acres
#A. Stephens
#02/26/2015


import arcpy
arcpy.env.overwriteOutput = True

inpolyFC = arcpy.GetParameterAsText (0) #Input Polygon Feature Class
insfptsFC = arcpy.GetParameterAsText(1) # Input Special Feature Points
insflnFC = arcpy.GetParameterAsText(2) # Input Special Feature Lines
workspace = arcpy.GetParameterAsText (3) # Choose Workspace

#Add Field

arcpy.AddField_management(inpolyFC, "ACRES", "DOUBLE",)

#Calculate Field

arcpy.CalculateField_management(inpolyFC, "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3")

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

#Select Layer By Location SUBSET_SELECTION "Acres" < 1.35
arcpy.SelectLayerByAttribute_management ("soil_w_lyr", "NEW_SELECTION", "ACRES < 1.35")

#Export the selected features to a new featureclass
arcpy.CopyFeatures_management("soil_w_lyr", workspace+'\\'+"Small_W")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inpolyFC, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insfptsFC, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insflnFC, "CLEAR_SELECTION")


print "Script Completed"
