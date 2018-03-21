library(tidyverse)
library(data.table)
library(foreach)
library(iterators)

source("r_functions/data_preparation.R")

# Prepare London Smart Meter Data ----
path <- "data/smart-meters-in-london/halfhourly_dataset/"
dtData <- load_data_bulk(path)
fst::write_fst(dtData, path = "prepared_data/london_smart_meter/smart_meters_london.fst")
write_csv(dtData, "prepared_data/london_smart_meter/smart_meters_london.csv")


# Add Weather Data ----
fst::read_fst("prepared_data/london_smart_meter/smart_meters_london.fst") %>% 
  as.data.table() -> dtData
weatherData <- readr::read_csv("data/smart-meters-in-london/weather_hourly_darksky.csv")
setnames(weatherData, "time", "date_time")
weatherData <- as.data.table(weatherData)
weatherData %>% 
  dplyr::select(-summary, -icon, -precipType) -> weatherData
setkey(dtData, date_time)
setkey(weatherData, date_time)
dtData <- weatherData[dtData]
setkey(dtData, id, date_time)
fst::write_fst(dtData, path = "prepared_data/london_smart_meter/smart_meters_london_with_weather.fst")
write_csv(dtData, "prepared_data/london_smart_meter/smart_meters_london_with_weather.csv")


# Add holiday ----
holiday <- readr::read_csv("data/smart-meters-in-london/uk_bank_holidays.csv")

