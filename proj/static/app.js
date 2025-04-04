document.addEventListener("DOMContentLoaded", () => {
    // 매수/매도 기록 가져오기
    fetch("/api/trade-history")
        .then(res => res.json())
        .then(data => {
            const tbody = document.querySelector("#trade-history tbody");
            data.forEach(trade => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${trade.type}</td>
                    <td>${new Date(trade.timestamp).toLocaleString()}</td>
                    <td>${Number(trade.price).toLocaleString()} KRW</td>
                    <td>${trade.amount.toFixed(6)} BTC</td>
                `;
                tbody.appendChild(row);
            });
        });

    // 상태 로그 가져오기
    fetch("/api/status-log")
        .then(res => res.json())
        .then(data => {
            const statusDiv = document.getElementById("status-log");
            data.forEach(log => {
                const p = document.createElement("p");
                p.textContent = log;
                statusDiv.appendChild(p);
            });
        });
});
