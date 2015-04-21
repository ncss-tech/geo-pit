library(stringr)
library(raster)
library(rgdal)
library(RSAGA)
library(gdalUtils)

setwd("C:/Users/stephen/Documents/workspace/landsat")

# Tassled Cap Components

lf <- list.files() # Subset list; lf <- lf[7:11]
tc1 <- list()
tc2 <- list()
tc3 <- list()

for(i in seq(lf)){
  tc1[[i]] <- raster(lf[i], band=1)
  tc2[[i]] <- raster(lf[i], band=2)
  tc3[[i]] <- raster(lf[i], band=3)
}

z04tc1 <- stack(tc1[1:3])
z04tc2 <- stack(tc2[1:3])
z04tc3 <- stack(tc3[1:3])
z13tc1 <- stack(tc1[4:6])
z13tc2 <- stack(tc2[4:6])
z13tc3 <- stack(tc3[4:6])

z04tc1avg <- calc(z04tc1, fun=mean)
z13tc1avg <- calc(z13tc1, fun=mean)
z04tc2avg <- calc(z04tc2, fun=mean)
z13tc2avg <- calc(z13tc2, fun=mean)
z04tc3avg <- calc(z04tc3, fun=mean)
z13tc3avg <- calc(z13tc3, fun=mean)

NAvalue(z04tc1avg) <- 0
NAvalue(z04tc2avg) <- 0
NAvalue(z04tc3avg) <- 0
NAvalue(z13tc1avg) <- 0
NAvalue(z13tc2avg) <- 0
NAvalue(z13tc3avg) <- 0

z_tc1avg <- mosaic(z13tc1avg, z04tc1avg, fun=mean)
z_tc2avg <- mosaic(z13tc2avg, z04tc2avg, fun=mean)
z_tc3avg <- mosaic(z13tc3avg, z04tc3avg, fun=mean)

writeRaster(z_tc1avg, filename="z_tc1avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_tc2avg, filename="z_tc2avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_tc3avg, filename="z_tc3avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")

dem <- raster("C:/Users/stephen/Documents/workspace/ned30m_vic8.sdat")

gdal_setInstallation(ignore.full_scan=FALSE)

