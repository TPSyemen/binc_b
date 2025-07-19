# E-Commerce Hub Frontend Templates

This directory contains comprehensive, modern, and responsive frontend templates for the intelligent e-commerce aggregation platform. The templates are designed with a mobile-first approach and follow WCAG accessibility guidelines.

## Template Structure

```
templates/
├── frontend/           # Public-facing templates
│   ├── base.html      # Base template with common layout
│   ├── home.html      # Homepage for visitors
│   ├── products.html  # Product search and listing
│   ├── product_detail.html  # Individual product details
│   ├── compare.html   # Product comparison tool
│   └── user_dashboard.html  # Customer account dashboard
├── admin/             # Admin interface templates
│   └── dashboard.html # Admin management dashboard
├── store/             # Store owner templates
│   └── dashboard.html # Store management dashboard
└── README.md          # This documentation file
```

## Design System

### Color Scheme
- **Primary**: #2563eb (Blue)
- **Primary Dark**: #1d4ed8
- **Success**: #10b981 (Green)
- **Warning**: #f59e0b (Amber)
- **Danger**: #ef4444 (Red)
- **Light Background**: #f8fafc
- **Text Primary**: #1e293b
- **Text Secondary**: #64748b

### Typography
- **Font Family**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700
- **Responsive scaling** with proper line heights

### Components
- **Cards**: Consistent shadow and border-radius
- **Buttons**: Multiple variants with hover effects
- **Forms**: Accessible with proper focus states
- **Navigation**: Responsive with mobile-friendly dropdowns

## Template Features

### 1. Base Template (`frontend/base.html`)
**Purpose**: Foundation template with common layout elements

**Features**:
- Responsive navigation with user authentication states
- Global CSS variables and utility classes
- Accessibility features (skip links, ARIA labels)
- Loading states and alert system
- Global JavaScript utilities
- SEO-optimized meta tags

**Key Components**:
- Navigation bar with role-based menu items
- Footer with platform information
- Message system for user feedback
- Global utility functions (currency formatting, date formatting)

### 2. Homepage (`frontend/home.html`)
**Purpose**: Landing page for visitors and authenticated users

**Features**:
- Hero section with intelligent search
- Autocomplete search functionality
- Trending products showcase
- Featured categories grid
- Best deals section
- Platform statistics
- Real-time data loading via API

**API Integration**:
- `GET /api/frontend/home_feed/` - Main content
- `GET /api/frontend/autocomplete/` - Search suggestions

### 3. Product Listing (`frontend/products.html`)
**Purpose**: Advanced product search and filtering interface

**Features**:
- Advanced filtering sidebar (categories, brands, price, rating)
- Product grid with hover effects
- Sorting options (relevance, price, rating, popularity)
- Pagination with URL state management
- Product comparison selection
- Real-time search with debouncing
- Loading states and error handling

**API Integration**:
- `GET /api/frontend/search_products/` - Product search
- Filter aggregations for dynamic filter options

### 4. Product Detail (`frontend/product_detail.html`)
**Purpose**: Comprehensive product information and interaction

**Features**:
- Product image gallery with thumbnails
- Price comparison across stores
- Customer reviews with sentiment analysis
- AI-powered product insights
- Similar product recommendations
- Price history charts
- Review submission form (authenticated users)
- Social sharing functionality

**API Integration**:
- `GET /api/frontend/product_details/` - Product information
- `POST /api/frontend/submit_review/` - Review submission
- `POST /api/frontend/track_engagement/` - User interactions

### 5. Product Comparison (`frontend/compare.html`)
**Purpose**: Side-by-side product comparison tool

**Features**:
- Dynamic comparison table
- Best value highlighting
- AI-powered comparison insights
- Add/remove products functionality
- Product search modal
- Shareable comparison URLs
- Print-friendly layout
- Mobile-responsive design

**API Integration**:
- `GET /api/frontend/compare_products/` - Comparison data
- `GET /api/frontend/search_products/` - Product search

### 6. User Dashboard (`frontend/user_dashboard.html`)
**Purpose**: Customer account management interface

**Features**:
- Activity timeline
- Review management
- Personalized recommendations
- Saved items (wishlist)
- Account settings
- Notification preferences
- Statistics and achievements

**API Integration**:
- `GET /api/frontend/user_dashboard/` - Dashboard data
- Profile and preference management endpoints

