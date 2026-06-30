import logging
from scraper import PeopleSearchNowScraper
from data_handler import DataHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("开始 People Search Now 反向查询")
    logger.info("=" * 60)
    
    handler = DataHandler()
    phones = handler.load_phones("phones.txt")
    
    if not phones:
        logger.error("No phones found!")
        return
    
    logger.info(f"✓ 读取了 {len(phones)} 个电话号码")
    logger.info("")
    
    scraper = PeopleSearchNowScraper()
    results = []
    
    try:
        for idx, phone in enumerate(phones, 1):
            logger.info(f"[{idx}/{len(phones)}] 正在查询: {phone}")
            result = scraper.search_by_phone(phone)
            
            if result:
                results.append(result)
                logger.info(f"✓ 找到结果")
            else:
                logger.info(f"✗ 未找到结果")
            logger.info("")
    
    finally:
        scraper.close()
    
    if results:
        logger.info(f"✓ 成功找到 {len(results)} 个结果，保存到 search_results.xlsx")
        handler.save_results(results, "search_results.xlsx")
    else:
        logger.info("未找到任何结果")

if __name__ == "__main__":
    main()
