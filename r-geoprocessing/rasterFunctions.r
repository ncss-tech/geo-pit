# Notes
# Iteration shows that the following procedure to produce the most realistic
# separation of classes, based on field experience.
# 1. Average three different seasons of landsat imagery (spring, leafon, and
#    leafoff. This reduces variation in reflectance between different seasons.
# 2. Transform seasonal average of individual bands, into principal components
#    (pc), based on the covariance matrix. This will be using for classifying
#    hills.
# 3. Create mask to separate hills from plains in the analysis, using
#    the multiresolution valley bottom flatness index (MrVBF).
# 4. Prepare data for analysis, by:
#    creating a separate raster stack for hills and plains,
#    defining NA values and layer names, 
#    sample raster stacks,
#    subset dataset into hills and plains,
#    remove the 1st and last pc (this removes the effect of strong shadows on 
#      north slopes and noise),
#    scale variables to have a mean of 0 and standard deviation of 1.
# 5. Evaluate the dataset by examining plots of hclust dendrogram and 
#    kmeans within group sum of squares (WSS) vs. number of groups, to determine
#    the number of potential clusters.
# 6. Perform unsupervised classification by identifying initial clusters with
#    hclust using wards method, input the multivariate means (i.e. centers) of
#    these clusters to kmeans, and then classify the clusters from kmeans using
#    lda and the raster stack.

# Set working directory
setwd("D:/work/Workspace/mojavePreserve")

# Load GIS libraries
library(RSAGA)
library(raster)

# 1. Average different seasons

# 3. Create mask to separate hills from plains

# 4. Data preparation
# Plains
landsat.plains.stack <- stack(
  paste("landsat30m_moja_seasons_b",c(1:5,7),".tif", sep=""),
  "ned30m_moja_ms_mrvbf.tif",
  "ned30m_moja_ms_sgp.tif",
  "mast30m_deserts_2013.tif")
NAvalue(landsat.plains.stack) <- -99999
names(landsat.plains.stack) <- c("band1","band2","band3","band4","band5","band7","mrvbf","slope","mast")
crs(landsat.plains.stack) <- "+init=epsg:26911"

mask.sp <- readOGR(dsn=getwd(), layer="Drainage_Basins1", encoding="ESRI Shapefile")
crs(mask.sp) <- "+init=epsg:26911"
mask.sample<-spsample(mask.sp,n=5000,"stratified")
mask.df<-cbind(mask.sample,over(mask.sample,mask.sp))

landsat.plains.sample <- extract(landsat.plains.stack,mask.sample)
landsat.plains.train <- as.data.frame(na.exclude(landsat.plains.sample))
landsat.plains <- subset(landsat.plains.train,mrvbf>0.5,select=c("band1", "band2", "band3", "band4", "band5", "band7", "slope", "mast"))

# Hills
landsat.hills.stack <- stack(paste("landsat30m_moja_seasons_pc", 2:5, ".sdat", sep=""),
                             "ned30m_moja_ms_mrvbf.sdat",
                             "ned30m_moja_ms_sgp.sdat",
                             "mast30m_deserts_2013.sdat")
NAvalue(landsat.hills.stack) <- -99999
names(landsat.hills.stack) <- c("pc2", "pc3", "pc4", "pc5", "mrvbf", "slope", "mast")
landsat.hills.sample <- sampleRegular(landsat.hills.stack,size=5000,asRaster=TRUE)
landsat.hills.sample <- as.data.frame(landsat.hills.sample)
landsat.hills.sample <- na.exclude(landsat.hills.sample)
landsat.hills <- subset(landsat.hills.sample,mrvbf<0.5,select=c("pc2", "pc3", "pc4", "pc5", "slope", "mast"))

# 5. Evaluate potential clusters

# Function to plot within group sum of squares (WSS)
kmeans.wss.plot=function(dataframe,sequence){
  n<-length(dataframe[,1])
  wss1<-(n-1)*sum(apply(dataframe,2,var))
  wss<-numeric(0)
  for(i in sequence) {
    h=hclust(dist(dataframe),method="ward")
    initial=tapply(as.matrix(dataframe),list(rep(cutree(h,k=i),ncol(dataframe)),col(dataframe)),mean)
    dimnames(initial)=list(NULL,dimnames(dataframe)[[2]])
    W<-sum(kmeans(dataframe,initial,iter.max=1000)$withinss)
    wss<-c(wss,W)
  }
  wss<-c(wss1,wss)
  plot(c(1,sequence),wss,type="l",xlab="Number of groups",ylab="Within groups sum of squares",lwd=2)  
}

kmeans.wss.plot(scale(landsat.plains),c(2:25))
kmeans.wss.plot(scale(landsat.hills,scale=FALSE),c(2:25))

# Examine clusters using hclust
# Plains
h=hclust(dist(scale(landsat.plains)),method="ward")
plot(h)
abline(10,0)
test=cutree(h,h=10);summary(as.factor(test))
abline(20,0)
test=cutree(h,h=20); summary(as.factor(test))
abline(30,0)
test=cutree(h,h=30); summary(as.factor(test))
abline(40,0)
test=cutree(h,h=40); summary(as.factor(test))
abline(50,0)
test=cutree(h,h=50); summary(as.factor(test))

