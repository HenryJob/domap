function readJson(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent) : null;
}

// Paleta categórica validada (dataviz): orden fijo, no se cicla.
const CAT = ['#e08a2e', '#2e9e7a', '#2f6fb0', '#c1443f', '#8a5cae', '#8a6d3b'];
const AMBER = '#d98e3f';
const BROWN = '#2e1c12';
const GREEN = '#2e9e7a';
const INK = '#6b5647';
const GRID = 'rgba(46,28,18,0.08)';

// Defaults comunes a todos los charts.
if (window.Chart) {
  Chart.defaults.font.family = "'Poppins', system-ui, sans-serif";
  Chart.defaults.color = INK;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 8;
  Chart.defaults.plugins.legend.labels.boxHeight = 8;
  Chart.defaults.plugins.legend.labels.padding = 14;
  Chart.defaults.maintainAspectRatio = false;
}

function axis(opts) {
  return Object.assign({
    grid: { color: GRID, drawBorder: false },
    ticks: { color: INK },
  }, opts || {});
}

function noChart(canvas, msg) {
  const wrap = canvas.parentElement;
  const p = document.createElement('p');
  p.className = 'text-muted text-center small py-4 mb-0';
  p.textContent = msg || 'Sin datos en este rango.';
  canvas.replaceWith(p);
  return wrap;
}

function hasData(arr) {
  return Array.isArray(arr) && arr.some((v) => Number(v) > 0);
}

