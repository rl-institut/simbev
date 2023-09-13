def plot_gridtimeseries_by_usecase(simbev, grid_timeseries_all):
    """Create grid timeseries plots split by use case."""
    import plotly.express as px

    plot_list = [
        "home_detached_total_power",
        "home_apartment_total_power",
        "work_total_power",
        "street_total_power",
        "retail_total_power",
        "urban_fast_total_power",
        "highway_fast_total_power",
    ]
    label_list = [
        "home_detached",
        "home_apartment",
        "work",
        "street",
        "retail",
        "urban_fast",
        "highway_fast",
    ]
    y_title = "P in kW"

    if simbev.output_options["region_plot"]:
        for idx, data in enumerate(simbev.grid_data_list):
            df_results = data.set_index("timestamp")
            figname = "grid-time-series region {}".format(idx + 1)
            fig = px.line(df_results[plot_list], title=figname, labels=label_list)
            fig.update_layout(yaxis_title=y_title)
            fig.write_html("{}/{}.html".format(simbev.save_directory, figname))

    if simbev.output_options["collective_plot"]:
        df_results = grid_timeseries_all.set_index("timestamp")
        figname = "grid-time-series all regions"
        fig = px.line(df_results[plot_list], title=figname, labels=label_list)
        fig.update_layout(yaxis_title=y_title)
        fig.write_html("{}/{}.html".format(simbev.save_directory, figname))
