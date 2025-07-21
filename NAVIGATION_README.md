# Reusable Navigation Component

This project now uses a centralized navigation component that eliminates the need to duplicate navigation code across all HTML pages.

## How It Works

The navigation component is implemented in `assets/js/navigation.js` and automatically:

1. **Detects the current page** based on the URL path
2. **Generates the appropriate navigation** with correct active states
3. **Handles relative paths** for different page locations
4. **Includes all styling** needed for the navigation
5. **Supports special features** like the animated GPT link

## Usage

To use the navigation component in any HTML page:

1. **Include the script** in the `<head>` section:
   ```html
   <script src="assets/js/navigation.js"></script>
   ```

2. **Add a placeholder comment** in the `<body>`:
   ```html
   <!-- Navigation will be automatically inserted here by navigation.js -->
   ```

3. **Include required dependencies**:
   ```html
   <!-- Bootstrap CSS -->
   <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
   <!-- Font Awesome -->
   <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
   ```

## Features

### Automatic Page Detection
- Portfolio: `/` or `/index.html`
- Travel Blog: `/travel/`
- Tech Blog: `/tech/`
- GPT: `/gpt/`

### Dynamic Path Resolution
The component automatically calculates the correct relative paths based on the current page location:
- Root pages: `./`
- Subdirectory pages: `../` or `../../`

### Navigation Items
- Portfolio
- Travel-Blog
- YouTube (external link)
- Tech-Blog
- Open GPT (with special animation)

### Social Media Links
- LinkedIn
- YouTube
- Instagram
- Twitter

## Benefits

1. **Single Source of Truth**: All navigation changes are made in one file
2. **Consistent Styling**: All pages automatically get the same navigation styling
3. **Easy Maintenance**: Adding new pages or changing links only requires updating the JavaScript file
4. **Automatic Active States**: The current page is automatically highlighted
5. **Responsive Design**: Works on all screen sizes

## Files Updated

The following files have been updated to use the new navigation component:

- `index.html` (main portfolio page)
- `travel/index.html` (travel blog)
- `tech/tech-index.html` (tech blog)
- `gpt/gpt-index.html` (GPT page)

## Testing

You can test the navigation component by opening any of the updated pages. The navigation should appear at the top with the correct active state for the current page.

## Future Enhancements

To add new navigation items or modify existing ones, simply update the `getNavItems()` method in `assets/js/navigation.js`. 