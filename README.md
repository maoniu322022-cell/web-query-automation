# 🔍 People Search Now 反向查询工具

快速查询电话号码对应的个人信息，支持批量查询和多线程加速。

---

## 📋 功能特性

✅ **批量查询** - 一次查询数百个电话号码  
✅ **多线程加速** - 3 个浏览器同时工作，速度提升 2-3 倍  
✅ **自动化提取** - 自动获取姓名、年龄、位置信息  
✅ **智能重试** - 网络异常自动暂停，手动刷新后继续  
✅ **Excel 导出** - 结果自动保存为 Excel 表格  

---

## 🚀 快速开始

### 方式 1️⃣：直接打包成 .exe（推荐）

**前提要求：** 你的电脑需要安装 Python 3.8+

**步骤：**

1. **下载仓库**
   ```bash
   git clone https://github.com/maoniu322022-cell/web-query-automation.git
   cd web-query-automation
   ```

2. **双击 `build.bat` 自动打包**
   - 自动检测 Python
   - 自动安装 PyInstaller
   - 生成 `开始查询.exe` 文件

3. **等待完成**
   - 第一次需要 3-5 分钟
   - 完成后会看到 `dist` 文件夹

4. **复制到其他电脑**
   ```
   dist 文件夹
   ├── 开始查询.exe
   ├── scraper.py
   └── data_handler.py
   ```

---

### 方式 2️⃣：直接运行 Python（开发模式）

**前提要求：** 需要安装 Python 和依赖

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **准备输入文件**
   - 在项目文件夹中创建 `phones.txt`
   - 每行一个电话号码
   ```
   410-390-3335
   555-123-4567
   888-999-0000
   ```

3. **运行查询**
   ```bash
   python main.py
   ```

---

## 📝 使用说明

### 准备输入文件

创建 `phones.txt` 文件，内容示例：
```
410-390-3335
(555) 123-4567
8889990000
```

支持多种格式：
- `410-390-3335`
- `(410) 390-3335`
- `4103903335`

### 运行程序

**Windows 用户：** 双击 `开始查询.exe` 或 `开始查询.bat`

**Linux/Mac 用户：** 
```bash
python main.py
```

### 查看结果

查询完成后，自动生成 `search_results.xlsx`

| Phone | Name | Age | Location |
|-------|------|-----|----------|
| 410-390-3335 | John Doe | 45 | California, USA |

---

## ⚙️ 高级配置

### 调整并发数

编辑 `main.py` 第 14 行：
```python
MAX_WORKERS = 3  # 改成 2-5
```

- `2` - 低配电脑
- `3` - 中等配置（推荐）
- `4-5` - 高配电脑

### 网络异常处理

程序会自动暂停并提示：
```
⚠️ 网络连接出现问题，请检查网络或切换 VPN 节点
✅ 切换完成后，在浏览器按 F5 刷新页面，然后按 Enter 继续...
```

按照提示操作即可。

---

## 🔧 故障排除

### ❌ 错误：`Page.goto: Timeout 30000ms exceeded`

**解决：** 网络不稳定或网站被限速
- 检查网络连接
- 切换 VPN 节点
- 等待几分钟后重试

### ❌ 错误：`Error 1015 Rate Limited`

**解决：** 查询频率过快，被网站限制
- 增加等待时间
- 减少 `MAX_WORKERS` 数量
- 更换 IP/VPN

### ❌ 其他 Python 相关错误

**检查依赖：**
```bash
pip install -r requirements.txt --upgrade
```

---

## 📦 依赖包

```
playwright>=1.40.0
beautifulsoup4>=4.12.0
openpyxl>=3.1.0
```

如果手动安装：
```bash
pip install playwright beautifulsoup4 openpyxl
playwright install
```

---

## 💡 常见问题

**Q: 查询结果不准确？**  
A: 网站数据可能不完整或已更新，多次查询可能得到不同结果。

**Q: 能查询其他国家的号码？**  
A: 可以尝试，但网站主要针对美国号码。

**Q: 支持国内 11 位号码吗？**  
A: 不支持，网站只支持美国格式。

**Q: 多久更新一次？**  
A: 网站数据实时更新，查询结果是最新的。

---

## 📄 许可证

MIT License - 自由使用和修改

---

## 🤝 反馈与支持

遇到问题？
- 提交 Issue
- 发送邮件至 maoniu322022@gmail.com

---

**最后更新：** 2026-07-01  
**版本：** 2.0 (多线程 + 自动打包)
