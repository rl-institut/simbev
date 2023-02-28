def plot_gridtimeseries_by_usecase(simbev, grid_timeseries_all):
    import matplotlib.pyplot as plt

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
    # TODO fix plot first region outputs all regions data (log_region_data)
    if simbev.output_options["region_plot"]:
        for idx, data in enumerate(simbev.grid_data_list):
            df_results = data.set_index("timestamp")

            plt.figure(figsize=(9, 6))
            for uc, label in zip(plot_list, label_list):
                plt.plot(
                    df_results[uc],
                    linestyle="-",
                    linewidth=1,
                    label=label,
                )

            plt.title("Region_{}".format(idx + 1))
            plt.ylabel("P in kW", fontsize=14, labelpad=20)
            plt.tick_params(direction="in", grid_alpha=0.5, labelsize=14, pad=10)
            plt.grid(True)
            plt.legend(fontsize=14)
            plt.gcf().autofmt_xdate()
            plt.tight_layout()
            plt.gca().set_xbound(simbev.start_date_input, simbev.end_date)
            figname = "region_{}".format(idx + 1)
            plt.savefig("{}/{}.png".format(simbev.save_directory, figname))

    if simbev.output_options["collective_plot"]:
        df_results = grid_timeseries_all.set_index("timestamp")

        plt.figure(figsize=(15, 9))
        for item, label in zip(plot_list, label_list):
            plt.plot(
                df_results[item],
                linestyle="-",
                linewidth=1,
                label=label,
            )

        plt.title("All Regions")
        plt.ylabel("P in kW", fontsize=14)
        plt.tick_params(direction="in", grid_alpha=0.5, labelsize=14, pad=10)
        plt.grid(True)
        plt.legend(fontsize=14)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.gca().set_xbound(simbev.start_date_input, simbev.end_date)
        figname = "region_all"
        plt.savefig("{}/{}.png".format(simbev.save_directory, figname))
