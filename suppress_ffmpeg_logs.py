"""
Suppress FFmpeg/libav logs at C level before importing OpenCV.
This must be imported before cv2.
"""
import os
import sys

# Set environment variables BEFORE any imports
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'  # AV_LOG_QUIET
os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'
os.environ['FFREPORT'] = '0'
os.environ['AV_LOG_FORCE_NOCOLOR'] = '1'

# Try to suppress FFmpeg logs at C level if possible
try:
    import ctypes
    import ctypes.util
    
    # Try to find and load libavutil
    libavutil_name = ctypes.util.find_library('avutil')
    if libavutil_name:
        libavutil = ctypes.CDLL(libavutil_name)
        # av_log_set_level(AV_LOG_QUIET = -8)
        if hasattr(libavutil, 'av_log_set_level'):
            libavutil.av_log_set_level(-8)
except:
    pass  # If fails, environment variables will still help
