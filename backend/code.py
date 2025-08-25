from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# Create PDF
file_name = "coffee_product_label.pdf"
c = canvas.Canvas(file_name, pagesize=A4)
width, height = A4

# Title
c.setFont("Helvetica-Bold", 24)
c.drawCentredString(width/2, height - 2.5*cm, "Premium Arabica Coffee Blend")

# Tagline
c.setFont("Helvetica-Oblique", 14)
c.drawCentredString(width/2, height - 3.5*cm, "Rich Aroma • Smooth Taste • Medium Roast")

# Product Description
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, height - 5*cm, "Product Description:")
c.setFont("Helvetica", 11)
description = (
    "Carefully selected 100% Arabica beans, roasted to perfection. "
    "Our medium roast delivers a balanced, smooth flavor with a rich aroma. "
    "Suitable for espresso, filter coffee, and French press."
)
c.drawString(2*cm, height - 6*cm, description)

# Ingredients
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, height - 7.5*cm, "Ingredients:")
c.setFont("Helvetica", 11)
c.drawString(2*cm, height - 8.5*cm, "100% Arabica Coffee Beans")

# Net Weight & Packaging Info
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, height - 10*cm, "Net Weight:")
c.setFont("Helvetica", 11)
c.drawString(5*cm, height - 10*cm, "250 g")

c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, height - 11*cm, "Packaging:")
c.setFont("Helvetica", 11)
c.drawString(5*cm, height - 11*cm, "Vacuum-sealed, food-grade foil pouch")

# Nutritional Information
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, height - 12.5*cm, "Nutritional Information (per 100g):")
c.setFont("Helvetica", 11)
nutrients = [
    ("Energy", "200 kcal"),
    ("Protein", "1.5 g"),
    ("Carbohydrates", "0 g"),
    ("Total Fat", "0 g"),
    ("Caffeine", "80 mg")
]
y = height - 13.5*cm
for label, value in nutrients:
    c.drawString(3*cm, y, f"{label}: {value}")
    y -= 0.7*cm

# Manufacturer Details
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, y-0.5*cm, "Manufacturer:")
c.setFont("Helvetica", 11)
c.drawString(2*cm, y-1.5*cm, "CoffeeCo Pvt. Ltd., 123 Bean Street, Bengaluru, Karnataka, India")

# Best Before & Storage
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, y-4.5*cm, "Best Before:")
c.setFont("Helvetica", 11)
c.drawString(5*cm, y-4.5*cm, "12 months from date of manufacture")

c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, y-5.5*cm, "Storage Instructions:")
c.setFont("Helvetica", 11)
c.drawString(5*cm, y-5.5*cm, "Store in a cool, dry place away from sunlight and moisture.")

# Barcode placeholder
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, y-7*cm, "Barcode:")
c.rect(3*cm, y-8*cm, 8*cm, 2*cm)

# Footer
c.setFont("Helvetica-Oblique", 10)
c.drawCentredString(width/2, 1.5*cm, "For any queries, contact: support@coffeeco.com | www.coffeeco.in")

# Save PDF
c.save()

print(f"PDF '{file_name}' generated successfully.")
