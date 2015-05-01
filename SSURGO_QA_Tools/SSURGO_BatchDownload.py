# SSURGO_BatchDownload2.py
#
# Download SSURGO data from Web Soil Survey
#
# Uses Soil Data Access query to generate choicelist and URLs for each survey
#
# Three different tools call this script. One tool uses an Areasymbol wildcard to
# select surveys for download. Another tool uses an Areaname wildcard to
# elect surveys for download. The third uses an SAPOLYGON layer to generate a list
# of Areasymbol values to select surveys for download.
#
# Requires MS Access to run optional text file import for a custom SSURGO Template DB,
# as well as a modification to the VBA in the Template DB. Name of macro is BatchImport

# There are a lot of problems with WSS 3.0. One issue is trying to determine which surveys have
# spatial data. Normally this should be sapubstatuscode = 2.
# According to Gary, there is a finer level of detail available in the sastatusmap table.
# The columns tabularmudist and spatialmudist tell what kind of mapunit data is present in either the
# tabular or spatial portions. The possible values are:
#
# 1 = has ordinary mapunits and no NOTCOM mapunits
# 2 = has both ordinary and NOTCOM mapunits
# 3 = has only NOTCOM mapunits
# 4 = has no mapunits at all
#
# 10-31-2013
# 11-22-2013
# 01-08-2014
# 01-16-2014 Bad bug, downloads and unzips extra copy of some downloads. fixed.
# 01-22-2014 Modified interface to require that one of the batchimport mdb files be used.
#            Posted all available state template databases to NRCS-GIS sharepoint
#
# Looking at potential for getting old downloads from the Staging Server. Lots of issues to consider...
# Staging Server URL requires E-Auth and has subdirectories
# 04-16-2014 https://soils-staging.sc.egov.usda.gov/NASIS_Export/Staging2Ssurgo/
#
# 05-13-2014 Modified unzip routine to handle other subfolder names at version 3.1 of WSS.
#
# 08-07-2014 Added function to find MS Access application by searching the Registry
# Looks under HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths
#
# 2014-09-27 Added post-import check to make sure tabular import was at least partially successful.
# Bails out if the SACATALOG table does not contain the SAVEREST date
#
# New version of script. Attempting to move most of the main code to functions so
# that failover works better. Breaks are a little messy and it wants to keep running no mater what.
#
# 2014-10-05 Added option to include NOTCOM survey using the tool validation query
#
# 2014-10-10 Trying to incorporate Adolfo's tabular import as a replacement for the slow MS Access import macro

# 2014-10-13 Modified to populate the "SYSTEM - Mapunit Sort Specifications" table
# NEED TO DO THE SAME FOR THE  "SYSTEM - INTERP DEPTH SEQUENCE TABLE"
# NEED TO LOOK AT IL177 legend.txt. Adolfo says this one will fail to import unless
# the csv reader is bumped up using csv.field_size_limit(sys.maxsize). Has failed at 128KB. Bumped to 512KB.
# Might also look at c = csv.reader(f, delimiter='|', quoting=csv.QUOTE_NONE)

# 2014-10-18 Modified SYSTEM table to only include cointerp records with ruledepth=0
# 2014-10-28 Increased sleep time before and after compact because of of errors
# 2014-10-30 Some problems adding MUNAME field to shapefile when output folder is on network share.

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + " \n"
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def PrintMsg(msg, severity=0):
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
                arcpy.AddError(" \n" + string)

    except:
        pass

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    try:
    # Format a number according to locality and given places
        #locale.setlocale(locale.LC_ALL, "")
        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)

        else:
            theNumber = locale.format("%.*f", (places, num), False)
        return theNumber

    except:
        errorMsg()
        return ""

