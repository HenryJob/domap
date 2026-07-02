function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}

function morePostJson(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(body || {}),
  }).then((r) => r.json());
}

function updateCartBadge(count) {
  document.querySelectorAll('.morde-badge').forEach((el) => {
    el.textContent = count;
    el.style.display = count > 0 ? 'flex' : 'none';
  });
  if (count > 0 && !document.querySelector('.morde-badge')) {
    const icon = document.querySelector('.morde-cart-icon');
    if (icon) {
      const badge = document.createElement('span');
      badge.className = 'morde-badge';
      badge.textContent = count;
      icon.appendChild(badge);
    }
  }
}

function addToCart(productId, quantity, extraIds, notes) {
  return morePostJson('/carrito/agregar/', {
    product_id: productId, quantity, extra_ids: extraIds, notes,
  }).then((data) => {
    updateCartBadge(data.cart_count);
    return data;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // --- Selector de favoritos (Menú) ---
  document.querySelectorAll('.js-wishlist-toggle').forEach((btn) => {
    btn.addEventListener('click', () => {
      const productId = btn.dataset.productId;
      morePostJson('/carrito/lista-deseos/alternar/', { product_id: productId }).then((data) => {
        btn.classList.toggle('active', data.in_wishlist);
        btn.textContent = data.in_wishlist ? '♥' : '♡';
      });
    });
  });

  // --- "Pedir": abre el modal para elegir cantidad/extras/notas (Menú) ---
  const modalEl = document.getElementById('addToCartModal');
  const qtyValueEl = document.getElementById('modal-qty-value');
  let pendingProductId = null;
  let modalInstance = null;

  if (modalEl && window.bootstrap) {
    modalInstance = new bootstrap.Modal(modalEl);
  }

  function resetExtraRow(row) {
    row.querySelector('.js-extra-qty-value').textContent = '0';
    row.classList.remove('has-quantity');
  }

  function setExtraRowValue(row, value) {
    const clamped = Math.max(0, value);
    row.querySelector('.js-extra-qty-value').textContent = String(clamped);
    row.classList.toggle('has-quantity', clamped > 0);
  }

  document.querySelectorAll('.js-add-to-cart').forEach((btn) => {
    btn.addEventListener('click', () => {
      pendingProductId = btn.dataset.productId;
      if (modalInstance) {
        qtyValueEl.textContent = '1';
        document.querySelectorAll('.js-extra-row').forEach(resetExtraRow);
        const notesEl = document.getElementById('modal-notes');
        if (notesEl) notesEl.value = '';
        modalInstance.show();
      } else {
        addToCart(pendingProductId, 1, [], '').then(() => {
          const original = btn.textContent;
          btn.textContent = '✓ Agregado';
          setTimeout(() => { btn.textContent = original; }, 1200);
        });
      }
    });
  });

  document.getElementById('modal-qty-increase')?.addEventListener('click', () => {
    qtyValueEl.textContent = String(parseInt(qtyValueEl.textContent, 10) + 1);
  });
  document.getElementById('modal-qty-decrease')?.addEventListener('click', () => {
    const next = parseInt(qtyValueEl.textContent, 10) - 1;
    qtyValueEl.textContent = String(Math.max(1, next));
  });

  document.querySelectorAll('.js-extra-row').forEach((row) => {
    const valueEl = row.querySelector('.js-extra-qty-value');
    row.querySelector('.js-extra-qty-increase')?.addEventListener('click', () => {
      setExtraRowValue(row, parseInt(valueEl.textContent, 10) + 1);
    });
    row.querySelector('.js-extra-qty-decrease')?.addEventListener('click', () => {
      setExtraRowValue(row, parseInt(valueEl.textContent, 10) - 1);
    });
  });

  document.getElementById('modal-confirm-add')?.addEventListener('click', () => {
    const quantity = parseInt(qtyValueEl.textContent, 10);
    const extraIds = [];
    document.querySelectorAll('.js-extra-row').forEach((row) => {
      const extraId = row.dataset.extraId;
      const extraQty = parseInt(row.querySelector('.js-extra-qty-value').textContent, 10);
      for (let i = 0; i < extraQty; i += 1) extraIds.push(extraId);
    });
    const notes = document.getElementById('modal-notes')?.value || '';
    addToCart(pendingProductId, quantity, extraIds, notes).then(() => {
      modalInstance.hide();
    });
  });

  // --- Resumen del pedido (Pedidos): eliminar / cambiar cantidad por línea ---
  // Usa delegación de eventos sobre el contenedor #order-summary (que no se
  // vuelve a crear) en vez de listeners por línea, porque el resumen se
  // refresca por AJAX (no se recarga la página, para no perder lo que el
  // cliente ya escribió en el formulario de al lado).
  const summaryEl = document.getElementById('order-summary');

  function refreshSummary() {
    return fetch('/pedidos/resumen-parcial/').then((r) => r.text()).then((html) => {
      summaryEl.innerHTML = html;
    });
  }

  summaryEl?.addEventListener('click', (event) => {
    const lineEl = event.target.closest('.js-cart-line');
    if (!lineEl) return;
    const lineId = lineEl.dataset.lineId;
    const qtyValueLineEl = lineEl.querySelector('.qty-value');

    if (event.target.closest('.js-line-remove')) {
      morePostJson(`/carrito/eliminar/${lineId}/`, {}).then((data) => {
        updateCartBadge(data.cart_count);
        if (data.cart_count === 0) { location.reload(); } else { refreshSummary(); }
      });
    } else if (event.target.closest('.js-line-qty-increase')) {
      const next = parseInt(qtyValueLineEl.textContent, 10) + 1;
      morePostJson(`/carrito/actualizar/${lineId}/`, { quantity: next }).then((data) => {
        updateCartBadge(data.cart_count);
        refreshSummary();
      });
    } else if (event.target.closest('.js-line-qty-decrease')) {
      const next = parseInt(qtyValueLineEl.textContent, 10) - 1;
      morePostJson(`/carrito/actualizar/${lineId}/`, { quantity: next }).then((data) => {
        updateCartBadge(data.cart_count);
        if (data.cart_count === 0) { location.reload(); } else { refreshSummary(); }
      });
    }
  });
});
