## Introduction
This program is intended to extract the frames and clips of a whale video when the whale is surfacing, to assist the scientists at Pacific Whale in their research.  

The program calls into pre-trained ML models that classify the frames of a video as:
- "surfacing" and "not surfacing"
- "quality" and "not quality"

The surfacing labels are used to determine timestamps when a whale has surfaced, while the quality labels are used to determine specific frames where important aspects of the whale body are sufficiently visible for measurement analysis. 

See */examples* for examples of clips and images that are extracted by this program. 

## Prerequisites
The following dependencies must be installed for the program to run:
- python3
- ffmpeg (for video processing)
- pytorch (for ML models)

It is also recommended to run this on a machine with a CUDA compatible GPU for speed.

## Run Settings & Output

The program outputs 3 different things into a specified folder:
1. a file containing video timestamps of a whale surfacing (output to .txt file **videoname** _surfacing_clip.txt)
2. a set of video clips extracted from the original video containing moments of whale surfacing (output to **/surfacing_clips**)
3. a set of images extracted from the original video containing high quality frames of the whale (output to **/quality_frames**)

In terms of computational cost, (2) and (3) are more expensive to output. Depending on the needs, one can switch them off for speed (TBC). By default, all 3 outputs are on. 

## How to Run (Windows)

```
python run.py "<video path>" "<output directory>"

```

## How to Run (Linux)

```
python3 run.py "<video path>" "<output directory>"

```


## Overview of Codebase

TBC

- classification models located in /models
- video processing tool located in /video
- model training scripts located in /training_scripts (TBC)

Users are welcome to implement their own classification models and/or video processing tools provided they inherit the required functions in the base classes. 

## Overview of Models

A few models were tested and the best design/model was chosen as described below. Samples of the training data are available in /training_scripts. 

Surfacing Model - this model classifies a frame into 5 different categories of surfacing. 
Quality Model - this model classifies a frame into 2 categories. 


## Limitations

Some limitations to be aware of when using this tool. TBC.