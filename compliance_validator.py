import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

class ComplianceValidator:
    """EDPS compliance validator for E2B R3 XML files"""
    
    def __init__(self):
        # GVP Module VI Addendum II compliance rules
        self.compliance_rules = {
            'personal_data_elements': {
                'A.2.1.1': {'name': 'Patient Initial', 'required_msk': True, 'weight': 10},
                'A.2.1.4': {'name': 'Patient Birth Date', 'required_msk': True, 'weight': 10},
                'A.3.1.2': {'name': 'Reporter Given Name', 'required_msk': True, 'weight': 8},
                'A.3.1.3': {'name': 'Reporter Family Name', 'required_msk': True, 'weight': 8},
                'A.3.1.4': {'name': 'Reporter Address', 'required_msk': True, 'weight': 6},
                'A.3.1.5': {'name': 'Reporter City', 'required_msk': True, 'weight': 5},
                'A.3.1.6': {'name': 'Reporter State', 'required_msk': True, 'weight': 4},
                'A.3.1.7': {'name': 'Reporter Postcode', 'required_msk': True, 'weight': 4},
                'A.3.1.8': {'name': 'Reporter Country', 'required_msk': False, 'weight': 2},
                'A.3.1.9': {'name': 'Reporter Telephone', 'required_msk': True, 'weight': 6},
                'A.3.1.10': {'name': 'Reporter Fax', 'required_msk': True, 'weight': 4},
                'A.3.1.11': {'name': 'Reporter Email', 'required_msk': True, 'weight': 8},
            },
            'compliance_thresholds': {
                'excellent': 0.90,
                'good': 0.80,
                'acceptable': 0.70,
                'poor': 0.50
            }
        }
        
        # Statistics storage
        self.stats_file = 'compliance_stats.json'
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def validate_compliance(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate EDPS compliance for parsed E2B R3 data
        
        Args:
            parsed_data: Parsed XML data from E2BParser
            
        Returns:
            Compliance validation results
        """
        try:
            # Extract personal data elements
            personal_data_elements = parsed_data.get('personal_data_elements', [])
            
            # Validate MSK application
            msk_validation = self._validate_msk_application(personal_data_elements)
            
            # Check data minimization
            data_minimization = self._check_data_minimization(parsed_data)
            
            # Validate XML structure compliance
            structure_compliance = self._validate_structure_compliance(parsed_data)
            
            # Calculate overall compliance score
            compliance_score = self._calculate_compliance_score(
                msk_validation, data_minimization, structure_compliance
            )
            
            # Identify issues
            issues = self._identify_compliance_issues(
                msk_validation, data_minimization, structure_compliance
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                msk_validation, data_minimization, issues
            )
            
            # Prepare result
            result = {
                'compliance_score': compliance_score,
                'compliance_level': self._get_compliance_level(compliance_score),
                'personal_data_count': len(personal_data_elements),
                'msk_applied_count': len([elem for elem in personal_data_elements if elem.get('has_msk_null_flavor')]),
                'personal_data_fields': personal_data_elements,
                'msk_validation': msk_validation,
                'data_minimization': data_minimization,
                'structure_compliance': structure_compliance,
                'issues': issues,
                'recommendations': recommendations,
                'validation_timestamp': datetime.now().isoformat(),
                'regulation_reference': 'GVP Module VI Addendum II'
            }
            
            # Update statistics
            self._update_statistics(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Compliance validation error: {str(e)}")
            return {
                'compliance_score': 0.0,
                'compliance_level': 'error',
                'error': str(e),
                'issues': [f"Validation error: {str(e)}"],
                'personal_data_count': 0,
                'msk_applied_count': 0
            }
    
    def _validate_msk_application(self, personal_data_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate MSK null flavor application"""
        validation_result = {
            'total_personal_elements': len(personal_data_elements),
            'elements_with_msk': 0,
            'elements_requiring_msk': 0,
            'correctly_masked': [],
            'missing_msk': [],
            'unnecessary_msk': [],
            'score': 0.0
        }
        
        for element in personal_data_elements:
            element_code = element.get('element_code')
            has_msk = element.get('has_msk_null_flavor', False)
            has_value = element.get('has_value', False)
            
            # Check if MSK is required for this element
            rule = self.compliance_rules['personal_data_elements'].get(element_code, {})
            requires_msk = rule.get('required_msk', False)
            
            if requires_msk:
                validation_result['elements_requiring_msk'] += 1
                
                if has_value and not has_msk:
                    # Has personal data but no MSK - violation
                    validation_result['missing_msk'].append({
                        'element_code': element_code,
                        'element_name': rule.get('name', element.get('element_name')),
                        'current_value': element.get('current_value'),
                        'weight': rule.get('weight', 1)
                    })
                elif has_msk:
                    # Correctly masked
                    validation_result['correctly_masked'].append({
                        'element_code': element_code,
                        'element_name': rule.get('name', element.get('element_name')),
                        'weight': rule.get('weight', 1)
                    })
                    validation_result['elements_with_msk'] += 1
            
            elif has_msk and not requires_msk:
                # Has MSK but not required - not necessarily wrong but worth noting
                validation_result['unnecessary_msk'].append({
                    'element_code': element_code,
                    'element_name': element.get('element_name')
                })
        
        # Calculate MSK compliance score
        if validation_result['elements_requiring_msk'] > 0:
            total_weight = sum(
                self.compliance_rules['personal_data_elements'].get(elem['element_code'], {}).get('weight', 1)
                for elem in validation_result['missing_msk'] + validation_result['correctly_masked']
            )
            correct_weight = sum(elem['weight'] for elem in validation_result['correctly_masked'])
            validation_result['score'] = correct_weight / total_weight if total_weight > 0 else 0.0
        else:
            validation_result['score'] = 1.0  # No personal data requiring MSK
        
        return validation_result
    
    def _check_data_minimization(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data minimization compliance"""
        minimization_result = {
            'total_elements': len(parsed_data.get('all_elements', [])),
            'elements_with_data': 0,
            'optional_elements_with_data': 0,
            'unnecessary_elements': [],
            'score': 0.0
        }
        
        # Define optional elements that should be minimized
        optional_elements = [
            'reporteraddress', 'reportercity', 'reporterstate', 'reporterpostcode',
            'reportertelephone', 'reporterfax', 'reporteremailaddress',
            'patientinitial', 'patientbirthdateformat'
        ]
        
        all_elements = parsed_data.get('all_elements', [])
        
        for element in all_elements:
            if element.get('text'):
                minimization_result['elements_with_data'] += 1
                
                if element.get('tag', '').lower() in [opt.lower() for opt in optional_elements]:
                    if not element.get('null_flavor'):
                        minimization_result['optional_elements_with_data'] += 1
                        minimization_result['unnecessary_elements'].append({
                            'element_name': element.get('tag'),
                            'has_msk': element.get('null_flavor') == 'MSK',
                            'recommendation': 'Apply MSK null flavor or remove data'
                        })
        
        # Calculate data minimization score
        if minimization_result['elements_with_data'] > 0:
            minimization_ratio = 1 - (minimization_result['optional_elements_with_data'] / 
                                    minimization_result['elements_with_data'])
            minimization_result['score'] = max(0.0, minimization_ratio)
        else:
            minimization_result['score'] = 1.0
        
        return minimization_result
    
    def _validate_structure_compliance(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate XML structure compliance with E2B R3 standards"""
        structure_result = {
            'has_required_elements': True,
            'missing_elements': [],
            'invalid_structure': [],
            'score': 0.0
        }
        
        # Check message header compliance
        header = parsed_data.get('message_header', {})
        if not header.get('message_type'):
            structure_result['missing_elements'].append('Message Type')
            structure_result['has_required_elements'] = False
        
        if not header.get('message_format_version'):
            structure_result['missing_elements'].append('Message Format Version')
            structure_result['has_required_elements'] = False
        
        # Check safety report compliance
        safety_report = parsed_data.get('safety_report', {})
        if not safety_report.get('safety_report_id'):
            structure_result['missing_elements'].append('Safety Report ID')
            structure_result['has_required_elements'] = False
        
        # Check patient data compliance
        patient_data = parsed_data.get('patient_data', {})
        if not patient_data.get('patient_sex'):
            structure_result['missing_elements'].append('Patient Sex')
        
        # Check reaction data compliance
        reaction_data = parsed_data.get('reaction_data', [])
        if not reaction_data:
            structure_result['missing_elements'].append('Reaction Information')
            structure_result['has_required_elements'] = False
        
        # Calculate structure compliance score
        total_checks = 5  # Number of structure checks
        failed_checks = len(structure_result['missing_elements'])
        structure_result['score'] = max(0.0, (total_checks - failed_checks) / total_checks)
        
        return structure_result
    
    def _calculate_compliance_score(self, msk_validation: Dict, data_minimization: Dict, 
                                   structure_compliance: Dict) -> float:
        """Calculate overall compliance score"""
        # Weighted scoring
        weights = {
            'msk_application': 0.4,  # 40% weight
            'data_minimization': 0.3,  # 30% weight
            'structure_compliance': 0.3  # 30% weight
        }
        
        msk_score = msk_validation.get('score', 0.0)
        minimization_score = data_minimization.get('score', 0.0)
        structure_score = structure_compliance.get('score', 0.0)
        
        overall_score = (
            msk_score * weights['msk_application'] +
            minimization_score * weights['data_minimization'] +
            structure_score * weights['structure_compliance']
        )
        
        return round(overall_score, 3)
    
    def _get_compliance_level(self, score: float) -> str:
        """Get compliance level based on score"""
        thresholds = self.compliance_rules['compliance_thresholds']
        
        if score >= thresholds['excellent']:
            return 'Excellent'
        elif score >= thresholds['good']:
            return 'Good'
        elif score >= thresholds['acceptable']:
            return 'Acceptable'
        elif score >= thresholds['poor']:
            return 'Poor'
        else:
            return 'Critical'
    
    def _identify_compliance_issues(self, msk_validation: Dict, data_minimization: Dict, 
                                   structure_compliance: Dict) -> List[str]:
        """Identify specific compliance issues"""
        issues = []
        
        # MSK issues
        missing_msk = msk_validation.get('missing_msk', [])
        for missing in missing_msk:
            issues.append(f"Personal data element '{missing['element_name']}' requires MSK null flavor")
        
        # Data minimization issues
        unnecessary_elements = data_minimization.get('unnecessary_elements', [])
        for element in unnecessary_elements:
            issues.append(f"Optional element '{element['element_name']}' contains personal data without MSK")
        
        # Structure issues
        missing_elements = structure_compliance.get('missing_elements', [])
        for element in missing_elements:
            issues.append(f"Required element missing: {element}")
        
        return issues
    
    def _generate_recommendations(self, msk_validation: Dict, data_minimization: Dict, 
                                 issues: List[str]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # MSK recommendations
        missing_msk_count = len(msk_validation.get('missing_msk', []))
        if missing_msk_count > 0:
            recommendations.append(
                f"Apply MSK null flavor to {missing_msk_count} personal data elements"
            )
        
        # Data minimization recommendations
        unnecessary_count = len(data_minimization.get('unnecessary_elements', []))
        if unnecessary_count > 0:
            recommendations.append(
                f"Review {unnecessary_count} optional elements for data minimization"
            )
        
        # General recommendations
        if len(issues) > 5:
            recommendations.append("Consider comprehensive review of E2B R3 file before submission")
        
        if not recommendations:
            recommendations.append("File meets EDPS compliance requirements")
        
        return recommendations
    
    def _update_statistics(self, validation_result: Dict[str, Any]) -> None:
        """Update compliance statistics"""
        try:
            # Load existing statistics
            stats = self._load_statistics()
            
            # Update counters
            stats['total_files'] = stats.get('total_files', 0) + 1
            stats['total_compliance_score'] = stats.get('total_compliance_score', 0.0) + validation_result['compliance_score']
            stats['avg_compliance'] = stats['total_compliance_score'] / stats['total_files']
            
            # Update compliance distribution
            compliance_level = validation_result['compliance_level']
            if 'compliance_distribution' not in stats:
                stats['compliance_distribution'] = {}
            stats['compliance_distribution'][compliance_level] = stats['compliance_distribution'].get(compliance_level, 0) + 1
            
            # Update issue statistics
            if 'common_issues' not in stats:
                stats['common_issues'] = {}
            for issue in validation_result.get('issues', []):
                stats['common_issues'][issue] = stats['common_issues'].get(issue, 0) + 1
            
            # Count files with issues
            if validation_result.get('issues'):
                stats['files_with_issues'] = stats.get('files_with_issues', 0) + 1
            
            # Update personal data statistics
            stats['total_personal_data'] = stats.get('total_personal_data', 0) + validation_result.get('personal_data_count', 0)
            
            # Save updated statistics
            self._save_statistics(stats)
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {str(e)}")
    
    def _load_statistics(self) -> Dict[str, Any]:
        """Load compliance statistics from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading statistics: {str(e)}")
        
        return {}
    
    def _save_statistics(self, stats: Dict[str, Any]) -> None:
        """Save compliance statistics to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving statistics: {str(e)}")
    
    def get_compliance_statistics(self) -> Dict[str, Any]:
        """Get current compliance statistics"""
        stats = self._load_statistics()
        
        # Format compliance distribution for charts
        if 'compliance_distribution' in stats:
            distribution_data = []
            for level, count in stats['compliance_distribution'].items():
                distribution_data.append({'range': level, 'count': count})
            stats['compliance_distribution'] = distribution_data
        
        return stats
    
    def validate_batch_compliance(self, batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate compliance for a batch of files"""
        if not batch_results:
            return {'error': 'No results to validate'}
        
        total_files = len(batch_results)
        total_score = sum(result.get('compliance_score', 0) for result in batch_results)
        avg_score = total_score / total_files
        
        # Categorize files by compliance level
        categorized = {}
        for result in batch_results:
            level = self._get_compliance_level(result.get('compliance_score', 0))
            if level not in categorized:
                categorized[level] = []
            categorized[level].append(result['filename'])
        
        # Identify problematic files
        problematic_files = [
            result for result in batch_results 
            if result.get('compliance_score', 0) < self.compliance_rules['compliance_thresholds']['acceptable']
        ]
        
        return {
            'total_files': total_files,
            'average_compliance_score': avg_score,
            'compliance_distribution': categorized,
            'problematic_files': problematic_files,
            'files_requiring_attention': len(problematic_files),
            'batch_validation_timestamp': datetime.now().isoformat()
        }
