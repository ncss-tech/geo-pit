#-------------------------------------------------------------------------------------------
# Name:        Insert NATSYM and MUNAME Value
#              Insert the National Mapunit Symbol and Mapunit Name to feature layer
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     2/21/2017
# Last Modified: 4/11/2017

# This tool will add the NASIS National Mapunti Symbol (NATSYM) and the SSURGO Mapunit
# Name (muname) to a user-provided spatial layer.  The NATSYM and MUNAME values are
# derived from Soil Data Access (SDA) using a couple of custom SQL queries written by
# Jason Nemecek, WI State Soil Scientist.  The query that is used depends on the fields
# in the input spatial layer.  The MUKEY field must be present.
#
# In order to receive NATSYM and MUNAME values from SDA, it must be first be determined
# what fields are available.  If both AREASYMBOL and MUKEY are available then the following
# SQL query will be used:
#
#       'SELECT mapunit.mukey, nationalmusym, muname '\
#       'FROM sacatalog ' \
#       'INNER JOIN legend ON legend.areasymbol = sacatalog.areasymbol AND sacatalog.areasymbol IN (' + values + ')' \
#       'INNER JOIN mapunit ON mapunit.lkey = legend.lkey'
#
# If only MUKEY is available then the following SQL query will be used:
#       SELECT m.mukey, m.nationalmusym, m.muname as natmusym from mapunit m where mukey in (" + values + ")
#
# Both queries return: ['mukey', 'natmusym','muname']
#
# The tool will handle Shapefiles and Geodatabase feature classes.

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    """prints messages to screen if the script is executed as
       a standalone script.  Otherwise, Adds tool message to the
       window geoprocessor.  Messages are color coded by severity."""

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
    """ Uses the traceback module to print the last known error message"""

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put the thousand seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ================================================================================================================
def FindField(layer,chkField):
    """ Check table or featureclass to see if specified field exists
        If fully qualified name is found, return that name; otherwise return False
        Set workspace before calling FindField"""

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

## ================================================================================================================
def GetUniqueValues(theInput,theField):
    """ This function creates a list of unique values from theInput using theField as
        the source field.  If the source field is AREASYMBOL than the list will be
        parsed into lists not exceeding 300 AREASYMBOL values.  If the source field is
        MUKEY than the list will be parsed into lists not exceeding 1000 MUKEY values.
        This list will ultimately be passed over to an SDA query."""

    try:
        featureCount = int(arcpy.GetCount_management(theInput).getOutput(0))

        # Inform the user of how the values are being compiled
        if bFGDBsapolygon:
            AddMsgAndPrint("\nCompiling a list of unique " + theField + " values from " + splitThousands(featureCount) + " polygons using SAPOLYGON feature class")
        elif bFGDBmapunit:
            AddMsgAndPrint("\nCompiling a list of unique " + theField + " values from " + splitThousands(featureCount) + " polygons using mapunit table")
        else:
            AddMsgAndPrint("\nCompiling a list of unique " + theField + " values from " + splitThousands(featureCount) + " records")

        # Unique value list
        valueList = list()

        """ ----------------- Iterate through all of the records in theInput to make a unique list-------------------"""
        arcpy.SetProgressor("step", "Compiling a list of unique " + theField + " values", 0, featureCount,1)
        if featureCount:

            with arcpy.da.SearchCursor(theInput, [theField]) as cur:
                for rec in cur:

                    if bAreaSym:
                        if not len(rec[0]) == 5:
                            AddMsgAndPrint("\t" + str(rec[0]) + " is not a valid AREASYMBOL",2)
                            continue

                    if not rec[0] in valueList:
                        valueList.append(rec[0])

                    arcpy.SetProgressorPosition()
            arcpy.ResetProgressor()

            AddMsgAndPrint("\tThere are " + splitThousands(len(valueList)) + " unique " + theField + " values")

        else:
            AddMsgAndPrint("\n\tThere are no features in layer.  Empty Geometry. EXITING",2)
            sys.exit()

        if not len(valueList):
            AddMsgAndPrint("\n\tThere were no" + theField + " values in layer. EXITING",2)
            sys.exit()

        # if number of Areasymbols exceed 300 than parse areasymbols
        # into lists containing no more than 300 areasymbols
        # MUKEY no more than 1000 values
        if bAreaSym:
            return parseValuesIntoLists(valueList,300)
        else:
            return parseValuesIntoLists(valueList)

    except:
        errorMsg()
        AddMsgAndPrint("\nCould not retrieve list of unique values from " + theField + " field",2)
        sys.exit()

