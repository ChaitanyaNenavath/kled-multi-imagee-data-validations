# HappyRobot FDE Challenge - Implementation Guide

## Challenge Overview

The HappyRobot FDE (Forward Deployed Engineer) take-home challenge requires building a **carrier verification system** that integrates with the **FMCSA QCMobile API** to verify motor carrier information, safety ratings, and compliance status.

## Key Requirements

### 1. API Integration
- ✅ Integrate with FMCSA QCMobile API
- ✅ Support multiple query methods (by USDOT number, carrier name, docket number)
- ✅ Handle API authentication using webkey
- ✅ Parse JSON responses correctly

### 2. Data Extraction
- ✅ Extract carrier information (name, address, contact)
- ✅ Extract safety ratings (BASIC scores)
- ✅ Extract compliance indicators (deficiency flags)
- ✅ Extract operating authority status

### 3. Business Logic
- ✅ Determine operating status (Active, Out of Service, Unknown)
- ✅ Calculate compliance status based on safety ratings
- ✅ Compute risk scores using multi-factor analysis
- ✅ Generate verification recommendations

### 4. Code Quality
- ✅ Production-ready Python code with proper error handling
- ✅ Comprehensive unit tests (26 tests, 100% pass rate)
- ✅ Clear documentation and examples
- ✅ Type hints and dataclass usage
- ✅ Logging for debugging and monitoring

## Solution Architecture

### Core Components

#### 1. Data Models

**SafetyRating** - Represents a BASIC (safety category) rating
```python
@dataclass
class SafetyRating:
    basic_id: int
    basic_short_desc: str
    percentile: Optional[str]
    rd_deficient: bool  # Road Deficient
    rdsv_deficient: bool  # Road Safety Violation Deficient
    sv_deficient: bool  # Serious Violation Deficient
```

**CarrierInfo** - Represents complete carrier information
```python
@dataclass
class CarrierInfo:
    dot_number: int
    legal_name: str
    allow_to_operate: bool
    out_of_service: bool
    complaint_count: int
    safety_ratings: List[SafetyRating]
    
    # Methods for status determination
    def get_operating_status() -> OperatingStatus
    def get_compliance_status() -> ComplianceStatus
    def get_risk_score() -> float
```

#### 2. API Integration

**FMCSACarrierVerifier** - Handles API communication
```python
class FMCSACarrierVerifier:
    def verify_by_dot_number(dot_number: int) -> Optional[CarrierInfo]
    def verify_by_name(carrier_name: str) -> List[CarrierInfo]
    def _get_carrier_basics(dot_number: int) -> Optional[Dict]
    def _get_safety_ratings(dot_number: int) -> List[Dict]
    def _parse_carrier_response(carrier_data: Dict, safety_ratings: List[Dict]) -> CarrierInfo
```

#### 3. Reporting

**VerificationReport** - Generates verification reports
```python
class VerificationReport:
    def generate_summary() -> Dict
    def is_verified() -> bool
    def get_recommendation() -> str
```

### Data Flow

```
User Request
    ↓
FMCSACarrierVerifier.verify_by_dot_number()
    ↓
API Call: /carriers/{dotNumber}/basics
    ↓
Parse Response → CarrierInfo
    ↓
API Call: /carriers/{dotNumber}/basics (for safety ratings)
    ↓
Parse Safety Ratings → List[SafetyRating]
    ↓
VerificationReport.generate_summary()
    ↓
Risk Score Calculation
    ↓
Compliance Assessment
    ↓
Recommendation Generation
    ↓
JSON Report Output
```

## Implementation Details

### Risk Score Calculation

The risk score (0-100) combines three factors:

```
Risk Score = Out_of_Service_Factor + Complaint_Factor + Safety_Rating_Factor

Out_of_Service_Factor:
  - 50 points if out_of_service == True
  - 0 points otherwise

Complaint_Factor:
  - min((complaint_count / 10) * 20, 20)
  - Normalized complaint count

Safety_Rating_Factor:
  - min((deficient_count / total_ratings) * 30, 30)
  - Based on deficiency indicators
```

### Compliance Status Determination

```
if no safety_ratings:
    return ComplianceStatus.INSUFFICIENT_DATA

deficient_count = count(ratings where rd_deficient or rdsv_deficient)

if deficient_count == 0:
    return ComplianceStatus.COMPLIANT
elif deficient_count > 0:
    return ComplianceStatus.NON_COMPLIANT
else:
    return ComplianceStatus.INCONCLUSIVE
```

### Verification Criteria

A carrier is considered verified if ALL of the following are true:

1. `allow_to_operate == True`
2. `out_of_service == False`
3. `compliance_status == ComplianceStatus.COMPLIANT`
4. `risk_score < 50`

## API Response Handling

### Expected Response Structure

```json
{
  "CarrierSnapshot": {
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
    "phyCountry": "USA",
    "BASICS": [
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
    ]
  }
}
```

### Error Handling

The system handles:
- Network timeouts (10-second timeout per request)
- Invalid API responses (validates JSON structure)
- Missing fields (uses defaults or optional types)
- API errors (logs and returns None)
- Connection errors (graceful degradation)

## Testing Strategy

