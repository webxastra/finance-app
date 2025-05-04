"""
Training data for expense categorization

This module provides training data for the expense categorizer model, including
examples for both main categories and detailed subcategories.
"""

import random
import logging

logger = logging.getLogger(__name__)

# Main category training data with balanced examples (15 categories, 30 examples each)
MAIN_CATEGORY_TRAINING_DATA = {
    "descriptions": [
        # Food & Dining (30 examples)
        "Grocery shopping at Walmart", "Restaurant dinner with friends", "Coffee at Starbucks",
        "Pizza delivery from Domino's", "Breakfast at IHOP", "Weekly grocery haul",
        "Lunch at food court", "Fast food at McDonald's", "Beer and snacks", 
        "Meal prep ingredients", "Dinner at Italian restaurant", "Smoothie shop",
        "Bakery items", "Takeout Chinese food", "Grocery delivery from Instacart",
        "Convenience store snacks", "Ice cream shop", "Whole Foods Market",
        "Food truck lunch", "Meal kit delivery", "Trader Joe's groceries",
        "Deli sandwich", "Office lunch", "Burger King drive-thru",
        "Costco bulk food purchase", "Sushi restaurant", "Organic grocery store",
        "Birthday dinner celebration", "Farm market vegetables", "Coffee beans and supplies",
        
        # Transportation (30 examples)
        "Gas station fill up", "Monthly train pass", "Uber ride home", "Car repair service",
        "Oil change and tire rotation", "Bus ticket", "Subway fare", "Parking garage fee",
        "Highway toll payment", "New tires for car", "Lyft to airport", "Car insurance premium",
        "Car wash", "Bike repair", "Monthly car payment", "Annual vehicle registration",
        "Electric scooter rental", "Car parts for DIY repair", "Motorcycle maintenance",
        "Parking meter", "Bridge toll", "Airport parking", "Taxi fare", "Car inspection",
        "Rental car for weekend", "Jump start service", "Car detailing", "Ferry ticket",
        "Train ticket for vacation", "Windshield wiper replacement",
        
        # Housing (30 examples)
        "Monthly rent payment", "Mortgage payment", "Property taxes", "Home insurance premium",
        "Electricity bill", "Plumber service call", "New sofa purchase", "Lawn mowing service",
        "Home renovation supplies", "New kitchen appliance", "Home cleaning service",
        "Carpet cleaning", "Window replacement", "Air conditioner repair",
        "Bedroom furniture", "Home office chair", "Lawn fertilizer", "Bathroom remodel costs",
        "Home security system", "Pest control service", "Landscaping project",
        "HOA monthly fee", "House painting service", "Replacing kitchen sink",
        "Smart home devices", "Garden supplies", "New mattress", "Home warranty coverage",
        "Water heater replacement", "Down payment on house",
        
        # Utilities (30 examples)
        "Water bill", "Internet service monthly", "Cell phone bill", "Natural gas bill",
        "Sewer service", "Trash collection fee", "Home phone service", "TV cable package",
        "Streaming subscription", "Electricity monthly bill", "Internet installation fee",
        "Solar panel lease", "Cell phone plan upgrade", "New WiFi router", "Gas bill",
        "Water filter service", "Energy bill payment", "Phone case and accessories",
        "Utility deposit for new home", "Generator fuel", "New smartphone purchase",
        "Cable box rental fee", "Late fee on electricity bill", "Propane tank refill",
        "Phone screen repair", "TV streaming device", "Internet data overage fee",
        "Battery replacement", "Phone charger", "Smart thermostat",
        
        # Healthcare (30 examples)
        "Doctor's office co-pay", "Prescription medication", "Dentist appointment",
        "Health insurance premium", "Eye doctor visit", "Therapy session",
        "Urgent care visit", "New glasses", "Monthly contact lenses", "Chiropractor visit",
        "Medical test copay", "Medical equipment", "Dermatologist appointment", 
        "Specialist consultation", "Dental cleaning", "Physical therapy session",
        "Vitamin supplements", "First aid supplies", "Gym membership fee", "Orthodontist payment",
        "Medical billing payment", "Over the counter medication", "Lab test fee",
        "Mental health counseling", "Health savings account contribution", "Hospital copay",
        "Pharmacy checkout", "Acupuncture session", "Nutrition counseling", "Weight loss program",
        
        # Entertainment (30 examples)
        "Movie theater tickets", "Netflix monthly fee", "Concert tickets",
        "Video game purchase", "Sporting event tickets", "Spotify subscription",
        "Bowling night", "Book purchase", "Museum admission", "Theater tickets",
        "Music album download", "Amusement park entry", "Board game purchase",
        "Magazine subscription", "Online movie rental", "Disney+ subscription",
        "Miniature golf", "Zoo admission", "HBO Max subscription", "Gaming console",
        "Art supplies", "Live music bar cover charge", "Comedy club tickets",
        "Theme park annual pass", "Movie streaming rental", "Kindle book purchase",
        "Hobby supplies", "Subscription box delivery", "Arcade games", "Festival tickets",
        
        # Shopping (30 examples)
        "New jeans at department store", "Online clothes shopping", "Electronics store purchase",
        "Amazon order", "Home goods at Target", "Back to school shopping", "New shoes purchase",
        "Cosmetics at Sephora", "Gift purchase", "Online order from Wayfair",
        "Sporting goods store", "Home Depot supplies", "Craft store materials",
        "Jewelry purchase", "Office supplies", "New smartphone case", "Discount store shopping",
        "Bath & Body Works", "Subscription box", "Pet store supplies", "Best Buy purchase",
        "Holiday decoration shopping", "Clothing at mall", "Baby items at Buy Buy Baby",
        "Sports equipment", "New handbag", "Online marketplace purchase", "Dollar store items",
        "Thrift store finds", "Shopping mall purchases",
        
        # Education (30 examples)
        "University tuition payment", "College textbooks", "Online course subscription",
        "School supplies", "Continuing education seminar", "Professional certification fee",
        "Language learning app subscription", "SAT prep class", "Private tutor session",
        "Student loan payment", "Elementary school fees", "School fundraiser donation",
        "Musical instrument rental", "Summer camp registration", "Educational toys",
        "College application fee", "Coding bootcamp payment", "Art school supplies",
        "Educational field trip", "Music lessons", "Professional development workshop",
        "MBA program tuition", "School uniform purchase", "Learning materials",
        "Technical course fee", "Academic conference registration", "Scientific calculator",
        "School club dues", "Vocational training program", "Laptop for school",
        
        # Personal Care (30 examples)
        "Haircut and styling", "Spa day package", "Manicure and pedicure", "Massage therapy session",
        "Facial treatment", "Gym membership fee", "Personal trainer session", "Hair care products",
        "Men's grooming supplies", "Salon hair coloring", "Yoga class package", "Toothpaste and dental supplies",
        "Skincare products", "Shaving supplies", "Wellness retreat", "Fitness equipment",
        "Waxing appointment", "Makeup products", "Body wash and lotion", "Deodorant and personal hygiene",
        "Eyebrow threading", "Tanning salon", "Perfume purchase", "Electric razor", "Contact lens solution",
        "Nail salon visit", "Hair styling tools", "Laser hair removal", "Teeth whitening", "Anti-aging cream",
        
        # Travel (30 examples)
        "Flight tickets to Miami", "Hotel stay in Chicago", "Airbnb booking for weekend",
        "Rental car for vacation", "All-inclusive resort package", "Cruise ship booking",
        "Train tickets for Europe trip", "Travel insurance policy", "Airport parking fee",
        "Tourist attraction tickets", "Travel guide books", "Beach vacation rental",
        "Ski trip lift tickets", "Foreign currency exchange", "Luggage purchase",
        "Theme park vacation package", "Travel vaccination", "Passport renewal fee",
        "International data plan", "Hotel room service", "Subway pass in foreign city",
        "Souvenir shopping", "Mountain cabin rental", "Camping site reservation",
        "Travel agency service fee", "Resort activities", "Duty-free shopping",
        "Boat tour excursion", "Breakfast at hotel", "Travel size toiletries",
        
        # Investments (30 examples)
        "Stock market investment", "Mutual fund contribution", "Retirement account deposit",
        "Cryptocurrency purchase", "Real estate investment", "Investment property down payment",
        "Brokerage account fee", "Financial advisor fee", "Bond purchase", "Gold investment",
        "Dividend reinvestment", "Robo-advisor fee", "Investment seminar", "Index fund purchase",
        "Investment property repairs", "Treasury bills purchase", "Business investment capital",
        "Real estate taxes", "IRA contribution", "ETF purchase", "Stock trading commission",
        "401k contribution", "Investment property insurance", "Silver coins purchase",
        "Investment research subscription", "Property manager fee", "REIT investment",
        "Stock option purchase", "Annuity investment", "Collectible investment",
        
        # Gifts & Donations (30 examples)
        "Birthday gift for friend", "Wedding present", "Holiday gift shopping",
        "Charitable donation to Red Cross", "Church donation", "Baby shower gift",
        "Graduation present", "Gift card purchase", "Donation to local food bank",
        "Anniversary gift", "Housewarming present", "Fundraiser contribution",
        "Tip to service worker", "Political campaign donation", "Gift for teacher",
        "Hospital charity donation", "Children's charity sponsorship", "Museum donation",
        "Environmental organization contribution", "Animal shelter donation", "Wedding gift cash",
        "Gift basket delivery", "Flowers for sick friend", "GoFundMe contribution",
        "Gift for coworker", "Religious tithing", "Disaster relief donation",
        "University alumni donation", "Personalized gift order", "Gift wrap service",
        
        # Insurance (30 examples)
        "Car insurance premium", "Home insurance payment", "Health insurance monthly premium",
        "Life insurance policy payment", "Renter's insurance", "Dental insurance premium",
        "Pet insurance plan", "Travel insurance purchase", "Vision insurance payment",
        "Umbrella insurance policy", "Insurance deductible payment", "Motorcycle insurance",
        "Disability insurance premium", "Long-term care insurance", "Insurance policy upgrade",
        "Flood insurance premium", "Business insurance payment", "Jewelry insurance rider",
        "Boat insurance premium", "Identity theft insurance", "Critical illness insurance",
        "Accident insurance premium", "Supplemental health insurance", "Wedding insurance",
        "Electronics insurance plan", "Funeral insurance policy", "Mobile phone insurance",
        "Gap insurance for car loan", "Earthquake insurance", "Homeowners association insurance",
        
        # Taxes (30 examples)
        "Federal tax payment", "State income tax", "Property tax bill", "Tax preparation service fee",
        "Self-employment tax payment", "Vehicle registration tax", "Sales tax on large purchase",
        "Tax software purchase", "Local income tax", "Estimated quarterly tax payment",
        "Back taxes payment", "Tax filing extension fee", "Tax consultant service",
        "Real estate transfer tax", "Personal property tax", "School district tax",
        "Business tax filing", "Tax penalty payment", "City income tax", "County tax bill",
        "Use tax payment", "Luxury tax on purchase", "Inheritance tax payment", "Tax lien payment",
        "Gift tax payment", "Excise tax", "IRS payment agreement", "Tax audit representation fee",
        "Road tax payment", "Import duty tax",
        
        # Miscellaneous (30 examples)
        "ATM withdrawal fee", "Bank account monthly fee", "Currency exchange fee",
        "Safe deposit box rental", "Money order purchase", "Late payment fee",
        "Notary public service", "Legal document preparation", "Credit card annual fee",
        "Credit report fee", "Membership club dues", "Professional association fee",
        "Storage unit rental", "Mail shipping costs", "Passport photos", "Moving truck rental",
        "Pet boarding service", "Veterinary visit", "Dog grooming", "Pet supplies",
        "Cigarettes purchase", "Lottery tickets", "Laundromat service", "Dry cleaning",
        "Newspaper subscription", "Public records request fee", "Background check fee",
        "Returned check fee", "Wire transfer fee", "Identity verification service"
    ],
    
    "categories": [
        # 30 Food & Dining examples
        "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining",
        "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining",
        "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining",
        "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining",
        "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining",
        "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining",
        
        # 30 Transportation examples
        "Transportation", "Transportation", "Transportation", "Transportation", "Transportation",
        "Transportation", "Transportation", "Transportation", "Transportation", "Transportation",
        "Transportation", "Transportation", "Transportation", "Transportation", "Transportation",
        "Transportation", "Transportation", "Transportation", "Transportation", "Transportation",
        "Transportation", "Transportation", "Transportation", "Transportation", "Transportation",
        "Transportation", "Transportation", "Transportation", "Transportation", "Transportation",
        
        # 30 Housing examples
        "Housing", "Housing", "Housing", "Housing", "Housing", 
        "Housing", "Housing", "Housing", "Housing", "Housing",
        "Housing", "Housing", "Housing", "Housing", "Housing",
        "Housing", "Housing", "Housing", "Housing", "Housing",
        "Housing", "Housing", "Housing", "Housing", "Housing",
        "Housing", "Housing", "Housing", "Housing", "Housing",
        
        # 30 Utilities examples
        "Utilities", "Utilities", "Utilities", "Utilities", "Utilities",
        "Utilities", "Utilities", "Utilities", "Utilities", "Utilities",
        "Utilities", "Utilities", "Utilities", "Utilities", "Utilities",
        "Utilities", "Utilities", "Utilities", "Utilities", "Utilities",
        "Utilities", "Utilities", "Utilities", "Utilities", "Utilities",
        "Utilities", "Utilities", "Utilities", "Utilities", "Utilities",
        
        # 30 Healthcare examples
        "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
        "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
        "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
        "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
        "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
        "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
        
        # 30 Entertainment examples
        "Entertainment", "Entertainment", "Entertainment", "Entertainment", "Entertainment",
        "Entertainment", "Entertainment", "Entertainment", "Entertainment", "Entertainment",
        "Entertainment", "Entertainment", "Entertainment", "Entertainment", "Entertainment",
        "Entertainment", "Entertainment", "Entertainment", "Entertainment", "Entertainment",
        "Entertainment", "Entertainment", "Entertainment", "Entertainment", "Entertainment",
        "Entertainment", "Entertainment", "Entertainment", "Entertainment", "Entertainment",
        
        # 30 Shopping examples
        "Shopping", "Shopping", "Shopping", "Shopping", "Shopping",
        "Shopping", "Shopping", "Shopping", "Shopping", "Shopping",
        "Shopping", "Shopping", "Shopping", "Shopping", "Shopping",
        "Shopping", "Shopping", "Shopping", "Shopping", "Shopping",
        "Shopping", "Shopping", "Shopping", "Shopping", "Shopping",
        "Shopping", "Shopping", "Shopping", "Shopping", "Shopping",
        
        # 30 Education examples
        "Education", "Education", "Education", "Education", "Education",
        "Education", "Education", "Education", "Education", "Education",
        "Education", "Education", "Education", "Education", "Education",
        "Education", "Education", "Education", "Education", "Education",
        "Education", "Education", "Education", "Education", "Education",
        "Education", "Education", "Education", "Education", "Education",
        
        # 30 Personal Care examples
        "Personal Care", "Personal Care", "Personal Care", "Personal Care", "Personal Care",
        "Personal Care", "Personal Care", "Personal Care", "Personal Care", "Personal Care",
        "Personal Care", "Personal Care", "Personal Care", "Personal Care", "Personal Care",
        "Personal Care", "Personal Care", "Personal Care", "Personal Care", "Personal Care",
        "Personal Care", "Personal Care", "Personal Care", "Personal Care", "Personal Care",
        "Personal Care", "Personal Care", "Personal Care", "Personal Care", "Personal Care",
        
        # 30 Travel examples
        "Travel", "Travel", "Travel", "Travel", "Travel",
        "Travel", "Travel", "Travel", "Travel", "Travel",
        "Travel", "Travel", "Travel", "Travel", "Travel",
        "Travel", "Travel", "Travel", "Travel", "Travel",
        "Travel", "Travel", "Travel", "Travel", "Travel",
        "Travel", "Travel", "Travel", "Travel", "Travel",
        
        # 30 Investments examples
        "Investments", "Investments", "Investments", "Investments", "Investments",
        "Investments", "Investments", "Investments", "Investments", "Investments",
        "Investments", "Investments", "Investments", "Investments", "Investments",
        "Investments", "Investments", "Investments", "Investments", "Investments",
        "Investments", "Investments", "Investments", "Investments", "Investments",
        "Investments", "Investments", "Investments", "Investments", "Investments",
        
        # 30 Gifts & Donations examples
        "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations",
        "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations",
        "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations",
        "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations",
        "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations",
        "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations", "Gifts & Donations",
        
        # 30 Insurance examples
        "Insurance", "Insurance", "Insurance", "Insurance", "Insurance",
        "Insurance", "Insurance", "Insurance", "Insurance", "Insurance",
        "Insurance", "Insurance", "Insurance", "Insurance", "Insurance",
        "Insurance", "Insurance", "Insurance", "Insurance", "Insurance",
        "Insurance", "Insurance", "Insurance", "Insurance", "Insurance",
        "Insurance", "Insurance", "Insurance", "Insurance", "Insurance",
        
        # 30 Taxes examples
        "Taxes", "Taxes", "Taxes", "Taxes", "Taxes",
        "Taxes", "Taxes", "Taxes", "Taxes", "Taxes",
        "Taxes", "Taxes", "Taxes", "Taxes", "Taxes",
        "Taxes", "Taxes", "Taxes", "Taxes", "Taxes",
        "Taxes", "Taxes", "Taxes", "Taxes", "Taxes",
        "Taxes", "Taxes", "Taxes", "Taxes", "Taxes",
        
        # 30 Miscellaneous examples
        "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous",
        "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous",
        "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous",
        "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous",
        "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous",
        "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous", "Miscellaneous"
    ]
}

