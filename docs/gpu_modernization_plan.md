# PyMOL 现代化 GPU 特性实施方案：DLSS 4.5 / FSR 4 / 硬件光线追踪

> 2026-09-09。前置阅读：[vulkan_feasibility.md](vulkan_feasibility.md)（OpenGL 依赖面调查与后端路线对比）。本文是其"长期路线 C"的具体工程化方案。

## 0. 目标与现状差距

目标：PyMOL 支持三组现代 GPU 特性——
1. **DLSS 4.5**（超分 SR / 光线重建 RR，二代 Transformer 模型，SDK 310.6+ / Streamline 2.11+）
2. **FSR 4**（AMD ML 超分，FidelityFX SDK 2.0，RDNA4 专属，老卡自动回落 FSR 3.1.5）
3. **硬件光线追踪**（NVIDIA RTX / AMD RDNA2+ / Intel Arc）

现状：PyMOL 渲染完全基于 OpenGL Compatibility Profile（41 个文件直接调 GL、35 个文件含立即模式、视口内嵌 2D GUI），**没有运动矢量输出、没有交换链控制、没有光追管线**——这三者分别是超分、补帧、光追的硬前置条件。因此本方案的第一性工作是**新建实时渲染后端**，而不是"接入几个 SDK"。

## 1. SDK/API 支持矩阵（2026-09 实测调研）

