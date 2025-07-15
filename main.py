#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import inspect
from typing import Any, Literal

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.common import Keys
from DrissionPage.items import ChromiumTab
from mcp.server.fastmcp import FastMCP, Image

from CodeBox import domTreeToJson
from ToolBox import save_dict_to_sqlite

# --- 常量与配置 ---

SERVER_INSTRUCTIONS = """
DrissionPage MCP 是一个强大的浏览器自动化服务器。
- 开始前，请使用 `connect_or_open_browser` 连接或打开浏览器。
- 在与元素交互前，请使用 `get_elements` 查找元素。
- 使用定位器，例如 'tag:div', 'text:点击我', '#elementID', '.elementClass'。
- 所有工具都返回一个 JSON 对象：{"success": true, "data": ...} 或 {"success": false, "error": "..."}。
"""

KEY_MAPPING = {
    "Enter": Keys.ENTER, "Backspace": Keys.BACKSPACE, "HOME": Keys.HOME,
    "END": Keys.END, "PAGE_UP": Keys.PAGE_UP, "PAGE_DOWN": Keys.PAGE_DOWN,
    "DOWN": Keys.DOWN, "UP": Keys.UP, "LEFT": Keys.LEFT, "RIGHT": Keys.RIGHT,
    "ESC": Keys.ESCAPE, "Ctrl+C": Keys.CTRL_C, "Ctrl+V": Keys.CTRL_V,
    "Ctrl+A": Keys.CTRL_A, "Delete": Keys.DELETE,
}

# --- 辅助函数 ---

def run_sync(func, *args, **kwargs):
    """在单独的线程中运行同步函数，以避免阻塞 asyncio 事件循环。"""
    return asyncio.to_thread(func, *args, **kwargs)

def success(data: Any = None) -> dict:
    """返回标准化的成功响应。"""
    return {"success": True, "data": data}

def error(message: str) -> dict:
    """返回标准化的错误响应。"""
    return {"success": False, "error": message}

# --- 核心控制器类 ---

