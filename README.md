# vision-bot

基于识图的自动化框架，当前实现「名将杀 · 千里单骑」。运行时只有 **Flow** 一层：`steps` 里放子 Flow 或步骤函数，失败时走 `routes` / `relocate` 纠偏。

## 架构

```text
Flow        步骤表：id → Flow | StepFn
StepFn      (ctx) -> StepResult（ok / fail + outcome）
RunContext  截图、点击、取消信号
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
  perception/                     # signal / snapshot
  apps/ming_jiang_sha/qian_li_dan_qi/
    build.py, run.py, detect.py, signals.py
    flows/                        # 各子流程
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
