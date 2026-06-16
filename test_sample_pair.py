#!/usr/bin/env python3
"""
Test with known working sample pair (Phenoxypropazine + Synephrine)
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# Read vectors from sample file
with open('samples/sample_model_inputs (1).txt', 'r') as f:
    content = f.read()

# Extract drug 1 vector
drug1_start = content.find("Drug 1 Vector (2048 values):\n[") + len("Drug 1 Vector (2048 values):\n")
drug1_end = content.find("]", drug1_start) + 1
drug1_vector = json.loads(content[drug1_start:drug1_end])

# Extract drug 2 vector
drug2_start = content.find("Drug 2 Vector (2048 values):\n[") + len("Drug 2 Vector (2048 values):\n")
drug2_end = content.find("]", drug2_start) + 1
drug2_vector = json.loads(content[drug2_start:drug2_end])

print("=" * 60)
print("Testing KNOWN WORKING PAIR (Phenoxypropazine + Synephrine)")
print("=" * 60)
print(f"Drug 1 Vector length: {len(drug1_vector)}")
print(f"Drug 2 Vector length: {len(drug2_vector)}")
print(f"Expected output: 1 (Harmful)")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/predict-sample",
        json={
            'drug1_vector': drug1_vector,
            'drug2_vector': drug2_vector
        },
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Prediction successful")
        print(f"  Prediction class: {result.get('prediction')} (0=Safe, 1=Harmful)")
        print(f"  Class name: {result.get('class_name')}")
        print(f"  Confidence: {result.get('confidence')}%")
        print(f"  All probabilities: {result.get('all_probabilities')}")
        
        print()
        if result.get('prediction') == 1:
            print(f"✓✓✓ CORRECT: Known pair predicts as Harmful")
            print(f"\nThe model IS working correctly for known test data!")
            print(f"This suggests your user vector may have:")
            print(f"  - Different feature representation")
            print(f"  - Different scaling/normalization")
            print(f"  - Features that don't match training distribution")
        else:
            print(f"✗ ERROR: Known pair should predict as Harmful but got {result.get('prediction')}")
            print(f"\nThe model may NOT be properly trained or weights not loaded correctly")
    else:
        print(f"✗ Error status: {response.status_code}")
        print(f"  Details: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
