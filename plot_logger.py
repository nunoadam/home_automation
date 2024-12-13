import duckdb
import plotly.express as px
import numpy as np
import pandas as pd

def calculate_vpd_hpa(T, RH, altitude=657):
    """
    Calculate VPD (Vapor Pressure Deficit) in hPa.
    """
    e_sat = 6.1078 * np.exp((17.269 * T) / (T + 237.3))  # Saturated vapor pressure in hPa
    e_air = e_sat * (RH / 100)  # Actual vapor pressure in hPa

    # Adjust for altitude
    p_air = 1013.25 * (1 - 0.0065 * altitude / 288.15)**5.255  # Pressure at altitude in hPa
    e_sat_site = e_sat * (p_air / 1013.25)
    e_air_site = e_air * (p_air / 1013.25)

    vpd = e_sat_site - e_air_site  # VPD in hPa
    
    return float(vpd)  # Return VPD as a float
    
def dew_point(temperature: float, humidity: float):
    if humidity < 0 or humidity > 100:
        raise ValueError("Humidity must be between 0 and 100")
    if temperature < -100 or temperature > 100:
        raise ValueError("Temperature is out of range")
    return temperature - ((100 - humidity) / 5)

def plot(metric, hours = 24, devices = None, height=500):
   
    def fetch_data(metric, hours):
        
        additional_metrics = ''
        
        if metric == 'vpd' or metric == 'dew':
            additional_metrics = "or metric in ('temperature', 'humidity')"
            
        devices_filter = ""
        if devices:
            devices_filter = f"and device in ({', '.join([repr(d) for d in devices])})"
        
        query = f"""
                select
                to_timestamp(timestamp) as fecha,
                device,
                metric,
                value
                from 'csv/*/*.csv'
                where to_timestamp(timestamp) >= current_timestamp - interval {hours} hour
                and (metric = '{metric}' {additional_metrics})
                {devices_filter}
                order by device, metric, fecha
                """
        
        return duckdb.sql(query).df()

    # Fetch raw data for the relevant metrics
    df = fetch_data(metric, hours)
    
    
    if metric == "activePower":
        df['value'] = df['value'] * 1000

    # Pivot the DataFrame to get temperature and humidity in separate columns for each device
    df_pivot = df.pivot_table(index=["fecha", "device"], columns="metric", values="value", aggfunc="sum")

    # Merge the temperature and humidity data
    df_pivot = df_pivot.reset_index()

    # Handle the plotting logic for metrics that require temperature and humidity (vpd, dew)
    if metric == 'vpd':
        # Calculate VPD for each row using temperature and humidity
        df_pivot['vpd'] = np.vectorize(calculate_vpd_hpa)(df_pivot['temperature'], df_pivot['humidity'])
        title = "VPD"
        y_col = 'vpd'
    elif metric == 'dew':
        # Calculate Dew Point for each row using temperature and humidity
        df_pivot['dew_temp'] = np.vectorize(dew_point)(df_pivot['temperature'], df_pivot['humidity'])
        title = "Dew Point Temperature"
        y_col = 'dew_temp'
    else:
        title = f"{metric}"
        y_col = metric

    # Create Plotly line chart
    fig = px.line(
        df_pivot,
        x="fecha",
        y=y_col,
        height=height,
        color="device",
        title=title
    )
    
    if metric == 'vpd':

        reference_lines = [4, 16]

        for line in reference_lines:
            fig.add_hline(y=line, line_dash="dash", line_color="grey", annotation_text=f"y={line}", line_width=1, annotation_position="top left")

    fig.update_layout(
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, title=""),
        #yaxis=dict (showticklabels=False),
        xaxis_title="",
        yaxis_title="",
        title="",
        margin=dict(l=0, r=0, t=20, b=0)
    )

    return fig, df_pivot

def multiplot(metrics = ['temperature', 'dew'], hours = 24, devices = None, height=500):

    df_pivot_list = []

    for metric in metrics:
        df_pivot = plot(metric, hours, devices)[1]
        
        df_pivot['metric'] = metric
        
        df_pivot_list.append(df_pivot)
        
    df_combined = pd.concat(df_pivot_list, ignore_index=True)

    df_combined = df_combined.sort_values(by='fecha')
    
    if 'temperature' not in metrics:
        df_combined = df_combined.drop(columns=['temperature'], errors='ignore')
    if 'humidity' not in metrics:
        df_combined = df_combined.drop(columns=['humidity'], errors='ignore')

    fig = px.line(
            df_combined,
            x="fecha",
            y=df_combined.columns[df_combined.columns != 'fecha'],  # Plot all columns except 'fecha'
            height=height,
            color="device",
            #line_group="metric",  # Use the 'metric' column to differentiate lines for each metric
            line_dash="metric",
            title="Combined Metrics Plot"
        )
    
    return fig, df_pivot
