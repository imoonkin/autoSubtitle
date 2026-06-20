#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ASR 测试脚本 - 加载本地音频文件进行识别
"""

import os
import sys
import time
import wave
import numpy as np
from pathlib import Path

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入你的 AsrProcessor
from backend.asr_processor import AsrProcessor

def load_audio_file(file_path: str, target_sample_rate: int = 16000) -> np.ndarray:
    """
    加载音频文件，支持 WAV 格式
    
    Args:
        file_path: 音频文件路径
        target_sample_rate: 目标采样率
    
    Returns:
        float32 格式的音频数据，范围 [-1.0, 1.0]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"音频文件不存在: {file_path}")
    
    # 使用 wave 模块读取 WAV
    try:
        with wave.open(file_path, 'rb') as wav:
            # 获取音频参数
            n_channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            n_frames = wav.getnframes()
            
            print(f"📋 音频参数:")
            print(f"  通道数: {n_channels}")
            print(f"  采样宽度: {sample_width} bytes")
            print(f"  采样率: {sample_rate} Hz")
            print(f"  帧数: {n_frames}")
            print(f"  时长: {n_frames / sample_rate:.2f} 秒")
            
            # 读取音频数据
            frames = wav.readframes(n_frames)
            
            # 转换为 numpy 数组
            if sample_width == 1:
                audio = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128
                audio = audio / 128.0
            elif sample_width == 2:
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 4:
                audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                raise ValueError(f"不支持的采样宽度: {sample_width}")
            
            # 如果是多声道，取平均
            if n_channels > 1:
                audio = audio.reshape(-1, n_channels).mean(axis=1)
            
            # 重采样到目标采样率
            if sample_rate != target_sample_rate:
                print(f"🔄 重采样: {sample_rate}Hz -> {target_sample_rate}Hz")
                audio = resample_audio(audio, sample_rate, target_sample_rate)
            
            return audio.astype(np.float32)
            
    except Exception as e:
        print(f"❌ 读取音频文件失败: {e}")
        return None


def resample_audio(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """
    简单的音频重采样（使用线性插值）
    """
    try:
        from scipy import signal
        # 使用 scipy 的 resample
        duration = len(audio) / src_rate
        new_length = int(duration * dst_rate)
        resampled = signal.resample(audio, new_length)
        return resampled.astype(np.float32)
    except ImportError:
        # 如果没有 scipy，使用简单的线性插值
        print("⚠️ scipy 未安装，使用简单线性插值")
        duration = len(audio) / src_rate
        new_length = int(duration * dst_rate)
        indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)
        return resampled.astype(np.float32)


def test_asr_file(file_path: str, asr_processor: AsrProcessor, show_details: bool = True):
    """
    测试单个音频文件
    
    Args:
        file_path: 音频文件路径
        asr_processor: ASR 处理器实例
        show_details: 是否显示详细信息
    """
    print("\n" + "=" * 70)
    print(f"📁 测试文件: {os.path.basename(file_path)}")
    print("=" * 70)
    
    # 1. 加载音频
    print("\n⏳ 加载音频文件...")
    audio_data = load_audio_file(file_path, target_sample_rate=16000)
    
    if audio_data is None or len(audio_data) == 0:
        print("❌ 音频数据为空")
        return
    
    print(f"✅ 加载成功，音频长度: {len(audio_data)} 采样点")
    print(f"  时长: {len(audio_data) / 16000:.2f} 秒")
    
    # 2. ASR 识别
    print("\n⏳ 执行 ASR 识别...")
    start_time = time.time()
    
    try:
        result = asr_processor.transcribe(audio_data)
        elapsed = time.time() - start_time
        
        print(f"✅ 识别完成 (耗时: {elapsed:.2f}s)")
        print(f"\n📝 识别结果:")
        print(f"  {result}")
        
        # 3. 统计信息
        if result:
            word_count = len(result.split())
            char_count = len(result)
            print(f"\n📊 统计:")
            print(f"  单词数: {word_count}")
            print(f"  字符数: {char_count}")
        
        return result
        
    except Exception as e:
        print(f"❌ 识别失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multiple_files(asr_processor: AsrProcessor, audio_dir: str, extensions: list = ['.wav']):
    """
    测试目录下的多个音频文件
    
    Args:
        asr_processor: ASR 处理器
        audio_dir: 音频文件目录
        extensions: 支持的文件扩展名
    """
    audio_dir = os.path.abspath(audio_dir)
    
    if not os.path.exists(audio_dir):
        print(f"❌ 目录不存在: {audio_dir}")
        return
    
    # 收集所有音频文件
    audio_files = []
    for ext in extensions:
        audio_files.extend(Path(audio_dir).glob(f"*{ext}"))
    
    if not audio_files:
        print(f"❌ 未找到音频文件 (扩展名: {extensions})")
        return
    
    print(f"\n📂 找到 {len(audio_files)} 个音频文件")
    print("=" * 70)
    
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}]")
        result = test_asr_file(str(audio_file), asr_processor, show_details=False)
        results.append({
            "file": str(audio_file),
            "result": result
        })
        print("-" * 70)
    
    # 打印总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    success_count = sum(1 for r in results if r["result"] and len(r["result"]) > 0)
    print(f"  总文件数: {len(results)}")
    print(f"  成功识别: {success_count}")
    print(f"  失败/空结果: {len(results) - success_count}")
    print("=" * 70)


def main():
    """主函数"""
    # 配置路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ASR 配置（与你的配置保持一致）
    asr_config = {
        "model_path": "../ModelsAI/sherpa sense voice/model.int8.onnx",
        "tokens_path": "../ModelsAI/sherpa sense voice/tokens.txt",
        "num_threads": 2,
    }
    
    # 1. 初始化 ASR 处理器
    print("=" * 70)
    print("🔧 初始化 ASR 处理器")
    print("=" * 70)
    
    try:
        asr_processor = AsrProcessor(current_dir, asr_config)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 2. 选择测试模式
    print("\n" + "=" * 70)
    print("选择测试模式:")
    print("  1. 测试单个音频文件")
    print("  2. 测试目录下的所有音频文件")
    print("  3. 交互模式 (输入文件路径)")
    print("=" * 70)
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        # 单个文件
        file_path = input("请输入音频文件路径: ").strip()
        if file_path:
            test_asr_file(file_path, asr_processor)
    
    elif choice == "2":
        # 目录
        dir_path = input("请输入音频文件目录路径: ").strip()
        if dir_path:
            test_multiple_files(asr_processor, dir_path)
    
    elif choice == "3":
        # 交互模式
        print("\n交互模式 (输入 'exit' 退出)")
        while True:
            file_path = input("\n请输入音频文件路径: ").strip()
            if file_path.lower() in ['exit', 'quit', 'q']:
                break
            if file_path:
                test_asr_file(file_path, asr_processor)
    
    else:
        print("无效选择")


if __name__ == "__main__":
    main()