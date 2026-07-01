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
        """初始化浏览器 - 作为备用方案"""
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
            self.page.set_default_timeout(30000)
            
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
    
    def _is_verification_page(self, html: str) -> bool:
        """
        检查是否是验证页面而不是搜索结果
        优先检查是否有搜索结果，只有在没有结果且有验证关键词时才判定为验证页面
        """
        html_lower = html.lower()
        
        # 首先检查是否有搜索结果标志
        has_search_results = (
            "Approximate Age" in html or
            "Current Location" in html or
            "Used to Live" in html or
            "people in u.s." in html_lower or
            "people in" in html_lower and ("named" in html_lower or "age" in html_lower)
        )
        
        if has_search_results:
            logger.info("✓ 检测到搜索结果内容")
            return False
        
        # 如果没有搜索结果，再检查是否有验证页面标志
        verification_keywords = [
            "Performing security verification",
            "Incompatible browser",
            "security verification",
            "challenges.cloudflare",
            "just a moment"
        ]
        
        for keyword in verification_keywords:
            if keyword.lower() in html_lower:
                logger.warning(f"⚠️ 检测到验证页面关键词: {keyword}")
                return True
        
        # 检查 HTML 大小（验证页面通常较小）
        if len(html) < 3000:
            logger.warning(f"⚠️ HTML 内容较小 ({len(html)} 字节)，可能是验证页面")
            return True
        
        return False
    
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
            
            # 优先使用 cloudscraper
            if self.scraper:
                logger.info("使用 cloudscraper 进行请求...")
                page_content = self._fetch_with_cloudscraper(search_url)
                
                if page_content:
                    # 检查是否是验证页面
                    if self._is_verification_page(page_content):
                        logger.warning("⚠️ cloudscraper 返回验证页面，切换到浏览器模式...")
                    else:
                        logger.info("✓ 获取到真实搜索结果，解析中...")
                        results = self._extract_results_from_html(page_content, name)
                        if results:
                            return results
            
            # 如果 cloudscraper 失败或返回验证页面，使用 Playwright
            logger.info("使用 Playwright 进行请求...")
            if not self.page:
                self.init_browser()
            
            self.page.goto(search_url, wait_until="networkidle")
            time.sleep(3)
            
            # 检查是否需要处理验证
            page_content = self.page.content()
            if self._is_verification_page(page_content):
                logger.warning("⚠️ 浏览器页面也是验证页面")
                logger.info("📌 需要手动完成 Cloudflare 验证")
                logger.info("等待用户完成验证... (按任何键继续)")
                input()
                time.sleep(2)
                page_content = self.page.content()
            
            results = self._extract_results_from_html(page_content, name)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _fetch_with_cloudscraper(self, url: str) -> str:
        """使用 cloudscraper 获取页面内容"""
        try:
            logger.info(f"用 cloudscraper 请求: {url}")
            
            headers = {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.scraper.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✓ 请求成功 (状态码: {response.status_code}, HTML长度: {len(response.text)} 字节)")
                
                # 输出 HTML 头部用于调试
                logger.debug(f"HTML 头部 (前 500 字): {response.text[:500]}")
                
                return response.text
            else:
                logger.warning(f"⚠️ 请求返回状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"cloudscraper 请求失败: {e}")
            return None
    
    def _extract_results_from_html(self, page_html: str, search_name: str) -> list:
        """
        从 HTML 内容提取结果
        """
        results = []
        
        try:
            logger.info("开始解析 HTML 内容...")
            logger.debug(f"HTML 长度: {len(page_html)} 字节")
            
            # 检查是否是验证页面
            if self._is_verification_page(page_html):
                logger.warning("⚠️ 页面是验证页面，不是搜索结果")
                return []
            
            # 检查是否有结果
            if "0 people" in page_html or "No results" in page_html or "404" in page_html:
                logger.info(f"未找到 '{search_name}' 的搜索结果")
                return []
            
            # 检查是否有 "Approximate Age"
            if "Approximate Age" not in page_html:
                logger.warning("⚠️ 页面中未找到 'Approximate Age'")
                logger.debug(f"页面内容片段: {page_html[1000:2000]}")
                return []
            
            logger.info("✓ 页面中找到 'Approximate Age'")
            
            # 使用正则表达式提取结果项
            # 查找包含名字和年龄的模式
            pattern = r'<h3[^>]*>([^<]+)</h3>.*?Approximate Age[:\s]+(\d+)'
            matches = re.findall(pattern, page_html, re.DOTALL | re.IGNORECASE)
            
            logger.info(f"找到 {len(matches)} 个潜在结果")
            
            if len(matches) == 0:
                # 尝试另一种模式
                logger.debug("尝试备用的提取方式...")
                pattern = r'([A-Z][a-z]+ [A-Z][a-z]+).*?Approximate Age[:\s]+(\d+)'
                matches = re.findall(pattern, page_html, re.IGNORECASE)
                logger.info(f"备用方式找到 {len(matches)} 个结果")
            
            # 处理每个匹配
            for idx, (name, age_str) in enumerate(matches):
                try:
                    name = name.strip()
                    age = int(age_str)
                    
                    logger.debug(f"结果 {idx+1}: {name} (年龄: {age})")
                    
                    # 筛选年龄 53-75
                    if age < 53 or age > 75:
                        logger.debug(f"跳过: {name} (年龄: {age} 不在范围内)")
                        continue
                    
                    logger.info(f"✓ 符合条件: {name} (年龄: {age})")
                    
                    # 提取位置信息
                    location = self._extract_location_from_html(page_html, name)
                    
                    # 由于是静态 HTML，无法直接提取电话，需要访问详情页
                    # 暂时保存基本信息
                    results.append({
                        "name": name,
                        "age": age,
                        "location": location,
                        "phone": "需要访问详情页"
                    })
                    
                except Exception as e:
                    logger.debug(f"处理结果 {idx+1} 出错: {e}")
                    continue
            
            logger.info(f"共提取 {len(results)} 个符合条件的结果")
            return results
            
        except Exception as e:
            logger.error(f"解析 HTML 出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_location_from_html(self, html: str, name: str) -> str:
        """从 HTML 中提取位置"""
        try:
            # 查找名字后面的位置信息
            pattern = f"{name}.*?(?:Current Location|Location)[:\\s]+([^<\\n]+)"
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                location = match.group(1).strip()
                # 清理 HTML 标签
                location = re.sub(r'<[^>]+>', '', location)
                return location
        except:
            pass
        
        return "Unknown"
    
    def search_by_name_with_details(self, name: str) -> list:
        """
        按名字搜索并获取详细信息（包括电话）
        """
        if not self.page:
            self.init_browser()
        
        results = []
        
        try:
            search_url = f"{self.search_url}/{name.replace(' ', '-').lower()}"
            logger.info(f"正在搜索(含详情): {name}")
            
            self.page.goto(search_url, wait_until="networkidle")
            time.sleep(3)
            
            # 检查是否需要处理验证
            page_content = self.page.content()
            if self._is_verification_page(page_content):
                logger.warning("⚠️ 需要手动完成验证")
                logger.info("等待用户完成验证... (按任何键继续)")
                input()
                time.sleep(2)
                page_content = self.page.content()
            
            if "Approximate Age" not in page_content:
                logger.warning("⚠️ 页面中未找到搜索结果")
                return []
            
            # 查找所有结果项
            result_divs = self.page.query_selector_all("div[class*='result']")
            if not result_divs:
                result_divs = self.page.query_selector_all("div")
            
            logger.info(f"找到 {len(result_divs)} 个可能的结果项")
            
            for idx, div in enumerate(result_divs):
                try:
                    div_text = div.inner_text()
                    
                    if "Approximate Age" not in div_text:
                        continue
                    
                    # 提取名字
                    name_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', div_text)
                    if not name_match:
                        continue
                    
                    person_name = name_match.group(1)
                    
                    # 提取年龄
                    age_match = re.search(r'Approximate Age[:\s]+(\d+)', div_text)
                    if not age_match:
                        continue
                    
                    age = int(age_match.group(1))
                    
                    if age < 53 or age > 75:
                        continue
                    
                    logger.info(f"✓ 找到: {person_name} (年龄: {age})")
                    
                    # 查找 View All Info 按钮
                    button = div.query_selector("button, a")
                    if not button:
                        continue
                    
                    # 点击按钮打开详情页
                    try:
                        with self.page.context.expect_page() as new_page_info:
                            button.click()
                        
                        detail_page = new_page_info.value
                        time.sleep(2)
                        
                        # 检查详情页是否需要验证
                        detail_content = detail_page.content()
                        if self._is_verification_page(detail_content):
                            logger.warning("⚠️ 详情页需要验证")
                            logger.info("等待验证完成... (按任何键继续)")
                            input()
                            time.sleep(2)
                        
                        # 提取电话
                        phones = self._extract_phones_from_detail_page(detail_page)
                        
                        if phones:
                            for phone in phones:
                                results.append({
                                    "name": person_name,
                                    "age": age,
                                    "phone": phone
                                })
                                logger.info(f"✓ 保存: {person_name} - {phone}")
                        
                        detail_page.close()
                    except Exception as e:
                        logger.debug(f"处理详情页出错: {e}")
                        continue
                    
                except Exception as e:
                    logger.debug(f"处理结果项出错: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def _extract_phones_from_detail_page(self, page) -> list:
        """从详情页提取电话号码"""
        phones = []
        
        try:
            page_text = page.content()
            
            # 查找所有包含 "Wireless" 或 "Mobile" 的元素
            phone_elements = page.query_selector_all("span, div, td")
            
            for elem in phone_elements:
                try:
                    elem_text = elem.inner_text()
                    
                    if "Wireless" in elem_text or "Mobile" in elem_text:
                        # 提取电话号码
                        phone_match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', elem_text)
                        if phone_match:
                            phone = phone_match.group(0)
                            if phone not in phones:
                                phones.append(phone)
                                logger.info(f"  ✓ 找到电话: {phone}")
                except:
                    continue
            
            return phones
        except Exception as e:
            logger.debug(f"提取电话出错: {e}")
            return []
