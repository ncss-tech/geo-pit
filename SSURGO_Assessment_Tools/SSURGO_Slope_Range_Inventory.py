#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     01/10/2014
# Copyright:   (c) Adolfo.Diaz 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
class ExitError(Exception):
    pass

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        #print msg

        f = open(textFilePath,'a+')
        f.write(msg + " \n")
        f.close

        del f

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
def logBasicSettings():
    # record basic user inputs and settings to log file for future purposes

    try:

        import getpass, time

        f = open(textFilePath,'a+')
        f.write("User Name: " + getpass.getuser() + "\n")
        f.write("Date Executed: " + time.ctime() + "\n")
        f.write("User Parameters:\n")
        f.write("\tArea of Interest: " + aoiLayerPath + "\n")
        f.write("\tSSURGO FGDB: " + ssurgoFGDB + "\n")
        f.write("\tOnly Major Components Evaluated" if onlyMajorComp == "true" else "\tMajor and Minor Components Evaluated\n")

        f.close
        del f

    except:
        errorMsg

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        AddMsgAndPrint(theMsg, 2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

## ===================================================================================
def setScratchWorkspace():
    # This function will set the scratchGDB environment based on the scratchWorkspace environment.
    #
    # The scratch workspac will typically not be defined by the user but the scratchGDB will
    # always be defined.  The default location for the scratchGDB is at C:\Users\<user>\AppData\Local\Temp
    # on Windows 7 or C:\Documents and Settings\<user>\Localsystem\Temp on Windows XP.  Inside this
    # directory, scratch.gdb will be created.
    #
    # If scratchWorkspace is set to something other than a GDB or Folder than the scratchWorkspace
    # will be set to C:\temp.  If C:\temp doesn't exist than the ESRI scratchWorkspace locations will be used.
    #
    # If scratchWorkspace is an SDE GDB than the scratchWorkspace will be set to C:\temp.  If
    # C:\temp doesn't exist than the ESRI scratchWorkspace locations will be used.

    try:
        # -----------------------------------------------
        # Scratch Workspace is defined by user or default is set
        if arcpy.env.scratchWorkspace is not None:

            # describe scratch workspace
            scratchWK = arcpy.env.scratchWorkspace
            descSW = arcpy.Describe(scratchWK)
            descDT = descSW.dataType.upper()

            # scratch workspace is geodatabase
            if descDT == "WORKSPACE":
                progID = descSW.workspaceFactoryProgID

                # scratch workspace is a FGDB
                if  progID == "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
                    arcpy.env.scratchWorkspace = os.path.dirname(scratchWK)
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                # scratch workspace is a Personal GDB -- set scratchWS to folder of .mdb
                elif progID == "esriDataSourcesGDB.AccessWorkspaceFactory.1":
                    arcpy.env.scratchWorkspace = os.path.dirname(scratchWK)
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                # scratch workspace is an SDE GDB.
                elif progID == "esriDataSourcesGDB.SdeWorkspaceFactory.1":

                    # set scratch workspace to C:\Temp; avoid the server
                    if os.path.exists(r'C:\Temp'):

                        arcpy.env.scratchWorkspace = r'C:\Temp'
                        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                    # set scratch workspace to default ESRI location
                    else:
                        arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
                        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

            # scratch workspace is simply a folder
            elif descDT == "FOLDER":
                arcpy.env.scratchWorkspace = scratchWK
                arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

            # scratch workspace is set to something other than a GDB or folder; set to C:\Temp
            else:
                # set scratch workspace to C:\Temp
                if os.path.exists(r'C:\Temp'):

                    arcpy.env.scratchWorkspace = r'C:\Temp'
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

                # set scratch workspace to default ESRI location
                else:
                    arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
                    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

        # -----------------------------------------------
        # Scratch Workspace is not defined. Attempt to set scratch to C:\temp
        elif os.path.exists(r'C:\Temp'):

            arcpy.env.scratchWorkspace = r'C:\Temp'
            arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

        # set scratch workspace to default ESRI location
        else:

            arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
            arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

##        AddMsgAndPrint("**********Scratch******")
##        AddMsgAndPrint(env.scratchFolder)
##        AddMsgAndPrint(env.scratchGDB)
        arcpy.Compact_management(arcpy.env.scratchGDB)

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def FindField(layer, chkField):
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

            return ""

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return ""

    except:
        errorMsg()
        return ""

## ===============================================================================================================
def splitThousands(someNumber):
# will determine where to put a thousands seperator if one is needed.
# Input is an integer.  Integer with or without thousands seperator is returned.

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ===============================================================================================================
def getSecondSlope(slpRange):

    if not slpRange == "Slope N\A":

        if len(str(slpRange)) == 7:
            #AddMsgAndPrint("\n Processing7: " + slpRange + " -- " + str(len(slpRange)),2)
            return int(slpRange[slpRange.find('-') + 2:slpRange.find('-') + 3])

        else:
            #AddMsgAndPrint("\n Processing7: " + slpRange + " -- " + str(len(slpRange)),2)
            return int(slpRange[slpRange.find('-') + 2:slpRange.find('-') + 4])

    else:
        return 1000

## ===============================================================================================================
##def getSlopeNumber(table,rangeNum):
##
##    firstNumList = []
##
##    slpRangeField = [f.name for f in arcpy.ListFields(table,"SlopeRange")][0]
##    sql_expression = (None, 'ORDER BY ' + slpRangeField + ' ASC')
##
##    with arcpy.da.SearchCursor(table, (slp), sql_clause=sql_expression) as cursor:
##        for row in cursor:
##            slpRange = str(row[0])
##
##            if not slpRange == "None":
##
##                if len(str(slpRange)) == 7:
##                    firstNumber = int(slpRange[slpRange.find('-') + 2:slpRange.find('-') + 3])
##                    firstNumList.append(firstNumber,slpRange)
##
##                else:
##                    firstNumber = int(slpRange[slpRange.find('-') + 2:slpRange.find('-') + 4])
##                    firstNumList.append(firstNumber,slpRange)

## ====================================== Main Body ==================================
import sys, string, os, locale, arcgisscripting, traceback, re, arcpy
from arcpy import env

if __name__ == '__main__':

    aoi = arcpy.GetParameterAsText(0)
    ssurgoFGDB = arcpy.GetParameterAsText(1)
    onlyMajorComp = arcpy.GetParameterAsText(2)

    # Set overwrite option
    arcpy.env.overwriteOutput = True

    # Start by getting information about the input layer
    descInput = arcpy.Describe(aoi)
    aoiLayerDT = descInput.dataType.upper()

    if aoiLayerDT == "FEATURELAYER":
        aoiLayerName = descInput.Name
        aoiLayerPath = descInput.FeatureClass.catalogPath
        if aoiLayerPath.find(".gdb") > 1:
            outputFolder = os.path.dirname(aoiLayerPath[:aoiLayerPath.find(".gdb")+4])
        else:
            outputFolder = os.path.basename(aoiLayerPath)

    elif aoiLayerDT in ("FEATURECLASS"):
        aoiLayerName = descInput.Name
        aoiLayerPath = descInput.catalogPath
        if arcpy.Describe(os.path.dirname(aoiLayerPath)).datatype == "FeatureDataset":
            outputFolder = os.path.dirname(os.path.dirname(os.path.dirname(aoiLayerPath)))
        else:
            outputFolder = os.path.dirname(os.path.dirname(aoiLayerPath))

    elif aoiLayerDT in ("SHAPEFILE"):
        aoiLayerName = descInput.Name
        aoiLayerPath = descInput.catalogPath
        outputFolder = os.path.dirname(aoiLayerPath)

    else:
        raise ExitError,"Invalid input data type (" + aoiLayerDT + ")"

    textFilePath = outputFolder + os.sep + "SlopeRange_" + os.path.basename(os.path.splitext(aoi)[0]) + ("_MajorComponents.txt" if onlyMajorComp == "true" else "_AllComponents.txt")
    if os.path.isfile(textFilePath):
        os.remove(textFilePath)

    # record basic user inputs and settings to log file for future purposes
    logBasicSettings()

    # Get the database and location of the SSURGO mapunit
    #theDB = GetWorkspace(ssurgoInput) # more than likely it will return a GDB or FD path
    #theDir = os.path.dirname(theDB)

    if setScratchWorkspace():

        arcpy.env.workspace = ssurgoFGDB

        """ ------------------------------------ Prepare Component Table --------------------------"""
        compTable = arcpy.ListTables("component", "ALL")

        # Exit if compTable doesn't exist
        if not len(compTable):
            raise ExitError,"\tComponent table was not found in " + os.path.basename(ssurgoFGDB)

        # compTable absolute path
        compTablePath = arcpy.env.workspace + os.sep + compTable[0]

        # make sure all of the following compTable fields exist
        compMukey = FindField(compTable[0],"mukey")
        compSlpLow = FindField(compTable[0],"slope_l")
        compSlpHigh = FindField(compTable[0],"slope_h")
        compPctRv = FindField(compTable[0],"comppct_r")
        majorField = FindField(compTable[0],"majcompflag")

        compFields = [compMukey, compSlpLow, compSlpHigh, compPctRv, majorField]

        # Exit if any compTable fields don't exist
        for field in compFields:
            if not field:
                raise ExitError,"\tComponent Table is missing \"" + field + "\" field"

        compTablefields = arcpy.ListFields(compTablePath)

        # Create a fieldinfo object
        fieldinfo = arcpy.FieldInfo()

        # Iterate through the fields and set them to fieldinfo
        for field in compTablefields:
            if field.name in compFields:
                fieldinfo.addField(field.name, field.name, "VISIBLE", "")
            else:
                fieldinfo.addField(field.name, field.name, "HIDDEN", "")

        compView = "compView"
        if arcpy.Exists(compView):
            arcpy.Delete_management(compView)

##        if onlyMajorComp == "true":
##            # The created component_view layer will have fields as set in fieldinfo object
##            majCompFlagYes = arcpy.AddFieldDelimiters(compTablePath,majorField) + " = 'Yes'"
##            arcpy.MakeTableView_management(compTablePath, compView, majCompFlagYes, "", fieldinfo)
##
##        else:
        arcpy.MakeTableView_management(compTablePath, compView, "", "", fieldinfo)

        """ ------------------------------------ Prepare MUPOLYGON Layer --------------------------"""
        fcList = arcpy.ListFeatureClasses("MUPOLYGON","Polygon")

        if not len(fcList):
            raise ExitError,"\nMUPOLYGON was not found in " + os.path.basename(ssurgoFGDB)

        muPolygonPath = arcpy.env.workspace + os.sep + fcList[0]
        muPolyMUKEY = FindField(fcList[0],"mukey")

        if not muPolyMUKEY:
            raise ExitError, "\nMUPOLYGON feature class is missing MUKEY field"

        # Create a feature layer from the MUPOLYGON
        muPolyLayer = "muPolyLayer"
        if arcpy.Exists(muPolyLayer):
            arcpy.Delete_management(muPolyLayer)

        arcpy.MakeFeatureLayer_management(muPolygonPath,muPolyLayer)

        """ --------------------- Create Unique set of MUKEYS and total Area -------------------"""
        # Create a feature layer from the AOI
        aoiLayer = "aoiLayer"
        if arcpy.Exists(aoiLayer):
            arcpy.Delete_management(aoiLayer)

        arcpy.MakeFeatureLayer_management(aoi,aoiLayer)

        # Select polygons that intersect with AOI
        arcpy.SelectLayerByLocation_management(muPolyLayer,"INTERSECT",aoiLayer)

        # Get total acres of selected Polygons
        shpAreaFld = [f.name for f in arcpy.ListFields(muPolyLayer,"*Shape_Area")][0]
        totalMupolyAcres = float("%.1f" %(sum([row[0] for row in arcpy.da.SearchCursor(muPolyLayer, (shpAreaFld))]) / 4046.85642))

        selectedPolys = splitThousands(int(arcpy.GetCount_management(muPolyLayer).getOutput(0)))
        AddMsgAndPrint("\n" + str(selectedPolys) + " SSURGO polygons were selected using " + aoiLayerName + " -- " + str(splitThousands(totalMupolyAcres)) + " Ac.",0)

        # Do a summary statistics on the select Polygons. Sum up the Shape_Area of all unique mukeys
        mukeyAreaSummary = env.scratchGDB + os.sep + "mukeyAreaSummary"
        if arcpy.Exists(mukeyAreaSummary):
            arcpy.Delete_management(mukeyAreaSummary)

        statsField = [[shpAreaFld, "SUM"]]
        arcpy.Statistics_analysis(muPolyLayer, mukeyAreaSummary, statsField, muPolyMUKEY)
        del shpAreaFld, statsField

        """ -------- Join mukeyAreaSummary to the component table and calculate weighted acres and slope range -----"""
        compView_joined = env.scratchGDB + os.sep + "compView_Joined"

        if arcpy.Exists(compView_joined):
            arcpy.Delete_management(compView_joined)

        # Join mukeyAreaSummary to the component table and only keep common records; This will
        # include both minor components and major components
        arcpy.AddJoin_management(compView,compMukey,mukeyAreaSummary,muPolyMUKEY,"KEEP_COMMON")

        # get a count of the record count from the joined table above
        allCompCount = int(arcpy.GetCount_management(compView).getOutput(0))

        # Only select major components
        if onlyMajorComp == "true":
            majCompFlagYes = arcpy.AddFieldDelimiters(compView,majorField) + " = 'Yes'"
            arcpy.SelectLayerByAttribute_management(compView, "NEW_SELECTION", where_clause=majCompFlagYes)
            majorCompCount = int(arcpy.GetCount_management(compView).getOutput(0))
            minorCompCount = allCompCount - majorCompCount

        arcpy.CopyRows_management(compView, compView_joined)
        arcpy.RemoveJoin_management(compView)

        # Exit if there are no matches in join from above
        selectedComps = int(arcpy.GetCount_management(compView_joined).getOutput(0))
        if not selectedComps > 0:
            raise ExitError,"\tNo MUKEYs match up to the Component Table"

        if onlyMajorComp == "true":
            AddMsgAndPrint("\n\t" + str(splitThousands(selectedComps)) + " Major Components will be evaluated\n",0)
        else:
            AddMsgAndPrint("\n\t" + str(splitThousands(selectedComps)) + " Components will be evaluated (Major & Minor)\n",0)

        waField = "Weighted_Acres"
        if not len(arcpy.ListFields(compView_joined, waField)) > 0:
            arcpy.AddField_management(compView_joined, waField, "DOUBLE")

        slpRangeField = "SlopeRange"
        if not len(arcpy.ListFields(compView_joined, slpRangeField)) > 0:
            arcpy.AddField_management(compView_joined,slpRangeField,"TEXT", "", "" ,10)

        # Get new field names from joined table.  Field names get their origin table name appended in the beginning i.e. component_slope_l
        shpAreaFld = [f.name for f in arcpy.ListFields(compView_joined,"*Shape_Area")][0]
        compPctRvFld = [f.name for f in arcpy.ListFields(compView_joined,"*comppct_r")][0]
        compSlpLowFld = [f.name for f in arcpy.ListFields(compView_joined,"*slope_l")][0]
        compSlpHighFld = [f.name for f in arcpy.ListFields(compView_joined,"*slope_h")][0]

        #waExpresion = "\"" + "(!" + shpAreaFld + "! * (float(!" + compPctRvFld + "!) " + "/ 100.0)) / 4046.85642" + "\""
        waExpresion = "(!" + shpAreaFld + "! * (float(!" + compPctRvFld + "!) " + "/ 100.0)) / 4046.85642"
        arcpy.CalculateField_management(compView_joined,waField,waExpresion,"PYTHON_9.3")

        slpRangeExpression = "genSlopeRange(!" + compSlpLowFld + "!, !" + compSlpHighFld + "!)"

        codeblock = """def genSlopeRange(low,high):
            if low > -1:
                return str(int(low)) + " - " + str(int(high)) + " %"
            else:
                nothing = "Slope N\A"
                return nothing"""

        arcpy.CalculateField_management(compView_joined,slpRangeField,slpRangeExpression,"PYTHON_9.3", codeblock)
        del shpAreaFld, compPctRvFld, compSlpLowFld, compSlpHighFld

        """ ------------------------------------- Report Slope Range Summary -------------------------------------------------"""
        # Table that will contain the unique slope ranges by total acres
        slpRangeSummary = env.scratchGDB + os.sep + "slpRangeSummary"

        if arcpy.Exists(slpRangeSummary):
            arcpy.Delete_management(slpRangeSummary)

        # Summarize the compView_joined table by unique slope ranges and sum up their acres
        statsField = [[waField, "SUM"]]
        arcpy.Statistics_analysis(compView_joined, slpRangeSummary, statsField, slpRangeField)

        shpAreaFld = [f.name for f in arcpy.ListFields(slpRangeSummary,"SUM*")][0]
        freqFld = [f.name for f in arcpy.ListFields(slpRangeSummary,"FREQUENCY")][0]

        slopeDict = dict()
        fields = [slpRangeField,freqFld,shpAreaFld]
        sql_expression = (None, 'ORDER BY ' + slpRangeField + ' ASC')

        with arcpy.da.SearchCursor(slpRangeSummary, (fields), sql_clause=sql_expression) as cursor:
            for row in cursor:
                slopeRange = str(row[0])
                numOfComponents = str(splitThousands(row[1]))
                acres = str(splitThousands(float("%.1f" %(row[2]))))
                acrePercent = str(float("%.1f" %((row[2] / totalMupolyAcres) * 100)))
                #secondSlope = getSecondSlope(slopeRange)
                slopeDict[slopeRange] = (len(slopeRange), len(numOfComponents), len(acres),len(acrePercent))
                del slopeRange, numOfComponents, acres, acrePercent

        # Strictly for formatting.  Get maximum character lengths for each
        maxSlopeRangeLength = sorted([slpinfo[0] for slpRange,slpinfo in slopeDict.iteritems()],reverse=True)[0]
        maxNumOfComponents = sorted([slpinfo[1] for slpRange,slpinfo in slopeDict.iteritems()],reverse=True)[0]
        maxAcreLength = sorted([slpinfo[2] for slpRange,slpinfo in slopeDict.iteritems()],reverse=True)[0]
        maxAcrePercent = sorted([slpinfo[3] for slpRange,slpinfo in slopeDict.iteritems()],reverse=True)[0]

        if onlyMajorComp == "true":
            maxSlopeRangeLength = 17
            majorCompAcres = float("%.1f" %(sum([row[0] for row in arcpy.da.SearchCursor(slpRangeSummary, (shpAreaFld))])))

            if len(str(minorCompCount)) > maxNumOfComponents:
                maxNumOfComponents = len(str(minorCompCount))

            if len(str(majorCompAcres)) > maxAcreLength:
                maxAcreLength = len(str(majorCompAcres))

        del slopeDict

        with arcpy.da.SearchCursor(slpRangeSummary, (fields), sql_clause=sql_expression) as cursor:
            for row in cursor:

                slopeRange = str(row[0])
                numOfComponents = str(splitThousands(row[1]))
                acres = str(splitThousands(float("%.1f" %(row[2]))))
                acrePercent = str(float("%.1f" %((row[2] / totalMupolyAcres) * 100)))

                firstSpace = " " * (maxSlopeRangeLength - len(slopeRange))
                secondSpace = " " * (maxNumOfComponents - len(numOfComponents))
                thirdSpace = " " * (maxAcreLength - len(acres))
                fourthSpace = " " * (maxAcrePercent - len(acrePercent))

                AddMsgAndPrint("\t\t" + slopeRange + firstSpace + " -- " + numOfComponents + secondSpace + " -- " + acres + thirdSpace + " Ac. -- " + acrePercent + " %",1)
                del slopeRange, numOfComponents, acres, acrePercent, firstSpace, secondSpace, thirdSpace, fourthSpace

        if onlyMajorComp == "true":

            firstSpace = " " * (maxNumOfComponents - len(str(minorCompCount)))
            secondSpace = " " * (maxAcreLength - len(str(majorCompAcres)))

            minorCompAcres = float("%.1f" %(totalMupolyAcres - majorCompAcres))
            minorCompPrct = str(float("%.1f" %((minorCompAcres / totalMupolyAcres) * 100)))

            AddMsgAndPrint("\n\t\tMinor Components:" + " -- " + str(minorCompCount) + firstSpace + " -- " + str(minorCompAcres) + secondSpace + " Ac. -- " + minorCompPrct + " %\n",1)
            del firstSpace, secondSpace, minorCompAcres, minorCompPrct

        else:
            AddMsgAndPrint("\n")

        gisToDelete = [compView, muPolyLayer, aoiLayer, mukeyAreaSummary, compView_joined, slpRangeSummary]

        for gis in gisToDelete:
            if arcpy.Exists(gis):
                arcpy.Delete_management(gis)

        del compTable, compTablePath, compMukey, compSlpLow, compSlpHigh, compPctRv, majorField, compFields, compTablefields, fieldinfo
        del compView, fcList, muPolygonPath, muPolyMUKEY, totalMupolyAcres, muPolyLayer, aoiLayer, mukeyAreaSummary, compView_joined
        del waField, slpRangeField, slpRangeExpression, codeblock, slpRangeSummary, statsField, shpAreaFld, freqFld, fields#, gisToDelete

    del aoi, ssurgoFGDB, onlyMajorComp, descInput, aoiLayerDT


# (!Sum_Shape_Area! * ( float(!comppct_r!) / 100.0 )) / 4046.85642
#([Shape_Area] * ( [comppct_r] / 100)) / 4046.85642
#str(int(!slope_l!)) + " - " + str(int( !slope_h!)) + " %"




