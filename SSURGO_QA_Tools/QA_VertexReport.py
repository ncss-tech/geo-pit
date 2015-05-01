# QA_VertexReport.py
#
# ArcMap 10.1, arcpy
#
# Steve Peaslee, USDA-NRCS National Soil Survey Center
#
# Identifies polygon line segments shorter than a specified length.
# Calculate area statistics for each polygon and load into a table
# Join table by OBJECTID to input featurelayer to spatially enable polygon statistics
# Create point featurelayer marking endpoints for those polygon line segments that
# are shorter than a specified distance.
#
# Issue with shapefile input. Script may fail if selected fieldname is longer than 8 characters.
#
# Fixed issue where the optional attribute field was not set. Uses OBJECTID field now.

# 07-22-2013 Found issue with ArcSDE workspace, need to fix problem with MakeStatsTable function

# 07-22-2013 Found apparent problem with using a selected set and MUSYM on SDM. Appears to get a list
# of MUSYM values within the selected set, but then queries the entire layer to process each individual value.
# Maybe it's just slow, but I need to make sure that the script is using a subset of the original selection as it loops through
# the unique values.
#
# 10-31-2013

class MyError(Exception):
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

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def CreateWebMercaturSR():
    # Create default Web Mercatur coordinate system for instances where needed for
    # calculating the projected length of each line segment. Only works when input
    # coordinate system is GCS_NAD_1983, but then it should work almost everywhere.
    #
    try:
        # Use WGS_1984_Web_Mercator_Auxiliary_Sphere
        #theSpatialRef = arcpy.SpatialReference("USA Contiguous Albers Equal Area Conic USGS")
        theSpatialRef = arcpy.SpatialReference(3857)
        arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"

        # return spatial reference string
        return theSpatialRef

    except:
        errorMsg()

