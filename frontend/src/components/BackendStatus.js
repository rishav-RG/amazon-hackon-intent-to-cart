import React, { useState, useEffect } from 'react';
import { API_ENDPOINTS } from '../config/api';

/**
 * BackendStatus - Shows connection status to backend
 * Displays a small indicator in the corner
 */
const BackendStatus = () => {
  const [status, setStatus] = useState('checking'); // 'checking', 'connected', 'disconnected'
  const [lastCheck, setLastCheck] = useState(null);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.health, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        setStatus('connected');
        setLastCheck(new Date());
      } else {
        setStatus('disconnected');
      }
    } catch (error) {
      setStatus('disconnected');
    }
  };

  useEffect(() => {
    // Check on mount
    checkBackendHealth();

    // Check every 30 seconds
    const interval = setInterval(checkBackendHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'disconnected':
        return 'bg-red-500';
      case 'checking':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Backend Connected';
      case 'disconnected':
        return 'Backend Disconnected';
      case 'checking':
        return 'Checking...';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-white rounded-lg shadow-lg p-3 flex items-center gap-2 text-sm">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${status === 'checking' ? 'animate-pulse' : ''}`} />
        <span className="font-medium text-gray-700">{getStatusText()}</span>
        {lastCheck && status === 'connected' && (
          <span className="text-xs text-gray-500">
            ({lastCheck.toLocaleTimeString()})
          </span>
        )}
      </div>
    </div>
  );
};

export default BackendStatus;
