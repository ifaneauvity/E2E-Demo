import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Sales Forecast Input Tool", layout="wide")

# ----------- CUSTOM STYLES -----------
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        font-size: 1.2rem;
    }
    h1, h2, h3 {
        font-weight: 600;
        color: #2F3E46;
    }
    .stButton>button {
        background-color: #0078D4;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        height: 3em;
        width: auto;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🖍️ Edit June Forecast")

# ----------- LOAD FROM EXCEL -----------
uploaded_file = st.file_uploader("Upload Forecast Excel File", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()

    @st.cache_data
    def get_unique_options(df, column):
        return sorted(df[column].dropna().unique())

    # ----------- FILTERING UI -----------
    st.header("🧱 Filter Your Data")

    rep_options = ["All"] + get_unique_options(df, "Grouped Customer Owner")
    rep_name = st.selectbox("Select your name (Grouped Customer Owner)", rep_options)

    if rep_name != "All":
        df_rep = df[df["Grouped Customer Owner"] == rep_name]
    else:
        df_rep = df.copy()

    col1, col2 = st.columns(2)
    with col1:
        customer = st.selectbox("Grouped Customer", ["All"] + get_unique_options(df_rep, "Grouped Customer"))
    with col2:
        sku_name = st.selectbox("SKU Name", ["All"] + get_unique_options(df_rep, "SKU Name"))

    optional_columns = [
        "A24 Total", "A24 Total_9L", "A24 Total_Value",
        "Contract_Vol_Q1", "Contract_Vol_Q2", "Contract_Vol_Q3", "Contract_Vol_Q4",
        "Contract_Vol_Q1_9L", "Contract_Vol_Q2_9L", "Contract_Vol_Q3_9L", "Contract_Vol_Q4_9L",
        "Contract_Vol_9L", "Contract_Value_Q1", "Contract_Value_Q2", "Contract_Value_Q3", "Contract_Value_Q4",
        "RF10_9L", "RF10_Value"
    ]

    selected_optional_columns = st.multiselect("📊 Select Additional Columns to Display", optional_columns)

    mask = pd.Series([True] * len(df))
    if rep_name != "All":
        mask &= df["Grouped Customer Owner"] == rep_name
    if customer != "All":
        mask &= df["Grouped Customer"] == customer
    if sku_name != "All":
        mask &= df["SKU Name"] == sku_name

    df_filtered = df[mask]

    # ----------- CLEANING + DEFAULTS -----------
    monthly_cols = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"]
    for col in monthly_cols + ["Jun", "RF10"]:
        if col not in df_filtered.columns:
            df_filtered[col] = 0
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce").fillna(0)

    # ----------- BUILD EDITOR TABLE -----------
    display_df = df_filtered[["Grouped Customer", "SKU Name", "Jun", "RF10"]].copy()
    display_df["Progress"] = df_filtered[monthly_cols].sum(axis=1).astype(int)
    display_df["Jun"] = pd.to_numeric(display_df["Jun"], errors="coerce").fillna(0).astype(int)
    display_df["RF10"] = display_df["RF10"].round(0).astype(int)

    for col in selected_optional_columns:
        if col in df_filtered.columns:
            display_df[col] = df_filtered[col]

    main_columns = ["Grouped Customer", "SKU Name", "RF10", "Progress", "Jun"]
    final_columns = main_columns + selected_optional_columns

    edited_df = st.data_editor(
        display_df[final_columns],
        column_config={
            "Grouped Customer": st.column_config.TextColumn(disabled=True),
            "SKU Name": st.column_config.TextColumn(disabled=True),
            "RF10": st.column_config.NumberColumn(disabled=True),
            "Progress": st.column_config.NumberColumn(disabled=True),
            "Jun": st.column_config.NumberColumn(
                label="✏️ June Forecast (Editable)",
                help="Enter forecast values for June",
                format="%d",
                disabled=False
            )
        },
        use_container_width=True,
        key="editor_june"
    )

    # ----------- STORE DRAFT -----------
    if st.button("🗂️ Store Draft (Calculate Totals)"):
        st.session_state["stored_forecast"] = edited_df.copy()

    # ----------- BOTTOM TABLE AFTER CALCULATION -----------
    if "stored_forecast" in st.session_state:
        draft_df = st.session_state["stored_forecast"].copy()
        draft_df["Progress"] = df_filtered[monthly_cols].sum(axis=1).astype(int)
        draft_df["Actual + Forecast"] = (draft_df["Progress"] + draft_df["Jun"]).astype(int)
        draft_df["Forecast Gap"] = (draft_df["Actual + Forecast"] - draft_df["RF10"]).astype(int)

        total_forecast = draft_df["Jun"].sum()
        total_rf10 = draft_df["RF10"].sum()
        total_actual_forecast = draft_df["Actual + Forecast"].sum()

        # KPI cards display (styled like metric cards)
        kpi1, kpi2, kpi3 = st.columns(3)

        with kpi1:
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 2rem; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom: 0.5rem; color: #333; font-size: 1.4rem;">Total RF10</h4>
                <p style="font-size: 2rem; font-weight: bold; color: #1f77b4;">{total_rf10:,} bottles</p>
            </div>
            """, unsafe_allow_html=True)

        with kpi2:
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 2rem; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom: 0.5rem; color: #333; font-size: 1.4rem;">Total Actual + Forecast</h4>
                <p style="font-size: 2rem; font-weight: bold; color: #9467bd;">{total_actual_forecast:,} bottles</p>
            </div>
            """, unsafe_allow_html=True)

        with kpi3:
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 2rem; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom: 0.5rem; color: #333; font-size: 1.4rem;">Total June Forecast</h4>
                <p style="font-size: 2rem; font-weight: bold; color: #2ca02c;">{total_forecast:,} bottles</p>
            </div>
            """, unsafe_allow_html=True)

        # Reorder and clean up for bottom table
        table_df = draft_df[["Grouped Customer", "SKU Name", "Jun", "RF10", "Actual + Forecast", "Forecast Gap"]].copy()

        colors = ["green" if v > 0 else "red" if v < 0 else "black" for v in table_df["Forecast Gap"]]
        formatted_gap = [f"<span style='color: {color}; font-weight: bold;'>{val}</span>" for val, color in zip(table_df["Forecast Gap"], colors)]
        values = [
            table_df[col].tolist() if col != "Forecast Gap" else formatted_gap
            for col in table_df.columns
        ]

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(table_df.columns),
                fill_color='#003049',
                align='left',
                font=dict(color='white', size=18)
            ),
            cells=dict(
                values=values,
                fill_color=[['#f6f6f6', '#ffffff'] * (len(table_df) // 2 + 1)][:len(table_df)],
                align='left',
                font=dict(size=18),
                height=34,
                line_color='lightgrey'
            )
        )])
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))

        st.plotly_chart(fig, use_container_width=True)

    # ----------- SUBMIT FORM -----------
    with st.form("forecast_form"):
        submitted = st.form_submit_button("✅ Submit Forecast")

else:
    st.warning("Please upload an Excel file to get started.")
