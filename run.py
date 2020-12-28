from datetime import timedelta
import math
import random
import sys
import time
import multiprocessing
import os
from PIL import Image
from numpy import asarray

import model.model_pytorch

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
torch.set_default_tensor_type('torch.cuda.FloatTensor')

def get_resnet18():
  model = models.resnet18(pretrained=True)
  num_ftrs = model.fc.in_features
  model.fc = nn.Linear(num_ftrs, 2)
  return model

def convert_original_video_to_scaled(original_video, scaled_video, scale=224):
  os.system("ffmpeg -i {0} -vf scale={1}:{1} {2}".format(original_video, scale, scaled_video))

def extract_per_second_frames(temp_dir, scaled_video, fps=30):
  os.system("ffmpeg -i {0} -r 1/1 {1}.png".format(scaled_video, os.path.join(temp_dir, "%03d")))

def frames_to_ts(frame_number, fps=30):
  span = timedelta(milliseconds= frame_number*1000/fps)
  return "{:02d}{:02d}{:02d}".format(int(span.seconds/60), int(span.seconds%60), int(span.microseconds/1000))

def get_final_image_name(original_vid, out_dir, frame, number):
  # File name templae: Species_Location_Date_OriginalVideoframe#_screencapture#_VideoTimeStamp(MMSS)
  # File name example: MN_HI_20200824_0001_001_0301
  original_vid_name = original_vid.split(".")[0]

  return os.path.join(out_dir, "{}_{:02d}_{}".format(original_vid_name, number, frames_to_ts(frame)))

def extract_frame_range_clip(temp_dir, ranges, original_vid):
  # construct range query
  # limit to 3 max at a time to save CPU and prevent crashing.
  number_of_clips = len(ranges)
  max_per_call = 5
  current_point = 0
  while current_point < number_of_clips:
    q = ""
    for r in ranges[current_point:min(number_of_clips, current_point+3)]:
      q += " -ss {0} -t {1} {2}".format(r[0], r[1]-r[0], os.path.join(temp_dir,"{0}_Surface{1}-{2}.mp4".format(original_vid, r[0], r[1])))

    os.system("ffmpeg {1} -i {0}".format(original_vid, q))
    current_point += 3

# ranges is a list of tuples with start/end timestamps
def extract_frame_range(temp_dir, ranges, scaled_vid):
  # construct range query
  q = "between(t\,{0}\,{1})".format(ranges[0][0], ranges[0][1])
  for r in ranges[1:]:
    q += "+between(t\,{0}\,{1})".format(r[0], r[1])

  os.system("ffmpeg -i {0} -vf select='{1}' -vsync 0 -frame_pts 1 {2}.png".format(scaled_vid, q, os.path.join(temp_dir, "%03d")))

def fetch_original_images(out_dir, frames, original_vid):
  q = "eq(n\,{0})".format(frames[0])
  for frame in frames[1:]:
    q += "+eq(n\,{0})".format(frame)

  os.system('ffmpeg -i {0} -vf "select={1}" -vsync 0 -frame_pts 1 {2}.jpg'.format(original_vid, q, os.path.join(out_dir, "%d")))

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

def run(original_video, output_dir, surface_model, quality_model, input_dir=None):
  original_video_name = original_video.split(".")[0]
  # temp dirs
  temp_dir1 = "temp_seconds"
  temp_dir2 = "temp_surface"
  clips_dir = "surfacing_clips"

  if not os.path.exists(temp_dir1):
    os.mkdir(temp_dir1)

  if not os.path.exists(temp_dir2):
    os.mkdir(temp_dir2)

  if not os.path.exists(clips_dir):
    os.mkdir(clips_dir)

  if not os.path.exists(output_dir):
    os.mkdir(output_dir)

  # temp dirs for specific video 
  seconds_temp_dir = os.path.join(temp_dir1, original_video_name)
  surface_temp_dir = os.path.join(temp_dir2, original_video_name)
  clips_temp_dir = os.path.join(clips_dir, original_video_name)
  scaled_temp_video = "scaled_{0}_224.mov".format(original_video_name)
  final_out_dir = os.path.join(output_dir, original_video_name)

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
    convert_original_video_to_scaled(original_video, scaled_temp_video)

  # extract per second
  print("Extracting per second frames from {0} to {1}".format(scaled_temp_video, seconds_temp_dir))
  extract_per_second_frames(seconds_temp_dir, scaled_temp_video)

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
  print(surfacing_ranges)
  extract_frame_range(surface_temp_dir, surfacing_ranges, scaled_temp_video)

  # get surfacing clips
  extract_frame_range_clip(clips_temp_dir, surfacing_ranges, original_video)
  
  # predict quality on the extracted images.
  # load quality model
  
  print("Predicting quality of images in {0}".format(surface_temp_dir))

  # load temporary 
  dirs = os.listdir(surface_temp_dir)
  quality_preds = [] # contains the frame numbers that have preds
  for f in dirs:
    image_path = os.path.join(surface_temp_dir, f)
    quality_pred = quality_model(image_path)

    if quality_pred == 1:
      quality_preds.append(int(f.split('.')[0])) # append frame number

  # finally, given list of successful frames, fetch the original image
  if len(quality_preds) > 0:
    print("Total of {0} frames of acceptable quality detected".format(len(quality_preds)))
    fetch_original_images(final_out_dir, quality_preds, original_video)
  else:
    print("No suitable frames found! :(")


if __name__ == "__main__":
  print("Starting run on video {0} : {1}".format(sys.argv[1], time.strftime("%H:%M:%S", time.localtime())))

  # init models
  surface_model = model_pytorch("model/pytorch/surface_model9-5-2020.pth")
  quality_model = model_pytorch("model/pytorch/quality_model9-5-2020.pth")

  run(sys.argv[1], sys.argv[2], surface_model, quality_model)
  print("End run. Output written to dir {0} : {1}".format(sys.argv[2], time.strftime("%H:%M:%S", time.localtime())))