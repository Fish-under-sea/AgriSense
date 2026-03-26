import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiService {
  // 根据实际部署情况修改
  static const String baseUrl = 'http://localhost:5000';
  
  WebSocketChannel? _webSocket;
  
  // API 端点
  static const String sensorsEndpoint = '/api/sensors';
  static const String devicesEndpoint = '/api/devices';
  static const String diseaseEndpoint = '/api/vision/disease';
  static const String growthEndpoint = '/api/vision/growth';
  static const String aiAdviceEndpoint = '/api/ai/advice';
  static const String wsEndpoint = '/ws';
  
  // 获取传感器数据
  Future<Map<String, dynamic>> getSensors() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl$sensorsEndpoint'),
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load sensor data');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
  
  // 获取设备状态
  Future<Map<String, dynamic>> getDevices() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl$devicesEndpoint'),
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load device data');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
  
  // 控制设备
  Future<bool> controlDevice(String deviceId, bool state) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$devicesEndpoint'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'device_id': deviceId,
          'state': state,
        }),
      );
      return response.statusCode == 200;
    } catch (e) {
      throw Exception('Error controlling device: $e');
    }
  }
  
  // 获取 AI 建议
  Future<Map<String, dynamic>> getAIAdvice(Map<String, dynamic> data) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$aiAdviceEndpoint'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(data),
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get AI advice');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
  
  // 上传图像进行病害分析
  Future<Map<String, dynamic>> analyzeDisease(String imagePath) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl$diseaseEndpoint'),
      );
      request.files.add(await http.MultipartFile.fromPath('image', imagePath));
      final response = await request.send();
      if (response.statusCode == 200) {
        final responseData = await http.Response.fromStream(response);
        return json.decode(responseData.body);
      } else {
        throw Exception('Failed to analyze disease');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
  
  // 连接 WebSocket
  void connectWebSocket() {
    _webSocket = WebSocketChannel.connect(
      Uri.parse('ws://$baseUrl$wsEndpoint'),
    );
  }
  
  // 断开 WebSocket
  void disconnectWebSocket() {
    _webSocket?.sink.close();
    _webSocket = null;
  }
  
  // 获取 WebSocket 流
  Stream<dynamic>? get webSocketStream => _webSocket?.stream;
  
  // 发送 WebSocket 消息
  void sendWebSocketMessage(String message) {
    _webSocket?.sink.add(message);
  }
}
