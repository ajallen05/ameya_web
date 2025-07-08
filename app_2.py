import json
import streamlit as st
from rapidfuzz import process
from collections import defaultdict
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="Dietary Score Calculator",
    page_icon="🥗",
    layout="wide"
)

# Load data from data.json
@st.cache_data
def load_data():
    json_path = r"data.json"
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"Could not find data.json at {json_path}")
        st.stop()

# Define dietary indices and their components with proper scoring
dietary_indices = {
    "AHEI-2010": {
        "components": {
            "other vegetables": 1,
            "Fruit": 1,
            "Whole Grains": 1,
            "sugar sweetened beverages": 1,  # reverse scored
            "nuts": 1,
            "fish": 1,
            "red & processed meat": 1,  # reverse scored
            "poultry (not fried, skinless)": 1,
            "dairy": 1,
            "alcohol": 1,
            "vegetable oils": 1,
            "trans fat": 1,  # reverse scored
            "n-3 fats": 1,
            "PUFA": 1
        },
        "max_score": 11,
        "description": "Alternative Healthy Eating Index - focuses on foods and nutrients that reduce chronic disease risk"
    },
    "aMED": {
        "components": {
            "other vegetables": 1,
            "Fruit": 1,
            "Whole Grains": 1,
            "legumes": 1,
            "nuts": 1,
            "fish": 1,
            "red & processed meat": 1,  # reverse scored
            "olive oil": 1,
            "alcohol": 1,
            "ratio of monounsaturated to saturated fat": 1
        },
        "max_score": 9,
        "description": "Alternative Mediterranean Diet - emphasizes traditional Mediterranean eating patterns"
    },
    "MIND": {
        "components": {
            "green leafy vegetables": 1,
            "other vegetables": 1,
            "Fruit": 1,
            "Berries": 1,
            "Whole Grains": 1,
            "nuts": 1,
            "beans & legumes": 1,
            "fish": 1,
            "poultry (not fried, skinless)": 1,
            "olive oil": 1,
            "red & processed meat": 1,  # reverse scored
            "fast and fried foods": 1,  # reverse scored
            "pastries and sweets": 1,  # reverse scored
            "butter & stick margarine": 1,  # reverse scored
            "regular cheese": 1  # reverse scored
        },
        "max_score": 15,
        "description": "Mediterranean-DASH Intervention for Neurodegenerative Delay - designed to promote brain health"
    },
    "DASH": {
        "components": {
            "other vegetables": 1,
            "Fruit": 1,
            "Whole Grains": 1,
            "nuts": 1,
            "legumes": 1,
            "low-fat dairy": 1,
            "red & processed meat": 1,  # reverse scored
            "sweets and desserts": 1,  # reverse scored
            "Sodium": 1  # reverse scored
        },
        "max_score": 8,
        "description": "Dietary Approaches to Stop Hypertension - designed to help lower blood pressure"
    },
    "PDI": {
        "components": {
            "other vegetables": 1,
            "Vegetables": 1,
            "Fruit": 1,
            "Berries": 1,
            "Whole Grains": 1,
            "Refined grains": 1,  # reverse scored
            "sugar sweetened beverages": 1,  # reverse scored
            "fruit juices": 1,  # reverse scored
            "nuts": 1,
            "legumes": 1,
            "fish": 1,
            "dairy": 1,  # reverse scored
            "egg": 1,  # reverse scored
            "red & processed meat": 1,  # reverse scored
            "poultry (not fried, skinless)": 1,  # reverse scored
            "fast and fried foods": 1,  # reverse scored
            "sweets and desserts": 1,  # reverse scored
            "animal fat": 1  # reverse scored
        },
        "max_score": 18,
        "description": "Plant-based Diet Index - emphasizes plant foods while limiting animal products"
    },
    "DII": {
        "components": {
            "Garlic (g)": 1,
            "Pepper (g)": 1,
            "Thyme/oregano (mg)": 1,
            "Rosemary (mg)": 1,
            "Green/black tea (g)": 1,
            "Ginger (g)": 1,
            "Onion (g)": 1,
            "Saffron (g)": 1,
            "Turmeric (mg)": 1,
            "Sodium": 1,  # pro-inflammatory
            "trans fat": 1,  # pro-inflammatory
            "n-3 fats": 1,  # anti-inflammatory
            "PUFA": 1,
            "Total fat (g)": 1,
            "Cholesterol (mg)": 1,
            "MUFA (g)": 1,
            "n-6 Fatty acids (g)": 1,
            "Saturated fat (g)": 1,
            "Fibre (g)": 1,  # anti-inflammatory
            "Energy (kcal)": 1,
            "Protein (g)": 1,
            "Carbohydrate (g)": 1,
            "Caffeine (g)": 1,
            "β-Carotene (μg)": 1,  # anti-inflammatory
            "Eugenol (mg)": 1,
            "Folic acid (μg)": 1,  # anti-inflammatory
            "Fe (mg)": 1,
            "Mg (mg)": 1,  # anti-inflammatory
            "Niacin (mg)": 1,  # anti-inflammatory
            "Riboflavin (mg)": 1,  # anti-inflammatory
            "Se (μg)": 1,
            "Thiamin (mg)": 1,  # anti-inflammatory
            "Zn (mg)": 1,
            "Vitamin B12 (μg)": 1,  # anti-inflammatory
            "Vitamin B6 (mg)": 1,  # anti-inflammatory
            "Vitamin A (RE)": 1,  # anti-inflammatory
            "Vitamin C (mg)": 1,  # anti-inflammatory
            "Vitamin D (μg)": 1,  # anti-inflammatory
            "Vitamin E (mg)": 1,  # anti-inflammatory
            "Anthocyanidins (mg)": 1,  # anti-inflammatory
            "Flavan-3-ol (mg)": 1,  # anti-inflammatory
            "Flavones (mg)": 1,  # anti-inflammatory
            "Flavonols (mg)": 1,  # anti-inflammatory
            "Flavonones (mg)": 1,  # anti-inflammatory
            "Isoflavones (mg)": 1  # anti-inflammatory
        },
        "max_score": 45,
        "description": "Dietary Inflammatory Index - measures the inflammatory potential of your diet"
    }
}

