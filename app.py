import streamlit as st
import pandas as pd

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Recruitment Performance Dashboard",
    layout="wide"
)

# st.title("Talent Acquisition Dashboard")

# -----------------------------
# Fancy Dashboard Title
# -----------------------------
st.markdown(
    """
    <style>
    @font-face {
        font-family: 'Proxima Nova';
        src: url('https://your-cdn.com/fonts/ProximaNova-Regular.woff') format('woff');
        font-weight: normal;
        font-style: normal;
    }

    .dashboard-title {
        text-align: center;
        background: linear-gradient(90deg, #6c7a89 0%, #a7bbc7 100%);
        color: white;
        padding: 10px 20px;  /* reduced height */
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        backdrop-filter: blur(5px);
        font-size: 48px;
        font-weight: bold;
        font-family: 'Proxima Nova', sans-serif;
    }
    </style>

    <div class="dashboard-title">
        Recruitment Performance Dashboard
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("    ") 

# -----------------------------
# Load Data
# -----------------------------
df = pd.read_csv("TA data.csv")
offer_df = pd.read_csv("offer status report.csv")

# -----------------------------
# Clean & parse date columns
# -----------------------------
df.columns = df.columns.str.strip()
offer_df.columns = offer_df.columns.str.strip()

df["Recruiter History_start_date"] = pd.to_datetime(
    df["Recruiter History_start_date"].astype(str).str.strip(),
    dayfirst=True,
    errors="coerce"
)

offer_df["Date Of Joining As Per Profile"] = pd.to_datetime(
    offer_df["Date Of Joining As Per Profile"].astype(str).str.strip(),
    dayfirst=True,
    errors="coerce"
)

offer_df["Offer Sent On"] = pd.to_datetime(
    offer_df["Offer Sent On"].astype(str).str.strip(),
    dayfirst=True,
    errors="coerce"
)

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", df["Recruiter History_start_date"].min())
end_date = st.sidebar.date_input("End Date", df["Recruiter History_start_date"].max())

# -----------------------------
# Filter df first
# -----------------------------
filtered_df = df[
    (df["Recruiter History_start_date"] >= pd.to_datetime(start_date)) &
    (df["Recruiter History_start_date"] <= pd.to_datetime(end_date)) &
    (df["Position Status"].isin(["Open", "Filled"]))
]

# st.write("Total Requisitions in filter:", filtered_df["Requisition Id"].nunique())

# -----------------------------
# Merge filtered TA data with offer data
# -----------------------------
merged_df = pd.merge(filtered_df, offer_df, on="Requisition Id", how="left")

# -----------------------------
# Compute all intervals
# -----------------------------
merged_df["Fulfillment Days"] = (merged_df["Date Of Joining As Per Profile"] - merged_df["Recruiter History_start_date"]).dt.days
merged_df["Ext_to_Offer_Days"] = (merged_df["Offer Sent On"] - merged_df["Recruiter History_start_date"]).dt.days
merged_df["Offer_to_DOJ_Days"] = (merged_df["Date Of Joining As Per Profile"] - merged_df["Offer Sent On"]).dt.days

# metrics

# -----------------------------
#  Declined Offers
# -----------------------------
# Only consider offers with Offer Sent date in selected period
declined_df = offer_df[
    (offer_df["Offer Sent On"] >= pd.to_datetime(start_date)) &
    (offer_df["Offer Sent On"] <= pd.to_datetime(end_date)) &
    (offer_df["Offer Status"].isin(["Offer Rejected by the candidate","Offer Dropped"]))
]

# -----------------------------
#  upcoming joinees
# -----------------------------

upcoming_df = offer_df[
    (offer_df["Offer Sent On"] >= pd.to_datetime(start_date)) &
    (offer_df["Offer Sent On"] <= pd.to_datetime(end_date)) &
    (offer_df["Offer Status"].isin([
        "Offer Pending With the Candidate",
        "Offer Accepted and to be added to the pending list",
        "In the Pending List"
    ]))
]


# -----------------------------
# Key Metrics Table: Declined & Joined
# -----------------------------
# Compute metrics
declined_count = declined_df["Candidate Id"].nunique()
total_joined_count = merged_df[merged_df["Date Of Joining As Per Profile"].notna()]["Candidate Id"].nunique()
upcoming_count = upcoming_df["Candidate Id"].nunique()


# Create table
metrics_table = pd.DataFrame({
    "Metric": ["Declined Offers", "Joinees", "Upcoming Joinees"],
    "Count": [declined_count, total_joined_count, upcoming_count]
})

# Display table
st.markdown("<h3><i>Key Metrics Overview</i></h3>", unsafe_allow_html=True)
st.dataframe(metrics_table, use_container_width=True)

# # Display as a metric
# st.metric("Declined Offers", declined_count)

st.markdown("---")  # professional horizontal separator

# -----------------------------
# KPI Metrics
# -----------------------------

st.markdown("<h3><i>Department Hiring Overview</i></h3>", unsafe_allow_html=True)
open_count = filtered_df[filtered_df["Position Status"] == "Open"]["Requisition Id"].nunique()
filled_count = filtered_df[filtered_df["Position Status"] == "Filled"]["Requisition Id"].nunique()
avg_tat = int(merged_df["Fulfillment Days"].mean(skipna=True)) if not merged_df.empty else 0

col1, col2, col3 = st.columns(3)
col1.metric("Open Positions", open_count)
col2.metric("Filled Positions", filled_count)
col3.metric("Average TAT (Days)", avg_tat)

# -----------------------------
# Department Hiring Overview
# -----------------------------
pivot = pd.pivot_table(
    filtered_df,
    values="Requisition Id",
    index="Department Code",
    columns="Position Status",
    aggfunc="count",
    fill_value=0
)
with st.expander("View Requisition Count by Department and Position Status"):
    st.dataframe(pivot)
st.bar_chart(pivot.reset_index().set_index("Department Code"))

st.markdown("---")  # professional horizontal separator

# -----------------------------
# Fulfillment / TAT Distribution
# -----------------------------
# st.subheader("Fulfillment / TAT Distribution")
st.markdown("<h3><i>Fulfillment / TAT Distribution</i></h3>", unsafe_allow_html=True)

def tat_bucket(days):
    if pd.isna(days):
        return "Pending Joining"
    elif days <= 7:
        return "0–7 days"
    elif days <= 14:
        return "8–14 days"
    elif days <= 30:
        return "15–30 days"
    elif days <= 60:
        return "31–60 days"
    elif days <= 90:
        return "60–90 days"
    else:
        return "90+ days (Critical)"

merged_df["TAT Bucket"] = merged_df["Fulfillment Days"].apply(tat_bucket)
tat_summary = merged_df.groupby("TAT Bucket")["Requisition Id"].nunique().reset_index()
bucket_order = ["0–7 days","8–14 days","15–30 days","31–60 days","60–90 days","90+ days (Critical)","Pending Joining"]
tat_summary["TAT Bucket"] = pd.Categorical(tat_summary["TAT Bucket"], categories=bucket_order, ordered=True)
tat_summary = tat_summary.sort_values("TAT Bucket")

with st.expander("View Fulfillment Data Table"):
    st.dataframe(tat_summary)
st.bar_chart(tat_summary.set_index("TAT Bucket"))

# QC count for pending joining
pending_joining_count = merged_df["Fulfillment Days"].isna().sum()
# st.write(f"Requisitions without joining date: {pending_joining_count}")

with st.expander("View Requisitions Pending Joining"):
    st.write(f"Requisitions without joining date: {pending_joining_count}")
    st.dataframe(merged_df[merged_df["Fulfillment Days"].isna()][["Requisition Id","Department Code","Position Status"]])

# -----------------------------
# Subview 1: External Hiring → Offer Sent
# -----------------------------
def ext_offer_bucket(days):
    if pd.isna(days):
        return "Pending Offer"
    elif days <= 7:
        return "0–7 days"
    elif days <= 14:
        return "8–14 days"
    elif days <= 30:
        return "15–30 days"
    elif days <= 60:
        return "31–60 days"
    else:
        return "60+ days"

merged_df["Ext_to_Offer_Bucket"] = merged_df["Ext_to_Offer_Days"].apply(ext_offer_bucket)
ext_offer_summary = merged_df.groupby("Ext_to_Offer_Bucket")["Requisition Id"].nunique().reset_index()
bucket_order_ext = ["0–7 days","8–14 days","15–30 days","31–60 days","60+ days","Pending Offer"]
ext_offer_summary["Ext_to_Offer_Bucket"] = pd.Categorical(ext_offer_summary["Ext_to_Offer_Bucket"], categories=bucket_order_ext, ordered=True)
ext_offer_summary = ext_offer_summary.sort_values("Ext_to_Offer_Bucket")

st.markdown("<b><i>Fulfillment Breakdown</i></b>", unsafe_allow_html=True)

with st.expander("External Hiring → Offer Sent (Days)"):
    st.bar_chart(ext_offer_summary.set_index("Ext_to_Offer_Bucket"))
    st.dataframe(ext_offer_summary)
# st.write(f"Pending Offer count: {merged_df['Offer Sent On'].isna().sum()}")



# -----------------------------
# Subview 2: Offer Sent → DOJ
# -----------------------------
def offer_doj_bucket(days):
    if pd.isna(days):
        return "Pending Joining"
    elif days <= 7:
        return "0–7 days"
    elif days <= 14:
        return "8–14 days"
    elif days <= 30:
        return "15–30 days"
    elif days <= 60:
        return "31–60 days"
    else:
        return "60+ days"

merged_df["Offer_to_DOJ_Bucket"] = merged_df["Offer_to_DOJ_Days"].apply(offer_doj_bucket)
offer_doj_summary = merged_df.groupby("Offer_to_DOJ_Bucket")["Requisition Id"].nunique().reset_index()
bucket_order_offer = ["0–7 days","8–14 days","15–30 days","31–60 days","60+ days","Pending Joining"]
offer_doj_summary["Offer_to_DOJ_Bucket"] = pd.Categorical(offer_doj_summary["Offer_to_DOJ_Bucket"], categories=bucket_order_offer, ordered=True)
offer_doj_summary = offer_doj_summary.sort_values("Offer_to_DOJ_Bucket")

with st.expander("Offer Sent → DOJ (Days)"):
    st.bar_chart(offer_doj_summary.set_index("Offer_to_DOJ_Bucket"))
    st.dataframe(offer_doj_summary)

# -----------------------------
# Subview 3: Roles filled ≤60 vs >60 days
# -----------------------------
filled_df = merged_df.dropna(subset=["Fulfillment Days"])
filled_df["≤60 vs >60"] = filled_df["Fulfillment Days"].apply(lambda x: "≤ 60 days" if x <= 60 else "> 60 days")
roles_60_summary = filled_df.groupby("≤60 vs >60")["Requisition Id"].nunique().reset_index()

with st.expander("Roles Filled ≤ 60 Days vs > 60 Days"):
    st.bar_chart(roles_60_summary.set_index("≤60 vs >60"))
    st.dataframe(roles_60_summary)

st.markdown("---")  # professional horizontal separator

# -----------------------------
# Gender Split of Joined Candidates
# -----------------------------
st.markdown("<h3><i>Gender Split of Joined Candidates</i></h3>", unsafe_allow_html=True)

# Only consider candidates who have actually joined (DOJ not null)
gender_df = merged_df.dropna(subset=["Date Of Joining As Per Profile"]).copy()

# Fill empty Gender values with 'NA'
gender_df["Gender"] = gender_df["Gender"].fillna("NA")

# Count unique Candidate Ids per Gender
gender_summary = (
    gender_df.groupby("Gender")["Candidate Id"]
    .nunique()
    .reset_index()
    .sort_values("Candidate Id", ascending=False)
)

# Display bar chart
st.bar_chart(gender_summary.set_index("Gender"))

# Show detailed table in expander
with st.expander("View Gender Split Table"):
    total_joined = gender_df["Candidate Id"].nunique()
    st.write(f"Total Joined Candidates from **{start_date}** to **{end_date}**: {total_joined}")
    st.dataframe(gender_summary)



# -----------------------------
# QC: Joined Candidates Count
# -----------------------------
st.markdown("<h4><i>Joined Candidates QC</i></h4>", unsafe_allow_html=True)

# 1️⃣ Candidates from filtered TA → offer merge
joined_filtered = merged_df.dropna(subset=["Date Of Joining As Per Profile"])
joined_filtered_count = joined_filtered["Candidate Id"].nunique()

# 2️⃣ Total candidates in raw offer data with non-null DOJ
joined_total = offer_df.dropna(subset=["Date Of Joining As Per Profile"])
joined_total_count = joined_total["Candidate Id"].nunique()

# 3️⃣ Missing requisitions (in offer_df but not in filtered TA)
missing_recs = offer_df[~offer_df["Requisition Id"].isin(filtered_df["Requisition Id"])]

col1, col2, col3 = st.columns(3)
col1.metric("Joined Candidates (Filtered TA)", joined_filtered_count)
col2.metric("Total Joined Candidates (Offer Data)", joined_total_count)
col3.metric("Requisitions Missing in Filtered TA", missing_recs["Requisition Id"].nunique())

# Optional: show list of missing requisitions
with st.expander("View Requisitions missing in filtered TA"):
    st.dataframe(missing_recs[["Requisition Id","Candidate Id","Date Of Joining As Per Profile"]])