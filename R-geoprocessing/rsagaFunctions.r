# This doesn't seem to work, the SAGA GUI asks for extent parameters that the commandline doesn't have access to
rsaga.mask <- function(grid, mask){
  gridm=paste(strsplit(grid, ".sgrd"), "_mask", ".sgrd", sep="")
  
  for(i in seq(grid)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"masking", grid[i],"\n"))
    
    rsaga.geoprocessor("grid_tools", 24, env=myenv, list(
      GRID=grid[i]),
      MASK=mask[i],
      MASKED=gridm[i]
      )
  }
}
  
  # Fill DEM if the MINSLOPE is set to less than 0.025 it causing the STRAHLER module to fail, if it's set to higher than 0.025 if fills in low relief areas.
rsaga.fill <- function(grid){
  gridf <- paste(strsplit(grid, ".sgrd"), "_filled", ".sgrd", sep="")
  
  for(i in seq(grid)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"filling", grid[i],"\n"))
    rsaga.geoprocessor("ta_preprocessor", 5, env=myenv, list(
      ELEV=grid[i],
      FILLED=gridf[i],
      MINSLOPE=0.025
      )
    )
  }
}

# Local morphometry
rsaga.d0 <- function(dem, radiusD){
  for(i in seq(dem)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating", elev[i],"\n"))
    rsaga.geoprocessor("ta_morphometry", 23,  env=myenv, list(
      DEM=dem[i],
      ELEVATION=elev[i],
      SIZE=radiusD))
  }
}

rsaga.d1 <- function(dem, radiusD){
  for(i in seq(dem)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating 1st derivatives for", dem[i],"\n"))
    rsaga.geoprocessor("ta_morphometry", 23,  env=myenv, list(
      DEM=dem[i],
      SLOPE=slopeD[i],
      ASPECT=aspect[i],
      SIZE=radiusD))
  }
}

rsaga.d2 <- function(dem, radiusD){
  for(i in seq(dem)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating 2nd derivatives for", dem[i],"\n"))
    rsaga.geoprocessor("ta_morphometry", 23,  env=myenv, list(
      DEM=dem[i],
      PROFC=cupro[i],
      PLANC=cucon[i],
      SIZE=radiusD)
      )
  }
}

rsaga.d3 <- function(dem, radiusD){
  for(i in seq(dem)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating 2nd derivatives for", dem[i],"\n"))
    rsaga.geoprocessor("ta_morphometry", 23,  env=myenv, list(
      DEM=dem[i],
      MINIC=cumin[i],
      MAXIC=cumax[i],
      SIZE=radiusD))
  }
}


rsaga.grid.calculus <- function(a.list, b.list, output.list, formula){
  for(i in seq(a.list)) {
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating", output.list[i],"\n"))
    rsaga.geoprocessor("grid_calculus", 1, env=myenv, list(
      GRIDS=paste(c(a.list[i],b.list[i]),collapse=";"),
      RESULT=output.list[i],
      FORMULA=formula))
  }
}


rsaga.residual <- function(x, radius){
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating", relief[i],"\n"))
    rsaga.geoprocessor("geostatistics_grid", 1,  env=myenv, list(
      GRID=x[i],
      PERCENT=relief[i],
      RADIUS=radius))
  }
}

# Multiresolution Index of Valley Bottom Flatness (if grid system is large crop data or must do manually using file caching)
rsaga.mrvbf <- function(dem, valleys, summits){
  for(i in seq(dem)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating mrvbf for", dem[i],"\n"))
    
    rsaga.geoprocessor("ta_morphometry", 8, env=myenv, list(
      DEM=dem[i],
      MRVBF=valleys[i],
      MRRTF=summits[i])
    )
  }
}


# Radius of variance, 1000m seems to be the best radius threshold, after than the rovar starts taking on weird shapes 
rsaga.rov <- function(dem, radius){
  for(i in seq(dem)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating rov for", dem[i],"\n"))
    rsaga.geoprocessor("geostatistics_grid", 3,  env=myenv, list(
      INPUT=dem[i],
      RESULT=rov[i],
      RADIUS=radius))
  }
}


