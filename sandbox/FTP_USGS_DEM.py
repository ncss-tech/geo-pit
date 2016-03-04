################################################
#Script downloads USGS NED DEMs based on input file...
# mosaics them together, then clips to input file
#Requires ArcGIS 10.1+ and Spatial Analyst extention
#written by Rob Vaughan 12/18/2015
#USFS-RSAC
################################################

import arcpy,os,os.path,zipfile, urllib

try:
	import urllib.request
except:
	import urllib

from arcpy import *
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

########################################################################
#user variables
########################################################################

outFolder = "G:\\NRCS_NED\\test\\"   #folder where you want things to go
finalDemName = "test"  #just the file name without file extention (ex. ".img")
cellmap = "G:\\NRCS_NED\\DEM\\ned_13arcsec_g.shp"   #cell map sent with code
inextent = "G:\\NRCS_NED\\SSR4_boundary_buffer20WGS84Copy.shp"   #your area of interest, be sure that it is in gcs_WGS84 projection to match the DEM
USGS_URL = 'ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/NED/13/IMG/'   #this is for 10 m DEM, can change for 1,30,90m etc.

########################################################################
#download function
########################################################################

def downloadDEM(filename):
	try:
		a = urllib.request.urlopen(USGS_URL+filename)
	except:
		a = urllib.urlopen(USGS_URL+filename)
	b = a.read()
	c = open(outzip+filename, 'wb')
	c.write(b)
	c.close()
	a = None

########################################################################

#create list of files to download using intersection
print("Gathering DEM tiles to download.....")
print("Tiles to download...")
arcpy.MakeFeatureLayer_management(cellmap, "cell_lyr")
selectCells = SelectLayerByLocation_management("cell_lyr","INTERSECT",inextent,'','')
cellList = []
field = ["FILE_ID"]
with arcpy.da.SearchCursor("cell_lyr",field,) as cellSearch:
    for datarow in cellSearch:
        print(datarow[0])
        cellList.append(datarow[0]+".zip")


#make folder structure
outzip = outFolder+"zips\\"
outunzipped = outFolder+"unzipped\\"

if not os.path.exists(outzip):
    os.makedirs(outzip)

if not os.path.exists(outunzipped):
    os.makedirs(outunzipped)


#do magic
try:
    for cell in cellList:
        filename = cell
        print("Downloading...." + cell)
        downloadDEM(filename) #run function

except Exception as e: #catch error messages
    import traceback, sys
    tb = sys.exc_info()[2]
    print ("Line %i" % tb.tb_lineno)
    print (e.message)
print("Finished downloading zips...")

#unzip all folders
print ("Unzipping all files...")
zipdir = os.listdir(outzip)
for item in zipdir: # loop through items in dir
    if item.endswith(".zip"):
        file_name = outzip+item # get full path of files
        zip_ref = zipfile.ZipFile(file_name) # create zipfile object
        zip_ref.extractall(outunzipped) # extract file to dir
        zip_ref.close() # close file
    else:
        print("Error...Can not unzip files?")
        sys.exit(0)
print ("Finished unzipping all files...")

#mosaic tiles together
print ("Mosaicing DEMs together....")
arcpy.env.workspace = outunzipped#chang workspace to folder with unzipped DEMs
demList = arcpy.ListRasters("*.img")#create a list of all DEMs in directory
arcpy.MosaicToNewRaster_management(demList,outFolder,finalDemName+"_full.img",'','32_BIT_FLOAT','',"1","") #mosaic all DEM into single image
print ("Finished mosaicing DEMs together....")

#extract by mask using original file
print("Clipping DEM to original extent...")
mosaicedfile = outFolder+finalDemName+"_full.img"
outExtractByMask = ExtractByMask(mosaicedfile, inextent)
outExtractByMask.save(outFolder+finalDemName+".img")

#end
print ("Done")