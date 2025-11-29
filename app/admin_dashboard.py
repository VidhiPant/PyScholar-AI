import streamlit as st
import pandas as pd
import sqlite3
import os

def get_all_bookings():
    """Fetch all bookings from the database."""
    # Ensure we connect to the correct path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'bookings.db')
    
    try:
        conn = sqlite3.connect(db_path)
        # We join customers and bookings to get a complete view
        query = """
        SELECT 
            b.id as Booking_ID,
            c.name as Customer_Name,
            c.email as Email,
            c.phone as Phone,
            b.booking_type as Service_Type,
            b.date as Date,
            b.time as Time,
            b.status as Status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        ORDER BY b.id DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error accessing database: {e}")
        return pd.DataFrame()

def show_dashboard():
    """Main function to render the Admin Dashboard."""
    st.header("🔒 Admin Dashboard")
    st.markdown("View and manage all mentorship bookings here.")

    # 1. Fetch Data
    df = get_all_bookings()

    if df.empty:
        st.info("No bookings found yet. Go to the Chat tab to create one!")
        return

    # 2. Filter / Search Section
    with st.expander("🔎 Filter & Search", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search by Name or Email")
        
        with col2:
            # Get unique dates for the dropdown
            unique_dates = ["All"] + list(df['Date'].unique())
            selected_date = st.selectbox("Filter by Date", unique_dates)

    # 3. Apply Filters
    if search_term:
        # Case-insensitive search on Name or Email
        df = df[
            df['Customer_Name'].str.contains(search_term, case=False) | 
            df['Email'].str.contains(search_term, case=False)
        ]
    
    if selected_date != "All":
        df = df[df['Date'] == selected_date]

    # 4. Display Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Bookings", len(df))
    m2.metric("Confirmed", len(df[df['Status'] == 'Confirmed']))
    m3.metric("Pending", len(df[df['Status'] == 'Pending']))

    # 5. Data Table
    st.subheader("Booking Records")
    # precise column config for better UI
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Booking_ID": st.column_config.NumberColumn("ID", width="small"),
            "Email": st.column_config.LinkColumn("Email"), # Makes email clickable
        }
    )

    # 6. Refresh Button (Manual refresh in case of new bookings)
    if st.button("🔄 Refresh Data"):
        st.rerun()