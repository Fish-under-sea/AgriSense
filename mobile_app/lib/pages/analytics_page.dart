import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/ai_provider.dart';
import '../providers/sensor_provider.dart';

class AnalyticsPage extends StatefulWidget {
  const AnalyticsPage({super.key});

  @override
  State<AnalyticsPage> createState() => _AnalyticsPageState();
}

class _AnalyticsPageState extends State<AnalyticsPage> {
  int _selectedPeriod = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('数据分析'),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await context.read<SensorProvider>().fetchSensors();
        },
        child: CustomScrollView(
          slivers: [
            // 时间段选择器
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '时间范围',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    _buildPeriodSelector(context),
                  ],
                ),
              ),
            ),
            
            // AI 建议列表
            SliverToBoxAdapter(
              child: _buildAIAdviceSection(context),
            ),
            
            // 病害分析
            SliverToBoxAdapter(
              child: _buildDiseaseAnalysisSection(context),
            ),
            
            // 传感器历史趋势
            SliverToBoxAdapter(
              child: _buildSensorTrends(context),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPeriodSelector(BuildContext context) {
    final periods = ['1 小时', '24 小时', '7 天', '30 天'];
    
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(periods.length, (index) {
          final isSelected = _selectedPeriod == index;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(periods[index]),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  _selectedPeriod = index;
                });
              },
              selectedColor: Theme.of(context).colorScheme.primaryContainer,
              labelStyle: TextStyle(
                color: isSelected
                    ? Theme.of(context).colorScheme.primary
                    : Colors.grey[600],
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildAIAdviceSection(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.auto_awesome, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'AI 智能建议',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Consumer<AIProvider>(
              builder: (context, aiProvider, _) {
                if (aiProvider.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (aiProvider.adviceList.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 8.0),
                    child: Text('暂无 AI 建议，系统运行正常'),
                  );
                }

                return ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: aiProvider.adviceList.length,
                  separatorBuilder: (context, index) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final advice = aiProvider.adviceList[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: aiProvider.getPriorityColor(advice.priority).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(
                              aiProvider.getCategoryIcon(advice.category),
                              color: aiProvider.getPriorityColor(advice.priority),
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      advice.title,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        fontSize: 14,
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 6,
                                        vertical: 2,
                                      ),
                                      decoration: BoxDecoration(
                                        color: aiProvider.getPriorityColor(advice.priority),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        '优先级：${aiProvider.getPriorityText(advice.priority)}',
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 10,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  advice.content,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDiseaseAnalysisSection(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.medical_services, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '病害分析',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Consumer<AIProvider>(
              builder: (context, aiProvider, _) {
                if (aiProvider.lastDiseaseAnalysis != null) {
                  final analysis = aiProvider.lastDiseaseAnalysis!;
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            '病害：${analysis.diseaseName}',
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: aiProvider.getConfidenceColor(analysis.confidence),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              '置信度 ${(analysis.confidence * 100).toInt()}%',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (analysis.description.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          analysis.description,
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                      if (analysis.treatments.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        const Text(
                          '建议措施:',
                          style: TextStyle(fontWeight: FontWeight.w500, fontSize: 12),
                        ),
                        ...analysis.treatments.map((treatment) => Padding(
                          padding: const EdgeInsets.only(left: 16, top: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('• ', style: TextStyle(color: Colors.grey[600])),
                              Expanded(
                                child: Text(
                                  treatment,
                                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                ),
                              ),
                            ],
                          ),
                        )),
                      ],
                    ],
                  );
                }

                return Column(
                  children: [
                    const Text('暂无病害分析记录'),
                    const SizedBox(height: 12),
                    ElevatedButton.icon(
                      onPressed: () {
                        // TODO: 打开相机或图片选择器
                      },
                      icon: const Icon(Icons.camera_alt),
                      label: const Text('上传叶片图片分析'),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSensorTrends(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.trending_up, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '传感器趋势',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Consumer<SensorProvider>(
              builder: (context, sensorProvider, _) {
                // 模拟历史数据用于展示
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildMiniChart(
                      context,
                      '温度趋势 (°C)',
                      [22, 23, 24, 23, 25, 24, 26],
                      const Color(0xFF4ecca3),
                    ),
                    const SizedBox(height: 16),
                    _buildMiniChart(
                      context,
                      '湿度趋势 (%)',
                      [60, 62, 58, 65, 63, 61, 59],
                      const Color(0xFF2196F3),
                    ),
                    const SizedBox(height: 16),
                    _buildMiniChart(
                      context,
                      '光照强度 (lux)',
                      [5000, 8000, 12000, 15000, 10000, 6000, 3000],
                      const Color(0xFFFFC107),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMiniChart(BuildContext context, String label, List<double> data, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 60,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: const FlTitlesData(show: false),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: data.asMap().entries.map((e) {
                    return FlSpot(e.key.toDouble(), e.value);
                  }).toList(),
                  isCurved: true,
                  color: color,
                  barWidth: 2,
                  dotData: const FlDotData(show: false),
                  belowBarData: BarAreaData(
                    show: true,
                    color: color.withOpacity(0.1),
                  ),
                ),
              ],
              minX: 0,
              maxX: (data.length - 1).toDouble(),
              minY: data.reduce((a, b) => a < b ? a : b) * 0.8,
              maxY: data.reduce((a, b) => a > b ? a : b) * 1.2,
            ),
          ),
        ),
      ],
    );
  }
}
