# AgriSense - 智能大棚监控系统

基于 AI 的智能农业环境监控与决策系统

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行主程序
```bash
cd src
python main.py
```

### 运行 Web 界面
```bash
cd src/web
python app.py
```
访问 http://localhost:5000

## 配置文件 (config.json)

```json
{
  "sensors": {
    "environment": {
      "i2c_address": "0x76",
      "simulation": {
        "temperature": {"min": 18, "max": 32, "value": 25},
        "humidity": {"min": 40, "max": 80, "value": 60},
        "light": {"min": 500, "max": 5000, "value": 2500},
        "co2": {"min": 400, "max": 1200, "value": 600}
      }
    },
    "soil": {
      "num_points": 3,
      "simulation": {
        "points": [
          {"min": 20, "max": 80, "value": 45},
          {"min": 20, "max": 80, "value": 50},
          {"min": 20, "max": 80, "value": 48}
        ]
      }
    }
  },
  "decision": {
    "rules_engine": {
      "enabled": true,
      "rules": {
        "temperature": {"min": 18, "max": 32},
        "humidity": {"min": 45, "max": 75},
        "soil_moisture": {"min": 35, "max": 65}
      }
    },
    "llm_advisor": {
      "enabled": true,
      "models": {
        "qwen3.5": {
          "provider": "ollama",
          "base_url": "http://localhost:11434"
        },
        "gpt-4o-mini": {
          "provider": "openai",
          "base_url": "https://api.openai.com/v1"
        }
      }
    }
  },
  "actuators": {
    "irrigation": {"pin": 17, "simulation": true},
    "light": {"pin": 27, "simulation": true},
    "fan": {"pin": 22, "simulation": true},
    "shade": {"pin": 23, "simulation": true}
  }
}
```

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
| SCD30 | I2C 0x61 | CO2 传感器 |

## 许可证

MIT License

---

📖 **详细文档**: 查看 [AgriSense_Requirements.md](AgriSense_Requirements.md) 了解系统架构、功能模块详解和开发计划。