import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import threading
import time
import re
import os
import platform
import urllib.request
import zipfile
import shutil

class FFmpegGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoSlimmer")
        
        # 输入文件
        self.input_label = tk.Label(root, text="输入文件:")
        self.input_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)
        self.input_button = tk.Button(root, text="浏览", command=self.browse_input)
        self.input_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 输出目录
        self.output_label = tk.Label(root, text="输出目录:")
        self.output_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        self.output_button = tk.Button(root, text="浏览", command=self.browse_output)
        self.output_button.grid(row=1, column=2, padx=5, pady=5)
        
        # 编码器选项
        self.encoder_label = tk.Label(root, text="选择视频编码器:")
        self.encoder_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.encoder_var = tk.StringVar(value='av1_nvenc')
        self.encoder_option = ttk.Combobox(root, textvariable=self.encoder_var, values=['av1_nvenc', 'h264_nvenc', 'hevc_nvenc'])
        self.encoder_option.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # CQ 值
        self.cq_label = tk.Label(root, text="视频 CQ (恒定质量):")
        self.cq_label.grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.cq_entry = tk.Entry(root, width=10)
        self.cq_entry.insert(0, "20")
        self.cq_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # 封装格式选项
        self.container_label = tk.Label(root, text="选择封装格式:")
        self.container_label.grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.container_var = tk.StringVar(value='mp4')
        self.container_option = ttk.Combobox(root, textvariable=self.container_var, values=['mp4', 'mov', 'mkv', 'flv'])
        self.container_option.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        
        # 保留字幕选项
        self.subtitle_var = tk.BooleanVar()
        self.subtitle_check = tk.Checkbutton(root, text="保留字幕", variable=self.subtitle_var)
        self.subtitle_check.grid(row=5, column=1, padx=5, pady=5, sticky='w')
        
        # 音频编码器选项
        self.audio_encoder_label = tk.Label(root, text="选择音频编码器:")
        self.audio_encoder_label.grid(row=6, column=0, padx=5, pady=5, sticky='e')
        self.audio_encoder_var = tk.StringVar(value='copy')
        self.audio_encoder_option = ttk.Combobox(root, textvariable=self.audio_encoder_var, values=['copy', 'aac', 'mp3', 'libopus'])
        self.audio_encoder_option.grid(row=6, column=1, padx=5, pady=5, sticky='w')
        
        # 音频比特率
        self.audio_bitrate_label = tk.Label(root, text="音频比特率 (kbps):")
        self.audio_bitrate_label.grid(row=7, column=0, padx=5, pady=5, sticky='e')
        self.audio_bitrate_entry = tk.Entry(root, width=10)
        self.audio_bitrate_entry.insert(0, "128")
        self.audio_bitrate_entry.grid(row=7, column=1, padx=5, pady=5, sticky='w')
        
        # 音频采样率
        self.audio_sample_rate_label = tk.Label(root, text="音频采样率 (Hz):")
        self.audio_sample_rate_label.grid(row=8, column=0, padx=5, pady=5, sticky='e')
        self.audio_sample_rate_entry = tk.Entry(root, width=10)
        self.audio_sample_rate_entry.insert(0, "44100")
        self.audio_sample_rate_entry.grid(row=8, column=1, padx=5, pady=5, sticky='w')
        
        # 音频声道数
        self.audio_channels_label = tk.Label(root, text="音频声道数:")
        self.audio_channels_label.grid(row=9, column=0, padx=5, pady=5, sticky='e')
        self.audio_channels_entry = tk.Entry(root, width=10)
        self.audio_channels_entry.insert(0, "2")
        self.audio_channels_entry.grid(row=9, column=1, padx=5, pady=5, sticky='w')
        
        # 开始和取消按钮
        self.button_frame = tk.Frame(root)
        self.button_frame.grid(row=10, column=0, columnspan=3, pady=5)
        self.start_button = tk.Button(self.button_frame, text="开始", command=self.start_encoding)
        self.start_button.pack(side='left', padx=5)
        self.cancel_button = tk.Button(self.button_frame, text="取消", command=self.cancel_encoding, state='disabled')
        self.cancel_button.pack(side='left', padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
        self.progress.grid(row=11, column=0, columnspan=3, padx=5, pady=5)
        
        # 预计剩余时间
        self.time_label = tk.Label(root, text="预计剩余时间: N/A")
        self.time_label.grid(row=12, column=0, columnspan=3, padx=5, pady=5)
        
        # 状态标签
        self.status_label = tk.Label(root, text="状态: 空闲")
        self.status_label.grid(row=13, column=0, columnspan=3, padx=5, pady=5)
        
        # 环境检查按钮
        self.check_env_button = tk.Button(root, text="环境检查", command=self.check_environment)
        self.check_env_button.grid(row=14, column=0, columnspan=3, padx=5, pady=5)
        
        # 初始化变量
        self.input_files = []
        self.duration = 0
        self.is_running = False
        self.process = None
        self.start_time = None
        self.current_file_index = 0
        self.total_files = 0
        
    def browse_input(self):
        filenames = filedialog.askopenfilenames()
        if filenames:
            self.input_files = list(filenames)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "; ".join(filenames))
            # 计算总文件数量
            self.total_files = len(self.input_files)
            
    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
            
    def start_encoding(self):
        if self.is_running:
            return
        input_files = self.input_files
        output_dir = self.output_entry.get()
        cq_value = self.cq_entry.get()
        encoder = self.encoder_var.get()
        container = self.container_var.get()
        keep_subtitles = self.subtitle_var.get()
        audio_encoder = self.audio_encoder_var.get()
        audio_bitrate = self.audio_bitrate_entry.get()
        audio_sample_rate = self.audio_sample_rate_entry.get()
        audio_channels = self.audio_channels_entry.get()
        
        if not input_files:
            self.status_label.config(text="状态: 输入文件无效")
            return
        if not output_dir or not os.path.isdir(output_dir):
            self.status_label.config(text="状态: 输出目录无效")
            return
        if not cq_value.isdigit():
            self.status_label.config(text="状态: 视频 CQ 值无效")
            return
        if audio_encoder != 'copy' and not audio_bitrate.isdigit():
            self.status_label.config(text="状态: 音频比特率无效")
            return
        if audio_encoder != 'copy' and not audio_sample_rate.isdigit():
            self.status_label.config(text="状态: 音频采样率无效")
            return
        if audio_encoder != 'copy' and not audio_channels.isdigit():
            self.status_label.config(text="状态: 音频声道数无效")
            return
        
        self.is_running = True
        self.cancel_button.config(state='normal')
        self.start_button.config(state='disabled')
        self.current_file_index = 0
        threading.Thread(target=self.encode_files, args=(
            input_files, output_dir, cq_value, encoder, container, keep_subtitles,
            audio_encoder, audio_bitrate, audio_sample_rate, audio_channels
        )).start()
        
    def encode_files(self, input_files, output_dir, cq_value, encoder, container, keep_subtitles,
                     audio_encoder, audio_bitrate, audio_sample_rate, audio_channels):
        total_files = len(input_files)
        for index, input_file in enumerate(input_files):
            if not self.is_running:
                break
            self.current_file_index = index + 1
            self.status_label.config(text=f"状态: 正在编码 {self.current_file_index}/{total_files}")
            self.progress['value'] = 0
            self.time_label.config(text="预计剩余时间: N/A")
            self.start_time = time.time()
            # 构建输出文件名
            filename = os.path.basename(input_file)
            name, _ = os.path.splitext(filename)
            output_file = os.path.join(output_dir, f"{name}.{container}")
            # 检查输出文件是否存在
            if os.path.exists(output_file):
                overwrite = messagebox.askyesno("文件已存在", f"文件 '{output_file}' 已存在。是否要覆盖？")
                if not overwrite:
                    self.status_label.config(text=f"状态: 已跳过 {self.current_file_index}/{total_files}")
                    continue
            # 获取文件时长
            self.duration = self.get_duration(input_file)
            # 构建 ffmpeg 命令
            cmd = [
                'ffmpeg',
                '-y',  # 自动覆盖已存在的文件
                '-i', input_file,
                '-c:v', encoder,
                '-preset', 'p7',
                '-rc', 'constqp',
                '-cq', cq_value,
                '-bf', '2',
                '-rc-lookahead', '32',
                '-spatial_aq', '1',
                '-temporal_aq', '1',
            ]
            # 处理音频编码器
            if audio_encoder == 'copy':
                cmd.extend(['-c:a', 'copy'])
            else:
                cmd.extend(['-c:a', audio_encoder])
                cmd.extend(['-b:a', f'{audio_bitrate}k'])
                cmd.extend(['-ar', audio_sample_rate])
                cmd.extend(['-ac', audio_channels])
            # 处理字幕选项
            if keep_subtitles:
                if container == 'mp4':
                    cmd.extend(['-c:s', 'mov_text'])
                else:
                    cmd.extend(['-c:s', 'copy'])
            else:
                cmd.extend(['-sn'])
            # 添加封装格式和输出文件
            cmd.extend(['-f', container, output_file])
            # 运行 ffmpeg
            self.run_ffmpeg(cmd)
        self.is_running = False
        self.cancel_button.config(state='disabled')
        self.start_button.config(state='normal')
        if self.is_running:
            self.status_label.config(text="状态: 完成")
        else:
            self.status_label.config(text="状态: 已取消")
            
    def run_ffmpeg(self, cmd):
        self.process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        duration = self.duration
        time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
        
        while True:
            if self.process.poll() is not None:
                break
            line = self.process.stderr.readline()
            if not line:
                continue
            print(line.strip())
            if 'time=' in line:
                match = time_pattern.search(line)
                if match:
                    hours = float(match.group(1))
                    minutes = float(match.group(2))
                    seconds = float(match.group(3))
                    elapsed = hours * 3600 + minutes * 60 + seconds
                    progress_percent = (elapsed / duration) * 100
                    self.progress['value'] = progress_percent
                    # 计算预计剩余时间
                    elapsed_time = time.time() - self.start_time
                    if progress_percent > 0:
                        total_estimated_time = elapsed_time / (progress_percent / 100)
                        remaining_time = total_estimated_time - elapsed_time
                        remaining_time_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
                        self.time_label.config(text=f"预计剩余时间: {remaining_time_str}")
                    self.root.update_idletasks()
        self.process.wait()
        self.progress['value'] = 100
        
    def cancel_encoding(self):
        if self.is_running:
            self.is_running = False
            if self.process:
                self.process.terminate()
            self.status_label.config(text="状态: 已取消")
            self.progress['value'] = 0
            self.time_label.config(text="预计剩余时间: N/A")
            self.cancel_button.config(state='disabled')
            self.start_button.config(state='normal')
        
    def get_duration(self, filename):
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                   'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0
        
    def check_environment(self):
        # 检查 ffmpeg 是否可用
        ffmpeg_available = False
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            ffmpeg_available = True
        except Exception:
            ffmpeg_available = False
        
        # 检查是否存在 NVIDIA 显卡
        nvidia_gpu_available = False
        try:
            result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
            if "NVIDIA-SMI" in result.stdout:
                nvidia_gpu_available = True
        except Exception:
            nvidia_gpu_available = False
        
        # 创建新的窗口显示结果
        env_window = tk.Toplevel(self.root)
        env_window.title("环境检查结果")
        
        # 使用 Unicode 字符显示对号和叉号
        check_mark = '\u2714'  # ✔
        cross_mark = '\u2718'  # ✘
        
        # ffmpeg 检查结果
        ffmpeg_label = tk.Label(env_window, text="ffmpeg 可用性：")
        ffmpeg_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ffmpeg_result = tk.Label(env_window, text=check_mark if ffmpeg_available else cross_mark, fg='green' if ffmpeg_available else 'red')
        ffmpeg_result.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # NVIDIA 显卡检查结果
        nvidia_label = tk.Label(env_window, text="NVIDIA 显卡：")
        nvidia_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        nvidia_result = tk.Label(env_window, text=check_mark if nvidia_gpu_available else cross_mark, fg='green' if nvidia_gpu_available else 'red')
        nvidia_result.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # 提示信息
        info_text = ""
        if not ffmpeg_available:
            info_text += "未找到 ffmpeg。"
            # 询问用户是否自动下载安装 ffmpeg
            install_ffmpeg = messagebox.askyesno("ffmpeg 未安装", "未检测到 ffmpeg。是否自动下载安装？")
            if install_ffmpeg:
                threading.Thread(target=self.install_ffmpeg).start()
            else:
                info_text += "请安装 ffmpeg 并将其添加到系统环境变量。\n"
        if not nvidia_gpu_available:
            info_text += "未检测到 NVIDIA 显卡。请确保已安装 NVIDIA 显卡和正确的驱动程序。\n"
        if info_text == "":
            info_text = "您的环境已正确配置。"
        info_label = tk.Label(env_window, text=info_text)
        info_label.grid(row=2, column=0, columnspan=2, padx=5, pady=10)
        
        # 关闭按钮
        close_button = tk.Button(env_window, text="关闭", command=env_window.destroy)
        close_button.grid(row=3, column=0, columnspan=2, pady=5)
    
    def install_ffmpeg(self):
        # 根据操作系统选择对应的 ffmpeg 下载链接
        system = platform.system()
        if system == 'Windows':
            ffmpeg_url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
            zip_name = 'ffmpeg.zip'
            install_path = os.path.join(os.getcwd(), 'ffmpeg')
            bin_path = os.path.join(install_path, 'bin')
        else:
            messagebox.showinfo("暂不支持", "自动安装 ffmpeg 的功能目前仅支持 Windows 系统。")
            return
        
        try:
            # 下载 ffmpeg
            self.status_label.config(text="状态: 正在下载 ffmpeg...")
            urllib.request.urlretrieve(ffmpeg_url, zip_name)
            # 解压缩
            self.status_label.config(text="状态: 正在安装 ffmpeg...")
            with zipfile.ZipFile(zip_name, 'r') as zip_ref:
                zip_ref.extractall(install_path)
            # 删除压缩文件
            os.remove(zip_name)
            # 更新系统环境变量
            os.environ['PATH'] += os.pathsep + bin_path
            messagebox.showinfo("安装完成", "ffmpeg 已成功安装。请重新启动程序以确保更改生效。")
            self.status_label.config(text="状态: ffmpeg 安装完成")
        except Exception as e:
            messagebox.showerror("安装失败", f"ffmpeg 安装失败：{e}")
            self.status_label.config(text="状态: ffmpeg 安装失败")
        
if __name__ == '__main__':
    root = tk.Tk()
    app = FFmpegGUI(root)
    root.mainloop()
