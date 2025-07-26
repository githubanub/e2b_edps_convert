import streamlit as st
import os
import zipfile
import tempfile
from io import BytesIO
import pandas as pd
from datetime import datetime
import json

from e2b_parser import E2BParser
from ai_pii_detector import AIPIIDetector
from utils import validate_file_type, format_file_size, create_audit_log

# Page configuration
st.set_page_config(
    page_title="E2B R3 to EDPS Converter",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize application components"""
    parser = E2BParser()
    ai_detector = AIPIIDetector()
    return parser, ai_detector

def main():
    """Main application interface"""
    st.title("🏥 E2B R3 to EDPS Converter")
    st.markdown("### Pharmaceutical Regulatory Compliance Tool")
    st.markdown("*Convert E2B R3 XML files to EDPS compliant format according to GVP Module VI Addendum II*")
    
    # Initialize components
    parser, ai_detector = init_components()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("AI PII Detection")
        st.markdown("### About")
        st.info("Upload E2B R3 XML files to automatically detect personal data fields using AI. Select which fields to mask with MSK null flavor.")
        
        st.markdown("### System Status")
        st.success("✅ AI PII Detector Ready")
        
        st.markdown("### Supported Files")
        st.markdown("- XML files (E2B R3 format)")
        st.markdown("- ZIP archives with XML files")
    
    # Main content
    file_upload_page(parser, ai_detector)

def file_upload_page(parser, ai_detector):
    """File upload and processing page"""
    st.header("📁 File Upload & Processing")
    
    # File upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Upload E2B R3 XML Files or ZIP Archives",
            type=['xml', 'zip'],
            accept_multiple_files=True,
            help="Upload individual XML files or ZIP archives containing multiple E2B R3 files"
        )
    
    with col2:
        st.markdown("### Supported Formats")
        st.markdown("- **XML**: E2B R3 individual files")
        st.markdown("- **ZIP**: Archives with multiple XML files")
        st.markdown("### File Size Limits")
        st.markdown("- Individual files: 50MB max")
        st.markdown("- ZIP archives: 200MB max")
    
    if uploaded_files:
        st.markdown("---")
        st.subheader("📋 File Processing Results")
        
        # Process files
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name} ({format_file_size(uploaded_file.size)})", expanded=True):
                try:
                    # Validate file type
                    if not validate_file_type(uploaded_file):
                        st.error("❌ Invalid file type or corrupted file")
                        continue
                    
                    # Process based on file type
                    if uploaded_file.name.endswith('.zip'):
                        process_zip_file_with_ai(uploaded_file, parser, ai_detector)
                    else:
                        process_single_file_with_ai(uploaded_file, parser, ai_detector)
                        
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    create_audit_log("error", f"File processing failed: {uploaded_file.name}", str(e))

def process_single_file_with_ai(uploaded_file, parser, ai_detector):
    """Process a single XML file with AI PII detection"""
    start_time = datetime.now()
    
    # Parse XML
    with st.spinner("Parsing XML structure..."):
        xml_content = uploaded_file.read().decode('utf-8')
        uploaded_file.seek(0)  # Reset file pointer
        parsed_data = parser.parse_e2b_xml(xml_content)
    
    if not parsed_data['success']:
        st.error(f"❌ XML Parsing failed: {parsed_data['error']}")
        return
    
    st.success("✅ XML structure validated successfully")
    
    # Display file information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File Size", format_file_size(len(xml_content.encode('utf-8'))))
    with col2:
        st.metric("XML Elements", parsed_data['element_count'])
    with col3:
        st.metric("Data Fields", parsed_data['field_count'])
    
    # AI PII Detection
    with st.spinner("🤖 Detecting PII fields with AI..."):
        detected_pii = ai_detector.detect_pii_fields(parsed_data['data'])
    
    # Display PII detection results
    st.subheader("🤖 AI PII Detection Results")
    
    if not detected_pii:
        st.info("No PII fields detected in this file.")
        return
    
    # Display summary metrics
    pii_summary = ai_detector.generate_pii_summary(detected_pii)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total PII Fields", pii_summary['total_pii_fields'])
    with col2:
        st.metric("High Priority", pii_summary['high_priority'])
    with col3:
        st.metric("Already Masked", pii_summary['already_masked'])
    with col4:
        st.metric("Avg Confidence", f"{pii_summary['avg_confidence']:.1%}")
    
    # Interactive PII field selection
    st.subheader("🔍 Select Fields to Mask")
    st.markdown("Review the PII fields detected by AI and select which ones to apply MSK null flavor:")
    
    # Create selection interface
    selected_fields = []
    
    for i, field in enumerate(detected_pii):
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        
        with col1:
            # Priority indicator
            priority_color = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢'
            }
            st.write(priority_color.get(field['priority'], '⚪'))
        
        with col2:
            st.write(f"**{field['element_tag']}**")
            st.caption(field['description'])
        
        with col3:
            st.write(f"*{field['element_text'][:30]}...*" if len(field['element_text']) > 30 else f"*{field['element_text']}*")
            st.caption(f"Confidence: {field['confidence']:.1%}")
        
        with col4:
            if field['has_msk_applied']:
                st.success("MSK Applied ✅")
                field['selected_for_masking'] = False
            else:
                field['selected_for_masking'] = st.checkbox(
                    "Apply MSK",
                    value=field.get('selected_for_masking', False),
                    key=f"mask_{i}_{uploaded_file.name}"
                )
        
        if field.get('selected_for_masking', False):
            selected_fields.append(field)
    
    # Show recommendations
    recommendations = ai_detector.get_masking_recommendations(detected_pii)
    if recommendations:
        st.subheader("💡 AI Recommendations")
        for rec in recommendations:
            if "CRITICAL" in rec:
                st.error(rec)
            elif "IMPORTANT" in rec:
                st.warning(rec)
            else:
                st.info(rec)
    
    # Apply masking if fields are selected
    if selected_fields:
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🛡️ Apply MSK Masking", type="primary"):
                with st.spinner("Applying MSK null flavor to selected fields..."):
                    masked_xml = ai_detector.apply_msk_masking(xml_content, selected_fields)
                    
                    # Store the masked XML in session state
                    st.session_state[f'masked_xml_{uploaded_file.name}'] = masked_xml
                    
                    st.success(f"✅ Applied MSK to {len(selected_fields)} fields")
                    
                    # Show before/after comparison
                    st.subheader("📊 Masking Results")
                    for field in selected_fields:
                        st.write(f"✅ Masked: **{field['element_tag']}** - *{field['element_text']}*")
        
        with col2:
            # Download masked XML
            if f'masked_xml_{uploaded_file.name}' in st.session_state:
                masked_xml = st.session_state[f'masked_xml_{uploaded_file.name}']
                st.download_button(
                    label="📥 Download Masked XML",
                    data=masked_xml.encode('utf-8'),
                    file_name=f"masked_{uploaded_file.name}",
                    mime="application/xml"
                )

def process_zip_file_with_ai(uploaded_file, parser, ai_detector):
    """Process ZIP file containing multiple XML files with AI PII detection"""
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
            
            if not xml_files:
                st.error("❌ No XML files found in ZIP archive")
                return
            
            st.info(f"📦 Found {len(xml_files)} XML files in archive")
            
            # Process each XML file in the archive
            for i, xml_file in enumerate(xml_files):
                st.markdown(f"### Processing: {xml_file}")
                
                try:
                    with zip_ref.open(xml_file) as f:
                        xml_content = f.read().decode('utf-8')
                    
                    # Create a temporary file object
                    temp_file = BytesIO(xml_content.encode('utf-8'))
                    temp_file.name = xml_file
                    
                    # Process with AI detection
                    with st.expander(f"📄 {xml_file}", expanded=True):
                        process_single_file_with_ai(temp_file, parser, ai_detector)
                        
                except Exception as e:
                    st.error(f"❌ Error processing {xml_file}: {str(e)}")
            
    except zipfile.BadZipFile:
        st.error("❌ Invalid or corrupted ZIP file")

# Old functions removed - now using simplified AI-based approach

if __name__ == "__main__":
    main()
