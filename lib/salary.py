"""Compute salary breakup from company-configured components."""
from __future__ import annotations
from decimal import Decimal


def _to_dec(x) -> Decimal:
    if x is None: return Decimal(0)
    return Decimal(str(x))


def compute_breakup(components: list[dict], annual_ctc: float | int) -> dict:
    """
    components: rows from salary_components ordered by display_order.
        Each has: name, component_type ('earning'|'deduction'),
                  calc_type ('percent_of_ctc'|'percent_of_basic'|'fixed'|'formula'),
                  calc_value, formula_expr
    annual_ctc: number

    Returns dict with:
      'annual': [{name, type, amount}, ...]
      'monthly': [{name, type, amount}, ...]
      'totals': {gross_annual, gross_monthly, deductions_annual, net_annual, ctc_annual}
    Two-pass so percent_of_basic resolves after Basic is computed.
    """
    ctc = _to_dec(annual_ctc)
    resolved: dict[str, Decimal] = {}

    # Pass 1: ctc / fixed / formula (formula limited to ctc references)
    for c in components:
        ct = c["calc_type"]
        val = _to_dec(c.get("calc_value"))
        if ct == "percent_of_ctc":
            resolved[c["name"]] = (ctc * val / Decimal(100)).quantize(Decimal("1"))
        elif ct == "fixed":
            resolved[c["name"]] = val.quantize(Decimal("1"))
        elif ct == "formula":
            # very small sandbox: allow only digits, *,/,+,-,(,) and 'ctc'
            expr = (c.get("formula_expr") or "").lower()
            safe = expr.replace("ctc", str(ctc))
            if all(ch in "0123456789.+-*/() " for ch in safe):
                try:
                    resolved[c["name"]] = Decimal(str(eval(safe))).quantize(Decimal("1"))
                except Exception:
                    resolved[c["name"]] = Decimal(0)
            else:
                resolved[c["name"]] = Decimal(0)

    basic = resolved.get("Basic", Decimal(0))
    if basic == 0:
        # try case-insensitive find
        for k, v in resolved.items():
            if k.lower() == "basic":
                basic = v; break

    # Pass 2: percent_of_basic
    for c in components:
        if c["calc_type"] == "percent_of_basic":
            val = _to_dec(c.get("calc_value"))
            resolved[c["name"]] = (basic * val / Decimal(100)).quantize(Decimal("1"))

    annual_rows = []
    monthly_rows = []
    gross_a = Decimal(0); ded_a = Decimal(0)
    for c in components:
        amt = resolved.get(c["name"], Decimal(0))
        row = {"name": c["name"], "type": c["component_type"], "amount": float(amt)}
        annual_rows.append(row)
        monthly_rows.append({**row, "amount": float((amt / Decimal(12)).quantize(Decimal("1")))})
        if c["component_type"] == "earning":
            gross_a += amt
        else:
            ded_a += amt

    return {
        "annual": annual_rows,
        "monthly": monthly_rows,
        "totals": {
            "ctc_annual": float(ctc),
            "gross_annual": float(gross_a),
            "gross_monthly": float((gross_a / Decimal(12)).quantize(Decimal("1"))),
            "deductions_annual": float(ded_a),
            "net_annual": float(gross_a - ded_a),
            "net_monthly": float(((gross_a - ded_a) / Decimal(12)).quantize(Decimal("1"))),
        },
    }


def format_inr(n: float | int) -> str:
    """Format number in Indian comma style: 12,34,567."""
    try:
        n = int(round(float(n)))
    except Exception:
        return str(n)
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    last3 = s[-3:]
    rest = s[:-3]
    # group rest in 2s from the right
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return sign + ",".join(groups) + "," + last3
