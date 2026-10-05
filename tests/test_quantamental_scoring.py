"""Unit Tests for Quantamental Impact Scoring & Macro Transmission (Gate 1)."""

import os
import sys

# Add scripts directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(os.path.dirname(current_dir), "scripts")
sys.path.insert(0, scripts_dir)

from daily_updater import calculate_quantamental_metrics


def test_score_range_bounds():
    """Verify that impact score is strictly bounded in [1.0, 10.0]."""
    test_cases = [
        ("Acuerdo de paz en el Estrecho de Ormuz", "Casa Blanca", "geopolitica_energia"),
        ("Declaración aislada de funcionario menor", "Blog Local", "mexico_banxico"),
        ("Reserva Federal recorta tasas de interés de emergencia", "Federal Reserve", "eeuu_fed"),
        ("Comentario genérico de fin de semana", "Medio X", "global_brics"),
    ]
    for title, source, channel in test_cases:
        res = calculate_quantamental_metrics(title, source, channel)
        assert 1.0 <= res["impact_score"] <= 10.0, f"Score out of bounds: {res['impact_score']}"
        assert res["impact_level"] in ["CRÍTICO", "ALTO", "MODERADO", "SEGUIMIENTO"]
        assert res["impact_badge"] in ["badge-critico", "badge-alto", "badge-moderado", "badge-bajo"]


def test_geopolitical_shock_direction_and_transmission():
    """Verify war escalations in Hormuz get ALCISTA_DOLAR and appropriate transmission."""
    title = "Escala guerra y bombardeo en el Estrecho de Ormuz con bloqueo petrolero"
    source = "Reuters"
    res = calculate_quantamental_metrics(title, source, "geopolitica_energia")
    assert res["direction"] == "ALCISTA_DOLAR"
    assert res["impact_score"] >= 7.5
    assert "Tensión militar o riesgo" in res["transmission"]


def test_monetary_easing_direction_and_transmission():
    """Verify Fed rate cuts trigger BAJISTA_DOLAR for USD/MXN."""
    title = "Reserva Federal anuncia recorte de tasa de interés para estimular la economía"
    source = "Federal Reserve"
    res = calculate_quantamental_metrics(title, source, "eeuu_fed")
    assert res["direction"] == "BAJISTA_DOLAR"
    assert res["impact_score"] >= 8.0
    assert "Señales de relajación monetaria" in res["transmission"]


def test_local_fiscal_and_reform_direction():
    """Verify local constitutional reform risk triggers sovereign risk caution."""
    title = "Presión cambiaria ante debate de reforma judicial en México"
    source = "El Economista"
    res = calculate_quantamental_metrics(title, source, "mexico_banxico")
    assert res["direction"] == "ALCISTA_DOLAR"
    assert "Riesgo legislativo, fiscal" in res["transmission"]


if __name__ == "__main__":
    test_score_range_bounds()
    test_geopolitical_shock_direction_and_transmission()
    test_monetary_easing_direction_and_transmission()
    test_local_fiscal_and_reform_direction()
    print("ALL 4 QUANTAMENTAL TESTS PASS DETERMINISTICALLY (100% SUCCESS).")
