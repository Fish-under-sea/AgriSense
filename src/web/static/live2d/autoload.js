/*!
 * Live2D Widget
 * https://github.com/stevenjoezhang/live2d-widget
 */

// Recommended to use absolute path for live2d_path parameter
// live2d_path 参数建议使用绝对路径
// const live2d_path = 'https://fastly.jsdelivr.net/npm/live2d-widgets@1.0.0-rc.6/dist/';
const live2d_path = '/static/live2d/';

// Method to encapsulate asynchronous resource loading
// 封装异步加载资源的方法
function loadExternalResource(url, type) {
  return new Promise((resolve, reject) => {
    let tag;

    if (type === 'css') {
      tag = document.createElement('link');
      tag.rel = 'stylesheet';
      tag.href = url;
    }
    else if (type === 'js') {
      tag = document.createElement('script');
      tag.type = 'module';
      tag.src = url;
    }
    if (tag) {
      tag.onload = () => resolve(url);
      tag.onerror = () => reject(url);
      document.head.appendChild(tag);
    }
  });
}

// =============================================
// AgriSense AI 对话面板样式
// =============================================
const aiPanelCSS = `
/* AI 对话侧边抽屉 - 多层动画效果 */
#waifu-ai-panel {
  position: fixed;
  top: 0;
  right: -420px;
  width: 400px;
  height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  backdrop-filter: blur(20px);
  border-left: 2px solid rgba(78, 204, 163, 0.4);
  z-index: 20000;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 40px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

/* 动画层背景 */
#waifu-ai-panel-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

/* 各层错位效果 - 初始状态与 panel 一致 */
#waifu-ai-panel-layer-1 {
  z-index: 3;
  background: rgba(26, 26, 46, 0.95);
  transform: translateX(100%);
}
#waifu-ai-panel-layer-2 {
  z-index: 2;
  background: rgba(22, 33, 62, 0.9);
  transform: translateX(100%);
}
#waifu-ai-panel-layer-3 {
  z-index: 1;
  background: rgba(15, 52, 96, 0.85);
  transform: translateX(100%);
}

/* 面板内容 */
#waifu-ai-panel .panel-content {
  position: relative;
  z-index: 4;
  display: flex;
  flex-direction: column;
  height: 100%;
  opacity: 0;
  transform: translateX(20px);
}

#waifu-ai-panel .panel-header {
  padding: 20px;
  border-bottom: 2px solid rgba(78, 204, 163, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0, 0, 0, 0.2);
}

#waifu-ai-panel .panel-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #4ecca3;
  display: flex;
  align-items: center;
  gap: 10px;
  text-shadow: 0 0 10px rgba(78, 204, 163, 0.5);
}

#waifu-ai-panel .panel-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

#waifu-ai-panel .panel-close:hover {
  background: rgba(231, 76, 60, 0.8);
  transform: rotate(90deg);
}

#waifu-ai-panel .model-selector {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(78, 204, 163, 0.2);
  background: rgba(0, 0, 0, 0.15);
}

#waifu-ai-panel .model-selector label {
  font-size: 0.85rem;
  color: #b8b8b8;
  margin-bottom: 8px;
  display: block;
}

#waifu-ai-panel .model-selector select {
  width: 100%;
  padding: 10px 15px;
  border-radius: 10px;
  border: 2px solid rgba(78, 204, 163, 0.4);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

#waifu-ai-panel .model-selector select:focus {
  outline: none;
  border-color: #4ecca3;
  box-shadow: 0 0 15px rgba(78, 204, 163, 0.2);
}

#waifu-ai-panel .model-selector select option {
  background: #1a1a2e;
  color: #fff;
}

#waifu-ai-panel .chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: rgba(0, 0, 0, 0.2);
}

#waifu-ai-panel .chat-messages::-webkit-scrollbar {
  width: 6px;
}

#waifu-ai-panel .chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

#waifu-ai-panel .chat-messages::-webkit-scrollbar-thumb {
  background: rgba(78, 204, 163, 0.3);
  border-radius: 3px;
}

#waifu-ai-panel .message {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 15px;
  font-size: 0.9rem;
  line-height: 1.5;
  animation: messageSlide 0.3s ease;
}

@keyframes messageSlide {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

#waifu-ai-panel .message.user {
  align-self: flex-end;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-bottom-right-radius: 5px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

#waifu-ai-panel .message.assistant {
  align-self: flex-start;
  background: rgba(78, 204, 163, 0.15);
  color: #e8e8e8;
  border: 1px solid rgba(78, 204, 163, 0.3);
  border-bottom-left-radius: 5px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

#waifu-ai-panel .message.error {
  background: rgba(231, 76, 60, 0.2);
  border: 1px solid rgba(231, 76, 60, 0.4);
  color: #ff6b6b;
}

#waifu-ai-panel .typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 15px 20px;
  color: #b8b8b8;
  font-size: 0.85rem;
}

#waifu-ai-panel .typing-dots {
  display: flex;
  gap: 4px;
}

#waifu-ai-panel .typing-dots span {
  width: 8px;
  height: 8px;
  background: #4ecca3;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite;
}

#waifu-ai-panel .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
#waifu-ai-panel .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-8px); opacity: 1; }
}

#waifu-ai-panel .chat-input-area {
  padding: 15px 20px;
  border-top: 2px solid rgba(78, 204, 163, 0.3);
  display: flex;
  gap: 10px;
  background: rgba(0, 0, 0, 0.2);
}

#waifu-ai-panel .chat-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 25px;
  border: 2px solid rgba(78, 204, 163, 0.4);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 0.9rem;
  transition: all 0.3s;
}

#waifu-ai-panel .chat-input:focus {
  outline: none;
  border-color: #4ecca3;
  box-shadow: 0 0 20px rgba(78, 204, 163, 0.3);
}

#waifu-ai-panel .chat-input::placeholder {
  color: #888;
}

#waifu-ai-panel .chat-send-btn {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #4ecca3, #38b2ac);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

#waifu-ai-panel .chat-send-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 5px 20px rgba(78, 204, 163, 0.4);
}

#waifu-ai-panel .chat-send-btn:disabled {
  background: #444;
  cursor: not-allowed;
  transform: none;
}

/* 遮罩层 */
#waifu-ai-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 19999;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
}

#waifu-ai-overlay.show {
  opacity: 1;
  visibility: visible;
}

/* 模型选择面板 */
#waifu-model-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0.9);
  width: 380px;
  max-height: 70vh;
  background: rgba(10, 10, 20, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(78, 204, 163, 0.2);
  z-index: 20001;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

#waifu-model-panel.open {
  opacity: 1;
  visibility: visible;
  transform: translate(-50%, -50%) scale(1);
}

#waifu-model-panel .model-panel-header {
  padding: 20px;
  border-bottom: 1px solid rgba(78, 204, 163, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

#waifu-model-panel .model-panel-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #4ecca3;
}

#waifu-model-panel .model-panel-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

#waifu-model-panel .model-panel-close:hover {
  background: rgba(231, 76, 60, 0.6);
}

#waifu-model-panel .model-list {
  padding: 15px;
  max-height: 400px;
  overflow-y: auto;
}

#waifu-model-panel .model-item {
  padding: 15px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

#waifu-model-panel .model-item:hover {
  border-color: rgba(78, 204, 163, 0.5);
  background: rgba(78, 204, 163, 0.1);
}

#waifu-model-panel .model-item.active {
  border-color: #4ecca3;
  background: rgba(78, 204, 163, 0.15);
}

#waifu-model-panel .model-item-name {
  font-weight: 600;
  color: #fff;
  margin-bottom: 5px;
}

#waifu-model-panel .model-item-desc {
  font-size: 0.8rem;
  color: #888;
}

/* 思考过程显示样式 */
#waifu-ai-panel .thinking-toggle {
  padding: 12px 20px;
  border-bottom: 1px solid rgba(78, 204, 163, 0.2);
  background: rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

#waifu-ai-panel .thinking-toggle label {
  font-size: 0.85rem;
  color: #b8b8b8;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

#waifu-ai-panel .thinking-toggle .toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

#waifu-ai-panel .thinking-toggle .toggle-switch input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  z-index: 1;
}

#waifu-ai-panel .thinking-toggle .toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.1);
  transition: 0.3s;
  border-radius: 24px;
  pointer-events: none;
}

#waifu-ai-panel .thinking-toggle .toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: #888;
  transition: 0.3s;
  border-radius: 50%;
  pointer-events: none;
}

#waifu-ai-panel .thinking-toggle input:checked + .toggle-slider {
  background-color: rgba(78, 204, 163, 0.4);
}

#waifu-ai-panel .thinking-toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
  background-color: #4ecca3;
}

/* 思考过程消息样式 */
#waifu-ai-panel .message.thinking {
  align-self: flex-start;
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-bottom-left-radius: 5px;
  font-size: 0.85rem;
}

/* 消息入场动画 */
#waifu-ai-panel .message {
  animation: messageSlideIn 0.3s ease forwards;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateX(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* 输入区域入场动画 */
#waifu-ai-panel .chat-input-area {
  animation: slideUpFade 0.4s ease 0.2s both;
}

@keyframes slideUpFade {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 思考开关入场 */
#waifu-ai-panel .thinking-toggle {
  animation: slideDownFade 0.35s ease 0.15s both;
}

@keyframes slideDownFade {
  from {
    opacity: 0;
    transform: translateY(-15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
`;

