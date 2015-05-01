# SSURGO_BatchDownload.py
#
# Download the most current SSURGO data from Web Soil Survey by Soil Survey Region.  A buffer of
# about 2 surveys around the region will be included.  This tool will normally be used in conjunction
# with the "Create Regional Spatial Geodatabase" tool.
#
# Uses Soil Data Access query to generate Areaname and version date for areasymbols being downloaded.
#
# This tool is specific to Soil Survey Regions in that a master table that contains SSA ownership
# is referenced.
#
# A SSURGO Access template will always be downloaed.  If an existing dataset is found in the outputfolder
# the dates will not be compared.  The dataset will simply be overwritten.
#
# The unzipped folder will be renamed to match the NRCS Geodata naming convention for soils. i.e soils_wi025
#
#
# 01-09-2014
# Steve Peaslee and Adolfo Diaz
#
## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # Adds tool message to the geoprocessor
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line

    #print msg

    try:
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
def Number_Format(num, places=0, bCommas=True):
# Format a number according to locality and given places

    try:

        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)
        else:
            theNumber = locale.format("%.*f", (places, num), False)

        return theNumber

    except:
        errorMsg()
        return ""

## ===================================================================================
def getRegionalAreaSymbolList(ssaTable, masterTable, userRegionChoice):
# Returns the actual region number from the first parameter.
# If the value has 1 integer than it should total 8 characters,
# last character will be returned.  Otherwise, value has 2 integers
# and last 2 will be returned.  Also return the real # of regional SSA ownership
# [u'WI001, u'WI003']

    try:
        areaSymbolList = []

        where_clause = "\"Region_Download\" = '" + userRegionChoice + "'"

        with arcpy.da.SearchCursor(ssaTable, ('AREASYMBOL'), where_clause) as cursor:
            for row in cursor:
                areaSymbolList.append(row[0])

        if len(userRegionChoice) == 8:
            region = userRegionChoice[-1:]
        else:
            region = userRegionChoice[-2:]

        where_clause = "\"Region\" = " + str(region)
        numOfRegionalSSA = len([row[0] for row in arcpy.da.SearchCursor(masterTable, ('AREASYMBOL'), where_clause)])

        return areaSymbolList,numOfRegionalSSA

    except:
        errorMsg
        return ""

## ===================================================================================
def getSDMaccessDict(areaSymbol):

    import httplib
    import xml.etree.cElementTree as ET

    try:

        # Create empty list that will contain list of 'Areasymbol, AreaName
        sdmAccessDict = dict()

        #sQuery = "SELECT AREASYMBOL, AREANAME, CONVERT(varchar(10), [SAVEREST], 126) AS SAVEREST FROM SASTATUSMAP WHERE AREASYMBOL LIKE '" + areaSymbol + "' AND SAPUBSTATUSCODE = 2 ORDER BY AREASYMBOL"
        sQuery = "SELECT AREASYMBOL, AREANAME, CONVERT(varchar(10), [SAVEREST], 126) AS SAVEREST FROM SASTATUSMAP WHERE AREASYMBOL LIKE '" + areaSymbol + "' ORDER BY AREASYMBOL"

        # This RunQuery runs your own custom SQL or SQL Data Shaping query against the Soil Data Mart database and returns an XML
        # data set containing the results. If an error occurs, an exception will be thrown.
        sXML = """<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
          <soap12:Body>
            <RunQuery xmlns="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
              <Query>""" + sQuery + """</Query>
            </RunQuery>
          </soap12:Body>
        </soap12:Envelope>"""

        dHeaders = dict()
        dHeaders["Host"] = "sdmdataaccess.nrcs.usda.gov"
        #dHeaders["User-Agent"] = "NuSOAP/0.7.3 (1.114)"
        #dHeaders["Content-Type"] = "application/soap+xml; charset=utf-8"
        dHeaders["Content-Type"] = "text/xml; charset=utf-8"
        dHeaders["Content-Length"] = len(sXML)
        dHeaders["SOAPAction"] = "http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx/RunQuery"
        sURL = "SDMDataAccess.nrcs.usda.gov"

        try:

            # Create SDM connection to service using HTTP
            conn = httplib.HTTPConnection(sURL, 80)

            # Send request in XML-Soap
            conn.request("POST", "/Tabular/SDMTabularService.asmx", sXML, dHeaders)

            # Get back XML response
            response = conn.getresponse()
            xmlString = response.read()

            # Close connection to SDM
            conn.close()

        except HTTPError, e:
            PrintMsg("\t\t" + areaSymbol + " encountered HTTP Error querying SDMaccess (" + str(e.code) + ")", 2)
            sleep(i * 3)
            return ""

        except URLError, e:
            PrintMsg("\t\t" + areaSymbol + " encountered URL Error querying SDMaccess: " + str(e.reason), 2)
            sleep(i * 3)
            return ""

        except socket.timeout, e:
            PrintMsg("\t\t" + areaSymbol + " encountered server timeout error querying SDMacess", 2)
            sleep(i * 3)
            return ""

        except socket.error, e:
            PrintMsg("\t\t" + areaSymbol + " encountered SDMaccess connection failure", 2)
            sleep(i * 3)
            return ""

        except:
            errorMsg
            return ""

        # Convert XML to tree format
        tree = ET.fromstring(xmlString)

        areasym = ""
        areaname = ""
        date = ""

        # Iterate through XML tree, finding required elements...
        for rec in tree.iter():

            if rec.tag == "AREASYMBOL":
                areasym = str(rec.text)

            if rec.tag == "AREANAME":
                areaname = str(rec.text)

            if rec.tag == "SAVEREST":
                # get the YYYYMMDD part of the datetime string
                # then reformat to match SQL query
                date = str(rec.text).split(" ")[0]

        sdmAccessDict[areaSymbol] = (areasym + "|" + str(date) + "|" + areaname)

        del sQuery, sXML, dHeaders, sURL, conn, response, xmlString, tree, areasym,  areaname, date

        return sdmAccessDict

    except:
        errorMsg
        return ""

