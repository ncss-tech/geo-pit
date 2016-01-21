
############################################################################
### Generate list from intersection of SAPOLYGON and NED metadata layer
############################################################################
make_ned_list <- function(ned_dsn, mo_dsn, mo_layer, crsarg){
  ned_l <- list()
  ned_tiles <- readOGR(dsn = ned_dsn, layer = "ned_13arcsec_g")
  ned_tiles <- spTransform(ned_tiles, CRS(crsarg))
  for(i in seq(mo_dsn)){
    mo_pol <- readOGR(dsn = mo_dsn[i], layer = mo_layer)
    mo_pol <- spTransform(mo_pol, CRS(crsarg))
    int <- intersect(mo_pol, ned_tiles)
    ned_l[[i]] <- sort(unique(as.character(int@data$FILE_ID)))
  }
  return(ned_l = ned_l)
}


#########################################################################
### Clean ned list of duplicates
#########################################################################
remove_dups <- function(files, file_names){
  zips_idx <- grep(".zip", files)
  zip_files <- files[zips_idx]
  zip_names <- unlist(strsplit(zip_files, ".zip"))
  dup <- match(file_names, zip_names)
  missing <- file_names[is.na(dup)]  
}


########################################################################
### Download img NED tiles
# For some reason this only works from the R console not Rstudio
########################################################################
batch_download <- function(url, destfile){
    for(i in seq(url)){
    download.file(url = url[i], destfile = destfile[i], mode = "wb")
  }
}

##########################################
### unzip nedlist
##########################################
batch_unzip <- function(zipfile, files, dir_out){
  for(i in seq(zipfile)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "unzipping", zipfile[i], "\n"))
    unzip(zipfile = zipfile[i], files = files[i], exdir = dir_out)
  }
}


#################################################
### Subset NLCD by MLRA office using gdalUtils:gdalwarp
#################################################
# Beware, using the cutline option shifts the raster, this can rectified using the -tap option, and shifting the output using raster shift() or gdal_translate -prjwin
# In order to correct for the half cell shift due to the GTIFF library its necessary to set --config GTIFF_POINT_GEO_IGNORE = TRUE preceding the other gdwarp arguements
batch_subset <- function(original, subsets, mo_dsn, mo_layer, crsarg){
  original_temp <- paste0(unlist(strsplit(subsets, ".tif")), "_temp.tif")
  for(i in seq(subsets)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "WARPING", subsets[i], "\n"))
    te <- c(bbox(spTransform(readOGR(dsn = mo_dsn[i], layer = mo_layer[i]), CRS(crsarg))))
    gdalwarp(
      srcfile = original,
      dstfile = original_temp[i],
      of = "GTiff",
      r = "near",
      te = te,
      tr = c(30,30),
      tap = T,
      ot = "Byte",
      co = c("TILED=YES", "COMPRESS=DEFLATE"),
      overwrite = T,
      verbose = T)
    
    bb <- c(bbox(raster(original_temp[i])))
    rat <- raster(original)@data@attributes
    foreign::write.dbf(rat, paste0(strsplit(subsets[i], ".tif"), ".tif.vat.dbf"))
    
    gdal_translate(
      src_dataset = original_temp[i],
      dst_dataset = subsets[i],
      a_ullr = c(bb[1]+15, bb[4]-15, bb[3]+15, bb[2]-15),
      a_srs = crsarg,
      ot = "Byte",
      co = c("TILED=YES", "COMPRESS=DEFLATE"),
      a_nodata = 0,
      overwrite = TRUE,
      verbose = TRUE
    )
    file.remove(original_temp[i])
    gdaladdo(
      filename = subsets[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE
    )
    gdalinfo(
      datasetname = subsets[i], 
      stats = TRUE,
      hist = TRUE
    )
  }
}



#################################################
### Mosaic rasters using gdalUtils:mosaic_rasters
#################################################
batch_mosaic <- function(mosaiclist, dstpath, datatype, co, nodata){
  for(i in seq(mosaiclist)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "mosaicing", dstpath[i], "\n"))
    mosaic_rasters(
      gdalfile = unlist(mosaiclist[i]),
      dst_dataset = dstpath[i],
      of = "GTiff",
      ot = datatype,
      co = co,
      vrtnodata = nodata,
      overwrite = TRUE,
      verbose = T
    )
    gdaladdo(
      filename = dstpath[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE
    )
    gdalinfo(
      datasetname = dstpath[i],
      stats = TRUE
    )
  }
}

