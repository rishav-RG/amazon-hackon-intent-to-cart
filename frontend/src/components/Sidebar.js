import React, { useState } from 'react';

const Sidebar = ({ onCategoryFilter }) => {
  const [isOpen, setIsOpen] = useState(false);

  const categories = [
    {
      title: "Electronics",
      subcategories: [
        { name: "Computers & Laptops", filter: "electronics-computers" },
        { name: "Mobile Phones", filter: "electronics-phones" },
        { name: "Audio & Headphones", filter: "electronics-audio" },
        { name: "Gaming", filter: "electronics-gaming" },
        { name: "Smart Home Devices", filter: "electronics-smart" }
      ]
    },
    {
      title: "Books",
      subcategories: [
        { name: "Fiction", filter: "books-fiction" },
        { name: "Non-Fiction", filter: "books-nonfiction" },
        { name: "Textbooks", filter: "books-textbooks" },
        { name: "Children's Books", filter: "books-children" }
      ]
    },
    {
      title: "Home & Kitchen",
      subcategories: [
        { name: "Furniture", filter: "home-furniture" },
        { name: "Kitchen & Dining", filter: "home-kitchen" },
        { name: "Home Decor", filter: "home-decor" },
        { name: "Bedding & Bath", filter: "home-bedding" },
        { name: "Storage & Organization", filter: "home-storage" }
      ]
    },
    {
      title: "Clothing & Accessories",
      subcategories: [
        { name: "Men's Clothing", filter: "clothing-men" },
        { name: "Women's Clothing", filter: "clothing-women" },
        { name: "Kids' Clothing", filter: "clothing-kids" },
        { name: "Shoes", filter: "clothing-shoes" },
        { name: "Jewelry & Watches", filter: "clothing-jewelry" }
      ]
    },
    {
      title: "Sports & Outdoors",
      subcategories: [
        { name: "Exercise & Fitness", filter: "sports-fitness" },
        { name: "Outdoor Recreation", filter: "sports-outdoor" },
        { name: "Team Sports", filter: "sports-team" },
        { name: "Water Sports", filter: "sports-water" }
      ]
    },
    {
      title: "Health & Beauty",
      subcategories: [
        { name: "Skincare", filter: "beauty-skincare" },
        { name: "Makeup & Cosmetics", filter: "beauty-makeup" },
        { name: "Health & Wellness", filter: "beauty-health" },
        { name: "Personal Care", filter: "beauty-personal" }
      ]
    },
    {
      title: "Tools & Home Improvement",
      subcategories: [
        { name: "Power Tools", filter: "tools-power" },
        { name: "Hand Tools", filter: "tools-hand" },
        { name: "Hardware", filter: "tools-hardware" },
        { name: "Electrical", filter: "tools-electrical" }
      ]
    },
    {
      title: "Toys & Games",
      subcategories: [
        { name: "Action Figures & Dolls", filter: "toys-figures" },
        { name: "Board Games & Puzzles", filter: "toys-board" },
        { name: "Educational Toys", filter: "toys-educational" },
        { name: "Outdoor Play", filter: "toys-outdoor" }
      ]
    }
  ];

  const handleSubcategoryClick = (filter) => {
    if (onCategoryFilter) {
      onCategoryFilter(filter);
    }
    // Close mobile sidebar after selection
    setIsOpen(false);
  };

  const handleQuickLinkClick = (linkType) => {
    // Handle quick links functionality
    if (onCategoryFilter) {
      switch (linkType) {
        case 'bestsellers':
          onCategoryFilter('bestsellers');
          break;
        case 'new-releases':
          onCategoryFilter('new-releases');
          break;
        case 'deals':
          onCategoryFilter('deals');
          break;
        default:
          onCategoryFilter('all');
      }
    }
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        className="lg:hidden fixed top-20 sm:top-24 left-2 sm:left-4 z-50 bg-gray-800 text-white p-2 rounded shadow-lg"
        onClick={() => setIsOpen(!isOpen)}
      >
        <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:static lg:translate-x-0 top-0 left-0 h-full w-72 sm:w-80 lg:w-64 xl:w-72
        bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out z-40
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        overflow-y-auto
      `}>
        {/* Sidebar Header */}
        <div className="bg-gray-800 text-white p-3 sm:p-4 lg:hidden">
          <div className="flex items-center justify-between">
            <h2 className="text-base sm:text-lg font-bold">Browse Categories</h2>
            <button onClick={() => setIsOpen(false)}>
              <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-3 sm:p-4">
          <h2 className="hidden lg:block text-base lg:text-lg font-bold text-gray-900 mb-4">Shop by Category</h2>
          
          {/* Show All Products Button */}
          <button
            onClick={() => handleSubcategoryClick('all')}
            className="w-full mb-4 bg-orange-400 hover:bg-orange-500 text-gray-900 font-medium py-2 px-3 sm:px-4 rounded-md transition-colors duration-200 text-sm sm:text-base"
          >
            Show All Products
          </button>
          
          {/* Categories */}
          <div className="space-y-1 sm:space-y-2">
            {categories.map((category, index) => (
              <CategoryItem 
                key={index} 
                category={category} 
                onSubcategoryClick={handleSubcategoryClick}
              />
            ))}
          </div>

          {/* Additional Links */}
          <div className="mt-6 sm:mt-8 pt-4 sm:pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <button 
                  onClick={() => handleQuickLinkClick('bestsellers')}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-left w-full py-1"
                >
                  Best Sellers
                </button>
              </li>
              <li>
                <button 
                  onClick={() => handleQuickLinkClick('new-releases')}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-left w-full py-1"
                >
                  New Releases
                </button>
              </li>
              <li>
                <button 
                  onClick={() => handleQuickLinkClick('deals')}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-left w-full py-1"
                >
                  Today's Deals
                </button>
              </li>
              <li>
                <button 
                  onClick={() => handleQuickLinkClick('reviews')}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-left w-full py-1"
                >
                  Customer Reviews
                </button>
              </li>
              <li>
                <button 
                  onClick={() => handleQuickLinkClick('gifts')}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-left w-full py-1"
                >
                  Gift Ideas
                </button>
              </li>
            </ul>
          </div>

          {/* Help Section */}
          <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Help & Settings</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <button className="text-gray-600 hover:text-gray-800 text-left w-full py-1">
                  Your Account
                </button>
              </li>
              <li>
                <button className="text-gray-600 hover:text-gray-800 text-left w-full py-1">
                  Customer Service
                </button>
              </li>
              <li>
                <button className="text-gray-600 hover:text-gray-800 text-left w-full py-1">
                  Sign In
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
};

// Category Item Component with Expandable Subcategories
const CategoryItem = ({ category, onSubcategoryClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border-b border-gray-100 last:border-b-0">
      <button
        className="w-full flex items-center justify-between py-2 sm:py-3 text-left hover:bg-gray-50 focus:outline-none px-2 sm:px-0"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="text-sm font-medium text-gray-900">{category.title}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isExpanded && (
        <div className="pb-2 sm:pb-3 pl-2 sm:pl-4">
          <ul className="space-y-1 sm:space-y-2">
            {category.subcategories.map((subcategory, index) => (
              <li key={index}>
                <button 
                  onClick={() => onSubcategoryClick(subcategory.filter)}
                  className="text-sm text-blue-600 hover:text-blue-800 hover:underline text-left w-full py-1"
                >
                  {subcategory.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Sidebar;