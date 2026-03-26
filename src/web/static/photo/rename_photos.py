#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片批量重命名工具 - 专门用于 AgriSense 项目
目标目录: D:\Fish-code\AgriSense\src\web\static\photo
将图片重命名为 dataset_1, dataset_2, dataset_3 ... 格式
"""

import os
import sys
import re
from pathlib import Path

# 目标目录
TARGET_DIR = r"D:\Fish-code\AgriSense\src\web\static\photo"

# 支持的图片格式
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}

def check_directory():
    """检查目标目录是否存在"""
    if not os.path.exists(TARGET_DIR):
        print(f"❌ 目录不存在: {TARGET_DIR}")
        print("请确认路径是否正确")
        return False
    
    print(f"✅ 目标目录: {TARGET_DIR}")
    return True

def get_image_files(directory):
    """获取目录下所有图片文件，按修改时间排序"""
    image_files = []
    
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        # 只处理文件，跳过目录
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                image_files.append(file)
    
    if not image_files:
        return []
    
    # 按修改时间排序，保持原始顺序
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)))
    
    return image_files

def get_existing_dataset_numbers(directory):
    """获取已存在的 dataset_N 格式文件的编号"""
    pattern = re.compile(r'^dataset_(\d+)\.\w+$')
    existing_numbers = []
    
    for file in os.listdir(directory):
        match = pattern.match(file)
        if match:
            existing_numbers.append(int(match.group(1)))
    
    return sorted(existing_numbers)

def preview_rename(directory, start_num=1):
    """预览重命名结果"""
    image_files = get_image_files(directory)
    
    if not image_files:
        print("❌ 未找到图片文件")
        return None
    
    print(f"\n📋 重命名预览 (共 {len(image_files)} 个文件):")
    print("=" * 70)
    
    renamed_list = []
    conflicts = []
    
    for idx, filename in enumerate(image_files):
        new_name = f"dataset_{start_num + idx}{os.path.splitext(filename)[1].lower()}"
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_name)
        
        # 检查冲突
        if os.path.exists(new_path) and old_path != new_path:
            conflicts.append((filename, new_name))
        
        renamed_list.append((filename, new_name))
        
        # 显示预览
        status = "⚠️  冲突" if os.path.exists(new_path) and old_path != new_path else ""
        print(f"  {idx + 1:3d}. {filename:35} → {new_name:25} {status}")
    
    if conflicts:
        print("\n" + "=" * 70)
        print("⚠️  检测到文件名冲突！")
        for old, new in conflicts:
            print(f"  {old} → {new}")
        print("请先处理冲突文件或调整起始编号")
        return None
    
    return renamed_list

def execute_rename(directory, renamed_list):
    """执行重命名"""
    if not renamed_list:
        return False
    
    print("\n" + "=" * 70)
    response = input(f"\n确认重命名以上 {len(renamed_list)} 个文件？(y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ 操作已取消")
        return False
    
    print("\n🔄 正在重命名...")
    success_count = 0
    error_count = 0
    
    for old_name, new_name in renamed_list:
        try:
            old_path = os.path.join(TARGET_DIR, old_name)
            new_path = os.path.join(TARGET_DIR, new_name)
            os.rename(old_path, new_path)
            print(f"  ✅ {old_name} → {new_name}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ 失败: {old_name} → {new_name}, 错误: {e}")
            error_count += 1
    
    print("\n" + "=" * 70)
    print(f"📊 重命名完成！")
    print(f"  成功: {success_count} 个文件")
    print(f"  失败: {error_count} 个文件")
    
    if success_count > 0:
        first_num = int(re.search(r'\d+', renamed_list[0][1]).group())
        last_num = first_num + success_count - 1
        print(f"✨ 文件已重命名为 dataset_{first_num} ~ dataset_{last_num}")
    
    return error_count == 0

def interactive_mode():
    """交互模式"""
    print("=" * 70)
    print("📸 AgriSense 照片批量重命名工具")
    print("=" * 70)
    
    # 检查目录
    if not check_directory():
        return
    
    # 获取现有图片
    image_files = get_image_files(TARGET_DIR)
    
    if not image_files:
        print(f"\n❌ 目录中没有找到支持的图片文件！")
        print(f"支持的格式: {', '.join(SUPPORTED_EXTENSIONS)}")
        return
    
    print(f"\n📷 找到 {len(image_files)} 个图片文件")
    
    # 显示前10个文件
    print("\n文件列表:")
    for i, img in enumerate(image_files[:10]):
        size = os.path.getsize(os.path.join(TARGET_DIR, img)) / 1024
        print(f"  {i+1:3d}. {img:35} ({size:.1f} KB)")
    if len(image_files) > 10:
        print(f"  ... 还有 {len(image_files) - 10} 个文件")
    
    # 检查已存在的 dataset 文件
    existing_numbers = get_existing_dataset_numbers(TARGET_DIR)
    default_start = 1
    
    if existing_numbers:
        max_existing = max(existing_numbers)
        print(f"\n⚠️  检测到已存在 {len(existing_numbers)} 个 dataset 格式文件")
        print(f"   最大编号: dataset_{max_existing}")
        print(f"   现有编号: {existing_numbers[:10]}{'...' if len(existing_numbers) > 10 else ''}")
        
        response = input(f"\n是否从 {max_existing + 1} 开始编号？(y/n，默认 y): ").strip().lower()
        if response != 'n':
            default_start = max_existing + 1
            print(f"✅ 将从编号 {default_start} 开始")
        else:
            start_input = input(f"请输入起始编号 (默认 1): ").strip()
            default_start = int(start_input) if start_input.isdigit() else 1
    else:
        start_input = input(f"\n请输入起始编号 (默认 1): ").strip()
        default_start = int(start_input) if start_input.isdigit() else 1
    
    # 预览
    renamed_list = preview_rename(TARGET_DIR, default_start)
    
    if renamed_list:
        # 执行重命名
        execute_rename(TARGET_DIR, renamed_list)

def quick_mode(start_num=1, dry_run=False):
    """快速模式 - 直接使用默认设置"""
    print("=" * 70)
    print("📸 AgriSense 照片批量重命名工具 - 快速模式")
    print("=" * 70)
    
    if not check_directory():
        return
    
    image_files = get_image_files(TARGET_DIR)
    
    if not image_files:
        print(f"❌ 未找到图片文件")
        return
    
    print(f"📷 找到 {len(image_files)} 个图片文件")
    
    # 检查已存在的 dataset 文件
    existing_numbers = get_existing_dataset_numbers(TARGET_DIR)
    if existing_numbers:
        max_existing = max(existing_numbers)
        if start_num <= max_existing:
            print(f"⚠️  起始编号 {start_num} 小于已存在的最大编号 {max_existing}")
            print(f"   建议使用 {max_existing + 1} 作为起始编号")
            response = input(f"是否自动调整为 {max_existing + 1}？(y/n): ").strip().lower()
            if response == 'y':
                start_num = max_existing + 1
    
    renamed_list = preview_rename(TARGET_DIR, start_num)
    
    if renamed_list:
        if dry_run:
            print("\n🔍 预览模式完成，未执行实际重命名")
        else:
            execute_rename(TARGET_DIR, renamed_list)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量重命名 AgriSense 项目图片文件')
    parser.add_argument('-s', '--start', type=int, default=1, help='起始编号 (默认: 1)')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际重命名')
    parser.add_argument('-q', '--quick', action='store_true', help='快速模式，跳过交互')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_mode(args.start, args.dry_run)
    else:
        interactive_mode()

if __name__ == "__main__":
    # 如果没有命令行参数，运行交互模式
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        main()