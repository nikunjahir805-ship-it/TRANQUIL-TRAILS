const currentUser = window.djangoUser || 'guest';
const cartKey = `cart_${currentUser}`;
const wishlistKey = `wishlist_${currentUser}`;
const staticPlaceholder = '/static/placeholder.jpg';

function parseStorage(key) {
    try {
        return JSON.parse(localStorage.getItem(key)) || [];
    } catch (error) {
        console.error(`Unable to read ${key}`, error);
        return [];
    }
}

function writeStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function getCsrfToken() {
    const csrfField = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfField) return csrfField.value;

    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='));

    return cookieValue ? cookieValue.split('=')[1] : '';
}

if (currentUser !== 'guest') {
    const guestCart = parseStorage('cart_guest');
    const guestWishlist = parseStorage('wishlist_guest');
    const mergedCart = parseStorage(cartKey);
    const mergedWishlist = parseStorage(wishlistKey);

    guestCart.forEach((guestItem) => {
        const item = mergedCart.find((entry) => entry.id === guestItem.id || entry.name === guestItem.name);
        if (item) item.quantity += guestItem.quantity || 1;
        else mergedCart.push(guestItem);
    });

    guestWishlist.forEach((guestItem) => {
        const exists = mergedWishlist.some((entry) => entry.id === guestItem.id || entry.name === guestItem.name);
        if (!exists) mergedWishlist.push(guestItem);
    });

    writeStorage(cartKey, mergedCart);
    writeStorage(wishlistKey, mergedWishlist);
    localStorage.removeItem('cart_guest');
    localStorage.removeItem('wishlist_guest');
}

let cart = parseStorage(cartKey);
let wishlist = parseStorage(wishlistKey);

function initToastContainer() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info', duration = 2500) {
    initToastContainer();
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 280);
    }, duration);
}

function normalizeImagePath(path) {
    if (!path) return staticPlaceholder;
    if (path.startsWith('http') || path.startsWith('/media/') || path.startsWith('/static/')) return path;
    return `/media/${path.replace(/^\/+/, '')}`;
}

function sanitizeName(name) {
    return String(name).replace(/'/g, "\\'");
}

function addToCart(id, name, price, img) {
    const numericPrice = parseFloat(price) || 0;
    const existingItem = cart.find((item) => String(item.id) === String(id) || item.name === name);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id,
            name,
            price: numericPrice,
            img: normalizeImagePath(img),
            quantity: 1,
        });
    }

    persistCart();
    openCartSidebar();
    showToast(`${name} added to cart`, 'success');
}

function updateQuantity(name, change) {
    const item = cart.find((entry) => entry.name === name);
    if (!item) return;

    item.quantity += change;
    if (item.quantity <= 0) {
        cart = cart.filter((entry) => entry.name !== name);
    }

    persistCart();
}

function removeFromCart(name) {
    cart = cart.filter((item) => item.name !== name);
    persistCart();
    showToast(`${name} removed from cart`, 'warning');
}

function clearCart() {
    if (!cart.length) return;
    if (confirm('Empty your cart?')) {
        cart = [];
        persistCart();
        showToast('Cart cleared', 'warning');
    }
}

function getCartMetrics() {
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) || 0) * item.quantity, 0);
    const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    return { subtotal, itemCount };
}

function renderCartSidebar() {
    const list = document.getElementById('cart-items-list');
    const totalEl = document.getElementById('total-price');
    const countEl = document.getElementById('cart-count');
    const { subtotal, itemCount } = getCartMetrics();

    if (countEl) countEl.textContent = itemCount;
    if (totalEl) totalEl.textContent = subtotal.toFixed(2);
    if (!list) return;

    list.innerHTML = '';

    if (!cart.length) {
        list.innerHTML = `
            <li class="cart-item cart-empty-state">
                <div class="cart-item-info">
                    <h4>Your bag is waiting</h4>
                    <p>Add handcrafted pieces and they will appear here.</p>
                </div>
            </li>
        `;
        return;
    }

    cart.forEach((item) => {
        const safeName = sanitizeName(item.name);
        const li = document.createElement('li');
        li.className = 'cart-item';
        li.innerHTML = `
            <img src="${normalizeImagePath(item.img)}" alt="${item.name}" onerror="this.src='${staticPlaceholder}'">
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <p class="item-price">Rs. ${(parseFloat(item.price) || 0).toFixed(2)}</p>
                <div class="qty-controls">
                    <button class="qty-btn" onclick="updateQuantity('${safeName}', -1)">-</button>
                    <span class="qty-val">${item.quantity}</span>
                    <button class="qty-btn" onclick="updateQuantity('${safeName}', 1)">+</button>
                </div>
            </div>
            <button class="remove-item" onclick="removeFromCart('${safeName}')">&times;</button>
        `;
        list.appendChild(li);
    });
}

