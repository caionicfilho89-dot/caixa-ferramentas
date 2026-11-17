"""Motor real de Simulação de Amortização Extra (SAC/PRICE) e Comparador Financiamento vs Consórcio (comparador-credito)."""
import math


def simulate_loan_with_extra_amort(principal: float, annual_rate_pct: float, months: int,
                                   system: str = "SAC", monthly_extra: float = 0.0,
                                   mode: str = "prazo") -> dict:
    """
    Simula financiamento SAC ou PRICE com e sem amortização extraordinária mensal,
    calculando economia real de juros e meses cortados.
    """
    pv = float(principal)
    n = max(1, int(months))
    i_month = (1.0 + float(annual_rate_pct) / 100.0) ** (1.0 / 12.0) - 1.0
    extra = max(0.0, float(monthly_extra))
    sys_up = (system or "SAC").upper()

    def run_schedule(extra_val: float) -> tuple[list[dict], float]:
        bal = pv
        rem_n = n
        rows = []
        tot_interest = 0.0
        tot_paid = 0.0
        m_idx = 0

        while bal > 0.01 and m_idx < n * 2:
            m_idx += 1
            juros = bal * i_month
            if sys_up == "SAC":
                amort_normal = (pv / n) if mode == "prazo" else (bal / max(1, rem_n))
                amort_normal = min(bal, amort_normal)
                pmt_normal = amort_normal + juros
            else:
                if i_month > 0:
                    eff_n = max(1, rem_n) if mode != "prazo" else max(1, n - m_idx + 1)
                    if mode == "prazo" and m_idx == 1:
                        fixed_pmt = pv * (i_month * (1 + i_month) ** n) / ((1 + i_month) ** n - 1)
                    pmt_normal = fixed_pmt if mode == "prazo" else bal * (i_month * (1 + i_month) ** eff_n) / ((1 + i_month) ** eff_n - 1)
                else:
                    pmt_normal = bal / max(1, rem_n)
                amort_normal = max(0.0, min(bal, pmt_normal - juros))

            rem_after_normal = max(0.0, bal - amort_normal)
            amort_extra = min(rem_after_normal, extra_val)
            new_bal = rem_after_normal - amort_extra
            total_mes = amort_normal + juros + amort_extra

            tot_interest += juros
            tot_paid += total_mes
            rows.append({
                "month": m_idx,
                "installment": round(amort_normal + juros, 2),
                "interest": round(juros, 2),
                "amortization": round(amort_normal, 2),
                "extra": round(amort_extra, 2),
                "total_outflow": round(total_mes, 2),
                "balance": round(new_bal, 2),
            })
            bal = new_bal
            rem_n = max(1, rem_n - 1)

        return rows, round(tot_interest, 2)

    base_rows, base_interest = run_schedule(0.0)
    opt_rows, opt_interest = run_schedule(extra)

    return {
        "system": sys_up,
        "original_months": len(base_rows),
        "optimized_months": len(opt_rows),
        "months_saved": max(0, len(base_rows) - len(opt_rows)),
        "original_interest": base_interest,
        "optimized_interest": opt_interest,
        "interest_saved": round(max(0.0, base_interest - opt_interest), 2),
        "schedule": opt_rows,
        "base_schedule": base_rows,
    }


def compare_consorcio_vs_financiamento(asset_value: float, months: int,
                                       fin_annual_rate_pct: float,
                                       cons_admin_fee_pct: float,
                                       cons_reserve_fund_pct: float = 2.0,
                                       annual_inflation_incc_pct: float = 5.0) -> dict:
    """Compara custo total desembolsado entre Financiamento SAC e Consórcio reajustado anualmente pelo INCC/IPCA."""
    val = float(asset_value)
    n = max(1, int(months))
    fin = simulate_loan_with_extra_amort(val, fin_annual_rate_pct, n, "SAC", 0.0)
    fin_total = round(val + fin["original_interest"], 2)

    # Consórcio: parcela incide sobre carta + taxa adm + fundo de reserva, corrigida a cada 12 meses
    mult_fee = 1.0 + (float(cons_admin_fee_pct) + float(cons_reserve_fund_pct)) / 100.0
    infl = 1.0 + float(annual_inflation_incc_pct) / 100.0
    base_monthly = (val * mult_fee) / n
    cons_total = 0.0
    first_pmt = round(base_monthly, 2)
    last_pmt = first_pmt

    for m in range(n):
        year_idx = m // 12
        pmt = base_monthly * (infl ** year_idx)
        cons_total += pmt
        last_pmt = round(pmt, 2)

    return {
        "financiamento_total": fin_total,
        "financiamento_juros": fin["original_interest"],
        "consorcio_total": round(cons_total, 2),
        "consorcio_first_pmt": first_pmt,
        "consorcio_last_pmt": last_pmt,
        "difference": round(abs(fin_total - cons_total), 2),
        "cheaper": "Consórcio" if cons_total < fin_total else "Financiamento",
    }
