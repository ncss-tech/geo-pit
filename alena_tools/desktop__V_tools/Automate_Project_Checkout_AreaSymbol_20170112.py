#Automate Project Checkout with AreaSymbol
#01/12/2017
#Alena Stephens

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
#IAREA = arcpy.GetParameterAsText (7) #Input AreaSymbol for selection
#indist = arcpy.GetParameter (7)#Input Search Distance 250 Meters, Search Distance, Linear unit, Optional

arcpy.env.workspace = out_folder

inprname = inprname.replace ('-',' ') #replace hyphens and space with underscores
inprname = inprname.replace (',',' ')
inprname =inprname.replace ('  ','_')
inprname =inprname.replace ('__','_')
inprname =inprname.replace (' ','_')

 
#Input Project Name
prjname = inprname+'_'
a = MUPOLYGON
p = FEATPOINT
l = FEATLINE
b = SAPOLYGON

#Input File Geodatabase Name
fdname = out_folder+'\\'+inprname+'.gdb'+'\\'+ prjname+'FD'

#Input Topology Name
inprname_topology = out_folder+'\\'+inprname+'.gdb'+ '\\'+ prjname+'FD'+ '\\' + prjname+'topology'

#Create File Geodatabase
arcpy.CreateFileGDB_management(out_folder, inprname, "CURRENT")

#Create Feature Dataset
arcpy.CreateFeatureDataset_management(out_folder+'\\'+inprname+'.gdb', prjname+'FD', incoord)

#Select By Attributes ~ arcpy.SelectLayerByAttribute_management (inFC, "NEW_SELECTION", " AREASYMBOL = IAREA ")
#arcpy.SelectLayerByAttribute_management ("OK097_R11_20170112_a", "NEW_SELECTION", " AREASYMBOL = 'OK097'")

# AS = IAREA

arcpy.SelectLayerByAttribute_management (inFC, "NEW_SELECTION", " AREASYMBOL = 'OK097'")
#arcpy.SelectLayerByAttribute_management (inFC, "NEW_SELECTION", " AREASYMBOL = AS ")
arcpy.SelectLayerByAttribute_management (insfpt, "NEW_SELECTION", " AREASYMBOL = 'OK097'")
#arcpy.SelectLayerByAttribute_management (insfpt, "NEW_SELECTION", " AREASYMBOL = AS ")
arcpy.SelectLayerByAttribute_management (insfln, "NEW_SELECTION", " AREASYMBOL = 'OK097' ")
#arcpy.SelectLayerByAttribute_management (insfln, "NEW_SELECTION", " AREASYMBOL = AS ")
arcpy.SelectLayerByAttribute_management (inbndy, "NEW_SELECTION", " AREASYMBOL = 'OK097' ")

#Select Layeer By Location ~ Input Soils, ADD_TO_SELECTION, 250 METERS, WITHIN_A_DISTANCE
#arcpy.SelectLayerByLocation_management (inFC, "WITHIN_A_DISTANCE", inbndy, indist,"ADD_TO_SELECTION" )

#Select Layer By Location ~Input SF Points, ADD_TO_SELECTION, 250 METERS, WITHIN_A_DISTANCE
#arcpy.SelectLayerByLocation_management (insfpt, "WITHIN_A_DISTANCE", inbndy, indist,"ADD_TO_SELECTION")

#Select Layer By Location ~ Input SF Lines, ADD_TO_SELECTION, 250 METERS, WITHIN_A_DISTANCE
#arcpy.SelectLayerByLocation_management (insfln, "WITHIN_A_DISTANCE", inbndy, indist,"ADD_TO_SELECTION")

#Feature Class to Feature Class ~ Soils
#arcpy.FeatureClassToFeatureClass_conversion(inFC, fdname, prjname+'a')
arcpy.FeatureClassToFeatureClass_conversion(inFC, fdname, a)
#Feature Class to Feature Class ~ SF Points
#arcpy.FeatureClassToFeatureClass_conversion(insfpt, fdname, prjname+'p')
arcpy.FeatureClassToFeatureClass_conversion(insfpt, fdname, p)
#Feature Class to Feature Class ~ SF Lines
#arcpy.FeatureClassToFeatureClass_conversion(insfln, fdname, prjname+"l")
arcpy.FeatureClassToFeatureClass_conversion(insfln, fdname, l)
#Feature Class to Feature Class ~ Boundary Line
#arcpy.FeatureClassToFeatureClass_conversion(inbndy, fdname, prjname+'b')
arcpy.FeatureClassToFeatureClass_conversion(inbndy, fdname, b)

#Create Topology
arcpy.CreateTopology_management(fdname,  prjname+'topology',".1")

#Add Feature Class To Topology ~ Soils
#arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+'a')
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+a)
#Add Topology Rule ~ Must Not Have Gaps (Poly)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Have Gaps (Area)", fdname+'\\'+prjname+'a')
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Have Gaps (Area)", fdname+'\\'+a)
#Add Topology Rule ~ Must Not Overlap (Poly)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Overlap (Area)", fdname+'\\'+prjname+'a')
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Overlap (Area)", fdname+'\\'+a)
#Add Feature Class To Topology ~ SF Points
#arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+'p')
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+p)
#Add Feature Class To Topology ~ SF Lines
#arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+"l")
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+p)

