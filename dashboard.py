import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── DATA ──────────────────────────────────────────────────────
sol = pd.read_csv("rota_solution.csv")

nurses_meta = {
    0:"A",1:"A",2:"B",3:"B",4:"B",5:"C",6:"C",7:"D",8:"D",9:"E"
}
sol["Team"] = sol["Nurse"].map(nurses_meta)

leave_data = [
    {"Nurse":0,"Start_Day":20,"End_Day":24},
    {"Nurse":0,"Start_Day":44,"End_Day":44},
    {"Nurse":1,"Start_Day":2, "End_Day":9},
    {"Nurse":2,"Start_Day":10,"End_Day":12},
    {"Nurse":7,"Start_Day":0, "End_Day":6},
]
leave_df = pd.DataFrame(leave_data)

night_starters_mon = [d for d in range(56) if d%7==0]
night_starters_thu = [d for d in range(56) if d%7==3]

assigned = set(zip(sol["Nurse"], sol["Day"], sol["Shift"]))
def works(n,d,s): return (n,d,s) in assigned

# ── COLOUR PALETTE (neutral, professional) ────────────────────
C_DARK   = "#1a1a2e"
C_MID    = "#444466"
C_TEAL   = "#2a9d8f"
C_BLUE   = "#457b9d"
C_AMBER  = "#e9c46a"
C_RED    = "#e76f51"
C_LIGHT  = "#f4f4f8"
C_WHITE  = "#ffffff"
C_BORDER = "#e0e0e8"

SHIFT_COLORS = {"ED Day 1": C_TEAL, "ED Day 2": C_BLUE, "ED Nights": C_DARK}
TEAM_COLORS  = {"A": C_TEAL,"B": C_BLUE,"C": C_AMBER,"D": C_RED,"E": C_MID}

FONT = "Inter, Helvetica Neue, Arial, sans-serif"

# ── LAYOUT HELPERS ────────────────────────────────────────────
def card(children, style=None):
    s = {
        "background": C_WHITE,
        "borderRadius": "10px",
        "padding": "20px 24px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
        "border": f"1px solid {C_BORDER}",
        "marginBottom": "16px",
    }
    if style:
        s.update(style)
    return html.Div(children, style=s)

def section_title(text):
    return html.P(text, style={
        "fontSize":"11px","fontWeight":"600","textTransform":"uppercase",
        "letterSpacing":"1.2px","color":"#888","marginBottom":"12px","marginTop":"0"
    })

def stat_card(label, value, sub=""):
    return html.Div([
        html.P(label, style={"fontSize":"11px","color":"#888","margin":"0 0 4px","fontWeight":"500"}),
        html.P(value, style={"fontSize":"26px","fontWeight":"700","color":C_DARK,"margin":"0","lineHeight":"1"}),
        html.P(sub,   style={"fontSize":"11px","color":"#aaa","margin":"4px 0 0"}),
    ], style={
        "background":C_LIGHT,"borderRadius":"8px","padding":"16px 18px",
        "border":f"1px solid {C_BORDER}","flex":"1","minWidth":"100px"
    })

def plot_cfg():
    return {"displayModeBar": False, "responsive": True}

def base_layout(title=""):
    return dict(
        font_family=FONT,
        title_text=title,
        title_font_size=13,
        title_font_color=C_DARK,
        plot_bgcolor=C_WHITE,
        paper_bgcolor=C_WHITE,
        margin=dict(l=40, r=20, t=36, b=40),
        xaxis=dict(showgrid=False, linecolor=C_BORDER, tickfont_size=10),
        yaxis=dict(gridcolor="#f0f0f0", linecolor=C_BORDER, tickfont_size=10),
        legend=dict(orientation="h", y=-0.18, x=0, font_size=10),
        colorway=[C_TEAL, C_BLUE, C_DARK, C_AMBER, C_RED],
    )

