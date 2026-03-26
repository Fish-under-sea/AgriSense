import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class Device {
  final String id;
  final String name;
  final String type;
  final bool state;
  final String status;
  final DateTime lastUpdated;

  Device({
    required this.id,
    required this.name,
    required this.type,
    required this.state,
    required this.status,
    required this.lastUpdated,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['device_id'] ?? json['id'] ?? '',
      name: json['name'] ?? '',
      type: json['type'] ?? '',
      state: json['state'] ?? json['is_on'] ?? false,
      status: json['status'] ?? 'online',
      lastUpdated: DateTime.tryParse(json['last_updated'] ?? '') ?? DateTime.now(),
    );
  }

  Device copyWith({
    String? id,
    String? name,
    String? type,
    bool? state,
    String? status,
    DateTime? lastUpdated,
  }) {
    return Device(
      id: id ?? this.id,
      name: name ?? this.name,
      type: type ?? this.type,
      state: state ?? this.state,
      status: status ?? this.status,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }
}

class DeviceProvider extends ChangeNotifier {
  final ApiService _apiService;
  List<Device> _devices = [];
  bool _isLoading = false;
  String? _error;

  DeviceProvider(this._apiService);

  List<Device> get devices => _devices;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // 获取通风设备
  List<Device> get ventilators => _devices.where((d) => d.type == 'ventilator').toList();
  
  // 获取灌溉设备
  List<Device> get irrigators => _devices.where((d) => d.type == 'irrigator').toList();
  
  // 获取补光灯
  List<Device> get lights => _devices.where((d) => d.type == 'light').toList();
  
  // 获取加热设备
  List<Device> get heaters => _devices.where((d) => d.type == 'heater').toList();

  // 获取所有设备
  Future<void> fetchDevices() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _apiService.getDevices();
      _devices = [];

      if (data['devices'] != null) {
        for (var deviceData in data['devices']) {
          _devices.add(Device.fromJson(deviceData));
        }
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  // 控制设备开关
  Future<bool> toggleDevice(String deviceId, bool newState) async {
    try {
      final success = await _apiService.controlDevice(deviceId, newState);
      if (success) {
        // 更新本地设备状态
        final index = _devices.indexWhere((d) => d.id == deviceId);
        if (index != -1) {
          _devices[index] = _devices[index].copyWith(
            state: newState,
            lastUpdated: DateTime.now(),
          );
          notifyListeners();
        }
      }
      return success;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  // 批量控制设备
  Future<void> controlAllDevices(bool state) async {
    for (var device in _devices) {
      await toggleDevice(device.id, state);
    }
  }

  // 获取设备类型图标
  IconData getDeviceTypeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'ventilator':
        return Icons.air;
      case 'irrigator':
        return Icons.water_drop;
      case 'light':
        return Icons.lightbulb;
      case 'heater':
        return Icons.local_fire_department;
      default:
        return Icons.devices;
    }
  }

  // 获取设备状态文本
  String getDeviceStatusText(Device device) {
    if (device.status == 'offline') {
      return '离线';
    }
    return device.state ? '开启' : '关闭';
  }

  // 获取设备状态颜色
  Color getDeviceStatusColor(Device device) {
    if (device.status == 'offline') {
      return const Color(0xFF757575);
    }
    return device.state ? const Color(0xFF4ecca3) : const Color(0xFF9E9E9E);
  }
}
