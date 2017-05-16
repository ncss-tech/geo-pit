#-------------------------------------------------------------------------------
# Name:        Set Distributed Geodatabase Directory
# Purpose:     Updating default distributed GDB registry path to user determined directory
#
# Author:      Adolfo.Diaz
#
# Created:     5/16/2017
# Copyright:   (c) Adolfo.Diaz 2017

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
        AddMsgAndPrint("\n" + theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass
## ===================================================================================

## ====================================== Main Body ==================================
import os, sys, arcpy, traceback
import _winreg as wreg
if __name__ == '__main__':

    try:
        userDirectory = arcpy.GetParameterAsText(0)

        if not os.path.exists(userDirectory):
            AddMsgAndPrint(userDirectory + " does NOT exist!",2)
            exit()

        AddMsgAndPrint("\nUser Name: " + os.environ['USERNAME'].replace('.',' '))
        AddMsgAndPrint("Computer Name: " + os.environ['COMPUTERNAME'])

        """ ------------------------------------- Get ESRI Product Name and Version -------------------------------------------"""
        if not arcpy.ProductInfo == 'NotInitialized':
            productName = str(arcpy.GetInstallInfo()['ProductName'])
            productVersion = str(arcpy.GetInstallInfo()['Version'])

            if productVersion.count('.') > 1:
                versionSplit = productVersion.split('.')
                versionKey = productName + str(versionSplit[0]) + "." + str(versionSplit[1])
                del versionSplit

            else:
                versionKey = productName + productVersion

            AddMsgAndPrint("ESRI Product: " + productName)
            AddMsgAndPrint("ESRI Version: " + productVersion)

        else:
            AddMsgAndPrint("\nNo ESRI License found on " + str(os.environ['COMPUTERNAME']) + " Exiting!",2)
            sys.exit()

        """ ---------------------------------------- Connect to the registry and modify keys ------------------------"""
        # set openKey parameters
        hKEYconstant = wreg.HKEY_CURRENT_USER
        subKeyPath = "Software" + os.sep + "ESRI" + os.sep + versionKey + os.sep + "ArcMap" + os.sep + "Settings"
        accessRights = wreg.KEY_ALL_ACCESS
        newKey = 'CreateLocalCopyPath'

        try:
            settingKey = wreg.OpenKey(hKEYconstant, subKeyPath, 0, accessRights)
        except WindowsError:
            AddMsgAndPrint("\nRegistry Key: " + subKeyPath + " does NOT exist",2)
            exit()
        except:
            errorMsg()

        try:
            # if the newKey exists check the current value.
            existingKeyValue = wreg.QueryValueEx(settingKey,newKey)[0]

            if existingKeyValue == userDirectory:
                AddMsgAndPrint("\nArcMap registry key \"CreateLocalCopyPath\" is already set to: " + userDirectory,1)
                AddMsgAndPrint("No update necessary\n",1)
            else:
                wreg.SetValueEx(settingKey,newKey, 0, wreg.REG_SZ, userDirectory)
                AddMsgAndPrint("\nSuccessfully updated ArcMap registry key \"CreateLocalCopyPath\" and set the value to:")
                AddMsgAndPrint("\t" + userDirectory + "\n")

        except:
            wreg.SetValueEx(settingKey,newKey, 0, wreg.REG_SZ, userDirectory)
            AddMsgAndPrint("\nSuccessfully created ArcMap registry key \"CreateLocalCopyPath\" and set the value to:")
            AddMsgAndPrint("\t" + userDirectory + "\n")

        wreg.CloseKey(settingKey)

    except:
        errorMsg()
