
library(foreign)
library(data.table)

Survey = FALSE #if TRUE survey files will be processed otherwise, DaySim outputs - LODES or ESD
LODES = FALSE
ESD = TRUE

filter_type = "trip" #hh or trip. if hh - households in/outside bkr will filtered. if trip - households with trips in/outside bkr will be filtered.

if(Survey){
  #survey
  wd <- 'D:/2018baseyear/BKR0V1-02/daysim_summaries/bkrcast_all/data'
  file.hhs <- 'Household_bkr_new.dat'
  file.persons <- 'Person_bkr_new_skim.dat'
  file.person_day <- 'PersonDay_bkr.dat'
  file.tours <- 'Tour_bkr_new_skim.dat'
  file.trips <- 'Trip_bkr_new_skim.dat'
  file.delim = ' '
  file.ext_inbkr = '_inbkr.dat'
  file.ext_outbkr = '_outbkr.dat'

} else if (LODES) {
  #bkrcast
  wd <- 'E:/Projects/Clients/bkr/model/bkrcast_tod_new_distbkr/outputs'
  
  #calibration
  #wd <- 'E:/Projects/Clients/bkr/tasks/calibration/outputs'
  file.hhs <- '_household.tsv'
  file.persons <- '_person.tsv' 
  file.person_day <- '_person_day.tsv'
  file.tours <- '_tour.tsv'
  file.trips <- '_trip.tsv'
  file.delim = '\t'
  file.ext_inbkr = '_inbkr.tsv'
  file.ext_outbkr = '_outbkr.tsv'
  
} else if (ESD) {
  #daysim - esd data
  wd <- 'D:/2018baseyear/BKR0V1-02/outputs'
  file.hhs <- '_household.tsv'
  file.persons <- '_person.tsv' 
  file.person_day <- '_person_day.tsv'
  file.tours <- '_tour.tsv'
  file.trips <- '_trip.tsv'
  file.delim = '\t'
  file.ext_inbkr = '_inbkr.tsv'
  file.ext_outbkr = '_outbkr.tsv'
}

file.correspondence <- 'D:/2018baseyear/BKR0V1-02/daysim_summaries/bkrcast_all/data/TAZ_District_CrossWalk.csv'

setwd(wd)
print("reading inputs ...")
hhs <- read.csv(file.hhs, sep = file.delim)
persons <- read.csv(file.persons, sep = file.delim)
person_day <- read.csv(file.person_day, sep = file.delim)
tours <- read.csv(file.tours, sep = file.delim)
trips <- read.csv(file.trips, sep = file.delim)
taz_corr <- read.csv(file.correspondence)