# Catchment area, height, and wetness index
rsaga.ca <- function(grid){
  for(i in seq(grid)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating catchment derivatives for", grid[i],"\n"))
    rsaga.geoprocessor("ta_hydrology", 0, env=myenv, list(
      ELEVATION=grid[i],
      CAREA=carea[i],
      CHEIGHT=cheight[i],
      Method=4)
      )
  }
}


rsaga.twi <- function(slopeR, carea){
  for(i in seq(wetness)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating catchment derivatives for", wetness[i],"\n"))
    rsaga.geoprocessor("ta_hydrology", 20, env=myenv, list(
      SLOPE=slopeR[i],
      AREA=carea[i],
      TWI=wetness[i])
      )
  }
}


rsaga.strahler <- function(x, threshold){
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating", strahler[i],"\n"))
    rsaga.geoprocessor("ta_channels", 5, env=myenv, list(
      DEM=x[i],
      ORDER=strahler[i],
      THRESHOLD=threshold
      )
    )
  }
}


rsaga.ofd <- function(x){
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating", z2stream[i],"\n"))
    rsaga.geoprocessor("ta_channels", 4, env=myenv, list(
      ELEVATION=x[i],
      CHANNELS=strahler.rc[i],
      DISTVERT=z2stream[i]
      )
    )
  }
}





# SAGA Wetness Index
rsaga.geoprocessor("ta_hydrology", 15, list(
  DEM=paste(dem,"_filled.sgrd",sep=""),
  C="test1.sgrd",
  GN="test2.sgrd",
  CS="test3.sgrd",
  SB="test10.sgrd"))

# Relative slope position
rsaga.geoprocessor("ta_morphometry", 14, env=myenv, list(
  DEM=paste(dem,"_filled.sgrd",sep=""),
  HO=zho,
  HU=zhu,
  NH=znorm,
  SH=zstd,
  MS=zmidslope)
  )

# Channel network
rsaga.geoprocessor(lib="ta_channels", module=0, param=list(
ELEVATION=paste("filled_", dem, sep=""),
CHNLNTWRK=paste("cn", gridsize, area, ".sgrd",sep=""),
CHNLROUTE=paste("cnr", gridsize, area, ".sgrd",sep=""),
SHAPES=paste("cn", gridsize, area, ".shp",sep=""),
INIT_GRID=paste("ca", gridsize, area, ".sgrd",sep=""),
INIT_METHOD=2,
INIT_VALUE=INIT_VALUE,
MINLEN=10))

# Altitude above channel network
rsaga.geoprocessor(lib="ta_channels", module=3, param=list(
ELEVATION=paste("filled_", dem, sep=""),
CHANNELS=paste("cn", gridsize, area, ".sgrd",sep=""),
ALTITUDE=paste("zc", gridsize, area, ".sgrd",sep=""),
THRESHOLD=0.1,
NOUNDERGROUND=TRUE))

gdal_setInstallation(search_path="C:/ProgramData/QGIS/QGISDufour/bin", rescan=T)

Int16 <- grids[c(3,4,5,7)]

for(i in seq(Int16)){
  gdal_translate(
    src_dataset=paste(Int16[i], ".sdat", sep=""),
    dst_dataset=paste(Int16[i], ".tif",sep=""),
    of="GTiff",
    ot="Int16",
    stats=T,
    verbose=T,
    a_nodata=-32768,
    overwrite=T)  
}

Float32 <- grids[c(10,11,13,14)]

for(i in seq(Float32)){
  gdal_translate(
    src_dataset=paste(Float32[i], ".sdat", sep=""),
    dst_dataset=paste(Float32[i], ".tif",sep=""),
    of="GTiff",
    ot="Float32",
    stats=T,
    verbose=T,
    a_nodata=-99999,
    overwrite=T)  
}

