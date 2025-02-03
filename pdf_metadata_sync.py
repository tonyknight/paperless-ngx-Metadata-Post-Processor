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

class SimplePaperlessAPI:
    def __init__(self, api_url, auth_token):
        self.logger = logging.getLogger(__name__)
        if api_url[-1] == "/":
            api_url = api_url[:-1]
        self._api_url = api_url
        self._auth_token = auth_token
        self.logger.info(f"Initialized API connection to {api_url}")

    def get_document_by_id(self, document_id):
        self.logger.debug(f"Fetching document {document_id}")
        try:
            response = requests.get(
                f"{self._api_url}/documents/{document_id}/",
                headers={"Authorization": f"Token {self._auth_token}"}
            )
            self.logger.debug(f"API Response: {response.status_code}")
            
            if not response.ok:
                self.logger.error(f"Failed to fetch document {document_id}: {response.status_code}")
                return {'tags': []}  # Return minimal valid document data
            
            try:
                return response.json()
            except ValueError:
                self.logger.error(f"Invalid JSON in response: {response.text[:100]}")
                return {'tags': []}  # Return minimal valid document data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            return {'tags': []}  # Return minimal valid document data

    def get_or_create_correspondent(self, name):
        # First try to find existing correspondent
        response = requests.get(
            f"{self._api_url}/correspondents/",
            headers={"Authorization": f"Token {self._auth_token}"},
            params={"name": name}
        )
        if response.ok and response.json()['results']:
            correspondent_id = response.json()['results'][0]['id']
            self.logger.info(f"Found existing correspondent '{name}' (ID: {correspondent_id})")
            return correspondent_id
        
        # Create new correspondent if not found
        self.logger.info(f"Creating new correspondent: {name}")
        response = requests.post(
            f"{self._api_url}/correspondents/",
            headers={"Authorization": f"Token {self._auth_token}"},
            json={"name": name}
        )
        if response.ok:
            correspondent_id = response.json()['id']
            self.logger.info(f"Created new correspondent '{name}' (ID: {correspondent_id})")
            return correspondent_id
        self.logger.error(f"Failed to create correspondent '{name}': {response.status_code}")
        return None

    def get_or_create_tag(self, name):
        # First try to find existing tag
        response = requests.get(
            f"{self._api_url}/tags/",
            headers={"Authorization": f"Token {self._auth_token}"},
            params={"name": name}
        )
        if response.ok and response.json()['results']:
            return response.json()['results'][0]['id']
        
        # Create new tag if not found
        response = requests.post(
            f"{self._api_url}/tags/",
            headers={"Authorization": f"Token {self._auth_token}"},
            json={"name": name}
        )
        return response.json()['id'] if response.ok else None

    def update_document(self, document_id, updates):
        self.logger.debug(f"Sending update request for document {document_id}")
        self.logger.debug(f"Update data: {updates}")
        try:
            response = requests.patch(
                f"{self._api_url}/documents/{document_id}/",
                headers={"Authorization": f"Token {self._auth_token}"},
                json=updates
            )
            self.logger.debug(f"Update response status: {response.status_code}")
            if not response.ok:
                self.logger.error(f"Update failed: {response.status_code}")
                self.logger.error(f"Response content: {response.text}")
            return response.ok
        except Exception as e:
            self.logger.error(f"Update request failed: {str(e)}")
            return False

