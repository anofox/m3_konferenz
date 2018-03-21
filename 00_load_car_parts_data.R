library(expsmooth)
library(zoo)
library(tidyverse)

m <- as.data.frame(carparts)
colnames(m) <- paste0("series_", 1:ncol(m))
m$dates <- as.Date(as.yearmon(time(carparts)))
m %>% 
  gather("series", "parts", -dates) -> m
write_csv(m, "prepared_data/car_parts/car_parts.csv", col_names = T)
