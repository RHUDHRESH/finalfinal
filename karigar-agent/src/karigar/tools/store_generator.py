from pathlib import Path
from typing import Tuple


class StoreGenerator:
    """Generates simple static HTML storefronts for artisans."""

    OUTPUT_DIR = Path("./uploads/stores")

    def __init__(self) -> None:
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def create_store_page(self, artisan_name: str, product: dict) -> Tuple[str, str]:
        safe_name = "_".join(filter(None, artisan_name.split())) or "artisan"
        filename = f"{safe_name.lower()}_store.html"
        file_path = self.OUTPUT_DIR / filename

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{artisan_name}'s Store</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 640px; margin: 40px auto; padding: 24px; background-color: #f8fafc; }}
                .product {{ background: #fff; border-radius: 12px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); padding: 32px; }}
                img {{ width: 100%; border-radius: 8px; margin-bottom: 24px; }}
                h1 {{ margin: 0 0 16px; font-size: 28px; color: #0f172a; }}
                .price {{ font-size: 26px; color: #16a34a; font-weight: bold; margin: 12px 0; }}
                .cta {{ display: inline-block; background: #2563eb; color: white; padding: 14px 28px; border-radius: 999px; text-decoration: none; font-weight: bold; margin-top: 24px; }}
                .cta:hover {{ background: #1d4ed8; }}
            </style>
        </head>
        <body>
            <div class="product">
                <h1>{product.get('name', 'Featured Product')}</h1>
                <img src="{product.get('image', 'https://via.placeholder.com/600x400?text=Karigar+Store')}" alt="{product.get('name', 'Product')}" />
                <p class="price">₹{product.get('price', 0):,.2f}</p>
                <p>{product.get('description', 'Discover handcrafted excellence curated by our artisans.')}</p>
                <a class="cta" href="tel:{product.get('phone', '')}">Call to Order</a>
            </div>
        </body>
        </html>
        """

        file_path.write_text(html, encoding="utf-8")
        relative_url = f"/uploads/stores/{filename}"
        return str(file_path), relative_url
