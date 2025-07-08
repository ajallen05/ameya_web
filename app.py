import json
import streamlit as st
from rapidfuzz import process
from collections import defaultdict

# Set page config
st.set_page_config(
    page_title="Dietary Score Calculator",
    page_icon="🥗",
    layout="wide"
)

# Load data from data.json
@st.cache_data
def load_data():
    json_path = r"C:\Users\ADMIN\OneDrive\Desktop\Ameya\second_web\data.json"
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"Could not find data.json at {json_path}")
        st.stop()

# Define dietary indices and their components
dietary_indices = {
    "AHEI-2010": {
        "components": [
            "other vegetables", "Fruit", "Whole Grains", "sugar sweetened beverages",
            "nuts", "fish", "red & processed meat", "poultry (not fried, skinless)",
            "dairy", "alcohol", "vegetable oils", "trans fat", "n-3 fats", "PUFA"
        ],
        "max_score": 11
    },
    "aMED": {
        "components": [
            "other vegetables", "Fruit", "Whole Grains", "legumes", "nuts", "fish",
            "red & processed meat", "olive oil", "alcohol", "ratio of monounsaturated to saturated fat"
        ],
        "max_score": 9
    },
    "MIND": {
        "components": [
            "green leafy vegetables", "other vegetables", "Fruit", "Berries", "Whole Grains",
            "nuts", "beans & legumes", "fish", "poultry (not fried, skinless)", "olive oil",
            "red & processed meat", "fast and fried foods", "pastries and sweets",
            "butter & stick margarine", "regular cheese"
        ],
        "max_score": 15
    },
    "DASH": {
        "components": [
            "other vegetables", "Fruit", "Whole Grains", "nuts", "legumes", "low-fat dairy",
            "red & processed meat", "sweets and desserts", "Sodium"
        ],
        "max_score": 8
    },
    "PDI": {
        "components": [
            "other vegetables", "Vegetables", "Fruit", "Berries", "Whole Grains", "Refined grains",
            "sugar sweetened beverages", "fruit juices", "nuts", "legumes", "fish", "dairy",
            "egg", "red & processed meat", "poultry (not fried, skinless)", "fast and fried foods",
            "sweets and desserts", "animal fat"
        ],
        "max_score": 18
    },
    "DII": {
        "components": [
            "Garlic (g)", "Pepper (g)", "Thyme/oregano (mg)", "Rosemary (mg)", "Green/black tea (g)",
            "Ginger (g)", "Onion (g)", "Saffron (g)", "Turmeric (mg)", "Sodium", "trans fat", "n-3 fats",
            "PUFA", "Total fat (g)", "Cholesterol (mg)", "MUFA (g)", "n-6 Fatty acids (g)",
            "Saturated fat (g)", "Fibre (g)", "Energy (kcal)", "Protein (g)", "Carbohydrate (g)",
            "Caffeine (g)", "β-Carotene (μg)", "Eugenol (mg)", "Folic acid (μg)", "Fe (mg)", "Mg (mg)",
            "Niacin (mg)", "Riboflavin (mg)", "Se (μg)", "Thiamin (mg)", "Zn (mg)", "Vitamin B12 (μg)",
            "Vitamin B6 (mg)", "Vitamin A (RE)", "Vitamin C (mg)", "Vitamin D (μg)", "Vitamin E (mg)",
            "Anthocyanidins (mg)", "Flavan-3-ol (mg)", "Flavones (mg)", "Flavonols (mg)", "Flavonones (mg)",
            "Isoflavones (mg)"
        ],
        "max_score": 45
    }
}

def calculate_dietary_scores(food_data, selected_optionals):
    """Calculate dietary scores based on food ingredients and selected optionals."""
    # Collect categories from primary and selected optional ingredients
    categories = set()
    
    # Add primary ingredient categories
    for name, info in food_data['primary_ingredients'].items():
        categories.add(info['category'])
    
    # Add selected optional ingredient categories
    for name, info in food_data['optional_ingredients'].items():
        if name in selected_optionals:
            categories.add(info['category'])
    
    # Calculate scores for each dietary index
    scores = []
    for index, info in dietary_indices.items():
        index_components = info['components']
        max_score = info['max_score']
        score = sum(1 for comp in index_components if comp in categories)
        
        # Add Energy (kcal) if total calories are present (all foods in data.json have this)
        if "Energy (kcal)" in index_components:
            score += 1  # Since all foods have a total_serving_calories
            
        scores.append((index, score, max_score))
    
    return scores

