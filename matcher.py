import pandas as pd

def exact_match(transactions_df, sales_df, date_window_days=1):
    """
    Matches transactions to sales by amount (exact) and date proximity.
    Returns three lists: matched pairs, unmatched transactions, unmatched sales.
    """
    matched_pairs = []
    used_sale_indices = set()

    # Only consider incoming money for sales matching (positive amounts)
    incoming = transactions_df[transactions_df["amount"] > 0].copy()

    for t_idx, txn in incoming.iterrows():
        best_match_idx = None

        for s_idx, sale in sales_df.iterrows():
            if s_idx in used_sale_indices:
                continue

            amount_matches = abs(txn["amount"] - sale["amount"]) < 0.01  # exact, allow float rounding
            date_diff = abs((txn["completion_time"].date() - sale["sale_date"].date()).days)
            date_matches = date_diff <= date_window_days

            if amount_matches and date_matches:
                best_match_idx = s_idx
                break  # first exact match wins for now — good enough for MVP

        if best_match_idx is not None:
            matched_pairs.append((t_idx, best_match_idx))
            used_sale_indices.add(best_match_idx)

    matched_txn_ids = {t for t, s in matched_pairs}
    matched_sale_ids = {s for t, s in matched_pairs}

    unmatched_transactions = incoming[~incoming.index.isin(matched_txn_ids)]
    unmatched_sales = sales_df[~sales_df.index.isin(matched_sale_ids)]

    return matched_pairs, unmatched_transactions, unmatched_sales
def fuzzy_match(unmatched_transactions, unmatched_sales, amount_tolerance=10, date_window_days=2):
    """Second pass: looser amount tolerance and wider date window."""
    fuzzy_pairs = []
    used_sale_indices = set()

    for t_idx, txn in unmatched_transactions.iterrows():
        best_match = None
        best_diff = amount_tolerance + 1

        for s_idx, sale in unmatched_sales.iterrows():
            if s_idx in used_sale_indices:
                continue

            amount_diff = abs(txn["amount"] - sale["amount"])
            date_diff = abs((txn["completion_time"].date() - sale["sale_date"].date()).days)

            if amount_diff <= amount_tolerance and date_diff <= date_window_days:
                if amount_diff < best_diff:
                    best_diff = amount_diff
                    best_match = s_idx

        if best_match is not None:
            confidence = 1 - (best_diff / amount_tolerance)  # closer amount = higher confidence
            fuzzy_pairs.append((t_idx, best_match, confidence))
            used_sale_indices.add(best_match)

    return fuzzy_pairs
def summarize(transactions_df, exact_pairs, fuzzy_pairs, unmatched_txns, unmatched_sales):
    total_incoming = transactions_df[transactions_df["amount"] > 0]["amount"].sum()
    matched_value = sum(transactions_df.loc[t, "amount"] for t, s in exact_pairs)
    matched_value += sum(transactions_df.loc[t, "amount"] for t, s, c in fuzzy_pairs)

    total_matches = len(exact_pairs) + len(fuzzy_pairs)
    total_considered = total_matches + len(unmatched_txns)

    return {
        "total_incoming_ksh": round(total_incoming, 2),
        "matched_count": total_matches,
        "exact_matches": len(exact_pairs),
        "fuzzy_matches": len(fuzzy_pairs),
        "unmatched_transactions": len(unmatched_txns),
        "unmatched_sales": len(unmatched_sales),
        "match_rate_pct": round((total_matches / total_considered) * 100, 1) if total_considered else 0,
        "unexplained_value_ksh": round(total_incoming - matched_value, 2),
    }