# Hills
h=hclust(dist(scale(landsat.hills)),method="ward")
plot(h)
abline(10,0)
test=cutree(h,h=10);summary(as.factor(test))
abline(15,0)
test=cutree(h,h=15);summary(as.factor(test))
abline(20,0)
test=cutree(h,h=20); summary(as.factor(test))
abline(30,0)
test=cutree(h,h=30); summary(as.factor(test))
abline(40,0)
test=cutree(h,h=40); summary(as.factor(test))
abline(50,0)
test=cutree(h,h=50); summary(as.factor(test))

# 6. Create unsupervised classification 
# Function to create unsupervised classificaiton using hclust, kmeans, and randomForest
uClass.f<-function(dataframe,stack,sequence){
  uClass.list <- list()
  for(i in sequence){
    uClass.list[[1]] <- dataframe
    dataframe.sc <- scale(dataframe)
    h <- hclust(dist(dataframe.sc), method="ward")
    uClass.list[[2]] <- h
    initial <- tapply(as.matrix(dataframe.sc), list(rep(cutree(h, k=i),ncol(dataframe.sc)) ,col(dataframe.sc)) ,mean)
    dimnames(initial) <- list(NULL, dimnames(dataframe.sc)[[2]])
    km <- kmeans(dataframe.sc, initial, iter.max=1000)
    uClass.list[[3]] <- km
    cluster <- as.factor(km$cluster)
    train <- as.data.frame(cbind(dataframe, cluster))
    train.rf <- randomForest(cluster~., data=train, importance=T, proximity=T)
    dataframe.p <- predict(stack, train.rf,type='response', progress="text")
    writeRaster(dataframe.p, filename=paste("R:/soilTemperatureMonitoring/geodata/","cluster", i, ".tif", sep=""), format="GTiff", datatype="INT1U", overwrite=TRUE, progress="text")
    uClass.list[[4]] <- train.rf
  }
  return(uClass.list)
}

unsupervised.classification(landsat.plains,landsat.plains.stack,c(15,10,20))
unsupervised.classification(landsat.hills,landsat.hills.stack,c(15))

# raster function to compute posterior probabilities for lda
unsupervised.probabilities=function(dataframe,stack,k){
  dataframe.sc=scale(dataframe)
  h=hclust(dist(dataframe.sc),method="ward")
  initial=tapply(as.matrix(dataframe.sc),list(rep(cutree(h,k=k),ncol(dataframe.sc)),col(dataframe.sc)),mean)
  dimnames(initial)=list(NULL,dimnames(dataframe.sc)[[2]])
  km=kmeans(dataframe.sc,initial,iter.max=1000)
  cluster=km$cluster
  train=as.data.frame(cbind(dataframe,cluster))
  library(MASS)
  train.lda=lda(cluster~.,data=train)
  n=1:k
  index=1:k+1
  for(i in n) {
    K=predict(stack,train.lda,index=index[i])
    K=setMinMax(K)
    writeRaster(K,
                filename=paste("cluster",k,"_",i,".sdat",sep=""),
                format="SAGA",
                overwrite=TRUE,
                datatype="FLT4S")
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste("cluster",k,"_",i,".sdat",sep=""),
      RESULT=paste("cluster",k,"_",i,".sdat",sep=""),
      FORMULA="a"))
  }
}


# raster function to compute principal components from raster stack
# pname = parameter name (e.g. "sr")
# DEMsame = dem name (e.g. "ifsar30m_pc")
# grid.stack = list of grids (e.g. grid.list=c("sg30m_oi.sdat","ca30m_oi.sdat")
# ssize = size of random sample (e.g. 5000)
# cor = logical value (e.g. T or F) to specify whether correlation matrix is used
raster.pc=function(pname,DEMsame,grid.list,ssize,cor){
  library(raster)
  grid.stack=stack(grid.list)
  grid.sample=sampleRandom(grid.stack,size=ssize,na.rm=TRUE)
  grid.pc=princomp(grid.sample,cor=cor)
  p=c(1:dim(grid.stack)[3])
  for(i in p) {
    pc=predict(grid.stack,grid.pc,index=p[i])
    
    writeRaster(pc,
    filename=paste(pname,"_","pc",p[i],"_",DEMsame,".sdat",sep=""),
    format="SAGA",
    overwrite=TRUE,
    datatype="FLT4S")
  }
}

raster.stack <- function(x, fname, datatype){
  for(i in seq(fname)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"stacking", fname[i],"\n"))
    st <- stack(x[[1]][i], x[[2]][i], x[[3]][i])
    writeRaster(
      x=st,
      filename=fname[i],
      datatype=datatype,
      options=c("BIGTIFF=YES", "COMPRESS=DEFLATE", "TILED=YES"),
      progress="text",
      overwrite=TRUE
      )
  }
}