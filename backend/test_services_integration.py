"""Test services with real data integration."""
import asyncio
import logging
from services.weather_service import WeatherService
from services.inventory_service import InventoryService
from services.pricing_service import PricingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_weather_service():
    """Test real weather data fetching."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing WeatherService (Real API)")
    logger.info("=" * 60)
    
    weather = WeatherService(latitude=40.7128, longitude=-74.0060)  # NYC
    
    try:
        # Get current weather
        current = await weather.get_current_weather()
        if current:
            logger.info(f"✓ Current weather: {current['temperature']}°C")
            logger.info(f"  Type: {weather.interpret_weather_code(current['weather_code'])}")
            logger.info(f"  Humidity: {current['humidity']}%")
            logger.info(f"  Precipitation: {current['precipitation']}mm")
        
        # Get forecast
        forecast = await weather.get_weather_forecast(days=3)
        if forecast:
            logger.info(f"✓ Forecast (3 days):")
            for day in forecast:
                logger.info(f"  {day['date']}: {day['temp_max']}°C max, {day['temp_min']}°C min")
        
        # Get normalized for state
        state_weather = await weather.get_weather_for_state()
        logger.info(f"✓ Weather for state space:")
        logger.info(f"  Temperature (norm): {state_weather['temperature']:.2f}")
        logger.info(f"  Humidity (norm): {state_weather['humidity']:.2f}")
        logger.info(f"  Weather type: {state_weather['weather_type']}")
        
    finally:
        await weather.close()


def test_inventory_service():
    """Test real inventory queries."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing InventoryService (Real DB)")
    logger.info("=" * 60)
    
    inventory = InventoryService()
    
    # Get inventory
    inv = inventory.get_inventory("PROD-001")
    if inv:
        logger.info(f"✓ Product PROD-001 inventory:")
        logger.info(f"  Current stock: {inv['current_stock']}")
        logger.info(f"  Reorder point: {inv['reorder_point']}")
        logger.info(f"  Status: {inv['status']}")
    
    # Get turnover
    turnover = inventory.get_turnover_rate("PROD-001", days=30)
    logger.info(f"✓ Turnover rate (30d): {turnover:.4f} units/day")
    
    # Check reorder alerts
    alerts = inventory.check_reorder_alerts()
    logger.info(f"✓ Reorder alerts: {len(alerts)} items need restocking")
    
    # Get metrics
    metrics = inventory.get_inventory_metrics()
    logger.info(f"✓ Inventory metrics:")
    logger.info(f"  Total items: {metrics.get('total_items')}")
    logger.info(f"  Total units: {metrics.get('total_units'):,}")
    logger.info(f"  Low stock count: {metrics.get('items_low_stock')}")
    logger.info(f"  Health score: {metrics.get('health_score', 0):.2f}")
    
    # Get for state
    state_inv = inventory.get_inventory_for_state("PROD-001")
    logger.info(f"✓ Inventory for state space:")
    logger.info(f"  Level (norm): {state_inv['inventory_level']:.2f}")
    logger.info(f"  Turnover: {state_inv['turnover_rate']:.4f}")


def test_pricing_service():
    """Test agent recommendation integration."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing PricingService (Agent Integration)")
    logger.info("=" * 60)
    
    # Test each agent type
    for agent_type in ["bandit", "ppo", "sac"]:
        logger.info(f"\n--- Testing {agent_type.upper()} Agent ---")
        
        try:
            pricing = PricingService(agent_type=agent_type)
            
            # Get recommendation
            rec = pricing.get_recommendation("PROD-001")
            if rec:
                logger.info(f"✓ {agent_type} recommendation:")
                logger.info(f"  Current price: ${rec['current_price']:.2f}")
                logger.info(f"  Recommended: ${rec['recommended_price']:.2f}")
                logger.info(f"  Confidence: {rec['confidence']:.2f}")
                logger.info(f"  Key factor: Inventory = {rec['factors']['inventory_level']:.0f} units")
            else:
                logger.warning(f"✗ Failed to get recommendation")
                
        except Exception as e:
            logger.warning(f"✗ {agent_type} test failed: {e}")


async def main():
    """Run all service tests."""
    logger.info("\n")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║ Service Integration Tests - Real Data                   ║")
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")
    
    # Test weather (async)
    try:
        await test_weather_service()
    except Exception as e:
        logger.error(f"Weather service test failed: {e}", exc_info=True)
    
    # Test inventory (sync)
    try:
        test_inventory_service()
    except Exception as e:
        logger.error(f"Inventory service test failed: {e}", exc_info=True)
    
    # Test pricing (sync)
    try:
        test_pricing_service()
    except Exception as e:
        logger.error(f"Pricing service test failed: {e}", exc_info=True)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Service Integration Tests Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. View database: python backend/view_db.py")
    logger.info("2. Create API endpoints using these services")
    logger.info("3. Connect frontend to pricing recommendations")


if __name__ == "__main__":
    asyncio.run(main())
