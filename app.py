import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import shiny
import plotly
import plotly.express as px
from shinywidgets import render_widget
from shiny import App, Inputs, Outputs, Session, render, ui
from shiny.ui import div, HTML

import plotly.express as px
from shinywidgets import render_plotly

from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from shiny.types import ImgData

app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_action_button("readme_btn", "Read Me"),
            ui.input_radio_buttons("radio", "", ["Helical⇒2D", "2D⇒Helical"]),
            ui.output_ui("conditional_inputs"),  # Placeholder for conditional inputs
            ui.input_checkbox("share_url", "Show sharable URL", value=False),
            ui.markdown("*Developed by the [Jiang Lab@Purdue University](https://jiang.bio.purdue.edu). Report problems to Wen Jiang (jiang12 at purdue.edu)*"),
            id="sidebar_always", open="always"
        ),
        ui.row(
            ui.column(10,  # Main content area
                ui.div(
                    ui.h2("HelicalLattice: 2D Lattice ⇔ Helical Lattice"),
                    "This is the main content area.",
                    style="text-align: center; margin-top: 20px;"
                ),
            ),
        )
    )
)

def server(input, output, session):
    @output
    @render.text
    def state_always():
        return f"testing here input.sidebar_always(): {input.sidebar_always()}"
    
    @reactive.Effect
    @reactive.event(input.readme_btn)
    def show_readme_info():
        ui.notification_show("HelicalLattice is a Web app that helps the user to understand how a helical lattice and its underlying 2D lattice can interconvert. The user can specify any 2D lattice and choose a line segment connecting any pair of lattice points that defines the block of 2D lattice to be rolled up into a helical lattice")

    @output
    @render.ui
    def conditional_inputs():
        if input.radio() == "Helical⇒2D":
            return ui.TagList(
                ui.input_numeric('twist', 'Twist (°)', value=-81.1, min=-180., max=180., step=1.0),
                ui.input_numeric('rise', 'Rise (Å)', value=19.4, min=0.001, step=1.0),
                ui.input_numeric('csym', 'Axial symmetry', value=1, min=1, step=1),
                ui.input_numeric('diameter', 'Helical diameter (Å)', value=290.0, min=0.1, step=1.0),
                ui.input_checkbox("primitive_unitcell", "Use primitive unit cell", value=False),
                ui.input_checkbox("horizontal", "Set unit cell vector a along x-axis", value=True),
                ui.input_numeric("lattice_size_factor", "2D lattice size factor", value=1.25, min=1.0, step=0.1),
                ui.input_numeric("marker_size", "Marker size (Å)", value=5.0, min=0.1, step=1.0),
                ui.input_numeric("figure_height", "Plot height (pixels)", value=800, min=1, step=10),
            
            )
        elif input.radio() == "2D⇒Helical":
            return ui.TagList(
                ui.input_numeric("ax", "Unit cell vector a.x (Å)", value=34.65, step=1.0),
                ui.input_numeric("ay", "Unit cell vector a.y (Å)", value=0.0, step=1.0),
                ui.input_numeric("bx", "Unit cell vector b.x (Å)", value=10.63, step=1.0),
                ui.input_numeric("by", "Unit cell vector b.y (Å)", value=-23.01, step=1.0),
                ui.input_numeric("na", "# units along unit cell vector a", value=16, step=1),
                ui.input_numeric("nb", "# units along unit cell vector b", value=1, step=1),
            )

app = App(app_ui, server)





def import_with_auto_install(packages, scope=locals()):
    if isinstance(packages, str): packages=[packages]
    for package in packages:
        if package.find(":")!=-1:
            package_import_name, package_pip_name = package.split(":")
        else:
            package_import_name, package_pip_name = package, package
        try:
            scope[package_import_name] = __import__(package_import_name)
        except ImportError:
            import subprocess
            subprocess.call(f'pip install {package_pip_name}', shell=True)
            scope[package_import_name] =  __import__(package_import_name)
required_packages = "numpy scipy pandas plotly".split()
import_with_auto_install(required_packages)

