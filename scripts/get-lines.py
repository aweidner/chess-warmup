import argparse
import json
from pprint import pprint
import sqlite3


parser = argparse.ArgumentParser("Fetch database of lichess tactics between particular range")
parser.add_argument("--state-file", help="Location of the state file to save progress", type=str, default="state.db")
parser.add_argument("--lines", help="Limit of the number of lines", type=int, default=None)
parser.add_argument("--outfile", help="File to output the data to", type=str, default="database.json")

args = parser.parse_args()

def get_conn():
    return sqlite3.connect(args.state_file)

conn = get_conn()
cur = conn.cursor()

limit = ""
if args.lines is not None:
    limit = f"LIMIT {args.lines}"


cur.execute(f"SELECT puzzle_data FROM puzzle_data {limit}")
entry_list = []

for index, row in enumerate(cur):
    data = json.loads(row[0])
    puzzle = data['puzzle']
    ply = puzzle['initialPly']
    initialFen = data['game']['treeParts'][ply]['fen']

    entry = {
        "f": initialFen,
        "c": puzzle['color'],
        "l": puzzle['lines']
    }

    entry_list.append(entry)


with open(args.outfile, "w") as outfile:
    outfile.write(json.dumps(entry_list, separators=(',', ':')))


print(f"Saved {len(entry_list)} tactics")
