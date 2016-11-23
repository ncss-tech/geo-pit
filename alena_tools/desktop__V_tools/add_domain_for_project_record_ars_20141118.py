#Add Domain Yes or No to Project Record
#A. Stephens
#11/18/2014
#Updated 10/12/2016
#Updated 11/23/2016 Add MUNAME Field Name


import arcpy

arcpy.env.overwriteOutput = True


#in_workspace = arcpy.GetParameterAsText (0) #Input Project Record File Geodatabase
#inFC = arcpy.GetParameterAsText (1) #Input Project Record Feature Class

workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace

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

#fieldLength = 175

#Add Field
#arcpy.AddField_management(workspace+'\\'"Project_Record", "MUNAME", "TEXT", "", "", fieldLength)


