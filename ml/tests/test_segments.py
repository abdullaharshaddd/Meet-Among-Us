from ml.segments import SegmentSettings, drop_short_intervals, merge_close_intervals, plan_segments, split_long_interval

SETTINGS = SegmentSettings(
    merge_gap_sec=0.3, min_segment_sec=1.0, split_over_sec=8.0, window_sec=4.0, absorb_under_sec=2.0
)


def test_gaps_under_threshold_are_merged() -> None:
    merged = merge_close_intervals([(0.0, 2.0), (2.2, 4.0), (5.0, 7.0)], SETTINGS.merge_gap_sec)

    assert merged == [(0.0, 4.0), (5.0, 7.0)]


def test_short_segments_are_dropped() -> None:
    kept = drop_short_intervals([(0.0, 0.9), (2.0, 3.0)], SETTINGS.min_segment_sec)

    assert kept == [(2.0, 3.0)]


def test_segment_up_to_the_split_length_is_not_split() -> None:
    assert split_long_interval(0.0, 8.0, SETTINGS) == [(0.0, 8.0)]


def test_long_segment_is_split_into_windows() -> None:
    assert split_long_interval(0.0, 12.0, SETTINGS) == [(0.0, 4.0), (4.0, 8.0), (8.0, 12.0)]


def test_final_window_under_the_absorb_length_joins_the_previous_one() -> None:
    windows = split_long_interval(0.0, 9.5, SETTINGS)

    assert windows == [(0.0, 4.0), (4.0, 9.5)]


def test_final_window_of_exactly_the_absorb_length_stays() -> None:
    windows = split_long_interval(0.0, 10.0, SETTINGS)

    assert windows == [(0.0, 4.0), (4.0, 8.0), (8.0, 10.0)]


def test_plan_merges_then_drops_then_splits() -> None:
    planned = plan_segments([(0.0, 0.5), (10.0, 14.0), (14.1, 22.0), (30.0, 30.4)], SETTINGS)

    assert planned == [(10.0, 14.0), (14.0, 18.0), (18.0, 22.0)]
