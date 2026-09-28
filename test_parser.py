from parser import load_statement, load_sales_record

if __name__ == "__main__":
    statement_df = load_statement(r"C:\Users\Sean\Downloads\MPESA_Statement_2026-09-11_to_2026-08-11_254711706250.xlsx")
    print("Statement loaded successfully:")
    print(statement_df.head())

    try:
        sales_df = load_sales_record(r"C:\Users\Sean\Downloads\sales_record_expanded.csv")
        print("Sales loaded successfully:")
        print(sales_df.head())
    except ValueError as e:
        print(f"Sales file failed to load: {e}")