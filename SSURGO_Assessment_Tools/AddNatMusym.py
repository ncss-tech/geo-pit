#-------------------------------------------------------------------------------
# Name:        AddNATMusym
#              Add National Mapunit Symbol
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     2/21/2017
# Last Modified: 2/21/2017

# Code copied from SDA_CustomQuery script and modified to get NationalMusym from Soil Data Access
# Steve Peaslee 10-18-2016

# Completely modified by Adolfo Diaz 02/21/2017 to update a user specific feature layer.
# Due to limitations from SDMaccess in terms of the number of mukeys it can accept the total
# number of mukeys need to be split into lists of no more than 1000 mukeys.
#

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

## ================================================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ================================================================================================================
def GetMukeys(theInput):
    # Create a list of unique MUKEY values from spatial layer for use in SDA query

    try:
        AddMsgAndPrint("\nCompiling a list of unique MUKEY values from " + splitThousands(int(arcpy.GetCount_management(theInput).getOutput(0))),0)
        arcpy.SetProgressorLabel("Compiling a list of unique MUKEY values from " + splitThousands(int(arcpy.GetCount_management(theInput).getOutput(0))))

        # Describe the input data
        theDesc = arcpy.Describe(theInput)
        theDataType = theDesc.dataType

        # Get Featureclass and total count
        if theDataType.lower() == "featurelayer":
            theFC = theDesc.featureClass.catalogPath
            featureCount = int(arcpy.GetCount_management(theFC).getOutput(0))

        elif theDataType.lower() in ["featureclass", "shapefile"]:
            theFC = theInput
            featureCount = int(arcpy.GetCount_management(theInput).getOutput(0))

        else:
            AddMsgAndPrint("\nUnknown data type: " + theDataType.lower(),2)
            sys.exit()

        mukeyField = FindField(theFC,"MUKEY")
        mukeyList = list()

        # Exit if "MUKEY" doesn't exist
        if not mukeyField:
            AddMsgAndPrint("\t\"MUKEY\" field is missing! -- Cannot get MUKEY Values.  EXITING!",2)
            sys.exit()

        arcpy.SetProgressor("step", "Compiling a list of unique MUKEY values", 0, int(arcpy.GetCount_management(theInput).getOutput(0)),1)
        if featureCount:

            with arcpy.da.SearchCursor(theInput, [mukeyField]) as cur:
                for rec in cur:
                    if not rec[0] in mukeyList:
                        mukeyList.append(rec[0])

                    arcpy.SetProgressorPosition()

            arcpy.ResetProgressor()

            AddMsgAndPrint("\tThere are " + splitThousands(len(mukeyList)) + " unique MUKEY values")

        else:
            AddMsgAndPrint("\n\tThere are no features in layer.  Empty Geometry. EXITING",2)
            sys.exit()

        if not len(mukeyList):
            AddMsgAndPrint("\n\tThere are no MUKEYS in layer. EXITING",2)
            sys.exit()

        return parseMukeysIntoLists(mukeyList)

    except:
        errorMsg()
        AddMsgAndPrint("\nCould not retrieve list of MUKEYs",2)
        sys.exit()

## ================================================================================================================
def FindField(layer,chkField):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that name; otherwise return ""
    # Set workspace before calling FindField

    try:

        if arcpy.Exists(layer):

            theDesc = arcpy.Describe(layer)
            theFields = theDesc.fields
            theField = theFields[0]

            for theField in theFields:

                # Parses a fully qualified field name into its components (database, owner name, table name, and field name)
                parseList = arcpy.ParseFieldName(theField.name) # (null), (null), (null), MUKEY

                # choose the last component which would be the field name
                theFieldname = parseList.split(",")[len(parseList.split(','))-1].strip()  # MUKEY

                if theFieldname.upper() == chkField.upper():
                    return theField.name

            return False

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return False

    except:
        errorMsg()
        return False

