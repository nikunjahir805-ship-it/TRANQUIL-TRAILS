/**
 * TRANQUIL TRAILS - MASTER SCRIPT
 * Final Clean Version: Navigation, 3D Slider, Filtering, and Enhanced Cart
 */

// --- Global State ---
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// --- 1. Navigation & Hamburger Menu ---
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navLinks.classList.toggle('active');
});

// Close menu when clicking links or clicking outside
navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
    });
});

document.addEventListener('click', (e) => {
    if (!navLinks.contains(e.target) && !hamburger.contains(e.target)) {
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
    cartIcon.classList.add('cart-shake');
    setTimeout(() => cartIcon.classList.remove('cart-shake'), 400);
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

        const li = document.createElement('li');
        li.className = 'cart-item';
        li.innerHTML = `
            <img src="${item.img}" alt="${item.name}">
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
    totalEl.innerText = subtotal.toFixed(2);
    countEl.innerText = totalItems;
}

// Sidebar Visibility
function openCartSidebar() { document.getElementById('cartSidebar').classList.add('open'); }
function closeCartSidebar() { document.getElementById('cartSidebar').classList.remove('open'); }

document.getElementById('cart-link').addEventListener('click', (e) => { e.preventDefault(); openCartSidebar(); });
document.getElementById('closeCart').addEventListener('click', closeCartSidebar);

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('cartSidebar');
    const cartBtn = document.getElementById('cart-link');
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && !cartBtn.contains(e.target)) {
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
        document.getElementById('proSlider').scrollTo({ left: 0, behavior: 'smooth' });
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
        newCard.innerHTML = `<div class="pro-image-wrapper"><img src="${img}"></div><div class="pro-info"><h4>${name}</h4><p class="price">$${price}</p><div class="pro-btn-group"><button class="add-to-cart-btn">Add to Cart</button><button class="buy-now-btn">Buy Now</button></div></div>`;
        slider.prepend(newCard); 
        alert("Product Added!");
    }
}

// Initial Load
window.addEventListener('DOMContentLoaded', () => {
    updateSlider();
    renderCartUI();
    const isAdmin = localStorage.getItem('isAdmin');
    if (isAdmin === 'true') {
        document.getElementById('adminForm').style.display = 'flex';
        document.querySelectorAll('.admin-link').forEach(link => link.style.display = 'block');
        const authBtn = document.getElementById('authBtn');
        authBtn.innerHTML = "Logout";
        authBtn.onclick = () => { localStorage.removeItem('isAdmin'); window.location.reload(); };
    }
});

// --- Updated Checkout Logic ---
document.querySelector('.checkout-btn').addEventListener('click', () => {
    const isAdmin = localStorage.getItem('isAdmin'); // Checking if user is logged in
    
    if (cart.length === 0) {
        alert("Your bag is empty!");
        return;
    }

    if (isAdmin === 'true') {
        // If logged in, go to payment
        window.location.href = 'payment.html';
    } else {
        // If not logged in, go to login and save a "redirect" flag
        alert("Please log in to complete your purchase.");
        localStorage.setItem('redirectAfterLogin', 'payment.html');
        window.location.href = 'login.html';
    }
});