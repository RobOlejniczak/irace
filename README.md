# iRace

Python module for fetching and parsing iRacing league results.


## Installation

```bash
git clone https://github.com/a-tal/irace.git
cd irace
pip install .
```


## Included utilities

Several command line utilities are included with iRace. These are here mostly
for development purposes, iRace Admin is intended to negate the need to use
any of these. Use `--help` with any command for usage details.

Command          | Description
-----------------|-------------------------------
`irace-populate` | Pull new data from iRacing.com
`irace-generate` | Generate JSON files
`irace-league`   | Display basic league information
`irace-storage`  | CouchDB connection test, can migrate to/from files
`irace-python`   | Open a python shell with iRace utilities imported
