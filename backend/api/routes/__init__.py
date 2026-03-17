from .prices import router as prices_router
from .inventory import router as inventory_router
from .pos import router as pos_router
from .agent import router as agent_router

__all__ = ['prices_router', 'inventory_router', 'pos_router', 'agent_router']
