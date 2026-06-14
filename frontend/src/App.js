import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Cart from './pages/Cart';
import TodaysDeals from './pages/TodaysDeals';
import CustomerService from './pages/CustomerService';
import Registry from './pages/Registry';
import GiftCards from './pages/GiftCards';
import Sell from './pages/Sell';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCategory, setSearchCategory] = useState('All');

  const handleSearch = (query, category) => {
    setSearchQuery(query);
    setSearchCategory(category);
  };

  return (
    <CartProvider>
      <Router>
        <div className="min-h-screen flex flex-col">
          <Navbar onSearch={handleSearch} />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Home searchQuery={searchQuery} searchCategory={searchCategory} />} />
              <Route path="/cart" element={<Cart />} />
              <Route path="/deals" element={<TodaysDeals />} />
              <Route path="/customer-service" element={<CustomerService />} />
              <Route path="/registry" element={<Registry />} />
              <Route path="/gift-cards" element={<GiftCards />} />
              <Route path="/sell" element={<Sell />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </CartProvider>
  );
}

export default App;
