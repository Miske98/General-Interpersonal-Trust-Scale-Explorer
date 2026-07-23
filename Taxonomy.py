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
# Data upload — main CSV
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


# ---------------------------------------------------------------------------
# Data upload — ProjectTrust_labelanddefinition.xlsx (Sheet1)
# ---------------------------------------------------------------------------
LABELDEF_COLS = [
    "Scale name",
    "Factor vs scale",
    "Scale label",
    "Definition",
    "Factors",
    "Charachteristic",
    "Framwork",
    "Alternative name",
]


@st.cache_data
def load_labeldef():
    df = pd.read_excel('./Data/ProjectTrust_labelanddefinition.xlsx', sheet_name="Sheet1")
    df = trim_columns(df)
    if "Author" not in df.columns:
        st.error("Column 'Author' missing in ProjectTrust_labelanddefinition.xlsx")
        st.stop()
    df["Author"] = df["Author"].astype(str).str.strip()
    for col in LABELDEF_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


# ---------------------------------------------------------------------------
# Data upload — General Interpersonal Trust Taxonomy and other.xlsx
# (sheet: JINGLE JANGLE FALLACIES)
# ---------------------------------------------------------------------------
JJ_COLS = [
    "Original Label 1",
    "Author 1",
    "Scale 1",
    "Original Label 2",
    "Scale 2",
    "Author 2",
    "Type of fallacy",
]


@st.cache_data
def load_jingle_jangle():
    df = pd.read_excel('./Data/General Interpersonal Trust Taxonomy and other.xlsx', sheet_name="JINGLE JANGLE FALLACIES")
    df = trim_columns(df)
    for col in ["Author 1", "Author 2"] + JJ_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


st.title("Taxonomy Explorer")

df_full = load_data()
df_labeldef = load_labeldef()
df_jinglejangle = load_jingle_jangle()

authors = sorted(df_full["Author"].unique())
labels = sorted(df_full["Original label"].unique())
color_map = get_color_map(df_full["New label"].unique())

