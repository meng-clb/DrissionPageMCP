#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import inspect
from typing import Any, Literal

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.common import Keys
from mcp.server.fastmcp import FastMCP, Image

from CodeBox import domTreeToJson
from ToolBox import save_dict_to_sqlite, get_element_in_iframe

# --- 常量与配置 ---

SERVER_INSTRUCTIONS = """
DrissionPage MCP v2.2 (Shadow DOM Support)
- This server uses a context management system to interact with the main page, shadow DOMs, and iframes.
- Start with `connect_or_open_browser`. This creates the 'main' context.
- To interact with an element inside a shadow DOM, first create a context for it using `get_shadow_root_context`.
- To interact with an iframe, first create a context for it using `get_frame_context`. You can search for iframes within shadow DOM contexts.
- All element-based tools (`get_elements`, `click_element`, etc.) accept an optional `context_name` parameter.
- If `context_name` is omitted, the tool operates on the 'main' context by default.
- All tools return a standard JSON object: {"success": true, "data": ...} or {"success": false, "error": "..."}.
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
        self.contexts: dict[str, Any] = {}

    def get_context(self, context_name: str = 'main'):
        """从上下文字典中获取可操作的对象（Tab 或 Frame），并确保其处于正确的模式。"""
        if not self.browser:
            raise ConnectionError("浏览器未连接。请先使用 'connect_or_open_browser'。")
        context = self.contexts.get(context_name)
        if not context:
            raise ValueError(f"上下文 '{context_name}' 不存在。可用的上下文: {list(self.contexts.keys())}")
        
        if hasattr(context, 'mode') and context.mode != 'b':
            context.change_mode('d', go=False)
            
        return context

    # --- 浏览器和上下文管理 ---

    async def get_version(self) -> dict:
        """获取此 MCP 工具的版本号。"""
        return success("2.2.0-final")

    async def connect_or_open_browser(self, debug_port: int = 9222, browser_path: str = None, headless: bool = False) -> dict:
        """
        连接到正在运行的浏览器或打开一个新浏览器。
        这将初始化一个名为 'main' 的主操作上下文。
        
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
            co.headless(headless)
            
            self.browser = await run_sync(Chromium, co)
            main_tab = self.browser.latest_tab
            self.contexts = {'main': main_tab}
            
            return success({
                "browser_address": self.browser.address,
                "main_context_title": main_tab.title,
                "main_context_id": main_tab.tab_id,
                "active_contexts": list(self.contexts.keys())
            })
        except Exception as e:
            return error(f"连接或打开浏览器失败：{e}")

    async def get_frame_context(self, locator: str, new_context_name: str, from_context: str = 'main') -> dict:
        """
        获取一个 iframe 并将其作为一个新的操作上下文保存起来。
        这完美复刻了 DrissionPage 的原生 iframe 操作模式。
        
        :param locator: 用于查找 iframe 的 DrissionPage 定位器。
        :param new_context_name: 为这个 iframe 上下文指定一个新名称，供后续操作使用。
        :param from_context: 从哪个已存在的上下文中查找这个 iframe，默认为 'main'。
        :return: 成功或失败的字典，包含当前所有可用的上下文列表。
        """
        try:
            parent_context = self.get_context(from_context)
            iframe_obj = await run_sync(parent_context.get_frame, locator)
            
            if not iframe_obj:
                return error(f"在上下文 '{from_context}' 中未能找到与定位器 '{locator}' 匹配的 iframe。")

            self.contexts[new_context_name] = iframe_obj
            return success({
                "message": f"已成功创建名为 '{new_context_name}' 的 iframe 上下文。",
                "active_contexts": list(self.contexts.keys())
            })
        except Exception as e:
            return error(f"获取 iframe 上下文失败：{e}")

    async def get_shadow_root_context(self, locator: str, new_context_name: str, from_context: str = 'main') -> dict:
        """
        获取一个元素的 shadow-root 并将其保存为一个新的操作上下文。
        这是处理封装在 Shadow DOM 中的元素的正确方法。
        
        :param locator: 用于查找 shadow root 宿主元素的 DrissionPage 定位器。
        :param new_context_name: 为这个 shadow root 上下文指定一个新名称。
        :param from_context: 从哪个已存在的上下文中查找宿主元素，默认为 'main'。
        :return: 成功或失败的字典，包含当前所有可用的上下文列表。
        """
        try:
            parent_context = self.get_context(from_context)
            host_element = await run_sync(parent_context.ele, locator)
            
            if not host_element:
                return error(f"在上下文 '{from_context}' 中未能找到宿主元素 '{locator}'。")

            shadow_root_obj = await run_sync(getattr, host_element, 'shadow_root')
            
            if not shadow_root_obj:
                return error(f"元素 '{locator}' 没有 shadow-root。")

            self.contexts[new_context_name] = shadow_root_obj
            return success({
                "message": f"已成功创建名为 '{new_context_name}' 的 shadow-root 上下文。",
                "active_contexts": list(self.contexts.keys())
            })
        except Exception as e:
            return error(f"获取 shadow-root 上下文失败：{e}")

    async def new_tab(self, url: str) -> dict:
        """打开一个新标签页并导航到指定的 URL。

        注意：返回一个标准的 JSON 对象：{"success": true/false, "data": ..., "error": "..."}。"""
        try:
            main_context = self.get_context('main')
            tab = await run_sync(main_context.new_tab, url)
            self.contexts['main'] = self.browser.latest_tab
            return success({"title": tab.title, "tab_id": tab.tab_id, "url": tab.url, "message": "主上下文已更新为新标签页。"})
        except Exception as e:
            return error(f"打开新标签页失败：{e}")

    async def get_page(self, url: str, context_name: str = 'main') -> dict:
        """
        在指定的上下文（标签页或 iframe）中导航到一个新的 URL。
        
        :param url: 要导航到的 URL。
        :param context_name: 要在其上执行导航的上下文名称。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context(context_name)
            await run_sync(context.get, url)
            return success({"title": context.title, "url": context.url})
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中导航到 URL 失败：{e}")

    async def wait(self, seconds: int) -> dict:
        """等待指定的秒数。

        注意：返回一个标准的 JSON 对象：{"success": true/false, "data": ..., "error": "..."}。"""
        try:
            await asyncio.sleep(seconds)
            return success(f"已等待 {seconds} 秒。")
        except Exception as e:
            return error(f"等待失败：{e}")

    # --- 元素交互 ---

    async def get_elements(self, locator: str, context_name: str = 'main') -> dict:
        """
        在指定的上下文中，使用 DrissionPage 定位器查找元素。
        
        :param locator: DrissionPage 定位器字符串。
        :param context_name: 要在其中查找元素的上下文名称。
        :return: 包含元素信息的字典列表。
        """
        try:
            context = self.get_context(context_name)
            elements = await run_sync(context.eles, locator)
            result = []
            for el in elements:
                element_info = {"tag": el.tag, "html": el.inner_html}
                try:
                    element_info["text"] = el.text
                except AttributeError:
                    element_info["text"] = None
                result.append(element_info)
            return success(result)
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中使用定位器 '{locator}' 获取元素失败：{e}")

    async def click_element(self, locator: str, index: int = 0, context_name: str = 'main') -> dict:
        """
        在指定的上下文中，点击由定位器找到的元素。
        
        :param locator: 用于查找元素的定位器字符串。
        :param index: 如果找到多个元素，要点击的元素的索引。
        :param context_name: 要在其中执行点击操作的上下文名称。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context(context_name)
            elements = await run_sync(context.eles, locator)
            if not elements:
                return error(f"在上下文 '{context_name}' 中未找到定位器为 '{locator}' 的元素。")
            if index >= len(elements):
                return error(f"索引 {index} 超出范围。在 '{context_name}' 中为 '{locator}' 找到了 {len(elements)} 个元素。")
            
            await run_sync(elements[index].click)
            return success(f"已在上下文 '{context_name}' 中点击定位器为 '{locator}' 的第 {index} 个元素。")
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中点击元素失败：{e}")

    async def input_text(self, locator: str, text: str, index: int = 0, clear: bool = True, context_name: str = 'main') -> dict:
        """
        在指定的上下文中，向由定位器找到的元素输入文本。
        
        :param locator: 用于查找元素的定位器字符串。
        :param text: 要输入的文本。
        :param index: 如果找到多个元素，要操作的元素的索引。
        :param clear: 输入前是否清除输入框。
        :param context_name: 要在其中执行输入操作的上下文名称。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context(context_name)
            elements = await run_sync(context.eles, locator)
            if not elements:
                return error(f"在上下文 '{context_name}' 中未找到定位器为 '{locator}' 的元素。")
            if index >= len(elements):
                return error(f"索引 {index} 超出范围。在 '{context_name}' 中为 '{locator}' 找到了 {len(elements)} 个元素。")

            await run_sync(elements[index].input, text, clear=clear)
            return success(f"已在上下文 '{context_name}' 中向定位器为 '{locator}' 的第 {index} 个元素输入文本。")
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中输入文本失败：{e}")

    async def send_key(self, key: Literal[tuple(KEY_MAPPING.keys())], context_name: str = 'main') -> dict:
        """
        向指定的上下文发送一个特殊的按键。
        
        :param key: 要发送的特殊按键。
        :param context_name: 要接收按键的上下文名称。
        :return: 成功或失败的字典。
        """
        if key not in KEY_MAPPING:
            return error(f"无效的按键 '{key}'。可用按键: {list(KEY_MAPPING.keys())}")
        try:
            context = self.get_context(context_name)
            await run_sync(context.actions.type, KEY_MAPPING[key])
            return success(f"已向上下文 '{context_name}' 发送按键 '{key}'。")
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中发送按键失败：{e}")

    # --- 数据提取与页面信息 ---

    async def get_page_info(self, context_name: str = 'main') -> dict:
        """
        返回指定上下文的信息 (URL, 标题等)。
        
        :param context_name: 要获取信息的上下文名称。
        :return: 包含上下文信息的字典。
        """
        try:
            context = self.get_context(context_name)
            info = {"url": context.url, "title": context.title}
            if hasattr(context, 'tab_id'):
                info["id"] = context.tab_id
            return success(info)
        except Exception as e:
            return error(f"获取上下文 '{context_name}' 的信息失败：{e}")

    async def get_body_text(self, context_name: str = 'main') -> dict:
        """
        获取指定上下文整个 body 的文本内容。
        
        :param context_name: 要获取 body 文本的上下文名称。
        :return: 包含 body 文本的字典。
        """
        try:
            context = self.get_context(context_name)
            text = await run_sync(context.ele, 't:body').text
            return success(text)
        except Exception as e:
            return error(f"获取上下文 '{context_name}' 的 body 文本失败：{e}")

    async def get_simplified_dom_tree(self, context_name: str = 'main') -> dict:
        """
        返回指定上下文 DOM 树的简化 JSON 表示。
        
        :param context_name: 要获取 DOM 树的上下文名称。
        :return: 包含 DOM 树的字典。
        """
        try:
            context = self.get_context(context_name)
            dom_tree = await run_sync(context.run_js, domTreeToJson)
            return success(dom_tree)
        except Exception as e:
            return error(f"获取上下文 '{context_name}' 的简化 DOM 树失败：{e}")

    async def get_screenshot(self, as_file_path: str = None, context_name: str = 'main') -> Any:
        """
        捕获指定上下文的屏幕截图。
        
        :param as_file_path: 如果提供，则将屏幕截图保存到此路径。否则，返回字节流。
        :param context_name: 要截取屏幕的上下文名称。
        :return: 包含文件路径的字典或 Image 对象。
        """
        try:
            context = self.get_context(context_name)
            if as_file_path:
                path = await run_sync(context.get_screenshot, path=as_file_path)
                return success({"file_path": path})
            else:
                jpeg_bytes = await run_sync(context.get_screenshot, as_bytes='jpeg')
                return Image(data=jpeg_bytes, format="jpeg")
        except Exception as e:
            return error(f"获取上下文 '{context_name}' 的屏幕截图失败：{e}")

    # --- 高级功能 & CDP ---

    async def run_js(self, js_code: str, context_name: str = 'main') -> dict:
        """
        在指定的上下文上执行 JavaScript 代码。
        
        :param js_code: 要执行的 JavaScript 代码。
        :param context_name: 要在其中执行 JS 的上下文名称。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context(context_name)
            result = await run_sync(context.run_js, js_code)
            return success(result)
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中执行 JavaScript 失败：{e}")

    async def run_cdp(self, cmd: str, context_name: str = 'main', **cmd_args) -> dict:
        """
        在指定的上下文上执行一个原始的 Chrome DevTools Protocol 命令。
        
        :param cmd: CDP 命令。
        :param context_name: 要在其中执行 CDP 的上下文名称。
        :param cmd_args: CDP 命令的参数。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context(context_name)
            result = await run_sync(context.run_cdp, cmd, **cmd_args)
            return success(result)
        except Exception as e:
            return error(f"在上下文 '{context_name}' 中执行 CDP 命令 '{cmd}' 失败：{e}")

    # --- 文件处理 ---

    async def download_file(self, url: str, path: str, rename: str = None) -> dict:
        """
        从 URL 下载文件。此操作在主上下文中执行。
        
        :param url: 要下载的文件的 URL。
        :param path: 保存文件的路径。
        :param rename: 重命名文件的名称。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context('main')
            result = await run_sync(context.download, file_url=url, save_path=path, rename=rename)
            return success({"download_result": str(result)})
        except Exception as e:
            return error(f"文件下载失败：{e}")

    async def upload_file(self, locator: str, file_path: str, index: int = 0, context_name: str = 'main') -> dict:
        """
        在指定的上下文中，通过与文件输入元素交互来上传文件。
        
        :param locator: 用于查找元素的定位器字符串。
        :param file_path: 要上传的文件的路径。
        :param index: 如果找到多个元素，要操作的元素的索引。
        :param context_name: 要在其中执行上传操作的上下文名称。
        :return: 成功或失败的字典。
        """
        try:
            context = self.get_context(context_name)
            elements = await run_sync(context.eles, locator)
            if not elements:
                return error(f"在上下文 '{context_name}' 中未找到定位器为 '{locator}' 的元素。")
            if index >= len(elements):
                return error(f"索引 {index} 超出范围。在 '{context_name}' 中为 '{locator}' 找到了 {len(elements)} 个元素。")
            
            target_element = elements[index]
            await run_sync(target_element.set.upload_files, file_path)
            await run_sync(target_element.click, by_js=True)
            return success(f"文件 '{file_path}' 已上传到上下文 '{context_name}' 中定位器为 '{locator}' 的元素。")
        except Exception as e:
            return error(f"文件上传失败：{e}")

    async def close_browser(self) -> dict:
        """关闭浏览器实例并清除所有上下文。"""
        try:
            if self.browser:
                await run_sync(self.browser.close)
                self.browser = None
                self.contexts = {}
                return success("浏览器已成功关闭。")
            else:
                return success("浏览器未连接，无需关闭。")
        except Exception as e:
            return error(f"关闭浏览器失败：{e}")

    # --- 新增的测试工具 ---
    async def run_iframe_test(self) -> dict:
        """
        一个用于测试跨域 iframe 元素获取的端到端工具。
        它会导航到测试页面，并尝试获取 iframe 内的特定元素。
        """
        try:
            main_tab = self.get_context('main')
            
            test_url = 'http://DrissionPage.cn/demos/iframe_diff_domain.html'
            await run_sync(main_tab.get, test_url)
            
            iframe_locator = 't:iframe'
            element_locator = '网易首页'
            
            # 调用我们之前创建的同步工具函数
            element = await run_sync(get_element_in_iframe, main_tab, iframe_locator, element_locator)
            
            if element:
                return success({
                    "message": "成功在 iframe 内获取到元素。",
                    "element_text": element.text,
                    "element_link": element.link
                })
            else:
                return error("未能在 iframe 内找到目标元素。")
                
        except Exception as e:
            return error(f"iframe 测试执行失败：{e}")


