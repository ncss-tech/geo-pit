setwd("C:/Users/stephen.roecker/Documents")

dsn<-getwd()

test1<-read.csv("nv755coordinatesUTMNAD83.csv")
coordinates(test1)<- ~UTM.Easting+UTM.Northing
proj4string(test1)<-CRS("+init=epsg:26911")

test2<-read.csv("nv755coordinatesLatLongNAD83.csv")
test2$y<-paste(test2$Lat..Degrees,"d",test2$Lat..Minutes,"'",test2$Lat..Seconds,"\"N",sep="")
test2$x<-paste(test2$Long..Degrees,"d",test2$Long..Minutes,"'",test2$Long..Seconds,"\"W",sep="")
test2$y2<-as.numeric(char2dms(test2$y))
test2$x2<-as.numeric(char2dms(test2$x))
coordinates(test2)<- ~x2+y2
proj4string(test2)<- ("+proj=latlong +datum=NAD83")
test2utm<-spTransform(test2, CRS("+init=epsg:26911"))

test3<-read.csv("nv755coordinatesLatLongNAD27.csv")
test3$y<-paste(test3$Lat..Degrees,"d",test3$Lat..Minutes,"'",test3$Lat..Seconds,"\"N",sep="")
test3$x<-paste(test3$Long..Degrees,"d",test3$Long..Minutes,"'",test3$Long..Seconds,"\"W",sep="")
test3$y2<-as.numeric(char2dms(test3$y))
test3$x2<-as.numeric(char2dms(test3$x))
coordinates(test3)<- ~x2+y2
proj4string(test3)<- ("+proj=latlong +datum=NAD27")
test3utm<-spTransform(test3, CRS("+init=epsg:26911"))

test1.sub<-subset(test1,select=c(User.Site.ID))
test2.sub<-subset(test2utm,select=c(User.Site.ID))
test3.sub<-subset(test3utm,select=c(User.Site.ID))

test<-rbind(test1.sub,test2.sub,test3.sub)

writeOGR(test,dsn=dsn,layer="testFull",driver="ESRI Shapefile",overwrite_layer=TRUE)
