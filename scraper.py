import time
import random
import logging
from typing import Dict, Optional
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class PeopleSearchNowScraper:
    def __init__(self, vpn_manager=None, proxy_manager=None, headers=None):
        self.playwright = None
        self.browser = None
        self.page = None
    
    def _ensure_browser(self):
        if self.browser is None:
            logger.info("Init Playwright browser (visible mode)...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            self.page = self.browser.new_page()
            self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
    
    def _format_phone(self, phone: str) -> str:
        phone = phone.strip()
        phone = re.sub(r'\D', '', phone)
        if len(phone) == 10:
            return f"{phone[0:3]}-{phone[3:6]}-{phone[6:10]}"
        elif len(phone) == 11 and phone[0] == "1":
            return f"{phone[1:4]}-{phone[4:7]}-{phone[7:11]}"
        return phone
    
    def search_by_phone(self, phone_number: str) -> Optional[Dict]:
        try:
            self._ensure_browser()
            
            delay = random.uniform(3, 6)
            logger.info(f"Wait {delay:.1f}s...")
            time.sleep(delay)
            
            formatted_phone = self._format_phone(phone_number)
            logger.info(f"Query: {formatted_phone}")
            
            search_url = f"https://www.peoplesearchnow.com/phone/{formatted_phone}"
            logger.info(f"Fetch: {search_url}")
            
            try:
                self.page.goto(search_url, wait_until="networkidle", timeout=120000)
            except:
                logger.warning("Timeout, trying with domcontentloaded...")
                self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            
            time.sleep(5)
            
            html = self.page.content()
            
            # 检查是否被限流 (Error 1015)
            if "Error 1015" in html or "You are being rate limited" in html:
                logger.error("❌ Rate limited! Error 1015 detected")
                logger.warning("⚠️  页面保留中... 请切换 VPN 节点")
                logger.warning("✅ 切换完成后，在浏览器按 F5 刷新页面，然后按 Enter 继续...")
                input("按 Enter 继续...")
                
                # 自动刷新页面
                logger.info("Refreshing page...")
                self.page.reload(wait_until="networkidle")
                time.sleep(5)
                html = self.page.content()
            
            logger.info(f"HTML length: {len(html)}")
            soup = BeautifulSoup(html, "html.parser")
            result = {"name": None, "age": None, "location": None, "phone": phone_number}
            
            logger.info("Extract name...")
            name_elem = soup.select_one("p[itemprop='name']")
            if name_elem:
                name_text = name_elem.get_text(strip=True)
                if name_text and len(name_text) > 2:
                    result["name"] = name_text
                    logger.info(f"Name: {result['name']}")
            
            logger.info("Extract age...")
            text = soup.get_text()
            age_match = re.search(r'Age[:\s]+(\d+)|(\d+)\s*years?\s*old', text, re.IGNORECASE)
            if age_match:
                age_val = age_match.group(1) or age_match.group(2)
                if age_val and 0 < int(age_val) < 150:
                    result["age"] = age_val
                    logger.info(f"Age: {result['age']}")
            
            logger.info("Extract location...")
            for elem in soup.find_all(['p', 'div', 'span', 'td']):
                text = elem.get_text(strip=True)
                if re.search(r',\s*[A-Z]{2}', text) and len(text) > 5 and len(text) < 200:
                    result["location"] = text
                    logger.info(f"Location: {text}")
                    break
            
            if result["name"]:
                logger.info("✓ Success")
                return result
            
            logger.warning("No data found")
            return None
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return None
    
    def close(self):
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
