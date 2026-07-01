import logging
from typing import List, Dict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from threading import Lock

logger = logging.getLogger(__name__)

# 全局锁，用于线程安全的结果保存
results_lock = Lock()

class DataHandler:
    def __init__(self, input_file="phones.txt", output_file="search_results.xlsx"):
        self.input_file = input_file
        self.output_file = output_file
    
    def load_phones(self, filename: str) -> List[str]:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                phones = [line.strip() for line in f if line.strip()]
            return phones
        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            return []
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return []
    
    def save_results(self, results: List[Dict], filename: str):
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Results"
            
            # 设置表头
            headers = ["Phone", "Name", "Age", "Location"]
            ws.append(headers)
            
            # 设置表头样式
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # 添加数据
            for result in results:
                ws.append([
                    result.get("phone", ""),
                    result.get("name", ""),
                    result.get("age", ""),
                    result.get("location", "")
                ])
            
            # 调整列宽
            ws.column_dimensions['A'].width = 15
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 10
            ws.column_dimensions['D'].width = 30
            
            wb.save(filename)
            logger.info(f"✓ Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
