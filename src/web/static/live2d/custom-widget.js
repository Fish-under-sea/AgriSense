/**
 * 自定义 Live2D 看板娘 - 使用 pixi-live2d-display
 * 支持 PMX/VRM 格式模型
 */

(function() {
    'use strict';

    // 默认配置
    const defaultConfig = {
        modelPath: '/static/live2d/models/maid-aris/maidaris.pmx',
        scale: 0.15,
        position: { x: 0.12, y: 0.85 }
    };

    class Live2DWidget {
        constructor(options = {}) {
            this.config = { ...defaultConfig, ...options };
            this.isDragging = false;
            this.model = null;
            this.app = null;
            this.init();
        }

        async init() {
            console.log('Live2D Widget 初始化中...');
            try {
                await this.loadDependencies();
                await this.loadModel();
                this.createUI();
                this.startAnimation();
                console.log('Live2D Widget 加载成功!');
            } catch (error) {
                console.error('Live2D Widget 初始化失败:', error);
                this.showError();
            }
        }

        async loadDependencies() {
        const cdnBase = 'https://cdn.jsdelivr.net/npm';

        // 加载 PIXI.js
        if (typeof PIXI === 'undefined') {
            console.log('加载 PIXI.js...');
            await this.loadScript(`${cdnBase}/pixi.js@7.4.2/dist/pixi.min.js`);
            console.log('PIXI loaded:', typeof PIXI !== 'undefined');
        }

        // 加载 pixi-live2d-display
        if (typeof live2d === 'undefined') {
            console.log('加载 pixi-live2d-display...');
            await this.loadScript(`${cdnBase}/pixi-live2d-display@0.4.0/dist/index.min.js`);
            console.log('live2d loaded:', typeof live2d !== 'undefined');
            console.log('Available globals:', Object.keys(window).filter(k => k.toLowerCase().includes('live2d') || k.toLowerCase().includes('pixi')));
        }
    }

    loadScript(src) {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = () => reject(new Error(`Failed to load: ${src}`));
                document.head.appendChild(script);
            });
        }

        async loadModel() {
            const canvas = document.createElement('canvas');
            canvas.id = 'live2d-canvas';
            canvas.style.cssText = `
                position: fixed;
                bottom: 0;
                left: ${this.config.position.x * 100}%;
                transform: translateX(-50%);
                z-index: 9999;
                pointer-events: auto;
                cursor: grab;
            `;
            document.body.appendChild(canvas);
            this.canvas = canvas;

            // 获取 Live2DModel
            const Live2DModel = window.live2d?.Live2DModel || window.PIXI?.live2d?.Live2DModel;
            if (!Live2DModel) {
                throw new Error('pixi-live2d-display 未正确加载');
            }

            // 创建 PIXI 应用
            this.app = new PIXI.Application({
                view: canvas,
                width: 400,
                height: 500,
                transparent: true,
                autoDensity: true,
                resolution: Math.min(window.devicePixelRatio || 1, 2)
            });

            // 加载模型
            console.log('加载模型:', this.config.modelPath);
            this.model = await Live2DModel.from(this.config.modelPath);

            // 设置模型属性
            this.model.anchor.set(0.5, 1);
            this.model.position.set(200, 500);
            this.model.scale.set(this.config.scale);

            // 启用交互
            this.model.interactive = true;
            this.model.cursor = 'grab';

            this.app.stage.addChild(this.model);

            // 拖拽事件
            canvas.addEventListener('mousedown', (e) => this.startDrag(e));
            canvas.addEventListener('mousemove', (e) => this.onDrag(e));
            canvas.addEventListener('mouseup', () => this.endDrag());
            canvas.addEventListener('mouseleave', () => this.endDrag());
            canvas.addEventListener('click', () => this.onTap());
        }

        createUI() {
            // 工具栏
            const toolbar = document.createElement('div');
            toolbar.id = 'live2d-toolbar';
            toolbar.style.cssText = `
                position: fixed;
                bottom: 510px;
                left: ${this.config.position.x * 100}%;
                transform: translateX(-50%);
                display: flex;
                flex-direction: column;
                gap: 8px;
                z-index: 10000;
            `;

            // 一言气泡
            this.speechBubble = document.createElement('div');
            this.speechBubble.style.cssText = `
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 12px 16px;
                font-size: 13px;
                color: #333;
                max-width: 220px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                opacity: 0;
                transform: translateY(10px);
                transition: all 0.4s ease;
                pointer-events: none;
            `;
            toolbar.appendChild(this.speechBubble);

            // 工具按钮
            const tools = [
                { icon: '💬', title: '发言', action: () => this.showSpeech() },
                { icon: '📷', title: '拍照', action: () => this.takePhoto() },
                { icon: '❌', title: '隐藏', action: () => this.hide() }
            ];

            tools.forEach(tool => {
                const btn = document.createElement('button');
                btn.innerHTML = tool.icon;
                btn.title = tool.title;
                btn.style.cssText = `
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    border: none;
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    cursor: pointer;
                    font-size: 18px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
                    transition: all 0.2s ease;
                    pointer-events: auto;
                `;
                btn.addEventListener('click', tool.action);
                btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.15)');
                btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1)');
                toolbar.appendChild(btn);
            });

            document.body.appendChild(toolbar);
            this.toolbar = toolbar;

            // 初始发言
            setTimeout(() => this.showSpeech('欢迎来到 AgriSense！'), 1000);
        }

        async showSpeech(text) {
            if (!text) {
                try {
                    const res = await fetch('https://v1.hitokoto.cn');
                    const data = await res.json();
                    text = data.hitokoto || '你好呀~';
                } catch {
                    text = '你好呀~';
                }
            }

            this.speechBubble.textContent = text;
            this.speechBubble.style.opacity = '1';
            this.speechBubble.style.transform = 'translateY(0)';

            setTimeout(() => {
                this.speechBubble.style.opacity = '0';
                this.speechBubble.style.transform = 'translateY(10px)';
            }, 4000);
        }

        startAnimation() {
            let time = 0;
            const animate = () => {
                time += 0.016;
                if (this.model) {
                    // 轻微的呼吸动画
                    const breathe = Math.sin(time * 2) * 0.01;
                    this.model.scale.y = this.config.scale + breathe;
                }
                requestAnimationFrame(animate);
            };
            animate();

            // 每30秒自动发言
            setInterval(() => this.showSpeech(), 30000);
        }

        onTap() {
            if (this.model) {
                // 点击时轻微晃动
                if (this.model.rotation !== undefined) {
                    const originalRotation = this.model.rotation;
                    this.model.rotation = originalRotation + 0.05;
                    setTimeout(() => {
                        this.model.rotation = originalRotation - 0.05;
                        setTimeout(() => {
                            this.model.rotation = originalRotation;
                        }, 100);
                    }, 100);
                }
            }
            this.showSpeech();
        }

        takePhoto() {
            if (this.canvas) {
                const link = document.createElement('a');
                link.download = `live2d-${Date.now()}.png`;
                link.href = this.canvas.toDataURL('image/png');
                link.click();
                this.showSpeech('照片已保存~');
            }
        }

        hide() {
            this.canvas.style.opacity = '0';
            this.canvas.style.pointerEvents = 'none';
            this.toolbar.style.opacity = '0';
            this.toolbar.style.pointerEvents = 'none';

            setTimeout(() => {
                this.canvas.style.opacity = '1';
                this.canvas.style.pointerEvents = 'auto';
                this.toolbar.style.opacity = '1';
                this.toolbar.style.pointerEvents = 'auto';
            }, 5000);

            this.showSpeech('5秒后回来~');
        }

        startDrag(e) {
            this.isDragging = true;
            this.dragStartX = e.clientX;
            this.dragStartY = e.clientY;
            this.canvas.style.cursor = 'grabbing';
        }

        onDrag(e) {
            if (!this.isDragging) return;

            const dx = (e.clientX - this.dragStartX) / window.innerWidth;
            const dy = (e.clientY - this.dragStartY) / window.innerHeight;

            let newX = this.config.position.x + dx;
            let newY = this.config.position.y + dy;

            // 限制范围
            newX = Math.max(0.05, Math.min(0.95, newX));
            newY = Math.max(0.5, Math.min(0.95, newY));

            this.config.position.x = newX;
            this.config.position.y = newY;

            this.canvas.style.left = `${newX * 100}%`;
            this.toolbar.style.left = `${newX * 100}%`;
            this.toolbar.style.bottom = `${(1 - newY) * 100 + 51}%`;
            this.toolbar.style.top = 'auto';

            this.dragStartX = e.clientX;
            this.dragStartY = e.clientY;
        }

        endDrag() {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
        }

        showError() {
            const errorDiv = document.createElement('div');
            errorDiv.style.cssText = `
                position: fixed;
                bottom: 10px;
                left: 10px;
                background: rgba(231, 76, 60, 0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                z-index: 99999;
            `;
            errorDiv.textContent = '⚠️ Live2D 模型加载失败，请检查模型文件';
            document.body.appendChild(errorDiv);
        }
    }

    // 等待 DOM 加载完成
    function initLive2DWidget() {
        // 检查 PIXI 是否已加载
        const checkAndInit = () => {
            if (typeof PIXI !== 'undefined' && typeof live2d !== 'undefined') {
                window.waifu = new Live2DWidget({
                    modelPath: '/static/live2d/models/maid-aris/maidaris.pmx',
                    scale: 0.12,
                    position: { x: 0.1, y: 0.85 }
                });
            } else {
                setTimeout(checkAndInit, 100);
            }
        };

        // 延迟初始化，等待页面完全加载
        if (document.readyState === 'complete') {
            setTimeout(checkAndInit, 500);
        } else {
            window.addEventListener('load', () => setTimeout(checkAndInit, 500));
        }
    }

    // 导出到全局
    window.Live2DWidget = Live2DWidget;
    window.initLive2DWidget = initLive2DWidget;
})();