## ===================================================================================
def CheckMSAccess():
    # Not using this function any more
    #
    # Make sure this computer has MS Access installed so that the tabular import will run

    try:
        msa = "MSACCESS.EXE"
        aReg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        aKey = OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        acccessPath = ""

        for i in range(1024):
            keyName = EnumKey(aKey, i)

            if keyName == msa:
                subKey = OpenKey(aKey, keyName)
                installPath = QueryValueEx(subKey, "Path")
                accessPath = os.path.join(installPath[0], msa)
                break

        return accessPath

    except WindowsError:
        return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def GetPublicationDate(areaSym):
    #
    #
    #
    # Please Note!!! Funtion not being used at this time
    # Alternate method of getting SSURGO publication date using SDM Access query
    #
    # This should use SASTATUSMAP table instead of SACATALOG
    # Add 'AND SAPUBSTATUSCODE = 2'
    import time, datetime, httplib, urllib2
    import xml.etree.cElementTree as ET

    try:

        # date formatting
        #    today = datetime.date.today()
        #    myDate = today + datetime.timedelta(days = -(self.params[0].value))
        #    myDate = str(myDate).replace("-","")
        #    wc = "'" + self.params[1].value + "%' AND SAVEREST > '" + myDate + "'"

        # return list sorted by date
        #SELECT S.AREASYMBOL, CONVERT (varchar(10), [SAVEREST], 126) AS SDATE FROM SACATALOG S WHERE AREASYMBOL LIKE 'KS%'

        sQuery = "SELECT CONVERT(varchar(10), [SAVEREST], 126) AS SAVEREST FROM SACATALOG WHERE AREASYMBOL = '" + areaSym + "'"
        sQuery = "SELECT CONVERT(varchar(10), [SAVEREST], 126) AS SAVEREST FROM SASTATUSMAP WHERE AREASYMBOL = '" + areaSym + "' AND SAPUBSTATUSCODE = 2"

        # Send XML query to SDM Access service
        #
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
        dHeaders["Content-Type"] = "text/xml; charset=utf-8"
        dHeaders["SOAPAction"] = "http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx/RunQuery"
        dHeaders["Content-Length"] = len(sXML)
        sURL = "SDMDataAccess.nrcs.usda.gov"

        # Create SDM connection to service using HTTP
        conn = httplib.HTTPConnection(sURL, 80)

        # Send request in XML-Soap
        conn.request("POST", "/Tabular/SDMTabularService.asmx", sXML, dHeaders)

        # Get back XML response
        response = conn.getresponse()
        xmlString = response.read()

        # Close connection to SDM
        conn.close()

        # Convert XML to tree format
        tree = ET.fromstring(xmlString)

        iCnt = 0
        # Create empty value list
        valList = list()

        # Iterate through XML tree, finding required elements...
        for rec in tree.iter():

            if rec.tag == "SAVEREST":
                # get the YYYYMMDD part of the datetime string
                # then reformat to match SQL query
                sdmDate = str(rec.text).split(" ")[0]

        return sdmDate

    except:
        errorMsg()
        return 0


## ===================================================================================
def SSURGOVersion(newDB, tabularFolder):
    # Get SSURGO version from the Template database "SYSTEM Template Database Information" table

    #
    # Ideally we want to compare with the value in version.txt with the version in
    # the "SYSTEM - Template Database Information" table. If they are not the same
    # the tabular import should be aborted. There are some more specifics about the
    # SSURGO version.txt valu in one of the Import macros of the Template database.
    # Need to follow up and research this more.
    # At this time we are only checking the first 'digit' of the string value.
    #
    # Should be able to get this to work using wildcard for fields and then
    # use the version.txt as an alternative or failover.
    try:
        # Valid SSURGO version for data model. Ensures
        # compatibility between template database and SSURGO download.
        versionTxt = os.path.join(tabularFolder, "version.txt")

        if not arcpy.Exists(newDB):
            raise MyError, "Missing input database (" + newDB + ")"

        if arcpy.Exists(versionTxt):
            # read just the first line of the version.txt file
            fh = open(versionTxt, "r")
            txtVersion = fh.readline().split(".")[0]
            fh.close()

        else:
            # Unable to compare vesions. Warn user but continue
            PrintMsg("Unable to find file: version.txt", 1)
            return True

        systemInfo = os.path.join(newDB, "SYSTEM - Template Database Information")

        if arcpy.Exists(systemInfo):
            # Get SSURGO Version from template database
            dbVersion = 0

            with arcpy.da.SearchCursor(systemInfo, "*", "") as srcCursor:
                for rec in srcCursor:
                    if rec[0] == "SSURGO Version":
                        dbVersion = str(rec[2]).split(".")[0]
                        #PrintMsg("\tSSURGO Version from DB: " + dbVersion, 1)

            del systemInfo
            del newDB

            if txtVersion != dbVersion:
                # SSURGO Versions do not match. Warn user but continue
                PrintMsg("Discrepancy in SSURGO Version number for Template database and SSURGO download", 1)

        else:
            # Unable to open SYSTEM table in existing dataset
            # Warn user but continue
            PrintMsg("Unable to open 'SYSTEM - Template Database Information'", 1)

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def GetTemplateDate(newDB):
    # Get SAVEREST date from previously existing Template database
    # Use it to compare with the date from the WSS dataset
    # If the existing database is same or newer, it will be kept and the WSS version skipped
    try:
        if not arcpy.Exists(newDB):
            return 0

        saCatalog = os.path.join(newDB, "SACATALOG")
        dbDate = 0

        if arcpy.Exists(saCatalog):
            with arcpy.da.SearchCursor(saCatalog, ("SAVEREST"), "[AREASYMBOL] = '" + areaSym + "'") as srcCursor:
                for rec in srcCursor:
                    dbDate = str(rec[0]).split(" ")[0]

            del saCatalog
            del newDB
            return dbDate

        else:
            # unable to open SACATALOG table in existing dataset
            # return 0 which will result in the existing dataset being overwritten by a new WSS download
            return 0

    except:
        errorMsg()
        return 0

