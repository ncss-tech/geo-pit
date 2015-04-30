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
#
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



def getIntrps(interpUrl, baseFile, interp, eSSA):

    import urllib2, socket
    from urllib2 import Request

    try:

        keyLst = list()

        r = Request(interpUrl)
        interpO = urllib2.urlopen(r, None)

        with open(baseFile, 'a') as f:

            parser = False
            n=0
            for eInterp in interpO:
                eInterp = eInterp.strip()
                if parser:

                    if eInterp == "STOP":
                        break
                    else:
                        n=n+1
                        key = eInterp.find("|")
                        keyLst.append(eInterp[1:key - 1])
                        f.write(eInterp.replace('"','').replace("|", "\t") + '\n')
                else:
                    if eInterp.find('START') <> -1:
                        parser = True

            if n < 2:
                Msg = 'Unable to gather valid ' + interp + ' interpretations for ' + eSSA
                return False, Msg, None

            else:
                Msg = 'Succesfully collected ' + interp + ' interpretations for ' + eSSA
                return True, Msg, keyLst

        f.close()
        del interpO


    except urllib2.HTTPError as e:
        Msg = 'Unable to open interps URL. HTTP Error: ' + str(e.code) + \
        '\nUnable to gather valid ' + interp + ' interpretations for ' + eSSA
        return False, Msg, None

    except urllib2.URLError as e:
        Msg = 'Unable to open interps URL. URL Error: ' + str(e.reason) + \
        '\nUnable to gather valid ' + interp + ' interpretations for ' + eSSA
        return False, Msg, None

    except socket.timeout as e:
        Msg = 'NASIS timeout error' + \
        '\nUnable to gather valid ' + interp + ' interpretations for ' + eSSA
        return False, Msg, None

    except socket.error as e:
        Msg = 'Socket error: ' + str(e) + \
        '\nUnable to gather valid ' + interp + ' interpretations for ' + eSSA
        return False, None

    except:
        errorMsg()
        Msg = 'Unknown error.\nUnable to gather valid ' + interp + ' interpretations for ' + eSSA
        return False, Msg, None

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
            AddMsgAndPrint("\tThe following mukey(s) are in the gSSURGO database but not returned from NASIS: " + ",".join(localinn),1)
        elif len(ninlocal) <> 0:
            AddMsgAndPrint("\tThe following mukey(s) are returned from NASIS but are not in the gSSURGO database: " + ",".join(ninlocal),1)

    except:
        errorMsg()
        AddMsgAndPrint('Unable to validate ' + aSSA)

#===============================================================================

import sys, os, arcpy, traceback, shutil, time


