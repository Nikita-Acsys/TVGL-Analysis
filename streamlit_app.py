import numpy as np
import pandas as pd
import TVGL as tvgl
import streamlit as st
import plotly.graph_objs as go

# Load your data
og_df = pd.read_csv(r'input_data_prices.csv')
returns = pd.read_csv(r'input_data_returns.csv')
og_df['Datetime'] = pd.to_datetime(og_df['Datetime'])

# Streamlit App
st.set_page_config(layout="wide")
st.title("TVGL Analysis")

# Dropdowns for selecting assets
asset1 = st.selectbox("Select Asset 1:", og_df.columns[1:])
asset2 = st.selectbox("Select Asset 2:", og_df.columns[1:])

# Inputs for TVGL parameters
lamb = st.number_input("Lambda:", value=0.8, step=0.1)
beta = st.number_input("Beta:", value=1, step=1)
lengthOfSlice = st.number_input("Length of Slice:", value=5, step=1)

# Button to update the graphs
if st.button("Update Graphs"):
    df = og_df.copy()
    df.set_index('Datetime', inplace=True)

    # Prepare the data for TVGL
    data = returns[[asset1, asset2]].values
    thetaSet = tvgl.TVGL(data, lengthOfSlice, lamb, beta, eps=2e-3, indexOfPenalty=1, verbose=False)
    
    # Calculate the ratio
    df[f'{asset1}_{asset2}_ratio'] = df[asset1] / df[asset2]

    # Remove outliers from the ratio using IQR method
    Q1 = df[f'{asset1}_{asset2}_ratio'].quantile(0.25)
    Q3 = df[f'{asset1}_{asset2}_ratio'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df_filtered = df[(df[f'{asset1}_{asset2}_ratio'] >= lower_bound) & (df[f'{asset1}_{asset2}_ratio'] <= upper_bound)]

# Prepare price plot with dual y-axes
    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(
        x=df.index, 
        y=df[asset1], 
        mode='lines', 
        name=asset1, 
        line=dict(color='blue'), 
        yaxis='y1',
        hovertemplate=f'{asset1}: %{{y:.2f}}<extra></extra>'
    ))  
    price_fig.add_trace(go.Scatter(
        x=df.index, 
        y=df[asset2], 
        mode='lines', 
        name=asset2, 
        line=dict(color='green'), 
        yaxis='y2',
        hovertemplate=f'{asset2}: %{{y:.2f}}<extra></extra>'
    ))

    # Update layout for dual axes and hover
    price_fig.update_layout(
        title='Close Prices', 
        xaxis_title='Date',
        yaxis_title=f'{asset1} Price',
        yaxis2=dict(title=f'{asset2} Price', overlaying='y', side='right', showgrid=False),
        legend=dict(x=0, y=1),
        hovermode='x unified'
    ) # Position the legend


    # Prepare ratio plot
    ratio_fig = go.Figure()
    ratio_fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered[f'{asset1}_{asset2}_ratio'], mode='lines', name=f'{asset1}/{asset2} Ratio', line=dict(color='orange')))
    ratio_fig.update_layout(title=f'{asset1} to {asset2} Ratio', xaxis_title='Date', yaxis_title=f'{asset1}/{asset2} Ratio')

    # Prepare precision plot
    precision_fig = go.Figure()
    precision_values = [theta[0, 1] for theta in thetaSet]
    dates = df.index[::lengthOfSlice][:len(precision_values)]
    precision_fig.add_trace(go.Scatter(x=dates, y=precision_values, mode='lines', name=f'Precision {asset1}-{asset2}'))
    precision_fig.update_layout(title='Precision Matrix Over Time', xaxis_title='Time', yaxis_title='Value')

    # Display the graphs in Streamlit
    st.plotly_chart(price_fig)
    st.plotly_chart(ratio_fig)
    st.plotly_chart(precision_fig)
