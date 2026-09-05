# PyMOL 接入 Vulkan 可行性评估

> 2026-09-06，基于 pymol-open-source-multilingual（上游 master 5e8bfca5，PyMOL 3.1.0）的代码调查与生态调研。

## 结论（TL;DR）

**"让 PyMOL 跑在 Vulkan 上"立刻可行（零代码改动），"把 PyMOL 移植到 Vulkan 原生渲染"技术上可行但代价极高（约数人年级别），不建议作为短期目标。** 推荐分两步：先用 Mesa Zink 验证 GL-over-Vulkan 的可行性与性能，若确有硬需求（macOS Metal/WebGPU/超大场景/光线追踪），再评估以 CGO 为输入新建并行渲染器的路线，而不是改造现有管线。

---

## 1. 现状：代码对 OpenGL 的耦合面（实测）

| 维度 | 事实 | 证据 |
|---|---|---|
| 直接调用 GL 的文件数 | 41 个（layer0–layer5） | `grep -rlE "gl(Begin\|DrawArrays\|…)"` |
| GL 调用最重的文件 | layer1/CGOGL.cpp (~198 处)、SceneRender.cpp (180)、Scene.cpp (127)、Ortho.cpp (106)、Control.cpp (91)、ScrollBar.cpp (59) | grep 统计 |
| 立即模式残留 | 35 个文件仍用 `glBegin/glEnd`（内嵌 GUI、文字、标尺等 overlay 绘制） | grep |
| 上下文 | Qt `QOpenGLWidget`/`QGLWidget`（modules/pmg_qt/pymol_gl_widget.py），请求多重采样与四缓冲立体；**依赖 Compatibility Profile**（实机启动显示 `GL_VERSION: 4.6.0 Compatibility Profile Context`） | pymol_gl_widget.py:60–95 |
| 着色器 | data/shaders/ 约 40 个源文件：#version 120 ×7、#version 400（bezier 曲面细分 tsc/tse）；含 OIT 透明排序、volume 重建、圆柱/球/表面、connector 几何着色器、立体/浮雕互补色、光照预计算 | data/shaders/ |
| 高级特性 | 实例化/SSBO 类（layer0/GenericBuffer.cpp）、曲面细分、OIT | grep |
| 场景抽象 | CGO（Compiled Graphics Objects，保留模式图元表）→ 每帧由 CGOGL.cpp 翻译成 GL 调用；**只有"半层"抽象，且 overlay/GUI 文字直接走 GL** | layer1/CGOGL.cpp |
| GUI | 内嵌 GUI（右侧 A/S/H/L/C 面板、视口底部鼠标状态文本）画在**同一个 GL 上下文**里，用内部位图字体 | layer1/Ortho.cpp、ButMode.cpp |
| 线程 | GL 上下文由 GUI 主线程持有；"multithreaded rendering" 指 CPU 光线追踪线程，与 GL 无关 | 启动日志、layer5/main.cpp |

关键结论：PyMOL 不只渲染分子——**视口里还画着整套 2D GUI 和位图文字**，全部依赖 Compatibility Profile（矩阵栈、glBegin、accum buffer 立体）。任何"原生 Vulkan 后端"都必须连这部分 2D 内容一起重写。

## 2. 生态调研

