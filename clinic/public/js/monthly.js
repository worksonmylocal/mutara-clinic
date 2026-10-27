/* Clinical officer's monthly report */
(async function () {
    const { call, esc } = Desk;
    const month = new URLSearchParams(location.search).get("month");
    const msg = document.getElementById("msg"), btn = document.getElementById("print");
    let d;
    try { d = await call("documents.monthly_report", { month }); } catch (e) { msg.textContent = e.message || "The report could not be loaded."; return; }
    const doc = d.doc || {}, c = d.clinical, ex = d.exams;
    let n = 0;
    const sec = (title, body) => `<section class="sec"><h2>${++n} · ${esc(title)}</h2><div class="body">${body}</div></section>`;
    const table = (head, rows, empty = "No records this month.") => rows.length
        ? `<table class="tbl"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((x) => `<td>${esc(x ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table>`
        : `<div class="note">${esc(empty)}</div>`;
    const para = (t) => (t ? `<div class="note" style="white-space:pre-line">${esc(t)}</div>` : "");
    const pct = (g) => (g == null ? "—" : g + "%");
    const day = (v) => Print.day(v);

    const referralList = d.referrals.facilities.length ? `<div class="note">Referred to: ${d.referrals.facilities.map((f) => `${esc(f.facility)} (${f.cases})`).join(", ")}${d.referrals.admitted ? `. ${d.referrals.admitted} admitted.` : ""}</div>` : "";
    const sections = [
        sec("General medical care and clinical operations", `
            ${table(["Activity", "Total", "Notes / significant observations"], [
                ["Clinical assessments", c.assessments, c.work_related ? `Includes ${c.work_related} work-related case${c.work_related === 1 ? "" : "s"}; the rest are general medical cases.` : "General medical cases."],
                ["Treatments provided", c.prescriptions + " prescribed items", [c.top_drugs.length ? "Most dispensed: " + c.top_drugs.map((x) => x.drug).join(", ") : "", c.notifiable.length ? "Notifiable: " + c.notifiable.map((x) => `${x.disease} (${x.cases})`).join(", ") : "No notifiable diseases identified.", doc.treatments_note].filter(Boolean).join(" · ")],
                ["External referrals", d.referrals.total, doc.referral_note || ""],
            ])}${referralList}`),
        sec("Statutory medical examinations", `
            ${table(["Category", "Total targeted", "Number completed", "Compliance gap"], [
                ["Pre-employment exams", ex.pre.targeted || "—", ex.pre.completed, pct(ex.pre.gap)],
                ["Post-employment exams", ex.post.targeted || "—", ex.post.completed, pct(ex.post.gap)],
            ])}${para(doc.exam_findings)}`),
        sec("Pharmacy and medical supplies", `
            ${table(["Medicine", "In stock", "Unit"], d.pharmacy.stock.slice(0, 10).map((s) => [s.item, s.qty, s.uom]), "No drugs registered in the pharmacy.")}
            <div class="note">${d.pharmacy.low.length ? `<b>${d.pharmacy.low.length} item(s) at 10 or fewer:</b> ${d.pharmacy.low.map((s) => esc(s.item)).join(", ")}. ` : "Stock levels are adequate. "}${d.pharmacy.units} units dispensed this month.</div>
            ${para(doc.stock_note)}${doc.restock_note ? para("Restock requirements: " + doc.restock_note) : ""}`),
        sec("Health education and counselling", `
            ${table(["Date", "Type", "Topic", "Audience", "Attendance"], d.education.sessions.concat(d.education.counselling).map((a) => [day(a.activity_date), a.activity_type, a.topic, a.audience, a.attendance_pct ? a.attendance_pct + "%" : (a.attendees || "")]), "No education or counselling sessions recorded.")}
            ${d.education.avg_attendance != null ? `<div class="note">Average attendance: ${d.education.avg_attendance}%</div>` : ""}${para(doc.education_note)}${para(doc.counselling_note)}`),
        sec("Emergency response and referral management", `
            ${table(["Date", "Incident / intervention", "Stabilization steps taken", "Referral destination", "Accompanied by CO?"], d.emergencies.map((i) => [day(i.incident_date), i.description, i.stabilization_steps, i.referral_destination, i.accompanied_by_co ? "Yes" : "No"]), "No emergency interventions this month.")}
            <div class="note" style="margin-top:8px"><b>First aid readiness by department.</b>${d.first_aid.rows.length ? ` ${d.first_aid.depleted} of ${d.first_aid.rows.length} (${Math.round(d.first_aid.depleted * 100 / d.first_aid.rows.length)}%) currently hold depleted stocks.` : ""}</div>
            ${table(["Department", "Kit present?", "Stock status", "Required action"], d.first_aid.rows.map((r) => [r.department, r.kit_present ? "Yes" : "No", r.stock_status, r.required_action]), "No first aid checks recorded.")}`),
        sec("First aid given on the farm", `
            ${d.field_first_aid.total ? `<div class="note">${d.field_first_aid.total} case${d.field_first_aid.total === 1 ? "" : "s"} recorded by first aiders. By outcome: ${d.field_first_aid.outcomes.map(([k, v]) => `${esc(k)} (${v})`).join(", ")}.</div>
                ${table(["Department", "Cases"], d.field_first_aid.by_department.map(([k, v]) => [k, v]))}
                ${table(["Nature", "Cases"], d.field_first_aid.by_nature.map(([k, v]) => [k, v]))}
                ${table(["Supplies used", "Quantity"], d.field_first_aid.supplies.map((x) => [x.item, x.qty + " " + (x.uom || "")]), "No supplies recorded.")}` : '<div class="note">No first aid cases were recorded by first aiders this month.</div>'}
            ${table(["Kit", "Department", "Supplies in kit", "Running low"], d.field_first_aid.kits.map((k) => [k.kit, k.department, k.items, k.low.join(", ") || "—"]), "No first aid kits registered.")}`),
                sec("Accident and incident management", `
            ${table(["Date", "Type", "Employee / department", "Severity", "DOSHMIS filing"], d.incidents.map((i) => [day(i.incident_date), i.report_type + (i.injury_type ? " — " + i.injury_type : ""), [i.employee_name, i.department].filter(Boolean).join(" · "), i.severity, i.doshmis_status]), "No incidents or accidents recorded.")}
            ${d.incidents.filter((i) => i.root_cause || i.corrective_actions).map((i) => `<div class="note"><b>RCA — ${esc(day(i.incident_date))}${i.department ? ", " + esc(i.department) : ""}:</b> ${esc(i.root_cause || "")}${i.corrective_actions ? ` <b>Corrective actions:</b> ${esc(i.corrective_actions)}` : ""}</div>`).join("")}
            ${para(doc.regulatory_note)}
            <div class="note"><b>Trend:</b> ${d.trend.length ? d.trend.slice(0, 4).map((t) => `${esc(t.category)} (${t.n})`).join(", ") : "no diagnoses recorded"}. ${esc(doc.trend_note || "")}</div>`),
        sec("Occupational health and specialized monitoring", `
            ${table(["Risk category", "Exams conducted", "Abnormal results", "Recommended actions"], d.surveillance.entries.map((s) => [s.risk_category, s.exams_conducted, s.abnormal_results, s.recommended_action]), "No surveillance entries this month.")}
            ${d.surveillance.requested.length ? `<div class="note">Requested this month: ${d.surveillance.requested.map((r) => `${esc(r.investigation)} (${r.n})`).join(", ")}.</div>` : ""}${para(doc.compliance_tracking)}`),
        sec("Hygiene, sanitation and environmental health", `
            ${table(["Category", "Facility / area", "Rating", "Result", "Frequency", "Corrective action"], d.hygiene.map((h) => [h.category, h.area, h.rating || "", [h.result, h.contractor_rating && "Contractor: " + h.contractor_rating].filter(Boolean).join(" · "), h.collection_frequency, h.corrective_action]), "No hygiene audits recorded.")}
            ${para(doc.hygiene_note)}`),
        sec("Policy implementation and compliance — " + (doc.policy_status || "Satisfactory"), `${para(doc.policy_note)}${para(doc.training_note)}${d.meetings.length ? `<div class="note"><b>Meetings:</b> ${d.meetings.map((m) => esc(day(m.activity_date) + " — " + m.topic)).join("; ")}</div>` : ""}`),
    ].join("");

    document.title = `Clinical Officer Monthly Report - ${d.period.label}`;
    document.getElementById("sheet-wrap").innerHTML = `
    <article class="sheet">
        <div class="wm">MUTARA</div>
        ${Print.letterhead(d.clinic)}
        ${Print.titlebar("Clinical Officer Monthly Report: " + d.period.label)}
        <section class="meta"><dl><dt>To</dt><dd>${esc(doc.report_to || "Human Resource Operations Manager")}</dd><dt>From</dt><dd>${esc([doc.prepared_by, doc.prepared_by_title || "Clinical Officer"].filter(Boolean).join(", "))}</dd></dl>
            <dl><dt>Report date</dt><dd>${esc(Print.day(doc.report_date || d.period.end))}</dd><dt>Period</dt><dd>${esc(d.period.label)}</dd></dl></section>
        <section class="sec"><h2>Executive summary</h2><div class="body"><div class="note" style="white-space:pre-line;font-size:11.5px">${esc(d.summary)}</div></div></section>
        ${sections}
        <div class="certify"><div><span class="sig"></span><small>Prepared by</small><b>${esc(doc.prepared_by || "")}</b><div class="note" style="margin:0">${esc(doc.prepared_by_title || "Clinical Officer")} · ${esc(Print.day(doc.report_date || d.period.end))}</div></div><div><div class="stamp-box">Clinic stamp</div></div></div>
        ${Print.footer({ clinic: d.clinic, printed_on: d.printed_on, printed_by: d.printed_by }, "Monthly report " + d.period.label)}
    </article>`;
    document.getElementById("warn").style.display = d.doc ? "none" : "";
    if (!d.doc) document.getElementById("warn").innerHTML = "No <b>Clinic Monthly Report</b> record exists for this month, so the targets and the officer's notes are blank. The figures are filled in automatically.";
    msg.style.display = "none"; btn.disabled = false;
    btn.addEventListener("click", () => window.print());
})();
