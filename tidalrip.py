#!/usr/bin/env python3
"""
tidalrip.py - Download tracks from Tidal using lucida.to
"""

import re
import os
import sys
import json
import time
import html
import argparse
import urllib.parse
import requests
from datetime import datetime, timedelta


def validate_tidal_track_url(url):
    """Validate that the provided URL is a valid Tidal track URL format."""
    pattern = r"^https://listen\.tidal\.com/track/\d+"
    return bool(re.match(pattern, url))


def get_tidal_track_id(url):
    """Extract the track ID from a Tidal URL."""
    match = re.search(r"track/(\d+)", url)
    if match:
        return match.group(1)
    return None


def get_track_info(tidal_url):
    """
    Get track title and artist information from lucida.to
    
    Args:
        tidal_url (str): A valid Tidal track URL
            
    Returns:
        tuple: (artist, title) or (None, None) if not found
    """
    try:
        encoded_url = urllib.parse.quote(tidal_url)
        info_url = f"https://lucida.to/?url={encoded_url}&country=auto"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }
        
        response = requests.get(info_url, headers=headers)
        response.raise_for_status()
        # Ensure we're using utf-8 encoding
        response.encoding = 'utf-8'
        
        # Extract title from HTML - trying multiple patterns
        patterns = [
            r'<title>(.*?)\s+\|\s+lucida</title>',  # Standard pattern
            r'<meta property="og:title" content="Download (.*?) on Lucida for free">',
            r'<title>(.*?)</title>'  # Fallback to any title
        ]
        
        title_text = None
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                title_text = html.unescape(match.group(1))
                break
        
        if not title_text:
            print(json.dumps({"status": "warning", "message": "Could not extract title from HTML response"}), file=sys.stderr)
            return None, None
        
        # The format is typically "TrackName by Artist"
        # Need to properly handle the "by" separator and decode any HTML entities
        by_match = re.search(r'(.*?)\s+by\s+(.*?)($|\s+\|)', title_text)
        if by_match:
            track_title = html.unescape(by_match.group(1).strip())
            artist = html.unescape(by_match.group(2).strip())
            
            # Normalize Unicode characters to avoid encoding issues
            import unicodedata
            track_title = unicodedata.normalize('NFC', track_title)
            artist = unicodedata.normalize('NFC', artist)
            
            print(json.dumps({"status": "debug", "message": f"Parsed title: '{track_title}' by '{artist}'"}), file=sys.stderr)
            return artist, track_title
        
        print(json.dumps({"status": "warning", "message": f"Could not parse artist and title from: {title_text}"}), file=sys.stderr)
        return None, None
        
    except Exception as e:
        print(json.dumps({"status": "warning", "message": f"Failed to get track info: {str(e)}"}), file=sys.stderr)
        return None, None


def create_filename(artist, title, track_id):
    """Create a clean filename from artist and title, with fallback to track ID."""
    if artist and title:
        # Ensure proper encoding of Unicode characters
        import unicodedata
        
        # Normalize Unicode characters (NFD then NFC for consistency)
        artist = unicodedata.normalize('NFC', artist)
        title = unicodedata.normalize('NFC', title)
        
        # Remove characters not allowed in filenames
        invalid_chars = r'[<>:"/\\|?*]'
        artist = re.sub(invalid_chars, '', artist)
        title = re.sub(invalid_chars, '', title)
        
        # Limit filename length
        max_length = 150  # Safe limit for most filesystems
        filename = f"{artist} - {title}"
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        return f"{filename}.flac"
    else:
        return f"tidal_track_{track_id}.flac"


