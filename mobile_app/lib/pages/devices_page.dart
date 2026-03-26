import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/device_provider.dart';

class DevicesPage extends StatefulWidget {
  const DevicesPage({super.key});

  @override
  State<DevicesPage> createState() => _DevicesPageState();
}

class _DevicesPageState extends State<DevicesPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DeviceProvider>().fetchDevices();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('设备控制'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<DeviceProvider>().fetchDevices(),
          ),
        ],
      ),
      body: Consumer<DeviceProvider>(
        builder: (context, deviceProvider, _) {
          if (deviceProvider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (deviceProvider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.grey),
                  const SizedBox(height: 16),
                  Text('加载失败：${deviceProvider.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => deviceProvider.fetchDevices(),
                    child: const Text('重试'),
                  ),
                ],
              ),
            );
          }

          if (deviceProvider.devices.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.devices, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('暂无设备', style: TextStyle(fontSize: 16, color: Colors.grey)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => deviceProvider.fetchDevices(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // 批量控制按钮
                _buildBatchControlCard(context, deviceProvider),
                const SizedBox(height: 16),
                
                // 设备列表
                ..._buildDeviceSections(context, deviceProvider),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildBatchControlCard(BuildContext context, DeviceProvider provider) {
    final allOn = provider.devices.isNotEmpty && provider.devices.every((d) => d.state);
    final allOff = provider.devices.isNotEmpty && provider.devices.every((d) => !d.state);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.batch_prediction, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '批量控制',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: allOff ? null : () => _confirmBatchControl(context, provider, false),
                    icon: const Icon(Icons.power_off),
                    label: const Text('全部关闭'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.grey[600],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: allOn ? null : () => _confirmBatchControl(context, provider, true),
                    icon: const Icon(Icons.power),
                    label: const Text('全部开启'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF4ecca3),
                      side: const BorderSide(color: Color(0xFF4ecca3)),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildDeviceSections(BuildContext context, DeviceProvider provider) {
    final sections = [
      ('通风设备', provider.ventilators, Icons.air),
      ('灌溉设备', provider.irrigators, Icons.water_drop),
      ('补光设备', provider.lights, Icons.lightbulb),
      ('加热设备', provider.heaters, Icons.local_fire_department),
    ];

    return sections
        .where((section) => section.$2.isNotEmpty)
        .map((section) => _buildDeviceSection(
              context,
              provider,
              section.$1,
              section.$2,
              section.$3,
            ))
        .toList();
  }

  Widget _buildDeviceSection(
    BuildContext context,
    DeviceProvider provider,
    String title,
    List<Device> devices,
    IconData icon,
  ) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: Theme.of(context).colorScheme.primaryContainer,
          child: Icon(icon, color: Theme.of(context).colorScheme.primary),
        ),
        title: Text(title),
        subtitle: Text('${devices.length} 台设备'),
        children: devices.map((device) => _buildDeviceTile(context, provider, device)).toList(),
      ),
    );
  }

  Widget _buildDeviceTile(BuildContext context, DeviceProvider provider, Device device) {
    return ListTile(
      leading: Icon(
        provider.getDeviceTypeIcon(device.type),
        color: provider.getDeviceStatusColor(device),
      ),
      title: Text(device.name),
      subtitle: Text(
        provider.getDeviceStatusText(device),
        style: TextStyle(
          color: provider.getDeviceStatusColor(device),
          fontSize: 12,
        ),
      ),
      trailing: Switch(
        value: device.state,
        onChanged: device.status == 'offline'
            ? null
            : (value) => _confirmDeviceToggle(context, provider, device, value),
        activeColor: const Color(0xFF4ecca3),
      ),
    );
  }

  void _confirmDeviceToggle(
    BuildContext context,
    DeviceProvider provider,
    Device device,
    bool newState,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认操作'),
        content: Text('确定要${newState ? '开启' : '关闭'} ${device.name} 吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await provider.toggleDevice(device.id, newState);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('${device.name} 已${newState ? '开启' : '关闭'}'),
                    backgroundColor: const Color(0xFF4ecca3),
                  ),
                );
              }
            },
            child: const Text('确认'),
          ),
        ],
      ),
    );
  }

  void _confirmBatchControl(
    BuildContext context,
    DeviceProvider provider,
    bool newState,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认批量操作'),
        content: Text('确定要${newState ? '开启' : '关闭'}所有设备吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await provider.controlAllDevices(newState);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('所有设备已${newState ? '开启' : '关闭'}'),
                    backgroundColor: const Color(0xFF4ecca3),
                  ),
                );
              }
            },
            child: const Text('确认'),
          ),
        ],
      ),
    );
  }
}
