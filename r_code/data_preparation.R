load_data_file <- function(path, file) {
  readr::read_csv(file.path(path, file), col_names = c("id", "date_time", "energy"), skip = 1, col_types = c("cTn")) %>% 
    data.table::as.data.table() -> dtData
  data.table::setkeyv(dtData, c("id", "date_time"))
  dtData[, hour := lubridate::hour(date_time)]
  dtData[, date := as.Date(date_time)]
  
  # aggregate to hourly data
  dtData <- dtData[, .(energy = sum(energy)), by = c("id", "date", "hour")]
  
  # drop non-full first and last days
  dtData[, `:=`(n = .N, date_numeric = as.numeric(date)), by = c("id", "date")]
  dtData[, date_numeric := date_numeric - min(date_numeric), by = "id"]
  dtData <- dtData[, drop := date_numeric == 0 & n < 24][drop == F]
  dtData[, date_numeric := date_numeric - max(date_numeric), by = "id"]
  dtData <- dtData[, drop := date_numeric == 0 & n < 24][drop == F]
  dtData[, `:=`(date_numeric = NULL, drop = NULL, n = NULL)]
  
  # impute missing gaps
  dtData[, date_time := as.POSIXct(paste0(date, " ", hour, ":00"))]
  dtData[, `:=`(date = NULL, hour = NULL)]
  dtTime <- dtData[, .(minDate = min(date_time), maxDate = max(date_time)), by = "id"]
  dtTime %>% 
    purrr::pmap(.f = function(id, minDate, maxDate) {
      data.table::data.table(id = id, date_time = as.POSIXct(seq(minDate, maxDate, by = 3600), origin = "1970-01-01"))
    }) %>% 
    purrr::reduce(rbind) -> dtTime
  data.table::setkeyv(dtTime, c("id", "date_time"))
  data.table::setkeyv(dtData, c("id", "date_time"))
  dtData <- dtData[dtTime]
  # drop series with more than 5% of missing values; there may be more sophisticatedways
  dtData[, `:=`(n = .N, na = sum(is.na(energy))), by = "id"]
  dtData[, percent_missing := na / n]
  dtData <- dtData[percent_missing < 0.05][,`:=`(n = NULL, na = NULL, percent_missing = NULL)]
  dtData[is.na(energy), energy := 0]
  dtData
}


load_data_bulk <- function(path) {
  AnoFox::registerLocalParallel()
  files <- dir(path)
  dtData <- foreach::foreach(file = iterators::iter(files), .export = "path", .packages = c("data.table", "readr") ,.combine = "rbind") %dopar% {
    load_data_file(path, file)
  } 
}




