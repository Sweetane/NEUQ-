#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东北大学秦皇岛分校 (NEUQ) 空教室极简查询脚本
专为考研自习与学生查空教室定制，支持自然语言识别、极简楼层分组排版、手机 Termux 部署与 OpenClaw 机器人调用。
"""

import sys
import os
import re
import json
import random
import base64
import argparse
import datetime
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== 个人配置区 (首次使用请在此配置您的学号与密码) ====================
DEFAULT_CONFIG = {
    "username": "YOUR_STUDENT_ID",    # 学号（例如：20230101）
    "password": "YOUR_PASSWORD",      # 统一身份认证密码
    "default_building": "工学馆",      # 默认教学楼（没说楼名时默认查工学馆）
    "min_seats": 80,                  # 工学馆常规自习室最小座位数（自动过滤8楼及小研讨室）
    "campus": "1"                     # 校区（1为学校本部）
}
# ====================================================================================

# ==================== 1. 纯 Python AES-128-CBC 加密 ====================
# 无需安装任何 C 编译扩展或 Rust 编译器，完美兼容 Android Termux

SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
]

RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

def _key_expansion_128(key_bytes):
    w = list(key_bytes)
    for i in range(4, 44):
        temp = w[(i - 1) * 4 : i * 4]
        if i % 4 == 0:
            temp = temp[1:] + temp[:1]
            temp = [SBOX[b] for b in temp]
            temp[0] ^= RCON[i // 4]
        for j in range(4):
            w.append(w[(i - 4) * 4 + j] ^ temp[j])
    return [w[i * 16 : (i + 1) * 16] for i in range(11)]

def _xtime(a):
    return ((a << 1) ^ 0x1b) & 0xff if (a & 0x80) else (a << 1)

def _aes_encrypt_block(block, round_keys):
    state = list(block)
    for i in range(16):
        state[i] ^= round_keys[0][i]

    for rnd in range(1, 10):
        state = [SBOX[b] for b in state]
        state = [
            state[0], state[5], state[10], state[15],
            state[4], state[9], state[14], state[3],
            state[8], state[13], state[2], state[7],
            state[12], state[1], state[6], state[11]
        ]
        new_state = [0] * 16
        for c in range(4):
            col = state[c * 4 : (c + 1) * 4]
            t = col[0] ^ col[1] ^ col[2] ^ col[3]
            u = col[0]
            col0 = col[0] ^ _xtime(col[0] ^ col[1]) ^ t
            col1 = col[1] ^ _xtime(col[1] ^ col[2]) ^ t
            col2 = col[2] ^ _xtime(col[2] ^ col[3]) ^ t
            col3 = col[3] ^ _xtime(col[3] ^ u) ^ t
            new_state[c * 4 : (c + 1) * 4] = [col0, col1, col2, col3]
        state = new_state
        for i in range(16):
            state[i] ^= round_keys[rnd][i]

    state = [SBOX[b] for b in state]
    state = [
        state[0], state[5], state[10], state[15],
        state[4], state[9], state[14], state[3],
        state[8], state[13], state[2], state[7],
        state[12], state[1], state[6], state[11]
    ]
    for i in range(16):
        state[i] ^= round_keys[10][i]

    return bytes(state)

def pure_aes_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)
    data = data + bytes([pad_len] * pad_len)
    round_keys = _key_expansion_128(key)
    ciphertext = b''
    prev = iv
    for i in range(0, len(data), 16):
        chunk = bytes(data[i + j] ^ prev[j] for j in range(16))
        enc = _aes_encrypt_block(chunk, round_keys)
        ciphertext += enc
        prev = enc
    return ciphertext

AES_CHARS = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'

def get_random_string(length):
    return ''.join(random.choice(AES_CHARS) for _ in range(length))

def encrypt_password(password: str, salt: str) -> str:
    if not salt:
        return password
    key = salt.strip().encode('utf-8')
    iv = get_random_string(16).encode('utf-8')
    data = (get_random_string(64) + password).encode('utf-8')
    ciphertext = pure_aes_cbc_encrypt(data, key, iv)
    return base64.b64encode(ciphertext).decode('utf-8')


# ==================== 2. 教务系统客户端类 ====================

BUILDING_MAP = {
    "全部": "",
    "工学馆": "1",
    "基础楼": "2",
    "综合实验楼": "3",
    "综合楼": "3",
    "地质楼": "4",
    "管理楼": "5",
    "大学会馆": "6",
    "旧实验楼": "7",
    "人文楼": "8",
    "科技楼": "9"
}

PREFIX_MAP = {
    "工学馆": "G",
    "基础楼": "J",
    "综合实验楼": "Z",
    "综合楼": "Z",
    "地质楼": "D",
    "管理楼": "M",
    "大学会馆": "H",
    "旧实验楼": "S",
    "人文楼": "R",
    "科技楼": "K"
}

IGNORE_KEYWORDS = [
    "停课", "腾讯会议", "场地", "球场", "体育", "跆拳道",
    "钉钉", "学习通", "超星", "雨课堂", "线上教学", "通知为准", "户外"
]

class NeuqClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def login(self):
        login_url = "https://ids.neuq.edu.cn/authserver/login?service=http%3A%2F%2Fjwxt.neuq.edu.cn%2Feams%2FhomeExt.action"
        try:
            resp = self.session.get(login_url, verify=False, timeout=15)
        except Exception as e:
            raise RuntimeError(f"连接统一身份认证服务器失败: {e}")

        soup = BeautifulSoup(resp.text, 'html.parser')
        salt_elem = soup.find(id='pwdDefaultEncryptSalt')
        salt = salt_elem.get('value') if salt_elem else None

        form = soup.find('form', id='casLoginForm') or soup.find('form')
        if not form:
            raise RuntimeError("未在页面中找到登录表单，可能是学校网络受限或服务维护。")

        execution = form.find('input', {'name': 'execution'}).get('value') if form.find('input', {'name': 'execution'}) else 'e1s1'
        lt = form.find('input', {'name': 'lt'}).get('value') if form.find('input', {'name': 'lt'}) else ''
        dllt = form.find('input', {'name': 'dllt'}).get('value') if form.find('input', {'name': 'dllt'}) else 'userNamePasswordLogin'

        encrypted_pwd = encrypt_password(self.password, salt)
        data = {
            'username': self.username,
            'password': encrypted_pwd,
            'lt': lt,
            'dllt': dllt,
            'execution': execution,
            '_eventId': 'submit',
            'rmShown': '1'
        }

        action = form.get('action')
        if not action.startswith('http'):
            action = f"https://ids.neuq.edu.cn{action}"

        try:
            post_resp = self.session.post(action, data=data, verify=False, allow_redirects=True, timeout=15)
        except Exception as e:
            raise RuntimeError(f"提交登录凭据失败: {e}")

        if "homeExt.action" in post_resp.url or "eams" in post_resp.url:
            return True
        else:
            soup_err = BeautifulSoup(post_resp.text, 'html.parser')
            err = soup_err.find(id='showErrorTip') or soup_err.find(class_='auth_error') or soup_err.find('span', {'id': 'msg'})
            msg = err.text.strip() if err else "未知错误（请检查学号或密码）"
            raise RuntimeError(f"登录失败: {msg}")

    def query_free_rooms(self, date_str: str, time_begin: int = 1, time_end: int = 2, building_name: str = "工学馆", campus_id: str = "1", page_size: int = 500):
        search_url = "http://jwxt.neuq.edu.cn/eams/classroom/apply/free!search.action"

        # 处理教学楼匹配
        building_id = ""
        if building_name:
            for b_name, b_id in BUILDING_MAP.items():
                if building_name in b_name or b_name in building_name:
                    building_id = b_id
                    break

        params = {
            "classroom.type.id": "",
            "classroom.campus.id": campus_id,
            "classroom.building.id": building_id,
            "seats": "",
            "classroom.name": "",
            "cycleTime.cycleCount": "1",
            "cycleTime.cycleType": "1",
            "cycleTime.dateBegin": date_str,
            "cycleTime.dateEnd": date_str,
            "roomApplyTimeType": "0",  # 0表示小节
            "timeBegin": str(time_begin),
            "timeEnd": str(time_end),
            "pageSize": str(page_size),
            "pageNo": "1"
        }

        headers = {
            "Referer": "http://jwxt.neuq.edu.cn/eams/classroom/apply/free.action"
        }

        # 尝试查询，若触发“请不要过快点击”则自动重试
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                r = self.session.post(search_url, data=params, headers=headers, timeout=20)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"查询请求超时或失败: {e}")
                time.sleep(1.0)
                continue

            if "请不要过快点击" in r.text:
                time.sleep(1.0)
                continue

            break

        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table', class_='gridtable')
        if not table:
            return []

        rooms = []
        rows = table.find_all('tr')
        for row in rows[1:]:
            cols = [c.text.strip() for c in row.find_all('td')]
            if len(cols) >= 6:
                seq, name, building, campus, config, capacity = cols[:6]
                try:
                    cap_num = int(capacity)
                except ValueError:
                    cap_num = 0

                rooms.append({
                    "name": name,
                    "building": building,
                    "campus": campus,
                    "config": config,
                    "capacity": cap_num
                })

        return rooms


# ==================== 3. 极简格式化与自习室提取 ====================

def abbreviate_room_name(name: str, building: str = "") -> str:
    """将教学楼名称缩写为字母，如 工学馆103 -> G103"""
    for k, v in PREFIX_MAP.items():
        if name.startswith(k):
            return name.replace(k, v, 1)
        if building == k and not name.startswith(v):
            return f"{v}{name}"
    return name

def get_floor_and_number(room_code: str):
    """
    提取房间的楼层和数字编号
    例如 G103 -> 楼层 1, 编号 103
         G725 -> 楼层 7, 编号 725
         G1107 -> 楼层 11, 编号 1107
    """
    m = re.search(r'([A-Za-z]+)?(\d+)', room_code)
    if m:
        num_str = m.group(2)
        num_val = int(num_str)
        if len(num_str) == 3:
            floor = int(num_str[0])
        elif len(num_str) == 4:
            floor = int(num_str[:2])
        else:
            floor = int(num_str[0])
        return floor, num_val
    return 999, 999

def format_clean_section(rooms, label: str, min_seats: int = 80, building_name: str = "工学馆"):
    """
    生成极简格式的单节次输出：
    1-2节：

    G103 G107 G112 G126 G129
    G207 G212 G221 G229
    ...
    """
    valid_rooms = []
    for r in rooms:
        name = r["name"]
        config = r["config"]
        cap = r["capacity"]

        # 过滤非自习、虚拟会议等
        if any(k in name for k in IGNORE_KEYWORDS) or any(k in config for k in IGNORE_KEYWORDS):
            continue

        # 过滤研讨室、小教室（默认常规自习教室 >= 80座）
        if min_seats > 0 and cap < min_seats:
            continue

        room_code = abbreviate_room_name(name, r["building"])
        floor, num_val = get_floor_and_number(room_code)

        # 工学馆排除 8 楼（均为小教研室）
        if building_name in ["工学馆", "G", ""] and floor == 8:
            continue

        valid_rooms.append((floor, num_val, room_code))

    if not valid_rooms:
        return f"{label}\n\n(无可用空教室)"

    # 按楼层分组
    floors = defaultdict(list)
    for floor, num_val, room_code in valid_rooms:
        floors[floor].append((num_val, room_code))

    lines = [label, ""]
    for fl in sorted(floors.keys()):
        # 楼层内按房间编号严格升序
        sorted_floor_rooms = sorted(floors[fl], key=lambda x: x[0])
        lines.append(" ".join(x[1] for x in sorted_floor_rooms))

    return "\n".join(lines)


# ==================== 4. 辅助函数与命令行处理 ====================

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_dir, "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg

def parse_natural_language(text: str):
    """
    智能解析用户的自然语言指令，提取日期、教学楼和节次
    例如：
    '明天工学馆1-4节连着没课的' -> date='tomorrow', building='工学馆', section='1-4'
    '第3节' -> section='3'
    '下午基础楼' -> section='afternoon', building='基础楼'
    """
    date = "today"
    building = ""
    section = ""

    # 1. 解析日期
    if any(k in text for k in ["后天", "后日"]):
        date = "after_tomorrow"
    elif any(k in text for k in ["明天", "明日", "次日"]):
        date = "tomorrow"
    elif any(k in text for k in ["今天", "今日", "当天"]):
        date = "today"
    else:
        # 尝试匹配 YYYY-MM-DD 或 MM-DD 或 M月D日
        m_date = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', text)
        if m_date:
            y, m, d = m_date.groups()
            date = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        else:
            m_short_date = re.search(r'(\d{1,2})[-/月](\d{1,2})', text)
            if m_short_date:
                now_y = datetime.date.today().year
                m, d = m_short_date.groups()
                date = f"{now_y}-{int(m):02d}-{int(d):02d}"

    # 2. 解析教学楼
    building_aliases = {
        "工学馆": ["工学馆", "工学", "工馆"],
        "基础楼": ["基础楼", "基础"],
        "综合实验楼": ["综合实验楼", "综合楼", "实验楼"],
        "管理楼": ["管理楼", "管楼"],
        "地质楼": ["地质楼", "地质"],
        "大学会馆": ["大学会馆", "会馆"],
        "人文楼": ["人文楼", "人文"],
        "科技楼": ["科技楼", "科技"]
    }
    for b_name, aliases in building_aliases.items():
        if any(alias in text for alias in aliases):
            building = b_name
            break

    # 3. 解析节次
    # 匹配连选区间：例如 1-4, 3到6, 5~8, 1至4
    m_range = re.search(r'(\d{1,2})\s*[-~至到与和]\s*(\d{1,2})', text)
    if m_range:
        section = f"{m_range.group(1)}-{m_range.group(2)}"
    else:
        # 匹配单节：例如 第3节, 3节
        m_single = re.search(r'第?\s*(\d{1,2})\s*节', text)
        if m_single:
            section = m_single.group(1)
        elif "上午" in text:
            section = "morning"
        elif "下午" in text:
            section = "afternoon"
        elif "晚上" in text or "晚自习" in text:
            section = "evening"
        elif "全天" in text or "整天" in text:
            section = "day"

    return date, building, section

def resolve_date(date_arg):
    today = datetime.date.today()
    if not date_arg or date_arg.lower() in ["today", "今", "今天"]:
        return today.strftime("%Y-%m-%d")
    elif date_arg.lower() in ["tomorrow", "明", "明天"]:
        return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_arg.lower() in ["after_tomorrow", "后", "后天"]:
        return (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    else:
        try:
            datetime.datetime.strptime(date_arg, "%Y-%m-%d")
            return date_arg
        except ValueError:
            return today.strftime("%Y-%m-%d")

def get_section_tasks(sec_arg):
    """
    根据参数返回要查询的节次任务列表：
    [(start, end, "1-2节："), ...]
    """
    sec_arg = str(sec_arg).strip().lower() if sec_arg else ""

    # 如果未指定节次，或指定为 all，默认输出全天常用自习节次（1-2节, 3-4节）或更多
    if not sec_arg or sec_arg in ["all", "全天"]:
        return [
            (1, 2, "1-2节："),
            (3, 4, "3-4节：")
        ]

    if sec_arg in ["day", "全天大课", "整天"]:
        return [
            (1, 2, "1-2节："),
            (3, 4, "3-4节："),
            (5, 6, "5-6节："),
            (7, 8, "7-8节："),
            (9, 10, "9-10节：")
        ]

    if sec_arg in ["morning", "上午"]:
        return [
            (1, 2, "1-2节："),
            (3, 4, "3-4节：")
        ]

    if sec_arg in ["afternoon", "下午"]:
        return [
            (5, 6, "5-6节："),
            (7, 8, "7-8节：")
        ]

    if sec_arg in ["evening", "晚上"]:
        return [
            (9, 10, "9-10节：")
        ]

    # 单独指定具体节次，例如 '1-2', '3-4'
    if "-" in sec_arg:
        parts = sec_arg.split("-")
        try:
            s_begin = max(1, min(12, int(parts[0])))
            s_end = max(s_begin, min(12, int(parts[1])))
            return [(s_begin, s_end, f"{s_begin}-{s_end}节：")]
        except ValueError:
            pass

    try:
        s = int(sec_arg)
        return [(s, s, f"第{s}节：")]
    except ValueError:
        return [(1, 2, "1-2节："), (3, 4, "3-4节：")]


def main():
    parser = argparse.ArgumentParser(description="东北大学秦皇岛分校 (NEUQ) 空教室极简查询脚本")
    parser.add_argument("query", nargs="?", default="", help="直接输入自然语言指令，例如：'明天工学馆1-4节'、'第3节'、'下午基础楼'")
    parser.add_argument("-u", "--user", help="学号（可由脚本配置、config.json 或环境变量提供）")
    parser.add_argument("-p", "--pwd", help="密码（可由脚本配置、config.json 或环境变量提供）")
    parser.add_argument("-d", "--date", default="", help="日期：today(默认)、tomorrow 或 YYYY-MM-DD")
    parser.add_argument("-s", "--section", default="", help="节次：1-2、3-4、1-4、3-6、5-8、morning、afternoon、evening、day")
    parser.add_argument("-b", "--building", default="", help="教学楼筛选：默认为工学馆（G），也支持基础楼、管理楼等")
    parser.add_argument("--min-seats", type=int, default=0, help="最小座位数限制（默认工学馆为80座）")
    parser.add_argument("--all-seats", action="store_true", help="不过滤小教室，显示所有座位")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    cfg = load_config()
    username = args.user or os.getenv("NEUQ_USERNAME") or cfg.get("username")
    password = args.pwd or os.getenv("NEUQ_PASSWORD") or cfg.get("password")

    if not username or not password or username == "YOUR_STUDENT_ID" or password == "YOUR_PASSWORD":
        print("=" * 50)
        print("❌ 提示：请先配置您的学号和教务系统密码！")
        print("👉 配置方式（非常简单）：")
        print("   打开 neuq_classroom.py 文件，在第 24 行填入您的学号和密码即可：")
        print("     \"username\": \"你的学号\",")
        print("     \"password\": \"你的统一身份认证密码\"")
        print("=" * 50)
        sys.exit(1)

    # 如果传入了自然语言句子，自动提取参数
    nl_date, nl_building, nl_sec = "", "", ""
    if args.query:
        nl_date, nl_building, nl_sec = parse_natural_language(args.query)

    target_date_raw = args.date or nl_date or "today"
    target_date = resolve_date(target_date_raw)
    building_filter = args.building or nl_building or cfg.get("default_building", "工学馆")
    target_sec = args.section or nl_sec or ""

    # 确定最小座位数：工学馆默认过滤80座以下，其他教学楼默认不过滤
    if args.all_seats:
        min_seats = 0
    elif args.min_seats > 0:
        min_seats = args.min_seats
    else:
        if building_filter in ["工学馆", "G"]:
            min_seats = cfg.get("min_seats", 80)
        else:
            min_seats = 0

    section_tasks = get_section_tasks(target_sec)

    try:
        client = NeuqClient(username, password)
        client.login()

        results_text_blocks = []
        json_results = []

        for idx, (sec_begin, sec_end, sec_label) in enumerate(section_tasks):
            if idx > 0:
                import time
                time.sleep(0.8)

            raw_rooms = client.query_free_rooms(
                date_str=target_date,
                time_begin=sec_begin,
                time_end=sec_end,
                building_name=building_filter
            )

            if args.json:
                json_results.append({
                    "section": sec_label.replace("：", ""),
                    "rooms": raw_rooms
                })
            else:
                block = format_clean_section(
                    rooms=raw_rooms,
                    label=sec_label,
                    min_seats=min_seats,
                    building_name=building_filter
                )
                results_text_blocks.append(block)

        if args.json:
            print(json.dumps(json_results, ensure_ascii=False, indent=2))
        else:
            final_output = "\n\n".join(results_text_blocks)
            print(final_output)

    except Exception as e:
        print(f"查询异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
