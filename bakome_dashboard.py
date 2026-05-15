#!/usr/bin/env python3
"""
BAKOME AI Terminal - Dashboard Web
Affiche DOM, Footprint & Scanner en temps réel
Pour attirer les sponsors et investisseurs
"""

import http.server
import json
import os
import time
import threading
import webbrowser
from datetime import datetime

# ============ CONFIGURATION ============
PORT = 8080
DATA_FILE = "BAKOME_LiveData.json"
REFRESH_INTERVAL = 2  # secondes

# ============ DONNÉES LIVE ============
live_data = {
    "symbol": "XAUUSD",
    "bid": 0,
    "ask": 0,
    "dom_imbalance": 0,
    "footprint_delta": 0,
    "signals": [],
    "balance": 10000,
    "equity": 10250,
    "profit": 250
}

# ============ HTML DASHBOARD ============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BAKOME AI Terminal - Live Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e); 
            color: #00ff88; 
            font-family: 'Courier New', monospace;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            text-align: center; 
            padding: 30px; 
            border: 2px solid #00ff88;
            border-radius: 15px;
            margin-bottom: 30px;
            background: rgba(0,255,136,0.05);
        }
        .header h1 { font-size: 2.5em; color: #00ff88; text-shadow: 0 0 20px rgba(0,255,136,0.5); }
        .header p { color: #888; margin-top: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: rgba(0,0,0,0.5);
            border: 1px solid #00ff8844;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s;
        }
        .card:hover { border-color: #00ff88; box-shadow: 0 0 30px rgba(0,255,136,0.2); }
        .card h2 { 
            color: #00ff88; 
            margin-bottom: 15px; 
            font-size: 1.3em;
            border-bottom: 1px solid #00ff8833;
            padding-bottom: 10px;
        }
        .value { font-size: 2em; color: #fff; margin: 10px 0; }
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .neutral { color: #ffaa00; }
        .progress-bar {
            height: 20px;
            background: #1a1a2e;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00cc66);
            transition: width 0.5s;
        }
        .sponsor-btn {
            display: block;
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            background: linear-gradient(135deg, #00ff88, #00cc66);
            color: #000;
            border: none;
            border-radius: 8px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            text-align: center;
        }
        .sponsor-btn:hover { 
            transform: scale(1.05); 
            box-shadow: 0 0 40px rgba(0,255,136,0.5);
        }
        .wallet { 
            background: rgba(0,0,0,0.7); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 10px 0;
            font-size: 0.8em;
            word-break: break-all;
        }
        .scanner-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            border-bottom: 1px solid #00ff8822;
        }
        .blink { animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
        .footer { 
            text-align: center; 
            margin-top: 40px; 
            padding: 20px;
            color: #888;
            border-top: 1px solid #00ff8833;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 BAKOME AI Terminal v3.0</h1>
            <p>Live DOM | Footprint Charts | Multi-Pair Scanner</p>
            <p class="blink">● EN DIRECT ●</p>
        </div>
        
        <div class="grid">
            <!-- DOM Card -->
            <div class="card">
                <h2>📊 Depth of Market</h2>
                <div id="dom-chart" style="height: 200px;"></div>
                <p>Déséquilibre: <span id="dom-imbalance" class="value">0%</span></p>
                <div class="progress-bar">
                    <div id="dom-bar" class="progress-fill" style="width: 50%;"></div>
                </div>
            </div>
            
            <!-- Footprint Card -->
            <div class="card">
                <h2>👣 Footprint Delta</h2>
                <div id="fp-chart" style="height: 200px;"></div>
                <p>Delta: <span id="fp-delta" class="value">0</span></p>
                <p>Biais: <span id="fp-bias" class="value neutral">Neutre</span></p>
            </div>
            
            <!-- Scanner Card -->
            <div class="card">
                <h2>🔍 Scanner Multi-Paires</h2>
                <div id="scanner-results">
                    <div class="scanner-item">
                        <span>XAUUSD</span>
                        <span class="positive">BUY 87%</span>
                    </div>
                </div>
            </div>
            
            <!-- Account Card -->
            <div class="card">
                <h2>💼 Compte</h2>
                <p>Balance: <span id="balance" class="value">$10,000</span></p>
                <p>Equity: <span id="equity" class="value">$10,250</span></p>
                <p>Profit: <span id="profit" class="value positive">+$250</span></p>
            </div>
            
            <!-- Sponsors Card -->
            <div class="card" style="grid-column: span 2;">
                <h2>💎 Devenir Sponsor / Soutenir le Projet</h2>
                <p style="color: #ccc; margin-bottom: 15px;">
                    Développé entièrement sur un Pixel 4a 5G, sans ordinateur ni Wi-Fi fixe.
                    Votre soutien finance les licences, les données de marché et l'infrastructure.
                </p>
                <div class="wallet">BTC: bc1qhtjp3qpqru4vuqd355dfcn46mqjrlpdfmngk6u0</div>
                <div class="wallet">ETH: 0x2fD73626714d9e37EA464109F8eCeA2CA5401062</div>
                <div class="wallet">SOL: 3CfhghA7hSNPBbd1RME5rRDm5UUeesTq9NKTcyzZdkz4</div>
                <div class="wallet">USDT: THkLdiKsmscJFwBPA4tpWeAn1xVw7DTKxq</div>
                <a href="https://app.drips.network/projects/BAKOME-Hub/BAKOME_Ultimate_Telegram_Bot" 
                   class="sponsor-btn" target="_blank">
                    🤝 Sponsoriser via Drips
                </a>
            </div>
        </div>
        
        <div class="footer">
            <p>📍 Goma, RDC | 👤 BAKOME | 🌐 github.com/BAKOME-Hub</p>
            <p>Construit sur un téléphone. Propulsé par la passion. 🚀</p>
        </div>
    </div>
    
    <script>
        // Mise à jour automatique
        setInterval(function() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(err => console.log('Attente données...'));
        }, 2000);
        
        function updateDashboard(data) {
            // DOM
            document.getElementById('dom-imbalance').textContent = 
                (data.dom_imbalance*100).toFixed(1) + '%';
            let domBar = document.getElementById('dom-bar');
            domBar.style.width = ((data.dom_imbalance+1)/2*100).toFixed(0) + '%';
            
            // Footprint
            document.getElementById('fp-delta').textContent = 
                data.footprint_delta.toFixed(0);
            
            // Compte
            document.getElementById('balance').textContent = 
                '$' + data.balance.toLocaleString();
            document.getElementById('equity').textContent = 
                '$' + data.equity.toLocaleString();
            document.getElementById('profit').textContent = 
                (data.profit >= 0 ? '+' : '') + '$' + data.profit.toLocaleString();
        }
    </script>
</body>
</html>
"""

# ============ SERVEUR HTTP ============
class BAKOMEDashboard(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        
        elif self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(live_data).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()

def read_mql5_data():
    """Lit les données exportées par l'EA MQL5"""
    global live_data
    while True:
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    live_data.update(data)
        except:
            pass
        time.sleep(1)

def start_server():
    """Démarre le serveur web"""
    server = http.server.HTTPServer(('0.0.0.0', PORT), BAKOMEDashboard)
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🚀 BAKOME AI Terminal v3.0                            ║
║   Dashboard Live: http://localhost:{PORT}                  ║
║                                                          ║
║   📊 DOM | 👣 Footprint | 🔍 Scanner | 💰 Support       ║
║                                                          ║
║   👤 BAKOME - Goma, RDC                                 ║
║   📱 Développé sur Pixel 4a 5G                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    server.serve_forever()

# ============ DÉMARRAGE ============
if __name__ == "__main__":
    # Thread pour lire les données MQL5
    data_thread = threading.Thread(target=read_mql5_data, daemon=True)
    data_thread.start()
    
    # Serveur web
    start_server()
