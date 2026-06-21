"""llama.cpp 后台服务器守护进程管理器。"""
import os
import subprocess
import time
import requests
from urllib.parse import urlparse

class LlamaServerManager:
    def __init__(self, current_dir: str, trans_config: dict, server_name: str):
        self.process = None
        self.bootstrap = trans_config.get("bootstrap_server", False)
        self.server_url = trans_config.get("server_url")
        self.server_name = server_name

        parsed = urlparse(self.server_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.port = parsed.port or 80
        self.abs_server_bin = os.path.abspath(os.path.join(current_dir, trans_config["server_bin_path"]))
        self.abs_model_path = os.path.abspath(os.path.join(current_dir, trans_config["model_path"]))
        if "proj_path" in trans_config:
            self.abs_proj_path = os.path.abspath(os.path.join(current_dir, trans_config["proj_path"]))
        if "n_gpu_layers" in trans_config:
            self.n_gpu_layers = trans_config["n_gpu_layers"]

    def check_server_available(self, max_retries: int = 3) -> bool:
        """检查服务器是否可用"""
        health_url = f"{self.base_url}/health"
        for attempt in range(max_retries):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                if attempt < max_retries - 1:
                    time.sleep(1)
        return False

    def start(self, threads: int = 2) -> bool:
        """启动服务器（仅当 bootstrap_server=True 且服务不可用时）"""
        if not self.bootstrap:
            print(f"ℹ️ [{self.server_name}] bootstrap_server=False，跳过启动")
            return False
            
        if self.check_server_available(1):
            print(f"✅ [{self.server_name}] 使用现有服务器: {self.server_url}")
            return True
            
        print(f"🚀 [{self.server_name}] 启动新进程...")
        
        if self.process:
            self.stop()
            
        if not os.path.exists(self.abs_server_bin) or not os.path.exists(self.abs_model_path):
            print(f"❌ [{self.server_name}] 文件不存在")
            return False

        cmd = [self.abs_server_bin, "-m", self.abs_model_path]
        if hasattr(self, 'abs_proj_path'):
            cmd.extend(["--mmproj", self.abs_proj_path])
        if hasattr(self, 'n_gpu_layers'):
            cmd.extend(["-ngl", str(self.n_gpu_layers)])
        cmd.extend(["--port", str(self.port), "-c", "512", "--threads", str(threads)])
        
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        
        for _ in range(15):
            if self.check_server_available(1):
                print(f"✅ [{self.server_name}] 服务就绪 (PID: {self.process.pid})")
                return True
            time.sleep(1)
            
        print(f"⚠️ [{self.server_name}] 启动超时，请手动检查: {self.base_url}/health")
        return False

    def stop(self):
        """终止进程"""
        if self.process:
            print(f"🛑 [{self.server_name}] 终止进程 (PID: {self.process.pid})")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def restart(self, threads: int = 4) -> bool:
        self.stop()
        time.sleep(1)
        return self.start(threads)