function renderCartPage() {
    const page = document.getElementById('cart-page-root');
    if (!page) return;

    const taxRate = parseFloat(page.dataset.taxRate || '0');
    const shippingRate = parseFloat(page.dataset.shippingRate || '0');
    const { subtotal, itemCount } = getCartMetrics();
    const shipping = itemCount ? shippingRate : 0;
    const tax = subtotal * (taxRate / 100);
    const grandTotal = subtotal + shipping + tax;

    const itemsMarkup = cart.length ? cart.map((item) => {
        const safeName = sanitizeName(item.name);
        const unitPrice = parseFloat(item.price) || 0;
        const lineTotal = unitPrice * item.quantity;

        return `
            <article class="cart-line-item">
                <div class="cart-line-media">
                    <img src="${normalizeImagePath(item.img)}" alt="${item.name}" onerror="this.src='${staticPlaceholder}'">
                </div>
                <div class="cart-line-content">
                    <div class="cart-line-top">
                        <div>
                            <span class="cart-line-label">Artisan Product</span>
                            <h3>${item.name}</h3>
                            <p>Carefully selected for the Tranquil Trails collection.</p>
                        </div>
                        <button class="cart-line-remove" onclick="removeFromCart('${safeName}')">Remove</button>
                    </div>
                    <div class="cart-line-meta">
                        <div>
                            <span>Price</span>
                            <strong>Rs. ${unitPrice.toFixed(2)}</strong>
                        </div>
                        <div>
                            <span>Quantity</span>
                            <div class="cart-line-qty">
                                <button onclick="updateQuantity('${safeName}', -1)">-</button>
                                <span>${item.quantity}</span>
                                <button onclick="updateQuantity('${safeName}', 1)">+</button>
                            </div>
                        </div>
                        <div>
                            <span>Total</span>
                            <strong>Rs. ${lineTotal.toFixed(2)}</strong>
                        </div>
                    </div>
                </div>
            </article>
        `;
    }).join('') : `
        <div class="cart-page-empty">
            <div class="cart-page-empty-copy">
                <span class="eyebrow">Your cart is empty</span>
                <h2>Bring home something beautiful.</h2>
                <p>Browse the collection and add handcrafted pieces to see your full cart summary here.</p>
                <a href="/shop/" class="primary-link-btn">Continue Shopping</a>
            </div>
        </div>
    `;

    page.innerHTML = `
        <div class="cart-main-grid">
            <section class="cart-main-panel">
                <div class="cart-panel-header">
                    <div>
                        <span class="eyebrow">Bag Summary</span>
                        <h2>${itemCount} item${itemCount === 1 ? '' : 's'} ready for checkout</h2>
                    </div>
                    <button class="ghost-link-btn" onclick="clearCart()">Clear Cart</button>
                </div>
                <div class="cart-lines-wrap">${itemsMarkup}</div>
            </section>
            <aside class="cart-summary-panel">
                <div class="summary-card">
                    <span class="eyebrow">Order Summary</span>
                    <h3>Checkout details</h3>
                    <div class="summary-row"><span>Subtotal</span><strong>Rs. ${subtotal.toFixed(2)}</strong></div>
                    <div class="summary-row"><span>Shipping</span><strong>Rs. ${shipping.toFixed(2)}</strong></div>
                    <div class="summary-row"><span>Tax</span><strong>Rs. ${tax.toFixed(2)}</strong></div>
                    <div class="summary-row total"><span>Total</span><strong>Rs. ${grandTotal.toFixed(2)}</strong></div>
                    <a href="/checkout/" class="summary-btn${itemCount ? '' : ' disabled'}">Proceed to Checkout</a>
                    <p class="summary-note">Secure packaging, artisan-safe handling, and delivery support included.</p>
                </div>
                <div class="summary-card support-card">
                    <span class="eyebrow">Store Support</span>
                    <h3>Need help before you order?</h3>
                    <p>Talk with our team for gift selection, bulk orders, or product questions.</p>
                    <ul class="support-list">
                        <li><strong>Phone:</strong> ${page.dataset.phone || 'Support available'}</li>
                        <li><strong>Email:</strong> ${page.dataset.email || 'hello@tranquiltrails.com'}</li>
                        <li><strong>Store:</strong> ${page.dataset.store || 'Tranquil Trails'}</li>
                    </ul>
                </div>
            </aside>
        </div>
    `;
}

