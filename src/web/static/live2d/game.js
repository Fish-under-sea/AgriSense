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

    // 显示结束画面
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#4ecca3';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('游戏结束!', canvas.width / 2, canvas.height / 2 - 40);

    ctx.fillStyle = '#fff';
    ctx.font = '24px Arial';
    ctx.fillText(`最终得分: ${score}`, canvas.width / 2, canvas.height / 2 + 10);

    // 重新开始按钮
    setTimeout(() => {
      const btn = document.createElement('button');
      btn.textContent = '再玩一次';
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
      gameContainer.appendChild(btn);
    }, 500);
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
