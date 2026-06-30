import dash
from dash import dash_table, dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import unidecode
from datetime import datetime
import re
import numpy as np

image_path = 'assets/logo.png'

items = [
    dbc.DropdownMenuItem("GROUPE DE RESOLUTION", id="item-1"),
    dbc.DropdownMenuItem("AGENCE", id="item-2"),
    dbc.DropdownMenuItem("TICKET", id="item-3"),
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)
server = app.server  # Expose le serveur Flask pour Gunicorn

# Augmenter la limite de taille des fichiers uploadés (défaut ~2MB, ici 50MB)
server.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ── Palette centralisée
C = {
    "bg":      "#0d1117", "sidebar": "#161b22", "card":   "#1c2128",
    "card2":   "#21262d", "accent":  "#58a6ff", "green":  "#3fb950",
    "red":     "#f78166", "orange":  "#ffa657", "muted":  "#8b949e",
    "text":    "#e6edf3", "border":  "#30363d", "violet": "#6e40c9",
}
PLOTLY_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", family="'Segoe UI', sans-serif"),
    margin=dict(l=12, r=12, t=48, b=12),
    hoverlabel=dict(bgcolor="#21262d", font_color="#e6edf3", bordercolor="#30363d"),
    xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=11)),
    yaxis=dict(showgrid=True, gridcolor="#30363d", zeroline=False, color="#8b949e", tickfont=dict(size=11)),
)
def apply_layout(fig, **kw):
    cfg = dict(PLOTLY_BASE); cfg.update(kw); fig.update_layout(**cfg); return fig

card_style  = {"borderRadius": "12px", "border": f"1px solid #30363d",
               "backgroundColor": "#1c2128", "padding": "16px", "marginBottom": "16px"}
btn_style   = {"borderRadius": "8px", "fontWeight": "600", "fontSize": "13px",
               "border": "none", "cursor": "pointer", "letterSpacing": "0.3px"}
label_style = {"color": "#8b949e", "fontWeight": "500", "fontSize": "11px", "marginBottom": "5px",
               "display": "block", "textTransform": "uppercase", "letterSpacing": "0.8px"}
title_style = {"color": "#e6edf3", "fontWeight": "700", "marginBottom": "15px"}

def kpi_card(label, value, icon, color, suffix=""):
    return dbc.Col(html.Div([
        html.Div([
            html.Span(icon, style={"fontSize":"20px","marginRight":"8px"}),
            html.Span(label, style={"fontSize":"11px","color":"#8b949e","textTransform":"uppercase",
                                    "letterSpacing":"0.8px","fontWeight":"600"}),
        ], style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
        html.Div(f"{value}{suffix}", style={"fontSize":"26px","fontWeight":"800","color":color,"lineHeight":"1"}),
    ], style={
        "backgroundColor":"#1c2128","border":"1px solid #30363d",
        "borderLeft":f"3px solid {color}","borderRadius":"10px",
        "padding":"14px 18px","marginBottom":"16px",
    }), width=3)

def kpi_row(df):
    total = df["Complaint reference"].nunique() if "Complaint reference" in df.columns else 0
    hd    = (df["DELAI_RECLAMATION"]=="HORS DELAI").sum() if "DELAI_RECLAMATION" in df.columns else 0
    taux  = round(hd/total*100,1) if total else 0
    fond  = (df["NATURE"]=="FONDEE").sum() if "NATURE" in df.columns else 0
    return dbc.Row([
        kpi_card("Total réclamations", f"{total:,}".replace(","," "), "📋", "#58a6ff"),
        kpi_card("Hors délai",         f"{hd:,}".replace(","," "),   "⚠️", "#f78166"),
        kpi_card("Taux hors délai",    taux,                          "📊", "#ffa657", "%"),
        kpi_card("Fondées",            f"{fond:,}".replace(","," "), "✅", "#3fb950"),
    ], className="mb-2")

DURATION_PATTERNS = {
    'days': re.compile(r'(\d+)\s*[dDjJ]'), 'hours': re.compile(r'(\d+)\s*[hH]'),
    'minutes': re.compile(r'(\d+)\s*[mM]'), 'seconds': re.compile(r'(\d+)\s*[sS]')
}

def convert_to_days(duration):
    if pd.isna(duration) or duration == '': return 0
    total_seconds = 0
    for unit, pattern in DURATION_PATTERNS.items():
        match = pattern.search(duration)
        if match:
            value = int(match.group(1))
            if unit == 'days': total_seconds += value * 86400
            elif unit == 'hours': total_seconds += value * 3600
            elif unit == 'minutes': total_seconds += value * 60
            elif unit == 'seconds': total_seconds += value
    return round(total_seconds / 86400, 2)

def categorize_segment(segment):
    if str(segment).startswith('101'): return 'PARTICULIER'
    elif str(segment).startswith('102'): return 'PROFESSIONNEL'
    elif segment == 'INCONNU': return 'INCONNU'
    else: return 'CORPORATE'

def load_data(df):
    df.columns = df.columns.str.replace("\n", " ")
    df["Claim SLA"] = df["Claim SLA"].str.replace('[', "", regex=False).str.replace('REC', "", regex=False).str.replace('-', "", regex=False).str.replace(']', "", regex=False)
    df['Claim SLA'] = df['Claim SLA'].str.split(',').explode().reset_index(drop=True)
    df['Claim SLA'] = df['Claim SLA'].str.strip()
    df['SLA_ETAPE'] = df['Claim SLA'].apply(lambda x: x.split(':')[0].strip() if ':' in x else None)
    df['Value'] = df['Claim SLA'].apply(lambda x: x.split(':')[1].strip() if ':' in x else None)
    df['SEGMENTATION'] = df['Segment'].apply(categorize_segment)
    df["Nature of the claim"] = df["Nature of the claim"].fillna("INCONNU")
    df.loc[df["Nature of the claim"] == 'Fondé avec faute SG', "NATURE"] = 'FONDEE'
    df.loc[df["Nature of the claim"] == 'Fondé sans faute SG', "NATURE"] = 'FONDEE'
    df.loc[df["Nature of the claim"] == 'Non fondée', "NATURE"] = 'NON FONDEE'
    df['NATURE'] = df['NATURE'].fillna('INCONNU')
    df['Date of creation'] = pd.to_datetime(df['Date of creation'].str.split(' ').str[0], format='%d-%m-%Y', errors='coerce')
    df['Resolved date'] = pd.to_datetime(df['Resolved date'].str.split(' ').str[0], format='%d-%m-%Y', errors='coerce')
    df['Annee'] = df['Date of creation'].dt.year
    df['Mois'] = df['Date of creation'].dt.month
    df["GROUPE RESOLUTION"] = df["Resolution group"].str.replace('SGCI', "", regex=False)
    df["AGENCE"] = df["Branch"].str[6:]
    df["Typology"] = df.Typology.str.upper().apply(unidecode.unidecode).str.replace("'", " ", regex=False)
    df["DATE_AUJOURDUI"] = datetime.today()
    time_columns = ["Time Technical Study", "Time Additional information", "Time Treatment",
                    "Time SUPPORT", "Time Treated", "Time To Complete", "Time Initialization",
                    "Time Validate Regularisation", "Time In the process of regularization", "Time Third party return waiting"]
    for col in time_columns:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce') / 86400
        else: df[col] = 0
    df["Treatment duration"] = df['Treatment duration (In Days)'].apply(convert_to_days) if 'Treatment duration (In Days)' in df.columns else 0
    df["Duree Traitee"] = df['Value'].apply(convert_to_days)
    df['signe'] = np.where(df["Value"].str[0] == "-", -1, 1)
    df["Duree Traitee"] = pd.to_numeric(df["Duree Traitee"], errors='coerce').fillna(0).astype(int)
    df["signe"] = df["signe"].astype(int)
    df["SLA_JOURS"] = df["Duree Traitee"] * df["signe"]
    df['DATE_RECLAMATION'] = df['Resolved date'].where(df['Resolved date'].notna(), df['DATE_AUJOURDUI']).sub(df['Date of creation']).dt.days
    df['DELAI_RECLAMATION'] = np.where(df['DATE_RECLAMATION'] <= 30, 'PAS HORS DELAI', 'HORS DELAI')
    return df

def parse_contents(contents, filename):
    try:
        content_type, content_string = contents.split(',', 1)
        decoded = base64.b64decode(content_string)
        if filename.endswith('.csv'):
            # Essayer UTF-8, puis latin-1 si ça échoue
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=7)
            except UnicodeDecodeError:
                df = pd.read_csv(io.StringIO(decoded.decode('latin-1')), header=7)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl', header=7)
        else:
            return None, f"Type de fichier non pris en charge : {filename}"
        if df.empty:
            return None, "Le fichier est vide."
        return df, ""
    except Exception as e:
        return None, f"Erreur lors du chargement : {str(e)}"

