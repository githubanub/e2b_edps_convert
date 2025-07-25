import json
import os
import magic
import zipfile
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import streamlit as st

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_file_type(uploaded_file) -> bool:
    """
    Validate uploaded file type and integrity
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        True if file is valid, False otherwise
    """
    try:
        # Check file extension
        filename = uploaded_file.name.lower()
        allowed_extensions = ['.xml', '.zip']
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return False
        
        # Read file content for validation
        file_content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer
        
        # Validate based on file type
        if filename.endswith('.xml'):
            return validate_xml_content(file_content)
        elif filename.endswith('.zip'):
            return validate_zip_content(file_content)
        
        return False
        
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False

def validate_xml_content(content: bytes) -> bool:
    """
    Validate XML content
    
    Args:
        content: File content as bytes
        
    Returns:
        True if valid XML, False otherwise
    """
    try:
        # Try to decode as UTF-8
        xml_string = content.decode('utf-8')
        
        # Basic XML structure check
        if not xml_string.strip().startswith('<?xml') and not xml_string.strip().startswith('<'):
            return False
        
        # Check for E2B specific elements (basic check)
        e2b_indicators = ['ichicsr', 'safetyreport', 'messageheader']
        has_e2b_elements = any(indicator in xml_string.lower() for indicator in e2b_indicators)
        
        return has_e2b_elements
        
    except UnicodeDecodeError:
        logger.warning("File is not valid UTF-8 encoded XML")
        return False
    except Exception as e:
        logger.error(f"XML validation error: {str(e)}")
        return False

def validate_zip_content(content: bytes) -> bool:
    """
    Validate ZIP file content
    
    Args:
        content: File content as bytes
        
    Returns:
        True if valid ZIP with XML files, False otherwise
    """
    try:
        # Check if it's a valid ZIP file
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Check if ZIP contains at least one XML file
            xml_files = [f for f in file_list if f.lower().endswith('.xml')]
            
            if not xml_files:
                logger.warning("ZIP file contains no XML files")
                return False
            
            # Validate at least one XML file in the ZIP
            for xml_file in xml_files[:3]:  # Check first 3 XML files
                try:
                    with zip_ref.open(xml_file) as f:
                        xml_content = f.read()
                        if validate_xml_content(xml_content):
                            return True
                except Exception as e:
                    logger.warning(f"Error validating {xml_file} in ZIP: {str(e)}")
                    continue
            
            return False
            
    except zipfile.BadZipFile:
        logger.warning("File is not a valid ZIP archive")
        return False
    except Exception as e:
        logger.error(f"ZIP validation error: {str(e)}")
        return False

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes = size_bytes / 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def create_audit_log(action: str, description: str, details: str = "") -> None:
    """
    Create an audit log entry
    
    Args:
        action: Action performed
        description: Description of the action
        details: Additional details
    """
    try:
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "description": description,
            "details": details,
            "user_session": st.session_state.get('session_id', 'unknown')
        }
        
        # Load existing audit log
        audit_log = []
        if os.path.exists('audit_log.json'):
            try:
                with open('audit_log.json', 'r') as f:
                    audit_log = json.load(f)
            except Exception as e:
                logger.error(f"Error loading audit log: {str(e)}")
                audit_log = []
        
        # Add new entry
        audit_log.append(audit_entry)
        
        # Keep only last 1000 entries
        if len(audit_log) > 1000:
            audit_log = audit_log[-1000:]
        
        # Save updated audit log
        with open('audit_log.json', 'w') as f:
            json.dump(audit_log, f, indent=2)
            
        logger.info(f"Audit log entry created: {action} - {description}")
        
    except Exception as e:
        logger.error(f"Error creating audit log entry: {str(e)}")

def get_session_id() -> str:
    """
    Get or create a session ID
    
    Returns:
        Session ID string
    """
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.now())}"
    
    return st.session_state.session_id

