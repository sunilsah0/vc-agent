"""Deterministic finance formulas. Every function returns a Result with the
value, the inputs used and warnings. Missing inputs give value=None, never a guess."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence


@dataclass(frozen=True)
class Result:
    name: str
    value: Optional[float]
    formula: str
    inputs: dict[str, Any]
    warnings: tuple[str, ...] = ()


def _calc(name: str, formula: str, inputs: dict[str, Any],
          fn: Callable[..., float], nonzero: Sequence[str] = ()) -> Result:
    missing = [k for k, v in inputs.items() if v is None]
    if missing:
        return Result(name, None, formula, inputs,
                      (f"Missing input(s): {', '.join(missing)}. Not calculated.",))
    zero = [k for k in nonzero if inputs[k] == 0]
    if zero:
        return Result(name, None, formula, inputs,
                      (f"{', '.join(zero)} is zero, so this cannot be calculated.",))
    return Result(name, fn(**inputs), formula, inputs)


def gross_margin(revenue, cogs):
    return _calc("Gross Margin", "(Revenue - COGS) / Revenue",
                 dict(revenue=revenue, cogs=cogs),
                 lambda revenue, cogs: (revenue - cogs) / revenue, ["revenue"])


def ebitda_margin(ebitda, revenue):
    return _calc("EBITDA Margin", "EBITDA / Revenue", dict(ebitda=ebitda, revenue=revenue),
                 lambda ebitda, revenue: ebitda / revenue, ["revenue"])


def net_margin(net_income, revenue):
    return _calc("Net Margin", "Net Income / Revenue",
                 dict(net_income=net_income, revenue=revenue),
                 lambda net_income, revenue: net_income / revenue, ["revenue"])


def cac(sales_marketing_cost, new_customers):
    return _calc("CAC", "Sales & Marketing Cost / New Customers",
                 dict(sales_marketing_cost=sales_marketing_cost, new_customers=new_customers),
                 lambda sales_marketing_cost, new_customers: sales_marketing_cost / new_customers,
                 ["new_customers"])


def ltv(arpu_monthly, gross_margin_pct, monthly_churn):
    """Assumption: lifetime = 1 / monthly churn (simple subscription model)."""
    r = _calc("LTV", "ARPU x Gross Margin / Monthly Churn",
              dict(arpu_monthly=arpu_monthly, gross_margin_pct=gross_margin_pct,
                   monthly_churn=monthly_churn),
              lambda arpu_monthly, gross_margin_pct, monthly_churn:
              arpu_monthly * gross_margin_pct / monthly_churn, ["monthly_churn"])
    if r.value is None:
        return r
    return Result(r.name, r.value, r.formula, r.inputs,
                  ("Assumes customer lifetime = 1 / monthly churn; churn is constant.",))


def ltv_cac(ltv_value, cac_value):
    return _calc("LTV:CAC", "LTV / CAC", dict(ltv_value=ltv_value, cac_value=cac_value),
                 lambda ltv_value, cac_value: ltv_value / cac_value, ["cac_value"])


def cac_payback_months(cac_value, arpu_monthly, gross_margin_pct):
    return _calc("CAC Payback (months)", "CAC / (ARPU x Gross Margin)",
                 dict(cac_value=cac_value, arpu_monthly=arpu_monthly,
                      gross_margin_pct=gross_margin_pct),
                 lambda cac_value, arpu_monthly, gross_margin_pct:
                 cac_value / (arpu_monthly * gross_margin_pct), ["arpu_monthly", "gross_margin_pct"])


def nrr(starting_recurring_revenue, expansion, contraction, churn):
    return _calc("NRR", "(Start + Expansion - Contraction - Churn) / Start",
                 dict(starting_recurring_revenue=starting_recurring_revenue,
                      expansion=expansion, contraction=contraction, churn=churn),
                 lambda starting_recurring_revenue, expansion, contraction, churn:
                 (starting_recurring_revenue + expansion - contraction - churn)
                 / starting_recurring_revenue, ["starting_recurring_revenue"])


def net_burn(cash_outflows, cash_inflows):
    return _calc("Net Burn", "Cash Outflows - Cash Inflows",
                 dict(cash_outflows=cash_outflows, cash_inflows=cash_inflows),
                 lambda cash_outflows, cash_inflows: cash_outflows - cash_inflows)


def runway_months(cash_available, monthly_net_burn):
    r = _calc("Runway (months)", "Cash Available / Monthly Net Burn",
              dict(cash_available=cash_available, monthly_net_burn=monthly_net_burn),
              lambda cash_available, monthly_net_burn:
              cash_available / monthly_net_burn if monthly_net_burn > 0 else float("inf"))
    if r.value == float("inf"):
        return Result(r.name, None, r.formula, r.inputs,
                      ("Net burn is zero or negative: company is not burning cash.",))
    return r


def enterprise_value(equity_value, debt, cash):
    return _calc("Enterprise Value", "Equity Value + Debt - Cash",
                 dict(equity_value=equity_value, debt=debt, cash=cash),
                 lambda equity_value, debt, cash: equity_value + debt - cash)


def equity_value(ev, net_debt):
    return _calc("Equity Value", "Enterprise Value - Net Debt", dict(ev=ev, net_debt=net_debt),
                 lambda ev, net_debt: ev - net_debt)


def ev_revenue(ev, revenue):
    return _calc("EV/Revenue", "EV / Revenue", dict(ev=ev, revenue=revenue),
                 lambda ev, revenue: ev / revenue, ["revenue"])


def ev_ebitda(ev, ebitda):
    r = _calc("EV/EBITDA", "EV / EBITDA", dict(ev=ev, ebitda=ebitda),
              lambda ev, ebitda: ev / ebitda, ["ebitda"])
    if r.value is not None and r.value < 0:
        return Result(r.name, None, r.formula, r.inputs,
                      ("EBITDA is negative, so the multiple is not meaningful.",))
    return r


def rule_of_40(revenue_growth_pct, profit_margin_pct):
    return _calc("Rule of 40", "Revenue Growth % + Profit Margin %",
                 dict(revenue_growth_pct=revenue_growth_pct, profit_margin_pct=profit_margin_pct),
                 lambda revenue_growth_pct, profit_margin_pct:
                 revenue_growth_pct + profit_margin_pct)


def debt_ebitda(debt, ebitda):
    return _calc("Debt/EBITDA", "Debt / EBITDA", dict(debt=debt, ebitda=ebitda),
                 lambda debt, ebitda: debt / ebitda, ["ebitda"])


def interest_coverage(ebit, interest_expense):
    return _calc("Interest Coverage", "EBIT / Interest Expense",
                 dict(ebit=ebit, interest_expense=interest_expense),
                 lambda ebit, interest_expense: ebit / interest_expense, ["interest_expense"])


def roi(gain, cost):
    return _calc("ROI", "Gain from Investment / Investment Cost", dict(gain=gain, cost=cost),
                 lambda gain, cost: gain / cost, ["cost"])


def moic(total_received, total_invested):
    return _calc("MOIC", "Total Cash Received / Total Cash Invested",
                 dict(total_received=total_received, total_invested=total_invested),
                 lambda total_received, total_invested: total_received / total_invested,
                 ["total_invested"])


def irr(cash_flows: Optional[Sequence[float]], periods_per_year: int = 1) -> Result:
    """Rate where NPV = 0, found by bisection. cash_flows[0] is usually negative."""
    inp = dict(cash_flows=list(cash_flows) if cash_flows is not None else None)
    if cash_flows is None or len(cash_flows) < 2:
        return Result("IRR", None, "rate where NPV of cash flows = 0", inp,
                      ("Need at least two cash flows.",))
    if not (any(c < 0 for c in cash_flows) and any(c > 0 for c in cash_flows)):
        return Result("IRR", None, "rate where NPV of cash flows = 0", inp,
                      ("Need both an outflow and an inflow; IRR undefined.",))

    def npv(rate: float) -> float:
        return sum(c / (1 + rate) ** i for i, c in enumerate(cash_flows))

    lo, hi = -0.99, 100.0
    if npv(lo) * npv(hi) > 0:
        return Result("IRR", None, "rate where NPV of cash flows = 0", inp,
                      ("No IRR found in range.",))
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if npv(lo) * npv(mid) > 0 else (lo, mid)
    period_rate = (lo + hi) / 2
    return Result("IRR", (1 + period_rate) ** periods_per_year - 1,
                  "rate where NPV of cash flows = 0", inp)


def dcf(cash_flows: Optional[Sequence[float]], discount_rate: Optional[float],
        terminal_growth: Optional[float]) -> Result:
    """EV = sum(CF_t / (1+r)^t) + TV/(1+r)^n, TV = CF_n x (1+g) / (r-g)."""
    inp = dict(cash_flows=list(cash_flows) if cash_flows is not None else None,
               discount_rate=discount_rate, terminal_growth=terminal_growth)
    f = "sum(CF_t/(1+r)^t) + TV/(1+r)^n"
    if cash_flows is None or not cash_flows or discount_rate is None or terminal_growth is None:
        return Result("DCF", None, f, inp, ("Missing cash flows, discount rate or growth.",))
    if discount_rate <= terminal_growth:
        return Result("DCF", None, f, inp, ("Discount rate must exceed terminal growth.",))
    n = len(cash_flows)
    pv = sum(c / (1 + discount_rate) ** (i + 1) for i, c in enumerate(cash_flows))
    tv = cash_flows[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    return Result("DCF", pv + tv / (1 + discount_rate) ** n, f, inp,
                  ("Terminal value is usually the largest part; test sensitivity.",))