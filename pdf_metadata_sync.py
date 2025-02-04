#!/usr/bin/env python3

import os
import logging
import requests
from PyPDF2 import PdfReader
from datetime import datetime

# Setup logging at the module level
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] PDF-Metadata-Sync: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add startup banner for clear visibility in logs
logger.info("="*50)
logger.info("PDF Metadata Sync Script Starting")
logger.info("="*50)
logger.info(f"Script location: {os.path.abspath(__file__)}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"PAPERLESS_URL: {os.getenv('PAPERLESS_URL', 'not set')}")
logger.info(f"PAPERLESS_TOKEN: {'set' if os.getenv('PAPERLESS_TOKEN') else 'not set'}")

class PaperlessAPI:
    def __init__(self):
        self.base_url = os.getenv('PAPERLESS_URL', 'http://localhost:8000')
        self.token = os.getenv('PAPERLESS_TOKEN')
        if not self.token:
            raise ValueError("PAPERLESS_TOKEN environment variable is required")
        
        self.headers = {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Test connection on initialization
        self.test_connection()
    
    def test_connection(self):
        """Test API connection and authentication"""
        try:
            logger.info("Testing API connection...")
            response = requests.get(
                f'{self.base_url}/api/documents/',
                headers=self.headers,
                params={'page_size': 1}  # Only request one document to minimize data transfer
            )
            
            if response.status_code == 200:
                data = response.json()
                doc_count = data.get('count', 0)
                logger.info(f"API connection successful! Found {doc_count} documents in system.")
                return True
            elif response.status_code == 401:
                logger.error("API authentication failed. Check your PAPERLESS_TOKEN.")
                raise ValueError("Invalid API token")
            else:
                logger.error(f"API connection failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise ConnectionError(f"API connection failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to {self.base_url}")
            logger.error(f"Connection error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error testing API connection: {str(e)}")
            raise
    
    def get_or_create_correspondent(self, name):
        """Get existing correspondent or create new one"""
        # First try to find existing
        response = requests.get(
            f'{self.base_url}/api/correspondents/?name={name}',
            headers=self.headers
        )
        results = response.json().get('results', [])
        
        if results:
            return results[0]['id']
            
        # Create new correspondent
        response = requests.post(
            f'{self.base_url}/api/correspondents/',
            headers=self.headers,
            json={'name': name}
        )
        return response.json()['id']
    
    def get_or_create_tags(self, keywords):
        """Convert PDF keywords to Paperless tags"""
        tag_ids = []
        for keyword in keywords.split(','):
            keyword = keyword.strip()
            if not keyword:
                continue
                
            # Try to find existing tag
            response = requests.get(
                f'{self.base_url}/api/tags/?name={keyword}',
                headers=self.headers
            )
            results = response.json().get('results', [])
            
            if results:
                tag_ids.append(results[0]['id'])
            else:
                # Create new tag
                response = requests.post(
                    f'{self.base_url}/api/tags/',
                    headers=self.headers,
                    json={'name': keyword}
                )
                tag_ids.append(response.json()['id'])
        
        return tag_ids

    def update_document(self, doc_id, metadata):
        """Update document with extracted metadata"""
        response = requests.patch(
            f'{self.base_url}/api/documents/{doc_id}/',
            headers=self.headers,
            json=metadata
        )
        return response.json()

def extract_pdf_metadata(pdf_path):
    """Extract metadata from PDF file"""
    logger.info(f"Attempting to extract metadata from: {pdf_path}")
    try:
        reader = PdfReader(pdf_path)
        info = reader.metadata
        
        # Log all available metadata for debugging
        logger.info("Raw PDF metadata found:")
        for key, value in info.items():
            logger.info(f"  {key}: {value}")
        
        metadata = {}
        if info.get('/Author'):
            metadata['author'] = info['/Author']
            logger.info(f"Found Author: {metadata['author']}")
        else:
            logger.info("No Author found in PDF metadata")
            
        if info.get('/Title'):
            metadata['title'] = info['/Title']
            logger.info(f"Found Title: {metadata['title']}")
        elif info.get('/Subject'):  # Fallback to Subject if Title missing
            metadata['title'] = info['/Subject']
            logger.info(f"No Title found, using Subject: {metadata['title']}")
        else:
            logger.info("No Title or Subject found in PDF metadata")
            
        if info.get('/Keywords'):
            metadata['keywords'] = info['/Keywords']
            logger.info(f"Found Keywords: {metadata['keywords']}")
        else:
            logger.info("No Keywords found in PDF metadata")
            
        if info.get('/CreationDate'):
            # Convert PDF date format (D:YYYYMMDDhhmmss) to ISO
            date_str = info['/CreationDate'][2:]  # Remove 'D:' prefix
            try:
                date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                metadata['created'] = date.isoformat()
                logger.info(f"Found Creation Date: {metadata['created']}")
            except ValueError as e:
                logger.warning(f"Could not parse PDF creation date: {date_str}")
                logger.warning(f"Parse error: {e}")
        else:
            logger.info("No Creation Date found in PDF metadata")
        
        return metadata
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
        return None

def process_document(doc_id, pdf_path):
    """Main processing function"""
    logger.info("="*30)
    logger.info(f"Processing document {doc_id}: {pdf_path}")
    logger.info("="*30)
    
    metadata = extract_pdf_metadata(pdf_path)
    if not metadata:
        logger.warning(f"No metadata found in {pdf_path}")
        return
    
    logger.info("Extracted metadata summary:")
    for key, value in metadata.items():
        logger.info(f"  {key}: {value}")
    
    try:
        api = PaperlessAPI()  # This will test connection
        update_data = {}
        
        # Handle correspondent (author)
        if metadata.get('author'):
            correspondent_id = api.get_or_create_correspondent(metadata['author'])
            update_data['correspondent'] = correspondent_id
            logger.info(f"Set correspondent ID: {correspondent_id} for author: {metadata['author']}")
        
        # Handle title
        if metadata.get('title'):
            update_data['title'] = metadata['title']
            logger.info(f"Set title: {metadata['title']}")
        
        # Handle creation date
        if metadata.get('created'):
            update_data['created'] = metadata['created']
            logger.info(f"Set creation date: {metadata['created']}")
        
        # Handle keywords/tags
        if metadata.get('keywords'):
            tag_ids = api.get_or_create_tags(metadata['keywords'])
            if tag_ids:
                update_data['tags'] = tag_ids
                logger.info(f"Set tag IDs: {tag_ids} for keywords: {metadata['keywords']}")
        
        # Update document
        if update_data:
            logger.info(f"Updating document {doc_id} with data: {update_data}")
            api.update_document(doc_id, update_data)
            logger.info(f"Successfully updated document {doc_id}")
        else:
            logger.info(f"No metadata updates needed for document {doc_id}")
            
    except Exception as e:
        logger.error(f"Failed to process document {doc_id}: {e}")
        raise

if __name__ == "__main__":
    import sys
    logger.info(f"Script called with {len(sys.argv)} arguments:")
    for i, arg in enumerate(sys.argv):
        logger.info(f"Argument {i}: {arg}")
    
    try:
        if len(sys.argv) != 3:
            logger.error("Incorrect number of arguments")
            logger.error("Usage: pdf_metadata_sync.py <document_id> <pdf_path>")
            sys.exit(1)
        
        # Test API connection before processing
        api = PaperlessAPI()  # This will test connection on init
        
        doc_id = sys.argv[1]
        pdf_path = sys.argv[2]
        logger.info(f"Processing document {doc_id} at path {pdf_path}")
        process_document(doc_id, pdf_path)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1) 