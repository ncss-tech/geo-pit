# Examine standard deviation with cor plots

# INITIATE GRASS SESSION
library(spgrass6)
initGRASS(
  gisBase="C:/Program Files/QGIS Chugiak/apps/grass/grass-6.4.3/bin",
  location="C:/grassdata/region11",
  mapset="PERMANENT",
  override=TRUE,
  use_g.dirseps.exe=TRUE)

window.list<-c(3,5,7,9,15,21,27)
dem<-"samb27m_ug"
# FUNCTION TO EXPORT LIST A OF RASTERS
spgrass.r.in.gdal<-function(input.list,output.list){
  for(i in 1:length(input.list)){
    execGRASS("r.in.gdal",
              parameters=list(
                input=input.list[i],
                output=output.list[i],
                nodata=-99999,
                type="Float32"))
  }
}

# FUNCTION TO COMPUTE TERRAIN PARAMETERS OVER A RANGE OF WINDOW SIZES
spgrass.r.param.scale<-function(input,output.list,window,param){
  for(i in 1:length(window)){
    execGRASS("r.param.scale",
              flags="overwrite",
              parameters=list(
                input=input,
                output=output.list[i],
                size=as.integer(window[i]),
                param=param))
  }
}

# FUNCTION TO EXPORT LIST A OF RASTERS
spgrass.r.out.gdal<-function(input.list,output.list){
  for(i in 1:length(input.list)){
    execGRASS("r.out.gdal",
              parameters=list(
                input=input.list[i],
                output=output.list[i],
                nodata=-99999,
                format="SAGA",
                type="Float32"))
  }
}

# FUNCTION TO SELECT OPTIMAL WINDOW SIZE FROM SAGA RASTER WINDOW OF VARIANCE
spgrass.select<-function(wov,window.list,input.list,test.list){
  for(i in 1:length(input.list)){
    n<-1:length(input.list)
    execGRASS("r.mapcalculator",
              flags="overwrite",
              parameters=list(
                outfile=paste("test",n[i]+1,sep=""),
                formula=paste("if(",wov,"==",window.list[i],",",input.list[i],",","test",n[i],")",sep="")))
  }
}

execGRASS("g.region",rast="samb09m_ug")
wov<-"samb09m_ug_wov4"
window.list<-seq(3,11,by=2)
dem<-"samb09m_ug"
input.list<-paste(dem,"_kc",window.list,"w",sep="")
test.list<-paste("test",1:length(window.list)+1,sep="")
spgrass.select("samb09m_ug_wov4",window.list,input.list,test.list)

rsaga.select<-function(wov,window.list,input.list,test){
  n<-1:length(input.list)
  for(i in 1:length(input.list)){
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(c(wov,input.list[i],test[i]),collapse=";"),
      RESULT=paste(test[i+1],sep=""),
      FORMULA=paste("ifelse(",a,"=",window.list[i],",",b[i],",",c[i],")",sep="")))
  }
}

window.list<-seq(11,13,by=2)
input.list<-paste("ned30m_moja_kt",window.list,"w.sgrd",sep="")
test<-paste("test",1:3,".sgrd",sep="")



z.list<-paste(dem,"_z",window.list,"w",sep="")
sg.list<-paste(dem,"_sg",window.list,"w",sep="")
kp.list<-paste(dem,"_kp",window.list,"w",sep="")
kc.list<-paste(dem,"_kc",window.list,"w",sep="")
sa.list<-paste(dem,"_sa",window.list,"w",sep="")
kmax.list<-paste(dem,"_kmax",window.list,"w",sep="")
kmin.list<-paste(dem,"_kmin",window.list,"w",sep="")

execGRASS("g.region",rast=dem)
spgrass.r.param.scale(dem,z.list,window.list,"elev")
spgrass.r.param.scale(dem,sg.list,window.list,"slope")
spgrass.r.param.scale(dem,kp.list,window.list,"profc")
spgrass.r.param.scale(dem,kc.list,window.list,"planc")
spgrass.r.param.scale(dem,sa.list,window.list,"aspect")
spgrass.r.param.scale(dem,kmax.list,window.list,"maxic")
spgrass.r.param.scale(dem,kmin.list,window.list,"minic")

