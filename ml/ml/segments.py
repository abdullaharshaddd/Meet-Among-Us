"""Cuts a recording into speech segments and embeds each one, so the backend can
decide who is talking in every stretch. See docs/GLOSSARY.md for VAD and embedding.

The cutting numbers are not defined here. The backend owns them (see its
SpeakerIdSettings) and sends them with each request, so tuning never touches this service.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ml import embedding, vad


@dataclass(frozen=True)
class SegmentSettings:
    merge_gap_sec: float
    min_segment_sec: float
    split_over_sec: float
    window_sec: float
    absorb_under_sec: float


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    embedding: list[float]


def merge_close_intervals(intervals: list[tuple[float, float]], merge_gap_sec: float) -> list[tuple[float, float]]:
    merged: list[tuple[float, float]] = []

    for start, end in intervals:
        if merged and start - merged[-1][1] < merge_gap_sec:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))

    return merged


def drop_short_intervals(intervals: list[tuple[float, float]], min_segment_sec: float) -> list[tuple[float, float]]:
    return [(start, end) for start, end in intervals if end - start >= min_segment_sec]


def split_long_interval(start: float, end: float, settings: SegmentSettings) -> list[tuple[float, float]]:
    # Speakers can swap inside a long stretch, and one embedding of the whole thing
    # would blur them together. Short windows catch the swap.
    if end - start <= settings.split_over_sec:
        return [(start, end)]

    windows: list[tuple[float, float]] = []
    window_start = start

    while window_start < end:
        windows.append((window_start, min(window_start + settings.window_sec, end)))
        window_start += settings.window_sec

    last_start, last_end = windows[-1]

    if last_end - last_start < settings.absorb_under_sec:
        windows.pop()
        windows[-1] = (windows[-1][0], last_end)

    return windows


def plan_segments(intervals: list[tuple[float, float]], settings: SegmentSettings) -> list[tuple[float, float]]:
    merged = merge_close_intervals(intervals, settings.merge_gap_sec)
    planned: list[tuple[float, float]] = []

    for start, end in drop_short_intervals(merged, settings.min_segment_sec):
        planned.extend(split_long_interval(start, end, settings))

    return planned


def find_segments(samples: np.ndarray, sample_rate: int, settings: SegmentSettings) -> list[Segment]:
    intervals = vad.detect_speech_intervals(samples, sample_rate)
    found: list[Segment] = []

    for start, end in plan_segments(intervals, settings):
        piece = samples[int(start * sample_rate) : int(end * sample_rate)]
        vector = embedding.normalise(embedding.embed(piece))
        found.append(Segment(start=start, end=end, embedding=vector))

    return found
