/* Referral form for laboratory or imaging investigations (the clinic has neither on site) */
(async function () {
    const { call, esc } = Desk;
    const q = new URLSearchParams(location.search);
    const consultation = q.get("consultation"), type = q.get("type") || "Laboratory";
    const msg = document.getElementById("msg"), btn = document.getElementById("print");
    if (!consultation) { msg.textContent = "No consultation selected."; return; }
    let d;
    try { d = await call("documents.referral", { consultation, category: type }); } catch (e) { msg.textContent = e.message || "The referral could not be loaded."; return; }

    const imaging = d.category === "Imaging";
    const title = imaging ? "Imaging Request / Referral" : "Laboratory Request / Referral";
    const t = d.triage;
    const vit = t ? [
        t.bp_systolic && `BP ${t.bp_systolic}/${t.bp_diastolic} mmHg`, t.pulse_rate && `Pulse ${t.pulse_rate} bpm`, t.temperature && `Temp ${t.temperature} °C`,
        t.spo2 && `SpO₂ ${t.spo2}%`, t.weight_kg && `Wt ${t.weight_kg} kg`, t.bmi && `BMI ${t.bmi}`,
    ].filter(Boolean).join("  ·  ") : "";
    const row = (l, v) => (v ? `<dt>${l}</dt><dd>${esc(v)}</dd>` : "");
    const dx = d.diagnoses.map((x) => x.diagnosis + (x.type === "Provisional" ? " (provisional)" : "")).join("; ");

    document.title = `${imaging ? "Imaging" : "Lab"} referral - ${d.patient.full_name} - ${d.consultation}`;
    Print.signerWarning(d.signer);
    document.getElementById("sheet-wrap").innerHTML = `
    <article class="sheet">
        <div class="wm">MUTARA</div>
        ${Print.letterhead(d.clinic)}
        ${Print.titlebar(title, d.urgent ? '<span class="urgent-tag">Urgent</span>' : "")}
        ${Print.patientBlock(d.patient, [], [["Date", Print.day(d.consultation_date)], ["Visit No.", d.visit]])}
        <div class="to-box"><small>Refer to</small><b>${esc(d.referred_to || "Laboratory / Imaging facility of the patient's choice")}</b></div>
        <section class="sec"><h2>Clinical summary</h2><div class="body"><dl class="kv">
            ${row("Complaint", d.complaint)}${row("History", d.history)}${row("Vital signs", vit)}
            ${row("Diagnosis", dx)}${d.drug_allergies ? row("Allergies", d.drug_allergies) : ""}
        </dl></div></section>
        <section class="sec"><h2>${imaging ? "Imaging requested" : "Tests requested"}</h2><div class="body">
            <table class="tbl"><thead><tr><th style="width:6%">#</th><th>${imaging ? "Study" : "Test"}</th><th style="width:14%">Priority</th><th style="width:40%">Clinical notes</th></tr></thead><tbody>
                ${d.items.map((i, n) => `<tr><td>${n + 1}</td><td><b>${esc(i.investigation)}</b></td><td>${i.urgency === "Urgent" ? '<b style="color:var(--alert)">URGENT</b>' : "Routine"}</td><td>${esc(i.clinical_notes || "")}</td></tr>`).join("")}
            </tbody></table>
            <div class="rx-note">Please send the results (report${imaging ? " and images" : ""}) back to the Mutara Orchards clinic with the patient.</div>
        </div></section>
        ${Print.signBlock(d.signer, "Requested by")}
        ${Print.footer(d, d.consultation)}
    </article>`;
    msg.style.display = "none";
    btn.disabled = false;
    btn.textContent = imaging ? "Print imaging referral" : "Print lab referral";
    btn.addEventListener("click", () => window.print());
})();