def create_datatable_from_df(df, page_size=10):
    def style_sla_cells(dataframe):
        styles = []
        for i, row in dataframe.iterrows():
            for col in dataframe.columns:
                if col == dataframe.columns[0]: continue
                value = row[col]
                if pd.isnull(value): continue
                try: val_float = float(value)
                except: continue
                if val_float > 0: styles.append({'if': {'row_index': i, 'column_id': col}, 'color': '#2ecc71', 'fontWeight': 'bold'})
                elif val_float < 0: styles.append({'if': {'row_index': i, 'column_id': col}, 'color': '#e74c3c', 'fontWeight': 'bold'})
        return styles
    return dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns], data=df.to_dict('records'), page_size=page_size,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'minWidth': '120px', 'whiteSpace': 'normal',
                    'color': 'white', 'backgroundColor': '#22272e', 'border': 'none'},
        style_header={'backgroundColor': '#2b303a', 'fontWeight': 'bold', 'color': 'white', 'border': 'none'},
        style_data_conditional=style_sla_cells(df), fill_width=True)

def add_line_breaks(text, max_chars=10):
    words = text.split(); line = ""; new_text = ""
    for word in words:
        if len(line) + len(word) + 1 <= max_chars: line += (word + " ")
        else: new_text += line.rstrip() + "<br>"; line = word + " "
    new_text += line.rstrip()
    return new_text

def generate_view_1(data):
    graphs = [dbc.Col(kpi_row(data), width=12)]
    # Donut nature
    nat = data.groupby("NATURE")["Complaint reference"].count().reset_index(name='nombre')
    fig1 = px.pie(nat, values='nombre', names='NATURE', title="Répartition par nature",
                  hole=0.55, color_discrete_sequence=["#58a6ff","#3fb950","#f78166","#ffa657"], template='plotly_dark')
    fig1.update_traces(textinfo='percent+label', hovertemplate="<b>%{label}</b><br>%{value}<extra></extra>")
    apply_layout(fig1)
    fig1.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig1, config={"displayModeBar":False}), style=card_style), width=6))
    # Line évolution avec aire
    ev = data.groupby("Mois")["Complaint reference"].nunique().reset_index(name='nombre')
    ev['Mois'] = ev['Mois'].apply(lambda m: datetime(2000, m, 1).strftime('%b'))
    fig2 = go.Figure(go.Scatter(
        x=ev['Mois'], y=ev['nombre'], mode='lines+markers+text',
        text=ev['nombre'], textposition='top center',
        line=dict(color="#58a6ff", width=2.5), marker=dict(size=8, color="#58a6ff"),
        fill='tozeroy', fillcolor="rgba(88,166,255,0.08)",
        hovertemplate="<b>%{x}</b><br>%{y} réclamations<extra></extra>",
    ))
    fig2.update_layout(title="Évolution mensuelle des réclamations")
    apply_layout(fig2)
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig2, config={"displayModeBar":False}), style=card_style), width=6))
    # Bar agences
    ag = data.groupby("AGENCE")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre').tail(10)
    fig3 = px.bar(ag, y="AGENCE", x='nombre', text='nombre', orientation='h',
                  title='Top 10 agences', color='nombre',
                  color_continuous_scale=px.colors.sequential.Blues, template='plotly_dark')
    fig3.update_traces(textfont_size=12, marker_line_width=0,
                       hovertemplate="<b>%{y}</b><br>%{x} réclamations<extra></extra>")
    fig3.update_layout(coloraxis_showscale=False)
    apply_layout(fig3, xaxis=dict(visible=False))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig3, config={"displayModeBar":False}), style=card_style), width=12))
    return graphs

def generate_view_2(data):
    graphs = [dbc.Col(kpi_row(data), width=12)]
    gr = data.groupby("GROUPE RESOLUTION")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre', ascending=False).head(5)
    gr['lbl'] = gr['GROUPE RESOLUTION'].apply(lambda x: add_line_breaks(x, max_chars=15))
    fig1 = px.bar(gr, x='lbl', y='nombre', text='nombre', title="Top 5 — Groupe de résolution",
                  color='nombre', color_continuous_scale=px.colors.sequential.Purples, template='plotly_dark')
    fig1.update_traces(textfont_size=12, marker_line_width=0)
    fig1.update_layout(coloraxis_showscale=False, xaxis_tickangle=0)
    apply_layout(fig1, yaxis=dict(visible=False), xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=11)))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig1, config={"displayModeBar":False}), style=card_style), width=6))
    ag = data.groupby("AGENCE")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre').tail(10)
    fig2 = px.bar(ag, y='AGENCE', x='nombre', text='nombre', orientation='h', title='Top 10 agences',
                  color='nombre', color_continuous_scale=px.colors.sequential.Teal, template='plotly_dark')
    fig2.update_traces(textfont_size=12, marker_line_width=0)
    fig2.update_layout(coloraxis_showscale=False)
    apply_layout(fig2, xaxis=dict(visible=False))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig2, config={"displayModeBar":False}), style=card_style), width=6))
    return graphs

def generate_view_3(data):
    graphs = [dbc.Col(kpi_row(data), width=12)]
    if 'Creator' in data.columns:
        cr = data.groupby("Creator")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre', ascending=False).head(10)
        cr['lbl'] = cr['Creator'].apply(lambda x: add_line_breaks(x, max_chars=15))
        fig1 = px.bar(cr, x='lbl', y='nombre', text='nombre', title="Top 10 — Par créateur",
                      color='nombre', color_continuous_scale=px.colors.sequential.Reds, template='plotly_dark')
        fig1.update_traces(textfont_size=12, marker_line_width=0)
        fig1.update_layout(coloraxis_showscale=False, xaxis_tickangle=0)
        apply_layout(fig1, yaxis=dict(visible=False), xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=11)))
        graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig1, config={"displayModeBar":False}), style=card_style), width=12))
    ty = data.groupby("Typology")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre', ascending=False)
    ty['lbl'] = ty['Typology'].apply(lambda x: add_line_breaks(x, max_chars=15))
    fig2 = px.bar(ty, x='lbl', y='nombre', text='nombre', title="Répartition par typologie",
                  color='nombre', color_continuous_scale=px.colors.sequential.Sunset, template='plotly_dark')
    fig2.update_traces(textfont_size=12, marker_line_width=0)
    fig2.update_layout(coloraxis_showscale=False, xaxis_tickangle=0)
    apply_layout(fig2, yaxis=dict(visible=False), xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=11)))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig2, config={"displayModeBar":False}), style=card_style), width=12))
    return graphs