# Define subcategory training data with common examples
SUBCATEGORY_DATA = {
    # Food & Dining subcategories with examples
    "Groceries": [
        "Walmart grocery shopping", "Kroger weekly haul", "Supermarket purchase", 
        "Aldi grocery run", "Safeway food shopping", "Trader Joe's groceries",
        "Whole Foods Market", "Food Lion purchase", "Grocery delivery from Instacart",
        "Farm market vegetables", "Bulk food purchase", "Organic grocery store",
        "Target grocery section", "Publix supermarket", "Ethnic food market",
        "Meat from butcher shop", "Fresh produce stand", "Costco bulk food"
    ],
    "Restaurants": [
        "Dinner at steakhouse", "Italian restaurant", "Family dinner out", 
        "Seafood restaurant", "Anniversary dinner", "Business lunch meeting",
        "Date night dinner", "Upscale restaurant", "Buffet restaurant",
        "Mexican restaurant", "Asian fusion restaurant", "Fine dining experience",
        "Restaurant week special", "Dinner with colleagues", "Birthday celebration dinner"
    ],
    "Fast Food": [
        "McDonald's drive-thru", "Burger King meal", "Taco Bell order", 
        "Wendy's fast food", "KFC chicken", "Subway sandwich", "Chipotle burrito bowl",
        "Chick-fil-A lunch", "Pizza Hut delivery", "Arby's sandwich meal",
        "Panda Express takeout", "Five Guys burgers", "Popeyes chicken",
        "In-N-Out burger", "Raising Cane's chicken"
    ],
    "Coffee Shops": [
        "Starbucks coffee", "Local coffee shop", "Coffee and pastry", 
        "Dunkin' Donuts coffee", "Morning cappuccino", "Caffeine fix",
        "Coffee shop meeting", "Latte and scone", "Specialty coffee purchase",
        "Iced coffee afternoon", "Coffee bean purchase", "Espresso shot"
    ],
    
    # Transportation subcategories with examples
    "Gas & Fuel": [
        "Shell gas station", "Chevron fill up", "Exxon gas purchase",
        "BP gas station", "Gas for commute", "Diesel fuel purchase",
        "Costco gas station", "Marathon gas fill up", "76 gas station",
        "Quick fuel stop", "Full tank of gas", "Premium fuel purchase"
    ],
    "Public Transportation": [
        "Monthly subway pass", "Bus ticket purchase", "Train ticket commute",
        "Light rail fare", "Transit card reload", "Weekly train pass",
        "Subway fare", "City bus ticket", "Commuter rail pass",
        "Transit system day pass", "Trolley ticket", "Express bus fare"
    ],
    "Ride Sharing": [
        "Uber ride home", "Lyft to airport", "Shared ride service",
        "Uber Eats delivery", "Lyft ride to work", "Late night Uber",
        "Airport rideshare", "Uber XL for group", "Lyft Line shared ride",
        "Ride home from event", "Rideshare tip", "Uber comfort ride"
    ],
    "Car Maintenance": [
        "Oil change service", "Tire rotation", "Car repair shop",
        "Brake service", "Engine tune-up", "Transmission repair",
        "Car battery replacement", "Car fluid check", "Wheel alignment",
        "Vehicle inspection", "Auto parts store", "Car detailing service"
    ],
    
    # Housing subcategories with examples
    "Mortgage/Rent": [
        "Monthly rent payment", "Mortgage payment", "Apartment rent",
        "Housing payment", "Lease payment", "Room rent",
        "Condo payment", "Townhouse rent", "Monthly housing",
        "Rent check", "Mortgage bill", "Home payment"
    ],
    "Home Maintenance": [
        "Plumber service call", "Electrician repair", "HVAC maintenance",
        "Lawn care service", "Handyman repairs", "Roof repair",
        "Carpet cleaning", "House cleaning service", "Chimney sweep",
        "Gutter cleaning", "Drain cleaning", "Window washing service"
    ],
    "Home Improvement": [
        "Home Depot supplies", "Lowe's purchase", "Renovation materials",
        "Paint supplies", "Bathroom remodel", "Kitchen upgrade",
        "New flooring materials", "Home renovation project", "Landscaping supplies",
        "DIY project materials", "Deck building supplies", "Remodeling contractor"
    ],
    "Furniture": [
        "New sofa purchase", "Bedroom furniture", "Dining table set",
        "Office desk and chair", "IKEA furniture", "Mattress purchase",
        "Bookshelf assembly", "Living room chair", "Patio furniture",
        "TV stand", "Nightstand purchase", "Furniture delivery fee"
    ]
}

