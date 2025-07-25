/**
 * 遍历DOM树，为每个元素（包括iframe和shadow DOM中的元素）分配一个唯一的引用ID。
 * @param {Node} [startNode=document.body] - 开始遍历的节点。
 * @param {number} [startId=1] - 起始ID。
 * @returns {number} - 返回分配的最后一个ID。
 */
function assignRefIds(startNode = document.body, startId = 1) {
    let refIdCounter = startId;
    const processedNodes = new WeakSet();

    function traverse(node) {
        if (!node || processedNodes.has(node)) return;
        processedNodes.add(node);

        if (node.nodeType === Node.ELEMENT_NODE) {
            node.setAttribute('ref_id', refIdCounter++);

            if (node.shadowRoot) {
                for (const child of node.shadowRoot.childNodes) {
                    traverse(child);
                }
            }

            if (node.tagName === 'IFRAME') {
                try {
                    const iframeDocument = node.contentDocument;
                    if (iframeDocument && iframeDocument.body) {
                        traverse(iframeDocument.body);
                    }
                } catch (e) {
                    // Cross-origin iframe, cannot access content.
                }
            }
        }

        for (const child of (node.childNodes || [])) {
            traverse(child);
        }
    }

    traverse(startNode);
    return refIdCounter;
}


/**
 * 构建一个简化的DOM树JSON表示，专注于可见和可交互的元素。
 * @param {Node} node - 当前遍历的节点。
 * @returns {Object|null} - 返回节点的JSON表示，如果节点应被忽略则返回null。
 */
function buildSimplifiedTree(node) {
    // 1. 过滤非元素节点和不可见/无用标签
    if (node.nodeType !== Node.ELEMENT_NODE) return null;

    const element = /** @type {Element} */ (node);
    const tagName = element.tagName.toLowerCase();
    const IGNORED_TAGS = ['script', 'style', 'meta', 'link', 'head', 'br', 'hr', 'svg', 'path'];
    if (IGNORED_TAGS.includes(tagName)) return null;

    try {
        const style = window.getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return null;
        }
    } catch (e) {
        return null;
    }

    // 2. 构建当前节点的基础JSON对象
    const jsonNode = {
        tag: tagName,
        ref_id: element.getAttribute('ref_id'),
        attributes: {},
        children: []
    };

    // 3. 提取关键属性
    const ATTRIBUTES_TO_CAPTURE = ['id', 'class', 'href', 'src', 'placeholder', 'aria-label', 'role', 'type', 'alt', 'title', 'name', 'value'];
    for (const attr of ATTRIBUTES_TO_CAPTURE) {
        if (element.hasAttribute(attr)) {
            jsonNode.attributes[attr] = element.getAttribute(attr);
        }
    }

    // 4. 提取直接文本内容
    let directText = '';
    for (const child of element.childNodes) {
        if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
            directText += child.textContent.trim() + ' ';
        }
    }
    if (directText) {
        jsonNode.text = directText.trim();
    }

    // 5. 递归处理子节点 (包括 Shadow DOM 和 iframe)
    const childrenParent = element.shadowRoot || element;
    
    for (const child of childrenParent.childNodes) {
        if (child.tagName && child.tagName.toLowerCase() === 'iframe') {
             try {
                const iframeDocument = child.contentDocument;
                if (iframeDocument && iframeDocument.body) {
                    // 为iframe本身创建一个节点
                    const iframeNode = buildSimplifiedTree(child);
                    if(iframeNode) {
                        // 递归处理iframe内部的body
                        const iframeBodyNode = buildSimplifiedTree(iframeDocument.body);
                        if (iframeBodyNode) {
                            iframeNode.children.push(iframeBodyNode);
                        }
                        jsonNode.children.push(iframeNode);
                    }
                } else {
                     const iframeNode = buildSimplifiedTree(child);
                     if(iframeNode) jsonNode.children.push(iframeNode);
                }
            } catch (e) {
                // 跨域iframe，只记录iframe标签本身
                const iframeNode = buildSimplifiedTree(child);
                if(iframeNode) {
                    iframeNode.attributes['cross_origin'] = 'true';
                    jsonNode.children.push(iframeNode);
                }
            }
        } else {
            const processedChild = buildSimplifiedTree(child);
            if (processedChild) {
                jsonNode.children.push(processedChild);
            }
        }
    }

    // 6. 清理：如果children为空，则删除该键
    if (jsonNode.children.length === 0) {
        delete jsonNode.children;
    }
    
    // 7. 如果一个节点除了tag和ref_id外没有任何信息（没有属性、文本或子节点），则可能不需要它
    if (Object.keys(jsonNode.attributes).length === 0 && !jsonNode.text && !jsonNode.children) {
        const INTERACTIVE_TAGS = ['button', 'a', 'input', 'select', 'textarea', 'option'];
        if (!INTERACTIVE_TAGS.includes(tagName)) {
            return null;
        }
    }

    return jsonNode;
}

/**
 * 主函数：执行ID分配和DOM树构建。
 * @returns {string} - 返回最终的JSON字符串。
 */
function getPageStructure() {
    assignRefIds(document.body);
    const simplifiedDom = buildSimplifiedTree(document.body);
    return JSON.stringify(simplifiedDom, null, 2);
}

return getPageStructure();