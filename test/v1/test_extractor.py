import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.extractor import Extractor, ExtractionType

def test_extractor():
    print("=== Testing Extractor ===")
    extractor = Extractor()
    
    text = (
        "Contact Sanjay at sanjay@example.com or support@agentium.org. "
        "Call us at +1-555-123-4567 or (555) 987-6543 on 2026-10-03. "
        "Visit https://github.com/RNSsanjay/Agentium-Python-Library for $49.99 software license."
    )
    
    # 1. Emails
    emails = extractor.extract(text, extraction_type=ExtractionType.EMAILS)
    print("Extracted Emails:", emails)
    assert "sanjay@example.com" in str(emails)
    
    # 2. URLs
    urls = extractor.extract(text, extraction_type=ExtractionType.URLS)
    print("Extracted URLs:", urls)
    assert "https://github.com/RNSsanjay/Agentium-Python-Library" in str(urls)
    
    # 3. Numbers
    numbers = extractor.extract(text, extraction_type=ExtractionType.NUMBERS)
    print("Extracted Numbers:", numbers)

    # 4. Dates
    dates = extractor.extract(text, extraction_type=ExtractionType.DATES)
    print("Extracted Dates:", dates)

    print("Result: PASS\n")

if __name__ == "__main__":
    test_extractor()
