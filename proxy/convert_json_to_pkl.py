# openup the output file from the chrome extension
# iterate over each host in the dict
# for each host, save the cookies and headers as a pickle file
# the filename should be the host, with periods replaced with underscores


import json
import pickle
from pathlib import Path

input_file = Path("output.json")
output_dir = Path("captured_sessions")
output_dir.mkdir(exist_ok=True)

with open(input_file, "r") as f:
    data = json.load(f)

for host, session in data.items():
    output_file = output_dir / Path(f"{host.replace('.', '_')}.pkl")
    with open(output_file, "wb") as f:
        pickle.dump(session, f)

print(f"Saved {len(data)} sessions to {output_dir}")
