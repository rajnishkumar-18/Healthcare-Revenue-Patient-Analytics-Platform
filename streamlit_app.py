import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data function
@st.cache_data
def load_data():
    # Debug: Show what files are available
    #import os
    #st.write("Files in current directory:", os.listdir('.'))
    #st.write("Current working directory:", os.getcwd())
    
    try:
        # Load the original CSV files
        patients = pd.read_csv(r"patients.csv")
        doctors = pd.read_csv(r"doctors.csv") 
        appointments = pd.read_csv(r"appointments.csv")
        treatments = pd.read_csv(r"treatments.csv")
        billing = pd.read_csv(r"billing.csv")
        
        # Basic data processing
        patients['birth_date'] = pd.to_datetime(patients['date_of_birth'])
        patients['age'] = (datetime.now() - patients['birth_date']).dt.days / 365.25
        
        appointments['appointment_datetime'] = pd.to_datetime(appointments['appointment_date'] + ' ' + appointments['appointment_time'])
        appointments['hour'] = appointments['appointment_datetime'].dt.hour
        appointments['day_of_week'] = appointments['appointment_datetime'].dt.dayofweek
        appointments['is_no_show'] = appointments['status'].isin(['No-show', 'Cancelled']).astype(int)
        
        # Create master dataset
        master_df = appointments.merge(patients[['patient_id', 'age', 'gender', 'insurance_provider']], on='patient_id', how='left')
        master_df = master_df.merge(doctors[['doctor_id', 'specialization', 'years_experience']], on='doctor_id', how='left')
        master_df = master_df.merge(treatments[['appointment_id', 'treatment_type', 'cost']], on='appointment_id', how='left')
        
        # Calculate key metrics
        total_revenue = master_df['cost'].sum()
        completed_revenue = master_df[master_df['status'] == 'Completed']['cost'].sum()
        lost_revenue = total_revenue - completed_revenue
        no_show_rate = master_df['is_no_show'].mean()
        completion_rate = (master_df['status'] == 'Completed').mean()
        
        metrics = {
            'total_patients': len(patients),
            'total_doctors': len(doctors),
            'total_appointments': len(appointments),
            'completion_rate': completion_rate,
            'no_show_rate': no_show_rate,
            'total_revenue': total_revenue,
            'completed_revenue': completed_revenue,
            'lost_revenue': lost_revenue,
            'avg_patient_age': master_df['age'].mean()
        }
        
        return master_df, patients, doctors, appointments, treatments, billing, metrics
        
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        st.info("Please make sure all CSV files are in the same directory as this app.")
        return None, None, None, None, None, None, None

# Main app
def main():
    st.title("Healthcare Analytics Dashboard")
    st.markdown("### Optimizing Hospital Operations Through Data-Driven Insights")

    #if st.button("Clear Cache"):
        #st.cache_data.clear()
        #st.rerun()
    
    # Load data
    data_loaded = load_data()
    if data_loaded[0] is None:
        return
    
    master_df, patients, doctors, appointments, treatments, billing, metrics = data_loaded
    
    # Sidebar navigation
    st.sidebar.title("Dashboard Navigation")
    page = st.sidebar.selectbox(
        "Select Analysis View",
        ["Executive Dashboard", "Operations Analytics", "Financial Analytics", 
         "Quality Analytics", "Business Recommendations"]
    )
    
    if page == "Executive Dashboard":
        executive_dashboard(master_df, metrics)
    elif page == "Operations Analytics":
        operations_analytics(master_df)
    elif page == "Financial Analytics":
        financial_analytics(master_df, metrics)
    elif page == "Quality Analytics":
        quality_analytics(master_df)
    elif page == "Business Recommendations":
        business_recommendations(master_df, metrics)