## ===============================================================================================================
def parseValuesIntoLists(valueList,limit=1000):
    """ This function will parse values into manageable chunks that will be sent to an SDaccess query.
        This function returns a list containing lists of values comprised of no more than what
        the 'limit' is set to. Default Limit set to 1000, this will be used if the value list is
        made up of MUKEYS.  Limit will be set to 300 if value list contains areasymbols"""

    try:
        arcpy.SetProgressorLabel("\nDetermining the number of requests to send to SDaccess Server")

        i = 0 # Total Count
        j = 0 # Mukey count; resets whenever the 'limit' is reached.

        listOfValueStrings = list()  # List containing lists of values
        tempValueList = list()

        for value in valueList:
            i+=1
            j+=1
            tempValueList.append(str(value))

            # End of mukey list has been reached
            if i == len(valueList):
                listOfValueStrings.append(tempValueList)

            # End of mukey list NOT reached
            else:
                # max limit has been reached; reset tempValueList
                if j == limit:
                    listOfValueStrings.append(tempValueList)
                    tempValueList = []
                    j=0

        del i,j,tempValueList

        if not len(listOfValueStrings):
            AddMsgAndPrint("\tCould not Parse value list into manageable sets",2)
            sys.exit()

        else:
            #AddMsgAndPrint("\t" + str(len(listOfValueStrings)) + " request(s) are needed to obtain NATSYM values for this layer")
            return listOfValueStrings

    except:
        AddMsgAndPrint("Unhandled exception (parseValuesIntoLists)", 2)
        errorMsg()
        sys.exit()

## ===================================================================================
def getNATMUSYM(listsOfValues, featureLayer):
    """POST request which uses urllib and JSON to send query to SDM Tabular Service and
       returns data in JSON format.  Sends a list of values (either MUKEYs or Areasymbols)
       and returns NATSYM and MUNAME values.  If MUKEYS are submitted a pair of values are returned
       [MUKEY,NATMUSYM].  If areasymbols are submitted than a list of all of MUKEY,NATSYM
       pairs that pertain to that areasymbol are returned.
       Adds NATMUSYM and MUNAME field to inputFeature layer if not present and populates."""

    try:
        AddMsgAndPrint("\nSubmitting " + str(len(listsOfValues)) + " request(s) to Soil Data Access")
        arcpy.SetProgressor("step", "Submitting request(s) to Soil Data Access", 0, len(listsOfValues),1)

        # Total Count of values
        iNumOfValues = 0
        iRequestNum = 1

        # master mukey:natmusym,muname dictionary
        natmusymDict = dict()

        # SDMaccess URL
        URL = "https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest"

        """ ---------------------------------------- Iterate through lists of unique values to submit requests for natsym ------------------------------"""
        # Iterate through each list that has been parsed for no more than 1000 mukeys
        for valueList in listsOfValues:
            arcpy.SetProgressorLabel("Requesting NATSYM and MUNAME values for " + splitThousands(len(valueList)) + " " + sourceField + "(s). Request " + str(iRequestNum) + " of " + str(len(listsOfValues)))

            iNumOfValues+=len(valueList)
            iRequestNum+=1

            # convert the list into a comma seperated string
            ## values = ",".join(valueList)
            values = str(valueList)[1:-1]

            # use this query if submitting request by AREASYMBOL
            if bAreaSym:
                sQuery = 'SELECT mapunit.mukey, nationalmusym, muname '\
                          'FROM sacatalog ' \
                          'INNER JOIN legend ON legend.areasymbol = sacatalog.areasymbol AND sacatalog.areasymbol IN (' + values + ')' \
                          'INNER JOIN mapunit ON mapunit.lkey = legend.lkey'

            # use this query if submitting request by MUKEY
            else:
                sQuery = "SELECT m.mukey, m.nationalmusym, m.muname as natmusym from mapunit m where mukey in (" + values + ")"
                #sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from legend AS l INNER JOIN mapunit AS m ON l.lkey=m.mukey AND m.mukey in (" + mukeys + ")"

            # Create request using JSON, return data as JSON
            dRequest = dict()
            dRequest["FORMAT"] = "JSON"
            ##dRequest["FORMAT"] = "JSON+COLUMNNAME+METADATA"
            dRequest["QUERY"] = sQuery
            jData = json.dumps(dRequest)

            # Send request to SDA Tabular service using urllib2 library
            req = urllib2.Request(URL, jData)

            """ --------------------------------------  Try connecting to SDaccess to read JSON response - You get 3 Attempts ------------------------"""
            # ---------------------------- First Attempt
            try:
                resp = urllib2.urlopen(req)
            except:

                # ---------------------------- Second Attempt
                try:
                    AddMsgAndPrint("\t2nd attempt at requesting data")
                    resp = urllib2.urlopen(req)
                except:

                    # ---------------------------- Last Attempt
                    try:
                        AddMsgAndPrint("\t3rd attempt at requesting data")
                        resp = urllib2.urlopen(req)

                    except URLError, e:
                        AddMsgAndPrint("\n\n" + sQuery,2)
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

            """ Sample Output:
                {u'Table': [[u'mukey', u'natmusym',u'muname'],
                        [u'ColumnOrdinal=0,ColumnSize=4,NumericPrecision=10,NumericScale=255,ProviderType=Int,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlInt32,DataTypeName=int',
                         u'ColumnOrdinal=1,ColumnSize=6,NumericPrecision=255,NumericScale=255,ProviderType=VarChar,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlString,DataTypeName=varchar'],
                        [u'753571', u'2tjpl', u'Amery sandy loam, 6 to 12 percent slopes'],
                        [u'753574', u'2szdz', u'Amery sandy loam, 1 to 6 percent slopes'],
                        [u'2809844', u'2v3f0', u'Grayling sand, 12 to 30 percent slopes']]}"""

            # Nothing was returned from SDaccess
            if not "Table" in data:
                AddMsgAndPrint("\tWarning! NATMUSYM values were not returned for any of the " + sourceField + "  values.  Possibly OLD mukey values.",2)
                continue

            # Add the mukey:natmusym,muname Values to the master dictionary
            for pair in data["Table"]:
                natmusymDict[pair[0]] = (pair[1],pair[2])

            del jData,req,resp,jsonString,data
            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

        """ -----------------------------------------  Add NATMUSYM and MUNAME to the Feature Layer if not present -----------------------------------------"""
        arcpy.SetProgressorLabel("Adding NATSYM and MUNAME fields if they don't exist")
        if not "muname" in [f.name.lower() for f in arcpy.ListFields(featureLayer)]:
            arcpy.AddField_management(featureLayer,'MUNAME','TEXT','#','#',175,'Mapunit Name')

        if not "natmusym" in [f.name.lower() for f in arcpy.ListFields(featureLayer)]:
            arcpy.AddField_management(featureLayer,'NATMUSYM','TEXT','#','#',23,'National MU Symbol')

        mukeyField = FindField(featureLayer,"MUKEY")

        """ -----------------------------------------  Add MUKEY Attribute Index to the Feature Layer if not present -----------------------------------------"""
