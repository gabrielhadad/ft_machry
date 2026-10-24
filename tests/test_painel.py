def test_painel_disponivel(client):
    resposta = client.get('/painel')
    assert resposta.status_code == 200
    assert b'Machry' in resposta.data
    assert b'productForm' in resposta.data


def test_assets_painel(client):
    for caminho in ('/static/painel.css', '/static/painel.js'):
        assert client.get(caminho).status_code == 200


def test_formulario_usa_api_existente(client):
    item = {'nome':'Produto do painel','tipo':'INSUMO','unidade_medida':'kg','conservacao':'SECO','validade_obrigatoria':0}
    criado = client.post('/api/produtos',json=item)
    assert criado.status_code == 201
    id_ = criado.json['id']
    assert client.put(f'/api/produtos/{id_}',json={'nome':'Produto editado'}).status_code == 200
    assert client.delete(f'/api/produtos/{id_}').status_code == 204