| 特性 | API 载体 | 硬件要求 | 集成 SDK | 备注 |
|---|---|---|---|---|
| DLSS 4.5 SR | D3D11/12、Vulkan（NGX） | 全系 NVIDIA RTX（20 起） | [DLSS SDK 310.x](https://github.com/NVIDIA/DLSS) + Streamline 2.11+ | 需运动矢量+深度+抖动 |
| DLSS 4.5 RR（去噪） | 同上 | 全系 RTX | 同上 | 需光追结果输入，是 RT 去噪器 |
| DLSS FG（补帧） | **仅 D3D12**（RTX 50 新增 Vulkan） | RTX 40/50 | Streamline | 见可行性报告：对科学工具价值低，**不做** |
| FSR 4 SR | **仅 D3D12**（SDK 2.0 尚无 Vulkan 后端） | 仅 RX 9000（RDNA4），否则回落 FSR 3.1.5 | [FidelityFX SDK 2.0](https://gpuopen.com/amd-fidelityfx-sdk/) | 开源模型；Vulkan 支持在 AMD 路线图上 |
| FSR 3.1 SR | DX11/12、Vulkan | 通用（含非 AMD 卡） | FidelityFX SDK 1.x/2.x | Vulkan 下的跨厂商兜底 |
| XeSS | DX11/12、Vulkan | Intel Arc 硬件路径 + DP4a 通用路径 | XeSS SDK | 可选第三家 |
| 硬件 RT | `VK_KHR_ray_tracing_*`（Vulkan）/ DXR（D3D12） | RTX / RDNA2+ / Arc | 无需 SDK（驱动级） | BLAS/TLAS + RT 管线 |

**关键结论**：
- DLSS 4.5 与 FSR 4 没有共同 API：DLSS 走 Vulkan/NGX 或 D3D12，FSR 4 只在 D3D12。要"两家最新都支持"，**Windows 上 D3D12 是最大公约数**；Vulkan 作为跨平台第二后端（Linux + DLSS NGX + FSR 3.1）。
- 硬件光追两条 API 都齐备（VK_RT / DXR），跟随所选后端。

## 2. 架构方案

```
┌─ Qt 主窗口（保留：全部 2D UI / 对话框 / 菜单，不改动）
│
├─ PyMOLViewport（新）
│   ├─ RenderDevice 抽象接口          ← 唯一后端契约
│   │    swapchain / buffer / texture(MRT) / pipeline / bindless 描述符 / 时间戳查询
│   ├─ D3D12Device (Windows 优先)     ← DLSS 4.5 Streamline + FSR 4 + DXR
│   ├─ VulkanDevice (跨平台)          ← DLSS NGX + FSR 3.1 + VK_RT
│   └─ (过渡期) GLDevice = 现有 QOpenGLWidget 路径，保证零回归
│
├─ SceneTranslator（新，C++/C++20）
│   └─ CGO → GPU 图元化缓存（球体→实例化/imposter，圆柱→实例化，mesh/surface→顶点索引，
│       标签→SDF 字体 atlas，2D overlay→Qt 层绘制而非 GPU 内绘制）
│   └─ 每帧输出：颜色 + 深度 + **运动矢量**（相机矩阵解析生成，分子场景天然友好）
│
├─ UpscalerChain（新）
│   └─ Streamline(DLSS4.5 SR/RR) | FidelityFX(FSR4/3.1) | XeSS | 后备 CAS 锐化
│
└─ RtRenderer（新，阶段 5）
    └─ BLAS/TLAS 构建 ← CGO 实例；RT 阴影/AO/玻璃/光滑表面；DLSS RR 或时域去噪
```

设计原则：
1. **CGO 是现成的场景中间层**——不重写 Executive/Rep 体系，只在帧末把 CGO 缓存翻译到新后端（复用现有 CGO→顶点逻辑的分发骨架，参考 CGORenderer.cpp 已有的非 GL 路径雏形）。
2. **2D overlay 迁出 GL**：内嵌 GUI 面板与状态文字改为 Qt overlay 合成，顺带解决位图字体无法渲染中文的问题（见 i18n 报告备注）。
3. **GL 路径全程保留为回退**，新后端按 `set render_backend` 切换，可逐表示方式（sphere/cyl/mesh/…）灰度迁移。

## 3. 分阶段实施（含工作量）

| 阶段 | 内容 | 交付物 | 估计 |
|---|---|---|---|
| **P1 设备抽象** | RenderDevice 接口 + GLDevice 适配（把现有路径包进接口） | 无用户可见变化，代码可测 | 3–4 人周 |
| **P2 D3D12 最小后端** | swapchain、静态几何缓存、基础着色器迁移（2–3 个 GLSL→HLSL/DXC SPIR-V）、运动矢量+深度 MRT、交互态连续渲染 | 视口可切换 D3D12 跑线框/球棍 | 6–8 人周 |
| **P3 超分接入** | Streamline(DLSS 4.5 SR) + FidelityFX(FSR4/回落3.1) + 半分辨率交互渲染 | 低端机/iGPU 交互帧率提升；4K 视口实用化 | 2–3 人周 |
| **P4 Vulkan 后端** | 复用抽象层移植 P2/P3（SPIR-V 直接复用）；Linux 通 | 跨平台；DLSS NGX 路径 | 5–6 人周 |
| **P5 硬件光追** | BLAS/TLAS 构建、RT 阴影/AO/玻璃、`ray` 命令的 GPU 加速路径、DLSS RR/时域去噪、离屏照片级导出 | GPU 实时光追预览 + 秒级照片导出 | 8–12 人周 |
| **P6 收尾** | 立体渲染、volume/OIT 迁移、ray-trace 帧序列、回归测试 | 功能对齐旧管线 | 6–8 人周 |

总计约 **9–12 人月**（单人全职）。可独立交付的里程碑：P3 结束即有"可演示的超分"。

## 4. 风险与约束

1. **上游协调**：Schrödinger 对渲染层有既定路线；fork 自行维护 9–12 人月的渲染栈意味着后续 upstream 合并成本显著上升。建议尽早开 issue 与上游沟通。
2. **DLSS 发布合规**：NGX/DLSS 二进制随应用分发需 NVIDIA 审批（application ID）；FSR/XeSS 为宽松许可（MIT 类）。
3. **FSR 4 硬件门槛**：仅 RX 9000 系；必须实现 FSR 3.1 回落链，否则非 RDNA4 用户（多数 AMD 用户）无超分。
4. **运动矢量正确性**：拾取高亮、闪现表示切换、动画状态插值都会产生非相机运动——需要几何级 MV 标注，否则超分画面会拖影（分子场景大部分时间是静态相机+静态物体，是最简单的 MV 情形，但动画播放时必须正确）。
5. **测试资产**：现有 `testing/testing.py` 全是 CPU/数据断言，需要新增图像回归（现成机制：`cmd.png` 哈希对比）覆盖两个后端。

## 5. 立即可做的下一步（本周可启动）

1. **P1 骨架**：在 `layer0/` 新建 `RenderDevice` 接口与 `GLDevice` 适配器，不改变任何行为（纯重构，测试守护）。
2. **FSR 3.1 Vulkan 前哨验证**：在现有 GL 视口用 FSR 1（EASU+RCAS compute）验证"半分辨率+超分"的画质/性能基线，为 P3 提供数据。
3. **Zink 基线**：用 mesa-dist-win 测当前 GL 在 Vulkan 上的性能基线（已有环境，半天）。
4. **向 NVIDIA 申请 NGX application ID**（审批有周期，尽早启动）。

## 参考

- [DLSS 4.5 发布（Gamescom 2026）](https://www.nvidia.com/en-us/geforce/news/gamescom-2026-dlss-4-5-ray-reconstruction-release-announcements-trailers/) / [DLSS SDK](https://github.com/NVIDIA/DLSS) / [Streamline SDK](https://developer.nvidia.com/rtx/streamline/get-started)
- [FidelityFX SDK 2.0（FSR 4）](https://gpuopen.com/amd-fidelityfx-sdk/) / [FSR 3](https://gpuopen.com/fidelityfx-super-resolution-3/)
- [VulkanSceneGraph（含 Qt 集成与 RT 支持，可参考其抽象）](https://github.com/vsg-dev/VulkanSceneGraph)
- [VTK 去 OpenGL 路线讨论（同类软件先例）](https://discourse.vtk.org/t/road-map-forward-past-opengl/13667)
