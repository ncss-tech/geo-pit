# SSURGO_FixDB.py
#
# Purpose:
#  1. Fix incorrectly populated SSURGO-SDVATTRIBUTE table for 'Hydric Rating by Map Unit'
# The attribute error results in Soil Data Viewer incorrectly assigning percent hydric as a
# TEXT data type which then corrupts the SDV Hydric map symbology.
#  2. Fix SSURGO version number so that the 'Import from another database' macro will work.
#     Version number is changed from 2 to 2.1
#  3. Remove double quotes from ECOCLASSNAME. ArcGIS cannot parse the text tables created by
#     Soil Data Viewer. This results in scrambled ECOCLASSNAME maps.
#  4. Resort SYSTEM Map Unit Sort Specification table because of a bug in the SSURGO Download Tools
#
#  2014-11-11
## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def PrintMsg(msg, severity=0):
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

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in errorMsg method", 2)
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
        return False

## ===================================================================================
def ValidSurveyId(sa):
    # Validate parsed value as being a soil survey areasymbol (SSNNN)
    try:

        # Make sure first two characters are string values
        if not ord(sa[0]) in range(65, 123) or not ord(sa[1]) in range(65, 123):
            #PrintMsg("\t\t" + sa + " first two characters are not text", 1)
            return False

        # Make sure last three characters are integer
        n = int(sa[2:5])

        return True

    except:
        PrintMsg("\t\t" + sa + " last three characters are not integer", 1)
        return False


## ===================================================================================
def SortMapunits(newDB):
    # Populate table 'SYSTEM - Mapunit Sort Specifications'. Required for Soil Data Viewer
    #
    # Populate table "SYSTEM - INTERP DEPTH SEQUENCE" from COINTERP using cointerpkey and seqnum
    #
    try:
        PrintMsg("\tSorting map units...", 0)
        env.workspace = newDB
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
            raise MyError, "Unable to find " + sysTbl

        # Clear the table
        arcpy.TruncateTable_management(sysTbl)

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
                lkey = rec[1]
                musym = rec[2]
                mukey = rec[3]

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
        # Clear the table
        arcpy.TruncateTable_management(outTbl)

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

# Import system modules
import sys, string, os, arcpy, locale, traceback, re
from arcpy import env

# Get parameters
p = arcpy.GetParameterAsText(0)              # top directory for SSURGO archive

