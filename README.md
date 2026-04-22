# AgriSense - 智能大棚监控系统

基于 AI 的智能农业环境监控与决策系统。

<!-- 徽章栏 -->
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Cross%E2%80%91Platform-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

## 功能特性

- **多传感器融合**：温度、湿度、光照、CO₂、气压、VOC 实时监测，支持 3 点土壤湿度采集
- **AI 智能决策**：规则引擎 + LLM 双轨决策，支持 Gemma 4 / Qwen 3.5 (Ollama 本地) / GPT-4o-mini (云端代理)
- **叶片病害识别**：OpenCV 颜色分析 + CNN 模型（TensorFlow），识别 10 种番茄叶片状态
- **AI 对话咨询**：支持多轮对话、带思考过程展示，可结合传感器上下文给出建议
- **执行器自动控制**：灌溉、补光、通风、遮阳，支持 GPIO 和模拟双模式
- **实时 Web 界面**：Flask 驱动，提供监控仪表盘、模拟数据控制、设备控制、AI 对话多页面
- **照片管理**：支持拍照上传、快照列表、自动清理历史照片
- **零硬件依赖**：所有传感器支持模拟数据模式，无需真实硬件即可开发测试

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行主程序（命令行模式）

```bash
cd src
python main.py
```

### 运行 Web 界面

```bash
cd src/web
python app.py
# 访问 http://localhost:5000
```

### Web 界面页面说明

| 页面 | 路径 | 说明 |
|------|------|------|
| 监控仪表盘 | `/` | 实时传感器数据、设备状态、AI 建议展示 |
| 设备控制 | `/controller` | 灌溉、补光、通风、遮阳独立控制 |
| 模拟数据控制 | `/simulator` | 调整模拟传感器数值，测试决策逻辑 |
| 移动端适配页 | `/mobile` | 适配手机浏览的控制页面 |

### 配置文件

主配置文件为 `config.json`，位于项目根目录。主要参数说明：

| 分段 | 用途 |
|------|------|
| `sensors.environment` | BME680 环境传感器，模拟数据范围（温度/湿度/光照/CO₂/气压/VOC） |
| `sensors.soil` | 土壤湿度监测 3 点位，模拟数据配置 |
| `decision.rules_engine` | 温度/湿度/土壤湿度的阈值区间及触发动作 |
| `decision.llm_advisor` | Ollama（本地 Gemma 4 / Qwen 3.5）/ OpenAI（GPT-4o-mini 云端代理）双轨配置 |
| `actuators` | 灌溉/补光/通风/遮阳的 GPIO 引脚与模拟开关 |

详细配置说明请查看 [AgriSense_Requirements.md](AgriSense_Requirements.md)。

## 技术栈

| 类别 | 技术 |
|------|------|
| 核心语言 | Python 3.8+ |
| Web 框架 | Flask + Flask-CORS |
| 传感器 | BME680 (I2C 0x76)、SCD30 (I2C 0x61) |
| 视觉分析 | OpenCV、TensorFlow、PyTorch、scikit-learn |
| CNN 病害识别 | TensorFlow Keras，支持 10 类番茄叶片（健康 + 9 种病害） |
| LLM 支持 | Ollama (Gemma 4 / Qwen 3.5 本地)、OpenAI GPT-4o-mini (云端代理) |
| 硬件平台 | Raspberry Pi（RPi.GPIO） |
| 移动端 | Flutter + Provider（见 `mobile_app/` 目录） |
| 模拟运行 | 全模块支持，无需硬件 |

## API 接口

### 传感器数据

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/sensors/all` | GET | 获取所有传感器数据 |
| `/api/sensors/environment` | GET | 获取环境数据（温度/湿度/光照/CO₂/气压/VOC） |
| `/api/sensors/soil` | GET | 获取土壤数据（3 点位湿度） |

### 视觉分析

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vision/leaf` | GET | 获取叶片健康分析（OpenCV 颜色分析） |
| `/api/vision/growth` | GET | 获取生长测量数据 |
| `/api/vision/crop-health` | GET | 获取 CNN 作物健康分析结果 |
| `/api/vision/crop-health/upload` | POST | 上传图像进行 CNN 病害识别（multipart） |
| `/api/vision/crop-health/classes` | GET | 获取 CNN 支持的 10 种病害类别 |

