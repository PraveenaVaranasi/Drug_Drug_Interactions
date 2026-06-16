#!/usr/bin/env python3
"""
Test API endpoints for drug-drug interaction model
Validates that all updates are working correctly
"""

import requests
import json
import time
import numpy as np

BASE_URL = "http://localhost:5000"

def test_api_health():
    """Test if server is running"""
    print("\n" + "="*60)
    print("TEST: Server Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Server is running")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return False

def test_api_info():
    """Test /api/info endpoint"""
    print("\n" + "="*60)
    print("TEST: API Info Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ /api/info endpoint working")
            print(f"\n  Classes: {data.get('class_names')}")
            print(f"  Input size: {data.get('input_size')}")
            print(f"  Max input size: {data.get('max_input_size')}")
            
            if 'example_input' in data:
                example = data['example_input']
                print(f"\n  Example Input:")
                print(f"    Drug 1: {example.get('drug1_name')} ({example.get('drug1_vector_length')} dims)")
                print(f"    Drug 2: {example.get('drug2_name')} ({example.get('drug2_vector_length')} dims)")
                print(f"    Combined: {example.get('combined_length')} dims")
                print(f"    Processed: {example.get('processed_length')} dims")
            
            # Verify classes
            if data.get('class_names') == ['Safe', 'Harmful']:
                print("\n✓ Classes are correct: ['Safe', 'Harmful']")
                return True
            else:
                print(f"\n✗ Classes are incorrect: {data.get('class_names')}")
                return False
        else:
            print(f"✗ Endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_api_predict():
    """Test /api/predict endpoint with sample data"""
    print("\n" + "="*60)
    print("TEST: API Predict Endpoint")
    print("="*60)
    
    # Create sample 4096-dimensional vector
    sample_vector = np.random.randn(4096).astype(np.float32)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict",
            json={'matrix': sample_vector.tolist()},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ /api/predict endpoint working")
            print(f"  Prediction: {result.get('prediction')}")
            print(f"  Class: {result.get('class_name')}")
            print(f"  Interaction: {result.get('interaction')}")
            print(f"  Confidence: {result.get('confidence')}%")
            
            if result.get('class_name') in ['Safe', 'Harmful']:
                print("✓ Response contains valid class names")
                return True
            else:
                print(f"✗ Response contains invalid class: {result.get('class_name')}")
                return False
        else:
            print(f"✗ Endpoint returned status {response.status_code}")
            print(f"  Details: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_api_predict_sample():
    """Test /api/predict-sample endpoint"""
    print("\n" + "="*60)
    print("TEST: API Predict-Sample Endpoint")
    print("="*60)
    
    # Create sample 2048-dimensional vectors
    drug1_vector = np.random.randn(2048).astype(np.float32)
    drug2_vector = np.random.randn(2048).astype(np.float32)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict-sample",
            json={
                'drug1_vector': drug1_vector.tolist(),
                'drug2_vector': drug2_vector.tolist()
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ /api/predict-sample endpoint working")
            print(f"  Prediction: {result.get('prediction')}")
            print(f"  Interaction Type: {result.get('interaction_type')}")
            print(f"  Confidence: {result.get('confidence')}%")
            
            if result.get('interaction_type') in ['Safe', 'Harmful']:
                print("✓ Response contains valid interaction type")
                return True
            else:
                print(f"✗ Response contains invalid interaction type: {result.get('interaction_type')}")
                return False
        else:
            print(f"✗ Endpoint returned status {response.status_code}")
            print(f"  Details: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("="*60)
    print("DRUG-DRUG INTERACTION MODEL - API TESTING")
    print("="*60)
    
    # Wait for server to start
    print("\nWaiting for server to start...")
    for i in range(30):
        try:
            requests.get(f"{BASE_URL}/api/health", timeout=1)
            print("✓ Server is ready")
            break
        except:
            if i < 29:
                print(f"  Attempt {i+1}/30 - server not ready yet...")
                time.sleep(1)
    
    # Run tests
    results = {
        'health': test_api_health(),
        'info': test_api_info(),
        'predict': test_api_predict(),
        'predict_sample': test_api_predict_sample()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✓ All tests passed! Model integration is complete.")
    else:
        print(f"\n✗ {total_tests - total_passed} test(s) failed.")

if __name__ == '__main__':
    main()
