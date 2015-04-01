gdal_GTiff2SAGA <- function(demlist, copylist){
  for(i in seq(demlist)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"copying", copylist[i],"\n"))
    gdal_translate(
      src_dataset=demlist[i],
      dst_dataset=copylist[i], 
      of="SAGA",  
      stats=TRUE,
      verbose=T)
  }
}

gdal_SAGA2GTiff <- function(x, copylist, datatype, nodata){
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"copying", copylist[i],"\n"))
    gdal_translate(
      src_dataset=x[i],
      dst_dataset=copylist[i], 
      ot=datatype, 
      co=c("TILED=YES", "COMPRESS=DEFLATE, BIGTIFF=YES"),
      stats=TRUE,
      a_nodata=nodata,
      verbose=T
    )
    gdaladdo(
      filename=copylist[i],
      r="nearest",
      levels=c(2, 4, 8, 16),
      clean=TRUE,
      ro=TRUE
    )
    gdalinfo(
      datasetname=copylist[i], 
      stats=TRUE,
      hist=TRUE
    )
  }
}


batchSubsetSAGA <- function(grid, grids, ref){
  for(i in seq(grids)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "copying", grids[i], "\n"))
    bb <- bbox(raster(ref[i]))
    
    gdal_translate(
      src_dataset=grid,
      dst_dataset=grids[i],
      projwin=c(bb[1,1], bb[2,2], bb[1,2], bb[2,1]),
      of="SAGA",
      a_nodata=-99999,
      overwrite=TRUE,
      verbose=TRUE
    )
  }
}

gdal_shift <- function(x, s){
  copy <- paste(strsplit(x, ".sdat"), "_s.sdat", sep="")
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"shifting", copy[i],"\n"))
    bb <- bbox(raster(x[i]))
    gdal_translate(
      src_dataset=x[i],
      dst_dataset=copy[i],
      of="SAGA",
      a_ullr=c(bb[1,1]+s[1], bb[2,2]+s[2], bb[1,2]+s[3], bb[2,1]+s[4]),
      stats=TRUE,
      verbose=T
    )
  }
}

gdal.stack <- function(x, fname, format, nodata){
  fname.vrt <- paste(strsplit(fname, ".tif"), ".vrt", sep="")
  for(i in seq(fname)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"stacking", fname[i],"\n"))
    xi <- c(x[[1]][i], x[[2]][i], x[[3]][i])
    gdalbuildvrt(
      gdalfile=xi, 
      output.vrt=fname.vrt[i],
      separate=TRUE,
      overwrite=TRUE,
      verbose=TRUE
      )
    gdal_translate(
      src_dataset=fname.vrt[i],
      dst_dataset=fname[i],
      of="GTiff",
      ot=format,
      a_nodata=nodata,
      co=c("TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=YES"),
      overwrite=TRUE,
      verbose=TRUE
      )
    gdaladdo(
      filename=fname[i],
      r="nearest",
      levels=c(2, 4, 8, 16),
      clean=TRUE,
      ro=TRUE
    )
    gdalinfo(
      datasetname=fname[i], 
      stats=TRUE,
      hist=TRUE
    )
  }
}

