module.exports = {
  apps: [
    {
      name: 'quantedge-btc',
      script: 'paper_trader_api.py',
      args: 'BTCUSDT 15m 5000',
      interpreter: './venv/Scripts/python.exe',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/btc-error.log',
      out_file: './logs/btc-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'quantedge-eth',
      script: 'paper_trader_api.py',
      args: 'ETHUSDT 15m 5001',
      interpreter: './venv/Scripts/python.exe',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/eth-error.log',
      out_file: './logs/eth-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'quantedge-sol',
      script: 'paper_trader_api.py',
      args: 'SOLUSDT 15m 5002',
      interpreter: './venv/Scripts/python.exe',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/sol-error.log',
      out_file: './logs/sol-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};