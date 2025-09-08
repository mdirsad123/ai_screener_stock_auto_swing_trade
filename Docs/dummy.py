from db_connection import get_db_connection

def save_stock_data(symbol, date, open_p, high_p, low_p, close_p, volume):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """INSERT INTO stock_prices 
             (symbol, date, open_price, high_price, low_price, close_price, volume) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(sql, (symbol, date, open_p, high_p, low_p, close_p, volume))
    conn.commit()
    cursor.close()
    conn.close()
