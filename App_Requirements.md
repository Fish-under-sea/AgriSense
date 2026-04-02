# AgriSense 移动应用

基于 Flutter 开发的智能农业大棚移动监控应用。

## 功能特性

- **实时监控**: 查看大棚内温度、湿度、光照、CO₂浓度、土壤湿度等环境数据
- **设备控制**: 远程控制通风、灌溉、补光、加热等设备
- **AI 智能分析**: 获取 AI 提供的环境优化建议和病害诊断
- **数据可视化**: 以图表形式展示传感器历史趋势
- **多主题支持**: 支持浅色/深色主题切换

## 项目结构

```
mobile_app/
├── lib/
│   ├── main.dart              # 应用入口
│   ├── services/
│   │   └── api_service.dart   # API 服务层
│   ├── providers/
│   │   ├── sensor_provider.dart    # 传感器数据状态管理
│   │   ├── device_provider.dart    # 设备控制状态管理
│   │   └── ai_provider.dart        # AI 建议状态管理
│   └── pages/
│       ├── home_page.dart      # 首页
│       ├── sensors_page.dart   # 传感器页面
│       ├── devices_page.dart   # 设备控制页面
│       ├── analytics_page.dart # 数据分析页面
│       └── settings_page.dart  # 设置页面
├── assets/
│   ├── images/                 # 图片资源
│   └── icons/                  # 图标资源
└── pubspec.yaml               # 项目配置
```

## 环境要求

- Flutter SDK >= 3.0.0
- Dart SDK >= 3.0.0

## 安装依赖

```bash
flutter pub get
```

## 运行应用

### 开发模式

```bash
flutter run
```

### 构建 Android APK

```bash
flutter build apk --release
```

### 构建 iOS 应用

```bash
flutter build ios --release
```

## API 配置

在 `lib/services/api_service.dart` 中修改 `baseUrl` 以连接您的后端服务器：

```dart
static const String baseUrl = 'http://your-server-ip:5000';
```

## 主要依赖

```yaml
# pubspec.yaml 中对应版本（推荐）
dependencies:
  provider: ^6.1.2          # 状态管理
  http: ^1.2.2              # HTTP 请求
  web_socket_channel: ^3.0.1 # WebSocket 通信（用于实时数据推送）
  fl_chart: ^0.69.0          # 图表绘制
  shared_preferences: ^2.3.3  # 本地存储
  camera: ^0.11.0+2           # 相机功能
  image_picker: ^1.1.2       # 图片选择
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

> 后端 WebSocket 端点：`ws://localhost:5000/ws/sensors`（需后端 `app.py` 支持，具体路径以实际实现为准）。

## 使用说明

### 1. 监控环境数据

打开应用后，在首页可以看到实时环境数据。点击底部导航栏的"传感器"可以查看更多详细信息。

### 2. 控制设备

在"设备"页面，可以单独或批量控制大棚内的通风、灌溉、补光、加热等设备。

### 3. 查看 AI 建议

在"分析"页面，可以查看 AI 根据当前环境数据提供的优化建议和病害诊断。

### 4. 设置

在"设置"页面，可以配置服务器地址、通知、主题等选项。

## 开发计划

- [x] 项目结构与 Provider 状态管理
- [x] HTTP API 服务层 (`api_service.dart`)
- [x] 实时数据监控界面
- [x] 设备控制界面
- [x] AI 建议展示页面
- [x] 多主题切换（浅色/深色）
- [ ] 实时数据推送 (WebSocket)
- [ ] 图像上传和病害识别
- [ ] 历史数据查询
- [ ] 告警通知功能
- [ ] 多大棚管理

## 许可证

MIT License
