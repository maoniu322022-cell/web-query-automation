import logging
import time
from playwright.async_api import async_playwright, TimeoutError
import asyncio

logger = logging.getLogger(__name__)

class PeopleSearchNameScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.base_url = "https://www.peoplesearchnow.com"
        self.search_url = "https://www.peoplesearchnow.com/name"
        
    async def init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(30000)
        
    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    async def search_by_name(self, name: str) -> list:
        """
        按名字搜索
        返回符合条件的结果列表
        """
        results = []
        
        try:
            # 访问搜索页面
            logger.info(f"正在搜索: {name}")
            await self.page.goto(f"{self.search_url}/{name.replace(' ', '-').lower()}", 
                                wait_until="commit")
            
            # 等待结果加载
            await asyncio.sleep(2)
            
            # 检查是否有错误信息
            try:
                error_msg = await self.page.query_selector(".error-message")
                if error_msg:
                    error_text = await error_msg.text_content()
                    if "1015" in error_text:
                        logger.warning("⚠️ 遇到 Error 1015 - 需要切换 VPN")
                        logger.warning("请按照以下步骤操作:")
                        logger.warning("1. 切换 VPN")
                        logger.warning("2. 按 F5 刷新")
                        logger.warning("3. 按 Enter 继续")
                        input("按 Enter 继续...")
                        return []
            except:
                pass
            
            # 获取当前页面的所有结果
            page_num = 1
            while True:
                logger.info(f"处理第 {page_num} 页")
                
                # 提取当前页的结果
                page_results = await self._extract_results_from_page(name)
                results.extend(page_results)
                
                # 检查是否有下一页
                has_next = await self._go_to_next_page()
                if not has_next:
                    logger.info(f"已到达最后一页")
                    break
                
                page_num += 1
                await asyncio.sleep(1)
            
            return results
            
        except TimeoutError:
            logger.error(f"页面加载超时")
            return []
        except Exception as e:
            logger.error(f"搜索出错: {e}")
            return []
    
    async def _extract_results_from_page(self, search_name: str) -> list:
        """
        从当前页提取结果
        """
        results = []
        
        try:
            # 获取所有结果项
            result_items = await self.page.query_selector_all(".result-item, [class*='result'], [class*='person']")
            
            logger.info(f"找到 {len(result_items)} 个结果项")
            
            for item in result_items:
                try:
                    # 提取名字
                    name_elem = await item.query_selector("h2, .name, [class*='name']") or \
                               await item.query_selector("a")
                    name = await name_elem.text_content() if name_elem else "Unknown"
                    name = name.strip()
                    
                    # 提取年龄
                    age_text = await item.inner_text()
                    age = self._extract_age(age_text)
                    
                    # 筛选年龄 53-75
                    if age and (age < 53 or age > 75):
                        continue
                    
                    # 提取位置
                    location_elem = await item.query_selector(".location, [class*='location']") or \
                                   await item.query_selector(".city, [class*='city']")
                    location = await location_elem.text_content() if location_elem else "Unknown"
                    location = location.strip()
                    
                    # 点击 "View All Info" 获取详细信息
                    view_info_btn = await item.query_selector("button:has-text('View All Info'), a:has-text('View All Info')")
                    if view_info_btn:
                        # 在新标签页打开
                        async with self.page.context.expect_page() as new_page_info:
                            await view_info_btn.click()
                        
                        detail_page = await new_page_info.value
                        await asyncio.sleep(1)
                        
                        # 提取电话号码（只要 Wireless）
                        phones = await self._extract_wireless_phones(detail_page)
                        
                        # 关闭详情页
                        await detail_page.close()
                        
                        # 如果有 Wireless 电话，保存结果
                        if phones:
                            for phone in phones:
                                results.append({
                                    "name": name,
                                    "age": age,
                                    "phone": phone,
                                    "location": location
                                })
                                logger.info(f"✓ 保存: {name} (年龄: {age}) - {phone}")
                
                except Exception as e:
                    logger.debug(f"提取结果项出错: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"提取页面结果出错: {e}")
            return []
    
    async def _extract_wireless_phones(self, page) -> list:
        """
        从详情页提取 Wireless 电话
        """
        phones = []
        
        try:
            await asyncio.sleep(1)
            
            # 获取所有电话号码
            phone_items = await page.query_selector_all(".phone-item, [class*='phone'], .number")
            
            for item in phone_items:
                phone_text = await item.inner_text()
                
                # 检查是否包含 "Wireless"
                if "Wireless" in phone_text or "wireless" in phone_text:
                    # 提取电话号码
                    phone_num = self._extract_phone_number(phone_text)
                    if phone_num:
                        phones.append(phone_num)
                        logger.info(f"  找到 Wireless 电话: {phone_num}")
            
            return phones
            
        except Exception as e:
            logger.debug(f"提取电话出错: {e}")
            return []
    
    async def _go_to_next_page(self) -> bool:
        """
        跳转到下一页
        返回 True 如果成功，False 如果已是最后一页
        """
        try:
            next_button = await self.page.query_selector(
                "a.next, button.next, a[rel='next'], .pagination a:has-text('Next')"
            )
            
            if next_button:
                await next_button.click()
                await asyncio.sleep(2)
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"获取下一页失败: {e}")
            return False
    
    def _extract_age(self, text: str) -> int:
        """
        从文本中提取年龄
        """
        import re
        match = re.search(r'(?:age|Age)\s*:?\s*(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_phone_number(self, text: str) -> str:
        """
        从文本中提取电话号码
        """
        import re
        # 匹配格式: (123) 456-7890 或 123-456-7890
        match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text)
        if match:
            return match.group(0)
        return None
