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
#This tool does creates OID table(s) for joining to spatial tables.
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
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

def getInterps(aUrl, theBaseFile, Interp, thePrj):

    try:

        #read the report
        request = urllib2.Request(aUrl)
        response = urllib2.urlopen(request)

        with open(theBaseFile, 'a') as f:

            #the following was borrowed from one of Steve Peaslee's tools.  Very handy!
            parser = False
            n=0
            for line in response:
                line = line.strip()
                if parser:

                    if line == "STOP":
                        break
                    else:
                        f.write(line + '\n')
                else:
                    if line.find("START") <> -1:
                        n=n+1
                        parser = True

        f.close()

        if n == 0:
            Msg = 'Unable to gather a valid interpretations table for ' + thePrj
            return False, Msg

        else:
            Msg = 'Succesfully collected interpretation table for ' + thePrj
            return True, Msg

    #try and trap errors
    except urllib2.HTTPError as e:
        Msg = 'Unable to open interps URL. HTTP Error: ' + str(e.code) + \
        '\nUnable to gather valid interpretations for ' + thePrj
        return False, Msg

    except urllib2.URLError as e:
        Msg = 'Unable to open interps URL. URL Error: ' + str(e.reason) + \
        '\nUnable to gather valid interpretations for ' + thePrj
        return False, Msg

    except socket.timeout as e:
        Msg = 'NASIS timeout error' + \
        '\nUnable to gather valid interpretations for ' + thePrj
        return False, Msg

    except socket.error as e:
        Msg = 'Socket error: ' + str(e) + \
        '\nUnable to gather valid interpretations for ' + thePrj
        return False, Msg

    except:
        errorMsg()
        Msg = 'Unknown error.\nUnable to gather valid interpretations for ' + thePrj
        return False, Msg

##================================================================================
##================================================================================

import sys, os, arcpy, shutil, urllib2, socket, traceback


try:
    arcpy.env.overwriteOutput = True
    pPrj = arcpy.GetParameterAsText(1)
    pInterpName = arcpy.GetParameterAsText(2)
    WS = arcpy.GetParameterAsText(3)
    srcDir = os.path.dirname(sys.argv[0])


    #arcpy.AddMessage("\n\nCollecting mapuint id's for " + prj)

    prjLst = pPrj.split(";")
    interpLst = pInterpName.split(";")
    progCnt = len(prjLst) * len(interpLst)

    #WS = srcDir + os.sep + 'Scratch_Interps.gdb'
    dataDir = os.getenv('APPDATA')
    tmpDir = dataDir + os.sep + 'NASIS_Interps_Tool'

    #create a temporary directory to store tables
    #delete it if it already exists to remove existing files
    if os.path.isdir(tmpDir):
            shutil.rmtree(tmpDir)

    os.mkdir(tmpDir)


    AddMsgAndPrint('\n \n')
    n = 0
    arcpy.SetProgressor("step", "Collecting interpretations from NASIS" , 0, progCnt, 1)
    for interpName in interpLst:

        AddMsgAndPrint('Collecting ' + interpName + ' interpretations' )

        for prj in prjLst:
            n = n + 1
            arcpy.SetProgressorLabel("Collecting interpretations from NASIS ("+ str(n) + " of " + str(progCnt) + ")")


            rootUrl = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-INTER_ARCGIS_PROJECT_DOM_COND&proj_name=FFFFF&rule_name=PPPPP'

            #since the prj and interpName come out of lists, need to handle the single quotes for the url
            #hence all the slicing and  extra parameters
            passPrj = prj.replace(' ', '%20')
            idx = interpName.find(':')
            passInterpName = interpName[idx + 1:-1].replace(' ', '%20').replace("{:}", ";")
            #interpName = interpName.replace(' ', '%20')
            interpUrl = rootUrl.replace('FFFFF', passPrj[1:-1]).replace("PPPPP", passInterpName)

            #arcpy.AddMessage(interpUrl)

            validInterp = arcpy.ValidateTableName(interpName)
            baseFile = tmpDir + os.sep + validInterp +'.tab'

            gI1, gI2 = getInterps(interpUrl, baseFile, interpName, passPrj)

            if gI1:
                AddMsgAndPrint('\t' + gI2.replace('%20', ' ') + '\n' )
                arcpy.SetProgressorPosition()

            else:
                AddMsgAndPrint('First attempt for ' + prj + ' falied. Attempting again...\n \n')
                gI1, gI2 = getInterps(interpUrl, baseFile, interpName, passPrj)

                if gI1:
                    AddMsgAndPrint('\t' + gI2.replace('%20', ' ') + '\n' )
                    arcpy.SetProgressorPosition()

                else:
                    AddMsgAndPrint('\t' + gI2.replace('%20', ' ') + '\n', 1)
                    AddMsgAndPrint('\n\tTry opening the URL manually  to verify\n\t'+ interpUrl)
                    arcpy.SetProgressorPosition()



        AddMsgAndPrint(' \n')


    #if you get at least one SSA returned with valid interpreatations then move along
    eBFLst = [x for x in os.listdir(tmpDir) if x.find('.tab') <> -1 and os.stat(os.path.join(tmpDir, x)).st_size > 0]
    #AddMsgAndPrint('\n \n' + str(intCnt) + ' interpretations requested and ' + str(len(eBFLst)) + ' interpretation tables collected for ' + str(acCnt) + ' Soil Survey Areas.' )
    arcpy.SetProgressor("step", "Creating join tables...", 0, len(eBFLst), 1)

    n = 0
    if len(eBFLst) > 0:

        AddMsgAndPrint('\n \nCreating tables in ' + WS + '...\n \n')
        for eBaseFile in eBFLst:

            n = n + 1

            arcpy.SetProgressorLabel("Creating join tables ("  + str(n) + " of " + str(len(eBFLst))+ ")")
            interpFeats = arcpy.ValidateTableName(eBaseFile[:-4]).replace("__", "_")
            output = interpFeats.replace("__", "_")
            output = output.replace("__", "_")

            #don't think Arc likes it when a layer starts with a number
            if output[0].isdigit():
                output = 'x'+ output

            #create dictionaries to store interp data. One for non-mlra mapunit ratings,
            #one for MLRA mapunit ratings and one to merege if the NASIS project both
            nonMLRAd = dict()
            hasMMUd = dict()
            #would you ever have a mlra rating for a mapunit and NOT have a non-mlra rating?
            compD = dict()
            pipe = "|"

            #open the file
            with open(tmpDir + os.sep + eBaseFile, 'r') as f:
                lines = f.readlines()
                for line in lines:

                    #format the line
                    fLine = line[:-1].replace('"', '')

                    #find your fields to slice
                    first = fLine.find(pipe)
                    second = fLine.find(pipe, first + 1)
                    third = fLine.find(pipe, second + 1)
                    fourth = fLine.find(pipe,third + 1)
                    fifth = fLine.find(pipe, fourth + 1)

                    #add to the appropriate dictionary
                    if fLine.find("non-mlra map unit") <> -1:
                        #arcpy.AddMessage(fLine)
                        key = fLine[:first]
                        nonMLRAd[key] = fLine[:first], int(fLine[:first]), fLine[second+1:third], fLine[third+1:fourth], fLine[fourth+1:fifth], fLine[fifth+1:]

                    elif fLine.find("mmu") <> -1:
                        #arcpy.AddMessage(fLine)
                        key = fLine[:first]
                        hasMMUd[key] = fLine[second+1:third], fLine[third+1:fourth], fLine[fourth+1:fifth], fLine[fifth+1:]

            f.close()


            #merge the dictionaries, even if one is empty
            for e in nonMLRAd:
                if e in hasMMUd:
                    compD[e] = nonMLRAd.get(e) + hasMMUd.get(e)
                else:
                    #add place holders if there aren't corresponding MLRA Mappunit interps returned
                    hldrLst = ['UNK'] * 4
                    tTup = nonMLRAd.get(e)
                    tLst = list(tTup)
                    tLst.extend(hldrLst)
                    compD[e] = tuple(tLst)
                    del tLst

