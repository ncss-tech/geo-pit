# gSSURGO_DistributeValuTable.py
#
# Steve Peaslee, USDA-NRCS NCSS
#
# For each selected gSSURGO geodatabase, queries matching records from the national
# VALU1 table and copies them to a new VALU1 table within each geodatabase.

# Original coding 2014-10-03

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
                arcpy.AddMessage("    ")
                arcpy.AddError(string)

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
        return False

## ===================================================================================
def StateNames():
    # Create dictionary object containing list of state abbreviations and their names that
    # will be used to name the file geodatabase.
    # For some areas such as Puerto Rico, U.S. Virgin Islands, Pacific Islands Area the
    # abbrevation is

    # NEED TO UPDATE THIS FUNCTION TO USE THE LAOVERLAP TABLE AREANAME. AREASYMBOL IS STATE ABBREV

    try:
        stDict = dict()
        stDict["AL"] = "Alabama"
        stDict["AK"] = "Alaska"
        stDict["AS"] = "American Samoa"
        stDict["AZ"] = "Arizona"
        stDict["AR"] = "Arkansas"
        stDict["CA"] = "California"
        stDict["CO"] = "Colorado"
        stDict["CT"] = "Connecticut"
        stDict["DC"] = "District of Columbia"
        stDict["DE"] = "Delaware"
        stDict["FL"] = "Florida"
        stDict["GA"] = "Georgia"
        stDict["HI"] = "Hawaii"
        stDict["ID"] = "Idaho"
        stDict["IL"] = "Illinois"
        stDict["IN"] = "Indiana"
        stDict["IA"] = "Iowa"
        stDict["KS"] = "Kansas"
        stDict["KY"] = "Kentucky"
        stDict["LA"] = "Louisiana"
        stDict["ME"] = "Maine"
        stDict["MD"] = "Maryland"
        stDict["MA"] = "Massachusetts"
        stDict["MI"] = "Michigan"
        stDict["MN"] = "Minnesota"
        stDict["MS"] = "Mississippi"
        stDict["MO"] = "Missouri"
        stDict["MT"] = "Montana"
        stDict["NE"] = "Nebraska"
        stDict["NV"] = "Nevada"
        stDict["NH"] = "New Hampshire"
        stDict["NJ"] = "New Jersey"
        stDict["NM"] = "New Mexico"
        stDict["NY"] = "New York"
        stDict["NC"] = "North Carolina"
        stDict["ND"] = "North Dakota"
        stDict["OH"] = "Ohio"
        stDict["OK"] = "Oklahoma"
        stDict["OR"] = "Oregon"
        stDict["PA"] = "Pennsylvania"
        stDict["PRUSVI"] = "Puerto Rico and U.S. Virgin Islands"
        stDict["RI"] = "Rhode Island"
        stDict["Sc"] = "South Carolina"
        stDict["SD"] ="South Dakota"
        stDict["TN"] = "Tennessee"
        stDict["TX"] = "Texas"
        stDict["UT"] = "Utah"
        stDict["VT"] = "Vermont"
        stDict["VA"] = "Virginia"
        stDict["WA"] = "Washington"
        stDict["WV"] = "West Virginia"
        stDict["WI"] = "Wisconsin"
        stDict["WY"] = "Wyoming"
        return stDict

    except:
        PrintMsg("\tFailed to create list of state abbreviations (CreateStateList)", 2)
        return stDict

