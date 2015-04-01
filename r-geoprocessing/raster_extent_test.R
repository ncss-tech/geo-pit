library(gdalUtils)
library(raster)
library(RSAGA)

src_dataset <- system.file("external/tahoe_lidar_bareearth.tif", package="gdalUtils")
test <- raster(x=src_dataset)
writeRaster(test, "test.tif", overwrite=T)

gdal_setInstallation(search_path="C:/ProgramData/QGIS/QGISDufour/bin", rescan=T, verbose=T)
gdalwarp(
  srcfile=src_dataset, 
  dstfile="test_gdal.tif", 
  of="GTiff", 
  r="average",
  ot="Float32",
  tr=res(test)*3, 
  overwrite=TRUE,
  verbose=TRUE)

aggregate(
  x=raster(src_dataset),
  fact=3,
  filename="test_raster.tif",
  format="GTiff",
  NAflag=-99999,
  progress="text",
  overwrite=T)


myenv <- rsaga.env(path="C:/Program Files (x86)/SAGA-GIS")
rsaga.geoprocessor("grid_tools",0, env=myenv, list(
  INPUT="test.sgrd",
  USER_GRID="test_saga.sgrd",
  TARGET="0",
  SCALE_UP_METHOD=6,
  USER_SIZE=res(test)[1]*3,
  GRID_GRID="test_raster.sgrd"))
t <- raster("test_saga.sdat")
writeRaster(x=t, filename="test_saga.tif", format="GTiff", overwrite=T)
