setwd("C:/Users/stephen.roecker/Documents")

library(rgdal)



# longlatdms to longlatdd and utm
setwd("C:/Users/stephen.roecker/Documents")
test <- read.csv("coords.csv")
attach(test)
test$latdms <-paste(Std.Longitude,"d",Lat..Degrees,"'", Lat..Seconds, "\"N",sep="")
test$longdms <-paste(longd,"d",longm,"'","\"W",sep="")
test$latdd <- as.numeric.DMS(char2dms(test$latdms))
test$longdd <- as.numeric.DMS(char2dms(test$longdms))
detach(test)
test.sp <- test
coordinates(test.sp) <- ~ longdd+latdd
proj4string(test.sp) <- CRS("+proj=longlat +datum=WGS84")
testutm.sp <- spTransform(test.sp, CRS("+init=epsg:26911"))
testutm.df <- cbind(test, testutm.sp@coords)
names(testutm.df) <- c(names(test), "utmeasting", "utmnorthing")
testutm.sp <- testutm.df
coordinates(testutm.sp) <- ~ utmeasting+utmnorthing
proj4string(testutm.sp) <- CRS("+init=epsg:26911")
write.csv(testutm.df,"C:/Users/stephen.roecker/Documents/testutm.csv")
writeOGR(testutm.sp, dsn=getwd(), layer="testutm", driver="ESRI Shapefile", overwrite=T)



# longlatdd to longlatdms and utm
setwd("C:/Users/stephen.roecker/Documents")
test <- read.csv("test2.csv")
attach(test)
test$latdms <- as.character(dd2dms(test$latdd))
test$longdms <- as.character(dd2dms(test$longdd))
detach(test)
test.sp <- test
coordinates(test.sp) <- ~ longdd+latdd
proj4string(test.sp) <- CRS("+proj=longlat +datum=WGS84")
testutm.sp <- spTransform(test.sp, CRS("+init=epsg:26911"))
testutm2.df <- cbind(test, testutm.sp@coords)
names(testutm2.df) <- c(names(test), "utmeasting", "utmnorthing")
testutm.sp <- testutm2.df
coordinates(testutm.sp) <- ~ utmeasting+utmnorthing
proj4string(testutm.sp) <- CRS("+init=epsg:26911")
write.csv(testutm.df,"C:/Users/stephen.roecker/Documents/testutm2.csv")
writeOGR(testutm.sp, dsn=getwd(), layer="testutm2", driver="ESRI Shapefile", overwrite=T)



# UTM to longlat decimal degrees and degrees minutes seconds
library(rgdal)
test1.sp <- readOGR(dsn=getwd(),layer="ca795_dp")
test1.df <- test1.sp@data
test2.sp <- spTransform(test1.sp, CRS("+proj=longlat +datum=NAD83"))
test1.df$latdd <- as.character(dd2dms(test2.sp@coords[,2],NS=T))
test1.df$longdd <- as.character(dd2dms(test2.sp@coords[,1]))
test3.sp <- spTransform(test1.sp, CRS("+proj=longlat +datum=WGS84"))
test1.df$lat <- test3.sp@coords[,2]
test1.df$long <- test3.sp@coords[,1]
write.csv(test1.df,"C:/Users/stephen.roecker/Documents/test_mast2004.csv")


coordinates(test1)<- ~UTM.Easting+UTM.Northing
proj4string(test1)<-CRS("+init=epsg:26911")

test2<-read.csv("nv755coordinatesLatLongNAD83.csv")
test2$y<-paste(test2$Lat..Degrees,"d",test2$Lat..Minutes,"'",test2$Lat..Seconds,"\"N",sep="")
test2$x<-paste(test2$Long..Degrees,"d",test2$Long..Minutes,"'",test2$Long..Seconds,"\"W",sep="")
test2$y2<-as.numeric.DMS(char2dms(test2$y))
test2$x2<-as.numeric.DMS(char2dms(test2$x))
coordinates(test2)<- ~x2+y2
proj4string(test2)<- ("+proj=latlong +datum=NAD83")
test2utm<-spTransform(test2, CRS("+init=epsg:26911"))

test3<-read.csv("nv755coordinatesLatLongNAD27.csv")
test3$y<-paste(test3$Lat..Degrees,"d",test3$Lat..Minutes,"'",test3$Lat..Seconds,"\"N",sep="")
test3$x<-paste(test3$Long..Degrees,"d",test3$Long..Minutes,"'",test3$Long..Seconds,"\"W",sep="")
test3$y2<-as.numeric.DMS(char2dms(test3$y))
test3$x2<-as.numeric.DMS(char2dms(test3$x))
coordinates(test3)<- ~x2+y2
proj4string(test3)<- ("+proj=latlong +datum=NAD27")
test3utm<-spTransform(test3, CRS("+init=epsg:26911"))

test1.sub<-subset(test1,select=c(User.Site.ID))
test2.sub<-subset(test2utm,select=c(User.Site.ID))
test3.sub<-subset(test3utm,select=c(User.Site.ID))

test<-rbind(test1.sub,test2.sub,test3.sub)

writeOGR(test,dsn=dsn,layer="testFull",driver="ESRI Shapefile",overwrite_layer=TRUE)
