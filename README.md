
# Widiscover

Widiscover is a RAG application based on Wikipedia. It provides answers to the users on topics regarding the articles in Wikipedia. The retrieval part is based on extracting Wikipedia's content and the generation part on Generating relevant content by a powerful LLM.

## Features

- **AI-Powered Q&A**: Generate answers from Wikipedia content using Groq's LLMs
- **Configuration Management**: Flexible settings for search parameters and model selection
- **Web Interface**: Serves a Svelte-based frontend with automatic browser launch
- **Error Handling**: Comprehensive error handling for API calls and file operations
- **Environment Management**: Secure API key storage in `.env` files

## API Endpoints

- `GET /api/init` - Initialize application and check required files
- `GET /api/main` - Validate configuration and load environment
- `GET /api/config` - Retrieve current configuration
- `POST /api/config` - Update configuration and API key
- `GET /api/default` - Get default configuration values
- `POST /api/query` - Submit queries and receive AI-generated answers

## Installation

### Prerequisites

- Python 3.8+
- Groq API key (get one at [https://console.groq.com/keys](https://console.groq.com/keys))

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/christos-golsouzidis/widiscover/
   cd ./widiscover
   ```

2. Install dependencies on a python virtual environment:
   ```bash
   pip install fastapi uvicorn aiofiles dotenv groq pydantic
   ```
   or by using uv:
   ```bash
   uv add fastapi uvicorn aiofiles dotenv groq pydantic
   ```

3. Ensure that the `widiscover_core` package is available in your Python environment.

4. Build the frontend:
   ```bash
   # Navigate to ui/ directory and build the Svelte app
   cd ui
   npm run build
   cd ..
   ```

## Configuration

### Environment Variables

You can optionally create an `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```
Alternatively you can skip this step as by running the application you will be redirected to the settings (`/config`) and by providing the API key the `.env` file will be created automatically.

### Configuration Settings

The application uses a `config.json` file with the following adjustable parameters:

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `configResultNumberPerPage` | Number of Wikipedia results per page | 1-10 | 3 |
| `configChunkLength` | Text chunk length for processing | 100-10000 | 1800 |
| `configChunkOverlap` | Overlap between text chunks | 0-2000 | 180 |
| `configTopKResults` | Top K results to consider | 1-16 | 4 |
| `configThreshold` | Relevance threshold for filtering | 0.0-0.75 | 0.3 |
| `configDistance` | Spelling distance tolerance | 0-2 | 1 |
| `configGenerativeModel` | Groq model to use | See below | `llama-3.3-70b-versatile` |

### Available Models

- `compound-beta`
- `compound-beta-mini`
- `gemma2-9b-it`
- `llama-3.1-8b-instant`
- `llama-3.3-70b-versatile`
- `meta-llama/llama-4-maverick-17b-128e-instruct`
- `meta-llama/llama-4-scout-17b-16e-instruct`
- `meta-llama/llama-guard-4-12b`
- `moonshotai/kimi-k2-instruct`
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`
- `qwen/qwen3-32b`

## Usage

### Starting the Server

Run the application directly:
```bash
python main.py
```
Alternatively you can execute on Linux the following command:
```bash
./widiscover
```

The server will:
1. Start on `http://127.0.0.1:7454`
2. Open your default web browser automatically
3. Check for required configuration files
4. Redirect to setup if configuration is missing, otherwise to the main page.

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `303`: Redirect required (configuration needed)
- `400`: Bad request (invalid input or configuration)
- `401`: Authentication error (invalid API key)
- `403`: Permission denied
- `429`: Rate limit exceeded

## File Structure

```
.
├── main.py              # Main application file
├── config.json          # Configuration file (auto-generated)
├── .env                 # Environment variables (auto-generated)
├── ui/
│   └── build/          # Frontend build files
│       ├── _app/
│       └── index.html
│       └── main.html
│       └── config.html
|
└── README.md           # This file
```

## Troubleshooting

### Common Issues

1. **"Cannot create 'config.json' file"**: Check write permissions in the directory
2. **"Authentication error"**: Verify your Groq API key in the `.env` file
3. **"Too Many Requests"**: You've exceeded Groq's rate limits
4. **Frontend not loading**: Ensure the UI build files exist in `ui/build/`

### Logs

Check the console output for error messages and server status.

## Version

Current version: 2.4

## License

Apache Lisence 2.0
