"""Idle screen lock: per-user PIN, the lock flag and the unlock attempts limit.

This is a screen lock for patient privacy on a shared screen, not a security boundary: API calls are not blocked while
the screen is locked. The PIN is only ever checked here, on the server.
"""

import hmac

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

MAX_TRIES = 5
LOCKOUT_SECONDS = 300
DEFAULT_MINUTES = 15


def _user():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in first."), frappe.AuthenticationError)
	return frappe.session.user


def _flag_key(user):
	return f"clinic_screen_locked:{user}"


def _tries_key(user):
	return f"clinic_screen_lock_tries:{user}"


def _profile(user):
	return frappe.db.get_value(
		"Clinic Staff Profile", {"user": user}, ["name", "lock_after_minutes"], as_dict=True
	)


def _pin(user):
	profile = _profile(user)
	if not profile:
		return None
	return get_decrypted_password("Clinic Staff Profile", profile.name, "screen_lock_pin", raise_exception=False) or None


def _minutes(user):
	profile = _profile(user)
	minutes = (profile and profile.lock_after_minutes) or frappe.db.get_single_value(
		"Clinic Settings", "idle_lock_minutes"
	)
	return max(1, min(int(minutes or DEFAULT_MINUTES), 240))


def _tries(user):
	return int(frappe.cache.get_value(_tries_key(user), expires=True) or 0)


@frappe.whitelist()
def status():
	user = _user()
	has_pin = bool(_pin(user))
	return {
		"has_pin": has_pin,
		"locked": bool(has_pin and frappe.cache.get_value(_flag_key(user))),
		"minutes": _minutes(user),
	}


@frappe.whitelist()
def lock():
	user = _user()
	if not _pin(user):
		return {"locked": False}  # nothing could unlock this user, so never lock them
	frappe.cache.set_value(_flag_key(user), 1)
	return {"locked": True}


@frappe.whitelist()
def unlock(pin=None):
	user = _user()
	saved = _pin(user)
	if not saved:
		frappe.cache.delete_value(_flag_key(user))
		return {"locked": False}

	tries = _tries(user)
	if tries >= MAX_TRIES:
		frappe.throw(
			_("Too many wrong PINs. Try again in 5 minutes, or use “Not you? Sign out” and sign in with your password."),
			frappe.ValidationError,
		)

	if hmac.compare_digest(str(pin or "").encode(), saved.encode()):
		frappe.cache.delete_value(_flag_key(user))
		frappe.cache.delete_value(_tries_key(user))
		return {"locked": False}

	tries += 1
	frappe.cache.set_value(_tries_key(user), tries, expires_in_sec=LOCKOUT_SECONDS)
	if tries >= MAX_TRIES:
		frappe.throw(
			_("Wrong PIN. Too many tries: the screen cannot be unlocked for 5 minutes. Use “Not you? Sign out” to sign in with your password."),
			frappe.ValidationError,
		)
	left = MAX_TRIES - tries
	frappe.throw(
		_("Wrong PIN. {0} {1} left.").format(left, _("try") if left == 1 else _("tries")), frappe.ValidationError
	)


def clear_on_login(login_manager=None):
	"""Signing in with the password is a real unlock, so nobody comes back to a locked screen."""
	user = frappe.session.user
	frappe.cache.delete_value(_flag_key(user))
	frappe.cache.delete_value(_tries_key(user))
