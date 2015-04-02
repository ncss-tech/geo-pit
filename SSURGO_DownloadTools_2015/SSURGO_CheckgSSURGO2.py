# SSURGO_CheckgSSURGO.py
#
# Steve Peaslee, USDA-NRCS NCSS
#
# Run basic completeness check on seleced file geodatabases in the specified folder.
# Assumes that all databases were created by the SSURGO Download tools.
#
# Checklist:
#  1. Looks for all 6 SSURGO featureclasses but does not check contents or projection
#  2. Looks for all 69 standalone attribute tables
#  3. Looks for MapunitRaster layer, checking for attribute table with MUKEY and statistics.
#  4. Compares mapunit count in raster with MAPUNIT table. A mismatch is not considered to
#     be an error, but a warning.

# Original coding 01-05-2014
#
# Updated 2014-09-27
#
# Updated 2014-11-24. Added comparison of gSSURGO and SDM record counts for most attribute tables
# 2014-12-03 Changed name of script and added an outer loop to compare survey by survey. This
# script should only be used when a problem has been found by the first script.

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
def GetFieldInfo(gdb):
    # Not being used any more.
    #
    # Assumption is that this is all dictated by the XML Workspace document so schema problems
    # should not occur as long as the standard tools were used to create all databases.
    #
    # Create standard schema description for each geodatabase and use it in comparison
    # to the rest of the tables

    try:
        env.workspace = gdb
        tblList = arcpy.ListTables()
        tblList.extend(arcpy.ListFeatureClasses())
        tblList.extend(arcpy.ListRasters())
        dSchema = dict()
        arcpy.SetProgressorLabel("Reading geodatabase schema...")
        arcpy.SetProgressor("step", "Reading geodatabase schema...",  0, len(tblList), 1)

        for tbl in tblList:
            tblName = tbl.encode('ascii').upper()
            arcpy.SetProgressorLabel("Reading schema for " + os.path.basename(gdb) + ": " + tblName )
            desc = arcpy.Describe(tblName)
            fields = desc.fields
            stdSchema = list()

            for fld in fields:
                stdSchema.append((fld.baseName.encode('ascii').upper(), fld.length, fld.precision, fld.scale, fld.type.encode('ascii').upper()))
                #stdSchema.append((fld.baseName.encode('ascii').upper(), fld.length, fld.precision, fld.scale, fld.type.encode('ascii').upper(), fld.aliasName.encode('ascii').upper()))

            dSchema[tblName] = stdSchema
            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()
        return dSchema

    except:
        errorMsg()
        return dict()

## ===================================================================================
def CheckFeatureClasses(theWS):
    # Simply make sure that each featureclass is present.
    #
    try:
        PrintMsg(" \n\tChecking for existence of featureclasses", 0)
        env.workspace = theWS
        missingFC = list()
        lFC = ['MUPOLYGON', 'FEATLINE', 'FEATPOINT', 'MULINE', 'SAPOLYGON', 'MUPOINT']

        for fc in lFC:
            if not arcpy.Exists(fc):
                missingFC.append(fc)

        if len(missingFC) > 0:
            PrintMsg("\t" + os.path.basename(theWS) +  " is missing the following gSSURGO featureclasses: " + ", ".join(missingFC), 2)
            return False

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def CheckTables(theWS):
    # Simply make sure that each table is present and that the SACATALOG table has at least one record
    # The rest of the tables will be checked for record count and existence

    try:
        PrintMsg(" \n\t\tChecking for existence of metadata and SDV attribute tables")
        env.workspace = theWS
        missingTbl = list()
        lTbl = ['mdstatdomdet', 'mdstatdommas', 'mdstatidxdet', 'mdstatidxmas',
        'mdstatrshipdet', 'mdstatrshipmas', 'mdstattabcols', 'mdstattabs', 'sdvalgorithm', 'sdvattribute', 'sdvfolder',
        'sdvfolderattribute']

        for tbl in lTbl:
            if not arcpy.Exists(tbl):
                missingTbl.append(tbl)

        if len(missingTbl) > 0:
            PrintMsg("\t" + os.path.basename(theWS) +  " is missing the following gSSURGO attribute tables: " + ", ".join(missingTbl), 2)
            return False

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def CheckCatalog(theWS):
    # Simply make sure that at least one survey is populated in the SACATALOG table

    try:
        env.workspace = theWS
        saTbl = os.path.join(theWS, "sacatalog")

        if arcpy.Exists(saTbl):
            # parse Areasymbol from database name. If the geospatial naming convention isn't followed,
            # then this will not work.
            surveyList = list()

            with arcpy.da.SearchCursor(saTbl, ("AREASYMBOL")) as srcCursor:
                for rec in srcCursor:
                    # Get Areasymbol from SACATALOG table, assuming just one survey is present in the database
                    surveyList.append(rec[0])

            if len(surveyList) == 0:
                PrintMsg("\t" + os.path.basename(theWS) + "\\SACATALOG table contains no surveys", 2)
                return False

            else:
                PrintMsg(os.path.basename(theWS) + " contains " + str(len(surveyList)) + " soil surveys", 0)

        else:
            # unable to open SACATALOG table in existing dataset
            PrintMsg("\tSACATALOG table not found in " + os.path.basename(theWS), 2)
            return False

    except:
        errorMsg()
        return False

