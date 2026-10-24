from app.utils.errors import registrar_tratadores_erro

from ..usuarios import routes 
from .routes import bp

registrar_tratadores_erro(bp)
