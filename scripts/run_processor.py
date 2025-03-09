#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 处理功能启动脚本
"""

import os
import sys
import argparse
import importlib
import logging
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.append(root_dir)

from src.utils.config import ConfigManager
from src.utils.logger import setup_logging

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='处理游戏Wiki数据')
    
    parser.add_argument('--input-dir', type=str, help='输入数据目录')
    parser.add_argument('--output-dir', type=str, help='输出数据目录')
    parser.add_argument('--processor', type=str, help='要运行的处理器，多个处理器用逗号分隔，不指定则运行所有启用的处理器')
    parser.add_argument('--log-level', type=str, help='日志级别')
    parser.add_argument('--config-file', type=str, help='配置文件路径')
    parser.add_argument('--threads', type=int, help='并发处理线程数')
    
    return parser.parse_args()

def load_processor(processor_name, input_dir, output_dir, processor_config):
    """
    加载处理器
    
    Args:
        processor_name (str): 处理器名称
        input_dir (str): 输入数据目录
        output_dir (str): 输出数据目录
        processor_config (dict): 处理器配置
        
    Returns:
        BaseProcessor: 处理器实例，加载失败则返回None
    """
    try:
        # 构建处理器类名
        class_name = f"{processor_name.capitalize()}Processor"
        
        # 尝试导入处理器模块
        module_name = f"src.processor.{processor_name.lower()}"
        module = importlib.import_module(module_name)
        
        # 获取处理器类
        processor_class = getattr(module, class_name)
        
        # 创建处理器实例
        processor = processor_class(input_dir, output_dir, processor_config)
        
        return processor
    
    except (ImportError, AttributeError) as e:
        logging.error(f"加载处理器失败: {processor_name}, 错误: {str(e)}")
        return None

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 加载配置
    config_manager = ConfigManager(args.config_file)
    config = config_manager.config
    
    # 设置日志
    log_config = config.get('logging', {})
    setup_logging(
        log_level=args.log_level or log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/processor.log'),
        max_size=log_config.get('max_size', 10485760),
        backup_count=log_config.get('backup_count', 5)
    )
    
    # 获取处理配置
    processor_config = config.get('processor', {})
    
    # 命令行参数优先级高于配置文件
    input_dir = args.input_dir or processor_config.get('input_dir', 'data/input')
    output_dir = args.output_dir or processor_config.get('output_dir', 'data/output')
    
    # 确保目录存在
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取要运行的处理器列表
    if args.processor:
        # 从命令行参数获取
        processor_names = [p.strip() for p in args.processor.split(',')]
    else:
        # 从配置文件获取启用的处理器
        processors_config = processor_config.get('processors', {})
        processor_names = [
            name for name, config in processors_config.items()
            if config.get('enabled', True)
        ]
    
    if not processor_names:
        logging.warning("没有指定要运行的处理器，将退出")
        sys.exit(0)
    
    logging.info(f"将运行以下处理器: {', '.join(processor_names)}")
    
    # 获取并发线程数
    threads = args.threads or processor_config.get('threads', 1)
    
    # 加载处理器
    processors = []
    for name in processor_names:
        processor_specific_config = processor_config.get('processors', {}).get(name, {})
        processor = load_processor(name, input_dir, output_dir, processor_specific_config)
        if processor:
            processors.append(processor)
    
    if not processors:
        logging.error("没有成功加载任何处理器，将退出")
        sys.exit(1)
    
    # 运行处理器
    if threads > 1 and len(processors) > 1:
        # 并发运行
        logging.info(f"使用 {threads} 个线程并发运行处理器")
        with ThreadPoolExecutor(max_workers=min(threads, len(processors))) as executor:
            futures = {executor.submit(processor.run): processor.name for processor in processors}
            for future in futures:
                name = futures[future]
                try:
                    result = future.result()
                    if result:
                        logging.info(f"处理器运行成功: {name}")
                    else:
                        logging.warning(f"处理器运行完成，但可能存在问题: {name}")
                except Exception as e:
                    logging.error(f"处理器运行失败: {name}, 错误: {str(e)}")
    else:
        # 顺序运行
        logging.info("顺序运行处理器")
        for processor in processors:
            try:
                result = processor.run()
                if result:
                    logging.info(f"处理器运行成功: {processor.name}")
                else:
                    logging.warning(f"处理器运行完成，但可能存在问题: {processor.name}")
            except Exception as e:
                logging.error(f"处理器运行失败: {processor.name}, 错误: {str(e)}")
    
    logging.info(f"所有处理器运行完成，输出数据已保存到: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    main() 