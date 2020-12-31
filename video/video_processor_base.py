"""
Parent class for all video processors. Functions effectively as an interface. 
All video processor implementations must inherit this class to function.
"""

class video_processor_base:
  def __init__(self):
    pass

  def scale_video(self, original_video, scaled_video, scale):
    """
    Scales a video (original) to a new video (scaled) into 
    given pixel dimensions (scale x scale)
    """
    pass

  def get_per_second_frames(self, original_video, out_dir):
    """
    Extracts a frame for each second of a given video into out_dir.
    """
    pass

  def get_frame_range_images(self, original_video, out_dir, ranges):
    """
    Extracts all the frames between the given 
    timestamp ranges (tuples of start/end timestamps in second increments)
    for a given video (original_video - path to original video).

    Extracted items are written to out_dir.
    """
    pass

  def get_frame_range_clips(self, original_video, out_dir, ranges, max_number_queries=3):
    """
    Extracts all the video clips between the given 
    timestamp ranges (tuples of start/end timestamps in second increments)
    for a given video (original_video - path to original video).

    Extracted items are written to out_dir.
    """
    pass

  def get_frame_images(self, original_video, out_dir, frames):
    """
    Given a list of frame numbers, extracts those frames from the video (original_video).
    Writes said frames to out_dir
    """
    pass