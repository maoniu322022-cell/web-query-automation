# PeopleSearchNow 名字搜索爬虫

## 功能描述

这是一个自动化爬虫工具，用于从 [PeopleSearchNow](https://www.peoplesearchnow.com) 网站按名字搜索人员信息。

### 功能特性

- ✅ 按名字搜索（支持多个名字批量查询）
- ✅ 自动分页遍历（处理搜索结果的所有页面）
- ✅ 多线程并发查询（3 个线程同时运行，提升速度）
- ✅ 智能筛选：
  - 年龄范围：53-75 岁
  - 电话类型：仅保留 Wireless（无线）电话
- ✅ 自动保存到 Excel 文件
- ✅ 自动推送结果到 GitHub
- ✅ 错误处理与恢复机制

## 环境要求

```bash
python >= 3.8
playwright >= 1.30.0
openpyxl >= 3.0.0
```

## 安装依赖

```bash
pip install playwright openpyxl
python -m playwright install
```

## 使用方法

### 1. 准备名字列表

编辑 `names.txt` 文件，每行一个名字：

```
Phong Thai Nguyen Quoc
Phuc Vo Huy
John Smith
```

### 2. 运行爬虫

**方法 A：双击批处理文件**
```
双击 "开始查询.bat"
```

**方法 B：命令行运行**
```bash
python main.py
```

### 3. 查看结果

爬虫完成后，结果会保存到 `search_results.xlsx`

## 文件说明

| 文件 | 说明 |
|------|------|
| `scraper.py` | 爬虫核心逻辑（Playwright 浏览器自动化） |
| `data_handler.py` | 数据处理和 Excel 保存 |
| `main.py` | 多线程并发管理 |
| `names.txt` | 输入的名字列表 |
| `search_results.xlsx` | 查询结果输出 |
| `开始查询.bat` | Windows 一键启动脚本 |

## 调整并发数

编辑 `main.py` 第 15 行：

```python
MAX_WORKERS = 3  # 改成 2-5 都可以
```

**建议值：**
- 电脑配置差：2
- 电脑配置中等：3 或 4
- 电脑配置高：5

## 错误处理

### Error 1015（限流）

如果遇到 Error 1015，说明网站限流了：

1. ✋ 爬虫会自动暂停
2. 🔄 请切换 VPN
3. 🔗 按 F5 刷新网页
4. ⌨️ 按 Enter 继续

### 网络连接错误

1. 检查网络连接
2. 按 F5 刷新
3. 按 Enter 继续

## 输出说明

### search_results.xlsx

| 列名 | 说明 |
|------|------|
| Name | 人名 |
| Age | 年龄（已筛选 53-75） |
| Phone | 电话号码（仅 Wireless） |
| Location | 位置/城市 |

## 性能提升

| 模式 | 时间 | 并发数 |
|------|------|--------|
| 单线程 | 100% | 1 |
| **多线程** | **33-50%** | **3** |

使用 3 个线程可以将查询速度提升 **2-3 倍**！

## GitHub 推送

查询完成后，结果会自动推送到 GitHub 仓库。

确保你已配置 Git 和 GitHub 认证：

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

## 常见问题

**Q: 为什么找不到结果？**
- A: 可能没有符合年龄 53-75 且有 Wireless 电话的人员
- 可以查看 PeopleSearchNow 网站是否有该人的信息

**Q: 可以查询哪些信息？**
- A: 仅保存名字、年龄、Wireless 电话和位置
- 其他信息会被过滤

**Q: 如何修改筛选条件？**
- A: 编辑 `scraper.py` 第 XX 行的年龄条件

## 许可证

MIT License

## 免责声明

本工具仅供学习和研究使用，请遵守网站的 robots.txt 和使用条款。
