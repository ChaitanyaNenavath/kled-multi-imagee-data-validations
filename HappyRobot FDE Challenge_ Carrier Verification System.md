# HappyRobot FDE Challenge: Carrier Verification System

## Overview

This is a complete carrier verification solution for the HappyRobot Forward Deployed Engineer (FDE) take-home challenge. The system integrates with the **FMCSA QCMobile API** to verify carrier information, safety ratings, compliance status, and operational authority.

## Features

### Core Functionality

- **Carrier Lookup by USDOT Number**: Query carrier information using FMCSA USDOT number
- **Carrier Search by Name**: Search for carriers by legal name or DBA name
- **Safety Rating Analysis**: Extract and analyze BASIC (Behavior Analysis and Safety Improvement Categories) ratings
- **Risk Scoring**: Calculate comprehensive risk scores (0-100) based on multiple factors
- **Compliance Assessment**: Determine compliance status based on safety metrics
- **Verification Reports**: Generate detailed verification reports with recommendations

### Data Elements Extracted

The system extracts the following information from the FMCSA API:

**Carrier Information:**
- USDOT Number
- Legal Name and DBA Name
- MC (Motor Carrier) Number
- Operating Authority Status
- Out of Service Status
- Contact Information (Phone, Address)
- Complaint Count

**Safety Ratings (BASICS):**
- Unsafe Driving
- Driver Fitness
- Fatigued Driving
- Controlled Substance/Alcohol
- Vehicle Maintenance

**Compliance Metrics:**
- Deficiency Indicators (RD, RDSV, SV)
- Inspection and Violation Counts
- Percentile Rankings
- Snapshot Dates

## Architecture

### Class Hierarchy

```
SafetyRating
  ├── basic_id
  ├── basic_short_desc
  ├── percentile
  ├── rd_deficient
  ├── rdsv_deficient
  └── sv_deficient

CarrierInfo
  ├── dot_number
  ├── legal_name
  ├── allow_to_operate
  ├── out_of_service
  ├── complaint_count
  ├── safety_ratings: List[SafetyRating]
  ├── get_operating_status()
  ├── get_compliance_status()
  └── get_risk_score()

FMCSACarrierVerifier
  ├── verify_by_dot_number(dot_number: int)
  ├── verify_by_name(carrier_name: str)
  ├── _get_carrier_basics(dot_number: int)
  └── _get_safety_ratings(dot_number: int)

VerificationReport
  ├── generate_summary()
  ├── is_verified()
  └── get_recommendation()
```

### Enumerations

**OperatingStatus:**
- `ACTIVE`: Carrier is actively operating
- `OUT_OF_SERVICE`: Carrier has received out-of-service order
- `UNKNOWN`: Status cannot be determined

**ComplianceStatus:**
- `COMPLIANT`: Carrier meets all compliance requirements
- `NON_COMPLIANT`: Carrier has deficiencies
- `INCONCLUSIVE`: Status cannot be determined
- `INSUFFICIENT_DATA`: No safety rating data available

## Installation

### Prerequisites

- Python 3.8+
- `requests` library

### Setup

```bash
# Install dependencies
pip install requests

# Make the script executable
chmod +x carrier_verification.py
```

## Usage

### Basic Usage

```python
from carrier_verification import FMCSACarrierVerifier, VerificationReport

# Initialize verifier with FMCSA API key
api_key = "your_fmcsa_api_key_here"
verifier = FMCSACarrierVerifier(api_key)

# Verify carrier by USDOT number
carrier_info = verifier.verify_by_dot_number(44110)

if carrier_info:
    # Generate verification report
    report = VerificationReport(carrier_info)
    summary = report.generate_summary()
    
    # Get recommendation
    recommendation = report.get_recommendation()
    print(f"Recommendation: {recommendation}")
    print(f"Verified: {report.is_verified()}")
```

### Search by Carrier Name

```python
# Search for carriers by name
carriers = verifier.verify_by_name("Greyhound")

for carrier in carriers:
    report = VerificationReport(carrier)
    print(f"{carrier.legal_name}: {report.get_recommendation()}")
```

### Command Line Usage

```bash
# Run the module directly
python3 carrier_verification.py

# Output includes:
# - Carrier information
# - Operating status
# - Compliance status
# - Risk score
# - Safety ratings
# - Recommendation
```

## Risk Score Calculation

The risk score is calculated on a scale of 0-100, where higher scores indicate higher risk:

```
Risk Score = Out_of_Service_Factor + Complaint_Factor + Safety_Rating_Factor

Out_of_Service_Factor:
  - 50 points if carrier is out of service
  - 0 points otherwise

Complaint_Factor:
  - (complaint_count / 10) * 20, capped at 20 points

Safety_Rating_Factor:
  - (deficient_ratings / total_ratings) * 30, capped at 30 points
```

### Risk Score Interpretation

- **0-25**: Low Risk - Carrier meets all criteria
- **25-50**: Medium-Low Risk - Minor issues, generally acceptable
- **50-75**: Medium-High Risk - Significant issues, manual review recommended
- **75-100**: High Risk - Major deficiencies, rejection recommended

## Verification Criteria

A carrier is considered **verified** if:

1. ✅ Allowed to operate (`allow_to_operate == True`)
2. ✅ Not out of service (`out_of_service == False`)
3. ✅ Compliant status (`compliance_status == COMPLIANT`)
4. ✅ Risk score below 50 (`risk_score < 50`)

