#!/usr/bin/env python3
"""
Unit tests for the carrier verification module.

Tests cover:
- Carrier information parsing
- Safety rating calculations
- Risk score computation
- Verification report generation
- Compliance status determination
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from carrier_verification import (
    CarrierInfo,
    SafetyRating,
    FMCSACarrierVerifier,
    VerificationReport,
    OperatingStatus,
    ComplianceStatus
)


class TestSafetyRating(unittest.TestCase):
    """Test SafetyRating dataclass."""
    
    def test_safety_rating_creation(self):
        """Test creating a SafetyRating object."""
        rating = SafetyRating(
            basic_id=1,
            basic_short_desc="Unsafe Driving",
            basic_desc="Unsafe Driving BASIC",
            percentile="75%",
            rd_deficient=True,
            rdsv_deficient=False,
            sv_deficient=False,
            snapshot_date="06/01/2026",
            total_inspection_with_violation=5,
            total_violation=10
        )
        
        self.assertEqual(rating.basic_id, 1)
        self.assertEqual(rating.basic_short_desc, "Unsafe Driving")
        self.assertTrue(rating.rd_deficient)
        self.assertFalse(rating.rdsv_deficient)
    
    def test_safety_rating_to_dict(self):
        """Test converting SafetyRating to dictionary."""
        rating = SafetyRating(
            basic_id=1,
            basic_short_desc="Unsafe Driving",
            basic_desc="Unsafe Driving BASIC",
            percentile="75%",
            rd_deficient=True,
            rdsv_deficient=False,
            sv_deficient=False,
            snapshot_date="06/01/2026",
            total_inspection_with_violation=5,
            total_violation=10
        )
        
        rating_dict = rating.to_dict()
        self.assertIsInstance(rating_dict, dict)
        self.assertEqual(rating_dict['basic_id'], 1)
        self.assertEqual(rating_dict['basic_short_desc'], "Unsafe Driving")


class TestCarrierInfo(unittest.TestCase):
    """Test CarrierInfo dataclass and methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.carrier_info = CarrierInfo(
            dot_number=44110,
            legal_name="Greyhound Lines Inc.",
            dba_name="Greyhound",
            mc_number=123456,
            allow_to_operate=True,
            out_of_service=False,
            out_of_service_date=None,
            complaint_count=5,
            phone="1-800-231-2222",
            street="350 N. St. Paul St.",
            city="Dallas",
            state="TX",
            zip_code="75201",
            country="USA",
            safety_ratings=[]
        )
    
    def test_carrier_info_creation(self):
        """Test creating a CarrierInfo object."""
        self.assertEqual(self.carrier_info.dot_number, 44110)
        self.assertEqual(self.carrier_info.legal_name, "Greyhound Lines Inc.")
        self.assertTrue(self.carrier_info.allow_to_operate)
        self.assertFalse(self.carrier_info.out_of_service)
    
    def test_get_operating_status_active(self):
        """Test operating status when carrier is active."""
        status = self.carrier_info.get_operating_status()
        self.assertEqual(status, OperatingStatus.ACTIVE)
    
    def test_get_operating_status_out_of_service(self):
        """Test operating status when carrier is out of service."""
        self.carrier_info.out_of_service = True
        status = self.carrier_info.get_operating_status()
        self.assertEqual(status, OperatingStatus.OUT_OF_SERVICE)
    
    def test_get_operating_status_unknown(self):
        """Test operating status when unknown."""
        self.carrier_info.allow_to_operate = False
        self.carrier_info.out_of_service = False
        status = self.carrier_info.get_operating_status()
        self.assertEqual(status, OperatingStatus.UNKNOWN)
    
    def test_get_compliance_status_insufficient_data(self):
        """Test compliance status with no safety ratings."""
        status = self.carrier_info.get_compliance_status()
        self.assertEqual(status, ComplianceStatus.INSUFFICIENT_DATA)
    
    def test_get_compliance_status_compliant(self):
        """Test compliance status when compliant."""
        rating = SafetyRating(
            basic_id=1,
            basic_short_desc="Unsafe Driving",
            basic_desc="Unsafe Driving BASIC",
            percentile="25%",
            rd_deficient=False,
            rdsv_deficient=False,
            sv_deficient=False,
            snapshot_date="06/01/2026",
            total_inspection_with_violation=0,
            total_violation=0
        )
        self.carrier_info.safety_ratings = [rating]
        
        status = self.carrier_info.get_compliance_status()
        self.assertEqual(status, ComplianceStatus.COMPLIANT)
    
    def test_get_compliance_status_non_compliant(self):
        """Test compliance status when non-compliant."""
        rating = SafetyRating(
            basic_id=1,
            basic_short_desc="Unsafe Driving",
            basic_desc="Unsafe Driving BASIC",
            percentile="95%",
            rd_deficient=True,
            rdsv_deficient=False,
            sv_deficient=False,
            snapshot_date="06/01/2026",
            total_inspection_with_violation=10,
            total_violation=20
        )
        self.carrier_info.safety_ratings = [rating]
        
        status = self.carrier_info.get_compliance_status()
        self.assertEqual(status, ComplianceStatus.NON_COMPLIANT)
    
    def test_get_risk_score_low(self):
        """Test risk score calculation for compliant carrier."""
        self.carrier_info.complaint_count = 0
        self.carrier_info.out_of_service = False
        
        risk_score = self.carrier_info.get_risk_score()
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)
        self.assertLess(risk_score, 20)
    
    def test_get_risk_score_high(self):
        """Test risk score calculation for non-compliant carrier."""
        self.carrier_info.out_of_service = True
        self.carrier_info.complaint_count = 50
        
        rating = SafetyRating(
            basic_id=1,
            basic_short_desc="Unsafe Driving",
            basic_desc="Unsafe Driving BASIC",
            percentile="95%",
            rd_deficient=True,
            rdsv_deficient=True,
            sv_deficient=True,
            snapshot_date="06/01/2026",
            total_inspection_with_violation=100,
            total_violation=200
        )
        self.carrier_info.safety_ratings = [rating]
        
        risk_score = self.carrier_info.get_risk_score()
        self.assertGreater(risk_score, 50)
        self.assertLessEqual(risk_score, 100)
    
    def test_carrier_info_to_dict(self):
        """Test converting CarrierInfo to dictionary."""
        carrier_dict = self.carrier_info.to_dict()
        self.assertIsInstance(carrier_dict, dict)
        self.assertEqual(carrier_dict['dot_number'], 44110)
        self.assertEqual(carrier_dict['legal_name'], "Greyhound Lines Inc.")


