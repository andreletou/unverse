// Données des produits
const products = [
    {
        id: 1,
        name: "Smartphone X1 Pro",
        price: 299900,
        originalPrice: 349900,
        image: "https://images.unsplash.com/photo-1555774698-0b77e0d5fac6?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        description: "Le dernier smartphone avec écran AMOLED et triple caméra.",
        rating: 4.5,
        reviews: 128,
        inStock: true,
        features: ["Écran 6.5\" AMOLED", "Triple caméra 48MP", "Batterie 4000mAh", "Charge rapide 30W"],
        colors: ["Noir", "Bleu", "Blanc"]
    },
    {
        id: 2,
        name: "Écouteurs Bluetooth",
        price: 49900,
        originalPrice: 69900,
        image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        description: "Écouteurs sans fil avec réduction de bruit active.",
        rating: 4.2,
        reviews: 86,
        inStock: true,
        features: ["Réduction de bruit", "Autonomie 20h", "Bluetooth 5.0", "IPX5"],
        colors: ["Noir", "Rouge"]
    },
    {
        id: 3,
        name: "Montre Connectée",
        price: 129900,
        image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        description: "Suivez votre activité physique et recevez des notifications.",
        rating: 4.7,
        reviews: 215,
        inStock: true,
        features: ["Écran AMOLED", "Suivi cardio", "Résistance à l'eau", "30 jours autonomie"],
        colors: ["Noir", "Argent", "Or"]
    },
    {
        id: 4,
        name: "Ordinateur Portable",
        price: 749900,
        originalPrice: 849900,
        image: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        description: "Ultra-fin et léger avec processeur haute performance.",
        rating: 4.8,
        reviews: 42,
        inStock: false,
        features: ["Processeur i7", "16GB RAM", "SSD 512GB", "Écran 15.6\" 4K"],
        colors: ["Gris", "Noir"]
    },
    {
        id: 5,
        name: "Haut-parleur Intelligent",
        price: 89900,
        image: "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        description: "Contrôlez votre maison intelligente avec votre voix.",
        rating: 4.3,
        reviews: 156,
        inStock: true,
        features: ["Assistant vocal", "Son 360°", "Bluetooth/WiFi", "Micro intégré"],
        colors: ["Noir", "Gris"]
    },
    {
        id: 6,
        name: "Casque VR",
        price: 199900,
        originalPrice: 249900,
        image: "https://images.unsplash.com/photo-1593508512255-86ab42a8e620?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        description: "Plongez dans des mondes virtuels avec une qualité HD.",
        rating: 4.6,
        reviews: 73,
        inStock: true,
        features: ["Écran OLED 4K", "120Hz", "Tracking précis", "Audio 3D"],
        colors: ["Noir", "Blanc"]
    }
];

// Configuration
const config = {
    whatsappNumber: "+22893020525",
    companyName: "UniversePro",
    freeShippingThreshold: 100000,
    shippingCost: 5000,
    currency: 'XOF',
    currencySymbol: 'FCFA',
    defaultProductImage: "https://via.placeholder.com/500x500?text=Produit+Indisponible"
};

// État de l'application
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

// Sélection des éléments DOM
const DOM = {
    productsContainer: document.getElementById('products-container'),
    favoritesContainer: document.getElementById('favorites-container'),
    cartCount: document.querySelectorAll('.cart-count'),
    favoritesCount: document.querySelectorAll('.favorites-count'),
    cartItemsContainer: document.getElementById('cart-items'),
    cartSummary: document.getElementById('cart-summary'),
    subtotalElement: document.getElementById('subtotal'),
    shippingElement: document.getElementById('shipping'),
    totalElement: document.getElementById('total'),
    checkoutBtn: document.getElementById('checkout-btn'),
    hamburger: document.getElementById('hamburger'),
    nav: document.querySelector('nav'),
    continueShoppingBtn: document.querySelector('.continue-shopping'),
    updateCartBtn: document.querySelector('.update-cart'),
    searchInput: document.getElementById('search-input'),
    sortSelect: document.getElementById('sort-select'),
    categoryFilter: document.getElementById('category-filter'),
    productModal: document.getElementById('product-modal'),
    modalClose: document.querySelector('.modal-close'),
    modalContent: document.querySelector('.modal-content')
};