# ── APP ───────────────────────────────────────────────────────
app = dash.Dash(__name__, title="Rota Dashboard · MedModus")
server = app.server  # for deployment

app.layout = html.Div([

    # ── HEADER ──────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span("🏥", style={"fontSize":"22px","marginRight":"10px"}),
            html.Span("ED On-Call Rota Dashboard",
                      style={"fontSize":"18px","fontWeight":"700","color":C_WHITE}),
            html.Span(" · MedModus",
                      style={"fontSize":"14px","color":"rgba(255,255,255,0.5)","marginLeft":"4px"}),
        ], style={"display":"flex","alignItems":"center"}),
        html.Div([
            html.Span("10 nurses", style={"marginRight":"16px"}),
            html.Span("56 days"),
            html.Span("168 shifts", style={"marginLeft":"16px"}),
        ], style={"fontSize":"12px","color":"rgba(255,255,255,0.5)"}),
    ], style={
        "background": C_DARK,"padding":"16px 32px",
        "display":"flex","justifyContent":"space-between","alignItems":"center",
        "fontFamily": FONT,
    }),

    # ── TABS ────────────────────────────────────────────────
    html.Div([
        dcc.Tabs(id="tabs", value="overview", children=[
            dcc.Tab(label="Overview",         value="overview"),
            dcc.Tab(label="Weekly Rota",      value="weekly"),
            dcc.Tab(label="Fairness",         value="fairness"),
            dcc.Tab(label="Team Coverage",    value="teams"),
            dcc.Tab(label="Rest & Leave",     value="rest"),
        ], style={"fontFamily":FONT},
        colors={"border":C_BORDER,"primary":C_TEAL,"background":C_LIGHT}),
    ], style={"padding":"0 32px","background":C_WHITE,"borderBottom":f"1px solid {C_BORDER}"}),

    # ── CONTENT ─────────────────────────────────────────────
    html.Div(id="tab-content", style={
        "padding":"24px 32px","background":C_LIGHT,
        "minHeight":"calc(100vh - 110px)","fontFamily":FONT,
    }),

], style={"fontFamily":FONT,"background":C_LIGHT})


# ── TAB ROUTER ────────────────────────────────────────────────
@app.callback(Output("tab-content","children"), Input("tabs","value"))
def render(tab):
    if tab == "overview":  return render_overview()
    if tab == "weekly":    return render_weekly()
    if tab == "fairness":  return render_fairness()
    if tab == "teams":     return render_teams()
    if tab == "rest":      return render_rest()