def generate_view_4(data):
    graphs = [dbc.Col(kpi_row(data), width=12)]
    # Donut délai
    dl = data["DELAI_RECLAMATION"].value_counts().reset_index(); dl.columns=["d","c"]
    fig0 = px.pie(dl, values='c', names='d', title="Respect des délais", hole=0.55,
                  color_discrete_map={"PAS HORS DELAI":"#3fb950","HORS DELAI":"#f78166"}, template='plotly_dark')
    fig0.update_traces(textinfo='percent+label')
    apply_layout(fig0)
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig0, config={"displayModeBar":False}), style=card_style), width=6))
    cn = data.groupby("Client notification channel")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre', ascending=False)
    cn['lbl'] = cn['Client notification channel'].apply(lambda x: add_line_breaks(x, max_chars=15))
    fig1 = px.bar(cn, x='lbl', y='nombre', text='nombre', title="Canaux de notification",
                  color='nombre', color_continuous_scale=px.colors.sequential.Teal, template='plotly_dark')
    fig1.update_traces(textfont_size=12, marker_line_width=0)
    fig1.update_layout(coloraxis_showscale=False, xaxis_tickangle=0)
    apply_layout(fig1, yaxis=dict(visible=False), xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=11)))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig1, config={"displayModeBar":False}), style=card_style), width=6))
    ty = data.groupby("Typology")["Complaint reference"].count().reset_index(name='nombre').sort_values('nombre', ascending=False)
    ty['lbl'] = ty['Typology'].apply(lambda x: add_line_breaks(x, max_chars=15))
    fig2 = px.bar(ty, x='lbl', y='nombre', text='nombre', title="Répartition par typologie",
                  color='nombre', color_continuous_scale=px.colors.sequential.Sunset, template='plotly_dark')
    fig2.update_traces(textfont_size=12, marker_line_width=0)
    fig2.update_layout(coloraxis_showscale=False, xaxis_tickangle=0)
    apply_layout(fig2, yaxis=dict(visible=False), xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=11)))
    graphs.append(dbc.Col(html.Div(dcc.Graph(figure=fig2, config={"displayModeBar":False}), style=card_style), width=12))
    return graphs

def generate_sla_table(data, group_by_field):
    mean_sla = data.pivot_table(index=group_by_field, values='SLA_JOURS', columns=['SLA_ETAPE'], aggfunc='mean').reset_index()
    count_sla = data.pivot_table(index=group_by_field, values='SLA_JOURS', columns=['SLA_ETAPE'], aggfunc='count').reset_index()
    mean_sla_rounded = mean_sla.round(2)
    tables = [
        html.Div(html.H5(f"Moyenne des SLA par {group_by_field}", style={"color":"white","backgroundColor":"#6a0dad","padding":"8px 12px","borderRadius":"8px","fontWeight":"bold","marginTop":"10px","marginBottom":"10px","textAlign":"center"})),
        create_datatable_from_df(mean_sla_rounded, page_size=10),
        html.Div(html.H5(f"Nombre d'entrées SLA par {group_by_field}", style={"color":"white","backgroundColor":"#6a0dad","padding":"8px 12px","borderRadius":"8px","fontWeight":"bold","marginTop":"20px","marginBottom":"10px","textAlign":"center"})),
        create_datatable_from_df(count_sla, page_size=10)
    ]
    return [dbc.Card(tables, style=card_style)]

def generate_sla_ticket_table(data):
    mean_sla = data.pivot_table(index='Complaint reference', values='SLA_JOURS', columns=['SLA_ETAPE'], aggfunc='mean').reset_index()
    mean_sla_rounded = mean_sla.round(2)
    table = [
        html.Div(html.H5("Moyenne des SLA par Ticket", style={"color":"white","backgroundColor":"#6a0dad","padding":"8px 12px","borderRadius":"8px","fontWeight":"bold","marginTop":"10px","marginBottom":"10px","textAlign":"center"})),
        create_datatable_from_df(mean_sla_rounded, page_size=10)
    ]
    return [dbc.Card(table, style=card_style)]

graph_mapping = {
    "btn-1": generate_view_1, "btn-2": generate_view_2,
    "btn-3": generate_view_3, "btn-4": generate_view_4,
    "item-1": lambda data: generate_sla_table(data, 'GROUPE RESOLUTION'),
    "item-2": lambda data: generate_sla_table(data, 'AGENCE'),
    "item-3": generate_sla_ticket_table
}

# ── PAGE ACCUEIL ─────────────────────────────────────────────────────────────
accueil = html.Div([
    html.Div([
        html.Img(src=image_path, style={'height': '80px', 'marginBottom': '24px'}),
        html.H1("Plateforme Réclamations SGCI", style={"color":"white","fontWeight":"800","fontSize":"32px","marginBottom":"12px"}),
        html.P("Choisissez un module pour continuer.", style={"color":"#8b949e","fontSize":"16px","marginBottom":"48px"}),
        html.Div([
            # Bouton 1 — Dashboard
            html.Div([
                html.Div("📊", style={"fontSize":"36px","marginBottom":"12px"}),
                html.H4("Dashboard Réclamations", style={"color":"white","fontWeight":"700","marginBottom":"8px"}),
                html.P("Analysez les réclamations, SLA, agences et segments.", style={"color":"#8b949e","fontSize":"13px","marginBottom":"20px"}),
                dbc.Button("Ouvrir le dashboard", id="btn-open-dashboard", color="primary",
                           style={"borderRadius":"8px","fontWeight":"600","width":"100%"}),
            ], style={"backgroundColor":"#1c2128","border":"1px solid #30363d","borderTop":"3px solid #58a6ff",
                      "borderRadius":"12px","padding":"28px","flex":"1","minWidth":"220px","textAlign":"center"}),
            # Bouton 2 — Lien externe
            html.Div([
                html.Div("🌐", style={"fontSize":"36px","marginBottom":"12px"}),
                html.H4("Ressource Externe", style={"color":"white","fontWeight":"700","marginBottom":"8px"}),
                html.P("Accédez à une ressource de référence externe.", style={"color":"#8b949e","fontSize":"13px","marginBottom":"20px"}),
                html.A(dbc.Button("Ouvrir le lien", color="success",
                           style={"borderRadius":"8px","fontWeight":"600","width":"100%"}),
                       href="https://fr.wikipedia.org/wiki/Lionel_Messi", target="_blank"),
            ], style={"backgroundColor":"#1c2128","border":"1px solid #30363d","borderTop":"3px solid #3fb950",
                      "borderRadius":"12px","padding":"28px","flex":"1","minWidth":"220px","textAlign":"center"}),
            # Bouton 3 — Page future
            html.Div([
                html.Div("🚧", style={"fontSize":"36px","marginBottom":"12px"}),
                html.H4("Module en cours", style={"color":"white","fontWeight":"700","marginBottom":"8px"}),
                html.P("Ce module est en cours de développement.", style={"color":"#8b949e","fontSize":"13px","marginBottom":"20px"}),
                dbc.Button("Bientôt disponible", id="btn-open-module", color="warning",
                           style={"borderRadius":"8px","fontWeight":"600","width":"100%"}),
            ], style={"backgroundColor":"#1c2128","border":"1px solid #30363d","borderTop":"3px solid #ffa657",
                      "borderRadius":"12px","padding":"28px","flex":"1","minWidth":"220px","textAlign":"center"}),
        ], style={"display":"flex","gap":"20px","flexWrap":"wrap","justifyContent":"center"}),
    ], style={"maxWidth":"900px","margin":"0 auto","textAlign":"center"}),
], style={"backgroundColor":"#0d1117","minHeight":"100vh","display":"flex",
          "alignItems":"center","justifyContent":"center","padding":"40px 20px"})

# ── DASHBOARD (original inchangé) ────────────────────────────────────────────
DD_STYLE = {"color": "#000", "fontSize": "13px"}

def filter_block(label, comp):
    return html.Div([html.Label(label, style=label_style), comp,
                     html.Div(style={"marginBottom": "14px"})])