# Define reverse-scored components (components that reduce the score when present)
reverse_scored_components = {
    "sugar sweetened beverages", "red & processed meat", "trans fat", "fast and fried foods",
    "pastries and sweets", "butter & stick margarine", "regular cheese", "sweets and desserts",
    "Sodium", "Refined grains", "fruit juices", "dairy", "egg", "animal fat"
}

# Define positive explanations for components
component_explanations = {
    "other vegetables": "vegetables provide essential vitamins, minerals, and fiber",
    "Fruit": "fruits are rich in antioxidants, vitamins, and natural fiber",
    "Whole Grains": "whole grains provide sustained energy and important nutrients",
    "nuts": "nuts contain healthy fats, protein, and various micronutrients",
    "fish": "fish provides omega-3 fatty acids that support heart and brain health",
    "green leafy vegetables": "leafy greens are packed with folate, iron, and antioxidants",
    "Berries": "berries are high in antioxidants and may support brain health",
    "beans & legumes": "legumes provide plant protein, fiber, and important minerals",
    "poultry (not fried, skinless)": "lean poultry provides high-quality protein",
    "olive oil": "olive oil contains healthy monounsaturated fats",
    "low-fat dairy": "low-fat dairy provides calcium and protein with less saturated fat",
    "legumes": "legumes offer plant protein, fiber, and various nutrients",
    "vegetable oils": "certain vegetable oils provide healthy unsaturated fats",
    "n-3 fats": "omega-3 fatty acids support heart and brain health",
    "PUFA": "polyunsaturated fats can help reduce inflammation",
    "alcohol": "moderate alcohol consumption may have some health benefits",
    "ratio of monounsaturated to saturated fat": "higher ratio indicates healthier fat profile",
    "Vegetables": "vegetables provide essential nutrients and protective compounds",
    "Onion (g)": "onions contain anti-inflammatory compounds",
    "Garlic (g)": "garlic has anti-inflammatory and antimicrobial properties",
    "Pepper (g)": "peppers contain antioxidants and anti-inflammatory compounds",
    "Thyme/oregano (mg)": "herbs like thyme and oregano have anti-inflammatory properties",
    "Rosemary (mg)": "rosemary contains powerful antioxidants",
    "Green/black tea (g)": "tea provides antioxidants and anti-inflammatory compounds",
    "Ginger (g)": "ginger has strong anti-inflammatory effects",
    "Saffron (g)": "saffron contains antioxidants and may support mood",
    "Turmeric (mg)": "turmeric contains curcumin, a powerful anti-inflammatory compound",
    "Fibre (g)": "fiber supports digestive health and may reduce inflammation",
    "β-Carotene (μg)": "beta-carotene is an antioxidant that converts to vitamin A",
    "Eugenol (mg)": "eugenol has anti-inflammatory and antioxidant properties",
    "Folic acid (μg)": "folate supports cell division and may reduce inflammation",
    "Mg (mg)": "magnesium supports many bodily functions and may reduce inflammation",
    "Niacin (mg)": "niacin (vitamin B3) supports energy metabolism",
    "Riboflavin (mg)": "riboflavin (vitamin B2) supports cellular energy production",
    "Thiamin (mg)": "thiamin (vitamin B1) supports nervous system function",
    "Vitamin B12 (μg)": "vitamin B12 supports nerve function and red blood cell formation",
    "Vitamin B6 (mg)": "vitamin B6 supports brain function and immune system",
    "Vitamin A (RE)": "vitamin A supports vision, immune function, and cell growth",
    "Vitamin C (mg)": "vitamin C is a powerful antioxidant that supports immune function",
    "Vitamin D (μg)": "vitamin D supports bone health and immune function",
    "Vitamin E (mg)": "vitamin E is an antioxidant that protects cells from damage",
    "Anthocyanidins (mg)": "anthocyanidins are antioxidants that give fruits their color",
    "Flavan-3-ol (mg)": "flavan-3-ols are antioxidants found in tea, cocoa, and fruits",
    "Flavones (mg)": "flavones are plant compounds with anti-inflammatory effects",
    "Flavonols (mg)": "flavonols are antioxidants found in many fruits and vegetables",
    "Flavonones (mg)": "flavonones are citrus compounds with anti-inflammatory properties",
    "Isoflavones (mg)": "isoflavones are plant compounds with potential health benefits"
}

