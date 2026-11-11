import pandas as pd

from simbev.region import RegionType, _strip_purpose_prefix


def test_strip_purpose_prefix_multiword():
    assert _strip_purpose_prefix("4_return_to_depot") == "return_to_depot"
    assert _strip_purpose_prefix("0_work") == "work"
    assert _strip_purpose_prefix("private") == "private"


def _write_distance_csv(region_dir, purpose_suffix):
    df = pd.DataFrame({"value": [1, 2], "distribution": [0.5, 0.5]})
    df.to_csv(region_dir / "distance_LR_Klein_{}.csv".format(purpose_suffix), index=False)


def test_load_probabilities_keeps_multiword_purpose_intact(tmp_path):
    # Regression test: the old file.stem.split("_")[-1] parsing truncated
    # "4_return_to_depot" down to just "depot". The fix must keep the
    # full compound purpose name.
    region_dir = tmp_path / "LR_Klein"
    region_dir.mkdir()
    _write_distance_csv(region_dir, "4_return_to_depot")

    region_type = RegionType("LR_Klein", False, 15, {}, 1000.0)
    probabilities = region_type._load_probabilities(tmp_path, "light_duty_vehicle")

    assert "return_to_depot" in probabilities["distance"]
    assert "depot" not in probabilities["distance"]


def test_load_probabilities_translates_legacy_german_purpose(tmp_path):
    # older commercial probability data uses German KiD2010 purpose names
    region_dir = tmp_path / "LR_Klein"
    region_dir.mkdir()
    _write_distance_csv(region_dir, "4_rueckfahrt_betrieb")

    region_type = RegionType("LR_Klein", False, 15, {}, 1000.0)
    probabilities = region_type._load_probabilities(tmp_path, "light_duty_vehicle")

    assert list(probabilities["distance"]) == ["return_to_depot"]


def test_ridesharing_rename_only_applies_to_private_group(tmp_path):
    region_dir = tmp_path / "LR_Klein"
    region_dir.mkdir()
    _write_distance_csv(region_dir, "42_ridesharing")

    region_type = RegionType("LR_Klein", False, 15, {}, 1000.0)

    private_probabilities = region_type._load_probabilities(tmp_path, "private")
    assert "private" in private_probabilities["distance"]
    assert "ridesharing" not in private_probabilities["distance"]

    commercial_probabilities = region_type._load_probabilities(tmp_path, "pkw_commercial")
    assert "ridesharing" in commercial_probabilities["distance"]
