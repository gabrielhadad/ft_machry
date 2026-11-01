from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, current_app, g, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.utils.errors import Conflito, RegistroNaoEncontrado
from app.utils.parsing import entrada
from db.database_config import db

from .models import Auditoria, Usuario
from .schemas import LoginInput, TrocaSenhaInput, UsuarioCreate, UsuarioUpdate
from .security import agora_iso, registrar_auditoria

bp = Blueprint("auth", __name__)


def serializar(usuario: Usuario) -> dict:
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "username": usuario.username,
        "papel": usuario.papel,
        "ativo": usuario.ativo,
        "deve_trocar_senha": usuario.deve_trocar_senha,
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


def _bloqueado(usuario: Usuario) -> bool:
    if not usuario.bloqueado_ate:
        return False
    try:
        bloqueado_ate = datetime.fromisoformat(usuario.bloqueado_ate)
    except ValueError:
        usuario.bloqueado_ate = None
        usuario.login_falhas = 0
        return False
    if bloqueado_ate.tzinfo is None:
        bloqueado_ate = bloqueado_ate.replace(tzinfo=timezone.utc)
    if bloqueado_ate <= datetime.now(timezone.utc):
        usuario.bloqueado_ate = None
        usuario.login_falhas = 0
        return False
    return True


@bp.post("/login")
def login():
    dados = entrada(LoginInput)
    usuario = db.session.execute(
        db.select(Usuario).where(db.func.lower(Usuario.username) == dados.username)
    ).scalar_one_or_none()

    if usuario is not None and _bloqueado(usuario):
        registrar_auditoria("LOGIN_BLOQUEADO", usuario=usuario, commit=True)
        return {"erro": "muitas tentativas; tente novamente mais tarde"}, 429

    valido = usuario is not None and usuario.ativo and check_password_hash(usuario.senha_hash, dados.password)
    if not valido:
        if usuario is not None:
            usuario.login_falhas = int(usuario.login_falhas or 0) + 1
            if usuario.login_falhas >= int(current_app.config["LOGIN_MAX_FAILURES"]):
                usuario.bloqueado_ate = (
                    datetime.now(timezone.utc)
                    + timedelta(minutes=int(current_app.config["LOGIN_LOCK_MINUTES"]))
                ).replace(microsecond=0).isoformat()
        registrar_auditoria("LOGIN_FALHA", usuario=usuario, username=dados.username)
        db.session.commit()
        status = 429 if usuario is not None and _bloqueado(usuario) else 401
        mensagem = "muitas tentativas; tente novamente mais tarde" if status == 429 else "usuário ou senha inválidos"
        return {"erro": mensagem}, status

    usuario.login_falhas = 0
    usuario.bloqueado_ate = None
    usuario.ultimo_login_em = agora_iso()
    session.clear()
    session["usuario_id"] = usuario.id
    session.permanent = True
    registrar_auditoria("LOGIN_SUCESSO", usuario=usuario)
    db.session.commit()
    return serializar(usuario)


@bp.post("/logout")
def logout():
    usuario = getattr(g, "usuario", None)
    if usuario is not None:
        registrar_auditoria("LOGOUT", usuario=usuario)
        db.session.commit()
    session.clear()
    return "", 204


@bp.get("/me")
def me():
    if not getattr(g, "usuario", None):
        return {"erro": "autenticação necessária"}, 401
    return serializar(g.usuario)


@bp.post("/change-password")
def trocar_senha():
    if not getattr(g, "usuario", None):
        return {"erro": "autenticação necessária"}, 401
    dados = entrada(TrocaSenhaInput)
    usuario = g.usuario
    if not check_password_hash(usuario.senha_hash, dados.current_password):
        registrar_auditoria("SENHA_TROCA_FALHA", usuario=usuario, commit=True)
        return {"erro": "senha atual inválida"}, 400
    if check_password_hash(usuario.senha_hash, dados.new_password):
        return {"erro": "a nova senha deve ser diferente da senha atual"}, 400
    usuario.senha_hash = generate_password_hash(dados.new_password)
    usuario.deve_trocar_senha = 0
    usuario.senha_alterada_em = agora_iso()
    registrar_auditoria("SENHA_ALTERADA", usuario=usuario)
    db.session.commit()
    return serializar(usuario)


@bp.get("/responsaveis")
@exigir_papeis("OWNER", "ADMIN")
def listar_responsaveis():
    usuarios = db.session.execute(
        db.select(Usuario).where(Usuario.ativo == 1).order_by(Usuario.nome)
    ).scalars()
    return [serializar(usuario) for usuario in usuarios]


@bp.get("/usuarios")
@exigir_papeis("OWNER")
def listar_usuarios():
    usuarios = db.session.execute(db.select(Usuario).order_by(Usuario.nome)).scalars()
    return [serializar(usuario) for usuario in usuarios]


@bp.get("/auditoria")
@exigir_papeis("OWNER")
def listar_auditoria():
    limite = min(max(request.args.get("limite", default=100, type=int) or 100, 1), 500)
    registros = db.session.execute(
        db.select(Auditoria).order_by(Auditoria.id.desc()).limit(limite)
    ).scalars()
    return [
        {
            "id": item.id, "evento": item.evento, "usuario_id": item.usuario_id,
            "username": item.username, "ip": item.ip, "metodo": item.metodo,
            "caminho": item.caminho, "detalhes": item.detalhes, "criado_em": item.criado_em,
        }
        for item in registros
    ]


@bp.post("/usuarios")
@exigir_papeis("OWNER")
def criar_usuario():
    dados = entrada(UsuarioCreate)
    username = dados.username.lower()
    existente = db.session.execute(
        db.select(Usuario).where(db.func.lower(Usuario.username) == username)
    ).scalar_one_or_none()
    if existente:
        raise Conflito("nome de usuário já cadastrado")
    usuario = Usuario(
        nome=dados.nome, username=username, senha_hash=generate_password_hash(dados.password),
        papel=dados.papel, deve_trocar_senha=1,
    )
    db.session.add(usuario)
    db.session.flush()
    registrar_auditoria("USUARIO_CRIADO", usuario=g.usuario, detalhes={"usuario_alvo_id": usuario.id, "papel": usuario.papel})
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
        if usuario.id == g.usuario.id:
            raise Conflito("use a troca de senha da própria conta")
        usuario.senha_hash = generate_password_hash(dados.password)
        usuario.deve_trocar_senha = 1
        usuario.senha_alterada_em = None
        usuario.login_falhas = 0
        usuario.bloqueado_ate = None
    if dados.papel is not None:
        usuario.papel = dados.papel
    if dados.ativo is not None:
        if usuario.id == g.usuario.id and not dados.ativo:
            raise Conflito("a conta em uso não pode ser desativada")
        usuario.ativo = dados.ativo
    registrar_auditoria("USUARIO_ATUALIZADO", usuario=g.usuario, detalhes={"usuario_alvo_id": usuario.id})
    db.session.commit()
    return serializar(usuario)