// Fonctions utilitaires
const utils = {
    formatPrice: (price) => {
        return new Intl.NumberFormat('fr-FR', { 
            style: 'currency', 
            currency: config.currency 
        }).format(price).replace('CFA', config.currencySymbol);
    },

    updateCartCount: () => {
        const count = cart.reduce((total, item) => total + item.quantity, 0);
        DOM.cartCount.forEach(element => {
            element.textContent = count;
        });
    },

    updateFavoritesCount: () => {
        const count = favorites.length;
        DOM.favoritesCount.forEach(element => {
            element.textContent = count;
        });
    },

    saveCartToLocalStorage: () => {
        localStorage.setItem('cart', JSON.stringify(cart));
    },

    saveFavoritesToLocalStorage: () => {
        localStorage.setItem('favorites', JSON.stringify(favorites));
    },

    calculateCartTotals: () => {
        const subtotal = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
        const shipping = subtotal > config.freeShippingThreshold ? 0 : config.shippingCost;
        const total = subtotal + shipping;
        
        return { subtotal, shipping, total };
    },

    debounce: (func, delay) => {
        let timeoutId;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(context, args), delay);
        };
    },

    getProductRatingStars: (rating) => {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let stars = '★'.repeat(fullStars);
        stars += hasHalfStar ? '½' : '';
        stars += '☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0));
        return stars;
    }
};