def generate_detailed_training_data():
    """
    Generate a comprehensive dataset for detailed category training.
    This dynamically creates training examples for all subcategories
    based on the main category examples.
    
    Returns:
        dict: Dictionary with descriptions and corresponding detailed categories
    """
    descriptions = []
    categories = []
    
    # Import category hierarchy from categorizer.py
    from .categorizer import CATEGORY_HIERARCHY
    
    # First, include all the explicit subcategory examples
    for subcategory, examples in SUBCATEGORY_DATA.items():
        descriptions.extend(examples)
        categories.extend([subcategory] * len(examples))
    
    logger.info(f"Added {len(descriptions)} explicit subcategory examples")
    
    # For subcategories without explicit examples, generate some from main categories
    for main_category, subcategories in CATEGORY_HIERARCHY.items():
        # Find main category examples from the main training dataset
        main_examples = []
        for i, cat in enumerate(MAIN_CATEGORY_TRAINING_DATA["categories"]):
            if cat == main_category:
                main_examples.append(MAIN_CATEGORY_TRAINING_DATA["descriptions"][i])
        
        # For each subcategory
        for subcategory in subcategories:
            # Skip subcategories that already have examples
            if subcategory in SUBCATEGORY_DATA:
                continue
                
            # Generate some examples by adding the subcategory name to some examples
            subcategory_examples = []
            
            # Create 5-10 examples for this subcategory
            num_examples = min(len(main_examples), random.randint(5, 10))
            
            # Get random examples from the main category
            selected_examples = random.sample(main_examples, num_examples)
            
            for example in selected_examples:
                # Create a new description that includes the subcategory name
                words = subcategory.lower().split()
                if any(word in example.lower() for word in words):
                    # The subcategory name is already in the example
                    subcategory_examples.append(example)
                else:
                    # Add a version with the subcategory mentioned
                    # Try to make it sound natural
                    templates = [
                        f"{example} for {subcategory}",
                        f"{subcategory} - {example}",
                        f"{example} ({subcategory})",
                        f"{subcategory} {example.lower()}"
                    ]
                    subcategory_examples.append(random.choice(templates))
            
            # Add these examples to our dataset
            descriptions.extend(subcategory_examples)
            categories.extend([subcategory] * len(subcategory_examples))
    
    # Log the final count
    logger.info(f"Generated {len(descriptions)} total detailed category examples")
    
    # Return the complete dataset
    return {
        "descriptions": descriptions,
        "categories": categories
    }

# Add a few special cases for common edge cases
EDGE_CASE_EXAMPLES = [
    ("Venmo payment to friend", "Miscellaneous"),
    ("PayPal purchase", "Miscellaneous"),
    ("Cash withdrawal", "Miscellaneous"),
    ("Bank transfer", "Miscellaneous"),
    ("ACH deposit", "Miscellaneous"),
    ("Zelle payment", "Miscellaneous"),
    ("Square payment", "Miscellaneous"),
    ("Check deposit", "Miscellaneous"),
    ("ATM withdrawal", "Miscellaneous"),
    ("Payment received", "Miscellaneous"),
    ("Credit card payment", "Miscellaneous"),
    ("Stripe payment", "Miscellaneous"),
    ("Bitcoin purchase", "Investments"),
    ("Direct deposit", "Miscellaneous"),
    ("Interest earned", "Investments")
]

# Add these to the main training data
for description, category in EDGE_CASE_EXAMPLES:
    MAIN_CATEGORY_TRAINING_DATA["descriptions"].append(description)
    MAIN_CATEGORY_TRAINING_DATA["categories"].append(category) 