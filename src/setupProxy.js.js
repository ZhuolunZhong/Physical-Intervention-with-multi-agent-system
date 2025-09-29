const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
    console.log("Proxy middleware loaded");
    app.use(
        '/policy',
        createProxyMiddleware({
            target: 'http://localhost:5000',
            changeOrigin: true,
            logLevel: 'debug',  // 添加这一行来查看详细日志
        })
    );
};