### 决策与 AI

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/decisions` | GET | 获取规则引擎 + LLM 双重决策建议 |
| `/api/ai/chat` | POST | AI 对话咨询，支持多轮上下文（JSON: message/session_id/use_context） |
| `/api/ai/history` | GET | 获取 AI 对话历史（query: session_id） |
| `/api/ai/history` | DELETE | 清空指定对话历史 |
| `/api/ai/info` | GET | 获取 AI 能力信息与当前模型 |
| `/api/ai/models` | GET | 获取可用模型列表 |
| `/api/ai/models/switch` | POST | 切换 LLM 模型（JSON: model_key） |
| `/api/advice/daily` | GET | 获取每日生长报告 |

### 执行器控制

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/actuators/status` | GET | 获取执行器状态 |
| `/api/actuators/<device>/control` | POST | 控制设备（irrigation/light/fan/shade，JSON: state） |
| `/api/actuators/stop` | POST | 紧急停止所有执行器 |

### 照片管理

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/snapshot` | POST | 拍照（硬件模式）；模拟模式返回提示 |
| `/api/snapshot/upload` | POST | 上传照片进行分析（multipart: image） |
| `/api/snapshots/list` | GET | 获取已保存照片列表 |
| `/api/snapshots/<filename>` | GET | 获取单张照片 |
| `/api/snapshots/<filename>` | DELETE | 删除单张照片 |
| `/api/snapshots/clear` | POST | 清空所有照片 |

### 系统与模拟控制

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/status` | GET | 获取系统状态（模式、运行状态） |
| `/api/health` | GET | 健康检查，返回所有模块初始化状态 |
| `/api/heartbeat` | GET | 心跳检测 |
| `/api/simulation/toggle` | POST | 切换模拟/硬件模式（JSON: enabled） |
| `/api/simulation/config` | GET | 获取模拟数据配置 |
| `/api/simulation/config` | POST | 更新模拟数据值（JSON: category/key/value） |
| `/api/simulation/randomize` | POST | 随机化模拟数据 |
| `/api/config/rules` | GET | 获取规则引擎配置 |
| `/api/config/rules` | POST | 更新规则阈值（JSON: category/key/value） |
| `/api/history` | GET | 获取传感器历史记录（内存中） |
| `/api/history/clear` | POST | 清空历史记录 |

### APK 构建

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/apk/directories` | GET | 获取可用输出目录列表 |
| `/api/apk/build` | POST | 触发 APK 构建（JSON: output_dir/app_name/version） |
| `/api/apk/download` | GET | 下载构建的 APK 文件 |
| `/api/apk/guide` | GET | 获取 APK 构建指南 |

## 硬件连接 (Raspberry Pi)

| 设备 | GPIO 引脚 | 说明 |
|------|----------|------|
| 灌溉系统 | GPIO 17 | 继电器控制 |
| 补光系统 | GPIO 27 | LED 补光灯 |
| 通风系统 | GPIO 22 | 排气风扇 |
| 遮阳系统 | GPIO 23 | 遮阳网电机 |
| BME680 | I2C 0x76 | 环境传感器 |
| SCD30 | I2C 0x61 | CO₂ 传感器 |

## 项目截图

> 系统架构图
>
> ![架构图](rendering/concept_art.png)

> Web 界面截图
>
> ![UI 原型](rendering/ui_mockup.png)

## 相关文档

- [AgriSense_Requirements.md](AgriSense_Requirements.md) — 系统架构、功能模块详解与开发计划
- [App_Requirements.md](App_Requirements.md) — Flutter 移动端架构、功能说明与 API 配置

## 贡献指南

欢迎提交 Issue 和 Pull Request。重大改动请先开 Issue 讨论。

## 许可证

MIT License