if (filter_type == "trip") {
  print("filter is trip")
  
  ##trips
  print("filter trips ...")
  columns <- colnames(trips)
  trips_bkr <- merge(trips, taz_corr, by.x = 'otaz', by.y = 'zone_id')
  names(trips_bkr)[names(trips_bkr)=='district'] <- 'o_district'
  trips_bkr <- merge(trips_bkr, taz_corr, by.x = 'dtaz', by.y = 'zone_id')
  names(trips_bkr)[names(trips_bkr)=='district'] <- 'd_district'
  
  #outside BKR
  trips_bkr_new <- trips_bkr[trips_bkr$o_district!='BKR' & trips_bkr$d_district!='BKR',]
  temp <- trips_bkr_new[,columns]
  write.table(temp, paste(unlist(strsplit(file.trips, "[.]"))[1], file.ext_outbkr, sep=""), quote=FALSE,
              sep = file.delim, row.names = FALSE)
  
  #within BKR - keep this as last as hhs will be identified using trips_bkr_new fromwithin bkr
  trips_bkr_new <- trips_bkr[trips_bkr$o_district=='BKR' | trips_bkr$d_district=='BKR',]
  temp <- trips_bkr_new[,columns]
  write.table(temp, paste(unlist(strsplit(file.trips, "[.]"))[1], file.ext_inbkr, sep=""), quote=FALSE,
              sep = file.delim, row.names = FALSE)
  
  #households
  hhno <- unique(trips_bkr_new$hhno)
  hhs_unique <- as.data.frame(hhno)
  hhs_unique$flag <- 1
  
} else {
  print("filter is hhs")
  
  #households
  columns <- colnames(hhs)
  hhs_bkr <- merge(hhs, taz_corr, by.x = 'hhtaz', by.y = 'zone_id')
  hhs_bkr_new  <- hhs_bkr[hhs_bkr$district == 'BKR',]
  hhno <- unique(hhs_bkr_new$hhno)
  hhs_unique <- as.data.frame(hhno)
  hhs_unique$flag <- 1
 
  ##trips
  print("filter trips ...")
  columns <- colnames(trips)
  trips_bkr <- merge(trips, hhs_unique, by = "hhno", all.x = TRUE)
  
  #within BKR
  trips_bkr_new <- trips_bkr[!is.na(trips_bkr$flag),]
  temp <- trips_bkr_new[,columns]
  write.table(temp, paste(unlist(strsplit(file.trips, "[.]"))[1], file.ext_inbkr, sep=""), quote=FALSE,
              sep = file.delim, row.names = FALSE)
  
  #outside BKR
  trips_bkr_new <- trips_bkr[is.na(trips_bkr$flag),]
  temp <- trips_bkr_new[,columns]
  write.table(temp, paste(unlist(strsplit(file.trips, "[.]"))[1], file.ext_outbkr, sep=""), quote=FALSE,
              sep = file.delim, row.names = FALSE)
  
}

##tours
print("filter tours ...")
columns <- colnames(tours)
tours_bkr <- merge(tours, hhs_unique, by = "hhno", all.x = TRUE)

#within BKR
tours_bkr_new <- tours_bkr[!is.na(tours_bkr$flag),]
temp <- tours_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.tours, "[.]"))[1], file.ext_inbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)

#outside BKR
tours_bkr_new <- tours_bkr[is.na(tours_bkr$flag),]
temp <- tours_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.tours, "[.]"))[1], file.ext_outbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)


##households
print("filter households ...")
columns <- colnames(hhs)
hhs_bkr <- merge(hhs, hhs_unique, by = "hhno", all.x = TRUE)

#within BKR
hhs_bkr_new <- hhs_bkr[!is.na(hhs_bkr$flag),]
temp <- hhs_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.hhs, "[.]"))[1], file.ext_inbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)
#outside BKR
hhs_bkr_new <- hhs_bkr[is.na(hhs_bkr$flag),]
temp <- hhs_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.hhs, "[.]"))[1], file.ext_outbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)

##person
print("filter persons ...")
columns <- colnames(persons)
persons_bkr <- merge(persons, hhs_unique, by = "hhno", all.x = TRUE)

#within BKR
persons_bkr_new <- persons_bkr[!is.na(persons_bkr$flag),]
temp <- persons_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.persons, "[.]"))[1], file.ext_inbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)
#outside BKR
persons_bkr_new <- persons_bkr[is.na(persons_bkr$flag),]
temp <- persons_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.persons, "[.]"))[1], file.ext_outbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)


##person_day
print("filter person days ...")
columns <- colnames(person_day)
person_day_bkr <- merge(person_day, hhs_unique, by = "hhno", all.x = TRUE)

#within BKR
person_day_bkr_new <- person_day_bkr[!is.na(person_day_bkr$flag),]
temp <- person_day_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.person_day, "[.]"))[1], file.ext_inbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)
#outside BKR
person_day_bkr_new <- person_day_bkr[is.na(person_day_bkr$flag),]
temp <- person_day_bkr_new[,columns]
write.table(temp, paste(unlist(strsplit(file.person_day, "[.]"))[1], file.ext_outbkr, sep=""), quote=FALSE,
            sep = file.delim, row.names = FALSE)