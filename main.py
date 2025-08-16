from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
import os
from time import time
from final_encoder import encode  
from final_decoder import decode
import struct

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def cleanup_files(paths: list):
    for path in paths:
        if os.path.exists(path):
            os.remove(path)

@app.post("/encode/")
async def encode_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):


    if not file.filename.endswith((".json", ".txt", ".png", ".jpg")):
        return {"error": "Unsupported file type."}


    
    file_bytes = await file.read()
    if len(file_bytes) > 2 * 1024 * 1024:
       return {"error": "File size exceeds 2MB limit."}

    

    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as f:
        f.write(file_bytes)

   
    output_filename = f"{int(time())}.chesscloud"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

   
    encode(input_path, output_path)

  
    background_tasks.add_task(cleanup_files, [input_path, output_path])

    
    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type="application/octet-stream"
    )


@app.post("/decode/")
async def decode_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):


    if not file.filename.endswith((".chesscloud")):
        return {"error": "Unsupported file type."}
    
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as f:
        f.write(await file.read())

    
    original_filename = "output"
    output_path = os.path.join(OUTPUT_DIR, original_filename)

    decode(input_path, output_path)

    
    for ext in ["txt", "json", "png", "jpg"]:
        candidate = output_path + f".{ext}"
        if os.path.exists(candidate):
            final_output_path = candidate
            break
    else:
        final_output_path = output_path  

    background_tasks.add_task(cleanup_files, [input_path, final_output_path])

    return FileResponse(
        path=final_output_path,
        filename=os.path.basename(final_output_path),
        media_type="application/octet-stream"
    )


# Route to get metadata about the chesscloud file 

@app.post("/getmetadata")

async def get_metadata(file : UploadFile = File(...), background_tasks: BackgroundTasks = None):


    if not file.filename.endswith((".chesscloud")):
        return {"error": "Unsupported file type."}

    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as f:
        f.write(await file.read())
    with open(input_path, "rb") as f:
       
        header = f.read(13)
        if len(header) != 13:
            raise ValueError("Corrupt file: header too short.")
        format_code, num_games, shortest_game_moves, longest_game_moves = struct.unpack(">BIII", header)
        length_bytes = f.read(4)
        if len(length_bytes) != 4:
            raise ValueError("Corrupt file: missing shortest-game length prefix.")
        shortest_game_len = struct.unpack(">I", length_bytes)[0]

        shortest_game_bytes = f.read(shortest_game_len)
        if len(shortest_game_bytes) != shortest_game_len:
            raise ValueError("Corrupt file: shortest-game section too short.")
        shortest_game_str = shortest_game_bytes.decode("utf-8")
        shortest_game_moves_list = shortest_game_str.split() if shortest_game_str else []
        padding_b = f.read(1)
        if len(padding_b) != 1:
            raise ValueError("Corrupt file: missing padding byte.")





    background_tasks.add_task(cleanup_files, [input_path])

    return {"metadata": {
        "numgames": num_games,
        "shortest_game": shortest_game_moves,
        "longest_game": longest_game_moves,
        "shortest_game_moves": shortest_game_moves_list
    }}


# File types supported check  
# No files greater then 2 MB
# And clearing the uploads directory after sending it.