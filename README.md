# tidalrip
Simple tool used to download tracks from Tidal via lucida.to.

## Disclaimer
This tool is for educational purposes only. Please respect copyright laws and the terms of service of Tidal. Only download content you have the right to access.  

**USE AT OWN RISK**: This software is provided "as is", without warranty of any kind. The authors are not responsible for any consequences of using this tool, including but not limited to potential violations of terms of service. Use of this tool could potentially violate Tidal's terms of service.

## Requirements

- Python 3.6+
- `requests` library

## Installation

### Using Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

## Usage

### Python

```bash
# Basic usage (download to current directory)
python tidal_ripper.py "https://listen.tidal.com/track/395197959"

# Download to a specific directory
python tidal_ripper.py "https://listen.tidal.com/track/395197959" -o "/path/to/music"
```

### Docker

```bash
# Download to current directory
docker run --rm -v "$(pwd):/app/output" -it $(docker build -q .) "https://listen.tidal.com/track/395197959" -o "/app/output"
```

Or build once, then run multiple times:

```bash
docker build -t tidal-ripper .
docker run --rm -v "$(pwd):/app/output" tidal-ripper "https://listen.tidal.com/track/395197959" -o "/app/output"
```

## Example Output

```json
{"status": "info", "message": "Track information retrieved", "artist": "Hedström & Pflug", "title": "Libertad (Danny Wabbit)"}
{"status": "pending", "message": "Download initiated", "handoff_id": "53951d61-b7af-4794-86cb-faeb88d4bd6f"}
{"success": true, "status": "metadata", "message": "Downloading stream for {item} to add metadata..."}
{"success": true, "status": "completed", "message": "Rip completed"}
{"tidal_url": "https://listen.tidal.com/track/395197959", "status": "success", "message": "Track downloaded successfully", "file_path": "/app/output/Hedström & Pflug - Libertad (Danny Wabbit).flac"}
```

## Limitations

- Does not support batch downloading
- Does not support authentication for premium-only content
- Quality settings cannot be modified (always downloads in highest available quality)
- If you need other formats, use FFmpeg or similar to convert formats