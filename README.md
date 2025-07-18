# WhatsApp Flow Tester

A dynamic, scalable WhatsApp flow testing framework that allows you to test various WhatsApp automation flows without code changes.

## Features

- 🚀 **Dynamic Flow Discovery**: Automatically discovers and loads flow templates
- 📱 **Multi-Tool Support**: Text, Location, Image, and Voice message testing
- 🧠 **LLM-Powered Analysis**: OpenAI integration for intelligent step parsing
- 📊 **Excel Integration**: Load employee data from Excel files
- 🔄 **Interactive Menu**: User-friendly flow selection interface
- 📝 **Comprehensive Logging**: Detailed execution tracking and reporting
- 🎯 **Flexible Configuration**: Environment-based configuration management

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the Tester**
   ```bash
   python -m src.flow_tester.main
   ```

## Project Structure

```
whatsapp-flow-tester/
├── src/flow_tester/          # Main application code
├── flows/                    # Flow template definitions
├── data/                     # Employee data files
├── media/                    # Media files for testing
├── results/                  # Execution logs and reports
└── docs/                     # Documentation
```

## Adding New Flows

1. Create a new JSON file in `flows/` directory
2. Define your flow steps and configuration
3. Run the tester - it will automatically discover your new flow

See `docs/adding_flows.md` for detailed instructions.

## Configuration

All configuration is handled through environment variables in `.env`:
- `WHATSAPP_ACCESS_TOKEN`: Your WhatsApp Business API token
- `WHATSAPP_PHONE_NUMBER_ID`: Your WhatsApp phone number ID
- `OPENAI_API_KEY`: OpenAI API key for LLM analysis
- `NESTJS_SERVER_URL`: Your webhook server URL
- `MESSAGE_API_URL`: Message API endpoint

## License

MIT License
