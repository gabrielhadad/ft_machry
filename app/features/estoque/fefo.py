"""Planejamento de consumo por FEFO (primeiro a vencer, primeiro a sair).

Usado pela produção, ao dar baixa de verdade, e pela ficha técnica, para
mostrar quanto custaria consumir os componentes agora. Por isso o mesmo
cálculo serve aos dois e o custo previsto bate com o realizado.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import ItemLote, Lote
from .repository import EstoqueRepository


@dataclass
class UsoPlanejado:
    lote: Lote
    quantidade: float
    itens: list[tuple[ItemLote, float]] | None


def planejar_consumo_fefo(
    estoque: EstoqueRepository, produto_id: int, quantidade: float, *, bloquear: bool
) -> tuple[list[UsoPlanejado], float]:
    """Lotes e itens que sairiam do estoque, e quanto falta se o saldo não bastar.

    `bloquear` trava as linhas para atualização; use só quando for dar a baixa.
    """
    restante = float(quantidade)
    usos: list[UsoPlanejado] = []
    for lote_row in estoque.lotes_fefo_disponiveis(produto_id):
        lote = estoque.obter_lote(lote_row["id"], para_atualizacao=bloquear)
        if estoque.lote_tem_itens(lote.id):
            itens = estoque.itens_fefo(lote.id, bloquear=bloquear)
            disponivel = sum(float(item.saldo) for item in itens)
            usar = min(restante, disponivel)
            usos_itens: list[tuple[ItemLote, float]] | None = []
            falta_no_lote = usar
            for item in itens:
                if falta_no_lote <= 0:
                    break
                parte = min(float(item.saldo), falta_no_lote)
                usos_itens.append((item, parte))
                falta_no_lote = round(falta_no_lote - parte, 6)
        else:
            usar = min(restante, float(lote.quantidade))
            usos_itens = None
        if usar > 0:
            usos.append(UsoPlanejado(lote, usar, usos_itens))
            restante = round(restante - usar, 6)
        if restante <= 0:
            break
    return usos, max(restante, 0.0)