## ===================================================================================
def UpdateMetadata(outputWS, target, surveyInfo):
    # Update metadata for target object (VALU1 table)
    #
    try:

        # Clear process steps from the VALU1 table. Mostly AddField statements.
        #
        # Different path for ArcGIS 10.2.2??
        #
        #
        #if not arcpy.Exists(target):
        #    target = os.path.join(outputWS, target)


        # Remove geoprocessing history
        remove_gp_history_xslt = os.path.join(os.path.dirname(sys.argv[0]), "remove geoprocessing history.xslt")
        out_xml = os.path.join(env.scratchFolder, "xxClean.xml")

        if arcpy.Exists(out_xml):
            arcpy.Delete_management(out_xml)

        # Using the stylesheet, write 'clean' metadata to out_xml file and then import back in
        arcpy.XSLTransform_conversion(target, remove_gp_history_xslt, out_xml, "")
        arcpy.MetadataImporter_conversion(out_xml, target)

        # Set metadata translator file
        dInstall = arcpy.GetInstallInfo()
        installPath = dInstall["InstallDir"]
        prod = r"Metadata/Translator/ARCGIS2FGDC.xml"
        mdTranslator = os.path.join(installPath, prod)

        # Define input and output XML files
        #mdExport = os.path.join(env.scratchFolder, "xxExport.xml")  # initial metadata exported from current data data
        xmlPath = os.path.dirname(sys.argv[0])
        mdExport = os.path.join(xmlPath, "gSSURGO_ValuTable.xml")  # template metadata stored in ArcTool folder
        mdImport = os.path.join(env.scratchFolder, "xxImport.xml")  # the metadata xml that will provide the updated info

        # Cleanup XML files from previous runs
        if os.path.isfile(mdImport):
            os.remove(mdImport)

        # Start editing metadata using search and replace
        #
        stDict = StateNames()
        st = os.path.basename(outputWS)[8:-4]

        if st in stDict:
            # Get state name from the geodatabase name
            mdState = stDict[st]

        else:
            mdState = ""

        # Set date strings for metadata, based upon today's date
        #
        d = datetime.date.today()
        today = str(d.isoformat().replace("-",""))

        # Set fiscal year according to the current month. If run during January thru September,
        # set it to the current calendar year. Otherwise set it to the next calendar year.
        #
        if d.month > 9:
            fy = "FY" + str(d.year + 1)

        else:
            fy = "FY" + str(d.year)

        # Convert XML from template metadata to tree format
        tree = ET.parse(mdExport)
        root = tree.getroot()

        # Update TITLE element
        #PrintMsg("\tmetadata title", 0)
        eTitle = root.find('idinfo/citation/citeinfo/title')

        if mdState != "":
            eTitle.text = os.path.basename(target).title() + " - " + mdState

        else:
            eTitle.text = os.path.basename(target).title()


        # Update place keywords
        #PrintMsg("\tplace keywords", 0)
        ePlace = root.find('idinfo/keywords/theme')

        if ePlace is not None:
            for child in ePlace.iter('themekey'):
                if child.text == "xxSTATExx":
                    #PrintMsg("\tReplaced xxSTATExx with " + mdState)
                    child.text = mdState

                elif child.text == "xxSURVEYSxx":
                    #child.text = "The Survey List"
                    child.text = surveyInfo

        else:
            PrintMsg("\tsearchKeys not found", 1)

        idPurpose = root.find('idinfo/descript')

        if not idPurpose is None:
            for child in idPurpose.iter('purpose'):
                ip = child.text
                #PrintMsg("\tip: " + ip, 1)
                if ip.find("xxFYxx") >= 0:
                    #PrintMsg("\t\tip", 1)
                    child.text = ip.replace("xxFYxx", fy)

        idAbstract = root.find('idinfo/descript/abstract')
        if not idAbstract is None:
            iab = idAbstract.text

            if iab.find("xxFYxx") >= 0:
                #PrintMsg("\t\tip", 1)
                idAbstract.text = iab.replace("xxFYxx", fy)
                PrintMsg("\tAbstract", 0)

        # Use contraints
        #idConstr = root.find('idinfo/useconst')
        #if not idConstr is None:
        #    iac = idConstr.text
            #PrintMsg("\tip: " + ip, 1)
        #    if iac.find("xxFYxx") >= 0:
        #        idConstr.text = iac.replace("xxFYxx", fy)
        #        PrintMsg("\t\tUse Constraint: " + idConstr.text, 0)

        # Update credits
        eIdInfo = root.find('idinfo')

        if not eIdInfo is None:

            for child in eIdInfo.iter('datacred'):
                sCreds = child.text

                if sCreds.find("xxTODAYxx") >= 0:
                    #PrintMsg("\tdata credits1", 1)
                    sCreds = sCreds.replace("xxTODAYxx", today)

                if sCreds.find("xxFYxx") >= 0:
                    #PrintMsg("\tdata credits2", 1)
                    sCreds = sCreds.replace("xxFYxx", fy)

                child.text = sCreds
                #PrintMsg("\tCredits: " + sCreds, 1)

        #  create new xml file which will be imported, thereby updating the table's metadata
        tree.write(mdImport, encoding="utf-8", xml_declaration=None, default_namespace=None, method="xml")

        # import updated metadata to the geodatabase table
        arcpy.MetadataImporter_conversion(mdExport, target)
        arcpy.ImportMetadata_conversion(mdImport, "FROM_FGDC", target, "DISABLED")

        # delete the temporary xml metadata files
        if os.path.isfile(mdImport):
            os.remove(mdImport)

        #if os.path.isfile(mdExport):
        #    os.remove(mdExport)

        return True

    except:
        errorMsg()
        False