## ===============================================================================================================
def parseMukeysIntoLists(mukeyList):
    """ This function will parse MUKEY values into manageable chunks that will be sent to the SDaccess query.
        This function returns lists of mukey lists no larger than 1000 mukeys."""

    try:
        arcpy.SetProgressorLabel("\nDetermining the number of requests to send to SDaccess Server")

        i = 0 # Total Count
        j = 0 # Mukey count; resets at 1000

        listOfMukeyStrings = list()  # List containing pedonIDstring lists; individual lists are comprised of about 265 pedons
        tempMukeyList = list()

        for mukey in mukeyList:
            i+=1
            j+=1
            tempMukeyList.append(mukey)

            # End of mukey list has been reached
            if i == len(mukeyList):
                listOfMukeyStrings.append(tempMukeyList)

            # End of mukey list NOT reached
            else:
                # 1000 mukeys have been reached; reset tempMukeyList
                if j == 1000:
                    listOfMukeyStrings.append(tempMukeyList)
                    tempMukeyList = []
                    j=0

        del i,j,tempMukeyList

        if not len(listOfMukeyStrings):
            AddMsgAndPrint("\tCould not Parse MUKEY list into manageable sets",2)
            sys.exit()

        else:
            AddMsgAndPrint("\t" + str(len(listOfMukeyStrings)) + " request(s) are needed to obtain NATSYM values for this layer")
            return listOfMukeyStrings

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        sys.exit()

## ===================================================================================
def getNATMUSYM(listsOfMUKEYs, featureLayer):
    # POST REST which uses urllib and JSON
    # Send query to SDM Tabular Service, returning data in JSON format
    # Sends a list of MUKEYS and returns a pair for each MUKEY [MUKEY,NATMUSYM]
    # Adds NATMUSYM field to inputFeature layer if not present.

    try:

        AddMsgAndPrint("\nSubmitting " + str(len(listsOfMUKEYs)) + " request(s) to the SDMaccess")
        arcpy.SetProgressor("step", "Sending tabular request to Soil Data Mart Access", 0, len(listsOfMUKEYs),1)

        # Total Count of MUKEYs
        iNumOfMukeys = 0
        iRequestNum = 1

        # master mukey:natmusym dictionary
        natmusymDict = dict()

        # SDMaccess URL
        URL = "https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest"

        """ ---------------------------------------- Iterate through lists of MUKEYS to submit requests for natsym ------------------------------"""
        # Iterate through each MUKEY list that has been parsed for no more than 1000 mukeys
        for mukeyList in listsOfMUKEYs:

            arcpy.SetProgressorLabel("Requesting NATSYM values for " + str(len(mukeyList)) + " mukeys. Request " + str(iRequestNum) + " of " + str(len(listsOfMUKEYs)))

            iNumOfMukeys+=len(mukeyList)
            iRequestNum+=1

            # convert the list into a comma seperated string
            mukeys = ",".join(mukeyList)

            # 'SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (753574,2809844,753571)'
            sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (" + mukeys + ")"
            #sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from legend AS l INNER JOIN mapunit AS m ON l.lkey=m.mukey AND m.mukey in (" + mukeys + ")"

            # Create request using JSON, return data as JSON
            dRequest = dict()
            dRequest["FORMAT"] = "JSON"
            #dRequest["FORMAT"] = "JSON+COLUMNNAME+METADATA"
            dRequest["QUERY"] = sQuery
            jData = json.dumps(dRequest)

            # Send request to SDA Tabular service using urllib2 library
            req = urllib2.Request(URL, jData)

            """ --------------------------------------  Try connecting to SDaccess to read JSON response - You get 3 tries ------------------------"""
            try:
                resp = urllib2.urlopen(req)
            except:
                try:
                    AddMsgAndPrint("\t2nd attempt at requesting data")
                    resp = urllib2.urlopen(req)

                except:
                    try:
                        AddMsgAndPrint("\t3rd attempt at requesting data")
                        resp = urllib2.urlopen(req)

                    except URLError, e:
                        AddMsgAndPrint(sQuery)
                        if hasattr(e, 'reason'):
                            AddMsgAndPrint("\n\t" + URL,2)
                            AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

                        elif hasattr(e, 'code'):
                            AddMsgAndPrint("\n\t" + URL,2)
                            AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

                        return False

                    except socket.timeout, e:
                        AddMsgAndPrint("\n\t" + URL,2)
                        AddMsgAndPrint("\tServer Timeout Error", 2)
                        return False

                    except socket.error, e:
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                        return False

                    except httplib.BadStatusLine:
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                        return False

            jsonString = resp.read()
            data = json.loads(jsonString)

            """{u'Table': [[u'mukey', u'natmusym'],
                        [u'ColumnOrdinal=0,ColumnSize=4,NumericPrecision=10,NumericScale=255,ProviderType=Int,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlInt32,DataTypeName=int',
                         u'ColumnOrdinal=1,ColumnSize=6,NumericPrecision=255,NumericScale=255,ProviderType=VarChar,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlString,DataTypeName=varchar'],
                        [u'753571', u'2tjpl'],
                        [u'753574', u'2szdz'],
                        [u'2809844', u'2v3f0']]}"""

            # Nothing was returned from SDaccess
            if not "Table" in data:
                AddMsgAndPrint("\tWarning! NATMUSYM value were not returned for any of the MUKEY values.  Possibly OLD mukey values.",2)
                continue

            # Add the mukey:natmusym Values to the master dictionary
            for pair in data["Table"]:
                natmusymDict[pair[0]] = pair[1]

            del jData,req,resp,jsonString,data

