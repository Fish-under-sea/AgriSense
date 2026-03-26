import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/sensor_provider.dart';
import '../providers/device_provider.dart';
import '../providers/ai_provider.dart';
import 'sensors_page.dart';
import 'devices_page.dart';
import 'analytics_page.dart';
import 'settings_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const HomeContent(),
    const SensorsPage(),
    const DevicesPage(),
    const AnalyticsPage(),
    const SettingsPage(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refreshData();
    });
  }

  Future<void> _refreshData() async {
    final sensorProvider = context.read<SensorProvider>();
    final deviceProvider = context.read<DeviceProvider>();
    await sensorProvider.fetchSensors();
    await deviceProvider.fetchDevices();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: '首页',
          ),
          NavigationDestination(
            icon: Icon(Icons.analytics_outlined),
            selectedIcon: Icon(Icons.analytics),
            label: '传感器',
          ),
          NavigationDestination(
            icon: Icon(Icons.devices_outlined),
            selectedIcon: Icon(Icons.devices),
            label: '设备',
          ),
          NavigationDestination(
            icon: Icon(Icons.bar_chart_outlined),
            selectedIcon: Icon(Icons.bar_chart),
            label: '分析',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: '设置',
          ),
        ],
      ),
    );
  }
}

class HomeContent extends StatelessWidget {
  const HomeContent({super.key});

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        const SliverAppBar(
          floating: true,
          title: Text('AgriSense'),
          subtitle: Text('智能农业大棚监控系统'),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: null, // Will be handled by parent
            ),
          ],
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 环境概览卡片
                _buildEnvironmentCard(context),
                const SizedBox(height: 16),
                
                // 快速控制卡片
                _buildQuickControlCard(context),
                const SizedBox(height: 16),
                
                // AI 建议卡片
                _buildAIAdviceCard(context),
                const SizedBox(height: 16),
                
                // 设备状态概览
                _buildDeviceOverview(context),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEnvironmentCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.eco, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '环境概览',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const Spacer(),
                Consumer<SensorProvider>(
                  builder: (context, sensorProvider, _) {
                    return TextButton(
                      onPressed: () => sensorProvider.fetchSensors(),
                      child: const Text('刷新'),
                    );
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            Consumer<SensorProvider>(
              builder: (context, sensorProvider, _) {
                if (sensorProvider.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _buildSensorChip(
                      context,
                      '温度',
                      sensorProvider.temperature?.value.toStringAsFixed(1) ?? '--',
                      '°C',
                      Icons.thermometer,
                      sensorProvider.temperature?.status ?? 'normal',
                    ),
                    _buildSensorChip(
                      context,
                      '湿度',
                      sensorProvider.humidity?.value.toStringAsFixed(1) ?? '--',
                      '%',
                      Icons.water_drop,
                      sensorProvider.humidity?.status ?? 'normal',
                    ),
                    _buildSensorChip(
                      context,
                      '光照',
                      sensorProvider.lightIntensity?.value.toStringAsFixed(0) ?? '--',
                      'lux',
                      Icons.light_mode,
                      sensorProvider.lightIntensity?.status ?? 'normal',
                    ),
                    _buildSensorChip(
                      context,
                      'CO₂',
                      sensorProvider.co2Level?.value.toStringAsFixed(0) ?? '--',
                      'ppm',
                      Icons.air,
                      sensorProvider.co2Level?.status ?? 'normal',
                    ),
                    _buildSensorChip(
                      context,
                      '土壤湿度',
                      sensorProvider.soilMoisture?.value.toStringAsFixed(1) ?? '--',
                      '%',
                      Icons.grass,
                      sensorProvider.soilMoisture?.status ?? 'normal',
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

  Widget _buildSensorChip(
    BuildContext context,
    String label,
    String value,
    String unit,
    IconData icon,
    String status,
  ) {
    Color statusColor;
    switch (status.toLowerCase()) {
      case 'normal':
        statusColor = const Color(0xFF4ecca3);
        break;
      case 'warning':
        statusColor = const Color(0xFFFFA726);
        break;
      case 'critical':
        statusColor = const Color(0xFFEF5350);
        break;
      default:
        statusColor = const Color(0xFF757575);
    }

    return Chip(
      avatar: Icon(icon, color: statusColor, size: 20),
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: const TextStyle(fontSize: 12)),
          const SizedBox(width: 4),
          Text(
            '$value $unit',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: statusColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickControlCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.speed, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '快速控制',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Consumer<DeviceProvider>(
              builder: (context, deviceProvider, _) {
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _buildQuickControlButton(
                      context,
                      deviceProvider,
                      '通风',
                      Icons.air,
                      deviceProvider.ventilators,
                    ),
                    _buildQuickControlButton(
                      context,
                      deviceProvider,
                      '灌溉',
                      Icons.water_drop,
                      deviceProvider.irrigators,
                    ),
                    _buildQuickControlButton(
                      context,
                      deviceProvider,
                      '补光',
                      Icons.lightbulb,
                      deviceProvider.lights,
                    ),
                    _buildQuickControlButton(
                      context,
                      deviceProvider,
                      '加热',
                      Icons.local_fire_department,
                      deviceProvider.heaters,
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

  Widget _buildQuickControlButton(
    BuildContext context,
    DeviceProvider deviceProvider,
    String label,
    IconData icon,
    List<Device> devices,
  ) {
    if (devices.isEmpty) {
      return const SizedBox.shrink();
    }

    final allOn = devices.every((d) => d.state);
    
    return OutlinedButton.icon(
      onPressed: () async {
        final newState = !allOn;
        for (var device in devices) {
          await deviceProvider.toggleDevice(device.id, newState);
        }
      },
      icon: Icon(icon, color: allOn ? const Color(0xFF4ecca3) : null),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: allOn ? const Color(0xFF4ecca3) : null,
        side: BorderSide(
          color: allOn ? const Color(0xFF4ecca3) : Colors.grey,
        ),
      ),
    );
  }

  Widget _buildAIAdviceCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.lightbulb, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'AI 建议',
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
                    child: Text('暂无 AI 建议'),
                  );
                }

                return ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: aiProvider.adviceList.length > 3 
                      ? 3 
                      : aiProvider.adviceList.length,
                  separatorBuilder: (context, index) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final advice = aiProvider.adviceList[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            aiProvider.getCategoryIcon(advice.category),
                            color: aiProvider.getPriorityColor(advice.priority),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  advice.title,
                                  style: const TextStyle(fontWeight: FontWeight.w500),
                                ),
                                Text(
                                  advice.content,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey[600],
                                  ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
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

  Widget _buildDeviceOverview(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.devices, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '设备状态',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const Spacer(),
                TextButton(
                  onPressed: () {
                    // Navigate to devices page
                  },
                  child: const Text('查看全部'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Consumer<DeviceProvider>(
              builder: (context, deviceProvider, _) {
                final totalDevices = deviceProvider.devices.length;
                final activeDevices = deviceProvider.devices.where((d) => d.state).length;
                
                return Column(
                  children: [
                    LinearProgressIndicator(
                      value: totalDevices > 0 ? activeDevices / totalDevices : 0,
                      backgroundColor: Colors.grey[200],
                      valueColor: AlwaysStoppedAnimation(
                        Theme.of(context).colorScheme.primary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '$activeDevices / $totalDevices 设备运行中',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
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
}
