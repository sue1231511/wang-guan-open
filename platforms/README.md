# Platform adapters

The private deployment connects multiple chat platforms. This public repository keeps the boundary but not the author's personal routing rules, IDs, relationship behavior, private group logic, or platform-specific private prompts.

Recommended split:

```text
platforms/
  telegram.py
  qq.py
  wechat.py

workers/
  telegram_worker.py
  qq_worker.py
  wechat_worker.py
```

A platform adapter should only handle transport: receive events, normalize messages, send replies, reconnect, and expose platform metadata. Business/persona behavior belongs in your own worker/context layer.
