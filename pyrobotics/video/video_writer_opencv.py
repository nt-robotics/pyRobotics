import datetime
import os
import cv2


class VideoWriterOpenCV(object):

    __DEFAULT_VIDEO_PATH = os.getenv('USERPROFILE')

    # CV_FOURCC('X', 'V', 'I', 'D') - кодек XviD
    # CV_FOURCC('P', 'I', 'M', '1') = MPEG - 1
    # CV_FOURCC('M', 'J', 'P', 'G') = motion - jpeg(does not work well)
    # CV_FOURCC('M', 'P', '4', '2') = MPEG - 4.2
    # CV_FOURCC('D', 'I', 'V', '3') = MPEG - 4.3
    # CV_FOURCC('D', 'I', 'V', 'X') = MPEG - 4
    # CV_FOURCC('U', '2', '6', '3') = H263
    # CV_FOURCC('I', '2', '6', '3') = H263I
    # CV_FOURCC('F', 'L', 'V', '1') = FLV1

    def __init__(self, folder_path: str = __DEFAULT_VIDEO_PATH, fps: float = 24.0, frame_size: tuple = (1280, 960)):
        self.__fps = fps
        self.__frame_size = frame_size
        self.__folder_path = ""
        self.__file_name = ""
        self.set_video_folder_path(folder_path)

        self.__writer = None
        # self.__fourcc = cv2.VideoWriter_fourcc(*'DIVX')
        # self.__fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', '2')
        self.__fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

    def start(self) -> None:
        today = datetime.datetime.today().strftime("%Y-%m-%d_%H_%M_%S")
        self.__file_name = "video_" + today + ".avi"
        file_path = os.path.join(self.__folder_path, self.__file_name)
        self.__writer = cv2.VideoWriter(file_path, self.__fourcc, self.__fps, self.__frame_size)

    def write(self, frame) -> None:
        if self.__writer is not None:
            self.__writer.write(frame)

    def release(self) -> None:
        if self.__writer is not None:
            self.__writer.close()
        self.__writer = None

    def set_fps(self, value: float):
        self.__fps = value

    def get_fps(self) -> float:
        return self.__fps

    def set_video_folder_path(self, path: str) -> None:
        self.__folder_path = os.path.abspath(path)

    def get_video_folder_path(self) -> str:
        return self.__folder_path

    def get_file_path(self) -> str:
        return os.path.join(self.__folder_path, self.__file_name)

    def get_file_name(self) -> str:
        return self.__file_name

#     def set_frame_size(self, size):
#         self.__video_frame_size = size
#
#     def get_frame_size(self):
#         return self.__video_frame_size
#
#     def _crop_frame(self, frame):
#         frame_wid = frame.shape[1]
#         frame_hei = frame.shape[0]
#         crop_wid = self.__video_frame_size[0]
#         crop_hei = self.__video_frame_size[1]
#
#         if frame_hei == crop_hei and frame_wid == crop_wid:
#             return frame
#
#         k_wid = crop_wid / frame_wid
#         k_hei = crop_hei / frame_hei
#
#         if k_wid > k_hei:
#             crop_frame = cv2.resize(frame, (0, 0), fx=k_wid, fy=k_wid)
#             offset_y = int((crop_frame.shape[0] - crop_hei) / 2)
#             crop_frame = crop_frame[offset_y:offset_y + crop_hei, 0:crop_wid]
#         else:
#             crop_frame = cv2.resize(frame, (0, 0), fx=k_hei, fy=k_hei)
#             offset_x = int((crop_frame.shape[1] - crop_wid) / 2)
#             crop_frame = crop_frame[0:crop_hei, offset_x:offset_x + crop_wid]
#
#         return crop_frame


# ================================================================================

# import subprocess as subp
# from os.path import join
#
# log_dir = '' # путь куда положить файл с записью
# CORE_DIR = '' # путь где лежит ffmpeg.exe
# video_file = join(log_dir, 'video_' + id_test + '.flv')
# FFMPEG_BIN = join(CORE_DIR, 'ffmpeg\\bin\\ffmpeg.exe')
#
# command = [
#     FFMPEG_BIN,
#     '-y',
#     '-loglevel', 'error',
#     '-f', 'gdigrab',
#     '-framerate', '12',
#     '-i', 'desktop',
#     '-s', '960x540',
#     '-pix_fmt', 'yuv420p',
#     '-c:v', 'libx264',
#     '-profile:v', 'main',
#     '-fs', '50M',
#     video_file
# ]
# ffmpeg = subp.Popen(command, stdin=subp.PIPE, stdout=subp.PIPE, stderr=subp.PIPE)
#
# ffmpeg.stdin.write("q")
# ffmpeg.stdin.close()

# ================================================================================