# Define negative explanations for reverse-scored components
negative_explanations = {
    "sugar sweetened beverages": "sugary drinks can lead to weight gain and increased diabetes risk",
    "red & processed meat": "high consumption may increase risk of heart disease and certain cancers",
    "trans fat": "trans fats raise bad cholesterol and increase heart disease risk",
    "fast and fried foods": "these foods are often high in unhealthy fats and calories",
    "pastries and sweets": "high sugar content can lead to blood sugar spikes and weight gain",
    "butter & stick margarine": "these fats are high in saturated fat which can raise cholesterol",
    "regular cheese": "high-fat cheese can contribute to saturated fat intake",
    "sweets and desserts": "high sugar content provides empty calories and can affect blood sugar",
    "Sodium": "excess sodium can contribute to high blood pressure",
    "Refined grains": "refined grains lack fiber and nutrients compared to whole grains",
    "fruit juices": "fruit juices are high in sugar and lack the fiber of whole fruits",
    "dairy": "in some diet indices, dairy is limited to emphasize plant-based foods",
    "egg": "in plant-based indices, eggs are limited as they're animal products",
    "animal fat": "animal fats are typically higher in saturated fat"
}

def normalize_category(category):
    """Normalize category names for better matching."""
    # Convert to lowercase and handle common variations
    category = category.lower().strip()
    
    # Map common variations
    category_mappings = {
        'vegetables': 'other vegetables',
        'leafy vegetables': 'green leafy vegetables',
        'beans': 'beans & legumes',
        'legumes': 'beans & legumes',
        'processed meat': 'red & processed meat',
        'red meat': 'red & processed meat',
        'fried foods': 'fast and fried foods',
        'desserts': 'sweets and desserts',
        'sweets': 'sweets and desserts',
        'margarine': 'butter & stick margarine',
        'butter': 'butter & stick margarine',
        'cheese': 'regular cheese',
        'refined grain': 'refined grains',
        'whole grain': 'whole grains',
        'fruit juice': 'fruit juices',
        'sweetened beverages': 'sugar sweetened beverages',
        'poultry': 'poultry (not fried, skinless)'
    }
    
    return category_mappings.get(category, category)

