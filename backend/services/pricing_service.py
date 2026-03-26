"""Pricing service - real agent integration for price recommendations."""
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session

from models import PriceHistory, Product, Transaction
from rl.environment.state_builder import StateBuilder
from rl.agents.ppo_agent import PPOAgent
from rl.agents.sac_agent import SACAgent
from rl.agents.bandit import ContextualBandit

logger = logging.getLogger(__name__)


class PricingService:
    """
    Service for price recommendations using RL agents.
    
    Workflow:
    1. Build state from current conditions (inventory, demand, weather)
    2. Query trained agent for price recommendation
    3. Apply price with validation
    4. Record transaction for agent feedback
    5. Feed outcome back to agent
    """

    def __init__(
        self,
        db_url: str = "sqlite:///pricing.db",
        agent_type: str = "ppo",  # "ppo", "sac", "bandit"
        checkpoint_path: Optional[str] = None,
    ):
        """
        Initialize pricing service with RL agent.
        
        Args:
            db_url: Database connection string
            agent_type: Which agent to use
            checkpoint_path: Path to load trained agent from (optional)
        """
        self.engine = create_engine(db_url)
        self.agent_type = agent_type
        self.state_builder = StateBuilder(db_url=db_url)
        
        # Initialize agent
        self.agent = self._init_agent(agent_type, checkpoint_path)
        
        logger.info(f"PricingService initialized with {agent_type} agent")

    def _init_agent(self, agent_type: str, checkpoint_path: Optional[str]):
        """Initialize RL agent."""
        try:
            if agent_type == "ppo":
                agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=128)
                if checkpoint_path:
                    agent.load_checkpoint(checkpoint_path)
            elif agent_type == "sac":
                agent = SACAgent(state_dim=12, action_dim=1, hidden_dim=128)
                if checkpoint_path:
                    agent.load_checkpoint(checkpoint_path)
            elif agent_type == "bandit":
                agent = ContextualBandit(n_arms=30, algorithm="ucb")
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            logger.info(f"Agent {agent_type} initialized successfully")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return None

    def get_recommendation(self, product_id: str) -> Optional[Dict]:
        """
        Get price recommendation from RL agent.
        
        Args:
            product_id: Product identifier
            
        Returns:
            {
                "product_id": "PROD-001",
                "recommended_price": 19.99,
                "agent": "ppo",
                "confidence": 0.92,
                "factors": {
                    "current_price": 20.00,
                    "inventory_level": 150,
                    "demand_velocity": 0.8,
                    "seasonality": 0.6,
                },
                "timestamp": "2024-03-19T10:30:00Z"
            }
        """
        try:
            if not self.agent:
                logger.error("Agent not initialized")
                return None
            
            # Build state from current conditions
            state = self.state_builder.build_state(product_id)
            
            if state is None or not isinstance(state, np.ndarray):
                logger.warning(f"Could not build state for {product_id}")
                return None
            
            # Get agent recommendation
            if self.agent_type in ["ppo", "sac"]:
                # Use deterministic action (mean) for inference
                result = self.agent.select_action(state, deterministic=True)
                # PPO returns (action, log_prob, value), SAC returns (action, log_prob)
                action = result[0]
                confidence = 0.9  # High confidence for deterministic
            else:  # bandit
                arm = self.agent.select_arm(state, epsilon=0.0)  # Greedy
                action = self.agent.prices[arm]
                confidence = 0.7  # Lower confidence for multi-arm
            
            # Get current price for comparison
            with Session(self.engine) as session:
                product = session.query(Product).filter(
                    Product.id == product_id
                ).first()
                
                if not product:
                    logger.error(f"Product not found: {product_id}")
                    return None
                
                current_price = product.current_price
            
            # Build factors dict for explanation
            factors = self._extract_state_factors(product_id, state)
            
            # CRITICAL: Constrain recommended price to product's bounds
            # Agent may output values outside [min_price, max_price] due to global scaling
            recommended_price = np.clip(
                float(action),
                float(product.min_price),
                float(product.max_price)
            )
            
            logger.debug(
                f"Price recommendation: {product_id} - "
                f"Agent output: ${action:.2f}, "
                f"Constrained to: ${recommended_price:.2f} "
                f"(bounds: ${product.min_price:.2f} - ${product.max_price:.2f})"
            )
            
            return {
                "product_id": product_id,
                "recommended_price": float(recommended_price),
                "current_price": float(current_price),
                "agent": self.agent_type,
                "confidence": float(confidence),
                "factors": factors,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation: {e}", exc_info=True)
            return None

    def apply_price(
        self,
        product_id: str,
        new_price: float,
        applied_by: str = "agent"
    ) -> Optional[Dict]:
        """
        Apply a price change and record in database.
        
        Args:
            product_id: Product identifier
            new_price: New price to apply
            applied_by: "agent", "manager", "customer"
            
        Returns:
            {
                "product_id": "PROD-001",
                "old_price": 20.00,
                "new_price": 19.99,
                "applied_at": "2024-03-19T10:30:00Z",
                "applied_by": "agent"
            }
        """
        try:
            with Session(self.engine) as session:
                product = session.query(Product).filter(
                    Product.id == product_id
                ).first()
                
                if not product:
                    logger.error(f"Product not found: {product_id}")
                    return None
                
                old_price = product.current_price
                product.current_price = new_price
                
                # Record in price history
                price_record = PriceHistory(
                    product_id=product_id,
                    old_price=old_price,
                    new_price=new_price,
                    changed_by=applied_by,
                    change_date=datetime.now(),
                )
                session.add(price_record)
                session.commit()
                
                logger.info(f"Price applied: {product_id} {old_price} → {new_price}")
                
                return {
                    "product_id": product_id,
                    "old_price": float(old_price),
                    "new_price": float(new_price),
                    "applied_at": datetime.now().isoformat(),
                    "applied_by": applied_by,
                }
                
        except Exception as e:
            logger.error(f"Error applying price: {e}")
            return None

    def get_price_history(self, product_id: str, days: int = 30) -> List[Dict]:
        """
        Fetch historical price changes.
        
        Args:
            product_id: Product identifier
            days: Look-back period
            
        Returns:
            [
                {
                    "date": "2024-03-19",
                    "old_price": 20.00,
                    "new_price": 19.99,
                    "changed_by": "agent"
                },
                ...
            ]
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with Session(self.engine) as session:
                history = session.query(PriceHistory).filter(
                    and_(
                        PriceHistory.product_id == product_id,
                        PriceHistory.change_date >= cutoff_date,
                    )
                ).order_by(PriceHistory.change_date.desc()).all()
                
                return [
                    {
                        "date": h.change_date.isoformat(),
                        "old_price": float(h.old_price),
                        "new_price": float(h.new_price),
                        "changed_by": h.changed_by,
                    }
                    for h in history
                ]
                
        except Exception as e:
            logger.error(f"Error fetching price history: {e}")
            return []

    def record_transaction(
        self,
        product_id: str,
        quantity: int,
        price: float,
        revenue: float,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Record a transaction for agent feedback.
        
        This feeds real outcome back to the agent for learning.
        
        Args:
            product_id: Product sold
            quantity: Units sold
            price: Price per unit
            revenue: Total revenue
            transaction_id: Optional existing transaction ID (if already recorded)
            
        Returns:
            Transaction record
        """
        try:
            from uuid import uuid4
            
            # Use provided ID or generate new one
            if not transaction_id:
                transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"
            
            with Session(self.engine) as session:
                transaction = Transaction(
                    id=transaction_id,
                    product_id=product_id,
                    quantity=quantity,
                    price=price,
                    revenue=revenue,
                    total=revenue,
                    timestamp=datetime.now(),
                )
                session.add(transaction)
                session.commit()
                
                logger.info(f"Transaction recorded: {transaction_id} - {product_id} x{quantity} @ {price}")
                
                return {
                    "id": transaction_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": float(price),
                    "revenue": float(revenue),
                    "timestamp": datetime.now().isoformat(),
                }
                
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            return None

    def _extract_state_factors(self, product_id: str, state: np.ndarray) -> Dict:
        """
        Extract human-readable factors from state vector.
        
        State vector structure (from StateBuilder):
        [price, cost, margin, inventory, turnover_7d, velocity_30d, trend,
         seasonality, weather, competitor, anomaly, trend_signal]
        """
        if len(state) < 12:
            return {}
        
        return {
            "current_price": float(state[0] * 1000),  # Denormalized
            "cost_price": float(state[1] * 1000),
            "margin_pct": float(state[2] * 100),
            "inventory_level": float(state[3] * 500),  # Estimated
            "turnover_7d": float(state[4]),
            "velocity_30d": float(state[5]),
            "price_trend": float(state[6]),
            "seasonality": float(state[7]),
            "weather_factor": float(state[8]),
            "competitor_price": float(state[9] * 1000),
            "anomaly_score": float(state[10]),
        }
