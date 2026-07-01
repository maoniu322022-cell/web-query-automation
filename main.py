import logging
from scraper import PeopleSearchNameScraper
from data_handler import DataHandler
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info(f"开始按名字搜索 (顺序执行模式)")
    logger.info("=" * 60)
    
    handler = DataHandler()
    names = handler.load_names("names.txt")
    
    if not names:
        logger.error("names.txt not found!")
        return
    
    logger.info(f"✓ 读取了 {len(names)} 个名字")
    logger.info(f"✓ 筛选条件: 年龄 53-75 岁, 仅保留 Wireless 电话")
    logger.info("")
    
    all_results = []
    
    for idx, name in enumerate(names):
        logger.info(f"\n[进度 {idx+1}/{len(names)}] 正在处理: {name}")
        
        try:
            scraper = PeopleSearchNameScraper()
            scraper.init_browser()
            
            results = scraper.search_by_name(name)
            
            if results:
                all_results.extend(results)
                logger.info(f"[✓] 找到 {len(results)} 条符合条件的结果")
            else:
                logger.info(f"[✗] 无符合条件的结果")
            
            scraper.close()
            
        except Exception as e:
            logger.error(f"[错误] 处理 {name} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("")
    logger.info("=" * 60)
    
    if all_results:
        logger.info(f"✓ 成功找到总计 {len(all_results)} 条符合条件的结果")
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
