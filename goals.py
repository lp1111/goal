import streamlit as st
import pandas as pd
from datetime import date, timedelta
import numpy as np
import altair as alt


def highlight_row(row):
    highlight = 'background-color: red;'
    highlight2 = 'background-color: green;'
    default = ''
    # must return one string per cell in this row
    if row['%'] < row['Target %']:
        return [highlight, default]
    else:
        return [highlight2, default]


def pivot_table(file1, file2, time):
    inc = pd.read_csv(file1)
    csat = pd.read_csv(file2)
    sla_p1 = 3
    sla_p2 = 8
    sla_p3_p4 = 36
    ag = 168
    today = date.today()
    if time == "This year":
        slide = today - timedelta(days=365)
    elif time == "Last month":
        slide = today - timedelta(weeks=4)
    elif time == "This week":
        slide = today - timedelta(weeks=1)
    priority = inc["inc_priority"].replace(["Priority 3", "Priority 4"], "Priority 3 and 4")
    inc = inc.assign(priority=priority)

    # Check wich incidentes meet the SLA.

    sla = ["Not" if inc["mi_duration"][i] > (sla_p1 * 3600) and inc["priority"][i] == "Priority 1" else "Not"
    if inc["mi_duration"][i] > (sla_p2 * 3600) and inc["priority"][i] == "Priority 2" else "Not"
    if inc["mi_duration"][i] > (sla_p3_p4 * 3600) and (inc["priority"][i] == "Priority 3 and 4") else "Yes"
           for i in range(len(inc["mi_duration"]))]

    # Check wich incidentes meet the aging.
    aging = ["Not" if inc["mi_duration"][i] > ((sla_p1 + ag) * 3600) and inc["priority"][i] == "Priority 1" else "Not"
    if inc["mi_duration"][i] > ((sla_p2 + ag) * 3600) and inc["priority"][i] == "Priority 2" else "Not"
    if inc["mi_duration"][i] > ((sla_p3_p4 + ag) * 3600) else "Yes" for i in range(len(inc["mi_duration"]))]

    sla_df = pd.DataFrame({"Closed": inc["inc_resolved_at"], "Aging_met": aging, "SLA_met": sla,
                           "Priority": inc["priority"]})
    sla_df['Closed'] = pd.to_datetime(sla_df['Closed'], format='%Y-%m-%d')
    sla_df['Closed'] = sla_df['Closed'].dt.date
    sla_df = sla_df.loc[(sla_df['Closed'] >= slide)]
    sla_pivot = pd.pivot_table(sla_df, values="Closed", index="Priority", columns="SLA_met", aggfunc="count",
                               margins=True,
                               dropna=True)
    sla_pivot = sla_pivot.div(sla_pivot.iloc[-4:, -1], axis=0).mul(100).round(2).fillna(0)

    aging_df = pd.pivot_table(sla_df, values="Closed", index="Priority", columns="Aging_met", aggfunc="count",
                              margins=True)
    aging_df = aging_df.div(aging_df.iloc[:, -1], axis=0).mul(100).round(2).fillna(0)
    csat["u_assessment_completed"] = pd.to_datetime(csat["u_assessment_completed"], format='%Y-%m-%d')
    csat["u_assessment_completed"] = csat["u_assessment_completed"].dt.date
    csat = csat.loc[(csat["u_assessment_completed"] >= slide)]
    csat_pivot = pd.pivot_table(csat, values="u_assessment_completed", index=None, columns="u_dsat", aggfunc="count",
                                margins=True,
                                dropna=True)
    print(csat_pivot)
    try:

        sla_p1 = sla_pivot["Yes"]["Priority 1"]

    except KeyError:
        sla_p1 = 100

    try:

        sla_p2 = sla_pivot["Yes"]["Priority 2"]

    except KeyError:
        sla_p2 = 0

    try:

        sla_p3_p4 = sla_pivot["Yes"]["Priority 3 and 4"]

    except KeyError:
        sla_p3_p4 = 0

    #final = {"Priority": ["SLA Priority 1", "SLA Priority 2", "SLA Priority 3 and 4", "Incident Aging"],
     #        '%': [sla_p1, sla_p2, sla_p3_p4, aging_df["All"]["All"]], "Target %": [90, 85, 75, 95]}

    final = {'%': [sla_p1, sla_p2, sla_p3_p4, aging_df["All"]["All"]], "Target %": [90, 85, 75, 95]}
    final = pd.DataFrame(data=final,
                         index=["SLA Priority 1", "SLA Priority 2", "SLA Priority 3 and 4", "Incident Aging"])

    df = final.style.apply(highlight_row, subset=['%', 'Target %'], axis=1)
    return df


st.set_page_config(
    page_title="Indicators", page_icon="📊", initial_sidebar_state="expanded"
)

st.write(
    """
# 📊 Indicators
Upload files.
"""
)

uploaded_file = st.file_uploader("Upload Aging and SLA file", type=".csv")
uploaded_file2 = st.file_uploader("Upload CSAT and DSAT file", type=".csv")

ab_default = None
result_default = None

if uploaded_file:
    st.markdown("### Select the period of time")
    with st.form(key="my_form"):
        ab = st.selectbox(
            "Period of time",
            options=["This week", "Last month", "This year", ],
            help="Select which column refers to your A/B testing labels.",
        )

        submit_button = st.form_submit_button(label="Refresh")
        # st.markdown("### Data preview")
        st.dataframe(pivot_table(uploaded_file, uploaded_file2, ab))
