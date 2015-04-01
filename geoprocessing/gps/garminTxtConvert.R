setwd("C:/Workspace/garminDump")
library(sp)
library(rgdal)
temp<-read.csv("C:/Workspace/garminDump/garminDump_2012_1018.txt")
temp$y<-temp$y_proj
temp$x<-temp$x_proj
temp<-subset(temp,select=c(type,ident,lat,long,comment,altitude,model,x,y,x_proj,y_proj))
coordinates(temp)<-~x_proj+y_proj
proj4string(temp)<-CRS("+init=epsg:26911")
writeOGR(temp,dsn="C:/Workspace/garminDump",layer="temp",driver="ESRI Shapefile",overwrite_layer=TRUE)