function persistCart() {
    writeStorage(cartKey, cart);
    renderCartSidebar();
    renderCartPage();
    renderCheckoutPage();
}

function addToWishlist(id, name, price, img) {
    const exists = wishlist.some((item) => String(item.id) === String(id) || item.name === name);
    if (exists) {
        showToast(`${name} is already in wishlist`, 'info');
        return;
    }

    wishlist.push({
        id,
        name,
        price: parseFloat(price) || 0,
        img: normalizeImagePath(img),
    });

    persistWishlist();
    showToast(`${name} saved to wishlist`, 'success');
}

function removeFromWishlist(name) {
    wishlist = wishlist.filter((item) => item.name !== name);
    persistWishlist();
    showToast(`${name} removed from wishlist`, 'warning');
}

function clearWishlist() {
    if (!wishlist.length) return;
    if (confirm('Clear your wishlist?')) {
        wishlist = [];
        persistWishlist();
        showToast('Wishlist cleared', 'warning');
    }
}

function moveWishlistToCart(name) {
    const item = wishlist.find((entry) => entry.name === name);
    if (!item) return;
    addToCart(item.id, item.name, item.price, item.img);
    wishlist = wishlist.filter((entry) => entry.name !== name);
    persistWishlist();
}

function renderWishlistCount() {
    const badges = document.querySelectorAll('[data-wishlist-count]');
    badges.forEach((badge) => {
        badge.textContent = wishlist.length;
    });
}

function renderWishlistPage() {
    const page = document.getElementById('wishlist-page-root');
    if (!page) return;

    if (!wishlist.length) {
        page.innerHTML = `
            <section class="wishlist-empty-state">
                <div class="wishlist-empty-visual">
                    <span></span><span></span><span></span>
                </div>
                <div class="wishlist-empty-copy">
                    <span class="eyebrow">Wishlist is empty</span>
                    <h2>Save the pieces you love.</h2>
                    <p>Tap the heart on any product and build your own curated collection with a smooth, real-store experience.</p>
                    <a href="/shop/" class="primary-link-btn">Explore Products</a>
                </div>
            </section>
        `;
        return;
    }

    page.innerHTML = `
        <section class="wishlist-hero-panel">
            <div>
                <span class="eyebrow">Curated for later</span>
                <h2>${wishlist.length} saved favorite${wishlist.length === 1 ? '' : 's'}</h2>
                <p>Keep your favorite handcrafted pieces in one beautiful place and move them to cart any time.</p>
            </div>
            <button class="ghost-link-btn" onclick="clearWishlist()">Clear Wishlist</button>
        </section>
        <section class="wishlist-grid">
            ${wishlist.map((item, index) => {
                const safeName = sanitizeName(item.name);
                return `
                    <article class="wishlist-card" style="animation-delay:${index * 120}ms">
                        <div class="wishlist-image-wrap">
                            <img src="${normalizeImagePath(item.img)}" alt="${item.name}" onerror="this.src='${staticPlaceholder}'">
                            <button class="wishlist-heart active" onclick="removeFromWishlist('${safeName}')">
                                <i class="fas fa-heart"></i>
                            </button>
                        </div>
                        <div class="wishlist-card-body">
                            <span class="wishlist-chip">Handcrafted Pick</span>
                            <h3>${item.name}</h3>
                            <p>Saved for your next calm, intentional purchase.</p>
                            <div class="wishlist-card-footer">
                                <strong>Rs. ${(parseFloat(item.price) || 0).toFixed(2)}</strong>
                                <div class="wishlist-actions">
                                    <button class="wishlist-secondary-btn" onclick="removeFromWishlist('${safeName}')">Remove</button>
                                    <button class="wishlist-primary-btn" onclick="moveWishlistToCart('${safeName}')">Move to Cart</button>
                                </div>
                            </div>
                        </div>
                    </article>
                `;
            }).join('')}
        </section>
    `;
}