dashboard = dbc.Container(fluid=True,
    style={"backgroundColor": "#0d1117", "minHeight": "100vh", "padding": "0"},
    children=[
        # ── Topbar ──
        html.Div([
            dbc.Row([
                dbc.Col(html.Img(src=image_path, style={"height": "38px"}), width="auto"),
                dbc.Col(html.Span("Dashboard Réclamations", style={
                    "color": "#e6edf3", "fontWeight": "700", "fontSize": "17px", "lineHeight": "38px",
                }), width="auto"),
                dbc.Col(
                    dbc.Button("← Accueil", id="btn-retour-accueil", color="secondary", size="sm",
                               style={**btn_style, "fontSize": "12px"}),
                    width="auto", style={"marginLeft": "auto"}
                ),
            ], align="center"),
        ], style={
            "backgroundColor": "#161b22", "borderBottom": "1px solid #30363d",
            "padding": "12px 24px", "position": "sticky", "top": "0", "zIndex": "100",
        }),
        dbc.Row([
            # ── Sidebar filtres ──
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Span("⚙ ", style={"opacity": "0.7"}),
                        html.Span("Filtres", style={"color": "#e6edf3", "fontWeight": "700",
                                                     "fontSize": "13px", "textTransform": "uppercase", "letterSpacing": "1px"}),
                    ], style={"marginBottom": "18px", "paddingBottom": "12px", "borderBottom": "1px solid #30363d"}),
                    filter_block("🎫 Ticket",     dcc.Dropdown(id="ticket-filter",      clearable=True, style=DD_STYLE)),
                    filter_block("🏢 Agence",     dcc.Dropdown(id="agence-filter",      multi=True,     style=DD_STYLE)),
                    filter_block("📅 Année",      dcc.Dropdown(id="annee-dropdown",     clearable=True, style=DD_STYLE)),
                    filter_block("🗓 Mois",       dcc.Dropdown(id="mois-dropdown",      clearable=True, style=DD_STYLE)),
                    filter_block("👤 Segmentation",dcc.Dropdown(id="segmentation-filter",clearable=True,style=DD_STYLE)),
                    filter_block("⏱ Délai",      dcc.Dropdown(id="delai-filter",       multi=True,     style=DD_STYLE)),
                    dbc.Button([html.I(className="bi bi-arrow-counterclockwise me-2"), "Réinitialiser"],
                               id="reset-filters", color="danger", outline=True, size="sm",
                               className="w-100 mt-1", style={**btn_style, "fontSize": "12px"}),
                    dcc.Upload(id="upload-data",
                        children=html.Div([
                            html.Span("☁", style={"fontSize": "26px", "display": "block", "marginBottom": "4px"}),
                            html.Span("Glisser / cliquer", style={"fontSize": "12px", "color": "#e6edf3", "fontWeight": "600"}),
                            html.Br(),
                            html.Span("CSV ou Excel", style={"fontSize": "11px", "color": "#8b949e"}),
                        ], style={"textAlign": "center"}),
                        style={"marginTop": "20px", "borderWidth": "1.5px", "borderStyle": "dashed",
                               "borderColor": "#58a6ff", "borderRadius": "10px", "padding": "18px 8px", "cursor": "pointer",
                               "backgroundColor": "rgba(88,166,255,0.04)"},
                        max_size=50 * 1024 * 1024,
                        multiple=False),
                    html.Div(id='upload-status'),
                ], style={
                    "backgroundColor": "#161b22", "borderRight": "1px solid #30363d",
                    "padding": "20px 16px", "minHeight": "calc(100vh - 64px)",
                }),
            ], width=2, style={"padding": "0"}),
            # ── Zone principale ──
            dbc.Col([
                html.Div([
                    dbc.Row([
                        dbc.Col(dbc.Button("📊 Vue Générale", id="btn-1", color="primary",   className="w-100", style={**btn_style, "fontSize": "12px", "padding": "8px"}), width=2),
                        dbc.Col(dbc.Button("👥 Par Groupe",   id="btn-2", color="secondary", className="w-100", style={**btn_style, "fontSize": "12px", "padding": "8px"}), width=2),
                        dbc.Col(dbc.Button("🎫 Par Ticket",  id="btn-3", color="secondary", className="w-100", style={**btn_style, "fontSize": "12px", "padding": "8px"}), width=2),
                        dbc.Col(dbc.Button("📡 Canaux",      id="btn-4", color="secondary", className="w-100", style={**btn_style, "fontSize": "12px", "padding": "8px"}), width=2),
                        dbc.Col(dbc.DropdownMenu(label="📋 SLA PAR", children=items, id="sla-dropdown",
                                                  color="info", className="w-100"), width=2),
                    ], className="mb-4 g-2"),
                    html.Div(id="content", style={"minHeight": "400px"}),
                    dcc.Store(id="stored-data"),
                    dcc.Store(id="stored-active-view"),
                    # ── Panneau debug (toujours visible en production) ──
                    html.Details([
                        html.Summary("🔍 Logs de débogage", style={
                            "color": "#8b949e", "fontSize": "12px", "cursor": "pointer",
                            "padding": "8px 0", "userSelect": "none",
                        }),
                        html.Div([
                            dbc.Button("⚡ Tester les callbacks", id="btn-test-cb", size="sm",
                                color="secondary", outline=True,
                                style={"fontSize": "11px", "marginBottom": "8px"}),
                            html.Div(id="debug-panel", style={
                                "backgroundColor": "#0d1117",
                                "border": "1px solid #30363d",
                                "borderRadius": "8px",
                                "padding": "12px",
                                "fontFamily": "monospace",
                                "fontSize": "12px",
                                "color": "#e6edf3",
                                "whiteSpace": "pre-wrap",
                                "maxHeight": "300px",
                                "overflowY": "auto",
                            }),
                        ]),
                    ], style={"marginTop": "32px", "borderTop": "1px solid #30363d", "paddingTop": "16px"}),
                ], style={"padding": "24px"}),
            ], width=10, style={"padding": "0"}),
        ], style={"margin": "0"}),
    ]
)

# ═══════════════════════════════════════════════════════════════
# MODULE KPI — à coller dans reclam_final.py
# Remplace le bloc "MODULE FUTUR" et ajoute les callbacks
# ═══════════════════════════════════════════════════════════════
import sqlite3, json
from dash import dash_table

DB_PATH = "kpi_historique.db"

# ── Init SQLite ──────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Table CRC : une ligne par indicateur par mois
    cur.execute("""CREATE TABLE IF NOT EXISTS kpi_crc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mois TEXT, indicateur TEXT, objectif TEXT, valeur TEXT,
        UNIQUE(mois, indicateur)
    )""")
    # Table SAT : une ligne par entité par feuille par mois
    cur.execute("""CREATE TABLE IF NOT EXISTS kpi_sat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mois TEXT, feuille TEXT, entite TEXT, valeur TEXT,
        UNIQUE(mois, feuille, entite)
    )""")
    # Table SAT PRO : une ligne par segment/indicateur par mois
    cur.execute("""CREATE TABLE IF NOT EXISTS kpi_sat_pro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mois TEXT, segment TEXT, indicateur TEXT, valeur TEXT,
        UNIQUE(mois, segment, indicateur)
    )""")
    con.commit(); con.close()

init_db()

# ── Parsers ──────────────────────────────────────────────────
def parse_crc(contents, filename, mois):
    """KPI CRC.xlsx : col A=indicateur, col B=objectif, col C+=mois.
    Recherche robuste de la ligne d'en-tête (gère les cellules fusionnées)."""
    _, data = contents.split(',', 1)
    raw = base64.b64decode(data)
    rows = []
    try:
        xf = pd.read_excel(io.BytesIO(raw), sheet_name=0, header=None, engine='openpyxl')
        if xf.empty or xf.shape[0] < 2:
            return False, "Fichier vide ou structure invalide."

        # Recherche de la ligne d'en-tête : celle qui contient le plus de mots-clés mois
        mois_kw = ['JANV','FEV','FÉV','MARS','AVR','MAI','JUIN','JUIL','AOUT','AOÛT',
                   'SEPT','OCT','NOV','DEC','DÉC']
        header_row = None
        best_score = 0
        for i in range(min(10, len(xf))):
            row_str = ' '.join([str(v).upper() for v in xf.iloc[i] if str(v).strip() not in ('nan','')])
            score = sum(1 for k in mois_kw if k in row_str)
            if score > best_score:
                best_score = score
                header_row = i
        if header_row is None:
            header_row = 2  # fallback raisonnable

        data_start = header_row + 1
        for i in range(data_start, len(xf)):
            indic = str(xf.iloc[i, 1]).strip()
            obj   = str(xf.iloc[i, 2]).strip() if xf.shape[1] > 2 else ''
            if indic in ('nan', '') or indic.upper() == 'NAN':
                continue
            vals_row = xf.iloc[i, 3:].dropna() if xf.shape[1] > 3 else pd.Series(dtype=object)
            valeur = str(vals_row.iloc[-1]).strip() if len(vals_row) > 0 else 'N/A'
            rows.append((mois, indic, obj if obj != 'nan' else '', valeur))

        if not rows:
            return False, "Aucun indicateur trouvé — vérifiez la structure du fichier."
    except Exception as e:
        return False, f"Erreur lecture : {str(e)}"

    try:
        con = sqlite3.connect(DB_PATH)
        con.executemany(
            "INSERT OR REPLACE INTO kpi_crc (mois, indicateur, objectif, valeur) VALUES (?,?,?,?)",
            rows
        )
        con.commit(); con.close()
        return True, f"{len(rows)} indicateurs CRC sauvegardés pour {mois}"
    except Exception as e:
        return False, f"Erreur SQLite : {str(e)}"


