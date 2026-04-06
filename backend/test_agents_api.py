"""Compare all 3 agents via API endpoint."""
import requests
import json

base_url = "http://localhost:8000/api/prices/recommend/p0001"

print("=" * 80)
print("TESTING ALL 3 AGENTS")
print("=" * 80)

results = []

for agent in ["sac", "ppo", "bandit"]:
    response = requests.get(f"{base_url}?agent_type={agent}")
    if response.status_code == 200:
        data = response.json()
        markup = ((data['recommended_price'] / data['current_price']) - 1) * 100
        
        results.append({
            'agent': agent.upper(),
            'recommended_price': data['recommended_price'],
            'current_price': data['current_price'],
            'confidence': data['confidence'],
            'markup_pct': markup
        })
        
        print(f"\n{agent.upper()} Agent:")
        print(f"  Recommended Price: ${data['recommended_price']:.2f}")
        print(f"  Current Price:     ${data['current_price']:.2f}")
        print(f"  Confidence:        {data['confidence']:.1%}")
        print(f"  Markup:            {markup:+.1f}%")
    else:
        print(f"\n{agent.upper()} Agent: ERROR - {response.status_code}")

# Summary comparison
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if results:
    # Sort by recommended price
    sorted_results = sorted(results, key=lambda x: x['recommended_price'], reverse=True)
    
    print(f"\nPrice Rankings (from highest to lowest):")
    for i, r in enumerate(sorted_results, 1):
        print(f"{i}. {r['agent']:6s} → ${r['recommended_price']:7.2f} ({r['markup_pct']:+.1f}%)")
    
    # Difference analysis
    prices = [r['recommended_price'] for r in results]
    max_price = max(prices)
    min_price = min(prices)
    diff_pct = ((max_price - min_price) / min_price) * 100
    
    print(f"\nPrice Range: ${min_price:.2f} - ${max_price:.2f} (variance: {diff_pct:.1f}%)")

print("\n" + "=" * 80)
