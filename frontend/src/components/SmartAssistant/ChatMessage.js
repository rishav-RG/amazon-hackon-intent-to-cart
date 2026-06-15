import React from 'react';

/**
 * Single chat message bubble — system (left, white) or user (right, blue).
 */
const ChatMessage = ({ role, content, children }) => {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-white text-gray-800 border border-gray-200 rounded-bl-md shadow-sm'
        }`}
      >
        {content && <p className="whitespace-pre-wrap">{content}</p>}
        {children}
      </div>
    </div>
  );
};

export default ChatMessage;