## ===================================================================================
def GetDownload(areasym, surveyDate, importDB):
    # download survey from Web Soil Survey URL and return name of the zip file
    # want to set this up so that download will retry several times in case of error
    # return empty string in case of complete failure. Allow main to skip a failed
    # survey, but keep a list of failures
    #
    # Only the version of zip file without a Template database is downloaded. The user
    # must have a locale copy of the Template database that has been modified to allow
    # automatic tabular imports.

    # create URL string from survey string and WSS 3.0 cache URL
    baseURL = "http://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/"

    try:
        # List of states that use a Template database other than US_2003.
        # This list will have to be updated in the future if it is used to
        # get downloads with the Template database included in the zipfile.
        dbInfo = {'AK':'AK', 'CT':'CT', 'FL':'FL', 'GA':'GA', 'HI':'HI', 'IA':'IA', \
        'ID':'ID', 'IN':'IN', 'ME':'ME', 'MI':'MI', 'MN':'MN', 'MT':'MT', 'NC':'NC', \
        'NE':'NE', 'NJ':'NJ', 'OH':'OH', 'OR':'OR', 'PA':'PA', 'SD':'SD', 'UT':'UT', \
        'VT':'VT', 'WA':'WA', 'WI':'WI', 'WV':'WV', 'WY':'WY', 'FM':'HI', 'PB':'HI'}

        # Incorporate the name of the Template database into the URL
        st = areaSym[0:2]
        if st in dbInfo:
            db = "_soildb_" + dbInfo[st] + "_2003"
        else:
            db = "_soildb_US_2003"

        # Use this zipfile for downloads without the Template database
        zipName = "wss_SSA_" + areaSym + "_[" + surveyDate + "].zip"

        # Use this URL for downloads with the state or US_2003 database
        #zipName = "wss_SSA_" + areaSym + db + "_[" + surveyDate + "].zip"

        zipURL = baseURL + zipName

        PrintMsg("\tDownloading survey " + areaSym + " from Web Soil Survey...", 0)

        # Open request to Web Soil Survey for that zip file
        request = urlopen(zipURL)

        # set the download's output location and filename
        local_zip = os.path.join(outputFolder, zipName)

        # make sure the output zip file doesn't already exist
        if os.path.isfile(local_zip):
            os.remove(local_zip)

        # save the download file to the specified folder
        output = open(local_zip, "wb")
        output.write(request.read())
        output.close()
        del request
        del output

        # if we get this far then the download succeeded
        return zipName

    except URLError, e:
        if hasattr(e, 'reason'):
            PrintMsg("\t\t" + areaSym + " - URL Error: " + str(e.reason), 1)

        elif hasattr(e, 'code'):
            PrintMsg("\t\t" + areaSym + " - " + e.msg + " (errorcode " + str(e.code) + ")", 1)

        return ""

    except socket.timeout, e:
        PrintMsg("\t\t" + areaSym + " - server timeout error", 1)
        return ""

    except socket.error, e:
        PrintMsg("\t\t" + areasym + " - Web Soil Survey connection failure", 1)
        return ""

    except:
        # problem deleting partial zip file after connection error?
        # saw some locked, zero-byte zip files associated with connection errors
        PrintMsg("\tFailed to download zipfile", 0)
        return ""
        sleep(1)
        return ""