def plot_2d_lattice(a, b, endpoint, length, lattice_size_factor, marker_size, figure_height):
    a = np.array(a)
    b = np.array(b)
    na, nb = endpoint
    v0 = na * a + nb * b
    circumference = np.linalg.norm(v0)
    v1 = np.array([-v0[1], v0[0]])
    v1 = length * v1/np.linalg.norm(v1)
    corner_points = [np.array([0, 0]), v0, v0+v1, v1]
    x, y = zip(*(corner_points+[na*a]))
    x0, x1 = min(x), max(x)
    y0, y1 = min(y), max(y)
    pad = min(x1-x0, y1-y0)*(lattice_size_factor-1)
    xmin = x0 - pad
    xmax = x1 + pad
    ymin = y0 - pad
    ymax = y1 + pad

    nas = []
    nbs = []
    m = np.vstack((a, b)).T
    for v in [(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)]:
        tmp_a, tmp_b = np.linalg.solve(m, v)
        nas.append(tmp_a)
        nbs.append(tmp_b)
    na_min = np.floor(sorted(nas)[0])-2
    na_max = np.floor(sorted(nas)[-1])+2
    nb_min = np.floor(sorted(nbs)[0])-2
    nb_max = np.floor(sorted(nbs)[-1])+2

    ia = np.arange(na_min, na_max)
    ib = np.arange(nb_min, nb_max)
    x = []
    y = []
    for j in ib:
        for i in ia:
            v = i*a+j*b
            if xmin <= v[0] <= xmax and ymin <= v[1] <= ymax:
                x.append(v[0])
                y.append(v[1])

    df = pd.DataFrame({'x': x, 'y': y})
    fig = px.scatter(df, x='x', y='y')

    x, y = zip(*corner_points)
    x = [*x, 0]
    y = [*y, 0]
    rectangle = go.Scatter(x=x, y=y, fill="toself", mode='lines', line=dict(color='green', width=marker_size/5, dash='dash'))
    fig.add_trace(rectangle)
  
    fig.data = (fig.data[1], fig.data[0])

    arrow_start = [0, 0]
    arrow_end = na*a
    fig.add_annotation(
        x=arrow_end[0],
        y=arrow_end[1],
        ax=arrow_start[0],
        ay=arrow_start[1],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=3,
        arrowcolor="grey",
        opacity=1.0
    )

    arrow_start = na*a
    arrow_end = v0
    fig.add_annotation(
        x=arrow_end[0],
        y=arrow_end[1],
        ax=arrow_start[0],
        ay=arrow_start[1],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=3,
        arrowcolor="grey",
        opacity=1.0
    )

    arrow_start = [0, 0]
    arrow_end = v0
    fig.add_annotation(
        x=arrow_end[0],
        y=arrow_end[1],
        ax=arrow_start[0],
        ay=arrow_start[1],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=3,
        arrowcolor="red",
        opacity=1.0
    )

    fig.update_traces(marker_size=marker_size, showlegend=False)

    fig.update_layout(
        xaxis=dict(title='X (Å)', range=[xmin, xmax], constrain='domain'),
        yaxis=dict(title='Y (Å)', range=[ymin, ymax], constrain='domain')
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    title = f"a=({a[0]:.2f}, {a[1]:.2f})Å\tb=({b[0]:.2f}, {b[1]:.2f})Å<br>equator=(0,0)→{na}*a{'+' if nb>=0 else ''}{nb}*b\tcircumference={circumference:.2f}"
    fig.update_layout(title_text=title, title_x=0.5, title_xanchor="center")
    fig.update_layout(height=figure_height)
    fig.update_layout(paper_bgcolor='rgba(0, 0, 0, 0)', plot_bgcolor='rgba(0, 0, 0, 0)')

    return fig

def plot_helical_lattice_unrolled(diameter, length, twist, rise, csym, marker_size, figure_height):
    circumference = np.pi * diameter
    if rise > 0:
        n = min(int(length/2/rise)+2, 1000)
        i = np.arange(-n, n+1)
        xs = []
        ys = []
        syms = []
        for si in range(csym):
            x = np.fmod(twist * i + si/csym * 360, 360)
            x[x > 360] -= 360
            x[x < 0] += 360
            y = rise * i
            xs.append(x)
            ys.append(y)
            syms.append(np.array([si] * len(x)))
        x = np.concatenate(xs)
        y = np.concatenate(ys)
        sym = np.concatenate(syms)

        df = pd.DataFrame({'x': x, 'y': y, 'csym': sym})
        df["csym"] = df["csym"].astype(str)
        
        fig = px.scatter(df, x='x', y='y', color='csym' if csym > 1 else None)

        if twist >= 0:
            arrow_start = [0, 0]
            arrow_end = [twist, rise]
        else:
            arrow_start = [360, 0]
            arrow_end = [360 + twist, rise]
        fig.add_annotation(
            x=arrow_end[0],
            y=arrow_end[1],
            ax=arrow_start[0],
            ay=arrow_start[1],
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red",
            opacity=1.0
        )

        i = np.arange(-n, n+1, 0.01)
        for si in range(csym):
            x = np.fmod(twist * i + si/csym * 360, 360)
            x[x > 360] -= 360
            x[x < 0] += 360
            y = rise * i
            color = fig.data[si].marker.color
            line = go.Scatter(x=x, y=y, mode='lines', line=dict(color=color, width=marker_size/10, dash='dot'), opacity=1, showlegend=False)
            fig.add_trace(line)
        equator = go.Scatter(x=[0, 360], y=[0, 0], xaxis='x', line=dict(color='grey', width=marker_size/3, dash='dash'))
        fig.add_trace(equator)
        fig.update_traces(marker_size=marker_size, showlegend=False)

        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=360 / circumference
        )
        fig.update_layout(
            xaxis=dict(title='twist (°)', range=[0, 360], tickvals=np.linspace(0, 360, 13), constrain='domain'),
            yaxis=dict(title='rise (Å)', range=[-length/2, length/2], constrain='domain'),
        )
        
        title = f"pitch={rise * abs(360 / twist):.2f}Å\ttwist={twist:.2f}° rise={rise:.2f}Å"
        fig.update_layout(title_text=title, title_x=0.5, title_xanchor="center")
        fig.update_layout(height=figure_height)
        fig.update_layout(paper_bgcolor='rgba(0, 0, 0, 0)', plot_bgcolor='rgba(0, 0, 0, 0)')
    else:
        fig = go.Figure()
    return fig

