# 🔍 RealtyAPI Skip Trace - 批量电话号码反查工具

使用 **RealtyAPI Skip Trace API**，快速查询电话号码对应的个人信息，包括姓名、年龄、地址、房产价值等。

---

## ✨ 功能特性

✅ **批量查询** - 支持查询数万个电话号码  
✅ **多线程加速** - 可配置 workers 和 RPS，速度快 10-100 倍  
✅ **自动提取** - 姓名、年龄、地址、房产价值、职业等  
✅ **智能重试** - 网络异常自动重试（最多 3 次）  
✅ **CSV 导出** - 结果自动保存为 CSV 格式  
✅ **恢复机制** - 支持 `--resume` 继续未完成的查询  
✅ **详细日志** - 实时显示进度和错误信息  

---

## 🚀 快速开始

### 前置要求
- Python 3.8+
- RealtyAPI 账户和 API Key（需要付费）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/maoniu322022-cell/web-query-automation.git
   cd web-query-automation
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 API Key**
   ```bash
   echo "rt_your_api_key_here" > api_key.txt
   ```
   - 将 `rt_your_api_key_here` 替换为您的实际 RealtyAPI Key
   - 从 https://realtyapi.io 获取 Key

4. **准备输入文件**
   - 创建 `input.csv` 文件
   - 第一列放电话号码（支持任何格式）
   ```csv
   phone
   410-390-3335
   (555) 123-4567
   8889990000
   ```

5. **运行查询**
   ```bash
   python main.py --input input.csv --output output.csv --workers 10 --rps 10
   ```

---

## 📖 使用说明

### 基本命令

```bash
python main.py --input input.csv --output output.csv --workers 10 --rps 10
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | `input.csv` | 输入文件路径 |
| `--output` | `output.csv` | 输出文件路径 |
| `--workers` | `10` | 并发线程数（2-50） |
| `--rps` | `10.0` | 每秒请求数 |
| `--limit` | `0` | 只查询前 N 个号码（0 = 全部） |
| `--resume` | - | 跳过已完成的，继续未完成的 |
| `--auth` | `api_key.txt` | API Key 文件路径 |
| `--json` | - | 可选：输出详细 JSON 文件 |

### 常用示例

**快速测试（只查询前 100 个）：**
```bash
python main.py --input input.csv --output output.csv --limit 100
```

**高速查询（并发 20，RPS 30）：**
```bash
python main.py --input input.csv --output output.csv --workers 20 --rps 30
```

**恢复中断的查询：**
```bash
python main.py --resume
```

**输出详细 JSON 日志：**
```bash
python main.py --input input.csv --output output.csv --json output.json
```

---

## 📊 输出格式

### CSV 输出示例

| input_phone | name | age | property_value | value_source | occupation |
|-------------|------|-----|----------------|--------------|-----------|
| 410-390-3335 | John Doe | 45 | 450000 | zillow | Engineer |
| 555-123-4567 | Jane Smith | 38 | 320000 | redfin | Doctor |

### 查询统计

查询完成后会显示：
```
[done] wrote output.csv
       resolved=950  no_results=45  error=5
       rows with property_value: 850
```

- **resolved** - 成功获取信息的号码
- **no_results** - 找不到相关信息的号码
- **error** - 查询出错的号码
- **property_value** - 成功获取房产价值的号码

---

## ⚙️ 性能优化

### 调整并发和速率

| 场景 | workers | rps | 说明 |
|------|---------|-----|------|
| 低配电脑 | 5 | 5 | 稳定，额度消耗慢 |
| 中等配置 | 10 | 10 | 平衡性能和额度 |
| 高配电脑 | 20-30 | 20-30 | 快速，额度消耗快 |
| 超高配置 | 50 | 50 | 最快（需要 Mega 计划） |

### 预计时间

按 10 workers, 10 RPS：
- 1,000 号码 ≈ 2 分钟
- 10,000 号码 ≈ 17 分钟
- 45,990 号码 ≈ 77 分钟

---

## 🔧 故障排除

### ❌ 错误：`ModuleNotFoundError: No module named 'requests'`

**解决：** 安装依赖
```bash
pip install -r requirements.txt
```

### ❌ 错误：`HTTP 402 Payment Required`

**解决：** API 额度不足
1. 访问 https://realtyapi.io 登录账户
2. 检查剩余额度（Credits）
3. 购买更多额度或升级套餐
4. 重新运行 `python main.py --resume`

### ❌ 错误：`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff`

**解决：** API Key 文件编码问题
```bash
# 删除旧文件
del api_key.txt

# 重新创建
echo rt_your_key > api_key.txt
```

### ❌ 错误：`[ERROR] phone_number: HTTP 401 Unauthorized`

**解决：** API Key 无效或过期
1. 检查 `api_key.txt` 中的 Key 是否正确
2. 确保 Key 前缀是 `rt_` 而不是其他
3. 从 https://realtyapi.io 复制新的 Key

### ⚠️ 查询速度慢

**优化方案：**
- 增加 `--workers` 值（如从 10 改到 20）
- 增加 `--rps` 值（如从 10 改到 30）
- 检查网络连接
- 升级到更高速率的套餐

---

## 📚 RealtyAPI 套餐信息

| 套餐 | 价格 | 查询数 | 速率 |
|------|------|--------|------|
| Starter | $99/月 | 1,000 | 10 RPS |
| Pro | $299/月 | 5,000 | 20 RPS |
| Mega | $999/月 | 25,000 | 50 RPS |

*注：价格和额度可能变更，请访问 https://realtyapi.io 确认*

---

## 📝 依赖包

```
requests>=2.28.0
openpyxl>=3.1.0
```

手动安装：
```bash
pip install requests>=2.28.0
```

---

## 💡 常见问题

**Q: 查询结果准确度如何？**  
A: 准确度约 85-90%，取决于数据库的完整性和最新性。某些号码可能没有记录。

**Q: 支持国内手机号吗？**  
A: 不支持，RealtyAPI 只支持美国号码（10 位）。

**Q: 能查询其他信息吗？**  
A: 可以，RealtyAPI 还支持姓名反查、地址查询等其他功能（需要集成相应 API）。

**Q: 查询过程中断了怎么办？**  
A: 运行 `python main.py --resume` 会自动跳过已完成的，继续查询剩余号码。

**Q: 怎么只查询部分号码测试？**  
A: 使用 `--limit 100` 只查询前 100 个。

**Q: 支持代理/VPN 吗？**  
A: 代码不支持代理，但 RealtyAPI 服务器在全球，通常不需要 VPN。

---

## 🔐 隐私与安全

⚠️ **重要提示：**
- 请确保 `api_key.txt` 被添加到 `.gitignore`（已默认添加）
- 不要将包含 API Key 的文件上传到公开仓库
- 仅用于合法目的（数据分析、营销研究等）
- 遵守当地法律和 RealtyAPI 的服务条款

---

## 📄 许可证

MIT License - 自由使用和修改

---

## 🤝 反馈与支持

遇到问题？
- 提交 Issue：https://github.com/maoniu322022-cell/web-query-automation/issues
- 发送邮件：maoniu322022@gmail.com

---

**最后更新：** 2026-07-23  
**版本：** 3.0 (RealtyAPI Skip Trace)  
**状态：** ✅ 生产级别
