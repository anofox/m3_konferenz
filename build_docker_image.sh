#!/usr/bin/env bash

docker build -t jrosskopf/m3_konferenz_notebooks .
docker login
docker push jrosskopf/m3_konferenz_notebooks

