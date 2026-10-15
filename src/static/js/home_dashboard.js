/* Native details retains no-JS access; overlays never move dashboard cards. */
document.addEventListener('keydown', event => {
 if (event.key !== 'Escape') return;
 const details = event.target.closest('.home-dashboard details.home-info[open]');
 if (details) { details.open = false; details.querySelector('summary').focus(); }
});
document.addEventListener('focusout', event => {
 const details = event.target.closest('.home-dashboard details.home-info');
 if (details && !details.contains(event.relatedTarget)) details.open = false;
});
document.addEventListener('click', event => {
 document.querySelectorAll('.home-dashboard details.home-info[open]').forEach(details => {
  if (!details.contains(event.target)) details.open = false;
 });
});
function dashboardJumps() {
 const dashboard = document.querySelector('.home-dashboard');
 const jumps = dashboard?.querySelector('.home-jumps');
 if (jumps) jumps.hidden = dashboard.scrollHeight > innerHeight * 2.2 ? false : true;
}
addEventListener('load', dashboardJumps);
addEventListener('resize', dashboardJumps);
