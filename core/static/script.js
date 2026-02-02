/**
 * TRANQUIL TRAILS - MASTER SCRIPT
 * Handles Navigation, Cart, Slider, and Checkout Logic
 */

// --- 1. User & Cart Setup ---
// Get the current user from the HTML (or default to 'guest')
const currentUser = window.djangoUser || 'guest';
const cartKey = `cart_${currentUser}`; 

// Load cart specific to this user
let cart = JSON.parse(localStorage.getItem(cartKey)) || [];
const staticBasePath = "/static/"; 

// --- 2. Navigation & Hamburger Menu ---
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

if(hamburger) {
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
    });
}

document.addEventListener('click', (e) => {
    if (navLinks && hamburger && !navLinks.contains(e.target) && !hamburger.contains(e.target)) {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
    }
});

// --- 3. 3D Carousel Slider Logic ---
const slides = document.querySelectorAll('.slide');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
const sliderWrapper = document.getElementById('sliderWrapper');
let currentIndex = 0;

function updateSlider() {
    if(slides.length === 0) return;
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

if (nextBtn && prevBtn) {
    nextBtn.addEventListener('click', () => { currentIndex = (currentIndex + 1) % slides.length; updateSlider(); });
    prevBtn.addEventListener('click', () => { currentIndex = (currentIndex - 1 + slides.length) % slides.length; updateSlider(); });
}

// Touch support
let touchStartX = 0;
if (sliderWrapper) {
    sliderWrapper.addEventListener('touchstart', (e) => { touchStartX = e.changedTouches[0].screenX; });
    sliderWrapper.addEventListener('touchend', (e) => {
        let touchEndX = e.changedTouches[0].screenX;
        if (touchEndX < touchStartX - 50) currentIndex = (currentIndex + 1) % slides.length;
        if (touchEndX > touchStartX + 50) currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        updateSlider();
    });
}

// --- 4. Unified Cart Logic ---

document.addEventListener('click', (e) => {
    // Robust check for buttons using .closest()
    const btn = e.target.closest('.add-btn, .add-to-cart-btn, .buy-now-btn');
    
    if (btn) {
        e.preventDefault(); 

        let name, price, img;

        if (btn.dataset.name) {
            // Data is on the button itself (Shop Page)
            name = btn.dataset.name;
            price = parseFloat(btn.dataset.price);
            img = btn.dataset.img;
        } else {
            // Data is on the parent card (Home/Offers Page)
            const parent = btn.closest('.product-card, .slide, .wood-card, .pro-card');
            if (!parent) return;
            name = parent.getAttribute('data-name');
            price = parseFloat(parent.getAttribute('data-price'));
            img = parent.getAttribute('data-img');
        }

        if (name && price) {
            const product = { name, price, img, quantity: 1 };
            handleAddToCart(product);
            
            // Visual Feedback
            const originalText = btn.innerText;
            btn.innerText = "Added!";
            setTimeout(() => btn.innerText = originalText, 1000);

            if (btn.classList.contains('buy-now-btn')) openCartSidebar();
        }
    }
});

function handleAddToCart(product) {
    const existingIndex = cart.findIndex(item => item.name === product.name);
    if (existingIndex > -1) {
        cart[existingIndex].quantity += 1;
    } else {
        cart.push(product);
    }
    saveAndUpdate();
    openCartSidebar();
}

function updateQuantity(name, change) {
    const item = cart.find(i => i.name === name);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) cart = cart.filter(i => i.name !== name);
        saveAndUpdate();
    }
}

function removeFromCart(name) {
    cart = cart.filter(item => item.name !== name);
    saveAndUpdate();
}

function clearCart() {
    if(confirm("Empty your shopping bag?")) {
        cart = [];
        saveAndUpdate();
    }
}

function saveAndUpdate() {
    localStorage.setItem(cartKey, JSON.stringify(cart));
    renderCartUI();
    
    const cartIcon = document.getElementById('cart-link');
    if(cartIcon) {
        cartIcon.classList.add('cart-shake');
        setTimeout(() => cartIcon.classList.remove('cart-shake'), 400);
    }
}

