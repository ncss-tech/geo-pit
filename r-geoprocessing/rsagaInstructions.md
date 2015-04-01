<p>This document displays some R batch functions for generating DEM derivatives using the RSAGA R package. It is assumes the reader has already compiled a series of DEM following the nedInstrucitons document.</p>

<p>SAGA is an open-source GIS that was originally developed in 1996 as a terrain analysis toolbox, known as DiGem. Since then it has become a fully fledged GIS, with additional modules for vector geoprocessing, image analysis, and geostatistics. While not as well documented at GRASS or ArcGIS it offers an intuitive interface, and includes a range algorithms not found elsewhere. Through the use of the RSAGA package, SAGA modules can be called from R, and workflows developed. Unlike other GIS, SAGA utilizes significant RAM instead of using file caching. This makes SAGA fast, but it can also overwhelm a computer if to many large rasters are loaded. However I&#39;ve noticed when using a solid state drive (SSD) I can process rasters than exceded my 16GB of RAM for certain SAGA modules that only use small local neighorhoods. </p>

<p>To begin, the necessary libaries must be loaded, as well as the custom batch functions.</p>

<pre><code class="r, eval=FALSE">library(gdalUtils)
library(RSAGA)

source(&quot;C:/Users/Stephen/Documents/Github/geoprocessing/gdalUtilsFunctions.R&quot;)
source(&quot;C:/Users/Stephen/Documents/Github/geoprocessing/rsagaFunctions.R&quot;)
</code></pre>

<p>Next the proper GDAL and RSAGA path has to be set. The first GDAL location is the default path on my work computer, the second my personal computer. If this isn&#39;t set gdalUtils will do a brute force search of your computer, which usually finds GDAL 1.7 instead of the GDAL 10.1. The new version has additional features, which many these batch functions use.</p>

<pre><code class="r, eval=FALSE">gdal_setInstallation(search_path=&quot;C:/ProgramData/QGIS/QGISDufour/bin&quot;, rescan=T)
gdal_setInstallation(search_path=&quot;C:/OSGeo4W64/bin&quot;, rescan=T)
myenv &lt;- rsaga.env(path=&quot;C:/Program Files (x86)/SAGA-GIS&quot;)
</code></pre>

<p>Next numerous parameters need to be set which get used later by many of the functions or commands. Modify these file paths and lists as necessary. For example, I organized my files by &ldquo;C:/geodata/project_data/11ATL&rdquo;&ldquo;, so 11 will have to replace by 10 or 2 for your respective Regions.</p>

<pre><code class="r, eval=FALSE">setwd(&quot;E:/geodata/project_data&quot;)
pd.p &lt;- &quot;D:/geodata/project_data/&quot;
office.l &lt;- c(&quot;8VIC&quot;)
sdat.p &lt;- paste(pd.p, office.l, &quot;/sdat/&quot;, sep=&quot;&quot;)
state &lt;- c(&quot;NV&quot;, &quot;CA&quot;)
nhdgdb &lt;- paste(&quot;D:/geodata/hydrography/NHDH_&quot;, state, &quot;.gdb&quot;, sep=&quot;&quot;)

# Generater raster names
dem10 &lt;- paste(sdat.p, &quot;ned10m_&quot;, office.l, &quot;.sgrd&quot;, sep=&quot;&quot;)
dem30 &lt;- paste(sdat.p, &quot;ned30m_&quot;, office.l, &quot;.sgrd&quot;, sep=&quot;&quot;)
radiusD &lt;- 2
radiusV &lt;- round(1000/30/2-1, 0)

res10 &lt;- paste(strsplit(dem10, &quot;.sgrd&quot;), sep=&quot;&quot;)
res30 &lt;- paste(strsplit(dem30, &quot;.sgrd&quot;), sep=&quot;&quot;)
g10 &lt;- list(
  slopeR=paste(res10, &quot;_slopeR&quot;, 1+2*radiusD, sep=&quot;&quot;),
  slope=paste(res10, &quot;_slope&quot;, 1+2*radiusD, sep=&quot;&quot;),
  slopeD=paste(res10, &quot;_slopeD&quot;, 1+2*radiusD, sep=&quot;&quot;),
  aspect=paste(res10, &quot;_aspect&quot;, 1+2*radiusD, sep=&quot;&quot;),
  cupro=paste(res10, &quot;_cupro&quot;, 1+2*radiusD, sep=&quot;&quot;),
  cucon=paste(res10, &quot;_cucon&quot;, 1+2*radiusD, sep=&quot;&quot;),
  cutan=paste(res10, &quot;_cutan&quot;, 1+2*radiusD, sep=&quot;&quot;),
  cumax=paste(res10, &quot;_cumax&quot;, 1+2*radiusD, sep=&quot;&quot;),
  cumin=paste(res10, &quot;_cumin&quot;, 1+2*radiusD, sep=&quot;&quot;)
  )
