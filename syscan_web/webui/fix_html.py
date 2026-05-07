import re

# Fix index.html - remove CDN links
with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove CDN script tags
content = re.sub(r'<script src="https://kit\.fontawesome\.com/.*?</script>\s*', '', content)
content = re.sub(r'<script src="https://cdn\.tailwindcss\.com.*?</script>\s*', '', content)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open('public/index.html', 'r', encoding='utf-8') as f:
    final = f.read()
    print('CDN removed:', 'fontawesome' not in final and 'tailwindcss' not in final)
