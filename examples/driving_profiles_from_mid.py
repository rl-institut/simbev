import json
import pathlib

import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'


def create_driving_profiles(number_of_dp, region_names, car_type_names):
    data_path = pathlib.Path("mid_data")
    way_cols = [0, 1, 2, 3, 4, 21, 28, 30, 35, 48, 53, 54, 58, 60, 67, 68, 94, 95, 163]
    way = pd.read_csv(
        pathlib.Path(data_path, "MiD2017_Wege.csv"),
        sep=";",
        decimal=",",
        usecols=way_cols,
    )

    # read MiD-Wege, required fields (see code plan for mid)
    # 0: HP_ID (Haushalts-Personen-ID)
    # 1: H_ID
    # 2: P_ID
    # 3: W_ID (Wege-ID)
    # 4: W_GEW Gewichtungsfaktor Wege
    # 17: W_RBW (regelmaessiger beruflicher Weg)
    # 19: ST_MONAT (Kalendermonat)
    # 21: ST_WOTAG (Wochentag)
    # 26: saison (Jahreszeit)
    # 28: W_SO1 (Startort 1. Weg 1: zu Hause, 2: anderer Ort, 9: keine Angabe, 701: bei rBW nicht erhoben, 809: ab 2. Weg nicht erhoben)
    # 30: W_SZ (Startzeit des Weges)
    # 35: W_AZ (Ankunftszeit des Weges)
    # 43: wegmin_imp1 (Wegedauer in Minuten, 1-480)
    # 53: WZWD_P (detaillierter Wegezweck private Erledigungen)
    # 54: WZWD_F (detaillierter Wegezweck Freizeit)
    # 48: zweck (Wegezweck. 1: Work, 2: business, 3: school, 4: shopping, 5: private, 6: ridesharing, 7: leisure, 8: home, 9: Rueckweg vom vorherigen Weg, 10: anderer Zweck, 99: keine Angabe)
    # 55: W_ZWD (detaillierter Wegezweck)
    # 58: wegkm_imp (Wegelaenge in km, 0,01 - 900)
    # 60: tempo (Geschwindigkeit 0,5 - 900, 9994 unplausibel, 9995 Wert nicht zu berechnen, 70701 bei rBW nicht zu bestimmen, 70703 Weg ohne Detailerfassung)
    # 67: W_VM_G (Verkehrsmittel - Pkw 0: nicht genannt, 1: genannt)
    # 68: W_VM_H (Verkehrsmittel - Carsharing 0: nicht genannt, 1: genannt)
    # 87: hvm_imp (Hauptverkehrsmittel - 1: zu Fuss, 2: Fahrrad, 3: MIV Mitfahrer, 4: MIV Fahrer, 5 OePV)
    # 94: W_AUTO_HH (Auto aus dem Haushalt - 1: ja, 2: nein, 9: keine Angabe, weitere Codes fuer Begruendung des Fehlens)
    # 95: W_WAUTO (A_ID des FAhrzeugs - 1: 1. Fahrzeug, 2: 2. Fahrzeug, 3: 3. Fahrzeug, 4: anderes Fahrzeug, 9: keine Angabe, weitere Codes fuer Begruendung des Fehlens)
    # 113: km_routing (geroutete Entfernung in Strassenkilometern)
    # 122: anzauto_gr1 (Anzahl Autos im Haushalt in Gruppen (0 bis 4+))
    # 163: RegioStaR7

    way["charging_use_case"] = ""

    uc_zwdp_retail = [503, 504, 601, 602, 603, 706, 714, 713]
    uc_zwdp_street = [701, 705, 711, 604, 715, 717, 999, 2020, 7704, 7705]

    uc_zwdf_retail = [503, 603, 702, 703, 704, 705, 706, 713, 714]
    uc_zwdf_street = [
        605,
        701,
        707,
        710,
        711,
        712,
        716,
        717,
        719,
        720,
        999,
        2202,
        7704,
        7705,
    ]

    way["charging_use_case"].loc[
        (way["W_ZWDP"].isin(uc_zwdp_street) & (way["zweck"] == 5))
        | (way["W_ZWDF"].isin(uc_zwdf_street) & (way["zweck"] == 7))
    ] = "street"
    way["charging_use_case"].loc[
        (way["W_ZWDP"].isin(uc_zwdp_retail) & (way["zweck"] == 5))
        | (way["W_ZWDF"].isin(uc_zwdf_retail) & (way["zweck"] == 7))
    ] = "retail"

    household_cols = [0, 1, 87, 97]
    households = pd.read_csv(
        pathlib.Path(data_path, "MiD2017_Haushalte.csv"),
        sep=";",
        decimal=",",
        usecols=household_cols,
    )

    households.head()

    person_cols = [0, 1, 3, 22]
    persons = pd.read_csv(
        pathlib.Path(data_path, "MiD2017_Personen.csv"),
        sep=";",
        decimal=",",
        usecols=person_cols,
    )
    persons.head()

    # group by H_ID and count number of unique ST_WOTAG values
    counts = persons.groupby("H_ID")["ST_WOTAG"].nunique()

    if (counts == 1).all():
        print("All ST_WOTAG values are the same for each H_ID")
    else:
        print("ST_WOTAG values are not always the same for the same H_ID")

    persons = persons.drop_duplicates(subset="HP_ID", keep="first")
    persons.head()

    households = households.join(persons.set_index("H_ID"), on="H_ID")
    households["ST_WOTAG"] -= 1
    way["ST_WOTAG"] -= 1
    households[["H_ID", "ST_WOTAG"]].tail()

    households["ST_WOTAG"].unique()

    way_distance_min = 0.1
    way_distance_max = 950.0

    speed_min = 1
    speed_max = 250

    # use wegkm_imp to avoid filtering out non-plausible distances

    # filter by only PKW (96 LIS vs 95 simbev)

    # filter by tempo: set_and_clean_tempo = find(raw_ways(:,61)==9994 | raw_ways(:,61)==9995 | raw_ways(:,61)==70701 | raw_ways(:,61)==70703 | raw_ways(:,61)>=settings.MiD_wege_max_v)

    # filter by ways with PKW/carsharing  => double filter for PKW?

    # fahrten mit fahrzeit = 0 raus filtern

    way_filtered = way.loc[
        (way["wegkm_imp"] >= way_distance_min)
        & (way["wegkm_imp"] <= way_distance_max)
        & ((way["W_VM_G"] == 1) | (way["W_VM_H"] == 1))
        & (way["tempo"] >= speed_min)
        & (way["tempo"] <= speed_max)
        & (way["W_SZ"].str.contains("^\d{1,2}:\d{2}:\d{2}$", regex=True))
        & (way["W_AZ"].str.contains("^\d{1,2}:\d{2}:\d{2}$", regex=True))
        & (way["zweck"] >= 1)
        & (way["zweck"] <= 10)
    ].copy()
    print("lenght_filterd", len(way_filtered))
    print("lenght_households", len(households))

    # fit zweck to simbev

    # private/ridesharing/anderer zweck zusammenfassen

    mid_zweck = range(1, 11)

    simbev_zweck = [
        "work",
        "business",
        "school",
        "shopping",
        "private",
        "private",
        "leisure",
        "home",
        "home",
        "private",
    ]

    zweck_dict = dict(zip(mid_zweck, simbev_zweck))

    way_filtered["zweck"] = way_filtered["zweck"].map(zweck_dict)
    way_filtered["zweck"].head()

    region_names = ["urban", "suburban", "rural"]
    regiostar7 = {
        "urban": [71, 72],
        "suburban": [73, 75, 76],
        "rural": [74, 77],
    }

    car_type_names = ["mini", "medium", "luxury"]
    kba_seg = {
        "mini": [1, 2],
        "medium": [3],
        "luxury": [4],
    }

    stats_names = ["number_of_households", "number_of_ways"]

    # creation of dicts
    driving_profile_dict = {}
    way_dict = {}
    household_dict = {}
    stats_dict = {}

    for region in region_names:
        driving_profile_dict[region] = {}
        way_dict[region] = {}
        household_dict[region] = {}
        stats_dict[region] = {}
        for car_type in car_type_names:
            driving_profile_dict[region][car_type] = None
            way_dict[region][car_type] = None
            household_dict[region][car_type] = None
            stats_dict[region][car_type] = {}
            for stat in stats_names:
                stats_dict[region][car_type][stat] = None

    # spalte 87 in HH-Datensatz "pkw_seg_kba"
    # spalte 97 in HH-Datensatz "RegioStaR7"

    # filter by region and car type, get 9 different data sets

    for region in region_names:
        for car_type in car_type_names:
            # print(region, car_type)
            # 1. find all households that mach region and car-type by region
            household_dict[region][car_type] = households.loc[
                households["RegioStaR7"].isin(regiostar7[region])
                & households["pkw_seg_kba"].isin(kba_seg[car_type])
            ].copy()
            stats_dict[region][car_type]["number_of_households"] = len(
                household_dict[region][car_type]["H_ID"].unique()
            )

            # 2. find all ways that are done by household
            way_dict[region][car_type] = way_filtered.loc[
                way_filtered["H_ID"].isin(household_dict[region][car_type]["H_ID"])
            ].copy()
            stats_dict[region][car_type]["number_of_ways"] = len(
                way_dict[region][car_type]
            )
            # print()

    def create_timestep_from_time(time_str):
        time_str_list = time_str.split(":")
        return int(time_str_list[0]) * 60 + int(time_str_list[1])

    for region in region_names:
        for car_type in car_type_names:
            way_dict[region][car_type]["departure_time"] = way_dict[region][car_type][
                "W_SZ"
            ].apply(create_timestep_from_time)
            way_dict[region][car_type]["arrival_time"] = way_dict[region][car_type][
                "W_AZ"
            ].apply(create_timestep_from_time)

    # choose H_ID out of Householdgroup by using weight column

    # check for households using weights

    def select_by_weight(df, column, weight):
        cumulative_weights = np.cumsum(df[weight])
        max_weight = cumulative_weights.iat[-1]

        # generate random number between 0 and max_weights
        random_num = np.random.uniform(0, max_weight)

        # select household by random number and cumulative_weights
        selected_df = df.iloc[(cumulative_weights > random_num).argmax()]

        # return household_id for further usage
        return selected_df[column]

    def select_randomly(df, column):
        selected_df = df.sample()
        return selected_df[column].iloc[0]

    # check choosen household for driving-events on given weekday
    def check_for_way(household_df, weekday, way_df):
        # households_df: all households with PkW in specific region and with specific car type
        household_df_weekday = household_df.loc[household_df["ST_WOTAG"] == weekday]
        # select households that have a maching "Stichtag"
        H_ID = select_randomly(household_df_weekday, "H_ID")

        # check for persons and persons with way
        unique_persons_with_way = way_df["HP_ID"].loc[(way_df["H_ID"] == H_ID)].unique()

        if unique_persons_with_way.size == 0:
            # If there is no persons with way in household write empty DataFrame
            specific_day = pd.DataFrame()
        else:
            # else check for person with way by weight
            HP_ID = select_randomly(
                household_df.loc[household_df["HP_ID"].isin(unique_persons_with_way)],
                "HP_ID",
            )
            # check if there is any connection to way dataframe
            specific_day = way_df.loc[(way_df["HP_ID"] == HP_ID)]

        return specific_day, (not specific_day.empty)

    # start with preperations for generating driving profiles
    dp_columns = [
        "id",
        "day",
        "location",
        "departure_time",
        "arrival_time",
        "distance",
        "charging_use_case",
    ]
    profile_columns = [
        "id",
        "ST_WOTAG",
        "zweck",
        "departure_time",
        "arrival_time",
        "wegkm_imp",
        "charging_use_case",
    ]

    new_column_dict = {key: value for key, value in zip(profile_columns, dp_columns)}

    days = 7

    # counters for identifying empty days
    day_counter = number_of_dp * len(region_names) * len(car_type_names) * days
    no_way_counter = 0

    for region in region_names:
        for car_type in car_type_names:
            driving_profiles = pd.DataFrame(columns=profile_columns)
            id_driving_profile = 0
            print("householdtype", region, car_type)
            for _ in range(number_of_dp):
                # start generating driving-profile for given household
                for weekday in range(days):
                    # check if day is empty
                    day_specific, ways_found = check_for_way(
                        household_dict[region][car_type],
                        weekday,
                        way_dict[region][car_type],
                    )
                    if not ways_found:
                        # skip day with no activities
                        no_way_counter += 1
                        continue

                    else:
                        # check for way
                        # todo: find proper methodology to connect events!
                        # fill day with activities
                        activity = day_specific.copy()
                        activity["id"] = id_driving_profile
                        activity = activity[profile_columns]
                        driving_profiles = pd.concat(
                            [driving_profiles, activity], ignore_index=True
                        )

                id_driving_profile += 1
            driving_profiles = driving_profiles.rename(columns=new_column_dict)

            driving_profile_dict[region][car_type] = driving_profiles

    share_of_empty_days = no_way_counter / day_counter
    stats_dict["share_of_empty_days"] = share_of_empty_days
    print("share of empty days", share_of_empty_days)

    save_dir = pathlib.Path("driving_profiles")
    save_dir.mkdir(exist_ok=True)

    for region in region_names:
        for car_type in car_type_names:
            # change datatypes
            driving_profile = driving_profile_dict[region][car_type]
            driving_profile["id"] = driving_profile["id"].astype("int32")
            driving_profile["day"] = driving_profile["day"].astype("int8")
            driving_profile["location"] = driving_profile["location"].astype("category")
            driving_profile["departure_time"] = driving_profile[
                "departure_time"
            ].astype("int16")
            driving_profile["arrival_time"] = driving_profile["arrival_time"].astype(
                "int16"
            )
            driving_profile["distance"] = driving_profile["distance"].astype("float32")

            # save to parquet
            driving_profile.to_parquet(
                pathlib.Path(save_dir, f"driving_profiles_{region}_{car_type}.gzip"),
                compression="gzip",
            )

            # save to csv
            # driving_profile.to_csv(pathlib.Path(save_dir, f'driving_profiles_{region}_{car_type}.csv'))

    # save statistics
    with open(f"stats.json", "w") as outfile:
        json.dump(stats_dict, outfile, indent=4)


if __name__ == "__main__":
    region_names = ["urban", "suburban", "rural"]
    car_type_names = ["mini", "medium", "luxury"]
    number_of_dp = 1000
    create_driving_profiles(number_of_dp, region_names, car_type_names)
