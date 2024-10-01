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
sys.path.append('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/scripts/exp_runners')
import ian_preston_threshold_runner as rn
# import ian_preston_rel_elev_runner as rn 
import numpy as np
import sounddevice as sd
from pathlib import Path 


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
BLOCK_LEN = 80

PART_IX = 14
EXP_DIR = Path("speaker_array_manifests")
PART_NAME = f"participant_{PART_IX:03d}"
EXP_TYPE = "thresholds_v02"  # Name of sub directory to save experiment results - should match dir of trial dicts!

EXPMT_TRIAL_DICT_NAME = f"{EXP_TYPE}/{PART_NAME}_pilot_trial_dict.pkl"

# params that could but usually shouldn't change 
EXPMT_TRIAL_DICT_DIR = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_spatial_word_recognition_thresholds/speaker_array_manifests")
EXPMT_TRIAL_DICT_PATH = EXPMT_TRIAL_DICT_DIR / EXPMT_TRIAL_DICT_NAME
# open trial manifest 
print(f"Running trial dict {EXPMT_TRIAL_DICT_PATH}")
with open(EXPMT_TRIAL_DICT_PATH, 'rb') as f:
    trial_dict = pickle.load(f)
    
# print(trial_dict)

# Set output data save path
output_dir = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_spatial_word_recognition_thresholds/data")
output_dir = output_dir / EXP_TYPE 
output_dir.mkdir(parents=True, exist_ok=True)
out_name = output_dir/ f"{PART_NAME}.csv"
# if out_name.exists():
#     raise FileExistsError("{out_name} already exists! Did you forget to update the participant number variable, PART_IX?")
    
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
        "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_spatial_word_recognition_thresholds/threshold_expmt.html"
    )

################################################
# Init main call/response fetching via websocket 
################################################

async def echo(websocket):
    global speaker_config
    global break_sound
    global break_soundsr
    global block_start_soundsr
    global block_start_sound
    global out_name

    async for message in websocket:
        data = json.loads(message)
        # print(f"got data from client: {data}")
        trial_ix = data.get("trial_ix", None)
        print(trial_ix)
        print('\n')
        if trial_ix != None:
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
                             dBA=DB_SPL)
        if data['action'] == 'store_data':
            exp_data = pd.DataFrame(json.loads(data['data']))
            exp_data.to_csv(out_name)
        ## lock data if done - buggy for now 
        # if trial_ix == len(trial_dict):
        #     os.chmod(out_name, 0o444) # sets permissions to read only
        #     file_stat = os.stat(out_name)
        #     file_permissions = oct(file_stat.st_mode)[-3:]
        #     print(f'{out_name} permissions set to {file_permissions}')
            
    return None

###############
# Launch Server 
###############

async def start_server():
    app = web.Application()
    app.add_routes([web.get("/", index), 
                    web.static("/jspsych/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/jspsych"),
                    web.static("/root/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_spatial_word_recognition_thresholds"),
                    web.static("/main/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/")])
    server = web.AppRunner(app)
    await server.setup()
    site = web.TCPSite(server, "mcdermottlab.local", 9091)
    await site.start()

    ws_server = websockets.serve(echo, "mcdermottlab.local", 8765, ping_interval=None)
    asyncio.ensure_future(ws_server)

    await asyncio.Future() # run forever
    return None 

if __name__ == "__main__":
    asyncio.run(start_server())
