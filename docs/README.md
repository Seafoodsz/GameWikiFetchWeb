# GameWiki Fetcher

A tool for fetching and processing game wiki data.

## Features

- Fetch content from any game wiki website
- Download images, tables, and other resources
- Process and structure game data: characters, items, skills, enemies, locations, quests, etc.
- Extract relationships between different data types
- Support multiple storage methods: JSON, MongoDB, SQLite
- Flexible configuration system
- Detailed logging
- Export data in multiple formats: JSON, CSV, HTML
- User-friendly web interface

## System Requirements

- Python 3.6 or higher
- Dependencies: BeautifulSoup4, requests, Flask, etc.

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

#### Fetching Wiki Data

```bash
python scripts/run_fetcher.py --wiki-url https://game-wiki-url.com --output-dir data/wiki/my_wiki
```

#### Processing Data

```bash
python scripts/run_processor.py --input-dir data/input --output-dir data/output
```

### Web Interface

```bash
python scripts/run_web.py
```

Then open your browser and navigate to `http://localhost:5000`.

## Directory Structure

```
GameWiki Fetcher/
├── src/                           # Core source code
│   ├── fetcher/                   # Wiki fetching module
│   │   ├── crawler.py             # Web crawler
│   │   ├── parser.py              # HTML parser
│   │   ├── downloader.py          # Resource downloader
│   │   └── extractor.py           # Content extractor
│   ├── processor/                 # Data processing module
│   │   ├── base.py                # Base processor
│   │   ├── character.py           # Character processor
│   │   ├── item.py                # Item processor
│   │   └── ...                    # Other processors
│   ├── storage/                   # Data storage module
│   │   ├── json_storage.py        # JSON storage
│   │   └── ...                    # Other storage implementations
│   ├── web/                       # Web interface module
│   │   ├── app.py                 # Flask application
│   │   └── ...                    # Web interface components
│   └── utils/                     # Utility module
│       ├── config.py              # Configuration management
│       ├── logger.py              # Logging utilities
│       └── ...                    # Other utilities
├── data/                          # Data directory
│   ├── input/                     # Input data
│   ├── output/                    # Output data
│   └── wiki/                      # Wiki data
├── config/                        # Configuration files
│   ├── config.json                # Main configuration
│   ├── fetcher_config.json        # Fetcher configuration
│   └── ...                        # Other configurations
├── scripts/                       # Script files
│   ├── run_fetcher.py             # Fetcher script
│   ├── run_processor.py           # Processor script
│   └── run_web.py                 # Web interface script
├── logs/                          # Log files
├── docs/                          # Documentation
└── tests/                         # Test files
```

## Configuration

The configuration files are located in the `config` directory. You can customize the behavior of the application by modifying these files.

### Main Configuration

The main configuration file is `config/config.json`. It contains settings for all modules.

### Fetcher Configuration

The fetcher configuration file is `config/fetcher_config.json`. It contains settings for the wiki fetching module.

- `wiki_url`: The base URL of the wiki website
- `output_dir`: The directory to save the fetched data
- `max_depth`: The maximum depth to crawl
- `download_images`: Whether to download images
- `download_tables`: Whether to download tables
- `user_agent`: The user agent to use for requests
- `delay`: The delay between requests (in seconds)
- `threads`: The number of concurrent threads
- `save_html`: Whether to save the original HTML
- `max_retries`: The maximum number of retries for failed requests

### Processor Configuration

The processor configuration file is `config/processor_config.json`. It contains settings for the data processing module.

- `input_dir`: The directory containing the input data
- `output_dir`: The directory to save the processed data
- `threads`: The number of concurrent threads
- `processors`: Configuration for individual processors

### Storage Configuration

The storage configuration file is `config/storage_config.json`. It contains settings for the data storage module.

- `type`: The storage type (json, mongodb, sqlite)
- `mongodb_uri`: The MongoDB connection URI
- `mongodb_db`: The MongoDB database name
- `sqlite_path`: The SQLite database path
- `export`: Export settings

### Web Configuration

The web configuration file is `config/web_config.json`. It contains settings for the web interface module.

- `host`: The host to bind to
- `port`: The port to listen on
- `debug`: Whether to enable debug mode
- `secret_key`: The secret key for the Flask application
- `upload_folder`: The folder to store uploaded files
- `allowed_extensions`: The allowed file extensions for uploads

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 