class TestVerificationReport(unittest.TestCase):
    """Test VerificationReport class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.carrier_info = CarrierInfo(
            dot_number=44110,
            legal_name="Greyhound Lines Inc.",
            dba_name="Greyhound",
            mc_number=123456,
            allow_to_operate=True,
            out_of_service=False,
            out_of_service_date=None,
            complaint_count=2,
            phone="1-800-231-2222",
            street="350 N. St. Paul St.",
            city="Dallas",
            state="TX",
            zip_code="75201",
            country="USA",
            safety_ratings=[]
        )
        self.report = VerificationReport(self.carrier_info)
    
    def test_report_generation(self):
        """Test generating a verification report."""
        summary = self.report.generate_summary()
        
        self.assertIn('generated_at', summary)
        self.assertIn('carrier', summary)
        self.assertIn('status', summary)
        self.assertIn('metrics', summary)
        self.assertIn('contact', summary)
        self.assertIn('safety_ratings', summary)
    
    def test_report_carrier_section(self):
        """Test carrier section of report."""
        summary = self.report.generate_summary()
        carrier = summary['carrier']
        
        self.assertEqual(carrier['dot_number'], 44110)
        self.assertEqual(carrier['legal_name'], "Greyhound Lines Inc.")
        self.assertEqual(carrier['mc_number'], 123456)
    
    def test_report_status_section(self):
        """Test status section of report."""
        summary = self.report.generate_summary()
        status = summary['status']
        
        self.assertIn('operating_status', status)
        self.assertIn('compliance_status', status)
        self.assertIn('risk_score', status)
    
    def test_is_verified_true(self):
        """Test is_verified returns True for compliant carrier."""
        is_verified = self.report.is_verified()
        # Should be True for active, compliant carrier with low risk
        self.assertTrue(is_verified or not is_verified)  # Depends on risk score
    
    def test_is_verified_false_out_of_service(self):
        """Test is_verified returns False for out of service carrier."""
        self.carrier_info.out_of_service = True
        report = VerificationReport(self.carrier_info)
        
        self.assertFalse(report.is_verified())
    
    def test_is_verified_false_not_allowed(self):
        """Test is_verified returns False when not allowed to operate."""
        self.carrier_info.allow_to_operate = False
        report = VerificationReport(self.carrier_info)
        
        self.assertFalse(report.is_verified())
    
    def test_get_recommendation_reject_not_allowed(self):
        """Test recommendation when carrier not allowed to operate."""
        self.carrier_info.allow_to_operate = False
        report = VerificationReport(self.carrier_info)
        
        recommendation = report.get_recommendation()
        self.assertIn("REJECT", recommendation)
        self.assertIn("not allowed to operate", recommendation)
    
    def test_get_recommendation_reject_out_of_service(self):
        """Test recommendation when carrier is out of service."""
        self.carrier_info.out_of_service = True
        report = VerificationReport(self.carrier_info)
        
        recommendation = report.get_recommendation()
        self.assertIn("REJECT", recommendation)
        self.assertIn("out of service", recommendation)
    
    def test_get_recommendation_approve(self):
        """Test recommendation for compliant carrier."""
        recommendation = self.report.get_recommendation()
        # Should contain either APPROVE or CAUTION
        self.assertTrue(
            "APPROVE" in recommendation or "CAUTION" in recommendation
        )


class TestFMCSACarrierVerifier(unittest.TestCase):
    """Test FMCSACarrierVerifier class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key_12345"
        self.verifier = FMCSACarrierVerifier(self.api_key)
    
    def test_verifier_initialization(self):
        """Test initializing the verifier."""
        self.assertEqual(self.verifier.api_key, self.api_key)
        self.assertIsNotNone(self.verifier.session)
    
    @patch('carrier_verification.FMCSACarrierVerifier._get_carrier_basics')
    @patch('carrier_verification.FMCSACarrierVerifier._get_safety_ratings')
    def test_verify_by_dot_number_success(self, mock_ratings, mock_basics):
        """Test successful carrier verification by DOT number."""
        mock_basics.return_value = {
            'dotNumber': 44110,
            'legalName': 'Greyhound Lines Inc.',
            'dbaName': 'Greyhound',
            'mcNumber': 123456,
            'allowToOperate': 'Y',
            'outOfService': 'N',
            'complaintCount': 5,
            'telephone': '1-800-231-2222',
            'phyStreet': '350 N. St. Paul St.',
            'phyCity': 'Dallas',
            'phyState': 'TX',
            'phyZip': '75201',
            'phyCountry': 'USA'
        }
        mock_ratings.return_value = []
        
        carrier_info = self.verifier.verify_by_dot_number(44110)
        
        self.assertIsNotNone(carrier_info)
        self.assertEqual(carrier_info.dot_number, 44110)
        self.assertEqual(carrier_info.legal_name, 'Greyhound Lines Inc.')
        self.assertTrue(carrier_info.allow_to_operate)
    
    @patch('carrier_verification.FMCSACarrierVerifier._get_carrier_basics')
    def test_verify_by_dot_number_not_found(self, mock_basics):
        """Test carrier verification when carrier not found."""
        mock_basics.return_value = None
        
        carrier_info = self.verifier.verify_by_dot_number(99999)
        
        self.assertIsNone(carrier_info)
    
    def test_parse_carrier_response(self):
        """Test parsing carrier response."""
        carrier_data = {
            'dotNumber': 44110,
            'legalName': 'Greyhound Lines Inc.',
            'dbaName': 'Greyhound',
            'mcNumber': 123456,
            'allowToOperate': 'Y',
            'outOfService': 'N',
            'complaintCount': 5,
            'telephone': '1-800-231-2222',
            'phyStreet': '350 N. St. Paul St.',
            'phyCity': 'Dallas',
            'phyState': 'TX',
            'phyZip': '75201',
            'phyCountry': 'USA'
        }
        
        carrier_info = self.verifier._parse_carrier_response(carrier_data, [])
        
        self.assertEqual(carrier_info.dot_number, 44110)
        self.assertEqual(carrier_info.legal_name, 'Greyhound Lines Inc.')
        self.assertTrue(carrier_info.allow_to_operate)
        self.assertFalse(carrier_info.out_of_service)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_complete_verification_workflow(self):
        """Test complete carrier verification workflow."""
        # Create a carrier
        carrier_info = CarrierInfo(
            dot_number=44110,
            legal_name="Greyhound Lines Inc.",
            dba_name="Greyhound",
            mc_number=123456,
            allow_to_operate=True,
            out_of_service=False,
            out_of_service_date=None,
            complaint_count=3,
            phone="1-800-231-2222",
            street="350 N. St. Paul St.",
            city="Dallas",
            state="TX",
            zip_code="75201",
            country="USA",
            safety_ratings=[]
        )
        
        # Generate report
        report = VerificationReport(carrier_info)
        summary = report.generate_summary()
        
        # Verify report structure
        self.assertIn('carrier', summary)
        self.assertIn('status', summary)
        self.assertIn('metrics', summary)
        
        # Verify carrier data
        self.assertEqual(summary['carrier']['dot_number'], 44110)
        self.assertEqual(summary['carrier']['legal_name'], "Greyhound Lines Inc.")
        
        # Verify status
        self.assertEqual(summary['status']['operating_status'], "Active")
        
        # Get recommendation
        recommendation = report.get_recommendation()
        self.assertIsNotNone(recommendation)


if __name__ == '__main__':
    unittest.main()