## ===================================================================================
def CheckRaster(theWS):
    # Simply make sure that at least one Mapunit Raster is present and that it has
    # a proper attribute table and statistics.
    env.workspace = theWS

    try:
        rasterList = arcpy.ListRasters()
        muRasters = list()

        if len(rasterList) > 0:
            # check fields in each raster to see if it has VALUE and MUKEY columns
            for ras in rasterList:
                fldList = arcpy.Describe(ras).fields
                hasMukey = False
                hasCount = False
                hasValue = False

                for fld in fldList:
                    if fld.name.upper() == "MUKEY":
                        hasMukey = True

                    elif fld.name.upper() == "VALUE":
                        hasValue = True

                    elif fld.name.upper() == "COUNT":
                        hasCount = True

                if hasMukey and hasCount and hasValue:
                    # this could be a Map unit raster layer, add to list
                    muRasters.append(ras)


        else:
            PrintMsg("\t\tNo raster layers found in " + os.path.basename(theWS), 2)
            return False

        if len(muRasters) > 0:
            # Check all rasters identified as being 'Map unit rasters'

            for inRas in muRasters:
                desc = arcpy.Describe(inRas)
                SR = desc.spatialReference
                gcs = SR.GCS
                dn = gcs.datumName
                PrintMsg(" \n\tChecking raster " + inRas,  0)
                PrintMsg(" \n\t\tCoordinate system: " + SR.name + ", " + dn, 0)

                # Make sure raster has statistics and check the MUKEY count
                try:
                    # Get the statistic (MAX value) for the raster
                    maxValue = int(arcpy.GetRasterProperties_management (inRas, "MAXIMUM").getOutput(0))
                    PrintMsg(" \n\t\tRaster has statistics", 0)

                except:
                    # Need to test it against a raster with no statistics
                    #
                    raise MyError, "\t" + inRas + " is missing raster statistics"

                try:
                    # Get the raster mapunit count
                    # This same check is run during the PolygonToRaster conversion.
                    uniqueValues = int(arcpy.GetRasterProperties_management (inRas, "UNIQUEVALUECOUNT").getOutput(0))

                    # Get the number of MUKEY values in the MAPUNIT table
                    muCnt = MapunitCount(theWS, uniqueValues)

                    # Compare tabular and raster MUKEY count
                    if muCnt <> uniqueValues:
                        PrintMsg("\t\tDiscrepancy in mapunit count for " + inRas, 1)
                        PrintMsg("\t\t Raster mapunits: " + Number_Format(uniqueValues, 0, True), 0)
                        PrintMsg("\t\tTabular mapunits: " + Number_Format(muCnt, 0, True), 0)

                    else:
                        PrintMsg(" \n\t\tMap unit count in raster matches featureclass", 0)

                except:
                    # Need to test it against a raster with no statistics
                    #
                    PrintMsg("\t" + inRas + "; unable to get map unit count", 2)
                    return False

                cellCnt = 0

                with arcpy.da.SearchCursor(inRas, ("MUKEY", "COUNT"), "MUKEY = ''") as srcCursor:
                    for rec in srcCursor:
                        # Get mukey value and cell count
                        theMukey, cellCnt = rec

                    if cellCnt> 0:
                        PrintMsg("\t" + inRas + " is missing MUKEY values for " + Number_Format(cellCnt, 0, True) + " cells", 2  )
                        return False

        else:
            raise MyError, "No valid map unit raster layers found"


        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n ", 2)

    except:
        errorMsg()
        return False

