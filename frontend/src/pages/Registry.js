import React, { useState } from 'react';

const Registry = () => {
  const [activeTab, setActiveTab] = useState('create');

  const registryTypes = [
    {
      type: 'wedding',
      title: 'Wedding Registry',
      description: 'Celebrate your special day with gifts from friends and family',
      icon: '💒',
      benefits: ['Free shipping', 'Completion discount', 'Extended returns']
    },
    {
      type: 'baby',
      title: 'Baby Registry',
      description: 'Get everything you need for your new arrival',
      icon: '👶',
      benefits: ['Welcome Box', 'Completion discount', 'Universal registry']
    },
    {
      type: 'birthday',
      title: 'Birthday List',
      description: 'Create a wish list for your special day',
      icon: '🎂',
      benefits: ['Easy sharing', 'Surprise protection', 'Group gifting']
    },
    {
      type: 'holiday',
      title: 'Holiday List',
      description: 'Share your holiday wishes with loved ones',
      icon: '🎁',
      benefits: ['Seasonal items', 'Price tracking', 'Gift recommendations']
    }
  ];

  const sampleRegistries = [
    {
      id: 1,
      name: 'Sarah & Mike\'s Wedding',
      type: 'Wedding Registry',
      date: 'June 15, 2024',
      items: 45,
      purchased: 23,
      image: 'https://images.unsplash.com/photo-1519741497674-611481863552?w=300&h=200&fit=crop'
    },
    {
      id: 2,
      name: 'Emma\'s Baby Shower',
      type: 'Baby Registry',
      date: 'Due March 2024',
      items: 32,
      purchased: 18,
      image: 'https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=300&h=200&fit=crop'
    },
    {
      id: 3,
      name: 'Alex\'s 30th Birthday',
      type: 'Birthday List',
      date: 'January 20, 2024',
      items: 12,
      purchased: 8,
      image: 'https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=300&h=200&fit=crop'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-4 sm:py-6 lg:py-8">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-2 sm:mb-4">Registry & Gift Lists</h1>
          <p className="text-base sm:text-lg lg:text-xl text-gray-600">Create and share your wish lists for any occasion</p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-6 sm:mb-8">
          <div className="bg-white rounded-lg shadow-md p-1 w-full max-w-md sm:max-w-none">
            <div className="grid grid-cols-3 sm:flex">
              <button
                onClick={() => setActiveTab('create')}
                className={`px-2 sm:px-6 py-2 sm:py-3 rounded-md font-medium text-xs sm:text-base ${
                  activeTab === 'create' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Create
              </button>
              <button
                onClick={() => setActiveTab('find')}
                className={`px-2 sm:px-6 py-2 sm:py-3 rounded-md font-medium text-xs sm:text-base ${
                  activeTab === 'find' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Find
              </button>
              <button
                onClick={() => setActiveTab('manage')}
                className={`px-2 sm:px-6 py-2 sm:py-3 rounded-md font-medium text-xs sm:text-base ${
                  activeTab === 'manage' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Manage
              </button>
            </div>
          </div>
        </div>

        {/* Create Registry Tab */}
        {activeTab === 'create' && (
          <div>
            <div className="text-center mb-6 sm:mb-8">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2 sm:mb-4">Choose Your Registry Type</h2>
              <p className="text-sm sm:text-base text-gray-600">Select the type of registry you'd like to create</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8 sm:mb-12">
              {registryTypes.map(registry => (
                <div key={registry.type} className="bg-white rounded-lg shadow-md p-4 sm:p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-blue-500">
                  <div className="text-center">
                    <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">{registry.icon}</div>
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">{registry.title}</h3>
                    <p className="text-sm sm:text-base text-gray-600 mb-3 sm:mb-4">{registry.description}</p>
                    <div className="space-y-1 sm:space-y-2 mb-4 sm:mb-6">
                      {registry.benefits.map((benefit, index) => (
                        <div key={index} className="flex items-center justify-center text-xs sm:text-sm text-gray-700">
                          <svg className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 mr-1 sm:mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          {benefit}
                        </div>
                      ))}
                    </div>
                    <button className="w-full bg-blue-600 text-white py-2 px-3 sm:px-4 rounded-md hover:bg-blue-700 font-medium text-sm sm:text-base">
                      Create {registry.title.split(' ')[0]}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Getting Started */}
            <div className="bg-blue-50 rounded-lg p-4 sm:p-8">
              <div className="text-center">
                <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">How It Works</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8">
                  <div className="text-center">
                    <div className="bg-blue-600 text-white w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-lg sm:text-xl font-bold mx-auto mb-3 sm:mb-4">1</div>
                    <h4 className="font-semibold text-base sm:text-lg mb-2">Create Your Registry</h4>
                    <p className="text-sm sm:text-base text-gray-600">Choose your registry type and add your favorite items</p>
                  </div>
                  <div className="text-center">
                    <div className="bg-blue-600 text-white w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-lg sm:text-xl font-bold mx-auto mb-3 sm:mb-4">2</div>
                    <h4 className="font-semibold text-base sm:text-lg mb-2">Share with Friends</h4>
                    <p className="text-sm sm:text-base text-gray-600">Send your registry link to family and friends</p>
                  </div>
                  <div className="text-center">
                    <div className="bg-blue-600 text-white w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-lg sm:text-xl font-bold mx-auto mb-3 sm:mb-4">3</div>
                    <h4 className="font-semibold text-base sm:text-lg mb-2">Receive Gifts</h4>
                    <p className="text-sm sm:text-base text-gray-600">Enjoy your gifts with free shipping and easy returns</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Find Registry Tab */}
        {activeTab === 'find' && (
          <div>
            <div className="max-w-2xl mx-auto">
              <div className="text-center mb-6 sm:mb-8">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2 sm:mb-4">Find a Registry or Gift List</h2>
                <p className="text-sm sm:text-base text-gray-600">Search for someone's registry to find the perfect gift</p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-4 sm:p-8">
                <div className="space-y-4 sm:space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Search by Name
                    </label>
                    <input
                      type="text"
                      placeholder="Enter first and last name"
                      className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
                    />
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        State/Province
                      </label>
                      <select className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base">
                        <option>Select State</option>
                        <option>California</option>
                        <option>New York</option>
                        <option>Texas</option>
                        <option>Florida</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Registry Type
                      </label>
                      <select className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base">
                        <option>All Registry Types</option>
                        <option>Wedding</option>
                        <option>Baby</option>
                        <option>Birthday</option>
                        <option>Holiday</option>
                      </select>
                    </div>
                  </div>

                  <button className="w-full bg-blue-600 text-white py-2 sm:py-3 px-4 sm:px-6 rounded-md hover:bg-blue-700 font-medium text-sm sm:text-base">
                    Search Registries
                  </button>
                </div>
              </div>

              {/* Sample Results */}
              <div className="mt-6 sm:mt-8">
                <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-3 sm:mb-4">Popular Registries</h3>
                <div className="space-y-3 sm:space-y-4">
                  {sampleRegistries.map(registry => (
                    <div key={registry.id} className="bg-white rounded-lg shadow-md p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
                      <img 
                        src={registry.image} 
                        alt={registry.name}
                        className="w-full sm:w-20 h-32 sm:h-20 object-cover rounded-lg"
                      />
                      <div className="flex-1 w-full">
                        <h4 className="font-semibold text-base sm:text-lg text-gray-900">{registry.name}</h4>
                        <p className="text-sm sm:text-base text-gray-600">{registry.type} • {registry.date}</p>
                        <div className="flex items-center mt-2">
                          <div className="bg-gray-200 rounded-full h-2 flex-1 mr-3 sm:mr-4">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${(registry.purchased / registry.items) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs sm:text-sm text-gray-600 whitespace-nowrap">
                            {registry.purchased}/{registry.items} items
                          </span>
                        </div>
                      </div>
                      <button className="w-full sm:w-auto bg-blue-600 text-white px-3 sm:px-4 py-2 rounded-md hover:bg-blue-700 text-sm sm:text-base">
                        View Registry
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Manage Registries Tab */}
        {activeTab === 'manage' && (
          <div>
            <div className="text-center mb-6 sm:mb-8">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2 sm:mb-4">Your Registries & Lists</h2>
              <p className="text-sm sm:text-base text-gray-600">Manage your existing registries and gift lists</p>
            </div>

            <div className="mb-4 sm:mb-6">
              <button className="w-full sm:w-auto bg-blue-600 text-white px-4 sm:px-6 py-2 sm:py-3 rounded-md hover:bg-blue-700 font-medium text-sm sm:text-base">
                Create New Registry
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {sampleRegistries.map(registry => (
                <div key={registry.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                  <img 
                    src={registry.image} 
                    alt={registry.name}
                    className="w-full h-32 sm:h-48 object-cover"
                  />
                  <div className="p-4 sm:p-6">
                    <div className="flex justify-between items-start mb-3 sm:mb-4">
                      <div>
                        <h3 className="text-lg sm:text-xl font-bold text-gray-900">{registry.name}</h3>
                        <p className="text-sm sm:text-base text-gray-600">{registry.type}</p>
                        <p className="text-xs sm:text-sm text-gray-500">{registry.date}</p>
                      </div>
                      <button className="text-gray-400 hover:text-gray-600">
                        <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                      </button>
                    </div>

                    <div className="mb-3 sm:mb-4">
                      <div className="flex justify-between text-xs sm:text-sm text-gray-600 mb-2">
                        <span>Progress</span>
                        <span>{registry.purchased}/{registry.items} items</span>
                      </div>
                      <div className="bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${(registry.purchased / registry.items) * 100}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                      <button className="flex-1 bg-blue-600 text-white py-2 px-3 sm:px-4 rounded-md hover:bg-blue-700 text-sm sm:text-base">
                        Manage List
                      </button>
                      <button className="flex-1 border border-gray-300 text-gray-700 py-2 px-3 sm:px-4 rounded-md hover:bg-gray-50 text-sm sm:text-base">
                        Share
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Registry;