## ===================================================================================
def ProcessLayer(inLayer, inField, outputSR):
    # Create a single summary for the entire layer
    #
    # inLayer = selected featurelayer or featureclass that will be processed
    try:

        # create new table to store individual polygon statistics
        # no input field so specify

        statsTbl = MakeStatsTable(inField, unitAbbrev)

        if arcpy.Exists(statsTbl):
            # open update cursor on polygon statistics table
            fieldList = ["ACRES","VERTICES","AVI","MIN_DIST","MULTIPART"]
            iCursor = arcpy.da.InsertCursor(statsTbl, fieldList )

        else:
            return False

        statsTbl = MakeStatsTable(inField, unitAbbrev)

        # Add QA_VertexReport table to ArcMap TOC
        arcpy.SetParameter(3, statsTbl)
        iCnt = int(arcpy.GetCount_management(inLayer).getOutput(0))

        arcpy.SetProgressorLabel("Reading polygon geometry...")
        arcpy.SetProgressor("step", "Reading polygon geometry...",  0, iCnt, 1)

        # initialize summary variables for entire dataset
        polygonTotal = 0
        totalArea = 0
        totalAcres = 0
        pointTotal = 0
        totalPerimeter = 0
        minDist = 1000
        bHasMultiPart = False

        fieldList = ["OID@","SHAPE@","SHAPE@AREA","SHAPE@LENGTH"]
        formatList = (15,15,15,15,15,20)
        hdrList = ["Polygons","Acres","Vertices","Avg_Length","Min_Length","IsMultiPart"]
        dashedLine = "    |------------------------------------------------------------------------------------------|"

        newHdr = ""

        for i in range(6):
            newHdr = newHdr + (" " * (formatList[i] - len(hdrList[i])) + hdrList[i])

        PrintMsg(" \n" + newHdr, 0)
        PrintMsg(dashedLine, 0)

        #PrintMsg(" \nSummarizing polygon statistics for " + inField.name + " value: '" + val + "'", 1)
        # initialize variables for the current value (eg. NE109)
        iSeg = 1000000  # use an arbitrarily high segment length to initialize segment length
        polygonCnt = 0
        sumArea = 0
        sumAcres = 0
        pointCnt = 0
        sumPerimeter = 0

        with arcpy.da.SearchCursor(inLayer, fieldList, "", outputSR) as sCursor:
            # Select polgyons with the current attribute value and process the geometry for each
            iPartCnt = 0

            for row in sCursor:
                # Process a polygon record. row[1] is the same as feat or SHAPE
                fid, feat, theArea, thePerimeter = row # do I need to worry about NULL geometry here?

                if not feat is None:
                    polygonCnt += 1
                    iPnts = feat.pointCount
                    pointCnt += iPnts
                    iPartCnt = feat.partCount

                    if feat.partCount > 1:
                        iPartCnt += 1
                        bHasMultiPart = True

                    elif iPartCnt == 0:
                        # bad polygon
                        raise MyError, "Bad geometry for polygon #" + str(fid)

                    sumArea += theArea
                    sumPerimeter += thePerimeter

                    for part in feat:
                        # accumulate 2 points for each segment
                        pntList = []  # initialize points list for polygon

                        for pnt in part:
                            if pnt:
                                # add vertice or to-node coordinates to list

                                if len(pntList) == 2:
                                    # calculate current segment length using 2 points
                                    dist = math.hypot(pntList[0][0] - pntList[1][0], pntList[0][1] - pntList[1][1] )

                                    if dist < iSeg:
                                        iSeg = dist

                                    # then drop the first point from the list
                                    pntList.pop(0)

                                # add the next point
                                pntList.append((pnt.X,pnt.Y))

                            else:
                                # interior ring encountered
                                #PrintMsg("\t\t\tInterior Ring...", 0)
                                pntList = []  # reset points list for interior ring

                else:
                    raise MyError, "NULL geometry for polygon #" + str(fid)

                # convert mapunit area to acres
                if theUnits == "meters":
                    sumAcres = sumArea / 4046.85643

                elif theUnits == "feet_us":
                    sumAcres = sumArea / 43560.0

                else:
                    PrintMsg(" \nFailed to calculate acre value using unit: " + theUnits, 2)
                    return False

                # calculate average vertex interval for this polygon
                avi = sumPerimeter / pointCnt

                if iSeg < minDist:
                    minDist = iSeg

                #outRow = [sumAcres, pointCnt,avi,iSeg,iPartCnt]

                #iCursor.insertRow(outRow)

                arcpy.SetProgressorPosition()

            # calculate average vertex interval for the current value
            avgInterval = sumPerimeter / pointCnt
            polygonTotal += polygonCnt
            totalAcres += sumAcres
            pointTotal += pointCnt
            totalPerimeter += sumPerimeter

            #"ACRES","VERTICES","AVI","MIN_DIST","MULTIPART"
            outRow = [totalAcres, pointTotal,avgInterval,minDist,iPartCnt]
            iCursor.insertRow(outRow)

        # calculate average vertex interval for entire dataset
        # if the cursor selection fails, this will throw a divide-by-zero error
        if pointTotal > 0:
            avgInterval = totalPerimeter / pointTotal

        else:
            avgInterval = -1

        # get minimum segment length for entire dataset
        if iSeg < minDist:
            minDist = iSeg


        # print final summary statistics for entire dataset
        if bHasMultiPart:
            totalMsg = [Number_Format(polygonCnt, 0, True), Number_Format(sumAcres, 1, True), Number_Format(pointCnt, 0, True), Number_Format(avgInterval, 3, True), Number_Format(minDist, 3, True), "Has Multipart!"]

        else:
            totalMsg = [Number_Format(polygonCnt, 0, True), Number_Format(sumAcres, 1, True), Number_Format(pointCnt, 0, True), Number_Format(avgInterval, 3, True), Number_Format(minDist, 3, True), "No Multipart"]

        newTotal = ""

        for i in range(6):
            newTotal = newTotal + (" " * (formatList[i] - len(totalMsg[i])) + totalMsg[i])

        PrintMsg(newTotal, 0)

        if bHasMultiPart:
            PrintMsg("Input layer has multipart polygons that require editing (explode)", 2)

        # Add QA_VertexReport table to ArcMap TOC
        PrintMsg(" \nPolygon statistics saved to " + statsTbl, 0)
        arcpy.SetParameter(3, statsTbl)

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def ProcessLayerBySum(inLayer, inField, outputSR):
    # All the real work is performed within this function
    #
    # inLayer = selected featurelayer or featureclass that will be processed
    # if it is a featureclass, then a featurelayer must be substituted to allow  a selection
    try:
        # Create table to store geometry statistics for each polygon
        # Later this table will be joined to the input layer on POLYID
        #
        # Create a list of coordinate pairs that have been added to the table to prevent duplicates
        #
        # create new table to store individual polygon statistics
        statsTbl = MakeStatsTable(inField, unitAbbrev)

        if arcpy.Exists(statsTbl):
            # open update cursor on polygon statistics table

            newFieldName = arcpy.ParseFieldName(inField.name).split(",")[3].strip()
            fieldList = [newFieldName,"ACRES","VERTICES","AVI","MIN_DIST","MULTIPART"]
            iCursor = arcpy.da.InsertCursor(statsTbl, fieldList )

        else:
            return False

        # Create a list of unique values for the inField
        fieldList = [inField.name]
        fldType = inField.type
        valList = [row[0] for row in arcpy.da.SearchCursor(inLayer, fieldList)]
        uniqueList = list(set(valList))
        uniqueList.sort()
        del valList

        if len(uniqueList) > 0:
            # only proceed if list contains unique values to be processed
            PrintMsg(" \nFound " + Number_Format(len(uniqueList), 0, True) + " unique values for " + inFieldName + " \n ", 0)

            # if the input is a featurelayer, need to see if there is a selection set or definition query that needs to be maintained
            #
            # initialize summary variables for entire dataset
            polygonTotal = 0
            totalArea = 0
            totalAcres = 0
            pointTotal = 0
            totalPerimeter = 0
            minDist = 1000000
            bHasMultiPart = False
            maxV = 100000  # set a polygon-vertex limit that will trigger a warning
            bigPolyList = list()  # add the polygon id to this list if it exceeds the limit

            fieldList = ["OID@","SHAPE@","SHAPE@AREA","SHAPE@LENGTH"]
            newFieldName = arcpy.ParseFieldName(inField.name).split(",")[3].strip()

            formatList = (20,15,15,15,15,15,15)
            hdrList = [newFieldName.capitalize(),"Polygons","Acres","Vertices","Avg_Length","Min_Length","IsMultiPart"]
            dashedLine = "    |----------------------------------------------------------------------------------------------------------|"
            newHdr = ""

            for i in range(7):
                newHdr = newHdr + (" " * (formatList[i] - len(hdrList[i])) + hdrList[i])

            PrintMsg(newHdr, 0)
            PrintMsg(dashedLine, 0)

            for val in uniqueList:
                arcpy.SetProgressorLabel("Reading polygon geometry for " + inField.name + " value:  " + str(val)  + "...")

                #if fldType != "OID":
                theSQL = arcpy.AddFieldDelimiters(inLayer, inField.name) + " = '" + val + "'"

                #else:
                #    theSQL =  inField.name  + " = " + str(val)

                arcpy.SelectLayerByAttribute_management(inLayer, "NEW_SELECTION", theSQL)

                iCnt = int(arcpy.GetCount_management(inLayer).getOutput(0))
                arcpy.SetProgressor("step", "Reading polygon geometry for " + inField.name + " value:  " + str(val)  + "...",  0, iCnt, 1)

                if val.strip() == "":
                    # if some values aren't populated, insert string 'NULL' into report table
                    val = "<NULL>"

                #PrintMsg(" \nSummarizing polygon statistics for " + inField.name + " value: '" + val + "'", 1)
                # initialize variables for the current value (eg. NE109)
                iSeg = 1000000  # use an arbitrarily high segment length to initialize segment length
                polygonCnt = 0
                sumArea = 0
                sumAcres = 0
                pointCnt = 0
                sumPerimeter = 0

                with arcpy.da.SearchCursor(inLayer, fieldList, "", outputSR) as sCursor:

                    # Select polgyons with the current attribute value and process the geometry for each
                    iPartCnt = 0

                    for row in sCursor:
                        # Process a polygon record. row[1] is the same as feat
                        fid, feat, theArea, thePerimeter = row # do I need to worry about NULL geometry here?

                        if not feat is None:
                            polygonCnt += 1

                            if feat.partCount > 1:
                                iPartCnt += 1
                                bHasMultiPart = True

                            elif feat.partCount == 0:
                                raise MyError, "Bad geometry for polygon #" + str(fid)

                            iPnts = feat.pointCount

                            if iPnts > maxV:
                                bigPolyList.append(str(fid))

                            pointCnt += iPnts
                            sumArea += theArea
                            sumPerimeter += thePerimeter

                            for part in feat:
                                # accumulate 2 points for each segment
                                pntList = []  # initialize points list for polygon

                                for pnt in part:
                                    if pnt:
                                        # add vertice or to-node coordinates to list

                                        if len(pntList) == 2:
                                            # calculate current segment length using 2 points
                                            dist = math.hypot(pntList[0][0] - pntList[1][0], pntList[0][1] - pntList[1][1] )

                                            if dist < iSeg:
                                                iSeg = dist

                                            # then drop the first point from the list
                                            pntList.pop(0)

                                        # add the next point
                                        pntList.append((pnt.X,pnt.Y))

                                    else:
                                        # interior ring encountered
                                        #PrintMsg("\t\t\tInterior Ring...", 0)
                                        pntList = []  # reset points list for interior ring

                            arcpy.SetProgressorPosition()

                        else:
                            raise MyError, "Null geometry for polygon #" + str(fid)

                    # convert mapunit area to acres
                    if theUnits == "meters":
                        sumAcres = sumArea / 4046.85643

                    elif theUnits == "feet_us":
                        sumAcres = sumArea / 43560.0

                    else:
                        PrintMsg(" \nFailed to calculate acre value using unit: " + theUnits, 2)
                        return False

                    # calculate average vertex interval for this polygon
                    avi = sumPerimeter / pointCnt

                    if iSeg < minDist:
                        minDist = iSeg

                    if inFieldName != "":
                        outRow = [val, sumAcres, pointCnt,avi,iSeg,iPartCnt]

                    else:
                        outRow = [sumAcres, pointCnt,avi,iSeg,iPartCnt]

                    iCursor.insertRow(outRow)

                    arcpy.ResetProgressor()

                # calculate average vertex interval for the current value
                avgInterval = sumPerimeter / pointCnt
                polygonTotal += polygonCnt
                totalAcres += sumAcres
                pointTotal += pointCnt
                totalPerimeter += sumPerimeter

                # print statistics to console window
                #
                # column headers: newFieldName.capitalize(), "Polygons", "Acres","Vertices","Avg_Length","Min_Length","IsMultiPart"
                # format message string into a fixed set of columns
                statsMsg =  [val, Number_Format(polygonCnt, 0, True), Number_Format(sumAcres, 1, True), Number_Format(pointCnt, 0, True), Number_Format(avgInterval, 3, True), Number_Format(iSeg, 3, True), str(iPartCnt)]
                newMsg = ""

                for i in range(7):
                    newMsg = newMsg + (" " * (formatList[i] - len(statsMsg[i])) + statsMsg[i])

                PrintMsg(newMsg, 0)

                #arcpy.SetProgressorPosition()

        else:
            PrintMsg(" \nFailed to create list of unique " + inFieldName + " values", 2)
            return False

        arcpy.ResetProgressor()

        # calculate average vertex interval for entire dataset
        # if the cursor selection fails, this will throw a divide-by-zero error
        if pointTotal > 0:
            avgInterval = totalPerimeter / pointTotal

        else:
            avgInterval = -1

        # get minimum segment length for entire dataset
        if iSeg < minDist:
            minDist = iSeg

        # print final summary statistics for entire dataset
        if bHasMultiPart:
            totalMsg = ["",Number_Format(polygonTotal, 0, True), Number_Format(totalAcres, 1, True), Number_Format(pointTotal, 0, True), Number_Format(avgInterval, 3, True), Number_Format(minDist, 3, True), "Has Multipart!"]

        else:
            totalMsg = ["",Number_Format(polygonTotal, 0, True), Number_Format(totalAcres, 1, True), Number_Format(pointTotal, 0, True), Number_Format(avgInterval, 3, True), Number_Format(minDist, 3, True), "No Multipart"]

        newTotal = ""

        for i in range(6):
            newTotal = newTotal + (" " * (formatList[i] - len(totalMsg[i])) + totalMsg[i])

        PrintMsg(dashedLine, 0)
        PrintMsg(newTotal, 0)

        if bHasMultiPart:
            PrintMsg("Input layer has multipart polygons that require editing (explode)", 2)

        if len(bigPolyList) > 0:
            PrintMsg("Warning! Input layer has " + str(len(bigPolyList)) + " polygons exceeding the " + Number_Format(maxV) + " vertex limit: " + ", ".join(bigPolyList), 2)

        # Add QA_VertexReport table to ArcMap TOC
        PrintMsg(" \nPolygon statistics saved to " + statsTbl, 0)
        arcpy.SetParameter(3, statsTbl)
        arcpy.SelectLayerByAttribute_management(inLayer, "CLEAR_SELECTION")

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e) + " \n", 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def MakeStatsTable(inField, unitAbbrev):
    # Create join table containing polygon statistics
    # If AREASYMBOL is the chosen field, this table could be joined to the SAPOLYGON
    # featureclass so that values can be mapped to show which surveys have general issues.
    #
    # Assumption is that the workspace has been set to the geodatabase or folder
    # If workspace is a featuredataset, the script will fail

    try:
        thePrefix = "QA_VertexReport"

        if env.workspace.endswith(".gdb") or env.workspace.endswith(".mdb"):
            theExtension = ""
            statsTbl = os.path.join(env.workspace, thePrefix + theExtension)

        elif env.workspace.endswith(".sde"):
            theExtension = ".dbf"
            statsTbl = os.path.join(env.scratchFolder, thePrefix + theExtension)

        else:
            theExtension = ".dbf"
            statsTbl = os.path.join(env.workspace, thePrefix + theExtension)

        try:
            if arcpy.Exists(statsTbl):
                arcpy.Delete_management(statsTbl)

            arcpy.CreateTable_management(os.path.dirname(statsTbl), os.path.basename(statsTbl))
            #PrintMsg("Created polygon stats table (" + statsTbl + ")", 1)

        except:
            errorMsg()
            return ""

        try:
            # inField,ACRES,VERTICES,AVI,MIN_DIST,MULTIPART
            # make sure new field is less than 10 characters if output format is .DBF

            if inFieldName != "":
                if theExtension == ".dbf":
                    newFieldName = arcpy.ParseFieldName(inField.name).split(",")[3].strip()[0:10]

                else:
                    newFieldName = arcpy.ParseFieldName(inField.name).split(",")[3].strip()

                arcpy.AddField_management(statsTbl, newFieldName, inField.type, inField.precision,inField.scale,inField.length, inField.aliasName)

            arcpy.AddField_management(statsTbl, "ACRES", "DOUBLE", "12", "1","", "Acres")
            arcpy.AddField_management(statsTbl, "VERTICES", "LONG", "12","","", "Vertex Count")
            arcpy.AddField_management(statsTbl, "AVI", "DOUBLE", "12", "1", "", "Avg Segment (" + unitAbbrev + ")")
            arcpy.AddField_management(statsTbl, "MIN_DIST", "DOUBLE", "12", "3", "", "Min Segment (" + unitAbbrev + ")")
            arcpy.AddField_management(statsTbl, "MULTIPART", "SHORT", "", "", "", "Is Multipart?")

            try:
                allFields = arcpy.ListFields(statsTbl)

                for badField in allFields:
                    #PrintMsg("\tBadFields: " + badField.name, 0)
                    if badField.name.upper() == "FIELD1":
                        arcpy.DeleteField_management(statsTbl, "Field1")

            except:
                pass

        except:
            errorMsg()
            return ""

        return statsTbl

    except:
        errorMsg()
        return ""

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
        return FalseoutputPoin

