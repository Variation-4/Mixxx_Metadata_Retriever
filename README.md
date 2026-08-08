# Mixxx Metadata Retriever

*Mixxx Metadata Retreiever* is a utility that can retrieve any metadata entry of the most recently played track
(which includes what's currently playing) from the DJ software [Mixxx](https://github.com/mixxxdj/mixxx).

## How it works

Every predefined amount of seconds (default: `5`), this program will check if there has been a new track that was
played. If so, it will obtain all metadata that was specified in the [configuration](#configuration) file, and write
each one to its own file inside the `metadata` directory (e.g. `artist` would be written to `artist.txt`).

## Configuration

The file `conf.txt` contains all configuration information for the program, such as the directory of Mixxx's database
and what metadata to obtain.

### Configuration fields

| Field          | Description                                                                                                                                                                                                                                                                                                   |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| db_path        | The path of Mixxx's database (`mixxxdb.sqlite`)<br/>`DEFAULT` will use the standard directory on Windows (i.e. `~/AppData/local/Mixxx/mixxxdb.sqlite`)                                                                                                                                                        |
| check_interval | The amount of time in seconds to wait between each check of if a new track is playing.                                                                                                                                                                                                                        |
| cover          | Whether or not to obtain the path of the cover art.<br/>Is either `True` or `False`.                                                                                                                                                                                                                          |
| tags           | Which metadata entries to retrieve.<br/>Must be an existing entry in the database (see [trackschema](https://github.com/mixxxdj/mixxx/blob/main/src/library/dao/trackschema.h), specifically all strings that are part of `LIBRARYTABLE`)<br/>Formatted as a comma-seperated list (e.g. `artist,title,genre`) |

## Usage

Commandline arguments have yet to be implemented.