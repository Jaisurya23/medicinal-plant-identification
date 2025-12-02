#!/usr/bin/env python
"""Script to add sample medicinal plants to the database."""

import sys
sys.path.insert(0, 'C:\\Users\\SAMCORE_ECE\\Desktop\\python pratice\\project\\medicine-plant-Identification')

from database import add_plant

# Sample plants data
plants_data = [
    {
        'plant_name': 'Neem',
        'botanical_name': 'Azadirachta indica',
        'benefits': 'Neem is a powerful medicinal plant used to treat skin disorders, reduce acne and pimples. It boosts immunity, promotes dental health, regulates blood sugar levels, and has anti-inflammatory properties. It is also used for treating infections and improving overall skin health.'
    },
    {
        'plant_name': 'Aloe Vera',
        'botanical_name': 'Aloe barbadensis miller',
        'benefits': 'Aloe Vera is excellent for treating burns and wounds. It moisturizes skin naturally, reduces acne scars, and aids in digestion. Rich in antioxidants and vitamins, it boosts immune function, promotes healthy hair growth, and has anti-inflammatory properties that help with various skin conditions.'
    },
    {
        'plant_name': 'Amla',
        'botanical_name': 'Phyllanthus emblica',
        'benefits': 'Amla (Indian Gooseberry) is rich in Vitamin C and strengthens immunity. It prevents hair fall, promotes hair growth, and improves hair color. Amla improves digestion, maintains healthy cholesterol levels, and is excellent for skin health. It also acts as a natural detoxifier and anti-aging agent.'
    },
    {
        'plant_name': 'Curry Leaf',
        'botanical_name': 'Murraya koenigii',
        'benefits': 'Curry leaves are rich in nutrients and promote hair health, prevent premature greying, and reduce hair loss. They aid in digestion, regulate blood sugar levels, and have antibacterial properties. Curry leaves support weight management, reduce inflammation, and are beneficial for treating anemia due to their iron content.'
    }
]

print("Adding sample medicinal plants to database...\n")

for plant in plants_data:
    success, message = add_plant(
        plant['plant_name'],
        plant['botanical_name'],
        plant['benefits']
    )
    
    if success:
        print(f"✓ Added: {plant['plant_name']} ({plant['botanical_name']})")
    else:
        print(f"✗ Error adding {plant['plant_name']}: {message}")

print("\nDone! All sample plants have been added to the database.")
