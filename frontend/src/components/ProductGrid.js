import React, { useState, useMemo } from 'react';
import ProductCard from './ProductCard';
import productsData from '../data/products.json';

const ProductGrid = ({ categoryFilter, onClearFilter, searchQuery, searchCategory }) => {
  const [sortBy, setSortBy] = useState('featured');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // Filter products based on category and search
  const filteredProducts = useMemo(() => {
    let products = productsData;

    // Apply search filter first
    if (searchQuery && searchQuery.trim() !== '') {
      products = products.filter(product => {
        const searchText = `${product.title} ${product.description}`.toLowerCase();
        const query = searchQuery.toLowerCase();
        
        // If a specific search category is selected, filter by that too
        if (searchCategory && searchCategory !== 'All') {
          const categoryMatch = searchText.includes(searchCategory.toLowerCase());
          return searchText.includes(query) && categoryMatch;
        }
        
        return searchText.includes(query);
      });
    }

    // Then apply category filter
    if (!categoryFilter || categoryFilter === 'all') {
      return products;
    }
    
    // Match products to categories based on our actual product data
    return products.filter(product => {
      const productId = product.id;
      
      switch (categoryFilter) {
        case 'electronics-computers':
          return [4, 15, 16].includes(productId); // MacBook Air, Dell XPS 13, HP Gaming Desktop
        case 'electronics-phones':
          return [1, 13, 14].includes(productId); // iPhone 15 Pro Max, Samsung Galaxy S24, Google Pixel 8
        case 'electronics-audio':
          return [3, 9, 17, 18].includes(productId); // Sony Headphones, AirPods Pro, Bose QC45, JBL Charge 5
        case 'electronics-gaming':
          return [6, 19, 20].includes(productId); // Nintendo Switch, PlayStation 5, Xbox Series X
        case 'electronics-smart':
          return [5, 2, 21, 22].includes(productId); // Echo Dot, Samsung TV, Ring Doorbell, Philips Hue
        case 'books-fiction':
          return [23, 24].includes(productId); // Seven Husbands of Evelyn Hugo, Where the Crawdads Sing
        case 'books-nonfiction':
          return [25, 26].includes(productId); // Atomic Habits, Educated
        case 'books-textbooks':
          return [27, 28].includes(productId); // Campbell Biology, Calculus
        case 'books-children':
          return [29, 30].includes(productId); // Green Eggs and Ham, Very Hungry Caterpillar
        case 'home-kitchen':
          return [7, 12, 31, 32].includes(productId); // Instant Pot, Ninja Blender, KitchenAid Mixer, Ninja Foodi
        case 'home-furniture':
          return [33, 34].includes(productId); // West Elm Coffee Table, Ashley Sofa
        case 'home-decor':
          return [10].includes(productId); // YETI Tumbler
        case 'home-bedding':
          return [35].includes(productId); // Brooklinen Sheets
        case 'home-storage':
          return [36].includes(productId); // Container Store Closet System
        case 'health-fitness':
        case 'sports-fitness':
          return [11, 37, 38, 39, 40].includes(productId); // Fitbit, Apple Watch, Garmin Watch, NordicTrack, Bowflex
        case 'beauty-health':
          return [11, 37, 38].includes(productId); // Health trackers
        case 'sports-outdoor':
          return [39, 40].includes(productId); // Treadmill, Dumbbells
        case 'bestsellers':
          return product.rating >= 4.7; // High-rated products
        case 'new-releases':
          return productId >= 35; // Latest products
        case 'deals':
          return product.price <= 200; // Lower-priced items
        case 'reviews':
          return product.reviewCount >= 15000; // Products with many reviews
        case 'gifts':
          return [5, 8, 9, 10, 21, 22, 29, 30, 37].includes(productId); // Gift-worthy items
        default:
          return true;
      }
    });
  }, [categoryFilter, searchQuery, searchCategory]);

  // Sort products based on selected option
  const sortedProducts = useMemo(() => {
    const products = [...filteredProducts];
    
    switch (sortBy) {
      case 'price-low':
        return products.sort((a, b) => a.price - b.price);
      case 'price-high':
        return products.sort((a, b) => b.price - a.price);
      case 'rating':
        return products.sort((a, b) => b.rating - a.rating);
      case 'newest':
        return products.sort((a, b) => b.id - a.id);
      default:
        return products;
    }
  }, [filteredProducts, sortBy]);

  // Paginate products
  const totalPages = Math.ceil(sortedProducts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentProducts = sortedProducts.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getCategoryDisplayName = () => {
    if (searchQuery && searchQuery.trim() !== '') {
      return `Search results for "${searchQuery}"`;
    }
    
    if (!categoryFilter || categoryFilter === 'all') return 'All Products';
    
    const categoryNames = {
      'electronics-computers': 'Computers & Laptops',
      'electronics-phones': 'Mobile Phones',
      'electronics-audio': 'Audio & Headphones',
      'electronics-gaming': 'Gaming',
      'electronics-smart': 'Smart Home Devices',
      'home-kitchen': 'Kitchen & Dining',
      'books-fiction': 'Books & Reading',
      'health-fitness': 'Health & Fitness',
      'home-decor': 'Home & Decor',
      'bestsellers': 'Best Sellers',
      'new-releases': 'New Releases',
      'deals': "Today's Deals"
    };
    
    return categoryNames[categoryFilter] || 'Products';
  };

  return (
    <div className="flex-1 p-2 sm:p-4">
      {/* Header and Sorting */}
      <div className="flex flex-col space-y-4 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
            {getCategoryDisplayName()}
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            {sortedProducts.length} results
            {categoryFilter && categoryFilter !== 'all' && (
              <button 
                onClick={() => onClearFilter && onClearFilter('all')} 
                className="ml-2 text-blue-600 hover:text-blue-800 text-sm underline"
              >
                (Clear filter)
              </button>
            )}
          </p>
        </div>
        
        <div className="w-full sm:w-auto">
          <label htmlFor="sort" className="block text-sm font-medium text-gray-700 mb-1">
            Sort by:
          </label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full sm:w-auto border border-gray-300 rounded-md px-3 py-2 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="featured">Featured</option>
            <option value="price-low">Price: Low to High</option>
            <option value="price-high">Price: High to Low</option>
            <option value="rating">Customer Rating</option>
            <option value="newest">Newest Arrivals</option>
          </select>
        </div>
      </div>

      {/* Product Grid */}
      {sortedProducts.length > 0 ? (
        <div className="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
          {currentProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 sm:py-12">
          <div className="mb-4">
            <svg className="w-12 h-12 sm:w-16 sm:h-16 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-2">No products found</h3>
          <p className="text-sm sm:text-base text-gray-600 mb-4 px-4">
            No products match your current filter. Try selecting a different category.
          </p>
          <button
            onClick={() => onClearFilter && onClearFilter('all')}
            className="bg-orange-400 hover:bg-orange-500 text-gray-900 font-medium py-2 px-4 rounded-md transition-colors duration-200"
          >
            Show All Products
          </button>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex flex-wrap justify-center items-center gap-2 mb-4">
          {/* Previous Button */}
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={`px-2 sm:px-3 py-2 rounded-md text-sm ${
              currentPage === 1
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="hidden sm:inline">Previous</span>
            <span className="sm:hidden">Prev</span>
          </button>

          {/* Page Numbers */}
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
            // Show only a few pages around current page
            if (
              page === 1 ||
              page === totalPages ||
              (page >= currentPage - 1 && page <= currentPage + 1)
            ) {
              return (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`px-2 sm:px-3 py-2 rounded-md text-sm ${
                    currentPage === page
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              );
            } else if (
              page === currentPage - 2 ||
              page === currentPage + 2
            ) {
              return (
                <span key={page} className="px-1 sm:px-2 py-2 text-gray-500 text-sm">
                  ...
                </span>
              );
            }
            return null;
          })}

          {/* Next Button */}
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className={`px-2 sm:px-3 py-2 rounded-md text-sm ${
              currentPage === totalPages
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="hidden sm:inline">Next</span>
            <span className="sm:hidden">Next</span>
          </button>
        </div>
      )}

      {/* Results Summary */}
      <div className="mt-4 sm:mt-6 text-center text-xs sm:text-sm text-gray-600">
        Showing {startIndex + 1}-{Math.min(endIndex, sortedProducts.length)} of {sortedProducts.length} results
      </div>
    </div>
  );
};

export default ProductGrid;