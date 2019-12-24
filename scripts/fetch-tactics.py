import requests
import argparse
import re
import json
from pprint import pprint
import sqlite3
import multiprocessing
import logging
import traceback
import time
from tqdm import tqdm


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


PUZZLE_REGEX = re.compile(r"lichess.puzzle = (.*?)</script>")
URL = "https://lichess.org/training"


parser = argparse.ArgumentParser("Fetch database of lichess tactics between particular range")
parser.add_argument("--start", help="Start range", type=int, default=1000)
parser.add_argument("--end", help="End range", type=int, default=1500)
parser.add_argument("--outfile", help="Path to the file to write the tactics to (JSON)", type=str, default="outfile.json")
parser.add_argument("--state-file", help="Location of the state file to save progress", type=str, default="state.db")
parser.add_argument("--error-file", help="Location of the error file", type=str, default="errorfile.dat")
parser.add_argument("--end-at-id", help="End at this tactic id", type=int, default=10)

args = parser.parse_args()


def get_conn():
    return sqlite3.connect(args.state_file)


def fetch_tactic_data(tactic_id):
    result = requests.get(f"{URL}/{tactic_id}")
    matched_group = PUZZLE_REGEX.search(result.text).group(1)
    matched_json = json.loads(matched_group)
    return matched_json["data"]


def filter_tactic_data(tactic_data, start, end):
    rating = tactic_data["puzzle"]["rating"]
    return start <= rating and rating <= end


def save_tactic_file_to_db(tactic_data):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO puzzle_data VALUES (?, ?, ?)", (tactic_data["puzzle"]["id"], tactic_data["puzzle"]["rating"], json.dumps(tactic_data)))
        conn.commit()
    except sqlite3.OperationalError as e:
        logger.debug(f"Skipping duplicate tactic data for {tactic_data['puzzle']['id']}")


def write_error_block(tactic_id, tb):
    with open("errorfile.dat", "a") as errorfile:
        errorfile.write(f"""
Could not fetch {tactic_id}:
{tb}

""")


def initialize_database():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS puzzle_data (
        puzzle_id int primary key,
        rating int,
        puzzle_data text
    )""")


def work(tactic_id):
    logging.debug(f"Downloading tactic {tactic_id}")
    try:
        data = fetch_tactic_data(tactic_id)
        if filter_tactic_data(data, args.start, args.end):
            logging.debug(f"Saving tactic {tactic_id} to db")
            save_tactic_file_to_db(data)
    except Exception as e:
        tb = traceback.format_exc()
        write_error_block(tactic_id, tb)
    time.sleep(3)


def get_highest_tactic():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MAX(puzzle_id) FROM puzzle_data")
    return cur.fetchone()[0] or 0


initialize_database()
highest_tactic = get_highest_tactic()
for x in tqdm(range(max(1, highest_tactic + 1), args.end_at_id)):
    work(x)
