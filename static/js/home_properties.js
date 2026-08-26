const DEFAULT_IMG = '/static/images/default_property.png';

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

let _allLoadedProperties = [];
let _allImageMap = {};
let _likeCounts = {};
let _userLiked = [];

document.addEventListener('DOMContentLoaded', () => {
  showSkeletons();
  loadProperties();
});

function showSkeletons(count = 6) {
  const container = document.getElementById('propertyShowcase');
  if (!container) return;
  container.innerHTML = Array.from({ length: count }, () => `
    <div class="property-card skeleton-card" aria-hidden="true">
      <div class="skeleton-img"></div>
      <div class="content">
        <div class="skeleton-line" style="width:75%;height:18px;margin-bottom:10px;"></div>
        <div class="skeleton-line" style="width:50%;height:13px;margin-bottom:6px;"></div>
        <div class="skeleton-line" style="width:40%;height:22px;margin-bottom:14px;"></div>
        <div style="display:flex;gap:12px;">
          <div class="skeleton-line" style="width:60px;height:12px;"></div>
          <div class="skeleton-line" style="width:60px;height:12px;"></div>
          <div class="skeleton-line" style="width:60px;height:12px;"></div>
        </div>
      </div>
    </div>
  `).join('');
}

async function loadProperties() {
  try {
    const [propRes, imgRes, likeRes] = await Promise.all([
      fetch('/api/properties'),
      fetch('/api/property_images'),
      fetch('/api/listings/likes'),
    ]);
    if (!propRes.ok) throw new Error('Failed to fetch properties');

    _allLoadedProperties = await propRes.json();
    _allImageMap = imgRes.ok ? await imgRes.json() : {};
    if (likeRes.ok) {
      const likeData = await likeRes.json();
      _likeCounts = likeData.counts || {};
      _userLiked  = likeData.user_liked || [];
    }

    renderPropertiesList(_allLoadedProperties);
  } catch (err) {
    console.error('Failed to load properties:', err);
  }
}


function renderPropertiesList(properties) {
  const container = document.getElementById('propertyShowcase');
  if (!container) return;
  container.innerHTML = '';

  const countSpan = document.getElementById('visibleCount');
  if (countSpan) countSpan.textContent = properties.length;

  if (properties.length === 0) {
    container.innerHTML = `
      <div style="grid-column:1/-1; text-align:center; padding:3rem 1rem; color:#94a3b8;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔍</div>
        <div style="font-size:1.1rem; font-weight:700; color:#fff;">No properties match your filter</div>
        <div style="font-size:0.85rem; margin-top:0.3rem;">Try adjusting your sector, price range or property type filters.</div>
      </div>
    `;
    return;
  }

  properties.forEach(prop => {
    const card = buildCard(prop, _allImageMap);
    container.appendChild(card);
  });
}

/* ── SEARCH & FILTER LOGIC ────────────────────────────────────── */
function applyPropertyFilters() {
  const keyword = (document.getElementById('filterKeyword')?.value || '').toLowerCase().trim();
  const type    = (document.getElementById('filterType')?.value || '').toLowerCase().trim();
  const sector  = (document.getElementById('filterSector')?.value || '').toLowerCase().trim();
  const priceVal= (document.getElementById('filterPrice')?.value || '');

  const filtered = _allLoadedProperties.filter(prop => {
    const title   = (prop.title || '').toLowerCase();
    const address = (prop.address || prop.location || '').toLowerCase();
    const pType   = (prop.property_type || '').toLowerCase();
    const pNum    = Number(prop.price_numeric || 0);

    // Keyword filter
    if (keyword && !title.includes(keyword) && !address.includes(keyword)) return false;

    // Type filter
    if (type && !pType.includes(type)) return false;

    // Sector filter
    if (sector && !address.includes(sector) && !title.includes(sector)) return false;

    // Price filter (in Lakhs/Crores)
    if (priceVal === '100' && pNum > 10000000) return false;          // < 1 Crore
    if (priceVal === '300' && pNum > 30000000) return false;          // < 3 Crore
    if (priceVal === '500' && pNum > 50000000) return false;          // < 5 Crore
    if (priceVal === '500+' && pNum > 0 && pNum < 50000000) return false; // 5+ Crore

    return true;
  });

  renderPropertiesList(filtered);
}

function resetPropertyFilters() {
  const kw = document.getElementById('filterKeyword'); if (kw) kw.value = '';
  const tp = document.getElementById('filterType'); if (tp) tp.value = '';
  const sc = document.getElementById('filterSector'); if (sc) sc.value = '';
  const pr = document.getElementById('filterPrice'); if (pr) pr.value = '';
  renderPropertiesList(_allLoadedProperties);
}

