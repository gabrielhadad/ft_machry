"""Verifica se o contrato OpenAPI acompanha a implementação das praças."""

from pathlib import Path

import yaml


DOCUMENTO = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"


def _documento():
    with DOCUMENTO.open(encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def test_openapi_documenta_rotas_e_metodos_de_pracas(app):
    especificacao = _documento()
    rotas = especificacao["paths"]
    esperados = {
        "/api/pracas": {"get", "post"},
        "/api/pracas/cozinheiros": {"get"},
        "/api/pracas/{id}": {"get", "put", "delete"},
        "/api/producao/solicitacoes/{id}/praca": {"put"},
    }
    metodos = {"get", "post", "put", "patch", "delete"}
    for caminho, acoes in esperados.items():
        assert acoes == (rotas[caminho].keys() & metodos)
        for acao in acoes:
            url = caminho.replace("{id}", "<int:praca_id>" if caminho.startswith("/api/pracas/") else "<int:sp_id>")
            assert any(
                regra.rule == url and acao.upper() in regra.methods
                for regra in app.url_map.iter_rules()
            ), f"Rota não registrada: {acao.upper()} {caminho}"


def test_openapi_documenta_campos_de_producao_e_permissoes():
    spec = _documento()
    schemas = spec["components"]["schemas"]
    assert {"praca_id", "praca"} <= schemas["SolicitacaoProducao"]["properties"].keys()
    assert "cozinheiros" in schemas["Praca"]["properties"]
    assert schemas["PracaCriar"]["required"] == ["nome", "cozinheiros"]
    assert schemas["PracaCriar"]["properties"]["cozinheiros"]["minItems"] == 1
    assert "praca_id" in spec["paths"]["/api/producao/solicitacoes"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]
    filtro = spec["paths"]["/api/producao/solicitacoes"]["get"]["parameters"]
    assert any(item.get("name") == "praca_id" for item in filtro)
    realocacao = spec["paths"]["/api/producao/solicitacoes/{id}/praca"]["put"]
    corpo = realocacao["requestBody"]["content"]["application/json"]["schema"]
    assert corpo["required"] == ["praca_id"]
    assert corpo["properties"]["praca_id"]["nullable"] is True
    assert "producao:criar" in realocacao["summary"]


def test_openapi_referencias_internas_resolvidas():
    spec = _documento()

    def verificar(entrada):
        if isinstance(entrada, dict):
            for nome, valor in entrada.items():
                if nome == "$ref" and isinstance(valor, str) and valor.startswith("#/"):
                    atual = spec
                    for parte in valor[2:].split("/"):
                        atual = atual[parte.replace("~1", "/").replace("~0", "~")]
                else:
                    verificar(valor)
        elif isinstance(entrada, list):
            for valor in entrada:
                verificar(valor)

    verificar(spec)
