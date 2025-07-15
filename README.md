# DrissionPage MCP Server

基于 DrissionPage 和 FastMCP 的浏览器自动化 MCP 服务器，提供现代化、异步且强大的浏览器操作 API 供 AI 调用。

## 项目简介
![logo](img/DrissionPageMCP-logo.png)

DrissionPage MCP 是一个经过重构的、基于 DrissionPage 和 FastMCP 的浏览器自动化 MCP 服务器。它提供了一系列强大、稳定且易于使用的异步 API，让您能够轻松、高效地通过 AI 实现复杂的网页自动化操作。

### 主要特性 (v2.0.0)

- **完全异步**: 所有工具均为异步实现，避免阻塞，性能更佳。
- **统一的 API**: 将数十个零散的工具重构为少数几个核心、通用的工具，更易于学习和使用。
- **标准化的返回格式**: 所有工具都返回 `{"success": true, "data": ...}` 或 `{"success": false, "error": "..."}` 格式的 JSON 对象，便于程序化处理。
- **强大的定位器**: 直接利用 DrissionPage 强大的定位器语法（如 `tag:div`, `text:文本`, `#id`, `.class` 等），实现精准的元素定位。
- **内置的健壮性**: 自动处理了浏览器连接、元素查找、超时等常见异常。
- **丰富的功能**: 完整保留并优化了截图、执行 JS/CDP、文��上传下载、键盘模拟等高级功能。

---

## 安装与配置

请先将本仓库 `git clone` 到您的本地电脑。核心启动文件是 `main.py`。

### 1. 安装依赖

本项目推荐使用 `uv` 进行包管理。请在项目根目录运行以下命令安装所有必需的 Python 包：

```bash
uv pip install -r requirements.txt
```

### 2. 配置编辑器

您需要在您使用的编辑器（如 Cursor 或 VSCode）的 `settings.json` 文件中添加 MCP 服务配置。

**重要提示：** 下列配置中的路径为示例，您必须将其替换为您自己电脑上项目的**绝对路径**。

---

#### **macOS / Linux 用户配置**

复制以下 JSON 代码块。将 `"command"` 和 `"args"` 中的路径替换为您本地的实际路径。

```json
{
  "mcpServers": {
    "DrissionPageMCP": {
      "type": "stdio",
      "command": "/path/to/your/project/DrissionPageMCP/venv-DrissionPageMCP/bin/python",
      "args": [
        "/path/to/your/project/DrissionPageMCP/main.py"
      ]
    }
  }
}
```

---

#### **Windows 用户配置**

复制以下 JSON 代码块。将 `"command"` 和 `"args"` 中的路径替换为您本地的实际路径。**请注意，Windows 路径中的反斜杠 `\` 需要转义成 `\\`**。

```json
{
  "mcpServers": {
    "DrissionPageMCP": {
      "type": "stdio",
      "command": "C:\\path\\to\\your\\project\\DrissionPageMCP\\venv-DrissionPageMCP\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\your\\project\\DrissionPageMCP\\main.py"
      ]
    }
  }
}
```

---

### 3. 在编辑器中启用

将上述对应您操作系统的配置粘贴到编辑器的 `mcpServers` 设置中。如果 `mcpServers` 中已有其他配置，请确保 JSON 格式正确（在条目之间加逗号）。

配置完成后，您就可以在编辑器中选择并使用 `DrissionPageMCP` 了。

- [《官方MCP安装参考教程》](https://docs.trae.ai/ide/model-context-protocol)

---

## 可用工具列表 (v2.0.0)

以下是所有可通过 `DrissionPageMCP` 调用的工具方法。所有工具都返回一个标准化的 JSON 对象。

### 核心交互

| 方法名 | 功能描述 |
| :--- | :--- |
| `get_elements(locator)` | **(最常用)** 使用 DrissionPage 定位器字符串查找页面上的一个或多个元素，并返回它们的标签、文本和 HTML 信息。 |
| `click_element(locator, index=0)` | 点击由定位器找到的元素。如果找到多个，默认点击第一个（`index=0`）。 |
| `input_text(locator, text, index=0, clear=True)` | 向由定位器找到的元素输入文本。 |
| `send_key(key)` | 向当前页面发送一个特殊的键盘按键（如 `Enter`, `Delete`, `Page_Down` 等）。 |

### 浏览器与页面管理

| 方法名 | 功能描述 |
| :--- | :--- |
| `connect_or_open_browser(debug_port, ...)` | 连接到一个正在运行的浏览器或打开一个新浏览器。 |
| `new_tab(url)` | 打开一个新标签页并导航到指定的 URL。 |
| `get_page(url)` | 在当前标签页导航到一个新的 URL。 |
| `get_page_info()` | 返回当前标签页的信息 (URL, 标题, ID)。 |
| `wait(seconds)` | 等待指定的秒数，用于页面加载或动画。 |

### 数据提取

| 方法名 | 功能描述 |
| :--- | :--- |
| `get_body_text()` | 获取整个页面 `<body>` 的文本内容。 |
| `get_simplified_dom_tree()` | 获取当前页面的一个简化版 DOM 树，用于快速分析页面结构。 |
| `get_screenshot(as_file_path=None)` | 截取当前页面的屏幕。可选择保存为文件或直接返回图像数据。 |

### 文件处理

| 方法名 | 功能描述 |
| :--- | :--- |
| `download_file(url, path, rename=None)` | 从指定的 URL 下载文件到本地路径。 |
| `upload_file(locator, file_path, index=0)` | 查找一个文件上传元素并上传指定的文件。 |

### 高级功能

| 方法名 | 功能描述 |
| :--- | :--- |
| `run_js(js_code)` | 在当前页面上执行任意 JavaScript 代码并返回结果。 |
| `run_cdp(cmd, **cmd_args)` | 执行一条原始的 Chrome 开发者协议（CDP）命令，用于高级浏览器控制。 |
| `save_data_to_sqlite(data, ...)` | 将一个字典或列表保存到一个 SQLite 数据库文件中。 |
| `get_version()` | 获取此 MCP 工具的版本号。 |

---

## 更新日志

### **v2.0.0 (核心重构)**
- **精简项目**: 删除冗余的 `main-1.py`，统一入口为 `main.py`。
- **重构核心类**: 
  - 将 `DrissionPageMCP` 的所有方法改造为异步 (`async`)。
  - 统一所有工具的返回格式为 `{'success': bool, 'data': ..., 'error': ...}` 的 JSON 对象，增强了 API 的可预测性。
  - 合并了多个功能重复的工具（如元素查找、点击、输入），创建了更通用的 `get_elements`, `click_element`, `input_text` 工具。
  - 实现了工具的自动注册，简化了 `main.py` 的代码。
- **本地化**: 将所有代码注释、文档字符串和错误信息翻译为中文。
- **健壮性**: 修复了多个在服务器启动和工具调用时发现的 bug，并改进了错误处理。

### v0.1.3
- 增加 自动上传下载文件功能

### v0.1.2
- 增加 网页后台监听数据包的功能

### v0.1.0
- 初始版本发布
- 实现基本的浏览器控制功能
- 提供元素操作 API