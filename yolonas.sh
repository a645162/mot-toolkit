#!/bin/bash
conda create -n yolonas python=3.10 -y
conda activate yolonas
# Python 3.8 - 3.10
conda install pycocotools==2.0.4 -c conda-forge
pip install ultralytics super-gradients
