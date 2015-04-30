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
#This tool does not create an OID table.  Since it is assumed that the user is going to want
#a polygon output, it just creates a dictionary and updates the attribute table from it
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

def getInterps(url, baseFile):

    try:

        arcpy.SetProgressor("step", "Sending request to NASIS...", 0, 2, 1)
        AddMsgAndPrint('\n \nSending request to NASIS...')
        #read the report
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)

        arcpy.SetProgressorLabel("Reading response...")
        arcpy.SetProgressorPosition(2)
        AddMsgAndPrint('\n \nReading response...')
        with open(baseFile, 'a') as f:

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
            return False

        else:
            return True

    #try and trap errors
    except urllib2.HTTPError as e:
        AddMsgAndPrint('Unable to open interps URL. Error: ' + str(e.code), 2)
        return False

    except urllib2.URLError as e:
        AddMsgAndPrint('Unable to open interps URL: ' + str(e.reason), 2)
        return False

    except socket.timeout as e:
        AddMsgAndPrint('NASIS timeout error', 2)
        return False

    except socket.error as e:
        AddMsgAndPrint('Socket error: ' + str(e))
        return False

    except:
        errorMsg()
        return False


##================================================================================
##================================================================================

import sys, os, arcpy,shutil, urllib2, socket, traceback


try:
    arcpy.env.overwriteOutput = True
    prj = arcpy.GetParameterAsText(1)
    interpName = arcpy.GetParameterAsText(2)
    polys = arcpy.GetParameterAsText(3)
    WS = arcpy.GetParameterAsText(4)
    srcDir = os.path.dirname(sys.argv[0])


    arcpy.AddMessage("\n\nCollecting mapuint id's for " + prj)


    rootUrl = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB-INTER_ARCGIS_PROJECT_DOM_COND&proj_name=FFFFF&rule_name=PPPPP'

    prj = prj.replace(' ', '%20')
    idx = interpName.find(':')
    outputName = interpName[idx + 1:]
    interpName = interpName[idx + 1:].replace(' ', '%20')
    #interpName = interpName.replace(' ', '%20')
    interpUrl = rootUrl.replace('FFFFF', prj).replace('PPPPP', interpName)
    #arcpy.AddMessage(interpUrl)

    interpFeats = arcpy.ValidateTableName(outputName).replace("__", "_")
    output = interpFeats.replace("__", "_")
    output = output.replace("__", "_")

    #don't think Arc likes it when a layer starts with a number
    if output[1].isdigit():
        output = 'x'+ output

    #WS = srcDir + os.sep + 'Scratch_Interps.gdb'
    dataDir = os.getenv('APPDATA')
    tmpDir = dataDir + os.sep + 'NASIS_Interps_Tool'

     #create file path to collect interps
    baseFile = tmpDir + os.sep + 'nasis_interp.tab'

    #create a temporary directory to store tables
    #delete it if it already exists to remove existing files
    if os.path.isdir(tmpDir):
            shutil.rmtree(tmpDir)

    os.mkdir(tmpDir)

    #force Arc to play nice with string fields that look like numbers
    with open(tmpDir + os.sep + 'schema.ini', 'w') as f:
        f.write('[interpJoin.tab]\nColNameHeader=True\nCol1=j_mukey Text')
    f.close()



    gI = getInterps(interpUrl, baseFile)

    if gI:

        arcpy.SetProgressor("Processing NASIS response...", 0, 3, 1)
        #create dictionaries to store interp data. One for non-mlra mapunit ratings,
        #one for MLRA mapunit ratings and one to merege if the NASIS project both
        nonMLRAd = dict()
        hasMMUd = dict()
        #would you ever have a mlra rating for a mapunit and NOT have a non-mlra rating?
        compD = dict()
        pipe = "|"

        #open the file
        with open(baseFile, 'r') as f:
            lines = f.readlines()
            for line in lines:

                #format the line
                fLine = line[:-1].replace('"', '')

                #arcpy.AddMessage(fLine)

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
                    nonMLRAd[key] = fLine[second+1:third], fLine[third+1:fourth], fLine[fourth+1:fifth], fLine[fifth+1:]

                elif fLine.find("mmu") <> -1:
                    #arcpy.AddMessage(fLine)
                    key = fLine[:first]
                    hasMMUd[key] = fLine[second+1:third], fLine[third+1:fourth], fLine[fourth+1:fifth], fLine[fifth+1:]

                #del first, second, third, fourth, fifth
        f.close()


        #merge the dictionaries, even if one is empty
        for e in nonMLRAd:
            if e in hasMMUd:
                compD[e] = nonMLRAd.get(e) + hasMMUd.get(e)
            #add place holders if one or more projects don't have interpretation values for MLRA Mapunits
            else:
                hldrLst = ['UNK'] * 4
                tTup = nonMLRAd.get(e)
                tLst = list(tTup)
                tLst.extend(hldrLst)
                compD[e] = tuple(tLst)
                del tLst

        if len(compD) == 0:
            raise ForceExit('No mapunits are populated in this project')

        AddMsgAndPrint('\n \nNASIS returned ' + str(len(compD)) + ' mapunits')

        #read thru the merged dictionaries. the values returned for each key
        #must be of length 4 or 8.  If a key doesn't have 4 or 8 values, it gets
        #kicked out.  Weird stuff comes out of NASIS based on what users have put in
        lenLst = (4,8)
        popLst = list()
        for e in compD:
            value = compD.get(e)
            if len(value) not in lenLst:
                popLst.append(e)

        if len(popLst) <> 0:
            AddMsgAndPrint( ",".join(popLst) + " mapunit(s) will be removed because invalid interpretations were returned from NASIS")
            for e in popLst:
                compD.pop(e)

        #count the values for the keys to determine what header to write for the join table
        mx = 0
        for dK in compD:
            v = compD.get(dK)
            if len(v) > mx:
                mx = len(v)

