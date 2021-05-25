import pandas as pd
import numpy as np
from dataset_failtimes import BeatmapSamples

## for repeat_count, duration, d_time
def CREATE_ARRAY_FOR_MODEL(colname, df, failtimes_rowindex_within_interval):
    col_for_model = []
    for interval in failtimes_rowindex_within_interval:
        col_for_one_interval = -1
        if len(interval) > 0:
            col_for_one_interval = 0
            for i in interval:
                col_for_one_interval += df.iloc[i,][colname]
            ## we take the average for d_time. we take the sum for other columnss
            if (colname == "d_time"):
                col_for_one_interval = col_for_one_interval / len(interval)
        else:
            col_for_one_interval = 0 # NaN
        col_for_model.append(col_for_one_interval)
    return col_for_model

# for coordinates distance (x,y,x1,y1)
def CREATE_COORDINATES_DIST_ARRAY_FOR_MODEL(df, failtimes_rowindex_within_interval):
    col_for_model = []
    for interval in failtimes_rowindex_within_interval:
        col_for_one_interval = -1
        if len(interval) > 0:
            col_for_one_interval = 0
            for i in interval:
                x = df.iloc[i,]["x"]
                y = df.iloc[i,]["y"]
                x1 = df.iloc[i,]["x1"]
                y1 = df.iloc[i,]["y1"]
                col_for_one_interval += np.sqrt((x1 - x) ** 2 + (y1 - y) ** 2)
        else:
            col_for_one_interval = 0 # NaN
        col_for_model.append(col_for_one_interval)
    return col_for_model

def CREATE_EASY_DF(new_beatmaps, hit_objects_colnames):
    # creating the easy data frame
    repeat_count_for_model = []
    duration_for_model = []
    d_time_for_model = []
    coord_dist_for_model = []
    fail_times_for_model = []
    fail_times_for_model_norm = []
    time_for_model = []

    for i in range(len(new_beatmaps)):

        # saving arrays into a data frame
        df = pd.DataFrame(new_beatmaps[i]["mlpp"]["hit_objects"], 
                      columns = hit_objects_colnames)

        # calculating time interval
        interval = df["time"].iloc[-1]/100
        # creating time array
        time = np.linspace(interval, df["time"].iloc[-1], 100)

        # putting hit objects into timeslot
        failtimes_rowindex_within_interval = []
        lowerBound = 0

        # creating arrays
        for j in np.arange(0, len(time)):
            upperBound = time[j]
            failtimes_rowindex_for_one_interval = []
            for k in np.arange(0, len(df["time"])):
                if df["time"][k] >= lowerBound and df["time"][k] < upperBound:
                    failtimes_rowindex_for_one_interval.append(k)
            failtimes_rowindex_within_interval.append(failtimes_rowindex_for_one_interval)
            lowerBound = upperBound

        time_for_model.extend(time)
        fail_times_for_model.extend(new_beatmaps[i]["mlpp"]["fail"])
        fail_times_for_model_norm.extend([failtime/new_beatmaps[i]["playcount"] for failtime in new_beatmaps[i]["mlpp"]["fail"]])
        coord_dist_for_model.extend(CREATE_COORDINATES_DIST_ARRAY_FOR_MODEL(df, failtimes_rowindex_within_interval))
        repeat_count_for_model.extend(CREATE_ARRAY_FOR_MODEL("repeat_count", df, failtimes_rowindex_within_interval))
        duration_for_model.extend(CREATE_ARRAY_FOR_MODEL("duration", df, failtimes_rowindex_within_interval))
        d_time_for_model.extend(CREATE_ARRAY_FOR_MODEL("d_time", df, failtimes_rowindex_within_interval))

    easy_df = pd.DataFrame({'time': time_for_model, 'failtimes': fail_times_for_model, 
                            'failtimes_norm': fail_times_for_model_norm, 'coord_dist_sum': coord_dist_for_model, 
                           'repeat_count_sum': repeat_count_for_model, 'duration_sum': duration_for_model, 
                           'd_time_avg': d_time_for_model})
    return easy_df

def CREATE_PARTITION_DF(new_beatmaps, easy_df, min_size):
    # for all beatmaps
    failtimes_norm_array = []
    coord_dist_sum_array = []
    repeat_count_sum_array = []
    duration_sum_array = []
    d_time_avg_array = []
    partition_all_df = pd.DataFrame()

    for j in range(len(new_beatmaps)):
        partition_j = BeatmapSamples.partition(new_beatmaps[j], min_size)
        partition_j_df = pd.DataFrame(partition_j,columns=['num_hit_objects', 'chunks'])

        failtimes_norm_list = list(easy_df.iloc[(j*100):((j+1)*100)]['failtimes_norm'])
        coord_dist_sum_list = list(easy_df.iloc[(j*100):((j+1)*100)]['coord_dist_sum'])
        repeat_count_sum_list = list(easy_df.iloc[(j*100):((j+1)*100)]['repeat_count_sum'])
        duration_sum_list = list(easy_df.iloc[(j*100):((j+1)*100)]['duration_sum'])
        d_time_avg_list = list(easy_df.iloc[(j*100):((j+1)*100)]['d_time_avg'])

        for i in partition_j_df['chunks']:
            failtimes_norm_array.append(sum(failtimes_norm_list[0:i]))
            del failtimes_norm_list[0:i]
            coord_dist_sum_array.append(sum(coord_dist_sum_list[0:i]))
            del coord_dist_sum_list[0:i]
            repeat_count_sum_array.append(sum(repeat_count_sum_list[0:i]))
            del repeat_count_sum_list[0:i]
            duration_sum_array.append(sum(duration_sum_list[0:i]))
            del duration_sum_list[0:i]
            d_time_avg_array.append(sum(d_time_avg_list[0:i])/len(d_time_avg_list[0:i]))
            del d_time_avg_list[0:i]

        partition_all_df = pd.concat([partition_all_df, partition_j_df])

    partition_all_df['failtimes_norm_sum'] = pd.DataFrame(failtimes_norm_array)
    partition_all_df['coord_dist_sum_sum'] = pd.DataFrame(coord_dist_sum_array)
    partition_all_df['repeat_count_sum_sum'] = pd.DataFrame(repeat_count_sum_array)
    partition_all_df['duration_sum_sum'] = pd.DataFrame(duration_sum_array)
    partition_all_df['d_time_avg_avg'] = pd.DataFrame(d_time_avg_array)

    return partition_all_df