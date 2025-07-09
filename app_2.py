import json
import streamlit as st
from rapidfuzz import process
from collections import defaultdict
import pandas as pd
import plotly.express as px

# Set page config with dark theme
st.set_page_config(
    page_title="Dietary Score Calculator",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Force dark theme with custom CSS
st.markdown("""
<style>
    /* Force dark theme */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .main .block-container {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stTextInput > div > div > input,
    .stButton > button,
    .metric-container,
    .stDataFrame,
    .streamlit-expanderHeader,
    .stAlert {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #4a4a4a !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
    }
    h1, h2, h3, h4, h5, h6,
    p, div, span, li {
        color: #fafafa !important;
    }
    .css-1d391kg { /* sidebar */
        background-color: #262730 !important;
    }
    .js-plotly-plot {
        background-color: #0e1117 !important;
    }
</style>
""", unsafe_allow_html=True)

# -- Data loading & definitions here (unchanged) --
@st.cache_data
def load_data():
    json_path = "data.json"
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Could not find data.json at {json_path}")
        st.stop()

# ... dietary_indices, reverse_scored_components, component_explanations, negative_explanations ...
# ... normalize_category, calculate_dietary_scores, get_doctor_explanation ...

def main():
    st.title("🥗 Dietary Score Calculator")
    st.markdown("Calculate dietary scores for foods based on various dietary indices.")

    # 1. Load data
    data = load_data()
    foods = data['foods']
    food_names = list(foods.keys())

    # 2. Food selection
    st.header("1. Select a Food")
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input("Enter food name:", placeholder="e.g., Pizza")
    with col2:
        search_button = st.button("🔍 Search", type="primary")

    if search_button and user_input:
        best_match = process.extractOne(user_input, food_names)
        if best_match and best_match[1] >= 50:
            st.session_state.selected_food = best_match[0]
            st.session_state.food_data = foods[best_match[0]]
            msg = "Exact match found" if best_match[1]==100 else f"Found closest match: **{best_match[0]}** (confidence: {best_match[1]:.1f}%)"
            st.success(msg)
        else:
            st.error(f"No close match for '{user_input}'")
            st.session_state.selected_food = None
            st.session_state.food_data = None

    # 3. Show food info
    if st.session_state.get('selected_food'):
        food_name = st.session_state.selected_food
        food_data = st.session_state.food_data

        st.header(f"2. Food Information: {food_name}")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Serving Size", food_data['usda_serving_size'])
        with c2:
            st.metric("Total Calories", f"{food_data['total_serving_calories']} kcal")

        # Primary ingredients table
        primary_list = [{
            "Ingredient": n,
            "Quantity": i['quantity_per_serving'],
            "Category": i['category'],
            "Calories": f"{i['calorific_value']} kcal"
        } for n, i in food_data['primary_ingredients'].items()]
        if primary_list:
            st.dataframe(primary_list, use_container_width=True)

        # Optional ingredients
        st.subheader("3. Optional Ingredients")
        selected_optionals = []
        opt_items = list(food_data['optional_ingredients'].items())
        cols = st.columns(2)
        for idx, (name, info) in enumerate(opt_items):
            with cols[idx % 2]:
                if st.checkbox(f"{name}", key=f"opt_{name}"):
                    selected_optionals.append(name)

        # 4. Calculate and display
        if st.button("📊 Calculate Dietary Scores", type="primary"):
            st.header("4. Dietary Scores")
            if selected_optionals:
                st.markdown("**Selected Optionals:** " + ", ".join(selected_optionals))

            scores = calculate_dietary_scores(food_data, selected_optionals)
            scores_pct = [(i, s, m, comps, s/m*100) for i,s,m,comps in scores]
            scores_pct.sort(key=lambda x: x[4], reverse=True)

            # Results table
            results = [{
                "Dietary Index": i,
                "Score": f"{s}/{m}",
                "Percentage": f"{pct:.1f}%",
                "Matched Components": len(comps)
            } for i,s,m,comps,pct in scores_pct]
            st.dataframe(results, use_container_width=True)

            # Bar chart
            df = pd.DataFrame({
                "Dietary Index": [i for i, *_ in scores_pct],
                "Percentage": [pct for *_, pct in scores_pct]
            })
            fig = px.bar(df, x="Dietary Index", y="Percentage")
            fig.update_layout(
                plot_bgcolor='#0e1117',
                paper_bgcolor='#0e1117',
                font_color='#fafafa'
            )
            fig.update_xaxes(color='#fafafa', gridcolor='#4a4a4a')
            fig.update_yaxes(color='#fafafa', gridcolor='#4a4a4a')
            st.plotly_chart(fig, use_container_width=True)

            # Detailed analysis
            with st.expander("📋 Detailed Health Assessment"):
                st.markdown("### Professional Dietary Analysis")
                for i, s, m, comps, pct in scores_pct:
                    st.markdown(f"## {i}")
                    st.markdown(get_doctor_explanation(i, s, m, comps, pct))
                    st.markdown("---")

                # Summary of categories
                st.markdown("### Summary of Your Food's Components")
                categories = set()
                for info in food_data['primary_ingredients'].values():
                    categories.add(normalize_category(info['category']))
                for name in selected_optionals:
                    categories.add(normalize_category(food_data['optional_ingredients'][name]['category']))

                for cat in sorted(categories):
                    st.write(f"• {cat.title()}")

if __name__ == "__main__":
    main()
