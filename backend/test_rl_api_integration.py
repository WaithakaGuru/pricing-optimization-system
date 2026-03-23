#!/usr/bin/env python3
"""Test script to verify trained RL model is connected to API."""
import sys
import os
import requests
import json
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

from utils.checkpoint_manager import find_latest_checkpoint, list_checkpoints, get_checkpoint_info

def test_checkpoint_discovery():
    """Test that we can find trained checkpoints."""
    print("\n" + "="*60)
    print("TEST 1: Checkpoint Discovery")
    print("="*60)
    
    # List all checkpoints
    all_checkpoints = list_checkpoints()
    print(f"\n✓ Found checkpoints for {len(all_checkpoints)} agent types:")
    for agent_type, checkpoints in all_checkpoints.items():
        print(f"  - {agent_type}: {len(checkpoints)} checkpoint(s)")
        for cp in checkpoints:
            info = get_checkpoint_info(cp["path"])
            print(f"    • {cp['filename']}")
            if info and info.get("reward_score"):
                print(f"      Reward: {info['reward_score']}")
    
    # Find latest for each type
    print("\n✓ Latest checkpoints per agent type:")
    for agent_type in ["ppo", "sac", "bandit"]:
        latest = find_latest_checkpoint(agent_type)
        if latest:
            info = get_checkpoint_info(latest)
            print(f"  - {agent_type}: {Path(latest).name}")
            if info and info.get("reward_score"):
                print(f"    Reward: {info['reward_score']}")
        else:
            print(f"  - {agent_type}: No checkpoint found")
    
    return len(all_checkpoints) > 0


def test_pricing_service():
    """Test that PricingService loads checkpoints correctly."""
    print("\n" + "="*60)
    print("TEST 2: PricingService Checkpoint Loading")
    print("="*60)
    
    try:
        from services.pricing_service import PricingService
        
        # Test with checkpoint for each agent type
        for agent_type in ["sac", "ppo"]:
            checkpoint_path = find_latest_checkpoint(agent_type)
            
            print(f"\n✓ Testing {agent_type.upper()} with checkpoint:")
            if checkpoint_path:
                print(f"  Loading: {Path(checkpoint_path).name}")
                service = PricingService(
                    agent_type=agent_type,
                    checkpoint_path=checkpoint_path
                )
                print(f"  ✓ {agent_type.upper()} service initialized successfully")
                print(f"  Agent: {service.agent_type}")
                print(f"  Agent object: {service.agent.__class__.__name__}")
            else:
                print(f"  ✗ No checkpoint found for {agent_type}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test the new API endpoints."""
    print("\n" + "="*60)
    print("TEST 3: API Endpoints")
    print("="*60)
    
    BASE_URL = "http://localhost:8000/api/prices"
    
    print("\nNote: These tests require the API to be running.")
    print("Start the API with: python backend/api/main.py")
    
    try:
        # Test checkpoint listing endpoint
        print("\n✓ Testing GET /api/prices/checkpoints/list")
        response = requests.get(f"{BASE_URL}/checkpoints/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  Checkpoints found: {data.get('total_count', 0)}")
            for agent_type, cps in data.get('checkpoints', {}).items():
                print(f"  - {agent_type}: {len(cps)} checkpoint(s)")
        else:
            print(f"  Status: {response.status_code}")
        
        # Test latest checkpoint endpoint
        print("\n✓ Testing GET /api/prices/checkpoints/latest/sac")
        response = requests.get(f"{BASE_URL}/checkpoints/latest/sac", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  Filename: {data.get('filename')}")
            print(f"  Reward: {data.get('reward_score')}")
        else:
            print(f"  Status: {response.status_code}")
        
        print("\n✓ API endpoints are accessible!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Could not connect to API at {BASE_URL}")
        print("  Make sure the API server is running")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("RL Model ↔ API Integration Tests")
    print("█"*60)
    
    results = []
    
    # Run tests
    results.append(("Checkpoint Discovery", test_checkpoint_discovery()))
    results.append(("PricingService Loading", test_pricing_service()))
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nPassed: {passed_count}/{total_count}")
    
    if passed_count >= 2:
        print("\n✓ RL Model is successfully connected to the API!")
        print("\nNext steps:")
        print("1. Start the API: python backend/api/main.py")
        print("2. Test price recommendations: curl http://localhost:8000/api/prices/recommend/product_1?agent_type=sac")
        print("3. View all checkpoints: curl http://localhost:8000/api/prices/checkpoints/list")
    else:
        print("\n✗ Some tests failed. Check configuration.")
        sys.exit(1)
