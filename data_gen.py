from groq import Groq
import streamlit as st
import csv
import re
import time
from tqdm import tqdm  # for progress bar

# Replace the model loading code with Groq client initialization
client = Groq(
    api_key=st.secrets["GROQ_API_KEY"],
)

# List of Vietnamese dishes
dishes = [
    "Bánh cuốn", "Mì quảng", "Bánh tráng nướng", "Gỏi cuốn", "Bánh giò", "Bún mắm", "Canh chua",
    "Nem chua", "Bún riêu", "Bánh đúc", "Bánh pía", "Bánh canh", "Bánh khọt", "Bánh bột lọc",
    "Bánh căn", "Bún thịt nướng", "Bánh chưng", "Bún đậu mắm tôm", "Bánh bèo", "Bánh tét", "Cao lầu",
    "Cháo lòng", "Cá kho tộ", "Bún bò Huế", "Phở", "Xôi xéo", "Bánh mì", "Bánh xèo", "Cơm tấm", "Hủ tiếu",
    "Bánh cu đơ", "Nem nướng", "Bánh mì cay", "Cơm cháy", "Bò bía", "Bánh đậu xanh", "Bánh đa cua", "Bún cá"
]

# Function to extract content from markdown sections
def extract_section(text, section):
    section = re.escape(section)
    # Updated pattern to better match section content
    pattern = rf'{section}:\*\* (.*?)(?=\n\d\. \*\*|$)'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        # Fallback pattern without the double asterisks
        pattern = rf'{section}: (.*?)(?=\n\d\.|$)'
        match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ''

# Function to get dish data with retry mechanism
def get_dish_data(dish, max_retries=3):
    prompt = f"""You are an expert in Vietnamese cuisine. For the dish {dish}, please provide:

1. **Dish Description:** A detailed description including its origin, main ingredients, and cultural significance.
2. **How to Cook:** A basic recipe including key ingredients and preparation steps.
3. **Similar Dishes:** List dishes that are similar in ingredients, preparation, or regional variants.
4. **Famous Restaurants in Vietnam:** List at least 3 specific restaurants or food stalls in Vietnam that are famous for this dish. Include their locations and why they are known for this dish.

Please format the response exactly as shown below:

Dish: {dish}
1. **Dish Description:** [description]
2. **How to Cook:** [recipe]
3. **Similar Dishes:** [similar dishes]
4. **Famous Restaurants in Vietnam:** [List at least 3 restaurants with locations]
"""

    for attempt in range(max_retries):
        try:
            result = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192,
                temperature=0.7
            )
            
            response_text = result.choices[0].message.content
            # Add debug logging
            print(f"\nRaw response for {dish}:\n{response_text}\n")
            
            return {
                'Dish': dish,
                'Description': extract_section(response_text, 'Dish Description'),
                'Recipe': extract_section(response_text, 'How to Cook'),
                'Similar_Dishes': extract_section(response_text, 'Similar Dishes'),
                'Famous_Restaurants': extract_section(response_text, 'Famous Restaurants in Vietnam')
            }
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {dish}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait 2 seconds before retrying
            else:
                print(f"Failed to get data for {dish} after {max_retries} attempts")
                return {
                    'Dish': dish,
                    'Description': f"Error: Failed to generate data after {max_retries} attempts",
                    'Recipe': '',
                    'Similar_Dishes': '',
                    'Famous_Restaurants': ''
                }

# Prepare CSV file
csv_file = 'vietnamese_dishes.csv'
headers = ['Dish', 'Description', 'Recipe', 'Similar_Dishes', 'Famous_Restaurants']

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    
    # Generate data for each dish with progress bar
    for dish in tqdm(dishes, desc="Generating dish data"):
        row = get_dish_data(dish)
        writer.writerow(row)
        # Add a small delay between requests to avoid rate limiting
        time.sleep(1)

print(f"\nData generation complete. Results saved to {csv_file}")
