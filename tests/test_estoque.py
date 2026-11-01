"""Executar no repositório completo: pytest -q tests/test_estoque.py"""
def test_estoque_com_seeds(seeded_client):
    c = seeded_client
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


def test_transformacao_e_transferencia(seeded_client):
    c = seeded_client
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


def test_localizacao_nao_pode_invalidar_lote(seeded_client):
    c = seeded_client
    lote=c.post('/api/estoque/lotes',json={'produto_id':1,'localizacao_id':1})
    assert lote.status_code==201,lote.json
    alteracao=c.put('/api/estoque/localizacoes/1',json={'tipo':'CONGELADO'})
    assert alteracao.status_code==400,alteracao.json
    assert next(l for l in c.get('/api/estoque/localizacoes').json if l['id']==1)['tipo']=='SECO'

def test_dados_invalidos_e_rollback(seeded_client):
    c = seeded_client
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
    spoof=c.post('/api/estoque/movimentacoes',json={**base,'quantidade':1,'usuario_id':999})
    assert spoof.status_code==201
    assert spoof.json['usuario_id']==1  # autoria vem da sessão; usuario_id do cliente é ignorado
    assert c.get(f'/api/estoque/lotes/{id_}').json['quantidade']==6


def test_inventario(seeded_client):
    c = seeded_client
    lote = c.post('/api/estoque/lotes', json={'produto_id': 1, 'localizacao_id': 1}).get_json()['id']
    c.post('/api/estoque/movimentacoes', json={'tipo': 'ENTRADA', 'lote_id': lote, 'usuario_id': 1, 'quantidade': 10})

    todos = c.get('/api/estoque/inventario')
    assert todos.status_code == 200
    item = next(i for i in todos.get_json() if i['lote_id'] == lote)
    assert item['produto_id'] == 1 and item['quantidade'] == 10 and item['localizacao'] == 'Estoque Seco'

    filtrado = c.get('/api/estoque/inventario?produto_id=1')
    assert filtrado.status_code == 200
    assert all(i['produto_id'] == 1 for i in filtrado.get_json())

    assert c.get('/api/estoque/inventario?produto_id=abc').status_code == 400


def test_movimentacoes_listagem_e_filtros(seeded_client):
    c = seeded_client
    lote = c.post('/api/estoque/lotes', json={'produto_id': 1, 'localizacao_id': 1}).get_json()['id']
    c.post('/api/estoque/movimentacoes', json={'tipo': 'ENTRADA', 'lote_id': lote, 'usuario_id': 1, 'quantidade': 10})
    c.post('/api/estoque/movimentacoes',
           json={'tipo': 'SAIDA', 'lote_id': lote, 'usuario_id': 1, 'quantidade': 3, 'motivo': 'uso'})

    todas = c.get('/api/estoque/movimentacoes')
    assert todas.status_code == 200
    assert [m['tipo'] for m in todas.get_json()] == ['SAIDA', 'ENTRADA']  # mais recente primeiro

    so_entrada = c.get('/api/estoque/movimentacoes?tipo=entrada')
    assert [m['tipo'] for m in so_entrada.get_json()] == ['ENTRADA']  # tipo é comparado em maiúsculas

    assert len(c.get(f'/api/estoque/movimentacoes?lote_id={lote}').get_json()) == 2
    assert c.get('/api/estoque/movimentacoes?limite=0').status_code == 400


def test_crud_localizacao(client):
    nova = client.post('/api/estoque/localizacoes', json={'nome': 'Depósito', 'tipo': 'SECO'})
    assert nova.status_code == 201
    loc = nova.get_json()
    assert loc['nome'] == 'Depósito' and loc['tipo'] == 'SECO'
    assert loc in client.get('/api/estoque/localizacoes').get_json()

    atualizada = client.put(f"/api/estoque/localizacoes/{loc['id']}", json={'nome': 'Depósito 2'})
    assert atualizada.status_code == 200
    assert atualizada.get_json()['nome'] == 'Depósito 2'

    assert client.delete(f"/api/estoque/localizacoes/{loc['id']}").status_code == 204
    assert client.put(f"/api/estoque/localizacoes/{loc['id']}", json={'nome': 'x'}).status_code == 404
    assert client.delete(f"/api/estoque/localizacoes/{loc['id']}").status_code == 404