try:

    PrintMsg(" \nApplying fixes to SSURGO databases in " + p + " \n ", 0)

    dbCnt = 0
    txtCnt = 0
    dbErrors = list()  # list of mdbs that failed cursor
    dbFixes = list()   # list of mdbs that were 'fixed' for SDVATTRIBUTE table
    dbFixes2 = list()  # list of mdbs that were 'fixed' for the SYSTEM table
    dbFixes3 = list()  # list of mdbs that were 'fixed' for COECOCLASS table (imbedded double quotes
    txtErrors = list() # list of text files that failed during the search-and-replace
    txtFixes = list()  # list of text files that were 'fixed'
    dbFound = list()
    surveyList = list()

    fldListA = ['attributelogicaldatatype', 'attributefieldsize']
    sqlHydric = "attributename = 'Hydric Rating by Map Unit'"
    fldListC = ['attributelogicaldatatype', 'attributeprecision']  # maplegendkey, maplegendclasses
    sqlNCCPI = "attributename = 'National Commodity Crop Productivity Index v2'"

    # fldListB = ('Item Name','Item Value')  # having problems getting these field names with spaces to work
    fldListB = ('Item Value')
    sqlB = "[Item Name] = 'SSURGO Version' AND [Item Value] = '2'"
    i = len(p) + 6

    for root, dirs, files in os.walk(p):
        #PrintMsg("\n" + root, 0)
        for f in files:
            if f.endswith(".mdb"):
                # Found an Access database

                # get the survey id assuming standard naming convention of soil_d_TTNNN.mdb
                sa = f[-9:-4]

                if not ValidSurveyId(sa):
                    # if the parsed string cannot be an areasymbol, just print the mdb
                    sa = f

                if not sa in surveyList:
                    surveyList.append(sa)
                    PrintMsg(" \n" + sa.upper() + ":", 0)

                dbCnt += 1
                dbFound.append(f)
                #PrintMsg(f, 0)

                bSorted = SortMapunits(os.path.join(root, f))

                if bSorted == False:
                    raise MyError, ""

                # Open update cursor on 'sdvattribute' table
                try:
                    tbl = os.path.join(root, os.path.join(f, "SDVATTRIBUTE"))

                    with arcpy.da.UpdateCursor(tbl, fldListA, sqlHydric) as upCursor:
                        for rec in upCursor:
                            # Update incorrect logical datatype for Hydric Rating and
                            # National Commodity Crop Index

                            rec = ("Integer", 0)
                            upCursor.updateRow(rec)
                            PrintMsg("\tsdvattribute hydric", 0)

                        dbFixes.append(os.path.join(f, "sdvattribute"))

                    #with arcpy.da.UpdateCursor(tbl, fldListA, sqlNCCPI) as upCursor:
                    #    for rec in upCursor:
                    #        # Update incorrect logical datatype for Hydric Rating and
                    #        # National Commodity Crop Index

                    #        rec = ("Float", 0)
                    #        upCursor.updateRow(rec)
                    #        PrintMsg("\tsdvattribute NCCPI", 0)

                    #    dbFixes.append(os.path.join(f, "sdvattribute"))

                    # Open update cursor on 'SYSTEM - Template Database Information' table
                    # Item Name   SSURGO Version
                    # Item Value  2.1
                    # Index number for 'Item Value' column is 2
                    tbl = os.path.join(root, os.path.join(f, '[SYSTEM - Template Database Information]'))

                    with arcpy.da.UpdateCursor(tbl, '*', sqlB) as upCursor:
                        for rec in upCursor:
                            # Update incorrect template database version number
                            rec[2] = ('2.1')
                            upCursor.updateRow(rec)

                        PrintMsg("\tSSURGO Version number", 0)
                        dbFixes2.append(tbl[i:])

                    # Open update cursor on 'coecoclass' table
                    # Item Name   ecoclassname
                    # Search for imbedded double quotes

                    tbl = os.path.join(root, os.path.join(f, '[coecoclass]'))

                    with arcpy.da.UpdateCursor(tbl, ('ecoclassname'), "") as upCursor:
                        for rec in upCursor:
                            # Update incorrect template database version number
                            rec[0] = rec[0].replace('"', '')
                            upCursor.updateRow(rec)

                        dbFixes3.append(tbl[i:])
                        PrintMsg("\tEcoclass Name", 0)

                except:
                    # Failed to update ecoclassname
                    dbErrors.append(tbl)

            elif f == "sdvattribute.txt":
                # fix original text file for hydric rating and NCCPI
                txtCnt += 1

                try:
                    txtFile = os.path.join(root, f)

                    # get the survey id assuming standard naming convention of soil_d_TTNNN.mdb
                    # sa has not been set at this point! Need to parse from path
                    sa = txtFile[-30:][0:5]

                    if not ValidSurveyId(sa):
                        # if the parsed string cannot be an areasymbol, just print the text file
                        sa = txtFile

                    fh = open(txtFile,'r')
                    filedata = fh.read()
                    fh.close()

                    if '"hydricrating"|"Choice"' in filedata:
                        # Replace the Choice data type with Integer so that ArcMap can use 'Classified' renderer
                        newdata = filedata.replace('"hydricrating"|"Choice"','"hydricrating"|"Integer"')

                        if '"National Commodity Crop Productivity Index v2"|"cointerp"|"interphrc"|"String"' in newdata:
                            # Replace String data type with Integer so that ArcMap can use a 'Classified' renderer
                            newdata = newdata.replace('"National Commodity Crop Productivity Index v2"|"cointerp"|"interphrc"|"String"', '"National Commodity Crop Productivity Index v2"|"cointerp"|"interphrc"|"Integer"')

                        fh = open(txtFile,'w')
                        fh.write(newdata)
                        fh.close()

                        txtFixes.append(txtFile)

                        if not sa in surveyList:
                            surveyList.append(sa)
                            PrintMsg(" \n" + sa.upper() + ":", 0)

                        PrintMsg("\tsdvattribute.txt", 0)

                except:
                    txtErrors.append(txtFile)

    # End of data processing

    PrintMsg(" \nChecked a total of " + Number_Format(dbCnt, 0, True) + " databases and " + Number_Format(txtCnt, 0, True) + " text files...", 0)

    if len(dbErrors) > 0:
        PrintMsg(" \nFailed to fix the following databases: " + ", ".join(dbErrors), 2)
        errorMsg()

    if len(dbFixes) == 0:
        PrintMsg(" \nNo databases were identified as requiring the 'Hydric fix'", 0)

    else:
        PrintMsg(" \nSuccessfully updated " + str(len(dbFixes)) + " SSURGO Template databases", 0)

    if len(txtErrors) > 0:
        PrintMsg(" \nFailed to fix the following sdvattribute.txt files: " + ", ".join(txtErrors) + "\n ", 2)
        errorMsg()

    if len(txtFixes) == 0:
        PrintMsg(" \nNo 'sdvattribute.txt' files were identified as requiring the 'Hydric fix' \n ", 0)

    else:
        PrintMsg(" \nSuccessfully updated " + str(len(txtFixes)) + " sdvattribute.txt files ", 0)

    if len(dbFixes2) == 0:
        PrintMsg(" \nNo template database version numbers were fixed' \n ", 0)

    else:
        PrintMsg(" \nSuccessfully updated " + str(len(dbFixes2)) + " version numbers to 2.1", 0)

    if len(dbFixes3) == 0:
        PrintMsg(" \nNo coecoclass tables had their ecoclassnames fixed \n ", 0)

    else:
        PrintMsg(" \nSuccessfully updated ecoclassname in " + str(len(dbFixes3)) + " coecoclass tables", 0)

    PrintMsg(" \n", 0)
    #PrintMsg(" \nFound databases: " + ", ".join(dbFound) + " \n ", 1)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e), 2)

except:
    errorMsg()


