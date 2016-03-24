#Add fields to feature classes
#A. Stephens
#11/18/2014

#12/11/2014 Updated with Calculate Fields

import arcpy

arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0) #Input polygon Feature Class
sfpinFC = arcpy.GetParameterAsText (1) #Input special feature point feature class
sflinFC = arcpy.GetParameterAsText (2) # Input special feature line feature class


fieldLength = 30

#Add Field
arcpy.AddField_management(inFC, "ORIG_MUSYM", "TEXT", "", "", fieldLength)

arcpy.AddField_management (sfpinFC, "ORIG_FEATSYM", "TEXT", "", "", fieldLength)

arcpy.AddField_management (sflinFC, "ORIG_FEATSYM", "TEXT", "", "", fieldLength)

#Calculate Fields

arcpy.CalculateField_management(inFC, "ORIG_MUSYM", '[MUSYM]', "VB" )
arcpy.CalculateField_management(sfpinFC, "ORIG_FEATSYM", '[FEATSYM]', "VB" )
arcpy.CalculateField_management(sflinFC, "ORIG_FEATSYM", '[FEATSYM]', "VB" )