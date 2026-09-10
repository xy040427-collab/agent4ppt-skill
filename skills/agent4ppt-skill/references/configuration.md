# 环境、配置与诊断

## 运行环境

需要 Python 3.10 或以上及 Pillow。已有可用环境就直接执行入口。`setup` 在 `AGENT4PPT_HOME/venv` 中建立独立环境并安装 Pillow，返回具体 Python 路径；后续命令使用这个解释器，`setup` 不会自动改变当前终端的解释器。Windows 下解释器位于 `Scripts/python.exe`，其他平台通常位于 `bin/python`。

安装完整仓库可用 `pip install .` 获得 `agent4ppt` 命令；复制 skill 文件夹则直接运行 `scripts/agent4ppt.py`。两条路径都包含风格资源。PPTX 写入不要求安装 PowerPoint，也不依赖 python-pptx；后者只用于开发验证。

## 配置位置与优先级

个人数据根目录默认为 `~/.agent4ppt`，设置 `AGENT4PPT_HOME` 可以改到指定目录。该目录与 skill 安装位置无关，更新工具不会覆盖个人风格。

| 设置 | 环境变量 | JSON 字段 |
|---|---|---|
| 图片服务密钥 | `OPENAI_API_KEY` | `api_key` |
| API 根地址 | `OPENAI_BASE_URL` | `base_url` |
| 默认图片模型 | `AGENT4PPT_MODEL` | `model` |

进程环境覆盖 `config.json`；单次任务的 `options.model` 覆盖默认模型。`image` 任务中的 `backend` 决定接口协议，不会仅凭域名自动选择 AtlasCloud。没有 `base_url` 时配置默认使用官方 OpenAI API 根地址。

```text
A4P config --base-url https://api.openai.com/v1 --model gpt-image-2
A4P config --base-url https://api.atlascloud.ai/api/v1/model --model openai/gpt-image-2
A4P config --clear-base
```

以上是配置形式，不证明账户具有该模型权限。兼容 API 地址应停在服务商规定的根路径，不要再包含 `images/generations`；适配器会追加端点。

## 密钥处理

可以只在进程环境中设置 `OPENAI_API_KEY`。执行 `config --key-env IMAGE_KEY` 则会读取名为 `IMAGE_KEY` 的变量，并把其值写入本地 `config.json`。后者是明文存储，不是系统凭据保险箱；文件权限设置也不等于加密，尤其不能把 Unix 权限位当作 Windows 完整 ACL 隔离。

不要把密钥写进 brief、提示词、讲稿、仓库或命令示例，也不要要求用户发到聊天。配置命令返回“是否配置”，不返回密钥。CLI 不会读取其他工具的旧配置目录。

## 排错顺序

先 `doctor` 看解释器与 Pillow；再确认选择的后端和任务 JSON；仅在 API 场景下执行 `doctor --check-api`。OpenAI 兼容路径测试 models 端点，成功也不代表有生图权限；AtlasCloud 不自动发计费探测。

认证错误先检查密钥对应服务，404 检查根路径和模型名称，参数错误检查尺寸与格式，限流按服务提示退避。网络断开或轮询超时保留任务标识；不要用反复提交来确认服务状态。运行库缺失时使用已确定的解释器安装依赖，避免装到了另一个 Python。

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/a7a9430e894f792774c8 -->