## ===================================================================================
def GetDownload(areasym, surveyDate):
    # download survey from Web Soil Survey URL and return name of the zip file
    # want to set this up so that download will retry several times in case of error
    # return empty string in case of complete failure. Allow main to skip a failed
    # survey, but keep a list of failures
    #
    # As of Aug 2013, states are using either a state or US 2003 template databases which would
    # result in two possible zip file names. If that changes in the future, these URL will fail

    # UPDATED: 1/9/2014 In this version, only the most current SSURGO dataset is downloaded
    # with a SSURGO Access Template
    # example URL without Template:
    # http://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_NE001_[2012-08-10].zip
    #

    # create URL string from survey string and WSS 3.0 cache URL
    baseURL = "http://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/"

    try:

        # create two possible zip file URLs, depending on the valid Template databases available
        # Always download dataset with a SSURGO Access template.
        zipName1 = "wss_SSA_" + areaSym + "_soildb_US_2003_[" + surveyDate + "].zip"  # wss_SSA_WI025_soildb_US_2003_[2012-06-26].zip
        zipName2 = "wss_SSA_" + areaSym + "_soildb_" + areaSym[0:2] + "_2003_[" + surveyDate + "].zip"  # wss_SSA_WI025_soildb_WI_2003_[2012-06-26].zip

        zipURL1 = baseURL + zipName1  # http://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_WI025_soildb_US_2003_[2012-06-26].zip
        zipURL2 = baseURL + zipName2  # http://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_WI025_soildb_WI_2003_[2012-06-26].zip

        PrintMsg("\tGetting zipfile from Web Soil Survey...", 0)

        # number of attempts allowed
        attempts = 5

        for i in range(attempts):

            try:
                # create a response object for the requested URL to download a specific SSURGO dataset.
                try:
                    # try downloading zip file with US 2003 Template DB first
                    request = urlopen(zipURL1)
                    zipName = zipName1

                except:
                    # if the zip file with US Template DB is not found, try the state template for 2003
                    # if the second attempt fails, it should fall down to the error messages
                    request = urlopen(zipURL2)
                    zipName = zipName2

                # path to where the zip file will be written to
                local_zip = os.path.join(outputFolder, zipName)  # C:\Temp\peaslee_download\wss_SSA_WI025_soildb_WI_2003_[2012-06-26].zip

                # delete the output zip file it exists
                if os.path.isfile(local_zip):
                    os.remove(local_zip)

                # response object is actually a file-like object that can be read and written to a specific location
                output = open(local_zip, "wb")
                output.write(request.read())
                output.close()

                # Download succeeded; return zipName; no need for further attempts; del local variables
                del request, local_zip, output, attempts, zipName1, zipName2, zipURL1, zipURL2
                return zipName

            except HTTPError, e:
                PrintMsg("\t\t" + areaSym + " encountered HTTP Error (" + str(e.code) + ")", 2)
                sleep(i * 3)

            except URLError, e:
                PrintMsg("\t\t" + areaSym + " encountered URL Error: " + str(e.reason), 2)
                sleep(i * 3)

            except socket.timeout, e:
                PrintMsg("\t\t" + areaSym + " encountered server timeout error", 2)
                sleep(i * 3)

            except socket.error, e:
                PrintMsg("\t\t" + areasym + " encountered Web Soil Survey connection failure", 2)
                sleep(i * 3)

            except:
                # problem deleting partial zip file after connection error?
                # saw some locked, zero-byte zip files associated with connection errors
                PrintMsg("\tFailed to download zipfile", 0)
                sleep(1)
                return ""

        # Download Failed!
        return ""

    except:
        errorMsg()
        return ""