# ---------------------------------------------------------------------------
# Helper: render the single-author info panel
# ---------------------------------------------------------------------------
def render_author_info_panel(author):
    st.markdown("---")
    st.header(f"Author: {author}")

    # --- ProjectTrust_labelanddefinition.xlsx ---
    matches = df_labeldef[df_labeldef["Author"] == author]
    if matches.empty:
        st.info(f"No entries found for '{author}' in ProjectTrust_labelanddefinition.xlsx, sheet1.")
    else:
        st.subheader("Scale / Label information")
        for _, row in matches.iterrows():
            with st.container(border=True):
                for col in LABELDEF_COLS:
                    if col not in matches.columns:
                        continue
                    val = row[col]
                    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
                        continue
                    st.markdown(f"**{col}:** {val}")

    # --- General Interpersonal Trust Taxonomy and other.xlsx ---
    st.subheader("Jingle-Jangle Fallacies")
    cols_present = [c for c in JJ_COLS if c in df_jinglejangle.columns]
    mask = pd.Series(False, index=df_jinglejangle.index)
    if "Author 1" in df_jinglejangle.columns:
        mask |= df_jinglejangle["Author 1"] == author
    if "Author 2" in df_jinglejangle.columns:
        mask |= df_jinglejangle["Author 2"] == author
    jj_matches = df_jinglejangle[mask]

    if jj_matches.empty:
        st.info(f"No jingle-jangle fallacy entries found for {author}.")
    else:
        for _, row in jj_matches.iterrows():
            with st.container(border=True):
                c1, c2, c3, c_mid, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 1, 1])

                def show(container, col_name):
                    if col_name in cols_present:
                        val = row[col_name]
                        if not (pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan"):
                            container.markdown(f"**{col_name}**\n\n{val}")

                show(c1, "Original Label 1")
                show(c2, "Author 1")
                show(c3, "Scale 1")

                if "Type of fallacy" in cols_present:
                    val = row["Type of fallacy"]
                    if not (pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan"):
                        c_mid.markdown(f"<div style='text-align:center'><b>Type of fallacy</b><br>{val}</div>", unsafe_allow_html=True)

                show(c4, "Original Label 2")
                show(c5, "Scale 2")
                show(c6, "Author 2")


# ---------------------------------------------------------------------------
# Top navigation (replaces sidebar)
# ---------------------------------------------------------------------------
tab_overview, tab_taxonomy, tab_search, tab_extra = st.tabs(
    ["Overview (stacked bar)", "GI Trust Taxonomy", "Item Search", "Extra"]
)

# ---------------------------------------------------------------------------
# Page 1 - Stacked barh (the ONLY page affected by author/label filters)
# ---------------------------------------------------------------------------
with tab_overview:
    st.title("Original Label | Author grouped by New Label")

    with st.container(border=True):
        st.subheader("Filters")
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            selected_authors = st.multiselect("Filter by author", authors, default=[], key="ov_authors")
        with fcol2:
            selected_labels = st.multiselect("Filter by label", labels, default=[], key="ov_labels")

    df_authors = df_full[df_full["Author"].isin(selected_authors)] if selected_authors else df_full
    df_labels = df_full[df_full["Original label"].isin(selected_labels)] if selected_labels else df_full
    if selected_labels and selected_authors:
        df_ov = pd.concat([df_authors, df_labels], axis=0, ignore_index=True).drop_duplicates()
    elif selected_labels:
        df_ov = df_labels
    elif selected_authors:
        df_ov = df_authors
    else:
        df_ov = df_full

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Number of items", len(df_ov))
    m2.metric("Original label | Author", df_ov["Original label|Author"].nunique())
    m3.metric("New labels", df_ov["New label"].nunique())
    m4.metric("Unique authors", df_ov["Author"].nunique())

    st.caption("Hover for details")

    if df_ov.empty:
        st.warning("Looks like you filtered everything out")
    else:
        table_pct = pd.crosstab(df_ov["Original label|Author"], df_ov["New label"], normalize="index")
        table_cnt = pd.crosstab(df_ov["Original label|Author"], df_ov["New label"])

        fig = go.Figure()
        for label in table_pct.columns:
            pct = table_pct[label] * 100
            cnt = table_cnt[label]
            fig.add_trace(
                go.Bar(
                    y=table_pct.index,
                    x=table_pct[label],
                    orientation="h",
                    name=label,
                    text=[label if v > 0 else "" for v in table_pct[label]],
                    textposition="inside",
                    insidetextanchor="middle",
                    constraintext="both",
                    textfont=dict(color="white", size=11),
                    marker=dict(color=color_map[label], line=dict(color="black", width=0.6)),
                    customdata=list(zip([label] * len(table_pct), pct, cnt)),
                    hovertemplate=(
                        "<b>New Label:</b> %{customdata[0]}<br>"
                        "<b>Percent:</b> %{customdata[1]:.1f}%<br>"
                        "<b>No. of items:</b> %{customdata[2]}"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

        fig.update_layout(
            barmode="stack",
            height=max(600, 28 * len(table_pct)),
            xaxis=dict(visible=False),
            yaxis=dict(title="Original label | Author", automargin=True),
            template="plotly_white",
            margin=dict(l=10, r=10, t=30, b=10),
            font=dict(family="Times New Roman", size=13),
        )
        fig = lock_chart(fig)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        # ---- Single-author info panel ----
        if len(selected_authors) == 1:
            render_author_info_panel(selected_authors[0])

# ---------------------------------------------------------------------------
# Page 2 - Filter by New Label (uses the FULL, unfiltered dataset)
# ---------------------------------------------------------------------------
with tab_taxonomy:
    df = df_full
    st.title("Ranking Original label | Author by chosen New Label")

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
            yaxis=dict(title="Original label | Author", automargin=True),
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
# Page 3 — Text search through items (uses the FULL, unfiltered dataset)
# ---------------------------------------------------------------------------
with tab_search:
    df = df_full
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
# Page 4 — Extra (uses the FULL, unfiltered dataset)
# ---------------------------------------------------------------------------
with tab_extra:
    df = df_full
    st.title("Extras")

    subtab1, subtab2, subtab3 = st.tabs(
        ["Distribution", "Heatmap Original vs New", "Randomizer"]
    )

    # --- Tab 1: New Label ---
    with subtab1:
        st.subheader("No. of Items for New Label")
        counts = df["New label"].value_counts().sort_values(ascending=True)
        fig = go.Figure(
            go.Bar(
                y=counts.index,
                x=counts.values,
                orientation="h",
                marker=dict(color=[color_map[l] for l in counts.index], line=dict(color="black", width=0.6)),
                hovertemplate="<b>%{y}</b><br>%{x} items<extra></extra>",
            )
        )
        fig.update_layout(
            height=max(400, 28 * len(counts)),
            template="plotly_white",
            xaxis_title="No. of Items",
            font=dict(family="Times New Roman", size=13),
        )
        fig = lock_chart(fig)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # --- Tab 2: Heatmap ---
    with subtab2:
        st.subheader("Relabeling Contingency Heatmap")
        heat_table = pd.crosstab(df["Original label"], df["New label"])
        fig = px.imshow(
            heat_table,
            aspect="auto",
            color_continuous_scale="Reds",
            labels=dict(x="New Label", y="Original Label", color="Items"),
        )
        fig.update_layout(
            height=max(500, 22 * len(heat_table)),
            font=dict(family="Times New Roman", size=12),
        )
        fig = lock_chart(fig)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # --- Tab 3: Random sampler ---
    with subtab3:
        st.subheader("Random Item Sample")

        pick_labels = st.multiselect(
            "Pick New Label(s)",
            sorted(df["New label"].unique()),
            default=[],
            key="sample_labels",
        )

        if not pick_labels:
            st.info("Pick at least one New Label above to configure sample sizes.")
        else:
            n_samples_per_label = {}
            cols = st.columns(min(len(pick_labels), 4))
            for i, label in enumerate(pick_labels):
                subset_size = len(df[df["New label"] == label])
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
                subset = df[df["New label"] == label]
                st.markdown(f"#### {label}")
                if subset.empty:
                    st.info("No items")
                    continue
                sample = subset.sample(min(n_samples_per_label[label], len(subset)), random_state=None)
                for _, row in sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['Original label|Author']}**")
                        st.write(row["Text"])