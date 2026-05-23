# 简介
这是一个自动生成字幕的工具。捕获语音，vad检测，送入asr转录。
项目使用uv。模型和llamacpp服务不在本项目中。
autoSubtitle/ (项目根目录)
├── config.toml               # 配置文件：存储 VAD、LLM、GUI 字体等所有参数
├── main.py                   # 🚀 程序主入口：初始化 QApplication，应用暗色主题，拉起主窗体
├── backend.py                # 🧠 后端核心引擎：负责初始化音频设备与模型，管理推理子线程
├── audio_processor.py        # 🎙️ 音频数据处理器：处理 WASAPI 环回音频流，执行 VAD 切片
├── modelServer.py            # 💾 服务守护模块：负责在后台拉起并管理 llama-server.exe 服务进程
├── callModel.py              # 🌐 模型通信接口：向 llama-server 发送音频字节流并获取 ASR 文本结果
└── gui/                      # 🎨 GUI 界面包文件夹
    ├── __init__.py           # 初始化文件：使 gui 文件夹成为一个标准的 Python 可导入包
    ├── main_window.py        # 🗂 主导航窗体：继承 FluentWindow，整合侧边栏并路由联通各子页面
    ├── home_interface.py     # 🎛 主控制台面板：提供开启/停止服务的大按钮以及运行状态反馈
    ├── setting_interface.py  # ⚙️ 独立设置页面：包含自定义的滑块和文件选择卡片，负责反向读写 TOML
    └── subtitle_view.py      # 📺 悬浮字幕视窗：实现置顶、无边框、半透明、可拖拽的纯净字幕渲染



# 开发记录
以下是开发过程中遇到的几个问题的解法：
1. 🌟 增加 64 采样点的前瞻拼接（Context Padding）—— 【解决全盘打印点】

    修改内容：在将每个 32ms（512采样点）的音频块喂给 ONNX 之前，必须强行把上一个音频块末尾的 最后 64 个采样点（约 4ms） 拼在当前帧的左侧，组成一个 576 长度的输入。

    必要原因：这是因为你下载的官方原生 v5 模型内部自带了 STFT 傅里叶变换卷积层。卷积核在边缘做特征提取时需要左侧上下文。如果没有这 64 点的平滑历史过渡，模型在做切片卷积时会因为“边缘全零填充”导致严重的频谱泄露，把好端端的语音解析成了离散相干噪音，结果就是模型变聋，输出概率死死卡在 0.0（全是点）。


2. 🌟 对输出状态执行 np.array(next_state, dtype=np.float32) 深拷贝 —— 【解决维度畸变报错】

    修改内容：在执行 out, next_state = ort_session.run(None, inputs) 得到返回之后，不能直接把 next_state 赋值回给 state，必须强行用 np.array() 对其在内存中进行全新重构和深拷贝。

    必要原因：这是由 Python ONNX Runtime 的隐藏内存机制决定的。ONNX 为了追求极致的速度，返回的 next_state 并不是一个纯净的 NumPy 数组，而是对 C++ 底层运行栈临时内存的一个只读指针引用。如果不做深拷贝，在下一轮循环它重新作为输入塞回给 inputs['state'] 时，ONNX 内部的 If-Else 条件节点就会发生严重的指针交错，让张量像穿衣服一样越滚越厚，最终在第二帧就爆出了著名的 Input X must have 3 dimensions only. Actual:{1,1,1,128,3} 的 5 维多层嵌套地狱崩溃。


3. 🌟 执行明确的列表显式解包（out, next_state = ...）—— 【解决属性报错】

    修改内容：由于 ONNX Runtime 的 run() 函数永远会把模型所有的输出结果打包成一个标准 Python list 返回。所以必须显式地用两个变量去承接这个列表中的元素（第一项是人声概率，第二项是下一帧的隐层状态）。

    必要原因：如果不进行显式解包，直接用单个变量承接整个列表，你就无法对第一项调用 .item() 提取浮点概率（引发 list object has no attribute item 报错），也无法干净地提取下一帧状态。