## ===================================================================================
def CheckExistingDataset(areaSym, surveyDate, newFolder, newDB):

    try:
        if os.path.isdir(newFolder):
            # This survey appears to have already been downloaded. Check to see if it is complete.
            # If not complete, overwrite it.
            bNewer = False

            if os.path.isfile(newDB):
                dbDate = GetTemplateDate(newDB)

            else:
                dbDate = 0

            PrintMsg(" \nLocal dataset for " + areaSym + " already exists (" + str(dbDate) + ")", 0)

            if dbDate == 0:
                # Could not get SAVEREST date from database, assume old dataset is incomplete and overwrite
                PrintMsg("\tLocal dataset is incomplete and will be overwritten", 1)
                shutil.rmtree(newFolder, True)
                sleep(3)
                bNewer = True

                if arcpy.Exists(newFolder):
                    raise MyError, "Failed to delete old dataset (" + newFolder + ")"

            else:
                # Compare SDM date with local database date
                if int(str(surveyDate).replace("-","")) > int(str(dbDate).replace("-","")):
                    # Downloaded data is newer than the local copy. Delete and replace with new data.
                    #
                    PrintMsg("\tReplacing local database with newer download", 1)
                    bNewer = True
                    # delete old data folder
                    shutil.rmtree(newFolder, True)
                    sleep(3)

                    if arcpy.Exists(newFolder):
                        raise MyError, "Failed to delete old dataset (" + newFolder + ")"

                else:
                    # according to the filename-date, the WSS version is the same or older
                    # than the local Template DB, skip download for this survey
                    if int(str(surveyDate).replace("-","")) == int(str(dbDate).replace("-","")):
                        PrintMsg("\tSkipping download. A current version already exists", 0)

                    else:
                        PrintMsg("\tSkipping download. Local copy of data is newer (" + str(dbDate) + ") than the WSS data!?", 1)

                    bNewer = False

        else:
            # This is a new download
            bNewer = True

        return bNewer

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def ProcessSurvey(outputFolder, importDB, areaSym, bImport, bRemoveTXT):
    # Download and import the specified SSURGO dataset

    try:
        survey = asDict[areaSym]
        env.workspace = outputFolder
        surveyInfo = survey.split(",")
        areaSym = surveyInfo[0].strip().upper()

        # get date string
        surveyDate = surveyInfo[1].strip()

        # get survey name
        surveyName = surveyInfo[2].strip()

        # set standard final path and name for template database
        newFolder = os.path.join(outputFolder, "soil_" + areaSym.lower())

        # set standard name and path for SSURGO Template database
        newDB = os.path.join(os.path.join(newFolder, "tabular"), "soil_d_" + areaSym.lower() + ".mdb")

        # check to make sure this survey hasn't already been downloaded
        bNewer = CheckExistingDataset(areaSym, surveyDate, newFolder, newDB)

        if bNewer:
            # Get new SSURGO download or replace an older version of the same survey
            # Otherwise skip download
            #
            PrintMsg(" \nProcessing survey " + areaSym + ":  " + surveyName, 0)

            # First attempt to download zip file
            zipName = GetDownload(areaSym, surveyDate, importDB)

            if zipName == "" or zipName is None:
                # Try downloading zip file a second time
                sleep(5)
                zipName = GetDownload(areaSym, surveyDate, importDB)

                if zipName == "" or zipName is None:
                    # Failed second attempt to download zip file
                    # Give up on this survey
                    return "Failed"

            bZip = UnzipDownload(outputFolder, newFolder, importDB, zipName)

            if not bZip:
                # Try unzipping a second time
                sleep(1)
                bZip = UnzipDownload(outputFolder, newFolder, importDB, zipName)

                if not bZip:
                    # Failed second attempt to unzip
                    # Give up on this survey
                    return "Failed"

            # Import tabular. Only try once.
            if bImport:
                if not ImportTabular(areaSym, newFolder, importDB, newDB, bRemoveTXT):
                    # Bail clear out of the whole download process
                    return "Failed"

            return "Successful"

        else:
            # Existing local dataset is same age or newer than downloaded version
            # skip it
            return "Skipped"

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return "Failed"

    except:
        errorMsg()
        return "Failed"

## ===================================================================================
def UnzipDownload(outputFolder, newFolder, importDB, zipName ):
    # Given zip file name, try to unzip it

    try:
        local_zip = os.path.join(outputFolder, zipName)

        if os.path.isfile(local_zip):
            # got a zip file, go ahead and extract it
            zipSize = (os.stat(local_zip).st_size / (1024.0 * 1024.0))

            if zipSize > 0:

                # Download appears to be successful
                PrintMsg("\tUnzipping " + zipName + " (" + Number_Format(zipSize, 3, True) + " MB)...", 0)

                with zipfile.ZipFile(local_zip, "r") as z:
                    # a bad zip file returns exception zipfile.BadZipFile
                    z.extractall(outputFolder)

                # remove zip file after it has been extracted,
                # allowing a little extra time for file lock to clear
                sleep(3)
                os.remove(local_zip)

                # rename output folder to NRCS Geodata Standard for Soils
                if os.path.isdir(os.path.join(outputFolder, zipName[:-4])):
                    # this is an older zip file that has the 'wss_' directory structure
                    os.rename(os.path.join(outputFolder, zipName[:-4]), newFolder)

                elif os.path.isdir(os.path.join(outputFolder, areaSym.upper())):
                    # this must be a newer zip file using the uppercase AREASYMBOL directory
                    os.rename(os.path.join(outputFolder, areaSym.upper()), newFolder)

                elif os.path.isdir(newFolder):
                    # this is a future zip file using the correct field office naming convention (soil_ne109)
                    # it does not require renaming.
                    pass

                else:
                    # none of the subfolders within the zip file match any of the expected names
                    raise MyError, "Subfolder within the zip file does not match any of the standard names"

            else:
                # Downloaded a zero-byte zip file
                # download for this survey failed, may try again
                PrintMsg("\tEmpty zip file downloaded for " + areaSym + ": " + surveyName, 1)
                os.remove(local_zip)

            return True

        else:
            # Don't have a zip file, need to find out circumstances and document
            # rename downloaded database using standard convention, skip import
            raise MyError, "Missing zip file (" + local_zip + ")"
            return False

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except zipfile.BadZipfile:
        PrintMsg(" \nBad zip file?", 2)
        return False

    except:
        errorMsg()
        return False

