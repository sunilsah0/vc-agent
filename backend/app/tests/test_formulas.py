import pytest
from app import formulas as f


def test_margins():
    assert f.gross_margin(100, 40).value == pytest.approx(0.6)
    assert f.ebitda_margin(20, 100).value == pytest.approx(0.2)
    assert f.net_margin(-10, 100).value == pytest.approx(-0.1)


def test_missing_input_is_never_invented():
    r = f.gross_margin(None, 40)
    assert r.value is None and "Missing" in r.warnings[0]


def test_zero_division_flagged():
    assert f.cac(1000, 0).value is None


def test_cac_ltv():
    c = f.cac(10000, 50).value
    assert c == 200
    l = f.ltv(100, 0.8, 0.02)
    assert l.value == pytest.approx(4000) and l.warnings
    assert f.ltv_cac(l.value, c).value == pytest.approx(20)
    assert f.cac_payback_months(200, 100, 0.8).value == pytest.approx(2.5)


def test_nrr():
    assert f.nrr(1000, 200, 50, 100).value == pytest.approx(1.05)


def test_burn_runway():
    assert f.net_burn(150, 100).value == 50
    assert f.runway_months(600, 50).value == 12
    assert f.runway_months(600, -5).value is None


def test_valuation():
    assert f.enterprise_value(100, 30, 10).value == 120
    assert f.equity_value(120, 20).value == 100
    assert f.ev_revenue(120, 40).value == 3
    assert f.ev_ebitda(120, 10).value == 12
    assert f.ev_ebitda(120, -5).value is None


def test_credit_and_rule40():
    assert f.rule_of_40(50, -10).value == 40
    assert f.debt_ebitda(300, 100).value == 3
    assert f.interest_coverage(90, 30).value == 3


def test_returns():
    assert f.roi(50, 100).value == 0.5
    assert f.moic(300, 100).value == 3
    assert f.irr([-100, 0, 0, 200]).value == pytest.approx(2 ** (1 / 3) - 1, rel=1e-6)
    assert f.irr([-100, -50]).value is None


def test_dcf():
    r = f.dcf([100, 100], 0.10, 0.0)
    expected = 100 / 1.1 + 100 / 1.21 + (100 / 0.10) / 1.21
    assert r.value == pytest.approx(expected)
    assert f.dcf([100], 0.05, 0.05).value is None