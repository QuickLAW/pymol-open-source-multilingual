"""zh_CN for the long text blocks that are passed to translate() by variable.

Nothing literal-based can see these: the call site reads
``print(ctr(helptext1))`` or ``_tr('Volume', VOLUME_HELP)``, so the argument
is a Name and the English text lives ~90 lines away. They are also the blocks
where a hand-copied catalogue key is most likely to drift by one character and
then never match -- which is why they are keyed by *variable name* and resolved
through the AST by generate_ts.py.

Layout is preserved (the option and mouse columns are read by eye); flag names,
setting names, key combos and command names stay English because the user types
them.
"""

BLOCK_ZH_BY_SOURCE = {
    'modules/pymol/invocation.py': {
        'helptext1': '''版权所有 (C) Schrodinger, LLC

用法：pymol [选项]... [文件]... [-- 自定义脚本参数]

选项

  --help    显示本帮助并退出
  --version 显示 PyMOL 版本并退出
  --gldebug 使用 glDebugMessageCallback 进行 OpenGL 调试
  --testing 运行 PyMOL 测试
  --diagnostics 转储系统诊断信息

  -1        config_mouse one_button（单键鼠标）
  -2        config_mouse two_button（双键鼠标）
  -a N      -A 的别名
  -A N      应用程序配置：
    -A1     简易查看窗口                   (-qxiF -X 68 -Y 100)
    -A3     仅内置 GUI，不显示启动画面     (-qx -X 68 -Y 100)
    -A4     供 PYMOLVIEWER 使用            (-X 68 -Y 100)
    -A5     辅助进程                       (-QxiICUF -X 68 -Y 100)
    -A6     全屏演示模式                   (-qxieICUPF)
  -b[N]     基准测试向导
  -B        （已弃用）
  -c        以纯命令行模式启动，用于批处理
  -C        按下 Ctrl-C 时不终止
  -d cmd    执行 PyMOL 命令
  -D N      defer_builds_mode=N
  -e        全屏
  -E N      多重采样 (GL_MULTISAMPLE_ARB)
  -f N      internal_feedback=N
  -F        internal_feedback=0
  -g file   保存图像 (png) 或电影 (mpg)
  -G        游戏模式（已弃用）
  -h        通用辅助进程（无控件、无反馈）
  -H N      窗口高度（像素）
  -i        internal_gui=0
  -I        auto_reinitialize=1（仅 Mac）
  -j        左右并列立体显示 (stereo_mode=4)
  -J        切换到用户主目录
  -k        不加载 pymolrc 或插件
  -K        保持存活：无 GUI 运行时，输入耗尽后不退出
  -l file   在新线程中运行 Python 脚本 (spawn)
  -L file   在所有内容之后再加载该文件（仅当此前已加载过内容）
  -m        内部使用 - 请勿使用（mac 外部 GUI）
  -M        强制单色显示
  -n        内部使用 - 请勿使用（incentive_product=1）
  -N name   不受支持 - 外部 GUI 类型 (pmg_qt 或 pmg_tk)（同 -w）
  -o        禁用安全保护
  -O N      sphere_mode=N
  -p        从标准输入读取命令
  -P        按会话以演示模式打开的方式处理场景
  -q        不显示启动信息
  -Q        安静模式，抑制所有文本输出
  -r file   运行 Python 脚本
  -R        启动 RPC 服务器
  -s file   将日志写入文件
  -S        强制立体显示
  -t N      stereo_mode=N
  -T name   不受支持 - Tcl/Tk GUI 皮肤
  -u file   续写日志文件（先执行已有内容，再追加新的日志输出）
  -U        不受支持：复用辅助进程
  -v        使用 openvr 桩而非真实硬件
  -V N      外部 GUI 窗口高度（像素）
  -w name   不受支持 - 外部 GUI 类型 (pmg_qt 或 pmg_tk)（同 -N）
  -W N      窗口宽度（像素）
  -x        不使用外部 GUI
  -X N      窗口在屏幕上的 x 位置
  -y        出错时退出
  -Y N      窗口在屏幕上的 y 位置
  -z N      window_visible=N
  -Z N      zoom_mode=N

文件扩展名

  pdb,sdf,...     分子结构文件
  ccp4,dx,...     密度图文件

  py,pym,pyc      Python 脚本
  pml             PyMOL 命令脚本

  p5m             隐含 -A5（PDB 文件）
  psw             隐含 -A6（PyMOL Show 文件）
  pwg             PyMOL Web GUI

当前生效的 "pymolrc" 文件
''',
        'helptext2': '''
缺陷报告请发送至 https://lists.sourceforge.net/lists/listinfo/pymol-users
''',
    },
    'modules/pmg_qt/volume.py': {
        'VOLUME_HELP': '''
体积面板帮助

--------------------------------------------------
画布鼠标操作（光标下没有控制点时）

  左键点击            添加控制点
  CTRL+左键点击       添加 3 个控制点（等值面）

  CTRL+右键拖动       放大

--------------------------------------------------
光标下有控制点时的鼠标操作

  左键点击            编辑该点颜色
  右键点击            编辑该点数值
  SHIFT+右键点击      编辑该点透明度
  CTRL+左键点击       编辑 3 个点的颜色

  中键点击            删除控制点
  SHIFT+左键点击      删除控制点
  CTRL+中键点击       删除 3 个点
  CTRL+SHIFT+左键点击 删除 3 个点

  左键拖动            移动控制点
  CTRL+左键拖动       移动 3 个点（仅水平方向）
  右键拖动            仅沿单一轴移动控制点

--------------------------------------------------
L = 鼠标左键
M = 鼠标中键
R = 鼠标右键

--------------------------------------------------
另请参阅 "volume_color" 命令，用于在命令行上获取
和设置体积颜色。
''',
    },
}
