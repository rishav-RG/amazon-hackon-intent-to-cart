# Intent-to-Cart: Frontend Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Project:** Amazon Hackathon - Intent to Cart Frontend  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Component Architecture](#component-architecture)
6. [User Flows](#user-flows)
7. [Summary](#Summary)
---

## Executive Summary

Intent-to-Cart Frontend is a modern React-based e-commerce UI that enables users to search for products using natural language. The application features an intelligent floating Smart Assistant powered by AI intent classification, interactive clarification dialogues, and personalized bundle recommendations. The UI mirrors Amazon's design patterns while integrating seamlessly with the FastAPI backend.

### Key Features:
- **Natural Language Shopping**: Conversational intent-based search
- **Smart Assistant**: Floating chat interface with multi-turn dialogue
- **Bundle Recommendations**: AI-curated three-tier product bundles
- **Shopping Cart**: Real-time cart management with backend sync
- **Amazon-like UX**: Sidebar navigation, product grid, checkout flow
- **Responsive Design**: Mobile-first with Tailwind CSS

---

## System Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          React Application                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    React Router (v7.9.1)                      │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐    │ │
│  │  │ Home     │ Cart     │ Deals    │ Registry │ Others   │    │ │
│  │  │ Page     │ Page     │ Page     │ Page     │ Pages    │    │ │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘    │ │
│  │         │              │           │           │             │ │
│  │         └──────────────┴───────────┴───────────┘             │ │
│  │                       │                                      │ │
│  │         ┌─────────────┴──────────────┐                       │ │
│  │         ▼                            ▼                       │ │
│  │  ┌──────────────────┐      ┌──────────────────┐             │ │
│  │  │ Shared           │      │ Layout           │             │ │
│  │  │ Components       │      │ Components       │             │ │
│  │  │                  │      │                  │             │ │
│  │  │ • ProductCard    │      │ • Navbar         │             │ │
│  │  │ • ProductGrid    │      │ • Sidebar        │             │ │
│  │  │ • SmartAssistant │      │ • Footer         │             │ │
│  │  │ • BundleCard     │      │ • Breadcrumbs    │             │ │
│  │  └──────────────────┘      └──────────────────┘             │ │
│  │         │                                                    │ │
│  │         └───────────────────┬───────────────────────┐        │ │
│  │                             ▼                       ▼        │ │
│  │                    ┌──────────────────┐  ┌─────────────┐   │ │
│  │                    │ Context (State)  │  │ Services    │   │ │
│  │                    │                  │  │ (API)       │   │ │
│  │                    │ • CartContext    │  │             │   │ │
│  │                    │ • useReducer     │  │ • api.js    │   │ │
│  │                    │ • Local Storage  │  │             │   │ │
│  │                    └──────────────────┘  └─────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│         │                                          │                │
│         │                                          ▼                │
│         │                              ┌────────────────────────┐   │
│         │                              │ Styling               │   │
│         │                              │                       │   │
│         │                              │ • Tailwind CSS (CDN)  │   │
│         │                              │ • CSS Modules         │   │
│         │                              │ • Responsive Grid     │   │
│         │                              └────────────────────────┘   │
│         │                                                            │
└─────────┼────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│       FastAPI Backend (localhost:8000)       │
│  ┌────────────┬────────────┬────────────┐   │
│  │ /v1/intent │ /v1/bundles│ /v1/cart   │   │
│  └────────────┴────────────┴────────────┘   │
│                    │                        │
│         ┌──────────┴──────────┐            │
│         ▼                     ▼            │
│   PostgreSQL          Redis Cache         │
└──────────────────────────────────────────────┘
```

### Core Concepts

| Layer | Purpose | Technologies |
|-------|---------|--------------|
| **Pages** | Route-level containers | React Router, useState |
| **Components** | Reusable UI elements | React functional components |
| **Context** | Global state management | useReducer, useContext |
| **Services** | API communication | fetch API |
| **Styling** | Visual presentation | Tailwind CSS |
| **Storage** | Persistence | localStorage, Context |

---

## Technology Stack

### Frontend Framework & Libraries

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Framework** | React | 19.1.1 | UI library for building components |
| **Routing** | React Router DOM | 7.9.1 | Client-side routing and navigation |
| **Styling** | Tailwind CSS | Latest (CDN) | Utility-first CSS framework |
| **Testing** | React Testing Library | 16.3.0 | Component testing utilities |
| **Testing** | Jest DOM | 6.8.0 | DOM matchers for assertions |
| **Performance** | Web Vitals | 2.1.4 | Measures web performance metrics |
| **Build Tool** | React Scripts | 5.0.1 | Create React App build system |
| **HTTP Client** | Fetch API | Built-in | Native browser HTTP requests |
| **State** | React Hooks | Built-in | useState, useContext, useReducer |

### Development Tools

| Tool | Purpose |
|------|---------|
| **npm** | Package management |
| **Create React App** | Project scaffolding & dev server |
| **ESLint** | Code linting |
| **GitHub Pages** | Static deployment |

### Browser Support

| Browser | Versions |
|---------|----------|
| Chrome | Latest |
| Firefox | Latest |
| Safari | Latest |
| Edge | Latest |
| Mobile Browsers | Modern (iOS 12+, Android 8+) |

---

## Project Structure

```
frontend/
├── public/
│   ├── index.html                  # Main HTML entry point
│   ├── manifest.json              # PWA manifest
│   ├── robots.txt                 # SEO robots directive
│   ├── favicon.ico                # Browser tab icon
│   └── Images/                    # Static image assets
│
├── src/
│   ├── index.js                   # React DOM render entry
│   ├── index.css                  # Global styles
│   ├── App.js                     # Root component with routing
│   ├── App.css                    # App-level styles
│   ├── App.test.js                # App component tests
│   │
│   ├── pages/                     # Page components (route-level)
│   │   ├── Home.js               # Main product grid page
│   │   ├── Cart.js               # Shopping cart page
│   │   ├── TodaysDeals.js        # Limited-time offers
│   │   ├── CustomerService.js    # Support page
│   │   ├── Registry.js           # Wishlist/Registry page
│   │   ├── GiftCards.js          # Gift card creation
│   │   └── Sell.js               # Seller program page
│   │
│   ├── components/               # Reusable UI components
│   │   ├── Navbar.js             # Top navigation bar
│   │   ├── Footer.js             # Page footer
│   │   ├── Sidebar.js            # Left sidebar (categories)
│   │   ├── ProductCard.js        # Individual product card
│   │   ├── ProductGrid.js        # Product grid display
│   │   │
│   │   └── SmartAssistant/       # AI-powered chat assistant
│   │       ├── index.js          # Barrel export
│   │       ├── SmartAssistant.js # Main assistant component
│   │       ├── ChatMessage.js    # Chat message display
│   │       ├── BundleCard.js     # Bundle recommendation card
│   │       └── SmartSearchBanner.js # Search suggestion banner
│   │
│   ├── context/                  # React Context providers
│   │   └── CartContext.js        # Global cart state (useReducer)
│   │
│   ├── services/                 # API & utility services
│   │   └── api.js                # FastAPI backend integration
│   │
│   ├── data/                     # Static data
│   │   └── products.json         # Mock product catalog
│   │
│   ├── setupTests.js             # Jest/Testing Library setup
│   ├── reportWebVitals.js        # Performance reporting
│   └── .gitignore                # Git exclusions
│
├── package.json                   # NPM dependencies & scripts
├── package-lock.json              # Locked dependency versions
└── README.md                       # Project documentation
```

### File Purposes

| File | Purpose | Key Content |
|------|---------|------------|
| **index.js** | Entry point | ReactDOM.render(App) |
| **App.js** | Root component | Routing, layout, cart provider |
| **CartContext.js** | State management | useReducer, cart actions |
| **api.js** | Backend integration | Fetch functions for endpoints |
| **Navbar.js** | Navigation UI | Search, user menu, cart count |
| **SmartAssistant.js** | AI chat | Intent→Clarification→Bundles flow |
| **ProductGrid.js** | Product list | Filtering, sorting, rendering |
| **ProductCard.js** | Product item | Image, rating, price, CTA |

---

## Component Architecture

### Component Hierarchy

```
App (Root)
├── Navbar
│   ├── Link (to="/")
│   ├── Search Form
│   │   ├── Category Dropdown
│   │   └── Search Input
│   └── Navigation Links
│
├── Routes (React Router)
│   ├── Route: Home (/)
│   │   └── Home Page
│   │       ├── Sidebar
│   │       │   └── Category List
│   │       └── ProductGrid
│   │           └── ProductCard[] (mapped)
│   │
│   ├── Route: Cart (/cart)
│   │   └── Cart Page
│   │       ├── Backend Cart Display
│   │       ├── Local Cart Display
│   │       ├── Checkout Summary
│   │       └── Checkout Button
│   │
│   ├── Route: Deals (/deals)
│   │   └── TodaysDeals Page
│   │
│   ├── Route: Registry (/registry)
│   │   └── Registry Page
│   │
│   ├── Route: Customer Service
│   ├── Route: Gift Cards
│   └── Route: Sell
│
├── Footer
│   ├── Footer Links
│   └── Copyright Info
│
└── SmartAssistant (Floating)
    ├── ChatMessage[] (Messages)
    ├── BundleCard[] (Recommendations)
    ├── Input Field
    └── Send Button
```






## User Flows

### Flow 1: Browse & Buy (Traditional)

```
User opens app
    ↓
Navbar visible
    ↓
User searches or browses categories
    ↓
ProductGrid displays filtered results
    ↓
User clicks ProductCard
    ↓
"Add to Cart" button
    ↓
Product added to local cart
    ↓ (repeat for multiple items)
    
Navigate to /cart
    ↓
Review items
    ↓
Click "Checkout"
    ↓
Order confirmation
```

### Flow 2: Smart Search (Intent-Based)

```
User clicks SmartAssistant or banner
    ↓ (or types in search banner)
User: "I need supplies for a dinner party"
    ↓
SmartAssistant.handleSendIntent()
    ↓ (POSTs to /v1/intent)
Backend classifies intent (party_supplies)
    ↓
If low confidence:
  │
  ├─ Backend: "How many guests?"
  ├─ User: "25 people"
  ├─ Backend: "What's your budget?"
  └─ User: "$300"
  
Backend builds bundle_context
    ↓
SmartAssistant.fetchBundles(intent_id)
    ↓ (GETs /v1/bundles/{intent_id})
Backend generates 3 bundles (budget, classic, premium)
    ↓
Display BundleCards in chat
    ↓
User: "I'll take the classic bundle"
    ↓
patchCart([{type: 'add', items: [...]}])
    ↓
Bundle added to backend cart (saved to localStorage)
    ↓
Message: "Added to cart! Ready to checkout?"
    ↓
User clicks checkout link
    ↓
Navigate to /cart
    ↓
Review items from both carts
    ↓
Click "Checkout"
    ↓
Order confirmation
```

### Flow 3: View Previously Ordered Items

```
Navigate to /buy-again (future feature)
    ↓
Backend queries: GET /v1/buy-again
    ↓
Display: Previously ordered items
    ↓
Quick reorder with one click
    ↓
Add to cart
    ↓
Checkout
```

## Summary

The Intent-to-Cart Frontend is a modern, responsive React application that seamlessly integrates natural language shopping with traditional e-commerce browsing. 

**Key Strengths:**

 **Modular Architecture** - Clear separation of pages, components, services  
 **State Management** - useReducer for predictable cart state  
 **API Integration** - Clean service layer with error handling  
 **Responsive Design** - Mobile-first Tailwind CSS  
 **User-Centric** - Amazon-familiar UX with AI innovation  
 **Performance** - Optimized images, lazy loading, code splitting  

**Technology Excellence:**

- **React 19**: Latest features and improvements
- **React Router v7**: Modern routing with lazy loading support
- **Tailwind CSS**: Utility-first styling at scale
- **Fetch API**: Native browser HTTP client
- **Context API**: Lightweight state management

This frontend provides an intuitive, powerful shopping experience powered by intelligent intent classification and personalized bundle recommendations, while maintaining the familiar Amazon-style interface users expect.

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Status:** Complete & Production-Ready


