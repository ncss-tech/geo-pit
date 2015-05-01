#-------------------------------------------------------------------------------
# Name:        module4
# Purpose:
#
# Author:      Charles.Ferguson
#
# Created:     25/10/2013
# Copyright:   (c) Charles.Ferguson 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

class MyError(Exception):
    pass


def errorMsg():

    try:

        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + " \n"
        arcMsg = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        PrintMsg(theMsg, 2)
        PrintMsg(arcMsg, 2)

    except:

        PrintMsg("Unhandled error in errorMsg method", 2)



def PrintMsg(msg, severity=0):

    try:

        for string in msg.split('\n'):
            if severity == 0:
                arcpy.AddMessage(string)

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                arcpy.AddError(" \n" + string)

    except:
        pass





import sys, os, arcpy, zipfile, traceback

try:


    rootDir = sys.argv[1]



    crossCLst = list()
    if os.path.isdir(rootDir):
        pntlLst = os.listdir(rootDir)
        for e in pntlLst:
            if os.path.isdir(rootDir + os.sep + e) and len(e) == 5 and e[:2].isalpha() and e[2:].isdigit():
                crossCLst.append(e.lower())

    crossCnt = len(crossCLst)


    zipSSA = []

    paramSSA = str(arcpy.GetParameterAsText(1))
    paramLst = list(paramSSA.split(';'))
    paramCnt = len(paramLst)

    arcpy.SetProgressor('step', 'Creating Archives...', 0, len(paramLst), 1)
    for eSSA in paramLst:
        zipSSA.append(str(arcpy.GetParameterAsText(0).strip(';')) + os.sep + eSSA)

    for SSA in zipSSA:
        arcpy.SetProgressorLabel('Archiving: ' + os.path.basename(SSA))
        PrintMsg(' \n ' + 'Creating zip archive for ' + os.path.basename(SSA) + '\n', 0)

        try:
            with zipfile.ZipFile(SSA.lower() + '.zip', 'w', zipfile.ZIP_DEFLATED) as outZip:
                for dirpath, dirnames, filenames in os.walk(SSA):
                    #outZip.write(dirpath)
                    for filename in filenames:
                        outZip.write(os.path.join(dirpath, filename), os.path.basename(SSA.lower()) + os.sep + filename)
            outZip.close()

        except:
            PrintMsg("Problems with " + SSA)
            continue

        arcpy.SetProgressorPosition()
    PrintMsg(' \n ')

    if paramCnt <> crossCnt:
        paramSet = set(paramLst)
        cCset = set(crossCLst)
        unAvLst = list(cCset.difference(paramSet))
        unAvLst.sort()
        PrintMsg(' \n ')
        unAvMsg = ('The following sub-folders in the Root Folder Folder appear to be SSURGO directories but are missing required files and were not available to the tool: \n \n' +'\t' + ','.join(unAvLst))
        PrintMsg(unAvMsg, 2)
        PrintMsg(' \n \n')
except:
    PrintMsg("Failed")
    errorMsg()