## Recommendations

The system provides four types of recommendations:

### REJECT: Carrier Not Allowed to Operate
- Carrier does not have operating authority
- **Action**: Do not work with this carrier

### REJECT: Carrier Out of Service
- Carrier has received out-of-service order
- **Action**: Do not work with this carrier

### REJECT: High Risk Carrier
- Risk score >= 75
- **Action**: Do not work with this carrier

### CAUTION: Medium Risk Carrier
- Risk score between 50-75, or non-compliant status
- **Action**: Manual review recommended before proceeding

### APPROVE: Carrier Meets Verification Criteria
- All verification criteria met
- Risk score < 50
- **Action**: Carrier is approved for work

## API Response Structure

### Carrier Basics Response

```json
{
  "dotNumber": 44110,
  "legalName": "Greyhound Lines Inc.",
  "dbaName": "Greyhound",
  "mcNumber": 123456,
  "allowToOperate": "Y",
  "outOfService": "N",
  "complaintCount": 5,
  "telephone": "1-800-231-2222",
  "phyStreet": "350 N. St. Paul St.",
  "phyCity": "Dallas",
  "phyState": "TX",
  "phyZip": "75201",
  "phyCountry": "USA"
}
```

### Safety Ratings Response

```json
{
  "basicId": 1,
  "basicShortDesc": "Unsafe Driving",
  "basicDesc": "Unsafe Driving BASIC",
  "percentile": "75%",
  "rdDeficient": "Y",
  "rdsvDeficient": "N",
  "svDeficient": "N",
  "snapShotDate": "06/01/2026",
  "totalInspectionWithViolation": 5,
  "totalViolation": 10
}
```

## Testing

The solution includes comprehensive unit tests covering:

- Data model creation and validation
- Operating status determination
- Compliance status calculation
- Risk score computation
- Verification report generation
- API response parsing
- Integration workflows

### Running Tests

```bash
# Run all tests
python3 -m unittest test_carrier_verification.py -v

# Run specific test class
python3 -m unittest test_carrier_verification.TestCarrierInfo -v

# Run specific test
python3 -m unittest test_carrier_verification.TestCarrierInfo.test_get_risk_score_high -v
```

### Test Coverage

The test suite includes:

- **SafetyRating Tests**: Creation, serialization, data validation
- **CarrierInfo Tests**: Status determination, risk calculation, compliance assessment
- **VerificationReport Tests**: Report generation, verification logic, recommendations
- **FMCSACarrierVerifier Tests**: API integration, response parsing, error handling
- **Integration Tests**: Complete workflow from verification to reporting

## Error Handling

The system includes robust error handling:

- **API Request Failures**: Gracefully handles network errors and timeouts
- **Invalid Responses**: Validates API response structure before parsing
- **Missing Data**: Handles missing or optional fields in API responses
- **Logging**: Comprehensive logging for debugging and monitoring

## Production Considerations

### Security

- API keys should be stored in environment variables, not hardcoded
- Use HTTPS for all API communications (enforced by FMCSA)
- Implement rate limiting to avoid API throttling
- Add authentication/authorization for report access

### Performance

- Implement caching for frequently queried carriers
- Use connection pooling for API requests
- Consider batch verification for multiple carriers
- Implement async/await for concurrent verifications

### Monitoring

- Log all verification requests and results
- Track API response times and error rates
- Monitor risk score distribution
- Alert on unusual patterns or high-risk carriers

### Scalability

- Use a message queue for asynchronous verification
- Implement database storage for verification history
- Create a web API for programmatic access
- Build a dashboard for monitoring and reporting

## Example Output

```json
{
  "generated_at": "2026-06-13T10:30:45.123456",
  "carrier": {
    "dot_number": 44110,
    "legal_name": "Greyhound Lines Inc.",
    "dba_name": "Greyhound",
    "mc_number": 123456
  },
  "status": {
    "operating_status": "Active",
    "compliance_status": "Compliant",
    "risk_score": 15.5
  },
  "metrics": {
    "complaint_count": 5,
    "allow_to_operate": true,
    "out_of_service": false,
    "out_of_service_date": null
  },
  "contact": {
    "phone": "1-800-231-2222",
    "address": {
      "street": "350 N. St. Paul St.",
      "city": "Dallas",
      "state": "TX",
      "zip": "75201",
      "country": "USA"
    }
  },
  "safety_ratings": []
}

Recommendation: APPROVE: Carrier meets verification criteria
Verified: true
```

## FMCSA API Documentation

For more information about the FMCSA QCMobile API, visit:
- [FMCSA Developer Portal](https://mobile.fmcsa.dot.gov/)
- [QCMobile API Documentation](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi)
- [API Elements Description](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiElements)
- [SAFER Database](https://safer.fmcsa.dot.gov/)

## References

- **FMCSA**: Federal Motor Carrier Safety Administration
- **SAFER**: Safety and Fitness Electronic Records
- **BASIC**: Behavior Analysis and Safety Improvement Categories
- **CSA**: Compliance, Safety, Accountability
- **USDOT**: United States Department of Transportation
- **MC Number**: Motor Carrier Authority Number

## Author

HappyRobot FDE Candidate

## License

This solution is provided for the HappyRobot FDE interview challenge.

## Support

For questions or issues, please refer to the FMCSA API documentation or contact the HappyRobot team.
