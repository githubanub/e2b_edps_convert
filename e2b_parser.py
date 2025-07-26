import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
try:
    from lxml import etree as lxml_ET
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

class E2BParser:
    """E2B R3 XML and ICH ICSR parser for pharmaceutical adverse event reports"""
    
    def __init__(self):
        self.namespace_map = {
            'ichicsr': 'http://www.ich.org/ICHCSRMSG.XSD'
        }
        
        # E2B R3 required elements
        self.required_elements = [
            'ichicsrmessageheader',
            'safetyreport',
            'patient',
            'reaction'
        ]
        
        # ICH ICSR v2.1 required elements (for .sgm files)
        self.icsr_required_elements = [
            'ichicsrmessageheader',
            'safetyreport',
            'patient'
        ]
        
        # Personal data elements that should have MSK null flavor
        self.personal_data_elements = {
            # E2B R3 format
            'A.2.1.1': ['patient', 'patientinitial'],
            'A.2.1.4': ['patient', 'patientbirthdateformat'],
            'A.3.1.2': ['primarysource', 'reportergivename'],
            'A.3.1.3': ['primarysource', 'reporterfamilyname'],
            'A.3.1.4': ['primarysource', 'reporteraddress'],
            'A.3.1.5': ['primarysource', 'reportercity'],
            'A.3.1.6': ['primarysource', 'reporterstate'],
            'A.3.1.7': ['primarysource', 'reporterpostcode'],
            'A.3.1.8': ['primarysource', 'reportercountrycode'],
            'A.3.1.9': ['primarysource', 'reportertelephone'],
            'A.3.1.10': ['primarysource', 'reporterfax'],
            'A.3.1.11': ['primarysource', 'reporteremailaddress'],
        }
        
        # ICH ICSR v2.1 personal data elements (for .sgm files)
        self.icsr_personal_data_elements = {
            # Patient information
            'patient_initials': ['patient', 'patientinitial'],
            'patient_birthdate': ['patient', 'patientbirthdate'],
            'patient_records': ['patient', 'patientgpmedicalrecordnumb'],
            # Reporter information
            'reporter_name': ['primarysource', 'reportergivename'],
            'reporter_family': ['primarysource', 'reporterfamilyname'],
            'reporter_middle': ['primarysource', 'reportermiddlename'],
            'reporter_address': ['primarysource', 'reporterstreet'],
            'reporter_city': ['primarysource', 'reportercity'],
            'reporter_state': ['primarysource', 'reporterstate'],
            'reporter_postcode': ['primarysource', 'reporterpostcode'],
            # Sender information
            'sender_name': ['sender', 'sendergivename'],
            'sender_family': ['sender', 'senderfamilyname'],
            'sender_middle': ['sender', 'sendermiddlename'],
            'sender_address': ['sender', 'senderstreetaddress'],
            'sender_city': ['sender', 'sendercity'],
            'sender_state': ['sender', 'senderstate'],
            'sender_postcode': ['sender', 'senderpostcode'],
            'sender_tel': ['sender', 'sendertel'],
            'sender_fax': ['sender', 'senderfax'],
            'sender_email': ['sender', 'senderemailaddress'],
            # Receiver information
            'receiver_name': ['receiver', 'receivergivename'],
            'receiver_family': ['receiver', 'receiverfamilyname'],
            'receiver_middle': ['receiver', 'receivermiddlename'],
            'receiver_address': ['receiver', 'receiverstreetaddress'],
            'receiver_city': ['receiver', 'receivercity'],
            'receiver_state': ['receiver', 'receiverstate'],
            'receiver_postcode': ['receiver', 'receiverpostcode'],
            'receiver_tel': ['receiver', 'receivertel'],
            'receiver_fax': ['receiver', 'receiverfax'],
            'receiver_email': ['receiver', 'receiveremailaddress'],
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_parent(self, element):
        """Get parent element with fallback for different XML libraries"""
        if hasattr(element, 'getparent'):
            return element.getparent()
        elif hasattr(element, '_parent'):
            return element._parent
        else:
            return None
    
    def parse_e2b_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse E2B R3 XML or ICH ICSR content and extract relevant data
        
        Args:
            xml_content: Raw XML content as string
            
        Returns:
            Dictionary containing parsed data and validation results
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Detect format type
            format_type = self._detect_format_type(root)
            
            # Validate basic structure based on format
            if format_type == 'icsr':
                validation_result = self._validate_icsr_structure(root)
            else:
                validation_result = self._validate_xml_structure(root)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"XML structure validation failed: {', '.join(validation_result['errors'])}",
                    'data': None
                }
            
            # Extract data
            extracted_data = self._extract_data(root)
            
            # Count elements and fields
            element_count = len(list(root.iter()))
            field_count = len(self._get_all_text_elements(root))
            
            # Extract all elements for PII detection
            all_elements = self._extract_all_elements(root)
            
            # Set personal data elements based on format
            format_type = self._detect_format_type(root)
            personal_data_map = self.icsr_personal_data_elements if format_type == 'icsr' else self.personal_data_elements
            
            return {
                'success': True,
                'format_type': format_type,
                'data': {
                    'header': extracted_data.get('message_header', {}),
                    'safety_report': extracted_data.get('safety_report', {}),
                    'validation': validation_result
                },
                'element_count': len(all_elements),
                'field_count': len([elem for elem in all_elements if elem.get('text', '').strip()]),
                'all_elements': all_elements,
                'personal_data_elements': self._identify_personal_data_elements(all_elements, personal_data_map)
            }
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {str(e)}")
            return {
                'success': False,
                'error': f"XML parsing error: {str(e)}",
                'data': None
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during parsing: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'data': None
            }
    
    def _validate_xml_structure(self, root: ET.Element) -> Dict[str, Any]:
        """
        Validate XML structure against E2B R3 requirements
        
        Args:
            root: XML root element
            
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        
        # Check for required elements
        missing_elements = []
        for element in self.required_elements:
            if root.find(f".//{element}") is None:
                missing_elements.append(element)
        
        if missing_elements:
            errors.append(f"Missing required elements: {', '.join(missing_elements)}")
        
        # Check for ICH ICSR message structure
        if root.tag != 'ichicsrmessageheader' and root.find('.//ichicsrmessageheader') is None:
            errors.append("Missing ICH ICSR message header")
        
        # Check for safety report
        safety_reports = root.findall('.//safetyreport')
        if not safety_reports:
            errors.append("No safety reports found")
        elif len(safety_reports) > 1:
            warnings.append(f"Multiple safety reports found: {len(safety_reports)}")
        
        # Validate XML namespace
        try:
            if hasattr(root, 'nsmap') and root.nsmap:
                if not any('ich' in str(ns) for ns in root.nsmap.values()):
                    warnings.append("ICH namespace not found - may indicate non-standard format")
            else:
                # Fallback check for standard ElementTree
                root_str = ET.tostring(root, encoding='unicode')
                if 'ich' not in root_str.lower():
                    warnings.append("ICH namespace not found - may indicate non-standard format")
        except:
            warnings.append("Could not validate XML namespace")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'required_elements_found': len(self.required_elements) - len(missing_elements),
            'total_required_elements': len(self.required_elements)
        }
    
    def _extract_data(self, root: ET.Element) -> Dict[str, Any]:
        """
        Extract relevant data from E2B R3 XML
        
        Args:
            root: XML root element
            
        Returns:
            Dictionary containing extracted data
        """
        data = {
            'message_header': self._extract_message_header(root),
            'safety_report': self._extract_safety_report(root),
            'patient_data': self._extract_patient_data(root),
            'reaction_data': self._extract_reaction_data(root),
            'personal_data_elements': self._find_personal_data_elements(root),
            'msk_elements': self._find_msk_elements(root),
            'all_elements': self._get_all_elements_info(root)
        }
        
        return data
    
    def _extract_all_elements(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all elements with their properties for PII detection"""
        elements = []
        for elem in root.iter():
            if elem.tag and elem.text and elem.text.strip():
                elements.append({
                    'tag': elem.tag,
                    'text': elem.text.strip(),
                    'path': self._get_element_path(elem),
                    'xpath': self._get_xpath(root, elem),
                    'has_msk_null_flavor': elem.get('nullFlavor') == 'MSK',
                    'attributes': dict(elem.attrib) if elem.attrib else {}
                })
        return elements
    
    def _identify_personal_data_elements(self, all_elements: List[Dict[str, Any]], personal_data_map: Dict) -> List[Dict[str, Any]]:
        """Identify which elements contain personal data based on mapping"""
        personal_elements = []
        
        for element in all_elements:
            # Check against known personal data patterns
            is_personal = False
            element_code = None
            
            for code, path_parts in personal_data_map.items():
                if len(path_parts) >= 2:
                    target_tag = path_parts[-1]
                    if element['tag'] == target_tag:
                        is_personal = True
                        element_code = code
                        break
            
            if is_personal:
                personal_elements.append({
                    'element_code': element_code,
                    'element_name': element['tag'],
                    'element_path': element['path'],
                    'has_value': bool(element['text']),
                    'has_msk_null_flavor': element['has_msk_null_flavor'],
                    'current_value': element['text'],
                    'xpath': element['xpath']
                })
        
        return personal_elements
    
    def _detect_format_type(self, root: ET.Element) -> str:
        """
        Detect whether this is E2B R3 or ICH ICSR v2.1 format
        
        Args:
            root: XML root element
            
        Returns:
            Format type: 'e2b' or 'icsr'
        """
        # Check root element
        if root.tag == 'ichicsr':
            return 'icsr'
        
        # Check for ICH ICSR v2.1 specific elements
        if root.find('.//messageformatversion') is not None:
            version_elem = root.find('.//messageformatversion')
            if version_elem is not None and version_elem.text and '2.1' in version_elem.text:
                return 'icsr'
        
        # Default to E2B R3
        return 'e2b'
    
    def _validate_icsr_structure(self, root: ET.Element) -> Dict[str, Any]:
        """
        Validate XML structure against ICH ICSR v2.1 requirements
        
        Args:
            root: XML root element
            
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        
        # Check root element
        if root.tag != 'ichicsr':
            errors.append("Root element should be 'ichicsr' for ICH ICSR v2.1 format")
        
        # Check for required elements
        missing_elements = []
        for element in self.icsr_required_elements:
            if root.find(f".//{element}") is None:
                missing_elements.append(element)
        
        if missing_elements:
            errors.append(f"Missing required elements: {', '.join(missing_elements)}")
        
        # Check for message format version
        version_elem = root.find('.//messageformatversion')
        if version_elem is not None:
            if version_elem.text != '2.1':
                warnings.append(f"Expected version 2.1, found: {version_elem.text}")
        else:
            warnings.append("Message format version not found")
        
        # Check for safety report
        safety_reports = root.findall('.//safetyreport')
        if not safety_reports:
            errors.append("No safety reports found")
        elif len(safety_reports) > 1:
            warnings.append(f"Multiple safety reports found: {len(safety_reports)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'required_elements_found': len(self.icsr_required_elements) - len(missing_elements),
            'total_required_elements': len(self.icsr_required_elements),
            'format_type': 'icsr'
        }
    
    def _extract_message_header(self, root: ET.Element) -> Dict[str, Any]:
        """Extract message header information"""
        header = {}
        
        # Find message header
        msg_header = root.find('.//ichicsrmessageheader')
        if msg_header is not None:
            header['message_type'] = self._get_element_text(msg_header, 'messagetype')
            header['message_format_version'] = self._get_element_text(msg_header, 'messageformatversion')
            header['message_format_release'] = self._get_element_text(msg_header, 'messageformatrelease')
            header['message_number'] = self._get_element_text(msg_header, 'messagenumb')
            header['message_sender'] = self._get_element_text(msg_header, 'messagesenderidentifier')
            header['message_receiver'] = self._get_element_text(msg_header, 'messagereceiveridentifier')
            header['message_date'] = self._get_element_text(msg_header, 'messagedateformat')
        
        return header
    
    def _extract_safety_report(self, root: ET.Element) -> Dict[str, Any]:
        """Extract safety report information"""
        report = {}
        
        safety_report = root.find('.//safetyreport')
        if safety_report is not None:
            report['safety_report_version'] = self._get_element_text(safety_report, 'safetyreportversion')
            report['safety_report_id'] = self._get_element_text(safety_report, 'safetyreportid')
            report['primary_source_country'] = self._get_element_text(safety_report, 'primarysourcecountry')
            report['occurcountry'] = self._get_element_text(safety_report, 'occurcountry')
            report['transmissiondate'] = self._get_element_text(safety_report, 'transmissiondateformat')
            report['receiptdate'] = self._get_element_text(safety_report, 'receiptdateformat')
        
        return report
    
    def _extract_patient_data(self, root: ET.Element) -> Dict[str, Any]:
        """Extract patient information"""
        patient = {}
        
        patient_elem = root.find('.//patient')
        if patient_elem is not None:
            patient['patient_initial'] = self._get_element_text(patient_elem, 'patientinitial')
            patient['patient_birthdate'] = self._get_element_text(patient_elem, 'patientbirthdateformat')
            patient['patient_age'] = self._get_element_text(patient_elem, 'patientagenumb')
            patient['patient_age_unit'] = self._get_element_text(patient_elem, 'patientageunit')
            patient['patient_sex'] = self._get_element_text(patient_elem, 'patientsex')
            patient['patient_weight'] = self._get_element_text(patient_elem, 'patientweight')
            patient['patient_height'] = self._get_element_text(patient_elem, 'patientheight')
        
        return patient
    
    def _extract_reaction_data(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract reaction information"""
        reactions = []
        
        reaction_elems = root.findall('.//reaction')
        for reaction_elem in reaction_elems:
            reaction = {
                'primary_source_reaction': self._get_element_text(reaction_elem, 'primarysourcereaction'),
                'reaction_meddra_version': self._get_element_text(reaction_elem, 'reactionmeddraversionllt'),
                'reaction_meddra_pt': self._get_element_text(reaction_elem, 'reactionmeddrapt'),
                'reaction_meddra_llt': self._get_element_text(reaction_elem, 'reactionmeddrallt'),
                'reaction_outcome': self._get_element_text(reaction_elem, 'reactionoutcome'),
                'reaction_start_date': self._get_element_text(reaction_elem, 'reactionstartdateformat'),
                'reaction_end_date': self._get_element_text(reaction_elem, 'reactionenddateformat')
            }
            reactions.append(reaction)
        
        return reactions
    
    def _find_personal_data_elements(self, root: ET.Element, personal_data_map: Dict = None) -> List[Dict[str, Any]]:
        """Find elements containing personal data"""
        personal_elements = []
        
        # Use provided map or default based on format
        if personal_data_map is None:
            format_type = self._detect_format_type(root)
            personal_data_map = self.icsr_personal_data_elements if format_type == 'icsr' else self.personal_data_elements
        
        for element_code, path_parts in personal_data_map.items():
            elements = self._find_elements_by_path(root, path_parts)
            for elem in elements:
                personal_elements.append({
                    'element_code': element_code,
                    'element_name': elem.tag,
                    'element_path': self._get_element_path(elem),
                    'has_value': elem.text is not None and elem.text.strip() != '',
                    'has_msk_null_flavor': elem.get('nullFlavor') == 'MSK',
                    'current_value': elem.text,
                    'null_flavor': elem.get('nullFlavor'),
                    'xpath': self._get_xpath(root, elem)
                })
        
        return personal_elements
    
    def _find_msk_elements(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Find all elements with MSK null flavor"""
        msk_elements = []
        
        for elem in root.iter():
            if elem.get('nullFlavor') == 'MSK':
                parent = self._get_parent(elem)
                msk_elements.append({
                    'element_name': elem.tag,
                    'element_path': self._get_element_path(elem),
                    'xpath': self._get_xpath(root, elem),
                    'parent_element': parent.tag if parent is not None else None
                })
        
        return msk_elements
    
    def _find_elements_by_path(self, root: ET.Element, path_parts: List[str]) -> List[ET.Element]:
        """Find elements by path components"""
        if not path_parts:
            return []
        
        # Build XPath expression
        xpath = './/' + '/'.join(path_parts)
        try:
            return root.findall(xpath)
        except:
            # Fallback to tag name search
            return root.findall(f'.//{path_parts[-1]}')
    
    def _get_element_text(self, parent: ET.Element, element_name: str) -> Optional[str]:
        """Get text content of a child element"""
        elem = parent.find(element_name)
        return elem.text if elem is not None else None
    
    def _get_element_path(self, element: ET.Element) -> str:
        """Get the path of an element"""
        path_parts = []
        current = element
        
        while current is not None:
            path_parts.append(current.tag)
            current = self._get_parent(current)
        
        return '/'.join(reversed(path_parts))
    
    def _get_xpath(self, root: ET.Element, target: ET.Element) -> str:
        """Get XPath expression for target element"""
        path_parts = []
        current = target
        
        while current is not None and current != root:
            # Count preceding siblings with same tag
            parent = self._get_parent(current)
            if parent is not None:
                siblings = [sibling for sibling in parent if sibling.tag == current.tag]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    path_parts.append(f"{current.tag}[{index}]")
                else:
                    path_parts.append(current.tag)
            else:
                path_parts.append(current.tag)
            current = self._get_parent(current)
        
        return '//' + '/'.join(reversed(path_parts))
    
    def _get_all_text_elements(self, root: ET.Element) -> List[str]:
        """Get all text content from XML"""
        text_elements = []
        for elem in root.iter():
            if elem.text and elem.text.strip():
                text_elements.append(elem.text.strip())
        return text_elements
    
    def _get_all_elements_info(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Get information about all elements in XML"""
        elements_info = []
        
        for elem in root.iter():
            elem_info = {
                'tag': elem.tag,
                'text': elem.text.strip() if elem.text else None,
                'attributes': dict(elem.attrib),
                'has_children': len(list(elem)) > 0,
                'xpath': self._get_xpath(root, elem),
                'null_flavor': elem.get('nullFlavor'),
                'is_personal_data': any(elem.tag.lower() in [part.lower() for part in path_parts] 
                                      for path_parts in self.personal_data_elements.values())
            }
            elements_info.append(elem_info)
        
        return elements_info
    
    def validate_e2b_schema(self, xml_content: str) -> Dict[str, Any]:
        """
        Validate XML against E2B R3 schema requirements
        
        Args:
            xml_content: Raw XML content
            
        Returns:
            Validation result
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Basic structure validation
            structure_validation = self._validate_xml_structure(root)
            
            # Additional E2B specific validations
            e2b_validations = self._validate_e2b_specific_rules(root)
            
            return {
                'valid': structure_validation['valid'] and e2b_validations['valid'],
                'structure_validation': structure_validation,
                'e2b_validation': e2b_validations,
                'total_errors': len(structure_validation['errors']) + len(e2b_validations['errors']),
                'total_warnings': len(structure_validation['warnings']) + len(e2b_validations['warnings'])
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'structure_validation': None,
                'e2b_validation': None
            }
    
    def _validate_e2b_specific_rules(self, root: ET.Element) -> Dict[str, Any]:
        """Validate E2B specific business rules"""
        errors = []
        warnings = []
        
        # Check message format version
        version_elem = root.find('.//messageformatversion')
        if version_elem is not None and version_elem.text != 'R3':
            warnings.append("Message format version is not R3")
        
        # Check for required patient information
        patient_elem = root.find('.//patient')
        if patient_elem is not None:
            if not self._get_element_text(patient_elem, 'patientsex'):
                warnings.append("Patient sex not specified")
        
        # Check for at least one reaction
        reactions = root.findall('.//reaction')
        if not reactions:
            errors.append("At least one reaction must be reported")
        
        # Check for primary source information
        primary_source = root.find('.//primarysource')
        if primary_source is None:
            errors.append("Primary source information missing")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
