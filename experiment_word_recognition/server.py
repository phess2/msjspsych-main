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

# open trial manifest 
with open("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/experiment_pilot_manifest_trial_dict.pkl", 'rb') as f:
    trial_dict = pickle.load(f)

dev = speaker_utils.set_DAC()
speaker_config = speaker_utils.create_speaker_config('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/Layouts/NewSpeakerLayoutUpdate.csv')
print(f"{dev=}")
if dev == "16A":
    asyncio.run(speaker_utils.force_unroute_all(speaker_config))

break_soundsr, break_sound = wavfile.read('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/sounds/bell-ringing-04.wav')
block_start_soundsr, block_start_sound = wavfile.read('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/sounds/beep-01a.wav')
break_sound = speaker_utils.rms_norm(break_sound, 60)
block_start_sound = speaker_utils.rms_norm(block_start_sound, 60)

async def index(request):
    return web.FileResponse(
        "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition/spkrm_attn_expmt.html"
    )
    
async def echo(websocket):
    global speaker_config
    global break_sound
    global break_soundsr
    global block_start_soundsr
    global block_start_sound
    async for message in websocket:
        data = json.loads(message)
        # print(f"got data from client: {data}")
        print(data)
        trial_ix = data.get("trial_ix", None)
        print(trial_ix)
        print('\n')
        if trial_ix != None:
            trial_data = trial_dict[trial_ix]
            await rn.run_exp(trial_ix, trial_data, speaker_config, break_sound, break_soundsr, block_start_sound, block_start_soundsr, block_length=90)


        # elif data.get("data", False):
        #     print(data.get("data"))
            
    
async def start_server():
    app = web.Application()
    app.add_routes([web.get("/", index), 
                    web.static("/jspsych/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/jspsych"),
                    web.static("/root/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition"),#])
                    web.static("/main/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/")])
    server = web.AppRunner(app)
    await server.setup()
    site = web.TCPSite(server, "mcdermottlab.local", 9090)
    await site.start()

    ws_server = websockets.serve(echo, "mcdermottlab.local", 8765)
    asyncio.ensure_future(ws_server)
    
    await asyncio.Future() # run forever
    


if __name__ == "__main__":
    asyncio.run(start_server())