## ===================================================================================
def MapunitCount(theWS, uniqueValues):
    # Return number of mapunits (mukey) in this survey using the MUPOLYGON featureclass
    #
    try:
        env.workspace = theWS
        muTbl = os.path.join(theWS, "mapunit")
        muPoly = os.path.join(theWS, "MUPOLYGON")

        if arcpy.Exists(muPoly):
            # use cursor to generate list of values
            # PrintMsg("\tGetting mapunit count...", 0)
            valList = [row[0] for row in arcpy.da.SearchCursor(muPoly, ['MUKEY'])]
            # convert long list to a sorted list of unique values
            valSet = set(valList)
            valList = list(sorted(valSet))
            return len(valList)

        else:
            # unable to find MUPOLYGON featureclass
            PrintMsg("\tMUPOLYGON featureclass not found in " + os.path.basename(theWS), 2)
            return 0

    except:
        errorMsg()
        return 0

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
def QuerySDA(sQuery):
    # Pass a query to Soil Data Access designed to get the count of the selected records
    import time, datetime, httplib, urllib2
    import xml.etree.cElementTree as ET

    try:
        # Create empty value list to contain the count
        # Normally the list should only contain one item
        valList = list()

        #PrintMsg("\t" + sQuery + " \n", 0)

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

        # Iterate through XML tree, finding required elements...

        for rec in tree.iter():
            #PrintMsg(str(rec), 0)

            if rec.tag == "RESULT":
                # get the target attribute value
                val = str(rec.text)
                #PrintMsg("\tFound " + val, 0)
                valList.append(val)

        if len(valList) == 0:
            # No count was returned, query timed out or bad connection?
            return -1

        return int(valList[0])

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return -1

    except:
        PrintMsg(" \n" + sQuery, 1)
        return -1