## ===============================================================================================================
def GetTableInfo(newDB):
    # Adolfo's function
    #
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores physical names (key) and aliases (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}
    # Fieldnames are Physical Name = AliasName,IEfilename

    try:
        tblInfo = dict()

        # Open mdstattabs table containing information for other SSURGO tables
        theMDTable = "mdstattabs"
        env.workspace = newDB


        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if arcpy.Exists(os.path.join(newDB, theMDTable)):

            fldNames = ["tabphyname","tablabel","iefilename"]
            with arcpy.da.SearchCursor(os.path.join(newDB, theMDTable), fldNames) as rows:

                for row in rows:
                    # read each table record and assign 'tabphyname' and 'tablabel' to 2 variables
                    physicalName = row[0]
                    aliasName = row[1]
                    importFileName = row[2]

                    # i.e. {chaashto:'Horizon AASHTO',chaashto}; will create a one-to-many dictionary
                    # As long as the physical name doesn't exist in dict() add physical name
                    # as Key and alias as Value.
                    #if not physicalName in tblAliases:
                    if not importFileName in tblInfo:
                        #PrintMsg("\t" + importFileName + ": " + physicalName, 1)
                        tblInfo[importFileName] = physicalName, aliasName

            del theMDTable

            return tblInfo

        else:
            # The mdstattabs table was not found
            raise MyError, "Missing mdstattabs table"
            return tblInfo


    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return tblInfo

    except:
        errorMsg()
        return tblInfo