def parse_sat(contents, filename, mois):
    """KPIS SAT.xlsx : plusieurs feuilles, col A=entité, B+= mois"""
    _, data = contents.split(',', 1)
    raw = base64.b64decode(data)
    rows = []
    try:
        xl = pd.ExcelFile(io.BytesIO(raw), engine='openpyxl')
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            # Trouver la ligne d'en-tête (contient "Fevrier" ou "FEVRIER" ou un mois)
            mois_keywords = ['JANV','FEV','MARS','AVR','MAI','JUIN','JUIL','AOUT','SEPT','OCT','NOV','DEC',
                             'Janv','Fev','Mars','Avr','Mai','Juin','Juil','Aout','Sept','Oct','Nov','Dec']
            hrow = 1  # fallback
            for i, row in df.iterrows():
                row_str = ' '.join([str(v) for v in row])
                if any(k in row_str for k in mois_keywords):
                    hrow = i
                    break
            for i in range(hrow + 1, len(df)):
                entite = str(df.iloc[i, 0]).strip()
                if entite in ('nan', '') or entite.upper() == 'NAN':
                    continue
                # Prendre la dernière valeur non-vide
                vals = df.iloc[i, 1:].dropna()
                valeur = str(vals.iloc[-1]).strip() if len(vals) > 0 else 'N/A'
                rows.append((mois, sheet, entite, valeur))
    except Exception as e:
        return False, str(e)

    try:
        con = sqlite3.connect(DB_PATH)
        con.executemany(
            "INSERT OR REPLACE INTO kpi_sat (mois, feuille, entite, valeur) VALUES (?,?,?,?)",
            rows
        )
        con.commit(); con.close()
        return True, f"{len(rows)} lignes SAT sauvegardées pour {mois}"
    except Exception as e:
        return False, str(e)


def parse_sat_pro(contents, filename, mois):
    """KPIS SAT PRO.xlsx : segments PRI/PRO/CORPO, indicateurs Indice SAT / NPS / Nb répondants"""
    _, data = contents.split(',', 1)
    raw = base64.b64decode(data)
    rows = []
    try:
        df = pd.read_excel(io.BytesIO(raw), sheet_name=0, header=None, engine='openpyxl')
        current_segment = None
        for i, row in df.iterrows():
            seg_val = str(row.iloc[0]).strip()
            indic   = str(row.iloc[1]).strip()
            if seg_val not in ('nan','') and seg_val.upper() != 'NAN':
                current_segment = seg_val
            if indic in ('nan','') or indic.upper() == 'NAN' or not current_segment:
                continue
            vals = [str(v).strip() for v in row.iloc[2:] if str(v).strip() not in ('nan','')]
            valeur = vals[-1] if vals else 'N/A'
            rows.append((mois, current_segment, indic, valeur))
    except Exception as e:
        return False, str(e)

    try:
        con = sqlite3.connect(DB_PATH)
        con.executemany(
            "INSERT OR REPLACE INTO kpi_sat_pro (mois, segment, indicateur, valeur) VALUES (?,?,?,?)",
            rows
        )
        con.commit(); con.close()
        return True, f"{len(rows)} lignes SAT PRO sauvegardées pour {mois}"
    except Exception as e:
        return False, str(e)


# ── Lecture historique ───────────────────────────────────────
def get_crc_history():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM kpi_crc ORDER BY mois", con)
    con.close(); return df

def get_sat_history(feuille=None):
    con = sqlite3.connect(DB_PATH)
    q = "SELECT * FROM kpi_sat"
    if feuille: q += f" WHERE feuille='{feuille}'"
    q += " ORDER BY mois"
    df = pd.read_sql(q, con)
    con.close(); return df

def get_sat_pro_history():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM kpi_sat_pro ORDER BY mois", con)
    con.close(); return df

def get_mois_list():
    con = sqlite3.connect(DB_PATH)
    mois = []
    for table in ['kpi_crc','kpi_sat','kpi_sat_pro']:
        try:
            df = pd.read_sql(f"SELECT DISTINCT mois FROM {table}", con)
            mois.extend(df['mois'].tolist())
        except: pass
    con.close()
    return sorted(list(set(mois)))

# ── Layout module ────────────────────────────────────────────
def make_status_badge(text, color):
    return html.Span(text, style={
        "backgroundColor": color, "color": "#fff", "borderRadius": "6px",
        "padding": "3px 10px", "fontSize": "11px", "fontWeight": "700",
        "marginLeft": "8px",
    })

def upload_zone(label, uid, icon):
    return html.Div([
        html.Label([icon, f"  {label}"], style={**label_style, "fontSize": "12px", "marginBottom": "6px"}),
        dcc.Upload(id=uid,
            children=html.Div([
                html.Span("☁", style={"fontSize": "20px", "display": "block", "marginBottom": "2px"}),
                html.Span("Choisir le fichier", style={"fontSize": "11px", "color": "#8b949e"}),
            ], style={"textAlign": "center"}),
            style={"borderWidth": "1.5px", "borderStyle": "dashed", "borderColor": "#30363d",
                   "borderRadius": "8px", "padding": "10px 6px", "cursor": "pointer",
                   "backgroundColor": "#0d1117"},
            multiple=False),
        html.Div(id=f"{uid}-status", style={"fontSize": "11px", "marginTop": "4px", "minHeight": "16px"}),
        html.Div(style={"marginBottom": "14px"}),
    ])