# RSAGA function to compute montly, seasonal, and seasonality solar radiation
# Compatiability: SAGA Version 2.05
# set the following parameters accordingly
# DEM = digital elevation model (e.g. "ifsar_ned30m_oi.sgrd")
# hours = interval of hours between estimation (e.g. 2)
# days = interval of days between estimation(e.g. 7)
# lat = latitutde (e.g. 34)

rsaga.solar.radiation <- function(DEM,lat,hours,days){
  for(i in 1:length(DEM)){
    DEMn <- DEM[i]
    DAY.A.list=c("0","0","0","0","0","0","0","0","0","0","0","0")
    DAY.B.list=c("30","26","29","28","29","28","29","29","28","29","28","29")
    MONTH.list=c("0","1","2","3","4","5","6","7","8","9","10","11")
    
    for(i in 1:12) {
      
      DEMs <- str_split_fixed(DEMn, pat=".sgrd", n=2)[,1]
      
      rsaga.geoprocessor(lib="ta_lighting", module=2, param=list(
        GRD_DEM=DEMn,
        LATITUDE=lat,
        GRD_TOTAL=paste(DEMs, "_sr_tot_",MONTH.list[i],".sgrd",sep=""),
        GRD_DIRECT=paste(DEMs, "_sr_dir_",MONTH.list[i],".sgrd",sep=""),
        GRD_DIFFUS=paste(DEMs, "_sr_dif_",MONTH.list[i],".sgrd",sep=""),
        PERIOD="2",
        DHOUR=paste(hours,sep=""),
        DDAYS=paste(days,sep=""),
        MON_A=MONTH.list[i],
        DAY_A=DAY.A.list[i],
        MON_B=MONTH.list[i],
        DAY_B=DAY.B.list[i]
      ))
    }
    sum.list=c(
      paste(DEMs, "_sr_tot_6.sgrd",sep=""),
      paste(DEMs, "_sr_tot_7.sgrd",sep=""),
      paste(DEMs, "_sr_tot_8.sgrd",sep=""))
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(sum.list, collapse=";"),
      RESULT=paste(DEMs, "_sr_sum.sgrd",sep=""),
      FORMULA="a+b+c"))
    
    win.list=c(
      paste(DEMs, "_sr_tot_11.sgrd",sep=""),
      paste(DEMs, "_sr_tot_0.sgrd",sep=""),
      paste(DEMs, "_sr_tot_1.sgrd",sep=""))
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(win.list, collapse=";"),
      RESULT=paste(DEMs, "_sr_win.sgrd",sep=""),
      FORMULA="a+b+c"))
    
    ann.list=c(
      paste(DEMs, "_sr_tot_",c(0:11),".sgrd",sep=""))
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(ann.list, collapse=";"),
      RESULT=paste(DEMs, "_sr_ann.sgrd",sep=""),
      FORMULA="a+b+c+d+e+f+g+h+i+j+k+l"))
    
    rsaga.geoprocessor("geostatistics_grid",4,list(
      GRIDS=paste(ann.list, collapse=";"),
      MEAN=paste(DEMs, "_sr_mean.sgrd",sep=""),
      STDDEV=paste(DEMs, "_sr_stddev.sgrd",sep="")))
    
    stat.list=c(
      paste(DEMs, "_sr_mean.sgrd",sep=""),
      paste(DEMs, "_sr_stddev.sgrd",sep=""))
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(stat.list, collapse=";"),
      RESULT=paste(DEMs, "_sr_cv.sgrd",sep=""),
      FORMULA="(b/a)*100"))
  }
}


