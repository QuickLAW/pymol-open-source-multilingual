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

## 4. 建议

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