## ===================================================================================
def SortMapunits(newDB):
    # Populate table 'SYSTEM - Mapunit Sort Specifications'. Required for Soil Data Viewer
    # Looks like an alpha sort on AREASYMBOL, then MUSYM will work to set
    # lseq and museq values within the "SYSTEM - Mapunit Sort Specifications" table
    #
    # Problem, this sort does not handle a mix of alpha and numeric musym values properly
    #
    # Populate table "SYSTEM - INTERP DEPTH SEQUENCE" from COINTERP using cointerpkey and seqnum
    #
    try:
        # Make query table using MAPUNIT and LEGEND tables and use it to assemble all
        # of the data elements required to create the "SYSTEM - Mapunit Sort Specification" table
        inputTbls = ["legend", "mapunit"]

        fldList = "legend.areasymbol areasymbol;legend.lkey lkey; mapunit.musym musym; mapunit.mukey mukey"
        sqlJoin = "mapunit.lkey = legend.lkey"
        queryTbl = "musorted"

        # Cleanup
        if arcpy.Exists(queryTbl):
            arcpy.Delete_management(queryTbl)

        # Find output SYSTEM table
        sysFields = ["lseq", "museq", "lkey", "mukey"]
        sysTbl = os.path.join(newDB, "SYSTEM - Mapunit Sort Specifications")
        if not arcpy.Exists(sysTbl):
            raise MyError, "Could not find " + sysTbl

        arcpy.MakeQueryTable_management(inputTbls, queryTbl, "ADD_VIRTUAL_KEY_FIELD", "", fldList, sqlJoin)

        # Open the query table, sorting on areasymbol
        #sqlClause = [None, "order by legend_areasymbol asc"]
        dMapunitSort = dict()  # dictionary to contain list of musyms for each survey. Will be sorted
        dMapunitData = dict()  # dictionary for containing all neccessary data for SYSTEM -Map Unit Sort Specification
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key)]

        with arcpy.da.SearchCursor(queryTbl, ["legend_areasymbol", "legend_lkey", "mapunit_musym", "mapunit_mukey"]) as cur:
            for rec in cur:
                areaSym = rec[0].encode('ascii')
                lkey = rec[1].encode('ascii')
                musym = rec[2].encode('ascii')
                mukey = rec[3].encode('ascii')

                # Append muysm values to dictionary by areasymbol key
                if areaSym in dMapunitSort:
                    musymList = dMapunitSort[areaSym]
                    musymList.append(musym)
                    dMapunitSort[areaSym] = musymList

                else:
                    dMapunitSort[areaSym] = [musym]

                # store legend and map unit keys by areasymbol and map unit symbol
                dMapunitData[(areaSym, musym)] = (lkey, mukey)

        # Iterate through dMapunitSort dictionary, sorting muysm values
        areaList = sorted(dMapunitSort.keys())  # sorted list of areasymbols
        lseq = 0
        mseq = 0

        # Now read the dictionary back out in sorted order and populate the SYSTEM - Mapunit Sort Specifications table
        #
        with arcpy.da.InsertCursor(sysTbl, "*") as outCur:

            for areaSym in areaList:
                #PrintMsg(" \nProcessing survey: " + areaSym, 1)
                lseq += 1
                musymList = sorted(dMapunitSort[areaSym], key = alphanum_key)

                for musym in musymList:
                    mseq += 1
                    mKey = (areaSym, musym)
                    lkey, mukey = dMapunitData[(areaSym, musym)]
                    outrec = lseq, mseq, lkey, mukey
                    outCur.insertRow(outrec)


        # Populate "SYSTEM - INTERP DEPTH SEQUENCE" fields: cointerpkey and depthseq
        # from COINTERP fields: cointerpkey and seqnum
        # I am assuming that the cointerp table is already sorted. Is that safe??
        #
        #PrintMsg("\tUpdating SYSTEM - Interp Depth Sequence", 1)
        inTbl = os.path.join(newDB, "cointerp")
        inFlds = ["cointerpkey", "seqnum"]
        outTbl = os.path.join(newDB, "SYSTEM - INTERP DEPTH SEQUENCE")
        outFlds = ["cointerpkey", "depthseq"]
        interpSQL = "ruledepth = 1"

        with arcpy.da.SearchCursor(inTbl, inFlds, interpSQL) as sCur:
            outCur = arcpy.da.InsertCursor(outTbl, outFlds)

            for inRec in sCur:
                outCur.insertRow(inRec)

            del outCur
            del inRec

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def ImportTabular(areaSym, newFolder, importDB, newDB, bRemoveTXT):
    # Given zip file name, try to unzip it

    try:
        # get database name from file listing in the new folder
        env.workspace = newFolder

        # move to tabular folder
        env.workspace = os.path.join(newFolder, "tabular")

        # copy over master database and run tabular import
        PrintMsg("\tCopying selected master template database to tabular folder...", 0)

        # copy user specified database to the new folder
        shutil.copy2(importDB, newDB)

        # Run Auto_Import routine which will import the tabular data from text files
        PrintMsg("\tImporting textfiles into new database " + os.path.basename(newDB) + "...", 0)

        # Using Adolfo's csv reader method to import tabular data from text files...
        tabularFolder = os.path.join(newFolder, "tabular")

        # if the tabular directory is empty return False
        if len(os.listdir(tabularFolder)) < 1:
            raise MyError, "No text files found in the tabular folder"

        if not SSURGOVersion(newDB, tabularFolder):
            raise MyError, ""

        # Create a dictionary with table information
        tblInfo = GetTableInfo(newDB)

        if len(tblInfo) == 0:
            raise MyError, "Failed to get information from mdstattabs table"

        # Create a list of textfiles to be imported. The import process MUST follow the
        # order in this list in order to maintain referential integrity. This list
        # will need to be updated if the SSURGO data model is changed in the future.
        #
        txtFiles = ["distmd","legend","distimd","distlmd","lareao","ltext","mapunit", \
        "comp","muaggatt","muareao","mucrpyd","mutext","chorizon","ccancov","ccrpyd", \
        "cdfeat","cecoclas","ceplants","cerosnac","cfprod","cgeomord","chydcrit", \
        "cinterp","cmonth", "cpmatgrp", "cpwndbrk","crstrcts","csfrags","ctxfmmin", \
        "ctxmoicl","ctext","ctreestm","ctxfmoth","chaashto","chconsis","chdsuffx", \
        "chfrags","chpores","chstrgrp","chtext","chtexgrp","chunifie","cfprodo","cpmat","csmoist", \
        "cstemp","csmorgc","csmorhpp","csmormr","csmorss","chstr","chtextur", \
        "chtexmod","sacatlog","sainterp","sdvalgorithm","sdvattribute","sdvfolder","sdvfolderattribute"]
        # Need to add featdesc import as a separate item (ie. spatial\soilsf_t_al001.txt: featdesc)

        # Static Metadata Table that records the metadata for all columns of all tables
        # that make up the tabular data set.
        mdstattabsTable = os.path.join(env.workspace, "mdstattabs")

        # set progressor object which allows progress information to be passed for every merge complete
        arcpy.SetProgressor("step", "Importing tabular data", 0, len(txtFiles) + 2, 1)

        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations

        # Problem with length of some memo fields, need to allocate more memory
        #csv.field_size_limit(sys.maxsize)
        csv.field_size_limit(512000)

        for txtFile in txtFiles:

            # Get table name and alias from dictionary
            if txtFile in tblInfo:
                tbl, aliasName = tblInfo[txtFile]

            else:
                raise MyError, "Textfile reference '" + txtFile + "' not found in 'mdstattabs table'"

            arcpy.SetProgressorLabel("Importing " + tbl + "...")

            # Full path to SSURGO text file
            txtPath = os.path.join(tabularFolder, txtFile + ".txt")

            # continue if the target table exists
            if arcpy.Exists(tbl):

                # Create cursor for all fields to populate the current table
                with arcpy.da.InsertCursor(tbl, "*") as cursor:
                    # counter for current record number
                    iRows = 1

                    try:
                        # Use csv reader to read each line in the text file
                        for row in csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"'):
                            # replace all blank values with 'None' so that the values are properly inserted
                            # into integer values otherwise insertRow fails
                            newRow = [None if value == '' else value for value in row]
                            cursor.insertRow(newRow)
                            iRows += 1

                    except:
                        errorMsg()
                        raise MyError, "Error loading line no. " + Number_Format(iRows, 0, True) + " of " + txtFile + ".txt"

            else:
                raise MyError, "Required table '" + tbl + "' not found in " + newDB

            arcpy.SetProgressorPosition()

        # Import feature description file
        # soilsf_t_al001.txt
        spatialFolder = os.path.join(os.path.dirname(tabularFolder), "spatial")
        txtFile ="soilsf_t_" + areaSym
        txtPath = os.path.join(spatialFolder, txtFile + ".txt")
        tbl = "featdesc"

        # Create cursor for all fields to populate the featdesc table
        with arcpy.da.InsertCursor(tbl, "*") as cursor:
            # counter for current record number
            iRows = 1
            arcpy.SetProgressorLabel(tbl + "...")

            try:
                # Use csv reader to read each line in the text file
                for rowInFile in csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"'):
                    # replace all blank values with 'None' so that the values are properly inserted
                    # into integer values otherwise insertRow fails
                    newRow = [None if value == '' else value for value in rowInFile]
                    cursor.insertRow(newRow)
                    iRows += 1

            except:
                errorMsg()
                raise MyError, "Error loading line no. " + Number_Format(iRows, 0, True) + " of " + txtFile + ".txt"

        arcpy.SetProgressorPosition()  # for featdesc table

        # Sort map units for Soil Data Viewer SYSTEM table
        arcpy.SetProgressorLabel("Sorting map units ...")
        bSorted = SortMapunits(newDB)
        arcpy.SetProgressorPosition()  # for map unit sort

        # Check the database to make sure that it completed properly, with at least the
        # SAVEREST date populated in the SACATALOG table. Added this primarily to halt
        # processing when the user forgets to set the Trusted Location in MS Access.
        dbDate = GetTemplateDate(newDB)

        if dbDate == 0:
            # With this error, it would be best to bailout and fix the problem before proceeding
            raise MyError, "Failed to import tabular data"

        else:
            # Compact database (~30% reduction in mdb filesize)
            try:
                arcpy.SetProgressorLabel("Compacting database ...")
                sleep(2)
                arcpy.Compact_management(newDB)
                sleep(1)
                PrintMsg("\tCompacted database", 0)

            except:
                # Sometimes ArcGIS is unable to compact (locked database?)
                # Usually restarting the ArcGIS application fixes this problem
                PrintMsg("\tUnable to compact database", 1)

            # Set the Progressor to show completed status
            arcpy.ResetProgressor()
            arcpy.SetProgressorLabel("Tabular import complete")

            # Import SSURGO metadata for shapefiles
            bNamed = AddMuName(newFolder)

            # Remove all the text files from the tabular folder
            if bRemoveTXT:
                txtList = glob.glob(os.path.join(tabularFolder, "*.txt"))
                PrintMsg("\tRemoving textfiles...", 0)

                for txtFile in txtList:
                    if not txtFile.endswith("version.txt"):
                        os.remove(txtFile)

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def AddMuName(newFolder):
    # Add muname column (map unit name) to soil polygon shapefile
    #
    # Started having problems with Addfield when the shapefile is on a Network Share.
    # Could it be virus scan locking the table??
    # No system or geoprocessing error message is displayed since this is not a serious problem
    #
    try:

        # Add MuName to mapunit polygon shapefile using mapunit.txt
        muDict = dict()

        tabPath = os.path.join(newFolder, "tabular")
        muTxt = os.path.join(tabPath, "mapunit.txt")
        spatialFolder = os.path.join(newFolder, "spatial")
        env.workspace = spatialFolder

        if not arcpy.Exists(muTxt):
            raise MyError, "Cannot find " + muTxt

        # Some of the tabular only shapefiles on WSS were created as polyline instead of
        # polygon. This situation will cause the next line to fail with index out of range
        shpList = arcpy.ListFeatureClasses("soilmu_a*", "Polygon")

        if len(shpList) == 1:
            try:
                # Make failure to add muname a warning rather than a failure
                # Have had this occur several times for unknown reason. Virus scan file lock?
                # Seems to happen more frequently on network share.
                #
                muShp = shpList[0]
                PrintMsg("\tAdding MUNAME to " + muShp, 0)
                # add muname column to shapefile

                try:
                    arcpy.AddField_management (muShp, "MUNAME", "TEXT", "", "", 175)

                except:
                    # wait one second, then try again
                    sleep(1)
                    arcpy.AddField_management (muShp, "MUNAME", "TEXT", "", "", 175)
                    sleep(1)

                # read mukey and muname into dictionary from mapunit.txt file
                with open(muTxt, 'r') as f:
                    data = f.readlines()

                for rec in data:
                    s = rec.replace('"','')
                    muList = s.split("|")
                    muDict[muList[len(muList) - 1].strip()] = muList[1]

                # update shapefile muname column using dictionary
                with arcpy.da.UpdateCursor(muShp, ("MUKEY","MUNAME")) as upCursor:
                    for rec in upCursor:
                        rec[1] = muDict[rec[0]]
                        upCursor.updateRow (rec)

                del muTxt, data, muDict

                # import FGDC metadata to mapunit polygon shapefile
                spatialFolder = os.path.join(newFolder, "spatial")
                env.workspace = spatialFolder
                shpList = arcpy.ListFeatureClasses("soilmu_a*", "Polygon")

                if len(shpList) == 1:
                    muShp = shpList[0]
                    PrintMsg("\tImporting metadata for " + muShp, 0)
                    arcpy.SetProgressorLabel("Importing metadata...")
                    metaData = os.path.join(newFolder, "soil_metadata_" + areaSym.lower() + ".xml")
                    arcpy.ImportMetadata_conversion(metaData, "FROM_FGDC", os.path.join(spatialFolder, muShp), "ENABLED")
                    del spatialFolder, muShp, metaData

                    # remove log file
                    # soil_metadata_ne137_xslttran.log
                    logFile = os.path.join(os.path.dirname(env.scratchFolder), "soil_metadata_" + areaSym.lower() + "_xslttran.log")

                    if arcpy.Exists(logFile):
                        arcpy.Delete_management(logFile, "File")

            except:
                PrintMsg("\tFailed to add MUNAME column to shapefile", 1)

            return True

        else:
            PrintMsg("\tMap unit polygon shapefile not found, 'Tabular-Only' survey?", 2)
            return False

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        #errorMsg()
        return False

