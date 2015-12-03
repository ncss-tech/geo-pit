options(stringsAsFactors = FALSE)

library(RCurl)

ned_url <- getURL("ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/NED/13/IMG/")
ned_ftp <- strsplit(ned_url, "\r\n")[[1]]
ned_ftp <- strsplit(ned_ftp, " ")

trim <- function(x) {
  p <- nchar(x) != 0
  p2 <- x[p]
return(p2)
}

ned_ftp <- data.frame(do.call(rbind, lapply(ned_ftp, trim)))[5:9]
names(ned_ftp) <- c("size", "month", "day", "year", "file")
ned_ftp <- ned_ftp[grep(".zip", ned_ftp$file), ]
write.csv(ned_ftp, paste0("M:/geodata/elevation/ned/ned_update", Sys.Date(), ".csv"))

ned <- read.csv("M:/geodata/elevation/ned/ned_update_2015_10_28.csv", stringsAsFactors = FALSE)
ned <- transform(ned, date = as.Date(date, format = "%m/%d/%Y"))
idx <- as.Date("2014-09-24", format = "%Y-%m-%d")
ned <- ned[ned$date > idx, ]
ned <- transform(ned, files2 = data.frame(do.call(rbind, strsplit(file, "USGS_NED_13_")))[, 2])
ned <- transform(ned, files2 = sapply(ned$files2, function(x) sub("_IMG", "", x)))
ned <- transform(ned, files3 = unlist(strsplit(files2, ".zip")))

ned_files <- list.files("M:/geodata/elevation/ned/tiles/img")

ned_sub <- ned[ned$files2 %in% ned_files, ]

url <- paste0("ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/NED/13/IMG/", ned_sub$file)
destfile <- paste0("M:/geodata/elevation/ned/tiles/", ned_sub$file)

batch_download <- function(url, destfile){
  for(i in seq(url)){
    download.file(url = url[i], destfile = destfile[i])
  }
}

batch_download(url, destfile)

lapply(mo_ned, function(x) x %in% ned_sub$files3)
