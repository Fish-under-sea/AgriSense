import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class SensorData {
  final String type;
  final double value;
  final String unit;
  final String status;
  final DateTime timestamp;

  SensorData({
    required this.type,
    required this.value,
    required this.unit,
    required this.status,
    required this.timestamp,
  });

  factory SensorData.fromJson(Map<String, dynamic> json, String type) {
    return SensorData(
      type: type,
      value: json['value']?.toDouble() ?? 0.0,
      unit: json['unit'] ?? '',
      status: json['status'] ?? 'normal',
      timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
    );
  }
}

class SensorProvider extends ChangeNotifier {
  final ApiService _apiService;
  Map<String, SensorData> _sensors = {};
  bool _isLoading = false;
  String? _error;

  SensorProvider(this._apiService);

  Map<String, SensorData> get sensors => _sensors;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // 获取温度传感器数据
  SensorData? get temperature => _sensors['temperature'];
  
  // 获取湿度传感器数据
  SensorData? get humidity => _sensors['humidity'];
  
  // 获取光照强度数据
  SensorData? get lightIntensity => _sensors['light_intensity'];
  
  // 获取 CO2 浓度数据
  SensorData? get co2Level => _sensors['co2_level'];
  
  // 获取土壤湿度数据
  SensorData? get soilMoisture => _sensors['soil_moisture'];

  // 获取所有传感器数据
  Future<void> fetchSensors() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _apiService.getSensors();
      _sensors = {};

      if (data['temperature'] != null) {
        _sensors['temperature'] = SensorData.fromJson(data['temperature'], 'temperature');
      }
      if (data['humidity'] != null) {
        _sensors['humidity'] = SensorData.fromJson(data['humidity'], 'humidity');
      }
      if (data['light_intensity'] != null) {
        _sensors['light_intensity'] = SensorData.fromJson(data['light_intensity'], 'light_intensity');
      }
      if (data['co2_level'] != null) {
        _sensors['co2_level'] = SensorData.fromJson(data['co2_level'], 'co2_level');
      }
      if (data['soil_moisture'] != null) {
        _sensors['soil_moisture'] = SensorData.fromJson(data['soil_moisture'], 'soil_moisture');
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  // 获取传感器状态颜色
  Color getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'normal':
        return const Color(0xFF4ecca3);
      case 'warning':
        return const Color(0xFFFFA726);
      case 'critical':
        return const Color(0xFFEF5350);
      default:
        return const Color(0xFF757575);
    }
  }

  // 获取传感器图标
  IconData getSensorIcon(String type) {
    switch (type.toLowerCase()) {
      case 'temperature':
        return Icons.thermometer;
      case 'humidity':
        return Icons.water_drop;
      case 'light_intensity':
        return Icons.light_mode;
      case 'co2_level':
        return Icons.air;
      case 'soil_moisture':
        return Icons.grass;
      default:
        return Icons.sensor_occupy;
    }
  }
}