function persistWishlist() {
    writeStorage(wishlistKey, wishlist);
    renderWishlistCount();
    renderWishlistPage();
    updateWishlistButtons();
}

function updateWishlistButtons() {
    document.querySelectorAll('.wishlist-btn, .wishlist-toggle, .wishlist-cta').forEach((button) => {
        const id = button.dataset.id;
        const name = button.dataset.name;
        const isSaved = wishlist.some((item) => String(item.id) === String(id) || item.name === name);
        button.classList.toggle('active', isSaved);

        const label = button.querySelector('.wishlist-btn-label');
        if (label) label.textContent = isSaved ? 'Saved' : 'Wishlist';
    });
}

function openCartSidebar() {
    const sidebar = document.getElementById('cartSidebar');
    if (sidebar) sidebar.classList.add('open');
}

function closeCartSidebar() {
    const sidebar = document.getElementById('cartSidebar');
    if (sidebar) sidebar.classList.remove('open');
}

function initHamburger() {
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');

    if (!hamburger || !navLinks) return;

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
    });

    document.addEventListener('click', (event) => {
        if (!navLinks.contains(event.target) && !hamburger.contains(event.target)) {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
        }
    });
}

function initCartSidebar() {
    const cartLink = document.getElementById('cart-link');
    const closeBtn = document.getElementById('closeCart');

    if (cartLink) {
        cartLink.addEventListener('click', (event) => {
            event.preventDefault();
            openCartSidebar();
        });
    }

    if (closeBtn) closeBtn.addEventListener('click', closeCartSidebar);

    document.addEventListener('click', (event) => {
        const sidebar = document.getElementById('cartSidebar');
        if (!sidebar || !sidebar.classList.contains('open')) return;
        if (sidebar.contains(event.target)) return;
        if (cartLink && cartLink.contains(event.target)) return;
        closeCartSidebar();
    });
}

function initDropdown() {
    const avatarBtn = document.getElementById('userAvatarBtn');
    const dropdown = document.getElementById('profileDropdown');
    if (!avatarBtn || !dropdown) return;

    avatarBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        dropdown.classList.toggle('show');
    });

    document.addEventListener('click', (event) => {
        if (!dropdown.contains(event.target) && !avatarBtn.contains(event.target)) {
            dropdown.classList.remove('show');
        }
    });
}

function initGlobalStoreButtons() {
    document.addEventListener('click', (event) => {
        const addButton = event.target.closest('.add-btn, .add-to-cart-btn, .buy-now-btn, .wishlist-primary-btn-direct');
        const wishlistButton = event.target.closest('.wishlist-btn, .wishlist-toggle, .wishlist-cta');

        if (wishlistButton) {
            event.preventDefault();
            const { id, name, price, img } = wishlistButton.dataset;
            if (!name) return;

            const alreadySaved = wishlist.some((item) => String(item.id) === String(id) || item.name === name);
            if (alreadySaved) {
                removeFromWishlist(name);
            } else {
                addToWishlist(id, name, price, img);
            }
            return;
        }

        if (!addButton) return;
        event.preventDefault();

        const source = addButton.dataset.name
            ? addButton.dataset
            : addButton.closest('[data-name][data-price]');

        if (!source) return;
        addToCart(source.id, source.name, source.price, source.img);
    });
}

