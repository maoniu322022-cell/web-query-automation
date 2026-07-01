import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import PeopleSearchNameScraper
from data_handler import DataHandler, results_lock
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 并发数（同时开启的浏览器数）
MAX_WORKERS = 1  # 先改为 1，Playwright 多线程需要小心处理

def search_worker(name: str, worker_id: int) -> list:
    """
    单个线程的工作函数
    """
    try:
        logger.info(f"[Worker {worker_id}] 开始处理: {name}")
        
        scraper = PeopleSearchNameScraper()
        scraper.init_browser()
        
        results = scraper.search_by_name(name)
        
        scraper.close()
        
        return results
        
    except Exception as e:
        logger.error(f"[Worker {worker_id}] 查询失败 {name}: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    logger.info("=" * 60)
    logger.info(f"开始按名字搜索 (多线程模式, {MAX_WORKERS} 个并发)")
    logger.info("=" * 60)
    
    handler = DataHandler()
    names = handler.load_names("names.txt")
    
    if not names:
        logger.error("No names found!")
        return
    
    logger.info(f"✓ 读取了 {len(names)} 个名字")
    logger.info(f"✓ 筛选条件: 年龄 53-75 岁, 仅保留 Wireless 电话")
    logger.info(f"✓ 将使用 {MAX_WORKERS} 个线程并发查询")
    logger.info("")
    
    all_results = []
    completed_count = 0
    
    try:
        # 使用线程池执行器
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_name = {
                executor.submit(search_worker, name, i % MAX_WORKERS + 1): name 
                for i, name in enumerate(names)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                completed_count += 1
                
                try:
                    results = future.result()
                    if results:
                        with results_lock:
                            all_results.extend(results)
                        logger.info(f"[进度] {completed_count}/{len(names)} 已完成 - 找到 {len(results)} 条结果")
                    else:
                        logger.info(f"[进度] {completed_count}/{len(names)} 已完成 - 无符合条件的结果")
                except Exception as e:
                    logger.error(f"任务执行出错 {name}: {e}")
    
    except KeyboardInterrupt:
        logger.warning("用户中止查询")
    
    logger.info("")
    logger.info("=" * 60)
    
    if all_results:
        logger.info(f"✓ 成功找到 {len(all_results)} 条符合条件的结果")
        logger.info(f"✓ 保存到 search_results.xlsx")
        handler.save_results(all_results, "search_results.xlsx")
        
        # 自动推送到 GitHub
        try:
            logger.info("正在推送到 GitHub...")
            subprocess.run(["git", "add", "search_results.xlsx"], check=True)
            subprocess.run(["git", "commit", "-m", "更新查询结果"], check=True)
            subprocess.run(["git", "push", "origin", "search_names"], check=True)
            logger.info("✓ 已推送到 GitHub")
        except Exception as e:
            logger.warning(f"推送失败: {e}")
    else:
        logger.info("未找到符合条件的结果")

if __name__ == "__main__":
    main()