g30 &lt;- list(
  elev=paste(res30, &quot;_elev&quot;, 1+2*radiusD, sep=&quot;&quot;),
  slope=paste(res30, &quot;_slope&quot;, 1+2*radiusD, sep=&quot;&quot;),
  slopeR=paste(res30, &quot;_slopeR&quot;, 1+2*radiusD, sep=&quot;&quot;),
  slopeD=paste(res30, &quot;_sloped&quot;, 1+2*radiusD, sep=&quot;&quot;),
  aspect=paste(res30, &quot;_aspect&quot;, 1+2*radiusD, sep=&quot;&quot;),
  valleys=paste(res30, &quot;_mvalleys&quot;, sep=&quot;&quot;),
  summits=paste(res30, &quot;_summits&quot;, sep=&quot;&quot;),
  carea=paste(res30, &quot;_carea&quot;, sep=&quot;&quot;),
  cheight=paste(res30, &quot;_cheight&quot;, sep=&quot;&quot;),
  wetness=paste(res30, &quot;_wetness&quot;, sep=&quot;&quot;),
  strahler=paste(res30, &quot;_strahler&quot;, sep=&quot;&quot;),
  z2stream=paste(res30, &quot;_z2stream&quot;, sep=&quot;&quot;)
  )
</code></pre>

<pre><code class="r, eval=FALSE"># Convert GTiff to SAGA
dem10.tif &lt;- paste(pd.p, office.l, &quot;/ned10m_&quot;, office.l, &quot;.tif&quot;, sep=&quot;&quot;)
dem30.tif &lt;- paste(pd.p, office.l, &quot;/ned30m_&quot;, office.l, &quot;.tif&quot;, sep=&quot;&quot;)
dem10.sdat &lt;- paste(strsplit(dem10, &quot;.sgrd&quot;), &quot;.sdat&quot;, sep=&quot;&quot;)
dem30.sdat &lt;- paste(strsplit(dem30, &quot;.sgrd&quot;), &quot;.sdat&quot;, sep=&quot;&quot;)

gdal_GTiff2SAGA(dem10.tif, dem10.sdat)
gdal_GTiff2SAGA(dem30.tif, dem30.sdat)
gdal_GTiff2SAGA(&quot;E:/geodata/project_data/11REGION/ned30m_R11.tif&quot;,
                &quot;E:/geodata/project_data/11REGION/sdat/ned30m_R11.sdat&quot;)
</code></pre>

<pre><code class="r, eval=FALSE"># Calculate local derivatives for 10-meter DEM
attach(lapply(g10, function(x) paste(x, &quot;.sgrd&quot;, sep=&quot;&quot;)))
rsaga.d1(dem10, 2)
rsaga.d2(dem10, 2)
rsaga.d3(dem10, 2)
# Converts to radians then percent, 57.29578=180/pi, degrees=radians*180/pi
rsaga.grid.calculus(slopeD, slopeD, slope, &quot;tan(a*(1/57.29578))*100&quot;)
# Rescales curvatures so they can be exported as UInt16 to save file size
rsaga.grid.calculus(cupro, cupro, cupro, &quot;10000*a&quot;)
rsaga.grid.calculus(cucon, cucon, cucon, &quot;-10000*a&quot;)
rsaga.grid.calculus(cumin, cumin, cumin, &quot;10000*a&quot;)
rsaga.grid.calculus(cumax, cumax, cumax, &quot;10000*a&quot;)
rsaga.grid.calculus(cucon, slopeD, cutan, &quot;a*sin(b/57.29578)&quot;)


# Calculate regional derivatives for 30-meter DEM
attach(lapply(g30, function(x) paste(x, &quot;.sgrd&quot;, sep=&quot;&quot;)))
rsaga.d0(dem30, 2)
rsaga.d1(dem30, 2)
rsaga.grid.calculus(slopeD, slopeD, slope, &quot;tan(a*(1/57.29578))*100&quot;)
rsaga.grid.calculus(slopeD, slopeD, slopeR, &quot;a*(1/57.29578)&quot;)
rsaga.mrvbf(dem30, valleys, summits)

# apply mask manually before
elev.sdat &lt;- paste(strsplit(elev, &quot;.sgrd&quot;), &quot;.sdat&quot;, sep=&quot;&quot;)
mosaicList(list(elev.sdat), &quot;E:/geodata/project_data/REGION11/ned30m_R11_elev5.tif&quot;)

gdal_translate(
  src_dataset=&quot;E:/geodata/project_data/REGION11/ned30m_R11_elev5.tif&quot;,
  dst_dataset=&quot;E:/geodata/project_data/REGION11/ned30m_R11_elev5_masked.tif&quot;,
  overwrite=TRUE,
  verbose=TRUE
)


nhdshp &lt;- paste(strsplit(nhdgdb, &quot;.gdb&quot;), &quot;_wb.shp&quot;, sep=&quot;&quot;)

for(i in seq(nhdgdb)){
  ogr2ogr(
    src_datasource_name=nhdgdb[i],
    dst_datasource_name=nhdshp[i],
    layer=&quot;NHDWaterbody&quot;,
    t_srs=&quot;EPSG:5070&quot;,
    overwrite=TRUE,
    verbose=TRUE,
    progress=TRUE)
}

