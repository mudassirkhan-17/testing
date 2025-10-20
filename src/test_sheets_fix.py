#!/usr/bin/env python3
"""
TEST: Verify Google Sheets fix works
"""

def test_sheets_function():
    """Test the fixed Google Sheets function"""
    
    # Mock carriers data
    carriers = [
        {'name': 'K'},
        {'name': 'Q'}
    ]
    
    # Import the function
    from multi_carrier import push_multi_carrier_to_sheets
    
    print("Testing Google Sheets function...")
    print("Carriers:", [c['name'] for c in carriers])
    
    # This should work without the Response [200] error
    try:
        result = push_multi_carrier_to_sheets(carriers)
        print(f"Result: {result}")
        print("✅ Test completed!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_sheets_function()
