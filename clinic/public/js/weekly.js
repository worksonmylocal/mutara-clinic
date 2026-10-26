/* Weekly clinic activity report */
(async function () {
    const { call, esc } = Desk;
    const q = new URLSearchParams(location.search);
    const msg = document.getElementById("msg"), btn = document.getElementById("print");
    let d;
    try { d = await call("documents.weekly_report", { week: q.get("week") || null, include_sunday: q.get("sunday") || 0 }); } catch (e) { msg.textContent = e.message || "The report could not be loaded."; return; }
    const r = d.report;
    document.title = `Weekly clinic activity ${r.start} to ${r.end}`;
    const cell = (v) => esc(v).replace(/\n/g, "<br>");
    document.getElementById("sheet-wrap").innerHTML = `
    <article class="sheet">
        <div class="wm">MUTARA</div>
        ${Print.letterhead(d.clinic)}
        ${Print.titlebar("Weekly Clinic Activity Report", `<div class="note" style="font-size:12px"><b>${esc(Print.day(r.start))} – ${esc(Print.day(r.end))}</b></div>`)}
        <table class="tbl" style="table-layout:fixed">
            <thead><tr><th style="width:17%">Activity</th>${r.days.map((x) => `<th>${esc(x.label)}<br><span style="font-weight:400">${esc(x.short)}</span></th>`).join("")}<th class="r" style="width:6%">Total</th></tr></thead>
            <tbody>${r.rows.map((row) => `<tr><td><b>${esc(row.label)}</b></td>${row.cells.map((c) => `<td style="vertical-align:top;${row.kind === "num" ? "text-align:center;font-weight:600" : ""}">${cell(c)}</td>`).join("")}<td class="r"><b>${esc(row.total)}</b></td></tr>`).join("")}</tbody>
        </table>
        ${Print.footer({ clinic: d.clinic, printed_on: d.printed_on, printed_by: d.printed_by }, "Weekly report")}
    </article>`;
    msg.style.display = "none"; btn.disabled = false;
    btn.addEventListener("click", () => window.print());
})();