def download_tidal_track(tidal_url, output_dir=None):
    """
    Download a track from Tidal using lucida.to
    
    Args:
        tidal_url (str): A valid Tidal track URL
        output_dir (str, optional): Directory to save the downloaded file
            
    Returns:
        dict: A dictionary with status and details about the download
    """
    result = {
        "tidal_url": tidal_url,
        "status": "fail",
        "message": "Failed to download track",
        "file_path": None
    }
    
    if not validate_tidal_track_url(tidal_url):
        result["message"] = "Invalid Tidal track URL"
        return result
    
    track_id = get_tidal_track_id(tidal_url)
    if not track_id:
        result["message"] = "Could not extract track ID from URL"
        return result
    
    # Use current working directory if output_dir is not specified
    if not output_dir:
        output_dir = os.getcwd()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get track info
    artist, title = get_track_info(tidal_url)
    filename = create_filename(artist, title, track_id)
    
    print(json.dumps({
        "status": "info", 
        "message": "Track information retrieved", 
        "artist": artist, 
        "title": title
    }))
    
    # Step 1: Send initial POST request to get handoff ID
    try:
        # Calculate expiry timestamp (30 days from now)
        expiry = int((datetime.now() + timedelta(days=30)).timestamp())
        
        payload = {
            "url": f"http://www.tidal.com/track/{track_id}",
            "metadata": True,
            "compat": False,
            "private": True,
            "handoff": True,
            "account": {
                "type": "country",
                "id": "auto"
            },
            "upload": {
                "enabled": False,
                "service": "pixeldrain"
            },
            "downscale": "original",
            "token": {
                "primary": "g-dQ7ptFr5_PIBqGmYk0mpMJkhI",
                "expiry": expiry
            }
        }
        
        headers = {
            "Content-Type": "text/plain;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Origin": "https://lucida.to",
            "Referer": f"https://lucida.to/?url={urllib.parse.quote(tidal_url)}&country=auto"
        }
        
        load_url = "https://lucida.to/api/load?url=%2Fapi%2Ffetch%2Fstream%2Fv2"
        response = requests.post(load_url, json=payload, headers=headers)
        response.raise_for_status()
        
        load_data = response.json()
        if not load_data.get("success") or not load_data.get("handoff"):
            result["message"] = "Failed to initiate download"
            return result
        
        handoff_id = load_data["handoff"]
        server_name = load_data.get("name", "katze")
        
        print(json.dumps({
            "status": "pending", 
            "message": "Download initiated", 
            "handoff_id": handoff_id
        }))
        
        # Step 2: Poll status until completed
        status_url = f"https://{server_name}.lucida.to/api/fetch/request/{handoff_id}"
        
        start_time = time.time()
        timeout = 300  # 5 minutes
        
        while True:
            if time.time() - start_time > timeout:
                result["message"] = "Download timed out after 5 minutes"
                return result
            
            time.sleep(2)  # Polling interval
            
            status_response = requests.get(status_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "Origin": "https://lucida.to",
                "Referer": "https://lucida.to/"
            })
            
            if status_response.status_code != 200:
                continue
            
            status_data = status_response.json()
            
            # Log progress
            print(json.dumps(status_data))
            
            if status_data.get("status") == "completed":
                break
        
        # Step 3: Download the file
        download_url = f"https://{server_name}.lucida.to/api/fetch/request/{handoff_id}/download"
        
        download_response = requests.get(download_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Referer": "https://lucida.to/",
        }, stream=True)
        
        file_path = os.path.join(output_dir, filename)
        
        # Log that we're downloading the file
        print(json.dumps({
            "status": "downloading",
            "message": f"Downloading file: {filename}",
            "path": file_path
        }))
    
        with open(file_path, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        result["status"] = "success"
        result["message"] = "Track downloaded successfully"
        result["file_path"] = file_path
        
        return result
        
    except requests.exceptions.RequestException as e:
        result["message"] = f"Request error: {str(e)}"
        return result
    except Exception as e:
        result["message"] = f"Unexpected error: {str(e)}"
        return result


def main():
    parser = argparse.ArgumentParser(description='Download tracks from Tidal using lucida.to')
    parser.add_argument('url', help='Tidal track URL to download')
    parser.add_argument('-o', '--output', help='Output directory for downloaded file')
    
    args = parser.parse_args()
    result = download_tidal_track(args.url, args.output)
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()