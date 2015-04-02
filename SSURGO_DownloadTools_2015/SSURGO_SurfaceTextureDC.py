# SSURGO_SurfaceTextureDC.py
#
# Steve Peaslee, USDA-NRCS
#
# Uses simplest method of determining dominant componet for each map unit. Takes
# the first component with the highest representative component percent. Adds
# surface texture for the dominant component
#
## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                arcpy.AddMessage(string)

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                arcpy.AddMessage("    ")
                arcpy.AddError(string)
                #arcpy.AddMessage("    ")

    except:
        pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    try:
    # Format a number according to locality and given places
        #locale.setlocale(locale.LC_ALL, "")
        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)

        else:
            theNumber = locale.format("%.*f", (places, num), False)
        return theNumber

    except:
        PrintMsg("Unhandled exception in Number_Format function (" + str(num) + ")", 2)
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcpy, traceback
from arcpy import env
inputDB = arcpy.GetParameterAsText(0)    # Input database. Assuming SSURGO or gSSURGO soils database
outputTbl = arcpy.GetParameterAsText(1)  # Output table containing surface texture for the dominant component

try:

    # Get surface texture for all components
    PrintMsg(" \nGetting surface texture for each component...", 0)
    env.workspace = inputDB
    qTbl = "QueryTexture"
    tbls = ["chtexture","chtexturegrp","chorizon"]
    qFlds = "chtexture.texcl texcl;chtexture.lieutex lieutex;chtexturegrp.texture texture;chtexturegrp.texdesc texdesc;chorizon.hzname hzname;chorizon.desgnmaster desgnmaster;chorizon.hzdept_r hzdept_r;chorizon.hzdepb_r hzdepb_r;chorizon.cokey cokey"
    query = "chtexture.chtgkey = chtexturegrp.chtgkey AND chtexturegrp.chkey = chorizon.chkey AND chorizon.hzdept_r = 0 AND chtexturegrp.rvindicator = 'Yes'"

    arcpy.MakeQueryTable_management(tbls, qTbl, "ADD_VIRTUAL_KEY_FIELD", "#", qFlds, query)

    # OBJECTID
	# chtexture_texcl
	# chtexture_lieutex
	# chtexturegrp_texture
	# chtexturegrp_texdesc
	# chorizon_hzname
	# chorizon_desgnmaster
	# chorizon_hzdept_r
	# chorizon_hzdepb_r
	# chorizon_cokey

    dTexture = dict()
    tFlds = ("chorizon_cokey", "chtexture_texcl", "chtexture_lieutex", "chtexturegrp_texture")

    with arcpy.da.SearchCursor(qTbl, tFlds) as cur:
        for rec in cur:
            cokey, textcl, lieutext, texture = rec
            dTexture[cokey] = (textcl, lieutext, texture)

    PrintMsg(" \nGetting dominant component for each map unit in " + os.path.basename(inputDB), 0)

    coTbl = os.path.join(inputDB, "component")

    if not arcpy.Exists(coTbl):
        raise MyError, "COMPONENT table not found for " + inputDB

    # Open component table sorted by cokey and comppct_r
    iCnt = int(arcpy.GetCount_management(coTbl).getOutput(0))

    dComp = dict()

    sqlClause = "ORDER BY MUKEY DESC, COMPPCT_R DESC, COKEY DESC"
    arcpy.SetProgressor("step", "Reading component table...",  0, iCnt, 1)

    with arcpy.da.SearchCursor(coTbl, ["mukey", "cokey", "compname", "comppct_r"], "", "", "", (None, sqlClause)) as incur:
        for inrec in incur:
            if not inrec[0] in dComp:
                # this is the dominant component
                dComp[inrec[0]] = inrec[1], inrec[2], inrec[3]

            arcpy.SetProgressorPosition()

    if len(dComp) > 0:
        arcpy.ResetProgressor()
        # write values to new table
        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        arcpy.CreateTable_management(os.path.dirname(outputTbl), os.path.basename(outputTbl))
        arcpy.AddField_management(outputTbl, "mukey", "Text", "", "", 30)
        arcpy.AddField_management(outputTbl, "cokey", "Text", "", "", 30)
        arcpy.AddField_management(outputTbl, "compname", "Text", "", "", 60)
        arcpy.AddField_management(outputTbl, "comppct_r", "Short")
        arcpy.AddField_management(outputTbl, "texcl", "Text", "", "", 254)
        arcpy.AddField_management(outputTbl, "lieutex", "Text", "", "", 254)
        arcpy.AddField_management(outputTbl, "texture", "Text", "", "", 254)

    arcpy.SetProgressor("step", "Saving dominant component information...",  0, len(dComp), 1)

    with arcpy.da.InsertCursor(outputTbl, ["mukey", "cokey", "compname", "comppct_r", "texcl", "lieutex", "texture"]) as outcur:
        for mukey, val in dComp.items():
            cokey, compname, comppct_r = val

            try:
                textcl, lieutex, texture = dTexture[cokey]

            except:
                textcl = None
                lieutex = None
                texture = None

            outrec = [mukey, cokey, compname, comppct_r, textcl, lieutex, texture]
            outcur.insertRow(outrec)
            arcpy.SetProgressorPosition()

    arcpy.AddIndex_management(outputTbl, "mukey", "Indx_dcMukey", "UNIQUE")
    PrintMsg(" \nFinished writing dominant component information to " + os.path.basename(outputTbl) + " \n ", 0)

except MyError, e:
    # Example: raise MyError("this is an error message")
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()
