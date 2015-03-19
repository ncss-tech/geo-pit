#Calculate acres after Adding a field Column
#6/6/2014
#Alena Stephens
#has one flaw that the acres column doesn't show up in the attribute table unti another tool is processed, or it's removed from the TOC and added back in, or ArcMap 
#is closed and reopened ~ has a tendency to kill ArcMap
#11/20/2014 Trying Refresh Active View
#3/18/2015 Added Try/except to edit and update the acres and it worked!

import arcpy
arcpy.env.overwriteOutput = True

inFC = arcpy.GetParameterAsText (0)
workspace = arcpy.GetParameterAsText (1)

try:

    #Add Field

    arcpy.AddField_management(inFC, "ACRES", "DOUBLE", )

    #Calculate Field

    with arcpy.da.Editor(workspace) as edit:arcpy.CalculateField_management(inFC, "ACRES", '!Shape.area@ACRES!', "PYTHON_9.3", )

except arcpy.ExecuteError:
    print (arcpy.GetMesssages (2))

#Refresh Active View
arcpy.RefreshActiveView()



print "Script Completed"