def extract_pdf_metadata(pdf_path):
    logger.info(f"Extracting metadata from: {pdf_path}")
    try:
        reader = PdfReader(pdf_path)
        metadata = reader.metadata
        
        if not metadata:
            logger.warning(f"No metadata found in PDF: {pdf_path}")
            return {}

        logger.debug(f"Raw PDF metadata: {metadata}")
        paperless_metadata = {}
        
        # Author → Correspondent
        if metadata.get('/Author'):
            paperless_metadata['correspondent'] = metadata['/Author']
            logger.info(f"Found Author: {metadata['/Author']}")
        else:
            logger.debug("No Author field found in PDF")
        
        # Title → Title (and fallback to Subject if Title is missing)
        if metadata.get('/Title'):
            paperless_metadata['title'] = metadata['/Title']
            logger.info(f"Found Title: {metadata['/Title']}")
        elif metadata.get('/Subject'):
            paperless_metadata['title'] = metadata['/Subject']
            logger.info(f"Using Subject as Title: {metadata['/Subject']}")
        else:
            logger.debug("No Title or Subject found in PDF")
        
        # CreationDate → Created Date
        if metadata.get('/CreationDate'):
            date_str = metadata['/CreationDate']
            logger.debug(f"Found Creation Date: {date_str}")
            # Remove D: prefix and timezone if present
            date_str = date_str.replace('D:', '')[:14]  # Get YYYYMMDDHHMMSS
            try:
                date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                paperless_metadata['created'] = date.isoformat()
                logger.info(f"Parsed Creation Date: {paperless_metadata['created']}")
            except ValueError as e:
                logger.error(f"Could not parse date {date_str}: {e}")
        else:
            logger.debug("No Creation Date found in PDF")
        
        # Keywords → Tags (if present)
        if metadata.get('/Keywords'):
            tags = [tag.strip() for tag in metadata['/Keywords'].split(',')]
            paperless_metadata['tags'] = tags
            logger.info(f"Found Keywords/Tags: {tags}")
        else:
            logger.debug("No Keywords found in PDF")
        
        logger.info(f"Extracted metadata: {paperless_metadata}")
        return paperless_metadata
        
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {str(e)}", exc_info=True)
        return {}

if __name__ == "__main__":
    try:
        document_id = os.environ["DOCUMENT_ID"]
        document_source = os.environ["DOCUMENT_SOURCE_PATH"]
        
        # Get these from environment or use defaults
        api_url = os.environ.get("PAPERLESS_URL", "http://localhost:8000/api")
        auth_token = os.environ.get("PAPERLESS_TOKEN")

        if not auth_token:
            logger.error("No PAPERLESS_TOKEN found in environment")
            exit(1)

        api = SimplePaperlessAPI(api_url, auth_token)

        # Only process PDFs
        if document_source.lower().endswith('.pdf'):
            logger.info(f"Processing PDF: {document_source}")
            
            # Get PDF metadata
            metadata = extract_pdf_metadata(document_source)
            
            if metadata:
                logger.info(f"Extracted metadata: {metadata}")
                
                # Get current document data
                logger.info(f"Fetching current document {document_id} from API...")
                doc = api.get_document_by_id(document_id)
                logger.debug(f"Current document data: {doc}")
                
                # Update fields with PDF metadata (always prefer PDF metadata)
                updates = {}
                
                if metadata.get('correspondent'):
                    logger.debug(f"Processing correspondent '{metadata['correspondent']}'")
                    correspondent_id = api.get_or_create_correspondent(metadata['correspondent'])
                    if correspondent_id:
                        updates['correspondent'] = correspondent_id
                        logger.info(f"Setting correspondent to: {metadata['correspondent']} (ID: {correspondent_id})")
                    else:
                        logger.warning(f"Failed to get/create correspondent: {metadata['correspondent']}")
                
                if metadata.get('title'):
                    updates['title'] = metadata['title']
                    logger.info(f"Setting title to: {metadata['title']}")
                    
                if metadata.get('created'):
                    updates['created'] = metadata['created']
                    logger.info(f"Setting created date to: {metadata['created']}")
                    
                if metadata.get('tags'):
                    # Keep existing tags and add new ones from PDF
                    existing_tags = set(t['id'] for t in doc.get('tags', []))
                    logger.debug(f"Existing tag IDs: {existing_tags}")
                    
                    new_tag_ids = []
                    for tag_name in metadata['tags']:
                        tag_id = api.get_or_create_tag(tag_name)
                        if tag_id:
                            new_tag_ids.append(tag_id)
                            logger.debug(f"Added tag: {tag_name} (ID: {tag_id})")
                        else:
                            logger.warning(f"Failed to get/create tag: {tag_name}")
                    
                    # Combine existing and new tags
                    updates['tags'] = list(existing_tags | set(new_tag_ids))
                    logger.info(f"Final tag list: {updates['tags']}")

                if updates:
                    logger.info(f"Preparing to update document {document_id}")
                    logger.debug(f"Update payload: {updates}")
                    if api.update_document(document_id, updates):
                        logger.info("Update successful")
                    else:
                        logger.error("Failed to update document")
                        logger.error("This might be due to invalid data in the updates payload")
                else:
                    logger.info("No updates needed")
            else:
                logger.info("No metadata found in PDF")
        else:
            logger.info(f"Skipping non-PDF file: {document_source}")

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        exit(1) 