def validate_e2b_element_codes() -> Dict[str, str]:
    """
    Get mapping of E2B R3 element codes to descriptions
    
    Returns:
        Dictionary mapping element codes to descriptions
    """
    return {
        'A.1.0.1': 'Sender Safety Report Unique Identifier',
        'A.1.1': 'Date of Creation',
        'A.1.2': 'Type of Report',
        'A.1.3': 'Date of Most Recent Information',
        'A.1.4': 'Additional Document Available',
        'A.1.5.1': 'Fulfil Expedited Reporting Criteria',
        'A.1.5.2': 'Fulfil Expedited Reporting Criteria',
        'A.1.6': 'Other Case Identifiers in Previous Transmissions',
        'A.1.7': 'Linked Report',
        'A.1.8.1': 'Report Classification for Submission',
        'A.1.8.2': 'Report Classification for Submission',
        'A.1.9': 'Geographic Location(s) for Regulatory Purpose',
        'A.1.10.1': 'Worldwide Unique Case Identification Number',
        'A.1.10.2': 'First Sender of this Case',
        'A.1.11.1': 'Report Nullification/Amendment',
        'A.1.11.2': 'Reason for Nullification/Amendment',
        'A.1.12': 'Case Safety Report Version',
        'A.1.13': 'Other Case Identifiers',
        'A.2.1.1': 'Patient (name or initials)',
        'A.2.1.1a': 'Patient Identifier',
        'A.2.1.1b': 'GP Medical Record Number',
        'A.2.1.1c': 'Specialist Record Number',
        'A.2.1.1d': 'Hospital Record Number',
        'A.2.1.1e': 'Investigation Number',
        'A.2.1.2': 'Date of Birth',
        'A.2.1.3': 'Age Information',
        'A.2.1.4': 'Patient Sex',
        'A.2.2': 'Medical History',
        'A.2.3': 'Concurrent Conditions',
        'A.3.1.1': 'Reporter Country',
        'A.3.1.2': 'Reporter Name',
        'A.3.1.3': 'Reporter Address',
        'A.3.1.4': 'Reporter Telephone',
        'A.3.1.5': 'Reporter Fax',
        'A.3.1.6': 'Reporter Email',
        'A.3.2.1': 'Reporter Qualification',
        'A.3.2.2': 'Primary Reporter',
        'A.3.2.3': 'Literature Reference',
        'A.3.3': 'Study Identification'
    }

def get_msk_application_rules() -> Dict[str, Dict[str, Any]]:
    """
    Get MSK null flavor application rules according to GVP Module VI Addendum II
    
    Returns:
        Dictionary with MSK application rules
    """
    return {
        'A.2.1.1': {
            'name': 'Patient Name/Initials',
            'msk_required': True,
            'rationale': 'Direct personal identifier',
            'priority': 'high'
        },
        'A.2.1.2': {
            'name': 'Patient Date of Birth',
            'msk_required': True,
            'rationale': 'Personal identifier that can lead to identification',
            'priority': 'high'
        },
        'A.3.1.2': {
            'name': 'Reporter Name',
            'msk_required': True,
            'rationale': 'Personal identifier of healthcare professional',
            'priority': 'high'
        },
        'A.3.1.3': {
            'name': 'Reporter Address',
            'msk_required': True,
            'rationale': 'Location data that can identify individual',
            'priority': 'medium'
        },
        'A.3.1.4': {
            'name': 'Reporter Telephone',
            'msk_required': True,
            'rationale': 'Direct contact information',
            'priority': 'medium'
        },
        'A.3.1.5': {
            'name': 'Reporter Fax',
            'msk_required': True,
            'rationale': 'Direct contact information',
            'priority': 'low'
        },
        'A.3.1.6': {
            'name': 'Reporter Email',
            'msk_required': True,
            'rationale': 'Direct contact information',
            'priority': 'medium'
        }
    }

