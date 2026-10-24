from functools import wraps

from flask import Blueprint, g, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.features.estoque.models import Usuario
from app.utils.errors import Conflito, RegistroNaoEncontrado
from app.utils.parsing import entrada
from db.database_config import db

from .schemas import LoginInput, UsuarioCreate, UsuarioUpdate

bp = Blueprint("auth", __name__)


def serializar(usuario: Usuario) -> dict:
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "username": usuario.username,
        "papel": usuario.papel,
        "ativo": usuario.ativo,
    }


def exigir_papeis(*papeis):
    def decorator(funcao):
        @wraps(funcao)
        def protegida(*args, **kwargs):
            if not getattr(g, "usuario", None):
                return {"erro": "autenticação necessária"}, 401
            if g.usuario.papel not in papeis:
                return {"erro": "você não tem permissão para esta ação"}, 403
            return funcao(*args, **kwargs)
        return protegida
    return decorator


@bp.post("/login")
def login():
    dados = entrada(LoginInput)
    usuario = db.session.execute(
        db.select(Usuario).where(db.func.lower(Usuario.username) == dados.username)
    ).scalar_one_or_none()
    if usuario is None or not usuario.ativo or not check_password_hash(usuario.senha_hash, dados.password):
        return {"erro": "usuário ou senha inválidos"}, 401
    session.clear()
    session["usuario_id"] = usuario.id
    session.permanent = True
    return serializar(usuario)


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/me")
def me():
    if not getattr(g, "usuario", None):
        return {"erro": "autenticação necessária"}, 401
    return serializar(g.usuario)


@bp.get("/usuarios")
@exigir_papeis("OWNER")
def listar_usuarios():
    usuarios = db.session.execute(db.select(Usuario).order_by(Usuario.nome)).scalars()
    return [serializar(usuario) for usuario in usuarios]


@bp.post("/usuarios")
@exigir_papeis("OWNER")
def criar_usuario():
    dados = entrada(UsuarioCreate)
    username = dados.username.lower()
    existente = db.session.execute(db.select(Usuario).where(db.func.lower(Usuario.username) == username)).scalar_one_or_none()
    if existente:
        raise Conflito("nome de usuário já cadastrado")
    usuario = Usuario(nome=dados.nome, username=username, senha_hash=generate_password_hash(dados.password), papel=dados.papel)
    db.session.add(usuario)
    db.session.commit()
    return serializar(usuario), 201


@bp.put("/usuarios/<int:usuario_id>")
@exigir_papeis("OWNER")
def atualizar_usuario(usuario_id: int):
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        raise RegistroNaoEncontrado("usuário não encontrado")
    dados = entrada(UsuarioUpdate)
    if dados.nome is not None:
        usuario.nome = dados.nome.strip()
    if dados.password is not None:
        usuario.senha_hash = generate_password_hash(dados.password)
    if dados.papel is not None:
        usuario.papel = dados.papel
    if dados.ativo is not None:
        if usuario.id == g.usuario.id and not dados.ativo:
            raise Conflito("a conta em uso não pode ser desativada")
        usuario.ativo = dados.ativo
    db.session.commit()
    return serializar(usuario)