MOIS_OPTIONS = [
    {"label": m, "value": m} for m in
    ["Janvier","Février","Mars","Avril","Mai","Juin",
     "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
]
ANNEE_OPTIONS = [{"label": str(a), "value": str(a)} for a in range(2024, 2028)]

module = dbc.Container(fluid=True,
    style={"backgroundColor": "#0d1117", "minHeight": "100vh", "padding": "0"},
    children=[
        # Topbar
        html.Div([dbc.Row([
            dbc.Col(html.Img(src='assets/logo.png', style={"height": "36px"}), width="auto"),
            dbc.Col(html.Span("Tableau de Bord KPI", style={
                "color": "#e6edf3", "fontWeight": "700", "fontSize": "16px",
                "fontFamily": "'Syne', sans-serif", "lineHeight": "36px"}), width="auto"),
            dbc.Col(html.Button("← Accueil", id="btn-retour-accueil-module", n_clicks=0, style={
                **btn_style, "backgroundColor": "transparent", "border": "1px solid #30363d",
                "color": "#8b949e", "padding": "6px 16px", "fontSize": "12px"}),
                width="auto", style={"marginLeft": "auto"}),
        ], align="center")],
        style={"backgroundColor": "#161b22", "borderBottom": "1px solid #30363d",
               "padding": "12px 24px", "position": "sticky", "top": "0", "zIndex": "100"}),

        dbc.Row([
            # ── Sidebar ──
            dbc.Col([html.Div([
                html.Div([
                    html.Span("📥 ", style={"opacity": "0.8"}),
                    html.Span("Import mensuel", style={"color": "#e6edf3", "fontWeight": "700",
                                                        "fontSize": "13px", "textTransform": "uppercase",
                                                        "letterSpacing": "1px"}),
                ], style={"marginBottom": "16px", "paddingBottom": "12px", "borderBottom": "1px solid #30363d"}),

                # Sélection mois/année
                html.Div([
                    html.Label("📅 Mois de référence", style=label_style),
                    dcc.Dropdown(id="kpi-mois-select", options=MOIS_OPTIONS, clearable=False,
                                 placeholder="Mois...", style={"color": "#000", "fontSize": "12px",
                                                               "marginBottom": "6px"}),
                    dcc.Dropdown(id="kpi-annee-select", options=ANNEE_OPTIONS, clearable=False,
                                 value="2026", style={"color": "#000", "fontSize": "12px"}),
                    html.Div(style={"marginBottom": "16px"}),
                ]),

                upload_zone("KPI CRC",     "upload-crc",     "📞"),
                upload_zone("KPIS SAT",    "upload-sat",     "😊"),
                upload_zone("KPIS SAT PRO","upload-sat-pro", "⭐"),

                html.Hr(style={"borderColor": "#30363d", "marginTop": "8px"}),

                # Filtre historique
                html.Label("🗂 Filtrer l'historique", style=label_style),
                dcc.Dropdown(id="kpi-hist-filter", clearable=True,
                             placeholder="Tous les mois...",
                             style={"color": "#000", "fontSize": "12px", "marginBottom": "14px"}),

            ], style={"backgroundColor": "#161b22", "borderRight": "1px solid #30363d",
                      "padding": "20px 16px", "minHeight": "calc(100vh - 64px)"})],
            width=2, style={"padding": "0"}),

            # ── Zone principale ──
            dbc.Col([html.Div([
                dbc.Row([
                    dbc.Col(dbc.Tabs(id="kpi-tabs", active_tab="tab-crc", children=[
                        dbc.Tab(label="📞 KPI CRC",      tab_id="tab-crc"),
                        dbc.Tab(label="😊 Satisfaction", tab_id="tab-sat"),
                        dbc.Tab(label="⭐ SAT PRO",      tab_id="tab-sat-pro"),
                    ]), width=9),
                    dbc.Col(
                        dbc.Button([html.I(className="bi bi-download me-2"), "Exporter Excel"],
                            id="btn-export-kpi", color="success", outline=True, size="sm",
                            className="w-100", style={**btn_style, "fontSize": "12px"}),
                        width=3,
                    ),
                ], align="center", className="mb-3"),
                dcc.Download(id="download-kpi-excel"),
                html.Div(id="kpi-tab-content", style={"minHeight": "400px"}),
            ], style={"padding": "24px"})],
            width=10, style={"padding": "0"}),
        ], style={"margin": "0"}),
    ]
)


# ═══════════════════════════════════════════════════════
# CALLBACKS MODULE KPI
# ═══════════════════════════════════════════════════════

def register_kpi_callbacks(app):

    # ── Upload CRC ──────────────────────────────────────
    @app.callback(
        Output("upload-crc-status", "children"),
        Output("kpi-hist-filter", "options"),
        Input("upload-crc", "contents"),
        State("upload-crc", "filename"),
        State("kpi-mois-select", "value"),
        State("kpi-annee-select", "value"),
        prevent_initial_call=True,
    )
    def upload_crc(contents, filename, mois, annee):
        if not contents:
            return "", dash.no_update
        if not mois or not annee:
            return html.Div("⚠ Sélectionnez d'abord le mois et l'année en haut de la sidebar !",
                style={"color": "#ffa657", "fontWeight": "700", "padding": "6px",
                       "backgroundColor": "rgba(255,166,87,0.1)", "borderRadius": "6px"}), dash.no_update
        mois_str = f"{mois} {annee}"
        ok, msg = parse_crc(contents, filename, mois_str)
        color = "#3fb950" if ok else "#f78166"
        icon  = "✅" if ok else "❌"
        opts  = [{"label": m, "value": m} for m in get_mois_list()]
        return html.Span(f"{icon} {msg}", style={"color": color}), opts

    # ── Upload SAT ──────────────────────────────────────
    @app.callback(
        Output("upload-sat-status", "children"),
        Output("kpi-hist-filter", "options", allow_duplicate=True),
        Input("upload-sat", "contents"),
        State("upload-sat", "filename"),
        State("kpi-mois-select", "value"),
        State("kpi-annee-select", "value"),
        prevent_initial_call=True,
    )
    def upload_sat(contents, filename, mois, annee):
        if not contents:
            return "", dash.no_update
        if not mois or not annee:
            return html.Div("⚠ Sélectionnez d'abord le mois et l'année en haut de la sidebar !",
                style={"color": "#ffa657", "fontWeight": "700", "padding": "6px",
                       "backgroundColor": "rgba(255,166,87,0.1)", "borderRadius": "6px"}), dash.no_update
        mois_str = f"{mois} {annee}"
        ok, msg = parse_sat(contents, filename, mois_str)
        color = "#3fb950" if ok else "#f78166"
        icon  = "✅" if ok else "❌"
        opts  = [{"label": m, "value": m} for m in get_mois_list()]
        return html.Span(f"{icon} {msg}", style={"color": color}), opts

    # ── Upload SAT PRO ───────────────────────────────────
    @app.callback(
        Output("upload-sat-pro-status", "children"),
        Output("kpi-hist-filter", "options", allow_duplicate=True),
        Input("upload-sat-pro", "contents"),
        State("upload-sat-pro", "filename"),
        State("kpi-mois-select", "value"),
        State("kpi-annee-select", "value"),
        prevent_initial_call=True,
    )
    def upload_sat_pro(contents, filename, mois, annee):
        if not contents:
            return "", dash.no_update
        if not mois or not annee:
            return html.Div("⚠ Sélectionnez d'abord le mois et l'année en haut de la sidebar !",
                style={"color": "#ffa657", "fontWeight": "700", "padding": "6px",
                       "backgroundColor": "rgba(255,166,87,0.1)", "borderRadius": "6px"}), dash.no_update
        mois_str = f"{mois} {annee}"
        ok, msg = parse_sat_pro(contents, filename, mois_str)
        color = "#3fb950" if ok else "#f78166"
        icon  = "✅" if ok else "❌"
        opts  = [{"label": m, "value": m} for m in get_mois_list()]
        return html.Span(f"{icon} {msg}", style={"color": color}), opts

    # ── Rendu des onglets ────────────────────────────────
    @app.callback(
        Output("kpi-tab-content", "children"),
        Input("kpi-tabs", "active_tab"),
        Input("kpi-hist-filter", "value"),
        Input("upload-crc", "contents"),
        Input("upload-sat", "contents"),
        Input("upload-sat-pro", "contents"),
    )
    def render_tab(tab, mois_filter, *_):
        if tab == "tab-crc":
            return render_crc(mois_filter)
        elif tab == "tab-sat":
            return render_sat(mois_filter)
        elif tab == "tab-sat-pro":
            return render_sat_pro(mois_filter)
        return html.Div("Sélectionnez un onglet")

    # ── Export Excel ──────────────────────────────────────
    @app.callback(
        Output("download-kpi-excel", "data"),
        Input("btn-export-kpi", "n_clicks"),
        State("kpi-tabs", "active_tab"),
        State("kpi-hist-filter", "value"),
        prevent_initial_call=True,
    )
    def export_excel(n, tab, mois_filter):
        if not n:
            return dash.no_update

        buffer = io.BytesIO()
        ts = datetime.now().strftime("%Y%m%d_%H%M")

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            if tab == "tab-crc":
                df = get_crc_history()
                if mois_filter: df = df[df["mois"] == mois_filter]
                if df.empty:
                    pivot = pd.DataFrame({"Message": ["Aucune donnée"]})
                else:
                    pivot = df.pivot_table(index=["indicateur","objectif"], columns="mois",
                                           values="valeur", aggfunc="first").reset_index()
                    pivot.columns.name = None
                pivot.to_excel(writer, sheet_name="KPI CRC", index=False)
                fname = f"KPI_CRC_export_{ts}.xlsx"

            elif tab == "tab-sat":
                df = get_sat_history()
                if mois_filter: df = df[df["mois"] == mois_filter]
                if df.empty:
                    pd.DataFrame({"Message": ["Aucune donnée"]}).to_excel(writer, sheet_name="SAT", index=False)
                else:
                    for feuille in df["feuille"].unique():
                        dff = df[df["feuille"] == feuille]
                        pivot = dff.pivot_table(index="entite", columns="mois",
                                                values="valeur", aggfunc="first").reset_index()
                        pivot.columns.name = None
                        sheet_name = feuille[:31] if len(feuille) > 31 else feuille
                        pivot.to_excel(writer, sheet_name=sheet_name, index=False)
                fname = f"KPIS_SAT_export_{ts}.xlsx"

            elif tab == "tab-sat-pro":
                df = get_sat_pro_history()
                if mois_filter: df = df[df["mois"] == mois_filter]
                if df.empty:
                    pivot = pd.DataFrame({"Message": ["Aucune donnée"]})
                else:
                    pivot = df.pivot_table(index=["segment","indicateur"], columns="mois",
                                           values="valeur", aggfunc="first").reset_index()
                    pivot.columns.name = None
                pivot.to_excel(writer, sheet_name="SAT PRO", index=False)
                fname = f"KPIS_SAT_PRO_export_{ts}.xlsx"
            else:
                return dash.no_update

        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), fname)


