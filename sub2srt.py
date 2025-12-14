import os
import re
import argparse
from pathlib import Path

def format_time_str(time_str: str) -> str:
    """
    将Sub格式的时间字符串（如00:00:27 或 00:00:11.5000000）转换为SRT标准时间格式（00:00:27,000）
    :param time_str: 原始时间字符串
    :return: SRT格式时间字符串
    """
    # 补全秒的小数部分（如 00:00:27 → 00:00:27.0000000）
    if "." not in time_str:
        time_str += ".0000000"
    
    # 拆分时:分:秒.微秒
    hh, mm, ss_ms = time_str.split(":")
    ss, ms = ss_ms.split(".")
    
    # 取前3位作为毫秒（SRT标准只保留3位毫秒）
    ms_3 = ms[:3].ljust(3, "0")  # 不足3位补0
    
    # 拼接为SRT格式：时:分:秒,毫秒
    return f"{hh}:{mm}:{ss},{ms_3}"

def convert_single_sub_to_srt(sub_file_path: str, output_dir: str = None) -> None:
    """
    转换单个Sub文件为SRT格式
    :param sub_file_path: Sub文件路径
    :param output_dir: 输出目录（默认和Sub文件同目录）
    """
    # 处理输出目录
    sub_path = Path(sub_file_path)
    if not output_dir:
        output_dir = sub_path.parent
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    # 生成输出文件名（替换后缀为.srt）
    srt_file_path = Path(output_dir) / f"{sub_path.stem}.srt"

    try:
        # 读取Sub文件（优先UTF-8，失败则尝试GBK）
        try:
            with open(sub_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(sub_path, "r", encoding="gbk") as f:
                content = f.read()

        # 按空行分割字幕块（处理多个连续空行的情况）
        subtitle_blocks = [block.strip() for block in re.split(r"\n\s*\n", content) if block.strip()]
        
        srt_content = []
        for idx, block in enumerate(subtitle_blocks, 1):
            # 拆分时间行和内容行
            lines = block.split("\n", 1)
            if len(lines) < 2:
                print(f"警告：第{idx}个字幕块格式异常，跳过 → {block[:50]}...")
                continue
            
            time_line, text_lines = lines
            # 拆分开始/结束时间
            start_time_str, end_time_str = [t.strip() for t in time_line.split(",")]
            
            # 转换为SRT时间格式
            start_srt = format_time_str(start_time_str)
            end_srt = format_time_str(end_time_str)
            
            # 拼接SRT块
            srt_block = (
                f"{idx}\n"
                f"{start_srt} --> {end_srt}\n"
                f"{text_lines.strip()}\n"
            )
            srt_content.append(srt_block)

        # 写入SRT文件
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))
        
        print(f"✅ 转换成功：{sub_file_path} → {srt_file_path}")

    except Exception as e:
        print(f"❌ 转换失败 {sub_file_path}：{str(e)}")

def batch_convert_sub_to_srt(input_path: str, output_dir: str = None) -> None:
    """
    批量转换Sub文件（支持单个文件/文件夹）
    :param input_path: 输入文件/文件夹路径
    :param output_dir: 输出目录
    """
    input_path = Path(input_path)
    
    if input_path.is_file() and input_path.suffix.lower() == ".sub":
        # 单个文件转换
        convert_single_sub_to_srt(str(input_path), output_dir)
    
    elif input_path.is_dir():
        # 遍历文件夹下所有.sub文件
        sub_files = list(input_path.glob("**/*.sub"))
        if not sub_files:
            print(f"⚠️ 未找到任何.sub文件：{input_path}")
            return
        
        print(f"📁 找到 {len(sub_files)} 个Sub文件，开始批量转换...")
        for sub_file in sub_files:
            convert_single_sub_to_srt(str(sub_file), output_dir)
    
    else:
        print(f"❌ 输入路径无效：{input_path}")

if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="Sub字幕文件批量转换为SRT格式")
    parser.add_argument("input", help="输入文件/文件夹路径（支持单个.sub或文件夹）")
    parser.add_argument("-o", "--output", help="输出目录（可选，默认和输入文件同目录）")
    args = parser.parse_args()

    # 执行转换
    batch_convert_sub_to_srt(args.input, args.output)
