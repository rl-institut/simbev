import argparse
from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers
import pathlib
import datetime
import copy

def sensitivity_analysis(simbev_obj, cfg, analysis_dict):

    analysis_values = analysis_dict["analysis_values"]
    analysis_variable = analysis_dict["analysis_variable"]

    for index, value in enumerate(analysis_values):
        analysis_variable_tuple = analysis_variable.split("-")
        simbev_obj_temporary = copy.deepcopy(simbev_obj)
        if analysis_variable_tuple[0] == "tech_data":
            simbev_obj_temporary.tech_data.loc[analysis_variable_tuple[2], analysis_variable_tuple[1]] = value
        path_parent = simbev_obj_temporary.save_directory.parent
        folder_name = simbev_obj_temporary.save_directory.name
        simbev_obj_temporary.save_directory = pathlib.Path(
            path_parent, folder_name + analysis_variable + "_" + str(value)
        )

        # run simulation with optional timing
        helpers.timeitlog(simbev_obj_temporary.output_options["timing"], simbev_obj_temporary.save_directory)(
            simbev_obj_temporary.run_multi
        )()

        helpers.export_metadata(simbev_obj_temporary, cfg)
