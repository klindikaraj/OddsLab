// php/assets/js/valuebets.js

document.addEventListener('DOMContentLoaded', function () {
    const modal       = document.getElementById('betModal');
    const bsModal     = modal ? new bootstrap.Modal(modal) : null;
    let currentVbId   = 0;
    let currentStake  = 0;

    // ===== Bottoni "Piazza scommessa" =====
    document.querySelectorAll('.btn-place-bet').forEach(btn => {
        btn.addEventListener('click', function () {
            currentVbId  = parseInt(this.dataset.vbId);
            currentStake = parseFloat(this.dataset.stake);

            document.getElementById('betMatchInfo').textContent  = this.dataset.match;
            document.getElementById('betEsito').textContent      = this.dataset.esito;
            document.getElementById('betQuota').textContent       = this.dataset.quota;
            document.getElementById('betAmount').value            = currentStake.toFixed(2);
            document.getElementById('betKellySuggest').textContent = currentStake.toFixed(2);

            if (bsModal) bsModal.show();
        });
    });

    // ===== Conferma scommessa =====
    const confirmBtn = document.getElementById('btnConfirmBet');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function () {
            const importo = parseFloat(document.getElementById('betAmount').value);

            if (isNaN(importo) || importo <= 0) {
                alert('Inserisci un importo valido');
                return;
            }

            confirmBtn.disabled  = true;
            confirmBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Invio...';

            try {
                const resp = await fetch('api/place_bet.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        value_bet_id: currentVbId,
                        importo: importo
                    })
                });

                const data = await resp.json();

                if (data.success) {
                    alert(data.message);
                    if (bsModal) bsModal.hide();
                    location.reload();
                } else {
                    alert('Errore: ' + (data.message || data.error));
                }
            } catch (e) {
                alert('Errore di rete: ' + e.message);
            }

            confirmBtn.disabled  = false;
            confirmBtn.innerHTML = '<i class="bi bi-check-lg"></i> Conferma';
        });
    }
});