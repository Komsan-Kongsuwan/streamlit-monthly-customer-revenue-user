# streamlit_monthly_revenue/chart_page.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re

def render_chart_page():
    # --- Page CSS tweaks ---
    st.markdown("""
        <style>
            .block-container {
                padding-top: 2.5rem;
                padding-left: 1rem;
                padding-right: 1rem;
                padding-bottom: 0rem;
            }
    
            /* --- Sidebar buttons --- */
            section[data-testid="stSidebar"] div.stButton {
                margin: 0px 0 !important; /* ลดช่องว่างบน-ล่าง */
            }
            section[data-testid="stSidebar"] div.stButton > button {
                font-size: 12px !important;
                padding: 0.1rem 0.2rem !important; /* ลด padding ให้ชิดกัน */
                height: auto !important;
                min-height: 40px !important;       /* ปรับให้สูงขึ้นเล็กน้อย */
                border-radius: 6px !important;
                line-height: 1.1 !important;
            }
            section[data-testid="stSidebar"] div.stButton p {
                font-size: 12px !important;
                margin: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Data check ---
    if "official_data" in st.session_state:
        df_raw = st.session_state["official_data"].copy()
    elif "customer_data" in st.session_state:  # fallback
        df_raw = st.session_state["customer_data"].copy()
    else:
        st.warning("⚠️ No data found. Please load sample data or generate the report first.")
        st.stop()

    df_raw["Amount"] = pd.to_numeric(df_raw["Amount"], errors="coerce").fillna(0)

    # Normalize Year/Month -> Period (robust to numeric)
    df_raw["Year"] = df_raw["Year"].astype(float).astype(int).astype(str)
    df_raw["Month"] = df_raw["Month"].astype(float).astype(int).astype(str).str.zfill(2)
    df_raw["Period"] = pd.to_datetime(df_raw["Year"] + "-" + df_raw["Month"], format="%Y-%m", errors="coerce")


    # Sites list and resilient selection
    sites = sorted([s for s in df_raw["Site"].dropna().unique().tolist() if str(s).strip() != ""])
    if not sites:
        st.error("No sites found in the current data.")
        st.stop()

    data_signature = (tuple(sites), df_raw["Period"].min(), df_raw["Period"].max())
    if st.session_state.get("data_signature") != data_signature:
        st.session_state["data_signature"] = data_signature
        st.session_state["selected_site"] = sites[0]

    if "selected_site" not in st.session_state or st.session_state.selected_site not in sites:
        st.session_state.selected_site = sites[0]

    for site in sites:
        if st.sidebar.button(site, use_container_width=True):
            st.session_state.selected_site = site

    site_code = st.session_state.selected_site
    df_site = df_raw[df_raw["Site"] == site_code].copy()
    if df_site.empty:
        st.info(f"No data for selected site: {site_code}")
        st.stop()

    # -----------------------------
    # Top 7 Customers Comparison Boxes
    # -----------------------------
    latest_month = df_site["Period"].max()
    if pd.isna(latest_month):
        st.info("No valid Period values in data.")
        st.stop()

    prior_in_data = df_site[df_site["Period"] < latest_month]["Period"].max()
    prior_month = prior_in_data if pd.notna(prior_in_data) else (latest_month - pd.DateOffset(months=1))

    # compute top 7 customers by latest-month revenue
    latest_totals = (df_site[df_site["Period"] == latest_month]
                     .groupby("Customer", as_index=False)["Amount"].sum()
                     .sort_values("Amount", ascending=False))
    top_customers = latest_totals["Customer"].head(7).tolist()

    def get_star_rating(this_month_val=0, last_month_val=0):
        diff = this_month_val - last_month_val
        pct = (diff / last_month_val * 100) if last_month_val != 0 else 0
        if this_month_val > 0:
            if pct > 50: return "⭐⭐⭐⭐"
            elif pct >= 25: return "⭐⭐⭐"
            elif pct >= 5: return "⭐⭐"
            elif pct >= 0: return "⭐"
            elif pct >= -5: return "🚨"
            elif pct >= -25: return "🚨🚨"
            elif pct >= -50: return "🚨🚨🚨"
            else: return "🚨🚨🚨🚨"
        else:
            if this_month_val > -5000: return "🚨"
            elif this_month_val >= -50000: return "🚨🚨"
            elif this_month_val >= -100000: return "🚨🚨🚨"
            elif this_month_val >= -500000: return "🚨🚨🚨🚨"
            else: return "🚨🚨🚨🚨"

    comparison_data = []
    for cust in top_customers:
        this_month_val = df_site[(df_site["Period"] == latest_month) & (df_site["Customer"] == cust)]["Amount"].sum()
        last_month_val = df_site[(df_site["Period"] == prior_month) & (df_site["Customer"] == cust)]["Amount"].sum()
        diff = this_month_val - last_month_val
        pct = (diff / last_month_val * 100) if last_month_val != 0 else 0
        rating = get_star_rating(this_month_val, last_month_val)
        arrow, color = ("▲", "green") if this_month_val > last_month_val else ("▼", "red")

        comparison_data.append({
            "Customer": cust,
            "Current": f"{this_month_val:,.0f} THB",
            "Previous": f"{last_month_val:,.0f} THB",
            "Diff": f"{abs(diff):,.0f} THB",
            "Pct": f"{abs(pct):.2f} %",
            "Arrow": arrow,
            "Month1": latest_month.strftime("%b-%Y"),
            "Month2": prior_month.strftime("%b-%Y"),
            "Color": color,
            "Rating": rating
        })

    # pad to 7 with truly blank cards
    while len(comparison_data) < 7:
        comparison_data.append({
            "Customer": "",
            "Current": "",
            "Previous": "",
            "Diff": "",
            "Pct": "",
            "Arrow": "",
            "Month1": "",
            "Month2": "",
            "Color": "black",
            "Rating": ""
        })

    st.markdown(f"""
        <p style='margin-top:0; margin-bottom:0.5rem; color:#333; font-size:20px; font-weight:bold'>
            Site : {site_code} - Top 7 Customers Comparison - {latest_month.strftime('%B %Y')}
        </p>
    """, unsafe_allow_html=True)

    cols = st.columns(7)
    for col, data in zip(cols, comparison_data):
        if data["Customer"]:
            col.markdown(f"""
            <div style="border:1px solid #ccc; border-radius:6px; padding:6px;
                        background-color:#f9f9f9; box-shadow:1px 1px 3px rgba(0,0,0,0.1);
                        font-size:11px; min-height:100px;">
                <p style="font-size:11px; font-weight:bold; margin-bottom:4px; color:#333;">
                    {data['Customer'][:10]} {data['Rating']}
                </p>
                <p style="margin:2px 0; font-size:12px;"><b>{data['Month2']}:</b>
                    <span style="color:black;">{data['Previous']}</span></p>
                <p style="margin:2px 0; font-size:12px; font-weight:bold;"><b>{data['Month1']}:</b>
                    <span style="color:black;">{data['Current']}</span></p>
                <p style="margin-top:2px; color:{data['Color']}; font-size:12px;">
                    {data['Arrow']} {data['Pct']} = {data['Diff']}
                </p>
            </div>
            <br>
            """, unsafe_allow_html=True)
        else:
            # blank placeholder
            col.markdown("""
            <div style="border:1px solid #eee; border-radius:6px; padding:6px;
                        background-color:#fafafa; box-shadow:1px 1px 3px rgba(0,0,0,0.05);
                        min-height:100px;">
                &nbsp;
            </div>
            <br>
            """, unsafe_allow_html=True)

    # -----------------------------
    # Charts (line and bar)
    # -----------------------------
    customers = sorted(df_site["Customer"].dropna().unique())
    default_customer = customers[0] if customers else None
    selected_customers = st.multiselect("Select Customer(s) for Chart", customers, default=[default_customer] if default_customer else [])
    if not selected_customers:
        st.info("Select at least one customer.")
        st.stop()

    col1, col2 = st.columns([6, 4])

    with col1:
        line_df = (df_site[df_site["Customer"].isin(selected_customers)]
                   .groupby(["Customer", "Period"], as_index=False)["Amount"].sum())
        fig_line = px.line(line_df, x="Period", y="Amount", color="Customer", markers=False)
        fig_line.update_layout(
            height=240, margin=dict(l=10, r=10, t=40, b=20),
            showlegend=False, xaxis_title="", yaxis_title="",
            hovermode="x",
            xaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor",
                       showline=False, spikedash="dash", spikecolor="red", spikethickness=1),
            hoverlabel=dict(bgcolor="#7F7F7F", font_size=12, font_color="white"),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        bar_df = (df_site[df_site["Customer"].isin(selected_customers)]
                  .groupby(["Customer", "Year"], as_index=False)["Amount"].sum())
        fig_bar = px.bar(bar_df, x="Year", y="Amount", color="Customer", text_auto=".2s")
        fig_bar.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=40),
                              legend=dict(orientation="h", y=-0.2, x=0.0, xanchor="left", yanchor="top"),
                              xaxis_title="", yaxis_title="", legend_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------------------
    # Rolling 24-Month Revenue Table (robust)
    # -----------------------------
    df_revenue = (df_site[df_site["Customer"].isin(selected_customers)]
                  .groupby(["Customer", "Period"], as_index=False)["Amount"].sum()
                  .sort_values("Period"))

    if df_revenue.empty:
        st.info("No revenue data available for the selected customers at this site.")
        return

    # keep last 24 months up to max available
    max_period = df_revenue["Period"].max()
    min_period = max_period - pd.DateOffset(months=23)
    df_revenue = df_revenue[df_revenue["Period"] >= min_period]

    # periods timeline (sorted timestamps)
    months_ts = sorted(df_revenue["Period"].unique())
    months_str = [p.strftime("%b-%Y") for p in months_ts]
    if not months_ts:
        st.info("No recent periods to show.")
        return

    # pivot table: rows=Customer, cols=Period
    pivot = df_revenue.pivot(index="Customer", columns="Period", values="Amount")

    data_rows = []
    for cust in selected_customers:
        if cust in pivot.index:
            row = pivot.loc[cust]
        else:
            # empty customer -> create empty series
            row = pd.Series(index=months_ts, dtype=float)

        # align to months_ts
        row_reindexed = row.reindex(months_ts)

        # amounts (in KB)
        amounts_list = []
        for v in row_reindexed:
            if pd.isna(v):
                amounts_list.append("")   # will render empty cell
            else:
                amounts_list.append(v / 1000.0)

        # diffs (in KB) - first diff is blank; diffs only if previous period exists
        diffs_list = []
        prev = None
        for v in row_reindexed:
            if prev is None or pd.isna(v) or pd.isna(prev):
                diffs_list.append("")   # blank (no diff)
            else:
                diffs_list.append((v - prev) / 1000.0)
            prev = v

        # build dict rows mapping month_str -> value (value may be "" or number)
        amt_row = {"Customer": cust, "Type": "Amount"}
        diff_row = {"Customer": cust, "Type": "Diff"}
        for mstr, aval, dval in zip(months_str, amounts_list, diffs_list):
            amt_row[mstr] = aval
            diff_row[mstr] = "" if dval == "" else dval

        data_rows.append(amt_row)
        data_rows.append(diff_row)

    df_pivot = pd.DataFrame(data_rows)

    # render as HTML table safely
    html = "<table style='font-size:10px; border-collapse: collapse;'>"
    html += "<tr><th style='padding:4px 4px;text-align:left;'>Customer / Type</th>"
    for m in months_str:
        html += f"<td style='padding:4px 4px;text-align:right;'>{m}</td>"
    html += "</tr>"

    for _, row in df_pivot.iterrows():
        row_label = (row["Customer"] + " (KB)") if row["Type"] == "Amount" else f"{row['Type']} (KB)"
        html += f"<tr><td style='padding:4px 4px; text-align:left;'><b>{row_label}</b></td>"

        for m in months_str:
            val = row.get(m, "")
            # treat empty/None/NaN as blank
            if val == "" or val is None or (isinstance(val, float) and np.isnan(val)):
                html += "<td></td>"
                continue

            # value is number (in KB)
            try:
                v = float(val)
            except (TypeError, ValueError):
                html += "<td></td>"
                continue

            formatted_val = f"{int(abs(v)):,}"
            if row["Type"] == "Diff":
                color = "green" if v > 0 else ("red" if v < 0 else "black")
                sign = "+" if v > 0 else ("-" if v < 0 else "")
                bold = "font-weight:bold;"
            else:
                color = "black"
                sign = ""
                bold = ""

            html += f"<td style='padding:0px 4px; text-align:right; {bold} color:{color}'>{sign}{formatted_val}</td>"

        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
