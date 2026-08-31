# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 19:00:39 2026

@author: Administrator
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Taxonomy Dashboard", layout="wide")

# ---------------------------------------------------------------------------
# Global plotly config: no zoom / no pan (better on touchscreens)
# ---------------------------------------------------------------------------
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
}


def lock_chart(fig):
    """Disable zoom/pan/drag so charts behave well on touchscreens."""
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(dragmode=False)
    return fig


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------
if "entered" not in st.session_state:
    st.session_state.entered = False

if not st.session_state.entered:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #000000;
        }
        .landing-wrap {
            max-width: 720px;
            margin: 6vh auto 0 auto;
            font-family: Georgia, 'Times New Roman', serif;
            color: #f2f2f2;
        }
        .landing-title {
            font-size: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        .landing-stats {
            text-align: center;
            font-size: 1.25rem;
            margin-bottom: 2.5rem;
        }
        .landing-text {
            font-size: 1.15rem;
            line-height: 1.9;
            margin-bottom: 1.5rem;
            text-align: justify;
        }
        </style>

        <div class="landing-wrap">
            <div class="landing-title">General Interpersonal Trust Scale Explorer</div>
            <div class="landing-stats">37 Trust Scales &nbsp;|&nbsp; 659 Items &nbsp;|&nbsp; 17 Trust Constructs</div>
            <div class="landing-text">Discover how existing trust measures relate to one another through semantic analysis.</div>
            <div class="landing-text">General interpersonal trust has been measured in many different ways over the past decades. This tool brings these measures together into one interactive resource, allowing you to explore trust scales, compare constructs, browse individual items, and better understand how different approaches to measuring trust relate to one another.</div>
            <div class="landing-text">This tool allows researchers to understand what each scale measures, making it easier to choose appropriate instruments, compare studies, identify conceptual overlap, develop future measures of generalized interpersonal trust.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid_col, _ = st.columns([1, 2, 1])
    with mid_col:
        if st.button("Explore →", use_container_width=True):
            st.session_state.entered = True
            st.rerun()

    st.stop()

# ---------------------------------------------------------------------------
# Color palette (17 colors)
# ---------------------------------------------------------------------------
BASE_COLORS = [
    "#C85C6F",
    "#5D9C73",
    "#C7A94A",
    "#5A78C9",
    "#C98550",
    "#7E62B3",
    "#4FA8AF",
    "#B95AA9",
    "#88A93B",
    "#CFA0A0",
    "#3E7E7E",
    "#B9A8D8",
    "#9B7653",
    "#7A4C4C",
    "#7C8340",
    "#485B9B",
    "#555555",
]


def get_color_map(labels):
    labels = sorted(labels)
    palette = BASE_COLORS if len(labels) <= len(BASE_COLORS) else px.colors.qualitative.Alphabet
    return {label: palette[i % len(palette)] for i, label in enumerate(labels)}


def trim_columns(df):
    """Trim whitespace from column names."""
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# Data upload — main dataset (GI TRUST TAXONOMY sheet)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel('./Data/General Interpersonal Trust Taxonomy and other.xlsx', sheet_name='GI TRUST TAXONOMY')
    df = trim_columns(df)
    required = {"New label", "Text", "Original label", "Author"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Columns missing: {missing}")
        st.stop()

    # Trim
    for col in ["New label", "Original label", "Author"]:
        df[col] = df[col].astype(str).str.strip()

    df["Original label|Author"] = df["Original label"] + " | " + df["Author"]
    return df


st.title("Taxonomy Explorer")

df_full = load_data()

scales = sorted(df_full["Original label"].unique())
authors = sorted(df_full["Author"].unique())
color_map = get_color_map(df_full["New label"].unique())

# ---------------------------------------------------------------------------
# Universal filters — Scale / Author (applies to all tabs below)
# ---------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Filters")
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        selected_scales = st.multiselect("Filter by scale", scales, default=[], key="filter_scales")
    with fcol2:
        selected_authors = st.multiselect("Filter by author", authors, default=[], key="filter_authors")

df_scales = df_full[df_full["Original label"].isin(selected_scales)] if selected_scales else df_full
df_authors = df_full[df_full["Author"].isin(selected_authors)] if selected_authors else df_full
if selected_scales and selected_authors:
    df = pd.concat([df_scales, df_authors], axis=0, ignore_index=True).drop_duplicates()
elif selected_scales:
    df = df_scales
elif selected_authors:
    df = df_authors
else:
    df = df_full

m1, m2, m3, m4 = st.columns(4)
m1.metric("Number of items", len(df))
m2.metric("Scale | Author", df["Original label|Author"].nunique())
m3.metric("New labels", df["New label"].nunique())
m4.metric("Unique authors", df["Author"].nunique())

# ---------------------------------------------------------------------------
# Top navigation
# ---------------------------------------------------------------------------
tab_taxonomy, tab_search, tab_create = st.tabs(
    ["GI Taxonomy", "Item Search", "Create your own scale"]
)

# ---------------------------------------------------------------------------
# Tab 1 — GI Taxonomy
# ---------------------------------------------------------------------------
with tab_taxonomy:
    st.title("GI Taxonomy")

    st.markdown(
        """
        Use this tab to explore how items from a specific **scale** are distributed across the
        **General Interpersonal Trust** taxonomy labels. Pick a New Label below to see which
        scale/author combinations contribute to it, ranked by percentage of their items that fall
        under that label. Use the **Filters** panel above to narrow the dataset by scale or author
        before ranking.
        """
    )

    if df.empty:
        st.warning("Looks like you filtered everything out")
    else:
        selected_label = st.selectbox("Select New Label", sorted(df["New label"].unique()))

        table_pct = pd.crosstab(df["Original label|Author"], df["New label"], normalize="index")
        table_cnt = pd.crosstab(df["Original label|Author"], df["New label"])

        if selected_label not in table_pct.columns:
            st.warning("Looks like you filtered everything out")
        else:
            filtered_pct = table_pct[selected_label]
            filtered_pct = filtered_pct[filtered_pct > 0].sort_values(ascending=True)  # ascending -> najveci na vrhu
            filtered_cnt = table_cnt[selected_label].loc[filtered_pct.index]

            fig = go.Figure(
                go.Bar(
                    y=filtered_pct.index,
                    x=filtered_pct.values * 100,
                    orientation="h",
                    marker=dict(color=color_map[selected_label], line=dict(color="black", width=0.6)),
                    customdata=filtered_cnt.values,
                    hovertemplate="<b>%{y}</b><br>%{x:.1f}%% (%{customdata} items)<extra></extra>",
                )
            )
            fig.update_layout(
                height=max(400, 28 * len(filtered_pct)),
                xaxis=dict(title="Percent (%)"),
                yaxis=dict(title="Scale | Author", automargin=True),
                template="plotly_white",
                font=dict(family="Times New Roman", size=13),
                margin=dict(l=10, r=10, t=30, b=10),
            )
            fig = lock_chart(fig)
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

            csv_out = df[df["New label"] == selected_label].drop(columns=['Original label|Author', 'New label']).rename(columns={'Cosine similarity': f'Cosine similarity with {selected_label}'})
            st.dataframe(csv_out, use_container_width=True, height=400, hide_index=True)
            st.download_button(
                "Download as CSV",
                csv_out.to_csv(index=False).encode("utf-8"),
                file_name=f"{selected_label}.csv",
                mime="text/csv",
            )

# ---------------------------------------------------------------------------
# Tab 2 — Item Search
# ---------------------------------------------------------------------------
with tab_search:
    st.title("Keyword search")

    query = st.text_input("Type here")
    case_sensitive = st.checkbox("Case sensitive", value=False)

    if query:
        mask = df["Text"].str.contains(query, case=case_sensitive, na=False, regex=False)
        results = df[mask]
        if case_sensitive == False:
            st.write(f"**{len(results)}** out of {len(df)} items have your keyword.")
        else:
            st.write(f"**{len(results)}** out of {len(df)} items have your keyword (Case sensitive).")

        display_df = results[["Original label|Author", "New label", "Text"]].reset_index(drop=True)
        st.table(display_df)

        st.download_button(
            "Download as CSV",
            display_df.to_csv(index=False).encode("utf-8"),
            file_name=f"search_results_{query}.csv",
            mime="text/csv",
        )
    else:
        st.info("Type something")

# ---------------------------------------------------------------------------
# Tab 3 — Create your own scale (Randomizer)
# ---------------------------------------------------------------------------
with tab_create:
    st.title("Create your own scale")

    if df.empty:
        st.warning("Looks like you filtered everything out")
    else:
        has_cosine = "Cosine similarity" in df.columns

        if has_cosine:
            cos_threshold = st.slider(
                "Minimum cosine similarity",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.01,
                help="Only items with a cosine similarity greater than or equal to this value will be considered.",
            )
            df_cos = df[df["Cosine similarity"] >= cos_threshold]
        else:
            st.info("Column 'Cosine similarity' not found — threshold filter is disabled.")
            df_cos = df

        pick_labels = st.multiselect(
            "Pick New Label(s)",
            sorted(df_cos["New label"].unique()),
            default=[],
            key="sample_labels",
        )

        if not pick_labels:
            st.info("Pick at least one New Label above to configure sample sizes.")
        else:
            n_samples_per_label = {}
            cols = st.columns(min(len(pick_labels), 4))
            for i, label in enumerate(pick_labels):
                subset_size = len(df_cos[df_cos["New label"] == label])
                with cols[i % len(cols)]:
                    n_samples_per_label[label] = st.slider(
                        label,
                        1,
                        max(1, subset_size),
                        min(1, subset_size),
                        key=f"sample_size_{label}",
                    )

            if st.button("New random sample"):
                st.rerun()

            for label in pick_labels:
                subset = df_cos[df_cos["New label"] == label]
                st.markdown(f"#### {label}")
                if subset.empty:
                    st.info("No items")
                    continue
                sample = subset.sample(min(n_samples_per_label[label], len(subset)), random_state=None)
                for _, row in sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['Original label|Author']}**")
                        st.write(row["Text"])
