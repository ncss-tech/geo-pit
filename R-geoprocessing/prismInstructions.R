setwd("/media/EXTERNAL/Work/geodata/climate/PRISM")
library(RSAGA)

# Import grids
months <- c("01", "02", "03", "04", "05", "06", "08", "09", "10", "11", "12", "14")

ppt.gz <- paste("us_ppt_1971_2000.", months, ".gz", sep="")
tmax.gz <- paste("us_tmax_1971_2000.", months, ".gz", sep="")
tmin.gz <- paste("us_tmin_1971_2000.", months, ".gz", sep="")
prism.gz <- c(ppt.gz, tmax.gz, tmin.gz)

ppt.txt <- paste("us_ppt_1971_2000.", months, ".txt", sep="")
tmax.txt <- paste("us_tmax_1971_2000.", months, ".txt", sep="")
tmin.txt <- paste("us_tmin_1971_2000.", months, ".txt", sep="")
prism.txt <- c(ppt.txt, tmax.txt, tmin.txt)

tmean <- "M:/geodata/climate/prism/PRISM_tmean_30yr_normal_800mM2_all_asc/PRISM_tmean_30yr_normal_800mM2_annual_asc.asc"
ppt <- "M:/geodata/climate/prism/PRISM_ppt_30yr_normal_800mM2_all_asc/PRISM_ppt_30yr_normal_800mM2_annual_asc.asc"

for(i in seq(prism.gz)){
  gunzip(prism.gz[i], prism.txt[i])
}



rsaga.rescale.loop=function(grid.list,name,formula)
for(i in 1:length(grid.list)){
  rsaga.geoprocessor("grid_calculus",1,list(
  GRIDS=paste(grid.list[i],".sgrd",sep=""),
  RESULT=paste(name,grid.list[i],".sgrd",sep=""),
  FORMULA=formula))
}

rsaga.convert.loop(ppt.list)
rsaga.convert.loop(tmax.list)
rsaga.convert.loop(tmin.list)

rsaga.rescale.loop(ppt.list,"in_","(a/100)*0.0393701")
rsaga.rescale.loop(tmax.list,"F_","(((a/100)*2)-((a/100)*2*0.1)+32)")
rsaga.rescale.loop(tmin.list,"F_","(((a/100)*2)-((a/100)*2*0.1)+32)")

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

office.l <- office.l[11]

res <- "10"
tmean.l <- paste0(pd.p, office.l, "/prism", res, "m_11", office.l, "_tmean_1981_2010_annual_C.tif")
ppt.l <- paste0(pd.p, office.l, "/prism", res, "m_11", office.l, "_ppt_1981_2010_annual_mm.tif")
ffp <- "M:/geodata/climate/rmrs/ffp.txt"
ffp.l <- paste0(pd.p, office.l, "/rmrs", res, "m_11WAV_ffp_1961_1990_annual_days.tif")
nlcd.p <- paste0(pd.p, office.l, "/nlcd", "30m_", office.l, "_lulc2011.tif")

co=c("TILED=YES", "COMPRESS=DEFLATE")
batchWarp(tmean, tmean.l, nlcd.p, res, "cubicspline", "EPSG:4269", crsarg, "Int16", "-32768", co)
batchWarp(ppt, ppt.l, nlcd.p, res, "cubicspline", "EPSG:4269", crsarg, "Int16", "-32768", co)
batchWarp(ffp, ffp.l, nlcd.p, res, "cubicspline", CRSargs(CRS("+init=EPSG:4326")), crsarg, "Int16", "-32768", co)

