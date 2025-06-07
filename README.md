# CTFd Challenge Downloader

A Python script that automates the process of downloading challenges from a [CTFd](https://ctfd.io/) instance, organizing them into category-based directories, and generating `README.md` files containing challenge details.

## Features

* Automatically fetches challenges using the CTFd API.
* Organizes challenges by category and name in local directories.
* Downloads challenge files and metadata.
* Generates a `README.md` file per challenge with:

  * Description
  * Category
  * Point value
  * Tags
  * File list
* Saves configuration in `.ctfd.yaml` for future reuse.

## Requirements

* Python 3.6+
* Required libraries:

  * `requests`
  * `PyYAML`

Install with:

```bash
pip install requests PyYAML
```

## Usage

```bash
python script.py -d <directory> -t <api_token> [-u <ctfd_url>] [-v]
```

### Arguments

* `-d`, `--directory` — Path to store the downloaded challenges.
* `-t`, `--token` — CTFd API token for authentication.
* `-u`, `--url` — Base URL of the CTFd instance (required only the first time).
* `-v`, `--verbose` — Enable verbose output (currently placeholder).

### First Time Usage

```bash
python script.py -d ./my_ctf -t ABCDEFG12345 -u https://ctf.example.com
```

This creates a `.ctfd.yaml` config and downloads all challenges.

### Subsequent Runs

```bash
python script.py -d ./my_ctf -t ABCDEFG12345
```

Reuses existing config in `.ctfd.yaml`.

## Example Directory Structure

```
my_ctf/
├── Web/
│   ├── SQL_Injection/
│   │   ├── README.md
│   │   └── challenge.zip
│   └── XSS/
│       ├── README.md
│       └── payload.txt
└── Crypto/
    └── RSA/
        ├── README.md
        └── encrypt.py
```

## Notes

* If a challenge has no downloadable files, a warning is printed.
* File and folder names are sanitized for filesystem compatibility.
* The `.ctfd.yaml` config tracks the platform, URL, timestamps, and syncs.
