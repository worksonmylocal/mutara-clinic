/* Shared pieces of the printed documents: letterhead, patient block, signature and footer */
window.Print = (function () {
    const { esc } = Desk;
    const parse = (v) => new Date(String(v).replace(" ", "T"));
    const day = (v) => (v ? parse(v).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "");
    const dt = (v) => { if (!v) return ""; const x = parse(v); return isNaN(x) ? String(v) : day(v) + ", " + x.toTimeString().slice(0, 5); };

    function letterhead(c) {
        const lines = [c.po_box, c.head_office && `Head Office: ${c.head_office}`, c.farm_location && `Farm Location: ${c.farm_location}`]
            .filter(Boolean).map(esc).join("<br>");
        const links = [c.email, c.website].filter(Boolean).map(esc).join("&nbsp;&nbsp;|&nbsp;&nbsp;");
        return `<header class="rh">
            <div class="rh__brand"><img src="/assets/clinic/images/mutara-logo.jpeg" alt="Mutara"></div>
            <div class="rh__contact"><span class="co">${esc(c.company_name || "Mutara Orchards Ltd.")}</span>${lines}
                ${links ? `<span class="links">${links}</span>` : ""}</div>
        </header><div class="rule"></div>`;
    }

    function titlebar(title, right = "") {
        return `<div class="titlebar"><h1>${esc(title)}</h1>${right}</div>`;
    }

    function patientBlock(p, extraLeft = [], extraRight = []) {
        const row = (l, v) => (v ? `<dt>${l}</dt><dd>${esc(v)}</dd>` : "");
        const isEmp = p.patient_type === "Employee";
        return `<section class="meta">
            <dl>
                <dt>Patient</dt><dd class="big">${esc(p.full_name)}</dd>
                ${row("Age / Sex", [p.age, p.sex].filter(Boolean).join(" / "))}
                ${row("ID / Passport", p.national_id)}
                ${isEmp ? row("Staff No.", p.staff_no || p.employee) : row("Phone", p.phone)}
                ${isEmp ? row("Department", p.department || p.section) : ""}
                ${extraLeft.map(([l, v]) => row(l, v)).join("")}
            </dl>
            <dl>
                ${row("Patient No.", p.name)}
                ${extraRight.map(([l, v]) => row(l, v)).join("")}
            </dl>
        </section>`;
    }

    function signBlock(s, label) {
        return `<div class="certify">
            <div><span class="sig">${s.signature ? `<img src="${esc(s.signature)}" alt="">` : ""}</span>
                <small>${esc(label)}</small><b>${esc(s.name || "—")}</b>
                <div class="note" style="margin:0">${esc([s.designation, s.registration_no && "Reg. No. " + s.registration_no].filter(Boolean).join(" · ") || "Doctor / Clinical Officer")}</div></div>
            <div><div class="stamp-box">Clinic stamp</div></div>
        </div>`;
    }

    function footer(d, label) {
        const c = d.clinic;
        return `<footer class="foot">
            <span class="c">CONFIDENTIAL</span> — ${esc(c.report_footer_note || "")}
            <div class="row"><span>${esc(c.clinic_name || "")}${c.licence_no ? " · Reg. No. " + esc(c.licence_no) : ""}</span><span>${esc(label)} · Printed ${esc(dt(d.printed_on))} by ${esc(d.printed_by)}</span></div>
        </footer>`;
    }

    // Warn on screen when the clinician has no Doctor / Clinical Officer profile to sign with
    function signerWarning(s) {
        if (s.can_sign) return;
        const w = document.getElementById("warn");
        w.style.display = "";
        w.innerHTML = `<b>Not yet signable:</b> ${esc(s.name || "The clinician")} has no Doctor or Clinical Officer profile. Add one under <b>Clinic Staff Profile</b> (with the registration number) so the document carries the right credentials.`;
    }

    return { day, dt, letterhead, titlebar, patientBlock, signBlock, footer, signerWarning };
})();
