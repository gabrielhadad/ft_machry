"""Gestão de estoque sobre as tabelas e triggers existentes em db/schema.sql."""
import sqlite3
from datetime import date
from flask import Blueprint, request
from ...db import get_db

bp = Blueprint('estoque', __name__, url_prefix='/api/estoque')


def erro(msg, status=400):
    return {'erro': str(msg)}, status


def corpo():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValueError('envie um objeto JSON')
    return dados


def inteiro(dados, nome, obrigatorio=True):
    valor = dados.get(nome)
    if valor is None and not obrigatorio:
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f'{nome} deve ser inteiro positivo')
    return valor


def quantidade(dados, nome='quantidade', obrigatorio=True):
    valor = dados.get(nome)
    if valor is None and not obrigatorio:
        return None
    try:
        if isinstance(valor, bool):
            raise ValueError()
        numero = float(valor)
        if not 0 < numero < float('inf'):
            raise ValueError()
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f'{nome} deve ser número positivo finito')
    return numero


def data_iso(valor, nome):
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError(f'{nome} deve ser uma data AAAA-MM-DD')
    try:
        return date.fromisoformat(valor).isoformat() if len(valor) == 10 else (_ for _ in ()).throw(ValueError())
    except ValueError:
        raise ValueError(f'{nome} deve ser uma data AAAA-MM-DD')


def existe(db, tabela, id_, onde=''):
    # Tabela vem apenas de chamadas internas, nunca do usuário.
    return db.execute(f'SELECT * FROM {tabela} WHERE id = ? {onde}', (id_,)).fetchone()


def validar_lote(db, lote_id):
    lote = existe(db, 'lote', lote_id)
    if lote is None:
        raise ValueError(f'lote {lote_id} não encontrado')
    return lote


def validar_usuario(db, id_):
    if existe(db, 'usuario', id_, 'AND ativo = 1') is None:
        raise ValueError('usuário não encontrado ou inativo')


def executar(acao):
    db = get_db()
    try:
        db.execute('BEGIN IMMEDIATE')
        resultado, status = acao(db)
        db.commit()
        return resultado, status
    except (ValueError, sqlite3.IntegrityError) as exc:
        db.rollback()
        return erro(str(exc))
    except Exception:
        db.rollback()
        raise


@bp.get('/inventario')
def inventario():
    sql = 'SELECT * FROM vw_inventario WHERE 1=1'
    parametros = []
    for campo in ('produto_id', 'lote_id'):
        if request.args.get(campo) is not None:
            try:
                valor = int(request.args[campo])
                if valor <= 0:
                    raise ValueError()
            except ValueError:
                return erro(f'{campo} inválido')
            sql += f' AND {campo} = ?'
            parametros.append(valor)
    return [dict(r) for r in get_db().execute(sql + ' ORDER BY produto, data_validade, lote_id', parametros)]


@bp.get('/movimentacoes')
def movimentacoes():
    try:
        limite = int(request.args.get('limite', 100))
        if not 1 <= limite <= 500:
            raise ValueError()
    except ValueError:
        return erro('limite deve estar entre 1 e 500')
    sql = 'SELECT * FROM movimentacao_estoque WHERE 1=1'
    args = []
    for filtro in ('lote_id', 'usuario_id'):
        if filtro in request.args:
            try:
                valor = int(request.args[filtro])
                if valor <= 0:
                    raise ValueError()
            except ValueError:
                return erro(f'{filtro} inválido')
            sql += f' AND {filtro} = ?'
            args.append(valor)
    if 'tipo' in request.args:
        sql += ' AND tipo = ?'
        args.append(request.args['tipo'].upper())
    sql += ' ORDER BY id DESC LIMIT ?'
    args.append(limite)
    return [dict(r) for r in get_db().execute(sql, args)]


@bp.get('/localizacoes')
def listar_localizacoes():
    return [dict(r) for r in get_db().execute('SELECT * FROM localizacao ORDER BY nome')]


