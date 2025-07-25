import streamlit as st
import os
import zipfile
import tempfile
from io import BytesIO
import pandas as pd
from datetime import datetime
import json

from e2b_parser import E2BParser
from compliance_validator import ComplianceValidator
from report_generator import ReportGenerator
from azure_config import AzureConfig
from utils import validate_file_type, format_file_size, create_audit_log

# Page configuration
st.set_page_config(
    page_title="E2B R3 to EDPS Converter",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Azure configuration
@st.cache_resource
def init_azure_config():
    """Initialize Azure configuration"""
    return AzureConfig()

# Initialize components
@st.cache_resource
def init_components():
    """Initialize application components"""
    azure_config = init_azure_config()
    parser = E2BParser()
    validator = ComplianceValidator()
    report_generator = ReportGenerator()
    return parser, validator, report_generator, azure_config

def main():
    """Main application interface"""
    st.title("🏥 E2B R3 to EDPS Converter")
    st.markdown("### Pharmaceutical Regulatory Compliance Tool")
    st.markdown("*Convert E2B R3 XML files to EDPS compliant format according to GVP Module VI Addendum II*")
    
    # Initialize components
    parser, validator, report_generator, azure_config = init_components()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Select Function",
            ["File Upload & Processing", "Compliance Dashboard", "Batch Processing", "Regulatory Guidance", "Audit Trail"]
        )
        
        st.markdown("---")
        st.markdown("### Current Regulations")
        st.info("**GVP Module VI Addendum II**\nEffective: July 25, 2025\nEDPS Recommended Format")
        
        st.markdown("### System Status")
        try:
            config = azure_config.get_config()
            if config:
                st.success("✅ Azure Services Connected")
            else:
                st.warning("⚠️ Running in Local Mode")
        except Exception as e:
            st.error(f"❌ Configuration Error: {str(e)}")
    
    # Main content based on selected page
    if page == "File Upload & Processing":
        file_upload_page(parser, validator, report_generator)
    elif page == "Compliance Dashboard":
        compliance_dashboard_page(validator)
    elif page == "Batch Processing":
        batch_processing_page(parser, validator, report_generator)
    elif page == "Regulatory Guidance":
        regulatory_guidance_page()
    elif page == "Audit Trail":
        audit_trail_page()

def file_upload_page(parser, validator, report_generator):
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
        processing_results = []
        
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name} ({format_file_size(uploaded_file.size)})"):
                try:
                    # Validate file type
                    if not validate_file_type(uploaded_file):
                        st.error("❌ Invalid file type or corrupted file")
                        continue
                    
                    # Process based on file type
                    if uploaded_file.name.endswith('.zip'):
                        results = process_zip_file(uploaded_file, parser, validator, report_generator)
                        processing_results.extend(results)
                    else:
                        result = process_single_file(uploaded_file, parser, validator, report_generator)
                        processing_results.append(result)
                        
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    create_audit_log("error", f"File processing failed: {uploaded_file.name}", str(e))
        
        # Display summary
        if processing_results:
            display_processing_summary(processing_results, report_generator)