function renderCartUI() {
    const list = document.getElementById('cart-items-list');
    const totalEl = document.getElementById('total-price');
    const countEl = document.getElementById('cart-count');
    
    if (!list) return;

    list.innerHTML = '';
    let subtotal = 0;
    let totalItems = 0;

    cart.forEach(item => {
        subtotal += item.price * item.quantity;
        totalItems += item.quantity;

        let displayImg = item.img;
        if (displayImg && !displayImg.startsWith('/static/') && !displayImg.startsWith('http')) {
            displayImg = staticBasePath + displayImg;
        }

        const li = document.createElement('li');
        li.className = 'cart-item';
        li.innerHTML = `
            <img src="${displayImg}" alt="${item.name}">
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <p class="item-price">$${item.price.toFixed(2)}</p>
                <div class="qty-controls">
                    <button class="qty-btn" onclick="updateQuantity('${item.name}', -1)">-</button>
                    <span class="qty-val">${item.quantity}</span>
                    <button class="qty-btn" onclick="updateQuantity('${item.name}', 1)">+</button>
                </div>
            </div>
            <button class="remove-item" onclick="removeFromCart('${item.name}')">&times;</button>
        `;
        list.appendChild(li);
    });

    if(totalEl) totalEl.innerText = subtotal.toFixed(2);
    if(countEl) countEl.innerText = totalItems;
}

// Sidebar Visibility
function openCartSidebar() { 
    const sidebar = document.getElementById('cartSidebar');
    if(sidebar) sidebar.classList.add('open'); 
}
function closeCartSidebar() { 
    const sidebar = document.getElementById('cartSidebar');
    if(sidebar) sidebar.classList.remove('open'); 
}

const cartLink = document.getElementById('cart-link');
if(cartLink) cartLink.addEventListener('click', (e) => { e.preventDefault(); openCartSidebar(); });

const closeCartBtn = document.getElementById('closeCart');
if(closeCartBtn) closeCartBtn.addEventListener('click', closeCartSidebar);

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('cartSidebar');
    const cartBtn = document.getElementById('cart-link');
    if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && !cartBtn.contains(e.target)) {
        closeCartSidebar();
    }
});

// --- 5. Checkout Logic (Updated) ---
const checkoutBtn = document.querySelector('.checkout-btn');
if(checkoutBtn) {
    checkoutBtn.addEventListener('click', () => {
        if (cart.length === 0) {
            alert("Your bag is empty!");
            return;
        }

        // Check if user is logged in (using window.djangoUser from HTML)
        if (currentUser === 'guest') {
            alert("Please log in to complete your purchase.");
            window.location.href = '/login/';
        } else {
            alert("Proceeding to payment...");
            // window.location.href = '/payment/'; 
        }
    });
}

// --- 6. Filter Logic (Gallery/Shop) ---
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const filterValue = btn.getAttribute('data-filter');
        const cards = document.querySelectorAll('.pro-card');
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        cards.forEach(card => {
            const category = card.getAttribute('data-category');
            if (filterValue === 'all' || category === filterValue) {
                card.style.display = "flex";
                setTimeout(() => card.style.opacity = "1", 10);
            } else {
                card.style.opacity = "0";
                setTimeout(() => card.style.display = "none", 400);
            }
        });
        
        // Scroll horizontal slider to start
        const slider = document.getElementById('proSlider');
        if(slider) slider.scrollTo({ left: 0, behavior: 'smooth' });
    });
});

// --- 7. Wood Section Interaction ---
document.addEventListener("DOMContentLoaded", () => {
    updateSlider(); // Init 3D slider
    renderCartUI(); // Init Cart

    const woodWrapper = document.getElementById('woodWrapper');
    const woodCards = document.querySelectorAll('.wood-card');

    if (woodWrapper && woodCards.length > 0) {
        woodCards.forEach(card => {
            card.addEventListener('click', (e) => {
                if(e.target.closest('.add-to-cart-btn')) return;

                const isActive = card.classList.contains('active');
                woodCards.forEach(c => c.classList.remove('active'));
                woodWrapper.classList.remove('has-active');

                if (!isActive) {
                    card.classList.add('active');
                    woodWrapper.classList.add('has-active');
                    setTimeout(() => {
                        card.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                    }, 100);
                }
            });
        });
        
        // Reset wood section on outside click
        document.addEventListener('click', (e) => {
            if (woodWrapper && !woodWrapper.contains(e.target)) {
                woodCards.forEach(c => c.classList.remove('active'));
                woodWrapper.classList.remove('has-active');
            }
        });
    }
});