## Introduction
This program is intended to extract the frames and clips of a whale video when the whale is surfacing, to assist the scientists at Pacific Whale in their research.  

The program calls into pre-trained ML models that classify the frames of a video as:
- "surfacing" and "not surfacing"
- "quality" and "not quality"

The surfacing labels are used to determine timestamps when a whale has surfaced, while the quality labels are used to determine specific frames where important aspects of the whale body are sufficiently visible for measurement analysis. 

See /sample_images for examples of clips and images that are extracted by this program. 

## Prerequisites
The following dependencies must be installed for the program to run:
- python3
- ffmpeg (for video processing)
- pytorch (for ML models)

It is also recommended to run this on a machine with a CUDA compatible GPU.

## Run Settings

The program outputs 3 different things:
1.- a file containing video timestamps of a whale surfacing
2.- a set of video clips extracted from the original video containing moments of whale surfacing
3.- a set of images extracted from the original video containing high quality frames of the whale

In terms of computational cost, (2) and (3) are more expensive to output. Depending on the needs, one can switch them off for speed. By default, all 3 outputs are on. 

## How to Run (Windows)

```
python run.py "<video path>" "<output directory>"

```

## How to Run (Linux)

```
python3 run.py "<video path>" "<output directory>"

```