library(gdalUtils)
library(rgdal)
library(raster)

gdal_setInstallation(search_path="C:/Program Files/QGIS Wien/bin", rescan=T)

source("C:/workspace/geo-pit/trunk/R-geoprocessing/nedFunctions.R")
source("C:/workspace/geo-pit/trunk/R-geoprocessing/gdalUtilsFunctions.R")

# Import grids
months <- c("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "annual")


ppt <- paste0("M:/geodata/climate/prism/PRISM_ppt_30yr_normal_800mM2_all_asc/PRISM_ppt_30yr_normal_800mM2_", months, "_asc.asc")
tmean <- paste0("M:/geodata/climate/prism/PRISM_tmean_30yr_normal_800mM2_all_asc/PRISM_tmean_30yr_normal_800mM2_", months, "_asc.asc")

test <- stack(ppt[c(7:9)]
test2 <- calc(test, function(x) (x[1] + x[2] + x[3]))
writeRaster(test2, paste0("M:/geodata/climate/prism/PRISM_ppt_30yr_normal_800mM2_all_asc/PRISM_ppt_30yr_normal_800mM2_", "summer", "_asc.asc"))


# Function to compute temperature statistics
rsaga.TEMPstats=function(tmax.list,tmin.list){
  
  num.list=1:12
  
  rsaga.geoprocessor("geostatistics_grid",4,list(
    GRIDS=c("F_us_tmax_1971_2000.14.txt.sgrd;F_us_tmin_1971_2000.14.txt.sgrd"),
    MEAN="F_us_tmean_1971_2000.14.sgrd",
    STDDEV="F_us_tsd_1971_2000.14.sgrd"))
  
  rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=c("F_us_tsd_1971_2000.14.sgrd;F_us_tmean_1971_2000.14.sgrd"),
    RESULT="F_us_tcv_1971_2000.14.sgrd",
    FORMULA="a/b*100"))
  
  rsaga.geoprocessor("geostatistics_grid",4,list(
    GRIDS=paste(c(paste("F_",tmax.list,".sgrd",sep=""),paste("F_",tmin.list,".sgrd",sep="")),collapse=";"),
    MAX="F_us_tmax_1971_2000.00.sgrd",
    MIN="F_us_tmin_1971_2000.00.sgrd"))
  
  rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=c("F_us_tmax_1971_2000.00.sgrd;F_us_tmin_1971_2000.00.sgrd"),
    RESULT="F_us_trng_1971_2000.00.sgrd",
    FORMULA="a-b"))
  
  for(i in 1:length(num.list)){
    rsaga.geoprocessor("geostatistics_grid",4,list(
      GRIDS=paste(c(paste("F_",tmax.list[i],".sgrd",sep=""),paste("F_",tmin.list[i],".sgrd",sep="")),collapse=";"),
      MEAN=paste("F_us_tmean_1971_2000.",num.list[i],".sgrd",sep="")))
    }
  tmean.list=paste("F_us_tmean_1971_2000.",num.list[1:12],".sgrd",sep="")
  rsaga.geoprocessor("geostatistics_grid",4,list(
    GRIDS=paste(tmean.list[6:8],sep="",collapse=";"),
    MEAN="F_us_tmeansum_1971_2000.14.sgrd"))
  rsaga.geoprocessor("geostatistics_grid",4,list(
    GRIDS=paste(tmean.list[c(12,1,2)],sep="",collapse=";"),
    MEAN="F_us_tmeanwin_1971_2000.14.sgrd"))
    
  for(i in 1:length(num.list)){
    name="F_us_trng_1971_2000."
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(c(paste("F_",tmax.list[i],".sgrd",sep=""),paste("F_",tmin.list[i],".sgrd",sep="")),collapse=";"),
      RESULT=paste(name,num.list[i],".sgrd",sep=""),
      FORMULA="a-b"))
    }
    rsaga.geoprocessor("geostatistics_grid",4,list(
      GRIDS=paste(name,1:12,".sgrd",sep="",collapse=";"),
      MEAN=paste("F_us_tmdr_1971_2000.14.sgrd",sep="")))
        
  rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=c("F_us_tmdr_1971_2000.14.sgrd;F_us_trng_1971_2000.00.sgrd"),
    RESULT="F_us_tiso_1971_2000.14.sgrd",
    FORMULA="a/b"))
}
# Function to compute precipitation statistics
rsaga.PPTstats=function(ppt.list){
  num.list=1:12
  rsaga.geoprocessor("geostatistics_grid",4,list(
    GRIDS=paste("in_",ppt.list[1:12],".sgrd",sep="",collapse=";"),
    MEAN="in_us_pptmean_1971_2000.14.sgrd",
    STDDEV="in_us_pptsd_1971_2000.14.sgrd",
    MAX="in_us_pptmax_1971_2000.00.sgrd",
    MIN="in_us_pptmin_1971_2000.00.sgrd"))
  rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=c("in_us_pptsd_1971_2000.14.sgrd;in_us_pptmean_1971_2000.14.sgrd"),
    RESULT="in_us_pptcv_1971_2000.14.sgrd",
    FORMULA="a/b*100"))
  rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=paste("in_",ppt.list[6:8],".sgrd",sep="",collapse=";"),
    RESULT="in_us_pptsum_1971_2000.14.sgrd",
    FORMULA="a+b+c"))
  rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=paste("in_",ppt.list[c(12,1,2)],".sgrd",sep="",collapse=";"),
    RESULT="in_us_pptwin_1971_2000.14.sgrd",
    FORMULA="a+b+c"))
} 
# Compute Thornthwaite Precipitation-Effectiveness Index (PE)
rsaga.PEindex=function(ppt.list,tmax.list,tmin.list){
  num.list=1:12
  for(i in 1:length(num.list)){
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste("in_",ppt.list[i],".sgrd",sep=""),
      RESULT=paste("mod_","in_",ppt.list[i],".sgrd",sep=""),
      FORMULA="ifelse(a<0.5,0.5,a)"))
  }
  for(i in 1:length(num.list)){
    rsaga.geoprocessor("geostatistics_grid",4,list(
      GRIDS=paste(c(paste("F_",tmax.list[i],".sgrd",sep=""),paste("F_",tmin.list[i],".sgrd",sep="")),collapse=";"),
      MEAN=paste("F_us_tmean_1971_2000.",num.list[i],".sgrd",sep="")))
  }
  for(i in 1:length(num.list)){
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste("F_us_tmean_1971_2000.",num.list[i],".sgrd",sep=""),
      RESULT=paste("mod_","F_us_tmean_1971_2000.",num.list[i],".sgrd",sep=""),
      FORMULA="ifelse(a<28.4,28.4,a)"))
  }
  for(i in 1:length(num.list)){
    rsaga.geoprocessor("grid_calculus",1,list(
    GRIDS=paste(c(paste("mod_","in_",ppt.list[i],".sgrd",sep=""),paste("mod_","F_us_tmean_1971_2000.",num.list[i],".sgrd",sep="")),collapse=";"),
    RESULT=paste("F_us_PEindex_1971_2000.",num.list[i],".sgrd",sep=""),
    FORMULA="115*((a/(b-10))^1.11)"))
  }
  rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste("F_us_PEindex_1971_2000.",num.list,".sgrd",sep="",collapse=";"),
      RESULT=paste("F_us_PEindex_1971_2000.14.sgrd",sep=""),
      FORMULA=paste(letters[1:12],sep="",collapse="+")))
}

