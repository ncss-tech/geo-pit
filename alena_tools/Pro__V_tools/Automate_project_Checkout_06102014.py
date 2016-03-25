#Automate Project Checkout
#02/27/2015
#Alena Stephens
#works best if the spatial data resides in TOC

import arcpy
import os

arcpy.env.overwriteOutput = True

out_folder = arcpy.GetParameterAsText (0)#Output Folder, Workspace, Required
inprname = arcpy.GetParameterAsText (1)#Input Project Name, String, Required
incoord = arcpy.GetParameterAsText (2)#Input Coordinate System, Spatial Reference
inFC = arcpy.GetParameterAsText (3) #Input soil polygons, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
insfpt = arcpy.GetParameterAsText (4)#Input special feature points, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
insfln = arcpy.GetParameterAsText (5)#Input special feature lines, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
inbndy = arcpy.GetParameterAsText (6)#Input project booundary, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
indist = arcpy.GetParameter (7)#Input Search Distance 250 Meters, Search Distance, Linear unit, Optional

arcpy.env.workspace = out_folder

inprname = inprname.replace ('-',' ') #replace hyphens and space with underscores
inprname = inprname.replace (',',' ')
inprname =inprname.replace ('  ','_')
inprname =inprname.replace ('__','_')
inprname =inprname.replace (' ','_')

 
#Input Project Name
prjname = inprname+'_'

#Input File Geodatabase Name
fdname = out_folder+'\\'+inprname+'.gdb'+'\\'+ prjname+'FD'

#Input Topology Name
inprname_topology = out_folder+'\\'+inprname+'.gdb'+ '\\'+ prjname+'FD'+ '\\' + prjname+'topology'

#Create File Geodatabase
arcpy.CreateFileGDB_management(out_folder, inprname, "10.0")

#Create Feature Dataset
arcpy.CreateFeatureDataset_management(out_folder+'\\'+inprname+'.gdb', prjname+'FD', incoord)

#Select Layeer By Location ~ Input Soils, ADD_TO_SELECTION, 250 METERS, WITHIN_A_DISTANCE
arcpy.SelectLayerByLocation_management (inFC, "WITHIN_A_DISTANCE", inbndy, indist,"ADD_TO_SELECTION" )

#Select Layer By Location ~Input SF Points, ADD_TO_SELECTION, 250 METERS, WITHIN_A_DISTANCE
arcpy.SelectLayerByLocation_management (insfpt, "WITHIN_A_DISTANCE", inbndy, indist,"ADD_TO_SELECTION")

#Select Layer By Location ~ Input SF Lines, ADD_TO_SELECTION, 250 METERS, WITHIN_A_DISTANCE
arcpy.SelectLayerByLocation_management (insfln, "WITHIN_A_DISTANCE", inbndy, indist,"ADD_TO_SELECTION")

#Feature Class to Feature Class ~ Soils
arcpy.FeatureClassToFeatureClass_conversion(inFC, fdname, prjname+'a')

#Feature Class to Feature Class ~ SF Points
arcpy.FeatureClassToFeatureClass_conversion(insfpt, fdname, prjname+'p')
#Feature Class to Feature Class ~ SF Lines
arcpy.FeatureClassToFeatureClass_conversion(insfln, fdname, prjname+"l")
#Feature Class to Feature Class ~ Boundary Line
arcpy.FeatureClassToFeatureClass_conversion(inbndy, fdname, prjname+"b")
#Create Topology
arcpy.CreateTopology_management(fdname,  prjname+'topology',".01")

#Add Feature Class To Topology ~ Soils
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+'a')
#Add Topology Rule ~ Must Not Have Gaps (Poly)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Have Gaps (Area)", fdname+'\\'+prjname+'a')
#Add Topology Rule ~ Must Not Overlap (Poly)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Overlap (Area)", fdname+'\\'+prjname+'a')
#Add Feature Class To Topology ~ SF Points
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+'p')
#Add Feature Class To Topology ~ SF Lines
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+"l")

#Add Topology Rule ~ Must Not Overlap (Line)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Overlap (Line)", fdname+'\\'+prjname+"l")
#Add Topology Rule ~ Must Be Single Part (Line)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Be Single Part (Line)", fdname+'\\'+prjname+"l")
#Add Topology Rule ~ Must Not Self-Overlap (Line)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Self-Overlap (Line)", fdname+'\\'+prjname+"l")
#Add Topology Rule ~ Must Not Intersect (Line)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Intersect (Line)", fdname+'\\'+prjname+"l")
#Add Topology Rule ~ Must Not Have Pseudo Nodes (Line)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Have Pseudo-Nodes (Line)", fdname+'\\'+prjname+"l")
#Add Topology Rule ~ Must Be Disjoint (Point)
arcpy.AddRuleToTopology_management (inprname_topology, "Must Be Disjoint (Point)", fdname+'\\'+prjname+'p')

#Add Feature Class to Topology ~ Boundary
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+"b")

#Validate Topology
arcpy.ValidateTopology_management(inprname_topology, "FULL_EXTENT")

#Add Field ~ Soil Polygons ~ ORIG_MUSYM, TEXT, (Alias) Original Musym, Check Field is Nullable
arcpy.AddField_management(fdname+'\\'+prjname+'a', "ORIG_MUSYM", "TEXT", "10", "", "", "Original_Musym", "NULLABLE")

#Calculate Field ~ Soil Polygons ~ _a, ORIG_MUSYM, [MUSYM], VB
arcpy.CalculateField_management(fdname+'\\'+prjname+'a', "ORIG_MUSYM", '[MUSYM]', "VB")

#Add Field ~ SF Points ~  _p, ORIG_FEATSYM, TEXT, (Alias) Original FEATSYM, Check Field is Nullable
arcpy.AddField_management(fdname+'\\'+prjname+'p', "ORIG_FEATSYM", "TEXT", "10","", "", "Original_FEATSYM", "NULLABLE")

#Calculate Field ~ SF Points ~ _p, ORIG_FEATSYM, [FEATSYM], VB
arcpy.CalculateField_management(fdname+'\\'+prjname+'p', "ORIG_FEATSYM", '[FEATSYM]', "VB")

#Add Field ~ SF Lines ~  _l, ORIG_FEATSYM, TEXT, (Alias) Original FEATSYM, Check Field is Nullable
arcpy.AddField_management(fdname+'\\'+prjname+"l", "ORIG_FEATSYM", "TEXT", "10","", "", "Original_FEATSYM", "NULLABLE" )

#Calculate Field ~ SF Lines ~ _l, ORIG_FEATSYM, [FEATSYM], VB
arcpy.CalculateField_management(fdname+'\\'+prjname+"l", "ORIG_FEATSYM", '[FEATSYM]', "VB")


#Add Field and Calculate Acres
#Add Field
arcpy.AddField_management(fdname+'\\'+prjname+'a', "ACRES", "DOUBLE",)
#Calculate Field
arcpy.CalculateField_management(fdname+'\\'+prjname+'a', "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insfpt, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insfln, "CLEAR_SELECTION")

#print "Script Completed"
print ("Script Completed")


