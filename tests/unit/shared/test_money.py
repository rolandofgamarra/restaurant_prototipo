"""Tests unitarios de shared/money.py — RF-7, RF-11, RF-15.

ADR 0002: un único punto de redondeo (`redondear_gs`), sin `Decimal` ni `float`,
aserciones exactas de dinero (nunca `pytest.approx`). Estos tests se escriben y
corren en rojo ANTES de que exista `src/shared/money.py` (plan §5.3).

`cuadrar_lineas` (plan §3.1, ADR 0002 §3): se redondea el TOTAL y se ajusta la
ÚLTIMA línea, de modo que la suma de las líneas iguale siempre al total. Nunca
al revés.
"""

import pytest
from src.shared.errors import ErrorDeNegocio
from src.shared.money import cuadrar_lineas, redondear_gs


class TestRedondearGs:
    """Casos del plan §3.1 para `redondear_gs(monto, multiplo)`."""

    def test_multiplo_menor_o_igual_a_uno_devuelve_el_monto_tal_cual(self):
        assert redondear_gs(13_300, 1) == 13_300
        assert redondear_gs(13_300, 0) == 13_300
        assert redondear_gs(13_300, -1) == 13_300
        # REDONDEO_VUELTO_GS mal configurado con un negativo mayor que -1 también
        # debe pasar de largo, no interpretarse como un múltiplo válido.
        assert redondear_gs(13_300, -500) == 13_300

    def test_redondea_hacia_arriba_cuando_el_resto_supera_la_mitad(self):
        # 13_300 mod 500 = 300; 300*2=600 >= 500 -> sube
        assert redondear_gs(13_300, 500) == 13_500

    def test_redondea_hacia_abajo_cuando_el_resto_no_llega_a_la_mitad(self):
        # 13_200 mod 500 = 200; 200*2=400 < 500 -> baja
        assert redondear_gs(13_200, 500) == 13_000

    def test_redondeo_comercial_mitad_hacia_arriba(self):
        # 13_250 mod 500 = 250; 250*2=500 >= 500 -> sube (mitad exacta va arriba)
        assert redondear_gs(13_250, 500) == 13_500

    def test_monto_negativo(self):
        # mod de Python: -13_300 mod 500 = 200 (siempre >= 0, como indica el plan)
        # resto=200; 200*2=400 < 500 -> baja: -13_300 - 200 = -13_500
        assert redondear_gs(-13_300, 500) == -13_500

    def test_monto_negativo_redondea_hacia_arriba_cuando_el_resto_supera_la_mitad(self):
        # -13_200 mod 500 = 300; 300*2=600 >= 500 -> sube: -13_200 - 300 + 500 = -13_000
        assert redondear_gs(-13_200, 500) == -13_000

    def test_monto_negativo_mitad_exacta_fija_la_semantica_del_adr(self):
        # -13_250 mod 500 = 250; mitad exacta va "hacia arriba" (hacia +infinito,
        # no "alejándose de cero"): -13_250 -> -13_000. Ver ADR 0002 y plan §3.1.
        assert redondear_gs(-13_250, 500) == -13_000

    def test_montos_enteros(self):
        """RF-7: el resultado siempre es int, nunca float ni Decimal."""
        casos = [
            redondear_gs(13_300, 500),
            redondear_gs(13_200, 500),
            redondear_gs(13_250, 500),
            redondear_gs(-13_300, 500),
            redondear_gs(13_300, 1),
        ]
        for resultado in casos:
            assert type(resultado) is int


class TestCuadrarLineas:
    """RF-15 / ADR 0002 §3: la suma de las líneas debe igualar siempre al total.

    Firma exacta del plan §3.1: `cuadrar_lineas(total_objetivo: int,
    totales_linea: list[int]) -> list[int]`. El ajuste (positivo o negativo)
    cae siempre en la última línea, nunca se reparte ni se recalcula el total.
    """

    @pytest.mark.parametrize(
        "total_objetivo, totales_linea, esperado",
        [
            # Lista vacía con total 0: no hay líneas que cuadrar.
            pytest.param(0, [], [], id="lista_vacia_total_cero"),
            # Una sola línea: el ajuste, si lo hay, cae en esa única línea.
            pytest.param(13_500, [13_300], [13_500], id="una_linea_con_ajuste"),
            pytest.param(13_500, [13_500], [13_500], id="una_linea_sin_ajuste"),
            # Frontera exacta: la última línea puede quedar en 0 (permitido
            # por el invariante >= 0), no debe levantar.
            pytest.param(30_000, [30_000, 5_000], [30_000, 0], id="ultima_linea_en_cero"),
            # N líneas, suma original MENOR al total redondeado (diferencia
            # positiva a repartir en la última línea).
            pytest.param(
                100_000,
                [30_000, 30_000, 30_000],
                [30_000, 30_000, 40_000],
                id="n_lineas_diferencia_positiva",
            ),
            # N líneas, suma original MAYOR al total redondeado (diferencia
            # negativa: se resta en la última línea).
            pytest.param(
                89_000,
                [30_000, 30_000, 30_000],
                [30_000, 30_000, 29_000],
                id="n_lineas_diferencia_negativa",
            ),
        ],
    )
    def test_lineas_suman_el_total_tras_redondeo(self, total_objetivo, totales_linea, esperado):
        resultado = cuadrar_lineas(total_objetivo, totales_linea)
        assert resultado == esperado
        assert sum(resultado) == total_objetivo

    def test_lineas_suman_el_total_tras_redondeo_no_toca_las_lineas_anteriores(self):
        # El ajuste cae exclusivamente en la última línea (ADR 0002): las
        # líneas previas a la última quedan bit a bit sin modificar, y la
        # lista de entrada no se muta (cuadrar_lineas trabaja sobre copia).
        totales_linea = [12_345, 67_890, 11_111]
        original = list(totales_linea)
        resultado = cuadrar_lineas(100_000, totales_linea)
        assert resultado[:-1] == original[:-1]
        assert sum(resultado) == 100_000
        assert totales_linea == original

    def test_lineas_suman_el_total_tras_redondeo_no_deja_la_ultima_linea_negativa(self):
        # Si restar el faltante en la última línea la dejaría negativa, esto
        # es un error de datos (plan §3.1: "invariante ajustadas[-1] >= 0, si
        # no, es un error de datos"), no un caso silencioso a tolerar.
        #
        # Decisión de Rolando (2026-09-22, tras adelantar T5): `cuadrar_lineas`
        # levanta `ErrorDeNegocio` (no `ValueError` genérico) — coexiste con
        # `Resultado[T]`, no son mutuamente excluyentes (ver plan §1.2, nota
        # 2026-09-22, y shared/errors.py). El código es el contrato estable.
        with pytest.raises(ErrorDeNegocio) as exc_info:
            cuadrar_lineas(1_000, [50_000, 500])
        assert exc_info.value.codigo == "CUADRE_LINEA_NEGATIVA"
        assert exc_info.value.mensaje

    def test_lista_vacia_con_total_distinto_de_cero_es_error_de_datos(self):
        # Invariante del plan §3.1: lista vacía exige total_objetivo == 0. Un
        # total sin ninguna línea que lo respalde es un dato inconsistente.
        with pytest.raises(ErrorDeNegocio) as exc_info:
            cuadrar_lineas(13_500, [])
        assert exc_info.value.codigo == "CUADRE_SIN_LINEAS"
        assert exc_info.value.mensaje
