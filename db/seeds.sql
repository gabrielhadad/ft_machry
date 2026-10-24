-- Dados de exemplo baseados na documentação (Bolo de Nozes)
PRAGMA foreign_keys = ON;

INSERT INTO usuario (id, nome, papel) VALUES
    (1, 'Admin', 'ADMIN'),
    (2, 'Cozinheiro José', 'USER');

INSERT INTO fase_producao (id, nome) VALUES
    (1, 'Bater/Misturar'),
    (2, 'Cozir'),
    (3, 'Confeitar'),
    (4, 'Fritar'),
    (5, 'Montar');

INSERT INTO localizacao (id, nome, tipo, parent_id) VALUES
    (1, 'Estoque Seco',             'SECO',      NULL),
    (2, 'Câmara Fria',              'RESFRIADO', NULL),
    (3, 'Câmara Fria - Congelados', 'CONGELADO', 2),
    (4, 'Câmara Fria - Resfriados', 'RESFRIADO', 2),
    (5, 'Cozinha',                  'SECO',      NULL),
    (6, 'Geladeira da Cozinha',     'RESFRIADO', 5),
    (7, 'Padaria',                  'SECO',      NULL);

INSERT INTO grupo_produto (id, nome) VALUES
    (1, 'Insumos secos'),
    (2, 'Laticínios'),
    (3, 'Semiacabados'),
    (4, 'Confeitaria');

INSERT INTO produto (id, nome, tipo, unidade_medida, grupo_id, conservacao,
                     validade_obrigatoria, validade_padrao_dias) VALUES
    (1, 'Farinha de trigo', 'INSUMO',        'g',  1, 'SECO',      0, 180),
    (2, 'Ovo',              'INSUMO',        'un', 2, 'RESFRIADO', 1, 20),
    (3, 'Leite',            'INSUMO',        'ml', 2, 'RESFRIADO', 1, 7),
    (4, 'Nozes',            'INSUMO',        'g',  1, 'SECO',      0, 90),
    (5, 'Queijo (bloco)',   'INSUMO',        'g',  2, 'RESFRIADO', 1, 30),
    (6, 'Queijo ralado',    'INTERMEDIARIO', 'g',  2, 'RESFRIADO', 1, 7),
    (7, 'Creme de nozes',   'INTERMEDIARIO', 'g',  3, 'RESFRIADO', 1, 3),
    (8, 'Massa de bolo',    'INTERMEDIARIO', 'g',  3, 'RESFRIADO', 1, 2),
    (9, 'Chantili',         'INTERMEDIARIO', 'g',  3, 'RESFRIADO', 1, 2),
    (10, 'Bolo de Nozes - Médio', 'FINAL',   'un', 4, 'RESFRIADO', 1, 4);

-- Transformação sem ficha técnica: queijo bloco -> queijo ralado
INSERT INTO produto_transformacao (produto_origem_id, produto_destino_id)
VALUES (5, 6);

-- Ficha técnica do Bolo de Nozes (previsto conforme documentação)
INSERT INTO ficha_tecnica (id, produto_id, rendimento)
VALUES (1, 10, 1);  -- rende 1 un

INSERT INTO ficha_tecnica_fase (id, ficha_tecnica_id, fase_id, ordem, tempo_previsto_min) VALUES
    (1, 1, 1, 1, 10),  -- Bater/Misturar
    (2, 1, 2, 2, 30),  -- Cozir
    (3, 1, 3, 3, 15);  -- Confeitar

INSERT INTO ficha_tecnica_componente (ficha_tecnica_id, produto_id, quantidade, ficha_tecnica_fase_id) VALUES
    (1, 8, 400, 1),   -- Massa de bolo (g)  -> Bater/Misturar
    (1, 3, 300, 1),   -- Leite (ml)         -> Bater/Misturar
    (1, 7, 500, 3),   -- Creme de nozes (g) -> Confeitar
    (1, 9,  50, 3),   -- Chantili (g)       -> Confeitar
    (1, 4, 100, 3);   -- Nozes (g)          -> Confeitar
