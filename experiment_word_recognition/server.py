from aiohttp import web
import websockets
import asyncio
import json

async def index(request):
    return web.FileResponse(
        "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition/index3.html"
        # "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/min_eg.html"
    )
    
async def echo(websocket):
    async for message in websocket:
        data = json.loads(message)
        print(f"got data from client: {data}")
        
        if data.get("action", None) != None:
            # wordResponse = data['response']
            print(data["action"])
        else:
        
            await websocket.send(message)
    
async def start_server():
    app = web.Application()
    app.add_routes([web.get("/", index), 
                    web.static("/jspsych/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/jspsych"),
                    web.static("/root/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_word_recognition"),#])
                    web.static("/main/", "/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/")])
    server = web.AppRunner(app)
    await server.setup()
    site = web.TCPSite(server, "mcdermottlab.local", 2090)
    await site.start()

    ws_server = websockets.serve(echo, "mcdermottlab.local", 8765)
    asyncio.ensure_future(ws_server)
    
    await asyncio.Future() # run forever


if __name__ == "__main__":
    asyncio.run(start_server())
