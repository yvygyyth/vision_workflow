# vision-bot

基于识图的自动化框架，当前支持「千里单骑」「八王之乱」「每日免费资源」。运行时使用 **Flow / Module** 编排：`children` 顺序执行，失败走 `relocate` 纠偏，模块内 `ctx.goto` / `ctx.call` 跳转。

## 架构

```text
Flow        id, name, children: list[Flow | Module], relocate?
Module      id, name, active(ctx) -> Result
Result      ok / message
RunContext  截图、点击、取消信号、goto/call
jobs.py     任务注册表 + start(job_id)
```

```python
from vision_bot import start

report = start("qian_li_dan_qi", wu_jiang="吕布")
```

新增任务：在 `src/vision_bot/jobs.py` 的 `JOBS` 列表追加一项，UI 下拉会自动出现。

## 目录

```text
data/ming_jiang_sha/<流程id>/     # 模板图（打包后在 exe 旁，可热更）
src/vision_bot/
  runtime/                        # Flow 引擎
  core/                           # 识图、设置、输入
  actions/                        # move / click / compose
  perception/                     # signal / snapshot（snap.found / snap.center）
  apps/ming_jiang_sha/qian_li_dan_qi/
    build.py, signals.py
    flows/                        # 各子 flow（detect / relocate 分文件）
  jobs.py                         # 任务注册
  ui/                             # 桌面界面
scripts/build_exe.py
```

## 桌面 UI

```powershell
pip install -e ".[dev]"
poe ui
# 或
vision-bot ui
python -m vision_bot.ui
```

界面：任务下拉、运行、停止、日志、设置。

## CLI

```powershell
vision-bot run                    # 默认千里单骑
vision-bot run -j qian_li_dan_qi --wu-jiang 吕布
vision-bot version
```

## 打包 exe

```powershell
pip install -e ".[dev]"
poe build
```

产物：`dist/VisionBot/VisionBot.exe`；同级带 `data/` 模板图目录。

## 开发

```powershell
pip install -e ".[dev]"
poe test
poe lint
```
