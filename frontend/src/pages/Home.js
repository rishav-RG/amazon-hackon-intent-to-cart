import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ProductGrid from '../components/ProductGrid';

const Home = ({ searchQuery, searchCategory }) => {
  const [categoryFilter, setCategoryFilter] = useState('all');

  const handleCategoryFilter = (filter) => {
    setCategoryFilter(filter);
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar onCategoryFilter={handleCategoryFilter} />
      
      {/* Main Content */}
      <div className="flex-1 lg:ml-0"> {/* Ensures content doesn't overlap with sidebar on desktop */}
        <ProductGrid 
          categoryFilter={categoryFilter} 
          onClearFilter={handleCategoryFilter}
          searchQuery={searchQuery}
          searchCategory={searchCategory}
        />
      </div>
    </div>
  );
};

export default Home;