### 7. Admin Dashboard (`admin/dashboard.html`)
**Purpose**: Platform administration interface

**Features**:
- Platform metrics and KPIs
- Store management interface
- User management tools
- Review moderation
- System health monitoring
- Analytics and reporting
- Quick action buttons

**Key Sections**:
- Overview with key metrics
- Store management
- Product catalog oversight
- User management
- Review moderation
- System analytics
- Platform settings

### 8. Store Dashboard (`store/dashboard.html`)
**Purpose**: Store owner management interface

**Features**:
- Store performance metrics
- Product management
- Integration status monitoring
- Review management
- Analytics and insights
- Store settings
- Sync controls

**Key Sections**:
- Performance overview
- Product catalog
- Platform integrations
- Customer reviews
- Store analytics
- Configuration settings

## Technical Implementation

### Responsive Design
- **Mobile-first approach** with progressive enhancement
- **Breakpoints**: 
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px
- **Flexible grid system** using CSS Grid and Flexbox

### Accessibility Features
- **WCAG 2.1 AA compliance**
- **Semantic HTML** with proper heading hierarchy
- **ARIA labels** and roles for screen readers
- **Keyboard navigation** support
- **Focus management** with visible focus indicators
- **Color contrast** meeting accessibility standards

### Performance Optimization
- **Lazy loading** for images and content
- **Debounced search** to reduce API calls
- **Efficient DOM updates** with minimal reflows
- **Optimized asset loading** with CDN resources
- **Caching strategies** for API responses

### JavaScript Architecture
- **Modular approach** with reusable utility functions
- **Event delegation** for dynamic content
- **Error handling** with user-friendly messages
- **Loading states** for better UX
- **Progressive enhancement** - works without JavaScript

### API Integration
- **RESTful API consumption** with fetch API
- **Error handling** and retry logic
- **Authentication** with CSRF token management
- **Real-time updates** where appropriate
- **Optimistic UI updates** for better perceived performance

## Customization Guide

### Styling
1. **CSS Variables**: Modify the `:root` variables in `base.html` for global theme changes
2. **Component Styles**: Each template has specific styles in `<style>` blocks
3. **Responsive Breakpoints**: Adjust media queries as needed

### Content
1. **Text Content**: Update static text in templates
2. **Images**: Replace placeholder images with actual assets
3. **Branding**: Update logos, colors, and brand elements

### Functionality
1. **API Endpoints**: Update API URLs in JavaScript sections
2. **Feature Toggles**: Enable/disable features based on requirements
3. **User Roles**: Adjust navigation and content based on user permissions

## Browser Support
- **Modern browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile browsers**: iOS Safari 14+, Chrome Mobile 90+
- **Graceful degradation** for older browsers

## Dependencies
- **Bootstrap 5.3.0**: UI framework
- **Font Awesome 6.4.0**: Icons
- **Chart.js**: Data visualization
- **Inter Font**: Typography
- **No jQuery dependency**: Pure vanilla JavaScript

## Development Guidelines

### Code Style
- **Consistent indentation** (2 spaces)
- **Semantic HTML** structure
- **BEM methodology** for CSS classes where applicable
- **Descriptive variable names** in JavaScript

### Testing
- **Cross-browser testing** required
- **Mobile device testing** on various screen sizes
- **Accessibility testing** with screen readers
- **Performance testing** with Lighthouse

### Maintenance
- **Regular updates** for security and performance
- **Documentation updates** when adding features
- **Code reviews** for template modifications
- **Version control** for template changes

## Integration with Django

### Template Inheritance
```python
# In your Django views
def home_view(request):
    return render(request, 'frontend/home.html', context)
```

### URL Configuration
```python
# urls.py
urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/', views.products_view, name='products'),
    path('products/<uuid:id>/', views.product_detail_view, name='product_detail'),
    # ... other URLs
]
```

### Context Processors
Add common context variables in Django settings for global template access.

## Security Considerations
- **CSRF protection** implemented
- **XSS prevention** with proper escaping
- **Content Security Policy** headers recommended
- **Input validation** on all forms
- **Authentication checks** for protected content

## Future Enhancements
- **Progressive Web App** features
- **Offline functionality** with service workers
- **Push notifications** for price alerts
- **Advanced animations** with CSS/JS
- **Internationalization** support
- **Dark mode** theme option

## Support and Maintenance
For questions or issues with these templates, please refer to the project documentation or contact the development team.
