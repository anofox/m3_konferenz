library(tidyverse)
library(data.table)
library(foreach)
library(iterators)
library(viridis)

source("r_code/data_preparation.R")

# 1.0 Prepare London Smart Meter Data ----
path <- "data/smart-meters-in-london/halfhourly_dataset/"
dtData <- load_data_bulk(path)
fst::write_fst(dtData, path = "prepared_data/london_smart_meter/smart_meters_london.fst")
write_csv(dtData, "prepared_data/london_smart_meter/smart_meters_london.csv")


# 2.0 Data Cleaning ----
fst::read_fst("prepared_data/london_smart_meter/smart_meters_london.fst") %>% 
  as.data.table() -> dtData

# Analyse length
dtLength <- dtData[, .N, by = id]
setkey(dtLength, N)
dtLength
summary(dtLength)
p <- AnoFox::heatmapTS(dtData, columnSort = "date_time", columnY = "energy", columnID = "id", doNormalize = T)
ggsave("images/smart_meter_heatmap.png", p, width = 12, height = 8)
rm(p)

# filter series not ending in January 2014
maxDate <- max(dtData$date_time)
dtData[, tmp := max(date_time), by = "id"]
dtData <- dtData[tmp == maxDate]

p <- AnoFox::heatmapTS(dtData, columnSort = "date_time", columnY = "energy", columnID = "id", doNormalize = T)
ggsave("images/smart_meter_heatmap_max_date.png", p, width = 12, height = 8)
rm(p)

fst::write_fst(dtData, path = "prepared_data/london_smart_meter/smart_meters_london_cleaned.fst")
write_csv(dtData, "prepared_data/london_smart_meter/smart_meters_london_cleaned.csv")


# filter series, s.t. they have the same start point
dtData[, tmp := min(date_time), by = "id"]
maxDate <- max(dtData$tmp)
dtData <- dtData[date_time >= maxDate]
dtData$tmp <- NULL

p <- AnoFox::heatmapTS(dtData, columnSort = "date_time", columnY = "energy", columnID = "id", doNormalize = T)
ggsave("images/smart_meter_heatmap_max_date_same_start.png", p, width = 12, height = 8)
rm(p)
dtData[, minDate := NULL]
fst::write_fst(dtData, path = "prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start.fst")
write_csv(dtData, "prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start.csv")

dtData <- read_csv("prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start.csv") %>% 
  as.data.table()
dtData %>% 
  dplyr::filter(id == "MAC000002") %>% 
  write_csv("prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start_example.csv")


# 3.0 Add Weather Data & drop short series ----
weatherData <- readr::read_csv("data/smart-meters-in-london/weather_hourly_darksky.csv")
setnames(weatherData, "time", "date_time")
weatherData <- as.data.table(weatherData)
weatherData %>% 
  dplyr::select(-summary, -icon, -precipType) -> weatherData
setkey(dtData, date_time)
setkey(weatherData, date_time)
dtData <- weatherData[dtData]
setkey(dtData, id, date_time)
fst::write_fst(dtData, path = "prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start_with_weather.fst")
write_csv(dtData, "prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start_with_weather.csv")
dtData <- read_csv("prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start.csv")
dtData %>% 
  dplyr::filter(id == "MAC000002") %>% 
  write_csv("prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start_with_weather_example.csv")


# Add holiday ? ----
holiday <- readr::read_csv("data/smart-meters-in-london/uk_bank_holidays.csv")

