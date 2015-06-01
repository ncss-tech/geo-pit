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


geoDataDirs = ['AIR_QUALITY', 'CADASTRAL', 'CENSUS', 'CLIMATE', 'COMMON_LAND_UNIT', 'CONSERVATION_PRACTICES', 'CULTURAL_RESOURCES', 'DISASTER_EVENTS', 'ECOLOGICAL', 'ELEVATION', 'ENDANGERED_HABITAT', 'ENVIRONMENTAL_EASEMENTS', 'GEOGRAPHIC_NAMES', 'GEOLOGY', 'GOVERNMENT_UNITS', 'GPS_DATA', 'HAZARD_SITE', 'HYDROGRAPHY', 'HYDROLOGIC_UNITS', 'IMAGERY', 'LAND_USE_LAND_COVER', 'LANDMARKS', 'MAP_INDEXES', 'MEASUREMENT_SERVICES', 'ORTHO_IMAGERY', 'PROJECT_DATA', 'PUBLIC_UTILITIES', 'SOILS', 'TOPOGRAPHIC_IMAGES', 'TRANSPORTATION', 'WETLANDS', 'WILDLIFE', 'ZONING']

trunkParam = arcpy.GetParameterAsText(0)
rOfficeParam = arcpy.GetParameterAsText(1)
ssoParam = arcpy.GetParameterAsText(2)

arcpy.AddMessage('\n\n')

try:

    n=0
    s=0

    ssoLst = str(ssoParam).split(";")

    regionalGeoDataDir = trunkParam + os.sep + rOfficeParam[:2]
    if not os.path.exists(regionalGeoDataDir):
        os.mkdir(regionalGeoDataDir)
        s=s+1
        arcpy.AddMessage("SUCCESS: created the " + rOfficeParam[:2] + " directory in " + trunkParam)
    else:
        n = n+1
        arcpy.AddWarning("FAIL: The " + regionalGeoDataDir + " directory already exists ")

    for eDir in geoDataDirs:
        if not os.path.exists(regionalGeoDataDir + os.sep + eDir):
            os.mkdir(regionalGeoDataDir + os.sep + eDir)
            s=s+1
            arcpy.AddMessage("SUCCESS: created " + eDir + " for  " + rOfficeParam[:2])
        else:
            n=n+1
            arcpy.AddWarning("FAIL: The subdirectory " + eDir + " already exists in " + regionalGeoDataDir)



    for sso in ssoLst:
        arcpy.AddMessage('\n')
        sso = sso.replace("-", "")
        ssoGeoDataDir = trunkParam + os.sep + "R" + sso
        if not os.path.exists(ssoGeoDataDir):
            os.mkdir(ssoGeoDataDir)
            s=s+1
            arcpy.AddMessage("SUCCESS: created the " + sso + " directory in " + trunkParam)
        else:
            n=n+1
            arcpy.AddWarning("FAIL: The " + trunkParam + os.sep + sso + " directory already exists " )

        for eDir in geoDataDirs:
            if not os.path.exists(ssoGeoDataDir + os.sep + eDir):
                os.mkdir(ssoGeoDataDir + os.sep + eDir)
                s=s+1
                arcpy.AddMessage("SUCCESS: created " + eDir + " for " + sso)
            else:
                n=n+1
                arcpy.AddWarning("FAIL: The subdirectory " + eDir + " already exists in " + ssoGeoDataDir)

    if s > 0:
        arcpy.AddMessage('\n' + 'Successfully created '+ str(s) + ' folders')

    if n > 0:
        arcpy.AddError('\n' + str(n) + ' FAILURE(S) encountered.  See messages above.')
    arcpy.AddMessage('\n\n')



except:
    errorMsg()
