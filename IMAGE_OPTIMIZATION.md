# Image Optimization Guide

This document explains the image optimization system implemented to ensure product photos don't impact system performance when uploading large quantities.

## Features

### 1. **Automatic Image Compression on Upload**

Compression happens in the model layer (`Product.save()`, `ProductImage.save()`,
`Brand.save()`, `ExclusiveBrand.save()`), so it applies no matter which door the
upload came through — staff portal, Django Admin, or a management command.

Every uploaded image is automatically:
- **Rotated upright** from its EXIF orientation (phone photos otherwise appear sideways)
- **Resized** to max 1200x1200px (larger images are scaled down)
- **Compressed** to progressive JPEG at 85% quality
- **Renamed** to the extension it actually holds, so a `.png` upload is stored as `.jpg`

Company and supplier **logos keep their transparency** and stay PNG, rather than
being flattened onto a white rectangle.

Re-saving a product does **not** re-compress its stored image. Only a genuinely
new upload is re-encoded, so repeated edits cannot slowly degrade a photo.

**Result**: Image files are typically 50-70% smaller than original uploads.

**Configuration** (in `settings.py`) — these values are read at runtime:
```python
IMAGE_OPTIMIZATION = {
    'MAX_WIDTH': 1200,
    'MAX_HEIGHT': 1200,
    'QUALITY': 85,
    'THUMBNAIL_SIZE': (300, 300),
    'THUMBNAIL_QUALITY': 75,
}
```

### 1b. **Separate Thumbnails for Listing Pages**

Each product stores a second, small image in `Product.thumbnail`, generated
automatically from the main image. Listing pages — the catalogue grid, the home
page, company pages and the quote basket — read `product.list_image`, which
serves the thumbnail and falls back to the full image if one has not been
generated yet.

This matters most on the catalogue, where 24 products load at once: those cards
now pull ~12KB thumbnails instead of ~150KB full-size photos. Only the product
detail page loads the full 1200px image.

### 1c. **Backfilling Existing Images**

Images stored before this system existed are handled by a management command:

```bash
python manage.py optimize_images --dry-run   # report only
python manage.py optimize_images             # apply
```

It re-compresses oversized files and fills in missing thumbnails. It is safe to
re-run — a second run is a no-op — and it never rewrites a file when
re-encoding would make it larger.

### 2. **Lazy Loading**

Product images use browser-native lazy loading:
```html
<img src="{{ product.image.url }}" loading="lazy" decoding="async" />
```

**Benefits**:
- Images only load when they become visible
- Reduces initial page load time
- Saves bandwidth for users who don't scroll

### 3. **Responsive Image Sizing**

Images use CSS `sizes` attribute for responsive delivery:
```html
<img src="{{ product.image.url }}" 
     loading="lazy" 
     decoding="async"
     sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw">
```

This tells browsers the expected image width at different screen sizes.

### 4. **Asynchronous Image Decoding**

```html
<img src="{{ product.image.url }}" decoding="async" />
```

Prevents image decoding from blocking page rendering on slower devices.

### 5. **Placeholder Backgrounds**

All images have placeholder backgrounds while loading:
```html
<img class="bg-gray-50" />
```

Prevents layout shifts (Cumulative Layout Shift issues).

## File Structure

```
products/
├── image_utils.py          # Image compression utilities
├── forms.py                # ProductForm with image optimization
└── models.py               # Brand and Product models

templates/
└── products/
    ├── list.html           # Lazy loading & responsive images
    ├── detail.html         # Optimized detail view
    └── _results.html       # Search results with optimization

settings.py                 # IMAGE_OPTIMIZATION configuration
```

## Performance Impact

### Before Optimization
- Product image: ~2-5 MB
- Page with 20 products: ~40-100 MB images
- Load time: 10-30 seconds on slow connections

### After Optimization
- Product image: ~300-600 KB (compressed)
- Page with 20 products: ~6-12 MB images  
- Load time: 2-5 seconds on slow connections
- **Performance improvement: 70-85% reduction**

## Bulk Upload with CSV

When uploading products via CSV:
1. Images are NOT included in CSV (only metadata)
2. Upload images separately through staff portal edit page
3. Images are automatically optimized on upload

**CSV Format**:
```
name,category,description,cost_price,stock_quantity,is_exclusive,specifications
Long Grain Rice,Grains,Premium rice,45.00,100,false,
```

## Best Practices

### Image Upload Guidelines
1. **Source images**: 1500x1500px or larger (will be optimized down)
2. **File format**: JPG or PNG (automatically converted to optimized JPEG)
3. **File size**: Doesn't matter - will be compressed anyway
4. **Batch uploads**: Upload many products without performance concerns

### Browser Support
- **Lazy loading**: All modern browsers (Chrome, Firefox, Safari, Edge)
- **Responsive sizes**: All modern browsers
- **Async decoding**: Chrome 65+, Firefox 63+, Safari 15+

### Monitoring

Check image sizes:
```bash
# List media files by size (largest first)
du -sh media/products/* | sort -hr

# Check average size
du -sh media/products/
```

## Future Enhancements

Possible optimizations for future consideration:

1. **WebP Format** - Even better compression
   ```html
   <picture>
     <source srcset="image.webp" type="image/webp">
     <img src="image.jpg">
   </picture>
   ```

2. **CDN Delivery** - Serve images from edge locations
   - AWS CloudFront
   - Cloudflare
   - Bunny CDN

3. **Progressive JPEG** - Better perceived load time
   ```python
   img.save('output.jpg', 'jpeg', quality=85, progressive=True)
   ```

4. **Automatic Thumbnail Generation** - For listing pages
   - Separate thumbnail model
   - Auto-generate on image upload

5. **Image Processing Queue** - For very large batches
   - Celery task queue
   - Process images in background

## Troubleshooting

### Images look blurry
- **Cause**: Compression quality too low
- **Fix**: Increase `QUALITY` setting (was 85, try 90-95)
- **Trade-off**: Larger file sizes

### Images loading very slowly
- **Cause**: Lazy loading not working
- **Check**: Browser DevTools → Network tab
- **Solution**: Ensure `loading="lazy"` attribute is present

### Out of disk space
- **Cause**: Too many original images + compressed versions
- **Solution**: Clean up old/unused images from media folder

### Images not optimizing
- **Cause**: PIL/Pillow not working properly
- **Check**: `python -c "from PIL import Image; print('OK')"`
- **Fix**: Reinstall Pillow: `pip install --upgrade pillow`
