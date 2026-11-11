from simbev.mid_timeseries import LEGACY_PURPOSE_NAMES, normalize_purpose_name
from simbev.car import PRIVATE_CHARGING_ROLES, PARTIAL_DEPOT_PURPOSES


def test_normalize_purpose_name_strips_prefix():
    assert normalize_purpose_name("4_return_to_depot") == "return_to_depot"
    assert normalize_purpose_name("10_home") == "home"
    assert normalize_purpose_name("work") == "work"


def test_normalize_purpose_name_translates_legacy_names():
    assert normalize_purpose_name("4_rueckfahrt_betrieb") == "return_to_depot"
    assert normalize_purpose_name("0_gueter") == "goods_transport"
    assert normalize_purpose_name("10_nach_hause") == "home"


def test_code_uses_only_english_purpose_names():
    # purposes referenced in the code must be reachable from both the new
    # English and the legacy German data
    english_names = set(LEGACY_PURPOSE_NAMES.values())
    for vehicle_group, roles in PRIVATE_CHARGING_ROLES.items():
        if vehicle_group == "private":
            continue
        assert set(roles) <= english_names
    assert PARTIAL_DEPOT_PURPOSES <= english_names
