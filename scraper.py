import logging
import re
import time
import json
from typing import List, Dict
from playwright.sync_api import sync_playwright, TimeoutError

logger = logging.getLogger(__name__)

# 尝试导入 cloudscraper
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    logger.warning("⚠️ cloudscraper 未安装，将使用 Playwright")

class PeopleSearchNameScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.context = None
        self.base_url = "https://www.peoplesearchnow.com"
        self.search_url = "https://www.peoplesearchnow.com/person"
        self.scraper = None
        
        # 初始化 cloudscraper
        if CLOUDSCRAPER_AVAILABLE:
            try:
                self.scraper = cloudscraper.create_scraper()
                logger.info("✓ cloudscraper 已初始化")
            except Exception as e:
                logger.warning(f"⚠️ cloudscraper 初始化失败: {e}")
                self.scraper = None
        
    def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = sync_playwright().start()
            
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = self.context.new_page()
            self.page.set_default_timeout(60000)  # 增加超时时间
            
            self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1'
            })
            
            logger.info("✓ 浏览器已启动")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            raise
        
    def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.debug("浏览器已关闭")
        except Exception as e:
            logger.debug(f"关闭浏览器时出错: {e}")
    
    def search_by_name(self, name: str) -> list:
        """
        按名字搜索
        返回符合条件的结果列表
        """
        results = []
        
        try:
            # 构造搜索 URL
            search_url = f"{self.search_url}/{name.replace(' ', '-').lower()}"
            logger.info(f"正在搜索: {name}")
            logger.info(f"访问 URL: {search_url}")
            
            # 使用 Playwright 打开页面（必须渲染 JavaScript）
            if not self.page:
                self.init_browser()
            
            logger.info("使用 Playwright 打开页面...")
            self.page.goto(search_url, wait_until="domcontentloaded")
            
            # 等待搜索结果 DOM 元素出现
            logger.info("等待搜索结果加载...")
            try:
                self.page.wait_for_selector("div:has-text('Approximate Age')", timeout=15000)
                logger.info("✓ 搜索结果已加载")
            except TimeoutError:
                logger.warning("⚠️ 等待结果超时，继续处理...")
            
            time.sleep(2)
            
            # 从 DOM 直接提取结果
            results = self._extract_results_from_dom(name)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_results_from_dom(self, search_name: str) -> list:
        """
        从 DOM 中直接提取搜索结果
        """
        results = []
        
        try:
            logger.info("开始从 DOM 提取结果...")
            
            # 获取所有包含 "Approximate Age" 文本的结果卡片
            result_cards = self.page.query_selector_all("div")
            
            logger.info(f"页面总共有 {len(result_cards)} 个 div 元素")
            
            processed_count = 0
            
            for card in result_cards:
                try:
                    card_text = card.inner_text()
                    
                    # 检查是否包含 "Approximate Age"
                    if "Approximate Age" not in card_text:
                        continue
                    
                    # 提取名字 - 查找 h3 或第一个粗体文本
                    name_elem = card.query_selector("h3, .name, [class*='name']")
                    person_name = None
                    
                    if name_elem:
                        person_name = name_elem.inner_text().strip()
                    else:
                        # 从文本中提取名字（通常是第一行）
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 3 and line[0].isupper():
                                # 检查是否像一个名字
                                if re.match(r'^[A-Z][a-z]+ [A-Z]', line):
                                    person_name = line
                                    break
                    
                    if not person_name:
                        logger.debug("无法提取名字")
                        continue
                    
                    logger.debug(f"提取到名字: {person_name}")
                    
                    # 提取年龄
                    age_match = re.search(r'Approximate Age[:\s]+(\d+)', card_text, re.IGNORECASE)
                    if not age_match:
                        logger.debug(f"未找到年龄")
                        continue
                    
                    age = int(age_match.group(1))
                    logger.debug(f"提取到年龄: {age}")
                    
                    # 筛选年龄 53-75
                    if age < 53 or age > 75:
                        logger.debug(f"跳过 {person_name} (年龄 {age} 不在范围内)")
                        continue
                    
                    logger.info(f"✓ 符合条件: {person_name} (年龄: {age})")
                    processed_count += 1
                    
                    # 提取位置
                    location_match = re.search(r'Current Location[:\s]+([^\n]+)', card_text, re.IGNORECASE)
                    location = location_match.group(1).strip() if location_match else "Unknown"
                    logger.debug(f"位置: {location}")
                    
                    # 查找 View All Info 按钮
                    button = card.query_selector("button:has-text('View All Info'), a:has-text('View All Info'), button, a")
                    
                    if not button:
                        logger.debug("未找到详情按钮")
                        continue
                    
                    # 点击按钮打开详情页
                    logger.debug("点击 View All Info 按钮...")
                    try:
                        with self.page.context.expect_page() as new_page_info:
                            button.click()
                        
                        detail_page = new_page_info.value
                        time.sleep(2)
                        
                        # 等待详情页加载
                        try:
                            detail_page.wait_for_selector("span:has-text('Wireless'), span:has-text('Mobile')", timeout=10000)
                        except:
                            pass
                        
                        # 提取电话
                        phones = self._extract_phones_from_detail_page(detail_page)
                        
                        if phones:
                            for phone in phones:
                                results.append({
                                    "name": person_name,
                                    "age": age,
                                    "location": location,
                                    "phone": phone
                                })
                                logger.info(f"✓ 保存: {person_name} (年龄: {age}) - {phone}")
                        else:
                            logger.debug(f"未找到 {person_name} 的 Wireless 电话")
                        
                        detail_page.close()
                    except Exception as e:
                        logger.debug(f"处理详情页出错: {e}")
                        continue
                    
                except Exception as e:
                    logger.debug(f"处理卡片出错: {e}")
                    continue
            
            logger.info(f"共处理 {processed_count} 个结果，提取 {len(results)} 个符合条件的记录")
            return results
            
        except Exception as e:
            logger.error(f"提取结果出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_phones_from_detail_page(self, page) -> list:
        """从详情页提取 Wireless 电话号码"""
        phones = []
        
        try:
            page_text = page.content()
            
            # 查找所有包含 "Wireless" 或 "Mobile" 的元素
            phone_elements = page.query_selector_all("span, div, td, tr")
            
            logger.debug(f"详情页总共有 {len(phone_elements)} 个元素")
            
            for elem in phone_elements:
                try:
                    elem_text = elem.inner_text()
                    
                    # 检查是否包含 "Wireless" 或 "Mobile"
                    if "Wireless" not in elem_text and "wireless" not in elem_text and "Mobile" not in elem_text and "mobile" not in elem_text:
                        continue
                    
                    logger.debug(f"找到包含 Wireless/Mobile 的元素: {elem_text[:100]}")
                    
                    # 提取电话号码
                    phone_match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', elem_text)
                    if phone_match:
                        phone = phone_match.group(0).strip()
                        if phone not in phones:
                            phones.append(phone)
                            logger.info(f"  ✓ 找到 Wireless 电话: {phone}")
                    else:
                        logger.debug(f"元素中没有找到电话号码格式")
                
                except Exception as e:
                    logger.debug(f"处理电话元素出错: {e}")
                    continue
            
            return phones
        except Exception as e:
            logger.debug(f"提取电话出错: {e}")
            return []
