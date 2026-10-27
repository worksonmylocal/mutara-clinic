/* First aider page: record first aid given on the farm, see the kit */
(async function () {
    const { call, $, $$, esc, num, timeOf, dateOf, pill, empty, toast, kpis, modal, field, read, suggest } = Desk;

    let me;
    try { me = (await call("firstaid.dashboard", {}, { quiet: true })).me; } catch (e) { me = null; }
    await Desk.shell({
        page: "firstaid",
        eyebrow: "Mutara Clinic · First Aid",
        title: "First Aid",
        sub: me ? `${me.name} · ${me.kit}${me.department ? " · " + me.department : ""}` : "Record the first aid you give on the farm",
        tools: `<button class="btn btn--primary" id="new-case">＋ Record a case</button>
                <button class="iconbtn" id="refresh" title="Refresh">${Desk.REFRESH_ICON}</button>`,
    });
    Desk.tabs();
    $("#refresh").addEventListener("click", () => { load(); toast("Refreshed"); });
    $("#new-case").addEventListener("click", () => openCase());

    const OUTCOME_CLS = { "Treated on site": "good", "Sent to the clinic": "info", "Referred to hospital": "warn", "Sent home": "mute" };
    let data;

    async function load() {
        try { data = await call("firstaid.dashboard"); }
        catch (e) { $("#cases").innerHTML = empty(e.message || "You are not registered as a first aider."); $("#kpis").innerHTML = ""; return; }
        const k = data.kpis;
        kpis($("#kpis"), [
            { label: "Cases This Month", value: k.cases_month, cls: "good", unit: `${k.cases_total} in total` },
            { label: "Supplies in Kit", value: k.kit_items, unit: "Different items" },
            { label: "Running Low", value: k.low_items, cls: k.low_items ? "warn" : "", unit: k.low_items ? "2 or fewer left. Ask the clinic to refill" : "Kit is stocked" },
            { label: "Certificate", value: data.me.certificate_expiry ? esc(dateOf(data.me.certificate_expiry)) : "—", unit: "Expiry date" },
        ]);
        $("#cases-meta").textContent = data.cases.length ? `Last ${data.cases.length}` : "";
        $("#cases").innerHTML = data.cases.length ? data.cases.map((c) => `
            <div class="qcard"><div class="qcard__stripe ${c.outcome === "Treated on site" ? "" : "Urgent"}"></div>
                <div><div class="qcard__name">${esc(c.patient_name)} ${pill(c.outcome, OUTCOME_CLS[c.outcome] || "mute")}${c.reviewed ? pill("Reviewed by clinic", "good") : ""}</div>
                <div class="qcard__meta">${esc(c.name)} · ${esc(dateOf(c.case_datetime))} ${esc(timeOf(c.case_datetime))}${c.department ? " · " + esc(c.department) : ""}</div>
                <div class="qcard__note">${esc(c.nature)}</div>
                ${c.supplies_note ? `<div class="qcard__note alert">${esc(c.supplies_note)}</div>` : ""}</div><div></div></div>`).join("") : empty("No cases recorded yet. Tap “Record a case” after giving first aid.");
        $("#kit-meta").textContent = data.kit.length ? `${data.kit.length} items` : "";
        $("#kit").innerHTML = data.kit.length ? `<table class="dtable"><tr><th>Supply</th><th class="num">In kit</th><th>Unit</th></tr>
            ${data.kit.map((r) => `<tr><td><b style="color:var(--ink)">${esc(r.item_name)}</b>${r.qty <= 2 ? " " + pill("Low", "warn") : ""}</td><td class="num">${num(r.qty)}</td><td>${esc(r.uom)}</td></tr>`).join("")}</table>`
            : empty("Your kit has no supplies. Ask the clinic to issue supplies to it.");
    }

    function openCase() {
        if (!data) return toast("Your kit could not be loaded", "error");
        const used = [];
        const h = modal({
            title: "Record a first aid case",
            sub: "Fill this in after you have treated the person.",
            size: "wide",
            body: `
                <div class="field"><label>Employee treated <span class="req">*</span></label><input class="input" id="fa-emp" placeholder="Type a name to search, or type any name" autocomplete="off"></div>
                <div class="grid-2">${field("department", "Department")}${field("location", "Where on the farm")}</div>
                <div class="grid-2">${field("nature", "What was it? *", { type: "select", options: ["", "Cut / wound", "Burn", "Fracture / sprain / soft tissue", "Eye injury", "Chemical exposure", "Fainting / dizziness", "Fever / illness", "Insect / snake bite", "Other"] })}
                    ${field("outcome", "Outcome *", { type: "select", options: ["Treated on site", "Sent to the clinic", "Referred to hospital", "Sent home"] })}</div>
                ${field("description", "What happened", { type: "textarea", rows: 2 })}
                ${field("treatment", "First aid given *", { type: "textarea", rows: 2 })}
                <div class="subhead">Supplies used from your kit</div>
                <div class="field"><input class="input" id="fa-add" placeholder="Search your kit…"></div>
                <div id="fa-used"></div>`,
            foot: [{ label: "Cancel" }, { label: "Save case", cls: "btn--primary", onClick: save }],
        });
        let employee = null;
        const empInput = $("#fa-emp", h.body);
        suggest(empInput, {
            fetch: (q) => (q.length < 2 ? [] : call("firstaid.search_employees", { q }, { quiet: true })),
            render: (e) => ({ main: e.employee_name, sub: `${e.name}${e.department ? " · " + e.department : ""}` }),
            onPick: (e) => { employee = e; empInput.value = e.employee_name; const d = $("[data-f=department]", h.body); if (!d.value) d.value = e.department || ""; },
        });
        empInput.addEventListener("input", () => { if (employee && empInput.value !== employee.employee_name) employee = null; });
        suggest($("#fa-add", h.body), {
            fetch: (q) => data.kit.filter((r) => !q || r.item_name.toLowerCase().includes(q.toLowerCase())).slice(0, 10),
            render: (r) => ({ main: r.item_name, sub: `${r.qty} ${r.uom} in kit` }),
            onPick: (r) => { if (!used.some((u) => u.item === r.item)) used.push({ item: r.item, name: r.item_name, qty: 1, max: r.qty, uom: r.uom }); $("#fa-add", h.body).value = ""; draw(); },
        });
        function draw() {
            $("#fa-used", h.body).innerHTML = used.length ? used.map((u, i) => `<div class="linebox"><div class="linebox__row"><b style="color:var(--ink)">${esc(u.name)}</b>
                <div style="display:flex;gap:10px;align-items:center"><input class="input" type="number" min="1" max="${u.max}" step="any" style="width:90px" data-q="${i}" value="${u.qty}"> ${esc(u.uom)}
                <button class="iconx" data-x="${i}" type="button">×</button></div></div></div>`).join("") : '<div class="printnote">Nothing used.</div>';
            $$("[data-q]", h.body).forEach((x) => x.addEventListener("input", () => (used[x.dataset.q].qty = x.value)));
            $$("[data-x]", h.body).forEach((x) => x.addEventListener("click", () => { used.splice(Number(x.dataset.x), 1); draw(); }));
        }
        draw();
        async function save(hh) {
            const v = read(hh.body);
            const name = (empInput.value || "").trim();
            if (!name) return toast("Enter the name of the person treated", "warn");
            if (!v.nature) return toast("Choose what it was", "warn");
            if (!(v.treatment || "").trim()) return toast("Describe the first aid given", "warn");
            const r = await call("firstaid.record_case", { data: { ...v, patient_name: name, employee: employee ? employee.name : null, items: used.map((u) => ({ item: u.item, qty: u.qty })) } });
            hh.close();
            toast(`Case ${r.name} saved`);
            if (r.supplies_note) toast(r.supplies_note, "warn");
            load();
        }
    }

    await load();
    Desk.poll(load, 60000);
})();
