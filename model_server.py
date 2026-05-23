import os
import subprocess
import atexit
import time
import httpx
import socket

_server_process = None

def start_llama_server():
    global _server_process
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    """
    .\llama\llama-server.exe -m ".\models\Qwen3-ASR-0.6B-Q8_0.gguf"
     --mmproj ".\models\mmproj-Qwen3-ASR-0.6B-Q8_0.gguf" 
     --device Vulkan0 -ngl 99 -c 4096 -np 1 --host 0.0.0.0 --port 8080
    """
    exe_path = os.path.join(base_dir, "llama", "llama-server.exe")
    model_path = os.path.join(base_dir, "models", "Qwen3-ASR-0.6B-Q8_0.gguf")
    mmproj_path = os.path.join(base_dir, "models", "mmproj-Qwen3-ASR-0.6B-Q8_0.gguf")
    port = "8080"
    cmd = [
        exe_path,
        "--model", model_path,
        "--mmproj",mmproj_path,
        "-ngl", "99",
        "-c", "4096",
        "-np","1",
        "--reasoning-format", "none",
        "--host", "127.0.0.1",
        "--port", port,
    ]
    
    print(f"🚀 [Server] 正在后台拉起大模型服务器...")
    
    try:
        # 使用 subprocess.Popen 异步启动，不阻塞 Python 主线程
        # stdout/stderr 设置为 DEVNULL 可以隐藏黑窗口的滚动日志，让控制台保持干净。
        # 如果你想看它的报错日志，可以把它们删掉或设为 None
        _server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP # 确保能完整杀掉整个进程组
        )
        
        atexit.register(stop_llama_server)
        
        print("⏳ [Server] 等待服务器响应 (正在进行健康检查)...")
        for i in range(30):  
            if _server_process.poll() is not None:
                print("❌ [Server] Server crashed during startup! Check the logs above.")
                return False
                
            try:
                res = httpx.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
                if res.status_code == 200:
                    print("\n✅ [Server] Qwen3-ASR Server is fully ready!")
                    return True
            except httpx.RequestError:
                pass
                
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex(('127.0.0.1', int(port))) == 0:
                        print("\n✅ [Server] Port 8080 is listening! Server is ready.")
                        return True
            except Exception:
                pass
                
            time.sleep(1)
                
        print("❌ [Server] 等待超时，服务未能正常响应。")
        return False
        
    except Exception as e:
        print(f"❌ [Server] 启动进程时发生硬件或路径错误: {e}")
        return False

def stop_llama_server():
    """安全关闭后台服务器进程"""
    global _server_process
    if _server_process and _server_process.poll() is None:
        print("\n🛑 [Server] 正在关闭后台大模型服务器...")
        try:
            _server_process.terminate()
            _server_process.wait(timeout=5)
            print("💀 [Server] 后台服务器进程已完全退出。")
        except subprocess.TimeoutExpired:
            _server_process.kill()
            print("💥 [Server] 服务器未响应，已强制杀掉进程。")
        _server_process = None