# import subprocess as sp
# import os
#
#
# ### for demonstration of how to write video data
# ### this class is an excerpt from the project moviepy https://github.com/Zulko/moviepy.git moviepy/video/io/ffmpeg_writer.py
# ###
#
# class FFMPEG_VideoWriter:
#     """ A class for FFMPEG-based video writing.
#
#     A class to write videos using ffmpeg. ffmpeg will write in a large
#     choice of formats.
#
#     Parameters
#     -----------
#
#     filename
#       Any filename like 'video.mp4' etc. but if you want to avoid
#       complications it is recommended to use the generic extension
#       '.avi' for all your videos.
#
#     size
#       Size (width,height) of the output video in pixels.
#
#     fps
#       Frames per second in the output video file.
#
#     codec
#       FFMPEG codec. It seems that in terms of quality the hierarchy is
#       'rawvideo' = 'png' > 'mpeg4' > 'libx264'
#       'png' manages the same lossless quality as 'rawvideo' but yields
#       smaller files. Type ``ffmpeg -codecs`` in a terminal to get a list
#       of accepted codecs.
#
#       Note for default 'libx264': by default the pixel format yuv420p
#       is used. If the video dimensions are not both even (e.g. 720x405)
#       another pixel format is used, and this can cause problem in some
#       video readers.
#
#     audiofile
#       Optional: The name of an audio file that will be incorporated
#       to the video.
#
#     preset
#       Sets the time that FFMPEG will take to compress the video. The slower,
#       the better the compression rate. Possibilities are: ultrafast,superfast,
#       veryfast, faster, fast, medium (default), slow, slower, veryslow,
#       placebo.
#
#     bitrate
#       Only relevant for codecs which accept a bitrate. "5000k" offers
#       nice results in general.
#
#     withmask
#       Boolean. Set to ``True`` if there is a mask in the video to be
#       encoded.
#
#     """
#
#     def __init__(self, filename, size, fps, codec="libx264", audiofile=None,
#                  preset="medium", bitrate=None, pixfmt="rgba",
#                  logfile=None, threads=None, ffmpeg_params=None):
#
#         if logfile is None:
#             logfile = sp.PIPE
#
#         self.filename = filename
#         self.codec = codec
#         self.ext = self.filename.split(".")[-1]
#
#         # order is important
#         cmd = [
#             "ffmpeg-4.2.1-win64-static/bin/ffmpeg",
#             '-y',
#             '-loglevel', 'error' if logfile == sp.PIPE else 'info',
#             '-f', 'rawvideo',
#             '-vcodec', 'rawvideo',
#             '-s', '%dx%d' % (size[1], size[0]),
#             '-pix_fmt', pixfmt,
#             '-r', '%.02f' % fps,
#             '-i', '-', '-an',
#         ]
#         cmd.extend([
#             '-vcodec', codec,
#             '-preset', preset,
#         ])
#         if ffmpeg_params is not None:
#             cmd.extend(ffmpeg_params)
#         if bitrate is not None:
#             cmd.extend([
#                 '-b', bitrate
#             ])
#         if threads is not None:
#             cmd.extend(["-threads", str(threads)])
#
#         if ((codec == 'libx264') and
#                 (size[0] % 2 == 0) and
#                 (size[1] % 2 == 0)):
#             cmd.extend([
#                 '-pix_fmt', 'yuv420p'
#             ])
#         cmd.extend([
#             filename
#         ])
#
#         popen_params = {"stdout": sp.DEVNULL,
#                         "stderr": logfile,
#                         "stdin": sp.PIPE}
#
#         # This was added so that no extra unwanted window opens on windows
#         # when the child process is created
#         if os.name == "nt":
#             popen_params["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
#
#         self.proc = sp.Popen(cmd, **popen_params)
#
#     def write_frame(self, img_array):
#         """ Writes one frame in the file."""
#         try:
#             self.proc.stdin.write(img_array.tobytes())
#         except IOError as err:
#             _, ffmpeg_error = self.proc.communicate()
#             error = (str(err) + ("\n\nMoviePy error: FFMPEG encountered "
#                                  "the following error while writing file %s:"
#                                  "\n\n %s" % (self.filename, str(ffmpeg_error))))
#
#             if b"Unknown encoder" in ffmpeg_error:
#
#                 error = error + ("\n\nThe video export "
#                                  "failed because FFMPEG didn't find the specified "
#                                  "codec for video encoding (%s). Please install "
#                                  "this codec or change the codec when calling "
#                                  "write_videofile. For instance:\n"
#                                  "  >>> clip.write_videofile('myvid.webm', codec='libvpx')") % (self.codec)
#
#             elif b"incorrect codec parameters ?" in ffmpeg_error:
#
#                 error = error + ("\n\nThe video export "
#                                  "failed, possibly because the codec specified for "
#                                  "the video (%s) is not compatible with the given "
#                                  "extension (%s). Please specify a valid 'codec' "
#                                  "argument in write_videofile. This would be 'libx264' "
#                                  "or 'mpeg4' for mp4, 'libtheora' for ogv, 'libvpx for webm. "
#                                  "Another possible reason is that the audio codec was not "
#                                  "compatible with the video codec. For instance the video "
#                                  "extensions 'ogv' and 'webm' only allow 'libvorbis' (default) as a"
#                                  "video codec."
#                                  ) % (self.codec, self.ext)
#
#             elif b"encoder setup failed" in ffmpeg_error:
#
#                 error = error + ("\n\nThe video export "
#                                  "failed, possibly because the bitrate you specified "
#                                  "was too high or too low for the video codec.")
#
#             elif b"Invalid encoder type" in ffmpeg_error:
#
#                 error = error + ("\n\nThe video export failed because the codec "
#                                  "or file extension you provided is not a video")
#
#             raise IOError(error)
#
#     def close(self):
#         if self.proc:
#             self.proc.stdin.close()
#             if self.proc.stderr is not None:
#                 self.proc.stderr.close()
#             self.proc.wait()
#
#         self.proc = None
#
#     # Support the Context Manager protocol, to ensure that resources are cleaned up.
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_value, traceback):
#         self.close()

# =============================================================