def executive_dashboard(master_df, metrics):
    st.header("Executive Dashboard")
    st.markdown("High-level KPIs and business performance overview")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Patients",
            value=f"{int(metrics['total_patients'])}",
            delta=f"{int(metrics['total_appointments'])} appointments"
        )
    
    with col2:
        completion_rate = metrics['completion_rate'] * 100
        st.metric(
            label="Completion Rate",
            value=f"{completion_rate:.1f}%",
            delta=f"{100-completion_rate:.1f}% opportunity"
        )
    
    with col3:
        st.metric(
            label="Total Revenue",
            value=f"${metrics['total_revenue']:,.0f}",
            delta=f"${metrics['lost_revenue']:,.0f} at risk"
        )
    
    with col4:
        st.metric(
            label="Average Patient Age",
            value=f"{metrics['avg_patient_age']:.0f} years",
            delta=f"No-show rate: {metrics['no_show_rate']*100:.1f}%"
        )
    
    st.markdown("---")
    
    # Revenue opportunity visualization
    col1, col2 = st.columns(2)
    
    with col1:
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Bar(
            name='Revenue Status',
            x=['Completed', 'At Risk'],
            y=[metrics['completed_revenue'], metrics['lost_revenue']],
            marker_color=['#2E8B57', '#DC143C']
        ))
        fig_revenue.update_layout(
            title='Revenue Recovery Opportunity',
            xaxis_title='Appointment Status',
            yaxis_title='Revenue ($)',
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        status_counts = master_df['status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Appointment Status Distribution',
            height=400
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Key insights
    st.markdown("### Key Executive Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **Revenue Opportunity**
        - ${metrics['lost_revenue']:,.0f} at risk from incomplete appointments
        - {(metrics['lost_revenue']/metrics['total_revenue'])*100:.1f}% revenue recovery potential
        - Target: Reduce no-show rate by 50%
        """)
    
    with col2:
        st.warning(f"""
        **Operational Efficiency**
        - {metrics['no_show_rate']*100:.1f}% no-show rate (industry: 15-20%)
        - Peak demand periods identified
        - Resource reallocation needed
        """)
    
    with col3:
        st.success(f"""
        **Growth Opportunities**
        - Specialization optimization available
        - {int(metrics['total_patients'])} active patients
        - Cross-selling potential identified
        """)

def operations_analytics(master_df):
    st.header("Operations Analytics")
    st.markdown("Patient flow optimization and resource allocation insights")
    
    # Demand analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Demand heatmap by hour and day
        demand_pivot = master_df.pivot_table(
            values='appointment_id',
            index='hour',
            columns='day_of_week',
            aggfunc='count',
            fill_value=0
        )
        
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        demand_pivot.columns = [day_names[i] for i in demand_pivot.columns if i < len(day_names)]
        
        fig_heatmap = px.imshow(
            demand_pivot,
            title='Appointment Demand Heatmap',
            labels=dict(x="Day of Week", y="Hour", color="Appointments"),
            color_continuous_scale="Blues",
            height=500
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        # Specialization performance
        spec_analysis = master_df.groupby('specialization').agg({
            'appointment_id': 'count',
            'is_no_show': 'mean',
            'cost': ['sum', 'mean']
        }).round(2)
        
        spec_analysis.columns = ['appointments', 'no_show_rate', 'total_revenue', 'avg_revenue']
        spec_analysis = spec_analysis.sort_values('appointments', ascending=False)
        
        fig_spec = px.bar(
            x=spec_analysis.index,
            y=spec_analysis['appointments'],
            title='Appointments by Medical Specialization',
            labels={'x': 'Specialization', 'y': 'Total Appointments'}
        )
        st.plotly_chart(fig_spec, use_container_width=True)
    
    # Peak demand insights
    st.subheader("Peak Demand Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    hourly_demand = master_df.groupby('hour').size()
    daily_demand = master_df.groupby('day_of_week').size()
    
    with col1:
        peak_hour = hourly_demand.idxmax()
        peak_appointments = hourly_demand.max()
        st.metric("Peak Hour", f"{peak_hour}:00", f"{peak_appointments} appointments")
    
    with col2:
        peak_day_idx = daily_demand.idxmax()
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        peak_day = day_names[peak_day_idx] if peak_day_idx < len(day_names) else f"Day {peak_day_idx}"
        st.metric("Peak Day", peak_day, f"{daily_demand.max()} appointments")
    
    with col3:
        avg_daily = daily_demand.mean()
        st.metric("Daily Average", f"{avg_daily:.1f}", f"appointments per day")

def financial_analytics(master_df, metrics):
    st.header("Financial Analytics")
    st.markdown("Revenue optimization and cost management insights")
    
    # Financial KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Potential Revenue", f"${metrics['total_revenue']:,.0f}")
    with col2:
        st.metric("Realized Revenue", f"${metrics['completed_revenue']:,.0f}")
    with col3:
        st.metric("Revenue at Risk", f"${metrics['lost_revenue']:,.0f}")
    with col4:
        st.metric("Recovery Potential", f"{(metrics['lost_revenue']/metrics['total_revenue'])*100:.1f}%")
    
    # Revenue analysis charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue by status
        revenue_by_status = master_df.groupby('status')['cost'].sum()
        fig_status_revenue = px.bar(
            x=revenue_by_status.index,
            y=revenue_by_status.values,
            title='Revenue by Appointment Status',
            labels={'x': 'Status', 'y': 'Total Revenue ($)'}
        )
        st.plotly_chart(fig_status_revenue, use_container_width=True)
    
    with col2:
        # Revenue by specialization
        spec_revenue = master_df.groupby('specialization')['cost'].sum()
        fig_spec_revenue = px.bar(
            x=spec_revenue.index,
            y=spec_revenue.values,
            title='Revenue by Medical Specialization',
            labels={'x': 'Specialization', 'y': 'Total Revenue ($)'}
        )
        st.plotly_chart(fig_spec_revenue, use_container_width=True)
    
    # ROI Calculator
    st.subheader("ROI Calculator - No-Show Reduction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_no_show = st.slider("Current No-Show Rate (%)", 0, 100, int(metrics['no_show_rate']*100))
        target_no_show = st.slider("Target No-Show Rate (%)", 0, current_no_show, 20)
        implementation_cost = st.number_input("Implementation Cost ($)", value=25000)
    
    with col2:
        reduction_percentage = (current_no_show - target_no_show) / current_no_show
        potential_recovery = metrics['lost_revenue'] * reduction_percentage
        roi_percentage = (potential_recovery - implementation_cost) / implementation_cost * 100
        
        st.metric("Potential Annual Recovery", f"${potential_recovery:,.0f}")
        st.metric("ROI", f"{roi_percentage:.0f}%")
        st.metric("Payback Period", f"{implementation_cost/potential_recovery*12:.1f} months")

def quality_analytics(master_df):
    st.header("Quality Analytics")
    st.markdown("Patient experience and clinical outcome insights")
    
    # Patient demographics analysis
    col1, col2 = st.columns(2)
    
    with col1:
        fig_age = px.histogram(
            master_df,
            x='age',
            nbins=15,  
            title='Patient Age Distribution',
            labels={'age': 'Patient Age (years)', 'count': 'Number of Patients'}
)
        st.plotly_chart(fig_age, use_container_width=True)
    
    with col2:
        gender_counts = master_df['gender'].value_counts()
        fig_gender = px.pie(
            values=gender_counts.values,
            names=gender_counts.index,
            title='Patient Gender Distribution'
        )
        st.plotly_chart(fig_gender, use_container_width=True)
    
    # Completion patterns
    st.subheader("Appointment Completion Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Completion rate by hour
        hourly_completion = master_df.groupby('hour')['is_no_show'].agg(['count', 'mean'])
        hourly_completion['completion_rate'] = 1 - hourly_completion['mean']
        
        fig_hourly = px.line(
            x=hourly_completion.index,
            y=hourly_completion['completion_rate'] * 100,
            title='Completion Rate by Hour of Day',
            labels={'x': 'Hour', 'y': 'Completion Rate (%)'}
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        # Completion by specialization
        spec_completion = master_df.groupby('specialization')['is_no_show'].mean()
        completion_by_spec = (1 - spec_completion) * 100
        
        fig_spec_comp = px.bar(
            x=completion_by_spec.index,
            y=completion_by_spec.values,
            title='Completion Rate by Specialization',
            labels={'x': 'Specialization', 'y': 'Completion Rate (%)'}
        )
        st.plotly_chart(fig_spec_comp, use_container_width=True)

def business_recommendations(master_df, metrics):
    st.header("Business Recommendations")
    st.markdown("Data-driven strategies for healthcare optimization")
    
    # Executive Summary
    st.markdown("### Executive Summary")
    
    lost_revenue = metrics['lost_revenue']
    no_show_rate = metrics['no_show_rate'] * 100
    
    st.error(f"""
    **CRITICAL ISSUE:** Current no-show rate of {no_show_rate:.1f}% is causing ${lost_revenue:,.0f} in lost revenue annually.
    Industry benchmark is 15-20%. Immediate intervention required.
    """)
    
    # Recommendations with ROI calculations
    st.markdown("### Strategic Recommendations")
    
    tab1, tab2, tab3 = st.tabs(["Immediate Actions", "Medium-term Strategy", "Long-term Growth"])
    
    with tab1:
        st.markdown("#### No-Show Reduction Program")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            **Implementation Plan:**
            1. **Appointment Reminder System** - SMS/Email 24-48 hours before
            2. **Flexible Rescheduling** - Online portal for easy changes  
            3. **Confirmation Calls** - For high-risk appointments
            4. **Waitlist Management** - Fill cancelled slots immediately
            5. **Incentive Program** - Rewards for consistent attendance
            """)
        
        with col2:
            potential_recovery = lost_revenue * 0.5
            st.metric("Potential Annual Savings", f"${potential_recovery:,.0f}")
            st.metric("Implementation Cost", "$25,000")
            st.metric("ROI", f"{(potential_recovery/25000)*100:.0f}%")
        
        st.success(f"**Expected Impact:** Reduce no-show rate from {no_show_rate:.1f}% to 25%, recovering ${potential_recovery:,.0f} annually")
    
    with tab2:
        st.markdown("#### Resource Optimization Strategy")
        
        # Analyze current resource allocation
        spec_analysis = master_df.groupby('specialization').agg({
            'appointment_id': 'count',
            'cost': 'mean'
        }).round(2)
        spec_analysis.columns = ['appointments', 'avg_revenue']
        
        highest_volume = spec_analysis.sort_values('appointments', ascending=False).index[0]
        highest_revenue = spec_analysis.sort_values('avg_revenue', ascending=False).index[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Current State Analysis:**
            - Highest volume: {highest_volume} ({spec_analysis.loc[highest_volume, 'appointments']} appointments)
            - Highest revenue per appointment: {highest_revenue} (${spec_analysis.loc[highest_revenue, 'avg_revenue']:.0f})
            - Average patient age: {metrics['avg_patient_age']:.0f} years
            """)
        
        with col2:
            st.markdown("""
            **Optimization Actions:**
            - Reallocate resources to high-revenue specializations
            - Cross-train staff for flexibility
            - Adjust capacity based on demand patterns
            - Implement dynamic scheduling
            """)
    
    with tab3:
        st.markdown("#### Long-term Growth Strategy")
        
        st.markdown("""
        **Strategic Initiatives:**
        
        1. **Technology Integration**
           - AI-powered appointment scheduling
           - Predictive analytics for resource planning
           - Patient portal for self-service
        
        2. **Service Expansion**
           - Telemedicine capabilities
           - Specialized clinics for high-revenue services
           - Preventive care programs
        
        3. **Partnership Development**
           - Insurance provider negotiations
           - Referral network expansion
           - Community health partnerships
        
        **Expected Outcomes:**
        - 25-30% increase in operational efficiency
        - 15-20% revenue growth
        - Improved patient satisfaction scores
        """)

if __name__ == "__main__":
    main()