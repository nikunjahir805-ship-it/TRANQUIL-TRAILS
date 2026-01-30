/**
 * TRANQUIL TRAILS - MASTER SCRIPT
 * Final Clean Version: Navigation, 3D Slider, Filtering, Enhanced Cart, and Login Logic
 */

// --- Global State ---
let cart = JSON.parse(localStorage.getItem('cart')) || [];
const staticBasePath = "/static/"; // Helper for Django images

// --- 1. Navigation & Hamburger Menu ---
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

if(hamburger) {
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
    });
}

// Close menu when clicking links or clicking outside
if(navLinks) {
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
        });
    });
}

document.addEventListener('click', (e) => {
    if (navLinks && hamburger && !navLinks.contains(e.target) && !hamburger.contains(e.target)) {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
    }
});

// --- 2. 3D Carousel Slider Logic ---
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

// Touch support for mobile swipe
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

// --- 3. Unified Enhanced Cart Logic ---

// Handles clicks on all "Add to Cart" and "Buy Now" buttons
document.addEventListener('click', (e) => {
    const btn = e.target;
    if (btn.classList.contains('add-to-cart-btn') || btn.classList.contains('buy-now-btn')) {
        const parent = btn.closest('.pro-card') || btn.closest('.slide');
        if (!parent) return;

        const product = {
            name: parent.getAttribute('data-name'),
            price: parseFloat(parent.getAttribute('data-price')),
            img: parent.getAttribute('data-img'),
            quantity: 1
        };

        handleAddToCart(product);
        if (btn.classList.contains('buy-now-btn')) openCartSidebar();
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
    localStorage.setItem('cart', JSON.stringify(cart));
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

        // Fix image path for cart display
        let displayImg = item.img;
        if (!displayImg.startsWith('/static/') && !displayImg.startsWith('http')) {
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

// --- 4. Filtering & Admin ---
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
        const slider = document.getElementById('proSlider');
        if(slider) slider.scrollTo({ left: 0, behavior: 'smooth' });
    });
});

function addNewProduct() {
    const name = document.getElementById('pName').value;
    const price = document.getElementById('pPrice').value;
    const img = document.getElementById('pImg').value;
    const slider = document.getElementById('proSlider');

    if(name && price && img) {
        const newCard = document.createElement('div');
        newCard.className = 'pro-card';
        newCard.setAttribute('data-name', name);
        newCard.setAttribute('data-price', price);
        newCard.setAttribute('data-img', img);
        
        // Ensure image has path
        let displayImg = img;
        if (!displayImg.startsWith('/static/')) {
            displayImg = staticBasePath + displayImg;
        }

        newCard.innerHTML = `<div class="pro-image-wrapper"><img src="${displayImg}"></div><div class="pro-info"><h4>${name}</h4><p class="price">$${price}</p><div class="pro-btn-group"><button class="add-to-cart-btn">Add to Cart</button><button class="buy-now-btn">Buy Now</button></div></div>`;
        slider.prepend(newCard); 
        alert("Product Added!");
    }
}

// --- 5. INITIAL LOAD & LOGIN CHECK ---
window.addEventListener('DOMContentLoaded', () => {
    updateSlider();
    renderCartUI();

    // Check Login State from LocalStorage
    // 'true' = Admin, 'false' = Normal User, null = Not Logged In
    const isAdmin = localStorage.getItem('isAdmin'); 
    const authBtn = document.getElementById('authBtn');

    // IF LOGGED IN (As Admin OR Normal User)
    if (isAdmin) {
        if (authBtn) {
            // Change "Log In" to "Logout"
            authBtn.innerHTML = "Logout";
            authBtn.href = "#";
            authBtn.classList.add('logout-mode');
            
            // Logout Functionality
            authBtn.onclick = (e) => { 
                e.preventDefault(); 
                localStorage.removeItem('isAdmin'); 
                alert("You have been logged out.");
                window.location.reload(); 
            };
        }

        // SPECIAL ADMIN FEATURES (Only if isAdmin is exactly 'true')
        if (isAdmin === 'true') {
            const adminForm = document.getElementById('adminForm');
            if (adminForm) adminForm.style.display = 'flex';
            
            document.querySelectorAll('.admin-link').forEach(link => {
                link.style.display = 'block';
            });
        }
    }
});

// --- Updated Checkout Logic ---
const checkoutBtn = document.querySelector('.checkout-btn');
if(checkoutBtn) {
    checkoutBtn.addEventListener('click', () => {
        const isAdmin = localStorage.getItem('isAdmin'); 
        
        if (cart.length === 0) {
            alert("Your bag is empty!");
            return;
        }

        if (isAdmin) {
            // Logged in (Admin or User) -> Proceed to Payment
            alert("Proceeding to payment...");
            // window.location.href = 'payment.html'; // Uncomment when payment page exists
        } else {
            // Not Logged in -> Send to Login
            alert("Please log in to complete your purchase.");
            window.location.href = '/login/'; // Using Django URL path
        }
    });
}