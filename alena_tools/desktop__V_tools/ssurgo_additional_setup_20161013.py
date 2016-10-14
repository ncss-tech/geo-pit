#Add fields to feature classes
#A. Stephens
#11/18/2014
#12/11/2014 Updated with Calculate Fields
#10/12/2016 Updated Workspace, added acres field and calculation, add fields for Project_Record

import arcpy

arcpy.env.overwriteOutput = True

#inFC = arcpy.GetParameterAsText (0) #Input polygon Feature Class
#sfpinFC = arcpy.GetParameterAsText (1) #Input special feature point feature class
#sflinFC = arcpy.GetParameterAsText (2) # Input special feature line feature class

workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace

fieldLength = 30

#Add Field
arcpy.AddField_management(workspace+'\\'"MUPOLYGON", "ORIG_MUSYM", "TEXT", "", "", fieldLength)

arcpy.AddField_management (workspace+'\\'"FEATPOINT", "ORIG_FEATSYM", "TEXT", "", "", fieldLength)

arcpy.AddField_management (workspace+'\\'"FEATLINE", "ORIG_FEATSYM", "TEXT", "", "", fieldLength)

#Calculate Fields

arcpy.CalculateField_management(workspace+'\\'"MUPOLYGON", "ORIG_MUSYM", '[MUSYM]', "VB" )
arcpy.CalculateField_management(workspace+'\\'"FEATPOINT", "ORIG_FEATSYM", '[FEATSYM]', "VB" )
arcpy.CalculateField_management(workspace+'\\'"FEATLINE", "ORIG_FEATSYM", '[FEATSYM]', "VB" )

#Add Field
arcpy.AddField_management(workspace+'\\'"MUPOLYGON", "ACRES", "DOUBLE", )

#Calculate Field
arcpy.CalculateField_management(workspace+'\\'"MUPOLYGON", "ACRES", '!Shape.area@acres!', "PYTHON", )

#Add Field
arcpy.AddField_management(workspace+'\\'"Project_Record", "ACRES", "DOUBLE", )

#Calculate Field
arcpy.CalculateField_management(workspace+'\\'"Project_Record", "ACRES", '!Shape.area@acres!', "PYTHON", )

#Add Field
arcpy.AddField_management(workspace+'\\'"Project_Record", "MUKEY", "TEXT", "", "", fieldLength)
arcpy.AddField_management(workspace+'\\'"Project_Record", "MUNAME", "TEXT", "", "", "300")
arcpy.AddField_management(workspace+'\\'"Project_Record", "ORIG_MUSYM", "TEXT", "", "", fieldLength)

#Add Attribute Index
#10/12/2016

#arcpy.AddIndex_management(inFC, "AREASYMBOL;MUSYM;MUKEY", "M_Att", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "MUSYM", "MUSYM", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "MUKEY", "MUKEY", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"MUPOLYGON", "MUNAME", "MUNAME", "UNIQUE", "ASCENDING")

arcpy.AddIndex_management(workspace+'\\'"FEATPOINT", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATPOINT", "FEATSYM", "FEATSYM", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATPOINT", "FEATKEY", "FEATKEY", "UNIQUE", "ASCENDING")

arcpy.AddIndex_management(workspace+'\\'"FEATLINE", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATLINE", "FEATSYM", "FEATSYM", "UNIQUE", "ASCENDING")
arcpy.AddIndex_management(workspace+'\\'"FEATLINE", "FEATKEY", "FEATKEY", "UNIQUE", "ASCENDING")

arcpy.AddIndex_management(workspace+'\\'"SAPOLYGON", "AREASYMBOL", "AREASYMBOL", "UNIQUE", "ASCENDING")

doname = "RECERT_NEEDED" #Domain Name 

#Create Domain

#arcpy.CreateDomain_management(in_workspace, doname, "No or Yes", "TEXT", "CODED")
arcpy.CreateDomain_management(workspace, doname, "No or Yes", "TEXT", "CODED")

# Add Coded Value to Domain

#arcpy.AddCodedValueToDomain_management (in_workspace, doname, "Yes", "Yes")
arcpy.AddCodedValueToDomain_management (workspace, doname, "Yes", "Yes")

#arcpy.AddCodedValueToDomain_management (in_workspace, doname, "No", "No")
arcpy.AddCodedValueToDomain_management (workspace, doname, "No", "No")

#Assign Domain To Field

#arcpy.AssignDomainToField_management (inFC, "RECERT_NEEDED", doname)
arcpy.AssignDomainToField_management (workspace+'\\'"Project_Record", "RECERT_NEEDED", doname)

arcpy.EnableEditorTracking_management(workspace+'\\'"MUPOLYGON","Creator_Field","Creation_Date_Field", "Editor_Field", "Last_Edit_Date_Field","ADD_FIELDS", "UTC")
arcpy.EnableEditorTracking_management(workspace+'\\'"FEATPOINT","Creator_Field","Creation_Date_Field", "Editor_Field", "Last_Edit_Date_Field","ADD_FIELDS", "UTC")
arcpy.EnableEditorTracking_management(workspace+'\\'"FEATLINE","Creator_Field","Creation_Date_Field", "Editor_Field", "Last_Edit_Date_Field","ADD_FIELDS", "UTC")


print "Script Completed"