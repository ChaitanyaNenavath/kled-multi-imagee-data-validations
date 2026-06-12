#!/usr/bin/env python3
"""
HappyRobot FDE Challenge: Carrier Verification using FMCSA API

This module provides a complete carrier verification solution that integrates
with the FMCSA QCMobile API to verify carrier information, safety ratings,
and compliance status.

Author: HappyRobot FDE Candidate
Date: 2026-06-13
"""

import json
import logging
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
import requests
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OperatingStatus(Enum):
    """Carrier operating status enumeration."""
    ACTIVE = "Active"
    OUT_OF_SERVICE = "Out of Service"
    UNKNOWN = "Unknown"


class ComplianceStatus(Enum):
    """Carrier compliance status enumeration."""
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    INCONCLUSIVE = "Inconclusive"
    INSUFFICIENT_DATA = "Insufficient Data"


@dataclass
class SafetyRating:
    """Represents a carrier's BASIC (Behavior Analysis and Safety Improvement Categories) rating."""
    basic_id: int
    basic_short_desc: str
    basic_desc: str
    percentile: Optional[str]
    rd_deficient: bool
    rdsv_deficient: bool
    sv_deficient: bool
    snapshot_date: str
    total_inspection_with_violation: int
    total_violation: int

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CarrierInfo:
    """Represents carrier information from FMCSA API."""
    dot_number: int
    legal_name: str
    dba_name: Optional[str]
    mc_number: Optional[int]
    allow_to_operate: bool
    out_of_service: bool
    out_of_service_date: Optional[str]
    complaint_count: int
    phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    safety_ratings: List[SafetyRating]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['safety_ratings'] = [sr.to_dict() for sr in self.safety_ratings]
        return data

    def get_operating_status(self) -> OperatingStatus:
        """Determine operating status."""
        if self.out_of_service:
            return OperatingStatus.OUT_OF_SERVICE
        elif self.allow_to_operate:
            return OperatingStatus.ACTIVE
        else:
            return OperatingStatus.UNKNOWN

    def get_compliance_status(self) -> ComplianceStatus:
        """Determine compliance status based on safety ratings."""
        if not self.safety_ratings:
            return ComplianceStatus.INSUFFICIENT_DATA

        deficient_count = sum(1 for sr in self.safety_ratings if sr.rd_deficient or sr.rdsv_deficient)
        
        if deficient_count == 0:
            return ComplianceStatus.COMPLIANT
        elif deficient_count > 0:
            return ComplianceStatus.NON_COMPLIANT
        else:
            return ComplianceStatus.INCONCLUSIVE

    def get_risk_score(self) -> float:
        """
        Calculate a risk score (0-100) based on carrier metrics.
        Higher score = higher risk.
        """
        score = 0.0
        
        # Out of service status (highest risk)
        if self.out_of_service:
            score += 50.0
        
        # Complaint count (normalized)
        complaint_score = min(self.complaint_count / 10.0 * 20.0, 20.0)
        score += complaint_score
        
        # Safety rating deficiencies
        if self.safety_ratings:
            deficient_count = sum(1 for sr in self.safety_ratings if sr.rd_deficient or sr.rdsv_deficient)
            rating_score = min(deficient_count / len(self.safety_ratings) * 30.0, 30.0)
            score += rating_score
        
        return min(score, 100.0)


