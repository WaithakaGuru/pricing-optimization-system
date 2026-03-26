#!/usr/bin/env python3
"""
Unified training orchestrator for all RL agents (PPO, SAC, Bandit).

Features:
- Trains all three models in sequence or parallel
- Manages checkpoints automatically
- Identifies and keeps only the best checkpoints
- Provides comprehensive training summary
- Cleans up weaker checkpoints to save disk space

Usage:
    python train_all_models.py --agents ppo sac bandit --episodes 500 --cleanup
    python train_all_models.py --agents ppo --episodes 1000 --no-cleanup
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import checkpoint manager
sys.path.insert(0, str(Path(__file__).parent))
from utils.checkpoint_manager import (
    list_checkpoints,
    find_best_checkpoint,
    cleanup_all_weaker_checkpoints,
    print_checkpoint_summary,
    register_checkpoint
)


class ModelTrainer:
    """Orchestrate training of all RL agents."""
    
    def __init__(self, episodes: int = 500, cleanup: bool = True, keep_top_n: int = 3):
        """
        Initialize trainer.
        
        Args:
            episodes: Number of training episodes per agent
            cleanup: Whether to cleanup weaker checkpoints
            keep_top_n: Number of best checkpoints to keep per agent
        """
        self.episodes = episodes
        self.cleanup = cleanup
        self.keep_top_n = keep_top_n
        self.results = {}
        self.training_log = []
        self.start_time = None
        
    def train_ppo(self) -> Tuple[bool, str]:
        """Train PPO agent."""
        logger.info("\n" + "="*80)
        logger.info("🎯 TRAINING PPO AGENT")
        logger.info("="*80)
        
        try:
            cmd = [
                "python", "train_agent.py",
                "--agent", "PPO",
                "--mode", "episodic",
                "--episodes", str(self.episodes)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PPO training failed:\n{result.stderr}")
                return False, result.stderr
            
            logger.info(result.stdout)
            
            # Extract best checkpoint info
            best_ckpt = find_best_checkpoint("ppo")
            if best_ckpt:
                logger.info(f"✅ PPO Training Complete! Best checkpoint: {Path(best_ckpt).name}")
                self.results["ppo"] = {"status": "success", "checkpoint": best_ckpt}
                return True, best_ckpt
            else:
                logger.warning("PPO training completed but no checkpoint found")
                self.results["ppo"] = {"status": "incomplete"}
                return False, "No checkpoint created"
                
        except Exception as e:
            logger.error(f"PPO training error: {e}")
            self.results["ppo"] = {"status": "error", "error": str(e)}
            return False, str(e)

    def train_sac(self) -> Tuple[bool, str]:
        """Train SAC agent."""
        logger.info("\n" + "="*80)
        logger.info("🎯 TRAINING SAC AGENT")
        logger.info("="*80)
        
        try:
            cmd = [
                "python", "train_agent.py",
                "--agent", "SAC",
                "--mode", "episodic",
                "--episodes", str(self.episodes)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"SAC training failed:\n{result.stderr}")
                return False, result.stderr
            
            logger.info(result.stdout)
            
            # Extract best checkpoint info
            best_ckpt = find_best_checkpoint("sac")
            if best_ckpt:
                logger.info(f"✅ SAC Training Complete! Best checkpoint: {Path(best_ckpt).name}")
                self.results["sac"] = {"status": "success", "checkpoint": best_ckpt}
                return True, best_ckpt
            else:
                logger.warning("SAC training completed but no checkpoint found")
                self.results["sac"] = {"status": "incomplete"}
                return False, "No checkpoint created"
                
        except Exception as e:
            logger.error(f"SAC training error: {e}")
            self.results["sac"] = {"status": "error", "error": str(e)}
            return False, str(e)

    def train_bandit(self) -> Tuple[bool, str]:
        """Train Contextual Bandit agent."""
        logger.info("\n" + "="*80)
        logger.info("🎯 TRAINING CONTEXTUAL BANDIT AGENT")
        logger.info("="*80)
        
        try:
            cmd = [
                "python", "train_bandit.py",
                "--episodes", str(min(self.episodes, 100)),  # Bandit trains faster
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Bandit training failed:\n{result.stderr}")
                return False, result.stderr
            
            logger.info(result.stdout)
            
            # Extract best checkpoint info
            best_ckpt = find_best_checkpoint("bandit")
            if best_ckpt:
                logger.info(f"✅ Bandit Training Complete! Best checkpoint: {Path(best_ckpt).name}")
                self.results["bandit"] = {"status": "success", "checkpoint": best_ckpt}
                return True, best_ckpt
            else:
                logger.warning("Bandit training completed but no checkpoint found")
                self.results["bandit"] = {"status": "incomplete"}
                return False, "No checkpoint created"
                
        except Exception as e:
            logger.error(f"Bandit training error: {e}")
            self.results["bandit"] = {"status": "error", "error": str(e)}
            return False, str(e)

    def train_all(self, agents: List[str]) -> None:
        """
        Train specified agents in sequence.
        
        Args:
            agents: List of agent types to train (ppo, sac, bandit)
        """
        self.start_time = datetime.now()
        logger.info("\n" + "🚀" * 40)
        logger.info("STARTING UNIFIED MODEL TRAINING ORCHESTRATOR")
        logger.info(f"Agents: {', '.join([a.upper() for a in agents])}")
        logger.info(f"Episodes per agent: {self.episodes}")
        logger.info(f"Cleanup weaker checkpoints: {self.cleanup}")
        logger.info("🚀" * 40)
        
        # Train each agent
        agent_map = {
            "ppo": self.train_ppo,
            "sac": self.train_sac,
            "bandit": self.train_bandit
        }
        
        for agent in agents:
            agent_lower = agent.lower()
            if agent_lower in agent_map:
                success, message = agent_map[agent_lower]()
                self.training_log.append({
                    "agent": agent_lower,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning(f"Unknown agent type: {agent}")
        
        # Cleanup weaker checkpoints
        if self.cleanup:
            logger.info("\n" + "🧹" * 40)
            cleanup_results = cleanup_all_weaker_checkpoints(self.keep_top_n)
            for agent_type, (deleted, remaining) in cleanup_results.items():
                logger.info(f"  {agent_type.upper()}: Deleted {deleted} weaker checkpoints, keeping {remaining}")
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self) -> None:
        """Print training summary."""
        elapsed = datetime.now() - self.start_time
        
        logger.info("\n" + "📊" * 40)
        logger.info("TRAINING COMPLETE - FINAL SUMMARY")
        logger.info("📊" * 40)
        
        # Show all checkpoints
        print_checkpoint_summary()
        
        # Show training results
        logger.info("\n📈 TRAINING RESULTS:")
        logger.info("-" * 80)
        
        for agent_type in ["ppo", "sac", "bandit"]:
            if agent_type in self.results:
                result = self.results[agent_type]
                status_icon = "✅" if result.get("status") == "success" else "❌"
                
                if result.get("status") == "success":
                    logger.info(f"  {status_icon} {agent_type.upper():10s} - SUCCESS")
                    logger.info(f"     Checkpoint: {Path(result['checkpoint']).name}")
                elif result.get("status") == "incomplete":
                    logger.info(f"  {status_icon} {agent_type.upper():10s} - INCOMPLETE (No checkpoint)")
                else:
                    logger.info(f"  {status_icon} {agent_type.upper():10s} - ERROR")
                    if "error" in result:
                        logger.info(f"     Error: {result['error']}")
        
        logger.info("-" * 80)
        logger.info(f"\n⏱️  Total training time: {elapsed}")
        logger.info("\n" + "🎉" * 40)
        logger.info("Next steps:")
        logger.info("  1. Evaluate models: python eval_agent.py --agent_type ppo")
        logger.info("  2. Test API endpoints: python test_api_endpoints.py")
        logger.info("  3. Deploy best model to production")
        logger.info("🎉" * 40 + "\n")
        
        # Save training log
        self._save_training_log()
    
    def _save_training_log(self) -> None:
        """Save training log to file."""
        try:
            log_file = Path(__file__).parent / "training_orchestrator.log"
            with open(log_file, 'w') as f:
                json.dump(self.training_log, f, indent=2)
            logger.info(f"Training log saved to: {log_file}")
        except Exception as e:
            logger.error(f"Failed to save training log: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified training orchestrator for RL agents (PPO, SAC, Bandit)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train all three models with 500 episodes each
  python train_all_models.py --agents ppo sac bandit --episodes 500

  # Train only PPO with 1000 episodes, no cleanup
  python train_all_models.py --agents ppo --episodes 1000 --no-cleanup

  # Train SAC and Bandit, keep top 5 checkpoints per agent
  python train_all_models.py --agents sac bandit --keep-top 5
        """
    )
    
    parser.add_argument(
        '--agents',
        nargs='+',
        choices=['ppo', 'sac', 'bandit'],
        default=['ppo', 'sac', 'bandit'],
        help='Which agents to train (default: all three)'
    )
    parser.add_argument(
        '--episodes',
        type=int,
        default=500,
        help='Number of training episodes per agent (default: 500)'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        default=True,
        help='Clean up weaker checkpoints after training (default: True)'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do NOT clean up weaker checkpoints'
    )
    parser.add_argument(
        '--keep-top',
        type=int,
        default=3,
        help='Number of best checkpoints to keep per agent (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Handle cleanup flag
    cleanup = args.cleanup and not args.no_cleanup
    
    # Create trainer and run
    trainer = ModelTrainer(
        episodes=args.episodes,
        cleanup=cleanup,
        keep_top_n=args.keep_top
    )
    
    trainer.train_all(args.agents)


if __name__ == "__main__":
    main()