# ── Fonctions de rendu ───────────────────────────────────────

def _gcard(fig, width=12):
    return dbc.Col(
        html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}), style=card_style),
        width=width,
    )

def empty_state(msg="Aucune donnée disponible. Importez un fichier pour commencer."):
    return html.Div([
        html.Div("📭", style={"fontSize": "52px", "textAlign": "center", "marginBottom": "12px"}),
        html.P(msg, style={"color": "#8b949e", "textAlign": "center", "fontSize": "14px"}),
    ], style={"paddingTop": "80px"})


def render_crc(mois_filter):
    df = get_crc_history()
    if df.empty:
        return empty_state("Importez le fichier KPI CRC.xlsx pour afficher les indicateurs.")
    if mois_filter:
        df = df[df["mois"] == mois_filter]

    rows = []
    # KPI cards pour le dernier mois disponible
    last = df["mois"].max()
    df_last = df[df["mois"] == last]
    kpis_importants = ["Taux de joignabilité", "Taux d'occupation", "Taux d'interaction",
                       "Qualité d'écoute", "Taux de réponse à la 1ère demande"]
    colors_cycle = [C["accent"], C["green"], C["orange"], C["purple"] if "purple" in C else "#d2a8ff", C["red"]]

    kpi_cards = []
    for i, indic in enumerate(kpis_importants):
        row = df_last[df_last["indicateur"].str.contains(indic[:15], case=False, na=False)]
        val = row.iloc[0]["valeur"] if not row.empty else "N/A"
        obj = row.iloc[0]["objectif"] if not row.empty else ""
        kpi_cards.append(
            dbc.Col(html.Div([
                html.Div(indic[:25], style={"fontSize": "10px", "color": "#8b949e",
                                             "textTransform": "uppercase", "letterSpacing": "0.7px",
                                             "fontWeight": "600", "marginBottom": "6px"}),
                html.Div(val, style={"fontSize": "24px", "fontWeight": "800",
                                     "color": colors_cycle[i % len(colors_cycle)], "lineHeight": "1"}),
                html.Div(f"Obj: {obj}" if obj else "", style={"fontSize": "11px", "color": "#8b949e", "marginTop": "4px"}),
            ], style={**card_style, "borderLeft": f"3px solid {colors_cycle[i % len(colors_cycle)]}",
                      "padding": "14px 16px", "marginBottom": "12px"}),
            width=2)
        )
    rows.append(dbc.Row(kpi_cards, className="mb-3"))

    # Tableau complet
    pivot = df.pivot_table(index=["indicateur", "objectif"], columns="mois", values="valeur", aggfunc="first").reset_index()
    pivot.columns.name = None
    rows.append(dbc.Row([dbc.Col(html.Div([
        html.H6("Historique des indicateurs", style={"color": "#e6edf3", "fontWeight": "700", "marginBottom": "12px"}),
        dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in pivot.columns],
            data=pivot.to_dict("records"),
            page_size=12,
            style_table={"overflowX": "auto"},
            style_cell={"backgroundColor": "#1c2128", "color": "#e6edf3", "border": "1px solid #30363d",
                        "fontSize": "12px", "padding": "8px 12px", "minWidth": "100px"},
            style_header={"backgroundColor": "#21262d", "fontWeight": "700", "color": "#8b949e",
                          "border": "1px solid #30363d", "textTransform": "uppercase", "fontSize": "11px"},
            style_data_conditional=[{"if": {"column_id": "indicateur"}, "fontWeight": "600", "color": "#58a6ff"},
                                    {"if": {"row_index": "odd"}, "backgroundColor": "#21262d"}],
        ),
    ], style=card_style), width=12)]))

    # Graphique évolution taux joignabilité
    df_indics = df[df["indicateur"].str.contains("joignab|occupation|écoute|interact", case=False, na=False)].copy()
    if not df_indics.empty:
        df_indics["valeur_num"] = pd.to_numeric(df_indics["valeur"].str.replace('%','',regex=False), errors='coerce')
        fig = px.line(df_indics, x="mois", y="valeur_num", color="indicateur", markers=True,
                      title="Évolution des taux clés (%)", template="plotly_dark",
                      color_discrete_sequence=PALETTE if 'PALETTE' in dir() else px.colors.qualitative.Set2)
        fig.update_traces(mode="lines+markers+text", textposition="top center")
        apply_layout(fig)
        rows.append(dbc.Row([_gcard(fig, 12)]))

    return html.Div(rows)


def render_sat(mois_filter):
    df = get_sat_history()
    if df.empty:
        return empty_state("Importez le fichier KPIS SAT.xlsx pour afficher les indicateurs.")
    if mois_filter:
        df = df[df["mois"] == mois_filter]

    feuilles = df["feuille"].unique().tolist()
    tabs = []
    for feuille in feuilles:
        dff = df[df["feuille"] == feuille]
        # Pivot : entités en lignes, mois en colonnes
        pivot = dff.pivot_table(index="entite", columns="mois", values="valeur", aggfunc="first").reset_index()
        pivot.columns.name = None

        # Graphique bar pour le dernier mois
        last = dff["mois"].max()
        df_last = dff[dff["mois"] == last].copy()
        df_last["valeur_num"] = pd.to_numeric(
            df_last["valeur"].str.replace('%','',regex=False).str.replace(',','.'), errors='coerce')
        df_last = df_last.dropna(subset=["valeur_num"]).sort_values("valeur_num", ascending=False)

        content = [
            html.H6(f"Feuille : {feuille}", style={"color": "#e6edf3", "fontWeight": "700", "marginBottom": "12px"}),
        ]
        if not df_last.empty:
            fig = px.bar(df_last.head(20), x="entite", y="valeur_num", text="valeur",
                         title=f"{feuille} — {last}",
                         color="valeur_num",
                         color_continuous_scale=px.colors.sequential.Blues,
                         template="plotly_dark")
            fig.update_traces(textfont_size=11, marker_line_width=0)
            fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-30)
            apply_layout(fig, yaxis=dict(visible=False),
                         xaxis=dict(showgrid=False, zeroline=False, color="#8b949e", tickfont=dict(size=10)))
            content.append(dbc.Row([_gcard(fig, 12)]))

        content.append(
            dash_table.DataTable(
                columns=[{"name": c, "id": c} for c in pivot.columns],
                data=pivot.to_dict("records"),
                page_size=15,
                style_table={"overflowX": "auto", "marginTop": "16px"},
                style_cell={"backgroundColor": "#1c2128", "color": "#e6edf3",
                            "border": "1px solid #30363d", "fontSize": "12px", "padding": "7px 12px"},
                style_header={"backgroundColor": "#21262d", "fontWeight": "700", "color": "#8b949e",
                              "border": "1px solid #30363d", "fontSize": "11px"},
                style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#21262d"}],
            )
        )
        tabs.append(dbc.Tab(html.Div(content, style={"paddingTop": "16px"}),
                            label=feuille, tab_id=f"sat-{feuille}"))

    if not tabs:
        return empty_state()
    return dbc.Tabs(tabs, active_tab=f"sat-{feuilles[0]}")


