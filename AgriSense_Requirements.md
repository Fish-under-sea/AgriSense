# AgriSense - 智能大棚监控系统

基于 AI 的智能农业环境监控与决策系统

## 项目概述

AgriSense 是一个面向智能大棚的农业监控系统，集成了环境传感器、土壤监测、计算机视觉和 AI 决策功能，帮助用户实时监控作物生长环境并提供智能管理建议。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AgriSense 主系统                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────────┐  ┌────────────────────┐        │
│  │    传感器模块   │  │    视觉分析模块     │  │      决策模块       │        │
│  │                │  │                    │  │                    │        │
│  │ - 环境传感器    │  │ - 叶片病害分析     │  │ - 规则引擎         │        │
│  │ - 土壤传感器    │  │ - CNN 作物分析     │  │ - LLM 顾问         │        │
│  │ - 相机模块     │  │ - 生长测量         │  │ - AI 对话系统       │        │
│  └────────────────┘  └────────────────────┘  └────────────────────┘        │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────┐  ┌────────────────────────────────────────┐             │
│  │    控制模块     │  │           Web 界面                     │             │
│  │                │  │                                        │             │
│  │ - 执行器控制    │  │ - 监控仪表盘 (/ )                      │             │
│  │ - GPIO 集成    │  │ - 设备控制 (/controller)               │             │
│  │                │  │ - 模拟数据控制 (/simulator)            │             │
│  └────────────────┘  │ - 移动端适配 (/mobile)                  │             │
│                      └────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 功能模块详解

### 1. 传感器模块 (src/sensors/)

#### 1.1 环境传感器 (environment.py)
- **功能**: 温度、湿度、光照强度、CO₂ 浓度、气压、VOC 监测
- **支持硬件**: BME680、SCD30 等传感器
- **模拟模式**: 当硬件不可用时自动切换到模拟数据
- **特色功能**:
  - 光合作用有效辐射 (PAR) 估算
  - 光合作用速率计算
  - 环境状态评估与建议

#### 1.2 土壤传感器 (soil_moisture.py)
- **功能**: 多点土壤湿度监测（支持 3 个点位）
- **支持硬件**: RPi.GPIO + ADC 传感器
- **功能特性**:
  - 湿度阈值判断（干燥 < 30% / 最佳 30-70% / 过湿 > 70%）
  - 各点位独立状态监测
  - 平均湿度计算
  - 灌溉决策支持

#### 1.3 相机模块 (camera.py)
- **功能**: 图像采集
- **支持硬件**: Raspberry Pi 摄像头
- **分辨率**: 640x480 (可配置)
- **模式**: 支持拍照和模拟两种模式

### 2. 视觉分析模块 (src/vision/)

#### 2.1 叶片病害分析 (leaf_disease.py)
- **病害类型**:
  - 白粉病、霜霉病、叶斑病
  - 炭疽病、脐腐病、早疫病、晚疫病
- **营养缺乏检测**: 缺氮、缺磷、缺钾、缺镁、缺铁、缺钙
- **虫害检测**: 蚜虫、红蜘蛛、白粉虱、蓟马、介壳虫
- **技术实现**:
  - 基于 OpenCV 的颜色特征分析
  - 健康评分系统（0-100）

#### 2.2 CNN 作物病害识别 (cnn_crop_analyzer.py)

**核心能力**：基于 TensorFlow CNN 模型，识别番茄叶片 10 种状态。

- **识别类别**:

| 类别代码 | 中文名称 |
|----------|----------|
| Tomato___healthy | 健康 |
| Tomato___Bacterial_spot | 细菌性斑点病 |
| Tomato___Early_blight | 早疫病 |
| Tomato___Late_blight | 晚疫病 |
| Tomato___Leaf_Mold | 叶霉病 |
| Tomato___Septoria_leaf_spot | Septoria 叶斑病 |
| Tomato___Spider_mites Two-spotted_spider_mite | 红蜘蛛虫害 |
| Tomato___Target_Spot | 靶斑病 |
| Tomato___Tomato_mosaic_virus | 花叶病毒病 |
| Tomato___Tomato_Yellow_Leaf_Curl_Virus | 黄曲叶病毒病 |

