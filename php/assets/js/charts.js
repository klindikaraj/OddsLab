// php/assets/js/charts.js

document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('bankrollChart');
    if (!canvas) return;

    if (typeof bankrollHistory === 'undefined' || bankrollHistory.length === 0) {
        canvas.closest('.chart-wrapper').innerHTML =
            '<p class="text-muted text-center pt-5">Nessun dato disponibile. Piazza la prima scommessa!</p>';
        return;
    }

    const labels = bankrollHistory.map(item => item.giorno);
    const data   = bankrollHistory.map(item => parseFloat(item.bankroll));
    const initLine = typeof bankrollInit !== 'undefined' ? bankrollInit : 1000;

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Bankroll (€)',
                    data: data,
                    borderColor: '#3fb950',
                    backgroundColor: 'rgba(63, 185, 80, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    pointBackgroundColor: '#3fb950',
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