// Fonctions pour les produits
const productFunctions = {
    renderProducts: (productsToRender = products) => {
        if (!DOM.productsContainer) return;
        
        DOM.productsContainer.innerHTML = productsToRender.map(product => `
            <div class="product-card" data-id="${product.id}">
                ${product.originalPrice && product.originalPrice > product.price ? 
                    `<span class="product-badge">-${Math.round((1 - product.price/product.originalPrice)*100)}%</span>` : ''}
                ${!product.inStock ? 
                    `<div class="out-of-stock">Rupture de stock</div>` : ''}
                
                <div class="product-image">
                    <img src="${product.inStock ? product.image : config.defaultProductImage}" 
                         alt="${product.name}" 
                         loading="lazy"
                         onclick="productFunctions.showProductDetails(${product.id})">
                    <button class="favorite-btn ${favorites.includes(product.id) ? 'active' : ''}" 
                            data-id="${product.id}"
                            aria-label="${favorites.includes(product.id) ? 'Retirer des favoris' : 'Ajouter aux favoris'}">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
                <div class="product-info">
                    <h3 class="product-title" onclick="productFunctions.showProductDetails(${product.id})">${product.name}</h3>
                    
                    <div class="product-rating">
                        <div class="stars" title="${product.rating.toFixed(1)}/5">
                            ${utils.getProductRatingStars(product.rating)}
                        </div>
                        <span class="reviews-count">(${product.reviews})</span>
                    </div>
                    
                    <div class="product-price">
                        <span class="current-price">${utils.formatPrice(product.price)}</span>
                        ${product.originalPrice && product.originalPrice > product.price ? 
                            `<span class="original-price">${utils.formatPrice(product.originalPrice)}</span>` : ''}
                    </div>
                    
                    <button class="add-to-cart" 
                            data-id="${product.id}" 
                            ${!product.inStock ? 'disabled' : ''}>
                        <i class="fas fa-shopping-cart"></i>
                        ${!product.inStock ? 'Indisponible' : 'Ajouter au panier'}
                    </button>
                </div>
            </div>
        `).join('');
        
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', cartFunctions.addToCart);
        });
        
        document.querySelectorAll('.favorite-btn').forEach(button => {
            button.addEventListener('click', productFunctions.toggleFavorite);
        });
    },

    renderFavorites: () => {
        if (!DOM.favoritesContainer) return;
        
        const favoriteProducts = products.filter(p => favorites.includes(p.id));
        
        if (favoriteProducts.length === 0) {
            DOM.favoritesContainer.innerHTML = `
                <div class="empty-favorites-message">
                    <i class="fas fa-heart"></i>
                    <h3>Vos favoris sont vides</h3>
                    <p>Ajoutez des produits à vos favoris en cliquant sur l'icône cœur</p>
                    <a href="index.html" class="btn btn-primary">Parcourir les produits</a>
                </div>
            `;
            return;
        }
        
        DOM.favoritesContainer.innerHTML = favoriteProducts.map(product => `
            <div class="product-card" data-id="${product.id}">
                ${product.originalPrice && product.originalPrice > product.price ? 
                    `<span class="product-badge">-${Math.round((1 - product.price/product.originalPrice)*100)}%</span>` : ''}
                ${!product.inStock ? 
                    `<div class="out-of-stock">Rupture de stock</div>` : ''}
                
                <div class="product-image">
                    <img src="${product.inStock ? product.image : config.defaultProductImage}" 
                         alt="${product.name}" 
                         loading="lazy"
                         onclick="productFunctions.showProductDetails(${product.id})">
                    <button class="favorite-btn active" 
                            data-id="${product.id}"
                            aria-label="Retirer des favoris">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
                <div class="product-info">
                    <h3 class="product-title" onclick="productFunctions.showProductDetails(${product.id})">${product.name}</h3>
                    
                    <div class="product-rating">
                        <div class="stars" title="${product.rating.toFixed(1)}/5">
                            ${utils.getProductRatingStars(product.rating)}
                        </div>
                        <span class="reviews-count">(${product.reviews})</span>
                    </div>
                    
                    <div class="product-price">
                        <span class="current-price">${utils.formatPrice(product.price)}</span>
                        ${product.originalPrice && product.originalPrice > product.price ? 
                            `<span class="original-price">${utils.formatPrice(product.originalPrice)}</span>` : ''}
                    </div>
                    
                    <button class="add-to-cart" 
                            data-id="${product.id}" 
                            ${!product.inStock ? 'disabled' : ''}>
                        <i class="fas fa-shopping-cart"></i>
                        ${!product.inStock ? 'Indisponible' : 'Ajouter au panier'}
                    </button>
                </div>
            </div>
        `).join('');
        
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', cartFunctions.addToCart);
        });
        
        document.querySelectorAll('.favorite-btn').forEach(button => {
            button.addEventListener('click', productFunctions.toggleFavorite);
        });
    },

    findProductById: (id) => {
        return products.find(p => p.id === id);
    },

    toggleFavorite: (e) => {
        e.stopPropagation();
        const productId = parseInt(e.currentTarget.getAttribute('data-id'));
        const index = favorites.indexOf(productId);
        
        if (index === -1) {
            favorites.push(productId);
            e.currentTarget.classList.add('active');
            e.currentTarget.setAttribute('aria-label', 'Retirer des favoris');
        } else {
            favorites.splice(index, 1);
            e.currentTarget.classList.remove('active');
            e.currentTarget.setAttribute('aria-label', 'Ajouter aux favoris');
        }
        
        utils.saveFavoritesToLocalStorage();
        utils.updateFavoritesCount();
        
        // Si on est sur la page des favoris, re-rendre la liste
        if (window.location.pathname.includes('favorites.html')) {
            productFunctions.renderFavorites();
        }
    },

    showProductDetails: (productId) => {
        const product = productFunctions.findProductById(productId);
        if (!product || !DOM.productModal) return;
        
        DOM.modalContent.innerHTML = `
            <div class="modal-product-images">
                <div class="main-image">
                    <img src="${product.image}" alt="${product.name}">
                </div>
            </div>
            <div class="modal-product-info">
                <h2>${product.name}</h2>
                
                <div class="modal-product-rating">
                    <div class="stars" title="${product.rating.toFixed(1)}/5">
                        ${utils.getProductRatingStars(product.rating)}
                    </div>
                    <span class="reviews-count">${product.reviews} avis</span>
                    ${product.inStock ? 
                        '<span class="in-stock"><i class="fas fa-check"></i> En stock</span>' : 
                        '<span class="out-of-stock"><i class="fas fa-times"></i> Rupture de stock</span>'}
                </div>
                
                <div class="modal-product-price">
                    <span class="current-price">${utils.formatPrice(product.price)}</span>
                    ${product.originalPrice && product.originalPrice > product.price ? 
                        `<span class="original-price">${utils.formatPrice(product.originalPrice)}</span>` : ''}
                </div>
                
                <div class="modal-product-description">
                    <h3>Description</h3>
                    <p>${product.description}</p>
                </div>
                
                <div class="modal-product-features">
                    <h3>Caractéristiques</h3>
                    <ul>
                        ${product.features.map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="modal-product-colors">
                    <h3>Couleurs disponibles</h3>
                    <div class="color-options">
                        ${product.colors.map(color => `
                            <div class="color-option" style="background-color: ${color.toLowerCase()}" title="${color}"></div>
                        `).join('')}
                    </div>
                </div>
                
                <button class="add-to-cart modal-add-to-cart" 
                        data-id="${product.id}" 
                        ${!product.inStock ? 'disabled' : ''}>
                    <i class="fas fa-shopping-cart"></i>
                    ${!product.inStock ? 'Indisponible' : 'Ajouter au panier'}
                </button>
            </div>
        `;
        
        document.querySelector('.modal-add-to-cart')?.addEventListener('click', cartFunctions.addToCart);
        DOM.productModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    },

    closeProductDetails: () => {
        DOM.productModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    },

    searchProducts: (query) => {
        const normalizedQuery = query.toLowerCase().trim();
        if (!normalizedQuery) return productFunctions.renderProducts();
        
        const filteredProducts = products.filter(product => 
            product.name.toLowerCase().includes(normalizedQuery) || 
            product.description.toLowerCase().includes(normalizedQuery)
        );
        
        productFunctions.renderProducts(filteredProducts);
    },

    sortProducts: (sortBy) => {
        let sortedProducts = [...products];
        
        switch(sortBy) {
            case 'price-asc':
                sortedProducts.sort((a, b) => a.price - b.price);
                break;
            case 'price-desc':
                sortedProducts.sort((a, b) => b.price - a.price);
                break;
            case 'rating':
                sortedProducts.sort((a, b) => b.rating - a.rating);
                break;
            case 'name':
                sortedProducts.sort((a, b) => a.name.localeCompare(b.name));
                break;
            default:
                // Pas de tri ou tri par défaut
                break;
        }
        
        productFunctions.renderProducts(sortedProducts);
    },

    filterByCategory: (category) => {
        if (!category || category === 'all') {
            productFunctions.renderProducts();
            return;
        }
        
        // Implémentez votre logique de filtrage par catégorie ici
        // Par exemple:
        // const filteredProducts = products.filter(p => p.category === category);
        // productFunctions.renderProducts(filteredProducts);
    }
};