## ===================================================================================
def elapsedTime(start):
    # Calculate amount of time since "start" and return time string
    try:
        # Stop timer
        #
        end = time.time()

        # Calculate total elapsed seconds
        eTotal = end - start

        # day = 86400 seconds
        # hour = 3600 seconds
        # minute = 60 seconds

        eMsg = ""

        # calculate elapsed days
        eDay1 = eTotal / 86400
        eDay2 = math.modf(eDay1)
        eDay = int(eDay2[1])
        eDayR = eDay2[0]

        if eDay > 1:
          eMsg = eMsg + str(eDay) + " days "
        elif eDay == 1:
          eMsg = eMsg + str(eDay) + " day "

        # Calculated elapsed hours
        eHour1 = eDayR * 24
        eHour2 = math.modf(eHour1)
        eHour = int(eHour2[1])
        eHourR = eHour2[0]

        if eDay > 0 or eHour > 0:
            if eHour > 1:
                eMsg = eMsg + str(eHour) + " hours "
            else:
                eMsg = eMsg + str(eHour) + " hour "

        # Calculate elapsed minutes
        eMinute1 = eHourR * 60
        eMinute2 = math.modf(eMinute1)
        eMinute = int(eMinute2[1])
        eMinuteR = eMinute2[0]

        if eDay > 0 or eHour > 0 or eMinute > 0:
            if eMinute > 1:
                eMsg = eMsg + str(eMinute) + " minutes inLayer"
            else:
                eMsg = eMsg + str(eMinute) + " minute "

        # Calculate elapsed secons
        eSeconds = "%.1f" % (eMinuteR * 60)

        if eSeconds == "1.00":
            eMsg = eMsg + eSeconds + " second "
        else:
            eMsg = eMsg + eSeconds + " seconds "

        return eMsg

    except:
        errorMsg()
        return ""

