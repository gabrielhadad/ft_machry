PRAGMA foreign_keys = ON;
CREATE TABLE usuario (
    id          INTEGER PRIMARY KEY,
    nome        TEXT    NOT NULL,
    papel       TEXT    NOT NULL DEFAULT 'USER'
                        CHECK (papel IN ('ADMIN', 'OWNER', 'USER')),
    foto_url    TEXT,
    ativo       INTEGER NOT NULL DEFAULT 1,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE grupo_produto (
    id   INTEGER PRIMARY KEY,
    nome TEXT    NOT NULL UNIQUE
);

CREATE TABLE fase_producao (
    id   INTEGER PRIMARY KEY,
    nome TEXT    NOT NULL UNIQUE
);

CREATE TABLE localizacao (
    id        INTEGER PRIMARY KEY,
    nome      TEXT    NOT NULL UNIQUE,
    tipo      TEXT    NOT NULL DEFAULT 'SECO'
                      CHECK (tipo IN ('CONGELADO', 'RESFRIADO', 'SECO')),
    parent_id INTEGER REFERENCES localizacao(id),
    foto_url  TEXT
);

CREATE TABLE produto (
    id                   INTEGER PRIMARY KEY,
    nome                 TEXT    NOT NULL,
    tipo                 TEXT    NOT NULL
                                 CHECK (tipo IN ('INSUMO', 'INTERMEDIARIO', 'FINAL')),
    unidade_medida       TEXT    NOT NULL,
    grupo_id             INTEGER REFERENCES grupo_produto(id),
    conservacao          TEXT    NOT NULL DEFAULT 'SECO'
                                 CHECK (conservacao IN ('CONGELADO', 'RESFRIADO', 'SECO')),
    validade_obrigatoria INTEGER NOT NULL DEFAULT 0,
    validade_padrao_dias INTEGER,
    foto_url             TEXT,
    ativo                INTEGER NOT NULL DEFAULT 1,
    criado_em            TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE produto_transformacao (
    produto_origem_id  INTEGER NOT NULL REFERENCES produto(id),
    produto_destino_id INTEGER NOT NULL REFERENCES produto(id),
    PRIMARY KEY (produto_origem_id, produto_destino_id),
    CHECK (produto_origem_id <> produto_destino_id)
);

CREATE TABLE ficha_tecnica (
    id         INTEGER PRIMARY KEY,
    produto_id INTEGER NOT NULL UNIQUE REFERENCES produto(id),
    rendimento NUMERIC NOT NULL CHECK (rendimento > 0),
    observacao TEXT
);

CREATE TABLE ficha_tecnica_fase (
    id                 INTEGER PRIMARY KEY,
    ficha_tecnica_id   INTEGER NOT NULL REFERENCES ficha_tecnica(id),
    fase_id            INTEGER NOT NULL REFERENCES fase_producao(id),
    ordem              INTEGER NOT NULL,
    tempo_previsto_min INTEGER NOT NULL CHECK (tempo_previsto_min > 0),
    UNIQUE (ficha_tecnica_id, ordem)
);

CREATE TABLE ficha_tecnica_componente (
    id                    INTEGER PRIMARY KEY,
    ficha_tecnica_id      INTEGER NOT NULL REFERENCES ficha_tecnica(id),
    produto_id            INTEGER NOT NULL REFERENCES produto(id),
    quantidade            NUMERIC NOT NULL CHECK (quantidade > 0),
    ficha_tecnica_fase_id INTEGER REFERENCES ficha_tecnica_fase(id),
    UNIQUE (ficha_tecnica_id, produto_id)
);

CREATE TRIGGER trg_ftc_fase_coerente_ins
BEFORE INSERT ON ficha_tecnica_componente
WHEN NEW.ficha_tecnica_fase_id IS NOT NULL
BEGIN
    SELECT CASE WHEN (SELECT ficha_tecnica_id FROM ficha_tecnica_fase
                       WHERE id = NEW.ficha_tecnica_fase_id) <> NEW.ficha_tecnica_id
    THEN RAISE(ABORT, 'fase de outra ficha tecnica') END;
END;

CREATE TRIGGER trg_ftc_fase_coerente_upd
BEFORE UPDATE OF ficha_tecnica_fase_id, ficha_tecnica_id ON ficha_tecnica_componente
WHEN NEW.ficha_tecnica_fase_id IS NOT NULL
BEGIN
    SELECT CASE WHEN (SELECT ficha_tecnica_id FROM ficha_tecnica_fase
                       WHERE id = NEW.ficha_tecnica_fase_id) <> NEW.ficha_tecnica_id
    THEN RAISE(ABORT, 'fase de outra ficha tecnica') END;
END;

CREATE TABLE lote (
    id             INTEGER PRIMARY KEY,
    produto_id     INTEGER NOT NULL REFERENCES produto(id),
    localizacao_id INTEGER NOT NULL REFERENCES localizacao(id),
    quantidade     NUMERIC NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    data_producao  TEXT,
    data_validade  TEXT,
    custo_unitario NUMERIC,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_lote_fifo ON lote (produto_id, data_validade, localizacao_id);

CREATE TABLE solicitacao_producao (
    id               INTEGER PRIMARY KEY,
    ficha_tecnica_id INTEGER NOT NULL REFERENCES ficha_tecnica(id),
    usuario_id       INTEGER NOT NULL REFERENCES usuario(id),
    status           TEXT    NOT NULL DEFAULT 'ABERTA'
                             CHECK (status IN ('ABERTA', 'EM_SEPARACAO',
                                               'EM_PRODUCAO', 'CONCLUIDA', 'CANCELADA')),
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now')),
    concluido_em     TEXT
);

CREATE TABLE sp_fase (
    id                      INTEGER PRIMARY KEY,
    solicitacao_producao_id INTEGER NOT NULL REFERENCES solicitacao_producao(id),
    fase_id                 INTEGER NOT NULL REFERENCES fase_producao(id),
    ordem                   INTEGER NOT NULL,
    tempo_previsto_min      INTEGER NOT NULL,
    tempo_realizado_min     INTEGER,
    UNIQUE (solicitacao_producao_id, ordem)
);

CREATE TABLE sp_componente (
    id                      INTEGER PRIMARY KEY,
    solicitacao_producao_id INTEGER NOT NULL REFERENCES solicitacao_producao(id),
    produto_id              INTEGER NOT NULL REFERENCES produto(id),
    quantidade_prevista     NUMERIC NOT NULL CHECK (quantidade_prevista > 0),
    sp_fase_id              INTEGER REFERENCES sp_fase(id),
    UNIQUE (solicitacao_producao_id, produto_id)
);

CREATE TRIGGER trg_spc_fase_coerente_ins
BEFORE INSERT ON sp_componente
WHEN NEW.sp_fase_id IS NOT NULL
BEGIN
    SELECT CASE WHEN (SELECT solicitacao_producao_id FROM sp_fase
                       WHERE id = NEW.sp_fase_id) <> NEW.solicitacao_producao_id
    THEN RAISE(ABORT, 'fase de outra solicitacao de producao') END;
END;

CREATE TRIGGER trg_spc_fase_coerente_upd
BEFORE UPDATE OF sp_fase_id, solicitacao_producao_id ON sp_componente
WHEN NEW.sp_fase_id IS NOT NULL
BEGIN
    SELECT CASE WHEN (SELECT solicitacao_producao_id FROM sp_fase
                       WHERE id = NEW.sp_fase_id) <> NEW.solicitacao_producao_id
    THEN RAISE(ABORT, 'fase de outra solicitacao de producao') END;
END;

CREATE TABLE movimentacao_estoque (
    id                      INTEGER PRIMARY KEY,
    tipo                    TEXT    NOT NULL
                                    CHECK (tipo IN ('ENTRADA', 'PRODUCAO', 'SAIDA',
                                                    'CONSUMO_PRODUCAO', 'TRANSFERENCIA',
                                                    'TRANSFORMACAO',
                                                    'AJUSTE_ENTRADA', 'AJUSTE_SAIDA')),
    lote_id                 INTEGER NOT NULL REFERENCES lote(id),
    lote_destino_id         INTEGER REFERENCES lote(id),
    quantidade              NUMERIC NOT NULL CHECK (quantidade > 0),
    quantidade_destino      NUMERIC CHECK (quantidade_destino > 0),
    motivo                  TEXT,
    usuario_id              INTEGER NOT NULL REFERENCES usuario(id),
    solicitacao_producao_id INTEGER REFERENCES solicitacao_producao(id),
    sp_componente_id        INTEGER REFERENCES sp_componente(id),
    observacao              TEXT,
    criado_em               TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (lote_destino_id IS NULL OR lote_destino_id <> lote_id),
    CHECK (tipo NOT IN ('TRANSFERENCIA', 'TRANSFORMACAO') OR lote_destino_id IS NOT NULL),
    CHECK (tipo = 'TRANSFORMACAO' OR quantidade_destino IS NULL),
    CHECK (tipo NOT IN ('SAIDA', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA') OR motivo IS NOT NULL),
    CHECK (tipo <> 'PRODUCAO' OR solicitacao_producao_id IS NOT NULL),
    CHECK (tipo <> 'CONSUMO_PRODUCAO' OR sp_componente_id IS NOT NULL)
);

CREATE INDEX idx_mov_lote ON movimentacao_estoque (lote_id, criado_em);
CREATE INDEX idx_mov_sp   ON movimentacao_estoque (solicitacao_producao_id);
CREATE INDEX idx_mov_sp_componente ON movimentacao_estoque (sp_componente_id);

CREATE TRIGGER trg_mov_valida
BEFORE INSERT ON movimentacao_estoque
WHEN NEW.lote_destino_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN NEW.tipo = 'TRANSFERENCIA'
         AND (SELECT produto_id FROM lote WHERE id = NEW.lote_id)
          <> (SELECT produto_id FROM lote WHERE id = NEW.lote_destino_id)
        THEN RAISE(ABORT, 'transferencia exige lotes do mesmo produto')

        WHEN NEW.tipo = 'TRANSFORMACAO'
         AND NOT EXISTS (
             SELECT 1 FROM produto_transformacao pt
              WHERE pt.produto_origem_id  = (SELECT produto_id FROM lote WHERE id = NEW.lote_id)
                AND pt.produto_destino_id = (SELECT produto_id FROM lote WHERE id = NEW.lote_destino_id))
        THEN RAISE(ABORT, 'transformacao nao cadastrada em produto_transformacao')
    END;
END;

CREATE TRIGGER trg_mov_imutavel_update
BEFORE UPDATE ON movimentacao_estoque
BEGIN
    SELECT RAISE(ABORT, 'movimentacao_estoque e append-only: eventos nao podem ser alterados');
END;

CREATE TRIGGER trg_mov_imutavel_delete
BEFORE DELETE ON movimentacao_estoque
BEGIN
    SELECT RAISE(ABORT, 'movimentacao_estoque e append-only: eventos nao podem ser apagados');
END;

CREATE TRIGGER trg_mov_aplica
AFTER INSERT ON movimentacao_estoque
BEGIN
    UPDATE lote SET quantidade = quantidade + NEW.quantidade
     WHERE id = NEW.lote_id
       AND NEW.tipo IN ('ENTRADA', 'PRODUCAO', 'AJUSTE_ENTRADA');

    UPDATE lote SET quantidade = quantidade - NEW.quantidade
     WHERE id = NEW.lote_id
       AND NEW.tipo IN ('SAIDA', 'CONSUMO_PRODUCAO', 'TRANSFERENCIA',
                        'TRANSFORMACAO', 'AJUSTE_SAIDA');

    UPDATE lote SET quantidade = quantidade + COALESCE(NEW.quantidade_destino, NEW.quantidade)
     WHERE id = NEW.lote_destino_id
       AND NEW.tipo IN ('TRANSFERENCIA', 'TRANSFORMACAO');
END;

CREATE VIEW vw_inventario AS
SELECT p.id              AS produto_id,
       p.nome            AS produto,
       p.tipo            AS tipo_produto,
       p.unidade_medida,
       l.id              AS lote_id,
       l.quantidade,
       l.data_validade,
       loc.nome          AS localizacao
  FROM lote l
  JOIN produto p       ON p.id = l.produto_id
  JOIN localizacao loc ON loc.id = l.localizacao_id
 WHERE l.quantidade > 0;

CREATE VIEW vw_fifo AS
SELECT l.*
  FROM lote l
 WHERE l.quantidade > 0
 ORDER BY l.produto_id, l.data_validade ASC, l.criado_em ASC;

CREATE VIEW vw_sp_componente AS
SELECT c.id                                 AS sp_componente_id,
       c.solicitacao_producao_id,
       c.produto_id,
       p.nome                               AS componente,
       p.unidade_medida,
       sf.ordem                             AS fase_ordem,
       fp.nome                              AS fase,
       c.quantidade_prevista,
       COALESCE(SUM(m.quantidade), 0)       AS quantidade_realizada,
       SUM(m.quantidade * l.custo_unitario) AS custo_realizado
  FROM sp_componente c
  JOIN produto p ON p.id = c.produto_id
  LEFT JOIN sp_fase sf ON sf.id = c.sp_fase_id
  LEFT JOIN fase_producao fp ON fp.id = sf.fase_id
  LEFT JOIN movimentacao_estoque m ON m.sp_componente_id = c.id
                                  AND m.tipo = 'CONSUMO_PRODUCAO'
  LEFT JOIN lote l ON l.id = m.lote_id
 GROUP BY c.id;

CREATE VIEW vw_sp_producao AS
SELECT m.solicitacao_producao_id,
       m.lote_id,
       m.quantidade,
       m.criado_em
  FROM movimentacao_estoque m
 WHERE m.tipo = 'PRODUCAO';
