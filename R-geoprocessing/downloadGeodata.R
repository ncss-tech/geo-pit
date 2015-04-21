# Cadastral
setwd("M:/geodata/cadastral/")
states <- c("ia", "il", "in", "ks", "ky", "mi", "mn", "mo", "ne", "oh", "ok", "sd", 
            "wi")
zipname <- paste0("alt_", states, ".zip")
url <- paste0("http://www.geocommunicator.gov/shapefilesall/state/", zipname)
dest <- paste0(getwd(), "/", zipname)

for(i in seq(states)){
  download.file(url=url[i], destfile=dest[i])
}

for(i in seq(states)){
  unzip(zipfile=dest[i])
}


# Elevation
# Download img NED tiles
# For some reason this only works from the R console not Rstudio
img <- readOGR(dsn="I:/geodata/elevation/ned/tiles", layer="ned_meta_R11", encoding="ESRI_Shapefile")
img <- sort(data.frame(img)$FILE_ID)

url <- paste0("ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/NED/13/IMG/", img, ".zip")
dest <- paste0("I:/geodata/elevation/ned/tiles/img/", img, ".zip")

for(i in seq(img)){
  download.file(url=url[i], destfile=dest[i])
}


# Imagery
# Download hdf WELD tiles
library(RCurl)
library(rgdal)
library(raster)

url <- "http://e4ftl01.cr.usgs.gov/WELD/"

# Year lists
weldyr <- "WELDUSYR.001/"
yrs <- c("2009.12.01/", "2010.12.01/", "2011.12.01/")
yr.p <- paste0(url, weldyr, yrs)
yr.p.l <- lapply(yr.p, getURL)
f1 <- function(x) strsplit(strsplit(x, "CONUS.")[[1]], ".hdf")
yr.p.l <- lapply(yr.p.l, f1)
f2 <- function(x) grep(pattern="v1.5", x=unlist(x), value=T)
yr.p.l <- lapply(yr.p.l, f2)
yr.p.l <- lapply(yr.p.l, function(x) unique(x))

# Season lists
weldse <- "WELDUSSE.001/"
ses <- c(2009, rep(2010, 4), rep(2011, 4), rep(2012, 3))
sesm <- rep(c(".12.01/", ".03.01/", ".06.01/", ".09.01/"), 3)
se.p <- paste0(url, weldse, ses, sesm)
se.p.l1 <- lapply(se.p, getURL)
f1 <- function(x) strsplit(strsplit(x, "CONUS.")[[1]], ".hdf")
se.p.l <- lapply(se.p.l1, f1)
f2 <- function(x) grep(pattern="v1.5", x=unlist(x), value=T)
se.p.l <- lapply(se.p.l, f2)
se.p.l <- lapply(se.p.l, function(x) unique(x))

# Weld tile list
weldtiles <- readOGR(dsn="M:/geodata/imagery/landsat/WELD-ARC", layer="WeldConusTiles", encoding="ESRI Shapefile")
weldtiles <- spTransform(weldtiles, CRS("+init=epsg:5070"))
sapolygon <- readOGR(dsn="M:/geodata/soils/Region_11_FY14.gdb", layer="SAPOLYGON", encoding="OpenFileGDB")
int <- raster::intersect(sapolygon, weldtiles)
int.df <- slot(int, "data")
h_v_fix <- sapply(int.df[1], function(x) ifelse(nchar(int.df$v)==1, paste0("h", int.df$h, "v0", int.df$v), as.character(int.df$h_v)))

# Download year lists
weld.l <- sort(unique(as.character(h_v_fix)))
weld.l <- lapply(yr.p.l, function(y) sapply(weld.l, function(x) grep(x, y, value=TRUE)))
weld.l <- lapply(weld.l, function(x) paste0("CONUS.", x, ".hdf"))

url.yr <- paste0(rep(yr.p, each=length(unlist(weld.l))/3))
url.yr <- paste0(url.yr, unlist(weld.l))  
dest.yr <- unlist(lapply(weld.l, function(x) paste0("M:/geodata/imagery/landsat/WELD/year/", x)))

for(i in seq(url.yr)){
  download.file(url=url.yr[i], destfile=dest.yr[i], mode="wb", cacheOK=TRUE)
}

# Download season lists
se.l <- sort(unique(as.character(h_v_fix)))
se.l <- lapply(se.p.l, function(y) sapply(se.l, function(x) grep(x, y, value=TRUE)))
se.l <- lapply(se.l, function(x) paste0("CONUS.", x, ".hdf"))

url.se <- paste0(rep(se.p, each=length(unlist(se.l))/12))
url.se <- paste0(url.se, as.character(unlist(se.l))) 
dest.se <- unlist(lapply(se.l, function(x) paste0("M:/geodata/imagery/landsat/WELD/season/", x)))

for(i in seq(url.se)){
  download.file(url=url.se[i], destfile=dest.se[i], mode="wb", cacheOK=TRUE)
}

# Geographic names
states <- c("IA", "IL", "IN", "KS", "KY", "MI", "MN", "MO", "NE", "OH", "OK", "SD", 
            "WI")
for(i in seq(states)){
  test <- read.delim(paste0("M:/geodata/geographic_names/", states[i], "_Features_20141202.txt"), stringsAsFactors=F, header=T, sep="|")
  test2 <- test[, c(1:11,16:20)]
  test2$ELEV_IN_FT <- as.numeric(test2$ELEV_IN_FT)
  test2$ELEV_IN_M <- test2$ELEV_IN_FT*0.3048
  test3 <- na.exclude(test2)
  coordinates(test3) <- ~PRIM_LONG_DEC+PRIM_LAT_DEC
  proj4string(test3) <- CRS("+init=epsg:4326")
  writeOGR(test3, dsn="M:/geodata/geographic_names", layer=paste0(states[i], "_Features_20141202"), driver="ESRI Shapefile")
}


