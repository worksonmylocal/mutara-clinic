"""Figures behind the weekly clinic activity report and the clinical officer's monthly report."""

from collections import Counter

import frappe
from frappe.utils import add_days, flt, formatdate, get_first_day, get_last_day, getdate

from clinic import stock

MEDICALS = ("Pre-Employment Medical", "Post-Employment Medical")


def _between(start, end):
	return [f"{start} 00:00:00", f"{end} 23:59:59"]


def _notifiable(start, end):
	return frappe.db.sql(
		"""
		SELECT DATE(c.consultation_date) AS day, d.diagnosis AS name
		FROM `tabClinic Consultation Diagnosis` d
		JOIN `tabClinic Consultation` c ON c.name = d.parent
		JOIN `tabClinic Diagnosis` x ON x.name = d.diagnosis
		WHERE x.is_notifiable = 1 AND c.consultation_date BETWEEN %s AND %s
		""",
		_between(start, end),
		as_dict=True,
	)


# ------------------------------------------------------------------ weekly
def weekly_data(any_date=None, include_sunday=False):
	"""One column per day (Monday to Saturday), one row per activity: the layout of the weekly clinic report."""
	start = getdate(any_date)
	start = add_days(start, -start.weekday())
	days = [add_days(start, i) for i in range(7 if include_sunday else 6)]
	end = days[-1]

	consultations = frappe.get_all(
		"Clinic Consultation",
		filters={"consultation_date": ["between", _between(start, end)]},
		fields=["name", "consultation_date", "consultation_type", "refer_out", "admitted"],
	)
	incidents = frappe.get_all(
		"Clinic Incident",
		filters={"incident_date": ["between", [start, end]]},
		fields=["incident_date", "report_type", "description", "department"],
		order_by="creation",
	)
	activities = frappe.get_all(
		"Clinic Health Activity",
		filters={"activity_date": ["between", [start, end]]},
		fields=["activity_date", "activity_type", "topic", "audience"],
		order_by="creation",
	)
	notifiable = _notifiable(start, end)
	field_cases = frappe.get_all(
		"Clinic First Aid Case",
		filters={"case_datetime": ["between", _between(start, end)]},
		fields=["case_datetime", "nature", "department", "outcome", "first_aider_name"],
		order_by="case_datetime",
	)

	def of_day(rows, key, day):
		return [r for r in rows if getdate(r[key]) == day]

	def numeric(label, pick):
		cells = [len(pick(of_day(consultations, "consultation_date", d))) for d in days]
		return {"label": label, "kind": "num", "cells": cells, "total": sum(cells)}

	def listing(label, rows, key, wanted, none, show):
		cells, total = [], 0
		for d in days:
			items = [r for r in of_day(rows, key, d) if wanted(r)]
			total += len(items)
			cells.append(
				"\n".join(f"{n}. {show(r)}" for n, r in enumerate(items, 1)) if items else none
			)
		return {"label": label, "kind": "text", "cells": cells, "total": total}

	def exam_cell(d):
		counts = Counter(c.consultation_type for c in of_day(consultations, "consultation_date", d) if c.consultation_type in MEDICALS)
		return ", ".join(f"{t.split('-')[0]}-employment {n}" for t, n in counts.items()) or "None"

	def notifiable_cell(d):
		counts = Counter(r["name"] for r in notifiable if getdate(r["day"]) == d)
		return ", ".join(f"{name} × {n}" for name, n in counts.items()) or "No notifiable disease"

	rows = [
		numeric("Total Patients Seen", lambda c: c),
		numeric("  of which Employment Medicals", lambda c: [x for x in c if x.consultation_type in MEDICALS]),
		numeric("  Referrals", lambda c: [x for x in c if x.refer_out]),
		numeric("  Admissions", lambda c: [x for x in c if x.admitted]),
		listing("Incident Reports (No. & Brief Description)", incidents, "incident_date", lambda r: r.report_type == "Incident",
			"No incident report", lambda r: f"{r.description}" + (f" — {r.department}" if r.department else "")),
		listing("Accident Reports (No. & Brief Description)", incidents, "incident_date", lambda r: r.report_type == "Accident",
			"No accident report", lambda r: f"{r.description}" + (f" — {r.department}" if r.department else "")),
		{"label": "Notifiable Diseases (Type & No. of Cases)", "kind": "text", "cells": [notifiable_cell(d) for d in days],
			"total": len(notifiable)},
		{"label": "Medical Examinations (No. & Type)", "kind": "text", "cells": [exam_cell(d) for d in days],
			"total": sum(1 for c in consultations if c.consultation_type in MEDICALS)},
		listing("First Aid Given on the Farm (by first aiders)", field_cases, "case_datetime", lambda r: True, "None",
			lambda r: f"{r.nature}" + (f" — {r.department}" if r.department else "") + (f" → {r.outcome}" if r.outcome != "Treated on site" else "")),
		listing("Meetings", activities, "activity_date", lambda r: r.activity_type == "Meeting", "None", lambda r: r.topic),
		listing("Health Education / Counselling / Training", activities, "activity_date",
			lambda r: r.activity_type != "Meeting", "None", lambda r: f"{r.activity_type}: {r.topic}"),
	]
	return {
		"start": str(start),
		"end": str(end),
		"days": [{"date": str(d), "label": d.strftime("%A"), "short": formatdate(d, "d/M/yy")} for d in days],
		"rows": rows,
	}