/* ── RICH CARD BUILDER ────────────────────────────────────────── */
function buildCard(prop, imageMap) {
  const card = document.createElement('div');
  card.className = 'property-card';

  // Determine status (For Sale vs For Rent)
  const rawStatus = prop.status || (String(prop.title).toLowerCase().includes('rent') ? 'For Rent' : 'For Sale');
  const isRent = rawStatus.toLowerCase().includes('rent');
  const isUnavailable = rawStatus.toLowerCase().includes('not available') || rawStatus.toLowerCase().includes('sold') || rawStatus.toLowerCase().includes('unavailable');
  const statusLabel = isUnavailable ? 'Not Available' : 'Available';
  const statusClass = isUnavailable ? 'status-unavailable' : (isRent ? 'for-rent' : 'for-sale');
  const listingModeLabel = isRent ? 'For Rent' : 'For Sale';
  const propType = prop.property_type || 'Residential';

  // ── MULTI-IMAGE SLIDER ─────────────────────────────────────────
  const imgWrap = document.createElement('div');
  imgWrap.className = 'img-wrap';
  imgWrap.id = `imgWrap-${prop.id}`;

  // Build images list: stored map value may be array or single string
  let imgList = [];
  const mapVal = imageMap[String(prop.id)];
  if (Array.isArray(mapVal)) {
    imgList = mapVal;
  } else if (typeof mapVal === 'string' && mapVal) {
    imgList = [mapVal];
  }
  if (imgList.length === 0 && prop.image_url) imgList = [prop.image_url];
  if (imgList.length === 0) imgList = [DEFAULT_IMG];

  // Main image element
  const img = document.createElement('img');
  img.src = imgList[0];
  img.alt = prop.title || 'Islamabad Property';
  img.dataset.idx = '0';
  imgWrap.appendChild(img);

  // Prev / Next arrows (only if multiple images)
  if (imgList.length > 1) {
    const btnPrev = document.createElement('button');
    btnPrev.className = 'slider-arrow slider-prev';
    btnPrev.innerHTML = '&#8249;';
    btnPrev.onclick = (e) => { e.stopPropagation(); slideImage(prop.id, imgList, -1); };

    const btnNext = document.createElement('button');
    btnNext.className = 'slider-arrow slider-next';
    btnNext.innerHTML = '&#8250;';
    btnNext.onclick = (e) => { e.stopPropagation(); slideImage(prop.id, imgList, 1); };

    imgWrap.appendChild(btnPrev);
    imgWrap.appendChild(btnNext);

    // Dot indicators
    const dots = document.createElement('div');
    dots.className = 'slider-dots';
    dots.id = `sliderDots-${prop.id}`;
    imgList.forEach((_, di) => {
      const dot = document.createElement('span');
      dot.className = 'slider-dot' + (di === 0 ? ' active' : '');
      dot.onclick = (e) => { e.stopPropagation(); jumpSlide(prop.id, imgList, di); };
      dots.appendChild(dot);
    });
    imgWrap.appendChild(dots);
  }

  // Image count badge (top-left, only if > 1)
  if (imgList.length > 1) {
    const countBadge = document.createElement('div');
    countBadge.className = 'img-count-badge';
    countBadge.id = `imgCountBadge-${prop.id}`;
    countBadge.textContent = `1 / ${imgList.length}`;
    imgWrap.appendChild(countBadge);
  }

  // Status Badge Overlay — professional 2-state: Available / Not Available
  const statusBadge = document.createElement('div');
  statusBadge.className = `status-badge ${statusClass}`;
  statusBadge.textContent = statusLabel;
  imgWrap.appendChild(statusBadge);

  // Listing mode badge (For Sale / For Rent) — separate from availability
  const modeBadge = document.createElement('div');
  modeBadge.className = 'mode-badge';
  modeBadge.textContent = listingModeLabel;
  imgWrap.appendChild(modeBadge);

  // Type Badge Overlay
  const typeBadge = document.createElement('div');
  typeBadge.className = 'type-badge';
  typeBadge.textContent = propType;
  imgWrap.appendChild(typeBadge);

  // Add Photo Button (appends to gallery)
  const uploadBtn = document.createElement('label');
  uploadBtn.title = 'Add photo to gallery';
  uploadBtn.style.cssText = [
    'position:absolute; bottom:8px; right:8px;',
    'background:rgba(0,0,0,.65); color:#fff; border-radius:6px;',
    'padding:4px 9px; font-size:0.72rem; cursor:pointer;',
    'backdrop-filter:blur(4px); font-weight:600; z-index:5;',
  ].join('');
  uploadBtn.textContent = '\u{1F4F7} Add Photo';

  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*';
  fileInput.style.display = 'none';
  fileInput.addEventListener('change', () => handleUpload(prop.id, fileInput));

  uploadBtn.appendChild(fileInput);
  imgWrap.appendChild(uploadBtn);
  card.appendChild(imgWrap);

  // Card Content
  const content = document.createElement('div');
  content.className = 'content';

  const title = document.createElement('div');
  title.className = 'title';
  title.textContent = prop.title || 'Islamabad Property';
  content.appendChild(title);

  const loc = document.createElement('div');
  loc.className = 'location';
  loc.innerHTML = `📍 ${esc(prop.address || prop.location || 'Islamabad')}`;
  content.appendChild(loc);

  // Price & Price-per-sqft
  const rawPrice = prop.price && prop.price !== 'None' ? prop.price : null;
  const numPrice = Number(prop.price_numeric || 0);
  let priceDisplay = rawPrice;
  if (!priceDisplay) {
    if (numPrice >= 10000000) priceDisplay = `PKR ${(numPrice / 10000000).toFixed(1).replace(/\.0$/, '')} Crore`;
    else if (numPrice >= 100000) priceDisplay = `PKR ${(numPrice / 100000).toFixed(0)} Lakh`;
    else if (numPrice > 0) priceDisplay = `PKR ${numPrice.toLocaleString()}`;
    else priceDisplay = 'Contact for Price';
  }
  const priceEl = document.createElement('div');
  priceEl.className = 'price';
  priceEl.textContent = priceDisplay;

  if (prop.price_numeric && prop.area_sqft) {
    const psf = Math.round(prop.price_numeric / prop.area_sqft);
    const psfSpan = document.createElement('span');
    psfSpan.className = 'price-psf';
    psfSpan.textContent = ` (${psf.toLocaleString()} PKR / sqft)`;
    priceEl.appendChild(psfSpan);
  }
  content.appendChild(priceEl);

  // Specs Row (Beds, Baths, Area)
  const specsRow = document.createElement('div');
  specsRow.className = 'specs-row';

  if (prop.beds) {
    specsRow.innerHTML += `<div class="spec-item"><span class="spec-icon">🛏</span> <b>${prop.beds}</b> Beds</div>`;
  }
  if (prop.baths) {
    if (specsRow.children.length) specsRow.innerHTML += '<div class="spec-divider"></div>';
    specsRow.innerHTML += `<div class="spec-item"><span class="spec-icon">🚿</span> <b>${prop.baths}</b> Baths</div>`;
  }
  if (prop.area_sqft) {
    if (specsRow.children.length) specsRow.innerHTML += '<div class="spec-divider"></div>';
    specsRow.innerHTML += `<div class="spec-item"><span class="spec-icon">📐</span> <b>${Number(prop.area_sqft).toLocaleString()}</b> sqft</div>`;
  }
  if (specsRow.children.length) content.appendChild(specsRow);

  // Description
  if (prop.description) {
    const desc = document.createElement('div');
    desc.className = 'description';
    desc.textContent = prop.description;
    content.appendChild(desc);
  }

  // Amenities Tags
  const amenitiesList = prop.amenities || ["100% NOC Verified", "Gated Security", "Prime Location"];
  if (Array.isArray(amenitiesList) && amenitiesList.length) {
    const amenitiesDiv = document.createElement('div');
    amenitiesDiv.className = 'amenities';
    amenitiesList.slice(0, 3).forEach(a => {
      const span = document.createElement('span');
      span.textContent = a;
      amenitiesDiv.appendChild(span);
    });
    content.appendChild(amenitiesDiv);
  }

  // Action Buttons (Details, WhatsApp Direct)
  const actions = document.createElement('div');
  actions.className = 'actions';

  const btnDetails = document.createElement('button');
  btnDetails.className = 'btn-details';
  btnDetails.textContent = 'View Details';
  btnDetails.onclick = () => showPropertyDetailsModal(prop, imageMap);

  const btnWa = document.createElement('button');
  btnWa.className = 'btn-whatsapp';
  btnWa.title = 'Chat on WhatsApp (03165756055)';
  btnWa.innerHTML = '💬';
  const waMsg = encodeURIComponent(`Hello! I am interested in "${prop.title}" (${priceDisplay}) listed on RealEstate AI Platform. Please share virtual tour and NOC details.`);
  btnWa.onclick = () => window.open(`https://wa.me/923165756055?text=${waMsg}`, '_blank');

  actions.appendChild(btnDetails);
  actions.appendChild(btnWa);
  content.appendChild(actions);

  // ── ENGAGEMENT ROW: ❤ Like + 💬 Reviews toggle ───────────────
  const engageRow = document.createElement('div');
  engageRow.className = 'engage-row';

  // Like button
  const likeCount = _likeCounts[prop.id] || 0;
  const isLiked   = _userLiked.includes(prop.id);
  const likeBtn   = document.createElement('button');
  likeBtn.className = 'like-btn' + (isLiked ? ' liked' : '');
  likeBtn.id        = `likeBtn-${prop.id}`;
  likeBtn.innerHTML = `<span class="heart-icon">${isLiked ? '❤️' : '🤍'}</span> <span class="like-count" id="likeCount-${prop.id}">${likeCount}</span>`;
  likeBtn.title     = 'Like this listing';
  likeBtn.onclick   = () => handleToggleLike(prop.id);

  // Reviews toggle button
  const revToggle = document.createElement('button');
  revToggle.className = 'rev-toggle-btn';
  revToggle.id        = `revToggle-${prop.id}`;
  revToggle.innerHTML = `💬 Reviews`;
  revToggle.onclick   = () => toggleReviewPanel(prop.id);

  engageRow.appendChild(likeBtn);
  engageRow.appendChild(revToggle);
  content.appendChild(engageRow);

  // ── ADMIN ACTION BAR (only shown in admin view via body[data-role='admin']) ──
  const adminBar = document.createElement('div');
  adminBar.className = 'admin-action-bar';
  // No inline style — visibility is purely controlled by CSS body[data-role] selector

  const btnToggleAvail = document.createElement('button');
  const isUnavail = (prop.availability || '').toLowerCase() === 'not available';
  btnToggleAvail.className = 'admin-btn admin-btn-avail';
  btnToggleAvail.id = `availBtn-${prop.id}`;
  btnToggleAvail.dataset.available = isUnavail ? 'false' : 'true';
  btnToggleAvail.innerHTML = isUnavail ? '🔴 Not Available' : '🟢 Available';
  btnToggleAvail.title = 'Toggle availability status';
  btnToggleAvail.onclick = () => adminToggleAvailability(prop, btnToggleAvail);

  const btnEditProp = document.createElement('button');
  btnEditProp.className = 'admin-btn admin-btn-edit';
  btnEditProp.innerHTML = '✏️ Edit';
  btnEditProp.title = 'Edit this property';
  btnEditProp.onclick = () => openAdminEditPropertyModal(prop);

  const btnDelProp = document.createElement('button');
  btnDelProp.className = 'admin-btn admin-btn-delete';
  btnDelProp.innerHTML = '🗑 Delete';
  btnDelProp.title = 'Delete this property';
  btnDelProp.onclick = () => adminDeleteProperty(prop.id, card);

  adminBar.appendChild(btnToggleAvail);
  adminBar.appendChild(btnEditProp);
  adminBar.appendChild(btnDelProp);
  content.appendChild(adminBar);
  // Visibility is controlled by CSS: body[data-role='admin'] .admin-action-bar { display: flex; }

  // ── REVIEWS PANEL (hidden by default) ────────────────────────
  const revPanel = document.createElement('div');
  revPanel.className = 'review-panel';
  revPanel.id        = `reviewPanel-${prop.id}`;
  revPanel.style.display = 'none';
  revPanel.innerHTML = `
    <div class="review-list" id="reviewList-${prop.id}">
      <div class="rev-loading">Loading reviews…</div>
    </div>
    <div class="review-form">
      <div class="rev-form-title">✍️ Write a Review</div>
      <input type="text" class="rev-input" id="revName-${prop.id}" placeholder="Your name" maxlength="60" />
      <div class="star-picker" id="starPicker-${prop.id}" data-rating="0">
        ${[1,2,3,4,5].map(n => `<span class="star" data-val="${n}" onclick="setReviewStar('${prop.id}',${n})">☆</span>`).join('')}
      </div>
      <textarea class="rev-textarea" id="revComment-${prop.id}" placeholder="Share your experience with this listing…" rows="2" maxlength="400"></textarea>
      <button class="rev-submit-btn" onclick="submitListingReview('${prop.id}')">Submit Review</button>
      <div class="rev-error" id="revError-${prop.id}" style="display:none;"></div>
    </div>
  `;
  content.appendChild(revPanel);

  card.appendChild(content);
  return card;
}

