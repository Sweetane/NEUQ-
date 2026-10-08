# 🏫 NEUQ Empty Classroom (东北大学秦皇岛分校 空教室极简查询工具)

> 专门针对考研自习与日常找空教室场景打造的轻量化自动化工具。  
> **彻底单文件设计**，内置纯 Python AES 加密算法，在电脑、服务器和**手机 Termux** 均可秒级运行，输出格式极度简洁，原生支持 **OpenClaw**、微信/QQ/钉钉机器人无缝对接。

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20Android%20Termux-orange.svg)](#)

---

## 💡 为什么做这个项目？

1. **查空教室繁琐**：每次想自习都要登录教务系统、经过繁琐的 CAS 认证并多层点击菜单，手机浏览器体验极差。
2. **手机 Termux 编译报错**：金智统一身份认证使用 AES 加密，在 Android Termux 上安装 `cryptography` 或 `pycryptodome` 经常因缺少 Rust/C 编译器而报错失败。本项目采用**纯 Python 实现了 AES-128-CBC**，实现零编译依赖！
3. **输出过于杂乱**：教务系统自带的空教室包含大量的研讨室、录播室、体育场甚至线上考试会议。本项目自动进行**自习室智能过滤**，并按照**楼层分行 + 房间号升序**紧凑排版，直接发到聊天群或个人对话极其舒适。

---

## 📸 效果预览

默认查询输出效果（无任何多余文字，一目了然）：

```text
1-2节：

G103 G107 G112 G126 G129
G207 G212 G221 G229
G330 G331
G503 G506 G517 G525
G606 G607 G610 G611 G614 G621 G625
G703 G706 G707 G710 G714 G717 G721 G725

3-4节：

G112 G127
G206 G211 G212 G221 G225 G226
G316 G326
G411 G414 G421
G510 G511 G517 G521
G603 G606 G614 G617 G621
G703 G706 G707 G710 G711 G714 G717 G721 G725
```

---

## ✨ 核心特性

- ⚡ **单文件极简设计**：整个项目只需单个 `neuq_classroom.py`，传输和部署极度清爽。
- 📱 **Termux 极其友好**：纯 Python 实现 AES 加密算法，仅需 `requests` 和 `beautifulsoup4` 两个基础纯 Python 库，手机上 10 秒装完。
- 🗣️ **自然语言语义解析**：直接支持整句输入（例如：“*明天工学馆1-4节*”、“*第3节*”、“*下午5-8节*”），机器人调用无需写复杂正则。
- 🕒 **支持连选与单节查询**：
  - 查单节（如第 3 节没课）；
  - 查多节连续没课（如 1-4 节、3-6 节、5-8 节整段空闲的自习室）。
- 🏢 **智能楼层排版**：
  - 工学馆 `G`、基础楼 `J`、综合楼 `Z`、管理楼 `M` 等；
  - 同楼层一行展示，不同楼层自动换行；
  - 自动过滤 8 楼小教研室、录播室、腾讯会议及体育场地。
- 🛡️ **教务系统频控保护**：内置自适应请求延时与自动重试，彻底解决教务系统“*请不要过快点击*”拦截。

---

## 🚀 快速上手指南

### 1. 下载脚本与安装依赖

```bash
# 克隆仓库
git clone https://github.com/your-username/neuq-empty-classroom.git
cd neuq-empty-classroom

# 安装仅有的两个基础库
pip install -r requirements.txt
```

### 2. 配置您的账号与密码

用任意文本编辑器打开 `neuq_classroom.py`，在顶部 **第 24 行** 填入您的学号和密码：

```python
# ==================== 个人配置区 ====================
DEFAULT_CONFIG = {
    "username": "你的学号",             # 例如: "20230101"
    "password": "你的统一身份认证密码",  # 例如: "123456"
    "default_building": "工学馆",       # 默认查询教学楼
    "min_seats": 80,                   # 工学馆常规自习室最小座位数
    "campus": "1"                      # 校区 (1为本部)
}
# ====================================================
```

*(也可以通过系统环境变量 `NEUQ_USERNAME` 和 `NEUQ_PASSWORD` 注入，安全不落地)*

### 3. 运行测试

```bash
python neuq_classroom.py
```

---

## 📱 手机 Android (Termux) 部署教程

非常适合部署在手机上作为自用后台：

1. **安装 Termux 基础环境**：
   ```bash
   pkg update -y
   pkg install -y python git
   ```

2. **安装运行依赖**：
   ```bash
   pip install requests beautifulsoup4
   ```

3. **下载脚本并配置**：
   将 `neuq_classroom.py` 传输至手机 Termux（或通过 git clone），使用 `nano neuq_classroom.py` 修改第 24 行的账号和密码后保存。

4. **随时随地执行**：
   ```bash
   python neuq_classroom.py "明天1-4节"
   ```

---

## 🗣️ 自然语言使用方式（支持直接对机器人对话）

本脚本内置了语义提取器，您可以直接在命令行后传入整句自然语言：

```bash
# 1. 默认查工学馆今天上午 (1-2节 + 3-4节)
python neuq_classroom.py

# 2. 查连着没课的时段
python neuq_classroom.py "1-4节"          # 1到4节整个上午没课
python neuq_classroom.py "3-6节"          # 3到6节中午连着没课
python neuq_classroom.py "5-8节"          # 5到8节下午连着没课

# 3. 查单节
python neuq_classroom.py "第3节"
python neuq_classroom.py "第5节"

# 4. 查特定日期
python neuq_classroom.py "明天1-4节"
python neuq_classroom.py "后天下午"

# 5. 查其他教学楼（默认未指定时为工学馆）
python neuq_classroom.py "基础楼1-2节"
python neuq_classroom.py "综合楼下午"
```

---

## 🤖 对接 OpenClaw / 微信 / QQ / Telegram 机器人

如果使用 **OpenClaw**、**OneBot**、**NoneBot**、**企微应用** 或 **Telegram Bot**：

1. 机器人接收到用户的聊天消息 `{msg}`。
2. 机器人调用系统命令：
   ```bash
   python neuq_classroom.py "{msg}"
   ```
3. 将该命令的标准输出 (stdout) 直接作为文本原样回复给用户即可！

---

## 🏫 其他高校迁移与适配指南 (移植到本校)

本项目基于国内高校广泛采用的 **金智统一身份认证 (Wisedu AuthServer / CAS) + 上海树维/金智 EAMS 教务管理系统** 开发。

如果你们学校也采用了这套架构（**常见特征**：统一登录地址包含 `/authserver/login`，教务系统地址包含 `/eams/`），其他高校的同学也可以非常轻松地将本项目移植到本校使用，**只需修改脚本中的 3 处配置**：

### 1. 修改学校域名与系统 URL
在 `neuq_classroom.py` 中，将东北大学秦皇岛分校的域名替换为您学校的域名：
- `login_url`：替换为本校的统一身份认证登录地址（带教务系统 service 参数）；
- `search_url`：替换为本校教务系统的空教室查询地址（通常为 `http://jwxt.your_univ.edu.cn/eams/classroom/apply/free!search.action`）。

### 2. 修改教学楼映射与缩写
根据本校实际的教学楼名称和楼宇 ID（可在浏览器 F12 网络请求中查看），更新脚本中的映射表：
```python
BUILDING_MAP = {
    "全部": "",
    "你们的教学楼A": "1",
    "你们的教学楼B": "2",
    ...
}

PREFIX_MAP = {
    "你们的教学楼A": "A",
    "你们的教学楼B": "B",
    ...
}
```

### 3. 微调自习室过滤规则
根据本校教室的座位数与非自习场所命名规则，在 `IGNORE_KEYWORDS` 中添加需要过滤的关键词（如体育场、机房等），并设置适合本校的常规自习室最小座位数 `min_seats`。

> 💡 如果你在适配其他高校时遇到问题，或者成功适配了新学校，非常欢迎提交 Issue 或 Pull Request 分享给更多同学！

---

## 🔒 安全与免责声明

- 本脚本仅作为个人查询教务系统公开空闲教室数据的便利工具。
- 账号和密码仅保存在本地设备中，直接与学校官方统一身份认证服务通信，不存在任何第三方中转或上传。
- 请合理使用查询频率，本脚本已内置防频控保护，请勿进行高频恶意刷取，遵守校园网络秩序与自习纪律。

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。欢迎 Star ⭐️ 和提交 PR！

