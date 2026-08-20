import sqlite3
from pathlib import Path
import time
from os import system

##CONSTANTS#############################################################
DEFAULT_DB_PATH = Path.home() / "AppData/Local/Mixxx/mixxxdb.sqlite"
CONF_FILE_PATH = "conf.txt"
COVER_FILENAME = "cover.txt"
ERROR_FILENAME = "errorLog.txt"
DEFAULT_CONFIGURATION = \
"""\
db_path:DEFAULT
check_interval:5
cover:True
tags:artist,title\
"""
##CONSTANTS#############################################################

class ConfigurationData:
    """
    Class to store the configuration data.
    """
    def __init__(self, db_path=DEFAULT_DB_PATH, check_interval=5, cover=True, tags=None):
        """
        Constructor for the ConfigurationData class
        :param db_path: the path of the database file (default: DEFAULT_DB_PATH)
        :param check_interval: the amount of time in seconds between checks (default: 5)
        :param cover: whether to obtain cover art (default: True)
        :param tags: list of metadata to retrieve (default: [artist, title])
        """
        if tags is None:
            tags = ["artist", "title"]
        self.db_path = db_path
        self.check_interval = check_interval
        self.cover = cover
        self.tags = tags

class Metadata:
    """
    Class to store the metadata of a track.
    """
    def __init__(self, track_id=None, location_id=None, filename=None, path=None, tags=None,
                 cover=None, cover_path=None):
        """
        Constructor for the Metadata class
        :param track_id: internal id of the track
        :param location_id: internal location id of the track
        :param filename: the name of the audio file
        :param path: the path of the audio file
        :param tags: the metadata fields of the track
        :param cover: the filename of the cover art
        :param cover_path: the path of the cover art
        """
        if tags is None:
            tags = dict()
        self.id = track_id
        self.location_id = location_id
        self.filename = filename
        self.path = path
        self.tags = tags
        self.cover = cover
        self.cover_path = cover_path

def read_conf_file(filename: str) -> dict:
    """
    Reads the configuration file.
    :param filename: name of the configuration file
    :return: A dictionary with keys relating to the configuration data
    """
    conf_data = dict()
    with open(filename, "r") as f:
        for line in f.readlines():
            line_split = line.strip().split(":")
            if len(line_split) == 2:
                conf_data[line_split[0].strip()] = line_split[1].strip()
    return conf_data

def write_meta_file(filename: str, data) -> None:
    """
    Writes a file to the metadata directory.
    :param filename: the name of the file
    :param data: the contents of the file
    :return: None
    """
    with open("metadata/" + filename, "w", encoding="utf-8") as f:
        if data is None:
            f.write("")
        else:
            f.write(str(data))

def write_default_conf_file() -> None:
    """
    Writes the default configuration file
    :return: None
    """
    with open("conf.txt", "w") as f:
        f.write(DEFAULT_CONFIGURATION)

def set_conf(conf_class: ConfigurationData, filename: str) -> None:
    """
    Sets the configuration data of the given ConfigurationData class with the given file.
    :param conf_class: the ConfigurationData class to set
    :param filename: the name of the configuration file
    :return: None
    """
    # Read the configuration file
    try:
        conf_data = read_conf_file(filename)
    except FileNotFoundError:
        print("Configuration file not found\nWriting new file and using default configuration")
        write_default_conf_file()
        return

    # db_path
    try:
        if conf_data["db_path"] != "DEFAULT":
            conf_class.db_path = conf_data["db_path"]
    except KeyError:
        print("Configuration file not formatted properly: Using default db path")

    # check_interval
    try:
        conf_class.check_interval = int(conf_data["check_interval"])
    except KeyError or ValueError:
        print("Configuration file not formatted properly: Using default check interval")

    # cover
    try:
        if conf_data["cover"].lower() == "true":
            conf_class.cover = True
        elif conf_data["cover"].lower() == "false":
            conf_class.cover = False
        else:
            print("Configuration file not formatted properly: Using default cover option")
    except KeyError or TypeError:
        print("Configuration file not formatted properly: Using default cover option")

    # tags
    try:
        conf_class.tags = conf_data["tags"].split(",")
    except KeyError:
        print("Configuration file not formatted properly: Using default tags")

def get_id(cursor: sqlite3.Cursor) -> int:
    """
    Retrieves the internal id of the most recently played track.
    :param cursor: the database cursor
    :return: the internal id
    """
    return \
    (cursor.execute("SELECT track_id FROM PlaylistTracks ORDER BY pl_datetime_added DESC LIMIT 1")).fetchall()[0][0]

