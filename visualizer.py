import plotly.express as px

def create_bar_chart(df, title, color_scale, is_ascending=False, target_val='Volume'):
    if df.empty:
        return None
    
    # Sorting berdasarkan pilihan user
    df_sorted = df.sort_values(by=target_val, ascending=is_ascending)
    
    fig = px.bar(
        df_sorted, 
        x=target_val, 
        y='Broker_Name', 
        text=target_val,
        orientation='h',
        color=target_val,
        color_continuous_scale=color_scale,
        title=title
    )
    
    fig.update_traces(texttemplate='%{x:,.2f}', textposition='outside',cliponaxis=False)
    fig.update_layout(
        height=400, 
        margin=dict(l=10, r=40, t=30, b=40),
        showlegend=False,
        xaxis=dict(tickformat=',.2f')
    )
    return fig