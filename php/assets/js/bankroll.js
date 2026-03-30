// php/assets/js/bankroll.js

document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('bankrollDetailChart');
    if (!canvas) return;

    if (typeof bankrollDetailHistory === 'undefined' || bankrollDetailHistory.length === 0) {
        canvas.closest('.chart-wrapper').innerHTML =
            '<p class="text-muted text-center pt-5">Nessun dato disponibile.</p>';
        return;
    }

    const labels = bankrollDetailHistory.map(item => item.giorno);
    const data   = bankrollDetailHistory.map(item => parseFloat(item.bankroll));
    const initLine = typeof bankrollDetailInit !== 'undefined' ? bankrollDetailInit : 1000;

    const lastVal  = data[data.length - 1];
    const isProfit = lastVal >= initLine;
    const color    = isProfit ? '#3fb950' : '#f85149';
    const bgColor  = isProfit ? 'rgba(63, 185, 80, 0.15)' : 'rgba(248, 81, 73, 0.15)';

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Bankroll (€)',
                    data: data,
                    borderColor: color,
                    backgroundColor: bgColor,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: color,
                },
                {
                    label: 'Bankroll Iniziale',
                    data: labels.map(() => initLine),
                    borderColor: '#6c757d',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#c9d1d9' }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => '€' + ctx.parsed.y.toFixed(2)
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8b949e' },
                    grid:  { color: '#21262d' }
                },
                y: {
                    ticks: {
                        color: '#8b949e',
                        callback: val => '€' + val.toFixed(0)
                    },
                    grid: { color: '#21262d' }
                }
            }
        }
    });
});