## ===================================================================================
## MAIN
import sys, string, os, locale, time, math, operator, traceback, collections, arcpy
from arcpy import env

try:
    # Set formatting for numbers
    locale.setlocale(locale.LC_ALL, "")

    # Script parameters

    # Target Featureclass
    inLayer = arcpy.GetParameter(0)

    # Target field (restricted to TEXT by the ArcTool validator)
    inFieldName = arcpy.GetParameterAsText(1)

    # Projection (optional when input layer has projected coordinate system)
    outputSR = arcpy.GetParameter(2)

    # Start timer
    begin = time.time()

    eMsg = elapsedTime(begin)

    env.overwriteOutput = True

    # reset field parameter to a field object so that the properties can be determined
    if inFieldName != "":
        fldList = arcpy.ListFields(inLayer)
        inField = None

        for fld in fldList:
            if fld.name == inFieldName:
                inField = fld

    # Setup: Get all required information from input layer
    #
    # Describe input layer
    desc = arcpy.Describe(inLayer)
    theDataType = desc.dataType.upper()
    theCatalogPath = desc.catalogPath
    fidFld = desc.OIDFieldName
    inputSR = desc.spatialReference
    inputDatum = inputSR.GCS.datumName

    # Set output workspace
    if arcpy.Describe(os.path.dirname(theCatalogPath)).dataType.upper() == "FEATUREDATASET":
        # if input layer is in a featuredataset, move up one level to the geodatabase
        env.workspace = os.path.dirname(os.path.dirname(theCatalogPath))

    else:
        env.workspace = os.path.dirname(theCatalogPath)

    PrintMsg(" \nOutput workspace set to: " + env.workspace, 0)

    # Get total number of features for the input featureclass
    iTotalFeatures = int(arcpy.GetCount_management(theCatalogPath).getOutput(0))

    # Get input layer information and count the number of input features
    if theDataType == "FEATURELAYER":
        # input layer is a FEATURELAYER, get featurelayer specific information
        defQuery = desc.whereClause
        fids = desc.FIDSet
        fidList = list()
        #PrintMsg(" \nSaved FIDSet: '" + str(fids) + "'", 0)

        if fids != "":
            # save list of feature ids in original selection
            fidList1 = list(fids.split("; "))

            if len(fidList1) > 0:
                #PrintMsg(" \nFound " + str(len(fidList1)) + " fids  in list '" + str(fidList1) + "'", 0)
                for fid in fidList1:
                    fidList.append(int(fid))

                del fidList1

        layerName = desc.nameString

        # get count of number of features being processed
        if len(fidList) == 0:
            # No selected features in layer
            iSelection = iTotalFeatures

            if defQuery == "":
                # No query definition and no selection
                iSelection = iTotalFeatures
                PrintMsg(" \nProcessing all " + Number_Format(iTotalFeatures, 0, True) + " polygons in '" + layerName + "'...", 0)

            else:
                # There is a query definition, so the only option is to use GetCount
                iSelection = int(arcpy.GetCount_management(inLayer).getOutput(0))  # Use selected features code
                PrintMsg(" \nSearching " + Number_Format(iSelection, 0, True) + " of " + Number_Format(iTotalFeatures, 0, True) + " features...", 0)

        else:
            # featurelayer has a selected set, get count using FIDSet
            iSelection = len(fidList)
            PrintMsg(" \nProcessing " + Number_Format(iSelection, 0, True) + " of " + Number_Format(iTotalFeatures, 0, True) + " features...", 0)

    elif theDataType in ("FEATURECLASS", "SHAPEFILE"):
        # input layer is a featureclass, get featureclass specific information
        layerName = desc.baseName + " Layer"
        defQuery = ""
        fids = ""
        fidList = list()

        iSelection = iTotalFeatures
        PrintMsg(" \nProcessing all " + Number_Format(iTotalFeatures, 0, True) + " polygons in '" + layerName + "'...", 0)


        # still need to create a featurelayer if the user wants to summarize on the basis of some attribute value
        PrintMsg(" \nCreating featurelayer '" + layerName + "' from featureclass: '" + theCatalogPath + "'", 0)
        arcpy.MakeFeatureLayer_management(theCatalogPath, layerName)
        inLayer = layerName

    # Make sure that input and output datums are the same, no transformations allowed
    if outputSR.name == '':
        outputSR = inputSR
        outputDatum = inputDatum
        #PrintMsg(" \nSetting output CS to same as input: " + outputSR.name + " \n" + outputDatum + " \n ", 1)

    else:
        outputDatum = outputSR.GCS.datumName
        #PrintMsg(" \nOutput datum: '" + outputDatum + "'", 0)

    if inputDatum != outputDatum:
        raise MyError, "Input and output datums do not match"

    if outputSR.type.upper() != "PROJECTED":
        if inputDatum in ("D_North_American_1983","D_WGS_1984"):
            # use Web Mercatur as output projection for calculating segment length
            PrintMsg(" \nInput layer coordinate system is not projected, switching to Web Mercatur (meters)", 1)
            outputSR = CreateWebMercaturSR()

        else:
            raise MyError, "Unable to handle output coordinate system: " + outputSR.name + " \n" + outputDatum

    else:
        PrintMsg(" \nOutput coordinate system: " + outputSR.name, 0)

    theUnits = outputSR.linearUnitName.lower()
    theUnits = theUnits.replace("foot", "feet")
    theUnits = theUnits.replace("meter", "meters")

    if theUnits.startswith("meter"):
        unitAbbrev = "m"

    else:
        unitAbbrev = "ft"

    # End of Setup
    #

    # run process

    if inFieldName == "":
        bProcessed = ProcessLayer(inLayer, fidFld, outputSR)

    else:
        bProcessed = ProcessLayerBySum(inLayer, inField, outputSR)

    # if there was a previous selection on the input layer, reapply
    #
    if theDataType == "FEATURELAYER":
        if len(fidList) > 0:
            if len(fidList) == 1:
                fidList ="(" + str(fidList[0]) + ")"

            else:
                fidList = str(tuple(fidList))

            sql = arcpy.AddFieldDelimiters(inLayer, fidFld) + " in " + fidList
            #PrintMsg(" \n " + sql, 0)
            arcpy.SelectLayerByAttribute_management(inLayer, "NEW_SELECTION", sql)

        else:
            arcpy.SelectLayerByAttribute_management(inLayer, "CLEAR_SELECTION")

    if bProcessed:
        if inFieldName == "":
            PrintMsg(" \nProcessing complete \n ", 0)

        else:
            PrintMsg(" \nProcessing complete, join table to the appropriate spatial layer on " + inFieldName + " to create a status map \n ", 0)

    try:
        del inLayer

    except NameError:
        pass

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e) + " \n", 2)

except:
    errorMsg()

    try:
        del inLayer

    except NameError:
        pass
