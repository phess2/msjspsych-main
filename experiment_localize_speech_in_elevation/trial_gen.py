import random
from copy import deepcopy
import pickle
import pandas as pd 
import numpy as np 
import itertools 
from pathlib import Path

def loc_to_label(loc):
    azim, elev = loc
    elev_string_map = {40:'A', 30:'B', 20:'C', 10:'D', 0:'E', -10:'F', -20:'G'}
    return elev_string_map[elev] + str(int((azim + 100) / 10))

def sample_df(df, group, cond1, cond2, n):
    df_1 = df[df[f'{group}'] == cond1]
    df_2 = df[df[f'{group}'] == cond2]
    df_1_sample = df_1.sample(n=n)
    df_2_sample = df_2[~df_2.word.isin(df_1_sample.word)].sample(n=n, replace=True)
    # keep original ixs to track metadata in analysis scripts 
    df_1_sample = df_1_sample.reset_index()
    df_1_sample.rename(columns={'index':'full_df_index'}, inplace=True)
    df_2_sample = df_2_sample.reset_index()
    df_2_sample.rename(columns={'index':'full_df_index'}, inplace=True)
    return pd.concat([df_1_sample, df_2_sample], axis=0, ignore_index=True)

def get_subset_df(df, n_words=480):
    n_to_samp = n_words // 4
    female_df = sample_df(df[df.gender == 'female'], 'sex_cond', 'same', 'different',n_to_samp)
    male_df = sample_df(df[(df.gender == 'male') & (~df.word.isin(female_df.word))], 'sex_cond', 'same', 'different', n_to_samp)
    return pd.concat([female_df, male_df], axis=0, ignore_index=True)

# get target key list 