/* ── LIKE / REVIEW HELPERS ────────────────────────────────────── */

async function handleToggleLike(propertyId) {
  const btn = document.getElementById(`likeBtn-${propertyId}`);
  const countEl = document.getElementById(`likeCount-${propertyId}`);
  if (!btn) return;

  btn.disabled = true;
  try {
    const res  = await fetch('/api/listings/like', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({property_id: propertyId}),
    });
    const data = await res.json();
    if (data.success) {
      const liked = data.liked;
      btn.className = 'like-btn' + (liked ? ' liked' : '');
      btn.querySelector('.heart-icon').textContent = liked ? '❤️' : '🤍';
      countEl.textContent = data.count;
      // Update local state
      if (liked) { _likeCounts[propertyId] = data.count; if (!_userLiked.includes(propertyId)) _userLiked.push(propertyId); }
      else        { _likeCounts[propertyId] = data.count; _userLiked = _userLiked.filter(id => id !== propertyId); }
    }
  } catch(e) { console.error('Like error:', e); }
  btn.disabled = false;
}

async function toggleReviewPanel(propertyId) {
  const panel = document.getElementById(`reviewPanel-${propertyId}`);
  if (!panel) return;

  if (panel.style.display === 'none') {
    panel.style.display = 'block';
    loadListingReviews(propertyId);
  } else {
    panel.style.display = 'none';
  }
}

