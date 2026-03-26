import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/sensor_provider.dart';

class SensorsPage extends StatefulWidget {
  const SensorsPage({super.key});

  @override
  State<SensorsPage> createState() => _SensorsPageState();
}

class _SensorsPageState extends State<SensorsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SensorProvider>().fetchSensors();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('传感器数据'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<SensorProvider>().fetchSensors(),
          ),
        ],
      ),
      body: Consumer<SensorProvider>(
        builder: (context, sensorProvider, _) {
          if (sensorProvider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (sensorProvider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.grey),
                  const SizedBox(height: 16),
                  Text('加载失败：${sensorProvider.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => sensorProvider.fetchSensors(),
                    child: const Text('重试'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => sensorProvider.fetchSensors(),
            child: CustomScrollView(
              slivers: [
                SliverPadding(
                  padding: const EdgeInsets.all(16),
                  sliver: SliverGrid(
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 1.2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                    ),
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final sensorTypes = [
                          ('temperature', '温度', Icons.thermometer, '°C'),
                          ('humidity', '湿度', Icons.water_drop, '%'),
                          ('light_intensity', '光照', Icons.light_mode, 'lux'),
                          ('co2_level', 'CO₂', Icons.air, 'ppm'),
                          ('soil_moisture', '土壤湿度', Icons.grass, '%'),
                        ];
                        
                        if (index >= sensorTypes.length) {
                          return const SizedBox.shrink();
                        }

                        final (type, label, icon, unit) = sensorTypes[index];
                        final sensor = sensorProvider.sensors[type];

                        return _buildSensorCard(
                          context,
                          label,
                          sensor?.value.toStringAsFixed(1) ?? '--',
                          unit,
                          icon,
                          sensor?.status ?? 'normal',
                        );
                      },
                      childCount: 5,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSensorCard(
    BuildContext context,
    String label,
    String value,
    String unit,
    IconData icon,
    String status,
  ) {
    Color statusColor;
    IconData statusIcon;
    
    switch (status.toLowerCase()) {
      case 'normal':
        statusColor = const Color(0xFF4ecca3);
        statusIcon = Icons.check_circle;
        break;
      case 'warning':
        statusColor = const Color(0xFFFFA726);
        statusIcon = Icons.warning;
        break;
      case 'critical':
        statusColor = const Color(0xFFEF5350);
        statusIcon = Icons.error;
        break;
      default:
        statusColor = const Color(0xFF757575);
        statusIcon = Icons.help;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: statusColor),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: statusColor,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  unit,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(statusIcon, size: 14, color: statusColor),
                const SizedBox(width: 4),
                Text(
                  _getStatusText(status),
                  style: TextStyle(
                    fontSize: 10,
                    color: statusColor,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _getStatusText(String status) {
    switch (status.toLowerCase()) {
      case 'normal':
        return '正常';
      case 'warning':
        return '警告';
      case 'critical':
        return '严重';
      default:
        return '未知';
    }
  }
}
