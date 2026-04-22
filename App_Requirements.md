# AgriSense 移动应用

基于 Flutter 开发的智能农业大棚移动监控应用。

## 功能特性

- **实时监控**: 查看大棚内温度、湿度、光照、CO₂浓度、气压、VOC、土壤湿度（3 点位）等环境数据
- **设备控制**: 远程控制灌溉、补光、通风、遮阳等设备
- **AI 智能分析**: 获取 AI 提供的环境优化建议和病害诊断
- **AI 对话咨询**: 与 AI 助手多轮对话，自动结合传感器上下文给出农业管理建议
- **数据可视化**: 以图表形式展示传感器历史趋势
- **多主题支持**: 支持浅色/深色主题切换（跟随系统设置）
- **APK 构建**: 支持通过后端 API 构建移动端安装包

## 项目结构

```
mobile_app/
├── lib/
│   ├── main.dart                  # 应用入口
│   ├── services/
│   │   └── api_service.dart       # API 服务层
│   ├── providers/
│   │   ├── sensor_provider.dart   # 传感器数据状态管理
│   │   ├── device_provider.dart   # 设备控制状态管理
│   │   └── ai_provider.dart      # AI 建议与对话状态管理
│   └── pages/
│       ├── home_page.dart        # 首页
│       ├── sensors_page.dart      # 传感器页面
│       ├── devices_page.dart      # 设备控制页面
│       ├── analytics_page.dart    # 数据分析页面
│       └── settings_page.dart     # 设置页面
├── assets/
│   ├── images/                   # 图片资源
│   └── icons/                    # 图标资源
└── pubspec.yaml                  # 项目配置
```

## 环境要求

- Flutter SDK >= 3.0.0
- Dart SDK >= 3.0.0
- Android SDK（构建 APK 时需要）

## 安装依赖

```bash
cd mobile_app
flutter pub get
```

## 运行应用

### 开发模式

```bash
cd mobile_app
flutter run
```

### 构建 Android APK

```bash
cd mobile_app
flutter build apk --release
```

### 构建 iOS 应用

```bash
cd mobile_app
flutter build ios --release
```

## API 配置

在 `lib/services/api_service.dart` 中修改 `baseUrl` 以连接您的后端服务器：

```dart
static const String baseUrl = 'http://your-server-ip:5000';
```

### 后端 API 端点对照

移动端各 Provider 调用后端的实际接口如下（`baseUrl` + 路径）：

| 数据类型 | 后端接口 | 方法 |
|----------|----------|------|
| 传感器数据（所有） | `/api/sensors/all` | GET |
| 环境数据 | `/api/sensors/environment` | GET |
| 土壤数据 | `/api/sensors/soil` | GET |
| 叶片健康分析 | `/api/vision/leaf` | GET |
| 作物健康（CNN） | `/api/vision/crop-health` | GET |
| CNN 病害识别 | `/api/vision/crop-health/upload` | POST (multipart) |
| CNN 病害类别 | `/api/vision/crop-health/classes` | GET |
| 决策建议 | `/api/decisions` | GET |
| AI 对话 | `/api/ai/chat` | POST |
| AI 对话历史 | `/api/ai/history` | GET |
| 清空对话历史 | `/api/ai/history` | DELETE |
| AI 模型信息 | `/api/ai/info` | GET |
| 可用模型列表 | `/api/ai/models` | GET |
| 切换模型 | `/api/ai/models/switch` | POST |
| 每日建议 | `/api/advice/daily` | GET |
| 执行器状态 | `/api/actuators/status` | GET |
| 控制执行器 | `/api/actuators/<device>/control` | POST |
| 紧急停止 | `/api/actuators/stop` | POST |
| 系统状态 | `/api/status` | GET |
| 健康检查 | `/api/health` | GET |
| 传感器历史 | `/api/history` | GET |
| 模拟模式切换 | `/api/simulation/toggle` | POST |

> **注意**: 当前 `api_service.dart` 中的部分端点路径（如 `/api/devices`、`/api/vision/disease`、`/api/ai/advice`）为占位实现，实际使用时请按上表替换为后端真实接口路径，或根据实际需求调整。