##        if mx == 4:
##            #if only non-mlra mapunits have been rated then columns are
##            #j(oin)_mukey,rating, class, type kind
##            hdrMsg = 'j_mukey\trating\tclass\ttype\tkind'
##        elif mx == 8:
##            #if MLRA mapunit ratings are present too, then as above with the following added
##            #m(lra)_rating, m(lra)_class, m(lra)_type, m(lra)_kind. redundant, but again, I have
##            #seen weird stuff come out of NASIS
##            hdrMsg = 'j_mukey\trating\tclass\ttype\tkind\tm_rating\tm_class\tm_type\tm_kind'
##        else:
##            IOError

##
##        #write everything out
##        with open(tmpDir + os.sep + 'interpJoin.tab', 'w') as f:
##            f.write(hdrMsg + '\n')
##            for k,v in compD.iteritems():
##                f.write(k + '\t' + '\t'.join(v) + '\n')
##        f.close()


##        #open file from tblPrp, grab the first column from each record and create qrcgis query
##        lmuiids = ''
##
##        interps = tmpDir + os.sep + 'interpJoin.tab'
##        with open(interps, 'r') as f:
##            next(f)
##            for line in f:
##                index = line.find("\t")
##                lmuiids = lmuiids + "'" + line[:index] + "',"
##        f.close()
##

        arcpy.SetProgressorLabel("Extracting polygons from: " + polys)
        arcpy.SetProgressorPosition(2)
        lmuiids = ''

        for key in compD.iterkeys():
            lmuiids = lmuiids + "'" + key + "',"

        lmuiids = "(" + lmuiids[:-1] + ")"





        fsSubQry = "\"MUKEY\" IN" + lmuiids
        pSubQry = "[MUKEY] IN" + lmuiids

        #create oid  Table
        #oidTbl = WS + os.sep + 'tbl_' + output
        #arcpy.CopyRows_management(interps, oidTbl)
        #arcpy.AddMessage(str([x.name for x in arcpy.ListFields(oidTbl)]))

        arcpy.FeatureClassToFeatureClass_conversion(polys, WS, output, fsSubQry)

        arcpy.SetProgressorLabel("Updating attribute table...")
        arcpy.SetProgressorPosition(3)
        AddMsgAndPrint("\n \nUpdating output polygon attribute table...")
        outName = WS + os.sep + output

        if mx == 4:
            #arcpy.AddMessage(compD)
            fields = ['n_rating', 'n_class', 'n_mukind', 'n_kind']
            for field in fields:
                arcpy.management.AddField(outName, field, "TEXT", "", "", 25)
##                if field == 'm_rating':
##                    arcpy.management.AddField(outName, field, "SHORT")
##                else:
##                    arcpy.management.AddField(outName, field, "TEXT", "", "", 25)

            with arcpy.da.UpdateCursor(outName, ['MUKEY', 'n_rating', 'n_class', 'n_mukind', 'n_kind']) as rows:
                for row in rows:
                    row[1] = compD.get(row[0])[0]
                    row[2] = compD.get(row[0])[1]
                    row[3] = compD.get(row[0])[2]
                    row[4] = compD.get(row[0])[3]

                    rows.updateRow(row)

            del row, rows

        elif mx == 8:
            #arcpy.AddMessage(compD)
            fields = ['n_rating', 'n_class', 'n_mukind', 'n_kind', 'm_rating', 'm_class', 'm_mukind', 'm_kind']
            for field in fields:
                arcpy.management.AddField(outName, field, "TEXT", "", "", 25)
##                if field == 'm_rating' or field == 'n_rating':
##                    arcpy.management.AddField(outName, field, "SHORT")
##                else:
##                    arcpy.management.AddField(outName, field, "TEXT", "", "", 25)

            with arcpy.da.UpdateCursor(outName, ['MUKEY', 'n_rating', 'n_class', 'n_mukind', 'n_kind', 'm_rating', 'm_class', 'm_mukind', 'm_kind']) as rows:
                for row in rows:
                    row[1] = compD.get(row[0])[0]
                    row[2] = compD.get(row[0])[1]
                    row[3] = compD.get(row[0])[2]
                    row[4] = compD.get(row[0])[3]
                    row[5] = compD.get(row[0])[4]
                    row[6] = compD.get(row[0])[5]
                    row[7] = compD.get(row[0])[6]
                    row[8] = compD.get(row[0])[7]


                    rows.updateRow(row)

            try:
                arcpy.env.addOutputsToMap = True
                mxd = arcpy.mapping.MapDocument("CURRENT")
                arcpy.MakeFeatureLayer_management(outName, os.path.basename(outName))
##                if len(retKind) == 1:
##                    symKind = ",".join(retKind)
##                    srcLyr = srcDir + os.sep + symKind + '.lyr'
##                    arcpy.ApplySymbologyFromLayer_management(os.path.basename(outName), srcLyr)
            except:
                errorMsg()



    AddMsgAndPrint('\n \n')

except:
    errorMsg()