document.addEventListener("DOMContentLoaded", async function () {
    const response = await fetch("http://localhost:8080/candles"); // FastAPI 서버 호출
    const data = await response.json();

    // timestamps, 가격 데이터 배열 생성
    const timestamps = data.map(item => item.timestamp);
    const closePrices = data.map(item => item.close);

    // Chart.js 차트 생성
    const ctx = document.getElementById("candleChart").getContext("2d");
    new Chart(ctx, {
        type: "line",  // 선 그래프
        data: {
            labels: timestamps,
            datasets: [{
                label: "BTC-KRW 종가",
                data: closePrices,
                borderColor: "blue",
                backgroundColor: "rgba(0, 0, 255, 0.1)",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: "시간 (KST)" } },
                y: { title: { display: true, text: "가격 (KRW)" } }
            }
        }
    });

    // DataTables.js를 이용한 테이블 생성
    const table = $("#candleTable").DataTable();
    data.forEach(item => {
        table.row.add([
            item.timestamp,
            item.market,
            item.open,
            item.high,
            item.low,
            item.close,
            item.volume
        ]).draw(false);
    });
});
