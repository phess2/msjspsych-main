from aiohttp import web
import websockets
import asyncio
import json
import pickle
from scipy.io import wavfile
import pandas as pd 
import sys
sys.path.append('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/src')
from utils import speaker_utils
sys.path.append('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/scripts/exp_runners')
import ian_preston_new_min_runner as rn 
import numpy as np
import sounddevice as sd
from pathlib import Path 

# TODO: Fix bug where mixtures don't play 
# Check rn.run_exp to make sure target + mixture made correctly 

"""
Before running, make a new manifest and trial dict using `gen_participant_trials.ipynb`
Then proceed with launching server

Checklist of changes to make to this file to run a new participant:
1. Update PART_IX to match new manifest you just generated.
2. ensure experiment paths are correct (are you piloting? Is this the main run?)
3. Source correct work answer key in `spkrm_attn_expmt.html`:
    1. change key path:
    <script src="../root/expmt_keys/participant_<ix>_key.js"></script>
    2. update number for trials to match:
        n_trials = <num_trials> 
        
"""

##################################
# SET EXPERIMENT PARAMS AND VARS
##################################
DB_SPL = 65
BLOCK_LEN = 35 # 35 for v01 and old expmnts 28 for v00 relative dist exp. 

PART_IX = 6
EXP_DIR = Path("speaker_array_manifests")
PART_NAME = f"participant_{PART_IX:03d}"
EXP_TYPE = "pilot_rel_dist_azim_elev_v01"  # Name of sub directory to save experiment results - should match dir of trial dicts!

EXPMT_TRIAL_DICT_NAME = f"{EXP_TYPE}/{PART_NAME}_pilot_trial_dict.pkl"

# params that could but usually shouldn't change 
EXPMT_TRIAL_DICT_DIR = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition/speaker_array_manifests")
EXPMT_TRIAL_DICT_PATH = EXPMT_TRIAL_DICT_DIR / EXPMT_TRIAL_DICT_NAME
# open trial manifest 
print(f"Running trial dict {EXPMT_TRIAL_DICT_PATH}")
with open(EXPMT_TRIAL_DICT_PATH, 'rb') as f:
    trial_dict = pickle.load(f)

# Set output data save path
output_dir = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition/data")
output_dir = output_dir / EXP_TYPE 
output_dir.mkdir(parents=True, exist_ok=True)
out_name = output_dir/ f"{PART_NAME}.csv"
    
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
break_sound = speaker_utils.rms_norm(break_sound, DB_SPL)
block_start_sound = speaker_utils.rms_norm(block_start_sound, DB_SPL)

#################
# Init html paths
#################

async def index(request):
    return web.FileResponse(
        "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition/spkrm_attn_expmt.html"
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
                             block_length=BLOCK_LEN)
        if data['action'] == 'store_data':
            exp_data = pd.DataFrame(json.loads(data['data']))
            exp_data.to_csv(out_name)
    return None

###############
# Launch Server 
###############

async def start_server():
    app = web.Application()
    app.add_routes([web.get("/", index), 
                    web.static("/jspsych/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/jspsych"),
                    web.static("/root/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition"),
                    web.static("/main/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/")])
    server = web.AppRunner(app)
    await server.setup()
    site = web.TCPSite(server, "mcdermottlab.local", 9090)
    await site.start()

    ws_server = websockets.serve(echo, "mcdermottlab.local", 8765, ping_interval=None)
    asyncio.ensure_future(ws_server)

    await asyncio.Future() # run forever
    
if __name__ == "__main__":
    asyncio.run(start_server())