# RSAGA function to filtering of local outliers using normal probability
# reference     : Hengl, T., S. Gruber, and D.P. Shrestha, 2004. Reduction of errors in digital terrain parameters used in soil-landscape modelling. International Journal of Applied Earth Observation and Geoinformation, 5(2):97-112.
# Compatiability: SAGA Version 2.05
# set the following parameters accordingly
# grid.list = list of grids (e.g. grid.list=c("sg30m_oi.sgrd","ca30m_oi.sgrd")
# deviation = standard deviation of gaussian filter
# shape = shape of filter (e.g. 0=square, 1=circle)
# radius = radius of filter measured in grid cells 
# outliers = condition if TRUE filters oultiers if FALSE filter noise
rsaga.filter.outliers=function(grid.list1,grid.list2,grid.list3,grid.list4,outliers){
  for(i in 1:length(grid.list1)) {
    zdif.list=c(grid.list2[i],grid.list1[i])
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(zdif.list, collapse=";"),
      RESULT=paste("zdif_", grid.list3[i], sep=""),
      FORMULA="a-b"))
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste("zdif_", grid.list3[i], sep=""),
      RESULT=paste("zprob_", grid.list3[i], sep=""),
      FORMULA="(1/sqrt(6.283185)*exp((-a^2)/2)/0.4)"))
    
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste("zprob_", grid.list3[i], sep=""),
      RESULT=paste("zprobi_", grid.list3[i], sep=""),
      FORMULA="sqrt((1-a)^2)"))
    
    if (outliers==TRUE){
      rsaga.geoprocessor("grid_calculus",1,list(
        GRIDS=paste(c(paste("zprob_",grid.list3[i], sep=""),
                      grid.list3[i],grid.list4[i]),collapse=";"),
        RESULT=paste("filtered_",grid.list4[i],sep=""),
        FORMULA="a*b+(1-a)*c"))
    }
    else
      rsaga.geoprocessor("grid_calculus",1,list(
        GRIDS=paste(c(paste("zprobi_",grid.list3[i],sep=""),
                      grid.list3[i],grid.list4[i]),collapse=";"),
        RESULT=paste("filtered_", grid.list4[i],sep=""),
        FORMULA="a*b+(1-a)*c"))
  }
}

# RSAGA function to resample list of grids to specific dimensions
# Compatiability: SAGA Version 2.07
# set the following parameters accordingly
# grid.list = list of grids (e.g. grid.list=c("sg30m_oi.sgrd","ca30m_oi.sgrd")
# METHOD = resampling method; 0 = neareast neighbor; 1 = bilinear;
# 4 = B-spline; 6 = mean value (cell area weighted)
# SIZE = grid size (e.g. 30)
# XMIN = x-coordinate of southwest corner
# XMAX = x-coordinate of southeast corner
# YMIN = y-coordinate of southwest corner
# YMAX = y-coordinate of northwest corner
rsaga.resample.grids=function(grid.list,METHOD,SIZE,XMIN,XMAX,YMIN,YMAX){
  library(RSAGA)
  for(i in 1:length(grid.list)) {
    rsaga.geoprocessor("grid_tools",0,list(
      INPUT=grid.list[i],
      USER_GRID=paste(grid.list[i],sep=""),
      TARGET="0",
      SCALE_DOWN_METHOD=paste(METHOD,sep=""),
      USER_SIZE=paste(SIZE,sep=""),
      USER_XMIN=paste(XMIN,sep=""),
      USER_XMAX=paste(XMAX,sep=""),
      USER_YMIN=paste(YMIN,sep=""),
      USER_YMAX=paste(YMAX,sep="")))
  }
}


### Misc
rsaga.grid.calculus=function(grid.list,name.list,formula){
  library(RSAGA)
  for(i in 1:length(grid.list)) {
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(grid.list[i], sep=""),
      RESULT=paste(name.list[i],sep=""),
      FORMULA=formula))
  }
}

rsaga.reclassify <- function(x, min, max){
  x.rc <- paste(strsplit(x, ".sgrd"), "_rc", max+1, ".sgrd", sep="")
  for(i in seq(x)) {
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"reclassifying", x[i],"\n"))
    rsaga.geoprocessor("grid_tools",15, env=myenv, list(
      INPUT=x[i],
      RESULT=x.rc[i],
      METHOD="1",
      MIN=min,
      MAX=max,
      RNEW=min,
      NODATAOPT=TRUE,
      NODATA=min)
      )
  }
}