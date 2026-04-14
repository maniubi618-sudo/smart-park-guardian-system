const express = require('express');
const https = require('https');
const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const HTTPS_PORT = 3443;
const HTTP_PORT  = 3080;

const app = express();

// ── HTTP → HTTPS 重定向（仅 HTTP 端口，重定向到 HTTPS） ──
app.use((req, res, next) => {
  // 跳过已转换的请求
  if (req.headers['x-forwarded-proto'] === 'https') return next();
  if (req.socket.encrypted) return next();
  // 来自同局域网 HTTP 的请求不过滤（PC 直接用 HTTP 访问）
  next();
});

app.use(express.static(__dirname));
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));

// ── 状态 ──
let phoneConnected = false;
let phoneMeta = {};
let viewerCount = 0;
let wss = null;

// ── WebSocket 处理 ──
function setupWSS(server) {
  wss = new WebSocket.Server({ server });

  wss.on('connection', (ws, req) => {
    const url     = req.url;
    const clientIP = req.socket.remoteAddress;
    const isPhone  = url.startsWith('/phone');

    console.log(`[WS] 连接: ${clientIP} -> ${url} (isPhone=${isPhone})`);

    if (isPhone) {
      // ── 手机端推流 ──
      phoneConnected = true;

      ws.on('message', (data) => {
        try {
          if (typeof data === 'string') {
            const msg = JSON.parse(data);
            if (msg.type === 'meta') {
              phoneMeta = msg.data || {};
              console.log('[📱] 手机元数据:', JSON.stringify(phoneMeta));
            }
          }
          // 转发给所有观看端
          wss.clients.forEach(client => {
            if (client !== ws && client.readyState === WebSocket.OPEN && client._isViewer) {
              client.send(data);
            }
          });
        } catch (e) {
          // 二进制帧 → 直接转发
          wss.clients.forEach(client => {
            if (client !== ws && client.readyState === WebSocket.OPEN && client._isViewer) {
              client.send(data);
            }
          });
        }
      });

      ws.on('close', () => {
        phoneConnected = false;
        phoneMeta = {};
        console.log('[📱] 手机断开');
      });

    } else {
      // ── PC 观看端 ──
      ws._isViewer = true;
      viewerCount++;
      console.log(`[💻] 观众加入 (${viewerCount}人)`);

      ws.on('close', () => {
        viewerCount = Math.max(0, viewerCount - 1);
        console.log(`[💻] 观众离开 (${viewerCount}人)`);
      });
    }
  });
}

// ── API ──
app.get('/api/status', (req, res) => {
  res.json({ phoneConnected, phoneMeta, viewerCount });
});

// ── 启动 ──
const localIP = (() => {
  const nets = require('os').networkInterfaces();
  for (const name of Object.keys(nets))
    for (const net of nets[name])
      if (net.family === 'IPv4' && !net.internal) return net.address;
  return '127.0.0.1';
})();

// 读取证书
const httpsOptions = {
  key:  fs.readFileSync(path.join(__dirname, 'server.key')),
  cert: fs.readFileSync(path.join(__dirname, 'server.crt')),
};

// HTTPS 服务器（手机 + PC）
const httpsServer = https.createServer(httpsOptions, app);
setupWSS(httpsServer);
httpsServer.listen(HTTPS_PORT, '0.0.0.0', () => {
  console.log('\n========================================');
  console.log('  📷 摄像头流服务已启动 (HTTPS)');
  console.log('========================================');
  console.log('');
  console.log(`  💻 PC端监控页面:`);
  console.log(`     https://localhost:${HTTPS_PORT}`);
  console.log('');
  console.log(`  📱 手机端连接地址:`);
  console.log(`     https://${localIP}:${HTTPS_PORT}/phone.html`);
  console.log('');
  console.log('  ⚠️  首次访问需信任自签名证书');
  console.log('     浏览器提示"不安全" → 点击"继续前往"');
  console.log('========================================\n');
});