## ===================================================================================
def CopyData(inputDB, inValuTbl, bOverwrite):
    # For the target database, get a list of mukeys from the mapunit table and
    # use them to query the national VALU1 table and copy those records to a
    # new VALU1 table in the target database.
    try:

        # First check for pre-existing output tables
        newTbl = os.path.join(inputDB, os.path.basename(inValuTbl))

        if arcpy.Exists(newTbl):
            if bOverwrite:
                arcpy.Delete_management(newTbl)

            else:
                raise MyError, "A " + os.path.basename(inValuTbl) + " table already exists for " + inputDB

            PrintMsg(" \nCreating VALU1 table for " + inputDB, 0)

        # Get list of survey areas from inputDB
        #
        saTbl = os.path.join(inputDB, "sacatalog")
        expList = list()
        queryList = list()

        with arcpy.da.SearchCursor(saTbl, ["AREASYMBOL", "SAVEREST"]) as srcCursor:
            for rec in srcCursor:
                expList.append(rec[0] + " (" + str(rec[1]).split()[0] + ")")
                queryList.append("'" + rec[0] + "'")

        surveyInfo = ", ".join(expList)

        # Get list of mukeys for query
        #
        muTbl = os.path.join(inputDB, "mapunit")
        if not arcpy.Exists(muTbl):
            raise MyError, "Could not find mapunit table for " + inputDB

        muList = list()

        with arcpy.da.SearchCursor(muTbl, ["mukey"]) as cur:
            for rec in cur:
                muList.append("'" + rec[0] +"'")

        iCnt = len(muList)

        if iCnt > 0:
            # List of mukeys is valid

            whereClause = "mukey in (" + ",".join(muList) + ")"

            # MakeQueryTable_management (in_table, out_table, in_key_field_option, {in_key_field}, {in_field}, {where_clause})
            tmpTbl = "Valu1_Selection"
            arcpy.MakeQueryTable_management(inValuTbl, tmpTbl, "NO_KEY_FIELD", "", "", whereClause)
            arcpy.CopyRows_management(tmpTbl, newTbl)
            iNew = int(arcpy.GetCount_management(newTbl).getOutput(0))

            if iNew != iCnt:
                raise MyError, "Discrepancy in record count for " + newTbl

            else:
                #bUpdated = UpdateMetadata(inputDB, os.path.basename(inValuTbl), surveyInfo)
                bUpdated = UpdateMetadata(inputDB, newTbl, surveyInfo)
                PrintMsg("\tNew table has " + Number_Format(iCnt, 0, True) + " records...", 0)

        else:
            raise MyError, "Failed to generate list of mukeys from " + inValuTbl

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
# main
import string, os, sys, traceback, locale, arcpy, time
import xml.etree.cElementTree as ET
from arcpy import env

try:

    # Script arguments...
    # Skipping parameter 0 because that is only used for the ArcTool menu
    inLoc = arcpy.GetParameterAsText(1)               # input folder
    gdbList = arcpy.GetParameter(2)                   # list of geodatabases in the folder
    inValuTbl = arcpy.GetParameterAsText(3)           # Source VALU1 table (national)
    bOverwrite = arcpy.GetParameter(4)                # Overwrite existing tables. Default = False

    arcpy.OverwriteOutput = bOverwrite

    iCnt = len(gdbList)
    PrintMsg(" \nProcessing " + str(iCnt) + " geodatabases", 0)

    # initialize list of problem geodatabases
    problemList = list()

    for i in range(0, iCnt):
        gdbName = gdbList[i]
        inputDB = os.path.join(inLoc, gdbName)

        if CopyData(inputDB, inValuTbl, bOverwrite) == False:
            problemList.append(gdbName)

    if len(problemList) > 0:
        PrintMsg("The following geodatabases encountered problems: " + ", ".join(problemList) + " \n ", 2)

    else:
        PrintMsg(" ", 0)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()
