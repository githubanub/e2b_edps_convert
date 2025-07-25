from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.flowables import HRFlowable
from io import BytesIO
from typing import Dict, List, Any
from datetime import datetime
import json

class ReportGenerator:
    """Generate compliance reports for E2B R3 to EDPS conversion"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.blue
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        self.compliance_colors = {
            'Excellent': colors.darkgreen,
            'Good': colors.green,
            'Acceptable': colors.orange,
            'Poor': colors.red,
            'Critical': colors.darkred
        }
    
    def generate_compliance_report(self, filename: str, parsed_data: Dict[str, Any], 
                                 compliance_result: Dict[str, Any], processing_time: float) -> bytes:
        """
        Generate comprehensive compliance report
        
        Args:
            filename: Name of the processed file
            parsed_data: Parsed XML data
            compliance_result: Compliance validation results
            processing_time: Time taken to process the file
            
        Returns:
            PDF report as bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Build report content
        content = []
        
        # Title page
        content.extend(self._build_title_page(filename, compliance_result))
        content.append(PageBreak())
        
        # Executive summary
        content.extend(self._build_executive_summary(compliance_result, processing_time))
        content.append(Spacer(1, 20))
        
        # Detailed compliance analysis
        content.extend(self._build_compliance_analysis(compliance_result))
        content.append(Spacer(1, 20))
        
        # File structure analysis
        content.extend(self._build_structure_analysis(parsed_data))
        content.append(Spacer(1, 20))
        
        # Personal data analysis
        content.extend(self._build_personal_data_analysis(compliance_result))
        content.append(Spacer(1, 20))
        
        # Issues and recommendations
        content.extend(self._build_issues_recommendations(compliance_result))
        content.append(Spacer(1, 20))
        
        # Regulatory compliance
        content.extend(self._build_regulatory_compliance())
        content.append(PageBreak())
        
        # Appendices
        content.extend(self._build_appendices(parsed_data, compliance_result))
        
        # Build PDF
        doc.build(content)
        
        # Return PDF data
        buffer.seek(0)
        return buffer.getvalue()
    
    def _build_title_page(self, filename: str, compliance_result: Dict[str, Any]) -> List:
        """Build report title page"""
        content = []
        
        # Title
        content.append(Paragraph("E2B R3 to EDPS Compliance Report", self.title_style))
        content.append(Spacer(1, 30))
        
        # File information
        content.append(Paragraph("File Information", self.heading_style))
        file_info = [
            ['Filename:', filename],
            ['Processing Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Report Version:', '1.0'],
            ['Regulation:', 'GVP Module VI Addendum II']
        ]
        
        file_table = Table(file_info, colWidths=[2*inch, 4*inch])
        file_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(file_table)
        content.append(Spacer(1, 30))
        
        # Compliance summary
        content.append(Paragraph("Compliance Summary", self.heading_style))
        
        compliance_score = compliance_result.get('compliance_score', 0)
        compliance_level = compliance_result.get('compliance_level', 'Unknown')
        compliance_color = self.compliance_colors.get(compliance_level, colors.black)
        
        score_style = ParagraphStyle(
            'ScoreStyle',
            parent=self.normal_style,
            fontSize=24,
            textColor=compliance_color,
            alignment=1  # Center alignment
        )
        
        content.append(Paragraph(f"Overall Compliance Score: {compliance_score:.1%}", score_style))
        content.append(Paragraph(f"Compliance Level: {compliance_level}", score_style))
        
        return content
    
    def _build_executive_summary(self, compliance_result: Dict[str, Any], processing_time: float) -> List:
        """Build executive summary section"""
        content = []
        
        content.append(Paragraph("Executive Summary", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        # Summary metrics
        summary_data = [
            ['Metric', 'Value', 'Status'],
            ['Overall Compliance Score', f"{compliance_result.get('compliance_score', 0):.1%}", compliance_result.get('compliance_level', 'Unknown')],
            ['Personal Data Fields Found', str(compliance_result.get('personal_data_count', 0)), 'Identified'],
            ['MSK Null Flavors Applied', str(compliance_result.get('msk_applied_count', 0)), 'Applied'],
            ['Compliance Issues', str(len(compliance_result.get('issues', []))), 'Found'],
            ['Processing Time', f"{processing_time:.2f} seconds", 'Completed']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        content.append(summary_table)
        content.append(Spacer(1, 12))
        
        # Key findings
        content.append(Paragraph("Key Findings", self.subheading_style))
        
        findings = []
        compliance_score = compliance_result.get('compliance_score', 0)
        
        if compliance_score >= 0.9:
            findings.append("• Excellent compliance with EDPS requirements")
        elif compliance_score >= 0.8:
            findings.append("• Good compliance with minor improvements needed")
        elif compliance_score >= 0.7:
            findings.append("• Acceptable compliance with some issues to address")
        else:
            findings.append("• Significant compliance issues requiring immediate attention")
        
        if compliance_result.get('msk_applied_count', 0) > 0:
            findings.append(f"• {compliance_result.get('msk_applied_count')} personal data fields properly masked")
        
        if len(compliance_result.get('issues', [])) > 0:
            findings.append(f"• {len(compliance_result.get('issues', []))} compliance issues identified")
        
        for finding in findings:
            content.append(Paragraph(finding, self.normal_style))
        
        return content
    
    def _build_compliance_analysis(self, compliance_result: Dict[str, Any]) -> List:
        """Build detailed compliance analysis section"""
        content = []
        
        content.append(Paragraph("Detailed Compliance Analysis", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        # MSK validation details
        msk_validation = compliance_result.get('msk_validation', {})
        content.append(Paragraph("MSK Null Flavor Application", self.subheading_style))
        
        msk_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Total Personal Elements', str(msk_validation.get('total_personal_elements', 0)), '100%'],
            ['Elements Requiring MSK', str(msk_validation.get('elements_requiring_msk', 0)), 
             f"{(msk_validation.get('elements_requiring_msk', 0) / max(msk_validation.get('total_personal_elements', 1), 1) * 100):.1f}%"],
            ['Elements with MSK Applied', str(msk_validation.get('elements_with_msk', 0)),
             f"{(msk_validation.get('elements_with_msk', 0) / max(msk_validation.get('elements_requiring_msk', 1), 1) * 100):.1f}%"],
            ['MSK Compliance Score', f"{msk_validation.get('score', 0):.1%}", '']
        ]
        
        msk_table = Table(msk_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        msk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(msk_table)
        content.append(Spacer(1, 12))
        
        # Data minimization analysis
        data_minimization = compliance_result.get('data_minimization', {})
        content.append(Paragraph("Data Minimization Analysis", self.subheading_style))
        
        min_data = [
            ['Metric', 'Count', 'Score'],
            ['Total Elements with Data', str(data_minimization.get('elements_with_data', 0)), ''],
            ['Optional Elements with Data', str(data_minimization.get('optional_elements_with_data', 0)), ''],
            ['Data Minimization Score', f"{data_minimization.get('score', 0):.1%}", 
             'Good' if data_minimization.get('score', 0) >= 0.8 else 'Needs Improvement']
        ]
        
        min_table = Table(min_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        min_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(min_table)
        
        return content
    
    def _build_structure_analysis(self, parsed_data: Dict[str, Any]) -> List:
        """Build XML structure analysis section"""
        content = []
        
        content.append(Paragraph("XML Structure Analysis", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        # Message header information
        header = parsed_data.get('message_header', {})
        content.append(Paragraph("Message Header", self.subheading_style))
        
        header_data = [
            ['Field', 'Value'],
            ['Message Type', header.get('message_type', 'Not specified')],
            ['Format Version', header.get('message_format_version', 'Not specified')],
            ['Message Number', header.get('message_number', 'Not specified')],
            ['Sender', header.get('message_sender', 'Not specified')],
            ['Message Date', header.get('message_date', 'Not specified')]
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 3.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(header_table)
        content.append(Spacer(1, 12))
        
        # Safety report information
        safety_report = parsed_data.get('safety_report', {})
        content.append(Paragraph("Safety Report", self.subheading_style))
        
        safety_data = [
            ['Field', 'Value'],
            ['Safety Report ID', safety_report.get('safety_report_id', 'Not specified')],
            ['Safety Report Version', safety_report.get('safety_report_version', 'Not specified')],
            ['Primary Source Country', safety_report.get('primary_source_country', 'Not specified')],
            ['Occurrence Country', safety_report.get('occurcountry', 'Not specified')],
            ['Receipt Date', safety_report.get('receiptdate', 'Not specified')]
        ]
        
        safety_table = Table(safety_data, colWidths=[2*inch, 3.5*inch])
        safety_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcyan),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(safety_table)
        
        return content
    
    def _build_personal_data_analysis(self, compliance_result: Dict[str, Any]) -> List:
        """Build personal data analysis section"""
        content = []
        
        content.append(Paragraph("Personal Data Analysis", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        personal_data_fields = compliance_result.get('personal_data_fields', [])
        
        if not personal_data_fields:
            content.append(Paragraph("No personal data fields found in the E2B R3 file.", self.normal_style))
            return content
        
        # Create table of personal data elements
        data_headers = ['Element Code', 'Element Name', 'Has Value', 'MSK Applied', 'Status']
        table_data = [data_headers]
        
        for field in personal_data_fields:
            status = "✓ Compliant" if field.get('has_msk_null_flavor') or not field.get('has_value') else "⚠ Needs MSK"
            table_data.append([
                field.get('element_code', 'Unknown'),
                field.get('element_name', 'Unknown'),
                'Yes' if field.get('has_value') else 'No',
                'Yes' if field.get('has_msk_null_flavor') else 'No',
                status
            ])
        
        personal_table = Table(table_data, colWidths=[1*inch, 1.5*inch, 0.8*inch, 0.8*inch, 1.2*inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        # Color code rows based on compliance
        for i, field in enumerate(personal_data_fields, 1):
            if field.get('has_value') and not field.get('has_msk_null_flavor'):
                # Non-compliant - red background
                personal_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.mistyrose)
                ]))
            elif field.get('has_msk_null_flavor'):
                # Compliant - green background
                personal_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.lightgreen)
                ]))
        
        content.append(personal_table)
        
        return content
    
    def _build_issues_recommendations(self, compliance_result: Dict[str, Any]) -> List:
        """Build issues and recommendations section"""
        content = []
        
        content.append(Paragraph("Issues and Recommendations", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        # Issues
        issues = compliance_result.get('issues', [])
        content.append(Paragraph("Identified Issues", self.subheading_style))
        
        if issues:
            for i, issue in enumerate(issues, 1):
                content.append(Paragraph(f"{i}. {issue}", self.normal_style))
        else:
            content.append(Paragraph("No compliance issues identified.", self.normal_style))
        
        content.append(Spacer(1, 12))
        
        # Recommendations
        recommendations = compliance_result.get('recommendations', [])
        content.append(Paragraph("Recommendations", self.subheading_style))
        
        if recommendations:
            for i, recommendation in enumerate(recommendations, 1):
                content.append(Paragraph(f"{i}. {recommendation}", self.normal_style))
        else:
            content.append(Paragraph("No specific recommendations at this time.", self.normal_style))
        
        return content
    
    def _build_regulatory_compliance(self) -> List:
        """Build regulatory compliance section"""
        content = []
        
        content.append(Paragraph("Regulatory Compliance Reference", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        # GVP Module VI Addendum II information
        content.append(Paragraph("GVP Module VI Addendum II", self.subheading_style))
        content.append(Paragraph(
            "This report is based on the requirements specified in Good Vigilance Practice (GVP) "
            "Module VI Addendum II, which establishes standards for the protection of personal data "
            "in pharmacovigilance activities.", 
            self.normal_style
        ))
        content.append(Spacer(1, 8))
        
        content.append(Paragraph("Key Requirements:", self.subheading_style))
        requirements = [
            "• Application of MSK null flavor to personal data elements",
            "• Data minimization in adverse event reports",
            "• Compliance with European Data Protection Supervisor (EDPS) guidelines",
            "• Standardized format for EudraVigilance submissions",
            "• Maintaining clinical data integrity while protecting privacy"
        ]
        
        for req in requirements:
            content.append(Paragraph(req, self.normal_style))
        
        content.append(Spacer(1, 12))
        
        content.append(Paragraph("Effective Date", self.subheading_style))
        content.append(Paragraph("July 25, 2025", self.normal_style))
        
        return content
    
    def _build_appendices(self, parsed_data: Dict[str, Any], compliance_result: Dict[str, Any]) -> List:
        """Build appendices section"""
        content = []
        
        content.append(Paragraph("Appendices", self.heading_style))
        content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.blue))
        content.append(Spacer(1, 12))
        
        # Appendix A: Technical Details
        content.append(Paragraph("Appendix A: Technical Processing Details", self.subheading_style))
        
        tech_details = [
            ['Processing Parameter', 'Value'],
            ['XML Parser', 'lxml ElementTree'],
            ['Validation Engine', 'Custom E2B R3 Validator'],
            ['Compliance Framework', 'GVP Module VI Addendum II'],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Report Version', '1.0']
        ]
        
        tech_table = Table(tech_details, colWidths=[2.5*inch, 3*inch])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(tech_table)
        
        return content
    
    def generate_batch_report(self, batch_results: List[Dict[str, Any]]) -> bytes:
        """Generate batch processing report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        content = []
        
        # Title
        content.append(Paragraph("Batch Processing Compliance Report", self.title_style))
        content.append(Spacer(1, 20))
        
        # Summary
        total_files = len(batch_results)
        avg_compliance = sum(r['compliance_score'] for r in batch_results) / total_files if total_files > 0 else 0
        total_issues = sum(r['issues_count'] for r in batch_results)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Files Processed', str(total_files)],
            ['Average Compliance Score', f"{avg_compliance:.1%}"],
            ['Total Issues Found', str(total_issues)],
            ['Processing Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        content.append(summary_table)
        content.append(Spacer(1, 20))
        
        # Detailed results
        content.append(Paragraph("Detailed Results", self.heading_style))
        
        results_data = [['Filename', 'Compliance Score', 'Issues', 'Processing Time']]
        for result in batch_results:
            results_data.append([
                result['filename'],
                f"{result['compliance_score']:.1%}",
                str(result['issues_count']),
                f"{result['processing_time']:.2f}s"
            ])
        
        results_table = Table(results_data, colWidths=[2.5*inch, 1.2*inch, 0.8*inch, 1*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        content.append(results_table)
        
        # Build PDF
        doc.build(content)
        
        buffer.seek(0)
        return buffer.getvalue()
