import os
import subprocess
import atexit
import time
import httpx
import socket

_server_process = None

def start_llama_server(llm_config: dict):
    """
    根据传入的配置字典，动态在后台拉起 llama-server
    """
    global _server_process
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 动态安全获取配置参数，并提供默认缺省值
    conf_exe = llm_config.get("exe_path", "llama/llama-server.exe")
    conf_model = llm_config.get("model_path", "models/Qwen3-ASR-0.6B-Q8_0.gguf")
    conf_mmproj = llm_config.get("mmproj_path", "models/mmproj-Qwen3-ASR-0.6B-Q8_0.gguf")
    
    host = llm_config.get("host", "127.0.0.1")
    port = str(llm_config.get("port", "8080"))
    
    ngl = str(llm_config.get("ngl", "99"))
    ctx_size = str(llm_config.get("ctx_size", "4096"))
    parallel = str(llm_config.get("parallel", "1"))

    # 2. 自动对齐路径（如果是相对路径，则转换为绝对路径）
    exe_path = conf_exe if os.path.isabs(conf_exe) else os.path.abspath(os.path.join(base_dir, conf_exe))
    model_path = conf_model if os.path.isabs(conf_model) else os.path.abspath(os.path.join(base_dir, conf_model))
    mmproj_path = conf_mmproj if os.path.isabs(conf_mmproj) else os.path.abspath(os.path.join(base_dir, conf_mmproj))

    # 3. 动态组装命令行
    cmd = [
        exe_path,
        "--model", model_path,
        "--mmproj", mmproj_path,
        "-ngl", ngl,
        "-c", ctx_size,
        "-np", parallel,
        "--reasoning-format", "none",
        "--host", host,
        "--port", port,
    ]

    print(f"🚀 [Server] 正在后台拉起大模型服务器...")
    print(f"📦 [Server] 使用模型: {os.path.basename(model_path)}")
    
    try:
        # 异步启动进程
        _server_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        atexit.register(stop_llama_server)
        
        print("⏳ [Server] 等待服务器响应 (正在进行健康检查)...")
        for i in range(30):
            if _server_process.poll() is not None:
                print("❌ [Server] 服务器启动中途崩溃！请检查模型路径或硬件加速驱动。")
                return False
                
            # 优先通过健康检查接口探测
            try:
                res = httpx.get(f"http://{host}:{port}/health", timeout=0.5)
                if res.status_code == 200:
                    print(f"\n✅ [Server] Qwen3-ASR Server 已完全就绪！监听地址: {host}:{port}")
                    return True
            except httpx.RequestError:
                pass
                
            # 备用 TCP 端口探针
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((host, int(port))) == 0:
                        print(f"\n✅ [Server] 端口 {port} 已被监听！服务已就绪。")
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
