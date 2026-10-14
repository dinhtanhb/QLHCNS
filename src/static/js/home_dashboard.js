/* Keep calculation disclosures usable without a mouse or a floating overlay. */
document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const details = event.target.closest('.home-dashboard details.home-info[open]');
    if (details) {
        details.open = false;
        details.querySelector('summary').focus();
    }
});
