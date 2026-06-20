"""配置管理后端。

负责项目的 config.toml 配置加载。
"""
import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

def _project_root():
    """获取项目根目录路径"""
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(_project_root(), "config.toml")

def load_config_dict() -> dict:
    """读取 config.toml 并返回嵌套的字典(dict)。

    如果文件不存在或解析失败，将返回一个包含默认参数的安全结构，防止下游崩溃。
    """
    # 🌟 定义基础防御型默认配置结构
    default_config = {
        "gui": {
            "font_size": 32
        },
        "models": {
            "vad": {
                "model_path": "models/silero_vad.onnx",
                "threshold": 0.50,
                "max_silence_chunks": 25,
                "max_speech_duration_s": 10
            },
            "asr": {
                "model_path": "models/sensevoice-small.onnx",
                "tokens_path": "models/tokens.txt",
                "num_threads": 2,
                "use_gpu": False
            },
            "translate": {
                "use_local_server": True,
                "server_bin_path": "bin/llama-server.exe",
                "model_path": "models/translation-model.gguf",
                "server_url": "http://127.0.0",
                "port": 8080,
                "threads": 4,
                "tgt_lang": "Chinese",
                "temperature": 0.3
            }
        }
    }

    if not os.path.exists(CONFIG_PATH):
        print(f"⚠️ 未找到配置文件: {CONFIG_PATH}，将使用系统默认配置运行。")
        return default_config

    try:
        with open(CONFIG_PATH, "rb") as f:
            user_config = tomllib.load(f)
            
        # 🌟 核心：使用用户配置覆盖/填充默认配置，防止用户本地漏写某项参数导致报错
        for section, sub_dict in user_config.items():
            if section in default_config and isinstance(sub_dict, dict):
                if section == "models":
                    for sub_section, values in sub_dict.items():
                        if sub_section in default_config["models"] and isinstance(values, dict):
                            default_config["models"][sub_section].update(values)
                else:
                    default_config[section].update(sub_dict)
                    
        return default_config

    except Exception as e:
        print(f"❌ 解析 config.toml 发生错误: {e}，启用安全默认配置。")
        return default_config