try:
    arcpy.env.overwriteOutput = True
    areaSyms = arcpy.GetParameterAsText(1)
    siteInterpLst = arcpy.GetParameterAsText(2)
    WS = arcpy.GetParameterAsText(3)
    #keyValid = arcpy.GetParameterAsText(4)
    WS2 = arcpy.GetParameterAsText(4)
    failUrlBool = arcpy.GetParameterAsText(5)

    srcDir = os.path.dirname(sys.argv[0])


    failDic = dict()

    failUrl = list()
    interpLst = list()

    areaLst = areaSyms.split(';')
    areaLst.sort()
    acCnt = len(areaLst)

    #get interps from parameter
    #clean up the name of the interpretations and get them useable
    tmpInterpLst = siteInterpLst.split(';')
    for interp in tmpInterpLst:
        spLoc = interp.find(":") + 1
        appVal = interp[spLoc:]
        interpLst.append(appVal.replace("'", "").replace("{:}", ";"))

    del interp
    interpLst.sort()
    intCnt = len(interpLst)

    #create a temporary directory to store tables
    #delete it if it already exists to remove existing files
    dataDir = os.getenv('APPDATA')
    tmpDir = dataDir + os.sep + 'NASIS_Interps_Tool'
    if os.path.isdir(tmpDir):
            shutil.rmtree(tmpDir)
    os.mkdir(tmpDir)

    rootUrl = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-INTERP_ARCGIS_AREASYMBOL&rule_name=ZZZZZ&asym=YYYYY'

    tCnt = acCnt*intCnt
    arcpy.SetProgressor('step', 'Starting Interps Tool...', 0, tCnt, 1)


    AddMsgAndPrint('\n \nWorking...\n \n')
    n = 0

    for interp in interpLst:

        failInterps = list()

        for eSSA in areaLst:

            n = n + 1

            #create file path to collect interps
            #run validate table name to get rid of invalid  characters for file paths in NASIS interps
            validInterp = arcpy.ValidateTableName(interp)
            baseFile = tmpDir + os.sep + validInterp +'.tab'

            #some interpretations have a ; which is the split character for a parameter list.
            #these were replaced with {:} in the validator class and now need to be switched
            #back so the report will run
            urlInterp = interp.replace(' ', '%20').replace('{:}', ';')

            arcpy.SetProgressorLabel('Collecting ' +  interp + ' for: ' + eSSA + " (" + str(n) + ' of ' + str(tCnt) + ')')
            interpUrl = rootUrl.replace('YYYYY', eSSA).replace('ZZZZZ', urlInterp)
            #arcpy.AddMessage(interpUrl)



            gI, gI2, gI3 = getIntrps(interpUrl, baseFile, interp, eSSA)
            if gI:
                AddMsgAndPrint(gI2)
                if WS2 !="":
                    localValidator(eSSA, WS2, gI3)

                arcpy.SetProgressorPosition()
                #AddMsgAndPrint(' \n')
            else:
                #AddMsgAndPrint(' \nFirst attempt failed for ' + eSSA + ': ' + interp + '. Running second attempt...\n \n', 1)
                gI, gI2, gI3 = getIntrps(interpUrl, baseFile, interp, eSSA)
                if gI:
                    AddMsgAndPrint(gI2 + ', 2nd attempt required.')
                    if WS2 !="":
                        localValidator(eSSA, WS2, gI3)
                    arcpy.SetProgressorPosition()
                    #AddMsgAndPrint(' \n')
                else:
                    failInterps.append(eSSA)
                    failUrl.append(interpUrl)
                    #AddMsgAndPrint(gI2 + '. 2 attempts made.')
                    #AddMsgAndPrint(' \nTry running the failed URL manually to verify the error:\n' + interpUrl + ' \n ', 1)
                    arcpy.SetProgressorPosition()
                    #AddMsgAndPrint('\n ')


            del interpUrl
            del baseFile

        if len(failInterps) > 0:
            failDic[interp] = ",".join(failInterps)

        del failInterps

    if len(failDic) > 0:
        AddMsgAndPrint(' \n \n \n ' + '='*10 + 'FAILURES'+'='*10 )
        for k,v in failDic.iteritems():
            AddMsgAndPrint('Failed after 2 attempts - '+ k + ' interpretations:' + str(v))

    #if you get at least one SSA returned WITH valid interpreatations then move along
    eBFLst = [x for x in os.listdir(tmpDir) if x.find('.tab') <> -1 and os.stat(os.path.join(tmpDir, x)).st_size > 0]

    if len(eBFLst) == 0:
        raise ForceExit('No valid interpreatation tables were returned from NASIS')

    arcpy.SetProgressor("step", "Creating join files...", 0, len(eBFLst), 1)


    AddMsgAndPrint(' \n \n \n ' + '='*11 + 'TABLES'+'='*11 )
    for eBaseFile in eBFLst:

        #get rid of interpretation special characters
        interpFeats = arcpy.ValidateTableName(eBaseFile[:-4])

        #try and clean it up a little
        output = interpFeats.replace("__", "_")
        output = output.replace("__", "_")

        #some of the interps start with a number
        if output[1].isdigit():
            output = 'x'+ output

        with open(tmpDir + os.sep + eBaseFile, 'r') as f:
            lines = f.readlines()

            #open the text file from getInterps and insert the colum headers
            hdrBaseFile = tmpDir + os.sep + 'hdr_' + output + '.tab'
            with open(hdrBaseFile, 'w') as j:
                hdrMsg = 'mukey\tmusym\trating\tclass\tkind\n'
                j.write(hdrMsg)
                for line in lines:
                    if line[0].isdigit():
                        j.write(line)
                f.close()
            j.close()

        oidTbl = WS + os.sep + 'tbl_' + output + '_dom_cond_rt'
        arcpy.CopyRows_management(hdrBaseFile, oidTbl)
        arcpy.management.AddField(oidTbl, "str_mukey", "TEXT" "", "", 10)
        arcpy.management.CalculateField(oidTbl, "str_mukey", "CStr([mukey])")
        AddMsgAndPrint('Interpretation created: ' + oidTbl)
        arcpy.SetProgressorPosition()


    if failUrlBool == "true":
        if len(failUrl) > 0:
            AddMsgAndPrint(' \n \n \n ' + '='*12 + 'URLs'+'='*12 )
            AddMsgAndPrint('Try running failed URLs manually to verify the error:')
            for url in failUrl:
                AddMsgAndPrint(url + '\n')



    AddMsgAndPrint('\n \n')
except:
    errorMsg()