# --- MCP 服务器设置 ---

mcp = FastMCP("DrissionPageMCP", log_level="ERROR", instructions=SERVER_INSTRUCTIONS)
controller = DrissionPageMCP()

# --- 自动工具注册 ---

def register_tools():
    """自动将控制器的所有公共方法注册为 MCP 工具。"""
    for name, method in inspect.getmembers(DrissionPageMCP, predicate=inspect.iscoroutinefunction):
        if not name.startswith('_'):
            bound_method = getattr(controller, name)
            mcp.add_tool(fn=bound_method, name=name, description=inspect.getdoc(method))

    # 手动添加来自其他模块的工具
    async def save_to_db_async(data, db_path='data.db', table_name='my_table', append=False):
        try:
            result = await run_sync(save_dict_to_sqlite, data, db_path, table_name, append)
            return success(result)
        except Exception as e:
            return error(f"保存到数据库失败：{e}")
            
    mcp.add_tool(
        fn=save_to_db_async,
        name="save_data_to_sqlite",
        description="将字典或字典列表保存到 SQLite 数据库表中。可以指定 `append=True` 来追加数据。"
    )

def main():
    """初始化并运行 MCP 服务器。"""
    print("正在初始化 DrissionPage MCP 服务器...")

    async def setup_and_list_tools():
        """在一个临时事件循环中注册并列出工具。"""
        register_tools()
        return await mcp.list_tools()

    # 在单独的事件循环中运行设置函数
    tool_list = asyncio.run(setup_and_list_tools())
    print(f"已注册 {len(tool_list)} 个工具。")
    
    print("DrissionPage MCP 服务器正在运行...")
    # mcp.run 是一个阻塞调用，它管理自己的事件循环
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