def calculate_dietary_scores(food_data, selected_optionals):
    """Calculate dietary scores based on food ingredients and selected optionals."""
    # Collect categories from primary and selected optional ingredients
    categories = set()
    
    # Add primary ingredient categories (normalized)
    for name, info in food_data['primary_ingredients'].items():
        normalized_cat = normalize_category(info['category'])
        categories.add(normalized_cat)
    
    # Add selected optional ingredient categories (normalized)
    for name, info in food_data['optional_ingredients'].items():
        if name in selected_optionals:
            normalized_cat = normalize_category(info['category'])
            categories.add(normalized_cat)
    
    # Calculate scores for each dietary index
    scores = []
    for index, info in dietary_indices.items():
        index_components = info['components']
        max_score = info['max_score']
        
        # Calculate actual score by checking each component only once
        score = 0
        matched_components = []
        
        for component, points in index_components.items():
            component_normalized = normalize_category(component)
            
            # Check if this component category exists in our food
            if component_normalized in categories:
                score += points
                matched_components.append(component)
            # Special case for Energy (kcal) - all foods have calories
            elif component == "Energy (kcal)":
                score += points
                matched_components.append(component)
        
        # Ensure score doesn't exceed maximum
        score = min(score, max_score)
        
        scores.append((index, score, max_score, matched_components))
    
    return scores

