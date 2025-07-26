# E2B R3 to EDPS Converter

A Streamlit-based pharmaceutical regulatory compliance tool that uses AI to detect PII fields in E2B R3 XML files and allows users to selectively apply MSK null flavor masking for EDPS compliance.

## Features

- 🤖 **Azure AI-Powered PII Detection**: Uses Azure OpenAI for intelligent PII analysis with semantic understanding and high-accuracy confidence scoring
- 🎯 **User-Controlled Masking**: Interactive interface for selecting which PII fields to mask
- 📁 **Multi-Format Support**: Handles individual XML files and ZIP archives
- 🔒 **MSK Null Flavor**: Applies regulatory-compliant masking to selected fields
- 📥 **Download Functionality**: Export masked XML files for regulatory submission

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install streamlit lxml pandas python-magic reportlab openai python-dotenv
   ```

2. **Configure Azure OpenAI** (Optional - will use pattern matching fallback if not configured)
   ```bash
   # Add to Replit Secrets or environment variables:
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2023-12-01-preview
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   ```

3. **Run the Application**
   ```bash
   streamlit run app.py --server.port 5000
   ```

3. **Upload E2B R3 XML Files**
   - Upload individual XML files or ZIP archives
   - Review AI-detected PII fields with confidence scores
   - Select fields to mask with MSK null flavor
   - Download the masked XML files

## Architecture

- **Frontend**: Streamlit web application with interactive PII selection
- **Backend**: Azure OpenAI for intelligent PII detection with fallback pattern matching
- **Processing**: E2B R3 XML parsing and MSK null flavor application
- **AI Engine**: Uses Azure OpenAI GPT-4 for semantic analysis of XML elements

## Compliance

Built according to:
- **GVP Module VI Addendum II**: Personal data protection requirements
- **EDPS Guidelines**: European data protection standards
- **ICH E2B R3**: International pharmaceutical reporting format

## License

This project is designed for pharmaceutical regulatory compliance use cases.