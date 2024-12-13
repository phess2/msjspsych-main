from aiohttp import web
import websockets
import asyncio
import json
import pickle
from scipy.io import wavfile
import pandas as pd 
import sys
import os 
sys.path.append('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/src')
from utils import speaker_utils
import numpy as np
import sounddevice as sd
from pathlib import Path 
import trial_gen 
import speech_localization_runner as rn 

"""
Before running, make a new manifest and trial dict using `gen_participant_trials.ipynb`
Then proceed with launching server

Checklist of changes to make to this file to run a new participant:
1. Update PART_IX to match new manifest you just generated.
2. ensure experiment paths are correct (are you piloting? Is this the main run?)
3. Source correct work answer key in `spkrm_attn_expmt.html`:
    1. change key path:k
    <script src="../root/expmt_keys/participant_<ix>_key.js"></script>
    2. update number for trials to match:
        n_trials = <num_trials> 
        
"""

##################################
# SET EXPERIMENT PARAMS AND VARS
##################################
DB_SPL = 65
DB_SPL_SPEAKER_WAKE = 40
BLOCK_LEN = 89 # 35 for v01 and old expmnts 28 for v00 relative dist exp. 

EXP_DIR = Path("speaker_array_manifests")
EXP_TYPE = "localize_speech_in_elevation_w_distractor_v01"  # Name of sub directory to save experiment results - should match dir of trial dicts!



#################################
# Get participant data 
################################
PART_IX, experiment_data, array_manifest, trial_dict = trial_gen.init_participant_stimuli(exp_type=EXP_TYPE)
PART_NAME = f"participant_{PART_IX:03d}"
print(f"{len(trial_dict)=}")
# Set output data save path
OUTPUT_DIR = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_localize_speech_in_elevation/data")
OUTPUT_DIR = OUTPUT_DIR / EXP_TYPE
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
out_name = OUTPUT_DIR / f'{PART_NAME}.json'

if out_name.exists():
    raise FileExistsError("{out_name} already exists! Did you forget to update the participant number variable, PART_IX?")
    
###################
# Set up speaker IO
################### 
dev = speaker_utils.set_DAC()
speaker_config = speaker_utils.create_speaker_config('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/Layouts/NewSpeakerLayoutUpdate.csv')
print(f"{dev=}")
if dev == "16A":
    asyncio.run(speaker_utils.force_unroute_all(speaker_config))
    
# set break and block sound paths and levels 
break_soundsr, break_sound = wavfile.read('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/sounds/three_tone.wav')
block_start_soundsr, block_start_sound = wavfile.read('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/sounds/beep-01a.wav')
break_sound = speaker_utils.set_dba_level(break_sound, DB_SPL)
block_start_sound = speaker_utils.set_dba_level(block_start_sound, DB_SPL)

#################
# Init html paths
#################

async def index(request):
    return web.FileResponse(
            "array_display_interface.html"
    )

################################################
# Init main call/response fetching via websocket 
################################################

def construct_spkr_disable_list(loc, mode, map_loc_to_name, map_name_to_loc):
    # there cannot be an "else" clause as these are the only two input options
    gt_spkr_name =  map_loc_to_name[loc]
    all_spkrs = list(set(map_name_to_loc.keys()))
    if mode == 'azim':
        list_name_disabled = [x for x in all_spkrs if gt_spkr_name[0] not in x]
    elif mode == 'elev':
        list_name_disabled = [x for x in all_spkrs if gt_spkr_name[1:]==x]
    return list_name_disabled

