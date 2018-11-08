gdal_tif2sdat <- function(x, copy){
  
  cat(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"copying", copy,"\n")
  
  gdal_translate(
    src_dataset = x,
    dst_dataset = copy, 
    of        = "SAGA",  
    stats     = TRUE,
    verbose   = TRUE,
    overwrite = TRUE
    )
  }


gdal_sdat2tif <- function(x, copy, datatype, nodata){
  
  cat(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"copying", copy,"\n")
  
  gdal_translate(
    src_dataset = x,
    dst_dataset = copy, 
    ot = datatype,
    of = "GTiff",
    co = c("COMPRESS=DEFLATE", "TILED=YES", "BIGTIFF=YES"),
    stats = TRUE,
    a_nodata = nodata,
    verbose = T,
    overwrite = TRUE
    )
  gdaladdo(
    filename = copy,
    r = "nearest",
    levels = c(2, 4, 8, 16),
    clean = TRUE,
    ro = TRUE
    )
  gdalinfo(
    datasetname = copy, 
    stats = TRUE,
    hist = TRUE
    )
  }


batchSubsetSAGA <- function(grid, subsets, ref){
  for(i in seq(subsets)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "copying", subsets[i], "\n"))
    bb <- bbox(raster(ref[i]))
    
    gdal_translate(
      src_dataset = grid,
      dst_dataset = subsets[i],
      projwin = c(bb[1,1], bb[2,2], bb[1,2], bb[2,1]),
      of = "SAGA",
      a_nodata = -99999,
      overwrite = TRUE,
      verbose = TRUE
    )
  }
}

gdal_shift <- function(x, s){
  copy <- paste0(strsplit(x, ".sdat"), "_s.sdat")
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"shifting", copy[i],"\n"))
    bb <- bbox(raster(x[i]))
    gdal_translate(
      src_dataset = x[i],
      dst_dataset = copy[i],
      of = "SAGA",
      a_ullr = c(bb[1,1]+s[1], bb[2,2]+s[2], bb[1,2]+s[3], bb[2,1]+s[4]),
      stats = TRUE,
      verbose = T
    )
  }
}


gdal_stack <- function(x, fname, format, nodata){
  
  fname.vrt <- sub(".tif$", ".vrt", fname)
  
  cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"stacking", fname,"\n"))
  
  gdalbuildvrt(
    gdalfile = x, 
    output.vrt = fname.vrt,
    separate  = TRUE,
    overwrite = TRUE,
    verbose   = TRUE
    )
  gdal_translate(
    src_dataset = fname.vrt,
    dst_dataset = fname,
    of = "GTiff",
    ot = format,
    a_nodata = nodata,
    co = c("TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=YES"),
    overwrite = TRUE,
    verbose   = TRUE
    )
  gdaladdo(
    filename = fname,
    r = "nearest",
    levels = c(2, 4, 8, 16),
    clean  = TRUE,
    ro     = TRUE
    )
  gdalinfo(
    datasetname = fname, 
    stats = TRUE,
    hist  = TRUE
    )
  }