def plot_helical_lattice(diameter, length, twist, rise, csym, marker_size=10, figure_height=500):
    if rise > 0:
        n = min(int(length/2/rise)+2, 1000)
        i = np.arange(-n, n+1)
        xs = []
        ys = []
        zs = []
        syms = []
        for si in range(csym):
            x = diameter/2 * np.cos(np.deg2rad(twist)*i + si/csym*2*np.pi)
            y = diameter/2 * np.sin(np.deg2rad(twist)*i + si/csym*2*np.pi)
            z = i * rise
            xs.append(x)
            ys.append(y)
            zs.append(z)
            syms.append(np.array([si]*len(z)))
        x = np.concatenate(xs)
        y = np.concatenate(ys)
        z = np.concatenate(zs)
        sym = np.concatenate(syms)

        df = pd.DataFrame({'x': x, 'y': y, 'z': z, 'csym': sym})
        df["csym"] = df["csym"].astype(str)
        
        fig = px.scatter_3d(df, x='x', y='y', z='z', labels={'x': 'X (Å)', 'y': 'Y (Å)', 'z': 'Z (Å)'}, color='csym' if csym > 1 else None)
        fig.update_traces(marker_size=marker_size)

        i = np.arange(-n, n+1, 5./(abs(twist)))
        for si in range(csym):
            x = diameter/2 * np.cos(np.deg2rad(twist)*i + si/csym*2*np.pi)
            y = diameter/2 * np.sin(np.deg2rad(twist)*i + si/csym*2*np.pi)
            z = i * rise
            color = fig.data[si].marker.color
            spiral = go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color=color, width=marker_size/2), opacity=1, showlegend=False)
            fig.add_trace(spiral)

        def cylinder(r, h, z0=0, n_points=100, nv=50):
            theta = np.linspace(0, 2*np.pi, n_points)
            v = np.linspace(z0, z0+h, nv)
            theta, v = np.meshgrid(theta, v)
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            z = v
            return x, y, z
        
        def equator_circle(r, z, n_points=36):
            theta = np.linspace(0, 2*np.pi, n_points)
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            z0 = z * np.ones(theta.shape)
            return x, y, z0

        x, y, z = cylinder(r=diameter/2 - marker_size/2, h=length, z0=-length/2)
        colorscale = [[0, 'white'], [1, 'white']]
        cyl = go.Surface(x=x, y=y, z=z, colorscale=colorscale, showscale=False, opacity=0.8)
        fig.add_trace(cyl)
        x, y, z = equator_circle(r=diameter/2, z=0)
        equator = go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='grey', width=marker_size/2, dash='dash'), opacity=1, showlegend=False)
        fig.add_trace(equator)

        title = f"pitch={rise*abs(360/twist):.2f}Å\ttwist={twist:.2f}° rise={rise:.2f}Å sym=c{csym}<br>diameter={diameter:.2f}Å circumference={np.pi*diameter:.2f}Å"
        fig.update_layout(title_text=title, title_x=0.5, title_xanchor="center")

        camera = dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=1, y=0, z=0)
        )
        fig.update_layout(scene_camera=camera)

        fig.update_scenes(
            xaxis=dict(range=[-diameter/2 - marker_size, diameter/2 + marker_size]),
            yaxis=dict(range=[-diameter/2 - marker_size, diameter/2 + marker_size]),
            zaxis=dict(range=[-length/2 - marker_size, length/2 + marker_size])
        )

        fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, camera_projection_type='orthographic', aspectmode='data')
        fig.update_layout(height=figure_height)
        fig.update_layout(paper_bgcolor='rgba(0, 0, 0, 0)')

        return fig
    else:
        fig = go.Figure()
        return fig