def test_localizacao_validacoes(client):
    assert client.post('/api/estoque/localizacoes', json={}).status_code == 400
    assert client.put('/api/estoque/localizacoes/1', json={}).status_code == 400  # corpo vazio

    pai = client.post('/api/estoque/localizacoes', json={'nome': 'Pai'}).get_json()
    filha = client.post('/api/estoque/localizacoes',
                         json={'nome': 'Filha', 'parent_id': pai['id']}).get_json()

    assert client.put(f"/api/estoque/localizacoes/{pai['id']}",
                       json={'parent_id': filha['id']}).status_code == 400  # ciclo
    assert client.put(f"/api/estoque/localizacoes/{pai['id']}",
                       json={'parent_id': pai['id']}).status_code == 400  # pai de si mesma
    assert client.put(f"/api/estoque/localizacoes/{pai['id']}",
                       json={'parent_id': 9999}).status_code == 400  # pai inexistente
    assert client.put(f"/api/estoque/localizacoes/{pai['id']}",
                       json={'campo_invalido': 1}).status_code == 400  # campo não editável


def test_nao_remove_localizacao_com_dependencias(seeded_client):
    c = seeded_client

    # "Cozinha" (id=5) é pai de "Geladeira da Cozinha" (id=6) no seed.
    resposta = c.delete('/api/estoque/localizacoes/5')
    assert resposta.status_code == 409
    assert 'sub-localizações' in resposta.get_json()['erro']

    # Mesmo sem filhos, uma localização com lote também não pode desaparecer.
    local = c.post(
        '/api/estoque/localizacoes',
        json={'nome': 'Depósito com lote', 'tipo': 'SECO'},
    ).get_json()
    lote = c.post(
        '/api/estoque/lotes',
        json={'produto_id': 1, 'localizacao_id': local['id']},
    )
    assert lote.status_code == 201

    resposta = c.delete(f"/api/estoque/localizacoes/{local['id']}")
    assert resposta.status_code == 409
    assert 'lotes vinculados' in resposta.get_json()['erro']


def test_lotes_listagem_e_detalhe(seeded_client):
    c = seeded_client
    lote1 = c.post('/api/estoque/lotes', json={'produto_id': 1, 'localizacao_id': 1}).get_json()['id']
    lote2 = c.post('/api/estoque/lotes', json={'produto_id': 4, 'localizacao_id': 1}).get_json()['id']

    todos = c.get('/api/estoque/lotes')
    assert todos.status_code == 200 and len(todos.get_json()) == 2
    assert {'produto', 'localizacao'} <= todos.get_json()[0].keys()

    so_produto1 = c.get('/api/estoque/lotes?produto_id=1')
    assert [l['id'] for l in so_produto1.get_json()] == [lote1]
    assert next(l for l in todos.get_json() if l['id'] == lote2)['produto'] == 'Nozes'

    # GET /lotes/<id> devolve só os campos da tabela lote, sem nomes de produto/localizacao
    assert c.get(f'/api/estoque/lotes/{lote2}').get_json()['produto_id'] == 4
    assert c.get('/api/estoque/lotes/9999').status_code == 404


def test_atualizar_lote(seeded_client):
    c = seeded_client
    lote = c.post('/api/estoque/lotes', json={'produto_id': 1, 'localizacao_id': 1}).get_json()['id']

    atualizado = c.put(f'/api/estoque/lotes/{lote}',
                        json={'custo_unitario': 2.5, 'data_validade': '2099-01-01'})
    assert atualizado.status_code == 200
    assert atualizado.get_json()['custo_unitario'] == 2.5
    assert atualizado.get_json()['data_validade'] == '2099-01-01'

    assert c.put(f'/api/estoque/lotes/{lote}', json={'quantidade': 50}).status_code == 400
    assert c.put('/api/estoque/lotes/9999', json={'custo_unitario': 1}).status_code == 404


def test_sugestao_saida_validacoes(client):
    assert client.get('/api/estoque/sugestao-saida/1').status_code == 400  # sem quantidade
    assert client.get('/api/estoque/sugestao-saida/9999?quantidade=1').status_code == 404