mosaicNlcdList <- function(mosaiclist, dstpath){
  for(i in seq(mosaiclist)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "mosaicing", dstpath[i], "\n"))
    mosaic_rasters(
      gdalfile = mosaiclist[[i]],
      dst_dataset = dstpath[i],
      a_srs = "EPSG:5070",
      of = "GTiff",
      ot = "Byte",
      co = c("TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=YES"),
      a_nodata = -99999,
      overwrite = TRUE,
      verbose = T
    )
  }
}
################################################################
### Warp 9d to 10m using -r bilinear
################################################################
### Notes: ArcGIS doesn't seem to recognize GDAL formatted files. To accommadate this the creation profile options are set to the vanilla GeoTIFF. Also the output projection is spelled out in it's entirey (e.g. "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs +ellps=GRS80 +towgs84=0,0,0") 
batch_warp <- function(inlist, warplist, reflist, resto, r, s_srs, t_srs, datatype, nodata, co){    
  for(i in seq(inlist)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"WARPING", inlist[i],"\n"))
 te <- c(bbox(raster(reflist[i])))
  gdalwarp(
    srcfile = inlist[i],
    dstfile = warplist[i],
    s_srs = s_srs,
    t_srs = t_srs,
    te = te,
    r = r,
    tr = c(resto,resto),
    of = "GTiff",
    ot = datatype,
    co = co,
    dstnodata = nodata,
    overwrite = T,
    verbose = T
  )
  gdaladdo(
    filename = warplist[i],
    r = "nearest",
    levels = c(2, 4, 8, 16),
    clean = TRUE,
    ro = TRUE
  )
  gdalinfo(
    datasetname = warplist[i],
    stats = TRUE
  )
  }
}


#################################################################
### Warp 10m to 30m using -r average
#################################################################
batch_average <- function(demlist, resfrom, resto){
  res <- as.numeric(unlist(strsplit(resto, "m")))
  demwarp <- unlist(lapply(strsplit(demlist, resfrom), paste, collapse = resto, sep = ""))
  
  for(i in seq(demlist)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"warping", demlist[i],"\n"))
    gdalwarp(
      srcfile = demlist[i],
      dstfile = demwarp[i],
      s_srs = crsarg,
      t_srs = crsarg,
      r = "average",
      tr = c(res,res),
      of = "GTiff",
      ot = "Float32",
      dstnodata = -99999,
      overwrite = T,
      verbose = T
    )
    gdaladdo(
      filename = demwarp[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE
    )
      gdalinfo(
      datasetname = demwarp[i],
      stats = TRUE
    )
  }
}


#################################################################
### Calculating derivatives
#################################################################
# Notes the compression seems to be a problem calculating derivatives, when the file size is greater than say a gigabyte
batch_DEM <- function(demlist, co){
  hillshade <- paste0(unlist(strsplit(demlist, ".tif")), "_hillshade.tif")
  slope <- paste0(unlist(strsplit(demlist, ".tif")), "_slope.tif")
  slope_temp <- paste0(unlist(strsplit(demlist, ".tif")), "_slope_temp.tif")
  aspect <- paste0(unlist(strsplit(demlist, ".tif")), "_aspect.tif")
  aspect_temp <- paste0(unlist(strsplit(demlist, ".tif")), "_aspect_temp.tif")
  
  for(i in seq(demlist)){
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating hillshade for", demlist[i],"\n"))
    gdaldem(
      mode = "hillshade",
      input_dem = demlist[i],
      output = hillshade[i],
      of = "GTiff",
      co = co,
      verbose = T
      )    
    gdaladdo(
      filename = hillshade[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE,
      )    
    gdalinfo(
      datasetname = hillshade[i],
      stats = TRUE,
      )
    
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating slope for", demlist[i],"\n"))
    gdaldem(
      mode = "slope",
      input_dem = demlist[i],
      output = slope_temp[i],
      of = "GTiff",
      p = TRUE,
      verbose = T
      )
    gdal_translate(
      src_dataset = slope_temp[i],
      dst_dataset = slope[i],
      ot = "Byte",
      co = c("TILED=YES", "COMPRESS=DEFLATE"),
      overwrite = TRUE,
      verbose = TRUE
    )
    file.remove(slope_temp[i])
    
    gdaladdo(
      filename = slope[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE,
    )    
    gdalinfo(
      datasetname = slope[i],
      stats = TRUE,
      hist = TRUE,
    )
    cat(paste(format(Sys.time(), "%Y-%m-%d %H:%M:%S"),"calculating aspect for", demlist[i],"\n"))
    file.remove(aspect_temp[i])
    gdaldem(
      mode = "aspect",
      input_dem = demlist[i],
      output = aspect_temp[i],
      of = "GTiff",
      verbose = T
    )
    gdal_translate(
      src_dataset = aspect_temp[i],
      dst_dataset = aspect[i],
      ot = "Int16",
      co = c("TILED=YES", "COMPRESS=DEFLATE"),
      overwrite = TRUE,
      verbose = TRUE
    )
    file.remove(aspect_temp[i])
    
    gdaladdo(
      filename = aspect[i],
      r = "nearest",
      levels = c(2, 4, 8, 16),
      clean = TRUE,
      ro = TRUE,
    )    
    gdalinfo(
      datasetname = aspect[i],
      stats = TRUE,
      hist = TRUE,
    )
  }
}
