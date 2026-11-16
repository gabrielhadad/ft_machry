from app.utils.errors import registrar_tratadores_erro

from .routes import grupos_bp, permissoes_bp

registrar_tratadores_erro(grupos_bp)
registrar_tratadores_erro(permissoes_bp)

__all__ = ["grupos_bp", "permissoes_bp"]
