# E2B R3 to EDPS Converter

A Streamlit-based pharmaceutical regulatory compliance tool that uses AI to detect PII fields in E2B R3 XML files and allows users to selectively apply MSK null flavor masking for EDPS compliance.

## Features

- 🤖 **AI-Powered PII Detection**: Automatically identifies personal data fields using pattern matching and confidence scoring
- 🎯 **User-Controlled Masking**: Interactive interface for selecting which PII fields to mask
- 📁 **Multi-Format Support**: Handles individual XML files and ZIP archives
- 🔒 **MSK Null Flavor**: Applies regulatory-compliant masking to selected fields
- 📥 **Download Functionality**: Export masked XML files for regulatory submission

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install streamlit lxml pandas python-magic reportlab
   ```

2. **Run the Application**
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
- **Backend**: AI pattern matching engine for PII detection
- **Processing**: E2B R3 XML parsing and MSK null flavor application

## Compliance

Built according to:
- **GVP Module VI Addendum II**: Personal data protection requirements
- **EDPS Guidelines**: European data protection standards
- **ICH E2B R3**: International pharmaceutical reporting format

## License

This project is designed for pharmaceutical regulatory compliance use cases.