def test_transferencia_por_localizacao_cria_e_reutiliza_lote_destino(seeded_client):
    c = seeded_client
    origem = c.post(
        '/api/estoque/lotes',
        json={
            'produto_id': 1,
            'localizacao_id': 1,
            'data_producao': '2026-11-01',
            'data_validade': '2027-11-01',
            'custo_unitario': 12.5,
        },
    ).get_json()
    c.post('/api/estoque/movimentacoes', json={
        'tipo': 'ENTRADA', 'lote_id': origem['id'], 'quantidade': 10
    })

    primeira = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFERENCIA',
        'lote_id': origem['id'],
        'localizacao_destino_id': 5,  # Cozinha também é SECO.
        'quantidade': 4,
        'observacao': 'Reposição da cozinha',
    })
    assert primeira.status_code == 201, primeira.get_json()
    movimento = primeira.get_json()
    assert movimento['lote_destino_id'] is not None

    destino_id = movimento['lote_destino_id']
    destino = c.get(f'/api/estoque/lotes/{destino_id}').get_json()
    assert destino['produto_id'] == origem['produto_id']
    assert destino['localizacao_id'] == 5
    assert destino['quantidade'] == 4
    assert destino['data_producao'] == origem['data_producao']
    assert destino['data_validade'] == origem['data_validade']
    assert destino['custo_unitario'] == origem['custo_unitario']
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 6

    segunda = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFERENCIA',
        'lote_id': origem['id'],
        'localizacao_destino_id': 5,
        'quantidade': 1,
    })
    assert segunda.status_code == 201, segunda.get_json()
    assert segunda.get_json()['lote_destino_id'] == destino_id
    assert c.get(f'/api/estoque/lotes/{destino_id}').get_json()['quantidade'] == 5
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 5


def test_transferencia_por_localizacao_rejeita_destino_incompativel_e_mesma_origem(seeded_client):
    c = seeded_client
    origem = c.post('/api/estoque/lotes', json={'produto_id': 1, 'localizacao_id': 1}).get_json()
    c.post('/api/estoque/movimentacoes', json={
        'tipo': 'ENTRADA', 'lote_id': origem['id'], 'quantidade': 10
    })

    mesma = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFERENCIA', 'lote_id': origem['id'],
        'localizacao_destino_id': 1, 'quantidade': 2,
    })
    assert mesma.status_code == 400

    incompativel = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFERENCIA', 'lote_id': origem['id'],
        'localizacao_destino_id': 2, 'quantidade': 2,  # Câmara Fria é RESFRIADO.
    })
    assert incompativel.status_code == 400
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 10
    assert c.get('/api/estoque/lotes?produto_id=1&localizacao_id=2').get_json() == []


def test_lista_transformacoes_disponiveis(seeded_client):
    c = seeded_client
    resposta = c.get('/api/estoque/transformacoes?produto_origem_id=5')
    assert resposta.status_code == 200
    assert resposta.get_json() == [
        {
            'produto_origem_id': 5,
            'produto_destino_id': 6,
            'produto_destino': 'Queijo ralado',
            'unidade_medida': 'g',
            'conservacao': 'RESFRIADO',
        }
    ]