async function loadListingReviews(propertyId) {
  const listEl = document.getElementById(`reviewList-${propertyId}`);
  if (!listEl) return;
  listEl.innerHTML = '<div class="rev-loading">Loading reviews…</div>';

  try {
    const res  = await fetch(`/api/listings/${propertyId}/reviews`);
    const data = await res.json();
    const reviews = data.reviews || [];

    if (reviews.length === 0) {
      listEl.innerHTML = '<div class="rev-empty">No reviews yet. Be the first!</div>';
      return;
    }

    listEl.innerHTML = reviews.map(r => `
      <div class="rev-item">
        <div class="rev-header">
          <span class="rev-name">${esc(r.reviewer_name)}</span>
          <span class="rev-stars">${'⭐'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</span>
          <span class="rev-date">${(r.created_at||'').slice(0,10)}</span>
        </div>
        <div class="rev-comment">${esc(r.comment)}</div>
      </div>
    `).join('');
  } catch(e) {
    listEl.innerHTML = '<div class="rev-empty">Could not load reviews.</div>';
  }
}

function setReviewStar(propertyId, val) {
  const picker = document.getElementById(`starPicker-${propertyId}`);
  if (!picker) return;
  picker.dataset.rating = val;
  picker.querySelectorAll('.star').forEach((s, i) => {
    s.textContent = i < val ? '⭐' : '☆';
  });
}

async function submitListingReview(propertyId) {
  const name    = (document.getElementById(`revName-${propertyId}`)?.value || '').trim();
  const rating  = parseInt(document.getElementById(`starPicker-${propertyId}`)?.dataset.rating || '0');
  const comment = (document.getElementById(`revComment-${propertyId}`)?.value || '').trim();
  const errEl   = document.getElementById(`revError-${propertyId}`);

  if (errEl) errEl.style.display = 'none';

  if (!name)            { showRevError(propertyId, 'Please enter your name.'); return; }
  if (rating < 1)       { showRevError(propertyId, 'Please select a star rating.'); return; }
  if (comment.length < 5) { showRevError(propertyId, 'Please write at least 5 characters.'); return; }

  const btn = document.querySelector(`#reviewPanel-${propertyId} .rev-submit-btn`);
  if (btn) { btn.disabled = true; btn.textContent = 'Submitting…'; }

  try {
    const res  = await fetch('/api/listings/review', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({property_id: propertyId, reviewer_name: name, rating, comment}),
    });
    const data = await res.json();
    if (data.success) {
      // Clear form
      document.getElementById(`revName-${propertyId}`).value = '';
      document.getElementById(`revComment-${propertyId}`).value = '';
      setReviewStar(propertyId, 0);
      loadListingReviews(propertyId);
    } else {
      showRevError(propertyId, data.error || 'Submission failed.');
    }
  } catch(e) {
    showRevError(propertyId, 'Server error. Try again.');
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Submit Review'; }
}

function showRevError(propertyId, msg) {
  const el = document.getElementById(`revError-${propertyId}`);
  if (el) { el.textContent = msg; el.style.display = 'block'; }
}


/* ── ADMIN CARD ACTIONS ───────────────────────────────────────── */

/** Toggle Available / Not Available on a property card */
async function adminToggleAvailability(prop, btn) {
  const currentlyAvailable = btn.dataset.available === 'true';
  const newAvail = currentlyAvailable ? 'Not Available' : 'Available';

  try {
    const res = await fetch(`/api/admin/edit_property/${prop.id}`, {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ availability: newAvail }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      btn.dataset.available = newAvail === 'Available' ? 'true' : 'false';
      btn.innerHTML = newAvail === 'Available' ? '🟢 Available' : '🔴 Not Available';
      prop.availability = newAvail;
      // Update the status badge on the card image
      const card = btn.closest('.property-card');
      const badge = card?.querySelector('.status-badge');
      if (badge) {
        badge.textContent = newAvail;
        badge.className = 'status-badge ' + (newAvail === 'Available' ? (btn.closest('.property-card')?.querySelector('.mode-badge')?.textContent?.includes('Rent') ? 'for-rent' : 'for-sale') : 'status-unavailable');
      }
    } else {
      alert('Update failed: ' + (data.error || 'Unknown error'));
    }
  } catch(e) {
    alert('Network error. Please try again.');
  }
}

