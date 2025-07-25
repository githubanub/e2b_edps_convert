# E2B R3 to EDPS Converter

## Overview

This is a pharmaceutical regulatory compliance tool built with Streamlit that converts E2B R3 XML files to EDPS compliant format according to GVP Module VI Addendum II. The application focuses on ensuring proper handling of personal data elements while maintaining regulatory compliance for pharmaceutical adverse event reporting.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **Layout**: Wide layout with expandable sidebar navigation
- **Caching**: Uses `@st.cache_resource` for component initialization and configuration loading
- **File Handling**: Supports XML and ZIP file uploads with validation

### Backend Architecture
- **Modular Design**: Separated into distinct components for parsing, validation, and reporting
- **Core Components**:
  - `E2BParser`: XML parsing for E2B R3 pharmaceutical data
  - `ComplianceValidator`: EDPS compliance validation against GVP Module VI rules
  - `ReportGenerator`: PDF report generation using ReportLab
  - `AzureConfig`: Cloud configuration management

### Data Processing Pipeline
1. **File Upload & Validation**: Multi-format support (XML/ZIP) with content validation
2. **XML Parsing**: Extract structured data from E2B R3 format
3. **Compliance Validation**: Check against EDPS requirements and personal data masking rules
4. **Report Generation**: Create detailed compliance reports in PDF format

## Key Components

### E2B Parser (`e2b_parser.py`)
- **Purpose**: Parse E2B R3 XML files for pharmaceutical adverse event reports
- **Key Features**:
  - Namespace-aware XML parsing
  - Personal data element identification and extraction
  - Required element validation
  - ICH ICSR message structure support

### Compliance Validator (`compliance_validator.py`)
- **Purpose**: Validate EDPS compliance according to GVP Module VI Addendum II
- **Key Features**:
  - Personal data masking validation (MSK null flavor requirements)
  - Weighted compliance scoring system
  - Threshold-based compliance categorization (excellent/good/acceptable/poor)
  - Statistics tracking and storage

### Report Generator (`report_generator.py`)
- **Purpose**: Generate professional compliance reports
- **Key Features**:
  - PDF generation using ReportLab
  - Custom styling and formatting
  - Color-coded compliance indicators
  - Detailed validation results presentation

### Azure Configuration (`azure_config.py`)
- **Purpose**: Manage cloud deployment and local development configurations
- **Key Features**:
  - Automatic Azure deployment detection
  - Environment variable management
  - Fallback configuration support
  - Azure OpenAI and Form Recognizer integration

## Data Flow

1. **Input**: User uploads E2B R3 XML files or ZIP archives
2. **Validation**: File type and content validation using magic library
3. **Parsing**: XML content extraction and structure validation
4. **Compliance Check**: Personal data element validation against EDPS rules
5. **Scoring**: Weighted compliance score calculation
6. **Reporting**: PDF report generation with detailed findings
7. **Audit**: Activity logging for compliance tracking

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **ReportLab**: PDF generation
- **lxml/xml.etree**: XML parsing
- **pandas**: Data manipulation
- **python-magic**: File type detection

### Azure Integration
- **Azure OpenAI**: AI-powered analysis capabilities
- **Azure Form Recognizer**: Document processing
- **Azure AI Studio**: Machine learning workspace
- **Azure App Service**: Web application hosting

### Compliance Framework
- **GVP Module VI Addendum II**: Regulatory compliance rules
- **EDPS Guidelines**: European data protection standards
- **ICH E2B R3**: International pharmaceutical reporting format

## Deployment Strategy

### Local Development
- Configuration loaded from environment variables or defaults
- File-based statistics storage
- Local Streamlit server deployment

### Azure Cloud Deployment
- **Detection**: Automatic Azure environment detection via `WEBSITE_SITE_NAME`
- **Configuration**: Azure App Service environment variables
- **Scaling**: Azure App Service Plan with horizontal scaling
- **Security**: Azure Key Vault for sensitive configuration
- **Monitoring**: Azure Application Insights integration

### Infrastructure Components
- **Azure OpenAI Service**: GPT-4 model deployment for AI analysis
- **Azure Form Recognizer**: Document intelligence capabilities
- **Azure App Service**: Streamlit application hosting
- **Azure AI Studio**: ML workspace for advanced analytics

The application is designed to handle both development and production environments seamlessly, with automatic configuration switching based on the deployment context.