def test_transformacao_automatica_cria_e_reutiliza_lote_destino(seeded_client):
    from datetime import date, timedelta

    c = seeded_client
    origem = c.post('/api/estoque/lotes', json={
        'produto_id': 5,
        'localizacao_id': 2,
        'data_validade': '2099-01-01',
        'custo_unitario': 0.05,
    }).get_json()
    c.post('/api/estoque/movimentacoes', json={
        'tipo': 'ENTRADA', 'lote_id': origem['id'], 'quantidade': 2000,
    })

    corpo = {
        'tipo': 'TRANSFORMACAO',
        'lote_id': origem['id'],
        'produto_destino_id': 6,
        'localizacao_destino_id': 4,
        'quantidade': 1000,
        'quantidade_destino': 900,
        'observacao': 'Queijo ralado para mise en place',
    }
    primeira = c.post('/api/estoque/movimentacoes', json=corpo)
    assert primeira.status_code == 201, primeira.get_json()
    mov = primeira.get_json()
    assert mov['perda_transformacao'] == 100
    assert mov['rendimento_percentual'] == 90
    assert 'perda de rendimento: 100 g' in mov['observacao']

    destino_id = mov['lote_destino_id']
    destino = c.get(f'/api/estoque/lotes/{destino_id}').get_json()
    assert destino['produto_id'] == 6
    assert destino['localizacao_id'] == 4
    assert destino['quantidade'] == 900
    assert destino['data_producao'] == date.today().isoformat()
    assert destino['data_validade'] == (date.today() + timedelta(days=7)).isoformat()
    assert round(destino['custo_unitario'], 6) == round((0.05 * 1000) / 900, 6)
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 1000

    segunda = c.post('/api/estoque/movimentacoes', json=corpo)
    assert segunda.status_code == 201, segunda.get_json()
    assert segunda.get_json()['lote_destino_id'] == destino_id
    assert c.get(f'/api/estoque/lotes/{destino_id}').get_json()['quantidade'] == 1800
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 0


def test_transformacao_automatica_rejeita_par_ou_local_invalido_sem_criar_lote(seeded_client):
    c = seeded_client
    origem = c.post('/api/estoque/lotes', json={
        'produto_id': 5, 'localizacao_id': 2, 'data_validade': '2099-01-01'
    }).get_json()
    c.post('/api/estoque/movimentacoes', json={
        'tipo': 'ENTRADA', 'lote_id': origem['id'], 'quantidade': 100,
    })
    antes = c.get('/api/estoque/lotes').get_json()

    nao_cadastrada = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFORMACAO', 'lote_id': origem['id'],
        'produto_destino_id': 7, 'localizacao_destino_id': 2,
        'quantidade': 10, 'quantidade_destino': 9,
    })
    assert nao_cadastrada.status_code == 400

    local_incompativel = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFORMACAO', 'lote_id': origem['id'],
        'produto_destino_id': 6, 'localizacao_destino_id': 1,
        'quantidade': 10, 'quantidade_destino': 9,
    })
    assert local_incompativel.status_code == 400

    depois = c.get('/api/estoque/lotes').get_json()
    assert len(depois) == len(antes)
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 100


def test_transformacao_automatica_rejeita_lote_origem_vencido(seeded_client):
    from datetime import date, timedelta

    c = seeded_client
    origem = c.post('/api/estoque/lotes', json={
        'produto_id': 5,
        'localizacao_id': 2,
        'data_validade': (date.today() - timedelta(days=1)).isoformat(),
    }).get_json()
    c.post('/api/estoque/movimentacoes', json={
        'tipo': 'ENTRADA', 'lote_id': origem['id'], 'quantidade': 100,
    })

    resposta = c.post('/api/estoque/movimentacoes', json={
        'tipo': 'TRANSFORMACAO',
        'lote_id': origem['id'],
        'produto_destino_id': 6,
        'localizacao_destino_id': 4,
        'quantidade': 100,
        'quantidade_destino': 90,
    })
    assert resposta.status_code == 409
    assert 'vencido' in resposta.get_json()['erro']
    assert c.get(f"/api/estoque/lotes/{origem['id']}").get_json()['quantidade'] == 100


def test_crud_regras_transformacao(seeded_client):
    c = seeded_client

    criada = c.post('/api/estoque/transformacoes', json={
        'produto_origem_id': 4,  # Nozes (g)
        'produto_destino_id': 7,  # Creme de nozes (g)
    })
    assert criada.status_code == 201, criada.get_json()
    assert criada.get_json()['produto_destino'] == 'Creme de nozes'

    duplicada = c.post('/api/estoque/transformacoes', json={
        'produto_origem_id': 4,
        'produto_destino_id': 7,
    })
    assert duplicada.status_code == 409

    unidade_incompativel = c.post('/api/estoque/transformacoes', json={
        'produto_origem_id': 3,  # Leite (ml)
        'produto_destino_id': 9,  # Chantili (g)
    })
    assert unidade_incompativel.status_code == 409

    removida = c.delete('/api/estoque/transformacoes/4/7')
    assert removida.status_code == 204
    assert c.delete('/api/estoque/transformacoes/4/7').status_code == 404
