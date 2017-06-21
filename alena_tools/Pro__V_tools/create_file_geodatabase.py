#Create File Geodatabase
#06/21/2017
#A. Stephens


import arcpy
import os
from arcpy import env

arcpy.env.overwriteOutput = True

out_folder = arcpy.GetParameterAsText (0)#Output Folder, Workspace, Required
inprname = arcpy.GetParameterAsText (1)#Input Project Name, String, Required
incoord = arcpy.GetParameterAsText (2)#Input Coordinate System, Spatial Reference
inFC = arcpy.GetParameterAsText (3) #Input soil polygons, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
insfpt = arcpy.GetParameterAsText (4)#Input special feature points, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
insfln = arcpy.GetParameterAsText (5)#Input special feature lines, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required
inbndy = arcpy.GetParameterAsText (6)#Input project booundary, Feature Layer or Raster Cataglo Layer or Mosaic Layer, Required

#Input Project Name
prjname = inprname+'_'

#Input File Geodatabase Name
fdname = out_folder+'\\'+inprname+'.gdb'+'\\'+ prjname+'FD'

#Create File Geodatabase - CreateFileGDB_management (out_folder_path, out_name)

arcpy.CreateFileGDB_management(out_folder, inprname, "10.0")

#Create Feature Dataset
arcpy.CreateFeatureDataset_management(out_folder+'\\'+inprname+'.gdb', prjname+'FD', incoord)

#Feature Class to Feature Class ~ Soils
arcpy.FeatureClassToFeatureClass_conversion(inFC, fdname, prjname+'a')

#Feature Class to Feature Class ~ SF Points
arcpy.FeatureClassToFeatureClass_conversion(insfpt, fdname, prjname+'p')
#Feature Class to Feature Class ~ SF Lines
arcpy.FeatureClassToFeatureClass_conversion(insfln, fdname, prjname+"l")
#Feature Class to Feature Class ~ Boundary Line
#arcpy.FeatureClassToFeatureClass_conversion(inbndy, fdname, prjname+"b")



#print "Script Completed"
print ("Script Completed")