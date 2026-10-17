"""Executar no repositório completo: pytest -q tests/test_estoque.py"""
def test_estoque_com_seeds(app):
    with app.app_context():
        r = app.test_cli_runner().invoke(args=['init-db', '--seed'])
        assert r.exit_code == 0, r.output
    c = app.test_client()
    loc = c.get('/api/estoque/localizacoes')
    assert loc.status_code == 200 and len(loc.json) >= 1
    novo = c.post('/api/estoque/lotes', json={'produto_id':1,'localizacao_id':1})
    assert novo.status_code == 201, novo.json
    lote = novo.json['id']
    entrada = c.post('/api/estoque/movimentacoes',json={'tipo':'ENTRADA','lote_id':lote,'usuario_id':1,'quantidade':10})
    assert entrada.status_code == 201, entrada.json
    assert c.get(f'/api/estoque/lotes/{lote}').json['quantidade'] == 10
    assert c.post('/api/estoque/movimentacoes',json={'tipo':'SAIDA','lote_id':lote,'usuario_id':1,'quantidade':11,'motivo':'consumo'}).status_code == 400
    assert c.post('/api/estoque/movimentacoes',json={'tipo':'SAIDA','lote_id':lote,'usuario_id':1,'quantidade':4,'motivo':'consumo'}).status_code == 201
    assert c.get(f'/api/estoque/lotes/{lote}').json['quantidade'] == 6
    assert c.get('/api/estoque/sugestao-saida/1?quantidade=5').json['quantidade_faltante'] == 0


def test_transformacao_e_transferencia(app):
    with app.app_context():
        r=app.test_cli_runner().invoke(args=['init-db','--seed'])
        assert r.exit_code==0, r.output
    c=app.test_client()
    def lote(produto,local,validade):
        r=c.post('/api/estoque/lotes',json={'produto_id':produto,'localizacao_id':local,'data_validade':validade})
        assert r.status_code==201,r.json
        return r.json['id']
    origem=lote(5,2,'2099-01-01')
    destino=lote(6,2,'2099-01-01')
    assert c.post('/api/estoque/movimentacoes',json={'tipo':'ENTRADA','lote_id':origem,'usuario_id':1,'quantidade':10}).status_code==201
    r=c.post('/api/estoque/movimentacoes',json={'tipo':'TRANSFORMACAO','lote_id':origem,'lote_destino_id':destino,'usuario_id':1,'quantidade':10,'quantidade_destino':9})
    assert r.status_code==201,r.json
    assert c.get(f'/api/estoque/lotes/{origem}').json['quantidade']==0
    assert c.get(f'/api/estoque/lotes/{destino}').json['quantidade']==9


def test_validacoes(client):
    assert client.post('/api/estoque/lotes',json={}).status_code==400
    assert client.post('/api/estoque/movimentacoes',json={'tipo':'ENTRADA','quantidade':-1}).status_code==400
    assert client.post('/api/estoque/localizacoes',json={'nome':'Novo','tipo':'INVALIDO'}).status_code==400


def test_localizacao_nao_pode_invalidar_lote(app):
    with app.app_context():
        r=app.test_cli_runner().invoke(args=['init-db','--seed'])
        assert r.exit_code==0,r.output
    c=app.test_client()
    lote=c.post('/api/estoque/lotes',json={'produto_id':1,'localizacao_id':1})
    assert lote.status_code==201,lote.json
    alteracao=c.put('/api/estoque/localizacoes/1',json={'tipo':'CONGELADO'})
    assert alteracao.status_code==400,alteracao.json
    assert next(l for l in c.get('/api/estoque/localizacoes').json if l['id']==1)['tipo']=='SECO'

def test_dados_invalidos_e_rollback(app):
    with app.app_context():
        r=app.test_cli_runner().invoke(args=['init-db','--seed'])
        assert r.exit_code==0,r.output
    c=app.test_client()
    lote=c.post('/api/estoque/lotes',json={'produto_id':1,'localizacao_id':1})
    assert lote.status_code==201,lote.json
    id_=lote.json['id']
    base={'tipo':'ENTRADA','lote_id':id_,'usuario_id':1,'quantidade':5}
    assert c.post('/api/estoque/movimentacoes',json={**base,'quantidade':'nan'}).status_code==400
    assert c.post('/api/estoque/movimentacoes',json={**base,'quantidade':'inf'}).status_code==400
    assert c.post('/api/estoque/movimentacoes',json=base).status_code==201
    saida={'tipo':'SAIDA','lote_id':id_,'usuario_id':1,'quantidade':5.0000000001,'motivo':'uso'}
    assert c.post('/api/estoque/movimentacoes',json=saida).status_code==400
    assert c.get(f'/api/estoque/lotes/{id_}').json['quantidade']==5
    assert c.post('/api/estoque/movimentacoes',json={**base,'quantidade':1,'usuario_id':999}).status_code==400
    assert c.get(f'/api/estoque/lotes/{id_}').json['quantidade']==5
