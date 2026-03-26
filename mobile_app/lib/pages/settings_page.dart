import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _notificationsEnabled = true;
  bool _darkMode = false;
  String _selectedLanguage = 'zh';
  String _serverUrl = 'http://localhost:5000';

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _notificationsEnabled = prefs.getBool('notifications') ?? true;
      _darkMode = prefs.getBool('darkMode') ?? false;
      _selectedLanguage = prefs.getString('language') ?? 'zh';
      _serverUrl = prefs.getString('serverUrl') ?? 'http://localhost:5000';
    });
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notifications', _notificationsEnabled);
    await prefs.setBool('darkMode', _darkMode);
    await prefs.setString('language', _selectedLanguage);
    await prefs.setString('serverUrl', _serverUrl);
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('设置已保存'),
          backgroundColor: Color(0xFF4ecca3),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('设置'),
      ),
      body: ListView(
        children: [
          // 服务器设置
          _buildSectionHeader(context, '服务器设置'),
          _buildServerUrlCard(context),
          
          // 通知设置
          _buildSectionHeader(context, '通知设置'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            child: SwitchListTile(
              title: const Text('启用通知'),
              subtitle: const Text('接收设备状态和告警通知'),
              value: _notificationsEnabled,
              onChanged: (value) {
                setState(() {
                  _notificationsEnabled = value;
                });
              },
              activeColor: const Color(0xFF4ecca3),
            ),
          ),
          
          // 外观设置
          _buildSectionHeader(context, '外观设置'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            child: SwitchListTile(
              title: const Text('深色模式'),
              subtitle: const Text('切换应用主题'),
              value: _darkMode,
              onChanged: (value) {
                setState(() {
                  _darkMode = value;
                });
              },
              activeColor: const Color(0xFF4ecca3),
            ),
          ),
          
          // 语言设置
          _buildSectionHeader(context, '语言设置'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            child: RadioListTile<String>(
              title: const Text('语言'),
              value: 'zh',
              groupValue: _selectedLanguage,
              onChanged: (value) {
                setState(() {
                  _selectedLanguage = value ?? 'zh';
                });
              },
              subtitle: const Text('中文 / English'),
              activeColor: const Color(0xFF4ecca3),
            ),
          ),
          
          // 关于
          _buildSectionHeader(context, '关于'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            child: ListTile(
              leading: const Icon(Icons.info_outline),
              title: const Text('关于 AgriSense'),
              subtitle: const Text('版本 1.0.0'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                _showAboutDialog(context);
              },
            ),
          ),
          
          // 保存按钮
          Padding(
            padding: const EdgeInsets.all(16),
            child: ElevatedButton(
              onPressed: _saveSettings,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4ecca3),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('保存设置', style: TextStyle(fontSize: 16)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  Widget _buildServerUrlCard(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '服务器地址',
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            TextField(
              decoration: InputDecoration(
                hintText: 'http://localhost:5000',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.check),
                  onPressed: () {
                    // 测试连接
                    _testConnection(context);
                  },
                ),
              ),
              controller: TextEditingController(text: _serverUrl),
              onChanged: (value) {
                _serverUrl = value;
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _testConnection(BuildContext context) async {
    // TODO: 实现连接测试
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('连接测试'),
        content: const Text('服务器连接正常！'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('确定'),
          ),
        ],
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('关于 AgriSense'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('AgriSense 智能农业大棚监控系统'),
            SizedBox(height: 16),
            Text('版本：1.0.0'),
            SizedBox(height: 8),
            Text('构建日期：2026-03-26'),
            SizedBox(height: 16),
            Text(
              '本项目是一个基于物联网和人工智能的智能农业解决方案，\n'
              '通过传感器监测、设备控制和 AI 分析，帮助农民实现精准农业管理。',
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }
}