class FMCSACarrierVerifier:
    """FMCSA Carrier Verification Service."""

    BASE_URL = "https://mobile.fmcsa.dot.gov/qc/services"
    
    def __init__(self, api_key: str):
        """
        Initialize the verifier with FMCSA API key.
        
        Args:
            api_key: FMCSA API webkey
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HappyRobot-FDE-Carrier-Verification/1.0'
        })

    def verify_by_dot_number(self, dot_number: int) -> Optional[CarrierInfo]:
        """
        Verify carrier by USDOT number.
        
        Args:
            dot_number: USDOT number
            
        Returns:
            CarrierInfo object or None if not found
        """
        logger.info(f"Verifying carrier with DOT number: {dot_number}")
        
        try:
            # Get basic carrier information
            carrier_data = self._get_carrier_basics(dot_number)
            if not carrier_data:
                logger.warning(f"No carrier found for DOT number: {dot_number}")
                return None
            
            # Get safety ratings
            safety_ratings = self._get_safety_ratings(dot_number)
            
            # Parse and construct CarrierInfo
            carrier_info = self._parse_carrier_response(carrier_data, safety_ratings)
            logger.info(f"Successfully verified carrier: {carrier_info.legal_name}")
            
            return carrier_info
            
        except Exception as e:
            logger.error(f"Error verifying carrier {dot_number}: {str(e)}")
            return None

    def verify_by_name(self, carrier_name: str) -> List[CarrierInfo]:
        """
        Verify carriers by name (returns list of matches).
        
        Args:
            carrier_name: Carrier legal name or DBA name
            
        Returns:
            List of CarrierInfo objects
        """
        logger.info(f"Searching for carriers with name: {carrier_name}")
        
        try:
            url = f"{self.BASE_URL}/carriers/name/{carrier_name}"
            params = {'webKey': self.api_key, 'size': 10}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'QueryCarrierResult' in data:
                carriers = data['QueryCarrierResult']
                if not isinstance(carriers, list):
                    carriers = [carriers]
                
                for carrier_data in carriers:
                    dot_number = carrier_data.get('dotNumber')
                    if dot_number:
                        carrier_info = self.verify_by_dot_number(dot_number)
                        if carrier_info:
                            results.append(carrier_info)
            
            logger.info(f"Found {len(results)} carrier(s) matching name: {carrier_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching carriers by name {carrier_name}: {str(e)}")
            return []

    def _get_carrier_basics(self, dot_number: int) -> Optional[Dict]:
        """Get basic carrier information from FMCSA API."""
        try:
            url = f"{self.BASE_URL}/carriers/{dot_number}/basics"
            params = {'webKey': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response structures
            if 'CarrierSnapshot' in data:
                return data['CarrierSnapshot']
            elif 'QueryCarrierResult' in data:
                result = data['QueryCarrierResult']
                if isinstance(result, list) and len(result) > 0:
                    return result[0]
                return result
            else:
                return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for DOT {dot_number}: {str(e)}")
            return None

    def _get_safety_ratings(self, dot_number: int) -> List[Dict]:
        """Get BASIC safety ratings for a carrier."""
        try:
            url = f"{self.BASE_URL}/carriers/{dot_number}/basics"
            params = {'webKey': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            ratings = []
            
            # Extract BASIC ratings if present
            if 'CarrierSnapshot' in data:
                snapshot = data['CarrierSnapshot']
                if 'BASICS' in snapshot:
                    basics = snapshot['BASICS']
                    if not isinstance(basics, list):
                        basics = [basics]
                    ratings = basics
            
            return ratings
            
        except Exception as e:
            logger.error(f"Error fetching safety ratings for DOT {dot_number}: {str(e)}")
            return []

    def _parse_carrier_response(self, carrier_data: Dict, safety_ratings: List[Dict]) -> CarrierInfo:
        """Parse FMCSA API response into CarrierInfo object."""
        
        # Parse safety ratings
        parsed_ratings = []
        for rating in safety_ratings:
            try:
                parsed_ratings.append(SafetyRating(
                    basic_id=rating.get('basicId', 0),
                    basic_short_desc=rating.get('basicShortDesc', ''),
                    basic_desc=rating.get('basicDesc', ''),
                    percentile=rating.get('percentile'),
                    rd_deficient=rating.get('rdDeficient', 'N') == 'Y',
                    rdsv_deficient=rating.get('rdsvDeficient', 'N') == 'Y',
                    sv_deficient=rating.get('svDeficient', 'N') == 'Y',
                    snapshot_date=rating.get('snapShotDate', ''),
                    total_inspection_with_violation=rating.get('totalInspectionWithViolation', 0),
                    total_violation=rating.get('totalViolation', 0)
                ))
            except Exception as e:
                logger.warning(f"Error parsing safety rating: {str(e)}")
        
        # Create CarrierInfo object
        carrier_info = CarrierInfo(
            dot_number=carrier_data.get('dotNumber', 0),
            legal_name=carrier_data.get('legalName', ''),
            dba_name=carrier_data.get('dbaName'),
            mc_number=carrier_data.get('mcNumber'),
            allow_to_operate=carrier_data.get('allowToOperate', 'N') == 'Y',
            out_of_service=carrier_data.get('outOfService', 'N') == 'Y',
            out_of_service_date=carrier_data.get('outOfServiceDate'),
            complaint_count=carrier_data.get('complaintCount', 0),
            phone=carrier_data.get('telephone'),
            street=carrier_data.get('phyStreet'),
            city=carrier_data.get('phyCity'),
            state=carrier_data.get('phyState'),
            zip_code=carrier_data.get('phyZip'),
            country=carrier_data.get('phyCountry'),
            safety_ratings=parsed_ratings
        )
        
        return carrier_info


class VerificationReport:
    """Generates a verification report for a carrier."""
    
    def __init__(self, carrier_info: CarrierInfo):
        """Initialize report with carrier information."""
        self.carrier_info = carrier_info
        self.generated_at = datetime.now().isoformat()
    
    def generate_summary(self) -> Dict:
        """Generate a summary report."""
        return {
            'generated_at': self.generated_at,
            'carrier': {
                'dot_number': self.carrier_info.dot_number,
                'legal_name': self.carrier_info.legal_name,
                'dba_name': self.carrier_info.dba_name,
                'mc_number': self.carrier_info.mc_number
            },
            'status': {
                'operating_status': self.carrier_info.get_operating_status().value,
                'compliance_status': self.carrier_info.get_compliance_status().value,
                'risk_score': round(self.carrier_info.get_risk_score(), 2)
            },
            'metrics': {
                'complaint_count': self.carrier_info.complaint_count,
                'allow_to_operate': self.carrier_info.allow_to_operate,
                'out_of_service': self.carrier_info.out_of_service,
                'out_of_service_date': self.carrier_info.out_of_service_date
            },
            'contact': {
                'phone': self.carrier_info.phone,
                'address': {
                    'street': self.carrier_info.street,
                    'city': self.carrier_info.city,
                    'state': self.carrier_info.state,
                    'zip': self.carrier_info.zip_code,
                    'country': self.carrier_info.country
                }
            },
            'safety_ratings': [sr.to_dict() for sr in self.carrier_info.safety_ratings]
        }
    
    def is_verified(self) -> bool:
        """Determine if carrier is verified and safe to work with."""
        return (
            self.carrier_info.allow_to_operate and
            not self.carrier_info.out_of_service and
            self.carrier_info.get_compliance_status() == ComplianceStatus.COMPLIANT and
            self.carrier_info.get_risk_score() < 50.0
        )
    
    def get_recommendation(self) -> str:
        """Get recommendation for carrier."""
        if not self.carrier_info.allow_to_operate:
            return "REJECT: Carrier is not allowed to operate"
        
        if self.carrier_info.out_of_service:
            return "REJECT: Carrier is out of service"
        
        risk_score = self.carrier_info.get_risk_score()
        if risk_score >= 75:
            return "REJECT: High risk carrier (risk score >= 75)"
        elif risk_score >= 50:
            return "CAUTION: Medium risk carrier (risk score 50-75) - Manual review recommended"
        elif self.carrier_info.get_compliance_status() != ComplianceStatus.COMPLIANT:
            return "CAUTION: Non-compliant carrier - Manual review recommended"
        else:
            return "APPROVE: Carrier meets verification criteria"


def main():
    """Main entry point for the carrier verification tool."""
    
    # Example usage
    api_key = "cdc33e44d693a3a58451898d4ec9df862c65b954"
    verifier = FMCSACarrierVerifier(api_key)
    
    # Example: Verify a carrier by DOT number
    dot_number = 44110  # Greyhound Lines Inc.
    
    print(f"\n{'='*60}")
    print(f"HappyRobot FDE Challenge - Carrier Verification")
    print(f"{'='*60}\n")
    
    carrier_info = verifier.verify_by_dot_number(dot_number)
    
    if carrier_info:
        report = VerificationReport(carrier_info)
        summary = report.generate_summary()
        
        print(json.dumps(summary, indent=2))
        print(f"\nRecommendation: {report.get_recommendation()}")
        print(f"Verified: {report.is_verified()}")
    else:
        print(f"Failed to verify carrier with DOT number: {dot_number}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
