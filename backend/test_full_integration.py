"""Test all 3 agents - find and test Matcha product."""
import requests

print("=" * 80)
print("TESTING AGENT ENDPOINTS (Agent Management)")
print("=" * 80)

base_url = "http://localhost:8000/api/agent"

# Test checkpoints endpoint
print("\n✓ GET /api/agent/checkpoints")
resp = requests.get(f"{base_url}/checkpoints")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Total checkpoints: {data.get('total')}")
    print(f"\n  Best checkpoints by agent:")
    for agent_type, best_info in data.get('best', {}).items():
        reward = best_info.get('reward_score')
        print(f"    {agent_type.upper()}: {best_info['filename']} (reward: {reward:.2f})")
else:
    print(f"  ERROR: {resp.status_code}")

# Test status endpoint
print("\n✓ GET /api/agent/status")
resp = requests.get(f"{base_url}/status")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Status: {data.get('status')}")
    print(f"  Default Agent: {data.get('default_agent')}")
    
    if data.get('evaluation'):
        eval_info = data['evaluation']
        print(f"\n  Evaluation Summary:")
        print(f"    Best Agent: {eval_info.get('best_agent').upper()}")
        print(f"    Best Reward: {eval_info.get('best_reward'):.2f}")
        for ranking in eval_info.get('rankings', []):
            rank = ranking['rank']
            agent = ranking['agent'].upper()
            reward = ranking['reward']
            print(f"      {rank}. {agent:6s} → {reward:.2f}")
else:
    print(f"  ERROR: {resp.status_code}")

# Test metrics endpoint
print("\n✓ GET /api/agent/metrics")
resp = requests.get(f"{base_url}/metrics")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Evaluation Report Generated: {data.get('timestamp')}")
    print(f"  Best Agent: {data.get('best_agent').upper()}")
    print(f"\n  Agent Comparison Metrics:")
    for agent, metrics in data.get('agent_comparison', {}).items():
        print(f"    {agent.upper()}:")
        print(f"      Mean Reward: {metrics.get('mean_reward'):.2f} ± {metrics.get('std_reward', 0):.2f}")
        print(f"      Checkpoints Trained: {metrics.get('num_checkpoints', '?')}")
else:
    print(f"  ERROR: {resp.status_code}")

# Test policy endpoint for SAC
print("\n✓ GET /api/agent/policy?agent_type=sac")
resp = requests.get(f"{base_url}/policy?agent_type=sac")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Agent: {data.get('agent_type').upper()}")
    print(f"  Algorithm: {data.get('learning_algorithm')}")
    print(f"  Training Mode: {data.get('training_mode')}")
    arch = data.get('architecture', {})
    print(f"  Architecture:")
    print(f"    State Dim: {arch.get('state_dim')}")
    print(f"    Action Dim: {arch.get('action_dim')}")
    print(f"    Network Type: {arch.get('network_type')}")
else:
    print(f"  ERROR: {resp.status_code}")

print("\n" + "=" * 80)
print("Now testing price recommendations with all agents...")
print("=" * 80)

# Test with PROD-001
product_id = "PROD-001"
base_url_prices = "http://localhost:8000/api/prices/recommend"

print(f"\nTesting with product: {product_id}")
results = []

for agent in ["sac", "ppo", "bandit"]:
    resp = requests.get(f"{base_url_prices}/{product_id}?agent_type={agent}")
    if resp.status_code == 200:
        data = resp.json()
        markup = ((data['recommended_price'] / data['current_price']) - 1) * 100
        
        results.append({
            'agent': agent.upper(),
            'recommended_price': data['recommended_price'],
            'current_price': data['current_price'],
            'confidence': data['confidence'],
            'markup_pct': markup
        })
        
        print(f"\n  {agent.upper()}:")
        print(f"    Current: ${data['current_price']:.2f} → Recommended: ${data['recommended_price']:.2f}")
        print(f"    Confidence: {data['confidence']:.0%}  |  Markup: {markup:+.1f}%")

if results:
    print("\n" + "-" * 80)
    sorted_results = sorted(results, key=lambda x: x['recommended_price'], reverse=True)
    print("\nPrice Ranking:")
    for i, r in enumerate(sorted_results, 1):
        print(f"  {i}. {r['agent']:6s} → ${r['recommended_price']:7.2f} ({r['markup_pct']:+.1f}%)")

print("\n" + "=" * 80)