function initSlider() {
    const slides = document.querySelectorAll('.slide');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const sliderWrapper = document.getElementById('sliderWrapper');
    let currentIndex = 0;

    function updateSlider() {
        if (!slides.length) return;

        slides.forEach((slide, index) => {
            slide.className = 'slide';
            let distance = index - currentIndex;
            if (distance > slides.length / 2) distance -= slides.length;
            if (distance < -slides.length / 2) distance += slides.length;

            if (distance === 0) slide.classList.add('active');
            else if (distance === 1) slide.classList.add('next1');
            else if (distance === 2) slide.classList.add('next2');
            else if (distance === -1) slide.classList.add('prev1');
            else if (distance === -2) slide.classList.add('prev2');
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % slides.length;
            updateSlider();
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + slides.length) % slides.length;
            updateSlider();
        });
    }

    if (sliderWrapper) {
        let touchStartX = 0;
        sliderWrapper.addEventListener('touchstart', (event) => {
            touchStartX = event.changedTouches[0].screenX;
        });
        sliderWrapper.addEventListener('touchend', (event) => {
            const touchEndX = event.changedTouches[0].screenX;
            if (touchEndX < touchStartX - 50) currentIndex = (currentIndex + 1) % slides.length;
            if (touchEndX > touchStartX + 50) currentIndex = (currentIndex - 1 + slides.length) % slides.length;
            updateSlider();
        });
    }

    updateSlider();
}

function initWoodSection() {
    const woodWrapper = document.getElementById('woodWrapper');
    const woodCards = document.querySelectorAll('.wood-card');

    if (!woodWrapper || !woodCards.length) return;

    woodCards.forEach((card) => {
        card.addEventListener('click', (event) => {
            if (event.target.closest('.add-to-cart-btn, .wishlist-btn, .wishlist-toggle')) return;

            const isActive = card.classList.contains('active');

            woodCards.forEach((entry) => entry.classList.remove('active'));
            woodWrapper.classList.remove('has-active');

            if (!isActive) {
                card.classList.add('active');
                woodWrapper.classList.add('has-active');

                setTimeout(() => {
                    card.scrollIntoView({
                        behavior: 'smooth',
                        block: 'nearest',
                        inline: 'center',
                    });
                }, 120);
            }
        });
    });

    document.addEventListener('click', (event) => {
        if (!woodWrapper.contains(event.target)) {
            woodCards.forEach((entry) => entry.classList.remove('active'));
            woodWrapper.classList.remove('has-active');
        }
    });
}

function getCheckoutTotals(root) {
    const taxRate = parseFloat(root.dataset.taxRate || '0');
    const shippingRate = parseFloat(root.dataset.shippingRate || '0');
    const { subtotal, itemCount } = getCartMetrics();
    const shipping = itemCount ? shippingRate : 0;
    const tax = subtotal * (taxRate / 100);
    const total = subtotal + shipping + tax;
    return { subtotal, shipping, tax, total, itemCount };
}

function renderCheckoutPage() {
    const root = document.querySelector('[data-checkout-root]');
    if (!root) return;

    const itemsContainer = document.getElementById('checkoutItems');
    const emptyState = document.getElementById('checkoutEmpty');
    const summary = document.getElementById('checkoutSummary');
    const submitButton = document.getElementById('checkoutSubmit');
    const totals = getCheckoutTotals(root);

    document.getElementById('checkoutSubtotal').textContent = `Rs. ${totals.subtotal.toFixed(2)}`;
    document.getElementById('checkoutShipping').textContent = `Rs. ${totals.shipping.toFixed(2)}`;
    document.getElementById('checkoutTax').textContent = `Rs. ${totals.tax.toFixed(2)}`;
    document.getElementById('checkoutTotal').textContent = `Rs. ${totals.total.toFixed(2)}`;

    if (!totals.itemCount) {
        itemsContainer.innerHTML = '';
        emptyState.style.display = 'block';
        summary.style.display = 'none';
        submitButton.disabled = true;
        return;
    }

    emptyState.style.display = 'none';
    summary.style.display = 'grid';
    submitButton.disabled = false;

    itemsContainer.innerHTML = cart.map((item) => `
        <article class="order-line">
            <img src="${normalizeImagePath(item.img)}" alt="${item.name}" onerror="this.src='${staticPlaceholder}'">
            <div>
                <strong>${item.name}</strong>
                <span class="checkout-muted">Quantity: ${item.quantity}</span>
            </div>
            <strong>Rs. ${((parseFloat(item.price) || 0) * item.quantity).toFixed(2)}</strong>
        </article>
    `).join('');
}

