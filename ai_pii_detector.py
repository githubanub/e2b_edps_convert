import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

class AIPIIDetector:
    """AI-powered PII detector for E2B R3 XML files"""
    
    def __init__(self):
        # Known PII patterns and field mappings
        self.pii_patterns = {
            'patient_initials': {
                'pattern': r'^[A-Z]{1,3}$',
                'description': 'Patient initials (1-3 uppercase letters)',
                'priority': 'high',
                'element_codes': ['A.2.1.1']
            },
            'email_address': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'description': 'Email address',
                'priority': 'high',
                'element_codes': ['A.3.1.6', 'A.3.1.11']
            },
            'phone_number': {
                'pattern': r'^[\+]?[\d\s\-\(\)]{7,15}$',
                'description': 'Phone/fax number',
                'priority': 'medium',
                'element_codes': ['A.3.1.4', 'A.3.1.5', 'A.3.1.9', 'A.3.1.10']
            },
            'postal_code': {
                'pattern': r'^[\d\w\s\-]{3,10}$',
                'description': 'Postal/ZIP code',
                'priority': 'medium',
                'element_codes': ['A.3.1.7']
            },
            'date_of_birth': {
                'pattern': r'^\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}$',
                'description': 'Date of birth',
                'priority': 'high',
                'element_codes': ['A.2.1.2', 'A.2.1.4']
            },
            'person_name': {
                'pattern': r'^[A-Z][a-z]+(\s[A-Z][a-z]+)*$',
                'description': 'Person name (First/Last name)',
                'priority': 'high',
                'element_codes': ['A.3.1.2', 'A.3.1.3']
            },
            'address': {
                'pattern': r'.*\d+.*[Ss]treet|.*[Aa]venue|.*[Rr]oad|.*[Bb]oulevard|.*[Ll]ane|.*[Dd]rive',
                'description': 'Street address',
                'priority': 'medium',
                'element_codes': ['A.3.1.4']
            },
            'city_name': {
                'pattern': r'^[A-Z][a-zA-Z\s\-]{2,}$',
                'description': 'City name',
                'priority': 'low',
                'element_codes': ['A.3.1.5']
            }
        }
        
        # E2B R3 element mappings for PII detection
        self.element_mappings = {
            'patientinitial': {'type': 'patient_initials', 'priority': 'high'},
            'patientbirthdateformat': {'type': 'date_of_birth', 'priority': 'high'},
            'reportergivename': {'type': 'person_name', 'priority': 'high'},
            'reporterfamilyname': {'type': 'person_name', 'priority': 'high'},
            'reporteraddress': {'type': 'address', 'priority': 'medium'},
            'reportercity': {'type': 'city_name', 'priority': 'low'},
            'reporterstate': {'type': 'city_name', 'priority': 'low'},
            'reporterpostcode': {'type': 'postal_code', 'priority': 'medium'},
            'reportertelephone': {'type': 'phone_number', 'priority': 'medium'},
            'reporterfax': {'type': 'phone_number', 'priority': 'medium'},
            'reporteremailaddress': {'type': 'email_address', 'priority': 'high'},
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def detect_pii_fields(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect PII fields in parsed E2B R3 data using AI pattern matching
        
        Args:
            parsed_data: Parsed XML data from E2BParser
            
        Returns:
            List of detected PII fields with recommendations
        """
        detected_pii = []
        
        try:
            # Analyze all elements for PII content
            all_elements = parsed_data.get('all_elements', [])
            
            for element in all_elements:
                element_tag = element.get('tag', '').lower()
                element_text = element.get('text', '')
                
                if not element_text or element_text.strip() == '':
                    continue
                
                # Check if element is already marked with MSK
                has_msk = element.get('null_flavor') == 'MSK'
                
                # Detect PII based on element name and content
                pii_detection = self._analyze_element_for_pii(element_tag, element_text)
                
                if pii_detection:
                    detected_pii.append({
                        'element_tag': element_tag,
                        'element_text': element_text,
                        'xpath': element.get('xpath', ''),
                        'pii_type': pii_detection['type'],
                        'description': pii_detection['description'],
                        'priority': pii_detection['priority'],
                        'confidence': pii_detection['confidence'],
                        'has_msk_applied': has_msk,
                        'recommendation': 'Apply MSK null flavor' if not has_msk else 'MSK already applied',
                        'element_code': pii_detection.get('element_code', 'Unknown'),
                        'selected_for_masking': not has_msk  # Default selection
                    })
            
            # Sort by priority and confidence
            detected_pii.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x['priority']],
                x['confidence']
            ), reverse=True)
            
            return detected_pii
            
        except Exception as e:
            self.logger.error(f"PII detection error: {str(e)}")
            return []
    
    def _analyze_element_for_pii(self, element_tag: str, element_text: str) -> Optional[Dict[str, Any]]:
        """Analyze individual element for PII content"""
        
        # Check if element is in known PII element mappings
        if element_tag in self.element_mappings:
            mapping = self.element_mappings[element_tag]
            pii_type = mapping['type']
            
            if pii_type in self.pii_patterns:
                pattern_info = self.pii_patterns[pii_type]
                
                # Check if content matches expected pattern
                if re.match(pattern_info['pattern'], element_text):
                    confidence = 0.95  # High confidence for known elements with matching patterns
                else:
                    confidence = 0.7   # Medium confidence for known elements with non-matching patterns
                
                return {
                    'type': pii_type,
                    'description': pattern_info['description'],
                    'priority': pattern_info['priority'],
                    'confidence': confidence,
                    'element_code': pattern_info['element_codes'][0] if pattern_info['element_codes'] else 'Unknown'
                }
        
        # Analyze content with AI pattern matching for unknown elements
        for pii_type, pattern_info in self.pii_patterns.items():
            if re.match(pattern_info['pattern'], element_text):
                return {
                    'type': pii_type,
                    'description': f"Potential {pattern_info['description']} (detected by AI)",
                    'priority': 'medium',  # Lower priority for AI-detected unknown elements
                    'confidence': 0.6,     # Lower confidence for pattern-only matching
                    'element_code': 'AI-Detected'
                }
        
        # Check for generic personal data indicators
        personal_indicators = [
            'name', 'address', 'phone', 'email', 'birth', 'initial',
            'contact', 'identifier', 'patient', 'reporter'
        ]
        
        if any(indicator in element_tag for indicator in personal_indicators):
            return {
                'type': 'generic_personal_data',
                'description': 'Generic personal data (AI detected)',
                'priority': 'low',
                'confidence': 0.4,
                'element_code': 'AI-Generic'
            }
        
        return None
    
    def apply_msk_masking(self, xml_content: str, selected_fields: List[Dict[str, Any]]) -> str:
        """
        Apply MSK null flavor to selected PII fields
        
        Args:
            xml_content: Original XML content
            selected_fields: List of fields selected for masking
            
        Returns:
            Modified XML content with MSK applied
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Apply MSK to selected fields
            for field in selected_fields:
                if field.get('selected_for_masking', False):
                    element_tag = field['element_tag']
                    xpath = field.get('xpath', '')
                    
                    # Find elements to mask
                    elements_to_mask = self._find_elements_by_tag(root, element_tag)
                    
                    for elem in elements_to_mask:
                        if elem.text and elem.text.strip() == field['element_text']:
                            # Apply MSK null flavor
                            elem.set('nullFlavor', 'MSK')
                            elem.text = None  # Remove the personal data
                            self.logger.info(f"Applied MSK to {element_tag}: {field['element_text']}")
            
            # Return modified XML
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            self.logger.error(f"MSK application error: {str(e)}")
            return xml_content
    
    def _find_elements_by_tag(self, root: ET.Element, tag: str) -> List[ET.Element]:
        """Find all elements with specified tag"""
        return root.findall(f'.//{tag}')
    
    def generate_pii_summary(self, detected_pii: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of PII detection results"""
        
        if not detected_pii:
            return {
                'total_pii_fields': 0,
                'high_priority': 0,
                'medium_priority': 0,
                'low_priority': 0,
                'already_masked': 0,
                'selected_for_masking': 0
            }
        
        summary = {
            'total_pii_fields': len(detected_pii),
            'high_priority': len([f for f in detected_pii if f['priority'] == 'high']),
            'medium_priority': len([f for f in detected_pii if f['priority'] == 'medium']),
            'low_priority': len([f for f in detected_pii if f['priority'] == 'low']),
            'already_masked': len([f for f in detected_pii if f['has_msk_applied']]),
            'selected_for_masking': len([f for f in detected_pii if f.get('selected_for_masking', False)]),
            'avg_confidence': sum(f['confidence'] for f in detected_pii) / len(detected_pii)
        }
        
        return summary
    
    def get_masking_recommendations(self, detected_pii: List[Dict[str, Any]]) -> List[str]:
        """Generate masking recommendations based on detected PII"""
        
        recommendations = []
        
        high_priority_unmasked = [f for f in detected_pii if f['priority'] == 'high' and not f['has_msk_applied']]
        medium_priority_unmasked = [f for f in detected_pii if f['priority'] == 'medium' and not f['has_msk_applied']]
        
        if high_priority_unmasked:
            recommendations.append(f"CRITICAL: Mask {len(high_priority_unmasked)} high-priority PII fields immediately")
        
        if medium_priority_unmasked:
            recommendations.append(f"IMPORTANT: Consider masking {len(medium_priority_unmasked)} medium-priority fields")
        
        if not high_priority_unmasked and not medium_priority_unmasked:
            recommendations.append("All critical PII fields are properly protected")
        
        # Add specific field type recommendations
        field_types = {}
        for field in detected_pii:
            field_type = field['pii_type']
            if field_type not in field_types:
                field_types[field_type] = {'total': 0, 'unmasked': 0}
            field_types[field_type]['total'] += 1
            if not field['has_msk_applied']:
                field_types[field_type]['unmasked'] += 1
        
        for field_type, counts in field_types.items():
            if counts['unmasked'] > 0:
                recommendations.append(f"Review {counts['unmasked']} {field_type.replace('_', ' ')} fields")
        
        return recommendations