def get_loc_id(cursor: sqlite3.Cursor, track_id: int) -> int:
    """
    Retrieves the internal location id of the track with the given id.
    :param cursor: the database cursor
    :param track_id: the internal id of the track
    :return: the internal location id
    """
    return (cursor.execute("SELECT location FROM library WHERE id="+str(track_id))).fetchall()[0][0]

def get_metadata(cursor: sqlite3.Cursor, track_id: int, tags: list[str]) -> dict:
    """
    Retrieves the metadata (as defined by `tags`) of the track with the given id.
    :param cursor: the database cursor
    :param track_id: the internal id of the track
    :param tags: the list of metadata fields to retrieve
    :return: a dictionary with keys relating to the metadata field
    """
    tag_string = ""
    for tag in tags:
        tag_string = tag_string + ("" if tag_string == "" else ", ") + tag.strip()
    metatags = (cursor.execute(f"SELECT {tag_string} FROM library WHERE id={str(track_id)}")).fetchall()[0]
    metadata = dict()
    for i in range(0, len(metatags)):
        metadata[tags[i]] = metatags[i]
    return metadata

def get_cover(cursor: sqlite3.Cursor, track_id: int) -> str:
    """
    Retrieves the cover art filename of the track with the given id.
    :param cursor: the database cursor
    :param track_id: the internal id of the track
    :return: the filename of the cover art
    """
    return (cursor.execute("SELECT coverart_location FROM library WHERE id="+str(track_id))).fetchall()[0][0]

def get_location(cursor: sqlite3.Cursor, track_loc_id: int) -> str:
    """
    Retrieves the file path of the track with the given location id.
    :param cursor: the database cursor
    :param track_loc_id: the location id of the track
    :return: the path of the track
    """
    return (cursor.execute("SELECT location FROM track_locations WHERE id=" + str(track_loc_id))).fetchall()[0][0]

def get_filename(cursor: sqlite3.Cursor, track_loc_id: int) -> str:
    """
    Retrieves the filename of the track with the given location id.
    :param cursor: the database cursor
    :param track_loc_id: the location id of the track
    :return: the filename of the track
    """
    return (cursor.execute("SELECT filename FROM track_locations WHERE id=" + str(track_loc_id))).fetchall()[0][0]

def db_access(db_path: Path, metadata: Metadata, tags: list, cover_access: bool = True) -> None:
    """
    Access Mixxx's database and provide Metadata the relevant metadata fields.
    :param db_path: the path to the database
    :param metadata: the Metadata class
    :param tags: the metadata fields to retrieve
    :param cover_access: whether to retrieve the cover art
    :return: None
    """
    print("-----------------------------------------")
    # Connect to Mixxx's database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obtain the id and location id of most recently played/current track
    metadata.id = get_id(cursor)
    print("ID -", metadata.id)
    metadata.location_id = get_loc_id(cursor, metadata.id)
    print("LOC ID -", metadata.location_id)

    # Obtain cover art and file path
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

    # Obtain metadata
    metatags = get_metadata(cursor, metadata.id, tags)
    for tag in metatags:
        metadata.tags[tag] = metatags[tag]
        print(f"{tag.upper()} - {metadata.tags[tag]}")

    print("-----------------------------------------")

    conn.close()

def new_data_check(db_path: Path, metadata: Metadata) -> bool:
    """
    Checks if the most recently played track is different from the one detailed in Metadata.
    :param db_path: the path to the database
    :param metadata: the Metadata class of the current track in memory
    :return: True if different, False otherwise
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_id = get_id(cursor)
    conn.close()

    return metadata.id != new_id

def main():
    # Construct dataclasses and load configuration data
    metadata = Metadata()
    config_data = ConfigurationData()
    set_conf(config_data, CONF_FILE_PATH)
    print("Configuration loaded\n--")
    while True:
        try:
            # Check if a new track is playing
            if new_data_check(config_data.db_path, metadata) or metadata.id is None:
                if not (metadata.id is None):
                    system('cls')
                # Retrieve metadata
                print("New data!\nAccessing...")
                db_access(config_data.db_path, metadata, config_data.tags, cover_access=config_data.cover)
                # Write metadata to relevant files
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
        time.sleep(config_data.check_interval)

if __name__ == "__main__":
    main()
