import numpy as np
import cv2
import pytest

from backend import video_processing


def _write_test_video(path, fps, total_frames, size=(64, 64)):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, size)
    assert writer.isOpened(), "OpenCV could not open VideoWriter"
    for i in range(total_frames):
        frame = np.full((size[1], size[0], 3), i % 256, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_extract_returns_requested_frame_count(tmp_path):
    video = tmp_path / "v.mp4"
    _write_test_video(video, fps=30, total_frames=300)  # 10s

    frames = video_processing.extract_video_frames(
        str(video), max_seconds=10, frame_count=15
    )

    assert len(frames) == 15


def test_extract_respects_max_seconds_cap(tmp_path):
    video = tmp_path / "v.mp4"
    _write_test_video(video, fps=30, total_frames=600)  # 20s of source

    frames = video_processing.extract_video_frames(
        str(video), max_seconds=5, frame_count=10
    )

    assert len(frames) == 10


def test_extract_caps_at_actual_duration_when_shorter(tmp_path):
    video = tmp_path / "v.mp4"
    _write_test_video(video, fps=30, total_frames=60)  # only 2s

    frames = video_processing.extract_video_frames(
        str(video), max_seconds=10, frame_count=4
    )

    assert len(frames) == 4


def test_base_encoder_roundtrips(tmp_path):
    image = tmp_path / "frame.jpg"
    arr = np.full((32, 32, 3), 128, dtype=np.uint8)
    cv2.imwrite(str(image), arr)

    encoded = video_processing.base_encoder(str(image))

    import base64
    decoded = base64.b64decode(encoded)
    assert decoded == image.read_bytes()
