import sqlite3
from pathlib import Path
import time
from os import system

# Define file paths
DEFAULT_DB_PATH = Path.home() / "AppData/Local/Mixxx/mixxxdb.sqlite"
CONF_FILE_PATH = "conf.txt"
COVER_FILENAME = "cover.txt"
ERROR_FILENAME = "errorLog.txt"
DEFAULT_CONFIGURATION = \
"""\
db_path:DEFAULT
cover:True
tags:artist,title
"""

class ConfigurationData:
    def __init__(self, db_path=DEFAULT_DB_PATH, cover=True, tags=None):
        if tags is None:
            tags = ["artist", "title"]
        self.db_path = db_path
        self.cover = cover
        self.tags = tags

class Metadata:
    def __init__(self, track_id=None, location_id=None, filename=None, path=None, tags=None,
                 cover=None, cover_path=None):
        if tags is None:
            tags = dict()
        self.id = track_id
        self.location_id = location_id
        self.filename = filename
        self.path = path
        self.tags = tags
        self.cover = cover
        self.cover_path = cover_path

def read_conf_file(filename: str):
    conf_data = dict()
    with open(filename, "r") as f:
        for line in f.readlines():
            line_split = line.strip().split(":")
            if len(line_split) == 2:
                conf_data[line_split[0].strip()] = line_split[1].strip()
    return conf_data

def write_meta_file(filename, data):
    with open("metadata/" + filename, "w", encoding="utf-8") as f:
        if data is None:
            f.write("")
        else:
            f.write(data)

def write_default_meta_file():
    with open("conf.txt", "w") as f:
        f.write(DEFAULT_CONFIGURATION)

def set_conf(conf_class: ConfigurationData, filename: str):
    try:
        conf_data = read_conf_file(filename)
    except FileNotFoundError:
        print("Configuration file not found\nWriting new file and using default configuration")
        write_default_meta_file()
        return
    try:
        if conf_data["db_path"] != "DEFAULT":
            conf_class.db_path = conf_data["db_path"]
    except KeyError:
        print("Configuration file not formatted properly: Using default db path")
    try:
        if conf_data["cover"].lower() == "true":
            conf_class.cover = True
        elif conf_data["cover"].lower() == "false":
            conf_class.cover = False
        else:
            print("Configuration file not formatted properly: Using default cover option")
    except KeyError or TypeError:
        print("Configuration file not formatted properly: Using default cover option")
    try:
        conf_class.tags = conf_data["tags"].split(",")
    except KeyError:
        print("Configuration file not formatted properly: Using default tags")

def get_id(cursor: sqlite3.Cursor) -> int:
    return \
    (cursor.execute("SELECT track_id FROM PlaylistTracks ORDER BY pl_datetime_added DESC LIMIT 1")).fetchall()[0][0]

def get_loc_id(cursor: sqlite3.Cursor, track_id: int) -> int:
    return (cursor.execute("SELECT location FROM library WHERE id="+str(track_id))).fetchall()[0][0]

def get_metadata(cursor: sqlite3.Cursor, track_id: int, tags: list[str]) -> dict:
    tag_string = ""
    for tag in tags:
        tag_string = tag_string + ("" if tag_string == "" else ", ") + tag
    metatags = (cursor.execute(f"SELECT {tag_string} FROM library WHERE id={str(track_id)}")).fetchall()[0]
    metadata = dict()
    for i in range(0, len(metatags)):
        metadata[tags[i]] = metatags[i]
    return metadata

def get_cover(cursor: sqlite3.Cursor, track_id: int) -> str:
    return (cursor.execute("SELECT coverart_location FROM library WHERE id="+str(track_id))).fetchall()[0][0]

def get_location(cursor: sqlite3.Cursor, track_loc_id: int) -> str:
    return (cursor.execute("SELECT location FROM track_locations WHERE id=" + str(track_loc_id))).fetchall()[0][0]

def get_filename(cursor: sqlite3.Cursor, track_loc_id: int) -> str:
    return (cursor.execute("SELECT filename FROM track_locations WHERE id=" + str(track_loc_id))).fetchall()[0][0]

# Accesses Mixxx's database
def db_access(db_path, metadata: Metadata, tags, cover_access: bool = True):
    print("-----------------------------------------")
    # Connect to Mixxx's database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obtain trackID of most recently played/current track
    metadata.id = get_id(cursor)
    print("ID -", metadata.id)
    metadata.location_id = get_loc_id(cursor, metadata.id)
    print("LOC ID -", metadata.location_id)

    # Obtain cover image and track location of most recently played/current track
    if cover_access:
        metadata.path = get_location(cursor, metadata.location_id)
        print("TRACK PATH -", metadata.path)
        metadata.filename = get_filename(cursor, metadata.location_id)
        print("FILENAME -", metadata.filename)
        metadata.cover = get_cover(cursor, metadata.id)
        print("COVER -", metadata.cover)
        if not (metadata.cover is None):
            metadata.cover_path = metadata.path[:len(metadata.filename)*(-1)] + metadata.cover
        print("COVER PATH -", metadata.cover_path)

    metatags = get_metadata(cursor, metadata.id, tags)
    for tag in metatags:
        metadata.tags[tag] = metatags[tag]
        print(f"{tag.upper()} - {metadata.tags[tag]}")

    print("-----------------------------------------")

    conn.close()

def new_data_check(db_path, metadata: Metadata):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_id = get_id(cursor)
    conn.close()

    return metadata.id != new_id

def main():
    metadata = Metadata()
    config_data = ConfigurationData()
    set_conf(config_data, CONF_FILE_PATH)
    print("Configuration loaded\n--")
    while True:
        try:
            #print(new_data)
            if new_data_check(config_data.db_path, metadata) or metadata.id is None:
                if not (metadata.id is None):
                    system('cls')
                print("New data!\nAccessing...")
                db_access(config_data.db_path, metadata, config_data.tags, cover_access=config_data.cover)
                print("Writing...")
                if config_data.cover:
                    write_meta_file(COVER_FILENAME, metadata.cover_path)
                for tag in metadata.tags:
                    write_meta_file(f"{tag}.txt", metadata.tags[tag])
                print("Data written")
        except Exception as error:
            named_tuple = time.localtime()
            formatted_time = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
            print("An error has occurred: ", error)
            with open(ERROR_FILENAME, "a" if Path(ERROR_FILENAME).is_file() else "w", encoding='utf-8') as f:
                f.write("[" + formatted_time + "]: Error: " + str(error) + "\n")
        time.sleep(5)

if __name__ == "__main__":
    main()
