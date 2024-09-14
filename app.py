import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import threading
import time
import re
import os

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
        
        # 输出文件
        self.output_label = tk.Label(root, text="输出文件:")
        self.output_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        self.output_button = tk.Button(root, text="浏览", command=self.browse_output)
        self.output_button.grid(row=1, column=2, padx=5, pady=5)
        
        # 编码器选项
        self.encoder_label = tk.Label(root, text="选择编码器:")
        self.encoder_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.encoder_var = tk.StringVar(value='av1_nvenc')
        self.encoder_option = ttk.Combobox(root, textvariable=self.encoder_var, values=['av1_nvenc', 'h264_nvenc', 'hevc_nvenc'])
        self.encoder_option.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # CQ 值
        self.cq_label = tk.Label(root, text="CQ (恒定质量):")
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
        
        # 开始和取消按钮
        self.button_frame = tk.Frame(root)
        self.button_frame.grid(row=5, column=0, columnspan=3, pady=5)
        self.start_button = tk.Button(self.button_frame, text="开始", command=self.start_encoding)
        self.start_button.pack(side='left', padx=5)
        self.cancel_button = tk.Button(self.button_frame, text="取消", command=self.cancel_encoding, state='disabled')
        self.cancel_button.pack(side='left', padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=3, padx=5, pady=5)
        
        # 预计剩余时间
        self.time_label = tk.Label(root, text="预计剩余时间: N/A")
        self.time_label.grid(row=7, column=0, columnspan=3, padx=5, pady=5)
        
        # 状态标签
        self.status_label = tk.Label(root, text="状态: 空闲")
        self.status_label.grid(row=8, column=0, columnspan=3, padx=5, pady=5)
        
        # 初始化变量
        self.duration = 0
        self.is_running = False
        self.process = None
        self.start_time = None
        
    def browse_input(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
            # 获取输入文件的时长
            self.duration = self.get_duration(filename)
            print(f"Duration: {self.duration} seconds")
        
    def browse_output(self):
        # 根据选择的封装格式设置默认扩展名
        default_ext = '.' + self.container_var.get()
        filename = filedialog.asksaveasfilename(defaultextension=default_ext, filetypes=[(self.container_var.get().upper(), f"*{default_ext}")])
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)
    
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
    
    def start_encoding(self):
        if self.is_running:
            return
        input_file = self.input_entry.get()
        output_file = self.output_entry.get()
        cq_value = self.cq_entry.get()
        encoder = self.encoder_var.get()
        container = self.container_var.get()
        
        if not os.path.isfile(input_file):
            self.status_label.config(text="状态: 输入文件无效")
            return
        if not output_file:
            self.status_label.config(text="状态: 输出文件无效")
            return
        if not cq_value.isdigit():
            self.status_label.config(text="状态: CQ 值无效")
            return
        
        # 检查输出文件是否存在
        if os.path.exists(output_file):
            overwrite = messagebox.askyesno("文件已存在", f"文件 '{output_file}' 已存在。是否要覆盖？")
            if not overwrite:
                self.status_label.config(text="状态: 操作已取消")
                return
        
        self.is_running = True
        self.progress['value'] = 0
        self.status_label.config(text="状态: 正在编码...")
        self.cancel_button.config(state='normal')
        self.start_button.config(state='disabled')
        self.start_time = time.time()
        
        # 构建 ffmpeg 命令，添加 '-y' 参数
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
            '-c:a', 'copy',
            '-f', container,
            output_file
        ]
        
        # 在单独的线程中运行 ffmpeg
        threading.Thread(target=self.run_ffmpeg, args=(cmd,)).start()
    
    def cancel_encoding(self):
        if self.is_running and self.process:
            self.process.terminate()
            self.is_running = False
            self.status_label.config(text="状态: 已取消")
            self.progress['value'] = 0
            self.time_label.config(text="预计剩余时间: N/A")
            self.cancel_button.config(state='disabled')
            self.start_button.config(state='normal')
    
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
        self.is_running = False
        if self.process.returncode == 0:
            self.status_label.config(text="状态: 完成")
            self.progress['value'] = 100
            self.time_label.config(text="预计剩余时间: 00:00:00")
        else:
            if self.process.returncode < 0:
                self.status_label.config(text="状态: 已取消")
            else:
                self.status_label.config(text="状态: 失败")
            self.progress['value'] = 0
            self.time_label.config(text="预计剩余时间: N/A")
        self.cancel_button.config(state='disabled')
        self.start_button.config(state='normal')

if __name__ == '__main__':
    root = tk.Tk()
    app = FFmpegGUI(root)
    root.mainloop()
