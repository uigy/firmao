# File: analysis/report_generation.py

import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenPyXLImage
from io import BytesIO
import logging

def generate_sales_report(df_transactions, df_products, report_path):
    """
    Generuje raport sprzedaży w formacie Excel z wizualizacjami.
    """
    try:
        # Tworzenie writer'a Excel
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            # Arkusz z transakcjami
            df_transactions.to_excel(writer, sheet_name='Transakcje', index=False)
            
            # Arkusz z produktami
            df_products.to_excel(writer, sheet_name='Produkty', index=False)
            
            # Podsumowanie sprzedaży
            sales_summary = df_transactions.groupby('product_id').agg(
                Total_Sales=pd.NamedAgg(column='amount', aggfunc='sum'),
                Total_Transactions=pd.NamedAgg(column='transaction_id', aggfunc='count')
            ).reset_index()
            
            # Łączenie z danymi produktów
            sales_summary = sales_summary.merge(df_products, left_on='product_id', right_on='id', how='left')
            sales_summary = sales_summary[['name', 'Total_Sales', 'Total_Transactions']]
            sales_summary.to_excel(writer, sheet_name='Podsumowanie Sprzedaży', index=False)
            
            # Tworzenie wykresu
            plt.figure(figsize=(10,6))
            plt.bar(sales_summary['name'], sales_summary['Total_Sales'], color='skyblue')
            plt.xlabel('Produkt')
            plt.ylabel('Łączna Sprzedaż')
            plt.title('Podsumowanie Sprzedaży Produktów')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Zapisywanie wykresu do obiektu BytesIO
            img_data = BytesIO()
            plt.savefig(img_data, format='png')
            plt.close()
            img_data.seek(0)
            
            # Ładowanie workbook'a
            writer.book = load_workbook(report_path)
            writer.sheets = {ws.title: ws for ws in writer.book.worksheets}
            
            # Dodawanie obrazu do arkusza 'Podsumowanie Sprzedaży'
            img = OpenPyXLImage(img_data)
            img.anchor = 'E2'  # Pozycja obrazu
            writer.sheets['Podsumowanie Sprzedaży'].add_image(img)
            
            writer.save()
        
        logging.info(f"Raport sprzedaży został pomyślnie wygenerowany: {report_path}")
        return True
    except Exception as e:
        logging.error(f"Błąd podczas generowania raportu sprzedaży: {e}")
        return False
