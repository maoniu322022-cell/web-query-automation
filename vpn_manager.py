"""
VPN 管理模块 - 处理NordVPN和IP池代理
"""

import subprocess
import time
import requests
import random
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VPNManager:
    """VPN 管理类"""
    
    def __init__(self, vpn_type: str = 'nordvpn', config: dict = None):
        self.vpn_type = vpn_type
        self.config = config or {}
        self.is_connected = False
        
    def connect(self) -> bool:
        """连接VPN"""
        if self.vpn_type == 'nordvpn':
            return self._connect_nordvpn()
        elif self.vpn_type == 'ip_pool':
            return self._connect_ip_pool()
        return False
    
    def disconnect(self) -> bool:
        """断开VPN"""
        if self.vpn_type == 'nordvpn':
            return self._disconnect_nordvpn()
        return True
    
    def _connect_nordvpn(self) -> bool:
        """连接 NordVPN"""
        try:
            nordvpn_path = r'C:\Program Files\NordVPN\NordVPN.exe'
            result = subprocess.run([nordvpn_path, 'connect'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            if result.returncode == 0:
                logger.info("✓ NordVPN 已连接")
                self.is_connected = True
                time.sleep(2)
                return True
            else:
                logger.info(f"℃ NordVPN 信息: {result.stdout}")
                logger.error(f"✗ NordVPN 连接失败: {result.stderr}")
                return True
        except FileNotFoundError:
            logger.error(r"✗ 未找到 NordVPN，请确保已安装在: C:\Program Files\NordVPN")
            return False
        except Exception as e:
            logger.error(f"✗ NordVPN 连接错误: {e}")
            return False
    
    def _disconnect_nordvpn(self) -> bool:
        """断开 NordVPN"""
        try:
            nordvpn_path = r'C:\Program Files\NordVPN\NordVPN.exe'
            result = subprocess.run([nordvpn_path, 'disconnect'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                logger.info("✓ NordVPN 已断开")
                self.is_connected = False
                return True
            else:
                logger.info(f"℃ NordVPN 信息: {result.stdout}")
        except Exception as e:
            logger.error(f"✗ NordVPN 断开错误: {e}")
        return True
    
    def _connect_ip_pool(self) -> bool:
        """连接 IP池代理"""
        logger.info("✓ IP池代理已准备")
        self.is_connected = True
        return True
    
    def get_proxy(self) -> Optional[dict]:
        """获取当前代理设置"""
        if self.vpn_type == 'ip_pool' and self.config.get('ip_pool'):
            proxy_url = random.choice(self.config['ip_pool'])
            return {
                'http': proxy_url,
                'https': proxy_url,
            }
        return None
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            proxy = self.get_proxy()
            response = requests.get('https://api.ipify.org?format=json', 
                                   proxies=proxy,
                                   timeout=10)
            if response.status_code == 200:
                ip = response.json().get('ip')
                logger.info(f"✓ 连接测试成功，当前IP: {ip}")
                return True
        except Exception as e:
            logger.error(f"✗ 连接测试失败: {e}")
        return False


class ProxyManager:
    """代理管理类"""
    
    def __init__(self, ip_pool: list = None):
        self.ip_pool = ip_pool or []
        self.current_index = 0
    
    def get_next_proxy(self) -> Optional[dict]:
        """获取下一个代理"""
        if not self.ip_pool:
            return None
        
        proxy_url = self.ip_pool[self.current_index % len(self.ip_pool)]
        self.current_index += 1
        
        return {
            'http': proxy_url,
            'https': proxy_url,
        }
    
    def get_random_proxy(self) -> Optional[dict]:
        """获取随机代理"""
        if not self.ip_pool:
            return None
        
        proxy_url = random.choice(self.ip_pool)
        return {
            'http': proxy_url,
            'https': proxy_url,
        }