- **技术实现**:
  - TensorFlow Keras CNN 模型（默认 `dataset/cnn_model.h5`）
  - 输入尺寸 128x128
  - 模拟模式下基于 HSV 颜色特征分析作为备选
  - 置信度阈值可配置（默认 0.6）
  - 每种病害对应处理建议

#### 2.3 生长测量 (growth_measure.py)
- **功能**: 作物生长状态分析
- **输出**: 生长阶段判断、生长率估算

### 3. 决策模块 (src/decision/)

#### 3.1 规则引擎 (rules_engine.py)
- **决策规则**:
  - 温度控制：18-32°C 最佳范围
  - 湿度控制：45-75% 最佳范围
  - 土壤湿度：35-65% 最佳范围
- **动作类型**: 灌溉、补光、通风、遮阳

#### 3.2 LLM 顾问 (llm_advisor.py)

**支持模型（配置于 `config.json`）**:

| 模型标识 | 名称 | 供应商 | 说明 |
|----------|------|--------|------|
| `gemma4` | Gemma 4 e4b (本地) | Ollama | 支持思考过程展示 |
| `gpt-4o-mini` | GPT-4o-mini (云端) | OpenAI | 通过代理调用 |
| `qwen3.5` | Qwen 3.5 9B (本地) | Ollama | 本地部署 |

**功能**:
- 智能决策建议（30 字以内）
- 每日生长报告
- 综合环境分析
- **多轮对话咨询**：支持带上下文的多轮对话，自动注入传感器数据作为上下文，支持思考过程（Think）展示
- 模型动态切换

**接入配置**:

1. **Ollama ( Gemma 4 / Qwen 3.5，本地推荐)**

   确保 Ollama 服务已启动：
   ```bash
   ollama run gemma4:e4b
   # 或
   ollama run qwen3.5:9b
   ```
   配置文件中启用并指向 `http://localhost:11434`。

2. **OpenAI (GPT-4o-mini，云端)**

   设置环境变量或直接修改 `config.json`：
   ```json
   "gpt-4o-mini": {
     "provider": "openai",
     "model": "gpt-4o-mini",
     "base_url": "https://your-proxy/v1",
     "api_key": "sk-..."
   }
   ```

3. **切换模型**：在 `config.json` 的 `decision.llm_advisor.default_model` 中选择，或通过 `/api/ai/models/switch` 接口动态切换。

### 4. 控制模块 (src/control/)

#### 执行器控制 (actuator.py)
- **设备控制**:

| 设备 | GPIO 引脚 | 说明 |
|------|----------|------|
| 灌溉系统 | GPIO 17 | 继电器控制 |
| 补光系统 | GPIO 27 | LED 补光灯 |
| 通风系统 | GPIO 22 | 排气风扇 |
| 遮阳系统 | GPIO 23 | 遮阳网电机 |

- **功能**:
  - 开关控制
  - 状态查询
  - 紧急停止（`/api/actuators/stop`）

### 5. Web 界面 (src/web/)

- **框架**: Flask + Flask-CORS
- **页面**:

| 页面 | 路由 | 说明 |
|------|------|------|
| 监控仪表盘 | `/` | 实时传感器数据、设备状态、AI 建议 |
| 设备控制 | `/controller` | 四个执行器的独立控制面板 |
| 模拟数据控制 | `/simulator` | 调整环境/土壤模拟数据，随机化测试 |
| 移动端适配 | `/mobile` | 手机端适配的控制页面 |

- **API 端点**: 详见 [README.md](README.md) API 接口部分

## 项目结构

