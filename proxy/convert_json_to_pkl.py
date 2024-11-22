# openup the output file from the chrome extension
# iterate over each host in the dict
# for each host, save the cookies and headers as a pickle file
# the filename should be the host, with periods replaced with underscores


import json
import pickle
from pathlib import Path
import os


input_file = Path("proxy/output.json")
output_dir = Path("proxy/captured_sessions")
output_dir.mkdir(exist_ok=True)

print(f"Current working directory: {os.getcwd()}")
print(f"Input file path: {input_file.resolve()}")
print(f"Output directory path: {output_dir.resolve()}")

with open(input_file, "r") as f:
    data = json.load(f)

for host, session in data.items():
    output_file = output_dir / Path(f"{host.replace('.', '_')}.pkl")
    with open(output_file, "wb") as f:
        pickle.dump(session, f)

print(f"Saved {len(data)} sessions to {output_dir}")
