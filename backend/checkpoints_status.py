#!/usr/bin/env python3
"""
Checkpoint Status Checker - View and manage trained model checkpoints.

Features:
- Display all available checkpoints
- Show best checkpoint for each agent
- Compare model performance
- Cleanup weaker checkpoints
- Generate checkpoint report

Usage:
    python checkpoints_status.py                  # Show all checkpoints
    python checkpoints_status.py --cleanup        # Cleanup weaker checkpoints
    python checkpoints_status.py --best           # Show only best per agent
    python checkpoints_status.py --cleanup --keep-top 5
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from utils.checkpoint_manager import (
    list_checkpoints,
    find_best_checkpoint,
    cleanup_all_weaker_checkpoints,
    print_checkpoint_summary,
    get_checkpoint_info,
    CHECKPOINTS_DIR
)
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


class CheckpointStatusChecker:
    """Check and manage checkpoint status."""
    
    def __init__(self):
        self.checkpoints = list_checkpoints()
    
    def show_all(self) -> None:
        """Show all checkpoints with details."""
        print_checkpoint_summary()
    
    def show_best_only(self) -> None:
        """Show only the best checkpoint for each agent."""
        print("\n🌟 BEST CHECKPOINTS BY AGENT:")
        print("=" * 80)
        
        best_models = {}
        for agent_type in ["ppo", "sac", "bandit"]:
            best_ckpt = find_best_checkpoint(agent_type)
            if best_ckpt:
                info = get_checkpoint_info(best_ckpt)
                best_models[agent_type] = {
                    "checkpoint": Path(best_ckpt).name,
                    "reward": info.get("reward_score"),
                    "path": best_ckpt
                }
                print(f"\n{agent_type.upper()}:")
                print(f"  Checkpoint: {Path(best_ckpt).name}")
                print(f"  Reward:     {info.get('reward_score', 'N/A'):.3f}")
                print(f"  Size:       {Path(best_ckpt).stat().st_size / (1024*1024):.2f} MB")
            else:
                print(f"\n{agent_type.upper()}:")
                print(f"  ❌ No checkpoints found")
        
        print("=" * 80)
        
        # Determine overall winner
        if best_models:
            winner = max(best_models, key=lambda x: best_models[x]["reward"])
            print(f"\n🏆 BEST OVERALL: {winner.upper()} ({best_models[winner]['reward']:.3f})")
    
    def show_comparison(self) -> None:
        """Show side-by-side comparison of all agents' best checkpoints."""
        print("\n📊 MODEL PERFORMANCE COMPARISON:")
        print("=" * 80)
        
        comparisons = []
        
        for agent_type in ["ppo", "sac", "bandit"]:
            best_ckpt = find_best_checkpoint(agent_type)
            if best_ckpt:
                info = get_checkpoint_info(best_ckpt)
                comparisons.append({
                    "agent": agent_type.upper(),
                    "reward": info.get("reward_score", 0),
                    "checkpoint": Path(best_ckpt).name,
                    "size_mb": Path(best_ckpt).stat().st_size / (1024*1024)
                })
        
        # Sort by reward
        comparisons.sort(key=lambda x: x["reward"], reverse=True)
        
        # Print header
        print(f"{'Rank':<6} {'Agent':<10} {'Reward':<12} {'Checkpoint':<45} {'Size':<10}")
        print("-" * 80)
        
        # Print rows
        for idx, comp in enumerate(comparisons, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else " "
            print(f"{medal} {idx:<4} {comp['agent']:<10} {comp['reward']:<12.3f} {comp['checkpoint']:<45} {comp['size_mb']:.2f}MB")
        
        print("=" * 80)
        
        if comparisons:
            winner = comparisons[0]
            print(f"\n🏆 RECOMMENDED FOR PRODUCTION: {winner['agent']} ({winner['reward']:.3f})")
    
    def show_statistics(self) -> None:
        """Show checkpoint statistics."""
        print("\n📈 CHECKPOINT STATISTICS:")
        print("=" * 80)
        
        total_checkpoints = sum(len(ckpts) for ckpts in self.checkpoints.values())
        total_size = sum(
            Path(ckpt["path"]).stat().st_size 
            for ckpts in self.checkpoints.values() 
            for ckpt in ckpts
        ) / (1024 * 1024)
        
        print(f"Total checkpoints:  {total_checkpoints}")
        print(f"Total disk usage:   {total_size:.2f} MB")
        print()
        
        for agent_type in sorted(self.checkpoints.keys()):
            ckpts = self.checkpoints[agent_type]
            agent_size = sum(
                Path(cp["path"]).stat().st_size for cp in ckpts
            ) / (1024 * 1024)
            
            if ckpts:
                rewards = [cp["reward_score"] for cp in ckpts if cp["reward_score"] is not None]
                avg_reward = sum(rewards) / len(rewards) if rewards else 0
                max_reward = max(rewards) if rewards else 0
                min_reward = min(rewards) if rewards else 0
                
                print(f"{agent_type.upper()}:")
                print(f"  Checkpoints:  {len(ckpts)}")
                print(f"  Disk usage:   {agent_size:.2f} MB")
                print(f"  Best reward:  {max_reward:.3f}")
                print(f"  Avg reward:   {avg_reward:.3f}")
                print(f"  Worst reward: {min_reward:.3f}")
        
        print("=" * 80)
    
    def cleanup(self, keep_top_n: int = 3) -> None:
        """Cleanup weaker checkpoints."""
        print(f"\n🧹 CLEANING UP CHECKPOINTS (keeping top {keep_top_n} per agent)...")
        print("=" * 80)
        
        results = cleanup_all_weaker_checkpoints(keep_top_n)
        
        total_deleted = 0
        total_remaining = 0
        
        for agent_type, (deleted, remaining) in results.items():
            total_deleted += deleted
            total_remaining += remaining
            status = "✅" if remaining > 0 else "⚠️"
            print(f"{status} {agent_type.upper():10s}: Deleted {deleted:2d}, Kept {remaining:2d}")
        
        print("=" * 80)
        print(f"\n📊 Summary: Deleted {total_deleted} checkpoints, Keeping {total_remaining}")
    
    def generate_report(self, output_file: str = None) -> None:
        """Generate a JSON report of all checkpoints."""
        report = {
            "timestamp": Path(CHECKPOINTS_DIR / "checkpoint_metadata.json").stat().st_mtime if CHECKPOINTS_DIR.exists() else None,
            "total_checkpoints": sum(len(ckpts) for ckpts in self.checkpoints.values()),
            "agents": {}
        }
        
        for agent_type in sorted(self.checkpoints.keys()):
            ckpts = self.checkpoints[agent_type]
            report["agents"][agent_type] = {
                "count": len(ckpts),
                "best": ckpts[0] if ckpts else None,
                "checkpoints": [
                    {
                        "filename": cp["filename"],
                        "reward": cp["reward_score"],
                        "size_mb": cp.get("size_mb", 0)
                    }
                    for cp in ckpts
                ]
            }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: {output_file}")
        else:
            print("\n📄 CHECKPOINT REPORT:")
            print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Checkpoint status checker and manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all checkpoints
  python checkpoints_status.py

  # Show only best checkpoint per agent
  python checkpoints_status.py --best

  # Compare model performance
  python checkpoints_status.py --compare

  # Show statistics
  python checkpoints_status.py --stats

  # Cleanup weaker checkpoints
  python checkpoints_status.py --cleanup

  # Keep only top 5 checkpoints per agent
  python checkpoints_status.py --cleanup --keep-top 5

  # Generate report
  python checkpoints_status.py --report checkpoints.json
        """
    )
    
    parser.add_argument(
        '--best',
        action='store_true',
        help='Show only best checkpoint per agent'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Show side-by-side comparison of best models'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show checkpoint statistics'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Cleanup weaker checkpoints'
    )
    parser.add_argument(
        '--keep-top',
        type=int,
        default=3,
        help='Number of best checkpoints to keep (default: 3)'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Generate JSON report to specified file'
    )
    
    args = parser.parse_args()
    
    checker = CheckpointStatusChecker()
    
    # If no specific option, show all
    if not any([args.best, args.compare, args.stats, args.cleanup, args.report]):
        checker.show_all()
    else:
        if args.best:
            checker.show_best_only()
        if args.compare:
            checker.show_comparison()
        if args.stats:
            checker.show_statistics()
        if args.cleanup:
            checker.cleanup(args.keep_top)
        if args.report:
            checker.generate_report(args.report)


if __name__ == "__main__":
    main()
