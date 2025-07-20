# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sqlite3
import json
import os

def save_dict_to_sqlite(data, db_path='data.db', table_name='my_table', append=False):
    """
    将字典或JSON字符串保存到SQLite数据库中。
    
    参数:
        data (dict, list of dict, or str): 字典、字典列表或JSON字符串。
        db_path (str): SQLite数据库文件的路径。
        table_name (str): 要操作的表的名称。
        append (bool): 如果为True，则向现有表追加数据；否则，覆盖表。
    """
    # 如果是JSON字符串，则解析为Python对象
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError("提供的字符串不是有效的JSON。")
    
    # 如果是单个字典，则转换为列表
    if isinstance(data, dict):
        data = [data]

    if not data or not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("输入必须是字典、字典列表或有效的JSON字符串。")

    # 提取列名（以第一个字典为准）
    columns = list(data[0].keys())
    
    # 连接到数据库
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone()

        if not append or not table_exists:
            # 覆盖模式：删除旧表并创建新表
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            col_defs = ', '.join([f'"{col}" TEXT' for col in columns])
            cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
            action_message = "数据已覆盖写入"
        else:
            # 追加模式：获取现有列
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            existing_columns = [row[1] for row in cursor.fetchall()]
            columns = [col for col in columns if col in existing_columns]
            action_message = "数据已追加到"

        # 插入数据
        if columns:
            placeholders = ', '.join(['?' for _ in columns])
            # 先构建列名字符串，避免在 f-string 中使用复杂的表达式
            column_names = ", ".join(f'"{col}"' for col in columns)
            insert_query = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
            for row in data:
                values = tuple(str(row.get(col, '')) for col in columns)
                cursor.execute(insert_query, values)

        # 提交更改
        conn.commit()

    return f"{action_message} {db_path} 的表 {table_name} 中。"

def get_element_in_iframe(tab, iframe_locator, element_locator):
    """
    获取跨域 iframe 内的元素。

    :param tab: DrissionPage 的 Tab 对象。
    :param iframe_locator: 用于定位 iframe 的定位符字符串。
    :param element_locator: 用于在 iframe 内部定位目标元素的定位符字符串。
    :return: 如果找到，返回 ChromiumElement 对象；否则返回 None。
    """
    print(f"开始查找 iframe，使用定位符: {iframe_locator}")
    iframe = tab.get_frame(iframe_locator)

    if not iframe:
        print(f"错误：无法找到 iframe。")
        return None

    print(f"成功找到 iframe (src: {iframe.attr('src')})。")
    print(f"开始在 iframe 内查找元素，使用定位符: {element_locator}")
    
    element = iframe.ele(element_locator)

    if not element:
        print(f"错误：在 iframe 内无法找到元素。")
        return None
        
    print("成功在 iframe 内找到元素。")
    return element