z.sdat.list<-paste(dem,"_z",window.list,"w.sdat",sep="")
sg.sdat.list<-paste(dem,"_sg",window.list,"w.sdat",sep="")
sa.sdat.list<-paste(dem,"_sa",window.list,"w.sdat",sep="")
kp.sdat.list<-paste(dem,"_kp",window.list,"w.sdat",sep="")
kmax.sdat.list<-paste(dem,"_kmax",window.list,"w.sdat",sep="")
kmin.sdat.list<-paste(dem,"_kmin",window.list,"w.sdat",sep="")

execGRASS("g.region",rast="ned10m_moja")
spgrass.r.out.gdal(z.list,z.sdat.list)
spgrass.r.out.gdal(sg.list,sg.sdat.list)
spgrass.r.out.gdal(sa.list,sa.sdat.list)
spgrass.r.out.gdal(kp.list,kp.sdat.list)
spgrass.r.out.gdal(kc.list,kc.sdat.list)
spgrass.r.out.gdal(kmax.list,kmax.sdat.list)
spgrass.r.out.gdal(kmin.list,kmin.sdat.list)

# Create grid lists
z.sgrd.list<-paste(dem,"_z",window,"w.sgrd",sep="")
sg.sgrd.list<-paste(dem,"_sg",window,"w.sgrd",sep="")
sgp.sgrd.list<-paste(dem,"_sgp",window,"w.sgrd",sep="")
sa.sgrd.list<-paste(dem,"_sa",window,"w.sgrd",sep="")
sa.sgrd.list360<-paste(dem,"_sa",window,"w360.sgrd",sep="")
kp.sgrd.list<-paste(dem,"_kp",window,"w.sgrd",sep="")
kc.sgrd.list<-paste(dem,"_kc",window,"w.sgrd",sep="")
kt.sgrd.list<-paste(dem,"_kt",window,"w.sgrd",sep="")
kmax.sgrd.list<-paste(dem,"_kmax",window,"w.sgrd",sep="")
kmin.sgrd.list<-paste(dem,"_kmin",window,"w.sgrd",sep="")

# Convert SG to SGp, -Kc to Kc, and Kc to Kt
# GRASS curvature values differ from ILWIS scripts by a factor of 100
# Conversion from Kc to Kt using Schmidt formulas based on Cmax and Cmin unsuccessful
rsaga.grid.calculus=function(a.list, name.list, formula){
  library(RSAGA)
  for(i in 1:length(a.list)) {
    rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(c(a.list[i],b.list[i]),collapse=";"),
      RESULT=paste(name.list[i],sep=""),
      FORMULA=formula))
  }
}

rsaga.grid.calculus(sg.list,sg.list,sgp.list,"tan(a*(1/57.295780000000001))*100")
rsaga.grid.calculus(sa.list,sa.list,sa.list360,"ifelse(a>90,a-90,a+270)")
rsaga.grid.calculus(kp.list,kp.list,kp.list,"a*100")
rsaga.grid.calculus(kc.list,kc.list,kc.list,"-100*a")
rsaga.grid.calculus(kc.list,sg.list,kt.list,"a*sin(b/57.295780000000001)")

# Merge scaled grids using radius of variance grid
rsaga.grid.merge=function(a,b.list,name,formula){
  library(RSAGA)
  rsaga.geoprocessor("grid_calculus",1,list(
      GRIDS=paste(c(a,b.list),collapse=";"),
      RESULT=paste(name,sep=""),
      FORMULA=formula))
}

rsaga.grid.merge(
  "ned10m_moja_radiusOfVariance.sgrd",
  kmin.list,
  "ned10m_moja_ms_kmin.sgrd",
"ifelse(a=10,b,
ifelse(a=20,c,
ifelse(a=30,d,
ifelse(a=40,e,
ifelse(a=50,f,
ifelse(a=60,g,
ifelse(a=70,h,
ifelse(a=80,i,
ifelse(a=90,j,
ifelse(a=100,k,
ifelse(a=110,l,
ifelse(a=120,m,m))))))))))))"
)