# Govunits
download.file(
  "ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/GovtUnit/FileGDB101/GOVTUNIT_NATIONAL.zip",
  "M:/geodata/government_units/GOVTUNIT_NATIONAL.zip")

index <- c(19, 17, 18, 20, 21, 26, 27, 29, 31, 39, 40, 46, 55)
states <- c("ia", "il", "in", "ks", "ky", "mi", "mn", "mo", "ne", "oh", "ok", "sd", 
            "wi")
zipname <- paste0("tlgdb_2014_a_", index, "_", states, ".gdb.zip")
extra <- c("tlgdb_2014_a_us_addr.gdb.zip")
zipname <- c(zipname, extra)
url <- paste0("ftp://ftp2.census.gov/geo/tiger/TGRGDB14/", zipname)
dest <- paste0(getwd(), "/", zipname)

for(i in seq(states)){
  download.file(url=url[i], destfile=dest[i])
}

for(i in seq(states)){
  unzip(zipfile=dest[i])
}

# http://www.gadm.org/


# Hydrography
# Download NHD by State
# The FileGDB are to big to be read into R, so they need to be converted using ogr2ogr with gdalUtils. However these FileGDB first need to be upgrade to ArcGIS 10.0. The ESRI File Geodatabase driver doesn't work with 
setwd("I:/geodata/hydrography/")
states <- c("IA", "IL", "IN", "KS", "KY", "MI", "MN", "MO", "NE", "OH", "OK", "SD", 
            "WI")
version <- c("v210", "v220", "v220", "V210", "v210", "v210", "v220", "v220", "v220", "v220", "v210", "v220", "v210")
zipname <- paste("NHDH_", states, "_931", version, ".zip", sep="")
url <- paste("ftp://nhdftp.usgs.gov/DataSets/Staged/States/FileGDB/HighResolution/", zipname, sep="")
dest <- paste(getwd(), "/", zipname, sep="")

for(i in seq(states)){
  download.file(url=url[i], destfile=dest[i])
}

for(i in seq(states)){
  unzip(zipfile=dest[i])
}

gdal_setInstallation(search_path="C:/ProgramData/QGIS/QGISDufour/bin", rescan=T)

ogr2ogr(
  src_datasource_name="I:/geodata/hydrography/NHDH_IN.gdb",
  dst_datasource_name="C:/Users/stephen.roecker/Documents/NHDH_IN_Flowline.shp",
  layer="NHDFlowline",
  overwrite=T,
  verbose=T)


# Soils
# OSDs
"ftp://ftp-fc.sc.egov.usda.gov/NSSC/pub/OSD_QA_QC_Files/NASIS_designated_OSDS.zip"

# Download netCDF dSSURGO tiles
# GDAL won't read netcdf files bigger than 2GB, not sure what the dssurgo dude is using to read/write his files

library(RCurl)

dssurgo <- "http://stream.princeton.edu/dSSURGO/"

makeDssurgoList <- function(dsn, office){
  ned.l <- list()
  nedtiles <- readOGR(dsn="M:/geodata/elevation/ned/tiles", layer="ned_13arcsec_g", encoding="ESRI Shapefile")
  nedtiles <- spTransform(nedtiles, CRS("+init=epsg:5070"))
  for(i in seq(office)){
    sapolygon <- readOGR(dsn=dsn[i], layer="SAPOLYGON", encoding="OpenFileGDB")
    proj4string(sapolygon) <- CRS(as.character(NA))
    proj4string(sapolygon) <- proj4string(nedtiles)
    int <- intersect(sapolygon, nedtiles)
    ned.l[[i]] <- sort(unique(as.character(paste0(int@data$UL_LAT, ",", abs(int@data$UL_LON)))))
  }
  return(ned.l=ned.l)
}

test <- makeDssurgoList(dsn, office.l)
test2 <- lapply(test, strsplit, ",")
g <- lapply(test2, function(x) lapply(x, function (x) paste0("lat", x[1], as.numeric(x[1])+1, "_lon-", x[2], "-", as.numeric(x[2])-1, ".nc")))
g <- unlist(g)

url <- paste0(dssurgo, g)
dest <- paste0("M:/geodata/soils/dssurgo/tiles/", g)

for(i in seq(url)){
  download.file(url=url[i], destfile=dest[i], mode="wb", cacheOK=TRUE)
}


# Transportation
# http://www.census.gov/geo/maps-data/data/tiger.html
dir.create(path="M:/geodata/transportation/", recursive=T) # create directory
setwd("M:/geodata/transportation/")
zipname <- "tlgdb_2014_a_us_roads.gdb.zip"

url <- paste0("ftp://ftp2.census.gov/geo/tiger/TGRGDB14/", zipname)
dest <- paste0(getwd(), "/", zipname)

download.file(url=url, destfile=dest)
unzip(zipfile=dest)



# Wetlands
dir.create(path="M:/geodata/wetlands/", recursive=T) # create directory
setwd("M:/geodata/wetlands/")
states <- c("IA", "IL", "IN", "KS", "KY", "MI", "MN", "MO", "NE", "OH", "OK", "SD", 
            "WI")
zipname <- paste0(states, "_wetlands.zip")
url <- paste0("http://www.fws.gov/wetlands/Downloads/State/", zipname)
dest <- paste0(getwd(), "/", zipname)

for(i in seq(states)){
  download.file(url=url[i], destfile=dest[i])
}

for(i in seq(states)){
  unzip(zipfile=dest[i])
}

# FEMA
http://www.floodmaps.fema.gov/NFHL/status.shtml
https://hazards.fema.gov/nfhlv2/output/County/01013C_20090911.zip