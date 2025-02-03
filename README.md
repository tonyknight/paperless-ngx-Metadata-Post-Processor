# Paperless-NGX PDF Metadata Sync

A simple post-processing script for Paperless-NGX that synchronizes embedded PDF metadata with Paperless-NGX fields.

## Purpose

Paperless-NGX currently ignores embedded PDF metadata when importing documents. This script automatically syncs metadata from your PDFs to Paperless-NGX, ensuring that your document's original metadata is preserved.

## Features

- **Automatic Metadata Sync**:
  - PDF Author → Paperless Correspondent
  - PDF Title → Paperless Title (falls back to Subject if Title is missing)
  - PDF Creation Date → Paperless Created Date
  - PDF Keywords → Paperless Tags

- **Metadata Priority**:
  - PDF metadata always takes precedence over Paperless-NGX values
  - Ensures original document metadata is preserved
  - Tags are merged (combines existing Paperless tags with PDF keywords)

- **Smart Processing**:
  - Creates correspondents automatically if they don't exist
  - Detailed logging for troubleshooting
  - Only processes PDF files

## Installation

1. Clone this repository into your Paperless-NGX directory:
```bash
# Navigate to your paperless-ngx directory (where docker-compose.yml is)
cd /path/to/your/paperless-ngx/

# Create a scripts directory if it doesn't exist
mkdir -p scripts

# Clone the repository
git clone https://github.com/yourusername/paperless-ngx-pdf-metadata-sync.git scripts/pdf-metadata-sync
```

2. Configure Paperless-NGX by adding to your docker-compose.yml:
```yaml
services:
  webserver:
    environment:
      - PAPERLESS_POST_CONSUME_SCRIPT=/usr/src/paperless/scripts/pdf-metadata-sync/post_consume_script.sh
    volumes:
      - ./scripts/pdf-metadata-sync:/usr/src/paperless/scripts/pdf-metadata-sync
```

3. Get your Paperless-NGX auth token:
   - Log into Paperless web interface
   - Go to Settings → Administration → Authentication Tokens
   - Click "Create Token" and copy the generated token

4. Create or edit your docker-compose.env file and add:
```env
PAPERLESS_TOKEN=your_auth_token_here
```

5. Restart Paperless-NGX to apply changes:
```bash
docker-compose down
docker-compose up -d
```

The virtual environment will be automatically created on first run.

## Verifying Installation

1. Check if the script is properly mounted:
```bash
docker-compose exec webserver ls -l /usr/src/paperless/scripts/pdf-metadata-sync
```

2. Test the metadata extraction:
```bash
docker-compose exec webserver python3 /usr/src/paperless/scripts/pdf-metadata-sync/test_pdf_metadata.py
```

3. Check the logs after adding a PDF:
```bash
docker-compose logs -f | grep "PDF-Metadata-Sync"
```

## How It Works

When Paperless-NGX imports a new PDF document:

1. The script checks if the imported file is a PDF
2. If it is a PDF, it extracts the embedded metadata:
   - Author becomes the Correspondent (creates if doesn't exist)
   - Title (or Subject as fallback) becomes the document Title
   - Creation Date becomes the document Created Date
   - Keywords become Tags (merged with existing tags)
3. Updates the Paperless-NGX document with the extracted metadata
4. Logs all actions for troubleshooting

## Metadata Handling

- **Correspondent**: PDF Author field is used to set/update the Correspondent
- **Title**: Uses PDF Title, falls back to PDF Subject if Title is missing
- **Created Date**: Uses PDF Creation Date (format: D:YYYYMMDDhhmmss)
- **Tags**: Merges any PDF Keywords with existing Paperless tags

## Troubleshooting

Check the Paperless-NGX logs for detailed processing information:
```bash
docker logs paperless-ngx | grep "PDF-Metadata-Sync"
```

The script logs:
- Which files it processes
- What metadata was found
- What updates were made
- Any errors that occur

## License

MIT License