## =====================================  MAIN BODY    ==============================================
# Import system modules
import arcpy, sys, os, locale, string, traceback, shutil, zipfile, glob, socket
from urllib2 import urlopen, URLError, HTTPError
from arcpy import env
from time import sleep

try:
    #--------------------------------------------------------------------------------------------Set Parameters
    arcpy.OverwriteOutput = True

    # Script arguments...
    regionChoice = arcpy.GetParameterAsText(0)  # User selects what region to download
    #regionChoice = "Region 13"

    outputFolder = arcpy.GetParameterAsText(1) # Folder to write the zip files to
    #outputFolder = r'G:\2014_SSURGO_Region10'

    # Path to the regional table that contains SSAs by region with extra extent and master table
    regionalTable = os.path.dirname(sys.argv[0]) + os.sep + "SSURGO_Soil_Survey_Area.gdb\SSA_by_Region_buffer"
    masterTable = os.path.dirname(sys.argv[0]) + os.sep + "SSURGO_Soil_Survey_Area.gdb\SSA_Regional_Ownership_MASTER"

    # set workspace to output folder
    env.workspace = outputFolder

    # Bail if reginal master table is not found
    if not arcpy.Exists(regionalTable) or not arcpy.Exists(masterTable):
        raise MyError, "\nRegion Buffer Table or Master Table is missing from " + os.path.dirname(sys.argv[0])

    # Get a list of areasymbols to download from the Regional Master Table. [u'WI001, u'WI003']
    asList,numOfRegionalSSA = getRegionalAreaSymbolList(regionalTable,masterTable,regionChoice)

    if not len(asList) > 0:
        raise MyError, "\nNo Areasymbols were selected. Possible problem with table"

    PrintMsg("\n\n" + str(len(asList)) + " SSURGO Dataset(s) will be downloaded for " + regionChoice, 1)
    PrintMsg("\tNumber of Soil Survey Areas assigned to " + regionChoice + ": " + str(numOfRegionalSSA),1)
    PrintMsg("\tNumber of Additional SSAs to be downloaded for the use of static datasets: " + str(len(asList) - numOfRegionalSSA),1)

    failedList = list()  # track list of failed downloads

    # Progress Counter
    iGet = 0

    arcpy.SetProgressor("step", "Downloading current SSURGO data from Web Soil Survey.....",  0, len(asList), 1)

    asList.sort()

    for SSA in asList:

        iGet += 1

        # Query SDMaccess Areaname and Spatial Version Date for a given areasymobl; return a dictionary
        asDict = getSDMaccessDict(SSA)  #{u'WI001': 'WI001,  2011-08-10,  Adams County, Wisconsin'}

        # if asDict came back empty, try to retrieve information again
        if len(asDict) < 1:
            asDict = getSDMaccessDict(SSA)

        survey = asDict[SSA]
        surveyInfo = survey.split("|")

        # Get Areasymbol, Date, and Survey Name from 'asDict'
        areaSym = surveyInfo[0].strip().upper()  # Why get areaSym again???

        # Could not get SDaccess info for this SSA - cannot continue
        if areaSym == "":
            PrintMsg("\t\t Could not get information for " + SSA + " from SD Access",2)
            failedList.append(SSA)
            continue

        surveyDate = surveyInfo[1].strip()    # Don't need this since we will always get the most current
        surveyName = surveyInfo[2].strip()    # Adams County, Wisconsin

        # set final path to NRCS Geodata Standard for Soils; This is what the unzipped folder will be renamed to
        newFolder = os.path.join(outputFolder, "soil_" + areaSym.lower())

        if os.path.exists(newFolder):
            #PrintMsg("\nOutput dataset for " + areaSym + " already exists and will be overwritten", 0)
            #arcpy.Delete_management(newFolder, "Folder")
            PrintMsg("\nOutput dataset for " + areaSym + " already exists.  Moving to the next one", 0)
            continue

        PrintMsg("\nDownloading survey " + areaSym + ": " + surveyName + " - Version: " + str(surveyDate), 1)
        arcpy.SetProgressorLabel("Downloading survey " + areaSym.upper() + "  (" + Number_Format(iGet, 0, True) + " of " + Number_Format(len(asList), 0, True) + ")")

        # Allow for multiple attempts to get zip file
        iTry = 2

        # Download the zip file; Sometimes a corrupt zip file is downloaded, so a second attempt will be made if the first fails
        for i in range(iTry):

            try:
                zipName = GetDownload(areaSym, surveyDate)  # wss_SSA_WI025_soildb_WI_2003_[2012-06-26].zip

                # path to the zip file i.e C:\Temp\peaslee_download\wss_SSA_WI025_soildb_WI_2003_[2012-06-26].zip
                local_zip = os.path.join(outputFolder, zipName)

                # if file is valid zipfile extract the file contents
                #if os.path.isfile(local_zip):
                if zipfile.is_zipfile(local_zip):

                    zipSize = (os.stat(local_zip).st_size)/1048576

                    # Proceed if size of zip file is greater than 0 bytes
                    if zipSize > 0:

                        # Less than 1 would be Kilabytes; show 2 decimal places
                        if zipSize < 1:
                            PrintMsg("\tUnzipping " + Number_Format(zipSize, 2, True) + " KB file to " + outputFolder, 0)

                        # Greater than 1 would be Megabytes; show 1 decimal place
                        else:
                            PrintMsg("\tUnzipping " + Number_Format(zipSize, 1, True) + " MB file to " + outputFolder, 0)

                        # Extract all members from the archive to the current working directory
                        with zipfile.ZipFile(local_zip, "r") as z:
                            # a bad zip file returns exception zipfile.BadZipFile
                            z.extractall(outputFolder)

                        # remove zip file after it has been extracted,
                        # allowing a little extra time for file lock to clear
                        sleep(3)
                        os.remove(local_zip)

                        # rename output folder to NRCS Geodata Standard for Soils
                        if os.path.isdir(os.path.join(outputFolder, areaSym.upper())):
                            # this must be a newer zip file using the uppercase AREASYMBOL directory
                            os.rename(os.path.join(outputFolder, areaSym.upper()), newFolder)

                        elif os.path.isdir(os.path.join(outputFolder, zipName[:-4])):
                            # this is an older zip file that has the 'wss_' directory structure
                            os.rename(os.path.join(outputFolder, zipName[:-4]), newFolder)

                        else:
                            # none of the subfolders within the zip file match any of the expected names
                            raise MyError, "Subfolder within the zip file does not match any of the expected names"

                        # import FGDC metadata to mapunit polygon shapefile
                        spatialFolder = os.path.join(newFolder, "spatial")
                        env.workspace = spatialFolder
                        shpList = arcpy.ListFeatureClasses("soilmu_a*", "Polygon")

                        try:
                            if len(shpList) == 1:
                                muShp = shpList[0]
                                PrintMsg("\tImporting metadata for " + muShp, 0)
                                metaData = os.path.join(newFolder, "soil_metadata_" + areaSym.lower() + ".xml")
                                arcpy.ImportMetadata_conversion(metaData, "FROM_FGDC", os.path.join(spatialFolder, muShp), "ENABLED")
                                del spatialFolder, muShp, metaData

                        except:
                            PrintMsg("\tImporting metadata for " + muShp + " Failed.  ", 0)
                            pass

                        # end of successful zip file download
                        break

                    # Zip file size is empty.  Attempt again if 2nd attempt has not been executed
                    else:
                        if i == 0:
                            PrintMsg("\n\Zip file for " + areaSym + " is empty. Reattempting to download, 1")
                            os.remove(local_zip)
                            continue

                # Zip file is corrupt or missing
                else:
                    if i == 0:
                        PrintMsg("\n\Zip file for " + areaSym + " is missing. Reattempting to download, 1")
                        continue

            # download zip file again if this is first error
            except (zipfile.BadZipfile, zipfile.LargeZipFile), e:
                pass

            except:
                pass

        # download for this survey failed twice
        if not os.path.exists(newFolder):
            PrintMsg("\n\tDownload failed for " + areaSym + ": " + surveyName, 2)
            failedList.append(SSA)

        del asDict, survey, surveyInfo, areaSym, surveyDate, surveyName, newFolder, iTry
        arcpy.SetProgressorPosition()

    if len(failedList) > 0:
        PrintMsg("\n" + str(len(asList) - len(failedList)) + " ouf of " + str(len(asList)) + " were successfully downloaded.",2)
        PrintMsg("\tThese surveys failed to download properly: " + ", ".join(failedList),2)

    else:
        PrintMsg("\nAll SSURGO datasets downloaded successfully\n", 0)

    arcpy.SetProgressorLabel("Processing complete...")
    env.workspace = outputFolder

except:
    errorMsg()