def process_single_file(uploaded_file, parser, validator, report_generator):
    """Process a single XML file"""
    start_time = datetime.now()
    
    # Parse XML
    with st.spinner("Parsing XML structure..."):
        xml_content = uploaded_file.read().decode('utf-8')
        parsed_data = parser.parse_e2b_xml(xml_content)
    
    if not parsed_data['success']:
        st.error(f"❌ XML Parsing failed: {parsed_data['error']}")
        return None
    
    st.success("✅ XML structure validated successfully")
    
    # Display file information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File Size", format_file_size(len(xml_content.encode('utf-8'))))
    with col2:
        st.metric("XML Elements", parsed_data['element_count'])
    with col3:
        st.metric("Data Fields", parsed_data['field_count'])
    
    # Validate compliance
    with st.spinner("Validating EDPS compliance..."):
        compliance_result = validator.validate_compliance(parsed_data['data'])
    
    # Display compliance results
    st.subheader("🔍 Compliance Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Compliance Score", f"{compliance_result['compliance_score']:.1%}")
    with col2:
        st.metric("Personal Data Fields", compliance_result['personal_data_count'])
    with col3:
        st.metric("MSK Applied", compliance_result['msk_applied_count'])
    with col4:
        st.metric("Issues Found", len(compliance_result['issues']))
    
    # Progress bar for compliance score
    st.progress(compliance_result['compliance_score'])
    
    # Display issues if any
    if compliance_result['issues']:
        st.warning("⚠️ Compliance Issues Detected")
        for i, issue in enumerate(compliance_result['issues'], 1):
            st.error(f"{i}. {issue}")
    
    # Display personal data findings
    if compliance_result['personal_data_fields']:
        st.subheader("🔒 Personal Data Analysis")
        df = pd.DataFrame(compliance_result['personal_data_fields'])
        st.dataframe(df, use_container_width=True)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Generate report
    report_data = report_generator.generate_compliance_report(
        uploaded_file.name,
        parsed_data,
        compliance_result,
        processing_time
    )
    
    # Download button for report
    st.download_button(
        label="📥 Download Compliance Report (PDF)",
        data=report_data,
        file_name=f"compliance_report_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )
    
    # Create audit log
    create_audit_log(
        "file_processed",
        f"File: {uploaded_file.name}",
        f"Compliance Score: {compliance_result['compliance_score']:.1%}, Issues: {len(compliance_result['issues'])}"
    )
    
    return {
        'filename': uploaded_file.name,
        'compliance_score': compliance_result['compliance_score'],
        'issues_count': len(compliance_result['issues']),
        'processing_time': processing_time,
        'personal_data_count': compliance_result['personal_data_count']
    }

def process_zip_file(uploaded_file, parser, validator, report_generator):
    """Process ZIP file containing multiple XML files"""
    results = []
    
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
            
            if not xml_files:
                st.error("❌ No XML files found in ZIP archive")
                return results
            
            st.info(f"📦 Found {len(xml_files)} XML files in archive")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, xml_file in enumerate(xml_files):
                status_text.text(f"Processing {xml_file}...")
                progress_bar.progress((i + 1) / len(xml_files))
                
                try:
                    with zip_ref.open(xml_file) as f:
                        xml_content = f.read().decode('utf-8')
                    
                    # Create a temporary file object
                    temp_file = BytesIO(xml_content.encode('utf-8'))
                    temp_file.name = xml_file
                    
                    result = process_single_file(temp_file, parser, validator, report_generator)
                    if result:
                        results.append(result)
                        
                except Exception as e:
                    st.error(f"❌ Error processing {xml_file}: {str(e)}")
            
            status_text.text("✅ All files processed")
            
    except zipfile.BadZipFile:
        st.error("❌ Invalid or corrupted ZIP file")
    
    return results

def display_processing_summary(results, report_generator):
    """Display summary of processing results"""
    st.markdown("---")
    st.subheader("📊 Processing Summary")
    
    if not results:
        st.warning("No files were successfully processed")
        return
    
    # Calculate summary statistics
    total_files = len(results)
    avg_compliance = sum(r['compliance_score'] for r in results) / total_files
    total_issues = sum(r['issues_count'] for r in results)
    avg_processing_time = sum(r['processing_time'] for r in results) / total_files
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Files Processed", total_files)
    with col2:
        st.metric("Average Compliance", f"{avg_compliance:.1%}")
    with col3:
        st.metric("Total Issues", total_issues)
    with col4:
        st.metric("Avg. Processing Time", f"{avg_processing_time:.2f}s")
    
    # Results table
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)
    
    # Generate batch report
    if st.button("📥 Generate Batch Report"):
        batch_report = report_generator.generate_batch_report(results)
        st.download_button(
            label="📥 Download Batch Report (PDF)",
            data=batch_report,
            file_name=f"batch_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )

def compliance_dashboard_page(validator):
    """Compliance dashboard page"""
    st.header("📊 Compliance Dashboard")
    
    # Load compliance statistics
    stats = validator.get_compliance_statistics()
    
    if not stats:
        st.info("No compliance data available. Please process some files first.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Files Processed", stats.get('total_files', 0))
    with col2:
        st.metric("Average Compliance Score", f"{stats.get('avg_compliance', 0):.1%}")
    with col3:
        st.metric("Files with Issues", stats.get('files_with_issues', 0))
    with col4:
        st.metric("Total Personal Data Fields", stats.get('total_personal_data', 0))
    
    # Compliance distribution chart
    st.subheader("📈 Compliance Score Distribution")
    if 'compliance_distribution' in stats:
        chart_data = pd.DataFrame(stats['compliance_distribution'])
        st.bar_chart(chart_data.set_index('range')['count'])
    
    # Common issues
    st.subheader("⚠️ Most Common Issues")
    if 'common_issues' in stats:
        for issue, count in stats['common_issues'].items():
            st.write(f"• {issue}: {count} occurrences")

def batch_processing_page(parser, validator, report_generator):
    """Batch processing page"""
    st.header("⚙️ Batch Processing")
    st.markdown("Process multiple files with automated compliance checking")
    
    # Batch upload
    uploaded_files = st.file_uploader(
        "Upload Multiple Files for Batch Processing",
        type=['xml', 'zip'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Processing options
        st.subheader("Processing Options")
        
        col1, col2 = st.columns(2)
        with col1:
            stop_on_error = st.checkbox("Stop processing on first error", value=False)
            generate_individual_reports = st.checkbox("Generate individual reports", value=True)
        with col2:
            compliance_threshold = st.slider("Minimum compliance score", 0.0, 1.0, 0.8, 0.1)
            notify_issues = st.checkbox("Highlight files with issues", value=True)
        
        if st.button("🚀 Start Batch Processing"):
            batch_results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                try:
                    if uploaded_file.name.endswith('.zip'):
                        results = process_zip_file(uploaded_file, parser, validator, report_generator)
                        batch_results.extend(results)
                    else:
                        result = process_single_file(uploaded_file, parser, validator, report_generator)
                        if result:
                            batch_results.append(result)
                            
                    # Check if we should stop on error
                    if stop_on_error and batch_results and batch_results[-1]['issues_count'] > 0:
                        st.warning(f"Stopping batch processing due to issues in {uploaded_file.name}")
                        break
                        
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    if stop_on_error:
                        break
            
            status_text.text("✅ Batch processing completed")
            
            # Display batch results
            if batch_results:
                display_processing_summary(batch_results, report_generator)
                
                # Highlight files below threshold
                if notify_issues:
                    low_compliance_files = [r for r in batch_results if r['compliance_score'] < compliance_threshold]
                    if low_compliance_files:
                        st.warning(f"⚠️ {len(low_compliance_files)} files below compliance threshold ({compliance_threshold:.1%})")
                        for file_info in low_compliance_files:
                            st.error(f"• {file_info['filename']}: {file_info['compliance_score']:.1%} compliance")

def regulatory_guidance_page():
    """Regulatory guidance page"""
    st.header("📋 Regulatory Guidance")
    
    # GVP Module VI Addendum II guidance
    st.subheader("🏛️ GVP Module VI Addendum II Requirements")
    
    with st.expander("📖 Overview", expanded=True):
        st.markdown("""
        **Good Vigilance Practice (GVP) Module VI Addendum II** establishes requirements for:
        
        - **Personal Data Protection**: Implementation of MSK null flavors for personal data elements
        - **EDPS Compliance**: Alignment with European Data Protection Supervisor guidelines
        - **EudraVigilance Submission**: Standardized format for regulatory submissions
        - **Data Minimization**: Reduction of personal data in safety reports
        """)
    
    with st.expander("🔒 MSK Null Flavor Application"):
        st.markdown("""
        **MSK (Masked) Null Flavor** should be applied to the following E2B R3 elements:
        
        1. **Patient Information**
           - Patient initials (A.2.1.1)
           - Patient birth date (A.2.1.4)
           - Patient address details
        
        2. **Reporter Information**
           - Reporter name (A.3.1.2)
           - Reporter address (A.3.1.3)
           - Reporter telephone/fax (A.3.1.4)
        
        3. **Healthcare Professional Information**
           - HCP name
           - HCP address
           - HCP contact details
        
        **Implementation**: `nullFlavor="MSK"`
        """)
    
    with st.expander("✅ Compliance Checklist"):
        st.markdown("""
        **Pre-Submission Checklist:**
        
        - [ ] All personal data elements identified
        - [ ] MSK null flavors correctly applied
        - [ ] XML structure validates against E2B R3 schema
        - [ ] Compliance score ≥ 80%
        - [ ] No critical validation errors
        - [ ] Audit trail generated
        - [ ] Report reviewed and approved
        """)
    
    # Compliance scoring explanation
    st.subheader("📊 Compliance Scoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Scoring Criteria:**
        - Personal data identification: 30%
        - MSK application completeness: 40%
        - XML structure validity: 20%
        - Regulatory alignment: 10%
        """)
    
    with col2:
        st.markdown("""
        **Score Interpretation:**
        - 90-100%: Excellent compliance
        - 80-89%: Good compliance
        - 70-79%: Acceptable with minor issues
        - <70%: Requires significant review
        """)

def audit_trail_page():
    """Audit trail page"""
    st.header("📋 Audit Trail")
    
    # Load audit logs
    try:
        with open('audit_log.json', 'r') as f:
            audit_logs = json.load(f)
    except FileNotFoundError:
        audit_logs = []
    
    if not audit_logs:
        st.info("No audit entries found.")
        return
    
    # Display filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox(
            "Filter by Action",
            ["All"] + list(set(log['action'] for log in audit_logs))
        )
    
    with col2:
        date_filter = st.date_input("Filter by Date")
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Filter logs
    filtered_logs = audit_logs
    if action_filter != "All":
        filtered_logs = [log for log in filtered_logs if log['action'] == action_filter]
    
    # Display logs
    st.subheader(f"📋 Audit Entries ({len(filtered_logs)} items)")
    
    for log in reversed(filtered_logs[-100:]):  # Show last 100 entries
        with st.expander(f"{log['timestamp']} - {log['action']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Action:** {log['action']}")
                st.write(f"**Description:** {log['description']}")
            with col2:
                st.write(f"**Timestamp:** {log['timestamp']}")
                if log.get('details'):
                    st.write(f"**Details:** {log['details']}")

if __name__ == "__main__":
    main()
