# ============================================================
# 配置文件
# ============================================================

# 文件配置
INPUT_FILE = 'phone_numbers.txt'
OUTPUT_FILE = 'search_results.xlsx'

# VPN 配置
VPN_TYPE = 'nordvpn'
NORDVPN_CONFIG = {
    'enabled': True,
    'protocol': 'OpenVPN',
    'obfuscate': True,
    'country': 'United States',
}

# IP 池配置
IP_POOL = []

# 延迟配置
REQUEST_DELAY_MIN = 2
REQUEST_DELAY_MAX = 8
SEARCH_DELAY = (2, 8)

# 重试配置
MAX_RETRIES = 3
TIMEOUT = 40

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = 'search.log'