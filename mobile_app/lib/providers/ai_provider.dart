import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class AIAdvice {
  final String title;
  final String content;
  final String category;
  final int priority;
  final DateTime createdAt;

  AIAdvice({
    required this.title,
    required this.content,
    required this.category,
    required this.priority,
    required this.createdAt,
  });

  factory AIAdvice.fromJson(Map<String, dynamic> json) {
    return AIAdvice(
      title: json['title'] ?? '',
      content: json['content'] ?? json['advice'] ?? '',
      category: json['category'] ?? 'general',
      priority: json['priority'] ?? 0,
      createdAt: DateTime.tryParse(json['timestamp'] ?? json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}

class DiseaseAnalysis {
  final String diseaseName;
  final double confidence;
  final String description;
  final List<String> treatments;
  final DateTime analyzedAt;

  DiseaseAnalysis({
    required this.diseaseName,
    required this.confidence,
    required this.description,
    required this.treatments,
    required this.analyzedAt,
  });

  factory DiseaseAnalysis.fromJson(Map<String, dynamic> json) {
    return DiseaseAnalysis(
      diseaseName: json['disease'] ?? json['disease_name'] ?? '未知病害',
      confidence: (json['confidence'] ?? 0.0).toDouble(),
      description: json['description'] ?? '',
      treatments: (json['treatments'] as List?)?.cast<String>() ?? [],
      analyzedAt: DateTime.now(),
    );
  }
}

class AIProvider extends ChangeNotifier {
  final ApiService _apiService;
  List<AIAdvice> _adviceList = [];
  DiseaseAnalysis? _lastDiseaseAnalysis;
  bool _isLoading = false;
  String? _error;

  AIProvider(this._apiService);

  List<AIAdvice> get adviceList => _adviceList;
  DiseaseAnalysis? get lastDiseaseAnalysis => _lastDiseaseAnalysis;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // 获取 AI 建议
  Future<void> fetchAIAdvice(Map<String, dynamic> sensorData) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _apiService.getAIAdvice(sensorData);
      _adviceList = [];

      if (data['advice'] != null) {
        if (data['advice'] is List) {
          for (var adviceData in data['advice']) {
            _adviceList.add(AIAdvice.fromJson(adviceData));
          }
        } else {
          _adviceList.add(AIAdvice.fromJson(data));
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

  // 分析病害
  Future<void> analyzeDisease(String imagePath) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _apiService.analyzeDisease(imagePath);
      _lastDiseaseAnalysis = DiseaseAnalysis.fromJson(data);
      
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  // 获取优先级颜色
  Color getPriorityColor(int priority) {
    if (priority >= 3) {
      return const Color(0xFFEF5350); // 高优先级 - 红色
    } else if (priority >= 2) {
      return const Color(0xFFFFA726); // 中优先级 - 橙色
    } else {
      return const Color(0xFF4ecca3); // 低优先级 - 绿色
    }
  }

  // 获取优先级文本
  String getPriorityText(int priority) {
    if (priority >= 3) {
      return '高';
    } else if (priority >= 2) {
      return '中';
    } else {
      return '低';
    }
  }

  // 获取分类图标
  IconData getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'temperature':
        return Icons.thermometer;
      case 'humidity':
        return Icons.water_drop;
      case 'irrigation':
        return Icons.water_drop_outlined;
      case 'disease':
        return Icons.warning;
      case 'growth':
        return Icons.sprout;
      default:
        return Icons.lightbulb;
    }
  }

  // 获取病害置信度颜色
  Color getConfidenceColor(double confidence) {
    if (confidence >= 0.8) {
      return const Color(0xFF4ecca3);
    } else if (confidence >= 0.6) {
      return const Color(0xFFFFA726);
    } else {
      return const Color(0xFFEF5350);
    }
  }
}
