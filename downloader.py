from bing_image_downloader import downloader

# Download 10 images for the query "pen". Setting output_dir to the
# workspace `images` folder makes the library create `images/pen` but
# avoids creating an extra nested `pen/pen` directory.

# downloader.download("pen", limit=100, output_dir='images',timeout=60)
# downloader.download("mug", limit=100, output_dir='images',timeout=60)
# downloader.download("stapler", limit=100, output_dir='images',timeout=60)
downloader.download("phone", limit=100, output_dir='images',timeout=60)


