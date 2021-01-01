from datetime import timedelta
import math
import random
import sys
import time
import multiprocessing
import os
from PIL import Image
from numpy import asarray

from model.model_pytorch import model_pytorch
from video.ffmpeg_processor import ffmpeg_processor

def frames_to_ts(frame_number, fps=30):
  span = timedelta(milliseconds= frame_number*1000/fps)
  return "{:02d}{:02d}{:02d}".format(int(span.seconds/60), int(span.seconds%60), int(span.microseconds/1000))

def seconds_to_ts(seconds_number):
  span = timedelta(seconds= seconds_number)
  return "{:02d}:{:02d}".format(int(span.seconds/60), int(span.seconds%60))

def get_final_image_name(original_vid, out_dir, frame, number):
  # File name templae: Species_Location_Date_OriginalVideoframe#_screencapture#_VideoTimeStamp(MMSS)
  # File name example: MN_HI_20200824_0001_001_0301
  original_vid_name = os.path.basename(original_vid).split(".")[0]

  return os.path.join(out_dir, "{}_{:02d}_{}".format(original_vid_name, number, frames_to_ts(frame)))

def fetch_original_images(out_dir, frames, original_vid, video_processor):
  video_processor.get_frame_images(original_vid, out_dir, frames)

  # rename all the images with their timestamps
  # File name templae: Species_Location_Date_OriginalVideoframe#_screencapture#_VideoTimeStamp(MMSS)
  # File name example: MN_HI_20200824_0001_001_0301
  c = 1
  for frame in frames:
    os.rename("{0}.jpg".format(os.path.join(out_dir, str(frame))), "{0}.jpg".format(get_final_image_name(original_vid, out_dir, frame, c)))
    c += 1

# We actually keep -2 seconds from each start range to capture the beginning of the surface.
# We also join close surfacings (i.e.within 1 seconds of each other)
def preds_to_range(preds):
  size_preds = len(preds)
  fixed_preds = []
  c = 0
  for i in preds:
    if i == 1:
      fixed_preds.append(i)
    else:
      if c != 0 and c != size_preds-1:
        if preds[c-1] == 1 and preds[c+1] == 1:
          fixed_preds.append(1) #adjust only if neighbours are also 1
        else:
          fixed_preds.append(i)
    c+=1

  ranges = []

  current = 0
  active = False
  c = 0 # this is actually the seconds
  for i in fixed_preds:
    if i == 0:
      if active:
        ranges.append((current, c))
        active = False
    else:
      # i = 1, keep track
      if not active:
        current = c if c <= 1 else c-2
        active = True

    c += 1

  if active:
    ranges.append((current, c))

  return ranges

def write_ranges_to_file(video_name, ranges, output_dir):
  output_file_name = os.path.join(output_dir, "{0}_surfacing_intervals.txt".format(video_name))

  if len(ranges) > 0:
    with open(output_file_name, 'w') as f:
      for r in ranges:
        write_line = "{0} - {1}\n".format(seconds_to_ts(r[0]), seconds_to_ts(r[1]))
        f.write(write_line)

def run(original_video, output_dir, surface_model, quality_model, video_processor, input_dir=None):
  original_video_name = os.path.basename(original_video).split(".")[0]

  # temp dirs
  temp_dir = "temp"
  temp_dir1 = os.path.join(temp_dir, "temp_seconds")
  temp_dir2 = os.path.join(temp_dir, "temp_surface")
  clips_dir = os.path.join(output_dir, "surfacing_clips")
  frames_dir = os.path.join(output_dir, "quality_frames")

  if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

  if not os.path.exists(temp_dir1):
    os.mkdir(temp_dir1)

  if not os.path.exists(temp_dir2):
    os.mkdir(temp_dir2)

  if not os.path.exists(clips_dir):
    os.mkdir(clips_dir)

  if not os.path.exists(frames_dir):
    os.mkdir(frames_dir)

  # temp dirs for specific video 
  seconds_temp_dir = os.path.join(temp_dir1, original_video_name)
  surface_temp_dir = os.path.join(temp_dir2, original_video_name)
  clips_temp_dir = os.path.join(clips_dir, original_video_name)
  scaled_temp_video = "scaled_{0}_224.mov".format(original_video_name)
  final_out_dir = os.path.join(frames_dir, original_video_name)

  if not os.path.exists(seconds_temp_dir):
    os.mkdir(seconds_temp_dir)

  if not os.path.exists(surface_temp_dir):
    os.mkdir(surface_temp_dir)

  if not os.path.exists(final_out_dir):
    os.mkdir(final_out_dir)

  if not os.path.exists(clips_temp_dir):
    os.mkdir(clips_temp_dir)

  # convert original video to scaled
  if not os.path.exists(scaled_temp_video):
    print("Scaling down original video {0} to {1}".format(original_video, scaled_temp_video))
    video_processor.scale_video(original_video, scaled_temp_video, 224)

  # extract per second
  print("Extracting per second frames from {0} to {1}".format(scaled_temp_video, seconds_temp_dir))
  video_processor.get_per_second_frames(scaled_temp_video, seconds_temp_dir)

  # This is the surface dir
  dirs = os.listdir(seconds_temp_dir)
  surfacing_series = []
  for f in dirs:
    image_path = os.path.join(seconds_temp_dir, f)
    surface_pred = surface_model.predict(image_path)
    print("path {0} pred {1} pred {2}".format(image_path, surface_pred, surface_pred))
    surfacing_series.append(surface_pred)

  # given surfacing predictions, get range of frames to fetch
  surfacing_ranges = preds_to_range(surfacing_series)
  print("Writing surfacing intervals to file {0}".format(original_video_name))
  write_ranges_to_file(original_video_name, surfacing_ranges, output_dir)

  # get frames of surfacing shots, but on the scaled video
  video_processor.get_frame_range_images(scaled_temp_video, surface_temp_dir, surfacing_ranges)

  # get surfacing clips
  video_processor.get_frame_range_clips(original_video, clips_temp_dir, surfacing_ranges)
  
  # predict quality on the extracted images.
  print("Predicting quality of images in {0}".format(surface_temp_dir))

  # load temporary 
  dirs = os.listdir(surface_temp_dir)
  quality_preds = [] # contains the frame numbers that have preds
  for f in dirs:
    image_path = os.path.join(surface_temp_dir, f)
    quality_pred = quality_model.predict(image_path)

    if quality_pred == 1:
      quality_preds.append(int(f.split('.')[0])) # append frame number

  # finally, given list of successful frames, fetch the original image
  if len(quality_preds) > 0:
    print("Total of {0} frames of acceptable quality detected".format(len(quality_preds)))
    fetch_original_images(final_out_dir, quality_preds, original_video, video_processor)
  else:
    print("No suitable frames found! :(")


if __name__ == "__main__":
  print("Starting run on video {0} : {1}".format(sys.argv[1], time.strftime("%H:%M:%S", time.localtime())))

  # init models
  surface_model = model_pytorch("model/pytorch/surface_model9-5-2020.pth")
  quality_model = model_pytorch("model/pytorch/quality_model9-5-2020.pth")

  input_vid = os.path.normpath(sys.argv[1])
  output_dir = os.path.normpath(sys.argv[2])

  # init video processor
  video_processor = ffmpeg_processor()

  if not os.path.exists(output_dir):
    os.mkdir(output_dir)

  run(input_vid, output_dir, surface_model, quality_model, video_processor)
  print("End run. Output written to directory {0} : {1}".format(sys.argv[2], time.strftime("%H:%M:%S", time.localtime())))