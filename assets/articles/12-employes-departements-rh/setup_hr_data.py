#!/usr/bin/env python3
"""
Setup HR data for OdooSkills Blog — Article 12: Employés & Départements RH.

Creates departments, job positions, and 8 employees for the fictional
company InfoSphere (Algeria, DZD) on an Odoo 19 instance via XML-RPC.

Records are created only if they do not already exist (idempotent).

Usage:
    python3 setup_hr_data.py
"""

import sys
import xmlrpc.client

# ---------------------------------------------------------------------------
# Connection parameters
# ---------------------------------------------------------------------------
SERVER = "http://195.110.35.177:8019"
DATABASE = "odooskills_demo_v19"
USERNAME = "iastagenie@gmail.com"
PASSWORD = "REDACTED"

# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    "Direction Générale",
    "Département IT & Réseaux",
    "Département Commercial",
]

JOBS = [
    "Directeur Général",
    "Responsable IT",
    "Technicien Réseaux",
    "Développeur",
    "Responsable Commercial",
    "Commercial",
    "Assistante Administrative",
    "Technicien Support",
]

# Each tuple: (name, department, job_title, work_email, work_phone, coach_name)
# coach_name is None when there is no coach.
EMPLOYEES = [
    ("Mustapha Benhamida", "Direction Générale", "Directeur Général",
     "mustapha@infosphere.dz", "+213 21 00 00 01", None),
    ("Karim Mehdaoui", "Département IT & Réseaux", "Responsable IT",
     "karim@infosphere.dz", "+213 21 00 00 02", "Mustapha Benhamida"),
    ("Amina Bouzidi", "Département Commercial", "Responsable Commercial",
     "amina@infosphere.dz", "+213 21 00 00 03", "Mustapha Benhamida"),
    ("Yacine Khediri", "Département IT & Réseaux", "Développeur",
     "yacine@infosphere.dz", "+213 21 00 00 04", "Karim Mehdaoui"),
    ("Nadia Tlemçani", "Département IT & Réseaux", "Technicien Réseaux",
     "nadia@infosphere.dz", "+213 21 00 00 05", "Karim Mehdaoui"),
    ("Omar Saïdi", "Département Commercial", "Commercial",
     "omar@infosphere.dz", "+213 21 00 00 06", "Amina Bouzidi"),
    ("Samira Rahmouni", "Direction Générale", "Assistante Administrative",
     "samira@infosphere.dz", "+213 21 00 00 07", "Mustapha Benhamida"),
    ("Farid Boudiaf", "Département IT & Réseaux", "Technicien Support",
     "farid@infosphere.dz", "+213 21 00 00 08", "Karim Mehdaoui"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def connect(server, database, username, password):
    """Authenticate via XML-RPC and return (uid, models_proxy)."""
    common = xmlrpc.client.ServerProxy(f"{server}/xmlrpc/2/common")
    uid = common.authenticate(database, username, password, {})
    if not uid:
        print("[ERREUR] Authentification echouee. Verifiez les identifiants.")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{server}/xmlrpc/2/object")
    print(f"[OK] Connecte en tant que uid={uid}")
    return uid, models


def execute(models, database, uid, password, model, method, *args, **kwargs):
    """Shortcut for models.execute_kw."""
    return models.execute_kw(database, uid, password, model, method, *args, **kwargs)


def search_read_one(models, db, uid, pw, model, domain, fields):
    """Search for a single record. Return dict or None."""
    results = execute(models, db, uid, pw, model, "search_read",
                      [domain], {"fields": fields, "limit": 1})
    return results[0] if results else None


def ensure_module_installed(models, db, uid, pw, module_name):
    """Install a module if it is not already installed."""
    rec = search_read_one(models, db, uid, pw, "ir.module.module",
                          [("name", "=", module_name)],
                          ["state"])
    if not rec:
        print(f"[ERREUR] Module '{module_name}' introuvable dans la base.")
        sys.exit(1)

    if rec["state"] == "installed":
        print(f"[OK] Module '{module_name}' deja installe.")
        return

    print(f"[...] Installation du module '{module_name}' (etat actuel: {rec['state']})...")
    execute(models, db, uid, pw, "ir.module.module", "button_immediate_install",
            [[rec["id"]]])
    print(f"[OK] Module '{module_name}' installe avec succes.")


def get_or_create_department(models, db, uid, pw, name):
    """Return department id, creating it if necessary."""
    rec = search_read_one(models, db, uid, pw, "hr.department",
                          [("name", "=", name)], ["id"])
    if rec:
        print(f"  [=] Departement existant : {name} (id={rec['id']})")
        return rec["id"]

    dep_id = execute(models, db, uid, pw, "hr.department", "create",
                     [{"name": name}])
    print(f"  [+] Departement cree : {name} (id={dep_id})")
    return dep_id


def get_or_create_job(models, db, uid, pw, name):
    """Return job id, creating it if necessary."""
    rec = search_read_one(models, db, uid, pw, "hr.job",
                          [("name", "=", name)], ["id"])
    if rec:
        print(f"  [=] Poste existant : {name} (id={rec['id']})")
        return rec["id"]

    job_id = execute(models, db, uid, pw, "hr.job", "create",
                     [{"name": name}])
    print(f"  [+] Poste cree : {name} (id={job_id})")
    return job_id


def get_or_create_employee(models, db, uid, pw, vals):
    """Return employee id, creating from *vals* dict if not found by name."""
    name = vals["name"]
    rec = search_read_one(models, db, uid, pw, "hr.employee",
                          [("name", "=", name)], ["id"])
    if rec:
        print(f"  [=] Employe existant : {name} (id={rec['id']})")
        return rec["id"]

    emp_id = execute(models, db, uid, pw, "hr.employee", "create", [vals])
    print(f"  [+] Employe cree : {name} (id={emp_id})")
    return emp_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("OdooSkills — Article 12 : Setup donnees RH (InfoSphere)")
    print("=" * 60)

    uid, models = connect(SERVER, DATABASE, USERNAME, PASSWORD)

    # -- Step 1: Ensure hr module is installed ---------------------------------
    print("\n--- Etape 1 : Verification / Installation du module 'hr' ---")
    ensure_module_installed(models, DATABASE, uid, PASSWORD, "hr")

    # -- Step 2: Create departments --------------------------------------------
    print("\n--- Etape 2 : Departements ---")
    dept_ids = {}
    for dept_name in DEPARTMENTS:
        dept_ids[dept_name] = get_or_create_department(
            models, DATABASE, uid, PASSWORD, dept_name
        )

    # -- Step 3: Create job positions ------------------------------------------
    print("\n--- Etape 3 : Postes (hr.job) ---")
    job_ids = {}
    for job_name in JOBS:
        job_ids[job_name] = get_or_create_job(
            models, DATABASE, uid, PASSWORD, job_name
        )

    # -- Step 4: Create employees (two passes — first without coach) -----------
    print("\n--- Etape 4 : Employes ---")

    # First pass: create all employees without coach_id
    emp_ids = {}
    for (name, dept, job, email, phone, _coach) in EMPLOYEES:
        vals = {
            "name": name,
            "department_id": dept_ids[dept],
            "job_id": job_ids[job],
            "job_title": job,
            "work_email": email,
            "work_phone": phone,
        }
        emp_ids[name] = get_or_create_employee(
            models, DATABASE, uid, PASSWORD, vals
        )

    # Second pass: assign coaches
    print("\n--- Etape 5 : Affectation des coaches ---")
    for (name, _dept, _job, _email, _phone, coach_name) in EMPLOYEES:
        if coach_name is None:
            continue
        coach_id = emp_ids.get(coach_name)
        if not coach_id:
            print(f"  [!] Coach '{coach_name}' introuvable pour {name}")
            continue
        execute(models, DATABASE, uid, PASSWORD, "hr.employee", "write",
                [[emp_ids[name]], {"coach_id": coach_id}])
        print(f"  [OK] {name} -> coach: {coach_name}")

    # -- Summary ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("RESUME")
    print("=" * 60)

    print(f"\nDepartements ({len(dept_ids)}) :")
    for name, did in dept_ids.items():
        print(f"  - {name} (id={did})")

    print(f"\nPostes ({len(job_ids)}) :")
    for name, jid in job_ids.items():
        print(f"  - {name} (id={jid})")

    print(f"\nEmployes ({len(emp_ids)}) :")
    for name, eid in emp_ids.items():
        print(f"  - {name} (id={eid})")

    print("\n[TERMINE] Donnees HR creees avec succes.")


if __name__ == "__main__":
    main()
