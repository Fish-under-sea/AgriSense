# AgriSense - 智能大棚监控系统

基于 AI 的智能农业环境监控与决策系统。

<!-- 徽章栏 -->
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Cross%E2%80%91Platform-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

## 功能特性

- **多传感器融合**：温度、湿度、光照、CO₂、土壤湿度实时监测
- **AI 智能决策**：规则引擎 + LLM 双轨决策，支持 Qwen3.5 / GPT-4o-mini
- **叶片病害识别**：OpenCV 颜色分析 + 可选 TensorFlow/CNN 模型
- **执行器自动控制**：灌溉、补光、通风、遮阳，支持 GPIO 和模拟双模式
- **实时 Web 界面**：Flask 驱动的仪表盘，开箱即用
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

### 配置文件

主配置文件为 `config.json`，位于项目根目录。主要参数说明：

| 分段 | 用途 |
|------|------|
| `sensors.environment` | BME680/SCD30 环境传感器地址与模拟数据范围 |
| `sensors.soil` | 土壤湿度监测点位与模拟数据 |
| `decision.rules_engine` | 温度/湿度/土壤湿度的阈值区间 |
| `decision.llm_advisor` | Ollama/OpenAI 双模型配置 |
| `actuators` | 灌溉/补光/通风/遮阳的 GPIO 引脚与模拟开关 |

详细配置说明请查看 [AgriSense_Requirements.md](AgriSense_Requirements.md)。

## 技术栈

| 类别 | 技术 |
|------|------|
| 核心语言 | Python 3.8+ |
| Web 框架 | Flask |
| 传感器 | BME680 (I2C 0x76)、SCD30 (I2C 0x61) |
| 视觉分析 | OpenCV、TensorFlow |
| LLM 支持 | Ollama (Qwen3.5)、OpenAI GPT-4o-mini |
| 硬件平台 | Raspberry Pi（RPi.GPIO） |
| 模拟运行 | 全模块支持，无需硬件 |

## API 接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/sensors/all` | GET | 获取所有传感器数据 |
| `/api/sensors/environment` | GET | 获取环境数据 |
| `/api/sensors/soil` | GET | 获取土壤数据 |
| `/api/vision/leaf` | GET | 获取叶片健康分析 |
| `/api/decisions` | GET | 获取决策建议 |
| `/api/actuators/status` | GET | 获取设备状态 |
| `/api/actuators/<device>/control` | POST | 控制设备 |
| `/api/advice/daily` | GET | 获取每日建议 |

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
- [App_Requirements.md](App_Requirements.md) — Flutter 移动端架构与功能说明

## 贡献指南

欢迎提交 Issue 和 Pull Request。重大改动请先开 Issue 讨论。

## 许可证

MIT License
