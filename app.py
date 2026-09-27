"""
💧 Straight Pipe Friction Loss Calculator
An educational Streamlit app demonstrating the Darcy–Weisbach equation:
    ΔP = f · (L/D) · (ρ·V²/2)
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------
# Page setup & constants
# ----------------------------------------------------------------------
st.set_page_config(page_title="Pipe Friction Loss Calculator",
                   page_icon="💧", layout="wide")

G = 9.81            # gravity [m/s²]
PA_PER_PSI = 6894.76

# ----------------------------------------------------------------------
# Engineering functions
# ----------------------------------------------------------------------
def pressure_drop_pa(f, L, D, rho, v):
    """Darcy–Weisbach pressure drop [Pa]."""
    return f * (L / D) * rho * v**2 / 2.0

def head_loss_m(f, L, D, v):
    """Head loss [m of fluid]."""
    return f * (L / D) * v**2 / (2.0 * G)

def reynolds(rho, v, D, mu):
    return rho * v * D / mu

def friction_factor(re, eps, D):
    """Darcy friction factor: laminar f=64/Re, turbulent Swamee–Jain."""
    if re <= 0:
        return 0.02
    f_lam = 64.0 / re
    if re < 2000:
        return f_lam
    f_turb = 0.25 / (np.log10(eps / (3.7 * D) + 5.74 / re**0.9))**2
    if re > 4000:
        return f_turb
    return 0.5 * (f_lam + f_turb)   # transition zone (rough blend)

# ----------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------
FLUIDS = {
    "Water (20 °C)":     {"rho": 998.0,  "mu": 1.002e-3},
    "Seawater":          {"rho": 1025.0, "mu": 1.08e-3},
    "Diesel":            {"rho": 850.0,  "mu": 2.4e-3},   # matches the infographic example
    "Gasoline":          {"rho": 740.0,  "mu": 0.6e-3},
    "Crude oil (light)": {"rho": 870.0,  "mu": 8.0e-3},
    "Custom…":           None,
}

MATERIALS = {  # typical roughness ε [mm]
    "PVC / HDPE (smooth)": 0.0015,
    "Commercial steel":    0.045,
    "Galvanised iron":     0.15,
    "Cast iron":           0.26,
    "Concrete":            1.0,
}

# ----------------------------------------------------------------------
# Sidebar — inputs
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Inputs")

    fluid_name = st.selectbox("Fluid", list(FLUIDS), index=2)
    if fluid_name == "Custom…":
        rho = st.slider("Density ρ (kg/m³)", 500.0, 1500.0, 850.0, 5.0)
        mu = st.slider("Viscosity μ (mPa·s)", 0.1, 100.0, 1.0, 0.1) / 1000.0
    else:
        rho = FLUIDS[fluid_name]["rho"]
        mu = FLUIDS[fluid_name]["mu"]
        st.caption(f"ρ = {rho:.0f} kg/m³  |  μ = {mu*1000:.2f} mPa·s")

    st.divider()
    L = st.slider("Pipe length L (m)", 1.0, 500.0, 50.0, 1.0)
    D_mm = st.slider("Pipe inner diameter D (mm)", 10.0, 600.0, 100.0, 5.0)
    D = D_mm / 1000.0

    st.divider()
    flow_mode = st.radio("Flow input", ("Velocity", "Flow rate"), horizontal=True)
    if flow_mode == "Velocity":
        v = st.slider("Velocity V (m/s)", 0.1, 6.0, 1.5, 0.05)
    else:
        Q_lps = st.slider("Flow rate Q (L/s)", 0.5, 200.0, 11.8, 0.1)
        v = Q_lps / 1000.0 / (np.pi * D**2 / 4.0)
        st.caption(f"→ V = {v:.2f} m/s in this pipe")

    st.divider()
    f_mode = st.radio("Friction factor", ("Manual f", "Estimate from roughness"),
                      horizontal=True)
    if f_mode == "Manual f":
        f = st.slider("Friction factor f (Darcy)", 0.005, 0.100, 0.030, 0.001,
                      format="%.3f")
        st.caption("Typical turbulent range: 0.015 – 0.045")
        Re = reynolds(rho, v, D, mu)
    else:
        mat = st.selectbox("Pipe material", list(MATERIALS))
        eps_m = MATERIALS[mat] / 1000.0
        Re = reynolds(rho, v, D, mu)
        f = friction_factor(Re, eps_m, D)
        regime_s = "Laminar" if Re < 2000 else ("Turbulent" if Re > 4000 else "Transition")
        st.caption(f"ε = {MATERIALS[mat]:.3f} mm | Re = {Re:,.0f} ({regime_s}) → f = {f:.4f}")

# ----------------------------------------------------------------------
# Calculations
# ----------------------------------------------------------------------
A = np.pi * D**2 / 4.0
Q = v * A
dp_pa = pressure_drop_pa(f, L, D, rho, v)
dp_kpa = dp_pa / 1000.0
dp_bar = dp_pa / 1e5
dp_psi = dp_pa / PA_PER_PSI
hf = head_loss_m(f, L, D, v)
regime = "Laminar" if Re < 2000 else ("Transitional" if Re <= 4000 else "Turbulent")

# ----------------------------------------------------------------------
# Header, metrics, pipe schematic
# ----------------------------------------------------------------------
st.title("💧 Straight Pipe Friction Loss Calculator")
st.caption("Darcy–Weisbach equation · an interactive educational demo — "
           "change length, diameter, velocity or friction and watch the pressure drop respond.Prepared by KAUNG HTAT NYUNT")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Pressure drop ΔP", f"{dp_kpa:,.2f} kPa", f"{dp_bar:.3f} bar")
c2.metric("In bar", f"{dp_bar:.3f} bar")
c3.metric("In psi", f"{dp_psi:.2f} psi")
c4.metric("Head loss h_f", f"{hf:.2f} m")
c5.metric("Reynolds number", f"{Re:,.0f}", regime)

# --- Gauge schematic (like the infographic) ---
st.markdown(
    """
    <style>
    .pf-wrap {display:flex; align-items:center; gap:16px; margin:14px 0 4px 0;}
    .pf-gauge {width:92px; height:92px; border-radius:50%; border:4px solid #0e7490;
               background:#f0f9ff; display:flex; flex-direction:column;
               align-items:center; justify-content:center;}
    .pf-gauge-label {font-size:0.85rem; color:#0e7490; font-weight:700;}
    .pf-gauge-value {font-size:1.0rem; font-weight:800; text-align:center; line-height:1.1;}
    .pf-unit {font-size:0.7rem; font-weight:600; color:#475569;}
    .pf-pipe {flex:1; height:64px; border-radius:14px; color:#fff; font-weight:700;
              background:linear-gradient(180deg,#38bdf8 0%,#0284c7 55%,#075985 100%);
              display:flex; align-items:center; justify-content:center; gap:12px;
              box-shadow:inset 0 -10px 14px rgba(0,0,0,0.25);}
    .pf-arrow {font-size:1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

p1 = st.slider("Upstream pressure P1 (kPa) — for the gauge illustration below",
               50.0, 1000.0, 500.0, 5.0)
p2 = max(p1 - dp_kpa, 0.0)

st.markdown(
    f"""
    <div class="pf-wrap">
      <div class="pf-gauge"><div class="pf-gauge-label">P1</div>
        <div class="pf-gauge-value">{p1:,.0f}<br><span class="pf-unit">kPa</span></div></div>
      <div class="pf-pipe">
        <span class="pf-arrow">➜</span>
        <span>L = {L:.0f} m&nbsp;·&nbsp;D = {D_mm:.0f} mm&nbsp;·&nbsp;V = {v:.2f} m/s&nbsp;·&nbsp;f = {f:.3f}</span>
      </div>
      <div class="pf-gauge" style="border-color:#b91c1c;"><div class="pf-gauge-label" style="color:#b91c1c;">P2</div>
        <div class="pf-gauge-value">{p2:,.1f}<br><span class="pf-unit">kPa</span></div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
if (p1 - dp_kpa) < 0:
    st.warning("ΔP exceeds P1 — this flow could not be delivered without a pump!")

# ----------------------------------------------------------------------
# Step-by-step calculation + what-if insights
# ----------------------------------------------------------------------
left, right = st.columns([1.1, 1.0])

with left:
    with st.container(border=True):
        st.subheader("📐 Step-by-step calculation")
        st.latex(r"\Delta P = f \cdot \frac{L}{D} \cdot \frac{\rho V^{2}}{2}")
        st.latex(
            rf"\Delta P = {f:.3f} \times \frac{{{L:.1f}}}{{{D:.3f}}}"
            rf"\times \frac{{{rho:.0f} \times \left({v:.2f}\right)^{{2}}}}{{2}}"
        )
        st.latex(
            rf"\Delta P = {f:.3f} \times {L/D:.1f} \times {rho*v**2/2:,.1f}\ \text{{Pa}}"
        )
        st.latex(
            rf"\boxed{{\Delta P = {dp_pa:,.0f}\ \text{{Pa}} = {dp_kpa:.2f}\ \text{{kPa}}"
            rf"= {dp_bar:.4f}\ \text{{bar}}}}"
        )
        st.caption(f"Head loss h_f = ΔP / (ρ·g) = {hf:.2f} m of fluid")

with right:
    with st.container(border=True):
        st.subheader("⚡ What-if summary (all else constant)")
        st.markdown(
            f"""
            - **Length × 2** → ΔP = **{pressure_drop_pa(f, 2*L, D, rho, v)/1000:,.2f} kPa**
              (ΔP ∝ L)
            - **Diameter × 2** (same V) → ΔP = **{pressure_drop_pa(f, L, 2*D, rho, v)/1000:,.2f} kPa**
              (ΔP ∝ 1/D)
            - **Velocity × 2** → ΔP = **{pressure_drop_pa(f, L, D, rho, 2*v)/1000:,.2f} kPa**
              (ΔP ∝ V²)
            - **Rougher pipe (f × 2)** → ΔP doubles
            """
        )
        if flow_mode == "Flow rate":
            st.caption("Tip: when holding the *flow rate* constant, ΔP ∝ 1/D⁵ — "
                       "see the Diameter tab!")

# ----------------------------------------------------------------------
# Warnings (educational)
# ----------------------------------------------------------------------
if f_mode == "Manual f" and Re < 2000:
    st.info(f"Re = {Re:,.0f} → laminar flow. Here f = 64/Re ≈ {64/Re:.4f} "
            "and roughness has no effect on f.")
if 2000 <= Re <= 4000:
    st.warning("Reynolds number lies in the transitional zone (2000–4000); "
               "the friction factor is uncertain there.")
if v > 3.0:
    st.warning(f"V = {v:.2f} m/s is above the typical liquid design range "
               "of 1–3 m/s (erosion, noise, water hammer).")

# ----------------------------------------------------------------------
# Interactive charts
# ----------------------------------------------------------------------
def make_fig(x, y, x_now, y_now, xtitle, ytitle, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                             line=dict(color="#0369a1", width=3), name="ΔP"))
    fig.add_trace(go.Scatter(x=[x_now], y=[y_now], mode="markers",
                             marker=dict(color="#dc2626", size=14, symbol="star"),
                             name="Current point"))
    fig.add_vline(x=float(x_now), line_width=1, line_dash="dot", line_color="#9ca3af")
    fig.update_layout(title=title, xaxis_title=xtitle, yaxis_title=ytitle,
                      template="plotly_white", height=400,
                      margin=dict(l=10, r=10, t=55, b=10), hovermode="x unified")
    return fig

tab_len, tab_dia, tab_vel, tab_f, tab_tbl = st.tabs(
    ["📏 Effect of Length", "🛢️ Effect of Diameter",
     "💨 Effect of Velocity", "🎚️ Effect of Friction Factor", "📋 Data Table"])

with tab_len:
    L_rng = np.linspace(1, max(2 * L, 60), 200)
    st.plotly_chart(make_fig(L_rng, pressure_drop_pa(f, L_rng, D, rho, v)/1000,
                             L, dp_kpa, "Pipe length L (m)", "ΔP (kPa)",
                             "Pressure drop vs pipe length"),
                    use_container_width=True)
    st.markdown("📌 ΔP grows **linearly** with length — twice the pipe, twice the loss.")

with tab_dia:
    D_mm_rng = np.linspace(50, 400, 300)
    D_rng = D_mm_rng / 1000.0
    dp_sameV = pressure_drop_pa(f, L, D_rng, rho, v) / 1000.0
    v_sameQ = Q / (np.pi * D_rng**2 / 4.0)
    dp_sameQ = pressure_drop_pa(f, L, D_rng, rho, v_sameQ) / 1000.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=D_mm_rng, y=dp_sameV, mode="lines",
                             line=dict(color="#0369a1", width=3),
                             name="Same velocity"))
    fig.add_trace(go.Scatter(x=D_mm_rng, y=dp_sameQ, mode="lines",
                             line=dict(color="#f59e0b", width=3),
                             name="Same flow rate"))
    fig.add_trace(go.Scatter(x=[D_mm], y=[dp_kpa], mode="markers",
                             marker=dict(color="#dc2626", size=14, symbol="star"),
                             name="Current point"))
    fig.update_layout(title="Pressure drop vs pipe diameter",
                      xaxis_title="Pipe inner diameter D (mm)",
                      yaxis_title="ΔP (kPa)", template="plotly_white", height=400,
                      margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("📌 Same velocity: ΔP ∝ 1/D. Same **flow rate**: ΔP ∝ 1/D⁵ — "
                "a small pipe carrying the same flow is dramatically worse!")

with tab_vel:
    v_rng = np.linspace(0.1, 6, 300)
    st.plotly_chart(make_fig(v_rng, pressure_drop_pa(f, L, D, rho, v_rng)/1000,
                             v, dp_kpa, "Velocity V (m/s)", "ΔP (kPa)",
                             "Pressure drop vs velocity"),
                    use_container_width=True)
    st.markdown("📌 ΔP grows with the **square** of velocity — doubling V quadruples the loss.")

with tab_f:
    f_rng = np.linspace(0.005, 0.1, 300)
    st.plotly_chart(make_fig(f_rng, pressure_drop_pa(f_rng, L, D, rho, v)/1000,
                             f, dp_kpa, "Friction factor f", "ΔP (kPa)",
                             "Pressure drop vs friction factor"),
                    use_container_width=True)
    st.markdown("📌 ΔP is **directly proportional** to f — smoother pipe (PVC) or "
                "larger Re lowers f and the loss.")

with tab_tbl:
    rows = []
    for d_mm in [50, 75, 100, 150, 200, 250, 300]:
        d = d_mm / 1000.0
        v_q = Q / (np.pi * d**2 / 4.0)
        rows.append({
            "D (mm)": d_mm,
            "ΔP @ same velocity (kPa)": round(pressure_drop_pa(f, L, d, rho, v)/1000, 2),
            "V needed for same Q (m/s)": round(v_q, 2),
            "ΔP @ same flow rate (kPa)": round(pressure_drop_pa(f, L, d, rho, v_q)/1000, 2),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("f, L, ρ held at current values. Compare the last two columns to see "
               "why undersizing a pipe is so costly.")

# ----------------------------------------------------------------------
# Theory & assumptions
# ----------------------------------------------------------------------
with st.expander("📚 Theory, assumptions & notes"):
    st.markdown(
        """
**Darcy–Weisbach equation** (straight pipe, friction only):

- Pressure form: **ΔP = f · (L/D) · (ρ·V²/2)**
- Head form: **h_f = f · (L/D) · (V²/2g)**

**Assumptions:** steady, incompressible, fully developed flow; straight circular pipe
of constant diameter; no elevation change; fittings/entrance/exit losses not included
(add them with K-values or equivalent lengths for a real system).

**Notes:**
- This app uses the **Darcy** friction factor (Moody chart convention).
  The Fanning factor = Darcy / 4 — a classic source of confusion!
- Turbulent f is estimated with the **Swamee–Jain** explicit approximation of the
  Colebrook equation; laminar flow uses **f = 64/Re**.
- Values are for education — verify with recognised standards before engineering use.
        """
    )

st.divider()
st.caption("Built with ❤️ using Streamlit · Educational demo · "
           "Defaults reproduce the classic example: f=0.03, L=50 m, D=100 mm, V=1.5 m/s, ρ=850 kg/m³ → 14.34 kPa")