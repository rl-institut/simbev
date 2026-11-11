from simbev.mid_timeseries import DEFAULT_PURPOSE_COLUMNS, get_purpose_columns

COMMERCIAL_PURPOSES = [
    "goods_transport",
    "services",
    "passenger_transport",
    "other_business",
    "return_to_depot",
    "work",
    "school",
    "shopping",
    "leisure",
    "other_private",
    "home",
]

LEGACY_COMMERCIAL_PURPOSES = [
    "gueter",
    "dienstleistung",
    "personen",
    "sonstige_dienstlich",
    "rueckfahrt_betrieb",
    "arbeitsplatz",
    "ausbildung",
    "einkauf",
    "freizeit",
    "sonstige_privat",
    "nach_hause",
]


def _write_winter_csv(tmp_path, purposes):
    region_dir = tmp_path / "LR_Klein"
    region_dir.mkdir()
    header = ";".join(
        ["week_minute"] + [f"{i}_{purpose}" for i, purpose in enumerate(purposes)]
    )
    (region_dir / "winter.csv").write_text(
        header + "\n" + ";".join(["0"] * (len(purposes) + 1)) + "\n"
    )
    return region_dir


def test_default_purpose_columns_match_historical_mid_list():
    # Guards against accidentally reordering/renaming the columns used for
    # every existing (private-Pkw-only) scenario's weekly departure profiles.
    assert DEFAULT_PURPOSE_COLUMNS == [
        "work",
        "business",
        "school",
        "shopping",
        "private",
        "leisure",
        "home",
    ]


def test_get_purpose_columns_reads_winter_csv_header(tmp_path):
    # winter.csv always carries the full purpose header (zero-filled for
    # purposes absent in that region), unlike the sparse distance_*.csv files
    # - it must be the single source of truth for the column list and order.
    _write_winter_csv(tmp_path, COMMERCIAL_PURPOSES)

    columns = get_purpose_columns(tmp_path, "LR_Klein")

    assert columns == COMMERCIAL_PURPOSES


def test_get_purpose_columns_translates_legacy_german_header(tmp_path):
    # older commercial probability data uses German KiD2010 purpose names,
    # the order of the columns must stay the same
    _write_winter_csv(tmp_path, LEGACY_COMMERCIAL_PURPOSES)

    columns = get_purpose_columns(tmp_path, "LR_Klein")

    assert columns == COMMERCIAL_PURPOSES


def test_get_purpose_columns_works_even_when_most_purposes_are_sparse(tmp_path):
    # Regression test: heavy trucks only accumulate enough records for a
    # handful of purposes in any region (per the KiD2010-Auswertung's
    # minimum-record threshold), but winter.csv still lists all purposes
    # relevant to the vehicle_group. get_purpose_columns must not try to
    # reconcile this against distance_*.csv file counts.
    region_dir = _write_winter_csv(tmp_path, COMMERCIAL_PURPOSES)
    # only one purpose actually has a distance file for this vehicle_group/region
    (region_dir / "distance_LR_Klein_4_return_to_depot.csv").write_text(
        "value,distribution\n1,1\n"
    )

    columns = get_purpose_columns(tmp_path, "LR_Klein")

    assert len(columns) == 11
    assert "return_to_depot" in columns
