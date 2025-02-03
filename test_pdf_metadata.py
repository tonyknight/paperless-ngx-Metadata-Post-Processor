#!/usr/bin/env python3

import sys
from PyPDF2 import PdfReader
import json
from datetime import datetime

def print_metadata(pdf_path):
    """Print all metadata from a PDF file in a readable format."""
    try:
        print(f"\nReading PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        metadata = reader.metadata
        
        print("\n=== PDF Metadata ===")
        if metadata:
            # Convert metadata to dict and pretty print
            metadata_dict = {}
            for key in metadata:
                # Clean up key name (remove leading '/')
                clean_key = key[1:] if key.startswith('/') else key
                metadata_dict[clean_key] = metadata[key]
            
            print(json.dumps(metadata_dict, indent=2))
            
            # Special handling for dates
            if '/CreationDate' in metadata:
                date_str = metadata['/CreationDate']
                print("\n=== Parsed Creation Date ===")
                print(f"Raw date string: {date_str}")
                if date_str.startswith('D:'):
                    # Remove D: prefix and try to parse
                    date_str = date_str[2:16]  # Get YYYYMMDDHHMMSS
                    try:
                        date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                        print(f"Parsed date: {date.isoformat()}")
                    except ValueError as e:
                        print(f"Could not parse date: {e}")
        else:
            print("No metadata found in PDF")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    # Hardcoded test PDF path - replace with your PDF path
    DEFAULT_PDF_PATH = "/Users/knight/Desktop/PDFs/Pre 1980/(1961-10-27) President of LSU Letter  - (Misc).pdf"
    
    # Use command-line argument if provided, otherwise use default path
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF_PATH
    
    print_metadata(pdf_path) 