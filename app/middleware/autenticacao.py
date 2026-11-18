from flask import Flask, g, request, session

from app.features.acessos.repository import AcessoRepository
from app.features.usuarios.models import Usuario
from app.utils.constantes import Constantes
from app.utils.permissoes import permissao_exigida
from db.database_config import db


def _carregar_usuario() -> None:
    usuario_id = session.get("usuario_id")
    g.usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
    if g.usuario is not None and not g.usuario.ativo:
        session.clear()
        g.usuario = None


def _rota_publica(caminho: str) -> bool:
    return caminho in Constantes.ROTAS_PUBLICAS or caminho.startswith(Constantes.PREFIXOS_PUBLICOS)


def registrar_middleware_autenticacao(app: Flask) -> None:
    @app.before_request
    def autenticar_e_autorizar():
        _carregar_usuario()
        if not request.path.startswith("/api/") or _rota_publica(request.path):
            return None
        if g.usuario is None:
            return {"erro": "autenticação necessária"}, 401
        if request.path in Constantes.ROTAS_DE_SESSAO or request.endpoint is None:
            return None
        permissao = permissao_exigida(app.view_functions[request.endpoint])
        if permissao is None:
            return {"erro": "rota sem permissão configurada"}, 403
        g.permissoes = AcessoRepository().listar_codigos_do_usuario(g.usuario.id)
        if permissao not in g.permissoes:
            return {"erro": "você não tem permissão para esta ação"}, 403
        return None
