import math
import uuid

from sqlalchemy.orm import Session

from app.core import ml_client
from app.core.config import SpeakerIdSettings
from app.core.vectors import normalise
from app.models.workspace import WorkspaceRole
from app.repositories import (
    user_repository,
    voiceprint_repository,
    workspace_member_repository,
    workspace_repository,
)
from app.services import speaker_id_service

MODEL_VERSION = "ecapa-voxceleb-v1"
SETTINGS = SpeakerIdSettings()


def voice(axis: int, blend_axis: int | None = None, blend: float = 0.0) -> list[float]:
    """A fake embedding that points along one axis. `blend` mixes in a second axis, which
    lowers the cosine similarity to a pure `axis` voice."""
    vector = [0.0] * 192
    vector[axis] = 1.0 - blend

    if blend_axis is not None:
        vector[blend_axis] = blend

    return normalise(vector)


def segment(start: float, embedding: list[float], length: float = 4.0) -> ml_client.SegmentResult:
    return ml_client.SegmentResult(start=start, end=start + length, embedding=embedding)


def candidate(name: str, axis: int) -> speaker_id_service.Candidate:
    return speaker_id_service.Candidate(user_id=uuid.uuid4(), name=name, centroid=voice(axis))


def decide(segments: list[ml_client.SegmentResult], candidates: list[speaker_id_service.Candidate]):
    runs = speaker_id_service.pool_into_runs(segments, candidates, SETTINGS)
    labelled = speaker_id_service.label_runs(runs, candidates, SETTINGS)

    return speaker_id_service.merge_into_turns(labelled)


def test_floor_grows_with_speech_then_stops_at_the_cap() -> None:
    floors = [speaker_id_service.floor_for(seconds, SETTINGS) for seconds in (1, 2, 3, 4, 10)]

    for actual, expected in zip(floors, [0.60, 0.65, 0.70, 0.72, 0.72]):
        assert math.isclose(actual, expected)


def test_clear_match_gets_the_members_name_and_the_evidence_behind_it() -> None:
    alice = candidate("Alice", axis=0)
    turns = decide([segment(0.0, voice(0))], [alice])

    assert len(turns) == 1
    assert turns[0].speaker_label == "Alice"
    assert turns[0].user_id == alice.user_id
    assert math.isclose(turns[0].best_score, 1.0)
    assert turns[0].pooled_seconds == 4.0
    assert math.isclose(turns[0].floor_applied, 0.72)


def test_score_below_the_floor_is_unknown_and_shows_the_closest_member() -> None:
    alice = candidate("Alice", axis=0)
    turns = decide([segment(0.0, voice(0, blend_axis=5, blend=0.5))], [alice])

    assert turns[0].speaker_label == "Unknown Speaker 1"
    assert turns[0].user_id is None
    assert turns[0].best_candidate_name == "Alice"
    assert turns[0].best_score < turns[0].floor_applied


def test_best_match_too_close_to_the_runner_up_is_unknown() -> None:
    alice = candidate("Alice", axis=0)
    bob = candidate("Bob", axis=1)
    ambiguous = normalise([1.0, 0.95] + [0.0] * 190)
    turns = decide([segment(0.0, ambiguous)], [alice, bob])

    assert turns[0].best_score >= turns[0].floor_applied
    assert turns[0].margin < SETTINGS.margin
    assert turns[0].speaker_label == "Unknown Speaker 1"


def test_one_weak_slice_does_not_flip_a_turn() -> None:
    alice = candidate("Alice", axis=0)
    weak = voice(0, blend_axis=5, blend=0.55)

    alone = decide([segment(4.0, weak)], [alice])
    pooled = decide([segment(0.0, voice(0)), segment(4.0, weak), segment(8.0, voice(0))], [alice])

    assert alone[0].speaker_label == "Unknown Speaker 1"
    assert len(pooled) == 1
    assert pooled[0].speaker_label == "Alice"
    assert pooled[0].pooled_seconds == 12.0


def test_two_different_unknown_voices_get_different_numbers() -> None:
    alice = candidate("Alice", axis=0)
    turns = decide([segment(0.0, voice(10)), segment(4.0, voice(11))], [alice])

    assert [turn.speaker_label for turn in turns] == ["Unknown Speaker 1", "Unknown Speaker 2"]


def test_same_unknown_voice_keeps_its_number() -> None:
    alice = candidate("Alice", axis=0)
    segments = [segment(0.0, voice(10)), segment(4.0, voice(11)), segment(8.0, voice(10, 12, 0.1))]
    turns = decide(segments, [alice])

    assert [turn.speaker_label for turn in turns] == [
        "Unknown Speaker 1",
        "Unknown Speaker 2",
        "Unknown Speaker 1",
    ]


def test_one_unknown_voice_whose_nearest_member_flips_stays_one_turn() -> None:
    alice = candidate("Alice", axis=0)
    bob = candidate("Bob", axis=1)
    toward_alice = normalise([0.05] + [0.0] * 9 + [1.0] + [0.0] * 181)
    toward_bob = normalise([0.0, 0.05] + [0.0] * 8 + [1.0] + [0.0] * 180)
    turns = decide([segment(0.0, toward_alice), segment(4.0, toward_bob)], [alice, bob])

    assert len(turns) == 1
    assert turns[0].speaker_label == "Unknown Speaker 1"
    assert turns[0].pooled_seconds == 8.0


