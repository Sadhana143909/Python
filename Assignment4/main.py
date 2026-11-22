import os
import shutil
import tempfile


class RegistrationError(Exception):
    """Raised when a registration line is damaged, invalid, or duplicate."""


def is_valid_email(email):
    email = email.strip()
    if email.count("@") != 1 or " " in email:
        return False
    local, domain = email.split("@")
    if not local or "." not in domain:
        return False
    return all(len(part) > 0 for part in domain.split("."))


def validate_line(raw_line):
    parts = [p.strip() for p in raw_line.strip().split(",")]
    if len(parts) != 5:
        raise RegistrationError(f"Damaged line: expected 5 fields, found {len(parts)}")

    reg_no, name, dept, email, events_str = parts
    if not reg_no or not name or not dept or not events_str:
        raise RegistrationError("Damaged line: one or more required fields are empty")

    if not is_valid_email(email):
        raise RegistrationError(f"Invalid email address: '{email}'")

    events = [e.strip() for e in events_str.split(";") if e.strip()]
    if not events:
        raise RegistrationError("No valid events listed")

    return {
        "reg_no": reg_no,
        "name": name,
        "dept": dept,
        "email": email,
        "events": events,
    }


def process_department_files(dept_files):
    seen_regs = set()
    master_list = []
    event_lists = {}
    dept_counts = {}
    errors = []

    for file_path in dept_files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_no, raw_line in enumerate(f, start=1):
                    if not raw_line.strip():
                        continue
                    try:
                        record = validate_line(raw_line)
                        reg_no = record["reg_no"]

                        if reg_no in seen_regs:
                            raise RegistrationError(f"Duplicate register number: '{reg_no}'")

                        seen_regs.add(reg_no)
                        master_list.append(record)

                        dept = record["dept"]
                        dept_counts[dept] = dept_counts.get(dept, 0) + 1

                        for ev in record["events"]:
                            event_lists.setdefault(ev, []).append(record)

                    except RegistrationError as err:
                        errors.append(f"{file_name} (Line {line_no}): {err}")

        except FileNotFoundError:
            errors.append(f"{file_name}: Missing department file")
        except PermissionError:
            errors.append(f"{file_name}: Permission denied")

    return master_list, event_lists, dept_counts, errors


def write_outputs(output_dir, master_list, event_lists, dept_counts, errors):
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "clean_master_list.csv"), "w", encoding="utf-8") as f:
        f.write("RegisterNumber,Name,Department,Email,Events\n")
        for rec in master_list:
            f.write(f"{rec['reg_no']},{rec['name']},{rec['dept']},{rec['email']},{';'.join(rec['events'])}\n")

    for event_name, participants in event_lists.items():
        safe_event = event_name.lower().replace(" ", "_")
        with open(os.path.join(output_dir, f"event_{safe_event}.csv"), "w", encoding="utf-8") as f:
            f.write("RegisterNumber,Name,Department,Email\n")
            for p in participants:
                f.write(f"{p['reg_no']},{p['name']},{p['dept']},{p['email']}\n")

    with open(os.path.join(output_dir, "summary_report.txt"), "w", encoding="utf-8") as f:
        f.write("=== COLLEGE FEST REGISTRATION SUMMARY ===\n")
        f.write(f"Total Valid Students: {len(master_list)}\n")
        f.write(f"Total Events: {len(event_lists)}\n")
        f.write(f"Total Errors Logged: {len(errors)}\n\n")
        f.write("--- Department-Wise Count ---\n")
        for dept, count in sorted(dept_counts.items()):
            f.write(f"{dept}: {count}\n")
        f.write("\n--- Event-Wise Count ---\n")
        for ev, plist in sorted(event_lists.items()):
            f.write(f"{ev}: {len(plist)}\n")

    with open(os.path.join(output_dir, "error_log.txt"), "w", encoding="utf-8") as f:
        for err in errors:
            f.write(err + "\n")


if __name__ == "__main__":
    demo_dir = tempfile.mkdtemp()
    input_dir = os.path.join(demo_dir, "inputs")
    output_dir = os.path.join(demo_dir, "outputs")
    os.makedirs(input_dir, exist_ok=True)

    # Create sample department files covering all test cases
    files_content = {
        "cse.txt": (
            "192565001,Kavitha B,CSE,kavitha@college.edu,Coding;Quiz\n"
            "192565001,Kavitha B,CSE,kavitha@college.edu,Dance\n"       # Duplicate
            "192565002,Arun M,CSE,arun_invalid_email,Music\n"           # Invalid email
        ),
        "ece.txt": (
            "192565003,Divya R,ECE,divya@college.edu,Coding;Dance\n"
            "192565004,DamagedRecordWithoutEnoughFields\n"              # Damaged line
        ),
        "it.txt": "192565005,Suresh K,IT,suresh@college.edu,Quiz;Music\n",
        "mech.txt": "192565006,Meena S,MECH,meena@college.edu,Dance\n",
        # civil.txt is intentionally omitted to test missing department file handling
    }

    for fname, content in files_content.items():
        with open(os.path.join(input_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)

    dept_file_paths = [
        os.path.join(input_dir, "cse.txt"),
        os.path.join(input_dir, "ece.txt"),
        os.path.join(input_dir, "it.txt"),
        os.path.join(input_dir, "mech.txt"),
        os.path.join(input_dir, "civil.txt"),
    ]

    master, events, depts, errs = process_department_files(dept_file_paths)
    write_outputs(output_dir, master, events, depts, errs)

    print("Generated Output Files:", sorted(os.listdir(output_dir)))
    for out_name in sorted(os.listdir(output_dir)):
        print(f"\n--- {out_name} ---")
        with open(os.path.join(output_dir, out_name), "r", encoding="utf-8") as f:
            print(f.read().strip())

    shutil.rmtree(demo_dir)
