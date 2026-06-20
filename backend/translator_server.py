"""llama.cpp 后台服务器守护进程管理器。"""
import os
import subprocess
import time
import requests
from urllib.parse import urlparse

class LlamaServerManager:
    def __init__(self, current_dir: str, trans_config: dict):
        self.process = None
        self.server_url = trans_config.get("server_url", "http://127.0.0.1:8080/v1/chat/completions")
        
        # 提取端口（用于健康检查）
        self.port = trans_config.get("port", 8080)
        
        # 如果 server_url 包含完整路径，提取基础 URL 用于健康检查
        parsed = urlparse(self.server_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # 提取路径配置（用于启动服务）
        server_bin = trans_config.get("server_bin_path", "bin/llama-server")
        model_path = trans_config.get("model_path", "models/translation-model.gguf")
        
        self.abs_server_bin = os.path.abspath(os.path.join(current_dir, server_bin)) if not os.path.isabs(server_bin) else server_bin
        self.abs_model_path = os.path.abspath(os.path.join(current_dir, model_path)) if not os.path.isabs(model_path) else model_path
        
        print(f"📋 [LlamaServer] 配置信息:")
        print(f"  Server URL: {self.server_url}")
        print(f"  Base URL: {self.base_url}")
        print(f"  Port: {self.port}")
        print(f"  Server Bin: {self.abs_server_bin}")
        print(f"  Model Path: {self.abs_model_path}")

    def check_server_available(self, max_retries: int = 3) -> bool:
        """检查 server_url 是否可用"""
        print(f"🔍 [LlamaServer] 检查服务器是否可用: {self.server_url}")
        
        # 先检查基础健康端点
        health_url = f"{self.base_url}/health"
        print(f"  → 尝试健康检查: {health_url}")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ [LlamaServer] 服务器已就绪 (健康检查通过)")
                    return True
                else:
                    print(f"  ⚠️ 健康检查返回状态码: {response.status_code}")
            except requests.ConnectionError:
                print(f"  ⚠️ 连接失败 (尝试 {attempt + 1}/{max_retries})")
            except requests.Timeout:
                print(f"  ⚠️ 连接超时 (尝试 {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"  ⚠️ 检查失败: {e} (尝试 {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                time.sleep(1)
        
        # 如果健康检查失败，尝试直接访问 server_url（可能没有 /health 端点）
        print(f"  → 尝试直接访问 API 端点: {self.server_url}")
        try:
            # 使用 OPTIONS 或 GET 方法检查端点是否存在
            response = requests.options(self.server_url, timeout=2)
            if response.status_code < 500:  # 只要不是服务器错误就算可达
                print(f"✅ [LlamaServer] API 端点可访问 (状态码: {response.status_code})")
                return True
        except requests.ConnectionError:
            print(f"  ❌ API 端点连接失败")
        except requests.Timeout:
            print(f"  ❌ API 端点超时")
        except Exception as e:
            print(f"  ❌ API 端点检查失败: {e}")
        
        print(f"❌ [LlamaServer] 服务器不可用")
        return False

    def start(self, threads: int = 4) -> bool:
        """启动 llama-server（如果服务器不可用）"""
        # 先检查服务器是否已经可用
        if self.check_server_available(1):
            print("✅ [LlamaServer] 使用现有服务器，无需启动新进程")
            return True
        
        # 服务器不可用，启动新进程
        print(f"🚀 [LlamaServer] 正在启动新服务器进程...")
        
        if self.process is not None:
            print("⚠️ [LlamaServer] 进程已存在，先停止旧进程")
            self.stop()
        
        # 检查文件是否存在
        if not os.path.exists(self.abs_server_bin):
            print(f"❌ [LlamaServer] 服务器可执行文件不存在: {self.abs_server_bin}")
            return False
        
        if not os.path.exists(self.abs_model_path):
            print(f"❌ [LlamaServer] 模型文件不存在: {self.abs_model_path}")
            return False

        # 组装 llama-server 启动命令
        cmd = [
            self.abs_server_bin,
            "-m", self.abs_model_path,
            "--port", str(self.port),
            "-c", "512",
            "--threads", str(threads)
        ]
        print(f"  📝 启动命令: {' '.join(cmd)}")
        
        # 异步非阻塞拉起，隐藏控制台输出
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"  ⏳ 等待服务器启动 (进程 PID: {self.process.pid})...")
        time.sleep(2)
        
        # 循环等待健康检查通过
        health_url = f"{self.base_url}/health"
        for attempt in range(15):
            try:
                response = requests.get(health_url, timeout=1)
                if response.status_code == 200:
                    print("✅ [LlamaServer] 进程就绪，健康检查通过。")
                    return True
            except requests.RequestException:
                time.sleep(1)
        
        # 如果健康检查失败，尝试直接访问 API
        print("  ⚠️ 健康检查超时，尝试直接访问 API...")
        for attempt in range(3):
            try:
                response = requests.options(self.server_url, timeout=1)
                if response.status_code < 500:
                    print(f"✅ [LlamaServer] API 端点可访问 (状态码: {response.status_code})")
                    return True
            except:
                time.sleep(1)
        
        print("⚠️ [LlamaServer] 进程已创建，但服务响应超时。")
        print(f"  💡 请手动检查: {health_url}")
        return False

    def stop(self):
        """安全终结外部进程，防止算力和内存泄漏"""
        if self.process:
            print("🛑 [LlamaServer] 正在终止外部服务器进程...")
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                    print("✅ [LlamaServer] 进程正常终止")
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    print("💀 [LlamaServer] 进程已被强制终止")
            except Exception as e:
                print(f"⚠️ [LlamaServer] 终止进程时出错: {e}")
            finally:
                self.process = None
        else:
            print("ℹ️ [LlamaServer] 没有需要终止的进程")

    def restart(self, threads: int = 4) -> bool:
        """重启服务器"""
        print("🔄 [LlamaServer] 重启服务器...")
        self.stop()
        time.sleep(1)
        return self.start(threads)