def test_short_run_that_fails_the_floor_is_unclear_not_a_new_unknown_speaker() -> None:
    alice = candidate("Alice", axis=0)
    turns = decide([segment(0.0, voice(10), length=2.0)], [alice])

    assert [turn.speaker_label for turn in turns] == ["Unclear"]
    assert turns[0].user_id is None


def test_short_run_that_passes_the_floor_is_still_named() -> None:
    alice = candidate("Alice", axis=0)
    turns = decide([segment(0.0, voice(0), length=1.5)], [alice])

    assert turns[0].speaker_label == "Alice"


def test_unclear_runs_do_not_take_up_unknown_speaker_numbers() -> None:
    alice = candidate("Alice", axis=0)
    segments = [segment(0.0, voice(10), length=2.0), segment(4.0, voice(11), length=4.0)]
    turns = decide(segments, [alice])

    assert [turn.speaker_label for turn in turns] == ["Unclear", "Unknown Speaker 1"]


def test_neighbouring_unclear_runs_merge_into_one_turn() -> None:
    alice = candidate("Alice", axis=0)
    segments = [segment(0.0, voice(10), length=2.0), segment(2.5, voice(11), length=2.0)]
    turns = decide(segments, [alice])

    assert len(turns) == 1
    assert turns[0].speaker_label == "Unclear"
    assert turns[0].pooled_seconds == 4.0


def test_the_unclear_length_comes_from_settings() -> None:
    alice = candidate("Alice", axis=0)
    strict = SpeakerIdSettings(min_group_seconds=1.0)
    segments = [segment(0.0, voice(10), length=2.0)]

    runs = speaker_id_service.pool_into_runs(segments, [alice], strict)
    labelled = speaker_id_service.label_runs(runs, [alice], strict)

    assert labelled[0].label == "Unknown Speaker 1"


def test_unknown_group_mean_stays_unit_length() -> None:
    group = speaker_id_service.UnknownGroup(number=1, total=[0.0] * 192)
    group.add(voice(10))
    group.add(voice(10, 11, 0.2))

    assert math.isclose(math.sqrt(sum(value * value for value in group.mean())), 1.0)


def test_no_enrolled_members_means_everyone_is_unknown() -> None:
    turns = decide([segment(0.0, voice(0))], [])

    assert turns[0].speaker_label == "Unknown Speaker 1"
    assert turns[0].best_score is None
    assert turns[0].best_candidate_name is None


def test_parameters_come_from_settings_not_code() -> None:
    strict = SpeakerIdSettings(floor_base=0.99, floor_cap=0.99)
    alice = candidate("Alice", axis=0)
    segments = [segment(0.0, voice(0, blend_axis=5, blend=0.3))]

    assert decide(segments, [alice])[0].speaker_label == "Alice"

    runs = speaker_id_service.pool_into_runs(segments, [alice], strict)
    labelled = speaker_id_service.label_runs(runs, [alice], strict)

    assert labelled[0].user_id is None
    assert math.isclose(labelled[0].floor, 0.99)


def _make_user(db: Session, name: str):
    return user_repository.create_password_user(
        db, email=f"{uuid.uuid4()}@example.com", password_hash="x", display_name=name
    )


def _enrol(db: Session, user, axis: int, model_version: str = MODEL_VERSION) -> None:
    voiceprint_repository.upsert(
        db,
        user_id=user.id,
        centroid=voice(axis),
        intra_speaker_variance=0.1,
        sample_count=3,
        model_version=model_version,
    )


def test_voiceprint_from_another_workspace_is_ignored(db: Session) -> None:
    alice = _make_user(db, "Alice")
    outsider = _make_user(db, "Outsider")
    workspace = workspace_repository.create_with_owner(
        db, name="Room", owner_user_id=alice.id, join_code="AAAABBBB"
    )
    workspace_repository.create_with_owner(
        db, name="Elsewhere", owner_user_id=outsider.id, join_code="CCCCDDDD"
    )
    _enrol(db, alice, axis=0)
    _enrol(db, outsider, axis=1)

    rows = voiceprint_repository.list_for_workspace(db, workspace.id)
    candidates, skipped = speaker_id_service.split_by_model_version(rows, MODEL_VERSION)
    turns = decide([segment(0.0, voice(1))], candidates)

    assert [c.name for c in candidates] == ["Alice"]
    assert skipped == []
    assert turns[0].speaker_label == "Unknown Speaker 1"


def test_voiceprint_with_a_different_model_version_is_skipped_and_reported(db: Session) -> None:
    alice = _make_user(db, "Alice")
    bob = _make_user(db, "Bob")
    workspace = workspace_repository.create_with_owner(
        db, name="Room", owner_user_id=alice.id, join_code="EEEEFFFF"
    )
    workspace_repository.create_with_owner(db, name="Other", owner_user_id=bob.id, join_code="GGGGHHHH")
    _enrol(db, alice, axis=0)
    _enrol(db, bob, axis=1, model_version="old-model-v0")
    workspace_member_repository.create(db, workspace_id=workspace.id, user_id=bob.id, role=WorkspaceRole.MEMBER)

    rows = voiceprint_repository.list_for_workspace(db, workspace.id)
    candidates, skipped = speaker_id_service.split_by_model_version(rows, MODEL_VERSION)

    assert [c.name for c in candidates] == ["Alice"]
    assert [item.name for item in skipped] == ["Bob"]
    assert skipped[0].model_version == "old-model-v0"
