#!/usr/bin/env python
"""
Quick setup script to populate the database with plant information.
Run this once after training the model to add all plant data.
"""

from database import add_plant, get_all_plants
import os

# Define plant information
PLANTS_DATA = [
    {
        "name": "aloevera",
        "botanical": "Aloe barbadensis",
        "benefits": "Treats burns and wounds, moisturizes skin, anti-inflammatory properties, improves digestion, boosts immune system"
    },
    {
        "name": "neem",
        "botanical": "Azadirachta indica",
        "benefits": "Antibacterial and antifungal properties, treats acne and skin infections, blood purification, excellent for dental health, antimalarial effects"
    },
    {
        "name": "tulsi",
        "botanical": "Ocimum sanctum",
        "benefits": "Boosts immunity, treats common cold and cough, relieves stress and anxiety, improves respiratory health, anti-inflammatory benefits"
    },
    {
        "name": "amla",
        "botanical": "Emblica officinalis",
        "benefits": "Rich in vitamin C, improves digestion, hair growth promoter, antioxidant rich, enhances bone strength, boosts eye health"
    }
]

def setup_plants():
    """Add all plant information to the database."""
    print("=" * 60)
    print("MEDICINAL PLANTS DATABASE SETUP")
    print("=" * 60)
    
    print("\nChecking existing plants in database...")
    existing_plants = get_all_plants()
    
    if len(existing_plants) > 0:
        print(f"\n✓ Found {len(existing_plants)} plants already in database:")
        for plant in existing_plants:
            print(f"  - {plant['plant_name']} ({plant['botanical_name']})")
        
        user_input = input("\nOverwrite? (y/n): ").lower().strip()
        if user_input != 'y':
            print("Setup cancelled.")
            return
    
    print("\nAdding plants to database...\n")
    
    success_count = 0
    error_count = 0
    
    for plant_data in PLANTS_DATA:
        plant_name = plant_data["name"]
        botanical_name = plant_data["botanical"]
        benefits = plant_data["benefits"]
        
        success, message = add_plant(plant_name, botanical_name, benefits)
        
        if success:
            print(f"✓ {plant_name.upper()}")
            print(f"  └─ {message}")
            success_count += 1
        else:
            print(f"✗ {plant_name.upper()}")
            print(f"  └─ Error: {message}")
            error_count += 1
        
        print()
    
    print("=" * 60)
    print(f"SETUP COMPLETE")
    print(f"✓ Successfully added: {success_count}")
    if error_count > 0:
        print(f"✗ Errors: {error_count}")
    print("=" * 60)
    print("\nYour plant information is now in the database!")
    print("When you upload plant images and predict, the results will show")
    print("the plant name, botanical name, and medicinal benefits.\n")

if __name__ == '__main__':
    print("\n")
    setup_plants()
