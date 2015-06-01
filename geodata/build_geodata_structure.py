#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      Charles.Ferguson
#
# Created:     01/06/2015
# Copyright:   (c) Charles.Ferguson 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        arcpy.AddError(theMsg)
    except:
        arcpy.AddError("Unhandled error in errorMsg method")
        pass


import sys, os, traceback, arcpy


geoDataDirs = ['AIR_QUALITY', 'CADASTRAL', 'CENSUS', 'CLIMATE', 'CLU_Tract_Maps', 'COMMON_LAND_UNIT', 'CONSERVATION_PRACTICES', 'CULTURAL_RESOURCES', 'DISASTER_EVENTS', 'ECOLOGICAL', 'ELEVATION', 'ENDANGERED_HABITAT', 'ENVIRONMENTAL_EASEMENTS', 'GEOGRAPHIC_NAMES', 'GEOLOGY', 'GOVERNMENT_UNITS', 'GPS_Data', 'HAZARD_SITE', 'HYDROGRAPHY', 'HYDROLOGIC_UNITS', 'IMAGERY', 'LAND_SITE', 'LAND_USE_LAND_COVER', 'MAP_INDEXES', 'MEASUREMENT_SERVICES', 'ORTHO_IMAGERY', 'PHOTOGRAPHS', 'PROJECT_DATA', 'PUBLIC_UTILITIES', 'SOILS', 'TOPOGRAPHIC_IMAGES', 'TRANSFER', 'TRANSPORTATION', 'WETLANDS', 'WILDLIFE', 'ZONING']

trunkParam = arcpy.GetParameterAsText(0)
rOfficeParam = arcpy.GetParameterAsText(1)
ssoParam = arcpy.GetParameterAsText(2)

arcpy.AddMessage('\n\n')

try:

    ssoLst = str(ssoParam).split(";")

    regionalGeoDataDir = trunkParam + os.sep + rOfficeParam[:2]
    if not os.path.exists(regionalGeoDataDir):
        os.mkdir(regionalGeoDataDir)
        arcpy.AddMessage("SUCCESS: created the " + rOfficeParam[:2] + " directory in " + trunkParam)
    else:
        arcpy.AddWarning("FAIL: The " + regionalGeoDataDir + " directory already exists ")

    arcpy.AddMessage('\n')
    for eDir in geoDataDirs:
        if not os.path.exists(regionalGeoDataDir + os.sep + eDir):
            os.mkdir(regionalGeoDataDir + os.sep + eDir)
            arcpy.AddMessage("Success: created " + eDir + " for  " + rOfficeParam[:2])
        else:
            arcpy.AddWarning("FAIL: The subdirectory " + eDir + " already exists in " + regionalGeoDataDir)



    for sso in ssoLst:
        arcpy.AddMessage('\n')
        sso = sso.replace("-", "")
        ssoGeoDataDir = trunkParam + os.sep + "R" + sso
        if not os.path.exists(ssoGeoDataDir):
            os.mkdir(ssoGeoDataDir)
            arcpy.AddMessage("SUCCESS: created the " + sso + " directory in " + trunkParam)
        else:
            arcpy.AddWarning("FAIL: The " + trunkParam + os.sep + sso + " directory already exists " )

        for eDir in geoDataDirs:
            if not os.path.exists(ssoGeoDataDir + os.sep + eDir):
                os.mkdir(ssoGeoDataDir + os.sep + eDir)
                arcpy.AddMessage("SUCCESS: created " + eDir + " for " + sso)
            else:
                arcpy.AddWarning("FAIL: The subdirectory " + eDir + " already exists in " + ssoGeoDataDir)

    arcpy.AddMessage('\n\n')

except:
    errorMsg()
