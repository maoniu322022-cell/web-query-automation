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
            
            # 获取页面完整内容用于调试
            page_content = self.page.content()
            logger.debug(f"页面长度: {len(page_content)} 字节")
            
            # 检查是否有真正的错误 JSON 响应
            if "{" in page_content and "error" in page_content.lower() and "validation_failed" in page_content:
                logger.warning("⚠️ 服务器返回错误")
                return []
            
            # 检查是否有结果
            if "0 people" in page_content or "No results" in page_content or "404" in page_content:
                logger.info(f"未找到 '{name}' 的搜索结果")
                return []
            
            # 获取当前页面的所有结果
            page_num = 1
            max_pages = 5
            
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
        从当前页提取结果 - 使用多种策略
        """
        results = []
        
        try:
            time.sleep(1)
            
            page_text = self.page.content()
            
            # 调试：输出页面中包含 "Approximate Age" 的部分
            if "Approximate Age" in page_text:
                logger.info("✓ 页面中找到 'Approximate Age' 文本")
            else:
                logger.warning("⚠️ 页面中未找到 'Approximate Age' 文本")
            
            # 策略 1: 尝试找到包含年龄信息的所有元素
            logger.info("尝试提取包含年龄信息的结果项...")
            
            # 获取所有可能的容器
            all_divs = self.page.query_selector_all("div")
            logger.debug(f"页面总共有 {len(all_divs)} 个 div")
            
            # 过滤出包含 "Approximate Age" 的 div
            result_items = []
            for div in all_divs:
                try:
                    div_text = div.inner_text()
                    if "Approximate Age" in div_text and len(div_text) > 50:
                        result_items.append(div)
                except:
                    continue
            
            logger.info(f"找到 {len(result_items)} 个包含年龄信息的结果项")
            
            if len(result_items) == 0:
                logger.warning("未找到包含年龄信息的结果项")
                logger.debug(f"页面内容片段: {page_text[500:1000]}")
                return []
            
            # 处理每个结果项
            for idx, item in enumerate(result_items):
                try:
                    item_text = item.inner_text()
                    logger.debug(f"\n=== 处理结果项 {idx+1} ===")
                    logger.debug(f"内容: {item_text[:200]}")
                    
                    # 提取名字
                    name = self._extract_name_from_item(item, item_text)
                    if not name:
                        logger.debug(f"无法提取名字")
                        continue
                    
                    logger.debug(f"名字: {name}")
                    
                    # 提取年龄
                    age = self._extract_age(item_text)
                    logger.debug(f"年龄: {age}")
                    
                    # 筛选年龄 53-75
                    if not age or age < 53 or age > 75:
                        logger.debug(f"跳过: {name} (年龄: {age})")
                        continue
                    
                    logger.info(f"✓ 符合条件: {name} (年龄: {age})")
                    
                    # 提取位置
                    location = self._extract_location_from_item(item_text)
                    logger.debug(f"位置: {location}")
                    
                    # 查找 View All Info 按钮
                    view_info_btn = item.query_selector(
                        "button, a"
                    )
                    
                    if not view_info_btn:
                        logger.debug(f"未找到按钮")
                        continue
                    
                    # 检查按钮文本
                    btn_text = ""
                    try:
                        btn_text = view_info_btn.inner_text()
                    except:
                        pass
                    
                    if "View All Info" not in btn_text and "view" not in btn_text.lower():
                        # 尝试找其他按钮
                        buttons = item.query_selector_all("button, a")
                        view_info_btn = None
                        for btn in buttons:
                            try:
                                if "View" in btn.inner_text() or "view" in btn.inner_text().lower():
                                    view_info_btn = btn
                                    break
                            except:
                                continue
                        
                        if not view_info_btn:
                            logger.debug(f"未找到 View All Info 按钮")
                            continue
                    
                    logger.debug(f"点击按钮获取详情...")
                    
                    try:
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
                    
                except Exception as e:
                    logger.debug(f"处理结果项出错: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"提取页面结果出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_name_from_item(self, item, item_text: str) -> str:
        """从结果项中提取名字"""
        # 尝试从标题标签提取
        for tag in ["h3", "h2", "h1"]:
            title_elem = item.query_selector(tag)
            if title_elem:
                name = title_elem.text_content().strip()
                if name and len(name) > 2:
                    return name
        
        # 从文本中提取第一行（通常是名字）
        lines = item_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and "Approximate" not in line and "Current" not in line:
                return line
        
        return None
    
    def _extract_location_from_item(self, text: str) -> str:
        """从结果项中提取位置"""
        # 查找 "Current Location:" 后面的内容
        match = re.search(r'Current\s+Location[:\s]+([^,\n]+(?:,\s*[A-Z]{2})?)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return "Unknown"
    
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
            
            logger.debug(f"在详情页找到 {len(phone_items)} 个可能的元素")
            
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
                    if 10 < age < 120:
                        return age
        except:
            pass
        
        return None
    
    def _extract_phone_number(self, text: str) -> str:
        """
        从文本中提取电话号码
        """
        try:
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