## APK 构建功能

后端 Flask 服务提供了 APK 构建相关接口，移动端可通过调用这些接口引导用户完成 APK 生成。

### 构建流程

1. **获取可用目录**：`GET /api/apk/directories`
2. **触发构建**：`POST /api/apk/build`（传入 output_dir、app_name、version）
3. **下载 APK**：`GET /api/apk/download?filename=xxx`
4. **查看构建指南**：`GET /api/apk/guide`

### 本地构建方法

如果需要本地构建真实 APK，推荐方式：

| 方式 | 说明 |
|------|------|
| Bubblewrap（推荐） | Google 官方 TWA 构建工具，需 Node.js + JDK + Android SDK |
| PWABuilder | 微软提供的在线 PWA 打包服务，访问 https://www.pwabuilder.com/ |
| Cordova | Apache 混合框架打包，需 npm + JDK + Android SDK |

## 主要依赖

```yaml
# pubspec.yaml 中对应版本
dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.6
  provider: ^6.1.1          # 状态管理
  http: ^1.1.0              # HTTP 请求
  web_socket_channel: ^2.4.0 # WebSocket 通信（实时数据推送）
  fl_chart: ^0.65.0          # 图表绘制
  cached_network_image: ^3.3.0 # 图片缓存
  flutter_svg: ^2.0.9       # SVG 支持
  intl: ^0.18.1             # 国际化/日期格式化
  permission_handler: ^11.3.0 # 权限管理
  camera: ^0.10.5+9         # 相机功能
  image_picker: ^1.0.7       # 图片选择
  shared_preferences: ^2.2.2  # 本地存储
```

### 状态管理选型说明

项目使用 **Provider** 作为状态管理方案，原因如下：

- API 简单，学习成本低，适合中小型应用
- 与 Flutter 官方推荐的架构风格一致
- `SensorProvider` / `DeviceProvider` / `AIProvider` 分别管理传感器数据、设备状态、AI 建议，职责清晰

### WebSocket 使用说明

实时数据推送通过 `web_socket_channel` 实现。连接方式：

```dart
import 'package:web_socket_channel/web_socket_channel.dart';

final channel = WebSocketChannel.connect(
  Uri.parse('ws://your-server-ip:5000/ws/sensors'),
);

// 监听实时数据
channel.stream.listen((message) {
  // message 为 JSON 格式的传感器数据
  print(message);
});

// 主动断开
channel.sink.close();
```

> **注意**: 当前后端 `app.py` 中尚未实现 WebSocket 端点 (`/ws/sensors`)，此功能属于开发计划中的待实现项。

## 使用说明

### 1. 监控环境数据

打开应用后，在首页可以看到实时环境数据。点击底部导航栏的"传感器"可以查看更多详细信息。

### 2. 控制设备

在"设备"页面，可以单独或批量控制大棚内的灌溉、补光、通风、遮阳等设备。

### 3. 查看 AI 建议与分析

在"分析"页面，可以查看 AI 根据当前环境数据提供的优化建议和病害诊断结果。也可以点击"AI 对话"与助手进行多轮咨询。

### 4. 拍照病害识别

在"分析"页面，点击拍照按钮拍摄作物叶片照片，应用将调用后端 CNN 模型识别 10 种番茄叶片病害。

### 5. 设置

在"设置"页面，可以配置服务器地址、通知、主题等选项。

## 开发计划

### 已完成

- [x] 项目结构与 Provider 状态管理
- [x] HTTP API 服务层 (`api_service.dart`)
- [x] 实时数据监控界面
- [x] 设备控制界面
- [x] AI 建议展示页面
- [x] 多主题切换（浅色/深色，跟随系统）

### 进行中

- [ ] 后端 WebSocket 实时推送集成
- [ ] API 服务层完善（对齐后端实际接口）

### 待开发

- [ ] 图像上传和病害识别（前端拍照/选图 + 后端 CNN 分析）
- [ ] 历史数据查询与图表展示
- [ ] 告警通知功能
- [ ] 多大棚管理
- [ ] APK 真实打包集成

## 许可证

MIT License
