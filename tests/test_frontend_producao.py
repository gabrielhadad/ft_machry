from pathlib import Path


def test_frontend_producao_consume_contratos_da_fase_88():
    source = Path("frontend/src/production.tsx").read_text(encoding="utf-8")
    assert "/api/producao/solicitacoes" in source
    assert "/execucao" in source
    assert "localizacao_destino_id" in source
    assert "quantidade_planejada" in source
    assert "quantidade_produzida" in source
    assert "sp_componente_id" in source
    assert "tempo_realizado_min" in source
    assert "perdas" in source


def test_app_carrega_responsaveis_e_localizacoes_para_producao():
    source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "/api/auth/responsaveis" in source
    assert "/api/estoque/localizacoes" in source
    assert "responsaveis={responsaveis}" in source
    assert "localizacoes={localizacoes}" in source