function initCheckoutOptions() {
    const options = document.querySelectorAll('[data-payment-option]');
    if (!options.length) return;

    options.forEach((option) => {
        option.addEventListener('click', () => {
            options.forEach((entry) => entry.classList.remove('active'));
            option.classList.add('active');
            const input = option.querySelector('input[type="radio"]');
            if (input) input.checked = true;
        });
    });
}

function buildCheckoutPayload(form) {
    const formData = new FormData(form);
    return {
        full_name: (formData.get('full_name') || '').trim(),
        email: (formData.get('email') || '').trim(),
        phone: (formData.get('phone') || '').trim(),
        address: (formData.get('address') || '').trim(),
        city: (formData.get('city') || '').trim(),
        state: (formData.get('state') || '').trim(),
        zipcode: (formData.get('zipcode') || '').trim(),
        payment_method: formData.get('payment_method') || 'COD',
        items: cart.map((item) => ({ id: item.id, quantity: item.quantity })),
    };
}

function handleRazorpayPayment(root, data) {
    const options = {
        key: data.razorpay.key,
        amount: data.razorpay.amount,
        currency: data.razorpay.currency,
        name: data.razorpay.name,
        description: data.razorpay.description,
        order_id: data.razorpay.order_id,
        prefill: data.razorpay.prefill,
        theme: { color: '#8B5E3C' },
        handler(response) {
            const verifyForm = new FormData();
            verifyForm.append('razorpay_payment_id', response.razorpay_payment_id);
            verifyForm.append('razorpay_order_id', response.razorpay_order_id);
            verifyForm.append('razorpay_signature', response.razorpay_signature);
            verifyForm.append('csrfmiddlewaretoken', getCsrfToken());

            fetch(root.dataset.verifyUrl, {
                method: 'POST',
                body: verifyForm,
            })
                .then((res) => res.json())
                .then((verifyData) => {
                    if (verifyData.status === 'success') {
                        cart = [];
                        persistCart();
                        window.location.href = verifyData.redirect_url || root.dataset.successUrl;
                    } else {
                        showToast(verifyData.error || 'Payment verification failed.', 'warning');
                    }
                })
                .catch(() => showToast('Unable to verify payment right now.', 'warning'));
        },
    };

    const razorpay = new Razorpay(options);
    razorpay.open();
}

function initCheckoutSubmit() {
    const root = document.querySelector('[data-checkout-root]');
    const form = document.getElementById('checkoutForm');
    const submitButton = document.getElementById('checkoutSubmit');
    if (!root || !form || !submitButton) return;

    submitButton.addEventListener('click', () => {
        if (!cart.length) {
            showToast('Your cart is empty.', 'warning');
            return;
        }

        if (!form.reportValidity()) return;

        const payload = buildCheckoutPayload(form);
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';

        fetch(root.dataset.createUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(payload),
        })
            .then((res) => res.json())
            .then((data) => {
                if (!data.success) {
                    throw new Error(data.error || 'Unable to start checkout.');
                }

                if (data.mode === 'cod') {
                    cart = [];
                    persistCart();
                    window.location.href = data.redirect_url || root.dataset.successUrl;
                    return;
                }

                if (!root.dataset.razorpayEnabled || root.dataset.razorpayEnabled === 'false') {
                    throw new Error('Razorpay is not configured yet.');
                }

                handleRazorpayPayment(root, data);
            })
            .catch((error) => {
                showToast(error.message || 'Checkout failed.', 'warning');
            })
            .finally(() => {
                submitButton.disabled = false;
                submitButton.textContent = 'Place Order';
            });
    });
}

function logoutUser() {
    fetch('/api/logout/')
        .then((response) => response.json())
        .then((data) => {
            if (data.success) window.location.href = '/';
        });
}

document.addEventListener('DOMContentLoaded', () => {
    initHamburger();
    initCartSidebar();
    initDropdown();
    initGlobalStoreButtons();
    initSlider();
    initWoodSection();
    initCheckoutOptions();
    initCheckoutSubmit();
    renderCartSidebar();
    renderCartPage();
    renderWishlistCount();
    renderWishlistPage();
    renderCheckoutPage();
    updateWishlistButtons();
});
