import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import PeopleSearchNowScraper
from utils import read_phone_numbers, save_results

MAX_WORKERS = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def worker_batch(worker_id: int, phones: list[str]):
    """
    一个 worker 只开一个浏览器，顺序处理分配到的所有号码
    """
    scraper = PeopleSearchNowScraper()
    results = []
    try:
        logger.info(f"[Worker {worker_id}] 启动，分配到 {len(phones)} 个号码")
        for idx, phone in enumerate(phones, 1):
            try:
                logger.info(f"[Worker {worker_id}] ({idx}/{len(phones)}) 查询: {phone}")
                result = scraper.search_by_phone(phone)
                if result:
                    results.append(result)
                    logger.info(f"[Worker {worker_id}] ✓ 命中: {phone} -> {result.get('name', '')}")
                else:
                    logger.info(f"[Worker {worker_id}] ✗ 无结果: {phone}")
            except Exception as e:
                logger.error(f"[Worker {worker_id}] 查询失败 {phone}: {e}", exc_info=True)
        return results
    finally:
        scraper.close()
        logger.info(f"[Worker {worker_id}] 结束，浏览器已关闭")


def split_phones_round_robin(phones: list[str], workers: int):
    """
    轮序分配：第1个给worker1，第2个给worker2，第3个给worker3，第4个再给worker1...
    """
    buckets = [[] for _ in range(workers)]
    for i, p in enumerate(phones):
        buckets[i % workers].append(p)
    return buckets


def main():
    logger.info("=" * 60)
    logger.info(f"开始 People Search Now 反向查询 (常驻浏览器模式, {MAX_WORKERS} 个并发)")
    logger.info("=" * 60)

    phones = read_phone_numbers("phone_numbers.txt")
    if not phones:
        logger.error("未读取到电话号码，请检查 phone_numbers.txt")
        return

    logger.info(f"读取了 {len(phones)} 个电话号码")
    logger.info(f"将启动 {MAX_WORKERS} 个浏览器实例，每个实例顺序查询分配到的号码")

    phone_groups = split_phones_round_robin(phones, MAX_WORKERS)

    all_results = []
    completed_workers = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(worker_batch, worker_id + 1, group): worker_id + 1
            for worker_id, group in enumerate(phone_groups)
            if group
        }

        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                worker_results = future.result()
                all_results.extend(worker_results)
                completed_workers += 1
                logger.info(f"[进度] Worker {worker_id} 完成 ({completed_workers}/{len(futures)})")
            except Exception as e:
                completed_workers += 1
                logger.error(f"[进度] Worker {worker_id} 失败 ({completed_workers}/{len(futures)}): {e}")

    save_results(all_results, "results.csv")
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"查询完成: 共 {len(phones)} 条, 成功 {len(all_results)} 条")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()