```
AgriSense/
├── src/
│   ├── main.py                   # 命令行主入口
│   ├── sensors/
│   │   ├── environment.py       # 环境传感器 (BME680/SCD30)
│   │   ├── soil_moisture.py     # 土壤湿度传感器 (3 点位)
│   │   └── camera.py            # 相机模块
│   ├── vision/
│   │   ├── leaf_disease.py      # 叶片病害分析 (OpenCV)
│   │   ├── cnn_crop_analyzer.py # CNN 作物病害识别 (TensorFlow)
│   │   └── growth_measure.py    # 生长测量
│   ├── decision/
│   │   ├── rules_engine.py      # 规则引擎
│   │   └── llm_advisor.py       # LLM 顾问 + 对话系统
│   ├── control/
│   │   └── actuator.py          # 执行器控制
│   └── web/
│       ├── app.py                # Flask Web 应用 (所有 API 路由)
│       └── templates/
│           ├── index.html        # 监控仪表盘
│           ├── controller.html    # 设备控制页
│           ├── simulator.html     # 模拟数据控制页
│           └── mobile.html        # 移动端适配页
├── dataset/
│   ├── cnn_train.py              # CNN 模型训练脚本
│   └── cnn_model.h5              # 训练好的模型文件 (需单独下载)
├── mobile_app/                   # Flutter 移动端应用
│   ├── lib/
│   │   ├── main.dart
│   │   ├── services/api_service.dart
│   │   ├── providers/
│   │   │   ├── sensor_provider.dart
│   │   │   ├── device_provider.dart
│   │   │   └── ai_provider.dart
│   │   └── pages/
│   │       ├── home_page.dart
│   │       ├── sensors_page.dart
│   │       ├── devices_page.dart
│   │       ├── analytics_page.dart
│   │       └── settings_page.dart
│   └── pubspec.yaml
├── config.json                   # 配置文件
├── requirements.txt              # Python 依赖
├── AgriSense_Requirements.md     # 本文件
├── App_Requirements.md            # 移动端需求文档
└── README.md                     # 项目总览
```

## 项目渲染

> **提示**：系统架构概念图和 Web UI 原型图请放入 `rendering/` 目录，命名为 `concept_art.png` 和 `ui_mockup.png` 后替换下方链接。若暂无图片，可直接删除以下两行。

![概念图](rendering/concept_art.png)

![UI 原型](rendering/ui_mockup.png)

## 运行模式

### 模拟模式 (Simulation Mode)
- 适用于开发和测试
- 自动生成模拟传感器数据
- 无需真实硬件连接
- 可通过 `/simulator` 页面动态调整模拟数据值

### 硬件模式 (Hardware Mode)
- 连接真实传感器和执行器
- 需要 Raspberry Pi 硬件
- 需要安装相应驱动

**模式切换**: 通过 `/api/simulation/toggle` 接口或 `initialize_modules(simulation=bool)` 调用。

## 开发计划

### 已完成

- [x] Web 界面 (Flask，src/web/)
- [x] 传感器模拟模式 (所有传感器支持)
- [x] 叶片病害分析 (OpenCV)
- [x] CNN 作物病害识别 (TensorFlow Keras，10 类番茄病害)
- [x] LLM 决策顾问 (Ollama / OpenAI，多模型支持)
- [x] AI 对话咨询系统 (多轮对话、上下文注入、思考过程展示)
- [x] 照片上传与管理系统 (快照、列表、删除、清理)
- [x] 模拟数据控制页面
- [x] 设备控制页面
- [x] 移动端适配页面
- [x] Flutter 移动端基础架构 (Provider 状态管理)

### 进行中

- [ ] 数据持久化 (SQLite)
- [ ] 历史数据图表展示
- [ ] Flutter 移动端完整实现

### 待开发

- [ ] 用户认证系统
- [ ] 多大棚管理
- [ ] 自动化控制策略优化
- [ ] 更多病害识别模型
- [ ] 实时 WebSocket 推送
- [ ] 告警通知功能
