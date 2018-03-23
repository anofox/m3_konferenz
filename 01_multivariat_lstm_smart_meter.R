library(AnoFox)
library(tidyverse)
library(data.table)


# 1.0 Load Data ----
dtData <- read_csv("prepared_data/london_smart_meter/smart_meters_london_cleaned_same_start_with_weather.csv")
dtData <- as.data.table(dtData)
setkey(dtData, id, date_time)
dtData[, date_time := date_time + 3600]


# 2.0 Data Quality Checks ----
# data is prepared properly
dtData[, max_energy := max(energy), by = id]
dtData <- dtData[max_energy > 0]
dtData[, max_energy := IQR(energy), by = id]
dtData <- dtData[max_energy > 0]
dtData[, max_energy := NULL]

# 3.0 Set Parameters ----
frequency <- 24L
nIn <- 1L
nOut <- 1L
step <- 1L
nTrain <- 100L
lstmParameters <- AnoFox::keras_default_lstm_parameters(columnID = "id", 
                                                        # the date variable is used for correctly sorted data
                                                        columnSort = "date_time", 
                                                        # the variable we want to predict
                                                        columnValue = "energy", 
                                                        # todays energy consumption is used for predicting tomorrows energy consumption
                                                        columnFeatures = c("energy", "temperature", "pressure", "windSpeed", "humidity", "windBearing", "visibility", "apparentTemperature", "dewPoint"), 
                                                        # energy is generally normalized, therefore the variable energy is not listed here
                                                        columnsNormalize = c("temperature", "pressure", "windSpeed", "humidity", "windBearing", "visibility", "apparentTemperature", "dewPoint"), 
                                                        # we have 121 days. 100 days are use for training, 10% (default) for validation, and 21 days for testing the model
                                                        nTrain = 100L, 
                                                        # we have hourly data 
                                                        frequency = 24L, 
                                                        # days for looking back and foreward
                                                        nIn = 1L, 
                                                        nOut = 1L, 
                                                        step = 1L, 
                                                        # epochs
                                                        nEpochs = 10,
                                                        batchSize = 512)

# 4.0 Train Model ----
AnoFox::registerLocalParallel()
dtData %>%
  AnoFox::keras_multi_series_experiment(dataParameters = lstmParameters$dataParameters,
                                        lstmParameters = lstmParameters$lstmParameters) -> lstmExperimentMulti
doParallel::stopImplicitCluster()


# 5.0 Evaluate Model ----



