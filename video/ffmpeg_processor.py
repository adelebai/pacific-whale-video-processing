"""
This class wraps the ffmpeg video processor on the command line.
"""

import os
from video.video_processor_base import video_processor_base

class ffmpeg_processor(video_processor_base):
  def __init__(self):
    video_processor_base.__init__(self)

  def scale_video(self, original_video, scaled_video, scale):
    """
    Scales a video (original) to a new video (scaled) into 
    given pixel dimensions (scale x scale)
    """
    os.system("ffmpeg -i {0} -vf scale={1}:{1} {2}".format(original_video, scale, scaled_video))
    
  def get_per_second_frames(self, original_video, out_dir):
    """
    Extracts a frame for each second of a given video into out_dir.
    """
    os.system("ffmpeg -i {0} -r 1/1 {1}.png".format(original_video, os.path.join(out_dir, "%03d")))

  def get_frame_range_images(self, original_video, out_dir, ranges):
    """
    Extracts all the frames between the given 
    timestamp ranges (tuples of start/end timestamps in second increments)
    for a given video (original_video - path to original video).

    Extracted items are written to out_dir.
    """
    if len(ranges) == 0:
      return

    q = "between(t\,{0}\,{1})".format(ranges[0][0], ranges[0][1])
    for r in ranges[1:]:
      q += "+between(t\,{0}\,{1})".format(r[0], r[1])

    os.system("ffmpeg -i {0} -vf select='{1}' -vsync 0 -frame_pts 1 {2}.png".format(original_video, q, os.path.join(out_dir, "%03d")))

  def get_frame_range_clips(self, original_video, out_dir, ranges, max_number_queries=3):
    """
    Extracts all the video clips between the given 
    timestamp ranges (tuples of start/end timestamps in second increments)
    for a given video (original_video - path to original video).

    Extracted items are written to out_dir.
    """
    base_video_name = os.path.basename(original_video)

    # construct range query
    # limit to 3 max at a time to save CPU and prevent crashing.
    number_of_clips = len(ranges)
    max_per_call = 5
    current_point = 0
    while current_point < number_of_clips:
      q = ""
      for r in ranges[current_point:min(number_of_clips, current_point+max_number_queries)]:
        q += " -ss {0} -t {1} {2}".format(r[0], r[1]-r[0], os.path.join(out_dir,"{0}_Surface{1}-{2}.mp4".format(base_video_name, r[0], r[1])))

      os.system("ffmpeg {1} -i {0}".format(original_video, q))
      current_point += max_number_queries

  def get_frame_images(self, original_video, out_dir, frames):
    """
    Given a list of frame numbers, extracts those frames from the video (original_video).
    Writes said frames to out_dir
    """
    if len(frames) == 0:
      return

    q = "eq(n\,{0})".format(frames[0])
    for frame in frames[1:]:
      q += "+eq(n\,{0})".format(frame)

    os.system('ffmpeg -i {0} -vf "select={1}" -vsync 0 -frame_pts 1 {2}.jpg'.format(original_video, q, os.path.join(out_dir, "%d")))
