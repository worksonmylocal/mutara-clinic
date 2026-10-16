/* Pre- and post-employment medical examination report */
(async function () {
    const { call, esc } = Desk;
    const consultation = new URLSearchParams(location.search).get("consultation");
    const msg = document.getElementById("msg"), btn = document.getElementById("print");
    if (!consultation) { msg.textContent = "No consultation selected."; return; }
    let d;
    try { d = await call("documents.medical_certificate", { consultation }); } catch (e) { msg.textContent = e.message || "The report could not be loaded."; return; }

    const pre = d.exam_type.startsWith("Pre");
    const t = d.triage;
    const vt = (l, v, u, bad) => (v ? `<div class="vt ${bad ? "bad" : ""}"><small>${l}</small><b>${esc(v)}</b> <span class="note" style="margin:0">${u}</span></div>` : "");
    const row = (l, v) => (v ? `<dt>${l}</dt><dd>${esc(v)}</dd>` : "");
    const cls = { Unfit: "bad", "Temporarily Unfit": "warn", "Fit with Restrictions": "warn" }[d.fitness_status] || "";
    const history = Object.entries(d.history).filter(([, v]) => v).map(([k, v]) => row(k, v)).join("");
    let sec = 0;
    const n = () => ++sec;
    const done = d.tests.filter((x) => x.result || x.findings);

    document.title = `${d.exam_type} - ${d.patient.full_name} - ${d.consultation}`;
    Print.signerWarning(d.signer);
    document.getElementById("sheet-wrap").innerHTML = `
    <article class="sheet">
        <div class="wm">MUTARA</div>
        ${Print.letterhead(d.clinic)}
        ${Print.titlebar(d.exam_type + " Report", '<div class="conf">Confidential</div>')}
        ${Print.patientBlock(d.patient, [[pre ? "Position applied" : "Position held", d.job_position]], [["Examined on", Print.day(d.consultation_date)], ["Report No.", d.consultation]])}
        ${t ? `<section class="sec"><h2>${n()} · Vital signs</h2><div class="body"><div class="vgrid">
            ${vt("BP", t.bp_systolic ? `${t.bp_systolic}/${t.bp_diastolic}` : "", "mmHg", t.bp_systolic >= 140 || t.bp_diastolic >= 90)}
            ${vt("Pulse", t.pulse_rate, "bpm", t.pulse_rate > 100 || t.pulse_rate < 60)}${vt("Temperature", t.temperature, "°C", t.temperature >= 38)}
            ${vt("SpO₂", t.spo2, "%", t.spo2 < 95)}${vt("Weight", t.weight_kg, "kg")}${vt("Height", t.height_cm, "cm")}${vt("BMI", t.bmi, t.bmi_category || "")}
        </div></div></section>` : ""}
        ${history ? `<section class="sec"><h2>${n()} · Medical history</h2><div class="body"><dl class="kv">${history}</dl></div></section>` : ""}
        <section class="sec"><h2>${n()} · Examination findings</h2><div class="body">
            ${done.length ? `<table class="tbl"><thead><tr><th style="width:34%">Examination</th><th style="width:16%">Result</th><th>Findings</th></tr></thead><tbody>
                ${done.map((x) => `<tr class="${x.result === "Abnormal" ? "abn" : ""}"><td>${esc(x.test)}</td><td>${esc(x.result || "")}</td><td>${esc(x.findings || "")}</td></tr>`).join("")}</tbody></table>`
                : '<div class="note">No examination findings recorded.</div>'}
            ${d.remarks ? `<div class="note">Examiner's remarks: ${esc(d.remarks)}</div>` : ""}
            ${d.investigations.length ? `<div class="note">Investigations requested: ${d.investigations.map((i) => esc(i.investigation)).join("; ")}</div>` : ""}
            ${d.diagnoses.length ? `<div class="note">Conditions noted: ${d.diagnoses.map((x) => esc(x.diagnosis)).join("; ")}</div>` : ""}
        </div></section>
        <section class="sec"><h2>${n()} · Conclusion</h2><div class="body"><div class="fit ${cls}">
            <div class="big">${esc(d.fitness_status || "Outcome not recorded")}</div>
            ${d.restrictions ? `<div style="margin-top:4px"><b>Restrictions / conditions:</b> ${esc(d.restrictions)}</div>` : ""}
            ${d.valid_until ? `<div style="margin-top:4px">Valid until <b>${esc(Print.day(d.valid_until))}</b></div>` : ""}
        </div></div></section>
        ${Print.signBlock(d.signer, "Examined and certified by")}
        ${Print.footer(d, d.consultation)}
    </article>`;
    msg.style.display = "none";
    btn.disabled = false;
    btn.addEventListener("click", () => window.print());
})();
