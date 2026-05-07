import plotly.express as px

def create_bar_chart(df, title, color_scale, is_ascending=False):
    if df.empty:
        return None
    
    # Sorting berdasarkan pilihan user
    df_sorted = df.sort_values(by='Volume', ascending=is_ascending)
    
    fig = px.bar(
        df_sorted, 
        x='Volume', 
        y='Broker_Name', 
        text='Volume',
        orientation='h',
        color='Volume',
        color_continuous_scale=color_scale,
        title=title
    )
    
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(
        height=350, 
        margin=dict(l=10, r=10, t=30, b=40),
        showlegend=False
    )
    return fig