document.addEventListener('DOMContentLoaded', () => {
  const visitDates = readJson('data-visit-dates');
  const visitCounts = readJson('data-visit-counts');
  const cartAddTotal = readJson('data-cart-add-total');
  const cartRemoveTotal = readJson('data-cart-remove-total');
  const wishlistAddTotal = readJson('data-wishlist-add-total');
  const funnelLabels = readJson('data-funnel-labels');
  const funnelValues = readJson('data-funnel-values');
  const salesDates = readJson('data-sales-dates');
  const webSales = readJson('data-web-sales');
  const whatsappSales = readJson('data-whatsapp-sales');
  const instagramSales = readJson('data-instagram-sales');
  const combinedSales = readJson('data-combined-sales');
  const sourceLabels = readJson('data-source-labels');
  const sourceValues = readJson('data-source-values');
  const deviceLabels = readJson('data-device-labels');
  const deviceValues = readJson('data-device-values');
  const hourlyCounts = readJson('data-hourly-counts');
  const waClicks = readJson('data-wa-clicks');
  const igClicks = readJson('data-ig-clicks');
  const webRevenue = readJson('data-web-revenue');
  const whatsappRevenue = readJson('data-whatsapp-revenue');
  const instagramRevenue = readJson('data-instagram-revenue');

  // Relleno degradado suave para líneas de área.
  function areaFill(ctx, hex) {
    const g = ctx.createLinearGradient(0, 0, 0, 220);
    g.addColorStop(0, hex + '55');
    g.addColorStop(1, hex + '00');
    return g;
  }

  // --- Visitas en el tiempo (área) ---
  const visitsEl = document.getElementById('chart-visits');
  if (hasData(visitCounts)) {
    new Chart(visitsEl, {
      type: 'line',
      data: {
        labels: visitDates,
        datasets: [{
          label: 'Visitas', data: visitCounts, borderColor: AMBER, tension: 0.35,
          fill: true, backgroundColor: areaFill(visitsEl.getContext('2d'), AMBER),
          pointRadius: 0, pointHoverRadius: 5, borderWidth: 2,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: axis({ beginAtZero: true, ticks: { precision: 0, color: INK } }), x: axis() },
      },
    });
  } else { noChart(visitsEl); }

  // --- Ventas en el tiempo (multi-línea) ---
  const salesEl = document.getElementById('chart-sales');
  if (hasData(combinedSales)) {
    new Chart(salesEl, {
      type: 'line',
      data: {
        labels: salesDates,
        datasets: [
          { label: 'Web', data: webSales, borderColor: AMBER, backgroundColor: AMBER, tension: 0.35, borderWidth: 2, pointRadius: 0, pointHoverRadius: 5 },
          { label: 'WhatsApp', data: whatsappSales, borderColor: GREEN, backgroundColor: GREEN, tension: 0.35, borderWidth: 2, pointRadius: 0, pointHoverRadius: 5 },
          { label: 'Instagram', data: instagramSales, borderColor: '#c1443f', backgroundColor: '#c1443f', tension: 0.35, borderWidth: 2, pointRadius: 0, pointHoverRadius: 5 },
          { label: 'Combinado', data: combinedSales, borderColor: BROWN, backgroundColor: BROWN, tension: 0.35, borderDash: [5, 4], borderWidth: 2, pointRadius: 0, pointHoverRadius: 5 },
        ],
      },
      options: {
        interaction: { mode: 'index', intersect: false },
        scales: { y: axis({ beginAtZero: true }), x: axis() },
      },
    });
  } else { noChart(salesEl); }

  // --- Embudo de conversión (barra horizontal) ---
  const funnelEl = document.getElementById('chart-funnel');
  if (hasData(funnelValues)) {
    new Chart(funnelEl, {
      type: 'bar',
      data: {
        labels: funnelLabels,
        datasets: [{ label: 'Sesiones', data: funnelValues, backgroundColor: AMBER, borderRadius: 4, barPercentage: 0.7 }],
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: { x: axis({ beginAtZero: true, ticks: { precision: 0, color: INK } }), y: axis({ grid: { display: false } }) },
      },
    });
  } else { noChart(funnelEl); }

  // --- Fuentes de tráfico (dona) ---
  const sourceEl = document.getElementById('chart-sources');
  if (hasData(sourceValues)) {
    new Chart(sourceEl, {
      type: 'doughnut',
      data: { labels: sourceLabels, datasets: [{ data: sourceValues, backgroundColor: CAT, borderColor: '#fff', borderWidth: 2 }] },
      options: { cutout: '60%', plugins: { legend: { position: 'right' } } },
    });
  } else { noChart(sourceEl); }

  // --- Dispositivos (dona) ---
  const deviceEl = document.getElementById('chart-devices');
  if (hasData(deviceValues)) {
    new Chart(deviceEl, {
      type: 'doughnut',
      data: { labels: deviceLabels, datasets: [{ data: deviceValues, backgroundColor: CAT, borderColor: '#fff', borderWidth: 2 }] },
      options: { cutout: '60%', plugins: { legend: { position: 'right' } } },
    });
  } else { noChart(deviceEl); }

  // --- Actividad por hora del día (barra) ---
  const hourEl = document.getElementById('chart-hours');
  if (hasData(hourlyCounts)) {
    new Chart(hourEl, {
      type: 'bar',
      data: {
        labels: Array.from({ length: 24 }, (_, h) => String(h).padStart(2, '0')),
        datasets: [{ label: 'Visitas', data: hourlyCounts, backgroundColor: AMBER, borderRadius: 3, barPercentage: 0.8, categoryPercentage: 0.9 }],
      },
      options: {
        plugins: { legend: { display: false }, tooltip: { callbacks: { title: (i) => i[0].label + ':00 h' } } },
        scales: { y: axis({ beginAtZero: true, ticks: { precision: 0, color: INK } }), x: axis({ grid: { display: false } }) },
      },
    });
  } else { noChart(hourEl); }

  // --- Canal preferido: WhatsApp vs Instagram (dona) ---
  const channelEl = document.getElementById('chart-channel');
  if (hasData([waClicks, igClicks])) {
    new Chart(channelEl, {
      type: 'doughnut',
      data: {
        labels: ['WhatsApp', 'Instagram'],
        datasets: [{ data: [waClicks, igClicks], backgroundColor: [GREEN, '#c1443f'], borderColor: '#fff', borderWidth: 2 }],
      },
      options: { cutout: '60%', plugins: { legend: { position: 'right' } } },
    });
  } else { noChart(channelEl); }

  // --- Carrito: agregados vs quitados vs favoritos (barra) ---
  const cartEl = document.getElementById('chart-cart-wishlist');
  if (hasData([cartAddTotal, cartRemoveTotal, wishlistAddTotal])) {
    new Chart(cartEl, {
      type: 'bar',
      data: {
        labels: ['Agregados', 'Quitados', 'Favoritos'],
        datasets: [{ label: 'Eventos', data: [cartAddTotal, cartRemoveTotal, wishlistAddTotal], backgroundColor: [AMBER, '#c1443f', '#8a5cae'], borderRadius: 4, barPercentage: 0.6 }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: axis({ beginAtZero: true, ticks: { precision: 0, color: INK } }), x: axis({ grid: { display: false } }) },
      },
    });
  } else { noChart(cartEl); }

  // --- Ingresos por canal (dona) ---
  const revenueEl = document.getElementById('chart-revenue');
  if (revenueEl && hasData([webRevenue, whatsappRevenue, instagramRevenue])) {
    new Chart(revenueEl, {
      type: 'doughnut',
      data: {
        labels: ['Web', 'WhatsApp', 'Instagram'],
        datasets: [{ data: [webRevenue, whatsappRevenue, instagramRevenue], backgroundColor: [AMBER, GREEN, '#c1443f'], borderColor: '#fff', borderWidth: 2 }],
      },
      options: {
        cutout: '60%',
        plugins: {
          legend: { position: 'right' },
          tooltip: { callbacks: { label: (c) => c.label + ': S/ ' + Number(c.raw).toFixed(2) } },
        },
      },
    });
  } else if (revenueEl) { noChart(revenueEl); }
});