def render_sat_pro(mois_filter):
    df = get_sat_pro_history()
    if df.empty:
        return empty_state("Importez le fichier KPIS SAT PRO.xlsx pour afficher les indicateurs.")
    if mois_filter:
        df = df[df["mois"] == mois_filter]

    segments = df["segment"].unique().tolist()
    rows = []

    # KPI cards par segment
    last = df["mois"].max()
    df_last = df[df["mois"] == last]
    seg_colors = {"PRI": C["accent"], "PRO": C["green"], "CORPO": C["orange"]}

    kpi_cards = []
    for seg in segments:
        dfs = df_last[df_last["segment"] == seg]
        color = seg_colors.get(seg.upper(), C["accent"])
        sub = []
        for _, r in dfs.iterrows():
            sub.append(html.Div([
                html.Span(r["indicateur"], style={"fontSize": "11px", "color": "#8b949e"}),
                html.Span(r["valeur"], style={"fontSize": "16px", "fontWeight": "800",
                                              "color": color, "float": "right"}),
            ], style={"marginBottom": "6px", "overflow": "hidden"}))
        kpi_cards.append(dbc.Col(html.Div([
            html.Div(seg, style={"fontSize": "13px", "fontWeight": "800", "color": color,
                                  "marginBottom": "12px", "textTransform": "uppercase",
                                  "letterSpacing": "1px"}),
            *sub,
        ], style={**card_style, "borderTop": f"3px solid {color}"}), width=4))
    rows.append(dbc.Row(kpi_cards, className="mb-3"))

    # Graphique évolution NPS par segment
    df_nps = df[df["indicateur"].str.upper().str.contains("NPS")].copy()
    if not df_nps.empty:
        df_nps["valeur_num"] = pd.to_numeric(df_nps["valeur"], errors='coerce')
        fig = px.line(df_nps, x="mois", y="valeur_num", color="segment", markers=True,
                      title="Évolution NPS par segment", template="plotly_dark",
                      color_discrete_map=seg_colors)
        fig.update_traces(mode="lines+markers+text",
                          text=df_nps["valeur_num"], textposition="top center")
        apply_layout(fig)
        rows.append(dbc.Row([_gcard(fig, 6)]))

    # Graphique évolution Indice SAT
    df_sat = df[df["indicateur"].str.upper().str.contains("SAT|INDICE")].copy()
    if not df_sat.empty:
        df_sat["valeur_num"] = pd.to_numeric(
            df_sat["valeur"].str.replace('%','',regex=False), errors='coerce')
        fig2 = px.line(df_sat, x="mois", y="valeur_num", color="segment", markers=True,
                       title="Évolution Indice SAT par segment (%)", template="plotly_dark",
                       color_discrete_map=seg_colors)
        fig2.update_traces(mode="lines+markers+text", textposition="top center")
        apply_layout(fig2)
        rows.append(dbc.Row([_gcard(fig2, 6)]))

    # Tableau historique
    pivot = df.pivot_table(index=["segment","indicateur"], columns="mois",
                           values="valeur", aggfunc="first").reset_index()
    pivot.columns.name = None
    rows.append(dbc.Row([dbc.Col(html.Div([
        html.H6("Historique complet", style={"color": "#e6edf3", "fontWeight": "700", "marginBottom": "12px"}),
        dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in pivot.columns],
            data=pivot.to_dict("records"),
            page_size=12,
            style_table={"overflowX": "auto"},
            style_cell={"backgroundColor": "#1c2128", "color": "#e6edf3",
                        "border": "1px solid #30363d", "fontSize": "12px", "padding": "8px 12px"},
            style_header={"backgroundColor": "#21262d", "fontWeight": "700", "color": "#8b949e",
                          "border": "1px solid #30363d", "fontSize": "11px"},
            style_data_conditional=[
                {"if": {"column_id": "segment"}, "fontWeight": "700", "color": "#58a6ff"},
                {"if": {"row_index": "odd"}, "backgroundColor": "#21262d"},
            ],
        ),
    ], style=card_style), width=12)]))

    return html.Div(rows)


# ── LAYOUT RACINE ─────────────────────────────────────────────────────────────
# On utilise display:none / display:block — PAS de routing, PAS de dcc.Location
# Les 3 pages sont toujours dans le DOM, on les affiche/masque simplement
app.layout = html.Div([
    html.Div(accueil,  id="page-accueil",  style={"display":"block"}),
    html.Div(dashboard, id="page-dashboard", style={"display":"none"}),
    html.Div(module,   id="page-module",   style={"display":"none"}),
])

# ── CALLBACK NAVIGATION ───────────────────────────────────────────────────────
@app.callback(
    Output("page-accueil",  "style"),
    Output("page-dashboard", "style"),
    Output("page-module",   "style"),
    Input("btn-open-dashboard",      "n_clicks"),
    Input("btn-open-module",         "n_clicks"),
    Input("btn-retour-accueil",      "n_clicks"),
    Input("btn-retour-accueil-module","n_clicks"),
    prevent_initial_call=True,
)
def navigate(n1, n2, n3, n4):
    show   = {"display": "block"}
    hide   = {"display": "none"}
    tid = ctx.triggered_id
    if tid == "btn-open-dashboard":
        return hide, show, hide
    if tid == "btn-open-module":
        return hide, hide, show
    # retour accueil (depuis dashboard ou module)
    return show, hide, hide

# ── CALLBACKS DASHBOARD (identiques à l'original) ─────────────────────────────
import traceback

@app.callback(
    Output('stored-data', 'data'),
    Output('upload-status', 'children'),
    Output('debug-panel', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def store_uploaded_data(contents, filename):
    ts = datetime.now().strftime("%H:%M:%S")
    logs = []

    if not contents or not filename:
        return dash.no_update, "", f"[{ts}] Aucun fichier recu."

    logs.append(f"[{ts}] Fichier recu : {filename}")
    logs.append(f"[{ts}] Taille base64 : {len(contents)} caracteres")

    try:
        df_raw, error = parse_contents(contents, filename)
        if error:
            logs.append(f"[{ts}] ERREUR parse : {error}")
            status = html.Div(f"Erreur : {error}", style={"color":"#f78166","fontSize":"12px","marginTop":"8px"})
            return dash.no_update, status, "\n".join(logs)
        logs.append(f"[{ts}] Parse OK - {len(df_raw)} lignes, {len(df_raw.columns)} colonnes")
        logs.append(f"[{ts}] Colonnes: {list(df_raw.columns[:6])}")
    except Exception as e:
        tb = traceback.format_exc()
        logs.append(f"[{ts}] EXCEPTION parse: {str(e)}")
        logs.append(tb)
        status = html.Div(f"Erreur lecture: {str(e)}", style={"color":"#f78166","fontSize":"12px","marginTop":"8px"})
        return dash.no_update, status, "\n".join(logs)

    try:
        df = load_data(df_raw)
        logs.append(f"[{ts}] load_data OK - {len(df)} lignes finales")
        if 'NATURE' in df.columns:
            logs.append(f"[{ts}] NATURE: {df['NATURE'].unique().tolist()}")
        if 'DELAI_RECLAMATION' in df.columns:
            logs.append(f"[{ts}] DELAI: {df['DELAI_RECLAMATION'].value_counts().to_dict()}")
        status = html.Div(
            f"Fichier charge : {filename} ({len(df)} lignes)",
            style={"color":"#3fb950","fontSize":"12px","marginTop":"8px","fontWeight":"600"}
        )
        return df.to_json(date_format='iso', orient='split'), status, "\n".join(logs)
    except Exception as e:
        tb = traceback.format_exc()
        logs.append(f"[{ts}] EXCEPTION load_data: {str(e)}")
        logs.append(tb)
        status = html.Div(f"Erreur traitement: {str(e)}", style={"color":"#f78166","fontSize":"12px","marginTop":"8px"})
        return dash.no_update, status, "\n".join(logs)


@app.callback(
    Output("debug-panel", "children", allow_duplicate=True),
    Input("btn-test-cb", "n_clicks"),
    prevent_initial_call=True,
)
def test_callback(n):
    ts = datetime.now().strftime("%H:%M:%S")
    import sys, platform
    lines = [
        f"[{ts}] Callback OK - les callbacks fonctionnent",
        f"[{ts}] Python : {sys.version.split()[0]}",
        f"[{ts}] Platform : {platform.system()}",
        f"[{ts}] Pandas : {pd.__version__}",
    ]
    try:
        import openpyxl
        lines.append(f"[{ts}] openpyxl : {openpyxl.__version__} - OK")
    except ImportError:
        lines.append(f"[{ts}] openpyxl : MANQUANT - les .xlsx ne fonctionneront pas !")
    try:
        import unidecode
        lines.append(f"[{ts}] unidecode : OK")
    except ImportError:
        lines.append(f"[{ts}] unidecode : MANQUANT !")
    return "\n".join(lines)


register_kpi_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
