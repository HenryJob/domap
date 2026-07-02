(function () {
  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  const pageviewId = window.MORDE_PAGEVIEW_ID;
  if (!pageviewId) return;

  const pageEnterTime = Date.now();
  let beaconSent = false;

  function sendDurationBeacon() {
    if (beaconSent) return;
    beaconSent = true;

    const durationSeconds = Math.round((Date.now() - pageEnterTime) / 1000);
    const formData = new FormData();
    formData.append('pageview_id', pageviewId);
    formData.append('duration', durationSeconds);
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    navigator.sendBeacon('/analytics/beacon/duracion/', formData);
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') sendDurationBeacon();
  });
  window.addEventListener('pagehide', sendDurationBeacon);

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.js-whatsapp-cta').forEach((link) => {
      link.addEventListener('click', () => {
        fetch('/analytics/evento/whatsapp-click/', {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
          keepalive: true,
        });
      });
    });
  });
})();