batch_warp(ppt[8], "M:/geodata/project_data/8VIC/prism30m_8VIC_ppt_1981_2010_annual_mm.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "cubicspline", CRSargs(CRS("+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/climate/prism/PRISM_ppt_30yr_normal_800mM2_all_asc/PRISM_ppt_30yr_normal_800mM2_summer_asc.asc", "M:/geodata/project_data/8VIC/prism30m_8VIC_ppt_1981_2010_summer_mm.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "cubicspline", CRSargs(CRS("+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp(tmean[8], "M:/geodata/project_data/8VIC/prism30m_8VIC_tmean_1981_2010_annual_C.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "cubicspline", CRSargs(CRS("+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))


batch_warp("M:/geodata/project_data/8VIC/ned30m_vic8_solar.tif", "M:/geodata/project_data/8VIC/ned30m_8VIC_solar2.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "bilinear", CRSargs(CRS("+init=epsg:26911")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/project_data/8VIC/ned30m_vic8_sr_months.tif", "M:/geodata/project_data/8VIC/ned30m_8VIC_solar_months.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "bilinear", CRSargs(CRS("+init=epsg:26911")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/project_data/8VIC/landsat30m_vic8_b123457.tif", "M:/geodata/project_data/8VIC/landsat30m_8VIC_b123457.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "bilinear", CRSargs(CRS("+init=epsg:26911")), CRSargs(CRS("+init=epsg:5070")), "Byte", 0, c("BIGTIFF=YES"))

batch_warp("M:/geodata/project_data/8VIC/landsat30m_vic8_tc123.tif", "M:/geodata/project_data/8VIC/landsat30m_8VIC_tc123.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "bilinear", CRSargs(CRS("+init=epsg:26911")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/imagery/gamma/namrad_k_aea_nogaps.tif", "M:/geodata/imagery/gamma/gamma30m_8VIC_namrad_k.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "cubicspline", CRSargs(CRS("+init=epsg:5070")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/imagery/gamma/namrad_th_aea_nogaps.tif", "M:/geodata/imagery/gamma/gamma30m_8VIC_namrad_th.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "cubicspline", CRSargs(CRS("+init=epsg:5070")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/imagery/gamma/namrad_u_aea_nogaps.tif", "M:/geodata/imagery/gamma/gamma30m_8VIC_namrad_u.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "cubicspline", CRSargs(CRS("+init=epsg:5070")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))

batch_warp("M:/geodata/project_data/8VIC/cluster15.tif", "M:/geodata/project_data/8VIC/cluster152.tif","M:/geodata/project_data/8VIC/ned30m_8VIC.tif", 30, "near", CRSargs(CRS("+init=epsg:26911")), CRSargs(CRS("+init=epsg:5070")), "Float32", -99999, c("BIGTIFF=YES"))
