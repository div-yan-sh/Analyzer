import re

# Keyword mapping for categories
KEYWORD_MAPPING = {
    "Food": [
        "burger", "pizza", "mcdonald", "kfc", "lunch", "breakfast", "dinner", 
        "restaurant", "cafe", "mess", "tea", "coffee", "starbucks", "subway", 
        "food", "swiggy", "zomato", "canteen", "samosa", "juice", "maggi", "snacks",
        "grocery", "groceries", "bistro", "eats"
    ],
    "Transport": [
        "uber", "ola", "metro", "auto", "bus", "rickshaw", "train", "ticket", 
        "cab", "taxi", "fuel", "petrol", "diesel", "rapido", "commute", "fare"
    ],
    "Education": [
        "book", "course", "notebook", "pen", "udemy", "coursera", "tuition", 
        "college", "exam", "sem", "registration", "lab", "stationery", "photocopy", 
        "print", "printer", "textbook", "tutorial", "fees"
    ],
    "Shopping": [
        "jeans", "shirt", "dress", "shoe", "sneaker", "amazon", "flipkart", 
        "myntra", "clothes", "shopping", "electronics", "mobile", "phone", 
        "laptop", "keyboard", "mouse", "headset", "earphones", "t-shirt", "jeans"
    ],
    "Entertainment": [
        "movie", "netflix", "prime", "spotify", "concert", "game", "gaming", 
        "steam", "pub", "bar", "party", "club", "bowling", "arcade"
    ],
    "Hostel/Rent": [
        "rent", "room", "pg", "hostel", "deposit", "accommodation"
    ],
    "Bills": [
        "electricity", "gas", "water", "internet", "wifi", "broadband", "bill", 
        "power", "utility"
    ],
    "Health": [
        "doctor", "medicine", "pharmacy", "clinic", "hospital", "dental", 
        "gym", "fitness", "supplement", "capsule", "syrup"
    ],
    "Recharge": [
        "jio", "airtel", "vi", "recharge", "talktime", "data pack", "topup"
    ],
    "Travel": [
        "flight", "hotel", "stay", "vacation", "trip", "tour", "holiday", 
        "irctc", "makemytrip", "goibibo", "outstation"
    ]
}

def classify_category(description, fallback_ai_func=None):
    """
    Classify expense based on description.
    First checks rule-based keywords.
    If no match and a fallback_ai_func is provided, it attempts to use Gemini, 
    otherwise falls back to "Other".
    """
    if not description:
        return "Other"
    
    desc_lower = description.lower()
    
    # Check rule-based matches
    for category, keywords in KEYWORD_MAPPING.items():
        for keyword in keywords:
            # Use regex word boundaries for precise matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, desc_lower):
                return category
                
    # Optional Gemini AI fallback
    if fallback_ai_func:
        try:
            ai_category = fallback_ai_func(description)
            # Ensure the returned category is one of the valid ones
            valid_categories = list(KEYWORD_MAPPING.keys()) + ["Other"]
            if ai_category in valid_categories:
                return ai_category
        except Exception as e:
            print(f"AI Category Fallback failed: {e}")
            
    return "Other"