#Add Topology Rule ~ Must Not Overlap (Line)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Overlap (Line)", fdname+'\\'+prjname+"l")
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Overlap (Line)", fdname+'\\'+l)
#Add Topology Rule ~ Must Be Single Part (Line)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Be Single Part (Line)", fdname+'\\'+prjname+"l")
arcpy.AddRuleToTopology_management (inprname_topology, "Must Be Single Part (Line)", fdname+'\\'+l)
#Add Topology Rule ~ Must Not Self-Overlap (Line)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Self-Overlap (Line)", fdname+'\\'+prjname+"l")
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Self-Overlap (Line)", fdname+'\\'+l)
#Add Topology Rule ~ Must Not Intersect (Line)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Intersect (Line)", fdname+'\\'+prjname+"l")
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Intersect (Line)", fdname+'\\'+l)
#Add Topology Rule ~ Must Not Have Pseudo Nodes (Line)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Have Pseudo-Nodes (Line)", fdname+'\\'+prjname+"l")
arcpy.AddRuleToTopology_management (inprname_topology, "Must Not Have Pseudo-Nodes (Line)", fdname+'\\'+l)
#Add Topology Rule ~ Must Be Disjoint (Point)
#arcpy.AddRuleToTopology_management (inprname_topology, "Must Be Disjoint (Point)", fdname+'\\'+prjname+'p')
arcpy.AddRuleToTopology_management (inprname_topology, "Must Be Disjoint (Point)", fdname+'\\'+l)

#Add Feature Class to Topology ~ Boundary
#arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+prjname+'b')
arcpy.AddFeatureClassToTopology_management(inprname_topology, fdname+'\\'+b)

#Validate Topology
arcpy.ValidateTopology_management(inprname_topology, "FULL_EXTENT")

#Need to add if/else statements
#Add Field ~ Soil Polygons ~ ORIG_MUSYM, TEXT, (Alias) Original Musym, Check Field is Nullable
#arcpy.AddField_management(fdname+'\\'+prjname+'a', "ORIG_MUSYM", "TEXT", "10", "", "", "ORIG_MUSYM", "NULLABLE")
arcpy.AddField_management(fdname+'\\'+a, "ORIG_MUSYM", "TEXT", "10", "", "", "ORIG_MUSYM", "NULLABLE")

#Calculate Field ~ Soil Polygons ~ _a, ORIG_MUSYM, [MUSYM], VB
#arcpy.CalculateField_management(fdname+'\\'+prjname+'a', "ORIG_MUSYM", '[MUSYM]', "VB")
arcpy.CalculateField_management(fdname+'\\'+a, "ORIG_MUSYM", '[MUSYM]', "VB")

#Add Field ~ SF Points ~  _p, ORIG_FEATSYM, TEXT, (Alias) Original FEATSYM, Check Field is Nullable
#arcpy.AddField_management(fdname+'\\'+prjname+'p', "ORIG_FEATSYM", "TEXT", "10","", "", "ORIG_FEATSYM", "NULLABLE")
arcpy.AddField_management(fdname+'\\'+p, "ORIG_FEATSYM", "TEXT", "10","", "", "ORIG_FEATSYM", "NULLABLE")

#Calculate Field ~ SF Points ~ _p, ORIG_FEATSYM, [FEATSYM], VB
#arcpy.CalculateField_management(fdname+'\\'+prjname+'p', "ORIG_FEATSYM", '[FEATSYM]', "VB")
arcpy.CalculateField_management(fdname+'\\'+p, "ORIG_FEATSYM", '[FEATSYM]', "VB")

#Add Field ~ SF Lines ~  _l, ORIG_FEATSYM, TEXT, (Alias) Original FEATSYM, Check Field is Nullable
#arcpy.AddField_management(fdname+'\\'+prjname+"l", "ORIG_FEATSYM", "TEXT", "10","", "", "ORIG_FEATSYM", "NULLABLE" )
arcpy.AddField_management(fdname+'\\'+l, "ORIG_FEATSYM", "TEXT", "10","", "", "ORIG_FEATSYM", "NULLABLE" )

#Calculate Field ~ SF Lines ~ _l, ORIG_FEATSYM, [FEATSYM], VB
#arcpy.CalculateField_management(fdname+'\\'+prjname+"l", "ORIG_FEATSYM", '[FEATSYM]', "VB")
arcpy.CalculateField_management(fdname+'\\'+l, "ORIG_FEATSYM", '[FEATSYM]', "VB")


#Add Field and Calculate Acres
#Add Field
#arcpy.AddField_management(fdname+'\\'+prjname+'a', "ACRES", "DOUBLE",)
arcpy.AddField_management(fdname+'\\'+a, "ACRES", "DOUBLE",)
#Calculate Field
#arcpy.CalculateField_management(fdname+'\\'+prjname+'a', "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3")
arcpy.CalculateField_management(fdname+'\\'+a, "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3")

#Clear Selected Features
arcpy.SelectLayerByAttribute_management (inFC, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insfpt, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (insfln, "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management (inbndy, "CLEAR_SELECTION")

print "Script Completed"