// Fonctions pour le panier
const cartFunctions = {
    addToCart: (e) => {
        const productId = parseInt(e.currentTarget.getAttribute('data-id'));
        const product = productFunctions.findProductById(productId);
        
        if (!product) return;
        
        const existingItem = cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                ...product,
                quantity: 1
            });
        }
        
        utils.updateCartCount();
        utils.saveCartToLocalStorage();
        
        // Feedback visuel
        const button = e.currentTarget;
        button.innerHTML = '<i class="fas fa-check"></i> Ajouté !';
        button.classList.add('added-to-cart');
        
        setTimeout(() => {
            if (product.inStock) {
                button.innerHTML = '<i class="fas fa-shopping-cart"></i> Ajouter au panier';
            }
            button.classList.remove('added-to-cart');
        }, 2000);
    },

    renderCartItems: () => {
        if (!DOM.cartItemsContainer) return;
        
        if (cart.length === 0) {
            DOM.cartItemsContainer.innerHTML = `
                <div class="empty-cart-message">
                    <i class="fas fa-shopping-bag"></i>
                    <h3>Votre panier est vide</h3>
                    <p>Parcourez nos produits et trouvez quelque chose qui vous plaît</p>
                    <a href="index.html" class="btn btn-primary">Commencer mes achats</a>
                </div>
            `;
            DOM.checkoutBtn.disabled = true;
            return;
        }
        
        DOM.cartItemsContainer.innerHTML = cart.map(item => `
            <div class="cart-item" data-id="${item.id}">
                <div class="cart-item-image">
                    <img src="${item.image}" alt="${item.name}" loading="lazy">
                </div>
                <div class="cart-item-info">
                    <div class="cart-item-title">${item.name}</div>
                    <div class="cart-item-price">${utils.formatPrice(item.price)}</div>
                    <div class="cart-item-quantity">
                        <button class="quantity-btn minus" aria-label="Réduire la quantité">-</button>
                        <input type="number" class="quantity-input" value="${item.quantity}" min="1">
                        <button class="quantity-btn plus" aria-label="Augmenter la quantité">+</button>
                    </div>
                    <div class="cart-item-total">${utils.formatPrice(item.price * item.quantity)}</div>
                </div>
                <button class="remove-item" aria-label="Supprimer l'article">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
        
        // Ajout des événements
        document.querySelectorAll('.quantity-btn.minus').forEach(button => {
            button.addEventListener('click', cartFunctions.decreaseQuantity);
        });
        
        document.querySelectorAll('.quantity-btn.plus').forEach(button => {
            button.addEventListener('click', cartFunctions.increaseQuantity);
        });
        
        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', cartFunctions.updateQuantity);
        });
        
        document.querySelectorAll('.remove-item').forEach(button => {
            button.addEventListener('click', cartFunctions.removeItem);
        });
        
        cartFunctions.updateCartSummary();
        DOM.checkoutBtn.disabled = false;
    },

    updateCartSummary: () => {
        const { subtotal, shipping, total } = utils.calculateCartTotals();
        
        DOM.subtotalElement.textContent = utils.formatPrice(subtotal);
        DOM.shippingElement.textContent = shipping === 0 ? 'Gratuit' : utils.formatPrice(shipping);
        DOM.totalElement.textContent = utils.formatPrice(total);
        
        // Afficher un message pour la livraison gratuite
        if (subtotal > 0 && subtotal < config.freeShippingThreshold) {
            const remaining = config.freeShippingThreshold - subtotal;
            DOM.cartSummary.innerHTML += `
                <div class="free-shipping-message">
                    <i class="fas fa-truck"></i>
                    Plus que ${utils.formatPrice(remaining)} pour la livraison gratuite !
                </div>
            `;
        } else if (shipping === 0) {
            DOM.cartSummary.innerHTML += `
                <div class="free-shipping-message success">
                    <i class="fas fa-check-circle"></i>
                    Félicitations ! Vous bénéficiez de la livraison gratuite.
                </div>
            `;
        }
    },

    decreaseQuantity: (e) => {
        const cartItem = e.target.closest('.cart-item');
        const productId = parseInt(cartItem.getAttribute('data-id'));
        const item = cart.find(item => item.id === productId);
        
        if (item.quantity > 1) {
            item.quantity -= 1;
        } else {
            cart = cart.filter(item => item.id !== productId);
        }
        
        utils.saveCartToLocalStorage();
        utils.updateCartCount();
        cartFunctions.renderCartItems();
    },

    increaseQuantity: (e) => {
        const cartItem = e.target.closest('.cart-item');
        const productId = parseInt(cartItem.getAttribute('data-id'));
        const item = cart.find(item => item.id === productId);
        
        item.quantity += 1;
        
        utils.saveCartToLocalStorage();
        utils.updateCartCount();
        cartFunctions.renderCartItems();
    },

    updateQuantity: (e) => {
        const newQuantity = parseInt(e.target.value);
        if (isNaN(newQuantity)) return;
        
        const cartItem = e.target.closest('.cart-item');
        const productId = parseInt(cartItem.getAttribute('data-id'));
        const item = cart.find(item => item.id === productId);
        
        if (newQuantity < 1) {
            cart = cart.filter(item => item.id !== productId);
        } else {
            item.quantity = newQuantity;
        }
        
        utils.saveCartToLocalStorage();
        utils.updateCartCount();
        cartFunctions.renderCartItems();
    },

    removeItem: (e) => {
        const cartItem = e.target.closest('.cart-item');
        const productId = parseInt(cartItem.getAttribute('data-id'));
        
        cart = cart.filter(item => item.id !== productId);
        
        utils.saveCartToLocalStorage();
        utils.updateCartCount();
        cartFunctions.renderCartItems();
    },

    clearCart: () => {
        cart = [];
        utils.saveCartToLocalStorage();
        utils.updateCartCount();
        cartFunctions.renderCartItems();
    },

    checkoutViaWhatsApp: () => {
        if (cart.length === 0) {
            alert('Votre panier est vide');
            return;
        }
        
        const { subtotal, shipping, total } = utils.calculateCartTotals();
        const orderNumber = `CMD-${Date.now().toString().slice(-6)}`;
        const currentDate = new Date().toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        
        let message = `*NOUVELLE COMMANDE - ${config.companyName}*\n`;
        message += `Numéro de commande: ${orderNumber}\n`;
        message += `Date: ${currentDate}\n\n`;
        message += `*Détails de la commande:*\n\n`;
        
        cart.forEach((item, index) => {
            message += `${index + 1}. *${item.name}*\n`;
            message += `   Quantité: ${item.quantity}\n`;
            message += `   Prix unitaire: ${utils.formatPrice(item.price)}\n`;
            message += `   Total: ${utils.formatPrice(item.price * item.quantity)}\n\n`;
        });
        
        message += `*Résumé de la commande:*\n`;
        message += `Sous-total: ${utils.formatPrice(subtotal)}\n`;
        message += `Livraison: ${shipping === 0 ? 'Gratuite' : utils.formatPrice(shipping)}\n`;
        message += `*TOTAL: ${utils.formatPrice(total)}*\n\n`;
        message += `*Informations client:*\n`;
        message += `Nom: [Veuillez indiquer votre nom complet]\n`;
        message += `Téléphone: [Votre numéro de contact]\n`;
        message += `Adresse de livraison: [Votre adresse complète]\n\n`;
        message += `Méthode de paiement préférée: [Mobile Money, Espèce, Carte]\n\n`;
        message += `Merci de confirmer la disponibilité des articles et les modalités de paiement.`;
        
        const encodedMessage = encodeURIComponent(message);
        const whatsappUrl = `https://wa.me/${config.whatsappNumber}?text=${encodedMessage}`;
        
        window.open(whatsappUrl, '_blank');
    }
};

