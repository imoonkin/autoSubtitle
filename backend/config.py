"""配置管理后端。

AppConfig 通过 Qt Property 将 config.toml 的每一项暴露给 QML。
load_config_dict() 是唯一读取 TOML 的地方，AppConfig 和 SubtitleController 共用。
"""
import os
import sys
import tomli_w
from PySide6.QtCore import QObject, Property, Signal

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# ── Path helpers ────────────────────────────────────────────────────────────

def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(_project_root(), "config.toml")


def load_config_dict():
    """读取 config.toml 返回原始 dict。

    这是整个项目读取配置文件的唯一入口。
    """
    if not os.path.exists(CONFIG_PATH):
        print(f"⚠️ 未找到配置文件: {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


# ── Config schema ───────────────────────────────────────────────────────────
# (property_name, toml_path_parts, default_value)
# NOTE: prop_name must match the Python getter/setter suffix, e.g.
# "font_size" → get_font_size() / set_font_size()
_CONFIG_SCHEMA = [
    ("font_size",             ("gui",       "font_size"),              32),
    ("vad_model_path",        ("models", "vad", "model_path"),        ""),
    ("max_silence_chunks",    ("models", "vad", "max_silence_chunks"), 25),
    ("max_speech_duration_s", ("models", "vad", "max_speech_duration_s"), 10),
    ("llm_exe_path",          ("models", "llm", "exe_path"),          ""),
    ("llm_model_path",        ("models", "llm", "model_path"),        ""),
    ("llm_mmproj_path",       ("models", "llm", "mmproj_path"),       ""),
    ("ngl",                   ("models", "llm", "ngl"),               99),
    ("ctx_size",              ("models", "llm", "ctx_size"),          4096),
]


def _deep_get(d: dict, keys: tuple, default):
    """安全读取嵌套 dict 的值。"""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, {})
    return d if not isinstance(d, dict) else default


def _deep_set(d: dict, keys: tuple, value):
    """安全写入嵌套 dict，自动创建中间层。"""
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


# ══════════════════════════════════════════════════════════════════════════════
# AppConfig — QML-facing config object
# ══════════════════════════════════════════════════════════════════════════════

