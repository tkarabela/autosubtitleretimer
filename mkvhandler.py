import mkvparse
from io import open
import pysubs2


class SubtitleHandler(mkvparse.MatroskaHandler):
    def __init__(self):
        self.subtitle_track = None
        self.subs = pysubs2.SSAFile()
        self.timecode_scale = None

    def tracks_available(self):
        for k in self.tracks:
            t=self.tracks[k]
            if t["CodecID"][1].startswith("S_TEXT"):
                self.subtitle_track = k
                break
        else:
            raise RuntimeError("No subtitle track in MKV file")

    def segment_info_available(self):
        for (k,(t_,v)) in self.segment_info:
            if k == "TimecodeScale":
                self.timecode_scale = int(v) / 1000 # us -> ms
                break

    def frame(self, track_id, timestamp, data, more_laced_frames, duration, keyframe, invisible, discardable):
        if track_id != self.subtitle_track:
            return

        ev = pysubs2.SSAEvent(start=int(self.timecode_scale*timestamp),
                              end=int(self.timecode_scale*(timestamp+duration)),
                              text=data.decode("utf-8"))
        self.subs.append(ev)


def extract_subtitle_track(path_to_mkv):
    """Returns SSAFile of first subtitle track in MKV file or raises RuntimeError"""
    handler = SubtitleHandler()
    with open(path_to_mkv, "rb") as fp:
        mkvparse.mkvparse(fp, handler)

    return handler.subs
