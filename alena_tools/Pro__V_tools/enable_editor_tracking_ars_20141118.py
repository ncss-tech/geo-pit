#Enable Editor Tracking
#Automatically add and enable the fields necesssary to track spatial edits in the file geodatabase.
#A. Stephens
#11/18/2014
#Works 3/19/2015

import arcpy, os

arcpy.env.overwriteOutput = True

#inFC = arcpy.GetParameterAsText (0) #Input Feature Class

#arcpy.EnableEditorTracking_management(inFC, "Creator_Field", "Creation_Date_Field", "Editor_Field", "Last_Edit_Date_Field", "ADD_FIELDS", "UTC")

# Set the workspace
workspace = arcpy.GetParameterAsText(0)

arcpy.env.workspace = workspace


# Get all the stand alone tables and feature classes
#dataList = arcpy.ListTables() + arcpy.ListFeatureClasses()
dataList = arcpy.ListFeatureClasses()

# For feature datasets get all of the featureclasses
# from the list and add them to the master list
for dataset in arcpy.ListDatasets("", "Feature"):
    arcpy.env.workspace = os.path.join(workspace, dataset)
    dataList += arcpy.ListFeatureClasses() + arcpy.ListDatasets()


# Execute enable editor tracking
for dataset in dataList:
    print 'Enabling tracking on ' + dataset
    arcpy.EnableEditorTracking_management(dataset,"Creator_Field","Creation_Date_Field", "Editor_Field", "Last_Edit_Date_Field","ADD_FIELDS", "UTC")
print 'Enabling complete'