##        # Remove the first 2 items from dataList: fields and column metadata-columninfo
##        """ [[u'753571', u'2tjpl'], [u'753574', u'2szdz'], [u'2809844', u'2v3f0']] """
##        columnNames = dataList.pop(0)  # [u'mukey', u'natmusym']
##        columnInfo = dataList.pop(0)

        """ --------------------------------------  Check the number of mukeys submitted vs. natmusym values received -----------------------------"""
        # Warn user about a discrepancy in mukey count
        if iNumOfMukeys != len(natmusymDict):
            AddMsgAndPrint("\tWarning! NATMUSYM value was not returned for the following " + splitThousands(len(mukeyList) - len(dataList)) + " MUKEYS", 1)

            # subtract both lists to see which MUKEYS had no NATSYM
            iNoMatches = list(set(mukeyList) - set([f[0] for f in dataList]))
            AddMsgAndPrint("\n\t\t" + str(iNoMatches),2)

        """ --------------------------------------------------  Add NATMUSYM to the Feature Layer ---------------------------------------------------"""
        # Add the 'NATMUSYM' field to inputFeature if not present
        if not "natmusym" in [f.name.lower() for f in arcpy.ListFields(featureLayer)]:
            arcpy.AddField_management(featureLayer,'NATMUSYM','TEXT','#','#',23,'National MU Symbol')

        mukeyField = FindField(featureLayer,"MUKEY")

        AddMsgAndPrint("\nImporting NATMUSYM Values",0)
        arcpy.SetProgressor("step", "Importing NATMUSYM Values into " + os.path.basename(featureLayer) + " layer", 0, len(natmusymDict),1)

        # itereate through mukey,natmusym values and update the NATMUSYM field
        # [[u'753571', u'2tjpl'], [u'753574', u'2szdz'], [u'2809844', u'2v3f0']]
        for rec in natmusymDict:

            mukey,natmusym = rec,natmusymDict[rec]
            arcpy.SetProgressorLabel("Importing NATMUSYM Values: " + mukey + " : " + natmusym)

            expression = arcpy.AddFieldDelimiters(featureLayer,mukeyField) + " = '" + mukey + "'"
            with arcpy.da.UpdateCursor(featureLayer, 'NATMUSYM', where_clause=expression) as cursor:

                for row in cursor:
                    row[0] = natmusym

                    cursor.updateRow(row)

            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

        AddMsgAndPrint("\tSuccessfully populated 'NATMUSYM' values for " + splitThousands(int(arcpy.GetCount_management(featureLayer).getOutput(0))) + " polygons \n",0)
        return True

    except urllib2.HTTPError:
        errorMsg()
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcpy, traceback, urllib2, httplib, json, re
from urllib2 import urlopen, URLError, HTTPError
from arcpy import env

if __name__ == '__main__':

    inputFeature = arcpy.GetParameterAsText(0)
    #inputFeature = r'C:\Temp\Export_Output.shp'

    try:

    	# Get list of unique mukeys for use in tabular request
        mukeyList = GetMukeys(inputFeature)

        # populate inputFeature with NATMUSYM
        if not getNATMUSYM(mukeyList, inputFeature):
            AddMsgAndPrint("\nFailed to update NATSYM field",2)

    except:
        errorMsg()