// =============================================
// AgriSense AI 面板管理类
// =============================================
class WaifuAIPanel {
  constructor() {
    this.isOpen = false;
    this.messages = [];
    this.showThinking = true;
    this.init();
  }

  init() {
    // 注入样式
    this.injectStyles();
    // 创建 DOM 结构
    this.createDOM();
    // 绑定事件
    this.bindEvents();
    // 加载模型列表
    this.loadModels();
  }

  injectStyles() {
    const style = document.createElement('style');
    style.textContent = aiPanelCSS;
    document.head.appendChild(style);
  }

  createDOM() {
    // 遮罩层
    const overlay = document.createElement('div');
    overlay.id = 'waifu-ai-overlay';
    document.body.appendChild(overlay);

    // AI 对话面板
    const panel = document.createElement('div');
    panel.id = 'waifu-ai-panel';
    panel.innerHTML = `
      <div id="waifu-ai-panel-layer-1" class="panel-layer"></div>
      <div id="waifu-ai-panel-layer-2" class="panel-layer"></div>
      <div id="waifu-ai-panel-layer-3" class="panel-layer"></div>
      <div class="panel-content">
        <div class="panel-header">
          <div class="panel-title">
            <span style="font-size: 1.5rem;">🌱</span>
            AgriSense AI 助手
          </div>
          <button class="panel-close" id="waifu-ai-close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="thinking-toggle">
          <label>🧠 显示思考过程</label>
          <div class="toggle-switch">
            <input type="checkbox" id="waifu-thinking-toggle" checked>
            <span class="toggle-slider"></span>
          </div>
        </div>
        <div class="chat-messages" id="waifu-chat-messages">
          <div class="message assistant">
            你好！我是 AgriSense AI 助手 🌱<br><br>
            我可以帮助你：<br>
            • 分析大棚环境数据<br>
            • 提供作物管理建议<br>
            • 回答农业相关问题<br><br>
            有什么我可以帮你的吗？
          </div>
        </div>
        <div class="chat-input-area">
          <input type="text" class="chat-input" id="waifu-chat-input" placeholder="输入你的问题..." />
          <button class="chat-send-btn" id="waifu-chat-send">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(panel);

    // 模型选择面板
    const modelPanel = document.createElement('div');
    modelPanel.id = 'waifu-model-panel';
    modelPanel.innerHTML = `
      <div class="model-panel-header">
        <div class="model-panel-title">🔄 切换 AI 模型</div>
        <button class="model-panel-close" id="waifu-model-close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="model-list" id="waifu-model-list">
        <div style="text-align: center; color: #888; padding: 20px;">加载中...</div>
      </div>
    `;
    document.body.appendChild(modelPanel);

    this.overlay = overlay;
    this.panel = panel;
    this.modelPanel = modelPanel;
  }

  bindEvents() {
    // 关闭按钮
    document.getElementById('waifu-ai-close').addEventListener('click', () => this.close());
    this.overlay.addEventListener('click', () => this.closeAll());

    // 思考过程开关
    document.getElementById('waifu-thinking-toggle').addEventListener('change', (e) => {
      this.showThinking = e.target.checked;
      localStorage.setItem('waifu-show-thinking', this.showThinking ? '1' : '0');
    });
    // 从 localStorage 恢复设置
    this.showThinking = localStorage.getItem('waifu-show-thinking') !== '0';
    document.getElementById('waifu-thinking-toggle').checked = this.showThinking;

    // 发送消息
    document.getElementById('waifu-chat-send').addEventListener('click', () => this.sendMessage());
    document.getElementById('waifu-chat-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });

    // 模型选择关闭
    document.getElementById('waifu-model-close').addEventListener('click', () => this.closeModelPanel());
  }

  closeAll() {
    this.close();
    this.closeModelPanel();
  }

  async loadModels() {
    try {
      const response = await fetch('/api/ai/models');
      const data = await response.json();
      
      if (data.models) {
        // 更新模型选择面板
        this.updateModelPanel(data.models, data.current_model);
      }
    } catch (error) {
      console.error('加载模型列表失败:', error);
    }
  }

  updateModelPanel(models, currentModel) {
    const list = document.getElementById('waifu-model-list');
    list.innerHTML = '';

    for (const [key, model] of Object.entries(models)) {
      if (model.enabled) {
        const item = document.createElement('div');
        item.className = `model-item${key === currentModel ? ' active' : ''}`;
        item.innerHTML = `
          <div class="model-item-name">${model.name}</div>
          <div class="model-item-desc">${model.description || '暂无描述'}</div>
        `;
        item.addEventListener('click', () => {
          this.switchModel(key);
        });
        list.appendChild(item);
      }
    }
  }

  async switchModel(modelKey) {
    if (!modelKey) return;

    try {
      const response = await fetch('/api/ai/models/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_key: modelKey })
      });
      
      if (response.ok) {
        this.addMessage('assistant', `✅ 已切换到新模型`);
      }
    } catch (error) {
      console.error('切换模型失败:', error);
      this.addMessage('error', '切换模型失败，请重试');
    }
  }

  open() {
    this.isOpen = true;
    this.panel.style.right = '0';
    this.overlay.classList.add('show');

    const layer1 = document.getElementById('waifu-ai-panel-layer-1');
    const layer2 = document.getElementById('waifu-ai-panel-layer-2');
    const layer3 = document.getElementById('waifu-ai-panel-layer-3');
    const content = this.panel.querySelector('.panel-content');

    const layers = [layer1, layer2, layer3];
    const panelWidth = '400px';

    // 重置初始状态（参考原网站 transform: translateX(100%)）
    layers.forEach((layer, i) => {
      if (layer) {
        layer.style.transform = 'translateX(100%)';
        layer.style.transition = 'none';
        layer.style.willChange = 'transform';
      }
    });

    if (content) {
      content.style.transform = 'translateX(100%)';
      content.style.opacity = '0';
      content.style.transition = 'none';
      content.style.willChange = 'transform, opacity';
    }

    // 强制重绘
    void this.panel.offsetWidth;

    // 参考原网站 GSAP timeline:
    // .to(prelayers[0], { x: '0%', duration: 0.55 })
    // .to(prelayers[1], { x: '0%', duration: 0.55 }, '-=0.35')  // 重叠 0.35s
    // .to(panel, { x: '0%', duration: 0.55 }, '-=0.35')
    // .to(items, { y: '0%', duration: 0.45, stagger: 0.05 }, '-=0.25')

    // 使用 easeOutBack 曲线模拟 power4.inOut
    const ease = 'cubic-bezier(0.34, 1.56, 0.64, 1)';
    const duration = 550; // ms

    // 第一层入场（0ms）
    if (layer1) {
      layer1.style.transition = `transform ${duration}ms ${ease}`;
      layer1.style.transform = 'translateX(0)';
    }

    // 第二层入场（重叠 200ms，与原网站 -0.35 一致）
    setTimeout(() => {
      if (layer2) {
        layer2.style.transition = `transform ${duration}ms ${ease}`;
        layer2.style.transform = 'translateX(0)';
      }
    }, 200);

    // 第三层入场（再重叠 200ms）
    setTimeout(() => {
      if (layer3) {
        layer3.style.transition = `transform ${duration}ms ${ease}`;
        layer3.style.transform = 'translateX(0)';
      }
    }, 300);

    // 主面板内容入场（再重叠 200ms，与原网站 -0.35 一致）
    setTimeout(() => {
      if (content) {
        content.style.transition = `transform ${duration}ms ${ease}, opacity ${duration * 0.7}ms ease`;
        content.style.transform = 'translateX(0)';
        content.style.opacity = '1';
      }
    }, 400);

    // 清理 will-change
    setTimeout(() => {
      layers.forEach(layer => {
        if (layer) layer.style.willChange = 'auto';
      });
      if (content) content.style.willChange = 'auto';
    }, 1200);
  }

  close() {
    const layer1 = document.getElementById('waifu-ai-panel-layer-1');
    const layer2 = document.getElementById('waifu-ai-panel-layer-2');
    const layer3 = document.getElementById('waifu-ai-panel-layer-3');
    const content = this.panel.querySelector('.panel-content');

    const layers = [layer1, layer2, layer3];

    // 参考原网站关闭动画：timeScale(1.6).reverse()
    const ease = 'cubic-bezier(0.34, 1.56, 0.64, 1)';
    const duration = 400; // ms，更快关闭

    // 先隐藏内容
    if (content) {
      content.style.transition = `opacity 200ms ease, transform ${duration}ms ${ease}`;
      content.style.opacity = '0';
      content.style.transform = 'translateX(100%)';
    }

    // 依次收回层（从后往前，与入场相反）
    setTimeout(() => {
      if (layer3) {
        layer3.style.transition = `transform ${duration}ms ${ease}`;
        layer3.style.transform = 'translateX(100%)';
      }
    }, 0);

    setTimeout(() => {
      if (layer2) {
        layer2.style.transition = `transform ${duration}ms ${ease}`;
        layer2.style.transform = 'translateX(100%)';
      }
    }, 100);

    setTimeout(() => {
      if (layer1) {
        layer1.style.transition = `transform ${duration}ms ${ease}`;
        layer1.style.transform = 'translateX(100%)';
      }
    }, 200);

    // 最后隐藏面板
    setTimeout(() => {
      this.isOpen = false;
      this.panel.style.right = '-420px';
      this.overlay.classList.remove('show');

      // 重置层位置
      layers.forEach((layer) => {
        if (layer) {
          layer.style.transition = 'none';
          layer.style.transform = 'translateX(100%)';
        }
      });

      if (content) {
        content.style.transition = 'none';
        content.style.opacity = '0';
        content.style.transform = 'translateX(100%)';
      }
    }, 350);
  }

  openModelPanel() {
    this.modelPanel.classList.add('open');
    this.overlay.classList.add('show');
  }

  closeModelPanel() {
    this.modelPanel.classList.remove('open');
  }

  addMessage(role, content) {
    const container = document.getElementById('waifu-chat-messages');
    const message = document.createElement('div');
    message.className = `message ${role}`;
    message.innerHTML = content.replace(/\n/g, '<br>');
    container.appendChild(message);
    container.scrollTop = container.scrollHeight;
  }

  showTyping() {
    const container = document.getElementById('waifu-chat-messages');
    const typing = document.createElement('div');
    typing.id = 'waifu-typing';
    typing.className = 'typing-indicator';
    typing.innerHTML = `
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
      AI 正在思考...
    `;
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
  }

  hideTyping() {
    const typing = document.getElementById('waifu-typing');
    if (typing) typing.remove();
  }

  async sendMessage() {
    const input = document.getElementById('waifu-chat-input');
    const message = input.value.trim();

    if (!message) return;

    input.value = '';
    this.addMessage('user', message);
    this.showTyping();

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, use_context: true, stream: true })
      });

      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text();
        this.hideTyping();
        this.addMessage('error', `服务器错误 (${response.status}): ${errorText}`);
        return;
      }

      // 处理流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let thinkingContent = '';
      let responseContent = '';
      let isThinking = true;

      // 创建消息元素
      this.hideTyping();
      const thinkingMsg = document.createElement('div');
      thinkingMsg.className = 'message thinking';
      thinkingMsg.innerHTML = '🧠 思考中...<br><span class="thinking-content"></span>';
      const thinkingContentEl = thinkingMsg.querySelector('.thinking-content');
      document.getElementById('waifu-chat-messages').appendChild(thinkingMsg);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              isThinking = false;
              continue;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.thinking && this.showThinking) {
                thinkingContent += parsed.thinking;
                if (thinkingContentEl) thinkingContentEl.textContent = thinkingContent.slice(-500);
              }
              if (parsed.response) {
                responseContent += parsed.response;
              }
            } catch (e) {}
          }
        }
      }

      // 移除思考消息
      thinkingMsg.remove();

      // 显示最终回复
      if (responseContent) {
        this.addMessage('assistant', responseContent);
      } else {
        this.addMessage('error', '未收到有效回复');
      }
    } catch (error) {
      this.hideTyping();
      this.addMessage('error', `网络错误: ${error.message}`);
    }
  }
}

// 全局 AI 面板实例
let waifuAIPanel = null;

// 获取或创建 AI 面板
function getAIPanel() {
  if (!waifuAIPanel) {
    waifuAIPanel = new WaifuAIPanel();
  }
  return waifuAIPanel;
}

// 打开 AI 对话面板
function openAIPanel() {
  getAIPanel().open();
}

// 打开模型选择面板
function openModelPanel() {
  getAIPanel().openModelPanel();
}

(async () => {
  // If you are concerned about display issues on mobile devices, you can use screen.width to determine whether to load
  // 如果担心手机上显示效果不佳，可以根据屏幕宽度来判断是否加载
  // if (screen.width < 768) return;

  // Avoid cross-origin issues with image resources
  // 避免图片资源跨域问题
  const OriginalImage = window.Image;
  window.Image = function(...args) {
    const img = new OriginalImage(...args);
    img.crossOrigin = "anonymous";
    return img;
  };
  window.Image.prototype = OriginalImage.prototype;

  // Load waifu.css and waifu-tips.js
  // 加载 waifu.css 和 waifu-tips.js
  await Promise.all([
    loadExternalResource(live2d_path + 'waifu.css', 'css'),
    loadExternalResource(live2d_path + 'waifu-tips.js', 'js')
  ]);

  // For detailed usage of configuration options, see README.en.md
  // 配置选项的具体用法见 README.md
  initWidget({
    waifuPath: live2d_path + 'waifu-tips.json',
    cdnPath: 'https://fastly.jsdelivr.net/gh/fghrsh/live2d_api/',
    cubism2Path: live2d_path + 'live2d.min.js',
    cubism5Path: 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
    tools: ['agent', 'llm', 'switch-avatar', 'asteroids', 'hitokoto', 'photo', 'info', 'quit'],
    logLevel: 'warn',
    drag: false,
  });
})();

// 延迟加载管理器
const Live2DLoader = {
  initialized: false,
  widgetLoaded: false,

  async init() {
    if (this.initialized) return;
    this.initialized = true;

    // 加载 CSS
    loadExternalResource(live2d_path + 'waifu.css', 'css').catch(() => {});

    // 预加载 Cubism SDK
    this.preloadCore();

    // 延迟加载 Live2D Widget
    this.loadWhenIdle();
  },

  preloadCore() {
    const link2 = document.createElement('link');
    link2.rel = 'preload';
    link2.href = live2d_path + 'live2d.min.js';
    link2.as = 'script';
    document.head.appendChild(link2);

    const link5 = document.createElement('link');
    link5.rel = 'preload';
    link5.href = 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js';
    link5.as = 'script';
    document.head.appendChild(link5);
  },

  loadWhenIdle() {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => this.loadWidget(), { timeout: 3000 });
    } else {
      setTimeout(() => this.loadWidget(), 1500);
    }
  },

  async loadWidget() {
    if (this.widgetLoaded) {
      // 已加载，只需显示
      this.showWaifu();
      return;
    }
    this.widgetLoaded = true;

    try {
      // 加载 waifu-tips.js（由它负责创建 toggle 按钮和加载模型）
      await loadExternalResource(live2d_path + 'waifu-tips.js', 'js');

      // 本地模型配置 - 使用下载到本地的 Pio 模型
      window.initWidget({
        waifuPath: live2d_path + 'waifu-tips.json',
        // 本地模型（不再使用 CDN cdnPath）
        models: [
          {
            name: 'Pio',
            message: '来自 Potion Maker 的 Pio 酱 ~',
            paths: [
              live2d_path + 'model/Pio/index.json'
            ]
          }
        ],
        cubism2Path: live2d_path + 'live2d.min.js',
        cubism5Path: 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
        tools: ['agent', 'llm', 'switch-avatar', 'asteroids', 'hitokoto', 'photo', 'info', 'quit'],
        logLevel: 'warn',
        drag: false,
      });
    } catch (e) {
      console.error('Live2D 加载失败:', e);
    }
  },

  showWaifu() {
    const waifu = document.getElementById('waifu');
    const toggle = document.getElementById('waifu-toggle');

    // 清除 localStorage，这样下次刷新页面不会误显示 toggle
    localStorage.removeItem('waifu-display');

    if (toggle) {
      toggle.classList.remove('waifu-toggle-active');
    }

    if (waifu) {
      waifu.classList.remove('waifu-hidden');
      waifu.classList.add('waifu-active');
    }
  }
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => Live2DLoader.init());
} else {
  Live2DLoader.init();
}

window.Live2DLoader = Live2DLoader;

console.log(`\n%cLive2D%cWidget%c\n`, 'padding: 8px; background: #cd3e45; font-weight: bold; font-size: large; color: white;', 'padding: 8px; background: #ff5450; font-size: large; color: #eee;', '');

/*
く__,.ヘヽ.        /  ,ー､ 〉
         ＼ ', !-─‐-i  /  /´
         ／｀ｰ'       L/／｀ヽ､
       /   ／,   /|   ,   ,       ',
     ｲ   / /-‐/  ｉ  L_ ﾊ ヽ!   i
      ﾚ ﾍ 7ｲ｀ﾄ   ﾚ'ｧ-ﾄ､!ハ|   |
        !,/7 '0'     ´0iソ|    |
        |.从"    _     ,,,, / |./    |
        ﾚ'| i＞.､,,__  _,.イ /   .i   |
          ﾚ'| | / k_７_/ﾚ'ヽ,  ﾊ.  |
            | |/i 〈|/   i  ,.ﾍ |  i  |
           .|/ /  ｉ：    ﾍ!    ＼  |
            kヽ>､ﾊ    _,.ﾍ､    /､!
            !'〈//｀Ｔ´', ＼ ｀'7'ｰr'
            ﾚ'ヽL__|___i,___,ンﾚ|ノ
                ﾄ-,/  |___.
                'ｰ'    !_,.:
*/
