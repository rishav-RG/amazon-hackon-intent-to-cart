import React, { useState } from 'react';

const Sell = () => {
  const [activeTab, setActiveTab] = useState('individual');

  const benefits = [
    {
      icon: '🌐',
      title: 'Reach Millions',
      description: 'Access hundreds of millions of customers worldwide'
    },
    {
      icon: '📦',
      title: 'Fulfillment by Amazon',
      description: 'Let Amazon handle storage, packing, and shipping'
    },
    {
      icon: '🛡️',
      title: 'Trusted Platform',
      description: 'Sell on the most trusted e-commerce platform'
    },
    {
      icon: '📊',
      title: 'Powerful Tools',
      description: 'Access analytics, advertising, and inventory management'
    }
  ];

  const sellingSteps = [
    {
      step: 1,
      title: 'Create Your Account',
      description: 'Sign up for a selling account and provide business information'
    },
    {
      step: 2,
      title: 'List Your Products',
      description: 'Add products with photos, descriptions, and competitive pricing'
    },
    {
      step: 3,
      title: 'Start Selling',
      description: 'Manage orders, handle customer service, and grow your business'
    }
  ];

  const categories = [
    'Electronics', 'Books', 'Home & Kitchen', 'Clothing', 'Sports & Outdoors',
    'Health & Beauty', 'Toys & Games', 'Automotive', 'Arts & Crafts', 'Baby Products'
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-8 sm:py-12 lg:py-16">
          <div className="text-center">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold mb-4 sm:mb-6">Start Selling on Amazon</h1>
            <p className="text-base sm:text-lg lg:text-xl mb-6 sm:mb-8 max-w-3xl mx-auto px-2">
              Join millions of sellers who have built successful businesses on Amazon. 
              Reach customers worldwide and grow your brand with our powerful selling tools.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 px-2">
              <button className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-3 sm:py-4 px-6 sm:px-8 rounded-md text-base sm:text-lg">
                Start Selling Now
              </button>
              <button className="border-2 border-white text-white hover:bg-white hover:text-blue-600 font-bold py-3 sm:py-4 px-6 sm:px-8 rounded-md text-base sm:text-lg">
                Request Info
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-8 sm:py-12">
        {/* Selling Plans */}
        <div className="mb-12 sm:mb-16">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 sm:mb-4">Choose Your Selling Plan</h2>
            <p className="text-base sm:text-lg lg:text-xl text-gray-600">Select the plan that best fits your business needs</p>
          </div>

          <div className="flex justify-center mb-6 sm:mb-8">
            <div className="bg-white rounded-lg shadow-md p-1 w-full max-w-md sm:max-w-none">
              <div className="grid grid-cols-2 sm:flex">
                <button
                  onClick={() => setActiveTab('individual')}
                  className={`px-3 sm:px-6 py-2 sm:py-3 rounded-md font-medium text-sm sm:text-base ${
                    activeTab === 'individual' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Individual Plan
                </button>
                <button
                  onClick={() => setActiveTab('professional')}
                  className={`px-3 sm:px-6 py-2 sm:py-3 rounded-md font-medium text-sm sm:text-base ${
                    activeTab === 'professional' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Professional Plan
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 max-w-4xl mx-auto">
            {/* Individual Plan */}
            <div className={`bg-white rounded-lg shadow-lg p-6 sm:p-8 ${activeTab === 'individual' ? 'border-2 border-blue-500' : 'border border-gray-200'}`}>
              <div className="text-center mb-6">
                <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Individual</h3>
                <div className="text-3xl sm:text-4xl font-bold text-blue-600 mb-2">$0.99</div>
                <div className="text-sm sm:text-base text-gray-600">per item sold</div>
              </div>
              <ul className="space-y-3 sm:space-y-4 mb-6 sm:mb-8">
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  No monthly subscription fee
                </li>
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Sell in most categories
                </li>
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Individual product listing
                </li>
                <li className="flex items-center text-gray-500 text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  Advanced selling tools
                </li>
              </ul>
              <button className={`w-full py-2 sm:py-3 px-4 sm:px-6 rounded-md font-medium text-sm sm:text-base ${
                activeTab === 'individual' 
                  ? 'bg-blue-600 text-white hover:bg-blue-700' 
                  : 'bg-gray-200 text-gray-600'
              }`}>
                Get Started
              </button>
            </div>

            {/* Professional Plan */}
            <div className={`bg-white rounded-lg shadow-lg p-6 sm:p-8 relative ${activeTab === 'professional' ? 'border-2 border-blue-500' : 'border border-gray-200'}`}>
              <div className="absolute -top-3 sm:-top-4 left-1/2 transform -translate-x-1/2 bg-orange-500 text-white px-3 sm:px-4 py-1 sm:py-2 rounded-full text-xs sm:text-sm font-bold">
                RECOMMENDED
              </div>
              <div className="text-center mb-6">
                <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Professional</h3>
                <div className="text-3xl sm:text-4xl font-bold text-blue-600 mb-2">$39.99</div>
                <div className="text-sm sm:text-base text-gray-600">per month</div>
              </div>
              <ul className="space-y-3 sm:space-y-4 mb-6 sm:mb-8">
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  No per-item fee
                </li>
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Sell in all categories
                </li>
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Bulk listing tools
                </li>
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Advanced analytics & reports
                </li>
                <li className="flex items-center text-sm sm:text-base">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mr-2 sm:mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Advertising tools
                </li>
              </ul>
              <button className={`w-full py-2 sm:py-3 px-4 sm:px-6 rounded-md font-medium text-sm sm:text-base ${
                activeTab === 'professional' 
                  ? 'bg-blue-600 text-white hover:bg-blue-700' 
                  : 'bg-gray-200 text-gray-600'
              }`}>
                Start Free Trial
              </button>
            </div>
          </div>
        </div>

        {/* Benefits */}
        <div className="mb-12 sm:mb-16">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 sm:mb-4">Why Sell on Amazon?</h2>
            <p className="text-base sm:text-lg lg:text-xl text-gray-600">Join the world's largest online marketplace</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
            {benefits.map((benefit, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-4 sm:p-6 text-center">
                <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">{benefit.icon}</div>
                <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-sm sm:text-base text-gray-600">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* How It Works */}
        <div className="mb-12 sm:mb-16">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 sm:mb-4">How It Works</h2>
            <p className="text-base sm:text-lg lg:text-xl text-gray-600">Start selling in just a few simple steps</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {sellingSteps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="bg-blue-600 text-white w-12 h-12 sm:w-16 sm:h-16 rounded-full flex items-center justify-center text-xl sm:text-2xl font-bold mx-auto mb-4 sm:mb-6">
                  {step.step}
                </div>
                <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-3 sm:mb-4">{step.title}</h3>
                <p className="text-sm sm:text-base text-gray-600">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Categories */}
        <div className="mb-12 sm:mb-16">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 sm:mb-4">What Can You Sell?</h2>
            <p className="text-base sm:text-lg lg:text-xl text-gray-600">Explore popular product categories</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
            {categories.map((category, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-3 sm:p-4 text-center hover:shadow-lg transition-shadow cursor-pointer">
                <div className="font-semibold text-gray-900 text-sm sm:text-base">{category}</div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-700 rounded-lg p-6 sm:p-8 lg:p-12 text-center text-white">
          <h2 className="text-2xl sm:text-3xl font-bold mb-3 sm:mb-4">Ready to Start Your Amazon Business?</h2>
          <p className="text-base sm:text-lg lg:text-xl mb-6 sm:mb-8">Join millions of successful sellers and grow your business on Amazon</p>
          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4">
            <button className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-3 sm:py-4 px-6 sm:px-8 rounded-md text-base sm:text-lg">
              Start Selling Today
            </button>
            <button className="border-2 border-white text-white hover:bg-white hover:text-blue-600 font-bold py-3 sm:py-4 px-6 sm:px-8 rounded-md text-base sm:text-lg">
              Learn More
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sell;