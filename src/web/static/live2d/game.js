// AgriSense 小游戏 - 目标点击
function TargetClickGame() {
  const that = this;
  let canvas, ctx;
  let gameContainer;
  let score = 0;
  let timeLeft = 30;
  let isRunning = false;
  let target = null;
  let timer = null;
  let animationId = null;

  // 初始化游戏
  this.init = function() {
    // 创建游戏容器
    gameContainer = document.createElement('div');
    gameContainer.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      z-index: 10000;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-family: 'Segoe UI', Arial, sans-serif;
    `;

    // 创建画布
    canvas = document.createElement('canvas');
    canvas.style.cssText = 'border: 3px solid #4ecca3; border-radius: 10px; cursor: crosshair;';
    updateCanvasSize();

    // 创建 UI
    const ui = document.createElement('div');
    ui.style.cssText = `
      display: flex;
      gap: 40px;
      margin-bottom: 20px;
      color: #4ecca3;
      font-size: 24px;
      font-weight: bold;
    `;
    ui.innerHTML = `
      <div>得分: <span id="tg-score">0</span></div>
      <div>时间: <span id="tg-time">30</span>秒</div>
    `;

    // 创建说明
    const info = document.createElement('div');
    info.style.cssText = `
      color: #888;
      font-size: 14px;
      margin-bottom: 20px;
    `;
    info.textContent = '点击出现的绿色目标得分！';

    // 创建关闭按钮
    const closeBtn = document.createElement('button');
    closeBtn.style.cssText = `
      margin-top: 20px;
      padding: 10px 30px;
      background: #4ecca3;
      color: #000;
      border: none;
      border-radius: 25px;
      font-size: 16px;
      cursor: pointer;
      transition: all 0.3s;
    `;
    closeBtn.textContent = '退出游戏';
    closeBtn.onmouseover = () => closeBtn.style.transform = 'scale(1.1)';
    closeBtn.onmouseout = () => closeBtn.style.transform = 'scale(1)';
    closeBtn.onclick = () => this.destroy();

    // 组装
    gameContainer.appendChild(info);
    gameContainer.appendChild(ui);
    gameContainer.appendChild(canvas);
    gameContainer.appendChild(closeBtn);
    document.body.appendChild(gameContainer);

    // 绑定事件
    canvas.addEventListener('click', handleClick);
    window.addEventListener('resize', updateCanvasSize);

    // 开始游戏
    this.start();
  };

  function updateCanvasSize() {
    const w = Math.min(window.innerWidth - 40, 600);
    const h = Math.min(window.innerHeight - 200, 400);
    canvas.width = w;
    canvas.height = h;
    ctx = canvas.getContext('2d');
  }

  this.start = function() {
    score = 0;
    timeLeft = 30;
    isRunning = true;
    updateUI();
    spawnTarget();
    startTimer();
    gameLoop();
  };

  function startTimer() {
    if (timer) clearInterval(timer);
    timer = setInterval(() => {
      timeLeft--;
      updateUI();
      if (timeLeft <= 0) {
        endGame();
      }
    }, 1000);
  }

  function updateUI() {
    const scoreEl = document.getElementById('tg-score');
    const timeEl = document.getElementById('tg-time');
    if (scoreEl) scoreEl.textContent = score;
    if (timeEl) {
      timeEl.textContent = timeLeft;
      if (timeLeft <= 5) {
        timeEl.style.color = '#ff6b6b';
      }
    }
  }

  function spawnTarget() {
    if (!isRunning) return;
    const radius = 25 + Math.random() * 15;
    target = {
      x: radius + Math.random() * (canvas.width - radius * 2),
      y: radius + Math.random() * (canvas.height - radius * 2),
      radius: radius,
      spawnTime: Date.now(),
      maxLife: 800 + Math.random() * 400
    };
  }

  function handleClick(e) {
    if (!isRunning || !target) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const dist = Math.sqrt((x - target.x) ** 2 + (y - target.y) ** 2);
    if (dist <= target.radius) {
      // 点击命中
      const timeBonus = Math.max(0, (target.maxLife - (Date.now() - target.spawnTime)) / target.maxLife);
      score += Math.floor(10 + timeBonus * 10);
      updateUI();
      spawnTarget();
    }
  }

  function gameLoop() {
    if (!isRunning) return;

    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 绘制网格背景
    ctx.strokeStyle = 'rgba(78, 204, 163, 0.1)';
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // 绘制目标
    if (target) {
      const age = Date.now() - target.spawnTime;
      const lifeRatio = Math.max(0, 1 - age / target.maxLife);

      // 外圈（渐变消失效果）
      const gradient = ctx.createRadialGradient(
        target.x, target.y, 0,
        target.x, target.y, target.radius
      );
      gradient.addColorStop(0, `rgba(78, 204, 163, ${lifeRatio})`);
      gradient.addColorStop(0.7, `rgba(78, 204, 163, ${lifeRatio * 0.6})`);
      gradient.addColorStop(1, `rgba(78, 204, 163, 0)`);

      ctx.beginPath();
      ctx.arc(target.x, target.y, target.radius, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();

      // 内圈
      ctx.beginPath();
      ctx.arc(target.x, target.y, target.radius * 0.6, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(78, 204, 163, ${lifeRatio})`;
      ctx.fill();

      // 中心点
      ctx.beginPath();
      ctx.arc(target.x, target.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#fff';
      ctx.fill();

      // 检查目标是否过期
      if (age >= target.maxLife) {
        spawnTarget();
      }
    }

    animationId = requestAnimationFrame(gameLoop);
  }

  function endGame() {
    isRunning = false;
    if (timer) clearInterval(timer);
    if (animationId) cancelAnimationFrame(animationId);

    // 清空画布
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#4ecca3';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('游戏结束!', canvas.width / 2, canvas.height / 2 - 40);

    ctx.fillStyle = '#fff';
    ctx.font = '24px Arial';
    ctx.fillText(`最终得分: ${score}`, canvas.width / 2, canvas.height / 2 + 10);

    // 移除已有的按钮（防止重复）
    const existingBtn = gameContainer.querySelector('.tg-retry-btn, .tg-egg-btn');
    if (existingBtn) existingBtn.remove();

    setTimeout(() => {
      const btn = document.createElement('button');

      if (score > 800) {
        // 彩蛋模式：显示鸡蛋按钮
        btn.textContent = '🥚';
        btn.className = 'tg-egg-btn';
        btn.title = '点我有惊喜！';
        btn.style.cssText = `
          position: absolute;
          top: ${canvas.getBoundingClientRect().top + canvas.height / 2 + 50}px;
          left: 50%;
          transform: translateX(-50%);
          width: 80px;
          height: 80px;
          background: radial-gradient(circle at 40% 35%, #fff8e1, #f5d060, #e8a020);
          border: 3px solid #c07010;
          border-radius: 50%;
          font-size: 40px;
          cursor: pointer;
          box-shadow: 0 6px 20px rgba(0,0,0,0.4), inset 0 -3px 8px rgba(0,0,0,0.15);
          transition: transform 0.2s;
          z-index: 10;
        `;
        btn.onmouseover = () => btn.style.transform = 'translateX(-50%) scale(1.15)';
        btn.onmouseout = () => btn.style.transform = 'translateX(-50%) scale(1)';
        btn.onclick = () => showEggExplosion();
      } else {
        // 普通模式：再玩一次
        btn.textContent = '再玩一次';
        btn.className = 'tg-retry-btn';
        btn.style.cssText = `
          position: absolute;
          top: ${canvas.getBoundingClientRect().top + canvas.height / 2 + 50}px;
          left: 50%;
          transform: translateX(-50%);
          padding: 12px 30px;
          background: #4ecca3;
          color: #000;
          border: none;
          border-radius: 25px;
          font-size: 16px;
          cursor: pointer;
        `;
        btn.onclick = () => {
          btn.remove();
          this.start();
        };
      }

      gameContainer.appendChild(btn);
    }, 500);
  }

  // ===== 彩蛋破蛋动画 =====
  function showEggExplosion() {
    // 隐藏鸡蛋按钮
    const eggBtn = gameContainer.querySelector('.tg-egg-btn');
    if (eggBtn) eggBtn.style.display = 'none';

    // 创建鸡蛋容器的中心位置
    const eggRect = gameContainer.getBoundingClientRect();
    const centerX = eggRect.width / 2;
    const centerY = eggRect.height / 2;

    // 创建动画覆盖层
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      pointer-events: none;
      z-index: 20;
    `;

    // 鸡蛋
    const egg = document.createElement('div');
    egg.style.cssText = `
      position: absolute;
      left: ${centerX - 60}px;
      top: ${centerY - 80}px;
      width: 120px;
      height: 160px;
      background: radial-gradient(circle at 40% 35%, #fff8e1, #f5d060, #e8a020);
      border: 4px solid #c07010;
      border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
      box-shadow: 0 8px 30px rgba(0,0,0,0.5);
      animation: egg-crack-in 0.4s ease-out forwards;
      transform-origin: center center;
    `;
    overlay.appendChild(egg);

    // 裂纹文字
    const crackText = document.createElement('div');
    crackText.textContent = '💥';
    crackText.style.cssText = `
      position: absolute;
      left: ${centerX - 30}px;
      top: ${centerY - 30}px;
      font-size: 60px;
      opacity: 0;
      animation: crack-flash 0.3s ease-out 0.3s forwards;
    `;
    overlay.appendChild(crackText);

    // 生成碎片和彩带
    const fragments = [];
    const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#FF69B4', '#7B68EE', '#FFD700', '#fff'];
    const fragmentsCount = 28;
    for (let i = 0; i < fragmentsCount; i++) {
      const angle = (Math.PI * 2 / fragmentsCount) * i + Math.random() * 0.5;
      const speed = 180 + Math.random() * 200;
      const size = 12 + Math.random() * 20;
      const color = colors[i % colors.length];
      const isCircle = i % 3 === 0;

      const frag = document.createElement('div');
      const delay = 0.15 + Math.random() * 0.2;
      const isConfetti = i % 4 === 0;

      frag.style.cssText = `
        position: absolute;
        left: ${centerX}px;
        top: ${centerY}px;
        width: ${isConfetti ? 12 : size}px;
        height: ${isConfetti ? size * 0.6 : size}px;
        background: ${isConfetti ? color : 'radial-gradient(circle at 30% 30%, #fff8e1, #f5d060, #c07010)'};
        ${isCircle ? 'border-radius: 50%;' : 'border-radius: 3px;'}
        border: ${isConfetti ? 'none' : '2px solid #a05000'};
        transform: translate(-50%, -50%) scale(0);
        animation: frag-fly-${i % 4} ${0.8 + Math.random() * 0.5}s ${delay}s ease-out forwards;
      `;

      // 动态创建关键帧
      const keyName = `frag-fly-${i % 4}`;
      if (!document.getElementById('egg-dyn-css')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'egg-dyn-css';
        document.head.appendChild(styleEl);
      }
      const styleEl = document.getElementById('egg-dyn-css');
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed - 80;
      const rot = (Math.random() * 720 - 360) + 'deg';
      const rot2 = (Math.random() * 720 - 360) + 'deg';
      styleEl.textContent += `
        @keyframes frag-fly-${i % 4} {
          0%   { transform: translate(-50%, -50%) scale(0); opacity: 1; }
          60%  { transform: translate(calc(-50% + ${vx * 0.6}px), calc(-50% + ${vy * 0.6}px)) scale(1.2) rotate(${rot}); opacity: 1; }
          100% { transform: translate(calc(-50% + ${vx}px), calc(-50% + ${vy + 150}px)) scale(0.5) rotate(${rot2}); opacity: 0; }
        }
      `;

      fragments.push(frag);
      overlay.appendChild(frag);
    }

    // 光芒扩散
    const flash = document.createElement('div');
    flash.style.cssText = `
      position: absolute;
      left: ${centerX - 100}px;
      top: ${centerY - 100}px;
      width: 200px;
      height: 200px;
      background: radial-gradient(circle, rgba(255,255,200,0.9), rgba(255,200,50,0.4), transparent);
      border-radius: 50%;
      animation: egg-flash 0.5s ease-out 0.2s forwards;
      transform: scale(0);
    `;
    overlay.appendChild(flash);

    // 注入关键帧
    injectEggStyles();

    gameContainer.appendChild(overlay);

    // 动画结束后跳转
    setTimeout(() => {
      overlay.remove();
      const dynCss = document.getElementById('egg-dyn-css');
      if (dynCss) dynCss.remove();

      // 跳转到目标网站（在新标签页打开）
      window.open('https://pornhub.com', '_blank');
    }, 1600);
  }

  function injectEggStyles() {
    if (document.getElementById('egg-css')) return;
    const style = document.createElement('style');
    style.id = 'egg-css';
    style.textContent = `
      @keyframes egg-crack-in {
        0%   { transform: scale(1); }
        20%  { transform: scale(1.15); }
        40%  { transform: scale(0.9) rotate(-5deg); }
        60%  { transform: scale(1.05) rotate(3deg); }
        100% { transform: scale(0); opacity: 0; }
      }
      @keyframes crack-flash {
        0%   { opacity: 0; transform: scale(0.3); }
        50%  { opacity: 1; transform: scale(1.8); }
        100% { opacity: 0; transform: scale(3); }
      }
      @keyframes egg-flash {
        0%   { transform: scale(0); opacity: 1; }
        50%  { transform: scale(3); opacity: 0.8; }
        100% { transform: scale(5); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

  this.destroy = function() {
    isRunning = false;
    if (timer) clearInterval(timer);
    if (animationId) cancelAnimationFrame(animationId);
    window.removeEventListener('resize', updateCanvasSize);
    if (gameContainer && gameContainer.parentNode) {
      gameContainer.parentNode.removeChild(gameContainer);
    }
  };
}

// 全局函数
window.TargetClickGame = TargetClickGame;
