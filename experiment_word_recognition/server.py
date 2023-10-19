from aiohttp import web
import websockets
import asyncio
import json
import pickle 
import pandas as pd 

# open trial manifest 
with open("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/experiment_pilot_manifest_trial_dict.pkl", 'rb') as f:
    trial_dict = pickle.load(f)

async def index(request):
    return web.FileResponse(
        "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition/spkrm_attn_expmt.html"
    )
    
async def echo(websocket):
    async for message in websocket:
        data = json.loads(message)
        print(f"got data from client: {data}")
        if data.get("trial_ix", None) != None:
            print(trial_dict[data.get("trial_ix")], '\n')
        elif data.get("data", False):
            print(data.get("data"))
    
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
