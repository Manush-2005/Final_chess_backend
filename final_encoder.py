


import chess
from math import log2
import struct
import os

FILE_TYPES = {
    "txt": 1,
    "json": 2,
    "png": 3,
    "jpg": 4
}

def encode(file_path: str, output_path: str):
    # 1. Read file
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Detect file extension
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext not in FILE_TYPES:
        raise ValueError(f"Unsupported file type: {ext}")
    format_code = FILE_TYPES[ext]

    # 2. Convert to bit string
    file_bits = "".join(f"{b:08b}" for b in file_bytes)
    total_bits = len(file_bits)
    bit_index = 0

    # 3. Initialize chess board and variables
    start_fen = "8/8/8/8/8/8/8/K6k w - - 0 1"
    board = chess.Board(start_fen)
    output_bits = []

    # Metadata tracking
    num_games = 0
    current_game_moves = 0
    current_game_moves_list = []
    shortest_game = float('inf')
    shortest_game_sequence = []
    longest_game = 0

    while bit_index < total_bits:
        pseudo_moves = list(board.generate_pseudo_legal_moves())

        if not pseudo_moves:
            # End of game
            if current_game_moves > 0:
                num_games += 1
                if current_game_moves < shortest_game:
                    shortest_game = current_game_moves
                    shortest_game_sequence = current_game_moves_list.copy()
                longest_game = max(longest_game, current_game_moves)
                current_game_moves = 0
                current_game_moves_list = []
            board = chess.Board(start_fen)
            continue

        max_bits = min(int(log2(len(pseudo_moves))), total_bits - bit_index)
        if max_bits <= 0:
            board = chess.Board(start_fen)
            continue

        move_bits_map = {i: f"{i:0{max_bits}b}" for i in range(len(pseudo_moves))}
        chunk = file_bits[bit_index:bit_index+max_bits]

        found = False
        for move_index, bits in move_bits_map.items():
            if bits == chunk:
                move = pseudo_moves[move_index]
                board.push(move)
                output_bits.append(bits)
                bit_index += max_bits
                current_game_moves += 1
                current_game_moves_list.append(move.uci())  # ✅ store UCI instead of index
                found = True
                break

        if not found:
            # Restart board if no match
            if current_game_moves > 0:
                num_games += 1
                if current_game_moves < shortest_game:
                    shortest_game = current_game_moves
                    shortest_game_sequence = current_game_moves_list.copy()
                longest_game = max(longest_game, current_game_moves)
                current_game_moves = 0
                current_game_moves_list = []
            board = chess.Board(start_fen)

    # Finalize last game
    if current_game_moves > 0:
        num_games += 1
        if current_game_moves < shortest_game:
            shortest_game = current_game_moves
            shortest_game_sequence = current_game_moves_list.copy()
        longest_game = max(longest_game, current_game_moves)

    # 4. Convert all bits to bytes
    all_bits = "".join(output_bits)
    padding = (8 - len(all_bits) % 8) % 8
    all_bits += "0" * padding
    byte_array = bytearray(int(all_bits[i:i+8], 2) for i in range(0, len(all_bits), 8))

    # 5. Prepare header (file format code + metadata)
    header = struct.pack(">BIII", format_code, num_games, shortest_game, longest_game)

    # 6. Encode shortest game moves as UCI string
    shortest_game_str = " ".join(shortest_game_sequence)  # space separated UCI
    shortest_game_bytes = shortest_game_str.encode("utf-8")

    # Prefix with length (so decoder knows how many bytes to read)
    shortest_game_len = struct.pack(">I", len(shortest_game_bytes))

    # 7. Write .chesscloud file
    with open(output_path, "wb") as f:
        f.write(header)
        f.write(shortest_game_len)       # length prefix
        f.write(shortest_game_bytes)     # UCI move sequence
        f.write(bytes([padding]))        # padding
        f.write(byte_array)              # encoded payload

   