def get_doctor_explanation(index, score, max_score, matched_components, percentage):
    """Generate doctor-style explanation for the dietary score."""
    explanation = []
    
    # Overall assessment
    if percentage >= 70:
        explanation.append(f"**Excellent news!** Your food scores {percentage:.1f}% on the {index} scale, which is considered very good.")
    elif percentage >= 50:
        explanation.append(f"**Good progress!** Your food scores {percentage:.1f}% on the {index} scale, which is moderately healthy.")
    elif percentage >= 30:
        explanation.append(f"**Room for improvement.** Your food scores {percentage:.1f}% on the {index} scale, indicating some healthy elements but with potential for enhancement.")
    else:
        explanation.append(f"**Significant improvement needed.** Your food scores {percentage:.1f}% on the {index} scale, suggesting this food doesn't align well with this dietary pattern.")
    
    # Explain what this index measures
    explanation.append(f"\n*{dietary_indices[index]['description']}.*")
    
    # Positive aspects
    if matched_components:
        positive_components = [comp for comp in matched_components if comp not in reverse_scored_components]
        negative_components = [comp for comp in matched_components if comp in reverse_scored_components]
        
        if positive_components:
            explanation.append(f"\n**What's working well:**")
            for comp in positive_components:
                if comp in component_explanations:
                    explanation.append(f"• Your food contains **{comp.lower()}** - {component_explanations[comp]}")
                else:
                    explanation.append(f"• Your food contains **{comp.lower()}** which contributes positively to this dietary pattern")
        
        if negative_components:
            explanation.append(f"\n**Areas of concern:**")
            for comp in negative_components:
                if comp in negative_explanations:
                    explanation.append(f"• Your food contains **{comp.lower()}** - {negative_explanations[comp]}")
                else:
                    explanation.append(f"• Your food contains **{comp.lower()}** which may not align with this dietary pattern")
    
    # Suggestions for improvement
    all_components = list(dietary_indices[index]['components'].keys())
    unmatched = [comp for comp in all_components if comp not in matched_components and comp not in reverse_scored_components]
    
    if unmatched:
        explanation.append(f"\n**To improve your score, consider adding:**")
        # Show top 3 most important missing components
        important_missing = []
        for comp in unmatched[:3]:
            if comp in component_explanations:
                important_missing.append(f"• **{comp.lower()}** - {component_explanations[comp]}")
            else:
                important_missing.append(f"• **{comp.lower()}** would benefit this dietary pattern")
        
        explanation.extend(important_missing)
        
        if len(unmatched) > 3:
            explanation.append(f"• ... and {len(unmatched) - 3} other beneficial components")
    
    return "\n".join(explanation)

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
            
            # Sort scores by percentage (descending) for consistent ordering
            scores_with_percentage = [(index, score, max_score, matched_components, (score / max_score) * 100) 
                                    for index, score, max_score, matched_components in scores]
            scores_with_percentage.sort(key=lambda x: x[4], reverse=True)
            
            # Display results
            st.subheader("Results")
            st.markdown("Scores based on matched food and nutrient components for each dietary index.")
            st.info("Note: Scores are calculated based on available ingredient categories. Actual dietary index calculations may require specific nutrient quantities and thresholds.")
            
            # Create results table with consistent ordering
            results_data = []
            for index, score, max_score, matched_components, percentage in scores_with_percentage:
                results_data.append({
                    "Dietary Index": index,
                    "Score": f"{score}/{max_score}",
                    "Percentage": f"{percentage:.1f}%",
                    "Matched Components": len(matched_components)
                })
            
            st.dataframe(results_data, use_container_width=True)
            
            # Create a bar chart with the same ordering using Plotly
            st.subheader("Score Visualization")
            
            # Prepare data for Plotly chart (maintains order)
            chart_df = pd.DataFrame({
                'Dietary Index': [index for index, _, _, _, _ in scores_with_percentage],
                'Percentage': [percentage for _, _, _, _, percentage in scores_with_percentage]
            })
            
            # Create Plotly bar chart
            fig = px.bar(
                chart_df, 
                x='Dietary Index', 
                y='Percentage',
                title='Dietary Index Scores (%)',
                labels={'Percentage': 'Percentage Score (%)', 'Dietary Index': 'Dietary Index'},
                color='Percentage',
                color_continuous_scale='Blues'
            )
            
            # Update layout for better appearance
            fig.update_layout(
                xaxis_title="Dietary Index",
                yaxis_title="Percentage Score (%)",
                height=500,
                showlegend=False
            )
            
            # Add percentage labels on bars
            fig.update_traces(
                texttemplate='%{y:.1f}%',
                textposition='outside'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show percentages as text below the chart
            st.markdown("**Percentage Scores:**")
            for index, _, _, _, percentage in scores_with_percentage:
                st.write(f"• {index}: {percentage:.1f}%")
            
            # Show detailed breakdown with doctor-style explanations
            with st.expander("📋 Detailed Health Assessment"):
                st.markdown("### Professional Dietary Analysis")
                st.markdown("*Based on the ingredients in your food, here's what a nutritionist would tell you:*")
                
                # Show doctor-style explanation for each dietary index
                for index, score, max_score, matched_components, percentage in scores_with_percentage:
                    st.markdown(f"## {index}")
                    
                    # Get doctor explanation
                    doctor_explanation = get_doctor_explanation(index, score, max_score, matched_components, percentage)
                    st.markdown(doctor_explanation)
                    
                    st.markdown("---")
                
                # Summary of food components
                st.markdown("### Summary of Your Food's Components")
                
                categories = set()
                # Add primary ingredient categories
                for name, info in food_data['primary_ingredients'].items():
                    normalized_cat = normalize_category(info['category'])
                    categories.add(normalized_cat)
                
                # Add selected optional ingredient categories
                for name, info in food_data['optional_ingredients'].items():
                    if name in selected_optionals:
                        normalized_cat = normalize_category(info['category'])
                        categories.add(normalized_cat)
                
                healthy_categories = [cat for cat in categories if cat not in reverse_scored_components]
                concerning_categories = [cat for cat in categories if cat in reverse_scored_components]
                
                if healthy_categories:
                    st.markdown("**✅ Beneficial components in your food:**")
                    for category in sorted(healthy_categories):
                        if category in component_explanations:
                            st.write(f"• **{category.title()}** - {component_explanations[category]}")
                        else:
                            st.write(f"• **{category.title()}** - generally beneficial for health")
                
                if concerning_categories:
                    st.markdown("**⚠️ Components to be mindful of:**")
                    for category in sorted(concerning_categories):
                        if category in negative_explanations:
                            st.write(f"• **{category.title()}** - {negative_explanations[category]}")
                        else:
                            st.write(f"• **{category.title()}** - should be consumed in moderation")
                
                st.markdown("---")
                st.markdown("💡 **Remember:** A balanced diet includes variety, and individual foods should be considered as part of your overall eating pattern. These scores help you understand how well individual foods align with established healthy dietary patterns.")

if __name__ == "__main__":
    main()
