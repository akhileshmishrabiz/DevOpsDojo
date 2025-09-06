const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 80;

// Backend URL configuration
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';

console.log(`Starting frontend server...`);
console.log(`Backend URL: ${BACKEND_URL}`);
console.log(`Port: ${PORT}`);

// Log all requests for debugging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Proxy API requests to backend
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  logLevel: 'debug',
  onProxyReq: (proxyReq, req, res) => {
    console.log(`Proxying ${req.method} ${req.url} to ${BACKEND_URL}${req.url}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`Received response ${proxyRes.statusCode} for ${req.url}`);
  },
  onError: (err, req, res) => {
    console.error('Proxy error:', err.message);
    console.error('Full error:', err);
    
    // Check if headers were already sent
    if (!res.headersSent) {
      res.status(500).json({
        error: 'Proxy error',
        message: err.message,
        backend: BACKEND_URL
      });
    }
  }
}));

// Health check endpoint
app.get('/health', (req, res) => {
  console.log('Health check requested');
  res.status(200).send('healthy');
});

// Serve static files
app.use(express.static(path.join(__dirname, 'build')));

// Catch all handler - send React app for any other route
app.get('*', (req, res) => {
  console.log(`Serving React app for route: ${req.url}`);
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Express error:', err);
  res.status(500).send('Internal Server Error');
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on http://0.0.0.0:${PORT}`);
  console.log(`API requests will be proxied to: ${BACKEND_URL}`);
});