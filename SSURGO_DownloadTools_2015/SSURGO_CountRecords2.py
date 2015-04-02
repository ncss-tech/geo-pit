# SSURGO_CountRecords.py
#
# Steve Peaslee, USDA-NRCS NCSS
#
# Run count on SDA tabular service to get record count for a selected set of survey areas.
# Requires ArcMap and SAPOLYGON layer selection
#
# Updated 2014-12-03. Just getting count of records from SDA. No comparison in this script.

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
            raise MyError, "SDA query failed: " + sQuery

        return int(valList[0])

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)

    except:
        PrintMsg(" \n" + sQuery, 1)
        return -1

## ===================================================================================
def GetSDMCount(saLayer):
    # Run all SDA queries necessary to get the count for each SDM - soil attribute table
    # Can be vulnerable to failure if the SDM database changes before the gSSURGO database is checked.
    #

    try:
        dCount = dict()  # store SDM count for each table in a dictionary
        Q = "SELECT COUNT(*) AS RESULT FROM "

        # Get list of areasymbols
        PrintMsg(" \nGetting list of survey areas...", 0)
        asList = list()

        with arcpy.da.SearchCursor(saLayer, ["AREASYMBOL"]) as cur:
            for rec in cur:
                asList.append("'" + rec[0] + "'")

        theAS = ",".join(asList)
        PrintMsg("\tFound " + Number_Format(len(asList)) + " surveys", 0)
        subQuery = "SELECT MUKEY FROM MAPUNIT M, LEGEND L WHERE m.LKEY = L.LKEY AND L.AREASYMBOL IN (" + theAS + ")"

        PrintMsg(" \nGetting record count from national database (SDM) tables", 0)
        arcpy.SetProgressor("step", "Getting record count from Soil Data Access...", 1, 55, 1)
        # CHORIZON
        tb1 = "chorizon"
        tb2 = "component"
        sQuery = Q + tb1.upper() + ", " + tb2.upper() + " WHERE component.mukey IN (" + subQuery + ") AND ( component.cokey = chorizon.cokey )"
        dCount[tb1] = QuerySDA(sQuery)
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
# main
import string, os, sys, traceback, locale, arcpy
from arcpy import env

try:
    arcpy.OverwriteOutput = True

    # Script arguments...
    saLayer = arcpy.GetParameterAsText(0)               # input folder

    dCount = GetSDMCount(saLayer)  # dictionary containing SDM record counts

    PrintMsg(" \nGetting record count for gSSURGO tables", 0)
    arcpy.SetProgressor("step", "Getting table record count from Soil Data Access...", 1, len(dCount), 1)
    tblList = sorted(dCount.keys())
    PrintMsg(" \nTABLE, COUNT", 0)
    for tbl in tblList:
        arcpy.SetProgressorLabel(tbl)
        PrintMsg(tbl + ", " + Number_Format(dCount[tbl], 0, False), 0)


    PrintMsg(" ", 0)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n ", 2)

except:
    errorMsg()