gdalwarp(srcfile="z_tc1avg.tif", dstfile="landsat30m_vic8_tc1.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)

gdalwarp(srcfile="z_tc2avg.tif", dstfile="landsat30m_vic8_tc2.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)

gdalwarp(srcfile="z_tc3avg.tif", dstfile="landsat30m_vic8_tc3.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)

tc1 <- raster("landsat30m_vic8_tc1.tif")
tc2 <- raster("landsat30m_vic8_tc2.tif")
tc3 <- raster("landsat30m_vic8_tc3.tif")
image(tc1)
image(tc2)
image(tc3)
tc <- stack(tc1, tc2, tc3)
NAvalue(tc) <- 0

writeRaster(tc, filename="landsat30m_vic8_tc.tif", overwrite=T, NAflag=0, progress="text", datatype="INT1U")

NAvalue(z_tc1avg) <- 0
NAvalue(z_tc2avg) <- 0
NAvalue(z_tc3avg) <- 0

tc1_2 <- aggregate(z_tc1avg, fact=2, na.rm=F)
tc2_2 <- aggregate(z_tc2avg, fact=2, na.rm=F)
tc3_2 <- aggregate(z_tc3avg, fact=2, na.rm=F)

writeRaster(tc1_2, filename="z_tc1avg2.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(tc2_2, filename="z_tc2avg2.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(tc3_2, filename="z_tc3avg2.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")

dem <- raster("C:/Users/stephen/Documents/workspace/ned60m_vic8.sdat")

gdal_setInstallation(ignore.full_scan=FALSE)

gdalwarp(srcfile="z_tc1avg2.tif", dstfile="landsat60m_vic8_tc1.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(60,60), overwrite=T)
gdalwarp(srcfile="z_tc2avg2.tif", dstfile="landsat60m_vic8_tc2.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(60,60), overwrite=T)
gdalwarp(srcfile="z_tc3avg2.tif", dstfile="landsat60m_vic8_tc3.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(60,60), overwrite=T)

tc60m <- stack("landsat60m_vic8_tc1.tif", "landsat60m_vic8_tc2.tif", "landsat60m_vic8_tc3.tif")

NAvalue(tc60m) <- 0

writeRaster(tc, filename="landsat60m_vic8_tc.tif", format="GTiff", overwrite=T, NAflag=0, progress="text", datatype="INT1U")


# Bands

lf <- list.files() # Subset list; lf <- lf[7:11]
b1 <- list()
b2 <- list()
b3 <- list()
b4 <- list()
b5 <- list()
b7 <- list()

for(i in seq(lf)){
  b1[[i]] <- raster(lf[i], band=1)
  b2[[i]] <- raster(lf[i], band=2)
  b3[[i]] <- raster(lf[i], band=3)
  b4[[i]] <- raster(lf[i], band=4)
  b5[[i]] <- raster(lf[i], band=5)
  b7[[i]] <- raster(lf[i], band=6)
}

z4b1 <- stack(b1[1:3])
z4b2 <- stack(b2[1:3])
z4b3 <- stack(b3[1:3])
z4b4 <- stack(b4[1:3])
z4b5 <- stack(b5[1:3])
z4b7 <- stack(b7[1:3])

z13b1 <- stack(b1[4:6])
z13b2 <- stack(b2[4:6])
z13b3 <- stack(b3[4:6])
z13b4 <- stack(b4[4:6])
z13b5 <- stack(b5[4:6])
z13b7 <- stack(b7[4:6])

z4b1avg <- calc(z4b1, fun=mean)
z4b2avg <- calc(z4b2, fun=mean)
z4b3avg <- calc(z4b3, fun=mean)
z4b4avg <- calc(z4b4, fun=mean)
z4b5avg <- calc(z4b5, fun=mean)
z4b7avg <- calc(z4b7, fun=mean)

z13b1avg <- calc(z13b1, fun=mean)
z13b2avg <- calc(z13b2, fun=mean)
z13b3avg <- calc(z13b3, fun=mean)
z13b4avg <- calc(z13b4, fun=mean)
z13b5avg <- calc(z13b5, fun=mean)
z13b7avg <- calc(z13b7, fun=mean)

NAvalue(z4b1avg) <- 0
NAvalue(z4b2avg) <- 0
NAvalue(z4b3avg) <- 0
NAvalue(z4b4avg) <- 0
NAvalue(z4b5avg) <- 0
NAvalue(z4b7avg) <- 0

NAvalue(z13b1avg) <- 0
NAvalue(z13b2avg) <- 0
NAvalue(z13b3avg) <- 0
NAvalue(z13b4avg) <- 0
NAvalue(z13b5avg) <- 0
NAvalue(z13b7avg) <- 0

z_b1avg <- mosaic(z13b1avg, z4b1avg, fun=mean)
z_b2avg <- mosaic(z13b2avg, z4b2avg, fun=mean)
z_b3avg <- mosaic(z13b3avg, z4b3avg, fun=mean)
z_b4avg <- mosaic(z13b1avg, z4b4avg, fun=mean)
z_b5avg <- mosaic(z13b2avg, z4b5avg, fun=mean)
z_b7avg <- mosaic(z13b3avg, z4b7avg, fun=mean)

writeRaster(z_b1avg, filename="z_b1avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_b2avg, filename="z_b2avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_b3avg, filename="z_b3avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_b4avg, filename="z_b4avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_b5avg, filename="z_b5avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")
writeRaster(z_b7avg, filename="z_b7avg.tif", format="GTiff", overwrite=T, NAflag=-99999, progress="text", datatype="FLT4S")

dem <- raster("C:/Users/stephen/Documents/workspace/ned30m_vic8.sdat")

gdal_setInstallation(ignore.full_scan=FALSE)

gdalwarp(srcfile="z_b1avg.tif", dstfile="landsat30m_vic8_b1.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)
gdalwarp(srcfile="z_b2avg.tif", dstfile="landsat30m_vic8_b2.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)
gdalwarp(srcfile="z_b3avg.tif", dstfile="landsat30m_vic8_b3.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)
gdalwarp(srcfile="z_b4avg.tif", dstfile="landsat30m_vic8_b4.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)
gdalwarp(srcfile="z_b5avg.tif", dstfile="landsat30m_vic8_b5.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)
gdalwarp(srcfile="z_b7avg.tif", dstfile="landsat30m_vic8_b7.tif", of="GTiff", s_srs="epsg:5070", t_srs="epsg:26911", r="bilinear", dstnodata=-99999, te=c(dem@extent@xmin, dem@extent@ymin, dem@extent@xmax, dem@extent@ymax), tr=c(30,30), overwrite=T)

b1 <- raster("landsat30m_vic8_b1.tif")
b2 <- raster("landsat30m_vic8_b2.tif")
b3 <- raster("landsat30m_vic8_b3.tif")
b4 <- raster("landsat30m_vic8_b4.tif")
b5 <- raster("landsat30m_vic8_b5.tif")
b7 <- raster("landsat30m_vic8_b7.tif")
image(b1)
image(b2)
image(b3)
b <- stack(b1, b2, b3, b4, b5, b7)
writeRaster(b, filename="landsat30m_vic8_b123457.tif", overwrite=T, NAflag=-99999, progress="text", datatype="INT1U")


gdal_translate(src_dataset="z04leafoff_refl.ige.gz", dst_dataset="z04leafoff_refl.tif", of="GTiff")
gdal_translate(src_dataset="z04leafon_refl.img", dst_dataset="z04leafon_refl.tif", of="GTiff")
gdal_translate(src_dataset="z04spring_refl.img", dst_dataset="z04spring_refl.tif", of="GTiff")
