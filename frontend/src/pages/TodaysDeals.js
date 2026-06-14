import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

// Static deals data - moved outside component to prevent re-creation
const allDealsData = [
  {
    id: 5,
    title: "Amazon Echo Dot (5th Gen)",
    originalPrice: 49.99,
    dealPrice: 29.99,
    discount: "40% off",
    image: "https://images.unsplash.com/photo-1543512214-318c7553f230?w=400&h=400&fit=crop",
    rating: 4.5,
    reviewCount: 23451,
    category: "electronics"
  },
  {
    id: 23,
    title: "The Seven Husbands of Evelyn Hugo",
    originalPrice: 16.99,
    dealPrice: 9.99,
    discount: "41% off",
    image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=400&fit=crop",
    rating: 4.8,
    reviewCount: 45623,
    category: "books"
  },
  {
    id: 18,
    title: "JBL Charge 5 Portable Speaker",
    originalPrice: 179.99,
    dealPrice: 119.99,
    discount: "33% off",
    image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&fit=crop",
    rating: 4.7,
    reviewCount: 8765,
    category: "electronics"
  },
  {
    id: 12,
    title: "Ninja Foodi Personal Blender",
    originalPrice: 79.99,
    dealPrice: 59.99,
    discount: "25% off",
    image: "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=400&h=400&fit=crop",
    rating: 4.5,
    reviewCount: 7634,
    category: "home"
  },
  {
    id: 3,
    title: "Sony WH-1000XM5 Headphones",
    originalPrice: 399.99,
    dealPrice: 299.99,
    discount: "25% off",
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",
    rating: 4.7,
    reviewCount: 15632,
    category: "electronics"
  },
  {
    id: 31,
    title: "KitchenAid Stand Mixer",
    originalPrice: 449.99,
    dealPrice: 329.99,
    discount: "27% off",
    image: "https://images.unsplash.com/photo-1595644258096-69155da290fd?q=80&w=1169&auto=format&fit=crop",
    rating: 4.8,
    reviewCount: 18765,
    category: "home"
  },
  {
    id: 25,
    title: "Atomic Habits Book",
    originalPrice: 18.99,
    dealPrice: 12.99,
    discount: "32% off",
    image: "https://images.unsplash.com/photo-1592496431122-2349e0fbc666?w=400&h=400&fit=crop",
    rating: 4.9,
    reviewCount: 52341,
    category: "books"
  },
  {
    id: 7,
    title: "Instant Pot Duo 7-in-1",
    originalPrice: 79.99,
    dealPrice: 49.99,
    discount: "38% off",
    image: "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",
    rating: 4.6,
    reviewCount: 34567,
    category: "home"
  }
];

const TodaysDeals = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Filter deals based on selected category
  const filteredDeals = useMemo(() => {
    if (selectedCategory === 'all') {
      return allDealsData;
    }
    return allDealsData.filter(deal => deal.category === selectedCategory);
  }, [selectedCategory]);

  const dealCategories = [
    { id: 'all', label: 'All Deals' },
    { id: 'electronics', label: 'Electronics' },
    { id: 'home', label: 'Home & Kitchen' },
    { id: 'books', label: 'Books' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-4 sm:py-6 lg:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-2">Today's Deals</h1>
          <p className="text-sm sm:text-base text-gray-600">Limited-time offers on top products</p>
        </div>

        {/* Deal Categories */}
        <div className="mb-6 sm:mb-8">
          <div className="flex flex-wrap gap-2 sm:gap-3 lg:gap-4 mb-4 sm:mb-6">
            {dealCategories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-3 sm:px-4 py-2 rounded-md text-sm sm:text-base font-medium transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Featured Deal */}
        <div className="bg-gradient-to-r from-orange-400 to-red-500 rounded-lg p-4 sm:p-6 lg:p-8 text-white mb-6 sm:mb-8">
          <div className="flex flex-col md:flex-row items-center">
            <div className="w-full md:w-1/2 mb-4 sm:mb-6 md:mb-0 text-center md:text-left">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2">Deal of the Day</h2>
              <p className="text-base sm:text-lg lg:text-xl mb-3 sm:mb-4">Save up to 40% on Amazon Echo devices</p>
              <div className="text-xl sm:text-2xl font-bold">Starting at $29.99</div>
              <div className="text-sm sm:text-lg opacity-90">Was $49.99</div>
            </div>
            <div className="w-full md:w-1/2 text-center">
              <img 
                src="https://images.unsplash.com/photo-1543512214-318c7553f230?w=300&h=300&fit=crop" 
                alt="Echo Dot"
                className="mx-auto rounded-lg shadow-lg max-w-[200px] sm:max-w-[250px] md:max-w-[300px] w-full h-auto"
              />
            </div>
          </div>
        </div>

        {/* Deals Grid */}
        <div className="mb-6 sm:mb-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 sm:mb-6 gap-2">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
              {selectedCategory === 'all' ? 'All Deals' : 
               selectedCategory === 'electronics' ? 'Electronics Deals' :
               selectedCategory === 'home' ? 'Home & Kitchen Deals' :
               selectedCategory === 'books' ? 'Book Deals' : 'Deals'}
            </h2>
            <span className="text-sm sm:text-base text-gray-600">{filteredDeals.length} deals found</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
            {filteredDeals.map(deal => (
              <div key={deal.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                <div className="relative">
                  <img 
                    src={deal.image} 
                    alt={deal.title}
                    className="w-full h-40 sm:h-48 object-cover"
                  />
                  <div className="absolute top-2 left-2 bg-red-600 text-white px-2 py-1 rounded text-xs sm:text-sm font-bold">
                    {deal.discount}
                  </div>
                </div>
                <div className="p-3 sm:p-4">
                  <h3 className="font-semibold text-base sm:text-lg mb-2 line-clamp-2">{deal.title}</h3>
                <div className="flex items-center mb-2">
                  <div className="flex text-yellow-400">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className={`w-3 h-3 sm:w-4 sm:h-4 ${i < Math.floor(deal.rating) ? 'fill-current' : 'text-gray-300'}`} viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                  <span className="text-gray-600 text-xs sm:text-sm ml-1">({deal.reviewCount.toLocaleString()})</span>
                </div>
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-lg sm:text-2xl font-bold text-red-600">${deal.dealPrice}</span>
                  <span className="text-sm sm:text-base text-gray-500 line-through">${deal.originalPrice}</span>
                </div>
                  <Link 
                    to="/"
                    className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold py-2 px-4 rounded block text-center text-sm sm:text-base"
                  >
                    View Deal
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Lightning Deals */}
        <div className="mt-8 sm:mt-12">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Lightning Deals</h2>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 sm:p-6">
            <div className="text-center">
              <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">⚡</div>
              <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">New Lightning Deals Starting Soon</h3>
              <p className="text-sm sm:text-base text-gray-600 mb-3 sm:mb-4">Check back every hour for new limited-time offers</p>
              <div className="text-xl sm:text-2xl font-bold text-orange-600">Next Deal: 2:00 PM</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TodaysDeals;