"""Training script for demand forecasting model."""
import logging

logger = logging.getLogger(__name__)


def train_demand_forecaster(data_path: str, output_path: str):
    """
    Train and save demand forecasting model.
    
    Args:
        data_path: Path to historical sales data
        output_path: Where to save trained model
    """
    # TODO: Load historical data
    # TODO: Fit Prophet model
    # TODO: Evaluate (cross-validation)
    # TODO: Save to output_path
    pass


if __name__ == "__main__":
    train_demand_forecaster("data/raw/sales_history.csv", "models/prophet/model.pkl")