class DrissionPageMCP:
    """一个封装了 MCP 服务器浏览器控制逻辑的类。"""

    def __init__(self):
        self.browser: Chromium | None = None
        self.response_listener_data = []
        self.cdp_event_data = []

    @property
    def latest_tab(self) -> ChromiumTab:
        """获取浏览器的最新标签页，如果不可用则引发错误。"""
        if not self.browser:
            raise ConnectionError("浏览器未连接。请先使用 'connect_or_open_browser'。")
        return self.browser.latest_tab

    # --- 浏览器管理 ---

    async def get_version(self) -> dict:
        """获取此 MCP 工具的版本号。"""
        return success("1.1.0-refactored-zh")

    async def connect_or_open_browser(self, debug_port: int = 9222, browser_path: str = None, headless: bool = False) -> dict:
        """
        连接到正在运行的浏览器或打开一个新浏览器。
        
        :param debug_port: 浏览器的调试端口。
        :param browser_path: 浏览器可执行文件的路径。
        :param headless: 是否以无头模式运行。
        :return: 包含浏览器信息的字典。
        """
        try:
            co = ChromiumOptions()
            co.set_local_port(debug_port)
            if browser_path:
                co.set_browser_path(browser_path)
            if headless:
                co.headless(True)
            
            self.browser = await run_sync(Chromium, co)
            tab = self.latest_tab
            
            return success({
                "browser_address": self.browser.address,
                "latest_tab_title": tab.title,
                "latest_tab_id": tab.tab_id,
            })
        except Exception as e:
            return error(f"连接或打开浏览器失败：{e}")

    async def new_tab(self, url: str) -> dict:
        """打开一个新标签页并导航到指定的 URL。"""
        try:
            tab = await run_sync(self.latest_tab.new_tab, url)
            return success({"title": tab.title, "tab_id": tab.tab_id, "url": tab.url})
        except Exception as e:
            return error(f"打开新标签页失败：{e}")

    async def get_page(self, url: str) -> dict:
        """将当前标签页导航到一个新的 URL。"""
        try:
            await run_sync(self.latest_tab.get, url)
            tab = self.latest_tab
            return success({"title": tab.title, "tab_id": tab.tab_id, "url": tab.url})
        except Exception as e:
            return error(f"导航到 URL 失败：{e}")

    async def wait(self, seconds: int) -> dict:
        """等待指定的秒数。"""
        try:
            await asyncio.sleep(seconds)
            return success(f"已等待 {seconds} 秒。")
        except Exception as e:
            return error(f"等待失败：{e}")

    # --- 元素交互 ---

    async def get_elements(self, locator: str) -> dict:
        """
        使用 DrissionPage 定位器字符串在页面上查找元素。
        
        :param locator: DrissionPage 定位器字符串 (例如, 'tag:div', '#id', '.class', 'text:content')。
        :return: 包含元素信息的字典列表。
        """
        try:
            elements = await run_sync(self.latest_tab.eles, locator)
            result = [
                {"tag": el.tag, "text": el.text, "html": el.inner_html}
                for el in elements
            ]
            return success(result)
        except Exception as e:
            return error(f"使用定位器 '{locator}' 获取元素失败：{e}")

    async def click_element(self, locator: str, index: int = 0) -> dict:
        """
        点击由定位器找到的元素。
        
        :param locator: 用于查找元素的定位器字符串。
        :param index: 如果找到多个元素，要点击的元素的索引。
        :return: 成功或失败的字典。
        """
        try:
            elements = await run_sync(self.latest_tab.eles, locator)
            if not elements:
                return error(f"未找到定位器为 '{locator}' 的元素。")
            if index >= len(elements):
                return error(f"索引 {index} 超出范围。为定位器 '{locator}' 找到了 {len(elements)} 个元素。")
            
            await run_sync(elements[index].click)
            return success(f"已点击定位器为 '{locator}' 的第 {index} 个元素。")
        except Exception as e:
            return error(f"点击定位器为 '{locator}' 的元素失败：{e}")

    async def input_text(self, locator: str, text: str, index: int = 0, clear: bool = True) -> dict:
        """
        向由定位器找到的元素输入文本。
        
        :param locator: 用于查找元素的定位器字符串。
        :param text: 要输入的文本。
        :param index: 如果找到多个元素，要操作的元素的索引。
        :param clear: 输入前是否清除输入框。
        :return: 成功或失败的字典。
        """
        try:
            elements = await run_sync(self.latest_tab.eles, locator)
            if not elements:
                return error(f"未找到定位器为 '{locator}' 的元素。")
            if index >= len(elements):
                return error(f"索引 {index} 超出范围。为定位器 '{locator}' 找到了 {len(elements)} 个元素。")

            await run_sync(elements[index].input, text, clear=clear)
            return success(f"已向定位器为 '{locator}' 的第 {index} 个元素输入文本。")
        except Exception as e:
            return error(f"向定位器为 '{locator}' 的元素输入文本失败：{e}")

    async def send_key(self, key: Literal[tuple(KEY_MAPPING.keys())]) -> dict:
        """向当前标签页发送一个特殊的按键。"""
        if key not in KEY_MAPPING:
            return error(f"无效的按键 '{key}'。可用按键: {list(KEY_MAPPING.keys())}")
        try:
            await run_sync(self.latest_tab.actions.type, KEY_MAPPING[key])
            return success(f"已发送按键 '{key}'。")
        except Exception as e:
            return error(f"发送按键 '{key}' 失败：{e}")

    # --- 数据提取与页面信息 ---

    async def get_page_info(self) -> dict:
        """返回当前标签页的信息 (URL, 标题等)。"""
        try:
            tab = self.latest_tab
            info = {"url": tab.url, "title": tab.title, "id": tab.tab_id}
            return success(info)
        except Exception as e:
            return error(f"获取页面信息失败：{e}")

    async def get_body_text(self) -> dict:
        """获取整个页面 body 的文本内容。"""
        try:
            text = await run_sync(self.latest_tab.ele, 't:body').text
            return success(text)
        except Exception as e:
            return error(f"获取 body 文本失败：{e}")

    async def get_simplified_dom_tree(self) -> dict:
        """返回 DOM 树的简化 JSON 表示。"""
        try:
            dom_tree = await run_sync(self.latest_tab.run_js, domTreeToJson)
            return success(dom_tree)
        except Exception as e:
            return error(f"获取简化 DOM 树失败：{e}")

    async def get_screenshot(self, as_file_path: str = None) -> Any:
        """
        捕获当前标签页的屏幕截图。
        
        :param as_file_path: 如果提供，则将屏幕截图保存到此路径。否则，返回字节流。
        :return: 包含文件路径的字典或 Image 对象。
        """
        try:
            if as_file_path:
                path = await run_sync(self.latest_tab.get_screenshot, path=as_file_path)
                return success({"file_path": path})
            else:
                jpeg_bytes = await run_sync(self.latest_tab.get_screenshot, as_bytes='jpeg')
                return Image(data=jpeg_bytes, format="jpeg")
        except Exception as e:
            return error(f"获取屏幕截图失败：{e}")

    # --- 高级功能 & CDP ---

    async def run_js(self, js_code: str) -> dict:
        """在当前标签页上执行 JavaScript 代码。"""
        try:
            result = await run_sync(self.latest_tab.run_js, js_code)
            return success(result)
        except Exception as e:
            return error(f"JavaScript 执行失败：{e}")

    async def run_cdp(self, cmd: str, **cmd_args) -> dict:
        """执行一个原始的 Chrome DevTools Protocol 命令。"""
        try:
            result = await run_sync(self.latest_tab.run_cdp, cmd, **cmd_args)
            return success(result)
        except Exception as e:
            return error(f"CDP 命令 '{cmd}' 失败：{e}")

    # --- 文件处理 ---

    async def download_file(self, url: str, path: str, rename: str = None) -> dict:
        """从 URL 下载文件。"""
        try:
            result = await run_sync(self.latest_tab.download, file_url=url, save_path=path, rename=rename)
            return success({"download_result": str(result)})
        except Exception as e:
            return error(f"文件下载失败：{e}")

    async def upload_file(self, locator: str, file_path: str, index: int = 0) -> dict:
        """通过与文件输入元素交互来上传文件。"""
        try:
            elements = await run_sync(self.latest_tab.eles, locator)
            if not elements:
                return error(f"未找到定位器为 '{locator}' 的元素。")
            if index >= len(elements):
                return error(f"索引 {index} 超出范围。为定位器 '{locator}' 找到了 {len(elements)} 个元素。")
            
            target_element = elements[index]
            await run_sync(target_element.set.upload_files, file_path)
            await run_sync(target_element.click, by_js=True) # 某些输入框在设置路径后需要点击
            return success(f"文件 '{file_path}' 已上传到定位器为 '{locator}' 的元素。")
        except Exception as e:
            return error(f"文件上传失败：{e}")


