import matplotlib.pyplot as plt


def plot_gridtimeseries_by_usecase(simbev, grid_timeseries_all):
    # TODO fix plot first region outputs all regions data (log_region_data)
    if simbev.plot_options["by_region"]:
        for idx, data in enumerate(simbev.grid_data_list):
            df_results = data.set_index('timestamp')

            plt.figure(figsize=(15, 9))

            plt.plot(df_results['home_total_power'], color='#FF5F00', linestyle='-', linewidth=1, label='home')
            plt.plot(df_results['work_total_power'], color='#0082D1', linestyle='-', linewidth=1, label='work')
            plt.plot(df_results['public_total_power'], color='#AFAFAF', linestyle='-', linewidth=1, label='public')
            plt.plot(df_results['hpc_total_power'], color='#76B900', linestyle='-', linewidth=1, label='hpc')

            plt.title('Region_{}'.format(idx+1))
            plt.ylabel("P in kW", fontsize=14)
            plt.tick_params(direction='in', grid_alpha=0.5, labelsize=14, pad=10)
            plt.grid(True)
            plt.legend(fontsize=14)
            plt.gcf().autofmt_xdate()
            plt.tight_layout()
            plt.gca().set_xbound(simbev.start_date_input, simbev.end_date)
            figname = "region_{}".format(idx+1)
            plt.savefig('{}/{}.png'.format(simbev.save_directory, figname))

    if simbev.plot_options["all_in_one"]:
        df_results = grid_timeseries_all.set_index('timestamp')

        plt.figure(figsize=(15, 9))

        plt.plot(df_results['home_total_power'], color='#FF5F00', linestyle='-', linewidth=1, label='home')
        plt.plot(df_results['work_total_power'], color='#0082D1', linestyle='-', linewidth=1, label='work')
        plt.plot(df_results['public_total_power'], color='#AFAFAF', linestyle='-', linewidth=1, label='public')
        plt.plot(df_results['hpc_total_power'], color='#76B900', linestyle='-', linewidth=1, label='hpc')

        plt.title('All Regions')
        plt.ylabel("P in kW", fontsize=14)
        plt.tick_params(direction='in', grid_alpha=0.5, labelsize=14, pad=10)
        plt.grid(True)
        plt.legend(fontsize=14)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.gca().set_xbound(simbev.start_date_input, simbev.end_date)
        figname = "region_all"
        plt.savefig('{}/{}.png'.format(simbev.save_directory, figname))
