// ============================================
// GLOBAL PERSISTENT CART SYSTEM (SAFE VERSION)
// ============================================

let cart = {};

// Detect gallery page safely
const IS_GALLERY_PAGE = document.body.classList.contains('page-gallery');

// ============================================
// 1. LOAD CART FROM LOCALSTORAGE
// ============================================
function loadCart() {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
        try {
            cart = JSON.parse(savedCart);
        } catch (e) {
            console.error('Cart parse error:', e);
            cart = {};
        }
    }
}

// ============================================
// 2. SAVE CART TO LOCALSTORAGE
// ============================================
function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

// ============================================
// 3. ADD TO CART
// ============================================
function addToCart(id, name, price, image) {
    if (!id || !name || !price || !image) return;

    if (cart[id]) {
        cart[id].quantity += 1;
    } else {
        cart[id] = {
            id,
            name,
            price: parseFloat(price),
            image,
            quantity: 1
        };
    }

    saveCart();
    updateCartUI();
    openCartSidebar();
    showCartFeedback(name);
}

// ============================================
// 4. UPDATE CART UI
// ============================================
function updateCartUI() {
    updateCartCount();

    if (IS_GALLERY_PAGE) return;

    updateCartSidebar();

    if (document.getElementById('cart-page-container')) {
        updateCartPage();
    }
}

// ============================================
// 5. CART COUNT BADGE
// ============================================
function updateCartCount() {
    let total = 0;
    Object.values(cart).forEach(item => total += item.quantity);

    const badge = document.getElementById('cart-count');
    if (badge) badge.textContent = total;
}

// ============================================
// 6. CART SIDEBAR
// ============================================
function updateCartSidebar() {
    const list = document.getElementById('cart-items-list');
    const totalEl = document.getElementById('total-price');
    if (!list) return;

    list.innerHTML = '';
    const items = Object.values(cart);

    if (!items.length) {
        list.innerHTML = `<li style="text-align:center;padding:40px;color:#888;">Your cart is empty</li>`;
        if (totalEl) totalEl.textContent = '0';
        return;
    }

    let total = 0;

    items.forEach(item => {
        total += item.price * item.quantity;

        const li = document.createElement('li');
        li.innerHTML = `
            <img src="${item.image}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;">
            <div>
                <strong>${item.name}</strong><br>
                ₹${item.price.toFixed(2)}
            </div>
            <button onclick="decreaseQuantity('${item.id}')">−</button>
            <span>${item.quantity}</span>
            <button onclick="increaseQuantity('${item.id}')">+</button>
            <button onclick="removeFromCart('${item.id}')">&times;</button>
        `;
        list.appendChild(li);
    });

    if (totalEl) totalEl.textContent = total.toFixed(2);
}

// ============================================
// 7. CART PAGE (cart.html)
// ============================================
function updateCartPage() {
    const container = document.getElementById('cart-page-container');
    if (!container) return;

    const items = Object.values(cart);
    if (!items.length) {
        container.innerHTML = `<h2 style="text-align:center;">Your Cart is Empty</h2>`;
        return;
    }

    let total = 0;
    container.innerHTML = '';

    items.forEach(item => {
        total += item.price * item.quantity;
        container.innerHTML += `
            <div>
                <img src="${item.image}" style="width:100px;">
                <strong>${item.name}</strong>
                ₹${item.price}
                x ${item.quantity}
                <button onclick="removeFromCart('${item.id}')">Remove</button>
            </div>
        `;
    });

    container.innerHTML += `<h3>Total: ₹${total.toFixed(2)}</h3>`;
}

// ============================================
// 8. QUANTITY CONTROLS
// ============================================
function increaseQuantity(id) {
    if (!cart[id]) return;
    cart[id].quantity++;
    saveCart();
    updateCartUI();
}

function decreaseQuantity(id) {
    if (!cart[id]) return;
    cart[id].quantity > 1 ? cart[id].quantity-- : delete cart[id];
    saveCart();
    updateCartUI();
}

function removeFromCart(id) {
    delete cart[id];
    saveCart();
    updateCartUI();
}

// ============================================
// 9. CLEAR CART
// ============================================
function clearCart() {
    cart = {};
    saveCart();
    updateCartUI();
}

// ============================================
// 10. SIDEBAR CONTROLS
// ============================================
function openCartSidebar() {
    if (IS_GALLERY_PAGE) return;
    document.getElementById('cartSidebar')?.classList.add('active');
}

function closeCartSidebar() {
    document.getElementById('cartSidebar')?.classList.remove('active');
}

// ============================================
// 11. TOAST NOTIFICATION
// ============================================
function showCartFeedback(name) {
    if (IS_GALLERY_PAGE) return;

    const toast = document.createElement('div');
    toast.textContent = `${name} added to cart`;
    toast.style.cssText = `
        position:fixed;top:90px;right:20px;
        background:#28a745;color:white;
        padding:12px 20px;border-radius:6px;
        z-index:9999;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

// ============================================
// 12. DOM READY
// ============================================
document.addEventListener('DOMContentLoaded', () => {

    loadCart();
    updateCartCount();

    if (IS_GALLERY_PAGE) return;

    updateCartUI();

    document.querySelectorAll('.add-to-cart-btn, .add-btn')
        .forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                addToCart(
                    btn.dataset.id,
                    btn.dataset.name,
                    btn.dataset.price,
                    btn.dataset.image
                );
            });
        });

    document.getElementById('closeCart')?.addEventListener('click', closeCartSidebar);

    document.getElementById('cart-link')?.addEventListener('click', e => {
        e.preventDefault();
        openCartSidebar();
    });
});