# ------------------------------------------------------------------ monthly
def monthly_data(any_date=None):
	start = get_first_day(getdate(any_date))
	end = get_last_day(start)
	rng = _between(start, end)
	doc = frappe.db.get_value("Clinic Monthly Report", {"period_start": start}, "*", as_dict=True)

	cons = frappe.get_all(
		"Clinic Consultation",
		filters={"consultation_date": ["between", rng]},
		fields=["name", "consultation_type", "work_related", "refer_out", "admitted", "referral_facility", "consultation_date"],
	)
	general = [c for c in cons if c.consultation_type == "Consultation"]
	pre = [c for c in cons if c.consultation_type == "Pre-Employment Medical"]
	post = [c for c in cons if c.consultation_type == "Post-Employment Medical"]
	referred = [c for c in cons if c.refer_out]

	def count(rows, kind):
		return sum(1 for r in rows if r.report_type == kind) if rows else 0

	incidents = frappe.get_all(
		"Clinic Incident", filters={"incident_date": ["between", [start, end]]},
		fields=["name", "incident_date", "report_type", "severity", "department", "employee_name", "description", "injury_type",
			"work_related", "stabilization_steps", "referral_destination", "accompanied_by_co", "root_cause", "corrective_actions",
			"doshmis_status", "insurance_status"], order_by="incident_date")
	drugs = frappe.db.sql(
		"""
		SELECT IFNULL(i.drug_name, i.drug) AS drug, SUM(i.dispensed_qty) AS qty
		FROM `tabClinic Dispensing Item` i JOIN `tabClinic Dispensing` d ON d.name = i.parent
		WHERE d.docstatus = 1 AND d.dispensed_on BETWEEN %s AND %s AND i.dispensed_qty > 0
		GROUP BY i.drug, i.drug_name ORDER BY qty DESC
		""", rng, as_dict=True)
	prescriptions = frappe.db.sql(
		"""SELECT COUNT(*) FROM `tabClinic Prescription Item` p JOIN `tabClinic Consultation` c ON c.name = p.parent
		WHERE c.consultation_date BETWEEN %s AND %s""", rng)[0][0]
	notifiable = Counter(r["name"] for r in _notifiable(start, end))

	from clinic.api.consultation import drug_groups

	items = frappe.get_all("Item", filters={"disabled": 0, "is_stock_item": 1, "item_group": ["in", drug_groups()]}, fields=["name", "item_name", "stock_uom"], order_by="item_name")
	on_hand = stock.on_hand([i.name for i in items])
	stock_rows = [{"item": i.item_name, "uom": i.stock_uom, "qty": on_hand.get(i.name, 0)} for i in items]
	stock_rows.sort(key=lambda r: r["qty"])

	activities = frappe.get_all(
		"Clinic Health Activity", filters={"activity_date": ["between", [start, end]]},
		fields=["activity_date", "activity_type", "topic", "audience", "expected_attendees", "attendees", "attendance_pct"], order_by="activity_date")
	education = [a for a in activities if a.activity_type in ("Health Education", "Training", "Other")]
	counselling = [a for a in activities if a.activity_type == "Counselling"]
	meetings = [a for a in activities if a.activity_type == "Meeting"]
	attendance = [a.attendance_pct for a in education if a.attendance_pct]

	first_aid = {}
	for row in frappe.get_all("Clinic First Aid Check", filters={"check_date": ["between", [start, end]]},
			fields=["department", "kit_present", "stock_status", "required_action", "check_date"], order_by="check_date asc, creation asc"):
		first_aid[row.department] = row  # the latest check of the month per department
	first_aid = sorted(first_aid.values(), key=lambda r: r.department)

	hygiene = frappe.get_all("Clinic Hygiene Audit", filters={"audit_date": ["between", [start, end]]},
		fields=["audit_date", "category", "area", "rating", "result", "collection_frequency", "contractor_rating", "corrective_action"], order_by="audit_date")
	surveillance = frappe.get_all("Clinic Surveillance Entry", filters={"entry_date": ["between", [start, end]]},
		fields=["entry_date", "risk_category", "exams_conducted", "abnormal_results", "recommended_action"], order_by="entry_date")
	requested = frappe.db.sql(
		"""SELECT r.investigation, COUNT(*) AS n FROM `tabClinic Investigation Request` r JOIN `tabClinic Consultation` c ON c.name = r.parent
		WHERE c.consultation_date BETWEEN %s AND %s AND (r.investigation LIKE %s OR r.investigation LIKE %s) GROUP BY r.investigation""",
		(*rng, "%Cholinesterase%", "%Audiometry%"), as_dict=True)
	categories = frappe.db.sql(
		"""SELECT IFNULL(x.category, 'Other') AS category, COUNT(*) AS n FROM `tabClinic Consultation Diagnosis` d
		JOIN `tabClinic Consultation` c ON c.name = d.parent LEFT JOIN `tabClinic Diagnosis` x ON x.name = d.diagnosis
		WHERE c.consultation_date BETWEEN %s AND %s GROUP BY x.category ORDER BY n DESC""", rng, as_dict=True)

	fa_cases = frappe.get_all(
		"Clinic First Aid Case", filters={"case_datetime": ["between", rng]},
		fields=["name", "case_datetime", "department", "nature", "outcome", "first_aider_name", "kit"])
	fa_supplies = frappe.db.sql(
		"""SELECT i.item_name AS item, SUM(i.qty) AS qty, i.uom FROM `tabClinic First Aid Item` i
		JOIN `tabClinic First Aid Case` c ON c.name = i.parent
		WHERE i.parenttype = 'Clinic First Aid Case' AND c.case_datetime BETWEEN %s AND %s GROUP BY i.item_name, i.uom ORDER BY qty DESC""", rng, as_dict=True)
	kits = []
	for kit in frappe.get_all("Clinic First Aid Kit", filters={"active": 1}, fields=["kit_name", "department", "warehouse"], order_by="kit_name"):
		rows = stock.kit_stock(kit.warehouse) if kit.warehouse else []
		kits.append({"kit": kit.kit_name, "department": kit.department, "items": len(rows), "low": [r["item_name"] for r in rows if r["qty"] <= 2]})

	def exam(done, target_field):
		target = (doc or {}).get(target_field) or 0
		return {"targeted": target, "completed": len(done), "gap": round((target - len(done)) * 100 / target) if target else None}

	exams = {"pre": exam(pre, "pre_employment_target"), "post": exam(post, "post_employment_target")}
	work_related = sum(1 for c in cons if c.work_related) or count(incidents, "Accident")
	month = formatdate(start, "MMMM yyyy")
	summary = (doc or {}).get("exec_summary") or (
		f"The month of {month} saw {len(cons)} patient visits ({len(general)} general assessments"
		f"{f', {work_related} work-related' if work_related else ''}), {len(pre)} pre-employment and {len(post)} post-employment "
		f"medical examinations, and {len(referred)} external referral{'' if len(referred) == 1 else 's'}. "
		f"{sum(notifiable.values()) or 'No'} notifiable disease case{'' if sum(notifiable.values()) == 1 else 's'} {'were' if sum(notifiable.values()) != 1 else 'was'} identified."
	)
	return {
		"period": {"start": str(start), "end": str(end), "label": month},
		"doc": doc,
		"summary": summary,
		"clinical": {"seen": len(cons), "assessments": len(general), "work_related": work_related, "prescriptions": prescriptions,
			"top_drugs": drugs[:5], "notifiable": [{"disease": k, "cases": v} for k, v in notifiable.items()]},
		"referrals": {"total": len(referred), "admitted": sum(1 for c in referred if c.admitted),
			"facilities": [{"facility": f or "Not stated", "cases": n} for f, n in Counter(c.referral_facility for c in referred).most_common()]},
		"exams": exams,
		"pharmacy": {"dispensed": drugs, "units": flt(sum(d.qty for d in drugs)), "stock": stock_rows, "low": [r for r in stock_rows if r["qty"] <= 10]},
		"education": {"sessions": education, "counselling": counselling, "avg_attendance": round(sum(attendance) / len(attendance), 1) if attendance else None},
		"meetings": meetings,
		"emergencies": [i for i in incidents if i.stabilization_steps or i.referral_destination],
		"field_first_aid": {"total": len(fa_cases), "by_department": Counter(c.department or "Not stated" for c in fa_cases).most_common(),
			"by_nature": Counter(c.nature for c in fa_cases).most_common(), "outcomes": Counter(c.outcome for c in fa_cases).most_common(),
			"supplies": fa_supplies, "kits": kits},
		"first_aid": {"rows": first_aid, "depleted": sum(1 for r in first_aid if r.stock_status == "Depleted")},
		"incidents": incidents,
		"surveillance": {"entries": surveillance, "requested": requested},
		"hygiene": hygiene,
		"trend": categories,
	}
