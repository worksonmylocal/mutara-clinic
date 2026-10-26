"""Data for the printable documents: investigation referrals (lab / imaging) and employment medical certificates."""

import frappe
from frappe import _
from frappe.utils import now_datetime

from clinic.api.common import clinic_profile, patient_card, require_any, user_name

SIGNING_DESIGNATIONS = ("Doctor", "Clinical Officer")
REFERRAL_TYPES = ("Laboratory", "Imaging")


def _signer(user):
	"""Who signs: the clinician who saw the patient, with their registration details."""
	profile = (
		frappe.db.get_value(
			"Clinic Staff Profile", {"user": user}, ["designation", "registration_no", "signature"], as_dict=True
		)
		if user
		else None
	)
	return {
		"name": user_name(user),
		"designation": profile.designation if profile else None,
		"registration_no": profile.registration_no if profile else None,
		"signature": profile.signature if profile else None,
		"can_sign": bool(profile and profile.designation in SIGNING_DESIGNATIONS),
	}


def _base(consultation):
	doc = frappe.get_doc("Clinic Consultation", consultation)
	triage = frappe.db.get_value("Clinic Triage", doc.triage, "*", as_dict=True) if doc.triage else None
	return doc, {
		"clinic": clinic_profile(),
		"patient": patient_card(doc.patient),
		"visit": doc.visit,
		"consultation": doc.name,
		"consultation_date": doc.consultation_date,
		"triage": triage,
		"signer": _signer(doc.doctor),
		"printed_by": user_name(frappe.session.user),
		"printed_on": now_datetime(),
	}


@frappe.whitelist()
def referral(consultation, category):
	"""Request form sent with the patient to an external laboratory or imaging centre."""
	require_any("consultation")
	if category not in REFERRAL_TYPES:
		frappe.throw(_("Unknown referral type {0}").format(category))
	doc, data = _base(consultation)
	rows = [r for r in doc.investigations if r.category == category]
	if not rows:
		frappe.throw(_("No {0} investigations have been requested on this consultation").format(category.lower()))
	data.update(
		category=category,
		items=[
			{"investigation": r.investigation, "urgency": r.urgency, "clinical_notes": r.clinical_notes}
			for r in rows
		],
		referred_to=next((r.referred_to for r in rows if r.referred_to), None),
		urgent=any(r.urgency == "Urgent" for r in rows),
		complaint=doc.presenting_complaint,
		history=doc.history_of_presenting_illness,
		diagnoses=[{"diagnosis": d.diagnosis, "type": d.diagnosis_type} for d in doc.diagnoses],
		drug_allergies=doc.drug_allergies,
	)
	doc.add_comment("Info", _("{0} referral printed by {1}").format(category, user_name(frappe.session.user)))
	return data


@frappe.whitelist()
def medical_certificate(consultation):
	"""Pre- or post-employment medical examination report."""
	require_any("consultation")
	doc, data = _base(consultation)
	if doc.consultation_type == "Consultation":
		frappe.throw(_("This is a normal consultation, not an employment medical"))
	data.update(
		exam_type=doc.consultation_type,
		job_position=doc.job_position,
		fitness_status=doc.fitness_status,
		valid_until=doc.certificate_valid_until,
		restrictions=doc.fitness_restrictions,
		remarks=doc.medical_remarks,
		tests=[{"test": t.test, "result": t.result, "findings": t.findings} for t in doc.medical_tests],
		history={
			"Past medical": doc.past_medical_history,
			"Past surgical": doc.past_surgical_history,
			"Current medication": doc.current_medication,
			"Allergies": doc.drug_allergies,
			"Family": doc.family_history,
			"Occupational": doc.occupational_history,
		},
		investigations=[
			{"investigation": r.investigation, "category": r.category} for r in doc.investigations
		],
		diagnoses=[{"diagnosis": d.diagnosis, "type": d.diagnosis_type} for d in doc.diagnoses],
	)
	doc.add_comment("Info", _("Medical certificate printed by {0}").format(user_name(frappe.session.user)))
	return data


@frappe.whitelist()
def weekly_report(week=None, include_sunday=0):
	"""The weekly clinic activity report: one column per day."""
	require_any("consultation")
	from clinic.reports import weekly_data

	return {
		"clinic": clinic_profile(),
		"report": weekly_data(week, int(include_sunday or 0)),
		"printed_by": user_name(frappe.session.user),
		"printed_on": now_datetime(),
	}


@frappe.whitelist()
def monthly_report(month=None):
	"""The clinical officer's monthly report for the month containing `month` (YYYY-MM or a date)."""
	require_any("consultation")
	from clinic.reports import monthly_data

	if month and len(month) == 7:
		month += "-01"
	data = monthly_data(month)
	data.update(clinic=clinic_profile(), printed_by=user_name(frappe.session.user), printed_on=now_datetime())
	return data