SNR = 0 
def create_new_experiment(num_elev_trials=1,
                          num_azim_trials=1):
    target_elevs = np.arange(-20,41,10)
    distractor_deltas = [None, 10, 30, 60]
    target_dist_elev_delta_pairs = list(itertools.product(*[target_elevs, distractor_deltas]))

    elev_trials = []
    for target_elev, dist_delta in target_dist_elev_delta_pairs:
            # print(dist_delta)
        for n in range(num_elev_trials):
            if dist_delta:
                if target_elev == -20:
                    dist_elev = dist_delta + target_elev
                elif target_elev == 40:
                    dist_elev = target_elev - dist_delta 
                else:
                    direction = 1 if n % 2 else -1 
                    # print('\t',  (dist_delta * direction))
                    dist_elev = target_elev + (dist_delta * direction)
                    if dist_elev < -20:
                        dist_elev = target_elev + dist_delta 
                    elif dist_elev > 40:
                        dist_elev = target_elev - dist_delta 
                if dist_elev < -20 or dist_elev > 40:
                    continue
                elev_trials.append(([(0, 0), (0,target_elev)], (0,dist_elev), 0, dist_delta, SNR))
            else:
                elev_trials.append(([(0, 0), (0,target_elev)], None, 0, None, SNR))

    ## Azimuth trials for main experiment:
    target_azims = np.arange(-90,91,10)
    target_dist_azim_delta_pairs = list(itertools.product(*[target_azims, distractor_deltas]) )

    azim_trials = []
    for target_azim, dist_delta in target_dist_azim_delta_pairs:
            # print(dist_delta)
        for n in range(num_azim_trials):
            if dist_delta:
                if target_azim == -90:
                    dist_azim = dist_delta + target_azim
                elif target_elev == 90:
                    dist_azim = target_azim - dist_delta 
                else:
                    direction = 1 if n % 2 else -1 
                    # print('\t',  (dist_delta * direction))
                    dist_azim = target_azim + (dist_delta * direction)
                    if dist_azim < -90:
                        dist_azim = target_azim + dist_delta 
                    elif dist_azim > 90:
                        dist_azim = target_azim - dist_delta 
                if dist_azim < -90 or dist_azim > 90:
                    continue
                # structure is cue loc, target loc, dist loc, azim delta, elev delta, SNR 
                azim_trials.append(([(0, 0), (target_azim, 0)], (dist_azim, 0), dist_delta, 0, SNR))
            else:
                # structure is cue loc, target loc, dist loc, azim delta, elev delta, SNR 
                azim_trials.append(([(0, 0), (target_azim,0 )], None, 0, None, SNR))
            
    all_trials = elev_trials + azim_trials 

    np.random.shuffle(all_trials)

    n_total_trials = len(all_trials)
    print(f"Generating {n_total_trials} trials")

    path_to_sounds = Path('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_spatial_word_recognition_thresholds/threshold_sounds/sounds')
    target_dir = list((path_to_sounds / 'target_excerpts').glob("*.wav"))
    distractor_dir = list((path_to_sounds / 'distractor_excerpts').glob("*.wav"))
    cue_dir = list((path_to_sounds / 'cue_excerpts').glob("*.wav"))

    full_df = pd.read_pickle('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_spatial_word_recognition_thresholds/full_cue_target_distractor_df_w_meta.pdpkl')
    full_df = full_df[~full_df.client_id.str.contains('bowie|1906-cc|laurahale')] # cull examples that made it through screening 
    if n_total_trials % 4 != 0:
        n_to_draw = n_total_trials + (n_total_trials % 4) ## need to draw n samples divisible by 4
    else:
        n_to_draw = n_total_trials
        
    participant_trial_stim_df = get_subset_df(full_df, n_words=n_to_draw).sample(frac=1.0)
    ## just need trial indices to get audio. Will match full_df_index string to ix number from participant_trial_df
    participant_stim_ixs = participant_trial_stim_df.full_df_index.to_list() 
    i = 0
    array_manifest = []
    for j, trial in enumerate(all_trials):
        trial_idx = participant_stim_ixs[i]
        i += 1
        ix_pattern = f"full_df_ix_{trial_idx:04}"
        ## Match ix pattern to file paths in cue, target, and distractor directories 
        cue_src_fn = [path for path in cue_dir if ix_pattern in path.stem]
        target_src_fn = [path for path in target_dir if ix_pattern in path.stem]
        # will get to distractors - only keep one for elevation trials 
        distractor_src_fn = [path for path in distractor_dir if ix_pattern in path.stem]
        if trial[1] is None:
            distractor_src_fn = None
        array_manifest.append((trial[0], trial[1], trial[4], cue_src_fn, target_src_fn, distractor_src_fn))

    experiment_data = dict()

    for j, trial in enumerate(all_trials):
        # dist_loc
        experiment_data[f'trial_{j}'] = {'target_loc': trial[0][1],
                                    'distractor_loc': trial[1],
                                    'azim_delta': trial[2],
                                    'elev_delta': trial[3],
                                    'snr': trial[4],
                                    'target_speaker_label':loc_to_label(trial[0][1]),
                                    'distractor_speaker_label':loc_to_label(trial[1]) if trial[1] else None,
                                    }
        
    trial_dict = {i:vals for i,vals in enumerate(array_manifest)}
    return experiment_data, array_manifest, trial_dict


def init_participant_stimuli(exp_type: str = "localize_speech_in_elevation_w_distractor_v00",
                             n_per_elev: int = 10,
                             n_per_azim: int = 4, 
                             ):
    # write out manifests 
    # Name of sub directory to save experiment results - should match dir of trial dicts!
    out_dir = Path(f'speaker_array_manifests/{exp_type}')
    exp_key_dir = Path(f'experiment_keys/{exp_type}')
    out_dir.mkdir(exist_ok=True, parents=True)
    exp_key_dir.mkdir(exist_ok=True, parents=True)
    n_files = len(list(out_dir.glob('*manifest.pkl')))

    part_ix = n_files+1

    np.random.seed(part_ix) # change seed for each participant!!!! 

    n_per_elev = 10
    n_per_azim = 4
    experiment, array_manifest, trial_dict = create_new_experiment(num_elev_trials=n_per_elev,
                                                                num_azim_trials=n_per_azim
                                                                )

    print(f"{len(trial_dict)} total trials")
    PART_NAME = f"participant_{n_files+1:03d}"
    print(PART_NAME)

    # meta will include speaker label 
    with open(out_dir / f'{PART_NAME}_pilot_meta.pkl', 'wb') as f:
        pickle.dump(experiment, f)

    with open(out_dir / f'{PART_NAME}_pilot_array_manifest.pkl', 'wb') as f:
        pickle.dump(array_manifest, f)

    with open(out_dir / f'{PART_NAME}_pilot_trial_dict.pkl', 'wb') as f:
        pickle.dump(trial_dict, f)
    
    return part_ix, experiment, array_manifest, trial_dict