## ===================================================================================
def GetSDMCount(areaSym):
    # Run all SDA queries necessary to get the count for each SDM - soil attribute table
    # Can be vulnerable to failure if the SDM database changes before the gSSURGO database is checked.
    #

    try:
        dCount = dict()  # store SDM count for each table in a dictionary
        Q = "SELECT COUNT(*) AS RESULT FROM "

        theAS = ",".join(asList)
        subQuery = "SELECT MUKEY FROM MAPUNIT M, LEGEND L WHERE m.LKEY = L.LKEY AND L.AREASYMBOL IN (" + theAS + ")"

        PrintMsg(" \n\t\tGetting record count from national database (SDM) tables", 0)
        arcpy.SetProgressor("step", "Getting record count from Soil Data Access...", 1, 55, 1)
        time.sleep(1)

        # CHORIZON
        tb1 = "chorizon"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)

        if dCount[tb1] == -1:
            PrintMsg("\tQuery failed for " + tbl, 2)

        arcpy.SetProgressorPosition()

        # CHAASHTO
        tb1 = "chaashto"
        tb2 = "chorizon"
        tb3 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chaashto.chkey AND component.cokey =  chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHCONSISTENCE
        tb1 = "chconsistence"
        tb2 = "chorizon"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chconsistence.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHDESGNSUFFIX
        tb1 = "chdesgnsuffix"
        tb2 = "chorizon"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chdesgnsuffix.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHFRAGS
        tb1 = "chfrags"
        tb2 = "chorizon"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chfrags.chkey AND  component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHPORES
        tb1 = "chpores"
        tb2 = "chorizon"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chpores.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHSTRUCTGRP
        tb1 = "chstructgrp"
        tb2 = "chorizon"
        tb3 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chstructgrp.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHTEXT
        tb1 = "chtext"
        tb2 = "chorizon"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chtext.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHTEXTUREGRP
        tb1 = "chtexturegrp"
        tb2 = "chorizon"
        tb3 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chtexturegrp.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHUNIFIED
        tb1 = "chunified"
        tb2 = "chorizon"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( chorizon.chkey = chunified.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHSTRUCT
        tb1 = "chstruct"
        tb2 = "chstructgrp"
        tb3 = "component"
        tb4 = "chorizon"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + ", " + tb4.upper() +" WHERE component.mukey IN (" + subQuery + ") AND ( chstructgrp.chstructgrpkey = chstruct.chstructgrpkey AND chorizon.chkey = chstructgrp.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHTEXTURE
        tb1 = "chtexture"
        tb2 = "chtexturegrp"
        tb3 = "component"
        tb4 = "chorizon"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + ", " + tb4.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( chtexturegrp.chtgkey = chtexture.chtgkey AND chorizon.chkey = chtexturegrp.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CHTEXTUREMOD
        tb1 = "chtexturemod"
        tb2 = "chtexture"
        tb3 = "chtexturegrp"
        tb4 = "component"
        tb5 = "chorizon"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + ", " + tb4.upper() + ", " + tb5.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( chtexture.chtkey = chtexturemod.chtkey AND chtexturegrp.chtgkey = chtexture.chtgkey AND chorizon.chkey = chtexturegrp.chkey AND component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COCANOPYCOVER
        tb1 = "cocanopycover"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cocanopycover.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COCROPYLD
        tb1 = "cocropyld"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cocropyld.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CODIAGFEATURES
        tb1 = "codiagfeatures"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = codiagfeatures.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COECOCLASS
        tb1 = "coecoclass"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = coecoclass.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)

        # COEROSIONACC
        tb1 = "coerosionacc"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = coerosionacc.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COEPLANTS
        tb1 = "coeplants"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = coeplants.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COFORPROD
        tb1 = "coforprod"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = coforprod.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COFORPRODO
        tb1 = "coforprodo"
        tb2 = "coforprod"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( coforprod.cofprodkey = coforprodo.cofprodkey AND component.cokey = coforprod.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COGEOMORDESC
        tb1 = "cogeomordesc"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cogeomordesc.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COHYDRICCRITERIA
        tb1 = "cohydriccriteria"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cohydriccriteria.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COINTERP
        tb1 = "cointerp"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cointerp.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COMONTH
        tb1 = "comonth"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey =  comonth.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)

        # COMPONENT
        tb1 = "component"
        sQuery = Q + tb1.upper() + " WHERE component.mukey IN (" + subQuery + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COPM
        tb1 = "copm"
        tb2 = "copmgrp"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( copmgrp.copmgrpkey = copm.copmgrpkey AND component.cokey = copmgrp.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COPMGRP
        tb1 = "copmgrp"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = copmgrp.cokey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COPWINDBREAK
        tb1 = "copwindbreak"
        tb2 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = copwindbreak.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # CORESTRICTIONS
        tb1 = "corestrictions"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = corestrictions.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSOILMOIST
        tb1 = "cosoilmoist"
        tb2 = "comonth"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( comonth.comonthkey = cosoilmoist.comonthkey AND component.cokey = comonth.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSOILTEMP
        tb1 = "cosoiltemp"
        tb2 = "comonth"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( comonth.comonthkey = cosoiltemp.comonthkey AND component.cokey = comonth.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSURFFRAGS
        tb1 = "cosurffrags"
        tb2 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cosurffrags.cokey) "
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COTAXFMMIN
        tb1 = "cotaxfmmin"
        tb2 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cotaxfmmin.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COTAXMOISTCL
        tb1 = "cotaxmoistcl"
        tb2 =  "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cotaxmoistcl.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COTEXT
        tb1 = "cotext"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() +  " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cotext.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COTREESTOMNG
        tb1 = "cotreestomng"
        tb2 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cotreestomng.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COTXFMOTHER
        tb1 = "cotxfmother"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = cotxfmother.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSURFMORPHGC
        tb1 = "cosurfmorphgc"
        tb2 = "cogeomordesc"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( cogeomordesc.cogeomdkey = cosurfmorphgc.cogeomdkey AND component.cokey = cogeomordesc.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSURFMORPHHPP
        tb1 = "cosurfmorphhpp"
        tb2 = "cogeomordesc"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( cogeomordesc.cogeomdkey = cosurfmorphhpp.cogeomdkey AND component.cokey = cogeomordesc.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSURFMORPHMR
        tb1 = "cosurfmorphmr"
        tb2 = "cogeomordesc"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( cogeomordesc.cogeomdkey = cosurfmorphmr.cogeomdkey AND component.cokey = cogeomordesc.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # COSURFMORPHSS
        tb1 = "cosurfmorphss"
        tb2 = "cogeomordesc"
        tb3 = "component"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE component.mukey IN (" + subQuery + ") AND (" + "cogeomordesc.cogeomdkey = cosurfmorphss.cogeomdkey AND component.cokey = cogeomordesc.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # DISTMD
        tb1 = "distmd"
        sQuery = Q + tb1.upper() + " WHERE distmd.areasymbol IN (" + theAS + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)

        # DISTINTERPMD
        tb1 = "distinterpmd"
        tb2 = "distmd"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE distmd.areasymbol IN (" + theAS + ") AND ( distmd.distmdkey = distinterpmd.distmdkey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # DISTLEGENDMD
        tb1 = "distlegendmd"
        tb2 = "distmd"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE distmd.areasymbol IN (" + theAS + ") AND ( distmd.distmdkey = distlegendmd.distmdkey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # FEATDESC
        tb1 = "featdesc"
        arcpy.SetProgressorLabel(tb1)
        sQuery = Q + tb1.upper() + " WHERE featdesc.areasymbol IN (" + theAS + ")"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # LAOVERLAP
        tb1 = "laoverlap"
        tb2 = "legend"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE legend.areasymbol IN (" + theAS + ") AND ( legend.lkey = laoverlap.lkey  )"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # LEGEND
        tb1 = "legend"
        sQuery = Q + tb1.upper() + " WHERE legend.areasymbol IN (" + theAS + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # LEGENDTEXT
        tb1 = "legendtext"
        tb2 = "legend"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE legend.areasymbol IN (" + theAS + ") AND ( legend.lkey = legendtext.lkey  )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # MAPUNIT
        tb1 = "mapunit"
        #sQuery = Q + tb1.upper() + " WHERE mapunit.mukey IN (" + theMU + ")"
        sQuery = Q + tb1.upper() + " WHERE mapunit.mukey IN (" + subQuery + ")"
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # MUAOVERLAP
        tb1 = "muaoverlap"
        tb2 = "legend"
        tb3 = "mapunit"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + ", " + tb3.upper() + " WHERE legend.areasymbol IN (" + theAS + ") AND ( mapunit.lkey = legend.lkey AND muaoverlap.mukey = mapunit.mukey )"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # MUAGGATT
        tb1 = "muaggatt"
        sQuery = Q + tb1.upper() + " WHERE muaggatt.mukey IN (" + subQuery + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # MUCROPYLD
        tb1 = "mucropyld"
        sQuery = Q + tb1.upper() + " WHERE SDM.DBO.mucropyld.mukey IN (" + subQuery + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # MUTEXT
        tb1 = "mutext"
        sQuery = Q + tb1.upper() + " WHERE mutext.mukey IN (" + subQuery + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # SACATALOG
        tb1 = "sacatalog"
        sQuery = Q + tb1.upper() + " WHERE SACATALOG.AREASYMBOL IN (" + theAS + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        # SAINTERP
        tb1 = "sainterp"
        sQuery = Q + tb1.upper() +  " WHERE sainterp.areasymbol IN (" + theAS + ")"
        arcpy.SetProgressorLabel(tb1)
        dCount[tb1] = QuerySDA(sQuery)
        arcpy.SetProgressorPosition()

        return dCount

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return dCount

    except:
        errorMsg()
        return dCount

## ===================================================================================
def GetGDBCount(theInputDB, dSDMCounts, areaSym):
    # Get record count from gSSURGO database
    # Only those soil attributes present in the SDM database will be checked
    # Some metadata and sdv tables are not found in SDM
    try:
        dGDBCounts = dict()
        env.workspace = theInputDB
        badCount = list()
        PrintMsg(" \n\t\tGetting record count from gSSURGO tables", 0)
        arcpy.SetProgressor("step", "Getting table record count from " + os.path.basename(theInputDB), 1, len(dSDMCounts), 1)

        tblList = sorted(dSDMCounts)

        for tbl in tblList:
            arcpy.SetProgressorLabel(tbl)
            sdmCnt = dSDMCounts[tbl]

            if arcpy.Exists(tbl):
                gdbCnt = int(arcpy.GetCount_management(os.path.join(theInputDB, tbl)).getOutput(0))

            else:
                raise MyError, "Missing table (" + tbl+ ") in " + os.path.basename(theInputDB)
                badCount.append((os.path.join(theInputDB, tbl), 0, sdmCnt))

            dGDBCounts[tbl] = gdbCnt
            arcpy.SetProgressorPosition()

            if sdmCnt != gdbCnt:
                if sdmCnt == -1:
                    # SDA query failed to get count for this table
                    badCount.append((tbl, 0, gdbCnt, gdbCnt))

                else:
                    # Record counts do not agree
                    badCount.append(( tbl, sdmCnt, gdbCnt, (sdmCnt - gdbCnt) ))

        if len(badCount) > 0:
            PrintMsg("\t\tDiscrepancy found in table counts:", 2)
            PrintMsg(" \nTABLE, SDM, GDB, DIFF", 0)

        for tbl in badCount:
            PrintMsg(tbl[0] + ", " + str(tbl[1]) + ", " + str(tbl[2]) + ", " + str(tbl[3]), 0)

        arcpy.SetProgressorLabel("")
        arcpy.ResetProgressor()

        if len(badCount) > 0:
            return False

        else:
            return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
# main
import string, os, sys, traceback, locale, arcpy
from arcpy import env

try:
    arcpy.OverwriteOutput = True

    # Script arguments...
    inLoc = arcpy.GetParameterAsText(1)               # input folder
    gdb = arcpy.GetParameter(2)               # list of geodatabases in the folder

    problemList = list()

    # Get list of areasymbols from legend table
    PrintMsg(" \n\tChecking attribute tables", 0)
    asList = list()
    theInputDB = os.path.join(inLoc, gdb)
    saTbl = os.path.join(theInputDB, "LEGEND")

    with arcpy.da.SearchCursor(saTbl, ["AREASYMBOL"]) as cur:
        for rec in cur:
            asList.append("'" + rec[0] + "'")

    for areaSym in asList:
        PrintMsg(" \n" + (65 * "*"), 0)
        PrintMsg("Checking " + areaSym + "...", 0)
        PrintMsg((65 * "*"), 0)

        dSDMCounts = GetSDMCount(areaSym)  # dictionary containing SDM record counts

        #bCounts = GetGDBCount(theInputDB, dSDMCounts)

        #if bCounts == False:
        #    if not gdbName in problemList:
        #        problemList.append(gdbName)

        if not gdbName in problemList:
            PrintMsg(" \n\t" + gdbName + " is OK", 0)

    if len(problemList) > 0:
        PrintMsg("The following geodatabases have problems: " + ", ".join(problemList) + " \n ", 2)

    else:
        PrintMsg(" ", 0)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n ", 2)

except:
    errorMsg()