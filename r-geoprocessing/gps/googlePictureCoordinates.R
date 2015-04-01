library(sp)
library(rgdal)
library(plyr)
library(stringr)

setwd("G:/documentation/pictures/temp/Rsplit")
lf <- list.files()

li <- list()

# Function to extract coordinate metadata from Google Picture files
for(i in seq_along(lf)){
  
  # Extract latitude, format, and convert
  mdata <- ldply(str_split(attr(GDALinfo(lf[i], returnStats=FALSE), "mdata"), "="))
               mdata <- t(pic[2])
               names(mdata) <- pic[1]
               mdata <- data.frame(mdata)
                 lat <- as.character(mdata$EXIF_GPSLatitude)
                 latRef <- as.character(mdata$EXIF_GPSLatitudeRef)
                 lat <- as.numeric(str_replace(str_replace(str_split(lat, " ")[[1]], '\\(', ''), '\\)', ''))
                 lat.d <- lat[1]
                 lat.m <- lat[2]
                 lat.s <- lat[3]
                 lat.dms <- paste(lat.d,"d",lat.m,"'",lat.s,"\"", latRef,sep="")
                 lat.dd <- as.numeric(char2dms(lat.dms))
                 
                 long <- mdata$EXIF_GPSLongitude
                 longRef <- mdata$EXIF_GPSLongitudeRef
                 long <- as.numeric(str_replace(str_replace(str_split(long, " ")[[1]], '\\(', ''), '\\)', ''))
                 long.d <- long[1]
                 long.m <- long[2]
                 long.s <- long[3]
                 long.dms <- paste(long.d,"d",long.m,"'",long.s,"\"", longRef, sep="")
                 long.dd <- as.numeric(char2dms(long.dms), WS=FALSE)
                 
                 time <- as.POSIXlt(mdata$EXIF_DateTimeDigitized,format="%Y:%m:%d %H:%M:%S")
                 ident <- NA
                 usiteid <- NA
  
  coords <- data.frame(lf[i],lat.dms, long.dms, lat.dd, long.dd, time, ident, usiteid)
  colnames(coords) <- c("picture", "lat.dms", "long.dms", "lat.dd", "long.dd", "time", "ident", "usiteid")
  li[[i]] <- coords
}

gps.coords <- ldply(li)
gps.coords.sp <- gps.coords
coordinates(gps.coords.sp) <- ~ long.dd+lat.dd
proj4string(gps.coords.sp) <- CRS("+proj=longlat +datum=WGS84")
plot(gps.coords.sp)
gps.coords.utm.sp <- spTransform(gps.coords.sp, CRS("+init=epsg:26911"))


writeOGR(gps.coords.sp, dsn=getwd(), layer="gps.coords", driver="ESRI Shapefile", overwrite_layer=T)
writeOGR(gps.coords.utm.sp, dsn=getwd(), layer="gps.coords.utm", driver="ESRI Shapefile", overwrite_layer=T)
writeOGR(gps.coords.sp["picture"], layer="gps.coords.kml", "gps.coords.kml", driver="KML", overwrite_layer=T)
