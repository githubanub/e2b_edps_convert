# E2B R3 to EDPS Converter

## Overview

This is a pharmaceutical regulatory compliance tool built with Streamlit that uses AI to detect PII fields in E2B R3 XML files and allows users to selectively apply MSK null flavor masking. The application focuses on AI-powered PII detection with user control over which fields to mask for EDPS compliance.

## User Preferences

Preferred communication style: Simple, everyday language.
Architecture preference: Simplified AI-only approach with PII detection and user selection for masking.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **Layout**: Wide layout with expandable sidebar navigation
- **Caching**: Uses `@st.cache_resource` for component initialization and configuration loading
- **File Handling**: Supports XML and ZIP file uploads with validation

### Backend Architecture
- **Simplified AI-Driven Design**: Focused on AI-powered PII detection and user-controlled masking
- **Core Components**:
  - `E2BParser`: XML parsing for E2B R3 pharmaceutical data
  - `AIPIIDetector`: AI-powered PII field detection with pattern matching and confidence scoring
  - `AzureConfig`: Re-integrated for Azure OpenAI PII detection services
- Removed: ComplianceValidator, ReportGenerator (per user request)

### Data Processing Pipeline
1. **File Upload & Validation**: Multi-format support (XML/ZIP) with content validation
2. **XML Parsing**: Extract structured data from E2B R3 format  
3. **AI PII Detection**: Automatically identify personal data fields using pattern matching and element analysis
4. **User Selection**: Interactive interface for users to choose which PII fields to mask
5. **MSK Application**: Apply MSK null flavor to selected fields and generate masked XML output

## Key Components

### E2B Parser (`e2b_parser.py`)
- **Purpose**: Parse E2B R3 XML files for pharmaceutical adverse event reports
- **Key Features**:
  - Namespace-aware XML parsing
  - Personal data element identification and extraction
  - Required element validation
  - ICH ICSR message structure support

### AI PII Detector (`ai_pii_detector.py`)
- **Purpose**: AI-powered detection of personally identifiable information in E2B R3 XML files
- **Key Features**:
  - Pattern-based PII recognition using regex and element mapping
  - Confidence scoring for detected PII fields
  - Priority classification (high/medium/low) based on data sensitivity
  - Interactive user selection interface for masking decisions
  - MSK null flavor application to selected fields
  - Support for known E2B R3 personal data elements and AI detection of unknown PII

## Data Flow

1. **Input**: User uploads E2B R3 XML files or ZIP archives
2. **Validation**: File type and content validation using magic library
3. **Parsing**: XML content extraction and structure validation
4. **AI PII Detection**: Automatic identification of personal data fields using pattern matching
5. **User Selection**: Interactive interface showing detected PII with confidence scores and priority levels
6. **MSK Application**: Apply MSK null flavor to user-selected fields
7. **Output**: Download masked XML files with personal data properly protected

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **ReportLab**: PDF generation
- **lxml/xml.etree**: XML parsing
- **pandas**: Data manipulation
- **python-magic**: File type detection

### Azure AI Integration
- **Azure OpenAI**: Advanced PII detection using GPT-4 for semantic analysis
- **Intelligent Analysis**: Context-aware detection beyond simple pattern matching
- **Fallback Support**: Automatic fallback to pattern matching if Azure AI unavailable
- **Configuration**: Environment variable based setup for security

### Compliance Framework
- **GVP Module VI Addendum II**: Regulatory compliance rules
- **EDPS Guidelines**: European data protection standards
- **ICH E2B R3**: International pharmaceutical reporting format

## Deployment Strategy

### Hybrid Deployment Strategy
- **Local Development**: Runs locally with optional Azure AI integration
- **Azure AI Enhanced**: Uses Azure OpenAI for superior PII detection when configured
- **Graceful Fallback**: Automatically uses pattern matching if Azure services unavailable
- **Flexible Configuration**: Environment variables for easy setup

The application now supports both local pattern matching and cloud-enhanced Azure AI analysis, providing the best of both worlds - local deployment simplicity with optional cloud intelligence for superior PII detection accuracy.