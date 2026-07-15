"""配置文件"""
import os
from datetime import datetime

# ============================================================
# RapidAPI 配置
# ============================================================
RAPIDAPI_KEY = "102f3bc64amsh7fab958ea93ff84p1bcf1fjsne0a3e5cca3fd"
RAPIDAPI_HOST = "skip-tracing-working-api.p.rapidapi.com"
RAPIDAPI_ENDPOINT = "https://skip-tracing-working-api.p.rapidapi.com/trace"

# ============================================================
# 文件配置
# ============================================================
INPUT_FILE = "input.xlsx"  # 输入的 XLSX 文件
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop")  # 输出到桌面
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# ============================================================
# 查询配置
# ============================================================
BATCH_SIZE = 10  # 每批查询的数量
DELAY_BETWEEN_REQUESTS = 1  # 请求间隔（秒）
TIMEOUT = 30  # 请求超时时间（秒）

# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "query.log"

# ============================================================
# 列名配置
# ============================================================
TODAY_DATE = datetime.now().strftime("%Y-%m-%d")  # 当日日期作为列名

# ============================================================
# 查询字段
# ============================================================
QUERY_FIELDS = {
    "name": "人物姓名",
    "age": "年龄",
    "property": "房产信息",
    "address": "准确地址",
    "phone": "电话号码"
}