@bp.post('/localizacoes')
def criar_localizacao():
    try:
        dados = corpo()
        nome = str(dados.get('nome') or '').strip()
        tipo = dados.get('tipo', 'SECO')
        pai = inteiro(dados, 'parent_id', False)
        if not nome or tipo not in ('SECO', 'RESFRIADO', 'CONGELADO'):
            raise ValueError('nome e tipo de localização são obrigatórios/válidos')
    except ValueError as exc:
        return erro(exc)
    def acao(db):
        if pai is not None and not existe(db, 'localizacao', pai):
            raise ValueError('localização pai não encontrada')
        cur = db.execute('INSERT INTO localizacao(nome,tipo,parent_id,foto_url) VALUES(?,?,?,?)',
                         (nome, tipo, pai, dados.get('foto_url')))
        return dict(existe(db, 'localizacao', cur.lastrowid)), 201
    return executar(acao)


@bp.put('/localizacoes/<int:loc_id>')
def atualizar_localizacao(loc_id):
    try:
        dados = corpo()
        permitido = {'nome', 'tipo', 'parent_id', 'foto_url'}
        if not dados or set(dados) - permitido:
            raise ValueError('campos inválidos ou ausentes')
        if 'nome' in dados:
            dados['nome'] = str(dados['nome'] or '').strip()
            if not dados['nome']:
                raise ValueError('nome vazio')
        if 'tipo' in dados and dados['tipo'] not in ('SECO','RESFRIADO','CONGELADO'):
            raise ValueError('tipo inválido')
        if 'parent_id' in dados and dados['parent_id'] is not None:
            inteiro(dados, 'parent_id')
    except ValueError as exc:
        return erro(exc)
    def acao(db):
        if not existe(db, 'localizacao', loc_id):
            return {'erro': 'localização não encontrada'}, 404
        pai = dados.get('parent_id')
        if pai is not None:
            if not existe(db, 'localizacao', pai):
                raise ValueError('localização pai não encontrada')
            if pai == loc_id:
                raise ValueError('localização não pode ser pai de si mesma')
            visitados = {loc_id}
            atual = pai
            while atual is not None:
                if atual in visitados:
                    raise ValueError('hierarquia de localização circular')
                visitados.add(atual)
                atual = existe(db, 'localizacao', atual)['parent_id']
        if 'tipo' in dados:
            incompatibilidade = db.execute('''SELECT 1 FROM lote l JOIN produto p ON p.id=l.produto_id
                WHERE l.localizacao_id=? AND p.conservacao<>? LIMIT 1''',
                (loc_id, dados['tipo'])).fetchone()
            if incompatibilidade:
                raise ValueError('alteração de tipo incompatível com produtos dos lotes existentes')
        sql = ', '.join(f'{k}=?' for k in dados)
        db.execute(f'UPDATE localizacao SET {sql} WHERE id=?', (*dados.values(),loc_id))
        return dict(existe(db, 'localizacao', loc_id)), 200
    return executar(acao)


@bp.delete('/localizacoes/<int:loc_id>')
def remover_localizacao(loc_id):
    def acao(db):
        cur = db.execute('DELETE FROM localizacao WHERE id=?', (loc_id,))
        return ({}, 204) if cur.rowcount else ({'erro':'localização não encontrada'},404)
    return executar(acao)


@bp.get('/lotes')
def listar_lotes():
    sql = '''SELECT l.*,p.nome AS produto,loc.nome AS localizacao FROM lote l
             JOIN produto p ON p.id=l.produto_id JOIN localizacao loc ON loc.id=l.localizacao_id WHERE 1=1'''
    args=[]
    for campo in ('produto_id','localizacao_id'):
        if campo in request.args:
            try:
                valor=int(request.args[campo]); assert valor>0
            except (ValueError, AssertionError):
                return erro(f'{campo} inválido')
            sql+=f' AND l.{campo}=?'; args.append(valor)
    return [dict(r) for r in get_db().execute(sql+' ORDER BY l.data_validade IS NULL,l.data_validade,l.id', args)]


@bp.get('/lotes/<int:lote_id>')
def detalhar_lote(lote_id):
    row=existe(get_db(),'lote',lote_id)
    return dict(row) if row else erro('lote não encontrado',404)