def calculate_compliance_score(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate detailed compliance score breakdown
    
    Args:
        validation_results: Results from compliance validation
        
    Returns:
        Detailed scoring breakdown
    """
    scoring = {
        'msk_application': {
            'weight': 0.4,
            'score': 0.0,
            'max_points': 100
        },
        'data_minimization': {
            'weight': 0.3,
            'score': 0.0,
            'max_points': 100
        },
        'structure_compliance': {
            'weight': 0.3,
            'score': 0.0,
            'max_points': 100
        }
    }
    
    # Calculate MSK application score
    msk_validation = validation_results.get('msk_validation', {})
    required_elements = msk_validation.get('elements_requiring_msk', 0)
    correct_elements = msk_validation.get('elements_with_msk', 0)
    
    if required_elements > 0:
        scoring['msk_application']['score'] = (correct_elements / required_elements) * 100
    else:
        scoring['msk_application']['score'] = 100  # No personal data requiring MSK
    
    # Calculate data minimization score
    data_min = validation_results.get('data_minimization', {})
    total_elements = data_min.get('elements_with_data', 0)
    unnecessary_elements = data_min.get('optional_elements_with_data', 0)
    
    if total_elements > 0:
        minimization_ratio = 1 - (unnecessary_elements / total_elements)
        scoring['data_minimization']['score'] = max(0, minimization_ratio * 100)
    else:
        scoring['data_minimization']['score'] = 100
    
    # Calculate structure compliance score
    structure_comp = validation_results.get('structure_compliance', {})
    scoring['structure_compliance']['score'] = structure_comp.get('score', 0) * 100
    
    # Calculate weighted overall score
    overall_score = sum(
        (scoring[category]['score'] * scoring[category]['weight'])
        for category in scoring
    )
    
    return {
        'overall_score': overall_score / 100,  # Convert to 0-1 scale
        'category_scores': scoring,
        'score_breakdown': {
            'msk_application': scoring['msk_application']['score'],
            'data_minimization': scoring['data_minimization']['score'],
            'structure_compliance': scoring['structure_compliance']['score']
        }
    }

def generate_compliance_recommendations(compliance_results: Dict[str, Any]) -> List[str]:
    """
    Generate specific compliance recommendations
    
    Args:
        compliance_results: Compliance validation results
        
    Returns:
        List of actionable recommendations
    """
    recommendations = []
    
    # MSK recommendations
    msk_validation = compliance_results.get('msk_validation', {})
    missing_msk = msk_validation.get('missing_msk', [])
    
    if missing_msk:
        high_priority = [item for item in missing_msk if item.get('weight', 0) >= 8]
        medium_priority = [item for item in missing_msk if 4 <= item.get('weight', 0) < 8]
        low_priority = [item for item in missing_msk if item.get('weight', 0) < 4]
        
        if high_priority:
            recommendations.append(
                f"CRITICAL: Apply MSK null flavor to {len(high_priority)} high-priority personal data elements"
            )
        
        if medium_priority:
            recommendations.append(
                f"IMPORTANT: Apply MSK null flavor to {len(medium_priority)} medium-priority elements"
            )
        
        if low_priority:
            recommendations.append(
                f"RECOMMENDED: Apply MSK null flavor to {len(low_priority)} additional elements"
            )
    
    # Data minimization recommendations
    data_min = compliance_results.get('data_minimization', {})
    unnecessary_elements = data_min.get('unnecessary_elements', [])
    
    if unnecessary_elements:
        recommendations.append(
            f"Review {len(unnecessary_elements)} optional elements containing personal data"
        )
    
    # Structure recommendations
    structure_comp = compliance_results.get('structure_compliance', {})
    missing_elements = structure_comp.get('missing_elements', [])
    
    if missing_elements:
        recommendations.append(
            f"Add missing required elements: {', '.join(missing_elements[:3])}"
        )
    
    # Overall score recommendations
    overall_score = compliance_results.get('compliance_score', 0)
    
    if overall_score < 0.7:
        recommendations.insert(0, "URGENT: File requires comprehensive review before submission")
    elif overall_score < 0.8:
        recommendations.insert(0, "File needs improvements to meet recommended compliance standards")
    
    # Add positive recommendations
    if overall_score >= 0.9:
        recommendations.append("File demonstrates excellent compliance with EDPS requirements")
    
    if not recommendations:
        recommendations.append("No specific recommendations - file meets compliance requirements")
    
    return recommendations

def export_compliance_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Export compliance summary for multiple files
    
    Args:
        results: List of compliance results
        
    Returns:
        Summary statistics
    """
    if not results:
        return {'error': 'No results to summarize'}
    
    total_files = len(results)
    compliance_scores = [r.get('compliance_score', 0) for r in results]
    
    summary = {
        'total_files': total_files,
        'average_compliance': sum(compliance_scores) / total_files,
        'min_compliance': min(compliance_scores),
        'max_compliance': max(compliance_scores),
        'files_above_80_percent': len([s for s in compliance_scores if s >= 0.8]),
        'files_below_70_percent': len([s for s in compliance_scores if s < 0.7]),
        'total_issues': sum(r.get('issues_count', 0) for r in results),
        'total_personal_data_fields': sum(r.get('personal_data_count', 0) for r in results),
        'export_timestamp': datetime.now().isoformat()
    }
    
    # Categorize files by compliance level
    excellent = len([s for s in compliance_scores if s >= 0.9])
    good = len([s for s in compliance_scores if 0.8 <= s < 0.9])
    acceptable = len([s for s in compliance_scores if 0.7 <= s < 0.8])
    poor = len([s for s in compliance_scores if s < 0.7])
    
    summary['compliance_distribution'] = {
        'excellent': excellent,
        'good': good,
        'acceptable': acceptable,
        'poor': poor
    }
    
    return summary

# Import required for BytesIO
import io