def main():
    st.title("🥗 Dietary Score Calculator")
    st.markdown("Calculate dietary scores for foods based on various dietary indices.")
    
    # Load data
    data = load_data()
    foods = data['foods']
    food_names = list(foods.keys())
    
    # Initialize session state
    if 'selected_food' not in st.session_state:
        st.session_state.selected_food = None
    if 'food_data' not in st.session_state:
        st.session_state.food_data = None
    
    # Food selection section
    st.header("1. Select a Food")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_input(
            "Enter food name:", 
            placeholder="e.g., Pizza",
            help="Type a food name to search for it in the database"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary")
    
    # Search functionality
    if search_button and user_input:
        # Fuzzy match to find the closest food name
        best_match = process.extractOne(user_input, food_names)
        if best_match and best_match[1] >= 50:  # Threshold for match confidence
            st.session_state.selected_food = best_match[0]
            st.session_state.food_data = foods[best_match[0]]
            if best_match[1] < 100:
                st.info(f"Found closest match: **{best_match[0]}** (confidence: {best_match[1]:.1f}%)")
            else:
                st.success(f"Exact match found: **{best_match[0]}**")
        else:
            st.error(f"No close match found for '{user_input}'. Please try a different food name.")
            st.session_state.selected_food = None
            st.session_state.food_data = None
    
    # Display food information if selected
    if st.session_state.selected_food and st.session_state.food_data:
        food_name = st.session_state.selected_food
        food_data = st.session_state.food_data
        
        st.header(f"2. Food Information: {food_name}")
        
        # Food summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Serving Size", food_data['usda_serving_size'])
        with col2:
            st.metric("Total Calories", f"{food_data['total_serving_calories']} kcal")
        
        # Primary ingredients
        st.subheader("Primary Ingredients")
        primary_ingredients_data = []
        for name, info in food_data['primary_ingredients'].items():
            primary_ingredients_data.append({
                "Ingredient": name,
                "Quantity": info['quantity_per_serving'],
                "Category": info['category'],
                "Calories": f"{info['calorific_value']} kcal"
            })
        
        if primary_ingredients_data:
            st.dataframe(primary_ingredients_data, use_container_width=True)
        
        # Optional ingredients selection
        st.subheader("3. Optional Ingredients")
        st.markdown("Select any optional ingredients that you want to include:")
        
        selected_optionals = []
        if food_data['optional_ingredients']:
            # Create columns for better layout
            num_cols = 2
            cols = st.columns(num_cols)
            
            optional_items = list(food_data['optional_ingredients'].items())
            for i, (name, info) in enumerate(optional_items):
                with cols[i % num_cols]:
                    if st.checkbox(
                        f"{name}",
                        key=f"opt_{name}",
                        help=f"Quantity: {info['quantity_per_serving']}, Category: {info['category']}, Calories: {info['calorific_value']} kcal"
                    ):
                        selected_optionals.append(name)
        else:
            st.info("No optional ingredients available for this food.")
        
        # Calculate and display scores
        if st.button("📊 Calculate Dietary Scores", type="primary"):
            st.header("4. Dietary Scores")
            
            # Show selected optional ingredients
            if selected_optionals:
                st.subheader("Selected Optional Ingredients:")
                for ingredient in selected_optionals:
                    st.write(f"• {ingredient}")
            
            # Calculate scores
            scores = calculate_dietary_scores(food_data, selected_optionals)
            
            # Display results
            st.subheader("Results")
            st.markdown("Scores based on matched food and nutrient components for each dietary index.")
            st.info("Note: Limited nutrient data may affect accuracy.")
            
            # Create results table
            results_data = []
            for index, score, max_score in scores:
                percentage = (score / max_score) * 100
                results_data.append({
                    "Dietary Index": index,
                    "Score": f"{score}/{max_score}",
                    "Percentage": f"{percentage:.1f}%"
                })
            
            st.dataframe(results_data, use_container_width=True)
            
            # Create a bar chart
            st.subheader("Score Visualization")
            chart_data = {}
            for index, score, max_score in scores:
                chart_data[index] = (score / max_score) * 100
            
            st.bar_chart(chart_data)
            
            # Show detailed breakdown
            with st.expander("View Detailed Breakdown"):
                st.subheader("Matched Categories")
                categories = set()
                
                # Add primary ingredient categories
                for name, info in food_data['primary_ingredients'].items():
                    categories.add(info['category'])
                
                # Add selected optional ingredient categories
                for name, info in food_data['optional_ingredients'].items():
                    if name in selected_optionals:
                        categories.add(info['category'])
                
                st.write("**Categories found in this food:**")
                for category in sorted(categories):
                    st.write(f"• {category}")
                
                # Show which components matched for each index
                for index, info in dietary_indices.items():
                    st.write(f"\n**{index} Components:**")
                    matched_components = []
                    for comp in info['components']:
                        if comp in categories:
                            matched_components.append(f"✅ {comp}")
                        else:
                            matched_components.append(f"❌ {comp}")
                    
                    # Show only first 10 components to avoid clutter
                    for comp in matched_components[:10]:
                        st.write(f"  {comp}")
                    if len(matched_components) > 10:
                        st.write(f"  ... and {len(matched_components) - 10} more components")

if __name__ == "__main__":
    main()