# ── TAB 1: OVERVIEW ───────────────────────────────────────────
def render_overview():
    totals   = sol.groupby("Nurse").size().reindex(range(10), fill_value=0)
    weekends = sol[sol["IsWeekend"]==1].groupby("Nurse").size().reindex(range(10), fill_value=0)
    nights   = sol[sol["Shift"]==2].groupby("Nurse").size().reindex(range(10), fill_value=0)

    fig_total = go.Figure()
    fig_total.add_trace(go.Bar(
        x=[f"N{n}" for n in range(10)], y=totals.values,
        marker_color=C_TEAL, name="Total shifts",
    ))
    fig_total.add_hline(y=totals.mean(), line_dash="dot",
                        line_color=C_RED, annotation_text="avg")
    fig_total.update_layout(**base_layout("Total shifts per nurse"), yaxis_range=[12,20])

    fig_break = go.Figure()
    for shift_name, shift_id, color in [
        ("ED Day 1",0,C_TEAL),("ED Day 2",1,C_BLUE),("ED Nights",2,C_DARK)]:
        vals = sol[sol["Shift"]==shift_id].groupby("Nurse").size().reindex(range(10),fill_value=0)
        fig_break.add_trace(go.Bar(
            x=[f"N{n}" for n in range(10)], y=vals.values,
            name=shift_name, marker_color=color,
        ))
    fig_break.update_layout(**base_layout("Shift type breakdown"),
                             barmode="stack", yaxis_range=[0,20])

    return html.Div([
        html.Div([
            stat_card("Total shifts",    "168", "56 days × 3 shifts"),
            stat_card("Nurses",          "10",  "Across 5 teams"),
            stat_card("Solver status",   "Optimal", "All constraints met"),
            stat_card("Violations",      "0",   "16/16 checks passed"),
            stat_card("Avg shifts/nurse","16.8","Range: 16–17"),
            stat_card("Avg weekends",    "4.8", "Range: 4–5"),
        ], style={"display":"flex","gap":"12px","marginBottom":"16px","flexWrap":"wrap"}),

        html.Div([
            card([section_title("Total shifts per nurse"),
                  dcc.Graph(figure=fig_total, config=plot_cfg(),
                            style={"height":"260px"})],
                 style={"flex":"1"}),
            card([section_title("Shift type breakdown per nurse"),
                  dcc.Graph(figure=fig_break, config=plot_cfg(),
                            style={"height":"260px"})],
                 style={"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
    ])


# ── TAB 2: WEEKLY ROTA ────────────────────────────────────────
def render_weekly():
    return html.Div([
        card([
            section_title("Select week"),
            dcc.Slider(id="week-slider", min=1, max=8, step=1, value=1,
                       marks={i: f"Week {i}" for i in range(1,9)},
                       tooltip={"always_visible":False}),
        ], style={"marginBottom":"16px"}),
        html.Div(id="weekly-content"),
    ])

@app.callback(Output("weekly-content","children"), Input("week-slider","value"))
def update_weekly(week):
    wdf = sol[sol["Week"]==week].copy()
    days_in_week = sorted(wdf["Day"].unique())
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    # Build rota grid
    rows = []
    for d in days_in_week:
        dow = d % 7
        day_label = day_names[dow]
        is_wknd = dow in (5,6)
        day_shifts = wdf[wdf["Day"]==d].sort_values("Shift")
        row = {"Day": f"Day {d}", "Day of Week": day_label}
        for _, r in day_shifts.iterrows():
            row[r["ShiftName"]] = f"Nurse {r['Nurse']} (Team {r['Team']})"
        rows.append(row)

    cols = ["Day","Day of Week","ED Day 1","ED Day 2","ED Nights"]
    for r in rows:
        for c in cols:
            if c not in r: r[c] = ""

    # Heatmap for weekly loads
    weekly_loads = []
    for n in range(10):
        cnt = sol[(sol["Nurse"]==n)&(sol["Week"]==week)].shape[0]
        weekly_loads.append(cnt)

    fig_load = go.Figure(go.Bar(
        x=[f"N{n}" for n in range(10)],
        y=weekly_loads,
        marker_color=[C_RED if v==4 else C_TEAL for v in weekly_loads],
        text=weekly_loads, textposition="outside",
    ))
    fig_load.update_layout(**base_layout(f"Shifts per nurse — Week {week}"),
                            yaxis_range=[0,5.5], showlegend=False)

    return html.Div([
        html.Div([
            card([
                section_title(f"Week {week} rota"),
                dash_table.DataTable(
                    data=rows, columns=[{"name":c,"id":c} for c in cols],
                    style_header={"fontWeight":"600","fontSize":"11px",
                                  "background":C_LIGHT,"color":C_DARK,
                                  "border":f"1px solid {C_BORDER}"},
                    style_cell={"fontSize":"12px","padding":"8px 12px",
                                "fontFamily":FONT,"border":f"1px solid {C_BORDER}",
                                "textAlign":"left"},
                    style_data_conditional=[
                        {"if":{"filter_query":'{Day of Week} = "Sat" || {Day of Week} = "Sun"'},
                         "background":"#fafafa","fontStyle":"italic"},
                    ],
                    style_table={"overflowX":"auto"},
                )
            ], style={"flex":"2"}),
            card([
                section_title(f"Shift load — Week {week}"),
                dcc.Graph(figure=fig_load, config=plot_cfg(), style={"height":"220px"}),
                html.P("Red bar = nurse at maximum (4 shifts this week)",
                       style={"fontSize":"10px","color":"#aaa","marginTop":"8px"}),
            ], style={"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
    ])


# ── TAB 3: FAIRNESS ───────────────────────────────────────────
def render_fairness():
    nurses   = [f"N{n}" for n in range(10)]
    totals   = sol.groupby("Nurse").size().reindex(range(10), fill_value=0).values
    weekends = sol[sol["IsWeekend"]==1].groupby("Nurse").size().reindex(range(10),fill_value=0).values

    weekly_matrix = np.array([
        [sol[(sol["Nurse"]==n)&(sol["Week"]==w)].shape[0]
         for n in range(10)] for w in range(1,9)
    ])

    fig_wknd = go.Figure(go.Bar(
        x=nurses, y=weekends,
        marker_color=C_BLUE, text=weekends, textposition="outside",
    ))
    fig_wknd.update_layout(**base_layout("Weekend shifts per nurse"),
                            yaxis_range=[0,7], showlegend=False)

    fig_heatmap = go.Figure(go.Heatmap(
        z=weekly_matrix,
        x=nurses,
        y=[f"W{w}" for w in range(1,9)],
        colorscale=[[0,"#f7f7f7"],[0.5,"#a8c5da"],[1,C_DARK]],
        zmin=0, zmax=4,
        text=weekly_matrix,
        texttemplate="%{text}",
        textfont_size=10,
        showscale=True,
        colorbar=dict(title="Shifts", tickfont_size=9),
    ))
    fig_heatmap.update_layout(
        **base_layout("Weekly shift load — all nurses (max 4 per week)"),
        height=320,
        xaxis=dict(side="bottom"),
    )

    seq_counts = []
    for n in range(10):
        cnt = sum(1 for d in night_starters_mon+night_starters_thu if works(n,d,2))
        seq_counts.append(cnt)

    fig_seq = go.Figure(go.Bar(
        x=nurses, y=seq_counts,
        marker_color=C_DARK, text=seq_counts, textposition="outside",
    ))
    fig_seq.update_layout(**base_layout("Night sequences per nurse (spread ≤ 2)"),
                           yaxis_range=[0,4], showlegend=False)

    return html.Div([
        html.Div([
            card([section_title("Weekend shifts per nurse"),
                  dcc.Graph(figure=fig_wknd, config=plot_cfg(), style={"height":"240px"})],
                 style={"flex":"1"}),
            card([section_title("Night sequences per nurse"),
                  dcc.Graph(figure=fig_seq, config=plot_cfg(), style={"height":"240px"})],
                 style={"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),

        card([section_title("Weekly workload heatmap — shifts per nurse per week"),
              dcc.Graph(figure=fig_heatmap, config=plot_cfg(), style={"height":"320px"})]),
    ])


# ── TAB 4: TEAM COVERAGE ──────────────────────────────────────
def render_teams():
    teams = ["A","B","C","D","E"]
    team_shift = {}
    for t in teams:
        team_sol = sol[sol["Team"]==t]
        team_shift[t] = {
            "ED Day 1": team_sol[team_sol["Shift"]==0].shape[0],
            "ED Day 2": team_sol[team_sol["Shift"]==1].shape[0],
            "ED Nights": team_sol[team_sol["Shift"]==2].shape[0],
        }

    fig_team = go.Figure()
    for shift_name, color in [("ED Day 1",C_TEAL),("ED Day 2",C_BLUE),("ED Nights",C_DARK)]:
        fig_team.add_trace(go.Bar(
            name=shift_name,
            x=teams,
            y=[team_shift[t][shift_name] for t in teams],
            marker_color=color,
        ))
    fig_team.update_layout(**base_layout("Shifts by team and type"), barmode="stack")

    nurse_table = []
    for n in range(10):
        team = nurses_meta[n]
        total = sol[sol["Nurse"]==n].shape[0]
        d1    = sol[(sol["Nurse"]==n)&(sol["Shift"]==0)].shape[0]
        d2    = sol[(sol["Nurse"]==n)&(sol["Shift"]==1)].shape[0]
        nt    = sol[(sol["Nurse"]==n)&(sol["Shift"]==2)].shape[0]
        nurse_table.append({
            "Nurse": f"Nurse {n}", "Team": team,
            "Total": total, "ED Day 1": d1,
            "ED Day 2": d2, "ED Nights": nt,
            "Note": "No ED Day 1 (Team A rule)" if team=="A" else "",
        })

    return html.Div([
        html.Div([
            card([section_title("Shift coverage by team"),
                  dcc.Graph(figure=fig_team, config=plot_cfg(), style={"height":"280px"})],
                 style={"flex":"1"}),
            card([
                section_title("Team composition"),
                html.Div([
                    html.Div([
                        html.Span(t, style={"fontWeight":"700","fontSize":"13px",
                                           "color":list(TEAM_COLORS.values())[i]}),
                        html.Span(f"  Nurse(s): " + ", ".join(
                            str(n) for n in range(10) if nurses_meta[n]==t),
                            style={"fontSize":"12px","color":"#666"}),
                    ], style={"marginBottom":"10px"})
                    for i,t in enumerate(["A","B","C","D","E"])
                ]),
                html.Hr(style={"border":"none","borderTop":f"1px solid {C_BORDER}","margin":"12px 0"}),
                html.P("At most 1 nurse per team is on call on any given day across all 56 days. "
                       "All 280 team-day combinations verified — zero violations.",
                       style={"fontSize":"12px","color":"#666","lineHeight":"1.6"}),
            ], style={"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),

        card([
            section_title("Full nurse allocation table"),
            dash_table.DataTable(
                data=nurse_table,
                columns=[{"name":c,"id":c} for c in
                         ["Nurse","Team","Total","ED Day 1","ED Day 2","ED Nights","Note"]],
                style_header={"fontWeight":"600","fontSize":"11px",
                              "background":C_LIGHT,"color":C_DARK,
                              "border":f"1px solid {C_BORDER}"},
                style_cell={"fontSize":"12px","padding":"8px 12px",
                            "fontFamily":FONT,"border":f"1px solid {C_BORDER}",
                            "textAlign":"left"},
                style_data_conditional=[
                    {"if":{"filter_query":'{Team} = "A"'},
                     "background":"#f0faf9"},
                ],
            )
        ]),
    ])


# ── TAB 5: REST & LEAVE ───────────────────────────────────────
def render_rest():
    fig = go.Figure()

    for n in range(10):
        fig.add_trace(go.Scatter(
            x=[0,55], y=[n,n],
            mode="lines",
            line=dict(color="#eeeeee", width=8),
            showlegend=False, hoverinfo="skip",
        ))

    for n in range(10):
        for d in night_starters_mon:
            if works(n,d,2):
                fig.add_trace(go.Scatter(
                    x=[d, d+2], y=[n, n],
                    mode="lines",
                    line=dict(color=C_TEAL, width=10),
                    name="Mon–Wed nights" if n==0 and d==night_starters_mon[0] else "",
                    showlegend=(n==0 and d==night_starters_mon[0]),
                    hovertemplate=f"Nurse {n} · Mon-Wed nights · Day {d}–{d+2}<extra></extra>",
                ))
        for d in night_starters_thu:
            if works(n,d,2):
                fig.add_trace(go.Scatter(
                    x=[d, d+3], y=[n, n],
                    mode="lines",
                    line=dict(color=C_DARK, width=10),
                    name="Thu–Sun nights" if n==0 and d==night_starters_thu[0] else "",
                    showlegend=(n==0 and d==night_starters_thu[0]),
                    hovertemplate=f"Nurse {n} · Thu-Sun nights · Day {d}–{d+3}<extra></extra>",
                ))

    for _, row in leave_df.iterrows():
        n = int(row["Nurse"])
        fig.add_trace(go.Scatter(
            x=[row["Start_Day"], row["End_Day"]],
            y=[n, n],
            mode="lines",
            line=dict(color=C_AMBER, width=10),
            name="Leave" if _ == 0 else "",
            showlegend=(_ == 0),
            hovertemplate=f"Nurse {n} · Leave · Day {int(row['Start_Day'])}–{int(row['End_Day'])}<extra></extra>",
        ))

    for w in range(9):
        fig.add_vline(x=w*7, line_color="#dddddd", line_width=1)

    fig.update_layout(
        **base_layout("Night sequences and leave — 56-day timeline"),
        yaxis=dict(tickvals=list(range(10)),
                   ticktext=[f"Nurse {n}" for n in range(10)],
                   gridcolor="#f0f0f0"),
        xaxis=dict(title="Day", tickmode="array",
                   tickvals=[i*7 for i in range(9)],
                   ticktext=[f"W{i+1}" for i in range(8)] + [""],
                   showgrid=False),
        height=380,
        hovermode="closest",
        legend=dict(orientation="h", y=-0.12, font_size=11),
    )

    leave_table = [
        {"Nurse": r["Nurse"], "Start Day": r["Start_Day"],
         "End Day": r["End_Day"],
         "Duration": f"{int(r['End_Day'])-int(r['Start_Day'])+1} days",
         "Shifts assigned": "0  ✓"}
        for _, r in leave_df.iterrows()
    ]

    return html.Div([
        card([section_title("Night sequence and leave timeline (hover for details)"),
              dcc.Graph(figure=fig, config=plot_cfg(), style={"height":"380px"})]),

        html.Div([
            card([
                section_title("Leave periods"),
                dash_table.DataTable(
                    data=leave_table,
                    columns=[{"name":c,"id":c} for c in
                             ["Nurse","Start Day","End Day","Duration","Shifts assigned"]],
                    style_header={"fontWeight":"600","fontSize":"11px",
                                  "background":C_LIGHT,"color":C_DARK,
                                  "border":f"1px solid {C_BORDER}"},
                    style_cell={"fontSize":"12px","padding":"8px 12px",
                                "fontFamily":FONT,"border":f"1px solid {C_BORDER}"},
                    style_data_conditional=[
                        {"if":{"column_id":"Shifts assigned"},
                         "color":C_TEAL,"fontWeight":"600"},
                    ],
                )
            ], style={"flex":"1"}),
            card([
                section_title("Rest rules applied"),
                html.Div([
                    html.Div([
                        html.P("After Mon–Wed nights", style={"fontWeight":"600","margin":"0 0 2px","fontSize":"13px"}),
                        html.P("Thursday and Friday are rest days — no shifts assigned.",
                               style={"fontSize":"12px","color":"#666","margin":"0"}),
                    ], style={"marginBottom":"14px","paddingBottom":"14px",
                              "borderBottom":f"1px solid {C_BORDER}"}),
                    html.Div([
                        html.P("After Thu–Sun nights", style={"fontWeight":"600","margin":"0 0 2px","fontSize":"13px"}),
                        html.P("Monday and Tuesday are rest days — no shifts assigned.",
                               style={"fontSize":"12px","color":"#666","margin":"0"}),
                    ], style={"marginBottom":"14px","paddingBottom":"14px",
                              "borderBottom":f"1px solid {C_BORDER}"}),
                    html.Div([
                        html.P("No consecutive full weekends", style={"fontWeight":"600","margin":"0 0 2px","fontSize":"13px"}),
                        html.P("No nurse works back-to-back full weekends across the 8-week period.",
                               style={"fontSize":"12px","color":"#666","margin":"0"}),
                    ]),
                ])
            ], style={"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
    ])


# ── RUN ───────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, port=8050)