@bp.post('/lotes')
def criar_lote():
    try:
        dados=corpo()
        pid=inteiro(dados,'produto_id'); loc=inteiro(dados,'localizacao_id')
        validade=data_iso(dados.get('data_validade'),'data_validade')
        producao=data_iso(dados.get('data_producao'),'data_producao')
        custo=dados.get('custo_unitario')
        if custo is not None:
            custo=float(custo)
            if not 0<=custo<float('inf'):
                raise ValueError('custo_unitario inválido')
    except (ValueError,TypeError,OverflowError) as exc:
        return erro(exc)
    def acao(db):
        p=existe(db,'produto',pid,'AND ativo=1')
        local=existe(db,'localizacao',loc)
        if not p or not local:
            raise ValueError('produto ativo ou localização não encontrados')
        if p['validade_obrigatoria'] and validade is None:
            raise ValueError('produto exige data_validade')
        if producao and validade and producao>validade:
            raise ValueError('validade anterior à produção')
        if p['conservacao'] != local['tipo']:
            raise ValueError('conservação do produto incompatível com localização')
        cur=db.execute('''INSERT INTO lote(produto_id,localizacao_id,data_producao,data_validade,custo_unitario)
                          VALUES(?,?,?,?,?)''',(pid,loc,producao,validade,custo))
        return dict(existe(db,'lote',cur.lastrowid)),201
    return executar(acao)


@bp.put('/lotes/<int:lote_id>')
def atualizar_lote(lote_id):
    try:
        dados=corpo()
        permitido={'data_producao','data_validade','custo_unitario'}
        if not dados or set(dados)-permitido:
            raise ValueError('somente datas e custo podem ser editados; saldo muda por movimentação')
        for campo in ('data_producao','data_validade'):
            if campo in dados:
                dados[campo]=data_iso(dados[campo],campo)
        if 'custo_unitario' in dados and dados['custo_unitario'] is not None:
            dados['custo_unitario']=float(dados['custo_unitario'])
            if not 0<=dados['custo_unitario']<float('inf'):
                raise ValueError('custo inválido')
    except (ValueError,TypeError,OverflowError) as exc:
        return erro(exc)
    def acao(db):
        lote=existe(db,'lote',lote_id)
        if not lote:
            return {'erro':'lote não encontrado'},404
        validade=dados.get('data_validade',lote['data_validade'])
        producao=dados.get('data_producao',lote['data_producao'])
        produto=existe(db,'produto',lote['produto_id'])
        if produto['validade_obrigatoria'] and not validade:
            raise ValueError('validade obrigatória')
        if producao and validade and producao>validade:
            raise ValueError('validade anterior à produção')
        db.execute('UPDATE lote SET '+','.join(f'{k}=?' for k in dados)+' WHERE id=?',(*dados.values(),lote_id))
        return dict(existe(db,'lote',lote_id)),200
    return executar(acao)