##        # Get list of indexes for the feature Layer
##        attrIndexes = arcpy.ListIndexes(featureLayer)
##        bMukeyIndex = False
##
##        for index in attrIndexes:
##            for field in index.fields:
##                if field.name == "MUKEY":
##                    bMukeyIndex = True
##
##        if not bMukeyIndex:
##            arcpy.AddIndex_management(featureLayer,mukeyField,mukeyField + "_Index")
##            AddMsgAndPrint("\nSuccessfully added an attribute index to " + mukeyField + " field",0)

        """ ----------------------------------------- Import NATSYM and MUSYM values into Feature Layer by MUKEY -----------------------------------------"""
        arcpy.SetProgressorLabel("Importing NATMUSYM and MUNAME values")
        AddMsgAndPrint("\nImporting NATMUSYM and MUNAME values",0)
        featureCount = int(arcpy.GetCount_management(featureLayer).getOutput(0))
        arcpy.SetProgressor("step", "Importing NATMUSYM  and Mapunit Name Values into " + os.path.basename(featureLayer) + " layer", 0, featureCount,1)

        """ itereate through the feature records and update the NATMUSYM and MUNAME field
            {'2809844': ('2v3f0', 'Grayling sand, 12 to 30 percent slopes'),
             '753571': ('2tjpl', 'Amery sandy loam, 6 to 12 percent slopes'),
             '753574': ('2szdz', 'Amery sandy loam, 1 to 6 percent slopes')}"""

        with arcpy.da.UpdateCursor(featureLayer, [mukeyField,'NATMUSYM','MUNAME']) as cursor:

            for row in cursor:

                uNatmusym = natmusymDict.get(row[0])[0]
                uMuName = natmusymDict.get(row[0])[1]
                arcpy.SetProgressorLabel("Importing Values: " + row[0] + " : " + uNatmusym + "--" + uMuName)

                try:
                    row[1] = uNatmusym
                    row[2] = uMuName
                    cursor.updateRow(row)

                    del uNatmusym,uMuName
                    arcpy.SetProgressorPosition()

                except:
                    AddMsgAndPrint("\tInvalid MUKEY: " + row[0],2)
                    continue

        arcpy.ResetProgressor()

        AddMsgAndPrint("\tSuccessfully populated 'NATMUSYM' and 'MUNAME' values for " + splitThousands(featureCount) + " records \n",0)

        if bAreaSym:
            AddMsgAndPrint("\tThere are " + splitThousands(len(natmusymDict))+ " unique mapunits")

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
import sys, string, os, locale, arcpy, traceback, urllib2, httplib, json, re, socket
from urllib2 import urlopen, URLError, HTTPError
from arcpy import env

