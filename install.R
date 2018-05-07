pkgs <- c("tidyverse", "rmarkdown", "data.table", "githubinstall")
install.packages(pkgs, repos="http://cloud.r-project.org")

# Install time series branch of mlr
githubinstall::gh_install_packages("mlr-org/mlr", ref = "forecasting")

