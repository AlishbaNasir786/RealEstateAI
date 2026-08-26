"""
HTML/CSS template for the competitor intelligence report.
3-colour palette only: Navy #1a2e4a | Gold #b8902a | Off-white #f5f6f8
"""

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f4;
     color:#1a2e4a;line-height:1.6;font-size:15px}
a{color:inherit;text-decoration:none}

/* ── wrapper ── */
.page{max-width:1160px;margin:32px auto;background:#fff;
      box-shadow:0 2px 16px rgba(0,0,0,.10)}

/* ── header ── */
.hdr{background:#1a2e4a;padding:44px 52px 36px;color:#fff}
.hdr-top{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px}
.hdr-title{font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;
           color:#b8902a;margin-bottom:10px}
.hdr h1{font-size:28px;font-weight:700;line-height:1.2;color:#fff}
.hdr-sub{font-size:13px;color:#aab4c4;margin-top:6px}
.hdr-meta{display:flex;gap:1px;margin-top:28px;border:1px solid rgba(255,255,255,.12)}
.hdr-stat{flex:1;padding:16px 20px;border-right:1px solid rgba(255,255,255,.12);min-width:110px}
.hdr-stat:last-child{border-right:none}
.hs-val{font-size:22px;font-weight:700;color:#fff}
.hs-lbl{font-size:11px;color:#8898aa;text-transform:uppercase;letter-spacing:.8px;margin-top:3px}
.hdr-notice{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}
.notice-tag{font-size:12px;font-weight:600;padding:5px 14px;
            border:1px solid rgba(255,255,255,.2);color:#d4a853}
.notice-tag.red{border-color:rgba(200,80,80,.5);color:#e08080}
.hdr-ts{font-size:12px;color:#6b7a8d;margin-top:16px}

/* ── section ── */
.sec{padding:40px 52px;border-bottom:1px solid #e4e8ef}
.sec:last-child{border-bottom:none}
.sec-title{font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
           color:#b8902a;margin-bottom:4px}
.sec-heading{font-size:20px;font-weight:700;color:#1a2e4a;margin-bottom:6px}
.sec-desc{font-size:13px;color:#6b7a8d;margin-bottom:24px;line-height:1.6;
          max-width:740px}
.sec-alt{background:#f5f6f8}

/* ── KPI row ── */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:0;
         border:1px solid #dde2ea}
.kpi-cell{padding:22px 18px;border-right:1px solid #dde2ea}
.kpi-cell:last-child{border-right:none}
.kpi-v{font-size:26px;font-weight:700;color:#1a2e4a}
.kpi-l{font-size:12px;font-weight:600;color:#6b7a8d;margin-top:4px;line-height:1.3}
.kpi-s{font-size:11px;color:#aab4c4;margin-top:2px}

/* ── data table ── */
.dt{width:100%;border-collapse:collapse;font-size:13.5px}
.dt thead tr{background:#1a2e4a;color:#fff}
.dt thead th{padding:10px 14px;text-align:left;font-weight:600;
             font-size:11px;letter-spacing:.7px;text-transform:uppercase}
.dt tbody tr{border-bottom:1px solid #e8ecf2}
.dt tbody tr:last-child{border-bottom:none}
.dt tbody tr:nth-child(even){background:#f8f9fb}
.dt tbody td{padding:11px 14px;color:#2d3e55}
.td-r{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:#1a2e4a}
.tag{display:inline-block;padding:2px 9px;font-size:11px;font-weight:600;
     text-transform:uppercase;letter-spacing:.4px}
.tag-red{background:#fdf0f0;color:#b94040;border:1px solid #f0c8c8}
.tag-grn{background:#f0fdf4;color:#276749;border:1px solid #b7e4c7}
.tag-amber{background:#fdf6e8;color:#92660a;border:1px solid #e8d09a}
.tag-navy{background:#eef1f7;color:#1a2e4a;border:1px solid #c8d0e0}

/* ── bar ── */
.bar-bg{background:#dde2ea;height:7px;margin-top:6px}
.bar-fg{height:7px;background:#b8902a}

/* ── city grid ── */
.city-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1px;
           background:#dde2ea;border:1px solid #dde2ea}
.city-card{background:#fff;padding:22px}
.city-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px}
.cc-name{font-size:17px;font-weight:700;color:#1a2e4a}
.cc-price{font-size:21px;font-weight:700;color:#1a2e4a;text-align:right}
.cc-cat{font-size:11px;font-weight:600;letter-spacing:.7px;text-transform:uppercase;
        color:#b8902a;margin-top:2px;margin-bottom:14px}
.cc-divider{border:none;border-top:1px solid #e4e8ef;margin:12px 0}
.cc-table-inner{width:100%;border-collapse:collapse;font-size:12.5px;margin-bottom:4px}
.cc-lbl{color:#6b7a8d;padding:5px 0}
.cc-val{font-weight:600;color:#1a2e4a;text-align:right;padding:5px 0}
.dist-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}
.di-num{font-size:16px;font-weight:700;color:#1a2e4a}
.di-lbl{font-size:10px;color:#8898aa;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}

/* ── keyword tags ── */
.kw-wrap{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.kw-item{font-size:13px;padding:4px 12px;background:#eef1f7;color:#1a2e4a;
         border:1px solid #c8d0e0}
.kw-item em{font-style:normal;font-size:11px;color:#8898aa;margin-left:4px}

/* ── suggestions ── */
.sug{padding:20px 22px;border-left:3px solid #1a2e4a;
     background:#f8f9fb;margin-bottom:12px}
.sug.critical{border-left-color:#b94040;background:#fef8f8}
.sug.high{border-left-color:#b8902a;background:#fdf8ef}
.sug-top{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.sug-num{font-size:11px;font-weight:700;color:#8898aa;min-width:24px}
.sug-pri{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.7px}
.sug-cat{font-size:11px;color:#8898aa;margin-left:4px}
.sug-title{font-size:15px;font-weight:700;color:#1a2e4a;margin-bottom:4px}
.sug-stat{font-size:12px;color:#6b7a8d;margin-bottom:10px}
.sug-desc{font-size:13.5px;color:#3d4e60;line-height:1.65;margin-bottom:10px}
.sug-action{font-size:13px;color:#1a2e4a;background:#eef1f7;
            padding:10px 14px;margin-bottom:8px;border-left:2px solid #b8902a}
.sug-impact{font-size:12px;color:#276749;font-weight:600}

/* ── strategy cards ── */
.strat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
            gap:1px;background:#dde2ea;border:1px solid #dde2ea}
.strat-card{background:#fff;padding:24px}
.strat-title{font-size:14px;font-weight:700;color:#1a2e4a;
             border-bottom:2px solid #b8902a;padding-bottom:8px;margin-bottom:12px}
.strat-body{font-size:13.5px;color:#3d4e60;line-height:1.7}

/* ── methodology ── */
.meth-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.meth-card{background:#fff;border:1px solid #dde2ea;padding:18px}
.meth-heading{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;
              color:#1a2e4a;margin-bottom:8px}
.meth-body{font-size:13px;color:#4a5568;line-height:1.65}

/* ── footer ── */
.ftr{background:#1a2e4a;padding:20px 52px;display:flex;
     justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.ftr-l{font-size:12px;color:#8898aa}
.ftr-r{font-size:12px;color:#6b7a8d}

@media(max-width:640px){
  .hdr,.sec,.ftr{padding-left:20px;padding-right:20px}
  .hdr h1{font-size:22px}
  .hdr-meta{flex-wrap:wrap}
  .hdr-stat{min-width:100px}
}
"""
