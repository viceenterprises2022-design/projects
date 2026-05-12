
const fs = require('fs');
const http = require('http');

const HTML = `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background: #0c0c0c; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
        .terminal { border: 2px solid #333; padding: 20px; background: #000; width: 900px; box-shadow: 0 0 20px rgba(0,255,0,0.1); }
        .header { border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px; color: #fff; }
        .grid { display: grid; grid-template-columns: 1fr; gap: 20px; }
        .panel { border: 1px solid #222; padding: 10px; }
        .panel-title { background: #111; padding: 5px; font-weight: bold; margin-bottom: 10px; border-left: 3px solid #00ff00; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; color: #888; border-bottom: 1px solid #222; padding: 5px; }
        td { padding: 5px; border-bottom: 1px solid #111; }
        .strike { color: #ffff00; font-weight: bold; text-align: center; }
        .ltp { color: #00ffff; }
        .oi { color: #ff00ff; }
        .vol { color: #ffa500; }
        .bar-bg { background: #111; height: 10px; width: 100px; display: inline-block; position: relative; }
        .bar-fill { background: #00ff00; height: 100%; position: absolute; }
        .atm { background: #1a1a00; }
    </style>
</head>
<body>
    <div class="terminal">
        <div class="header">
            BTC-DASHBOARD | 2026-05-12 14:00:01 | SPOT: 64,231.50 | MAX PAIN: 64,000
        </div>
        
        <div class="grid">
            <div class="panel">
                <div class="panel-title">OPTIONS CHAIN (DERIBIT)</div>
                <table>
                    <thead>
                        <tr>
                            <th>CALL LTP</th>
                            <th>CALL OI</th>
                            <th style="text-align:center">STRIKE</th>
                            <th>PUT OI</th>
                            <th>PUT LTP</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td class="ltp">1240.5</td><td class="oi">12.4k</td><td class="strike">63,000</td><td class="oi">5.1k</td><td class="ltp">120.2</td></tr>
                        <tr><td class="ltp">850.2</td><td class="oi">8.2k</td><td class="strike">63,500</td><td class="oi">4.2k</td><td class="ltp">245.5</td></tr>
                        <tr class="atm"><td class="ltp">420.1</td><td class="oi">22.5k</td><td class="strike">64,000</td><td class="oi">18.4k</td><td class="ltp">415.8</td></tr>
                        <tr><td class="ltp">180.5</td><td class="oi">15.1k</td><td class="strike">64,500</td><td class="oi">9.2k</td><td class="ltp">820.1</td></tr>
                        <tr><td class="ltp">45.2</td><td class="oi">6.2k</td><td class="strike">65,000</td><td class="oi">3.1k</td><td class="ltp">1240.5</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="panel">
                <div class="panel-title">LIQUIDATION HEATMAP (BINANCE + BYBIT)</div>
                <table>
                    <thead>
                        <tr>
                            <th>PRICE</th>
                            <th>VOLUME (24H)</th>
                            <th>OI (PERP)</th>
                            <th>DENSITY</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>63,200</td><td class="vol">$1.2M</td><td class="oi">450 BTC</td><td><div class="bar-bg"><div class="bar-fill" style="width: 80%"></div></div></td></tr>
                        <tr><td>63,150</td><td class="vol">$850k</td><td class="oi">320 BTC</td><td><div class="bar-bg"><div class="bar-fill" style="width: 55%"></div></div></td></tr>
                        <tr><td>64,500</td><td class="vol">$720k</td><td class="oi">210 BTC</td><td><div class="bar-bg"><div class="bar-fill" style="width: 45%"></div></div></td></tr>
                        <tr><td>65,100</td><td class="vol">$680k</td><td class="oi">190 BTC</td><td><div class="bar-bg"><div class="bar-fill" style="width: 40%"></div></div></td></tr>
                        <tr><td>62,800</td><td class="vol">$450k</td><td class="oi">150 BTC</td><td><div class="bar-bg"><div class="bar-fill" style="width: 25%"></div></div></td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
`;

http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(HTML);
}).listen(8081);
console.log('Mockup running at http://localhost:8081');
