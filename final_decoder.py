# import struct


# FILE_TYPES_REV = {
#     1: "txt",
#     2: "json",
#     3: "png",
#     4: "jpg"
# }


# def decode(input_path: str, output_path: str):
#     with open(input_path, "rb") as f:
        
#         header = f.read(13)
#         if len(header) != 13:
#             raise ValueError("Corrupt file: header too short.")
#         format_code, num_games, shortest_game_len, longest_game_len = struct.unpack(">BIII", header)

#         if format_code not in FILE_TYPES_REV:
#             raise ValueError(f"Unknown format code {format_code}")
#         file_ext = FILE_TYPES_REV[format_code]

#         # 2) Shortest game move indices (payload just for metadata/inspection)
#         shortest_game_bytes = f.read(shortest_game_len)
#         if len(shortest_game_bytes) != shortest_game_len:
#             raise ValueError("Corrupt file: shortest-game section too short.")

#         # 3) Padding byte
#         padding_b = f.read(1)
#         if len(padding_b) != 1:
#             raise ValueError("Corrupt file: missing padding byte.")
#         padding = padding_b[0]

#         # 4) Encoded bytes (this is just the original file bits + zero padding)
#         encoded_bytes = f.read()
#         if not encoded_bytes:
#             raise ValueError("Corrupt file: no encoded data present.")

    
#     all_bits = "".join(f"{b:08b}" for b in encoded_bytes)
#     if padding:
#         if padding > 7 or padding > len(all_bits):
#             raise ValueError("Corrupt file: invalid padding.")
#         all_bits = all_bits[:-padding]

   
#     if len(all_bits) % 8 != 0:
        
#         raise ValueError("Bitstream not byte-aligned after removing padding.")

#     out = bytearray(int(all_bits[i:i+8], 2) for i in range(0, len(all_bits), 8))

#     output_path += f".{file_ext}"
            

#     with open(output_path, "wb") as f:
#         f.write(out)

#     print(f"Decoded file saved to {output_path}")
#     print(f"Number of games: {num_games}")
#     print(f"Shortest game: {shortest_game_len} moves, Longest game: {longest_game_len} moves")
#     print(f"Shortest game move indices (len={len(shortest_game_bytes)}): {list(shortest_game_bytes)[:16]}{'...' if len(shortest_game_bytes)>16 else ''}")



import struct

FILE_TYPES_REV = {
    1: "txt",
    2: "json",
    3: "png",
    4: "jpg"
}

def decode(input_path: str, output_path: str):
    with open(input_path, "rb") as f:
        # 1) Header
        header = f.read(13)
        if len(header) != 13:
            raise ValueError("Corrupt file: header too short.")
        format_code, num_games, shortest_game_moves, longest_game_moves = struct.unpack(">BIII", header)

        if format_code not in FILE_TYPES_REV:
            raise ValueError(f"Unknown format code {format_code}")
        file_ext = FILE_TYPES_REV[format_code]

        # 2) Shortest game UCI sequence length
        length_bytes = f.read(4)
        if len(length_bytes) != 4:
            raise ValueError("Corrupt file: missing shortest-game length prefix.")
        shortest_game_len = struct.unpack(">I", length_bytes)[0]

        # 3) Shortest game UCI sequence
        shortest_game_bytes = f.read(shortest_game_len)
        if len(shortest_game_bytes) != shortest_game_len:
            raise ValueError("Corrupt file: shortest-game section too short.")
        shortest_game_str = shortest_game_bytes.decode("utf-8")
        shortest_game_moves_list = shortest_game_str.split() if shortest_game_str else []

        # 4) Padding byte
        padding_b = f.read(1)
        if len(padding_b) != 1:
            raise ValueError("Corrupt file: missing padding byte.")
        padding = padding_b[0]

        # 5) Encoded bytes
        encoded_bytes = f.read()
        if not encoded_bytes:
            raise ValueError("Corrupt file: no encoded data present.")

    # Decode bitstream
    all_bits = "".join(f"{b:08b}" for b in encoded_bytes)
    if padding:
        if padding > 7 or padding > len(all_bits):
            raise ValueError("Corrupt file: invalid padding.")
        all_bits = all_bits[:-padding]

    if len(all_bits) % 8 != 0:
        raise ValueError("Bitstream not byte-aligned after removing padding.")

    out = bytearray(int(all_bits[i:i+8], 2) for i in range(0, len(all_bits), 8))

    # Write back original file
    output_path += f".{file_ext}"
    with open(output_path, "wb") as f:
        f.write(out)

    
    