# --- MCP 服务器设置 ---

mcp = FastMCP("DrissionPageMCP", log_level="ERROR", instructions=SERVER_INSTRUCTIONS)
controller = DrissionPageMCP()

# --- 自动工具注册 ---

def register_tools():
    """自动将控制器的所有公共方法注册为 MCP 工具。"""
    for name, method in inspect.getmembers(DrissionPageMCP, predicate=inspect.iscoroutinefunction):
        if not name.startswith('_'):
            # 为每个工具的描述添加关于返回格式的说明
            doc = inspect.getdoc(method)
            if doc:
                doc += '\n\n注意：返回一个标准的 JSON 对象：{"success": true/false, "data": ..., "error": "..."}。'
            
            # We need to bind the method to the instance `controller`
            bound_method = getattr(controller, name)
            mcp.add_tool(fn=bound_method, name=name, description=doc)

    # 手动添加来自其他模块的工具
    async def save_to_db_async(data, db_path='data.db', table_name='my_table'):
        try:
            result = await run_sync(save_dict_to_sqlite, data, db_path, table_name)
            return success(result)
        except Exception as e:
            return error(f"保存到数��库失败：{e}")
            
    mcp.add_tool(
        fn=save_to_db_async,
        name="save_data_to_sqlite",
        description="将字典或字典列表保存到 SQLite 数据库表中。"
    )

def main():
    """初始化并运行 MCP 服务器。"""
    print("正在初始化 DrissionPage MCP 服务器...")
    register_tools()
    
    # To get the list of tools, we need to run the async function separately
    tool_list = asyncio.run(mcp.list_tools())
    print(f"已注册 {len(tool_list)} 个工具。")
    
    print("DrissionPage MCP 服务器正在运行...")
    # mcp.run is a blocking call that manages its own event loop
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()