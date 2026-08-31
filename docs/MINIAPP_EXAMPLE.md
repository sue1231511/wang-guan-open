# MiniApp 接线示例

公开仓库不会提供原私人 MiniApp UI，但会提供完整的调用写法。

`miniapp/miniapp.html` 演示了以下内容：

1. 如何确定网关地址
2. 如何向 `/v1/chat/completions` 发送请求
3. 如何使用 `Authorization: Bearer <API_SECRET>`
4. 如何传入 OpenAI Chat Completions 风格的 `messages`
5. 如何设置 `stream: true`
6. 如何通过 `ReadableStream` 读取 SSE 响应
7. 如何解析 `data: {...}` 与 `[DONE]`

## 最小请求

```js
const response = await fetch(`${gateway}/v1/chat/completions`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiSecret}`
  },
  body: JSON.stringify({
    stream: true,
    messages: [
      { role: 'user', content: 'hello' }
    ]
  })
});
```

## CORS

如果 MiniApp 与网关部署在同一个域名下，不需要额外开放 CORS。

如果前端与网关跨域部署，需要在服务端配置：

```env
CORS_ALLOW_ORIGIN=https://your-frontend.example.com
```

不要为了省事直接开放不受限制的跨域访问，尤其不要在未设置 `API_SECRET` 的情况下这样做。

## 安全提醒

浏览器前端里填写的 `API_SECRET` 对使用该页面的人本身是可见的，所以这个示例适合个人管理面板或受控环境。

如果你要做面向多用户的公开前端，不要把服务端长期密钥直接发给浏览器。应该再加一层自己的登录、会话或后端代理。
