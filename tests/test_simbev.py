from simbev.simbev_class import SimBEV
import pathlib


def test_simbev_from_config():
    scenario_path = pathlib.Path("scenarios", "default", "configs", "default.cfg")
    simbev_obj, cfg = SimBEV.from_config(scenario_path)
    assert simbev_obj.name == scenario_path.stem