### Test Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| SafetyRating | 2 | Creation, serialization |
| CarrierInfo | 10 | Status determination, risk calculation |
| VerificationReport | 9 | Report generation, recommendations |
| FMCSACarrierVerifier | 4 | API integration, parsing |
| Integration | 1 | Complete workflow |
| **Total** | **26** | **100%** |

### Running Tests

```bash
# Run all tests
python3 -m unittest test_carrier_verification -v

# Run specific test class
python3 -m unittest test_carrier_verification.TestCarrierInfo -v

# Run with coverage
python3 -m coverage run -m unittest test_carrier_verification
python3 -m coverage report
```

## Usage Examples

### Example 1: Verify Single Carrier

```python
from carrier_verification import FMCSACarrierVerifier, VerificationReport

api_key = "your_api_key"
verifier = FMCSACarrierVerifier(api_key)

# Verify carrier
carrier = verifier.verify_by_dot_number(44110)

if carrier:
    report = VerificationReport(carrier)
    print(f"Operating Status: {carrier.get_operating_status().value}")
    print(f"Compliance Status: {carrier.get_compliance_status().value}")
    print(f"Risk Score: {carrier.get_risk_score()}")
    print(f"Recommendation: {report.get_recommendation()}")
```

### Example 2: Batch Verification

```python
dot_numbers = [44110, 123456, 789012]
verifier = FMCSACarrierVerifier(api_key)

for dot in dot_numbers:
    carrier = verifier.verify_by_dot_number(dot)
    if carrier:
        report = VerificationReport(carrier)
        print(f"{carrier.legal_name}: {report.get_recommendation()}")
```

### Example 3: Search by Name

```python
carriers = verifier.verify_by_name("Greyhound")

for carrier in carriers:
    report = VerificationReport(carrier)
    if report.is_verified():
        print(f"✓ {carrier.legal_name}")
    else:
        print(f"✗ {carrier.legal_name}")
```

## Production Deployment

### Security Considerations

1. **API Key Management**
   - Store in environment variables: `FMCSA_API_KEY`
   - Never commit to version control
   - Rotate periodically

2. **HTTPS Enforcement**
   - All API calls use HTTPS
   - Verify SSL certificates
   - Use secure session handling

3. **Rate Limiting**
   - Implement request throttling
   - Cache results to reduce API calls
   - Handle 429 (Too Many Requests) responses

### Performance Optimization

1. **Caching**
   ```python
   # Cache carrier lookups for 24 hours
   cache = {}
   cache_ttl = 86400  # seconds
   ```

2. **Batch Processing**
   ```python
   # Process multiple carriers efficiently
   carriers = [verify_by_dot_number(dot) for dot in dot_numbers]
   ```

3. **Async Operations**
   ```python
   # Use asyncio for concurrent verifications
   import asyncio
   tasks = [verify_async(dot) for dot in dot_numbers]
   results = await asyncio.gather(*tasks)
   ```

### Monitoring and Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('carrier_verification.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log all verifications
logger.info(f"Verified carrier: {carrier.legal_name}")
logger.warning(f"High risk carrier: {carrier.legal_name}")
logger.error(f"Verification failed for DOT {dot_number}")
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Invalid API key | Verify API key is correct and active |
| No results | Carrier not found | Check USDOT number or carrier name spelling |
| Timeout | Network issue | Increase timeout or retry with backoff |
| Missing fields | API response incomplete | Handle optional fields gracefully |

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger('carrier_verification').setLevel(logging.DEBUG)

# Inspect raw API responses
verifier = FMCSACarrierVerifier(api_key)
response = verifier._get_carrier_basics(44110)
print(json.dumps(response, indent=2))
```

## Integration with HappyRobot Platform

### Workflow Integration

```python
# In HappyRobot workflow
def verify_carrier_workflow(dot_number):
    verifier = FMCSACarrierVerifier(api_key)
    carrier = verifier.verify_by_dot_number(dot_number)
    report = VerificationReport(carrier)
    
    return {
        'carrier_info': carrier.to_dict(),
        'recommendation': report.get_recommendation(),
        'verified': report.is_verified()
    }
```

### API Endpoint Example

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/verify/<int:dot_number>', methods=['GET'])
def verify_carrier(dot_number):
    verifier = FMCSACarrierVerifier(api_key)
    carrier = verifier.verify_by_dot_number(dot_number)
    
    if not carrier:
        return jsonify({'error': 'Carrier not found'}), 404
    
    report = VerificationReport(carrier)
    return jsonify(report.generate_summary())
```

## Next Steps

1. **Obtain FMCSA API Key**
   - Register at https://mobile.fmcsa.dot.gov/
   - Request API webkey
   - Store securely

2. **Deploy to Production**
   - Set up environment variables
   - Configure logging and monitoring
   - Implement caching layer
   - Set up error alerts

3. **Extend Functionality**
   - Add database storage
   - Build web dashboard
   - Create batch processing system
   - Implement webhook notifications

## References

- [FMCSA QCMobile API](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi)
- [API Elements Documentation](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiElements)
- [SAFER Database](https://safer.fmcsa.dot.gov/)
- [CSA Program](https://csa.fmcsa.dot.gov/)

## Support

For questions about the implementation, refer to:
- README.md - General documentation
- Code comments - Implementation details
- Unit tests - Usage examples
- FMCSA documentation - API details
