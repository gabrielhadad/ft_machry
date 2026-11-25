"""Valores em dinheiro: sempre `Decimal`, nunca `float`.

Custos unitários guardam 6 casas (o custo por grama ou mililitro costuma ser
uma fração de centavo); valores totais são arredondados para centavos só na
hora de exibir ou gravar um total.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CASAS_DO_CUSTO = Decimal("0.000001")
CENTAVO = Decimal("0.01")
ZERO = Decimal(0)


def para_decimal(valor) -> Decimal | None:
    """Converte sem herdar o erro binário do float (0.1 vira 0.1, não 0.1000000000000000055)."""
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def custo_unitario(valor: Decimal | None) -> Decimal | None:
    return None if valor is None else valor.quantize(CASAS_DO_CUSTO, rounding=ROUND_HALF_UP)


def em_reais(valor: Decimal | None) -> Decimal | None:
    return None if valor is None else valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def para_json(valor: Decimal | None) -> float | None:
    """A API continua devolvendo número; o valor já chega arredondado."""
    return None if valor is None else float(valor)