@bp.post('/movimentacoes')
def registrar_movimentacao():
    try:
        d=corpo()
        tipo=d.get('tipo')
        tipos={'ENTRADA','SAIDA','AJUSTE_ENTRADA','AJUSTE_SAIDA','TRANSFERENCIA','TRANSFORMACAO'}
        if tipo not in tipos:
            raise ValueError('tipo inválido; PRODUCAO/CONSUMO_PRODUCAO são reservados ao módulo produção')
        lote_id=inteiro(d,'lote_id'); usuario_id=inteiro(d,'usuario_id')
        qtd=quantidade(d)
        destino=inteiro(d,'lote_destino_id',False)
        qtd_destino=quantidade(d,'quantidade_destino',False)
        motivo=str(d.get('motivo') or '').strip() or None
        if tipo in {'SAIDA','AJUSTE_ENTRADA','AJUSTE_SAIDA'} and not motivo:
            raise ValueError('motivo obrigatório')
        if (tipo in {'TRANSFERENCIA','TRANSFORMACAO'}) != (destino is not None):
            raise ValueError('lote_destino_id obrigatório apenas para transferência/transformação')
        if (tipo=='TRANSFORMACAO') != (qtd_destino is not None):
            raise ValueError('quantidade_destino obrigatória apenas para transformação')
        if destino==lote_id:
            raise ValueError('origem e destino precisam ser diferentes')
    except (ValueError, TypeError, OverflowError) as exc:
        return erro(exc)
    def acao(db):
        origem=validar_lote(db,lote_id)
        validar_usuario(db,usuario_id)
        if tipo in {'SAIDA','AJUSTE_SAIDA','TRANSFERENCIA','TRANSFORMACAO'} and origem['quantidade']<qtd:
            raise ValueError('saldo insuficiente')
        if destino is not None:
            outro=validar_lote(db,destino)
            local_destino = existe(db, 'localizacao', outro['localizacao_id'])
            produto_destino = existe(db, 'produto', outro['produto_id'])
            if not local_destino or not produto_destino or produto_destino['conservacao'] != local_destino['tipo']:
                raise ValueError('lote destino com conservação incompatível')
            if tipo=='TRANSFERENCIA' and origem['produto_id']!=outro['produto_id']:
                raise ValueError('transferência requer mesmo produto')
            if tipo=='TRANSFORMACAO' and not db.execute('''SELECT 1 FROM produto_transformacao
                 WHERE produto_origem_id=? AND produto_destino_id=?''',
                 (origem['produto_id'],outro['produto_id'])).fetchone():
                raise ValueError('transformação não cadastrada entre os produtos')
        cur=db.execute('''INSERT INTO movimentacao_estoque
            (tipo,lote_id,lote_destino_id,quantidade,quantidade_destino,motivo,usuario_id,observacao)
            VALUES (?,?,?,?,?,?,?,?)''', (tipo,lote_id,destino,qtd,qtd_destino,motivo,usuario_id,d.get('observacao')))
        registro=db.execute('SELECT * FROM movimentacao_estoque WHERE id=?',(cur.lastrowid,)).fetchone()
        return dict(registro),201
    return executar(acao)


@bp.get('/sugestao-saida/<int:produto_id>')
def sugestao_saida(produto_id):
    try:
        qtd=quantidade({'quantidade':request.args.get('quantidade')})
    except ValueError as exc:
        return erro(exc)
    db=get_db()
    if not existe(db,'produto',produto_id,'AND ativo=1'):
        return erro('produto não encontrado',404)
    lotes=db.execute('''SELECT * FROM lote WHERE produto_id=? AND quantidade>0
      AND (data_validade IS NULL OR data_validade>=date('now'))
      ORDER BY data_validade IS NULL,data_validade,criado_em,id''',(produto_id,)).fetchall()
    faltante=qtd; selecao=[]
    for lote in lotes:
        usar=min(faltante,lote['quantidade'])
        if usar>0:
            selecao.append({'lote_id':lote['id'],'quantidade':usar,'data_validade':lote['data_validade']})
            faltante-=usar
        if faltante<=0:
            break
    return {'produto_id':produto_id,'quantidade_solicitada':qtd,'lotes':selecao,
            'quantidade_faltante':max(0,faltante),
            'criterio':'FEFO: menor validade primeiro (somente lotes não vencidos)',
            'aviso':'Sugestão de separação: não movimenta o estoque'}


@bp.get('/usuarios')
def usuarios_ativos():
    """Usuários disponíveis para identificação de eventos no painel acadêmico (sem autenticação)."""
    return [dict(x) for x in get_db().execute('SELECT id, nome, papel FROM usuario WHERE ativo=1 ORDER BY nome')]


@bp.get('/transformacoes')
def listar_transformacoes():
    return [dict(x) for x in get_db().execute('SELECT produto_origem_id, produto_destino_id FROM produto_transformacao ORDER BY produto_origem_id, produto_destino_id')]


@bp.post('/transformacoes')
def autorizar_transformacao():
    try:
        dados = corpo()
        origem = inteiro(dados, 'produto_origem_id')
        destino = inteiro(dados, 'produto_destino_id')
        if origem == destino:
            raise ValueError('origem e destino precisam ser diferentes')
    except ValueError as exc:
        return erro(exc)
    def acao(db):
        if not existe(db, 'produto', origem, 'AND ativo=1') or not existe(db, 'produto', destino, 'AND ativo=1'):
            raise ValueError('produtos ativos não encontrados')
        db.execute('INSERT INTO produto_transformacao (produto_origem_id, produto_destino_id) VALUES (?,?)', (origem, destino))
        return {'produto_origem_id': origem, 'produto_destino_id': destino}, 201
    return executar(acao)