if __name__ == '__main__':

    try:
        inputFeature = arcpy.GetParameterAsText(0)

        bFGDBmapunit = False
        bFGDBsapolygon = False
        bAreaSym = False
        source = inputFeature

        """ ------------------------------------------- MUKEY field must be present ----------------------------------------------"""
        if not FindField(inputFeature,"MUKEY"):
            AddMsgAndPrint("\n\"MUKEY\" field is missing from input feature!  EXITING!",2)
            sys.exit()

        """ -------------------------------- Describe Data to determine the source field of the unique values ---------------------"""
        theDesc = arcpy.Describe(inputFeature)
        theDataType = theDesc.dataType
        theName = theDesc.name
        theElementType = theDesc.dataElementType

        """ -------------------------------------------- Input feature is a Shapefile or Raster """
        if theElementType.lower() in ('deshapefile','derasterdataset'):

            if FindField(inputFeature,"AREASYMBOL"):
                sourceField = "AREASYMBOL"
                bAreaSym = True

            elif FindField(inputFeature,"MUKEY"):
                sourceField = "MUKEY"
            else:
                AddMsgAndPrint("\t\"AREASYMBOL\" and \"MUKEY\" fields are missing from " + theName  + " layer -- Need one or the other to continue.  EXITING!",2)
                sys.exit()

            """ ------------------------------------- Input feature is a feature class"""
        elif theElementType.lower().find('featureclass') > -1:

            theFCpath = theDesc.catalogPath
            theFGDBpath = theFCpath[:theFCpath.find(".gdb")+4]
            arcpy.env.workspace = theFGDBpath

            # -------------------------------------- Use AREASYMBOL if available
            # summarize areasymbols from SAPOLYGON layer first.
            # This is the fastest method since it is the records
            if arcpy.ListFeatureClasses("SAPOLYGON", "Polygon"):
                bFGDBsapolygon = True
                source = theFGDBpath + os.sep + "SAPOLYGON"
                sourceField = "AREASYMBOL"
                bAreaSym = True

            # summarize AREASYMBOL from input feature class.
            # this method is the same as summarizing by MUKEY
            # but still preferred over MUKEY b/c of fewer
            # requests to SDA
            elif FindField(inputFeature,"AREASYMBOL"):
                sourceField = "AREASYMBOL"
                bAreaSym = True

            # ----------------------------------------- Use MUKEYS
            # Use mapunit table to collect MUKEYs.  This is
            # preferred way to summarize MUKEYs b/c of fewer
            # records.
            elif arcpy.ListTables("mapunit", "ALL"):
                bFGDBmapunit = True
                source = theFGDBpath + os.sep + "mapunit"
                sourceField = "MUKEY"
                bFGDBmapunit = True

            # mapunit table was not found - summarize MUKEYS from
            # input feature.  Least Ideal since it is the slowest.
            elif FindField(inputFeature,"MUKEY"):
                sourceField = "MUKEY"
            else:
                AddMsgAndPrint("\t\"AREASYMBOL\" and \"MUKEY\" fields are missing from feature class! -- Need one or the other to continue.  EXITING!",2)
                sys.exit()

        # Input Feature data type not recognized
        else:
            AddMsgAndPrint("\nInvalid data type: " + theDataType.lower(),2)
            sys.exit()

    	""" -------------------------------  Get list of unique values from the specified source field  ---------------------------------"""
        uniqueValueList = GetUniqueValues(source,sourceField)

        """ --------------------------------- Populate input Feature with NATMUSYM and MUNAME values-------------------------------------"""
        if not getNATMUSYM(uniqueValueList,inputFeature):
            AddMsgAndPrint("\nFailed to update NATSYM field",2)

    except:
        errorMsg()