async def run_experiment(websocket):
    global speaker_config
    global break_sound
    global break_soundsr
    global block_start_soundsr
    global block_start_sound
    global out_name
    
    fn_config = "/Users/mcdermottspeakerarray/user/lakshmi/speaker_array/assets/speaker_config.csv"
    df_speaker_config = pd.read_csv(fn_config)
    speaker_config = {}
    for _itr in range(len(df_speaker_config)):
        dfi = df_speaker_config.iloc[_itr]
        speaker_config[(dfi["Azimuth"], dfi["Elevation"])] = {
            "device": dfi["Device"],
            "url": dfi["DeviceURL"],
            "channel": dfi["Channel"],
            "ibank": dfi["InputBank"],
        }
    map_name_to_loc = {}
    map_loc_to_name = {}
    for azim, elev in speaker_config.keys():
        row = "ABCDEFG"[(40 - elev) // 10]
        col = (azim + 90) // 10 + 1
        name = f"{row}{col}"
        map_name_to_loc[name] = (azim, elev)
        map_loc_to_name[(azim, elev)] = name
        
    list_loc = [(azim, elev) for (azim, elev) in speaker_config.keys()]
    list_response_allowed = [map_loc_to_name[_] for _ in list_loc]
    assert len(list_loc) == 133
    list_name_disabled = list(set(map_name_to_loc.keys()).difference(list_response_allowed))
    
    trial_ix = 0 
    
    hits = 0
    speaker_array_prepared = False
    df_responses = []
    async for message in websocket:
        data = json.loads(message)
        print(data)
        response = data.get("response", "")
        id = data.get("id", "")
        
        print(trial_ix)
        print('\n')
        if not speaker_array_prepared:
            await websocket.send(
                json.dumps(
                    {
                        "message": "Press here to start next trial",
                        "disabled": True,
                    }
                )
            )
            # prime the participant for the next trial!
            # loc = trial_dict[trial_ix]['target_loc']
            # list_name_disabled = construct_spkr_disable_list(loc, mode, map_loc_to_name, map_name_to_loc)    
            await rn.recolor_speaker_grid(websocket, [])
            speaker_array_prepared = True

        elif "start" in response.lower():
        # if trial_ix != None:
            trial_data = trial_dict[trial_ix]
            print(f"trial data: \n {trial_data}")
            await rn.run_exp(trial_ix,
                             trial_data,
                             speaker_config,
                             break_sound,
                             break_soundsr,
                             block_start_sound,
                             block_start_soundsr,
                             block_length=BLOCK_LEN,
                             dBA=DB_SPL,
                             DB_SPL_SPEAKER_WAKE=DB_SPL_SPEAKER_WAKE)
            await rn.reset_speaker_grid(websocket, [])
            print(trial_data)

        elif 'submit' in id:
            # record participant's response
            resp = {
                'trial': trial_ix,
                'resp_loc': data.get('select_loc'),
                'gt_info': trial_data,
                'true_loc':experiment_data[f'trial_{trial_ix}']['target_speaker_label']
            } 
            df_responses.append(resp)
            exp_data = pd.DataFrame.from_records(df_responses)
            exp_data.to_csv(out_name)
            
            # compute hits for display str: strings same or not? 
            hits += int(resp['resp_loc'] == resp['true_loc'])
            trial_ix += 1 
            acc_str = f"{(hits / trial_ix)*100}"
            
            
            if trial_ix >= len(trial_dict):
                await websocket.send(
                    json.dumps({
                            ## message that also provides feedback!
                            "message": f"Trials completed: {trial_ix}/{len(trial_dict)} | Total score: {acc_str}%"
                        })
                )
                print('Overall accuracy: {}'.format(acc_str))
                return

            elif trial_ix % BLOCK_LEN == 0:
                # pause on break
                await websocket.send(
                    json.dumps({
                            "message": f"Trials completed: {trial_ix} of {len(trial_dict)}. Break time! Hit this button when you're ready.",
                            "disabled": True,
                        })
                )
                speaker_array_prepared = False
            else:
                await rn.recolor_speaker_grid(websocket, [])

                await websocket.send(
                    json.dumps(
                        {
                            "message": f"Press here to start next trial | Trials completed: {trial_ix}/{len(trial_dict)} | Current score: {acc_str}%",
                            "disabled": True,
                        }
                    )
                )
        else:
            if not data.get('id', '') == 'start':
                await websocket.send(
                    json.dumps(
                        {
                            "alert": f"Invalid response: {response}",
                        }
                    )
                )

    return None


###############
# Launch Server 
###############

async def start_server():
    app = web.Application()
    app.add_routes([web.get("/", index), 
                    web.static("/jspsych/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/jspsych"),
                    web.static("/root/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_localize_speech_in_elevation"),
                    web.static("/main/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/")])
    server = web.AppRunner(app)
    await server.setup()
    site = web.TCPSite(server, "mcdermottlab.local", 9092)
    await site.start()

    ws_server = websockets.serve(run_experiment, "mcdermottlab.local", 8765, ping_interval=None)
    asyncio.ensure_future(ws_server)

    await asyncio.Future() # run forever
    return None 

if __name__ == "__main__":
    asyncio.run(start_server())