/** Delete a property card (admin only) */
async function adminDeleteProperty(propertyId, cardEl) {
  if (!confirm('Are you sure you want to delete this property listing? This cannot be undone.')) return;

  try {
    const res = await fetch(`/api/admin/delete_property/${propertyId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') {
      // Animate card removal
      if (cardEl) {
        cardEl.style.transition = 'all 0.35s ease';
        cardEl.style.opacity = '0';
        cardEl.style.transform = 'scale(0.92)';
        setTimeout(() => cardEl.remove(), 350);
      }
      // Update loaded properties cache
      _allLoadedProperties = _allLoadedProperties.filter(p => String(p.id) !== String(propertyId));
    } else {
      alert('Delete failed: ' + (data.error || 'Unknown error'));
    }
  } catch(e) {
    alert('Network error. Please try again.');
  }
}

/** Open pre-filled edit modal for an existing property */
function openAdminEditPropertyModal(prop) {
  const oldModal = document.getElementById('adminEditPropModalOverlay');
  if (oldModal) oldModal.remove();

  const currentAvail = prop.availability || 'Available';
  const currentStatus = prop.status || 'For Sale';

  const modal = document.createElement('div');
  modal.id = 'adminEditPropModalOverlay';
  modal.className = 'auth-modal-overlay visible';
  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:680px; max-height:90vh; overflow-y:auto; padding:0; border-radius:24px;">
      <div style="background:linear-gradient(135deg,rgba(245,158,11,0.18),rgba(56,189,248,0.12)); padding:1.6rem 2rem 1.2rem; border-bottom:1px solid rgba(255,255,255,0.08); border-radius:24px 24px 0 0; position:relative;">
        <button class="modal-close" onclick="document.getElementById('adminEditPropModalOverlay').remove()" style="top:16px; right:16px;">✕</button>
        <div style="display:flex; align-items:center; gap:0.8rem;">
          <div style="font-size:1.8rem; background:rgba(245,158,11,0.2); border:1px solid rgba(245,158,11,0.4); width:48px; height:48px; border-radius:50%; display:flex; align-items:center; justify-content:center;">✏️</div>
          <div>
            <div style="font-size:1.1rem; font-weight:800; color:#fff;">Edit Property Listing</div>
            <div style="font-size:0.78rem; color:#94a3b8;">Admin Portal · Modify Listing Details</div>
          </div>
        </div>
      </div>

      <form id="adminEditPropForm" onsubmit="handleAdminEditPropertySubmit(event, '${esc(String(prop.id))}')" style="padding:1.6rem 2rem;">

        <div style="font-size:0.7rem; font-weight:800; color:#f59e0b; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.8rem;">📋 Property Information</div>

        <div class="form-group">
          <label>Property Title *</label>
          <input type="text" name="title" class="form-control" value="${esc(prop.title || '')}" required />
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
          <div class="form-group">
            <label>Property Type</label>
            <select name="property_type" class="form-control">
              ${['Residential Villa','Apartment / Flat','Penthouse','Commercial Office','Residential Plot','Commercial Plot','Upper Portion','Lower Portion']
                .map(t => `<option value="${t}" ${prop.property_type===t?'selected':''}>${t}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label>Listing Status</label>
            <select name="status" class="form-control">
              <option value="For Sale" ${currentStatus==='For Sale'?'selected':''}>🟢 For Sale</option>
              <option value="For Rent" ${currentStatus==='For Rent'?'selected':''}>🔵 For Rent</option>
            </select>
          </div>
        </div>

        <div class="form-group" style="margin-bottom:1rem;">
          <label style="font-weight:700; color:#f59e0b;">🏷️ Availability Status *</label>
          <div style="display:flex; gap:0.8rem; margin-top:0.4rem;">
            <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer; padding:0.6rem 1rem; border:2px solid ${currentAvail==='Available'?'rgba(16,185,129,0.6)':'rgba(255,255,255,0.1)'}; border-radius:10px; background:${currentAvail==='Available'?'rgba(16,185,129,0.12)':'rgba(255,255,255,0.03)'}; flex:1; transition:all 0.2s;" id="availLabelYes">
              <input type="radio" name="availability" value="Available" ${currentAvail==='Available'?'checked':''} style="accent-color:#10b981;" onchange="updateAvailStyle()" />
              <span style="font-weight:700; color:#10b981;">🟢 Available</span>
            </label>
            <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer; padding:0.6rem 1rem; border:2px solid ${currentAvail==='Not Available'?'rgba(100,100,120,0.6)':'rgba(255,255,255,0.1)'}; border-radius:10px; background:${currentAvail==='Not Available'?'rgba(100,100,120,0.15)':'rgba(255,255,255,0.03)'}; flex:1; transition:all 0.2s;" id="availLabelNo">
              <input type="radio" name="availability" value="Not Available" ${currentAvail==='Not Available'?'checked':''} style="accent-color:#6b7280;" onchange="updateAvailStyle()" />
              <span style="font-weight:700; color:#94a3b8;">🔴 Not Available</span>
            </label>
          </div>
        </div>

        <div style="font-size:0.7rem; font-weight:800; color:#f59e0b; text-transform:uppercase; letter-spacing:1px; margin:1rem 0 0.8rem;">💰 Pricing</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
          <div class="form-group">
            <label>Price in PKR (numerals)</label>
            <input type="number" name="price_numeric" class="form-control" value="${prop.price_numeric || ''}" min="0" />
          </div>
          <div class="form-group">
            <label>Display Price</label>
            <input type="text" name="price" class="form-control" value="${esc(prop.price || '')}" placeholder="PKR 4.5 Crore" />
          </div>
        </div>

        <div style="font-size:0.7rem; font-weight:800; color:#f59e0b; text-transform:uppercase; letter-spacing:1px; margin:1rem 0 0.8rem;">📐 Specifications</div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.8rem;">
          <div class="form-group">
            <label>🛏 Bedrooms</label>
            <input type="number" name="beds" class="form-control" value="${prop.beds || 0}" min="0" />
          </div>
          <div class="form-group">
            <label>🚿 Bathrooms</label>
            <input type="number" name="baths" class="form-control" value="${prop.baths || 0}" min="0" />
          </div>
          <div class="form-group">
            <label>📐 Area (Sq Ft)</label>
            <input type="number" name="area_sqft" class="form-control" value="${prop.area_sqft || 0}" min="0" />
          </div>
        </div>

        <div class="form-group">
          <label>Description</label>
          <textarea name="description" class="form-control" rows="3">${esc(prop.description || '')}</textarea>
        </div>

        <div id="adminEditPropError" class="auth-error" style="display:none;"></div>

        <div style="display:flex; gap:0.8rem; margin-top:1rem;">
          <button type="button" onclick="document.getElementById('adminEditPropModalOverlay').remove()"
            style="flex:0 0 auto; padding:0.8rem 1.2rem; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); color:#94a3b8; border-radius:12px; font-weight:700; font-size:0.88rem; cursor:pointer;">
            Cancel
          </button>
          <button type="submit" class="btn-auth-submit" style="margin-top:0; flex:1; background:linear-gradient(135deg,#f59e0b,#d97706);">
            ✏️ Save Changes
          </button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

function updateAvailStyle() {
  const yes = document.getElementById('availLabelYes');
  const no  = document.getElementById('availLabelNo');
  const val = document.querySelector('#adminEditPropForm input[name="availability"]:checked')?.value;
  if (yes) {
    yes.style.borderColor = val==='Available' ? 'rgba(16,185,129,0.6)' : 'rgba(255,255,255,0.1)';
    yes.style.background  = val==='Available' ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.03)';
  }
  if (no) {
    no.style.borderColor = val==='Not Available' ? 'rgba(100,100,120,0.6)' : 'rgba(255,255,255,0.1)';
    no.style.background  = val==='Not Available' ? 'rgba(100,100,120,0.15)' : 'rgba(255,255,255,0.03)';
  }
}

async function handleAdminEditPropertySubmit(event, propertyId) {
  event.preventDefault();
  const form   = document.getElementById('adminEditPropForm');
  const errDiv = document.getElementById('adminEditPropError');
  const btn    = form.querySelector('button[type="submit"]');
  if (errDiv) errDiv.style.display = 'none';
  if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

  const fd = new FormData(form);
  const payload = {
    title:         fd.get('title')?.trim(),
    property_type: fd.get('property_type'),
    status:        fd.get('status'),
    availability:  fd.get('availability'),
    price_numeric: parseFloat(fd.get('price_numeric') || 0),
    price:         fd.get('price')?.trim(),
    beds:          parseInt(fd.get('beds') || 0),
    baths:         parseInt(fd.get('baths') || 0),
    area_sqft:     parseFloat(fd.get('area_sqft') || 0),
    description:   fd.get('description')?.trim(),
  };

  if (!payload.title) {
    if (errDiv) { errDiv.textContent = 'Title is required.'; errDiv.style.display = 'block'; }
    if (btn) { btn.disabled = false; btn.textContent = '✏️ Save Changes'; }
    return;
  }

  try {
    const res  = await fetch(`/api/admin/edit_property/${propertyId}`, {
      method:  'PATCH',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.status === 'success') {
      document.getElementById('adminEditPropModalOverlay')?.remove();
      // Refresh listings to show changes
      _invalidateFrontendCache();
      await loadProperties();
    } else {
      if (errDiv) { errDiv.textContent = data.error || 'Save failed.'; errDiv.style.display = 'block'; }
    }
  } catch(e) {
    if (errDiv) { errDiv.textContent = 'Network error. Please try again.'; errDiv.style.display = 'block'; }
  }
  if (btn) { btn.disabled = false; btn.textContent = '✏️ Save Changes'; }
}

function _invalidateFrontendCache() {
  _allLoadedProperties = [];
  _allImageMap = {};
}


/* ── PROPERTY DETAILS MODAL ───────────────────────────────────── */
function showPropertyDetailsModal(prop, imageMap) {
  let old = document.getElementById('propDetailsModalOverlay');
  if (old) old.remove();

  const imgUrl = imageMap[prop.id] || prop.image_url || DEFAULT_IMG;
  const rawPriceModal = prop.price && prop.price !== 'None' ? prop.price : null;
  const numPriceModal = Number(prop.price_numeric || 0);
  let priceDisplay = rawPriceModal;
  if (!priceDisplay) {
    if (numPriceModal >= 10000000) priceDisplay = `PKR ${(numPriceModal / 10000000).toFixed(1).replace(/\.0$/, '')} Crore`;
    else if (numPriceModal >= 100000) priceDisplay = `PKR ${(numPriceModal / 100000).toFixed(0)} Lakh`;
    else if (numPriceModal > 0) priceDisplay = `PKR ${numPriceModal.toLocaleString()}`;
    else priceDisplay = 'Contact for Price';
  }

  const modal = document.createElement('div');
  modal.id = 'propDetailsModalOverlay';
  modal.className = 'auth-modal-overlay visible';
  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:650px; text-align:left;">
      <button class="modal-close" onclick="document.getElementById('propDetailsModalOverlay').remove()">✕</button>
      <img src="${imgUrl}" style="width:100%; height:260px; object-fit:cover; border-radius:14px; margin-bottom:1rem;" />
      
      <div style="font-size:0.75rem; color:#10b981; font-weight:700; text-transform:uppercase;">📍 ${esc(prop.address || 'Islamabad')}</div>
      <h2 style="color:#fff; font-size:1.3rem; margin:0.3rem 0; font-weight:800;">${esc(prop.title)}</h2>
      <div style="font-size:1.4rem; font-weight:800; color:#10b981; margin-bottom:1rem;">${priceDisplay}</div>

      <div style="display:flex; gap:1.5rem; background:rgba(255,255,255,0.05); padding:0.8rem 1.2rem; border-radius:10px; margin-bottom:1rem;">
        <div><b>${prop.beds || 'N/A'}</b> <span style="color:#94a3b8; font-size:0.8rem;">Bedrooms</span></div>
        <div><b>${prop.baths || 'N/A'}</b> <span style="color:#94a3b8; font-size:0.8rem;">Bathrooms</span></div>
        <div><b>${prop.area_sqft ? Number(prop.area_sqft).toLocaleString() : 'N/A'}</b> <span style="color:#94a3b8; font-size:0.8rem;">Sq Ft</span></div>
        <div><b>${esc(prop.property_type || 'Villa')}</b> <span style="color:#94a3b8; font-size:0.8rem;">Type</span></div>
      </div>

      <div style="color:#cbd5e1; font-size:0.9rem; line-height:1.6; margin-bottom:1.2rem;">${esc(prop.description || 'No description provided.')}</div>

      <div style="display:flex; gap:0.8rem;">
        <button class="btn-auth-submit" onclick="window.open('https://wa.me/923165756055','_blank'); document.getElementById('propDetailsModalOverlay').remove();">📞 Contact Now</button>
        <button class="preset-btn client-p" style="padding:0.8rem 1.2rem; font-size:0.9rem;" onclick="window.open('https://wa.me/923165756055', '_blank')">💬 WhatsApp 03165756055</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

async function handleUpload(propertyId, fileInput) {
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('property_id', propertyId);
  formData.append('file', file);

  try {
    const res  = await fetch('/api/upload_image', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.all_images) {
      // Reload properties to rebuild slider with new image
      await loadProperties();
    } else {
      alert('Upload failed: ' + (data.error || 'Unknown error'));
    }
  } catch (err) {
    console.error('Upload error:', err);
    alert('Upload failed. Check console.');
  }
}

/* ── SLIDER HELPERS ─────────────────────────────────────────── */
function slideImage(propId, imgList, direction) {
  const wrap = document.getElementById(`imgWrap-${propId}`);
  if (!wrap) return;
  const img = wrap.querySelector('img');
  if (!img) return;
  let idx = parseInt(img.dataset.idx || '0', 10);
  idx = (idx + direction + imgList.length) % imgList.length;
  img.src = imgList[idx] + '?cache=' + idx;
  img.dataset.idx = String(idx);
  _updateSliderUI(propId, imgList.length, idx);
}

function jumpSlide(propId, imgList, idx) {
  const wrap = document.getElementById(`imgWrap-${propId}`);
  if (!wrap) return;
  const img = wrap.querySelector('img');
  if (!img) return;
  img.src = imgList[idx] + '?cache=' + idx;
  img.dataset.idx = String(idx);
  _updateSliderUI(propId, imgList.length, idx);
}

function _updateSliderUI(propId, total, activeIdx) {
  // Update dots
  const dotsEl = document.getElementById(`sliderDots-${propId}`);
  if (dotsEl) {
    dotsEl.querySelectorAll('.slider-dot').forEach((d, i) => {
      d.classList.toggle('active', i === activeIdx);
    });
  }
  // Update count badge
  const badge = document.getElementById(`imgCountBadge-${propId}`);
  if (badge) badge.textContent = `${activeIdx + 1} / ${total}`;
}

/* ── ADMIN ADD PROPERTY MODAL ───────────────────────────────── */
function openAdminAddPropertyModal() {
  let modal = document.getElementById('adminAddPropModalOverlay');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'adminAddPropModalOverlay';
    modal.className = 'auth-modal-overlay';
    modal.innerHTML = `
      <div class="auth-modal-card" style="max-width:700px; max-height:92vh; overflow-y:auto; padding:0; border-radius:24px;">
        
        <!-- Modal Header -->
        <div style="background:linear-gradient(135deg,rgba(16,185,129,0.18),rgba(56,189,248,0.12)); padding:1.6rem 2rem 1.2rem; border-bottom:1px solid rgba(255,255,255,0.08); border-radius:24px 24px 0 0; position:relative;">
          <button class="modal-close" onclick="closeAdminAddPropertyModal()" style="top:16px; right:16px;">✕</button>
          <div style="display:flex; align-items:center; gap:0.8rem;">
            <div style="font-size:1.8rem; background:rgba(16,185,129,0.2); border:1px solid rgba(16,185,129,0.4); width:48px; height:48px; border-radius:50%; display:flex; align-items:center; justify-content:center;">🏛️</div>
            <div>
              <div style="font-size:1.1rem; font-weight:800; color:#fff;">Add New Property Listing</div>
              <div style="font-size:0.78rem; color:#94a3b8;">Admin Portal · Islamabad Inventory Management</div>
            </div>
          </div>
        </div>

        <!-- Form Body -->
        <form id="adminAddPropForm" onsubmit="handleAdminAddPropertySubmit(event)" enctype="multipart/form-data" style="padding:1.6rem 2rem;">
          
          <!-- SECTION 1: Core Info -->
          <div style="font-size:0.7rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.8rem;">📋 Property Information</div>

          <div class="form-group">
            <label>Property Title *</label>
            <input type="text" name="title" class="form-control" placeholder="e.g. 4-Bed Modern Villa · F-7/2 Islamabad" required />
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
            <div class="form-group">
              <label>Islamabad Sector / Area *</label>
              <select name="sector" class="form-control" required>
                <option value="">— Select Sector —</option>
                <option value="F-6">Sector F-6</option>
                <option value="F-7">Sector F-7</option>
                <option value="F-8">Sector F-8</option>
                <option value="F-10">Sector F-10</option>
                <option value="F-11">Sector F-11</option>
                <option value="E-11">Sector E-11</option>
                <option value="G-9">Sector G-9</option>
                <option value="G-10">Sector G-10</option>
                <option value="G-11">Sector G-11</option>
                <option value="DHA Phase 2">DHA Phase 2</option>
                <option value="DHA Phase 1">DHA Phase 1</option>
                <option value="Bahria Town">Bahria Town Islamabad</option>
                <option value="Blue Area">Blue Area Commercial</option>
                <option value="B-17">B-17 Multi Gardens</option>
                <option value="CDA Sectors">CDA Sectors (Other)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Property Type *</label>
              <select name="property_type" class="form-control">
                <option value="Residential Villa">🏡 Residential Villa</option>
                <option value="Apartment / Flat">🏢 Apartment / Flat</option>
                <option value="Penthouse">🏙️ Penthouse</option>
                <option value="Commercial Office">🏦 Commercial Office</option>
                <option value="Residential Plot">📐 Residential Plot</option>
                <option value="Commercial Plot">🏗️ Commercial Plot</option>
                <option value="Upper Portion">🏠 Upper Portion</option>
                <option value="Lower Portion">🏠 Lower Portion</option>
              </select>
            </div>
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
            <div class="form-group">
              <label>Listing Status</label>
              <select name="status" class="form-control">
                <option value="For Sale">🟢 For Sale</option>
                <option value="For Rent">🔵 For Rent</option>
                <option value="New Listing">⭐ New Listing</option>
              </select>
            </div>
            <div class="form-group">
              <label>Availability *</label>
              <select name="availability" class="form-control">
                <option value="Available" selected>🟢 Available</option>
                <option value="Not Available">🔴 Not Available</option>
              </select>
            </div>
            <div class="form-group">
              <label>Purpose</label>
              <select name="purpose" class="form-control">
                <option value="Ready to Move">Ready to Move</option>
                <option value="Under Construction">Under Construction</option>
                <option value="Investment">Investment Opportunity</option>
              </select>
            </div>
          </div>

          <!-- SECTION 2: Pricing -->
          <div style="font-size:0.7rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:1px; margin:1.2rem 0 0.8rem;">💰 Pricing</div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
            <div class="form-group">
              <label>Price in PKR (numerals) *</label>
              <input type="number" name="price_numeric" class="form-control" placeholder="45000000" min="0"
                oninput="document.getElementById('priceDisplayPreview').value = formatPricePreview(this.value)" required />
            </div>
            <div class="form-group">
              <label>Display Price Text (auto-filled)</label>
              <input type="text" id="priceDisplayPreview" name="price_display" class="form-control" placeholder="PKR 4.5 Crore" />
            </div>
          </div>

          <!-- SECTION 3: Specs -->
          <div style="font-size:0.7rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:1px; margin:1.2rem 0 0.8rem;">📐 Property Specifications</div>

          <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.8rem;">
            <div class="form-group">
              <label>🛏 Bedrooms (Rooms)</label>
              <input type="number" name="beds" class="form-control" value="3" min="0" max="20" />
            </div>
            <div class="form-group">
              <label>🚿 Bathrooms</label>
              <input type="number" name="baths" class="form-control" value="3" min="0" max="20" />
            </div>
            <div class="form-group">
              <label>📐 Area (Sq Ft)</label>
              <input type="number" name="area_sqft" class="form-control" value="2250" min="0" />
            </div>
          </div>

          <!-- SECTION 4: Description -->
          <div style="font-size:0.7rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:1px; margin:1.2rem 0 0.8rem;">📝 Description</div>

          <div class="form-group">
            <label>Property Description &amp; Highlights</label>
            <textarea name="description" class="form-control" rows="3" 
              placeholder="Describe key highlights: marble flooring, gas connection, water availability, nearby schools, parks, metro access, etc."></textarea>
          </div>

          <!-- SECTION 5: Amenities Checkboxes -->
          <div style="font-size:0.7rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:1px; margin:1.2rem 0 0.8rem;">✅ Amenities &amp; Features</div>

          <div id="amenitiesCheckboxGrid" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.5rem; margin-bottom:1rem;">
            ${['Gated Community','24/7 Guard','Backup Generator','Central Gas','Underground Parking','Swimming Pool','Gymnasium',
               'Rooftop Access','Fiber Internet','CCTV Security','School Nearby','Park Facing',
               'Near Metro','100% NOC Verified','Virtual Tour Available','Installment Plan']
              .map(a => `
                <label style="display:flex; align-items:center; gap:0.4rem; cursor:pointer; padding:0.35rem 0.5rem; border:1px solid rgba(255,255,255,0.06); border-radius:8px; background:rgba(255,255,255,0.03); font-size:0.75rem; color:#cbd5e1; transition:all 0.15s ease;"
                  onmouseover="this.style.background='rgba(16,185,129,0.1)'; this.style.borderColor='rgba(16,185,129,0.3)'"
                  onmouseout="if(!this.querySelector('input').checked){this.style.background='rgba(255,255,255,0.03)'; this.style.borderColor='rgba(255,255,255,0.06)'}">
                  <input type="checkbox" name="amenity" value="${a}" style="accent-color:#10b981;" onchange="this.closest('label').style.background=this.checked?'rgba(16,185,129,0.15)':'rgba(255,255,255,0.03)'; this.closest('label').style.borderColor=this.checked?'rgba(16,185,129,0.4)':'rgba(255,255,255,0.06)';" />
                  ${a}
                </label>
              `).join('')}
          </div>

          <!-- SECTION 6: Image Upload with Preview -->
          <div style="font-size:0.7rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:1px; margin:1.2rem 0 0.8rem;">📸 Property Photos (Up to 5)</div>

          <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:0.5rem; margin-bottom:1rem;" id="imgPreviewGrid">
            ${[1,2,3,4,5].map(i => `
              <div class="img-upload-slot" id="imgSlot${i}" onclick="document.getElementById('imgInput${i}').click()"
                style="aspect-ratio:1; border:2px dashed rgba(255,255,255,0.15); border-radius:12px; background:rgba(255,255,255,0.03); 
                  display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; 
                  transition:all 0.2s ease; position:relative; overflow:hidden;"
                onmouseover="this.style.borderColor='rgba(16,185,129,0.5)'; this.style.background='rgba(16,185,129,0.08)'"
                onmouseout="if(!this.querySelector('img')){this.style.borderColor='rgba(255,255,255,0.15)'; this.style.background='rgba(255,255,255,0.03)'}">
                <span style="font-size:1.4rem;">📷</span>
                <span style="font-size:0.65rem; color:#64748b; margin-top:0.2rem;">${i === 1 ? 'Cover Photo' : 'Photo ' + i}</span>
                <input type="file" id="imgInput${i}" name="image_${i}" accept="image/*" style="display:none;" 
                  onchange="previewImgSlot(${i}, this)" />
              </div>
            `).join('')}
          </div>
          <div style="font-size:0.72rem; color:#64748b; margin-bottom:1rem;">📌 First image will be used as the cover photo on the listing card.</div>

          <div id="adminAddPropError" class="auth-error" style="display:none;"></div>
          
          <!-- Submit Row -->
          <div style="display:flex; gap:0.8rem; margin-top:1rem;">
            <button type="button" onclick="closeAdminAddPropertyModal()"
              style="flex:0 0 auto; padding:0.8rem 1.2rem; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); color:#94a3b8; border-radius:12px; font-weight:700; font-size:0.88rem; cursor:pointer;">
              Cancel
            </button>
            <button type="submit" id="adminAddPropSubmitBtn" class="btn-auth-submit" style="margin-top:0; flex:1;">
              🏛️ Publish Property to Islamabad Listings
            </button>
          </div>

        </form>
      </div>
    `;
    document.body.appendChild(modal);
  }
  modal.classList.add('visible');
}

function closeAdminAddPropertyModal() {
  const modal = document.getElementById('adminAddPropModalOverlay');
  if (modal) modal.classList.remove('visible');
}

/* ── IMAGE SLOT PREVIEW ─────────────────────────────────────── */
function previewImgSlot(slotNum, inputEl) {
  const slot = document.getElementById('imgSlot' + slotNum);
  if (!slot || !inputEl.files || !inputEl.files[0]) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    // Remove existing preview if any
    const existingImg = slot.querySelector('img');
    if (existingImg) existingImg.remove();
    slot.querySelector('span:first-of-type').style.display = 'none';
    slot.querySelector('span:last-of-type').style.display = 'none';

    const preview = document.createElement('img');
    preview.src = e.target.result;
    preview.style.cssText = 'position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; border-radius:10px;';

    // Remove button
    const rmBtn = document.createElement('button');
    rmBtn.type = 'button';
    rmBtn.textContent = '✕';
    rmBtn.style.cssText = 'position:absolute; top:4px; right:4px; background:rgba(239,68,68,0.85); color:#fff; border:none; border-radius:50%; width:20px; height:20px; font-size:0.65rem; cursor:pointer; z-index:2; display:flex; align-items:center; justify-content:center;';
    rmBtn.onclick = (ev) => {
      ev.stopPropagation();
      preview.remove(); rmBtn.remove();
      inputEl.value = '';
      slot.querySelector('span:first-of-type').style.display = '';
      slot.querySelector('span:last-of-type').style.display = '';
      slot.style.borderColor = 'rgba(255,255,255,0.15)';
      slot.style.background = 'rgba(255,255,255,0.03)';
    };

    slot.appendChild(preview);
    slot.appendChild(rmBtn);
    slot.style.borderColor = 'rgba(16,185,129,0.5)';
    slot.style.borderStyle = 'solid';
  };
  reader.readAsDataURL(inputEl.files[0]);
}

/* ── PRICE AUTO-FORMAT ──────────────────────────────────────── */
function formatPricePreview(val) {
  const n = parseInt(val, 10);
  if (!n || isNaN(n)) return '';
  if (n >= 10000000) return 'PKR ' + (n / 10000000).toFixed(1).replace(/\.0$/, '') + ' Crore';
  if (n >= 100000)   return 'PKR ' + (n / 100000).toFixed(0) + ' Lakh';
  return 'PKR ' + n.toLocaleString();
}

async function handleAdminAddPropertySubmit(e) {
  e.preventDefault();
  const form = document.getElementById('adminAddPropForm');
  const formData = new FormData(form);
  const errDiv = document.getElementById('adminAddPropError');
  errDiv.style.display = 'none';

  const sector = formData.get('sector');
  if (!sector) {
    errDiv.textContent = 'Please select an Islamabad sector.';
    errDiv.style.display = 'block';
    return;
  }
  formData.set('address', `${sector}, Islamabad`);

  // Collect checked amenities as comma-separated string
  const checkedAmenities = [...form.querySelectorAll('input[name="amenity"]:checked')].map(c => c.value);
  formData.delete('amenity'); // remove individual checkbox fields
  formData.set('amenities_json', JSON.stringify(checkedAmenities));

  try {
    const res = await fetch('/api/admin/add_property', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.status === 'success' && data.property) {
      alert('🎉 Property successfully created in Islamabad inventory!');
      closeAdminAddPropertyModal();
      form.reset();
      loadProperties(); // Reload properties grid
    } else {
      errDiv.textContent = data.error || 'Failed to create property.';
      errDiv.style.display = 'block';
    }
  } catch (err) {
    errDiv.textContent = 'Server error creating property.';
    errDiv.style.display = 'block';
  }
}