- **没有现成的 PyMOL Vulkan 后端**（官方或社区均无）。最接近的先行者：[molar_vis](https://github.com/yesint/molar_vis)（wgpu→Vulkan/Metal/DX12/WebGPU 的分子查看器）、PyMOL-wasm（把 PyMOL 移植到浏览器 WebGL）。
- **Mesa Zink（GL-on-Vulkan）**：OpenGL 4.6 已 conformant；Linux 上性能与原生驱动持平、已成为 NVIDIA Nouveau 的默认 GL 驱动；Windows 端 Kopper/WGL 支持逐年成熟，Wine 已在把 Zink 作为默认 GL 实现（[Phoronix](https://www.phoronix.com/news/Wine-MR-Zink-By-Default)）。Windows 可用 [mesa-dist-win](https://github.com/pal1000/mesa-dist-win/) 预编译 `opengl32.dll` 直接放进应用目录生效。已知问题：Windows 上相对原生 ICD 有性能损耗（个别场景明显），兼容性需逐应用验证。
- **Qt + Vulkan**：Qt 6 提供 `QVulkanWindow`（刻意保留了 OpenGL 习惯如 Y 轴方向以方便移植）；VulkanSceneGraph 有官方 [vsgQt](https://github.com/vsg-dev/VulkanSceneGraph) 集成；GL↔Vulkan 可经外部信号量/共享内存互操作（X-Plane 11.5 有先例，见 [VSG discussion #763](https://github.com/vsg-dev/VulkanSceneGraph/discussions/763)）。
- 参考案例：[VTK "Road map forward past OpenGL"](https://discourse.vtk.org/t/road-map-forward-past-opengl/13667) —— 同为 Qt 科学可视化，迁离 OpenGL 的动因主要是 macOS 弃用 OpenGL（封顶 4.1）。

## 3. 路线对比

| 路线 | 做法 | 工作量 | 收益 | 风险 |
|---|---|---|---|---|
| **A. Zink 透传（推荐起步）** | 把 mesa-dist-win 的 `opengl32.dll` 放到 pymol.exe 同目录（或环境变量指向 Mesa），PyMOL 零改动跑在 Vulkan 上 | 半天验证 | 立刻验证兼容性/性能；统一 GPU 后端叙事；AMD Windows GL 驱动较弱时反而可能更快 | 性能损耗、个别驱动 bug；不产生代码资产 |
| **B. GL/Vulkan 互操作混合** | QVulkanWindow 另开 Vulkan 上下文，经信号量/共享图像与现有 GL 互操作，新效果（如 RT）用 Vulkan 画 | 数人月 | 增量引入 Vulkan-only 特性 | 两套上下文同步复杂；收益场景有限 |
| **C. 原生 Vulkan 后端** | 抽象渲染接口；CGO→Vulkan pipeline 重写（约 40 个着色器、OIT、volume、曲面细分）；重写视口内 2D GUI/文字；立体渲染；多平台 WSI | **数人年** | 脱离 Compatibility Profile；macOS 可用；现代化（mesh shader、GPU RT） | 巨大回归面（立体重建、标签、GUI、ray 预览…）；上游（Schrödinger）不背书则长期维护负担自担 |
| **D. 仅 Vulkan compute** | 不动渲染，用 Vulkan compute 做 GPU 光线追踪/MD 后处理 | 人月级 | 新功能 | 与"渲染后端"诉求是两回事 |

## 4. 现代特性落地路径：超分 / 补帧 / 光追

先澄清一个常见误解：**Vulkan 本身不"带来"DLSS/FSR/光追**——DLSS 是 NVIDIA NGX SDK 的功能、FSR 是 AMD GPUOpen 的开源 SDK、光追是 `VK_KHR_ray_tracing_*` 扩展族。Vulkan 只是提供承载它们的原语（compute 管线、光追管线、swapchain 控制、运动矢量纹理）。各特性对 API 的真实依赖差别很大：

### 4.1 超分（DLSS / FSR / XeSS）

| 技术 | API 要求 | 引擎侧要求 | 对 PyMOL 的适配度 |
|---|---|---|---|
| FSR 1（EASU+RCAS） | **任意**（纯后处理着色器，OpenGL 也能跑） | 无 | ★★★ 现有 GL 管线即可加，性价比最高 |
| FSR 3.1 SR | DX12/Vulkan（开源，[GPUOpen](https://gpuopen.com/fidelityfx-super-resolution-3/)） | 渲染分辨率运动矢量 + 深度 | ★★ 需 Vulkan 后端 |
| XeSS | DX11/12/Vulkan（DP4a 路径兼容非 Intel 卡） | 同上 | ★★ 同上 |
| DLSS SR / Ray Reconstruction | DX11/12/Vulkan，经 [NVIDIA NGX SDK](https://docs.nvidia.com/ngx/latest/programming-guide/index.html)（[DLSS SDK](https://github.com/NVIDIA/DLSS)），无公开注册的 `VK_NV_DLSS` 通用扩展 | 运动矢量 + 深度 + 相机抖动（jitter），仅 NVIDIA RTX | ★★ 仅惠及 N 卡用户 |

时域类超分（FSR2+/XeSS/DLSS）要求**连续帧流**，而 PyMOL 是"按需重绘"（不转就不画）。好消息是分子场景的运动矢量可以**解析生成**（相机矩阵已知；静态画面运动矢量为零，属最简单情形），且真正需要超分的时机恰是拖拽/旋转/播放动画时。适配点：在交互态以半分辨率连续渲染 + 超分，静止态恢复全分辨率按需渲染。

### 4.2 补帧（Frame Generation）

- DLSS FG：仅 DX12（经 [Streamline SDK](https://developer.nvidia.com/rtx/streamline/get-started)）；RTX 50 系刚开放 Vulkan 支持。
- FSR 3 FG：DX12 + Vulkan，开源，可与第三方超分组合。
- **对 PyMOL 价值有限**：补帧解决的是"游戏 60fps→120fps"的流畅度，而 PyMOL 视口含 2D overlay（内嵌 GUI、标签、鼠标状态文字），补帧会让 UI 残影，必须把 overlay 标记为 UI 层才能规避——集成成本高；且分子场景本身渲染很轻，动画（movie/turntable）直接多画几帧即可。**建议不作为目标**。

### 4.3 光线追踪——真正有价值的现代化方向

PyMOL 已有 CPU 光线追踪器（`ray` 命令，质量基准但慢）。GPU RT 的合理切入点**不是**重写整个视口，而是**离屏 Vulkan-RT 照片级渲染器**：

- 以 CGO 网格/实例构建 BLAS，环境光遮蔽、软阴影、玻璃/半透明表面（分子可视化里最高价值的视觉特性）走 `VK_KHR_ray_tracing_pipeline`；
- 输出 PNG（替代/加速 `ray`），后续再考虑作为视口预览；
- 不动现有 GL 视口，回归面小，**人月级**而非人年级，是路线 C 的"前哨战"。

### 4.4 分阶段建议

1. **零门槛（现在）**：实测 Zink；在现有 GL 管线加 FSR 1/NIS 后处理（提升低端机视口与 4K 导出）。
2. **中期**：离屏 Vulkan-RT 照片级渲染模式（GPU 版 `ray`）。
3. **长期**：若 RT 模式验证成功且诉求成立，再做完整 Vulkan 视口后端；届时 FSR 3.1 SR / DLSS（NGX Vulkan）可自然接入。

## 5. 建议

1. **现在就可以做**：用 mesa-dist-win 对 conda 环境里的 pymol.exe 做 Zink 实测（本机为 AMD 8050S，Windows AMD GL 驱动口碑差，Zink 可能不降反升），跑 `testing/testing.py` + 大体系（如 PDB 巨型复合物）对比帧率。
2. **若动因是 macOS/WebGPU**：与其改造 C++ 管线，不如评估以 **CGO/wgpu** 为目标做"新渲染器并行"（参考 molar_vis），旧管线继续服务桌面端——这也与 PyMOL-wasm 的方向一致。
3. **i18n 备注**：调查中确认 PyMOL 视口状态栏文字走内部位图字体，**无法渲染中文**（实机显示 `Mouse Mode ??????`，我们 fork 的翻译值已被正确写入设置但字形缺失）。若未来真做渲染层重写（路线 C），把 overlay 文字迁到 Qt/SDF 字体渲染可一并解决该问题。

## 参考链接

- [Mesa Zink 文档](https://docs.mesa3d.org/drivers/zink.html)
- [Phoronix: Zink Windows Kopper 进展](https://www.phoronix.com/news/Zink-Windows-Kopper-Progress) / [Wine 默认内置 Zink](https://www.phoronix.com/news/Wine-MR-Zink-By-Default)
- [mesa-dist-win（Windows 预编译）](https://github.com/pal1000/mesa-dist-win/)
- [VulkanSceneGraph: OSG 迁移讨论（GL/Vulkan 互操作先例）](https://github.com/vsg-dev/VulkanSceneGraph/discussions/763)
- [Qt QVulkanWindow 文档](https://doc.qt.io/qt-6/qvulkanwindow.html)
- [VTK 迁移路线讨论](https://discourse.vtk.org/t/road-map-forward-past-opengl/13667)
- [molar_vis（wgpu 分子可视化）](https://github.com/yesint/molar_vis)
