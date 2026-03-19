"""Test API endpoints end-to-end."""
import asyncio
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
logger_prefix = "✓" 

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_section(title):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_test(name, passed, details=""):
    """Print test result."""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} — {name}")
    if details and not passed:
        print(f"      {Colors.RED}{details}{Colors.RESET}")


def test_health():
    """Test health check endpoint."""
    print_section("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = response.status_code == 200
        print_test("Health check", passed)
        
        if passed:
            print(f"  {Colors.GREEN}API is running{Colors.RESET}")
        return passed
    except Exception as e:
        print_test("Health check", False, f"Connection failed: {e}")
        print(f"\n{Colors.RED}ERROR: API server is not running!{Colors.RESET}")
        print(f"Start it with: cd backend && python main.py\n")
        return False


def test_prices():
    """Test price endpoints."""
    print_section("2. Prices API")
    
    product_id = "PROD-001"
    all_passed = True
    
    # Test: Get current price
    try:
        response = requests.get(f"{BASE_URL}/api/prices/current/{product_id}", timeout=5)
        passed = response.status_code == 200
        print_test(f"Get current price", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Current price: ${data.get('current_price', 'N/A')}")
    except Exception as e:
        print_test("Get current price", False, str(e))
        all_passed = False
    
    # Test: Get recommendation (PPO)
    try:
        response = requests.get(
            f"{BASE_URL}/api/prices/recommend/{product_id}?agent_type=ppo",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get price recommendation (PPO)", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Recommended price: ${data.get('recommended_price', 'N/A')}")
            print(f"      Confidence: {data.get('confidence', 'N/A'):.2f}")
    except Exception as e:
        print_test("Get price recommendation (PPO)", False, str(e))
        all_passed = False
    
    # Test: Get price history
    try:
        response = requests.get(
            f"{BASE_URL}/api/prices/history/{product_id}?days=30",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get price history", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      History entries: {len(data)}")
    except Exception as e:
        print_test("Get price history", False, str(e))
        all_passed = False
    
    return all_passed


def test_inventory():
    """Test inventory endpoints."""
    print_section("3. Inventory API")
    
    product_id = "PROD-001"
    all_passed = True
    
    # Test: Get all inventory
    try:
        response = requests.get(f"{BASE_URL}/api/inventory/items", timeout=5)
        passed = response.status_code == 200
        print_test(f"List all inventory", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Total items: {len(data)}")
    except Exception as e:
        print_test("List all inventory", False, str(e))
        all_passed = False
    
    # Test: Get inventory for product
    try:
        response = requests.get(
            f"{BASE_URL}/api/inventory/items/{product_id}",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get inventory for product", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Current stock: {data.get('current_stock', 'N/A')}")
            print(f"      Status: {data.get('status', 'N/A')}")
    except Exception as e:
        print_test("Get inventory for product", False, str(e))
        all_passed = False
    
    # Test: Get reorder alerts
    try:
        response = requests.get(
            f"{BASE_URL}/api/inventory/alerts?urgency=all",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get reorder alerts", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Alerts: {len(data)}")
    except Exception as e:
        print_test("Get reorder alerts", False, str(e))
        all_passed = False
    
    # Test: Get inventory metrics
    try:
        response = requests.get(
            f"{BASE_URL}/api/inventory/metrics",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get inventory metrics", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Health score: {data.get('health_score', 'N/A'):.2f}")
            print(f"      Total units: {data.get('total_units', 'N/A'):,}")
    except Exception as e:
        print_test("Get inventory metrics", False, str(e))
        all_passed = False
    
    return all_passed


def test_transactions():
    """Test POS transaction endpoints."""
    print_section("4. POS Transactions API")
    
    all_passed = True
    
    # Test: Get POS stats
    try:
        response = requests.get(
            f"{BASE_URL}/api/pos/stats?days=30",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get POS statistics", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Total transactions: {data.get('total_transactions', 'N/A')}")
            print(f"      Total revenue: ${data.get('total_revenue', 'N/A'):.2f}")
    except Exception as e:
        print_test("Get POS statistics", False, str(e))
        all_passed = False
    
    # Test: Get recent transactions
    try:
        response = requests.get(
            f"{BASE_URL}/api/pos/transactions?limit=10&days=30",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get recent transactions", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Recent transactions: {len(data)}")
    except Exception as e:
        print_test("Get recent transactions", False, str(e))
        all_passed = False
    
    # Test: Record transaction
    try:
        transaction = {
            "items": [
                {
                    "product_id": "PROD-001",
                    "quantity": 1,
                    "price": 15.99,
                    "subtotal": 15.99
                }
            ],
            "total": 15.99,
            "payment_method": "cash",
            "notes": "API test transaction"
        }
        response = requests.post(
            f"{BASE_URL}/api/pos/transaction",
            json=transaction,
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Record POS transaction", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Transaction ID: {data.get('transaction_id', 'N/A')}")
            print(f"      Status: {data.get('status', 'N/A')}")
    except Exception as e:
        print_test("Record POS transaction", False, str(e))
        all_passed = False
    
    return all_passed


def test_metrics():
    """Test metrics and dashboard endpoints."""
    print_section("5. Metrics & Dashboard API")
    
    all_passed = True
    
    # Test: Get dashboard summary
    try:
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard?days=30",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get dashboard summary", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Total revenue: ${data.get('total_revenue', 'N/A'):.2f}")
            print(f"      Inventory health: {data.get('inventory_health', 'N/A'):.2f}")
            print(f"      Pricing confidence: {data.get('pricing_confidence', 'N/A'):.2f}")
    except Exception as e:
        print_test("Get dashboard summary", False, str(e))
        all_passed = False
    
    # Test: Get recommendation metrics
    try:
        response = requests.get(
            f"{BASE_URL}/api/metrics/recommendations?days=30",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get recommendation metrics", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Total recommendations: {data.get('total_recommendations', 'N/A')}")
            print(f"      Applied rate: {data.get('applied_rate', 'N/A'):.1f}%")
    except Exception as e:
        print_test("Get recommendation metrics", False, str(e))
        all_passed = False
    
    # Test: Get pricing opportunities
    try:
        response = requests.get(
            f"{BASE_URL}/api/metrics/opportunities?limit=5",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get pricing opportunities", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Opportunities found: {len(data)}")
            if data:
                first = data[0]
                print(f"      Top opportunity: {first.get('product_name')} "
                      f"(${first.get('current_price'):.2f} → ${first.get('recommended_price'):.2f})")
    except Exception as e:
        print_test("Get pricing opportunities", False, str(e))
        all_passed = False
    
    # Test: Get performance metrics
    try:
        response = requests.get(
            f"{BASE_URL}/api/metrics/performance",
            timeout=5
        )
        passed = response.status_code == 200
        print_test(f"Get performance metrics", passed)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json()
            print(f"      Uptime: {data.get('uptime_pct', 'N/A')}%")
            print(f"      Prediction accuracy: {data.get('accuracy', 'N/A'):.1f}%")
    except Exception as e:
        print_test("Get performance metrics", False, str(e))
        all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═" * 58 + "╗")
    print("║ API Endpoints Integration Test Suite                   ║")
    print("╚" + "═" * 58 + "╝")
    print(f"{Colors.RESET}\n")
    
    # Check if API is running
    if not test_health():
        return
    
    time.sleep(1)
    
    # Run all tests
    results = {
        "Prices": test_prices(),
        "Inventory": test_inventory(),
        "Transactions": test_transactions(),
        "Metrics": test_metrics(),
    }
    
    # Summary
    print_section("SUMMARY")
    
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    for name, passed in results.items():
        status = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
        print(f"{status} {name}")
    
    print(f"\n{Colors.BOLD}Total: {total_passed}/{total_tests} test groups passed{Colors.RESET}")
    
    if total_passed == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed! API is ready for frontend integration.{Colors.RESET}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed. Check errors above.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
