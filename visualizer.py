import plotly.express as px

def create_bar_chart(df, title, color_scale, is_ascending=False, target_val='Volume'):
    """
    Membuat bar chart horizontal dengan sorting yang konsisten.
    
    Parameters:
    - df: DataFrame dengan kolom Broker_Name dan target_val
    - title: Judul chart
    - color_scale: Skala warna (Viridis, Plasma, dll)
    - is_ascending: Jika True, urutkan dari kecil ke besar (ascending)
    - target_val: Nama kolom yang akan divisualisasikan (Volume atau Fee)
    """
    if df.empty:
        return None
    
    # Sorting berdasarkan pilihan user terhadap target_val
    # PENTING: Kita sort df terlebih dahulu sebelum pass ke plotly
    df_sorted = df.sort_values(by=target_val, ascending=is_ascending).reset_index(drop=True)
    
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
    
    fig.update_traces(texttemplate='%{x:,.0f}', textposition='outside', cliponaxis=False)
    fig.update_layout(
        height=400, 
        margin=dict(l=10, r=40, t=30, b=40),
        showlegend=False,
        xaxis=dict(tickformat=',.0f'),
        yaxis=dict(autorange='reversed')  # PERBAIKAN: Reverse Y-axis agar broker pertama di atas
    )
    return fig