def convert_2d_lattice_to_helical_lattice(a=(1, 0), b=(0, 1), endpoint=(10, 0)):
  def set_to_periodic_range(v, min=-180, max=180):
    from math import fmod
    tmp = fmod(v-min, max-min)
    if tmp>=0: tmp+=min
    else: tmp+=max
    return tmp
  def length(v):
    return np.linalg.norm(v)
  def transform_vector(v, vref=(1, 0)):
    ang = np.arctan2(vref[1], vref[0])
    cos = np.cos(ang)
    sin = np.sin(ang)
    m = [[cos, sin], [-sin, cos]]
    v2 = np.dot(m, v.T)
    return v2
  def on_equator(v, epsilon=0.5):
      # test if b vector is on the equator
      if abs(v[1]) > epsilon: return 0
      return 1
  
  a, b, endpoint = map(np.array, (a, b, endpoint))
  na, nb = endpoint
  v_equator = na*a + nb*b
  circumference = length(v_equator)
  va = transform_vector(a, v_equator)
  vb = transform_vector(b, v_equator)
  minLength = max(1.0, min(np.linalg.norm(va), np.linalg.norm(vb)) * 0.9)
  vs_on_equator = []
  vs_off_equator = []
  epsilon = 0.5
  maxI = 10
  for i in range(-maxI, maxI + 1):
      for j in range(-maxI, maxI + 1):
          if i or j:
              v = i * va + j * vb
              v[0] = set_to_periodic_range(v[0], min=0, max=circumference)
              if np.linalg.norm(v) > minLength:
                  if v[1]<0: v *= -1
                  if on_equator(v, epsilon=epsilon):
                      vs_on_equator.append(v)
                  else:
                      vs_off_equator.append(v)
  twist, rise, csym = 0, 0, 1
  if vs_on_equator:
      vs_on_equator.sort(key=lambda v: abs(v[0]))
      best_spacing = abs(vs_on_equator[0][0])
      csym_f = circumference / best_spacing
      expected_spacing = circumference/round(csym_f)
      if abs(best_spacing - expected_spacing)/expected_spacing < 0.05:
          csym = int(round(csym_f))
  if vs_off_equator:
      vs_off_equator.sort(key=lambda v: (abs(round(v[1]/epsilon)), abs(v[0])))
      twist, rise = vs_off_equator[0]
      twist *= 360/circumference
      twist = set_to_periodic_range(twist, min=-360/(2*csym), max=360/(2*csym))
  diameter = circumference/np.pi
  return twist, rise, csym, diameter