class AppConfig(QObject):
    configSaved = Signal(bool, str)

    # ── signals ─────────────────────────────────────────────────────────
    fontSizeChanged          = Signal(int)
    vadModelPathChanged      = Signal(str)
    maxSilenceChunksChanged  = Signal(int)
    maxSpeechDurationSChanged = Signal(int)
    llmExePathChanged        = Signal(str)
    llmModelPathChanged      = Signal(str)
    llmMmprojPathChanged     = Signal(str)
    nglChanged               = Signal(int)
    ctxSizeChanged           = Signal(int)

    def __init__(self):
        super().__init__()
        self._font_size            = 32
        self._vad_model_path       = ""
        self._max_silence_chunks   = 25
        self._max_speech_duration_s = 10
        self._llm_exe_path         = ""
        self._llm_model_path       = ""
        self._llm_mmproj_path      = ""
        self._ngl                  = 99
        self._ctx_size             = 4096
        self.load_config()

    # ── load / save ─────────────────────────────────────────────────────

    def load_config(self):
        data = load_config_dict()
        if not data:
            return

        for prop_name, toml_path, default in _CONFIG_SCHEMA:
            val = _deep_get(data, toml_path, default)
            setter = getattr(self, f"set_{prop_name}", None)
            if setter:
                # ngl / ctx_size are stored as strings in TOML
                setter(int(val) if isinstance(default, int) and not isinstance(val, int) else val)

    def save_config(self):
        data = load_config_dict()

        for prop_name, toml_path, default in _CONFIG_SCHEMA:
            getter = getattr(self, f"get_{prop_name}")
            val = getter()
            # Store ngl / ctx_size as strings for backward compat
            if prop_name in ("ngl", "ctx_size"):
                val = str(val)
            _deep_set(data, toml_path, val)

        try:
            with open(CONFIG_PATH, "wb") as f:
                tomli_w.dump(data, f)
            self.configSaved.emit(True, "配置已成功写入 config.toml！")
        except Exception as e:
            self.configSaved.emit(False, f"无法写入配置文件: {str(e)}")

    # ── fontSize ────────────────────────────────────────────────────────
    def get_font_size(self): return self._font_size
    def set_font_size(self, v):
        if self._font_size != v:
            self._font_size = v
            self.fontSizeChanged.emit(v)
    fontSize = Property(int, fget=get_font_size, fset=set_font_size, notify=fontSizeChanged)

    # ── vadModelPath ────────────────────────────────────────────────────
    def get_vad_model_path(self): return self._vad_model_path
    def set_vad_model_path(self, v):
        if self._vad_model_path != v:
            self._vad_model_path = v
            self.vadModelPathChanged.emit(v)
    vadModelPath = Property(str, fget=get_vad_model_path, fset=set_vad_model_path, notify=vadModelPathChanged)

    # ── maxSilenceChunks ────────────────────────────────────────────────
    def get_max_silence_chunks(self): return self._max_silence_chunks
    def set_max_silence_chunks(self, v):
        if self._max_silence_chunks != v:
            self._max_silence_chunks = v
            self.maxSilenceChunksChanged.emit(v)
    maxSilenceChunks = Property(int, fget=get_max_silence_chunks, fset=set_max_silence_chunks, notify=maxSilenceChunksChanged)

    # ── maxSpeechDurationS ──────────────────────────────────────────────
    def get_max_speech_duration_s(self): return self._max_speech_duration_s
    def set_max_speech_duration_s(self, v):
        if self._max_speech_duration_s != v:
            self._max_speech_duration_s = v
            self.maxSpeechDurationSChanged.emit(v)
    maxSpeechDurationS = Property(int, fget=get_max_speech_duration_s, fset=set_max_speech_duration_s, notify=maxSpeechDurationSChanged)

    # ── llmExePath ──────────────────────────────────────────────────────
    def get_llm_exe_path(self): return self._llm_exe_path
    def set_llm_exe_path(self, v):
        if self._llm_exe_path != v:
            self._llm_exe_path = v
            self.llmExePathChanged.emit(v)
    llmExePath = Property(str, fget=get_llm_exe_path, fset=set_llm_exe_path, notify=llmExePathChanged)

    # ── llmModelPath ────────────────────────────────────────────────────
    def get_llm_model_path(self): return self._llm_model_path
    def set_llm_model_path(self, v):
        if self._llm_model_path != v:
            self._llm_model_path = v
            self.llmModelPathChanged.emit(v)
    llmModelPath = Property(str, fget=get_llm_model_path, fset=set_llm_model_path, notify=llmModelPathChanged)

    # ── llmMmprojPath ───────────────────────────────────────────────────
    def get_llm_mmproj_path(self): return self._llm_mmproj_path
    def set_llm_mmproj_path(self, v):
        if self._llm_mmproj_path != v:
            self._llm_mmproj_path = v
            self.llmMmprojPathChanged.emit(v)
    llmMmprojPath = Property(str, fget=get_llm_mmproj_path, fset=set_llm_mmproj_path, notify=llmMmprojPathChanged)

    # ── ngl ─────────────────────────────────────────────────────────────
    def get_ngl(self): return self._ngl
    def set_ngl(self, v):
        if self._ngl != v:
            self._ngl = v
            self.nglChanged.emit(v)
    ngl = Property(int, fget=get_ngl, fset=set_ngl, notify=nglChanged)

    # ── ctxSize ─────────────────────────────────────────────────────────
    def get_ctx_size(self): return self._ctx_size
    def set_ctx_size(self, v):
        if self._ctx_size != v:
            self._ctx_size = v
            self.ctxSizeChanged.emit(v)
    ctxSize = Property(int, fget=get_ctx_size, fset=set_ctx_size, notify=ctxSizeChanged)
