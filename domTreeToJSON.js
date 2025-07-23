// --- 新增的辅助函数 ---
function getXPath(node) {
    // 1. 如果元素有ID，直接使用ID，这是最稳定的
    if (node.id) {
        return `//*[@id="${node.id}"]`;
    }

    // 2. 如果没有ID，递归构建XPath
    if (node === document.body) {
        return '/html/body';
    }
    if (node.parentNode === null) {
        return '';
    }

    let ix = 0;
    const siblings = node.parentNode.childNodes;
    for (let i = 0; i < siblings.length; i++) {
        const sibling = siblings[i];
        if (sibling === node) {
            // 构建路径：父级XPath + / + 当前标签名[索引]
            // 索引从1开始
            return getXPath(node.parentNode) + '/' + node.tagName.toLowerCase() + '[' + (ix + 1) + ']';
        }
        // 只计算相同标签的元素节点
        if (sibling.nodeType === 1 && sibling.tagName === node.tagName) {
            ix++;
        }
    }
    return ''; // Should not happen
}


// --- 修改原有的函数 ---
function buildSimplifiedDom(node, counters) {
    if (node.nodeType !== 1 || !node.tagName) { // Only process element nodes
        return null;
    }

    const tagName = node.tagName.toLowerCase();
    
    if (['script', 'style', 'meta', 'link', 'head'].includes(tagName)) {
        return null;
    }

    if (counters[tagName] === undefined) {
        counters[tagName] = 0;
    }
    const nodeId = `${tagName}${counters[tagName]++}`;

    const result = {};
    // 修改这里，让每个节点不仅是一个空对象，而是包含xpath属性
    result[nodeId] = {
        "xpath": getXPath(node) // <--- 关键改动：添加xpath
    };

    const childrenParent = node.shadowRoot || node;
    const children = Array.from(childrenParent.children);
    if (children.length > 0) {
        children.forEach(child => {
            const childJson = buildSimplifiedDom(child, counters);
            if (childJson) {
                Object.assign(result[nodeId], childJson);
            }
        });
    }

    return result;
}

function getPageStructure() {
    const counters = {};
    const bodyJson = buildSimplifiedDom(document.body, counters);
    return JSON.stringify({ "body": bodyJson }, null, 2);
}

return getPageStructure();