def convert_helical_lattice_to_2d_lattice(twist=30, rise=20, csym=1, diameter=100, primitive_unitcell=False, horizontal=True):
    def angle90(v1, v2):  # angle between two vectors, ignoring vector polarity [0, 90]
        p = np.dot(v1, v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
        p = np.clip(abs(p), 0, 1)
        ret = np.rad2deg(np.arccos(p))  # 0<=angle<90
        return ret

    def transform_vector(v, vref=(1, 0)):
        ang = np.arctan2(vref[1], vref[0])
        cos = np.cos(ang)
        sin = np.sin(ang)
        m = [[cos, sin], [-sin, cos]]
        v2 = np.dot(m, v.T)
        return v2

    imax = int(5 * 360 / abs(twist))
    n = np.tile(np.arange(-imax, imax), reps=(2, 1)).T
    v = np.array([twist, rise], dtype=float) * n
    if csym > 1:
        vs = []
        for ci in range(csym):
            tmp = v * 1.0
            tmp[:, 0] += ci / csym * 360
            vs.append(tmp)
        v = np.vstack(vs)
    v[:, 0] = np.fmod(v[:, 0], 360)
    v[v[:, 0] < 0, 0] += 360
    v[:, 0] *= np.pi * diameter / 360  # convert x-axis values from angles to distances
    dist = np.linalg.norm(v, axis=1)
    dist_indices = np.argsort(dist)

    v = v[dist_indices]  # now sorted from short to long distance
    err = 1.0  # max angle between 2 vectors to consider non-parallel
    vb = v[1]
    for i in range(1, len(v)):
        if angle90(vb, v[i]) > err:
            va = v[i]
            break

    ve = np.array([np.pi * diameter, 0])
    m = np.vstack((va, vb)).T
    na, nb = np.linalg.solve(m, ve)
    endpoint = (round(na), round(nb))

    if not primitive_unitcell:
        vabs = []
        for ia in range(-1, 2):
            for ib in range(-1, 2):
                vabs.append(ia * va + ib * vb)
        vabs_good = []
        area = np.linalg.norm(np.cross(va, vb))
        for vai, vatmp in enumerate(vabs):
            for vbi in range(vai + 1, len(vabs)):
                vbtmp = vabs[vbi]
                areatmp = np.linalg.norm(np.cross(vatmp, vbtmp))
                if abs(areatmp - area) > err:
                    continue
                vabs_good.append((vatmp, vbtmp))
        dist = []
        for vi, (vatmp, vbtmp) in enumerate(vabs_good):
            m = np.vstack((vatmp, vbtmp)).T
            na, nb = np.linalg.solve(m, ve)
            if abs(na - round(na)) > 1e-3:
                continue
            if abs(nb - round(nb)) > 1e-3:
                continue
            dist.append((abs(na) + abs(nb), -round(na), -round(nb), round(na), round(nb), vatmp, vbtmp))
        if len(dist):
            dist.sort(key=lambda x: x[:3])
            na, nb, va, vb = dist[0][3:]
            if np.linalg.norm(vb) > np.linalg.norm(va):
                va, vb = vb, va
                na, nb = nb, na
            endpoint = (na, nb)

    if va[0] < 0:
        va *= -1
        vb *= -1
        na *= -1
        nb *= -1

    if horizontal:
        vb = transform_vector(vb, vref=va)
        va = np.array([np.linalg.norm(va), 0.0])

    return va, vb, endpoint

int_types = {'csym':1, 'figure_height':800, 'horizontal':1, 'na':16, 'nb':1, 'primitive_unitcell':0, 'share_url':0}
float_types = {'ax':34.65, 'ay':0.0, 'bx':10.63, 'by':-23.01, 'diameter':290.0, 'lattice_size_factor':1.25, 'length':1000.0, 'marker_size':5.0, 'rise':19.4, 'twist':-81.1}
default_values = int_types | float_types | {'direction':'Helical⇒2D', }
def set_initial_session_state():
    global session_state
    session_state = shiny.reactiveValues()
    for attr in sorted(default_values.keys()):
        if attr in int_types:
            setattr(session_state, attr, int(default_values[attr]))
        elif attr in float_types:
            setattr(session_state, attr, float(default_values[attr]))
        else:
            setattr(session_state, attr, default_values[attr])

def set_query_params_from_session_state():
    global session_state
    # Create a dictionary to hold query parameters
    params = {}
    
    # Filter and prepare the parameters based on session state
    for attr in sorted(default_values.keys()):
        v = getattr(session_state, attr)
        if session_state.direction == '2D⇒Helical':
            if attr in ['twist', 'rise', 'csym']:
                continue
        else:
            if attr in ['ax', 'ay', 'bx', 'by', 'na', 'nb']:
                continue
        
        if v == default_values[attr]:
            continue
        
        if attr in int_types or isinstance(v, bool):
            params[attr] = int(v)
        elif attr in float_types:
            params[attr] = f'{float(v):g}'
        else:
            params[attr] = v

def set_session_state_from_query_params():
    # Retrieve query parameters from URL
    query_params = shiny.get_query_parameters()
    
    # Update session state based on query parameters
    for attr in sorted(query_params.keys()):
        v = query_params[attr]
        if attr in int_types:
            setattr(session_state, attr, int(v))
        elif attr in float_types:
            setattr(session_state, attr, float(v))
        else:
            setattr(session_state, attr, v)

import pathlib
import stat
from shiny import App, Inputs, Outputs, Session, render, ui

def setup_anonymous_usage_tracking():
    try:
        index_file = pathlib.Path(__file__).parent / "static/index.html"
        index_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        txt = index_file.read_text()
        if "gtag/js?" not in txt:
            txt = txt.replace("<head>", '''<head><script async src="https://www.googletagmanager.com/gtag/js?id=G-CTBKF6J4CG"></script><script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-CTBKF6J4CG');</script>''')
            index_file.write_text(txt)
    except Exception as e:
        print(f"An error occurred: {e}")