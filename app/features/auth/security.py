from __future__ import annotations

import json
from datetime import datetime, timezone

from flask import request

from db.database_config import db
from .models import Auditoria, Usuario


def agora_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def registrar_auditoria(
    evento: str,
    *,
    usuario: Usuario | None = None,
    username: str | None = None,
    detalhes: dict | str | None = None,
    commit: bool = False,
) -> Auditoria:
    registro = Auditoria(
        evento=evento,
        usuario_id=usuario.id if usuario is not None else None,
        username=(usuario.username if usuario is not None else username),
        ip=request.remote_addr if request else None,
        metodo=request.method if request else None,
        caminho=request.path if request else None,
        detalhes=(json.dumps(detalhes, ensure_ascii=False, sort_keys=True) if isinstance(detalhes, dict) else detalhes),
    )
    db.session.add(registro)
    if commit:
        db.session.commit()
    return registro
