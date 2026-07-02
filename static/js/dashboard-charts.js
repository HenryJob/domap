function readJson(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent) : null;
}

document.addEventListener('DOMContentLoaded', () => {
  const visitDates = readJson('data-visit-dates');
  const visitCounts = readJson('data-visit-counts');
  const cartAddTotal = readJson('data-cart-add-total');
  const wishlistAddTotal = readJson('data-wishlist-add-total');
  const funnelLabels = readJson('data-funnel-labels');
  const funnelValues = readJson('data-funnel-values');
  const salesDates = readJson('data-sales-dates');
  const webSales = readJson('data-web-sales');
  const whatsappSales = readJson('data-whatsapp-sales');
  const combinedSales = readJson('data-combined-sales');

  const amber = '#d98e3f';
  const brown = '#2e1c12';

  new Chart(document.getElementById('chart-visits'), {
    type: 'line',
    data: {
      labels: visitDates,
      datasets: [{ label: 'Visitas', data: visitCounts, borderColor: amber, backgroundColor: amber, tension: 0.3 }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });

  new Chart(document.getElementById('chart-cart-wishlist'), {
    type: 'bar',
    data: {
      labels: ['Agregados al carrito', 'Guardados como favorito'],
      datasets: [{ label: 'Eventos', data: [cartAddTotal, wishlistAddTotal], backgroundColor: [amber, brown] }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });

  new Chart(document.getElementById('chart-funnel'), {
    type: 'bar',
    data: {
      labels: funnelLabels,
      datasets: [{ label: 'Sesiones', data: funnelValues, backgroundColor: amber }],
    },
    options: { responsive: true, indexAxis: 'y', plugins: { legend: { display: false } } },
  });

  new Chart(document.getElementById('chart-sales'), {
    type: 'line',
    data: {
      labels: salesDates,
      datasets: [
        { label: 'Web', data: webSales, borderColor: amber, backgroundColor: amber, tension: 0.3 },
        { label: 'WhatsApp', data: whatsappSales, borderColor: brown, backgroundColor: brown, tension: 0.3 },
        { label: 'Combinado', data: combinedSales, borderColor: '#7a9e6e', backgroundColor: '#7a9e6e', tension: 0.3, borderDash: [4, 4] },
      ],
    },
    options: { responsive: true },
  });
});
