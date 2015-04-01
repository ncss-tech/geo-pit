library(rgdal)

setwd("C:/Users/stephen.roecker/Documents/Workspace/garminDump/temp")

myfiles <- list.files()

gpx1<-readOGR(dsn = myfiles[1], layer="waypoints")
gpx2<-readOGR(dsn = myfiles[2], layer="waypoints")
gpx3<-readOGR(dsn = myfiles[10], layer="waypoints")
   
temp1<-rbind(gpx1,gpx2)

temp1<-spTransform(temp1,CRS("+init=epsg:26911"))
temp1@data$x_proj<-temp1@coords[,1]
temp1@data$y_proj<-temp1@coords[,2]
temp1<-subset(temp1,select=c(name,x_proj,y_proj,ele,time))
names(temp1)<-c("SiteID","x_proj","y_proj","altitude","time")
temp1@data$time<-as.POSIXlt(temp1@data$time)

temp2<-spTransform(temp1, CRS("+proj=latlong +datum=NAD83"))
temp3<-spTransform(temp1, CRS("+proj=latlong +datum=WGS84"))
temp1@data$longdms<-as.character(dd2dms(temp2@coords[,2],NS=TRUE))
temp1@data$latdms<-as.character(dd2dms(temp2@coords[,1]))
temp1@data$longdd<-temp3@coords[,1]
temp1@data$latdd<-temp3@coords[,2]

dsn<-getwd()

writeOGR(temp1,dsn=dsn,
         layer="temp",driver="ESRI Shapefile",overwrite_layer=TRUE)

