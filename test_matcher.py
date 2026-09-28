from parser import load_statement, load_sales_record
from matcher import exact_match, fuzzy_match

if __name__ == "__main__":
    # Load your real data — adjust these paths to match your actual files
    transactions_df = load_statement(r"C:\Users\Sean\Downloads\MPESA_Statement_2026-09-11_to_2026-08-11_254711706250.xlsx")
    sales_df = load_sales_record(r"C:\Users\Sean\Downloads\sales_record_expanded.csv")

    # --- Pass 1: exact matching ---
    exact_pairs, unmatched_txns, unmatched_sales = exact_match(transactions_df, sales_df)

    print("=== Exact Match Results ===")
    print(f"Exact matches: {len(exact_pairs)}")
    print(f"Still unmatched transactions: {len(unmatched_txns)}")
    print(f"Still unmatched sales: {len(unmatched_sales)}")

    # Show the actual matched pairs, not just counts
    if exact_pairs:
        print("\nMatched pairs (transaction amount <-> sale amount):")
        for t_idx, s_idx in exact_pairs:
            txn_amount = transactions_df.loc[t_idx, "amount"]
            sale_amount = sales_df.loc[s_idx, "amount"]
            sale_desc = sales_df.loc[s_idx, "description"]
            print(f"  KES {txn_amount} <-> KES {sale_amount} ({sale_desc})")

    # --- Pass 2: fuzzy matching on whatever's left over ---
    fuzzy_pairs = fuzzy_match(unmatched_txns, unmatched_sales)

    print("\n=== Fuzzy Match Results ===")
    print(f"Fuzzy (near-miss) matches: {len(fuzzy_pairs)}")

    if fuzzy_pairs:
        print("\nFuzzy matched pairs (transaction amount <-> sale amount, confidence):")
        for t_idx, s_idx, confidence in fuzzy_pairs:
            txn_amount = transactions_df.loc[t_idx, "amount"]
            sale_amount = sales_df.loc[s_idx, "amount"]
            sale_desc = sales_df.loc[s_idx, "description"]
            print(f"  KES {txn_amount} <-> KES {sale_amount} ({sale_desc}) — confidence: {confidence:.2f}")

    # --- Final tally: what's left truly unmatched after both passes ---
    fuzzy_txn_ids = {t for t, s, c in fuzzy_pairs}
    fuzzy_sale_ids = {s for t, s, c in fuzzy_pairs}

    still_unmatched_txns = unmatched_txns[~unmatched_txns.index.isin(fuzzy_txn_ids)]
    still_unmatched_sales = unmatched_sales[~unmatched_sales.index.isin(fuzzy_sale_ids)]

    print("\n=== Final Summary ===")
    print(f"Total exact matches: {len(exact_pairs)}")
    print(f"Total fuzzy matches: {len(fuzzy_pairs)}")
    print(f"Truly unmatched transactions (no sale found): {len(still_unmatched_txns)}")
    print(f"Truly unmatched sales (no payment found): {len(still_unmatched_sales)}")

    if not still_unmatched_txns.empty:
        print("\nUnmatched transactions (payment with no matching sale):")
        print(still_unmatched_txns[["completion_time", "details", "amount"]])

    if not still_unmatched_sales.empty:
        print("\nUnmatched sales (sale with no matching payment):")
        print(still_unmatched_sales[["sale_date", "description", "amount"]])