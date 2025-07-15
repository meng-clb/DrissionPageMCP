# DrissionPage MCP Server -- 骚神出品

基于DrissionPage和FastMCP的浏览器自动化MCP服务器，提供丰富的浏览器操作API供AI调用。

## 项目简介
![logo](img/DrissionPageMCP-logo.png)

DrissionPage MCP 是一个基于 DrissionPage 和 FastMCP 的浏览器自动化MCP server服务器，它提供了一系列强大的浏览器操作 API，让您能够轻松通过AI实现网页自动化操作。

### 主要特性

- 支持浏览器的打开、关闭和连接管理
- 提供丰富的页面元素操作方法
- 支持 JavaScript 代码执行
- 支持 CDP 协议操作
- 提供便捷的文件下载功能
- 支持键盘按键模拟
- 支持页面截图功能
- 增加 网页后台监听数据包的功能
- 增加自动上传下载文件功能

---

## 安装与配置

请先将本仓库 `git clone` 到您的本地电脑。核心启动文件是 `main.py`。

### 1. 安装依赖

本项目使用 `uv` 进行包管理。请在项目根目录运行以下命令安装所有必需的Python包：

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
    "DrssionPageMCP": {
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
    "DrssionPageMCP": {
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

将上述对应您操作系统的配置粘贴到编辑器的 `mcpServers` 设置中。如果 `mcpServers` 中已有其他配置，请确保 JSON ���式正确（在条目之间加逗号）。

配置完成后，您就可以在编辑器中选择并使用 `DrssionPageMCP` 了。

- [《官方MCP安装参考教程》](https://docs.trae.ai/ide/model-context-protocol)

---

## 可用工具列表

以下是所有可通过 `DrissionPageMCP` 调用的工具方法：

| 方法名                             | 功能描述                                                                                             |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `get_version`                      | 获取当前MCP服务的版本号。                                                                            |
| `connect_or_open_browser`          | 打开或接管一个已存在的浏览器实例。可配置调试端口、浏览器路径和无头模式。                               |
| `new_tab`                          | 在当前浏览器中打开一个新的标签页，并访问指定的URL。                                                  |
| `wait`                             | 程序暂停，等待指定的秒数。                                                                           |
| `get`                              | 在当前活动的标签页中打开一个指定的URL。                                                              |
| `download_file`                    | 从指定的URL下载文件，并保存到本地指定路径，可重命名。                                                |
| `upload_file`                      | 在当前页面上查找文件上传元素 (`<input type="file">`) 并上传指定路径的文件。                          |
| `send_enter`                       | 向当前页面发送“回车”键。                                                                             |
| `getInputElementsInfo`             | 获取页面上所有可交互的输入元素（输入框、下拉选择、按钮等）的信息。                                   |
| `click_by_xpath`                   | 通过XPath表达式精确定位并点击一个页面元素。                                                          |
| `click_by_containing_text`         | 点击包含指定文本内容的元素。如果找到多个，可指定索引。                                               |
| `input_by_xapth`                   | 通过XPath表达式精确定位一个元素，并向其输入指定的文本内容。                                          |
| `get_body_text`                    | 获取当前页面`<body>`部分的所有文本内容。                                                             |
| `run_js`                           | 在当前页面执行一段JavaScript代码，并返回其执行结果。                                                 |
| `run_cdp`                          | 执行一条Chrome开发者协议（CDP）命令，用于高级浏览器控制。                                            |
| `listen_cdp_event`                 | 设置一个监听器来捕获特定的CDP事件。                                                                  |
| `get_cdp_event_data`               | 获取通过`listen_cdp_event`收集到的所有CDP事件数据。                                                  |
| `get_url_with_response_listener`   | 开启一个监听器，在新标签页访问URL，并捕获特定类型的网络响应数据包。                                  |
| `response_listener_stop`           | 停止监听网络数据包，并可选择是否清空已捕获的数据。                                                   |
| `get_response_listener_data`       | 获取通过`get_url_with_response_listener`捕获到的所有网络响应数据。                                   |
| `get_current_tab_screenshot`       | 截取当前页面的屏幕，并以二进制数据的形式返回。                                                       |
| `get_current_tab_screenshot_as_file` | 截取当前页面的屏幕，并将其保存为文件到指定路径。                                                     |
| `get_current_tab_info`             | 获取当前标签页的基本信息，包括URL、标题和ID。                                                        |
| `send_key`                         | 向当前页面发送一个特殊的键盘按键（如 `Ctrl+C`, `Delete`, `Page Down` 等）。                          |
| `getSimplifiedDomTree`             | 获取当前页面的一个简化版DOM（文档对象模型）树，用于分析页面结构。                                    |
| `move_to`                          | 将鼠标光标移动并悬停在由XPath指定的元素上。                                                          |
| `drag`                             | 拖动一个指定的元素，按照给定的x和y轴偏移量进行移动。                                                 |
| `save_dict_to_sqlite`              | 将一个字典或JSON数据保存到一个SQLite数据库文件中。                                                   |

---

## 调试命令

您可以使用 `mcp` 命令行工具来调试您的服务。请确保已安装 `mcp-cli` (`pip install "mcp[cli]"`)。

```bash
# 将 /path/to/your/main.py 替换为您的文件路径
mcp dev /path/to/your/main.py
```

## 更新日志
### v0.1.3
增加 自动上传下载文件功能
### v0.1.2
增加 网页后台监听数据包的功能

### v0.1.0

- 初始版本发布
- 实现基本的浏览器控制功能
- 提供元素操作 API
