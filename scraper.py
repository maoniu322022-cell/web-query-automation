import logging
import re
import time
from playwright.sync_api import sync_playwright, TimeoutError

logger = logging.getLogger(__name__)

class PeopleSearchNameScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.context = None
        self.base_url = "https://www.peoplesearchnow.com"
        self.search_url = "https://www.peoplesearchnow.com/person"
        
    def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_default_timeout(30000)
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
        
        # 初始化浏览器
        if not self.page:
            self.init_browser()
        
        try:
            # 访问搜索页面
            # URL 格式: https://www.peoplesearchnow.com/person/{name-with-dashes}
            search_url = f"{self.search_url}/{name.replace(' ', '-').lower()}"
            logger.info(f"正在搜索: {name}")
            logger.info(f"访问 URL: {search_url}")
            
            self.page.goto(search_url, wait_until="commit")
            
            # 等待页面加载
            try:
                self.page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass
            
            time.sleep(2)
            
            # 检查是否需要处理 Error 1015
            self._handle_error_1015()
            
            time.sleep(1)
            
            # 检查是否有真正的错误页面（JSON 错误响应）
            page_text = self.page.content()
            
            # 只检查真正的错误 JSON 响应
            if "{" in page_text and "error" in page_text.lower() and "validation_failed" in page_text:
                logger.warning("⚠️ 服务器返回错误")
                logger.debug(f"错误内容: {page_text[:200]}")
                return []
            
            # 检查是否有结果
            if "0 people" in page_text or "No results" in page_text or "404" in page_text:
                logger.info(f"未找到 '{name}' 的搜索结果")
                return []
            
            # 获取当前页面的所有结果
            page_num = 1
            max_pages = 5  # 最多处理5页
            
            while page_num <= max_pages:
                logger.info(f"处理第 {page_num} 页")
                
                # 提取当前页的结果
                page_results = self._extract_results_from_page(name)
                results.extend(page_results)
                
                if not page_results:
                    logger.debug("当前页无结果")
                
                # 检查是否有下一页
                has_next = self._go_to_next_page()
                if not has_next:
                    logger.info(f"已到达最后一页")
                    break
                
                page_num += 1
                time.sleep(1)
            
            return results
            
        except TimeoutError:
            logger.error(f"页面加载超时")
            return []
        except Exception as e:
            logger.error(f"搜索出错: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            # 不关闭浏览器，保留给下一次使用
            pass
    
    def _handle_error_1015(self):
        """处理 Error 1015（限流）- 等待用户刷新后继续"""
        try:
            page_text = self.page.content()
            
            if "1015" in page_text:
                logger.warning("⚠️ 遇到 Error 1015 - 网站限流")
                logger.warning("请按照以下步骤操作:")
                logger.warning("1. 切换 VPN")
                logger.warning("2. 按 F5 刷新")
                logger.warning("3. 按 Enter 继续")
                input("按 Enter 继续...")
                
                # 等待页面刷新
                time.sleep(2)
        except Exception as e:
            logger.debug(f"处理 1015 错误时出错: {e}")
    
    def _extract_results_from_page(self, search_name: str) -> list:
        """
        从当前页提取结果
        """
        results = []
        
        try:
            # 等待结果加载
            time.sleep(1)
            
            # 尝试找到包含人物信息的容器
            # 根据网站结构，每个人物结果通常在一个独立的 div 或 card 中
            items = self.page.query_selector_all(
                "div[class*='result'], div[class*='person'], article, .profile-card, [class*='card']"
            )
            
            logger.info(f"找到 {len(items)} 个结果项")
            
            # 如果没找到结果，尝试其他选择器
            if len(items) == 0:
                logger.debug("尝试备选选择器...")
                items = self.page.query_selector_all("div")
                logger.info(f"尝试全部 div，找到 {len(items)} 个")
            
            for idx, item in enumerate(items):
                try:
                    item_text = item.inner_text()
                    
                    if not item_text or len(item_text.strip()) < 5:
                        continue
                    
                    # 检查是否包含年龄信息（这是判断是否是人物卡片的关键）
                    if "Approximate Age" not in item_text and "age" not in item_text.lower():
                        continue
                    
                    logger.debug(f"处理结果项 {idx+1}: {item_text[:150]}")
                    
                    # 提取名字 - 寻找加粗、橙色或标题标签
                    name_elem = item.query_selector("h3, h2, .name, strong, b, [style*='bold'], [style*='orange']")
                    if not name_elem:
                        name_elem = item.query_selector("a")
                    
                    if name_elem:
                        name = name_elem.text_content().strip()
                    else:
                        # 从整个文本中提取第一行作为名字
                        lines = item_text.split('\n')
                        name = lines[0].strip() if lines else "Unknown"
                    
                    if not name or len(name) < 2:
                        continue
                    
                    # 提取年龄 - 查找 "Approximate Age: XX" 模式
                    age = self._extract_age(item_text)
                    
                    logger.debug(f"名字: {name}, 年龄: {age}")
                    
                    # 筛选年龄 53-75
                    if not age or age < 53 or age > 75:
                        logger.debug(f"跳过: {name} (年龄: {age})")
                        continue
                    
                    # 提取位置
                    location_elem = item.query_selector(".location, .city, [class*='location']")
                    location = location_elem.text_content().strip() if location_elem else "Unknown"
                    
                    # 点击 "View All Info" 获取详细信息
                    view_info_btn = item.query_selector(
                        "button:has-text('View All Info'), a:has-text('View All Info'), [class*='view']:has-text('Info')"
                    )
                    
                    if view_info_btn:
                        try:
                            logger.debug(f"点击 View All Info 获取 {name} 的详情")
                            
                            # 在新标签页中打开
                            with self.page.context.expect_page() as new_page_info:
                                view_info_btn.click()
                            
                            detail_page = new_page_info.value
                            time.sleep(2)
                            
                            try:
                                # 提取 Wireless 电话
                                phones = self._extract_wireless_phones(detail_page)
                                
                                if phones:
                                    for phone in phones:
                                        results.append({
                                            "name": name,
                                            "age": age,
                                            "phone": phone,
                                            "location": location
                                        })
                                        logger.info(f"✓ 保存: {name} (年龄: {age}) - {phone}")
                                else:
                                    logger.debug(f"未找到 {name} 的 Wireless 电话")
                            finally:
                                detail_page.close()
                        except Exception as e:
                            logger.debug(f"处理详情页出错: {e}")
                            continue
                    else:
                        logger.debug(f"未找到 {name} 的 View All Info 按钮")
                    
                except Exception as e:
                    logger.debug(f"提取结果项出错: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"提取页面结果出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_wireless_phones(self, page) -> list:
        """
        从详情页提取 Wireless 电话
        """
        phones = []
        
        try:
            time.sleep(1)
            
            page_text = page.content()
            
            # 查找所有包含电话号码的元素
            phone_items = page.query_selector_all(
                ".phone-item, [class*='phone'], .number, .contact, span, div, tr, td"
            )
            
            logger.debug(f"在详情页找到 {len(phone_items)} 个可能的电话项")
            
            for item in phone_items:
                try:
                    item_text = item.inner_text()
                    
                    # 检查是否包含 "Wireless" 或 "Mobile"
                    if ("Wireless" in item_text or "wireless" in item_text or 
                        "Mobile" in item_text or "mobile" in item_text):
                        
                        # 提取电话号码
                        phone_num = self._extract_phone_number(item_text)
                        if phone_num and phone_num not in phones:
                            phones.append(phone_num)
                            logger.info(f"  ✓ 找到 Wireless 电话: {phone_num}")
                
                except Exception as e:
                    logger.debug(f"处理电话项出错: {e}")
                    continue
            
            return phones
            
        except Exception as e:
            logger.debug(f"提取电话出错: {e}")
            return []
    
    def _go_to_next_page(self) -> bool:
        """
        跳转到下一页
        返回 True 如果成功，False 如果已是最后一页
        """
        try:
            next_button = self.page.query_selector(
                "a.next, button.next, a[rel='next'], .pagination a:has-text('Next'), "
                "a[aria-label*='next'], .next-page, a:has-text('Next Page')"
            )
            
            if next_button:
                logger.debug("找到下一页按钮，点击中...")
                next_button.click()
                time.sleep(2)
                return True
            
            logger.debug("未找到下一页按钮")
            return False
            
        except Exception as e:
            logger.debug(f"获取下一页失败: {e}")
            return False
    
    def _extract_age(self, text: str) -> int:
        """
        从文本中提取年龄
        """
        try:
            # 尝试多种格式
            patterns = [
                r'Approximate\s+Age[:\s]+(\d+)',
                r'Age[:\s]+(\d+)',
                r'age\s*:?\s*(\d+)',
                r'年龄\s*:?\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    age = int(match.group(1))
                    if 10 < age < 120:  # 基本合理性检查
                        return age
        except:
            pass
        
        return None
    
    def _extract_phone_number(self, text: str) -> str:
        """
        从文本中提取电话号码
        """
        try:
            # 匹配格式: (123) 456-7890 或 123-456-7890 等
            patterns = [
                r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
                r'\d{3}[\s.-]?\d{3}[\s.-]?\d{4}',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    phone = match.group(0).strip()
                    return phone
        except:
            pass
        
        return None
