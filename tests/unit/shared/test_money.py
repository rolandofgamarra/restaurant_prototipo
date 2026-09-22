"""Tests unitarios de shared/money.py — RF-7, RF-11.

ADR 0002: un único punto de redondeo (`redondear_gs`), sin `Decimal` ni `float`,
aserciones exactas de dinero (nunca `pytest.approx`). Estos tests se escriben y
corren en rojo ANTES de que exista `src/shared/money.py` (plan §5.3).
"""

from src.shared.money import redondear_gs


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