## ===================================================================================
# main
# Import system modules
import arcpy, sys, os, locale, string, traceback, shutil, zipfile, subprocess, glob, socket, csv, re
from urllib2 import urlopen, URLError, HTTPError
from arcpy import env
from _winreg import *
from time import sleep

try:
    arcpy.OverwriteOutput = True

    # Script arguments...
    wc = arcpy.GetParameter(0)
    dateFilter = arcpy.GetParameter(1)
    outputFolder = arcpy.GetParameterAsText(2)
    surveyList = arcpy.GetParameter(3)
    importDB = arcpy.GetParameterAsText(4)
    bRemoveTXT = arcpy.GetParameter(5)

    # Set tabular import to False if no Template database is specified
    if importDB == "":
        PrintMsg(" \nWarning! Tabular import turned off (no database specified)", 0)
        bImport = False

    else:
        bImport = True

    # initialize error and progress trackers
    failedList = list()  # track list of failed downloads
    failedCnt = 0        # track consecutive failures
    skippedList = list() # track list of downloads that were skipped because a newer version already exists
    iGet = 0

    PrintMsg(" \n" + str(len(surveyList)) + " soil survey(s) selected for WSS download", 0)

    # set workspace to output folder
    env.workspace = outputFolder

    # Create ordered list by Areasymbol
    asList = list()
    asDict = dict()

    for survey in surveyList:
        env.workspace = outputFolder
        surveyInfo = survey.split(",")
        areaSym = surveyInfo[0].strip().upper()
        asList.append(areaSym)
        asDict[areaSym] = survey

    asList.sort()

    arcpy.SetProgressor("step", "Downloading SSURGO data...",  0, len(asList), 1)

    # Proccess list of areasymbols
    #
    for areaSym in asList:
        #
        # Run import process in order of listed Areasymbol values
        #
        iGet += 1

        # put new function here
        arcpy.SetProgressorLabel("Downloading survey " + areaSym + " from Web Soil Survey  (number " + str(iGet) + " of " + str(len(asList)) + " total)")
        bProcessed = ProcessSurvey(outputFolder, importDB, areaSym, bImport, bRemoveTXT)

        if bProcessed == "Failed":
            failedList.append(areaSym)
            failedCnt += 1
            #raise MyError, ""

        elif bProcessed == "Skipped":
            skippedList.append(areaSym)

        elif bProcessed == "Successful":
            # download successful
            failedCnt = 0

        if failedCnt > 4:
            raise MyError, "Five consecutive download failures, bailing out"

        if len(failedList) > 24:
            raise MyError, "Twenty-five download failures, bailing out"

        arcpy.SetProgressorPosition()

    if len(failedList) > 0 or len(skippedList) > 0:
        PrintMsg(" \nDownload process completed with the following issues...", 1)

    else:
        if importDB:
            PrintMsg(" \nAll " + Number_Format(len(asList), 0, True) + " surveys succcessfully downloaded, tabular import process complete", 0)

        else:
            PrintMsg(" \nAll " + Number_Format(len(asList), 0, True) + " surveys succcessfully downloaded (no tabular import)", 0)

    arcpy.SetProgressorLabel("Processing complete...")
    env.workspace = outputFolder

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e), 2)

except:
    errorMsg()

finally:
    if len(failedList) > 0:
        PrintMsg("WSS download failed for: " + ", ".join(failedList), 2)

    if len(skippedList) > 0:
        PrintMsg(" \nSkipped download because a local version already exists: " + ", ".join(skippedList), 1)

    PrintMsg(" ", 0)