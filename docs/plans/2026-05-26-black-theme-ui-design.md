# Stock Analyst Professional Black UI Theme Specification

This specification outlines the UI overhaul to transform the Julian Komar Stock Analyst dashboard into a high-end, professional pitch-black SaaS interface with cyber-neon blue and cyan accents, powered by custom CSS overlays and polished Plotly area charts.

---

## 1. Design Aesthetics & Colors

We will implement a unified dark color palette that creates an immersive developer-centric environment:

| Layer | Color | Purpose |
| :--- | :--- | :--- |
| **App Canvas** | `#020202` | Solid pitch-black primary background |
| **Sidebar Canvas** | `#09090b` | Dark secondary side navigation |
| **Ambient Glow** | `#081026` | Subtle cyber-blue radial background glow |
| **Glass Card Background** | `rgba(10, 10, 12, 0.8)` | Translucent premium card panels |
| **Glass Card Border** | `rgba(59, 130, 246, 0.08)` | Sub-pixel glowing borders |
| **Accent Primary** | `#3b82f6` (Neon Blue) | Active links, primary headers, button gradients |
| **Accent Secondary** | `#06b6d4` (Cyan) | Secondary indicators, technical text highlights |

---

## 2. Component Design Specifications

### A. Core Custom CSS Styling (`src/ui_components.py`)
1. **Google Fonts**: Load the premium **Outfit** font and apply it to all elements in the app.
2. **Container Overrides**:
   - Set Streamlit's container background to `#020202` with an ambient top-left radial gradient.
   - Set Streamlit's sidebar background to `#09090b` with a sub-pixel border.
3. **Metric Card Overhaul (`.komar-card`)**:
   - Translucent panel (`rgba(10, 10, 12, 0.8)`) with `backdrop-filter: blur(20px)`.
   - Add a subtle glow on hover with 3D elevation transitions.
   - Refine text colors: labels to `#64748b` (slate-500) and metric values to `#f8fafc` (slate-50) for high readability.
4. **Vibrant Call-to-Action Buttons**:
   - Set glowing cyber-blue button gradients.
   - Implement micro-animations (`transform: translateY(-2px)` on hover).
5. **Polished Tabs Layout**:
   - Custom style Streamlit's Tab selector bar with a clean sub-pixel border, dark background, and an active neon-blue indicator tag.
6. **Dark Tables**:
   - Custom style Streamlit tables to feature dark borders (`rgba(255, 255, 255, 0.04)`), aligned headers, and highlighted statuses.

### B. High-End Plotly Charts (`src/ui_components.py`)
1. **Unified Gridlines**: All charts set background as fully transparent (`paper_bgcolor="rgba(0,0,0,0)"`, `plot_bgcolor="rgba(0,0,0,0)"`). All gridlines set to a highly subtle, elegant translucency (`rgba(255, 255, 255, 0.02)`).
2. **Stock close price line**: Set close price line to neon-blue (`#3b82f6`, `width=3`) with an area fill under the curve (`rgba(59, 130, 246, 0.03)`).
3. **Volume overlay**: Translucent volume bars in the background (`rgba(148, 163, 184, 0.1)`).
4. **Financial Growth Comparison**: Cyber-blue/cyan bars for positive growth, subtle dark-red bars for low-growth values, highlighting contrast.

---

## 3. Implementation and Verification

- The existing metrics computations, ticker overrides, and yfinance caches remain strictly untouched to ensure calculations remain 100% correct.
- Verification will be conducted by running `streamlit run app.py` and manually checking visual consistency, contrast ratios, and neon transitions across all screen sizes.
