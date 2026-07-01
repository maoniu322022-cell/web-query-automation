import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import PeopleSearchNowScraper
from data_handler import DataHandler, results_lock

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 并发数（同时开启的浏览器数）
MAX_WORKERS = 3  # 建议 2-4 个，根据电脑配置调整

def search_worker(phone: str, worker_id: int, total: int) -> dict:
    """
    单个线程的工作函数
    """
    try:
        scraper = PeopleSearchNowScraper()
        logger.info(f"[Worker {worker_id}] 开始查询: {phone}")
        result = scraper.search_by_phone(phone)
        scraper.close()
        
        if result:
            logger.info(f"[Worker {worker_id}] ✓ 找到结果: {phone}")
            return result
        else:
            logger.info(f"[Worker {worker_id}] ✗ 未找到结果: {phone}")
            return None
    except Exception as e:
        logger.error(f"[Worker {worker_id}] 查询失败 {phone}: {e}")
        return None

def main():
    logger.info("=" * 60)
    logger.info(f"开始 People Search Now 反向查询 (多线程模式, {MAX_WORKERS} 个并发)")
    logger.info("=" * 60)
    
    handler = DataHandler()
    phones = handler.load_phones("phones.txt")
    
    if not phones:
        logger.error("No phones found!")
        return
    
    logger.info(f"✓ 读取了 {len(phones)} 个电话号码")
    logger.info(f"✓ 将使用 {MAX_WORKERS} 个线程并发查询")
    logger.info("")
    
    results = []
    completed_count = 0
    
    try:
        # 使用线程池执行器
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_phone = {
                executor.submit(search_worker, phone, i % MAX_WORKERS + 1, len(phones)): phone 
                for i, phone in enumerate(phones)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_phone):
                phone = future_to_phone[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    if result:
                        with results_lock:
                            results.append(result)
                    logger.info(f"[进度] {completed_count}/{len(phones)} 已完成")
                except Exception as e:
                    logger.error(f"任务执行出错 {phone}: {e}")
    
    except KeyboardInterrupt:
        logger.warning("用户中止查询")
    
    logger.info("")
    logger.info("=" * 60)
    
    if results:
        logger.info(f"✓ 成功找到 {len(results)} 个结果")
        logger.info(f"✓ 成功率: {len(results)}/{len(phones)} = {len(results)*100//len(phones)}%")
        logger.info(f"✓ 保存到 search_results.xlsx")
        handler.save_results(results, "search_results.xlsx")
    else:
        logger.info("未找到任何结果")

if __name__ == "__main__":
    main()
