import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import secrets

# Setup aplikasi dan logging
auth_app = FastAPI()
logging.basicConfig(level=logging.INFO)
app = auth_app

# Mount static assets
app.mount("/static", StaticFiles(directory="static"), name="static")
# Templates folder
templates = Jinja2Templates(directory="templates")

# Struktur data rooms: {code: {clients: [...], board: [...], turn: 'X'}}
rooms = {}

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request, "rooms": rooms.keys()})

@app.post("/admin/create")
async def create_room():
    code = secrets.token_hex(3)
    rooms[code] = {"clients": [], "board": [''] * 9, "turn": 'X'}
    logging.info(f"Room created: {code}")
    return JSONResponse({"code": code})

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def notify_status(room):
    data = {"type": "status", "players": len(room["clients"])}
    for client in room["clients"]:
        await client.send_json(data)

@app.websocket("/ws/{code}")
async def websocket_endpoint(websocket: WebSocket, code: str):
    logging.info(f"Incoming WS connection for room {code}")
    await websocket.accept()

    # Validasi room
    if code not in rooms:
        logging.warning(f"Room {code} not found")
        await websocket.send_json({"type": "error", "message": "Room not found"})
        await websocket.close()
        return

    room = rooms[code]
    # Batasi maksimal 2 pemain
    if len(room["clients"]) >= 2:
        logging.warning(f"Room {code} full")
        await websocket.send_json({"type": "error", "message": "Room full"})
        await websocket.close()
        return

    room["clients"].append(websocket)
    logging.info(f"Client joined room {code}, total: {len(room['clients'])}")
    # Kirim status ke semua pemain
    await notify_status(room)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "move":
                idx = data.get("index")
                # Validasi: kotak kosong & sudah ada 2 pemain
                if 0 <= idx < 9 and room["board"][idx] == '' and len(room["clients"]) == 2:
                    symbol = room["turn"]
                    room["board"][idx] = symbol
                    room["turn"] = 'O' if symbol == 'X' else 'X'
                    update = {"type": "update", "board": room["board"], "turn": room["turn"]}
                    for client in room["clients"]:
                        await client.send_json(update)
    except WebSocketDisconnect:
        logging.info(f"Client left room {code}")
        room["clients"].remove(websocket)
        if not room["clients"]:
            # Reset game saat semua pemain keluar
            room["board"] = [''] * 9
            room["turn"] = 'X'
            logging.info(f"Room {code} reset")