##                for k,v in compD.iteritems():
##                    arcpy.AddMessage(str(k) + str(v))

            #read thru the merged dictionaries. the values returned for each key
            #must be of length 10.  Weird stuff comes out of NASIS based on what users have put in
            popLst = list()
            for e in compD:
                thisTuple = compD.get(e)
                if len(thisTuple) != 10:
                    popLst.append(e)

            if len(popLst) <> 0:
                AddMsgAndPrint( ",".join(popLst) + " mapunit(s) will be removed because invalid interpretations were returned from NASIS")
                for e in popLst:
                    compD.pop(e)


            template_table = srcDir + os.sep + 'Scratch_Interps.gdb' + os.sep + 'template_table'


            #get field list of template table and remove OID field so it can be passed to insert cursor
            desc = arcpy.Describe(template_table)
            fldLst = [x.name for x in desc.fields]
            fldLst.pop(0)

            #Delete the gdb table if it exists, and create it
            #for some reason create table management does not honor env setting of overwrite output
            if arcpy.Exists(WS + os.sep + 'tbl_' + output):
                arcpy.Delete_management(WS + os.sep + 'tbl_' + output)

            arcpy.CreateTable_management(WS, 'tbl_' + output, template_table)

            #create a cursor and iterate over the comprehensive dictionary and insert into nrely created table
            cursor = arcpy.da.InsertCursor(WS + os.sep + 'tbl_' + output, fldLst)

            for value in compD:
                row = compD.get(value)
                try:
                    AddMsgAndPrint(str(row), 1)
                    cursor.insertRow(row)
                except:
                    arcpy.AddMessage(row)

            #clean up for the next run
            del cursor
            del compD
            del hasMMUd
            del nonMLRAd

            arcpy.SetProgressorPosition()

    else:
        raise ForceExit('No valid interpretations returned from NASIS')

    AddMsgAndPrint('\n \n')

except:
    errorMsg()