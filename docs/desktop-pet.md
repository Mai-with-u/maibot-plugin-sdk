# 控制内置桌宠

需要 SDK 2.17.0+，以及实现桌宠能力的 MaiBot 1.3.16+ Host。桌宠当前仅支持 Windows，用户须先启用主程序配置 `desktop_pet.enabled`。插件不能绕过该开关启动窗口。

按需在清单 `capabilities` 声明 `desktop_pet.status`、`desktop_pet.show`、`desktop_pet.hide`、`desktop_pet.say`、`desktop_pet.set_thinking`。

```python
state = await self.ctx.desktop_pet.status()
if state["ready"]:
    await self.ctx.desktop_pet.show()
    await self.ctx.desktop_pet.set_thinking(True)
    try:
        await self.ctx.desktop_pet.say("任务完成了")
    finally:
        await self.ctx.desktop_pet.set_thinking(False)
```

- `status()`：始终可查询，返回 `enabled/supported/running/ready/visible/error`。
- `show()` / `hide()`：显示/隐藏已就绪的窗口，隐藏不结束进程。
- `say(text)`：显示去掉首尾空白后 1～2000 字符的纯文本气泡，不写聊天记录、学习或记忆，不触发麦麦回复，也不自动显示隐藏的窗口。
- `set_thinking(active)`：必须为布尔值，开启或结束思考动画。正常聊天也会更新动画。

控制操作等待窗口确认后返回与 `status()` 相同的状态结构；未就绪、执行失败、超时或未获授权会抛错，不会悄悄忽略。插件不支持传入 HTML/JavaScript、任意窗口命令或自定义用户身份。

如果要代主人向麦麦发言，请使用 `ctx.internal_chat.send(text)`；它和单纯展示提示气泡不同，发言会进入 `internal / owner` 聊天流并可能触发回复。