# Seems to take exceptionally long for the States touching the Great Lakes, particularly MI. Best to run these States separately from OSGeo4W Shell to monitor their progress or do manually in SAGA.
for(i in seq(nhdshp)){
  cat(paste(format(Sys.time(), &quot;%Y-%m-%d %H:%M:%S&quot;), &quot;burning&quot;, nhdshp[i], &quot;\n&quot;))
  gdal_rasterize(
    src_datasource=paste(&quot;E:/geodata/hydrography&quot;, sep=&quot;&quot;),
    dst_filename=&quot;E:/geodata/project_data/REGION11/ned30m_R11_elev5_masked.tif&quot;,
    l=paste(&quot;NHDH_&quot;, state[i], &quot;_wb&quot;, sep=&quot;&quot;),
    where=&quot;AreaSqKm &gt; 0.04047&quot;,
    b=1,
    burn=-99999,
    verbose=TRUE
  ) 
}


dem.sdat&lt;- paste(strsplit(dem30, &quot;.sgrd&quot;), &quot;_elev5_masked.sgrd&quot;, sep=&quot;&quot;)
batchSubsetSAGA(&quot;E:/geodata/project_data/REGION11/ned30m_R11_elev5_masked.tif&quot;, dem.sdat, nlcdpath)

dem.l&lt;- paste(strsplit(dem30, &quot;.sgrd&quot;), &quot;_elev5_masked.sgrd&quot;, sep=&quot;&quot;)
rsaga.fill(dem.l)
dem.l&lt;- paste(strsplit(dem30, &quot;.sgrd&quot;), &quot;_elev5_masked_filled.sgrd&quot;, sep=&quot;&quot;)
rsaga.ca(dem.l)
rsaga.twi(slopeR, carea)
rsaga.strahler(dem.l,4)
rsaga.reclassify(strahler, -3, -1)

strahler.rc&lt;- paste(strsplit(dem30, &quot;.sgrd&quot;), &quot;_strahler_rc0.sgrd&quot;, sep=&quot;&quot;)
rsaga.ofd(dem.l, 1)

# Write SAGA to GTiff
attach(lapply(g10, function(x) paste(x, &quot;.sdat&quot;, sep=&quot;&quot;)))
int16.sdat &lt;- c(slope)
int16.tif &lt;- unlist(lapply(strsplit(int16.sdat, &quot;/sdat&quot;), paste, collapse=&quot;&quot;, sep=&quot;&quot;))
int16.tif &lt;- paste(strsplit(int16.tif, &quot;.sdat&quot;), &quot;.tif&quot;, sep=&quot;&quot;)
gdal_SAGA2GTiff(int16.sdat, int16.tif, &quot;Int16&quot;, -32768)

slopeshape &lt;- paste(pd.p, office.l, &quot;/ned10m_11&quot;, office.l, &quot;_slopeshape.tif&quot;, sep=&quot;&quot;)
test &lt;- list(cupro, cutan, slope)
gdal.stack(test, slopeshape, &quot;Int16&quot;, -32768)

attach(lapply(g30, function(x) paste(x, &quot;.sdat&quot;, sep=&quot;&quot;)))
flt.sdat &lt;- c(z2stream, valleys, wetness)
flt.tif &lt;- unlist(lapply(strsplit(flt.sdat, &quot;/sdat&quot;), paste, collapse=&quot;&quot;, sep=&quot;&quot;))
flt.tif &lt;- paste(strsplit(flt.tif, &quot;.sdat&quot;), &quot;.tif&quot;, sep=&quot;&quot;)
gdal_SAGA2GTiff(flt.sdat, flt.tif, &quot;Float32&quot;, -99999)

office.l &lt;- office.l[11]
nlcd.p &lt;- nlcd.p[11]
t.l &lt;- c(&quot;z2stream&quot;, &quot;mvalleys&quot;)
n30.l &lt;- paste0(pd.p, office.l, &quot;/sdat/ned&quot;, 30, &quot;m_&quot;, office.l, &quot;_&quot;, t.l, &quot;.sdat&quot;)
n10.l &lt;- paste0(pd.p, office.l, &quot;/ned&quot;, 10, &quot;m_&quot;, office.l, &quot;_&quot;, t.l, &quot;.tif&quot;)
co &lt;- c(&quot;TILED=YES&quot;, &quot;COMPRESS=DEFLATE&quot;, &quot;BIGTIFF=YES&quot;)
batchWarp(n30.l, n10.l, rep(nlcd.p, 2), 10, &quot;cubicspline&quot;, crsarg, crsarg, &quot;Float32&quot;, &quot;-32768&quot;, co)

mosaicList(list(slope), &quot;E:/geodata/project_data/11REGION/ned10m_11R_slope5.tif&quot;, &quot;Int16&quot;, c(&quot;COMPRESS=DEFLATE&quot;, &quot;TILED=YES&quot;, &quot;BIGTIFF=YES&quot;), -32768)

</code></pre>