// Gestion des événements
const eventHandlers = {
    init: () => {
        utils.updateCartCount();
        utils.updateFavoritesCount();
        productFunctions.renderProducts();
        cartFunctions.renderCartItems();
        
        // Menu hamburger
        if (DOM.hamburger) {
            DOM.hamburger.addEventListener('click', () => {
                DOM.hamburger.classList.toggle('active');
                DOM.nav.classList.toggle('active');
            });
        }
        
        // Bouton de commande WhatsApp
        if (DOM.checkoutBtn) {
            DOM.checkoutBtn.addEventListener('click', cartFunctions.checkoutViaWhatsApp);
        }
        
        // Fermer le menu lorsqu'on clique sur un lien
        document.querySelectorAll('nav a').forEach(link => {
            link.addEventListener('click', () => {
                DOM.hamburger.classList.remove('active');
                DOM.nav.classList.remove('active');
            });
        });
        
        // Continuer les achats
        if (DOM.continueShoppingBtn) {
            DOM.continueShoppingBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = 'index.html';
            });
        }
        
        // Actualiser le panier
        if (DOM.updateCartBtn) {
            DOM.updateCartBtn.addEventListener('click', (e) => {
                e.preventDefault();
                cartFunctions.renderCartItems();
            });
        }
        
        // Recherche de produits
        if (DOM.searchInput) {
            DOM.searchInput.addEventListener('input', utils.debounce(() => {
                productFunctions.searchProducts(DOM.searchInput.value);
            }, 300));
        }
        
        // Tri des produits
        if (DOM.sortSelect) {
            DOM.sortSelect.addEventListener('change', () => {
                productFunctions.sortProducts(DOM.sortSelect.value);
            });
        }
        
        // Filtrage par catégorie
        if (DOM.categoryFilter) {
            DOM.categoryFilter.addEventListener('change', () => {
                productFunctions.filterByCategory(DOM.categoryFilter.value);
            });
        }
        
        // Modal produit
        if (DOM.modalClose) {
            DOM.modalClose.addEventListener('click', productFunctions.closeProductDetails);
        }
        
        // Fermer la modal en cliquant à l'extérieur
        if (DOM.productModal) {
            DOM.productModal.addEventListener('click', (e) => {
                if (e.target === DOM.productModal) {
                    productFunctions.closeProductDetails();
                }
            });
        }
        
        // Rendre les favoris si on est sur la page
        if (window.location.pathname.includes('favorites.html')) {
            productFunctions.renderFavorites();
        }
    }
};

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', eventHandlers.init);

// Exposer certaines fonctions au scope global pour les événements HTML
window.productFunctions = productFunctions;
window.cartFunctions = cartFunctions;