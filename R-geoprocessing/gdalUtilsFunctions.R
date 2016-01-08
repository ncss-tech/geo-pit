gdal_GTiff2SAGA <- function(x, copy){
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"copying", copy[i],"\n"))
    gdal_translate(
      src_dataset = x[i],
      dst_dataset = copy[i], 
      of = "SAGA",  
      stats = TRUE,
      verbose = T)
  }
}

gdal_SAGA2GTiff <- function(x, copy, datatype, nodata, of, co){
  for(i in seq(x)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"copying", copy[i],"\n"))
    gdal_translate(
      src_dataset = x[i],
      dst_dataset = copy[i], 
      ot = datatype,
      of = of,
      co = co,
      stats = TRUE,
      a_nodata = nodata,
      verbose = T,
      overwrite = TRUE
    )
    gdaladdo(
      filename = copy[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE
    )
    gdalinfo(
      datasetname = copy[i], 
      stats = TRUE,
      hist = TRUE
    )
  }
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
  fname.vrt <- paste0(strsplit(fname, ".tif"), ".vrt")
  for(i in seq(fname)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"stacking", fname[i],"\n"))
    xi <- c(x[[1]][i], x[[2]][i], x[[3]][i])
    gdalbuildvrt(
      gdalfile = xi, 
      output.vrt = fname.vrt[i],
      separate = TRUE,
      overwrite = TRUE,
      verbose = TRUE
      )
    gdal_translate(
      src_dataset = fname.vrt[i],
      dst_dataset = fname[i],
      of = "GTiff",
      ot = format,
      a_nodata = nodata,
      co = c("TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=YES"),
      overwrite = TRUE,
      verbose = TRUE
      )
    gdaladdo(
      filename = fname[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE
    )
    gdalinfo(
      datasetname = fname[i], 
      stats = TRUE,
      hist = TRUE
    )
  }
}

