#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      Charles.Ferguson
#
# Created:     29/09/2014
# Copyright:   (c) Charles.Ferguson 2014
# Licence:     <your licence>
#
# many lines of code borrowed from Steve Peaslee's
#-------------------------------------------------------------------------------
class ForceExit(Exception):
    pass

def AddMsgAndPrint(msg, severity=0):
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

    except:
        pass


def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        AddMsgAndPrint(theMsg, 2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass



def getIntrps(interpUrl, baseFile, eSSA):

    import urllib2, socket
    from urllib2 import Request

    try:

        keyLst = list()

        r = Request(interpUrl)
        interpO = urllib2.urlopen(r, None)

        with open(baseFile, 'a') as f:

            parser = False
            n=0
            for interp in interpO:
                interp = interp.strip()
                if parser:

                    if interp == "STOP":
                        break
                    else:
                        n=n+1
                        key = interp.find("|")
                        keyLst.append(interp[1:key - 1])
                        f.write(interp.replace('"','').replace("|", "\t") + '\n')
                else:
                    if interp.find('START') <> -1:
                        parser = True

        f.close()

        if n < 2:
            Msg = 'Unable to gather valid interpretations for ' + eSSA
            return False, Msg, None

        else:
            return True, 'Succesfully collected interpretations for ' + eSSA, keyLst

    except urllib2.HTTPError as e:
        Msg = 'Unable to open interps URL. HTTP Error: ' + str(e.code)
        return False, Msg, None

    except urllib2.URLError as e:
        Msg = 'Unable to open interps URL.  URL Error: ' + str(e.reason)
        return False, Msg, None

    except socket.timeout as e:
        Msg = 'NASIS timeout error'
        return False, Msg, None

    except socket.error as e:
        Msg = 'Socket error: ' + str(e)
        return False, None, None

    except:
        errorMsg()
        Msg = 'Unknown error collecting interpreations for ' + eSSA
        return False, Msg, None



def symbolCounter(baseFile):

    try:
        l = 'Limitation'
        s = 'Suitability'
        kindLst = list()
        with open(baseFile, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.find(l) <> -1:
                    kindLst.append(l)
                elif line.find(s) <> -1:
                    kindLst.append(s)
            retKind = list(set(kindLst))

            if len(retKind) == 1:

                return True, retKind

            else:

                return False, None
    except:
        errorMsg()

def localValidator(aSSA, aWS, mukeyLst):

    try:

        #arcpy.AddMessage('Validating results' + str(gI3))
        kHldLst = list()
        expression = '"AREASYMBOL" = ' + "'" + aSSA + "'"
        with arcpy.da.SearchCursor(aWS + os.sep + 'MUPOLYGON', ["AREASYMBOL", "MUKEY"], expression) as rows:
            for row in rows:
                kHldLst.append(str(row[1]))

        localKeySet = set(kHldLst)
        nasisKeySet = set(mukeyLst)

        ninlocal = nasisKeySet - localKeySet
        localinn = localKeySet - nasisKeySet

        locallen = len(localinn)
        nasislen = len(ninlocal)

        if locallen == 0 and nasislen == 0:
                AddMsgAndPrint('\tMapunits from NASIS and validation source are in sync')
        elif len(localinn) <> 0:
            AddMsgAndPrint("\tThe following mukey(s) are in the gSSURGO database but not returned from NASIS: " + ",".join(localinn), 1)
        elif len(ninlocal) <> 0:
            AddMsgAndPrint("\tThe following mukey(s) are returned from NASIS but are not in the gSSURGO database: " + ",".join(ninlocal), 1)

    except:
        errorMsg()
        AddMsgAndPrint('Unable to validate ' + aSSA)

##================================================================================
##================================================================================

import sys, os, arcpy, traceback, shutil, time


try:
    arcpy.env.overwriteOutput = True
    areaSyms = arcpy.GetParameterAsText(1)
    siteInterpName = arcpy.GetParameterAsText(2)
    WS = arcpy.GetParameterAsText(3)
    #csBool = arcpy.GetParameterAsText(4)
    polys = arcpy.GetParameterAsText(4)
    #jRasterBool = arcpy.GetParameterAsText(6)
    srcRaster = arcpy.GetParameterAsText(5)
    srcDir = os.path.dirname(sys.argv[0])
    #keyValid = arcpy.GetParameterAsText(8)
    WS2 = arcpy.GetParameterAsText(6)
    printUrl = arcpy.GetParameterAsText(7)

    failInterps = dict()

    areaLst = areaSyms.split(';')
    areaLst.sort()
    acCnt = len(areaLst)

    #clean up the name of the interpretation and get it useable
    spLoc = siteInterpName.find(":") + 1
    interpName = siteInterpName[spLoc:]

    #get rid of interpretation special characters
    interpFeats = arcpy.ValidateTableName(interpName)

    #try and clean it up a little
    output = interpFeats.replace("__", "_")
    output = output.replace("__", "_")
    #some of the interps start with a number
    if output[1].isdigit():
        output = 'x'+ output


    #WS = srcDir + os.sep + 'Scratch_Interps.gdb'
    dataDir = os.getenv('APPDATA')
    tmpDir = dataDir + os.sep + 'NASIS_Interps_Tool'

    rootUrl = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-INTERP_ARCGIS_AREASYMBOL&rule_name='+ interpName.replace(' ', '%20') + '&asym=YYYYY'

    #create file path to collect interps
    baseFile = tmpDir + os.sep + 'nasis_interp.tab'

    #create a temporary directory to store tables
    #delete it if it already exists to remove existing files
    if os.path.isdir(tmpDir):
            shutil.rmtree(tmpDir)

    os.mkdir(tmpDir)


    arcpy.SetProgressor('step', 'Starting Interps Tool...', 0, acCnt, 1)
    AddMsgAndPrint('\n \n')
    n = 0
    for eSSA in areaLst:
        n = n + 1
        arcpy.SetProgressorLabel('Collecting Interpretations for: ' + eSSA + " (" + str(n) + ' of ' + str(acCnt) + ')')
        interpUrl = rootUrl.replace('YYYYY', eSSA)
        #arcpy.AddMessage(interpUrl)


        gI, gI2, gI3 = getIntrps(interpUrl, baseFile, eSSA)
        if gI:
            AddMsgAndPrint(gI2)
            arcpy.SetProgressorPosition()

            if WS2 !="":

                localValidator(eSSA, WS2, gI3)

        else:
            AddMsgAndPrint(' \nFirst attempt failed for ' + eSSA + '. Running second attempt...\n \n', 1)
            gI, gI2, gI3 = getIntrps(interpUrl, baseFile, eSSA)
            if gI:
                AddMsgAndPrint(gI2)
                arcpy.SetProgressorPosition()
                if WS2 !="":
                    localValidator(eSSA, WS2, gI3)
            else:
                failInterps[eSSA] = interpUrl
                AddMsgAndPrint(gI2, 1)
                #AddMsgAndPrint(' \nTry running the failed URL manually to verify the error:\n' + interpUrl + ' \n ', 1)
                arcpy.SetProgressorPosition()

        del interpUrl


    #if you get at least one SSA returned with valid interpreatations then move along
    if not len(failInterps) == acCnt:

        interpDic = dict()

        arcpy.SetProgressor("step", "Creating Interpretations table...", 0,1,1)
        template_table_2 = srcDir + os.sep + 'Scratch_Interps.gdb' + os.sep + 'template_table_2'

        if arcpy.Exists(WS + os.sep + 'tbl_' + output):
                arcpy.Delete_management(WS + os.sep + 'tbl_' + output)

        arcpy.CreateTable_management(WS, 'tbl_' + output, template_table_2)
        oidTbl = WS + os.sep +'tbl_' + output
        if os.path.exists(baseFile):

            with open(baseFile, 'r') as f:
                lines = f.readlines()
                arcpy.SetProgressor("step", "Creating join file...", 0, len(lines), 1)
                for line in lines:
                    tmpLine = line.replace("\t", ",")[:-1]
                    tmpLst = tmpLine.split(",")
                    interpDic[tmpLst[0]] = tmpLst[0], int(tmpLst[0]), tmpLst[2], tmpLst[3], tmpLst[4]
                f.close


            desc = arcpy.Describe(WS + os.sep + 'tbl_' + output)
            fldLst = [x.name for x in desc.fields]
            fldLst.pop(0)

            cursor = arcpy.da.InsertCursor(WS + os.sep + 'tbl_' + output, fldLst)

            for value in interpDic:
                row = interpDic.get(value)
                cursor.insertRow(row)

            del cursor
    else:
        if printUrl == 'true':
            if len(failInterps) > 0:
                AddMsgAndPrint('\n \nThese Soil Survey Areas failed to run successfully:\n')
                for k, v in failInterps.iteritems():
                    AddMsgAndPrint(k + '\n' + v +'\n \n')
        raise ForceExit('Unable to find collection of interpretations.')

    if polys != "":

        arcpy.SetProgressor("step", "Creating spatial query...", 0, 3, 1)
        #append the legend mapunit id's to an empty string
        lmuiids = ''

        with arcpy.da.SearchCursor(oidTbl, ['mukey']) as rows:
            for row in rows:
                lmuiids = lmuiids + "'" + str(row[0]) + "',"

        #format the string for query,
        lmuiids = "(" + lmuiids[:-1] + ")"

        #generate the query
        fsSubQry = "\"MUKEY\" IN" + lmuiids

        fields = ['class', 'rating', 'kind']

        outName = WS + os.sep + output


        arcpy.SetProgressorLabel("Creating Polygon Output...")
        AddMsgAndPrint('\n \nCreating Polygon Output...')
        arcpy.SetProgressorPosition(2)
        arcpy.FeatureClassToFeatureClass_conversion(polys, WS, output, fsSubQry)

        for field in fields:
            arcpy.management.AddField(outName, field, "TEXT", "", "", 25)

        #interpDic[tmpLst[0]] = tmpLst[0], int(tmpLst[0]), tmpLst[2], tmpLst[3], tmpLst[4]
        with arcpy.da.UpdateCursor(outName, ['MUKEY', 'rating', 'class', 'kind']) as rows:
            for row in rows:
                row[1] = interpDic.get(row[0])[2]
                row[2] = interpDic.get(row[0])[3]
                row[3] = interpDic.get(row[0])[4]
                rows.updateRow(row)

        del row, rows


        arcpy.SetProgressorLabel("Attempting to draw layer if in ArcMap environment...")
        arcpy.SetProgressorPosition(3)
        try:
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            arcpy.MakeFeatureLayer_management(outName, os.path.basename(outName))

            sC1, sC2 = symbolCounter(baseFile)
            if sC1:
                symKind = ",".join(sC2)
                AddMsgAndPrint(symKind)
                srcLyr = srcDir + os.sep + symKind + '.lyr'
                arcpy.ApplySymbologyFromLayer_management(os.path.basename(outName), srcLyr)

        except:
            errorMsg()
            #AddMsgAndPrint("Can't draw and symbolize")

    if srcRaster != "":

        sC1, sC2 = symbolCounter(baseFile)

        AddMsgAndPrint('\n \nReading raster layer...')
        arcpy.env.addOutputsToMap = True
        arcpy.SetProgressor("step", "Attempting to render...", 0, 1, 1)
        try:
            mxd = arcpy.mapping.MapDocument("CURRENT")
            dfs = arcpy.mapping.ListDataFrames(mxd, "*")[0]
            desc = arcpy.Describe(srcRaster)
            rType = desc.dataType

            if rType.upper() == 'RASTERDATASET':
                rLyr = os.path.basename(srcRaster)
                arcpy.MakeRasterLayer_management(srcRaster, rLyr)
                arcpy.management.AddJoin(rLyr, "mukey", oidTbl, "mukey")


            elif rType.upper() == 'RASTERLAYER':
                lyr = arcpy.mapping.ListLayers(mxd, srcRaster, dfs)
                rLyr = lyr[0]
                flds = [x.name for x in desc.fields]
                if not "Value" in flds:
                    AddMsgAndPrint('\n \nReloading ' + srcRaster + ' due to existing join')
                    arcpy.mapping.RemoveLayer(dfs, rLyr)
                    bName = desc.baseName
                    arcpy.MakeRasterLayer_management(desc.catalogPath, bName)
                    arcpy.management.AddJoin(bName, "mukey", oidTbl, "mukey")

                else:
                    arcpy.management.AddJoin(rLyr, "mukey", oidTbl, "mukey")
                    #try and add symbology
                    if sC1:
                        symKind = ",".join(sC2)
                        srcLyr = srcDir + os.sep + 'Raster_' + symKind + '.lyr'
                        arcpy.ApplySymbologyFromLayer_management(rLyr, srcLyr)

        except:
            errorMsg()
            AddMsgAndPrint('\n \n Unable to join to ' + srcRaster)

    AddMsgAndPrint('\n \nInterpretation table location: ' + oidTbl + '\n \n')

    if printUrl == 'true':
        if len(failInterps) > 0:
            AddMsgAndPrint('\n \nThese Soil Survey Areas failed to run successfully:\n')
            for k, v in failInterps.iteritems():
                AddMsgAndPrint(k + '\n' + v +'\n \n')

except:
    errorMsg()
