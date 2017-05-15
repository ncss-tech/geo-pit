#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     15/05/2017
# Copyright:   (c) Adolfo.Diaz 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

## ===================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass



import os, arcpy, traceback
if __name__ == '__main__':

    try:

        AddMsgAndPrint("\nUser Name: " + os.environ['USERNAME'].replace('.',' '))
        AddMsgAndPrint("Computer Name: " + os.environ['COMPUTERNAME'])

        """ ------------------------------------- Get ESRI Product Name and Version -------------------------------------------"""
        if not arcpy.ProductInfo == 'NotInitialized':
            productName = str(arcpy.GetInstallInfo()['ProductName'])
            productVersion = str(arcpy.GetInstallInfo()['Version'])

            if productVersion.count('.') > 1:
                versionSplit = productVersion.split('.')
                versionKey = productName + str(versionSplit[0]) + "." + str(versionSplit[1])
            else:
                versionKey = productName + productVersion

            AddMsgAndPrint("ESRI Product: " + productName)
            AddMsgAndPrint("ESRI Version: " + productVersion)

        else:
            AddMsgAndPrint("\nNo ESRI License found on " + str(os.environ['COMPUTERNAME']) + " Exiting!",2)
            sys.exit()


        settingKey = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\\ESRI\\Desktop10.3\\ArcMap\\Settings",0,wreg.KEY_SET_VALUE)
        wreg.SetValueEx(settingKey,'CreateLocalCopyPath', 0, wreg.REG_SZ, 'c:\\Temp')
