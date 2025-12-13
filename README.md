# Email Extractor - Broker Portfolio Holdings

A Flask web application that extracts portfolio holdings from various stock brokers' statements. Supports both manual file upload and automatic extraction from Gmail.

## Supported Brokers

- **Groww** - PDF statements
- **Zerodha** - PDF statements  
- **AngleOne** - Excel statements
- **Dhan** - PDF statements
- **MSTOCK** - PDF statements

## Features

- 📧 **Gmail Integration** - Automatically fetch latest statements from Gmail
- 📁 **Manual Upload** - Upload PDF/Excel statements manually
- 🔐 **Secure Authentication** - Google OAuth 2.0 for Gmail access
- 👥 **Multi-user Support** - Session-based authentication
- 📊 **JSON Export** - Download extracted holdings as JSON

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd am-email-extractor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
# or using uv
uv sync
```

### 3. Set Up Gmail OAuth (Optional)

If you want to use Gmail integration, follow the [Gmail OAuth Setup Guide](GMAIL_OAUTH_SETUP.md).

After getting your credentials, create a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
SESSION_SECRET=your-random-secret-key
```

### 4. Run the Application

```bash
python app.py
```

The application will be available at: `http://127.0.0.1:5000`

## Usage

### Using Gmail Integration

1. Navigate to the Gmail page: `http://127.0.0.1:5000/gmail`
2. Click "Connect Gmail" and authorize the application
3. Choose a broker page (e.g., Groww, Zerodha)
4. Click "Fetch from Gmail" and enter your PAN number
5. View and download your extracted holdings

### Using Manual Upload

1. Navigate to a broker page (e.g., `http://127.0.0.1:5000/groww`)
2. Upload your statement file (PDF or Excel)
3. Enter the password (usually your PAN number)
4. Click "Extract Holdings"
5. View and download your extracted holdings

## Password Information

- **Groww, Zerodha, MSTOCK**: PAN number (all uppercase)
- **Dhan**: PAN number (all uppercase)
- **AngleOne**: No password required for Excel files

## Project Structure

```
am-email-extractor/
├── app.py                  # Main Flask application
├── gmail_integration.py    # Gmail API integration
├── brokers/               # Broker-specific extractors
│   ├── groww/
│   ├── zerodha/
│   ├── angleone/
│   ├── dhan/
│   └── mstock/
├── templates/             # HTML templates
├── user_tokens/           # User OAuth tokens (git-ignored)
├── .env                   # Environment variables (git-ignored)
└── GMAIL_OAUTH_SETUP.md   # OAuth setup guide
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | For Gmail integration |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | For Gmail integration |
| `SESSION_SECRET` | Flask session secret key | Recommended |
| `REPLIT_DEV_DOMAIN` | Replit domain (auto-set on Replit) | For Replit deployment |

## Security Notes

⚠️ **Important**:
- Never commit your `.env` file to version control
- Keep your OAuth credentials confidential
- The `.env` file is already in `.gitignore`
- User tokens are stored locally and git-ignored

## Troubleshooting

### "Gmail credentials not found in environment variables"

- Make sure you've created a `.env` file with valid credentials
- Follow the [Gmail OAuth Setup Guide](GMAIL_OAUTH_SETUP.md)
- Restart the application after setting credentials

### Password-protected files not extracting

- Ensure you're using the correct password (usually PAN number in uppercase)
- For Groww/Zerodha statements, try your PAN number
- AngleOne Excel files typically don't require a password

### OAuth redirect URI mismatch

- Verify redirect URIs in Google Cloud Console match:
  - `http://localhost:5000/gmail/callback`
  - `http://127.0.0.1:5000/gmail/callback`

## Development

### Debug Mode

The application runs in debug mode by default with auto-reload enabled.

### Adding a New Broker

1. Create a new directory in `brokers/`
2. Implement `extract_holdings(file_path, password)` function
3. Add broker patterns to `gmail_integration.py`
4. Create HTML template in `templates/`
5. Add route in `app.py`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
