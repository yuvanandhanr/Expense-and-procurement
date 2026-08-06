from PIL import Image, ImageDraw, ImageFont

def create_invoice_image():
    # Create a white image
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Try to load a default font
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    d.text((50, 50), "VENDOR INVOICE", fill=(0,0,0), font=font)
    d.text((50, 100), "Invoice Number: INV-9999", fill=(0,0,0), font=font)
    d.text((50, 150), "Date: 2026-08-05", fill=(0,0,0), font=font)
    d.text((50, 250), "Item 1: Server Hardware     $4,000.00", fill=(0,0,0), font=font)
    d.text((50, 300), "Item 2: Software License    $2,500.00", fill=(0,0,0), font=font)
    
    d.text((50, 400), "Total Amount:", fill=(0,0,0), font=font)
    d.text((350, 400), "$6,500.00", fill=(0,0,0), font=font)
    
    img.save("test_invoice.png")
    print("Created test_invoice.png")

if __name__ == "__main__":
    create_invoice_image()
